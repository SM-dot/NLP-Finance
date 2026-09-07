# Assignment 1 report

### Uncertainty and Sentiment Analysis of Quarterly and Annual Financial Reports

FRE-GY 7871 A · NLP and the Investment Process

**Name:**
**NetID:**
**GitHub repo:**

Export to PDF and upload to Brightspace. Keep it short. Prose over bullet points where a sentence will
do; the writing is graded alongside the code.

---

## The six questions

These are also in the assignment brief on Brightspace, which is the authoritative
copy. They are repeated here because this skeleton refers to them by number.
Answer them in the sections indicated, in order, with numbers.

**Q1. What is each measure actually made of?**
From Table 3: how concentrated is each list's count, and what fraction comes from
the ten most frequent words? For uncertainty in particular, are the words driving
the count management hedging, or the standing furniture of a risk-factor section
that gets copied forward unchanged?

**Q2. Are sentiment and uncertainty measuring different things?**
Report the correlation between the two proportional measures, and again between the
two tf.idf measures. Then find a filing that scores high on one and low on the
other, and say what it looks like. If the correlation is high, say honestly how much
of the rest of your report is one result rather than two.

**Q3. Did either measure trend over 2021-2025?**
Figure 1 and Table 4. Give the direction, the size in percentage points per year,
and the t-statistic from the specification you trust, saying which that is and why.
Then say which reading of the trend your own evidence supports.

**Q4. Does uncertainty language predict volatility?**
Table 5, both specifications. Report both coefficients and explain what changed
between them and why. The difference is the answer, not either number on its own.

**Q5. Do 10-Qs behave like 10-Ks?**
Run Tables 4 and 5 separately on each form type. Then address three things: 10-Qs
are shorter and more templated, so what happens to the variance of a proportional
measure; a 10-Q lands within days of an earnings release, so is the filing-date
reaction even separately identified; and which form type should carry more textual
signal.

**Q6. Which of your results do you believe?**
Not the same question as which of them are significant. Your tests do not all have
the same power, and they do not all fail in the same direction. Go test by test.

---

## 1. What I did

The question, the corpus, and the measure, in one short paragraph. A reader who
has not seen the assignment should understand what was tested.

## 2. Data construction

Universe, sample window, forms, and every filter, with **Table 1** (the waterfall).
State the parsing decisions you made and what they cost: table-stripping threshold,
tokenisation, how many filings failed to parse, how many lost a share count.

State how you handled point-in-time: the day-0 rule, how many filings it moved,
and where your share counts came from.

## 3. Word lists

Size of each list and the overlap between them. What that overlap implies for how
independent your two measures really are.

## 4. Method

The two weighting schemes, with equation (1) written out and your reading of the
ambiguous terms. How you aggregated to quarters and what you did about form mix and
firm mix. The regression specifications and the standard errors, with a sentence each
on why you clustered the way you did and why the aggregate trend test needs
Newey-West.

## 5. What the measures are made of

**Table 2** summary statistics, 10-K and 10-Q separately, with the correlation between
the two measures. **Table 3** the thirty most frequent words on each list. Answer Q1
and Q2 here.

## 6. Trends, 2021-2025

**Figure 1** and **Table 4**. State the composition corrections you applied before
describing anything. Give the aggregate trend with both OLS and Newey-West
t-statistics, and lead with the within-firm result. Answer Q3, including which of the
two readings of the trend your own evidence supports.

## 7. Uncertainty, volatility and returns

**Table 5**, reported both with and without the pre-filing volatility control, and the
difference explained. Then **Table 6**, the return test, with the power arithmetic
stated before you interpret it. Answer Q4 and Q6.

## 8. 10-K versus 10-Q

What differs between the two form types, and whether your trend and volatility
results differ with it. Answer Q5.

## 9. Limitations

Survivorship, with a number, including the sharper version of it for the trend work:
survivors are the firms that did not blow up. Twenty quarters is a short series.
Benchmark choice. And every specification you ran, not only the one you are reporting.

## 10. What I would do next

Two or three sentences. What is the single change that would most improve this
test, and what would it cost?
