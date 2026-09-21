"""Turns the daily NLP measures into the two day-sets the estimator needs, and
builds Table 1.

This is where the NLP and the econometrics meet, and it is the step the professor's
guidance describes directly: "Use NLP on war news to flag high-news days (1 = high,
0 = low), then apply heteroskedasticity-based identification." Rigobon and Sack built
their Table 1 by reading newspapers and writing down seventeen dates by hand. Here
that job is done automatically by a measure computed from GDELT's coverage timelines
(script 03), so the day-selection itself does not depend on anyone's memory of which
days felt important, and is unaffected by anything in this script.

The score is the average of three standardised components built in src/event_days.py
- a jump in coverage volume above its own trailing baseline, a shift in the
escalation/de-escalation balance, and how contested that balance was. Every trading day
gets an explicit binary `war_news_flag` (1 = high-news day, 0 = everything else); a
matched `set` column (H/L/other) additionally marks the equal-sized comparison group
the estimator uses (see src/event_days.pick_low_days for why the comparison days
cannot simply be "the rest").

News sourcing for Table 1's event column. GDELT's *article* endpoint (used in an
earlier version of this script, and still the source for script 10's vocabulary-
coverage check where it succeeds) refuses the large majority of individual requests
under sustained use and could not reliably deliver a corpus for the 18 selected days
within a session - this was tested extensively (see README.md, "Why Table 1's sources
were hand-verified"). Rather than present tertiary-source summaries as if they were
primary reporting, Table 1's event descriptions are sourced from
data/news/verified_events.json: dated, attributed summaries checked against Al
Jazeera, CNN and Bloomberg reporting for each of the 18 selected days, with a source
URL for every entry. This is a manual verification step, run once and cached - it
does not feed the day-selection (which is complete before this file is ever read) and
does not affect reproducibility of the estimation results, only the citations printed
next to them.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from config import INTERIM, MARKET, NEWS, TABLES, N_HIGH_DAYS, NORMALISING_VAR, PAPER_NORMALISING_VAR
from event_days import build_score, pick_high_days, pick_low_days
import warrisk_lexicon as lex
import news_score as ns

SUM_COLS = ["war_volume", "iran_volume", "escalation_volume",
            "deescalation_volume", "hormuz_volume"]
MEAN_COLS = ["direction", "contest", "war_tone", "war_share", "hormuz_share"]


def map_news_to_trading_days(news: pd.DataFrame,
                             trading_days: pd.DatetimeIndex) -> pd.DataFrame:
    """Assign each calendar day of news to the next trading day at or after it, so
    weekend news is priced on the following Monday."""
    news = news.copy()
    pos = trading_days.searchsorted(news.index, side="left")
    inside = pos < len(trading_days)
    news = news[inside]
    news["trading_day"] = trading_days[pos[inside]]

    g = news.groupby("trading_day")
    out = g[SUM_COLS].sum()
    w = news["war_volume"].clip(lower=1e-6)
    for c in MEAN_COLS:
        num = (news[c] * w).groupby(news["trading_day"]).sum()
        den = w.where(news[c].notna()).groupby(news["trading_day"]).sum()
        out[c] = num / den.replace(0, np.nan)
    out["n_calendar_days"] = g.size()
    return out


def load_verified_events() -> dict:
    path = NEWS / "verified_events.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def direction_label(x: float) -> str:
    if x > 0.10:
        return "Increased"
    if x < -0.10:
        return "Decreased"
    return "Unclear"


def main():
    news = pd.read_csv(INTERIM / "news_daily.csv", index_col="date", parse_dates=True)
    changes = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
    changes = changes[changes.index <= news.index.max()]
    trading_days = changes.index

    daily = map_news_to_trading_days(news, trading_days).reindex(trading_days)
    daily = build_score(daily)

    high = pick_high_days(daily["war_news_score"], N_HIGH_DAYS)
    low = pick_low_days(high, trading_days, score=daily["war_news_score"])

    daily["set"] = "other"
    daily.loc[high, "set"] = "H"
    daily.loc[low, "set"] = "L"
    # The explicit binary flag the professor's guidance describes: 1 = high-news
    # day, 0 = everything else. `set` additionally marks the matched L subset of
    # the 0s that the paired heteroskedasticity estimator uses.
    daily["war_news_flag"] = daily["set"].eq("H").astype(int)
    daily.to_csv(INTERIM / "event_days.csv")

    # ---- verified real-news sourcing + NLP cross-check on that real text
    verified = load_verified_events()
    fin_by_day, lex_by_day = {}, {}
    for d in high:
        key = d.date().isoformat()
        summary = verified.get(key, {}).get("summary", "")
        if not summary:
            continue
        sents = [s.strip() for s in summary.replace("; ", ". ").split(". ") if len(s.split()) >= 4]
        fin_by_day[key] = ns.daily_moments(ns.score_headlines(sents)) if sents else {"mean": np.nan, "sd": np.nan, "n": 0}
        lex_by_day[key] = float(np.mean([lex.polarity(s) for s in sents])) if sents else np.nan

    # ---- Table 1
    x1 = changes[NORMALISING_VAR]          # the normalising variable (Brent)
    y2 = changes[PAPER_NORMALISING_VAR]    # the paper's normalising variable
    rows = []
    for d in high:
        key = d.date().isoformat()
        v = verified.get(key, {})
        fin = fin_by_day.get(key, {"mean": np.nan, "sd": np.nan, "n": 0})
        rows.append({
            "date": key,
            "event": v.get("summary", ""),
            "source": v.get("source", ""),
            "source_url": v.get("url", ""),
            "war_risk": direction_label(float(daily.loc[d, "direction"])),
            "news_score": round(float(daily.loc[d, "war_news_score"]), 2),
            "attention_z": round(float(daily.loc[d, "z_attention"]), 2),
            "tone_shift_z": round(float(daily.loc[d, "z_tone_shift"]), 2),
            "contest_z": round(float(daily.loc[d, "z_disagreement"]), 2),
            "direction": round(float(daily.loc[d, "direction"]), 3),
            "event_lexicon_mean": round(lex_by_day.get(key, np.nan), 3),
            "event_finbert_mean": round(fin["mean"], 3) if fin["n"] else np.nan,
            "d_brent_usd": round(float(x1.get(d, np.nan)), 2),
            "d_2y_bp": round(float(y2.get(d, np.nan)) * 100, 1),
        })
    t1 = pd.DataFrame(rows)
    t1.to_csv(TABLES / "table1_war_news_days.csv", index=False)

    # ---- the testable implication: H days must actually be more volatile
    h_mask = daily["set"].eq("H").values
    l_mask = daily["set"].eq("L").values
    v_h = float(np.nanmean(x1.values[h_mask] ** 2))
    v_l = float(np.nanmean(x1.values[l_mask] ** 2))

    print(f"\nTrading days in sample: {len(trading_days)}")
    print(f"H (war-news, flag=1) days: {len(high)}   "
          f"L (matched comparison, flag=0) days: {len(low)}")
    print(f"\nTable 1 -> {TABLES / 'table1_war_news_days.csv'}\n")
    print(t1[["date", "war_risk", "news_score", "d_brent_usd", "d_2y_bp",
              "source"]].to_string(index=False))

    print(f"\nVariance of the change in '{NORMALISING_VAR}' "
          f"(the identifying assumption):")
    print(f"  H days {v_h:.6f}   L days {v_l:.6f}   ratio {v_h / v_l:.2f}")

    print("\nWar-risk direction on H days:")
    print(t1["war_risk"].value_counts().to_string())

    missing = t1["event"].eq("").sum()
    if missing:
        print(f"\n{missing} H day(s) have no verified event text in "
              f"data/news/verified_events.json")

    ok = t1["event_finbert_mean"].notna() & t1["event_lexicon_mean"].notna()
    if ok.sum() > 2:
        print("\nAgreement between the two NLP methods, scored on the verified real "
              f"event text: r = "
              f"{t1.loc[ok, 'event_lexicon_mean'].corr(t1.loc[ok, 'event_finbert_mean']):+.3f}")


if __name__ == "__main__":
    main()
