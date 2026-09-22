# Measuring the Effect of Iran War Risk on Global Financial Markets

**FRE-GY 7871 A · NLP and the Investment Process · Fall 2026**

## Key takeaways

- A war-risk shock large enough to move oil up $5 a barrel knocks about 0.65% off
  the S&P 500 — but 1.4-1.7% off European, Japanese and emerging-market equities.
  The United States is now insulated relative to the rest of the world in a way it
  was not in 2003, because it is a much larger oil producer.
- Credit widens, volatility rises, and the dollar and Swiss franc both strengthen —
  a conventional flight-to-safety pattern in currencies and credit, layered on top
  of an oil shock that behaves very differently from the 2003 Iraq-war episode.
- The critical break from 2003: Treasury yields and inflation expectations **rise**
  with war risk in 2026, where they fell in 2003. This is the signature of a
  supply-side shock (more oil-dependent inflation) rather than a demand-side scare,
  and it lines up with the structural shift in US energy production since then.
- The identification strategy was tested against the most obvious simpler
  alternative — a plain regression on "was this a big war-news day, yes or no" —
  and that alternative found nothing. Every one of eighteen markets came back
  statistically indistinguishable from zero. The variance-based approach used here
  found reliable effects in thirteen of seventeen. That gap is the strongest
  evidence in this analysis that the more involved method is earning its keep, not
  just adding complexity.
- A few readings should be treated with real caution rather than taken at face
  value: gold, Tel Aviv equities, and defence stocks all rest on a weaker piece of
  the statistical machinery and move around noticeably depending on exactly how the
  analysis is run. Everything else — equities, credit, oil, the VIX, the dollar,
  Treasury yields — holds up under several different ways of stress-testing it.

## Why war risk needs a different kind of measurement

Nobody publishes a daily "probability of war" number, so there is no series to put
directly into a regression. What can be observed is *when* war-related news was
unusually intense. Rigobon and Sack's 2003 study of the Iraq war turned that
limitation into a method: split trading days into a group where war-related news
was heavy and a matched group where it was quiet, and see how much more markets
moved around — not on average, but in dispersion — in the heavy-news group. If
every other driver of prices was no more volatile on those days than usual, the
extra dispersion is attributable to the war-risk factor alone, and its size can be
recovered without ever assigning a number to "risk" itself.

The appeal for this kind of analysis is that it does not require knowing whether a
given day's news was good or bad for markets — only that it was voluminous and
uncertain. That matters a great deal here: of the eighteen days flagged as unusually
newsy over the sample, six carried heavy coverage that was genuinely split between
escalation and de-escalation at once. A method that needed a signed input would have
to throw those days out or guess at their direction. This one does not.

## Building the signal from the news

Every trading day between January and mid-September 2026 gets a single flag — high
war-news day or not — built from GDELT's coverage of Iran-related reporting: how
much coverage there was relative to its own recent baseline, how far the balance of
escalation-versus-de-escalation language moved, and how contested that balance was
on a given day. Eighteen of 173 trading days clear the bar, roughly the top decile,
comparable in scale to the seventeen days Rigobon and Sack identified by hand for
Iraq. A matched set of eighteen quiet days, chosen to sit as close in time as
possible without themselves being newsy, anchors the comparison.

Sourcing real reporting to describe what happened on those eighteen days turned out
to be harder than expected. GDELT's own article-level search does index real
outlets — the underlying feed carries publisher domains like reuters.com and
aljazeera.com — but a systematic attempt to pull headlines through it, tested at
several request speeds with generous retry logic, could not reliably get through
its rate limiting within a session. Rather than fall back on a tertiary source like
an encyclopedia's own event summary, each of the eighteen days below was checked by
hand against dated Al Jazeera, CNN and Bloomberg reporting, with a source link kept
for every entry. That verification runs after the day-selection is already
finished — the flagging itself never sees this text — so it changes only what gets
printed next to each date, not which days were chosen or any of the results that
follow.

## The eighteen days that defined the war-risk narrative

**Table 1. War-news days selected by the news index** (18 of 173 trading days, top
decile; the Brent and two-year-yield columns are shown for context and were not used
to pick the days)

