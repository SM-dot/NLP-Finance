# Measuring the Effect of Iran War Risk on Global Financial Markets

**FRE-GY 7871 A · NLP and the Investment Process · Fall 2026**
**Submitted:** September 17, 2026

The United States and Israel struck Iran on February 28, 2026. This report measures how
sensitive eighteen global financial variables are to Iranian war risk over the eight
months to September 11, 2026, using the heteroskedasticity-based estimator of Rigobon and
Sack (2003) — with the one step those authors performed by hand, choosing the days on
which war news dominated, performed instead by an NLP index built from news coverage.

All numbers below come from `analysis.ipynb`, which is the source of record; this report
explains what they mean.

## 1. The problem, and why the obvious approaches fail

War risk is unobservable. We know precisely *when* war news broke in 2026; we cannot say
by how much any particular day's news changed the probability of escalation, the expected
duration of the conflict, or the odds that Hormuz stays shut. So there is no war-risk
series to put on the right-hand side of a regression.

The natural fallback, an event study on signed news, fails for a reason this episode
illustrates well. Of the eighteen days our index selects, six carry heavy escalation *and*
heavy de-escalation coverage simultaneously — March 24–26, when the US was reported to be
sending forces while Trump extended his deadline; July 8, when the ceasefire broke but
both sides were still talking. An event study must either discard those days or guess
their sign. They are precisely the days on which the most war-related information arrived.

Rigobon and Sack's answer is to identify the effect from a shift in *variance* rather
than from the level of the factor. Name a set of days H on which war news was unusually
intense, and a set L on which it was not. Assume that (i) the war-risk factor is
orthogonal to the other drivers of asset prices, and (ii) those other drivers were no
more volatile on H than on L. Then the entire change in the covariance matrix of returns
between the two sets is attributable to the war factor, and each asset's sensitivity to
it can be read off that change — without ever measuring war risk. The paper shows this is
equivalent to an instrumental-variables regression, so the usual IV machinery, including
standard errors, comes with it.

Naming the days is therefore the whole ballgame. It is also the one step that is pure
judgment in the original: Rigobon and Sack read newspapers and wrote down seventeen
dates. That is the step NLP replaces here.

## 2. Building the war-risk news index

The daily measures come from GDELT's coverage timelines — five themed queries, each
returning the full window in one request and counting every article GDELT monitored.
(The article endpoint would cap at 250 records a day and refuses so large and random a
share of requests that a full sweep neither finishes in reasonable time nor reproduces;
that route was tried and abandoned, and the reasoning is recorded in
`src/wikinews.py`.)

Three components, each standardised and then averaged:

- **Attention** — log war-risk coverage volume minus its own trailing 10-day median. The
  *level* of coverage is useless once a war is running: Iran was front-page news every
  day from March onwards. What marks a news day is coverage jumping above its own recent
  baseline.
- **Tone shift** — the absolute change in (escalation − de-escalation) ÷ (escalation +
  de-escalation) coverage, where the two vocabularies come from the same escalation axis
  as the hand-built lexicon in `src/warrisk_lexicon.py`. This is the analogue of the
  paper's hand-assigned "Increased / Decreased" column. Only the *shift* enters: a day
  that makes war dramatically less likely is as informative, for variance purposes, as
  one that makes it more likely.
- **Contest** — (1 − |direction|) × log(1 + coverage). High when the day's coverage is
  both heavy and split between the two vocabularies. This is the measure that captures
  the paper's "Unclear" days, and it is the reason those six days are usable here.

**Does the index track reality?** Nothing about the 2026 chronology was supplied to the
code, so this is a real test. Coverage peaks on **February 28**, the day the war began.
The Hormuz-specific series peaks on **April 8**, the day of the two-week ceasefire and
safe passage through the strait. The most conciliatory readings of the direction measure
fall on **June 16–17** and **June 23–24** — the Islamabad Memorandum and the technical
talks that followed it. The direction measure correlates **−0.63** with GDELT's
independently computed tone series, with the expected sign.

![Figure 1](figures/figure1_war_news_index.png)

**Table 1** (in `report_tables/table1_war_news_days.csv`, printed in full in the
notebook) lists the eighteen selected days with the event text for each, drawn from
Wikipedia's Current Events Portal. That text is used only to label and to give the
lexicon and FinBERT something to read — never to choose the days. Eight days tip towards
escalation, four towards de-escalation, six are genuinely mixed.

