# Evaluating the Impact of FOMC Communications on Asset Prices

**FRE-GY 7871 A · NLP and the Investment Process · Fall 2026**
**Submitted:** September 15, 2026

Kevin Warsh was sworn in as Federal Reserve Chair on May 22, 2026, succeeding Jerome
Powell. This report scores the tone of every Federal Reserve communication from February
2018 through September 15, 2026 — 314 documents in total — with two independent methods,
checks whether that tone moved markets once the rate decision itself is controlled for,
and forecasts the September 16, 2026 FOMC decision, which had not yet happened as of this
assignment's deadline.

All numbers below are produced by `analysis.ipynb`, which is the source of record; this
report explains what they mean.

## 1. The data

Every FOMC post-meeting statement and set of minutes since February 2018 — including the
four intermeeting emergency actions of March 2020 — every Chair speech and congressional
testimony (Powell and Warsh, the only two chairs in the window), and every FOMC press
conference transcript, scraped directly from federalreserve.gov.

**Table 1. Documents collected, by type and by Chair**

| Document type | Powell | Warsh | Total |
|---|---:|---:|---:|
| Statement | 72 | 2 | 74 |
| Minutes | 66 | 2 | 68 |
| Press conference | 64 | 2 | 66 |
| Speech | 77 | 2 | 79 |
| Testimony | 26 | 1 | 27 |
| **Total** | **305** | **9** | **314** |

Warsh's sample is small by construction: he has chaired two FOMC meetings. Every exhibit
below that speaks to "the Warsh era" should be read with that in mind — Table 2 shows the
Warsh-era data in full so the reader can see exactly how little of it there is, and Table 3
deliberately pools the full sample to get usable statistical power, rather than
running an under-powered Warsh-only regression.

Market data: DXY and the Russell 1000 Growth / Russell 2000 Value ETFs (IWF, IWN) from
Yahoo Finance; the 10s2s spread, 1-year Treasury yield, and 3-month bill (control) from
FRED. All four target indicators plus the control cover the same Feb 2018 - Sep 2026 window.

## 2. Tone over time (Figure 1)

Two independent tone measures were built for every document:

1. **A custom hawkish/dovish word list** — phrases like "higher inflation," "raise interest
   rates" and "restrictive stance" scored +1, phrases like "inflation has eased," "cut
   rates" and "accommodative stance" scored -1, net score per 1,000 words. This is a
   purpose-built monetary-policy list, not the general-purpose Loughran-McDonald finance
   dictionary, which has no hawkish/dovish axis at all.
2. **FinBERT** (`ProsusAI/finbert`) sentence-level sentiment, aggregated as mean
   P(positive) − mean P(negative) per document.

![Figure 1](figures/figure1_tone_over_time.png)

The full-sample chart shows the story you'd expect from the last eight years: tone climbs
sharply through the 2022 hiking cycle (statement word-list scores above +10), collapses to
near zero (even slightly negative) at the depth of the 2020 pandemic response, rises again
through the 2022-2023 tightening, and has been declining since the 2024-2025 cutting cycle
began. Statements — short, dense, and written to move markets — carry by far the most
volatile word-list scores; minutes, press conferences and speeches are longer and read
close to zero, since a few hawkish or dovish phrases get diluted across thousands of words
of surrounding prose.

**Zooming into 2025-2026** (below) is where the Powell-to-Warsh comparison actually lives:

![Figure 1b](figures/figure1b_tone_zoom_2025_2026.png)

**Word-list tone barely moves at the transition** — Powell's last statements (Feb-Apr 2026,
scores 5.2-5.7) and Warsh's first two (June 5.85, July 4.81) sit in the same range;
July's reading is, if anything, the lowest since October 2025. **FinBERT tells a different
story**: it jumps from a Powell-era 2026 range of roughly 0.04-0.11 to 0.38 (June) and 0.29
(July) under Warsh — the two Warsh statements are the two highest FinBERT readings for any
statement in the entire 8.5-year sample. The same gap shows up pooling every document type
(mean FinBERT score 0.050 for Powell vs. 0.155 for Warsh, more than a full standard
deviation apart) while the pooled word-list means are close (1.55 vs. 1.61).

**Why the two measures disagree.** FinBERT is a generic financial-sentiment classifier — it
was trained to recognize optimistic-sounding financial language, not a hawkish/dovish axis.
Warsh's remarks lean on upbeat framing ("productivity growth and capital investment are
strong," "truly lucky to work with colleagues so capable") that reads as positive sentiment
regardless of the policy stance behind it. The word list only rewards phrases that are
actually about the rate path, so it isn't fooled by generally optimistic language. This is
the same gap the "Parsing the Fed" comparison flags between FinBERT and a purpose-built
word list — and it's a genuine methods finding here, not a bug: **the two "hawkish/dovish"
measures the assignment asks for are not measuring the same thing**, and a reader who only
looked at FinBERT would conclude Warsh is dramatically more hawkish than Powell, while a
reader who only looked at the word list would say almost nothing has changed.

## 3. Validating market reactions

**Table 2. Warsh-era releases: tone scores next to the one-day market reaction**

