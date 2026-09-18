"""Monte Carlo check that the estimator in src/heteroskedasticity.py recovers a
known parameter, and that OLS on the same data does not.

Data are generated exactly from the paper's equation (2): a war-risk factor z1 whose
variance is higher on H days than on L days, a second common factor z2 whose variance
is the same on both, and idiosyncratic shocks. The true response of x2 to the war
factor is d21 = TRUE_D.

This is run before the real estimation so that any number in the report can be traced
back to an estimator that has been shown to work on data where the answer is known.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import heteroskedasticity as het

TRUE_D = -3.75          # e.g. equities fall 3.75% per unit of the war factor
N_H, N_L = 18, 18       # the paper pairs each war-news day with one nearby other day
N_SIMS = 400


def simulate(rng, true_d=TRUE_D, sigma_H=3.0, sigma_L=1.0, n_h=None, n_l=None):
    n_h = N_H if n_h is None else n_h
    n_l = N_L if n_l is None else n_l
    n = n_h + n_l
    high = np.zeros(n, bool)
    high[:n_h] = True

    # war-risk factor: same mean (zero), different variance across regimes
    z1 = rng.normal(0, np.where(high, sigma_H, sigma_L))
    # a second common factor, homoskedastic across regimes, plus idiosyncratic noise
    z2 = rng.normal(0, 1.5, n)
    mu1 = rng.normal(0, 1.0, n)
    mu2 = rng.normal(0, 2.0, n)

    dx1 = z1 + 0.8 * z2 + mu1
    dx2 = true_d * z1 + 1.4 * z2 + mu2
    return dx1, dx2, high


def main():
    rng = np.random.default_rng(20260917)
    est = {k: [] for k in ["w1", "w2", "w3", "ols"]}
    covered = {k: 0 for k in ["w1", "w2", "w3"]}

    for _ in range(N_SIMS):
        dx1, dx2, high = simulate(rng)
        res = het.estimate_all(dx1, dx2, high)
        for k in ["w1", "w2", "w3"]:
            est[k].append(res[k]["coef"])
            lo = res[k]["coef"] - 1.96 * res[k]["se"]
            hi = res[k]["coef"] + 1.96 * res[k]["se"]
            covered[k] += int(lo <= TRUE_D <= hi)
        est["ols"].append(float(np.polyfit(dx1, dx2, 1)[0]))

    print(f"True d21 = {TRUE_D}   ({N_SIMS} simulations, "
          f"{N_H} high-variance and {N_L} low-variance days)\n")
    print("IV estimators have heavy-tailed small-sample distributions, so the median")
    print("is the meaningful centre; the mean is pulled around by a few draws where")
    print("the first stage is near-degenerate.\n")
    print(f"{'estimator':<12}{'median':>9}{'bias':>9}{'mean':>9}{'IQR':>8}{'95% CI cover':>14}")
    for k in ["w1", "w2", "w3"]:
        a = np.array(est[k])
        med = float(np.median(a))
        iqr = float(np.quantile(a, .75) - np.quantile(a, .25))
        print(f"{'IV w/ ' + k:<12}{med:>9.3f}{med - TRUE_D:>9.3f}{a.mean():>9.3f}"
              f"{iqr:>8.3f}{100 * covered[k] / N_SIMS:>13.1f}%")
    a = np.array(est["ols"])
    med = float(np.median(a))
    print(f"{'OLS':<12}{med:>9.3f}{med - TRUE_D:>9.3f}{a.mean():>9.3f}"
          f"{float(np.quantile(a, .75) - np.quantile(a, .25)):>8.3f}{'  (biased)':>14}")

    # The rank condition should reject zero on data built to satisfy it, and should
    # fail when both variances are scaled by the same factor (Rigobon 2003, prop. 1).
    dx1, dx2, high = simulate(rng)
    good = het.rank_condition_bootstrap(dx1, dx2, high, n_boot=800)
    print(f"\nRank condition, identified data:   stat={good['stat']:.4f} "
          f"p={good['p_value']:.4f}")

    n = N_H + N_L
    high2 = np.zeros(n, bool); high2[:N_H] = True
    base1 = rng.normal(0, 1, n); base2 = rng.normal(0, 1, n)
    scale = np.where(high2, 3.0, 1.0)      # both variances scaled identically
    flat = het.rank_condition_bootstrap(base1 * scale, base2 * scale, high2, n_boot=800)
    print(f"Rank condition, proportional data: stat={flat['stat']:.4f} "
          f"p={flat['p_value']:.4f}  (should NOT reject)")

    # Unequal H/L sets. The paper's raw instrument silently breaks here, because
    # w'dx1 becomes n_H*E_H[dx1^2] - n_L*E_L[dx1^2] rather than the difference in
    # variances; the 1/n weighting in build_instruments(balanced=True) fixes it.
    # This case is what the real data would look like without matched L days.
    bal, raw = [], []
    for _ in range(N_SIMS):
        dx1, dx2, high = simulate(rng, n_h=18, n_l=159)
        bal.append(het.estimate_all(dx1, dx2, high, balanced=True)["w1"]["coef"])
        raw.append(het.estimate_all(dx1, dx2, high, balanced=False)["w1"]["coef"])
    print(f"\nUnequal sets (18 high / 159 low), IV w/ w1:")
    print(f"  balanced instrument    median {np.median(bal):8.3f}  bias {np.median(bal) - TRUE_D:7.3f}")
    print(f"  paper's raw instrument median {np.median(raw):8.3f}  bias {np.median(raw) - TRUE_D:7.3f}")

    tol = 0.15 * abs(TRUE_D)
    for k in ["w1", "w2", "w3"]:
        bias = abs(float(np.median(est[k])) - TRUE_D)
        assert bias < tol, f"{k} median bias {bias:.3f} exceeds tolerance {tol:.3f}"
    assert abs(float(np.median(est["ols"])) - TRUE_D) > tol, "OLS should be visibly biased here"
    assert abs(float(np.median(bal)) - TRUE_D) < tol, "balanced instrument should survive unequal sets"
    assert abs(float(np.median(raw)) - TRUE_D) > tol, "raw instrument should fail on unequal sets"
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
