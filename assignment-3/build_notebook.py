"""Builds analysis.ipynb from the cell definitions below. Run once, then execute
with nbconvert to produce the saved-output notebook for submission."""
import json
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


md("""# Assignment 3: Measuring the Effect of Iran War Risk on Global Financial Markets

FRE-GY 7871 A · NLP and the Investment Process · Fall 2026

**Question.** The US and Israel struck Iran on 28 February 2026, and the war has run
since. How sensitive are global financial variables to Iranian war risk — and by how
much?

**The problem.** War risk is not observable. We know *when* war news broke; we cannot
say by how much any given day's news moved the probability or severity of war. Regressing
asset prices on a war-risk variable is therefore impossible, and an event study on the
signed news runs straight into the fact that on many days even the sign is unclear.

**The method.** Rigobon and Sack (2003) identify the effect from a shift in *variance*
instead of from the level of the factor. Name a set of days on which war news was
unusually intense; assume no other driver of asset prices was unusually volatile on
those days; then the change in the covariance matrix of returns between those days and
ordinary days is attributable to the war factor alone, and each asset's sensitivity can
be recovered without ever measuring war risk itself.

**Where the NLP comes in.** Naming the days is the whole ballgame, and it is the one step
Rigobon and Sack did by hand — they read newspapers and wrote down seventeen dates. Here
that step is done from the text: a daily war-risk news index built from GDELT coverage,
combining how much war coverage there was, how far the escalation/de-escalation balance
moved, and how contested that balance was.

This notebook reads the output of the pipeline in `scripts/`; run `scripts/00`–`06`
first (see `README.md`).""")

code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))

import numpy as np
import pandas as pd

from config import (TABLES, FIGURES, INTERIM, MARKET, WAR_START,
                    NORMALISATION_LABEL, N_HIGH_DAYS)
import heteroskedasticity as het

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

news = pd.read_csv(INTERIM / "news_daily.csv", index_col="date", parse_dates=True)
ev = pd.read_csv(INTERIM / "event_days.csv", index_col=0, parse_dates=True)
ch = pd.read_csv(MARKET / "changes.csv", index_col="date", parse_dates=True)
ch = ch[ch.index <= ev.index.max()]

t1 = pd.read_csv(TABLES / "table1_war_news_days.csv")
t2 = pd.read_csv(TABLES / "table2_war_risk_impact.csv")
t2b = pd.read_csv(TABLES / "table2b_normalised_on_2y.csv")
t3 = pd.read_csv(TABLES / "table3_variance_decomposition.csv")
t4 = pd.read_csv(TABLES / "table4_rank_condition.csv")
t5 = pd.read_csv(TABLES / "table5_robustness_window.csv")
t6 = pd.read_csv(TABLES / "table6_foreign_next_day.csv")

print(f"Sample: {ch.index.min().date()} to {ch.index.max().date()}, "
      f"{len(ch)} US trading days")
print(f"War began {WAR_START} - {int((ch.index.date < WAR_START).sum())} pre-war "
      f"trading days in the window")
print(f"News coverage: {len(news)} calendar days")
print(f"Day sets: {int(ev['set'].eq('H').sum())} war-news (H), "
      f"{int(ev['set'].eq('L').sum())} comparison (L)")""")

md("""## 1. The war-risk news index

Three measures, each computed from GDELT's coverage timelines and then standardised:

| component | what it is | why |
|---|---|---|
| **attention** | log war-risk coverage volume minus its own trailing 10-day median | the *level* of coverage is useless once a war is running — Iran was front-page news every day from March. A news day is one where coverage jumps above its recent baseline. |
| **tone shift** | absolute change in (escalation − de-escalation) ÷ (escalation + de-escalation) coverage | the analogue of Rigobon and Sack's hand-assigned "Increased/Decreased" column. Only the *shift* counts: a day that makes war dramatically less likely is as informative as one that makes it more likely. |
| **contest** | (1 − \\|direction\\|) × log(1 + coverage) | a day carrying heavy escalation *and* heavy de-escalation coverage at once is a high-variance news day even though the two cancel in the mean. This is the case the paper tags "Unclear". |

The first check is whether these track reality at all.""")

code("""top = news["war_volume"].nlargest(8)
print("Heaviest war-risk coverage days\\n")
for d, v in top.items():
    print(f"  {d.date()}  coverage {v:6.3f}%  direction {news.loc[d, 'direction']:+.2f}")

print("\\nMost conciliatory days by direction:")
for d in news["direction"].nsmallest(5).index:
    print(f"  {d.date()}  direction {news.loc[d, 'direction']:+.2f}")