*(same-day close-to-close; statements/minutes/press conferences are released at 2:00 p.m.
ET, mid-session, so this is the standard event-study window; see `README.md` for the
convention used for speeches/testimony)*

| Date | Type | Word-list tone | FinBERT tone | ΔDXY | Δ10s2s | Δ1y yield | ΔGrowth−Value | Δ3mo bill (control) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-31 | speech | 0.00 | 0.076 | +0.29 | -0.05 | +0.04 | +0.0125 | +0.09 |
| 2026-06-17 | minutes | 0.91 | 0.127 | +0.55 | -0.09 | +0.14 | -0.0026 | +0.04 |
| 2026-06-17 | press conf. | 0.40 | 0.073 | +0.55 | -0.09 | +0.14 | -0.0026 | +0.04 |
| 2026-06-17 | **statement** | **5.85** | **0.381** | +0.55 | -0.09 | +0.14 | -0.0026 | +0.04 |
| 2026-07-14 | testimony | 0.71 | 0.188 | -0.34 | +0.04 | -0.10 | +0.0143 | -0.05 |
| 2026-07-29 | minutes | 0.83 | 0.106 | -0.58 | +0.10 | -0.05 | -0.0097 | -0.07 |
| 2026-07-29 | press conf. | 0.53 | 0.067 | -0.58 | +0.10 | -0.05 | -0.0097 | -0.07 |
| 2026-07-29 | **statement** | **4.81** | **0.294** | -0.58 | +0.10 | -0.05 | -0.0097 | -0.07 |
| 2026-08-28 | speech | 0.43 | 0.082 | +0.54 | -0.08 | +0.11 | -0.0021 | +0.06 |

Note that all three releases sharing a meeting date (minutes, press conference, statement)
necessarily share the same market reaction — they hit the tape the same day — so this table
really contains six independent market-reaction days, not nine. The June 17 hold (12-0,
unanimous) coincided with a stronger dollar and a small back-up in yields; the July 29 hold
(9-3, with three dissents *for* a hike) coincided with dollar weakness and lower yields —
the opposite of what the word-list and FinBERT tone scores alone would predict, since July's
statement reads more hawkish on both measures than June's minutes/press-conference pair.
This is exactly why Step 3 asks for a regression that controls for the decision itself: with
only six days to look at, a table like this can't separate "the words moved the market" from
"the market already knew what the decision would be, and moved on that."

**Table 3. Each indicator's one-day change regressed on each tone score, controlling for
the change in the 3-month bill (full Feb 2018 - Sep 2026 sample, OLS, HC1 robust SEs)**

| Indicator | Tone method | n | Tone coef. | Tone p-value | 3mo-bill coef. | 3mo-bill p-value | R² |
|---|---|---:|---:|---:|---:|---:|---:|
| DXY | Word list | 311 | 0.004 | 0.643 | 3.968 | <0.001 | 0.080 |
| DXY | FinBERT | 311 | 0.398 | 0.081 * | 3.782 | <0.001 | 0.088 |
| 10s2s spread | Word list | 311 | -0.0013 | 0.166 | -0.436 | <0.001 | 0.109 |
| 10s2s spread | FinBERT | 311 | 0.009 | 0.689 | -0.429 | <0.001 | 0.102 |
| 1-year yield | Word list | 311 | 0.0003 | 0.713 | 0.924 | <0.001 | 0.306 |
| 1-year yield | FinBERT | 311 | 0.020 | 0.398 | 0.914 | <0.001 | 0.307 |
| Growth − value | Word list | 311 | 0.0005 | **0.017 \*\*** | 0.007 | 0.684 | 0.013 |
| Growth − value | FinBERT | 311 | -0.006 | 0.338 | 0.006 | 0.745 | 0.003 |

**The 3-month bill control does exactly what it's supposed to do.** It is significant at
p<0.001 in six of eight regressions (everything except growth-minus-value, which the bill
barely explains at all — a sensible result, since growth-vs-value is a relative-return
spread, not a rate-sensitive level). Once the decision itself is controlled for, tone has
almost no independent power over three of the four indicators: seven of the eight tone
coefficients are statistically indistinguishable from zero.