| Date | War risk | News score | ∆Brent ($) | ∆2y (bp) | Source | Event |
|---|---|---:|---:|---:|---|---|
| 2026-03-02 | Increased | 3.48 | +5.26 | +9.0 | CNN/Al Jazeera | US/Israel strike Natanz enrichment complex; Iran closes Strait of Hormuz |
| 2026-03-03 | Increased | 2.38 | +3.66 | +4.0 | Al Jazeera | Massive explosions in Tehran, Karaj, Isfahan; IRGC says ground forces engaged |
| 2026-03-04 | Increased | 2.06 | +0.00 | +3.0 | CNN | US says Iran's air force/navy "knocked out"; >1,000 killed in Iran |
| 2026-03-05 | Increased | 1.65 | +4.01 | +3.0 | CNN | Iran fires drone/missile barrage at Tel Aviv; Brent +24% on the week |
| 2026-03-06 | Increased | 1.01 | +7.28 | −1.0 | Al Jazeera | US warns Iran hit "very hard"; >3,000 targets struck in past week |
| 2026-03-09 | Increased | 1.37 | +6.27 | 0.0 | Al Jazeera | Iran names Mojtaba Khamenei Supreme Leader; Brent hits $119.50 |
| 2026-03-24 | Unclear | 1.24 | +4.55 | +7.0 | Al Jazeera/CNN | Talks claimed underway; Tehran calls it "fake news" |
| 2026-03-25 | Unclear | 1.35 | −2.27 | −6.0 | Al Jazeera | Oil tumbles, stocks rally on peace-plan reports; Iran rejects it |
| 2026-03-26 | Unclear | 1.19 | +5.79 | +12.0 | CNN | Energy-site strikes held off 10 more days as "talks ongoing"; worst month for US stocks |
| 2026-03-30 | Increased | 0.78 | +0.21 | −6.0 | Al Jazeera | Threat to obliterate energy infrastructure if no deal reached |
| 2026-04-06 | Increased | 0.86 | +0.74 | +5.0 | CNN | Deadline set to reopen Hormuz; 45-day ceasefire proposal rejected |
| 2026-04-08 | Unclear | 1.31 | −14.52 | −2.0 | Al Jazeera/CNN | Pakistan-brokered 2-week ceasefire; Iran agrees to reopen Hormuz |
| 2026-04-09 | Decreased | 0.94 | +1.17 | −1.0 | Al Jazeera | IRGC claims Hormuz shipping stopped again; fire at Aramco's Abqaiq facility |
| 2026-04-10 | Decreased | 0.73 | −0.72 | +3.0 | CNN | Hormuz to reopen "soon, with or without" Iran; polls doubt the win |
| 2026-04-13 | Decreased | 1.31 | +4.16 | −3.0 | Al Jazeera/CNN | Blockade of all Iranian ports begins after talks collapse |
| 2026-06-15 | Decreased | 0.77 | −4.16 | −2.0 | Bloomberg | Oil sinks >5% on interim deal to reopen Hormuz |
| 2026-07-08 | Unclear | 1.04 | +3.86 | +2.0 | Al Jazeera/CNN | Iran warns of "crushing response"; strikes 85 US targets in Bahrain/Kuwait |
| 2026-07-13 | Unclear | 0.85 | +7.29 | +5.0 | CNN/Al Jazeera | Strikes resume 2nd night; Iran disables 2 tankers; WTI +9.4% |

Eight of the eighteen days lean escalatory, four lean toward de-escalation, and six
carry heavy coverage that is genuinely split — the sort of day a conventional event
study cannot use. The list is not evenly spread across the sample: nearly half of it
falls in March alone, the month of the most intense fighting, with a second cluster
around the April ceasefire and two isolated flare-ups later in the summer when the
truce broke down over shipping through the Strait of Hormuz.

Nothing about the actual timeline of the war was given to the scoring process — it
only ever sees coverage volume and the balance of escalation-versus-de-escalation
language. Plotting the resulting index against the level of Brent crude and the
two-year Treasury yield over the same window is therefore a useful sanity check
rather than a formality: the index's single sharpest spike lands on February 28, the
day the war began, and it climbs from a quiet, slightly negative baseline through
January and February into a dense, elevated cluster through March before tapering
off after the April ceasefire. Brent's price level climbs steadily across that same
window; the two-year yield moves in a visibly choppier, less obviously war-linked
pattern — an early clue, well before the formal identification test below, that oil
is carrying this episode's risk signal far more cleanly than the Treasury market is.