Two NLP methods were run over that event text, as in Assignment 2: the hand-built
war-risk lexicon and FinBERT. They agree only weakly (r = +0.08 across the selected
days), and the disagreement is instructive rather than alarming. FinBERT is trained on
financial disclosure and earnings commentary; asked to read "Iran's military command
rejects an ultimatum," it scores the sentiment of the *language*, with no notion that a
rejected ultimatum raises the probability of war. This is why the index is built on the
purpose-made escalation axis and not on an off-the-shelf sentiment model — and it is the
same lesson Assignment 2 drew about Loughran–McDonald and hawkish/dovish tone.

## 3. The identifying assumption, and where 2026 parts company with 2003

The method needs the selected days to be genuinely more volatile. That is testable.

| | variance on war-news days ÷ on comparison days |
|---|---:|
| Brent crude | **6.21×** |
| VIX | 4.72× |
| Tel Aviv 125 | 3.59× |
| Euro Stoxx 50 | 3.34× |
| High-yield spread | 3.12× |
| Broad dollar | 2.52× |
| S&P 500 | 1.60× |
| **Two-year Treasury yield** | **1.05×** |
| Gold | 1.03× |
| **Ten-year Treasury yield** | **0.84×** |

![Figure 2](figures/figure2_variance_ratio.png)

Rigobon and Sack normalise everything on the two-year Treasury yield, because in 2003
that was the cleanest barometer of war risk: their Table 3 shows its variance rising from
.00096 on quiet days to .00594 on war-news days, a factor of 6.2.

**In 2026 the Treasury market barely notices.** The two-year's variance is 1.05 times
higher on war-news days; the ten-year's is *lower*. The factor of 6.2 has moved to oil.

The reason is economic, not statistical. A war that arrives as an oil-supply shock in an
inflationary economy pushes yields down through flight to quality and up through the
inflation outlook, and the two roughly cancel. Normalising on a variable that barely
responds to the factor puts a number near zero in the estimator's denominator — exactly
the rank-condition failure Rigobon (2003) warns about. So **Brent takes the two-year
yield's role** as the normalising variable, and results are reported scaled to a war-risk
increase large enough to raise Brent by $5 a barrel.

The paper's own normalisation is reported alongside rather than quietly dropped, because
what it produces is itself a result: gold moving $1,968 per 25bp, the S&P *rising* 18.7%
when war risk increases, the three instrument sets disagreeing wildly, and not one
t-statistic clearing 2.1. Those coefficients are not small and insignificant; they are
enormous and insignificant, which is the signature of dividing by something near zero.

## 4. Results

**Table 2. Estimated impact of a war-risk increase that raises Brent $5/bbl**
(combined instrument ω₃; *** p<1%, ** p<5%, * p<10%)

| Variable | Units | ω₁ | ω₂ | ω₃ | t(ω₃) | |
|---|---|---:|---:|---:|---:|---|
| Two-year Treasury yield | pp | 0.02 | 0.01 | 0.018 | 1.68 | * |
| Ten-year Treasury yield | pp | 0.02 | −0.03 | 0.019 | 2.28 | ** |
| Break-even inflation (10y) | pp | 0.01 | −0.00 | 0.014 | 3.45 | *** |
| S&P 500 | pct | −0.65 | −0.63 | −0.650 | −2.96 | *** |
| BBB yield spread | pp | 0.01 | 0.01 | 0.008 | 2.91 | *** |
| High-yield yield spread | pp | 0.05 | 0.08 | 0.048 | 3.61 | *** |
| Gold price | $ | −35.11 | −7.58 | −36.63 | −1.90 | * |
| Dollar (broad index) | pct | 0.26 | 0.35 | 0.257 | 3.24 | *** |
| VIX | pts | 1.60 | 3.04 | 1.748 | 3.72 | *** |
| Euro Stoxx 50 | pct | −1.35 | −1.68 | −1.370 | −4.47 | *** |
| Nikkei 225 | pct | −1.62 | −2.80 | −1.649 | −3.28 | *** |
| Tel Aviv 125 | pct | 0.03 | 128.55 | 0.069 | 0.10 | |
| MSCI EM equities | pct | −1.67 | −0.70 | −1.651 | −3.45 | *** |
| Swiss franc per dollar | pct | 0.24 | 0.37 | 0.237 | 2.36 | ** |
| US energy equities (XLE) | pct | 1.04 | 1.64 | 0.958 | 3.17 | *** |
| US airlines (JETS) | pct | −1.49 | −2.03 | −1.359 | −2.83 | *** |
| Aerospace & defence (ITA) | pct | −0.65 | −1.82 | −0.554 | −1.01 | |

