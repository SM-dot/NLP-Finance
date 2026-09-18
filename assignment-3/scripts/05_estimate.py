"""Estimates the response of every financial variable to the Iran war-risk factor.

Replicates Tables 2 and 3 of Rigobon and Sack (2003) on 2026 data, and adds the
robustness checks that Rigobon (2003) section IV says this estimator needs:

  Table 2  d_j1 for each variable under all three instrument sets, scaled to a
           war-risk increase large enough to move the two-year yield 25bp.
  Table 3  how much of each variable's variance the war factor accounts for.
  Table 4  the rank condition for each pair (Rigobon 2003, eq. 7) - the condition
           that fails when the H and L covariance matrices are proportional, in
           which case nothing is identified.
  Table 5  stability of the estimates as the H-set is widened and narrowed. This is
           the empirical counterpart of propositions 3 and 4: misspecified regime
           windows leave the estimator consistent as long as the rank condition
           still holds, so the estimates should not move much.
  Table 6  the same estimates using next-day changes for the three non-US indices,
           which close before the US session.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from config import (MARKET, INTERIM, TABLES, VARIABLES, VAR_LABELS, VAR_UNITS,
                    VAR_GROUP, NORMALISING_VAR, NORMALISATION, ROBUSTNESS_N,
                    N_HIGH_DAYS, BASELINE_WINDOW, NORMALISATION_LABEL,
                    PAPER_NORMALISING_VAR, PAPER_NORMALISATION,
                    PAPER_NORMALISATION_LABEL)
from event_days import pick_high_days, pick_low_days
import heteroskedasticity as het

FOREIGN = {"stoxx": "stoxx_next", "nikkei": "nikkei_next", "ta125": "ta125_next"}


def load(next_day_foreign: bool = False):
    ch = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
    ev = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    ev = ev.reindex(ch.index)
    if next_day_foreign:
        for base, nxt in FOREIGN.items():
            ch[base] = ch[nxt]
    return ch, ev


def day_masks(ev: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    return ev["set"].eq("H").values, ev["set"].eq("L").values


def estimate_table(ch: pd.DataFrame, ev: pd.DataFrame,
                   normaliser: str = NORMALISING_VAR,
                   scale: float = NORMALISATION) -> pd.DataFrame:
    """Table 2: every variable against the normalising variable, two at a time."""
    h, l = day_masks(ev)
    keep = h | l
    x1 = ch.loc[keep, normaliser].values
    high = h[keep]

    rows = []
    for col, label, unit, group in VARIABLES:
        if col == normaliser:
            continue
        x2 = ch.loc[keep, col].values
        res = het.estimate_all(x1, x2, high)
        row = {"variable": label, "column": col, "units": unit, "group": group}
        for k in ["w1", "w2", "w3"]:
            row[f"{k}_coef"] = res[k]["coef"] * scale
            row[f"{k}_t"] = res[k]["t"]
            row[f"{k}_se"] = res[k]["se"] * abs(scale)
        row["n"] = res["w1"]["n"]
        row["first_stage_F_w1"] = res["w1"]["first_stage_F"]
        rows.append(row)
    return pd.DataFrame(rows)


def variance_ratio_table(ch: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """The identifying assumption, variable by variable: is the variance actually
    higher on war-news days? This is what decides which variable can serve as the
    normalising one."""
    h, l = day_masks(ev)
    rows = []
    for col, label, unit, group in VARIABLES:
        x = ch[col]
        vH = float(np.nanmean(x[h] ** 2))
        vL = float(np.nanmean(x[l] ** 2))
        rows.append({"variable": label, "column": col, "units": unit, "group": group,
                     "var_H": vH, "var_L": vL,
                     "ratio": vH / vL if vL > 0 else np.nan})
    return pd.DataFrame(rows).sort_values("ratio", ascending=False)


def variance_table(ch: pd.DataFrame, ev: pd.DataFrame,
                   t2: pd.DataFrame) -> pd.DataFrame:
    """Table 3: variance on H and L days, and the share the war factor explains.

    The H/L variances use the estimation day-sets. The 'all days' column uses every
    trading day in the window, splitting it into the H days and everything else,
    which is what the paper does over its ten-week window.
    """
    h, l = day_masks(ev)
    keep = h | l
    x1_est = ch.loc[keep, NORMALISING_VAR].values
    high_est = h[keep]

    coef = dict(zip(t2["column"], t2["w3_coef"] / NORMALISATION))
    all_high = h                      # H days within the full window

    rows = []
    for col, label, unit, group in VARIABLES:
        d_j1 = 1.0 if col == NORMALISING_VAR else coef.get(col, np.nan)
        x2_est = ch.loc[keep, col].values

        # variances over the matched estimation sets
        ok = np.isfinite(x2_est)
        var_H = float(np.mean(x2_est[ok & high_est] ** 2))
        var_L = float(np.mean(x2_est[ok & ~high_est] ** 2))
        d_var1 = float(np.mean(x1_est[high_est] ** 2) - np.mean(x1_est[~high_est] ** 2))
        predicted = (d_j1 ** 2) * d_var1 if np.isfinite(d_j1) else np.nan

        # share of the cumulative variance over the whole window
        full = ch[col].values
        okf = np.isfinite(full)
        n_H = int((all_high & okf).sum())
        n_O = int((~all_high & okf).sum())
        var_H_full = float(np.mean(full[all_high & okf] ** 2)) if n_H else np.nan
        var_O_full = float(np.mean(full[~all_high & okf] ** 2)) if n_O else np.nan
        var_cum = n_H * var_H_full + n_O * var_O_full

        rows.append({
            "variable": label, "column": col, "units": unit, "group": group,
            "var_L": var_L, "var_H": var_H,
            "predicted_change": predicted if col != NORMALISING_VAR else np.nan,
            "pct_var_H_days": (100 * predicted / var_H) if col != NORMALISING_VAR and var_H > 0 else np.nan,
            "pct_var_all_days": (100 * n_H * predicted / var_cum)
                                 if col != NORMALISING_VAR and var_cum > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def rank_table(ch: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """Table 4: is the system actually identified, pair by pair?

    Two readings of the same requirement. The rank statistic of Rigobon (2003) eq.
    (7) is zero exactly when the two covariance matrices are proportional, in which
    case the heteroskedasticity teaches us nothing. Its bootstrap test has very
    little power at 18 days a regime - it is a function of products of second
    moments - so the first-stage F on the excluded instrument is reported beside it.
    That is the operational form of the same condition: it asks directly how much of
    the variation in the normalising variable the instrument explains, and it is what
    the standard errors in Table 2 already respond to.
    """
    h, l = day_masks(ev)
    keep = h | l
    x1 = ch.loc[keep, NORMALISING_VAR].values
    high = h[keep]

    rows = []
    for col, label, _, _ in VARIABLES:
        if col == NORMALISING_VAR:
            continue
        x2 = ch.loc[keep, col].values
        r = het.rank_condition_bootstrap(x1, x2, high, n_boot=2000)
        est = het.estimate_all(x1, x2, high)
        rows.append({"variable": label, "column": col, "rank_stat": r["stat"],
                     "p_value": r["p_value"], "ci_low": r["ci_low"],
                     "ci_high": r["ci_high"],
                     "ci_excludes_zero": (r["ci_low"] > 0) or (r["ci_high"] < 0),
                     "first_stage_F_w1": est["w1"]["first_stage_F"],
                     "first_stage_F_w2": est["w2"]["first_stage_F"],
                     "t_w3": est["w3"]["t"]})
    return pd.DataFrame(rows)


def robustness_table(ch: pd.DataFrame) -> pd.DataFrame:
    """Re-select H and L for several H-set sizes and re-estimate (Rigobon 2003,
    propositions 3 and 4: the estimates should survive a misspecified window)."""
    ev_full = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    score = ev_full.reindex(ch.index)["war_news_score"]

    rows = []
    for n_high in ROBUSTNESS_N:
        high = pick_high_days(score, n_high)
        low = pick_low_days(high, ch.index, score=score)
        mask_h = ch.index.isin(high)
        mask_l = ch.index.isin(low)
        keep = mask_h | mask_l
        x1 = ch.loc[keep, NORMALISING_VAR].values
        hh = mask_h[keep]
        for col, label, _, _ in VARIABLES:
            if col == NORMALISING_VAR:
                continue
            res = het.estimate_all(x1, ch.loc[keep, col].values, hh)
            rows.append({"n_high": n_high, "variable": label, "column": col,
                         "coef": res["w3"]["coef"] * NORMALISATION,
                         "t": res["w3"]["t"]})
    return pd.DataFrame(rows)


def fmt(t2: pd.DataFrame) -> str:
    lines = [f"{'Variable':<34}{'Units':>6}{'w1':>10}{'w2':>10}{'w3':>10}{'t(w3)':>8}"]
    for _, r in t2.iterrows():
        lines.append(f"{r['variable']:<34}{r['units']:>6}{r['w1_coef']:>10.2f}"
                     f"{r['w2_coef']:>10.2f}{r['w3_coef']:>10.2f}{r['w3_t']:>8.2f}")
    return "\n".join(lines)


def main():
    ch, ev = load()
    n_h = int(ev["set"].eq("H").sum())
    print(f"Estimating on {n_h} war-news days and "
          f"{int(ev['set'].eq('L').sum())} comparison days\n")

    t0 = variance_ratio_table(ch, ev)
    t0.to_csv(TABLES / "table0_variance_ratios.csv", index=False)
    print("Identifying assumption: variance on war-news days vs comparison days")
    print(t0[["variable", "var_H", "var_L", "ratio"]].round(4).to_string(index=False))
    print(f"\nNormalising on '{NORMALISING_VAR}' "
          f"(ratio {float(t0.loc[t0['column'].eq(NORMALISING_VAR), 'ratio'].iloc[0]):.2f}); "
          f"the paper's choice '{PAPER_NORMALISING_VAR}' has ratio "
          f"{float(t0.loc[t0['column'].eq(PAPER_NORMALISING_VAR), 'ratio'].iloc[0]):.2f}.")

    t2 = estimate_table(ch, ev)
    t2.to_csv(TABLES / "table2_war_risk_impact.csv", index=False)
    print(f"\n\nTable 2. Estimated impact of {NORMALISATION_LABEL}\n")
    print(fmt(t2))

    t2b = estimate_table(ch, ev, normaliser=PAPER_NORMALISING_VAR,
                         scale=PAPER_NORMALISATION)
    t2b.to_csv(TABLES / "table2b_normalised_on_2y.csv", index=False)
    print(f"\n\nTable 2b. The same, normalised the paper's way: {PAPER_NORMALISATION_LABEL}")
    print("(reported for comparability; the two-year yield barely responds to war")
    print(" news in 2026, so this column is weakly identified - see Table 4)\n")
    print(fmt(t2b))

    t3 = variance_table(ch, ev, t2)
    t3.to_csv(TABLES / "table3_variance_decomposition.csv", index=False)
    print("\n\nTable 3. Variances of the financial variables")
    print(t3[["variable", "var_L", "var_H", "predicted_change",
              "pct_var_H_days", "pct_var_all_days"]].round(5).to_string(index=False))

    t4 = rank_table(ch, ev)
    t4.to_csv(TABLES / "table4_rank_condition.csv", index=False)
    print("\n\nTable 4. Is the system identified? (Rigobon 2003, eq. 7)")
    print(t4[["variable", "rank_stat", "p_value", "first_stage_F_w1",
              "first_stage_F_w2", "t_w3"]].round(3).to_string(index=False))

    t5 = robustness_table(ch)
    t5.to_csv(TABLES / "table5_robustness_window.csv", index=False)
    piv = t5.pivot(index="variable", columns="n_high", values="coef")
    print("\n\nTable 5. Coefficient (w3) as the war-news day set is widened")
    print(piv.round(2).to_string())

    ch_next, ev_next = load(next_day_foreign=True)
    t6 = estimate_table(ch_next, ev_next)
    t6 = t6[t6["column"].isin(FOREIGN)]
    t6.to_csv(TABLES / "table6_foreign_next_day.csv", index=False)
    print("\n\nTable 6. Non-US indices measured next day (they close before the US)")
    print(t6[["variable", "w3_coef", "w3_t"]].round(2).to_string(index=False))

    print(f"\nTables written to {TABLES}")


if __name__ == "__main__":
    main()