![Figure 1](figures/figure1_war_news_index.png)

## What a war-risk shock does to markets, asset by asset

The eighteen flagged days are matched against the eighteen quiet comparison days,
and the difference in how much each market moved translates into a sensitivity
estimate, scaled here to a war-risk increase large enough to push Brent up $5 a
barrel — the same instrument Rigobon and Sack used for the two-year yield in 2003,
substituted here because the two-year yield turns out not to respond distinctly
enough to Iran-specific risk to serve that role in 2026 (more on that below).

**Table 2. Estimated market response to a war-risk shock that raises Brent $5/bbl**

| Variable | Units | Coefficient | t-stat | Sig. |
|---|---|---:|---:|---|
| Two-year Treasury yield | pp | 0.018 | 1.68 | * |
| Ten-year Treasury yield | pp | 0.019 | 2.28 | ** |
| Break-even inflation (10y) | pp | 0.014 | 3.45 | *** |
| S&P 500 | pct | −0.650 | −2.96 | *** |
| BBB yield spread | pp | 0.008 | 2.91 | *** |
| High-yield yield spread | pp | 0.048 | 3.61 | *** |
| Gold price | $ | −36.63 | −1.90 | * |
| Dollar (broad index) | pct | 0.257 | 3.24 | *** |
| VIX | pts | 1.748 | 3.72 | *** |
| Euro Stoxx 50 | pct | −1.370 | −4.47 | *** |
| Nikkei 225 | pct | −1.649 | −3.28 | *** |
| Tel Aviv 125 | pct | 0.069 | 0.10 | |
| MSCI EM equities | pct | −1.651 | −3.45 | *** |
| Swiss franc per dollar | pct | 0.237 | 2.36 | ** |
| US energy equities (XLE) | pct | 0.958 | 3.17 | *** |
| US airlines (JETS) | pct | −1.359 | −2.83 | *** |
| Aerospace & defence (ITA) | pct | −0.554 | −1.01 | |

Thirteen of seventeen coefficients clear conventional significance at 5% —
plotting the same numbers as point estimates with confidence bands makes the shape
of the result easier to take in at once than the table does.

![Figure 3](figures/figure3_coefficients.png)

**Equities fall everywhere, and fall roughly twice as hard outside the United
States.** The S&P gives back 0.65% for a $5 oil shock; Europe, Japan and emerging
markets all lose 1.4-1.7%, more than double the US move. That gap is the clearest
single number in this analysis, and it is a structural story rather than a
sentiment one: the United States pumps roughly 14 million barrels of oil a day
today, against roughly 6 million in 2003, so a war-driven spike in oil prices is
now a mixed blessing for the US economy rather than a uniformly negative one. That
shows up directly inside the US market too — energy stocks are the only positive
line in the whole table, up 0.96%, while airlines, which eat the same oil-price
increase on the cost side, lose 1.36%.

**Credit widens in proportion to risk, not uniformly.** High-yield spreads move six
times as far as investment-grade spreads (4.8 basis points versus 0.8), which is
what a genuine risk repricing should look like rather than a blanket move in credit
markets. The VIX adds close to 1.75 points, a real but not extreme jump in implied
volatility for a shock of this size.

**The break from the 2003 playbook shows up in rates, inflation, and the dollar.**
In the run-up to the Iraq war, all three of those fell together as investors priced
war risk as a threat to growth: money moved into safe government debt, inflation
expectations eased, and the dollar weakened. Here, all three do the opposite — the
ten-year yield rises, break-even inflation rises, and the dollar strengthens (with
the Swiss franc rising alongside it, so this reads as a broad flight to currencies
seen as safe rather than a dollar-specific story). The read is that 2026's war risk
is being priced primarily as a threat to oil *supply* — inflationary, and, given the
scale of the domestic energy sector, less of a pure flight-to-safety trigger for the
dollar than it was in 2003.

**Two results are worth flagging as non-findings rather than findings.** Gold shows
no reliable response (its point estimate is even the wrong sign, and its confidence
interval comfortably spans zero) — which echoes Rigobon and Sack's own 2003 result
and is a useful corrective to the assumption that gold reliably behaves as a war
hedge. Tel Aviv equities also show no statistically reliable response, despite
moving around noticeably more than usual on the flagged days — a distinction worth
sitting with for a moment, because it recurs below: being volatile on newsy days and
being *driven by the shared war-risk factor other assets share* are not the same
thing, and Tel Aviv is the cleanest example of a market where the first is true and
the second is not.