![Figure 3](figures/figure3_coefficients.png)

**Global equities fall, and they fall harder outside the United States.** The S&P loses
0.65%; the Euro Stoxx 1.37%, the Nikkei 1.65%, emerging markets 1.65% — between two and
two and a half times the US move. That ordering is what an oil-supply shock implies:
Europe, Japan and the emerging world import the oil whose price is rising, and the US,
now a net exporter, does not. The same logic shows up within the US cross-section, where
energy producers *gain* 0.96% while airlines lose 1.36%.

**Credit widens and volatility rises**, as in 2003: high-yield spreads by 4.8bp, BBB by
0.8bp, the VIX by 1.7 points. The ratio between the two credit grades — high yield moving
six times as far as investment grade — is close to what Rigobon and Sack found (34bp
versus 5bp).

**Three signs are the opposite of 2003, and they all say the same thing.**

| | Rigobon–Sack (2003) | This paper (2026) |
|---|---|---|
| Ten-year Treasury yield | **falls** −0.26pp | **rises** +0.019pp (t=2.3) |
| Break-even inflation | **falls** −0.11pp | **rises** +0.014pp (t=3.4) |
| Broad dollar | **falls** −0.44% | **rises** +0.26% (t=3.2) |

In 2003, war risk was priced as a threat to *demand*: disinflationary, bad for growth,
bad for the dollar. In 2026 it is priced as a threat to *supply* — inflationary, and with
the dollar the asset investors run towards rather than away from. The Swiss franc also
appreciates against the dollar (+0.24%), which says this is a general flight into safe
currencies that the dollar participates in, not a dollar-specific story.

**Two non-results.** Gold does not respond significantly (t = −1.90, and the point
estimate is negative). Rigobon and Sack also found no significant gold response — one of
the more durable findings across twenty-three years, and a useful corrective to the
assumption that gold is a war hedge. And the Tel Aviv 125 shows no significant response
at all, despite its variance rising 3.6× on war-news days: Israeli equities moved a great
deal on these days, but not in proportion to the common war factor that oil prices. Their
volatility was Israel-specific.

**Table 3. Share of variance attributable to the war factor** (lower bounds)

| Variable | on war-news days | over the whole window |
|---|---:|---:|
| Euro Stoxx 50 | 53.0% | 16.8% |
| VIX | 49.4% | 12.5% |
| Dollar (broad) | 43.9% | 8.5% |
| MSCI EM equities | 42.9% | 8.7% |
| Break-even inflation | 42.2% | 4.6% |
| High-yield spread | 41.3% | 9.0% |
| S&P 500 | 38.7% | 6.1% |
| Nikkei 225 | 33.4% | 8.2% |
| US airlines | 31.5% | 3.9% |
| US energy equities | 30.8% | 4.3% |
| BBB spread | 28.3% | 5.1% |
| Ten-year Treasury yield | 16.8% | 2.0% |

These are lower bounds for the reason the paper gives: the comparison days are not free
of war news either, so the variance *shift* understates the war-related variance level.
Rigobon and Sack report 13–63% over their ten weeks; our window is three times longer,
so war-news days are a smaller share of it and the whole-window figures are
correspondingly smaller.

## 5. Is any of this identified?

Rigobon (2003) gives the condition: the estimator fails when the two covariance matrices
are proportional, so that the war-news days are just a scaled-up version of ordinary days
and nothing is learned. The test statistic is a function of products of second moments,
and at eighteen days a regime its bootstrap test has almost no power — it rejects nothing
at 5%, which sits oddly beside t-statistics above 4.

The first-stage F on the excluded instrument is the operational form of the same
condition, and it is decisive:

- **ω₁ is strong everywhere**, F ≈ 38, well clear of the conventional threshold of 10.
- **ω₂ varies enormously**: 16.2 for the Euro Stoxx, 11.5 for the VIX, but **0.002 for
  the Tel Aviv 125**, and below 2 for gold, the two-year yield and defence stocks.

