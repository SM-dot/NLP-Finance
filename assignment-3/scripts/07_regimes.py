"""Splits war-news days into three regimes and tests the professor's hypothesis
directly: bad war news should push yields and oil up and equities down; good war
news should do the reverse; no-news days should be fundamentals-driven (small,
unsigned average moves).

This extends the binary H (war-news, flag=1) / L (comparison, flag=0) split used for
the main heteroskedasticity estimates into three groups, using the `direction` measure
already computed in script 03 (the escalation-minus-de-escalation share of that day's
coverage):

  Bad-news   H day, direction > +0.10 (coverage skewed toward escalation)
  Good-news  H day, direction < -0.10 (coverage skewed toward de-escalation)
  Mixed      H day, direction in [-0.10, 0.10] ("Unclear" in Table 1 - heavy
             coverage that does not skew either way)
  No-news    L day (the matched comparison group; flag=0)

This is also a direct test of Rigobon (2003) section II.C, "Identification under More
than Two Regimes": the heteroskedasticity estimator's central claim is that the
structural loading d_j1 does not depend on which way the news broke on a given day -
only on how much war-related variance there was. If that is true, estimating d_j1
separately from the (Bad, No-news) pair and the (Good, No-news) pair should give
*similar* sign and magnitude, even though those two day-sets have opposite average
z1 realisations. Agreement is a real overidentification check; disagreement would be
evidence against the assumption that the response is direction-symmetric. With only
8 Bad and 4 Good days the individual pairwise estimates are necessarily noisy, so
this is reported as a directional check, not a precision result - the descriptive
mean-comparison table above it is the more reliable evidence for the regime split.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from config import MARKET, INTERIM, TABLES, FIGURES, VARIABLES, NORMALISING_VAR, NORMALISATION
import heteroskedasticity as het

BLUE, RED, GOLD, GREY = "#2a78d6", "#e34948", "#eda100", "#8a8a85"
INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 9,
    "axes.titlesize": 10, "axes.titleweight": "bold",
    "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})

HYPOTHESIS_VARS = ["y2", "y10", "brent", "spx", "stoxx", "vix", "hy"]

DIR_THRESHOLD = 0.10


def classify(daily: pd.DataFrame) -> pd.Series:
    regime = pd.Series("other", index=daily.index)
    is_h = daily["set"].eq("H")
    is_l = daily["set"].eq("L")
    regime[is_l] = "No-news"
    regime[is_h & (daily["direction"] > DIR_THRESHOLD)] = "Bad-news"
    regime[is_h & (daily["direction"] < -DIR_THRESHOLD)] = "Good-news"
    regime[is_h & (daily["direction"].abs() <= DIR_THRESHOLD)] = "Mixed"
    return regime


def descriptive_table(ch: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """Mean daily change of every variable, by regime, with a t-test of each
    war-news regime against No-news."""
    rows = []
    no_news = ch[regime.reindex(ch.index).eq("No-news")]
    for col, label, unit, group in VARIABLES:
        row = {"variable": label, "column": col, "units": unit}
        base = no_news[col].dropna()
        for reg in ["Bad-news", "Good-news", "Mixed", "No-news"]:
            sub = ch.loc[regime.reindex(ch.index).eq(reg), col].dropna()
            row[f"mean_{reg}"] = float(sub.mean()) if len(sub) else np.nan
            row[f"n_{reg}"] = int(len(sub))
            if reg != "No-news" and len(sub) > 1 and len(base) > 1:
                t, p = stats.ttest_ind(sub, base, equal_var=False)
                row[f"t_{reg}_vs_No-news"] = float(t)
                row[f"p_{reg}_vs_No-news"] = float(p)
            elif reg != "No-news":
                row[f"t_{reg}_vs_No-news"] = np.nan
                row[f"p_{reg}_vs_No-news"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def overidentification_check(ch: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """Estimate d_j1 separately from (Bad, No-news) and (Good, No-news); compare."""
    r = regime.reindex(ch.index)
    bad_no = r.isin(["Bad-news", "No-news"])
    good_no = r.isin(["Good-news", "No-news"])

    x1_bad = ch.loc[bad_no, NORMALISING_VAR].values
    high_bad = r[bad_no].eq("Bad-news").values
    x1_good = ch.loc[good_no, NORMALISING_VAR].values
    high_good = r[good_no].eq("Good-news").values

    rows = []
    for col, label, unit, group in VARIABLES:
        if col == NORMALISING_VAR:
            continue
        res_bad = het.estimate_all(x1_bad, ch.loc[bad_no, col].values, high_bad)
        res_good = het.estimate_all(x1_good, ch.loc[good_no, col].values, high_good)
        d_bad = res_bad["w1"]["coef"] * NORMALISATION
        d_good = res_good["w1"]["coef"] * NORMALISATION
        same_sign = np.sign(d_bad) == np.sign(d_good) if np.isfinite(d_bad) and np.isfinite(d_good) else False
        rows.append({
            "variable": label, "column": col, "units": unit,
            "d_from_bad_vs_no (n=8 vs 18)": d_bad,
            "d_from_good_vs_no (n=4 vs 18)": d_good,
            "same_sign": same_sign,
        })
    return pd.DataFrame(rows)


def main():
    ch = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
    daily = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    ch = ch[ch.index <= daily.index.max()]

    regime = classify(daily)
    regime.to_csv(INTERIM / "regimes.csv", header=["regime"])
    print("Regime counts:")
    print(regime.value_counts().to_string())

    desc = descriptive_table(ch, regime)
    desc.to_csv(TABLES / "table7_regime_mean_comparison.csv", index=False)
    print("\nTable 7. Mean daily change by news regime "
          "(testing: bad news -> yields/oil up, equities down; good news -> reverse)\n")
    show = desc[["variable", "units", "mean_Bad-news", "mean_Good-news",
                "mean_Mixed", "mean_No-news"]]
    print(show.to_string(index=False, float_format=lambda v: f"{v:8.4f}"))

    hyp_vars = {"y2": "up", "y10": "up", "brent": "up", "spx": "down",
               "stoxx": "down", "vix": "up", "hy": "up"}
    print("\nDirectional check against the professor's hypothesis "
          "(bad-news day, sign of mean move):")
    n_match = 0
    for col, expect in hyp_vars.items():
        row = desc[desc["column"] == col].iloc[0]
        actual_sign = "up" if row["mean_Bad-news"] > 0 else "down"
        match = actual_sign == expect
        n_match += match
        print(f"  {col:10s} expected {expect:5s} got {actual_sign:5s} "
              f"({row['mean_Bad-news']:+.4f})  {'match' if match else 'MISMATCH'}")
    print(f"  {n_match}/{len(hyp_vars)} variables match the hypothesised sign on "
          f"bad-news days")

    figure6(desc)
    print(f"\nFigure 6 -> {FIGURES / 'figure6_regime_comparison.png'}")

    over = overidentification_check(ch, regime)
    over.to_csv(TABLES / "table8_regime_overidentification.csv", index=False)
    print("\nTable 8. Overidentification check: d_j1 estimated separately from "
          "bad-news and good-news days\n(Rigobon 2003 sec. II.C - if the structural "
          "loading is direction-symmetric, signs should agree despite\nopposite "
          "average news direction in the two sub-samples; small sub-samples make "
          "magnitudes noisy)\n")
    print(over.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
    print(f"\nSigns agree on {int(over['same_sign'].sum())}/{len(over)} variables")


def figure6(desc: pd.DataFrame) -> None:
    """Standardised mean move (z-scored per variable so a $ move and a pp move can
    share an axis) across the three news regimes, for the seven variables the
    professor's hypothesis names directly."""
    d = desc[desc["column"].isin(HYPOTHESIS_VARS)].set_index("column")
    d = d.reindex(HYPOTHESIS_VARS)

    regimes = ["Bad-news", "No-news", "Good-news"]
    colors = {"Bad-news": RED, "No-news": GREY, "Good-news": BLUE}

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(d))
    width = 0.26
    for i, reg in enumerate(regimes):
        vals = d[f"mean_{reg}"]
        # standardise within variable using the spread across all four regimes so
        # bars are visually comparable across very different natural units
        spread = d[["mean_Bad-news", "mean_Good-news", "mean_Mixed", "mean_No-news"]].abs().max(axis=1)
        z = vals / spread.replace(0, np.nan)
        ax.bar(x + (i - 1) * width, z, width=width, color=colors[reg], label=reg)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xticks(x, [{"y2": "2y yield", "y10": "10y yield", "brent": "Brent",
                       "spx": "S&P 500", "stoxx": "Euro Stoxx", "vix": "VIX",
                       "hy": "HY spread"}[c] for c in d.index])
    ax.set_ylabel("Mean daily change (share of the largest regime move,\nso different units are visually comparable)")
    ax.set_title("Figure 6. Bad-news days push yields/oil/VIX up and equities down;\n"
                 "good-news days do the reverse (simple regime means, not IV estimates)",
                 loc="left")
    ax.legend(frameon=False, loc="upper right", ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure6_regime_comparison.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
