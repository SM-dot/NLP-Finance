# The Iran War and Global Markets: A Plain-Language Summary

**What this project measures:** how much the Iran war has actually moved markets in
2026, using a method that turns news headlines into a number a computer can measure
against.

## The problem we're solving

Everyone agrees that news about the Iran war moves markets — oil jumps when there's a
strike, stocks wobble when there's a ceasefire scare. But "war risk" isn't a number you
can look up anywhere. Nobody publishes a "probability of war" index. So how do you put a
number on something nobody measures directly?

The trick, borrowed from a 2003 academic paper (Rigobon and Sack, written about the
lead-up to the Iraq war) is this: you don't need to measure war risk itself. You just
need to know **which days had unusually intense war news** and which days didn't. If you
can identify those two groups of days, you can watch how much *more* markets moved on the
noisy days compared to the calm days, and that difference tells you how sensitive each
market is to war risk — without ever having to put a number on "risk" itself.

The 2003 paper did this by hand: the authors literally read newspapers for ten weeks and
wrote down which 17 days felt like the big ones. Our project does that same
day-picking step automatically, using an NLP program that reads a running measure of
how much war coverage there was and whether that coverage was mostly "things are
escalating" or "things are calming down."

## How we picked the "big news" days

We built a program that tracks, for every day in 2026, how much English-language news
coverage mentioned the Iran war, and whether that coverage leaned toward escalation
words (strike, missile, blockade, ultimatum) or de-escalation words (ceasefire, talks,
agreement, truce). A day scores high on our "war-news index" if:

1. Coverage spiked well above its recent normal level, **and**
2. The escalation/de-escalation balance swung hard in one direction, **or**
3. The coverage was heavy on *both* escalation and de-escalation stories at once — a
   day where the news is genuinely confusing counts as a big news day too, since
   uncertainty itself is what moves markets.

We didn't have to tell the program any real dates. As a sanity check, we looked at what
it found on its own, and it lined up with what actually happened:

- The single biggest news day it found is **February 28, 2026** — the day the US and
  Israel actually struck Iran.
- Coverage specifically about the Strait of Hormuz (the oil chokepoint) peaked on
  **April 8, 2026** — the day of a two-week ceasefire that reopened it.
- The calmest, most conciliatory news days it found cluster around **June 16–17,
  2026** — when the US and Iran signed a memorandum aiming to end the war.

That match, found without us pointing the program at those dates, is what gives us
confidence the index is measuring something real rather than noise.

Out of 173 trading days from January through mid-September, the program picked **18**
as unusually high-news days (the top 1-in-10), and matched each one to a calmer
comparison day nearby.

## What we found

Using those 18 "big news" days versus their calm-day matches, here's what moves and by
how much, for a war-risk jump big enough to push oil (Brent crude) up about $5 a
barrel:

**Stocks fall — and fall harder outside the US.**
- S&P 500 (US): down about **0.65%**
- Euro Stoxx 50 (Europe): down about **1.37%**
- Nikkei 225 (Japan): down about **1.65%**
- Emerging markets: down about **1.65%**

US stocks fall the least. That makes sense: the US produces a lot of its own oil now,
so a spike in oil prices hurts US companies less than it hurts oil-importing regions
like Europe and Japan.

**Inside the US stock market, energy and airlines move in opposite directions**, which
is exactly what you'd expect from an oil shock:
- Energy company stocks (XLE): **up about 0.96%**
- Airline stocks (JETS): **down about 1.36%** (jet fuel is their biggest cost)

**Borrowing costs for risky companies go up.** The extra interest rate that lower-rated
companies have to pay over safe government debt (called a "credit spread") widens by
about **5 basis points** (0.05 percentage points) for junk-rated companies, and less
for investment-grade companies — riskier borrowers get hit harder, as you'd expect.

**Market fear (the VIX) rises** by about **1.7 points** — a real but not dramatic jump
in nervousness.

