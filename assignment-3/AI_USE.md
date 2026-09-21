# AI Use Statement

This assignment was completed with Claude Code (Anthropic) as a collaborative tool.
This statement describes what the AI did, what I directed and reviewed, and where
the substantive judgment calls were made — updated to cover the version 2 changes
made in response to the professor's additional guidance.

## What the AI helped with (version 1, carried forward)

- **Implementing the estimator**, the Monte Carlo validation, the data collection
  clients, and the initial notebook/report drafting — see the version 1 statement
  below for the full account of that work, which is unchanged.

## What the AI helped with in this update (version 2)

- **Diagnosing the Wikipedia sourcing problem and testing the alternative.** When I
  flagged that Wikipedia's Current Events Portal wasn't a credible source, Claude
  first tried the more rigorous fix — pulling real news-wire headlines from GDELT's
  article endpoint, restricted to only the ~36 selected days rather than the full
  258-day sample. This was tested at three different request spacings (7, 16, then
  22 seconds) with multi-pass retry logic; all three failed to reliably clear
  GDELT's throttling within the session (a sustained run at the widest spacing
  produced zero successes over five minutes). Rather than keep retrying
  indefinitely or quietly fall back to Wikipedia again, Claude reported this
  concretely and switched to targeted web searches against named, credible outlets
  (Al Jazeera, CNN, Bloomberg) for each of the 18 selected days individually,
  compiling dated summaries with source URLs into `data/news/verified_events.json`.
  I directed this as the right tradeoff given the constraints (a free-API,
  single-session pipeline with no paid news-archive access): real, checkable
  citations obtained through a manual step, clearly documented as such, rather than
  an automated pipeline stage misrepresenting an unreliable process as robust.
- **Building and running the alternative-method comparisons.** Claude implemented
  the three-regime split, the supervised/unsupervised day-classifiers, and the
  event-study regression, then ran all of them against the existing data before
  writing any conclusions. The event-study result (0/18 significant, versus
  heteroskedasticity's 13/17) and the classifier's below-random AUC were not
  anticipated outcomes I asked for — they are what the code produced, and both are
  reported in full rather than adjusted or omitted because they were surprising or
  unflattering to the pipeline.
- **The interpretation of the classifier's poor AUC** (0.43) as evidence *for* the
  news-based day-selection design, not simply a failed experiment, was Claude's
  analysis, checked by me against the underlying numbers: the market-composite label
  used to train it is built partly from the two-year yield, which the same pipeline
  had already shown barely responds to Iran-specific war risk, so a poor score
  there is a specification observation about the label, not a refutation of the
  news measure.
- **Drafting.** The expanded report, summary, and README sections were drafted by
  Claude against the computed tables and revised by me.

## What I directed and decided

- **The scope of the update**: real news sourcing, the three-regime extension, and a
  tested (not merely argued) answer to "is heteroskedasticity the best approach,"
  following the professor's guidance point by point.
- **Which alternative methods to implement versus discuss.** I asked for concrete,
  runnable comparisons rather than a purely literature-based answer — the event-study
  regression and the two day-classification methods were built and executed, not
  just cited. Methods needing data or scope this project doesn't have (a proper
  Geopolitical Risk Index needing ten newspapers' full-text archives, a full
  structural VAR across seventeen variables) were left as a literature review with
  explicit reasons, which I reviewed for whether the reasons were genuine scope
  limits rather than convenient excuses.
- **All output was inspected before use.** I checked the three-regime hypothesis-
  match claim (7/7) against the underlying Table 7 numbers by hand, verified the
  event-study's 0/18 result against Table 12's p-values directly, and read the
  vocabulary-coverage examples (Table 13) to confirm the "novel phrasing" cases were
  real quotes from the verified news text, not paraphrased or invented.
- **The verified news citations.** I did not independently re-verify every one of
  the 18 dated summaries against the original articles myself, but reviewed the
  sourcing approach (targeted, one-day-at-a-time search against three named outlets,
  URLs recorded) and consider it a legitimate improvement over the previous
  version's tertiary source, while noting in the report itself that this is a
  manual, one-time step rather than an infinitely reproducible pipeline stage — a
  limitation I asked to be stated plainly rather than glossed over.

## What I did not do

I did not ask the AI to keep retrying an unreliable data source until it produced a
result, to hide the classifier's or the event-study's unfavorable results, or to
claim the manually-sourced citations were pipeline output. Where results contradict
either the 2003 paper or an initial expectation (the classifier's below-random AUC,
the event-study's zero significant variables, the three-regime overidentification
test's 59% rather than 100% agreement), those are reported as found, with the
reasoning for why laid out rather than asserted. No data files are included in this
repository except `data/news/verified_events.json` (the hand-verified citations,
explicitly not something the scripts regenerate); everything else under `data/` is
regenerated by the scripts in `scripts/`.

---

## Version 1 statement (for reference)

This assignment was completed with Claude Code (Anthropic) as a collaborative tool.

### What the AI helped with

- **Implementing the estimator.** The Rigobon–Sack estimators in
  `src/heteroskedasticity.py` — the three instrument sets, the IV/2SLS algebra, the
  heteroskedasticity-robust standard errors, the rank-condition bootstrap and the
  variance decomposition — were written by Claude from the two papers' equations and
  then checked line by line against them. I asked for the Monte Carlo in
  `scripts/00_test_estimator.py` before trusting any of it.
- **Data collection.** The GDELT client and the market-data downloader were written
  by Claude after I specified what the analysis needed. It probed the API directly
  to work out what was actually usable, which is how the per-day article collection
  was found to be impractical for a full 258-day sweep.
- **Live research.** Because this assignment concerns events post-dating the model's
  training data, Claude used web search to establish the 2026 chronology, used only
  to check the NLP index against reality.
- **Drafting.** The notebook narrative and report were drafted by Claude against the
  computed tables and revised by me.

### What I directed and decided

- The war-risk lexicon's design (escalation/de-escalation axis, not sentiment).
- The three-component design of the news index and the decision to discard the
  *direction* of news and keep only its magnitude for day-selection.
- The decision to change the normalising variable from the two-year yield to Brent,
  and to report the failed version alongside as a finding.
- The comparison-day rule fix when the first run broke identification.
- All output was inspected before use: signs, magnitudes, and figures checked by
  hand against the underlying tables.

### What I did not do

I did not ask the AI to invent data or to produce conclusions without the underlying
numbers.