**Two exceptions are worth a closer look.** The word-list score is significantly (p=0.017)
associated with growth-minus-value: a more hawkish statement corresponds with growth stocks
*outperforming* value on the same day — the opposite of the standard duration-sensitivity
story, where hawkish surprises should hurt long-duration growth names more. One reading:
in this sample, the most hawkish statements were written during strong-economy periods
(2022's "the economy is strong enough to bear higher rates" framing), and growth stocks
respond more to the strong-economy signal embedded in hawkish language than to the discount-
rate mechanics. FinBERT sentiment is marginally (p=0.081) associated with a stronger dollar
— consistent with "upbeat Fed commentary supports the currency," though at 10% significance
this is suggestive, not conclusive. R² for the 1-year yield regressions (~0.31) is far
higher than for the other three indicators (0.01-0.11), which makes sense: a 1-year yield is
priced almost entirely off near-term Fed policy, so the 3-month bill control alone explains
most of its variance, leaving less room for anything — tone included — to add power.

## 4. How this compares with the readings

- **Doh, Kim and Yang (2021)** build a word-count tone measure and find it explains a
  small but statistically real share of Treasury-yield moves around FOMC statements once
  the rate decision is controlled for. Table 3 lands in the same place: the word-list tone
  measure here is directionally sensible on three of four indicators but rarely clears
  conventional significance after the 3-month bill is in the regression — the decision
  dominates the words, just as in their result. Where we differ: they find modest but
  positive explanatory power on yields; we find none there, but do find a significant
  effect on the growth-value spread that their setup does not test.
- **Doh, Song and Yang (2020/2023)** isolate wording from the decision more cleanly than we
  can, by comparing the statement the Committee chose to the alternative statements it
  considered and rejected. Our 3-month-bill control is a cruder proxy for the same idea —
  "what had the market already priced in" — and arrives at a similar qualitative
  conclusion: wording matters at the margin, not at the center of the market reaction.
- **"Parsing the Fed" (2021)** runs the same three methods this assignment specifies
  (factor similarity, word list, FinBERT sentiment) and reports that FinBERT frequently
  disagrees with the other two, because it measures generic sentiment rather than a
  hawkish/dovish axis. Section 2 above reproduces that exact disagreement: FinBERT rates
  Warsh-era communication as dramatically more "positive" while the purpose-built word list
  shows almost no change from Powell — the clearest single finding in this report, and one
  that would be invisible if only one of the two required methods had been used.

## 5. Forecast: the September 16, 2026 FOMC meeting

**What the evidence says heading into the meeting.** The July 29 statement drew three
dissents — Hammack, Kashkari and Logan — all wanting to hike immediately, up from zero
dissents in June: the hawks are gaining ground inside the Committee, not losing it. Both
2026 Warsh-era statements repeat the same "inflation remains elevated ... supply shocks ...
including energy" language almost verbatim, tied explicitly to the conflict in the Middle
East. The Fed funds target has sat at 3.50-3.75% since April 2026. None of that comes from
the tone regressions in Table 3 — it comes from reading the documents — which is itself a
finding: **the fundamental narrative (rising dissent, persistent inflation language, an
external energy shock) carries more information about the decision than either tone score
does**, exactly consistent with Table 3 showing tone explains very little of same-day market
moves once the decision is controlled for.

**Rate decision.**
- **Hike (+25bp, to 3.75-4.00%): 85%**
- **Hold (3.50-3.75%): 13%**
- **Cut: 2%**

These are our own probabilities, built from the dissent trend and the persistence of
"elevated inflation" language across every 2026 statement. As an external check — not the
source of the number — market-implied odds (CME FedWatch, in the days before the meeting)
were pricing in a similar range, which corroborates rather than drives this estimate.

**Statement tone.** Probability the September statement is more hawkish than July's on the
word-list score: **~55%**, close to a coin flip. The dissent trend argues for continuity or
a further rise; working against that, the word-list score itself *fell* from June (5.85) to
July (4.81) even as dissents rose — tone and voting behavior are not moving in lockstep —
and a hike itself does some of the Committee's hawkish "work," which historically tempers
the marginal wording change in the statement that follows.

**Market reaction**, probability-weighted across the three rate scenarios above (sizes are
calibrated off Table 3's 3-month-bill coefficients, scaled down because a hike is already
mostly priced in, and scaled up for the two scenarios that would be genuine surprises):

| Indicator | P(rises on the day) | Expected 1-day change |
|---|---:|---:|
| DXY | 55% | +0.04 (index points) |
| 10s2s spread | 41% | +0.00 (roughly flat, slight flattening bias) |
| 1-year yield | 49% | -0.00 (roughly flat) |
| Growth − value | 53% | +0.002 |

All four sit close to a coin flip, because the modal scenario (a hike) is already
substantially priced in — most of the potential reaction has already happened over the
weeks leading up to the meeting. The resolution of the remaining 15% probability
(hold-or-worse) is what would actually move markets on September 16.

**Recommendation.** Position for a **flatter 10s2s spread** heading into the meeting (e.g.,
short the spread, or receive 2-year / pay 10-year). This is the one relationship in Table 3
that is both economically large and highly significant — the 3-month-bill coefficient on
the 10s2s spread is -0.436 (p<0.001) — a hike mechanically pulls the front end up faster
than the back end, and that mechanical effect is far stronger than anything the tone scores
add. It also agrees with the fundamental read: rising hawkish dissent and unchanged
"elevated inflation" language both point toward the front end staying anchored higher for
longer, even if the September decision itself is small or already priced in.

**What would prove this wrong.** A hold paired with a statement whose word-list score drops
well below July's 4.81 — i.e., explicit language that inflation is cooling, not just
persisting — would point to a steepening, not a flattening, curve, and would be the signal
to exit the position. A cut would prove it decisively wrong; given the dissent trend and the
inflation language repeated in every 2026 statement, we assign that outcome only 2%
probability.

---
*Code, data-collection scripts, the scored corpus (regenerable, not checked into git) and
`analysis.ipynb` with output saved are in the accompanying GitHub repository, in
`assignment-2/`. See `AI_USE.md` for the AI-use statement.*
