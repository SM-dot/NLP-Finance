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

Figure 1 makes this visual: the top panel is the daily war-risk score with the 18
selected H days marked in red, and the two panels below plot Brent and the two-year
yield over the same dates with the same days marked as vertical bands, so the reader
can check by eye whether the flagged days line up with real market moves rather than
taking the correlation number above on faith. The tallest spike in the top panel is
28 February itself; the score sits in a mostly negative range through January and
February (ordinary background chatter, not a war), rises to a dense, elevated cluster
through March (the most intense fighting), and falls back to a low, occasional-spike
pattern from May onward. The Brent panel climbs steadily across this window; the
two-year panel is visibly choppier and less obviously tied to the marked days — an
early visual hint of the section below.

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

Figure 2 shows this ratio for every variable, sorted, so the pattern is visible at a
glance rather than read off a table: oil at the top (6.2×), the VIX (4.7×) and Tel
Aviv equities (3.6×) not far behind, and Treasuries, gold and break-even inflation
clustered at the bottom near or below the no-effect line at 1×. One pairing is worth
flagging now, ahead of the coefficient table below: Tel Aviv's bar here is the
third-highest in the whole chart, yet its estimated coefficient turns out to be
statistically indistinguishable from zero. Those two facts sit together comfortably —
a variable can be genuinely noisier on war-news days for reasons specific to it
(Israel-specific wartime news, not the oil-and-risk-sentiment channel that moves
everything else) without that extra noise being explained by the *shared* factor the
other variables respond to. Figure 2 answers "is this variable more volatile on war
days"; the coefficient in Table 2 answers "is that volatility the same common war-risk
factor everyone else is exposed to" — and for Tel Aviv those two answers diverge.

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

