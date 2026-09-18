"""Turns the daily NLP measures into the two day-sets the estimator needs, and
builds Table 1.

This is where the NLP and the econometrics meet. Rigobon and Sack built their Table 1
by reading newspapers and writing down seventeen days on which war news was clearly
the dominant driver. Here that job is done by a measure computed from the coverage
itself, so the selection is reproducible and does not depend on anyone's memory of
which days felt important.

The score is the average of three standardised components built in src/event_days.py
- a jump in coverage volume above its own trailing baseline, a shift in the
escalation/de-escalation balance, and how contested that balance was. H is the top
N_HIGH_DAYS trading days by that score.

News is mapped to trading days by settlement convention: everything published after
the previous trading day's close through the current close belongs to the current
trading day, so the Saturday the war began (28 February) lands on Monday 2 March.

L pairs each H day with the nearest trading day that is neither an H day nor adjacent
to one, and that also sits in the quiet half of the war-news score distribution. That
last restriction is an adaptation of the paper's footnote 7 rule, and it is necessary
here: their window was the run-up to a war, where "nearby" days were genuinely quiet,
whereas 2026 contains six months of running war, so the days nearest a big war-news
day are themselves war days. See src/event_days.pick_low_days.

Event text for the selected days is then pulled from Wikipedia's Current Events
Portal, so Table 1 can name what happened and so the lexicon and FinBERT have a
common piece of text to read. It plays no part in choosing the days.

Outputs:
  data/interim/event_days.csv              every trading day, its score and its set
  report_tables/table1_war_news_days.csv   Table 1: the H days and what happened
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from config import (INTERIM, MARKET, TABLES, N_HIGH_DAYS, NORMALISING_VAR,
                    PAPER_NORMALISING_VAR)
from event_days import build_score, pick_high_days, pick_low_days
import warrisk_lexicon as lex
import news_score as ns
import wikinews

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


def fetch_events(days: list[pd.Timestamp],
                 trading_days: pd.DatetimeIndex) -> dict[str, list[str]]:
    """Iran-related event text for the calendar days feeding each selected day."""
    print(f"Fetching event text for {len(days)} selected trading days...")
    out: dict[str, list[str]] = {}
    for d in days:
        prev = trading_days[trading_days < d]
        lo = (prev[-1] if len(prev) else d - pd.Timedelta(days=3)).date()
        items: list[str] = []
        c = lo + pd.Timedelta(days=1).to_pytimedelta()
        while c <= d.date():
            items += wikinews.day_events(c)
            c += pd.Timedelta(days=1).to_pytimedelta()
        seen, keep = set(), []
        for t in items:
            k = "".join(ch for ch in t.lower() if ch.isalnum() or ch == " ")
            if k not in seen:
                seen.add(k)
                keep.append(t)
        out[d.date().isoformat()] = keep
    return out


def best_event(items: list[str]) -> str:
    """The event carrying the most war-risk vocabulary, trimmed of its source note."""
    best, best_hits = "", -1
    for t in items:
        s = lex.score_text(t)
        hits = s["escalation"] + s["de_escalation"]
        if hits > best_hits:
            best, best_hits = t, hits
    return re.sub(r"\s*\([^()]*\)\s*$", "", best).strip()


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
    daily.to_csv(INTERIM / "event_days.csv")

    # ---- event text and FinBERT for the selected days
    heads = fetch_events(high + low, trading_days)
    fin_by_day = {}
    for day, titles in heads.items():
        if titles:
            fin_by_day[day] = ns.daily_moments(ns.score_headlines(titles))

    # ---- Table 1
    x1 = changes[NORMALISING_VAR]          # the normalising variable (Brent)
    y2 = changes[PAPER_NORMALISING_VAR]    # the paper's normalising variable
    rows = []
    for d in high:
        key = d.date().isoformat()
        titles = heads.get(key, [])
        fin = fin_by_day.get(key, {"mean": np.nan, "sd": np.nan, "n": 0})
        lex_pol = [lex.polarity(t) for t in titles]
        rows.append({
            "date": key,
            "event": best_event(titles),
            "war_risk": direction_label(float(daily.loc[d, "direction"])),
            "news_score": round(float(daily.loc[d, "war_news_score"]), 2),
            "attention_z": round(float(daily.loc[d, "z_attention"]), 2),
            "tone_shift_z": round(float(daily.loc[d, "z_tone_shift"]), 2),
            "contest_z": round(float(daily.loc[d, "z_disagreement"]), 2),
            "direction": round(float(daily.loc[d, "direction"]), 3),
            "headline_lexicon_mean": round(float(np.mean(lex_pol)), 3) if lex_pol else np.nan,
            "headline_finbert_mean": round(fin["mean"], 3) if fin["n"] else np.nan,
            "n_headlines": fin.get("n", 0),
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
    print(f"H (war-news) days: {len(high)}   L (comparison) days: {len(low)}")
    print(f"\nTable 1 -> {TABLES / 'table1_war_news_days.csv'}\n")
    print(t1[["date", "war_risk", "news_score", "d_brent_usd", "d_2y_bp", "event"]]
          .to_string(index=False, max_colwidth=54))

    print(f"\nVariance of the change in '{NORMALISING_VAR}' "
          f"(the identifying assumption):")
    print(f"  H days {v_h:.6f}   L days {v_l:.6f}   ratio {v_h / v_l:.2f}")
    if v_h <= v_l:
        print("  WARNING: H days are not more volatile - identification fails.")

    print("\nWar-risk direction on H days:")
    print(t1["war_risk"].value_counts().to_string())

    ok = t1["headline_finbert_mean"].notna() & t1["headline_lexicon_mean"].notna()
    if ok.sum() > 2:
        print("\nAgreement between the two headline-level NLP methods on H days: "
              f"r = {t1.loc[ok, 'headline_lexicon_mean'].corr(t1.loc[ok, 'headline_finbert_mean']):+.3f}")


if __name__ == "__main__":
    main()