print(f"\\nCorrelation of our direction measure with GDELT's own tone series: "
      f"{news['direction'].corr(news['war_tone']):+.3f}")""")

md("""Coverage peaks on **28 February**, the day the war began, and the Hormuz-specific
series peaks on **8 April**, the day of the two-week ceasefire and safe passage through
the strait. The most conciliatory readings land on **16–17 June** and **23–24 June** —
the Islamabad Memorandum and the technical talks that followed. None of those dates was
supplied to the code; they fall out of the coverage measures. The direction measure
correlates −0.63 with GDELT's independently computed tone series, with the expected sign
(escalation coverage reads as more negative news).

![Figure 1](figures/figure1_war_news_index.png)""")

md("""## 2. Table 1 — the days the index selects

The equivalent of Rigobon and Sack's Table 1, except that the dates come from the
coverage measures rather than from reading newspapers. The event text is from
Wikipedia's Current Events Portal and plays no part in the selection; it is here so the
table can say what happened.""")

code("""cols = ["date", "war_risk", "news_score", "attention_z", "tone_shift_z",
        "contest_z", "d_brent_usd", "d_2y_bp"]
print(t1[cols].to_string(index=False))
print("\\nDirection of war risk on the selected days:")
print(t1["war_risk"].value_counts().to_string())""")

code("""for _, r in t1.iterrows():
    ev_txt = (r["event"][:96] + "...") if isinstance(r["event"], str) and len(r["event"]) > 96 else r["event"]
    print(f"{r['date']}  [{r['war_risk']:>9}]  {ev_txt}")""")

md("""Eight days where the coverage balance tipped towards escalation, four towards
de-escalation, six genuinely mixed. That distribution matters: a conventional event study
would have to throw the six "Unclear" days away, or guess their sign. The
heteroskedasticity-based estimator uses them, because it only needs the news to have been
*voluminous and contested*, not signed.""")

md("""## 3. Does the identifying assumption hold?

The method needs the selected days to be genuinely more volatile. This is testable, and
it is where the 2026 episode departs sharply from 2003.""")

code("""h = ev["set"].eq("H").values
l = ev["set"].eq("L").values
rows = []
for c in ["brent", "vix", "stoxx", "hy", "dollar", "spx", "y2", "y10",
          "breakeven10", "gold"]:
    x = ch[c]
    vH, vL = np.nanmean(x[h] ** 2), np.nanmean(x[l] ** 2)
    rows.append({"variable": c, "var_H": vH, "var_L": vL, "ratio": vH / vL})
print(pd.DataFrame(rows).sort_values("ratio", ascending=False)
      .to_string(index=False, float_format=lambda v: f"{v:,.5f}"))""")

md("""**Brent's variance is 6.2 times higher on war-news days. The two-year Treasury
yield's is 1.05 times higher, and the ten-year's is *lower*.**

In 2003 it was the other way round: Rigobon and Sack's Table 3 shows the two-year yield's
variance rising from .00096 on quiet days to .00594 on war-news days — a factor of 6.2,
almost exactly what Brent does here. They normalised on the two-year yield because in
2003 it was the cleanest barometer of war risk.

It is not one in 2026, and the reason is economic rather than statistical. A war that
arrives as an oil-supply shock in an inflationary economy pushes yields down through
flight to quality and up through the inflation outlook; the two roughly cancel, leaving
the Treasury market with no more variance on war-news days than on any other. Normalising
on a variable that barely responds to the factor puts a number near zero in the
estimator's denominator — precisely the rank-condition failure Rigobon (2003) warns
about. **Brent takes the two-year yield's role**, and both normalisations are reported
below so the comparison is visible.

![Figure 2](figures/figure2_variance_ratio.png)""")

md("""## 4. Table 2 — the estimates

Each variable is paired with Brent and estimated two at a time, under all three
instrument sets. Coefficients are scaled to a war-risk increase large enough to raise
Brent by $5 a barrel.""")

code("""def stars(t):
    a = abs(t)
    return "***" if a >= 2.576 else "**" if a >= 1.96 else "*" if a >= 1.645 else ""

