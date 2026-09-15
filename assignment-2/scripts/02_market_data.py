"""Downloads the four target indicators plus the 3-month bill control.

FRED series (T10Y2Y, DGS1, DGS3MO) come from the public fredgraph.csv
endpoint, no API key needed. DXY, IWF and IWN come from Yahoo Finance via
yfinance. Everything is saved as one wide daily CSV.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import requests
import yfinance as yf

from config import MARKET, START_DATE, END_DATE, FRED_SERIES, YAHOO_TICKERS

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def fetch_fred(series_id: str) -> pd.Series:
    r = requests.get(FRED_CSV.format(sid=series_id), timeout=30)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.set_index("date")[series_id]
    return df[(df.index.date >= START_DATE) & (df.index.date <= END_DATE)]


def fetch_yahoo(ticker: str) -> pd.Series:
    for attempt in range(4):
        try:
            df = yf.download(ticker, start=str(START_DATE), end=str(END_DATE),
                              progress=False, auto_adjust=True)
            if len(df) > 0:
                s = df["Close"]
                if hasattr(s, "columns"):
                    s = s.iloc[:, 0]
                s.name = ticker
                return s
        except Exception as e:
            print(f"  retry {ticker}: {e}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"could not fetch {ticker}")


def main():
    frames = {}
    for sid, label in FRED_SERIES.items():
        print(f"FRED {sid} ({label})...")
        frames[sid] = fetch_fred(sid)

    for ticker, label in YAHOO_TICKERS.items():
        print(f"Yahoo {ticker} ({label})...")
        frames[ticker] = fetch_yahoo(ticker)

    market = pd.concat(frames, axis=1)
    market.index.name = "date"
    market = market.sort_index()

    # Derived series
    market["DXY"] = market["DX-Y.NYB"]
    market["growth_minus_value"] = market["IWF"].pct_change() - market["IWN"].pct_change()
    market["growth_minus_value_level"] = (1 + market["growth_minus_value"].fillna(0)).cumprod()

    out = MARKET / "daily_indicators.csv"
    market.to_csv(out)
    print(f"\nSaved {market.shape} -> {out}")
    print(market.tail())


if __name__ == "__main__":
    main()
