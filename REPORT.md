# Assignment 1 report

### Uncertainty and Sentiment Analysis of Quarterly and Annual Financial Reports

FRE-GY 7871 A · NLP and the Investment Process

**Name:** Syonaa Mehra  
**NetID:** sm13644 
**GitHub repo:** https://github.com/SM-dot/NLP-Finance

---

## The six questions

**Q1. What is each measure actually made of?**  
From Table 3, word frequencies are heavily skewed by Zipf's law. The ten most frequent negative words account for 27.4% of the total negative count, representing a balanced mix of operational losses (`LOSS`, `LOSSES`), adverse business impacts (`ADVERSELY`, `ADVERSE`, `HARM`), and legal/regulatory frictions (`CLAIMS`, `AGAINST`, `LITIGATION`). In contrast, uncertainty is overwhelmingly dominated by boilerplate structure: the top ten uncertainty words account for 78.1% of the total count, with just two modal verbs (`MAY` at 37.5% and `COULD` at 20.7%) driving over half of all occurrences. These modal terms represent the standing furniture of routine risk-factor safe harbors copied forward unchanged across quarters rather than active, dynamic managerial hedging.

**Q2. Are sentiment and uncertainty measuring different things?**  
The cross-sectional correlation between proportional sentiment and uncertainty shares is 0.889, and between tf.idf measures is 0.935. Despite this high collinearity, they capture distinct economic dimensions: level versus dispersion. For instance, DraftKings (DKNG) Q3 2024 Form 10-Q scored in the 99th percentile of negative sentiment (share = 5.04%) due to severe legal and regulatory penalties, but only in the 38th percentile of uncertainty (share = 1.64%), reflecting definitive disclosures of operational headwinds rather than abstract hedging. Because the correlation is high, approximately 80% to 85% of the aggregate cross-sectional variance reflects general corporate risk-disclosure intensity, making separation via term-weighting and firm fixed effects essential.

**Q3. Did either measure trend over 2021–2025?**  
Evaluating Figure 1 and Table 4 requires separating form types to avoid calendar sawtooth artifacts from Q1 10-K clustering. In aggregate OLS with Newey-West HAC standard errors (maxlags = 4) and within-firm panel regressions (clustered by firm), Form 10-Ks exhibited a statistically significant upward drift in negative sentiment (+0.076 percentage points/year within-firm, $t = 9.74$) and uncertainty (+0.036 pp/year within-firm, $t = 6.95$). Conversely, Form 10-Qs exhibited a mild downward trend (sentiment: -0.034 pp/year, $t = -2.01$; uncertainty: -0.025 pp/year, $t = -2.56$). The evidence supports structural expansions in mandatory annual risk disclosures (e.g., cybersecurity, supply chain resilience) counterbalanced by quarterly streamlining.

**Q4. Does uncertainty language predict volatility?**  
Table 5 demonstrates that without pre-filing volatility, pooled OLS specifications yield near-zero coefficients. When pre-filing realized volatility ($\text{vol\_pre}$) is included as a control, the coefficient on uncertainty tf.idf remains economically negligible ($\beta = -0.000053$, $t = -0.064$), while historical volatility dominates ($\beta \approx 0.724$, $t > 18.0$, $R^2 = 0.7386$). The difference proves that uncertainty language does not predict a change in volatility once baseline firm risk is absorbed; volatile firms simply write more hedged disclosures.

**Q5. Do 10-Qs behave like 10-Ks?**  
When estimating volatility regressions separately by form type, Form 10-Qs reveal a positive, statistically significant relationship between uncertainty tf.idf and post-filing volatility ($\beta = +0.0040$, $t = 2.11$, $N = 1,143$), whereas Form 10-Ks do not ($\beta = +0.0053$, $t = 1.23$, $N = 374$). Form 10-Qs exhibit more than double the proportional cross-sectional standard deviation (0.0066 vs. 0.0026 in 10-Ks) because annual 10-Ks are heavily scrubbed by legal counsel into standardized boilerplate, whereas 10-Qs capture timely, interim operational shifts that forecast earnings volatility.

**Q6. Which of your results do you believe?**  
We believe the within-firm trend tests (Table 4) and the Form 10-Q volatility results (Section 8) because they leverage panel fixed effects and possess adequate statistical power within the sample. Conversely, we interpret the null result in Table 6 (filing-period excess return on sentiment: $\beta = -0.000148$, $t = -1.460$, $N = 1,517$) as a consequence of low statistical power. With $N = 1,517$, 4-day announcement returns are overwhelmed by contemporaneous earnings surprises; a null result here is expected and correct, not evidence that sentiment lacks economic content.

---

## 1. What I did
This study evaluates corporate disclosure tone across SEC Form 10-K and 10-Q filings from 2021 to 2025 for 93 operating companies held across ARK Invest active ETFs. Following Loughran and McDonald (2011), the analysis measures textual sentiment (bad news via financial negative words) and uncertainty (managerial hedging via imprecision words) using both proportional shares and tf.idf weighting. We examine summary statistics, lexical concentration, time-series trends, and test whether disclosure tone predicts post-filing stock volatility and announcement-period returns.

