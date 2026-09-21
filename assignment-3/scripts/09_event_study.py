"""The plain alternative to the heteroskedasticity estimator: regress each
variable's daily change on the same binary war-news flag used everywhere else,
and compare.

    dx_t = alpha + beta * war_news_flag_t + u_t          (OLS, HC1 robust SE)

This is the standard finance "event study" approach - does the variable move
differently, on average, on flagged days versus not - and it is worth running
because it is simpler and more familiar than Rigobon-Sack, so any difference between
the two is worth understanding rather than assuming away.

The key conceptual difference, spelled out because it is the crux of "is
heteroskedasticity the best approach": this regression estimates a MEAN shift -
whether the average return differs on war-news days. The heteroskedasticity
estimator estimates a VARIANCE-implied structural loading - how sensitive the
variable is to the war-risk factor - and it needs no assumption that war days have
a different average return, only that they have a different variance. A level
shock unrelated to the war that happened to land on a few war-news days (e.g. an
unrelated earnings surprise) biases this regression's beta directly, through the
mean; it only biases the heteroskedasticity estimator if that unrelated shock was
*also* unusually volatile on exactly those days, which is a narrower and more
checkable condition (that is what Table 4's rank condition and diagnostics test).
So the two methods answering different questions is expected, not a bug - the
comparison in the report's Table 12 and Figure 5 is what makes that difference
concrete rather than asserted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from config import MARKET, INTERIM, TABLES, VARIABLES, NORMALISATION


def main():
    ch = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
    daily = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
    ch = ch[ch.index <= daily.index.max()]
    flag = daily.reindex(ch.index)["war_news_flag"]

    df = ch.copy()
    df["war_news_flag"] = flag

    rows = []
    for col, label, unit, group in VARIABLES:
        sub = df[[col, "war_news_flag"]].dropna()
        model = smf.ols(f"{col} ~ war_news_flag", data=sub).fit(cov_type="HC1")
        rows.append({
            "variable": label, "column": col, "units": unit,
            "beta": model.params["war_news_flag"],
            "se": model.bse["war_news_flag"],
            "t": model.tvalues["war_news_flag"],
            "p": model.pvalues["war_news_flag"],
            "n": int(model.nobs), "r2": model.rsquared,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "table12_event_study.csv", index=False)

    print("Table 12. Event-study OLS: dx = alpha + beta * war_news_flag (HC1 SEs)\n")
    print(out[["variable", "units", "beta", "t", "p"]]
          .to_string(index=False, float_format=lambda v: f"{v:9.4f}"))

    n_sig = int((out["p"] < 0.05).sum())
    print(f"\n{n_sig}/{len(out)} variables significant at 5% under the event-study "
          f"dummy regression alone (no variance-shift correction)")


if __name__ == "__main__":
    main()
