"""Three independent ways to produce the same binary flag - war-news day (1) versus
not (0) - compared against each other and against the heuristic z-score threshold
used for the main results.

Why build three. The professor's guidance is to flag days 1/0 from NLP and let the
heteroskedasticity estimator do the identifying. The main pipeline does that with a
hand-tuned threshold (the top N_HIGH_DAYS by a z-score average - see event_days.py).
A threshold is simple and transparent, but it is also a researcher's choice, and a
natural question is whether the results are an artefact of that choice. Two more
principled ways to draw the same line:

  1. SUPERVISED - logistic regression, trained to predict an independent,
     market-based definition of a "high-stress" day from the NLP features alone.
     This tests something a threshold cannot: is the news content *predictive* of
     what the market will actually do, evaluated out-of-sample?

  2. UNSUPERVISED - a two-component Gaussian mixture fitted only on the NLP
     features (no market data touches this model at all, not even for validation).
     This asks whether the data has a genuine two-regime structure on its own, or
     whether the threshold is imposing one that isn't really there.

A crucial design choice for (1): the label used to train and evaluate the classifier
is built from market prices, but it is *never* used to select the day-sets fed back
into the heteroskedasticity estimator for the headline results - only the classifier's
own cross-validated, text-only predictions are. Using the market-volatility label
itself as an "H-set" would be circular for this purpose: selecting days by realised
volatility in the same variables you then use those days to estimate sensitivity for
guarantees an inflated variance ratio by construction, telling you nothing about
whether news content carries information. This is exactly why Rigobon and Sack select
days from news coverage rather than from ex-post market moves, and it is a real
methodological advantage of the news-based approach that this comparison makes
concrete rather than assumed - see REPORT.md section 5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
                             recall_score, f1_score, roc_auc_score, roc_curve)
from sklearn.preprocessing import StandardScaler

FEATURES = ["attention", "tone_shift", "disagreement", "war_share", "hormuz_share"]

MARKET_BASKET = ["brent", "vix", "hy", "spx", "y2"]


def market_composite_label(ch: pd.DataFrame, n_positive: int) -> pd.Series:
    """An independent, market-only definition of a 'high-stress' day: the average
    absolute z-score of daily changes across a small war-sensitive basket, top
    n_positive days flagged 1. Never used to pick the H-set for headline estimates -
    see module docstring."""
    z = pd.DataFrame({c: (ch[c] - ch[c].mean()).abs() / ch[c].std(ddof=0)
                      for c in MARKET_BASKET})
    composite = z.mean(axis=1)
    top = composite.nlargest(n_positive).index
    label = pd.Series(0, index=ch.index)
    label.loc[top] = 1
    return label, composite


def build_feature_matrix(daily: pd.DataFrame) -> pd.DataFrame:
    X = daily[FEATURES].copy()
    return X


def fit_logistic_cv(X: pd.DataFrame, y: pd.Series, n_splits: int = 5,
                    seed: int = 7) -> dict:
    """Stratified k-fold cross-validated logistic regression.

    Why logistic regression and not a more flexible model (random forest, gradient
    boosting, a neural net): the sample is small (173 days) and the positive class
    is rare (~18 days, ~10%). A model with many parameters relative to that many
    positives will fit noise, and its cross-validated performance is unlikely to
    beat a well-regularised linear model on features this few (five). Logistic
    regression also returns coefficients that answer a question this course cares
    about directly - which NLP signal actually carries predictive information - and
    it is the standard baseline for binary classification with tabular features at
    this scale, so any more complex model needs to earn its complexity against it.
    class_weight='balanced' corrects for the ~9-to-1 class imbalance rather than
    letting the model default to always predicting 0.
    """
    ok = X.notna().all(axis=1) & y.notna()
    Xo, yo = X[ok], y[ok]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(Xo)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    model = LogisticRegression(class_weight="balanced", max_iter=1000, C=1.0)

    proba = cross_val_predict(model, Xs, yo, cv=skf, method="predict_proba")[:, 1]
    pred = (proba >= 0.5).astype(int)

    cm = confusion_matrix(yo, pred)
    fpr, tpr, _ = roc_curve(yo, proba)

    model.fit(Xs, yo)  # in-sample fit, for interpreting coefficients only
    coefs = pd.Series(model.coef_[0], index=Xo.columns).sort_values(
        key=np.abs, ascending=False)

    return {
        "index": Xo.index, "y_true": yo.values, "proba_cv": proba, "pred_cv": pred,
        "confusion_matrix": cm,
        "accuracy": accuracy_score(yo, pred),
        "precision": precision_score(yo, pred, zero_division=0),
        "recall": recall_score(yo, pred, zero_division=0),
        "f1": f1_score(yo, pred, zero_division=0),
        "roc_auc": roc_auc_score(yo, proba),
        "roc_fpr": fpr, "roc_tpr": tpr,
        "coefficients": coefs,
        "n_positive": int(yo.sum()), "n_total": int(len(yo)),
    }


def fit_gmm(X: pd.DataFrame) -> dict:
    """Unsupervised 2-component Gaussian mixture on the NLP features alone - no
    market data anywhere in this function."""
    ok = X.notna().all(axis=1)
    Xo = X[ok]
    scaler = StandardScaler()
    Xs = scaler.fit_transform(Xo)

    gmm = GaussianMixture(n_components=2, random_state=7, n_init=10)
    gmm.fit(Xs)
    post = gmm.predict_proba(Xs)
    # The "high" component is whichever has the larger mean attention feature
    attn_idx = list(X.columns).index("attention")
    high_component = int(np.argmax(gmm.means_[:, attn_idx]))
    p_high = post[:, high_component]

    return {"index": Xo.index, "p_high": pd.Series(p_high, index=Xo.index),
           "means": gmm.means_, "high_component": high_component,
           "weights": gmm.weights_}
