# The Iran War and Global Markets: A Plain-Language Summary

**What this project measures:** how much the Iran war has actually moved markets in
2026, using a method that turns news headlines into a number a computer can measure
against — and how confident we can be that this is the *best* way to do it, given
the alternatives.

## The problem we're solving

Everyone agrees that news about the Iran war moves markets — oil jumps when there's a
strike, stocks wobble when there's a ceasefire scare. But "war risk" isn't a number you
can look up anywhere. So how do you put a number on something nobody measures directly?

The trick, borrowed from a 2003 academic paper (Rigobon and Sack, about the lead-up to
the Iraq war): you don't need to measure war risk itself. You just need to know **which
days had unusually intense war news**. Watch how much *more* markets moved on those
noisy days compared to calm days, and that tells you how sensitive each market is to
war risk — without ever guessing whether any single day's news was "good" or "bad."

The 2003 paper picked its noisy days by hand — the authors read newspapers for ten
weeks and wrote down 17 dates that felt important. This project does that same
day-picking step automatically: a computer program flags each day **1 (high war news)
or 0 (not)**, based on how much news coverage there was and how one-sided or split it
was. That 1/0 flag is exactly what feeds into the statistical method.

## Sourcing the news

Every one of the 18 selected big-news days is described using real reporting checked
by hand against Al Jazeera, CNN and Bloomberg, with a link to the actual article for
each one. (Real news-wire headlines were also pulled through a free data feed called
GDELT, which does index real outlets — but it kept refusing requests no matter how
patiently they were spaced out, so for this specific step the verification was done by
hand rather than relying on an automated process that wasn't reliably delivering.)

## Is this even the best method? We tested that directly.

This is the main methodological question in this analysis, and rather than just argue
about it, the obvious alternative was built and run side by side.

**The alternative:** instead of the fancier "compare how much noisier markets are on
big-news days" method, just do the simple, standard thing — take the same 1/0 flag and
run an ordinary regression: "is the average price move different on flagged days versus
not?" This is called an event study, and it's the first thing most people would try.

**The result: the simple method found nothing.** Zero out of eighteen markets showed a
statistically meaningful difference. The fancier method (the one from the 2003 paper)
found meaningful effects in 13 out of 17 markets, using the *exact same* 18 days.

**Why such a big gap?** Of the 18 big-news days, 8 leaned "things are getting worse"
and 4 leaned "things are calming down" (6 were genuinely mixed). A simple average
mixes those together — a bad day that pushes stocks down and a good day that pushes
them up cancel each other out in a plain average, making it look like nothing
happened. But the fancier method isn't looking at averages — it's looking at how much
*more spread out* the results are on big-news days, and a swing in either direction
adds to that spread the same way. That's the whole reason the 2003 authors invented
this method in the first place, and this test demonstrates concretely why it matters
here too.

**So: for this specific problem, the fancier method is genuinely the better
choice** — not because it's more sophisticated, but because the simple alternative
was tested head-to-head and it came up empty.

## Splitting news into three flavors

Instead of just "big news day" vs. "calm day," the big-news days can also be split
into three groups: **bad news** (coverage leaning toward escalation), **good news**
(coverage leaning toward de-escalation), and **no news** (calm days). The natural
expectation is that bad news should push yields and oil up and stocks down, and good
news should do the reverse.

**Checking this the simplest possible way — just comparing average price moves on
each type of day — all seven markets checked matched the expected pattern
exactly:** on bad-news days, both bond yields rose, oil rose, and the "fear gauge"
(VIX) rose, while stocks fell. On good-news days, several of those reversed (stocks
actually rose on average, and the fear gauge fell). Simple, intuitive, and it worked.

## Can news content actually predict which days will be stressful? A classifier
was built to check, and the honest answer taught something useful.

A small machine-learning model (a standard, simple type called logistic regression)
was asked to learn: given only the news-coverage patterns for a day, can you predict
whether that day will turn out to be a high-stress day for markets overall?

**The honest answer: not really.** The model did worse than random guessing at this
specific task. That sounds bad, but digging into *why* actually reinforces the main
approach rather than undermining it: the "high market stress" days it was asked to
predict were defined using a broad basket of markets (bonds, stocks, oil, credit,
volatility) — and plenty of those stressful days had nothing to do with Iran at all
(Fed decisions, other economic news, etc.). On those days, financial news coverage was
naturally focused elsewhere, not on Iran, so of course Iran-specific news coverage
doesn't predict them well. This is actually a good argument for why picking "big news
days" from the news itself (rather than from overall market chaos) is the right
design — it stays focused on the one specific risk being measured, instead of getting
confused by every other thing that moves markets.

A separate check: does the choice of exactly *how* you draw the "big news day" line
matter for the final results? Three different ways to draw that line were tried — the
original hand-tuned rule, the machine-learning classifier's guess, and an unsupervised
pattern-finder that never even looked at prices. **The core economic story (stocks
down, credit costs up) held up under all three; only a couple of markets (the VIX and
the dollar) were sensitive to exactly which line was drawn**, and those happen to be
the same two markets flagged as less reliable for other reasons too.

## Checking whether the word list misses new war vocabulary

Any list of "war words" built ahead of time is going to miss brand-new terminology
that a specific, unfolding war invents as it goes. This was checked directly against
real news sentences from the 18 selected days.

**Result: over half (52.5%) of clearly war-relevant sentences scored zero matches
against the hand-built word list.** Real examples the list completely missed:
"Natanz nuclear enrichment complex" (a facility name — the list has no idea what
Natanz is), "rogue supertankers" (a phrase this specific conflict's coverage
invented), and "the memorandum-of-understanding ceasefire" (a named agreement that
didn't exist before this war). This is a real, quantified limitation — the honest fix
would be to have a more flexible AI model read the actual sentences in context (which
understands "Natanz" is a nuclear site without needing it pre-programmed), rather
than count fixed phrases. That wasn't built as a full automated step here, but the
work was done by hand on a sample to show what it would catch.

## Checking the results against what 2003 would predict

Comparing 2026 to 2003 gives a natural benchmark, with one deliberate difference: oil,
stock, and credit-market reactions should look similar to 2003, but **interest rates
should behave the opposite way**, because the US now pumps roughly 14 million barrels
of oil a day versus about 6 million back in 2003 — meaning a war-driven oil price
spike now benefits US oil producers a lot more than it did back then, changing how the
whole economy reacts.

**Every single piece of that prediction came true in the results.** Oil, stocks, and
credit spreads moved the same direction they did in 2003. Interest rates, inflation
expectations, and the dollar all moved the *opposite* direction from 2003, exactly as
expected — because this time the war is being priced mainly as an oil-supply shock
(which pushes prices and rates up) rather than a pure "the economy is in danger"
scare (which pushed rates down in 2003).

## Bottom line

Three things came together in this analysis: real, checked news citations replaced an
unreliable source; the choice of statistical method was tested, not just asserted, by
building the obvious simpler alternative and watching it fail where the fancier method
succeeded; and a three-way news split matched the expected economic pattern
perfectly, alongside an honest look at where the underlying methods (the word list,
the classifier) have real limits. The headline economic story: a war that threatens
oil supply pushes stocks down (more outside the US than in), widens credit spreads,
lifts volatility, sends money into safe currencies, and — unlike the 2003 Iraq war —
pushes interest rates and inflation expectations *up* rather than down, because
America's much larger oil industry changes how this kind of shock hits the economy.

---

*This is a simplified companion to the full technical report (`REPORT.md`), which
includes all the statistical tables, confidence levels, and methodology details,
including the alternative methods and literature review, for readers who want the
underlying math.*