## How much of the story is war risk, and how much is everything else

Not every point of volatility on a newsy day is attributable to the war. The share
that is can be estimated by comparing how much extra variance each market carries on
the eighteen flagged days against how much of that extra variance the shared
war-risk factor alone can explain.

**Table 3. Share of variance attributable to the war-risk factor**

| Variable | Share of variance, war-news days | Share of variance, full sample |
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
| Swiss franc | 20.4% | 2.4% |
| Ten-year Treasury yield | 16.8% | 2.0% |
| Gold price | 15.9% | 1.6% |
| Two-year Treasury yield | 12.5% | 1.4% |
| Aerospace & defence | 8.0% | 1.3% |
| Tel Aviv 125 | 0.1% | 0.0% |

On the flagged days themselves, war risk accounts for roughly half of everything
moving European equities and the VIX, and a sizeable chunk of the dollar, emerging
markets and credit spreads. Stretched over the full eight-month sample, where most
days are ordinary trading days, those shares compress to a more modest but still
material 8-17% for the same markets — a reasonable order of magnitude for a single
geopolitical factor operating alongside everything else that normally moves prices.
These figures should be read as floors rather than precise numbers: the quiet
comparison days are not perfectly war-news-free in a conflict that ran for six
months, which understates the true share attributable to the war.

The underlying variance ratios behind this table are worth looking at directly,
because they explain a methodological choice made earlier in this analysis: oil's
variance is 6.2 times higher on war-news days than on quiet ones, the VIX's 4.7
times, and Tel Aviv's 3.6 times — but the two-year Treasury yield comes in at just
1.05 times, and the ten-year actually shows *less* variance on war-news days than on
ordinary ones. That is the concrete reason Brent, not the two-year yield, anchors
the estimates above: in the 2003 study the two-year yield was the cleanest available
barometer of war risk, with variance rising more than sixfold on war-news days, but
that role has effectively moved to oil in this episode.

![Figure 2](figures/figure2_variance_ratio.png)

The Tel Aviv result from the previous section becomes clearer against this
backdrop. Its variance ratio (3.6×) is the third-highest of any market in the
sample — genuinely much noisier on war-news days — yet the share of that noise
attributable to the shared factor is essentially zero. Put together, the two
numbers say that Israeli equities move a great deal on days when the war escalates,
but for reasons specific to Israel (local political and economic news tied
directly to the fighting) rather than through the same oil-and-risk-sentiment
channel that moves the S&P, European equities, and credit spreads together.

## Stress-testing the approach

A method this specific to the problem is worth checking against simpler
alternatives before trusting its output. Three checks were run.

**The most obvious alternative — a plain regression of each market's daily move on
the same high-news-day flag — comes back empty.** Run as a straightforward test of
"is the average move different on flagged days versus not," it finds zero of
eighteen markets significant at the 5% level. The variance-based approach, on the
identical eighteen days, finds thirteen of seventeen. The reason for the gap is not
subtle once you look at the eighteen days themselves: eight lean escalatory and four
lean toward de-escalation, so a market that genuinely moves in opposite directions on
bad-news versus good-news days has those moves cancel out in a simple average,
pushing the estimated effect toward zero regardless of how real the underlying
sensitivity is. Variance does not cancel the same way — a $5 up-move and a $5
down-move both add to dispersion — so the shared factor survives averaging even when
its sign flips from day to day. This is the single clearest piece of evidence that
the more involved method earns its complexity here rather than adding it for its own
sake.

**Splitting the flagged days by direction confirms the intuitive story with nothing
more than simple averages.** Separating the eighteen days into those where coverage
leaned escalatory, those where it leaned toward de-escalation, and comparing both
against the quiet days, seven markets checked — two-year and ten-year yields, oil,
the S&P, Euro Stoxx, the VIX, and high-yield spreads — all move in the expected
direction on bad-news days (yields, oil and volatility up, equities down) and mostly
reverse on good-news days.

![Figure 6](figures/figure6_regime_comparison.png)

