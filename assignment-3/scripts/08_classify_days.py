"""Alternative day-classification methods, and the robustness check they enable.

Produces three more ways to flag a day 1 (war-news) / 0 (not), beyond the heuristic
z-score threshold used for the headline Table 2, and re-runs the heteroskedasticity
estimator on each to see how much the choice of classification method actually
matters for the economic conclusions. See src/classify.py for the methodology and
why a market-based label is used to *evaluate* the classifier but never to *select*
the H-set fed back into estimation.

Outputs:
  report_tables/table9_classifier_performance.csv    confusion matrix + metrics
  report_tables/table10_classifier_coefficients.csv   which NLP features matter
  report_tables/table11_method_comparison.csv         d_j1 under four day-sets
  figures/figure4_classifier_diagnostics.png          ROC curve, confusion matrix,
                                                      probability time series,
                                                      coefficient plot
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import (MARKET, INTERIM, TABLES, FIGURES, VARIABLES, NORMALISING_VAR,
                    NORMALISATION, N_HIGH_DAYS)
from event_days import pick_high_days, pick_low_days
import classify as clf
import heteroskedasticity as het

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


def estimate_for_highset(ch: pd.DataFrame, high_idx: pd.DatetimeIndex,
                         low_idx: pd.DatetimeIndex) -> pd.DataFrame:
    mask_h = ch.index.isin(high_idx)
    mask_l = ch.index.isin(low_idx)
    keep = mask_h | mask_l
    x1 = ch.loc[keep, NORMALISING_VAR].values
    hh = mask_h[keep]
    rows = []
    for col, label, unit, group in VARIABLES:
        if col == NORMALISING_VAR:
            continue
        res = het.estimate_all(x1, ch.loc[keep, col].values, hh)
        rows.append({"variable": label, "column": col, "units": unit,
                     "coef": res["w3"]["coef"] * NORMALISATION, "t": res["w3"]["t"]})
    return pd.DataFrame(rows)


def main():
    ch = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
    daily = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    ch = ch[ch.index <= daily.index.max()]
    daily = daily.reindex(ch.index)

    # ---- ground-truth label and features
    label, composite = clf.market_composite_label(ch, N_HIGH_DAYS)
    X = clf.build_feature_matrix(daily)

    overlap = int((label.eq(1) & daily["war_news_flag"].eq(1)).sum())
    print(f"Market-composite label: {int(label.sum())} high-stress days "
          f"(independent of NLP)")
    print(f"Overlap with the NLP-heuristic H-set: {overlap}/{N_HIGH_DAYS} days "
          f"({100 * overlap / N_HIGH_DAYS:.0f}%)\n")

    # ---- supervised classifier
    res = clf.fit_logistic_cv(X, label)
    perf = pd.DataFrame([{
        "n_total": res["n_total"], "n_positive": res["n_positive"],
        "accuracy": res["accuracy"], "precision": res["precision"],
        "recall": res["recall"], "f1": res["f1"], "roc_auc": res["roc_auc"],
        "tn": res["confusion_matrix"][0, 0], "fp": res["confusion_matrix"][0, 1],
        "fn": res["confusion_matrix"][1, 0], "tp": res["confusion_matrix"][1, 1],
    }])
    perf.to_csv(TABLES / "table9_classifier_performance.csv", index=False)
    print("Table 9. 5-fold cross-validated logistic classifier "
          "(NLP features -> market-composite label)\n")
    print(perf.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\nConfusion matrix (rows=actual, cols=predicted):\n{res['confusion_matrix']}")

    coefs = res["coefficients"].rename("standardised_coefficient").reset_index()
    coefs.columns = ["feature", "standardised_coefficient"]
    coefs.to_csv(TABLES / "table10_classifier_coefficients.csv", index=False)
    print("\nTable 10. Logistic regression coefficients (standardised features)\n")
    print(coefs.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    # classifier-based H-set: top N_HIGH_DAYS by cross-validated predicted probability
    proba_series = pd.Series(res["proba_cv"], index=res["index"])
    clf_high = list(proba_series.nlargest(N_HIGH_DAYS).index.sort_values())
    clf_low = pick_low_days(clf_high, ch.index, score=proba_series.reindex(ch.index))

    # ---- unsupervised GMM (NLP features only, no market data at all)
    gmm_res = clf.fit_gmm(X)
    p_high = gmm_res["p_high"]
    gmm_high = list(p_high.nlargest(N_HIGH_DAYS).index.sort_values())
    gmm_low = pick_low_days(gmm_high, ch.index, score=p_high.reindex(ch.index))

    overlap_clf = len(set(clf_high) & set(daily.index[daily["war_news_flag"].eq(1)]))
    overlap_gmm = len(set(gmm_high) & set(daily.index[daily["war_news_flag"].eq(1)]))
    print(f"\nClassifier-predicted H-set overlap with heuristic H-set: "
          f"{overlap_clf}/{N_HIGH_DAYS}")
    print(f"GMM (unsupervised, NLP-only) H-set overlap with heuristic H-set: "
          f"{overlap_gmm}/{N_HIGH_DAYS}")

    # ---- re-estimate under all four day-classification schemes
    heur_high = daily.index[daily["war_news_flag"].eq(1)]
    heur_low = daily.index[daily["set"].eq("L")]
    market_high = label[label.eq(1)].index
    market_low = pick_low_days(list(market_high), ch.index,
                               score=composite.reindex(ch.index))

    schemes = {
        "Heuristic z-score (headline results)": (heur_high, heur_low),
        "Supervised classifier (CV-predicted)": (pd.DatetimeIndex(clf_high), pd.DatetimeIndex(clf_low)),
        "Unsupervised GMM (NLP-only)": (pd.DatetimeIndex(gmm_high), pd.DatetimeIndex(gmm_low)),
        "Market-composite (oracle, for reference only)": (market_high, pd.DatetimeIndex(market_low)),
    }
    comp = None
    for name, (h, l) in schemes.items():
        est = estimate_for_highset(ch, h, l)
        est = est.rename(columns={"coef": f"coef__{name}", "t": f"t__{name}"})
        comp = est if comp is None else comp.merge(
            est[["column", f"coef__{name}", f"t__{name}"]], on="column")
    comp.to_csv(TABLES / "table11_method_comparison.csv", index=False)

    print("\nTable 11. d_j1 (coefficient, ω3) under four ways of drawing the H/L line")
    key_vars = ["y2", "y10", "spx", "stoxx", "hy", "vix", "dollar", "brent"]
    show = comp[comp["column"].isin(key_vars)]
    cols = ["variable"] + [c for c in show.columns if c.startswith("coef__")]
    print(show[cols].to_string(index=False, float_format=lambda v: f"{v:8.3f}"))

    figure4(res, proba_series, daily, label)
    print(f"\nFigures written to {FIGURES}")


def figure4(res, proba_series, daily, label):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    # ROC curve
    ax = axes[0, 0]
    ax.plot(res["roc_fpr"], res["roc_tpr"], color=BLUE, lw=2,
           label=f"AUC = {res['roc_auc']:.2f}")
    ax.plot([0, 1], [0, 1], color=GREY, lw=1, ls="--")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC curve (5-fold cross-validated)", loc="left")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.5)

    # Confusion matrix
    ax = axes[0, 1]
    cm = res["confusion_matrix"]
    im = ax.imshow(cm, cmap="Blues", vmin=0)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                   fontsize=14, color=INK if cm[i, j] < cm.max() / 1.5 else "white")
    ax.set_xticks([0, 1], ["Predicted 0", "Predicted 1"])
    ax.set_yticks([0, 1], ["Actual 0", "Actual 1"])
    ax.set_title("Confusion matrix (out-of-fold)", loc="left")

    # Predicted probability time series with true label
    ax = axes[1, 0]
    idx = proba_series.index
    ax.plot(idx, proba_series.values, color=BLUE, lw=1.2)
    true_pos = label.reindex(idx)
    ax.scatter(idx[true_pos.eq(1).values], proba_series.values[true_pos.eq(1).values],
              color=RED, s=24, zorder=3, label="Actual high-stress day")
    ax.axhline(0.5, color=GREY, lw=1, ls="--")
    ax.set_ylabel("CV-predicted P(high-stress)")
    ax.set_title("Classifier probability over time", loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.5)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    # Coefficients
    ax = axes[1, 1]
    c = res["coefficients"].sort_values()
    colors = [RED if v > 0 else BLUE for v in c.values]
    ax.barh(range(len(c)), c.values, color=colors)
    ax.set_yticks(range(len(c)), c.index)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_title("Standardised logistic coefficients", loc="left")
    ax.set_xlabel("log-odds per 1 SD")
    ax.grid(axis="x", alpha=0.5)

    fig.suptitle("Figure 4. Can NLP features predict which days will be "
                 "high-market-stress days?", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure4_classifier_diagnostics.png", dpi=170,
               bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
