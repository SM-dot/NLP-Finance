"""Builds the report's figures.

Figure 1  the NLP war-risk news index through 2026, with the selected war-news days
          marked, above the two variables that anchor the story - Brent and the
          two-year Treasury yield. Three stacked panels sharing one x-axis rather
          than one panel with several y-axes: series on different scales never
          belong on a shared vertical axis.
Figure 2  variance of each variable on war-news days relative to comparison days -
          the heteroskedasticity the estimator runs on.
Figure 3  the estimated impact of a war-risk increase, by variable, with 95%
          intervals; colour carries the sign, grey marks estimates that are not
          significant at 5%.

Palette: the blue/red diverging pair from the course's chart palette, validated for
colour-vision deficiency; sign is carried by colour *and* by position either side of
zero, never by colour alone.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from config import MARKET, INTERIM, TABLES, FIGURES, NORMALISATION_LABEL

BLUE, RED, GREY = "#2a78d6", "#e34948", "#8a8a85"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
GRID = "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2,
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})


def figure1(ev: pd.DataFrame, lv: pd.DataFrame) -> None:
    h = ev.index[ev["set"].eq("H")]
    fig, axes = plt.subplots(3, 1, figsize=(9.5, 8.0), sharex=True,
                             gridspec_kw={"height_ratios": [1.15, 1, 1], "hspace": 0.18})

    ax = axes[0]
    ax.plot(ev.index, ev["war_news_score"], color=BLUE, lw=1.4, zorder=2)
    ax.scatter(h, ev.loc[h, "war_news_score"], s=34, color=RED, zorder=3,
               edgecolor=SURFACE, linewidth=1.2, label="War-news day (H)")
    ax.axhline(0, color=GRID, lw=1)
    ax.set_ylabel("Index (z-score)")
    ax.set_title("NLP war-risk news index, and the days it selects", loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.7)

    for ax, col, lab, unit in [(axes[1], "brent", "Brent crude", "$/barrel"),
                               (axes[2], "y2", "Two-year Treasury yield", "percent")]:
        ax.plot(lv.index, lv[col], color=BLUE, lw=1.4, zorder=2)
        for d in h:
            ax.axvline(d, color=RED, alpha=0.20, lw=1.6, zorder=1)
        ax.set_ylabel(unit)
        ax.set_title(lab, loc="left")
        ax.grid(axis="y", alpha=0.7)

    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    axes[-1].set_xlabel("2026")
    fig.savefig(FIGURES / "figure1_war_news_index.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def figure2(t3: pd.DataFrame) -> None:
    d = t3[t3["var_L"] > 0].copy()
    d["ratio"] = d["var_H"] / d["var_L"]
    d = d.sort_values("ratio")

    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    y = np.arange(len(d))
    colours = [BLUE if r > 1 else GREY for r in d["ratio"]]
    ax.barh(y, d["ratio"], color=colours, height=0.62, zorder=2)
    ax.axvline(1, color=INK2, lw=1.1, zorder=3)
    ax.set_yticks(y, d["variable"])
    ax.set_xlabel("Variance on war-news days ÷ variance on comparison days")
    ax.set_title("Figure 2. Oil and the risk gauges carry the war factor;\n"
                 "Treasuries and gold barely register it\n"
                 "(grey: no more volatile on war-news days than on comparison days)",
                 loc="left")
    ax.grid(axis="x", alpha=0.7)
    for yi, v in zip(y, d["ratio"]):
        ax.text(v + 0.12, yi, f"{v:.1f}×", va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, d["ratio"].max() * 1.16)
    fig.savefig(FIGURES / "figure2_variance_ratio.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


UNIT_PANELS = [
    ("pct", "Percent change"),
    ("pp", "Percentage-point change (yields and spreads)"),
    ("vol", "Index-point change"),
    ("$", "Dollar change"),
]


def figure3(t2: pd.DataFrame) -> None:
    """One panel per unit. Percentage points, percent and dollars cannot share an
    x-axis - a 36-dollar move in gold and a 0.65 percent move in the S&P are not
    comparable lengths - so each unit gets its own scale."""
    d = t2.dropna(subset=["w3_coef", "w3_se"]).copy()
    groups = [(u, lab, d[d["units"].eq(u)].sort_values("w3_coef"))
              for u, lab in UNIT_PANELS]
    groups = [g for g in groups if len(g[2])]

    heights = [len(g[2]) for g in groups]
    fig, axes = plt.subplots(len(groups), 1, figsize=(8.6, 0.42 * sum(heights) + 2.4),
                             gridspec_kw={"height_ratios": heights, "hspace": 0.32})
    axes = np.atleast_1d(axes)

    for ax, (unit, label, g) in zip(axes, groups):
        sig = g["w3_t"].abs() >= 1.96
        colours = [GREY if not s else (RED if c > 0 else BLUE)
                   for s, c in zip(sig, g["w3_coef"])]
        y = np.arange(len(g))
        ax.errorbar(g["w3_coef"], y, xerr=1.96 * g["w3_se"], fmt="none",
                    ecolor=GREY, elinewidth=1.4, capsize=3, zorder=2)
        ax.scatter(g["w3_coef"], y, s=54, c=colours, zorder=3,
                   edgecolor=SURFACE, linewidth=1.2)
        ax.axvline(0, color=INK2, lw=1.1, zorder=1)
        ax.set_yticks(y, list(g["variable"]))
        ax.set_ylim(-0.7, len(g) - 0.3)
        ax.set_title(label, loc="left", fontsize=9)
        ax.grid(axis="x", alpha=0.7)

    axes[0].annotate("Figure 3. Estimated impact of higher Iran war risk\n"
                     f"Response to {NORMALISATION_LABEL}. Combined instrument, "
                     "95% intervals;\ngrey marks estimates not significant at 5%.",
                     xy=(0, 1), xytext=(0, 34), xycoords="axes fraction",
                     textcoords="offset points", va="bottom", fontsize=10,
                     fontweight="bold", color=INK)
    fig.savefig(FIGURES / "figure3_coefficients.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    ev = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    lv = pd.read_csv(MARKET / "levels.csv", index_col="date", parse_dates=True)
    t2 = pd.read_csv(TABLES / "table2_war_risk_impact.csv")
    t3 = pd.read_csv(TABLES / "table3_variance_decomposition.csv")

    figure1(ev, lv)
    figure2(t3)
    figure3(t2)
    print(f"Figures written to {FIGURES}")
    for p in sorted(FIGURES.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
