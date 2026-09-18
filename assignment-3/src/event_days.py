"""Selection of the high- and low-war-news-variance day sets.

Kept in src/ rather than in the script that first uses it because script 05 re-runs
the same selection at several set sizes for the robustness table, and both must use
identical logic for that comparison to mean anything.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import BASELINE_WINDOW, QUIET_QUANTILE


def build_score(df: pd.DataFrame, baseline_window: int = BASELINE_WINDOW) -> pd.DataFrame:
    """Attach the three news-variance components and their average.

    attention     log coverage volume less its own trailing median: the jump in
                  coverage, not its level, since a running war is always in the news
    tone_shift    absolute move in the escalation/de-escalation balance from its
                  trailing mean - direction discarded, because a day that makes war
                  dramatically less likely is as informative as one that makes it
                  more likely
    disagreement  how split the day's coverage was between the two vocabularies,
                  weighted by volume (the "contest" measure from script 03)
    """
    df = df.copy()

    log_vol = np.log(df["war_volume"].clip(lower=1e-4))
    baseline = log_vol.shift(1).rolling(baseline_window, min_periods=3).median()
    df["attention"] = log_vol - baseline

    tone_base = df["direction"].shift(1).rolling(baseline_window, min_periods=3).mean()
    df["tone_shift"] = (df["direction"] - tone_base).abs()

    df["disagreement"] = df["contest"]

    for c in ["attention", "tone_shift", "disagreement"]:
        s = df[c]
        df["z_" + c] = (s - s.mean()) / s.std(ddof=0)
    df["war_news_score"] = df[["z_attention", "z_tone_shift", "z_disagreement"]].mean(axis=1)
    return df


def pick_high_days(score: pd.Series, n_high: int) -> list[pd.Timestamp]:
    return list(score.dropna().nlargest(n_high).index.sort_values())


def pick_low_days(high: list[pd.Timestamp], all_days: pd.DatetimeIndex,
                  score: pd.Series | None = None,
                  quiet_quantile: float = QUIET_QUANTILE) -> list[pd.Timestamp]:
    """One comparison day per war-news day.

    Rigobon and Sack choose low-variance days "as close as possible to, but not
    included in" the war-news days, so that the variances of every *other* factor
    are as similar as possible across the two sets (their footnote 7). Days
    immediately either side of a war-news day are excluded too, since news that
    breaks after a close lands on the following session.

    One adaptation is needed here, and it matters. Their window was the ten weeks
    *before* a war, where war news arrived on seventeen identifiable days and the
    rest of the sample was comparatively quiet, so "nearby" and "quiet" were much
    the same thing. 2026 contains a war that ran for six months, and the days
    nearest a big war-news day are themselves war days. Taking the nearest
    non-adjacent day therefore fills L with exactly the coverage L is supposed to
    exclude - in this sample it made L *more* volatile than H, which breaks
    identification outright.

    So candidates for L are restricted to days in the quiet part of the war-news
    score distribution, and the nearest such day is then chosen. Both of the paper's
    goals survive: L days are still as close in time to their H day as possible, so
    the other factors' variances are comparable, and they are now genuinely
    low-war-news days.

    The two sets come out equal-sized, which the estimator needs: with unequal sets
    the paper's raw instrument measures n_H*E_H[dx^2] - n_L*E_L[dx^2] instead of the
    difference in variances.
    """
    pos_of = {d: i for i, d in enumerate(all_days)}
    high_pos = sorted(pos_of[d] for d in high if d in pos_of)

    banned = set()
    for p in high_pos:
        banned |= {p - 1, p, p + 1}

    if score is not None:
        s = score.reindex(all_days)
        cutoff = s.dropna().quantile(quiet_quantile)
        for q, d in enumerate(all_days):
            v = s.get(d, np.nan)
            if not np.isfinite(v) or v > cutoff:
                banned.add(q)

    chosen: list[int] = []
    for p in high_pos:
        best, best_dist = None, None
        for q in range(len(all_days)):
            if q in banned or q in chosen:
                continue
            dist = abs(q - p)
            if best_dist is None or dist < best_dist:
                best, best_dist = q, dist
        if best is not None:
            chosen.append(best)
    return [all_days[q] for q in sorted(chosen)]
