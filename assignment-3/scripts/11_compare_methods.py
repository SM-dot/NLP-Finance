"""Table 14 and Figure 5: the methods, side by side.

Three genuinely different questions get asked of the same 173 trading days, and this
script is where their answers meet:

  1. Heteroskedasticity (Rigobon-Sack, heuristic H-set) - the headline result. A
     structural loading, from the shift in variance between war-news and comparison
     days, scaled to a war-risk increase that moves Brent $5.
  2. Heteroskedasticity, but the H-set comes from the cross-validated logistic
     classifier instead of the hand-tuned threshold - same estimator, different day
     labels, a check on whether the headline results depend on exactly how the line
     was drawn.
  3. Event-study OLS - the mean level of each variable on flagged days minus
     unflagged days, no variance-shift logic at all.

The numbers in (1) and (2) are directly comparable (same units, same normalisation).
The event-study numbers in (3) are not on the same scale - they answer "how much
higher/lower is the average day when the flag is on," not "how much does X move per
unit of the war-risk factor" - so the comparison that matters here is of *sign* and
*statistical significance*, not magnitude. That distinction is the point of this
table: where all three agree on sign and significance, the finding does not depend
on which method or which day-set you trust; where they disagree, the report says so
rather than picking whichever number is largest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import TABLES, FIGURES, VAR_LABELS

BLUE, RED, GREY, GOLD = "#2a78d6", "#e34948", "#8a8a85", "#eda100"
INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 9,
    "axes.titlesize": 10, "axes.titleweight": "bold",
    "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})

KEY_VARS = ["y2", "y10", "breakeven10", "spx", "stoxx", "hy", "bbb", "vix",
           "dollar", "brent", "gold"]
# Gold's classifier-based estimate is a documented outlier (a near-zero first
# stage inflates it to +305 - see Table 4/11's own diagnostics), so it is kept in
# the numeric tables but dropped from Figure 5, where one outlier bar would
# otherwise compress every other variable to an invisible sliver.
FIGURE_VARS = [v for v in KEY_VARS if v != "gold"]


def main():
    t2 = pd.read_csv(TABLES / "table2_war_risk_impact.csv")
    t11 = pd.read_csv(TABLES / "table11_method_comparison.csv")
    t12 = pd.read_csv(TABLES / "table12_event_study.csv")

    rows = []
    for col in KEY_VARS:
        if col not in t2["column"].values:
            continue
        het_heur = t2[t2["column"] == col].iloc[0]
        het_clf_row = t11[t11["column"] == col]
        es = t12[t12["column"] == col].iloc[0]

        het_clf_coef = float(het_clf_row["coef__Supervised classifier (CV-predicted)"].iloc[0]) if len(het_clf_row) else np.nan
        het_clf_t = float(het_clf_row["t__Supervised classifier (CV-predicted)"].iloc[0]) if len(het_clf_row) else np.nan

        rows.append({
            "variable": VAR_LABELS.get(col, col), "column": col,
            "het_heuristic_coef": het_heur["w3_coef"], "het_heuristic_t": het_heur["w3_t"],
            "het_classifier_coef": het_clf_coef, "het_classifier_t": het_clf_t,
            "event_study_beta": es["beta"], "event_study_t": es["t"],
            "sign_het_heuristic": np.sign(het_heur["w3_coef"]),
            "sign_het_classifier": np.sign(het_clf_coef) if np.isfinite(het_clf_coef) else 0,
            "sign_event_study": np.sign(es["beta"]),
        })
    comp = pd.DataFrame(rows)
    comp["all_signs_agree"] = (
        (comp["sign_het_heuristic"] == comp["sign_het_classifier"]) &
        (comp["sign_het_heuristic"] == comp["sign_event_study"])
    )
    comp["sig_het_heuristic"] = comp["het_heuristic_t"].abs() >= 1.96
    comp["sig_event_study"] = comp["event_study_t"].abs() >= 1.96
    comp.to_csv(TABLES / "table14_method_agreement.csv", index=False)

    print("Table 14. Sign and significance agreement across three independent "
          "ways of measuring the same thing\n")
    show = comp[["variable", "het_heuristic_coef", "het_heuristic_t",
                "het_classifier_coef", "event_study_beta", "event_study_t",
                "all_signs_agree"]]
    print(show.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))

    n_agree = int(comp["all_signs_agree"].sum())
    print(f"\n{n_agree}/{len(comp)} key variables agree in sign across all three "
          f"day-classification/estimation combinations")

    figure5(comp)
    print(f"\nFigure 5 -> {FIGURES / 'figure5_method_comparison.png'}")


def figure5(comp: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    d = comp[comp["column"] != "gold"].sort_values("het_heuristic_coef")
    y = np.arange(len(d))
    h = 0.25

    ax.barh(y + h, d["het_heuristic_coef"], height=h, color=BLUE,
           label="Heteroskedasticity, heuristic H-set (headline result)")
    ax.barh(y, d["het_classifier_coef"], height=h, color=GOLD,
           label="Heteroskedasticity, classifier H-set")
    # event-study is on a different scale - show as sign-only markers, not bars
    for yi, v, t in zip(y - h, d["event_study_beta"], d["event_study_t"]):
        marker = "o" if abs(t) >= 1.96 else "x"
        ax.scatter([np.sign(v) * 0.02 * (abs(d["het_heuristic_coef"]).max())], [yi],
                  color=RED, marker=marker, s=50, zorder=3)

    ax.axvline(0, color=INK2, lw=1.1)
    ax.set_yticks(y, d["variable"])
    ax.set_xlabel("Coefficient (heteroskedasticity methods, both scaled the same way)")
    ax.set_title("Figure 5. Three ways to draw the day-classification line, and one\n"
                 "plain event-study check, mostly agree on sign", loc="left")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=RED,
                              markersize=8, label="Event-study sign (●=sig., ×=not) — different scale, shown at ±edge"))
    ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=7.5)
    ax.grid(axis="x", alpha=0.5)
    ax.text(0.01, -0.09, "Gold omitted: its classifier-H-set estimate is a "
           "documented near-zero-first-stage outlier (+306, see Table 11) that "
           "would compress every other bar.", transform=ax.transAxes,
           fontsize=7, color=INK2, style="italic")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure5_method_comparison.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
