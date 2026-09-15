"""OLS regressions for Table 3: each indicator's one-day change on each tone
score, controlling for the change in the 3-month bill yield, HC1 robust SEs.
"""
import pandas as pd
import statsmodels.formula.api as smf

INDICATORS = {
    "d_dxy": "DXY",
    "d_10s2s": "10s2s spread",
    "d_1y": "1-year yield",
    "d_growth_minus_value": "Growth minus value",
}
TONE_SCORES = {
    "wordlist_score": "Word list",
    "finbert_score": "FinBERT",
}


def run_all(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ind_col, ind_label in INDICATORS.items():
        for tone_col, tone_label in TONE_SCORES.items():
            sub = df[[ind_col, tone_col, "d_3mo_bill"]].dropna()
            if len(sub) < 10:
                continue
            model = smf.ols(f"{ind_col} ~ {tone_col} + d_3mo_bill", data=sub).fit(cov_type="HC1")
            rows.append(dict(
                indicator=ind_label, tone_method=tone_label, n=int(model.nobs),
                tone_coef=model.params[tone_col], tone_se=model.bse[tone_col],
                tone_t=model.tvalues[tone_col], tone_p=model.pvalues[tone_col],
                bill_coef=model.params["d_3mo_bill"], bill_p=model.pvalues["d_3mo_bill"],
                r2=model.rsquared,
            ))
    return pd.DataFrame(rows)


def stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""
