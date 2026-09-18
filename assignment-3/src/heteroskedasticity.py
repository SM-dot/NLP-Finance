"""The heteroskedasticity-based estimator of Rigobon and Sack (2003), with the
identification conditions of Rigobon (2003).

Setup. Two financial variables, x1 (the normalising variable, here the two-year
Treasury yield) and x2. Their daily changes are driven by a common war-risk factor
z1 plus other factors and idiosyncratic shocks:

    [dx1, dx2]' = D z + mu,   D = [[1, d12, ...], [d21, d22, ...]]

d21 - the response of x2 to the war-risk factor, relative to x1 - is the parameter of
interest. z1 is never observed. Identification comes from a set of days H on which
the *variance* of war-related news was high, compared with a set L on which it was
low; all other factors are assumed to keep the same variance across the two sets and
to be orthogonal to z1. Then (Rigobon-Sack eq. 5)

    dOmega = Omega_H - Omega_L = dsigma^2(z1) * [[1, d21], [d21, d21^2]]

and d21 can be read off the change in the covariance matrix three ways, implemented
here as instrumental-variables regressions of dx2 on dx1 with the instruments

    w1 = {dx1 on H} U {-dx1 on L}            -> eq. (7):  dOmega_21 / dOmega_11
    w2 = {dx2 on H} U {-dx2 on L}            -> eq. (6):  dOmega_22 / dOmega_21
    w3 = [w1, w2] together (2SLS, over-identified)

Note on the paper's own table: the text derives IV-with-w1 as equation (7) and
IV-with-w2 as equation (6), while the Table 2 column headers pair them the other way
round. Columns here are labelled by instrument, which is unambiguous.

Following footnote 12 of the paper, second moments are raw (E[dx^2]) rather than
demeaned, and the IV regressions run without a constant, matching their equation (9).
"""
from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------- moments


def regime_moments(dx1: np.ndarray, dx2: np.ndarray,
                   high: np.ndarray) -> dict[str, float]:
    """Raw second moments of (dx1, dx2) on the high- and low-variance day sets."""
    h, l = high.astype(bool), ~high.astype(bool)
    return {
        "var1_H": float(np.mean(dx1[h] ** 2)), "var1_L": float(np.mean(dx1[l] ** 2)),
        "var2_H": float(np.mean(dx2[h] ** 2)), "var2_L": float(np.mean(dx2[l] ** 2)),
        "cov_H": float(np.mean(dx1[h] * dx2[h])), "cov_L": float(np.mean(dx1[l] * dx2[l])),
        "n_H": int(h.sum()), "n_L": int(l.sum()),
    }


def delta_omega(m: dict[str, float]) -> np.ndarray:
    """dOmega = Omega_H - Omega_L."""
    return np.array([[m["var1_H"] - m["var1_L"], m["cov_H"] - m["cov_L"]],
                     [m["cov_H"] - m["cov_L"], m["var2_H"] - m["var2_L"]]])


# ----------------------------------------------------------------- instruments