**The dollar and the Swiss franc both strengthen** — investors are running to safe
currencies, and it's a general flight to safety rather than just a dollar story.

**Gold does NOT move in a statistically reliable way**, despite gold's reputation as a
"war hedge." Interestingly, the original 2003 paper found the exact same thing about
gold. Twenty-three years apart, gold just doesn't reliably spike on war news the way
people assume it does.

**Israel's own stock market (Tel Aviv 125) doesn't move in a way we can tie to the
broader war-risk factor**, even though it's plenty volatile on big news days — its
ups and downs are more about local, Israel-specific news than about the shared "war
risk" factor that moves everything else.

## The one big surprise: markets are treating this war very differently than the 2003 war

The original 2003 study of Iraq-war risk found that war fears made **interest rates go
down**, made **inflation expectations go down**, and made the **dollar go down**. The
logic was: investors got scared, fled to safe government bonds (pushing rates down),
and worried the war would hurt the economy (fewer people expect inflation, and money
leaves the dollar).

**We found the exact opposite sign on all three** in 2026: interest rates **rise**,
inflation expectations **rise**, and the dollar **rises** with war risk.

That's not a mistake — it's a genuinely different economic story. In 2003, war fear was
treated as a threat to economic *growth* (bad for the economy, so rates and the dollar
fall). In 2026, war fear is being treated as a threat to *oil supply* (which pushes up
prices/inflation, so rates rise to compensate, and the dollar — now backed by a bigger
US oil industry — gets treated as the safe place to be instead of being sold off). Same
method, same kind of war, opposite market psychology — because this war hits the
economy through a completely different channel (the oil pump) than the 2003 one did.

## How much of market movement is "the war," really?

On the big-news days specifically, the war-risk factor explains a *large* chunk of what
happened — roughly half the swings in European stocks (53%) and in the VIX (49%), and
around 40% of the swings in the dollar, emerging markets, and high-yield credit spreads
on those specific days.

Zoomed out over the whole eight-month period (most days are calm, not war-news days),
the war factor's share drops to a more modest 5–17% depending on the market — which
makes sense, since most days aren't the 18 big-news days.

## How confident should you be in these numbers?

Pretty confident on most of them, with two honest caveats:

1. **A couple of the estimates lean on a weak backup measurement.** We use two
   different statistical "instruments" to double-check each number, and for most
   markets they agree closely. For a few — gold, Tel Aviv stocks, defense stocks —
   one of the two checks is unreliable, so those specific numbers should be treated
   with more caution than the rest. We flag exactly which ones in the full report.

2. **We tested whether these results hold up if we change our definition of "big news
   day"** — using anywhere from 12 to 30 days instead of 18. Almost every number barely
   moved. That stability is a good sign the results aren't just an artifact of how we
   drew the line.

3. **We also had to fix our own method along the way.** Early on, our "calm comparison
   days" accidentally included days that were themselves fairly newsy (because this war
   has been running for six months — unlike 2003's ten-week run-up to a single war,
   there's no long calm stretch to draw from). We caught this because a basic sanity
   check failed (the "calm" days weren't actually calmer than the "big news" days), and
   fixed the day-picking rule to only use genuinely quiet days as the comparison group.

## Bottom line

Putting a number on "how much the market has priced in the Iran war" turns out to be
possible, using only news coverage patterns and price moves — no guessing required about
whether any single day's news was good or bad. And the number that comes out tells a
coherent, sensible economic story: a war that threatens oil supply pushes stocks down
(more outside the US than in), widens credit spreads, lifts volatility, sends money into
safe currencies — and, unlike the 2003 Iraq war, pushes interest rates and inflation
expectations *up* rather than down, because this time investors see the war as an oil
shock, not a demand shock.

---

*This is a simplified companion to the full technical report (`REPORT.md`), which
includes the statistical tables, confidence levels, and methodology details for readers
who want the underlying math.*