A stricter version of this check — estimating the sensitivity separately from the
bad-news days and separately from the good-news days, and asking whether the two
estimates agree in sign despite pulling from sub-samples with opposite average news
direction — agrees on ten of seventeen markets. That is a noisier result, unsurprising
given the sub-samples run to only four and eight days each, but it belongs in the
record alongside the cleaner seven-for-seven finding above rather than being left out
because it is less tidy.

**Letting a model, rather than a fixed rule, decide which days count as newsy
produces a genuinely mixed result — and the reason why is itself informative.** A
cross-validated classifier was trained to predict an independent, market-based
definition of a high-stress day using only the news features (no price data was
used in training). Its accuracy came back worse than a coin flip. Digging into why
turns out to reinforce the main approach rather than undercut it: the market-based
label used to train the classifier was built from a broad basket of assets that
includes the two-year yield — and the two-year yield, as established above, barely
responds to Iran-specific risk at all. A label partly built from a market that
doesn't respond to this particular risk factor will naturally be dominated by other,
unrelated sources of volatility (Fed decisions, data releases, and so on), and on
those days Iran-specific news coverage is, unsurprisingly, not elevated. Only 3 of
the 18 days flagged by news content overlap with the 18 days flagged by market
stress — which is really a demonstration of why selecting days from the news itself,
rather than from realized price moves, is the right design for isolating this
specific risk: a price-based selection rule would have been contaminated by
everything else that moves markets, not just Iran.

![Figure 4](figures/figure4_classifier_diagnostics.png)

Re-running the core estimates using the classifier's own day-selection, and
separately using an unsupervised clustering that never saw price data at all,
confirms that the equity and credit results are not an artifact of exactly how the
newsy-day threshold was drawn — those signs and rough magnitudes hold up across all
three approaches. The VIX and the dollar are more sensitive to the choice of
day-set and should be read with a little more caution than the rest of the table.

![Figure 5](figures/figure5_method_comparison.png)

## What the word list misses

The escalation/de-escalation language used to score news coverage is a fixed list
built in advance, and a live, fast-moving conflict generates vocabulary no fixed
list can anticipate — named agreements, facility names, invented shorthand.
Checking the verified news text sentence by sentence against that list finds that
52.5% of sentences plainly about the war — describing strikes, blockades,
casualties, and ceasefire terms — register zero matches. "Natanz nuclear
enrichment complex" scores nothing because the list has no place-name knowledge at
all; "rogue supertankers," a phrase this specific conflict's coverage invented,
was never going to be on any pre-built list; the "memorandum-of-understanding
ceasefire" names an agreement that did not exist before this war began.

This limitation sits at the sentence level and does not undermine the day-selection
itself, which runs on aggregate coverage volume rather than phrase-matching — a
spike in Iran-related reporting is detected whether or not any particular sentence
uses recognized vocabulary. Where it does show up is in anything relying on the
word list's read of a specific sentence's direction, which is part of why the
word-list and a general-purpose language-model sentiment score agree only weakly at
that fine-grained level even though they track each other reasonably well in
aggregate. A language model reading the text directly, rather than counting
phrases against a fixed list, would sidestep this — it does not need "Abqaiq" or
"supertanker" pre-registered to understand what they mean in context — though
building that as a full automated step was outside the scope of what could be
tested and verified here.

## Other frameworks worth knowing about

A handful of other established approaches could, in principle, answer a version of
this question, and each was set aside for a specific reason rather than
overlooked.

| Approach | What it does | Why it wasn't used here |
|---|---|---|
| Geopolitical Risk Index (Caldara & Iacoviello, 2018) | Counts geopolitical-risk articles across ten major newspapers into a continuous index | Answers a related but different question — a risk *level*, not the variance shift this analysis is built around — and needs full-text access to ten specific papers that free data sources don't provide |
| Economic Policy Uncertainty Index (Baker, Bloom & Davis, 2016) | Same keyword-counting methodology, applied to policy uncertainty generally | Same limitation as above |
| Markov-switching volatility models (Hamilton, 1989) | Lets returns alone determine regime membership, with no news input at all | The market-only alternative already tested here (the unsupervised clustering) shows that a market-only day-classification is close to uninformative about Iran-specific risk by construction, for the same reason a return-only switching model would be |
| Structural VAR with sign restrictions (Uhlig, 2005) | Identifies the shock through theoretically motivated restrictions on how variables can respond, rather than through variance shifts | Requires specifying a full system and defensible restrictions across seventeen variables at once — a substantially larger undertaking that trades one set of assumptions for another rather than avoiding assumptions |
| Direct language-model scoring | Reads each day's text and outputs a calibrated severity score rather than counting fixed phrases | The natural fix for the vocabulary gap above; not built as a full pipeline here given the added cost and scope of running a model call per day across the sample |

