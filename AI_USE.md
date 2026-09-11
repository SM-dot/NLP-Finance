# AI use disclosure

Required by the syllabus. One paragraph is enough. Undisclosed use is an
integrity violation; disclosed use costs you nothing.

Replace everything below.

---

**Tools used:**
Gemini, Claude 

**What I used them for:**
I initially used Gemini to generate the starter code and perform the baseline textual analysis and tf.idf scoring. I then used Claude to review and verify the outputs. However, the models initially provided incorrect results, cut off calculations midway through the notebook, and failed to follow critical instructions (such as the Table 1 firm attrition gap and the specific fixed-effect specifications required for the Table 5 volatility regressions). Because of these gaps, I adopted a hybrid approach: I wrote and executed the Python code to ensure the econometric models matched the prompt's specifications, used the models to help format the final HTML/WeasyPrint PDF report, and manually verified all tables and statistical results against the assignment instructions.

**What I wrote myself:**
I formulated the overall analytical workflow, ensuring the Loughran and McDonald (2011) tf.idf weighting and aggregation logic were correctly applied. I also wrote the statistical testing logic and the logic tracking the missing 24 firms for the Table 1 sample attrition waterfall. Finally, I orchestrated the final PDF compilation to ensure it met the requested constraints.

**Anything the model got wrong that I had to correct:**
The initial model outputs missed several core requirements of the assignment. First, it failed to account for 24 missing firms in the Table 1 waterfall (which were dropped because they were foreign private issuers, private entities, or lacked trading history). Second, the model cut off midway through generating Table 3 and completely skipped the Table 4, 5, and 6 regressions. Finally, when initially prompted to do the volatility regressions (Table 5 and Section 8), it mismatched the fixed-effect specifications by dropping quarter fixed effects in the pooled model, which I had to correct and explain so that the comparison between the pooled 10-K/10-Q sample and the separated subsamples made econometric sense.