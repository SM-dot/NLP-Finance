"""Merges the two tone scores with the one-day market reaction for each
document release, and writes the master analysis table used by the notebook.

Reaction-day rule: statements, minutes and press conferences are released at
2:00 p.m. ET (confirmed in the source text), well inside the trading day, so
the reaction window is that day's close vs. the prior trading day's close.
Speeches and testimony carry no reliable intraday timestamp in the scraped
text, so - as a documented simplification - they use the same same-day
close-to-close convention. DXY, the 10s2s spread and the 1-year yield are
measured as a level change; growth-minus-value is already a return spread,
so its "one-day change" is that spread on the reaction day itself.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from config import INTERIM, MARKET, TABLES, WARSH_START


def nearest_trading_days(market: pd.DataFrame, doc_date: pd.Timestamp):
    idx = market.index
    on_or_after = idx[idx >= doc_date]
    if len(on_or_after) == 0:
        return None, None
    reaction_day = on_or_after[0]
    before = idx[idx < reaction_day]
    if len(before) == 0:
        return None, None
    prior_day = before[-1]
    return reaction_day, prior_day


def main():
    wl = pd.read_csv(INTERIM / "documents_wordlist_scored.csv")
    fb = pd.read_csv(INTERIM / "documents_finbert_scored.csv")
    keep_fb = ["doc_type", "date", "path", "finbert_score", "n_sentences", "mean_pos", "mean_neg", "mean_neu"]
    df = wl.merge(fb[keep_fb], on=["doc_type", "date", "path"], how="left")

    market = pd.read_csv(MARKET / "daily_indicators.csv", index_col=0, parse_dates=True).sort_index()

    level_cols = {"T10Y2Y": "d_10s2s", "DGS1": "d_1y", "DXY": "d_dxy", "DGS3MO": "d_3mo_bill"}
    rows = []
    for _, row in df.iterrows():
        doc_date = pd.Timestamp(row["date"])
        reaction_day, prior_day = nearest_trading_days(market, doc_date)
        rec = dict(reaction_day=reaction_day, prior_day=prior_day)
        if reaction_day is None:
            rows.append(rec)
            continue
        for col, newname in level_cols.items():
            try:
                rec[newname] = market.loc[reaction_day, col] - market.loc[prior_day, col]
            except KeyError:
                rec[newname] = np.nan
        rec["d_growth_minus_value"] = market.loc[reaction_day, "growth_minus_value"]
        rows.append(rec)

    reactions = pd.DataFrame(rows)
    out = pd.concat([df.reset_index(drop=True), reactions], axis=1)
    out["chair"] = out["chair"].astype(str)
    out["is_warsh"] = pd.to_datetime(out["date"]) >= pd.Timestamp(WARSH_START)

    out_path = INTERIM / "master_dataset.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved {out.shape} -> {out_path}")
    print(out[["doc_type", "d_dxy", "d_10s2s", "d_1y", "d_growth_minus_value", "d_3mo_bill"]].describe())


if __name__ == "__main__":
    main()