out = t2[["variable", "units", "w1_coef", "w2_coef", "w3_coef", "w3_t"]].copy()
out["sig"] = out["w3_t"].map(stars)
print(f"Response to {NORMALISATION_LABEL}\\n")
print(out.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
print("\\n*** p<1%, ** p<5%, * p<10% (on the combined instrument)")""")

md("""![Figure 3](figures/figure3_coefficients.png)

**What happens when Iranian war risk rises.** Global equities fall, and they fall *more
outside the United States* than inside it: the S&P drops 0.65%, but the Euro Stoxx 1.37%,
the Nikkei 1.65% and emerging markets 1.65%. Credit widens — 4.8bp on high yield, 0.8bp
on BBB. The VIX adds 1.7 points. Within equities the cross-section is exactly what an
oil-supply shock implies: energy producers *gain* 0.96%, airlines lose 1.36%.

**Three signs are the opposite of 2003**, and they all say the same thing:

| | Rigobon–Sack, 2003 | This paper, 2026 |
|---|---|---|
| Treasury yields | **fall** (−0.26pp on the 10-year) | **rise** (+0.019pp, t=2.3) |
| Break-even inflation | **falls** (−0.11pp) | **rises** (+0.014pp, t=3.4) |
| Dollar | **falls** (−0.44%) | **rises** (+0.26%, t=3.2) |

In 2003 war risk was priced as a threat to demand: disinflationary, bad for growth, bad
for the dollar. In 2026 it is priced as a threat to supply — inflationary, and with the
dollar as the asset investors run *to* rather than from. The Swiss franc appreciates
against the dollar too (+0.24%), so this is a general flight to safe currencies in which
the dollar participates rather than a dollar-specific story.

**Two non-results worth stating.** Gold does not respond significantly (t=−1.9, and
negative) — Rigobon and Sack also found no significant gold response, which is one of the
more durable findings across twenty-three years. And the Tel Aviv 125 shows no
significant response at all despite its variance rising 3.6× on war-news days: Israeli
equities moved a great deal on these days, but not in proportion to the common war factor
that oil prices. Their volatility was Israel-specific.""")

md("""### The paper's normalisation, for comparison

The same estimates anchored on the two-year yield, as Rigobon and Sack do. This is what
a weakly identified system looks like.""")

code("""cmp = t2b[["variable", "units", "w1_coef", "w2_coef", "w3_coef", "w3_t"]]
print(cmp.to_string(index=False, float_format=lambda v: f"{v:10.2f}"))""")

md("""Gold moves $1,968 per 25bp; the S&P rises 18.7% when war risk *increases*; the three
instrument sets disagree wildly and not one t-statistic clears 2.1. The coefficients are
not small and insignificant — they are enormous and insignificant, which is the signature
of dividing by a denominator near zero. Reporting this rather than quietly switching
normalisations is the point: the diagnostic *is* a result.""")

md("""## 5. Table 3 — how much of the variance war risk explains""")

code("""v = t3[["variable", "units", "var_L", "var_H", "predicted_change",
        "pct_var_H_days", "pct_var_all_days"]]
print(v.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))""")

md("""Read the last two columns as lower bounds, for the reason the paper gives: the
comparison days are not free of war news either, so the variance *shift* understates the
war-related variance level.

Even so, on war-news days the factor accounts for 53% of the variance of the Euro Stoxx,
49% of the VIX, 44% of the dollar, 42% of break-even inflation and 41% of the high-yield
spread. Across the whole eight-month window the shares are 17% for the Euro Stoxx and
12% for the VIX. Rigobon and Sack report 13–63% over their ten weeks; our window is three
times longer, so war-news days are a smaller fraction of it and the whole-sample shares
are correspondingly lower.""")

md("""## 6. Is the system identified? (Rigobon 2003)

Two readings of the same requirement. The rank statistic of Rigobon (2003) equation (7)
is zero exactly when the two covariance matrices are proportional — when the war-news
days are just a scaled-up version of ordinary days and nothing is learned. Its bootstrap
test has very little power at eighteen days a regime, since it is a function of products
of second moments. The first-stage F on the excluded instrument is the operational form
of the same condition, and it is what the standard errors already respond to.""")

code("""print(t4[["variable", "rank_stat", "p_value", "first_stage_F_w1",
          "first_stage_F_w2", "t_w3"]]
      .to_string(index=False, float_format=lambda v: f"{v:10.3f}"))""")

md("""The ω₁ instrument is strong everywhere — a first-stage F around 38, well clear of the
conventional threshold of 10. The ω₂ instrument varies enormously: 16.2 for the Euro
Stoxx, 11.5 for the VIX, but **0.002 for the Tel Aviv 125** and below 2 for gold, the
two-year yield and defence stocks.

That single number explains the strangest entry in Table 2. Tel Aviv's ω₂ estimate is
+128.55 — not a finding, an artefact of a first stage with essentially no explanatory
power. Rigobon and Sack anticipate exactly this: "the estimator based on the ω₂
instrument is typically less precise, and the estimator obtained using the combined
instrument set accordingly tends to be closer to that based on the ω₁ instrument." Our
ω₃ column sits on top of ω₁ throughout, for the same reason.

The bootstrap rank test rejects nothing at 5%, which at first looks like it contradicts
t-statistics above 4. It does not: it is a low-power test on 36 observations. The
honest summary is that the rank condition is not *separately* verifiable at this sample
size, and that instrument strength — which is verifiable — is comfortable for ω₁.""")

md("""## 7. Robustness

Rigobon (2003, section IV) proves that misspecifying the regime windows leaves the
estimator consistent as long as the rank condition still holds — propositions 3 and 4.
The empirical counterpart is to move the window and see whether the estimates move.""")

code("""piv = t5.pivot(index="variable", columns="n_high", values="coef")
print("Combined-instrument coefficient as the war-news day set is widened\\n")
print(piv.to_string(float_format=lambda v: f"{v:8.2f}"))""")

md("""From 12 days to 30 — a two-and-a-half-fold change in the definition of the regime —
the S&P estimate moves between −0.60 and −0.66, the Euro Stoxx between −1.33 and −1.53,
the high-yield spread between 0.05 and 0.06, and the VIX between 1.54 and 1.80. This is
what proposition 3 predicts, and it is reassuring in a way a single specification cannot
be: the results are not an artefact of choosing eighteen days.

The two coefficients that *do* wander — gold (−31 to −55) and Tel Aviv (−0.42 to +0.19) —
are the two that Table 4 flags as weakly instrumented. The diagnostics and the robustness
check agree with each other about which numbers to trust.""")

md("""### Non-US indices close before the US session

Europe, Tokyo and Tel Aviv close before New York, so a headline breaking during US hours
reaches them the next day. The baseline measures every variable same-day; this checks
whether the foreign response is really a next-day one.""")

code("""print(t6[["variable", "w3_coef", "w3_t"]]
      .to_string(index=False, float_format=lambda v: f"{v:8.2f}"))""")

md("""Measured next-day, the foreign responses are indistinguishable from zero (t between
−0.7 and 0.5), while same-day they were −1.37 and −1.65 with t-statistics beyond 3. So
the response is contemporaneous and complete within the day: Middle East news generally
breaks during Asian and European hours, and by the following session it is in the price.
The same-day convention is the right one, and there is no delayed drift to collect.""")

md("""## 8. What this says, and what it does not

**The headline numbers.** A war-risk shock large enough to add $5 to Brent takes 0.65%
off the S&P 500, 1.37% off the Euro Stoxx, 1.65% off the Nikkei and off emerging markets;
adds 4.8bp to high-yield spreads, 1.7 points to the VIX and 0.26% to the dollar; and
moves energy equities up 0.96% while taking 1.36% off airlines. Over the eight months to
11 September 2026, this single factor accounts for at least 17% of the variance of
European equity returns and 12% of the VIX.

**The methodological finding.** The 2003 result that war risk depresses Treasury yields,
break-even inflation and the dollar does not survive into 2026 — all three signs flip.
That is not a failure of the method; it is the method working. The same estimator, applied
to a war that transmits through oil supply rather than through demand, returns the
opposite signs on exactly the variables where the transmission channel differs, and the
same signs everywhere else (equities down, credit wider, oil up, gold insignificant).

**Where it could be wrong.**

- *The orthogonality assumption.* Identification requires that no other factor was
  unusually volatile on the selected days. March 2026 was not only a war; it contained
  whatever else was moving markets that month. The robustness across window sizes is
  reassuring but not decisive, and this is the assumption that would break first.
- *The comparison days are not war-free.* Nothing in an eight-month war is. That biases
  the variance shares *down*, so the numbers in Table 3 are lower bounds — but it also
  attenuates the coefficients in Table 2 towards zero.
- *One factor, many dimensions.* "War risk" here bundles the probability of escalation,
  its expected duration, and how much of Hormuz stays open. The estimator recovers the
  dominant combination, not its parts, and the paper is explicit that separating them
  would need assumptions it declines to make.
- *Sample size.* Eighteen days a regime. The estimates are stable and the ω₁ instrument
  is strong, but the rank condition cannot be separately confirmed at this size, and
  four of the seventeen coefficients rest on weak second instruments.""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.13"},
}

with open("analysis.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("wrote analysis.ipynb with", len(cells), "cells")