md("""Figure 3 is the point-and-interval version of the table above, split into four
panels by unit (percent, percentage-point, index-point, and dollar changes cannot
share an axis) — each dot a coefficient, the bar through it a 95% interval, coloured
red or blue when the interval clears zero and grey when it does not. Two things are
easier to see here than in the table: the equity panel sorts cleanly into a single
red bar (US energy) on the positive side against a wall of blue bars (S&P, Euro
Stoxx, Nikkei, EM, airlines) on the negative side - the cross-sectional signature of
an oil-supply shock, visible at a glance - and the *width* of each interval is doing
real work: Tel Aviv's bar is wide enough to straddle zero by a large margin (the
weak-ω₂-instrument problem quantified in Section 6 below), which is a different and
more informative statement than simply "not significant."

![Figure 3](figures/figure3_coefficients.png)

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

md("""# Extending the analysis

Sections 1-7 above replicate the paper's core design: flag days 1/0 from NLP, let
heteroskedasticity do the estimating. Sections 9-16 below extend that in four
directions: a more reliable news source than Wikipedia, a three-regime split
(bad/good/no war news), a direct, tested answer to "is heteroskedasticity the best
approach" with concrete alternatives, and a quantified check of the lexicon's
vocabulary coverage.""")

code("""t7 = pd.read_csv(TABLES / "table7_regime_mean_comparison.csv")
t8 = pd.read_csv(TABLES / "table8_regime_overidentification.csv")
t9 = pd.read_csv(TABLES / "table9_classifier_performance.csv")
t10 = pd.read_csv(TABLES / "table10_classifier_coefficients.csv")
t11 = pd.read_csv(TABLES / "table11_method_comparison.csv")
t12 = pd.read_csv(TABLES / "table12_event_study.csv")
t13 = pd.read_csv(TABLES / "table13_vocabulary_coverage.csv")
t14 = pd.read_csv(TABLES / "table14_method_agreement.csv")
print("Loaded Tables 7-14")""")

md("""## 9. Sourcing news reliably

Wikipedia's Current Events Portal, used for Table 1's event descriptions in an
earlier pass, is a tertiary, community-edited summary, not journalism. GDELT's
*article* endpoint (real news-wire content, with each record's publishing domain
attached) was tried as the fix, restricted to only the ~36 selected days. It was tested
at three request spacings (7s, 16s, 22s) with up to 10 retry passes and 45-second
cooldowns between passes; none reliably cleared GDELT's throttling within the session -
a sustained run at the widest spacing produced zero successes across five minutes of
continuous attempts.

Table 1's 18 event descriptions were instead compiled through targeted, one-day-at-a-
time research against Al Jazeera, CNN and Bloomberg reporting, each with a source URL,
stored in `data/news/verified_events.json`. This is a manual, one-time step that runs
*after* day-selection is complete - it changes only what Table 1 prints next to each
date, not which days were selected or any estimation result. Table 1 above already
reflects this sourcing.""")

md("""## 10. Is heteroskedasticity-based identification the best approach? The verdict

**For this problem - a shared risk factor whose sign is often ambiguous day to day,
observed through news volume - yes, and Section 13 below is a direct empirical test of
why, not an assertion.**

- It is the only method here that doesn't need to know the sign of the news: 6 of the
  18 selected days are genuinely mixed (heavy escalation *and* de-escalation coverage
  at once).
- It survives an adversarial head-to-head test against the standard alternative
  (Section 13): a plain OLS event study on the identical day-flag finds **zero**
  significant variables at 5% out of 18; heteroskedasticity finds **13 of 17**.
- It is robust to how the day-classification line is drawn (Section 7's window-size
  check, and Section 12's three independent classification methods below).

**Where it is not the best tool:** it needs at least two regimes of genuinely
different variance (testable but low-power at this sample size - four coefficients
rest on a weak second instrument); it estimates a sensitivity, not a level effect; and
it needs the day-classification to be exogenous to the outcome - which Section 12
shows concretely by demonstrating what goes wrong when it isn't.""")

md("""## 11. Extension 1 - three regimes, not two

War-news days can be split into bad-news (coverage skews escalatory), good-news
(skews de-escalatory), and no-news, built from the `direction` measure already
computed for Table 1. This follows Rigobon (2003, section II.C)'s multi-regime
extension of the same estimator.""")

code("""hyp = ["y2", "y10", "brent", "spx", "stoxx", "vix", "hy"]
show = t7[t7["column"].isin(hyp)][["variable", "mean_Bad-news", "mean_Good-news",
                                    "mean_No-news"]]
print(show.to_string(index=False, float_format=lambda v: f"{v:9.4f}"))""")

md("""All seven core variables match the expected sign on bad-news
days using nothing more than simple conditional means: yields, oil and the VIX rise;
equities fall. Good-news days largely reverse it (S&P +0.79% vs -0.14% on bad-news
days; VIX -0.85 vs +0.69).

![Figure 6](figures/figure6_regime_comparison.png)""")

code("""print(t8[["variable", "d_from_bad_vs_no (n=8 vs 18)",
          "d_from_good_vs_no (n=4 vs 18)", "same_sign"]]
      .to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
print(f"\\nSigns agree on {int(t8['same_sign'].sum())}/{len(t8)} variables")""")

md("""A genuine overidentification test (Rigobon 2003, section II.C): if the
structural loading is direction-symmetric, estimating it separately from
(bad-news, no-news) and (good-news, no-news) should agree in sign despite the two
sub-samples having opposite average news direction. They agree on 10/17 (59%) - an
honest result given sub-samples of only 4 and 8 days, not a clean pass. The
descriptive mean-comparison above (7/7) is the more reliable evidence for the regime
split; this stricter test is reported because an honest overidentification check,
even a noisy one, belongs in the record.""")

md("""## 12. Extension 2 - classifying war-news days three independent ways

Beyond the hand-tuned z-score threshold, two more principled ways to produce the same
1/0 flag: **(a)** a cross-validated logistic regression, trained to predict an
*independent, market-based* definition of a high-stress day (never used to select the
H-set fed to estimation - see `src/classify.py`'s docstring for why that would be
circular) from the NLP features alone; **(b)** an unsupervised Gaussian mixture on the
NLP features, with no market data anywhere in the model.""")

code("""print(t9.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print()
print(t10.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))""")

md("""![Figure 4](figures/figure4_classifier_diagnostics.png)

**ROC-AUC of 0.43 - worse than random.** This is a genuinely negative result, and it
is informative rather than simply a failure: `attention` and `war_share` load
*negatively* on the market-based label, and the reason is structural - that label is
built from a basket that includes the two-year yield, which Section 3 already
established barely responds to Iran war risk specifically (1.05x variance ratio,
against Brent's 6.21x). A composite that includes a variable the war factor doesn't
move is, by construction, dominated by *other* macro-driven volatile days that have
nothing to do with Iran - and on those days, Iran-specific news coverage is naturally
lower, not higher. This is evidence *for* news-content-based day selection over
market-based selection, not against the news measure: the overlap between the
market-composite label and the NLP-heuristic H-set is only 3/18 (17%).""")

code("""key = ["y2", "y10", "spx", "hy", "dollar", "vix", "stoxx"]
show = t11[t11["column"].isin(key)][["variable",
    "coef__Heuristic z-score (headline results)",
    "coef__Supervised classifier (CV-predicted)",
    "coef__Unsupervised GMM (NLP-only)"]]
print(show.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))""")

md("""Given the classifier's poor predictive power, its day-set should be trusted
less than the heuristic one - and the table bears this out: equity and credit results
(S&P, high-yield spread) keep their sign and order of magnitude across all three
classification methods, but VIX and the dollar flip sign under the classifier-based
set, the clearest sign that a weak classifier propagates its weakness downstream.""")

md("""## 13. Extension 3 - the plain alternative: event-study OLS, and why it loses

The most standard alternative to heteroskedasticity: regress each variable's daily
change on the identical 1/0 flag, plain OLS with HC1 robust SEs.

    dx_t = alpha + beta * war_news_flag_t + u_t""")

code("""n_sig_het = 13  # from Table 2 above
n_sig_es = int((t12["p"] < 0.05).sum())
print(t12[["variable", "beta", "t", "p"]]
      .to_string(index=False, float_format=lambda v: f"{v:9.4f}"))
print(f"\\nEvent-study: {n_sig_es}/{len(t12)} significant at 5%")
print(f"Heteroskedasticity (Table 2, same days): 13/17 significant at 5%")""")

md("""**Zero of eighteen variables significant, against heteroskedasticity's 13 of
17 on the exact same 18 flagged days.** Of the 18 flagged days, 8 are escalatory and 4
de-escalatory (6 mixed) - a variable that responds to war risk with *opposite* signs
on bad- versus good-news days (Section 11 demonstrates it does) sees those moves
cancel in a simple average, pushing beta toward zero regardless of the true
sensitivity. Variance doesn't cancel the same way: a $5 up-move and a $5 down-move
contribute equally to variance, so the heteroskedasticity estimator recovers the
shared factor loading even when its sign varies day to day. This is the cleanest
empirical demonstration in this report of why the paper's method fits this specific
problem - a head-to-head test, not an assumption.""")

md("""## 14. Sign and significance across all methods""")

code("""show = t14[["variable", "het_heuristic_coef", "het_heuristic_t",
            "event_study_beta", "event_study_t", "all_signs_agree"]]
print(show.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
print(f"\\n{int(t14['all_signs_agree'].sum())}/{len(t14)} agree in sign across all "
      f"three method/day-set combinations")""")

md("""![Figure 5](figures/figure5_method_comparison.png)

4/10 headline variables agree in sign across all three combinations - but the
event-study column is statistically indistinguishable from zero for every row, so
comparing its sign against methods that *do* find significant effects is comparing a
coin flip against a real estimate. The informative comparison is heteroskedasticity-
heuristic versus heteroskedasticity-classifier, which agree on 7/10 - failing only on
VIX, dollar and gold, precisely the three variables already flagged as riding on a
near-random classifier day-set.""")

md("""## 15. Vocabulary coverage of the lexicon

A fixed phrase list built in advance cannot anticipate the specific vocabulary a
live, unfolding conflict generates. Checked directly against the verified real-news
text, sentence by sentence, against the hand-built lexicon.""")

code("""print(t13.to_string(index=False))""")

md("""**52.5% of sentences from real, dated, sourced reporting on these war-news
days score zero lexicon hits**, despite describing strikes, blockades, casualties and
ceasefire negotiations. Concrete examples the lexicon is blind to: "Natanz nuclear
enrichment complex" (a facility name - no place-name knowledge at all), "rogue
supertankers" (a compound noun this conflict's coverage invented), "the
memorandum-of-understanding ceasefire" (a named diplomatic instrument that didn't
exist before this war). This affects sentence-level lexicon scoring specifically -
the day-selection itself runs on GDELT's aggregate coverage-volume timelines, not
phrase-matching, so it is unaffected. The honest fix (not built as a full pipeline
step here, for scope) is an LLM reading the text in context rather than a fixed
phrase list.""")

md("""## 16. Comparison against the 2003 episode

An economically motivated prior: oil, credit spreads and equities should move like
2003, but yields should flip given higher inflation, debt concerns, weaker
flight-to-quality, and US oil output now ~14M bbl/day versus ~6M in 2003.

| | 2003 | 2026 | Matches prior? |
|---|---|---|---|
| Oil, credit, equities | up/wider/down | up/wider/down | Yes |
| Gold | insignificant | insignificant (t=-1.90) | Yes |
| Treasury yields | fall (-26bp) | **rise** (+1.9bp, t=2.28) | No - as predicted |
| Break-even inflation | falls | **rises** (t=3.45) | No - as predicted |
| Dollar | falls | **rises** (t=3.24) | No - as predicted |

Every sign expected to hold, held; every sign expected to flip, flipped. This is the
direct market-level expression of the US's much larger oil industry: a war-driven oil
spike is now a mixed rather than uniformly negative shock to the US economy, consistent
with yields rising (an inflation/growth story) rather than falling (a pure
flight-to-safety story).""")

md("""## 17. What this says, and what it does not

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
  four of the seventeen coefficients rest on weak second instruments.
- *The supervised classifier's near-random performance (Section 12) is itself worth
  stating as a limitation*: "can NLP features predict market stress" and "can NLP
  features identify Iran-specific war-risk days" are different questions with
  different answers here, and only the second is what the headline method needs.
- *The vocabulary-coverage gap (Section 15, 52.5% zero-hit rate)* affects
  sentence-level lexicon scoring specifically, not the aggregate coverage-volume
  measure the day-selection runs on - but limits any future extension that scores
  individual sentences with this fixed phrase list.
- *Table 1's event descriptions are a hand-verified, one-time research step*, not an
  automated, infinitely reproducible pipeline stage the way day-selection is -
  re-running the scripts reproduces the day-selection and Tables 2-14 exactly, but
  Table 1's citations would need re-verification if the selected days changed.""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.13"},
}

with open("analysis.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("wrote analysis.ipynb with", len(cells), "cells")