That single number explains the strangest entry in Table 2 — Tel Aviv's ω₂ estimate of
+128.55 is not a finding but an artefact of a first stage with no explanatory power.
Rigobon and Sack anticipate this exactly: "the estimator based on the ω₂ instrument is
typically less precise, and the estimator obtained using the combined instrument set
accordingly tends to be closer to that based on the ω₁ instrument." Our ω₃ column sits on
top of ω₁ throughout, for that reason.

**Robustness.** Rigobon (2003, propositions 3 and 4) proves that misspecifying the regime
windows leaves the estimator consistent as long as the rank condition still holds. Moving
the war-news set from 12 days to 30 — a two-and-a-half-fold change in the definition of
the regime — the S&P estimate stays between −0.60 and −0.66, the Euro Stoxx between −1.33
and −1.53, the high-yield spread between 0.05 and 0.06, the VIX between 1.54 and 1.80.
The two coefficients that *do* wander, gold (−31 to −55) and Tel Aviv (−0.42 to +0.19),
are the two the instrument diagnostics already flagged. The diagnostics and the
robustness check agree about which numbers to trust.

**Timing.** Europe, Tokyo and Tel Aviv close before New York. Measured next-day instead
of same-day, the foreign equity responses are indistinguishable from zero (t between −0.7
and +0.5), against −1.37 and −1.65 with t beyond 3 same-day. The response is
contemporaneous and complete within the day — Middle East news generally breaks during
Asian and European hours — so the same-day convention is right and there is no delayed
drift to collect.

## 6. What would make this wrong

- **The orthogonality assumption is the one that would break first.** Identification
  requires that no *other* factor was unusually volatile on the selected days. March 2026
  was not only a war; it was also whatever else was moving markets that month. Stability
  across window sizes is reassuring but not decisive.
- **The comparison days are not war-free.** Nothing in an eight-month war is. This biases
  the variance shares in Table 3 down — they are honestly labelled as lower bounds — but
  it also attenuates the Table 2 coefficients towards zero, so the estimated sensitivities
  are, if anything, too small.
- **"War risk" is one factor standing in for several.** It bundles the probability of
  further escalation, the expected duration, and how much of Hormuz stays open. The
  estimator recovers the dominant combination of these, not the parts; the paper is
  explicit that separating them would need assumptions it declines to make.
- **Eighteen days a regime is not many.** The estimates are stable and ω₁ is strong, but
  the rank condition cannot be confirmed separately at this sample size, and four of the
  seventeen coefficients rest on weak second instruments.

## 7. Two things the replication turned up about the method itself

**The equal-sized-sets requirement is load-bearing.** The paper defines its instrument
over "an equal-sized set of other days," which reads like a convenience. It is not. With
unequal sets the instrument's moment condition becomes n_H·E_H[Δx²] − n_L·E_L[Δx²] rather
than the difference in variances, and the estimator is badly biased rather than merely
noisier. In the Monte Carlo in `scripts/00_test_estimator.py`, an 18/159 split returns
+0.9 when the truth is −3.75; the same data with matched sets returns −3.89.
`src/heteroskedasticity.py` weights each regime by 1/n so the moment condition is correct
either way, and the day sets are built equal-sized regardless.

**The paper's footnote 7 rule needs adapting to a running war.** Rigobon and Sack choose
comparison days "as close as possible to" the war-news days, so that other factors'
variances are similar across the sets. Their window was the *run-up* to a war, where
nearby days really were quiet. In 2026 the days nearest a big war-news day are themselves
war days, and the literal rule filled the comparison set with exactly the coverage it was
supposed to exclude — which made L *more* volatile than H and broke identification
outright. Restricting comparison days to the quiet half of the news-score distribution,
and then taking the nearest qualifying day, preserves both of the paper's goals.

Both points are recorded where the code implements them, and the first is covered by a
Monte Carlo that fails if the estimator regresses.

## References

- Rigobon, R. and B. Sack (2003), "The Effects of War Risk on U.S. Financial Markets,"
  NBER Working Paper 9609.
- Rigobon, R. (2003), "Identification through Heteroskedasticity," *Review of Economics
  and Statistics* 85(4), 777–792.
- News data: GDELT Project DOC 2.0 API; event chronology from Wikipedia's Current Events
  Portal.
- Market data: FRED (Federal Reserve Bank of St. Louis) and Yahoo Finance.