def build_instruments(dx1: np.ndarray, dx2: np.ndarray, high: np.ndarray,
                      balanced: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """w1 and w2 of equations (8) and (11): the variable itself on high-variance
    days, its negative on low-variance days.

    The paper defines these over an *equal-sized* set of other days, because with
    n_H = n_L the raw cross-product w1'dx1 is proportional to Var_H - Var_L, which
    is what equation (10) requires. With unequal sets the raw cross-product is
    n_H*E_H[dx1^2] - n_L*E_L[dx1^2], which is not the difference in variances at
    all - and the estimator is badly biased, not merely less efficient.

    `balanced=True` weights each regime by 1/n so the moment condition is the
    difference in *mean* second moments for any split. It is identical to the
    paper's instrument (up to a harmless common scale) when n_H = n_L, and correct
    when they differ. The H/L sets built in script 04 are equal-sized anyway, per
    the paper; this keeps the estimator right either way.
    """
    h = high.astype(bool)
    if balanced:
        n_h, n_l = max(h.sum(), 1), max((~h).sum(), 1)
        w = np.where(h, 1.0 / n_h, -1.0 / n_l)
    else:
        w = np.where(h, 1.0, -1.0)
    return dx1 * w, dx2 * w


# --------------------------------------------------------------------- the IV


def iv_estimate(y: np.ndarray, x: np.ndarray, z: np.ndarray) -> dict[str, float]:
    """IV/2SLS of y on x (no constant) using instrument matrix z, with
    heteroskedasticity-robust (HC1) standard errors.

    Just-identified (one instrument) reduces to d = (z'x)^-1 (z'y), which is exactly
    Rigobon-Sack equation (9).
    """
    y = np.asarray(y, float).ravel()
    x = np.asarray(x, float).ravel()
    z = np.asarray(z, float).reshape(len(y), -1)
    n = len(y)

    zz_inv = np.linalg.pinv(z.T @ z)
    xhat = z @ (zz_inv @ (z.T @ x))            # first-stage fitted values
    xhx = float(xhat @ x)
    if abs(xhx) < 1e-14:
        return {"coef": np.nan, "se": np.nan, "t": np.nan, "n": n,
                "first_stage_F": np.nan}

    coef = float(xhat @ y) / xhx
    u = y - x * coef

    # Robust sandwich: (xhat'x)^-1 * sum(xhat_i^2 u_i^2) * (x'xhat)^-1, HC1-scaled
    meat = float(np.sum((xhat ** 2) * (u ** 2)))
    var = meat / (xhx ** 2)
    var *= n / max(n - 1, 1)
    se = float(np.sqrt(var)) if var > 0 else np.nan

    # First-stage F on the excluded instruments (instrument strength)
    resid_fs = x - xhat
    ssr = float(resid_fs @ resid_fs)
    sst = float(x @ x)
    k = z.shape[1]
    f_stat = ((sst - ssr) / k) / (ssr / max(n - k, 1)) if ssr > 0 else np.inf

    return {"coef": coef, "se": se,
            "t": coef / se if se and np.isfinite(se) and se > 0 else np.nan,
            "n": n, "first_stage_F": float(f_stat)}


def estimate_all(dx1: np.ndarray, dx2: np.ndarray, high: np.ndarray,
                 balanced: bool = True) -> dict[str, dict[str, float]]:
    """All three instrument sets, plus the closed-form moment estimators."""
    ok = np.isfinite(dx1) & np.isfinite(dx2)
    dx1, dx2, high = dx1[ok], dx2[ok], high[ok]

    w1, w2 = build_instruments(dx1, dx2, high, balanced=balanced)
    res = {
        "w1": iv_estimate(dx2, dx1, w1),
        "w2": iv_estimate(dx2, dx1, w2),
        "w3": iv_estimate(dx2, dx1, np.column_stack([w1, w2])),
    }

    m = regime_moments(dx1, dx2, high)
    dO = delta_omega(m)
    res["moments"] = {
        "eq7_dO21_over_dO11": dO[0, 1] / dO[0, 0] if dO[0, 0] != 0 else np.nan,
        "eq6_dO22_over_dO21": dO[1, 1] / dO[0, 1] if dO[0, 1] != 0 else np.nan,
        **m,
    }
    return res


# --------------------------------------------------- identification diagnostics


def rank_condition(dx1: np.ndarray, dx2: np.ndarray,
                   high: np.ndarray) -> float:
    """Rigobon (2003) equation (7): w11,1*w12,2 - w11,2*w12,1, which must be
    non-zero for the two regimes to identify the system. It is zero exactly when
    the two covariance matrices are proportional - i.e. when the high-variance days
    are just a scaled-up version of the low-variance days and nothing is learned.
    """
    ok = np.isfinite(dx1) & np.isfinite(dx2)
    m = regime_moments(dx1[ok], dx2[ok], high[ok])
    return m["var1_L"] * m["cov_H"] - m["var1_H"] * m["cov_L"]


def rank_condition_bootstrap(dx1: np.ndarray, dx2: np.ndarray, high: np.ndarray,
                             n_boot: int = 2000, seed: int = 7) -> dict[str, float]:
    """Bootstrap p-value for the rank condition being zero, resampling days within
    each regime (so the H/L split is held fixed)."""
    ok = np.isfinite(dx1) & np.isfinite(dx2)
    dx1, dx2, high = dx1[ok], dx2[ok], high[ok].astype(bool)
    stat = rank_condition(dx1, dx2, high)

    rng = np.random.default_rng(seed)
    idx_h = np.flatnonzero(high)
    idx_l = np.flatnonzero(~high)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        ih = rng.choice(idx_h, size=len(idx_h), replace=True)
        il = rng.choice(idx_l, size=len(idx_l), replace=True)
        take = np.concatenate([ih, il])
        mask = np.concatenate([np.ones(len(ih), bool), np.zeros(len(il), bool)])
        draws[b] = rank_condition(dx1[take], dx2[take], mask)

    # Two-sided bootstrap p-value for H0: statistic = 0
    centred = draws - draws.mean()
    p = float(np.mean(np.abs(centred) >= abs(stat)))
    return {"stat": float(stat), "p_value": p,
            "ci_low": float(np.quantile(draws, 0.025)),
            "ci_high": float(np.quantile(draws, 0.975))}


# ------------------------------------------------------- variance decomposition


def variance_decomposition(dxj: np.ndarray, dx1: np.ndarray, high: np.ndarray,
                           d_j1: float) -> dict[str, float]:
    """Table 3 of Rigobon-Sack.

    The war-risk factor raises the variance of dxj on high-news days by
    d_j1^2 * dVar(dx1). Comparing that with the variance actually observed gives a
    lower bound on the share of variance attributable to war news - a lower bound
    because the low-variance days still contain some war news.
    """
    ok = np.isfinite(dxj) & np.isfinite(dx1)
    dxj, dx1, high = dxj[ok], dx1[ok], high[ok].astype(bool)

    var_j_H = float(np.mean(dxj[high] ** 2))
    var_j_L = float(np.mean(dxj[~high] ** 2))
    d_var1 = float(np.mean(dx1[high] ** 2) - np.mean(dx1[~high] ** 2))
    predicted = (d_j1 ** 2) * d_var1

    n_H, n_L = int(high.sum()), int((~high).sum())
    # Variance of the cumulative change over the window, under serial independence
    var_cumulative = n_H * var_j_H + n_L * var_j_L
    war_cumulative = n_H * predicted

    return {
        "var_L": var_j_L, "var_H": var_j_H, "predicted_change": predicted,
        "pct_of_H_days": 100 * predicted / var_j_H if var_j_H > 0 else np.nan,
        "pct_of_all_days": 100 * war_cumulative / var_cumulative if var_cumulative > 0 else np.nan,
        "n_H": n_H, "n_L": n_L,
    }