## 2. Data construction
The universe originates from 130 raw holding entries across six ARK ETFs (ARKK, ARKQ, ARKW, ARKF, ARKG, ARKX), resolving to 117 SEC-registered filers. Exactly 24 firms were excluded as foreign private issuers filing Form 20-F/40-F, private entities, or recent listings without continuous 2021–2025 history, leaving 93 domestic operating filers and 1,702 downloaded filings. 

Applying assignment filters yielded 1,585 viable filings:
* **Table 1 Waterfall:** Initial raw filings ($N = 1,702$) $\rightarrow$ Drop amendments ($N = 1,702$) $\rightarrow$ Minimum word threshold ($N = 1,702$) $\rightarrow$ One filing per firm-calendar quarter ($N = 1,688$) $\rightarrow$ Usable Day 0 and price at $t-1 \ge \$3.00$ ($N = 1,585$) $\rightarrow$ $\ge 60$ trading days before/after ($N = 1,585$).
* **Parsing & Point-in-Time:** Tables and exhibits were stripped to prevent boilerplate safe-harbor contamination. Day 0 was defined as the first trading day on or after the filing date, adjusted forward for acceptances at or after 16:00 ET (shifting 948 filings, or 56.2%). Share counts printed directly on each filing were merged via `accession` numbers to ensure point-in-time accuracy.

## 3. Word lists
We utilize the Loughran-McDonald Master Dictionary (2,355 Fin-Neg words and 297 Fin-Unc words). The overlap is restricted to 40 words (1.7% of negative and 13.5% of uncertainty), confirming that sentiment and uncertainty capture distinct linguistic constructs despite high cross-sectional collinearity.

## 4. Method
We score filings using proportional token share and tf.idf weighting (Loughran & McDonald 2011, eq. 1). Term frequencies are adjusted by document length using $a_j$ (total words over distinct words) and downweighted for ubiquitous terms using inverse document frequency ($\ln(N / df_i)$). The tf.idf self-check confirmed accurate implementation across three test documents (d1: 0.8480, d2: 0.2885, d3: 0.5026). Quarterly aggregation was performed separately by form type. Panel regressions utilize OLS with Newey-West HAC standard errors (maxlags = 4) for aggregate trends to account for autocorrelation, and firm-clustered standard errors with firm and quarter fixed effects for asset pricing tests to isolate within-firm variance.

## 5. What the measures are made of
Table 2 summary statistics show 10-Ks carry higher mean proportional sentiment (2.55% vs. 2.16%) and uncertainty (2.11% vs. 1.93%) than 10-Qs, while 10-Qs exhibit higher cross-sectional dispersion. Table 3 confirms Zipf's law concentration: top-10 negative words represent 27.4% of sentiment, while top-10 uncertainty words represent 78.1% of uncertainty, dominated by modal verbs `MAY` (37.5%) and `COULD` (20.7%). Questions Q1 and Q2 are addressed above.

## 6. Trends, 2021–2025
Figure 1 separates 10-K and 10-Q trends to eliminate calendar seasonality. Table 4 reports aggregate slopes (10-K sentiment: +0.0575 pp/yr, OLS $t = 2.11$, NW $t = 4.72$; within-firm sentiment: +0.0762 pp/yr, clustered $t = 9.74$). Question Q3 is addressed above.

## 7. Uncertainty, volatility and returns
Table 5 shows that uncertainty tf.idf loses predictive power on post-filing volatility ($\beta = -0.000053$, $t = -0.064$) once pre-filing volatility is controlled for ($\beta = 0.724$, $t > 18.0$). Table 6 reports the 4-day announcement return regression ($\beta = -0.000148$, $t = -1.460$, $N = 1,517$). Questions Q4 and Q6 are addressed above.

## 8. 10-K versus 10-Q
Section 8 highlights that Form 10-Q uncertainty successfully forecasts subsequent volatility ($\beta = +0.0040$, $t = 2.11$) due to higher cross-sectional variance and timely operational disclosures, whereas 10-Ks are legally scrubbed and templated. Question Q5 is addressed above.

## 9. Limitations
Survivorship bias affects the sample, as bankrupt or delisted firms are implicitly excluded. Furthermore, the 20-quarter window is relatively short for macro-trend analysis. Our 4-day event window regressions also capture noisy concurrent earnings disclosures that land alongside 10-K/10-Q filings, which heavily attenuates the linguistic signal. Finally, alternative specifications explored the pooling of form types, which artificially inflated statistical significance due to seasonality artifacts.

## 10. What I would do next
Future analysis would be improved by parsing specific subsections—specifically Item 7 MD&A and Item 1A Risk Factors—independently rather than analyzing full-document text. This would isolate managerial narrative shifts from mandatory boilerplate disclosures at minimal computational cost.