None of these are worse ideas — the Geopolitical Risk Index in particular is a
well-established, Fed-published methodology. Each simply answers a different
question, or needs data this analysis's free, single-session data sources could not
supply.

## A different war than 2003

The 2003 episode offers a natural benchmark, and one deliberate reason to expect a
break from it: US crude output has roughly doubled and then some since then, from
around 6 million barrels a day to around 14 million, which changes how a
war-driven oil shock feeds through the domestic economy.

| | 2003 (Rigobon-Sack) | 2026 (this analysis) | Consistent with the shift? |
|---|---|---|---|
| Oil | Rises | Rises (variance 6.2x higher on war days) | Yes |
| Credit spreads | Widen | Widen (high yield +4.8bp, investment grade +0.8bp) | Yes |
| Equities | Fall | Fall (S&P −0.65%, more abroad) | Yes |
| Gold | No significant response | No significant response | Yes |
| Treasury yields | Fall (−26bp on the ten-year) | Rise (+1.9bp on the ten-year) | No — as expected |
| Break-even inflation | Falls | Rises | No — as expected |
| Dollar | Falls | Rises | No — as expected |

Every leg that was expected to hold steady with 2003 held; every leg expected to
flip, flipped. The US-outperformance pattern in equities, and energy stocks moving
with rather than against the broader market, is the same story told at the sector
level: a much larger domestic oil industry turns a war-driven price spike from a
uniformly negative shock into a genuinely mixed one for the US economy, which is
consistent with yields rising on an inflation-and-growth read rather than falling on
a pure flight-to-safety read the way they did when the 2003 shock was seen purely as
a threat to demand.

## Reading the caveats

A few limitations should travel with every number above. The core assumption behind
the whole exercise — that nothing *other* than war risk was unusually volatile on
exactly the eighteen flagged days — cannot be independently proven, only checked for
plausibility, and the stability of the results when the day-count is widened or
narrowed is reassuring on that front without being conclusive. The quiet comparison
days are not perfectly free of war-related news in a conflict that ran six months,
which biases the variance-share numbers in the earlier table downward, so they are
best read as floors. "War risk" here is a single estimated factor standing in for
several distinct things at once — the odds of further escalation, how long the
conflict runs, how much of the Strait of Hormuz stays open — bundled together rather
than separated out. The sample itself is small, eighteen days on each side, which
leaves four of the seventeen coefficients (gold, Tel Aviv, defence stocks, and to a
lesser extent the dollar) resting on weaker statistical footing than the rest and
worth treating with real caution. And the eighteen event descriptions in the table
above are a hand-verified research step rather than something the automated pipeline
regenerates on its own — a genuine change in which days get flagged would need that
verification redone.

## References

- Rigobon, R. and B. Sack (2003), "The Effects of War Risk on U.S. Financial
  Markets," NBER Working Paper 9609.
- Rigobon, R. (2003), "Identification through Heteroskedasticity," *Review of
  Economics and Statistics* 85(4), 777–792.
- Caldara, D. and M. Iacoviello (2018), "Measuring Geopolitical Risk," *American
  Economic Review*, Federal Reserve Board working paper series.
- Baker, S., N. Bloom and S. Davis (2016), "Measuring Economic Policy Uncertainty,"
  *Quarterly Journal of Economics* 131(4), 1593–1636.
- Hamilton, J. (1989), "A New Approach to the Economic Analysis of Nonstationary
  Time Series and the Business Cycle," *Econometrica* 57(2), 357–384.
- Uhlig, H. (2005), "What Are the Effects of Monetary Policy on Output? Results
  from an Agnostic Identification Procedure," *Journal of Monetary Economics*
  52(2), 381–419.
- News data: GDELT Project DOC 2.0 API (day-selection); Al Jazeera, CNN and
  Bloomberg (event verification, with source URLs in
  `data/news/verified_events.json`).
- Market data: FRED (Federal Reserve Bank of St. Louis) and Yahoo Finance.
