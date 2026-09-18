"""Downloads the financial variables and builds the daily change matrix.

Levels come from FRED (yields and spreads, via the public fredgraph.csv endpoint)
and Yahoo Finance (equity indices, commodities, FX, VIX). The output is two files:

  data/market/levels.csv    daily levels, one column per variable
  data/market/changes.csv   daily changes in the units of Rigobon-Sack Table 2
                            (percentage points for yields and spreads, percent for
                            price indices, dollars for oil and gold)

Non-US equity indices close before the US session, so a war headline that breaks
during US hours is first tradeable in Tokyo or Frankfurt the next day. The same-day
change is kept as the baseline for every variable (consistent with the paper, and a
mistimed variable attenuates rather than biases the estimate); the t+1 variant for
the three foreign indices is written alongside it as `<col>_next` for the robustness
check in script 05.
"""
import sys
import time
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import requests
import yfinance as yf

from config import (MARKET, START_DATE, END_DATE, FRED_SERIES, YAHOO_TICKERS,
                    VAR_UNITS, USER_AGENT)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FOREIGN_INDICES = ["stoxx", "nikkei", "ta125"]


def fetch_fred(series_id: str) -> pd.Series:
    r = requests.get(FRED_CSV.format(sid=series_id), timeout=60,
                     headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")[series_id], errors="coerce")
    return s[(s.index.date >= START_DATE) & (s.index.date <= END_DATE)]


def fetch_yahoo(tickers: list[str]) -> pd.DataFrame:
    for attempt in range(4):
        try:
            df = yf.download(tickers, start=str(START_DATE),
                             end=str(END_DATE + pd.Timedelta(days=1).to_pytimedelta()),
                             progress=False, auto_adjust=True)["Close"]
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"  retry Yahoo batch: {e}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("could not fetch Yahoo Finance data")


def main():
    print("FRED...")
    fred = pd.concat({sid: fetch_fred(sid) for sid in FRED_SERIES}, axis=1)
    print(f"  {fred.shape}")

    print("Yahoo Finance...")
    yah = fetch_yahoo(list(YAHOO_TICKERS))
    print(f"  {yah.shape}")

    lv = pd.DataFrame(index=fred.index.union(yah.index).sort_values())
    # US block, Rigobon-Sack Table 2 order
    lv["y2"] = fred["DGS2"]
    lv["y10"] = fred["DGS10"]
    lv["breakeven10"] = fred["DGS10"] - fred["DFII10"]
    lv["spx"] = yah["^GSPC"]
    lv["bbb"] = fred["BAMLC0A4CBBB"]
    lv["hy"] = fred["BAMLH0A0HYM2"]
    lv["brent"] = yah["BZ=F"]
    lv["gold"] = yah["GC=F"]
    lv["dollar"] = fred["DTWEXBGS"]
    lv["vix"] = yah["^VIX"]
    # Global and sector block
    lv["stoxx"] = yah["^STOXX50E"]
    lv["nikkei"] = yah["^N225"]
    lv["ta125"] = yah["^TA125.TA"]
    lv["em"] = yah["EEM"]
    lv["chf"] = yah["CHF=X"]
    lv["energy"] = yah["XLE"]
    lv["airlines"] = yah["JETS"]
    lv["defence"] = yah["ITA"]
    lv["bill3mo"] = fred["DGS3MO"]

    # Keep US trading days only: a day is a trading day if the S&P has a close.
    lv = lv[lv["spx"].notna()]
    lv.index.name = "date"

    # Changes, in the units each variable is reported in
    ch = pd.DataFrame(index=lv.index)
    for col in lv.columns:
        unit = VAR_UNITS.get(col, "pp")
        if unit == "pct":
            ch[col] = lv[col].pct_change() * 100.0
        elif unit == "$":
            ch[col] = lv[col].diff()
        else:                      # "pp": yields, spreads, VIX
            ch[col] = lv[col].diff()
    ch["bill3mo"] = lv["bill3mo"].diff()

    # t+1 variant for markets that close before the US session
    for col in FOREIGN_INDICES:
        ch[f"{col}_next"] = ch[col].shift(-1)

    ch = ch.iloc[1:]
    lv.to_csv(MARKET / "levels.csv")
    ch.to_csv(MARKET / "changes.csv")

    print(f"\nLevels  {lv.shape} -> {MARKET / 'levels.csv'}")
    print(f"Changes {ch.shape} -> {MARKET / 'changes.csv'}")
    print(f"Window: {lv.index[0].date()} to {lv.index[-1].date()}, "
          f"{len(lv)} US trading days")
    print("\nMissing values per column:")
    print(ch.isna().sum()[lambda s: s > 0].to_string() or "  none")
    print("\nStandard deviation of daily changes:")
    print(ch.std().round(4).to_string())


if __name__ == "__main__":
    main()
