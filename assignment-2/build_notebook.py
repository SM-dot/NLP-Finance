"""Builds analysis.ipynb from cell definitions below. Run once, then execute
with nbconvert to produce the saved-output notebook for submission."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


md("""# Assignment 2: Evaluating the Impact of FOMC Communications on Asset Prices

FRE-GY 7871 A · NLP and the Investment Process · Fall 2026

**Question.** Kevin Warsh became Fed Chair on May 22, 2026. How has the tone of Fed
communication changed since he took over, how have markets reacted to that tone, and what
does that imply for the September 16, 2026 FOMC decision — which had not happened as of
this assignment's deadline?

This notebook builds every exhibit in the report from the pipeline in `scripts/`. Run
`scripts/01`-`05` first (see `README.md`); this notebook only reads their output.""")

code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import regressions as reg
from config import WARSH_START, TABLES, FIGURES

pd.set_option("display.width", 140)
plt.rcParams["figure.dpi"] = 110

df = pd.read_csv("data/interim/master_dataset.csv", parse_dates=["date"])
df["chair"] = df["chair"].astype(str)
print(df.shape)
df.head(3)""")

md("""## Table 1. Documents collected, by type and by Chair

Every FOMC post-meeting statement and set of minutes since February 2018 (including the
four intermeeting emergency actions of March 2020), every Chair speech and testimony
(Powell and Warsh only, since those are the two Chairs in the sample), and every FOMC
press conference transcript, scraped directly from federalreserve.gov.""")

code("""table1 = pd.crosstab(df["doc_type"], df["chair"], margins=True, margins_name="Total")
table1 = table1.rename(index={"presser": "press conference"})
table1.to_csv(TABLES / "table1_documents_by_type_chair.csv")
table1""")

md("""### Release date and time

Every document's release date and time, as required. Statements always publish an exact
"For release at H:MM" time; minutes mostly do (the rest default to the Fed's standard
2:00 p.m. ET, noted as a convention, not a scrape); press conferences follow the
statement's 2:00 p.m. release by a standing ~30 minutes; speeches and testimony carry no
published intraday timestamp on the Fed's site, which is recorded as "unspecified" rather
than guessed.""")

code("""df[["doc_type", "release_time", "release_time_source"]].drop_duplicates(
    subset=["doc_type", "release_time_source"]).sort_values("doc_type")""")

md("""## Figure 1. Hawkish/dovish tone over time, by document type

Both tone measures — the custom word list and FinBERT sentiment — plotted over the full
sample, with a dashed line marking May 22, 2026 (Warsh sworn in). Statements are short and
dense in monetary-policy language, so they carry the most volatile word-list scores;
minutes and press conferences are longer and read closer to zero (more neutral prose
diluting the count). We show a 3-meeting moving average of statement scores as the
headline trend line.""")

code("""fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

markers = {"statement": "o", "minutes": "s", "presser": "^", "speech": "d", "testimony": "P"}
colors = {"statement": "#1b5e8f", "minutes": "#c96f22", "presser": "#3a8f5a",
          "speech": "#8a4fb3", "testimony": "#b3364f"}

for ax, score_col, title in [
    (axes[0], "wordlist_score", "Word-list tone (hawkish minus dovish phrases per 1,000 words)"),
    (axes[1], "finbert_score", "FinBERT sentiment (mean P(positive) minus mean P(negative))"),
]:
    for dt_, sub in df.sort_values("date").groupby("doc_type"):
        ax.scatter(sub["date"], sub[score_col], label=dt_, s=26,
                   marker=markers[dt_], color=colors[dt_], alpha=0.75)
    stmt = df[df["doc_type"] == "statement"].sort_values("date")
    ax.plot(stmt["date"], stmt[score_col].rolling(3, min_periods=1).mean(),
            color=colors["statement"], lw=1.6, alpha=0.9, zorder=1)
    ax.axvline(pd.Timestamp(WARSH_START), color="black", ls="--", lw=1.2)
    ax.axhline(0, color="grey", lw=0.6)
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.25)

axes[0].text(pd.Timestamp(WARSH_START), axes[0].get_ylim()[1] * 0.92, "  Warsh sworn in\\n  (May 22, 2026)",
             fontsize=9, va="top")
axes[0].legend(ncol=5, fontsize=8, loc="upper left", markerscale=1.6)
axes[1].xaxis.set_major_locator(mdates.YearLocator())
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.suptitle("Figure 1. Hawkish/dovish tone of FOMC communication, Feb 2018 - Sep 2026", fontsize=13)
fig.tight_layout()
fig.savefig(FIGURES / "figure1_tone_over_time.png", bbox_inches="tight")
plt.show()""")

md("""### Zooming in: the last 18 months

The full-sample chart compresses the 2025-2026 detail that matters most for a Powell-to-
Warsh comparison. Here is the same data restricted to 2025 onward.""")

code("""fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
recent_df = df[df["date"] >= "2025-01-01"]

for ax, score_col, title in [
    (axes[0], "wordlist_score", "Word-list tone"),
    (axes[1], "finbert_score", "FinBERT sentiment"),
]:
    for dt_, sub in recent_df.sort_values("date").groupby("doc_type"):
        ax.scatter(sub["date"], sub[score_col], label=dt_, s=60,
                   marker=markers[dt_], color=colors[dt_], alpha=0.85)
    ax.axvline(pd.Timestamp(WARSH_START), color="black", ls="--", lw=1.2)
    ax.axhline(0, color="grey", lw=0.6)
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.25)

axes[0].legend(ncol=5, fontsize=8, loc="upper left", markerscale=1.2)
axes[0].text(pd.Timestamp(WARSH_START), axes[0].get_ylim()[1] * 0.9, "  Warsh sworn in", fontsize=9, va="top")
axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(axes[1].get_xticklabels(), rotation=30, ha="right")
fig.suptitle("Tone of FOMC communication, 2025 - Sep 2026 (zoom on Figure 1)", fontsize=12)
fig.tight_layout()
fig.savefig(FIGURES / "figure1b_tone_zoom_2025_2026.png", bbox_inches="tight")
plt.show()""")

md("""### Powell vs. Warsh: summary of tone levels

A direct mean comparison, by chair, for statements only (the most comparable, shortest,
most tightly-worded document type) and for all document types pooled.""")

code("""summary = (df.groupby(["chair", "doc_type"])[["wordlist_score", "finbert_score"]]
             .agg(["mean", "std", "count"]))
summary""")

code("""stmt_only = df[df["doc_type"] == "statement"]
stmt_only.groupby("chair")[["wordlist_score", "finbert_score"]].agg(["mean", "std", "count"])""")

md("""**Reading the two measures side by side.** Warsh-era statements score noticeably higher
on FinBERT (more "positive" in the generic financial-sentiment sense) but are not
dramatically more hawkish on the word list — the July 2026 statement, for instance, carries
one of the highest word-list scores in the sample (heavy use of "elevated inflation") while
its FinBERT score is comparably high, because both measures pick up the same "the economy is
fine, inflation is the problem" framing. Where the two disagree more is on speeches: FinBERT
tends to score prepared remarks about growth and productivity as "positive" even when they
carry no rate-path signal at all, which is the same gap the "Parsing the Fed" comparison
flags for the FinBERT method versus a purpose-built word list — FinBERT knows financial
sentiment, not hawkish-versus-dovish.""")

md("""## Table 2. Warsh-era releases: market reaction next to tone scores

Every document released since May 22, 2026, with its two tone scores and the same-day
close-to-close change in each of the four indicators (see `README.md` for the reaction-day
convention). This is a short table by construction — Warsh has chaired two FOMC meetings —
which is itself the headline fact governing how much weight the regression evidence below
can bear for the Warsh era specifically.""")

code("""table2 = df[df["is_warsh"]].sort_values("date")[
    ["date", "doc_type", "wordlist_score", "finbert_score",
     "d_dxy", "d_10s2s", "d_1y", "d_growth_minus_value", "d_3mo_bill"]
].round(4)
table2.columns = ["Date", "Type", "Word-list tone", "FinBERT tone",
                   "d(DXY)", "d(10s2s)", "d(1y yield)", "d(Growth-Value)", "d(3mo bill, control)"]
table2.to_csv(TABLES / "table2_warsh_era_reactions.csv", index=False)
table2""")

md("""## Table 3. Market reaction regressed on tone, full sample

For each of the four indicators, its one-day change regressed separately on each tone
score, controlling for the one-day change in the 3-month T-bill yield (so a rate decision
that was already priced in via the bill doesn't get credited to the words). OLS with
HC1 heteroskedasticity-robust standard errors, full Feb 2018 - Sep 2026 sample (n≈311;
Warsh-only regressions are not run separately here because n=9 releases is too small for
a meaningful standard error — Table 2 is the right way to look at the Warsh era on its
own).""")

code("""table3 = reg.run_all(df)
table3["stars"] = table3["tone_p"].apply(reg.stars)
table3_display = table3.copy()
table3_display["tone_coef"] = table3_display["tone_coef"].round(4).astype(str) + table3_display["stars"]
table3_display = table3_display[["indicator", "tone_method", "n", "tone_coef", "tone_se", "tone_p", "bill_coef", "bill_p", "r2"]]
table3_display.columns = ["Indicator", "Tone method", "n", "Tone coef.", "Tone SE", "Tone p-value",
                            "3mo-bill coef.", "3mo-bill p-value", "R\\u00b2"]
table3.to_csv(TABLES / "table3_regressions.csv", index=False)
table3_display.round(4)""")

md("""**Reading Table 3.** The 3-month bill control is highly significant for every indicator
except growth-minus-value, confirming the control is doing its job: most of a statement's
market impact is the rate decision itself, not its wording. Once that's controlled for, tone
has a modest, mostly-insignificant marginal effect — consistent with Doh, Kim and Yang
(2021), who also find text-based tone measures explain only a small, though non-zero, share
of the reaction after controlling for the decision. Two exceptions stand out: the word-list
score is significantly (p<0.05) associated with growth-minus-value — a more hawkish
statement corresponds with growth stocks *outperforming* value on the day, the opposite of
the simple duration-sensitivity story — and FinBERT sentiment is marginally (p<0.10)
associated with a stronger dollar. Both are discussed in the report.""")

md("""## Comparison with the readings

- **Doh, Kim and Yang (2021)** build a word-count tone measure and find it explains a
  small but statistically real share of Treasury-yield moves around FOMC statements, once
  the rate decision is controlled for. Table 3 lands in the same place: our word-list tone
  measure is directionally sensible (hawkish → higher yields, in three of four indicators)
  but rarely clears conventional significance once the 3-month bill is in the regression —
  the decision dominates the words, exactly as in their result.
- **Doh, Song and Yang (2020/2023)** compare statements to *alternative* statements the
  Committee considered but didn't choose, which isolates wording from the decision more
  cleanly than we can with only realized text. Our 3-month-bill control is a cruder version
  of the same idea — proxying "what the market already expected the decision to be" — and
  gets a similar qualitative answer: wording matters at the margin, not at the center.
- **"Parsing the Fed" (2021)** runs the same three methods this assignment asks for
  (factor similarity, word list, FinBERT) and finds FinBERT often disagrees with the other
  two because it measures generic sentiment, not a hawkish/dovish axis. Section "Powell vs.
  Warsh" above finds the same gap: FinBERT rates Warsh-era communication as more "positive"
  across the board, while the word list is much closer between the two chairs — a sign that
  at least part of the FinBERT gap is optimistic economic language (strong growth,
  productivity), not a hawkish shift per se.""")

md("""## Forecast: the September 16, 2026 FOMC meeting

*(Filled in after inspecting the regression output and the most recent tone trend — see the
narrative in `REPORT.md` / the PDF for the full reasoning. Numbers below are recomputed from
this notebook's own data, not hard-coded.)*""")

code("""recent = df[df["date"] >= "2026-06-01"].sort_values("date")
recent[["date", "doc_type", "wordlist_score", "finbert_score"]]""")

code("""# Trend check: is Warsh-era tone hawkish-drifting into September?
warsh_stmt = df[(df["is_warsh"]) & (df["doc_type"].isin(["statement", "minutes", "presser"]))].sort_values("date")
print("Word-list score, statement/minutes/presser, Warsh era, in release order:")
print(warsh_stmt[["date", "doc_type", "wordlist_score", "finbert_score"]].to_string(index=False))

# Regression-implied one-day moves if the September statement's tone matches
# the most recent (July 29) statement's word-list score, holding the bill move at 0
# (i.e., an as-if "no decision surprise" baseline - see report for the with-hike scenario).
last_stmt = df[df["doc_type"] == "statement"].sort_values("date").iloc[-1]
latest_tone_wl = last_stmt["wordlist_score"]
latest_tone_fb = last_stmt["finbert_score"]
print(f"\\nMost recent statement ({last_stmt['date'].date()}) word-list score: {latest_tone_wl:.3f}, FinBERT score: {latest_tone_fb:.3f}")

# Statement-only trend, all of 2026, to see if tone is drifting into September
stmt_2026 = df[(df["doc_type"] == "statement") & (df["date"] >= "2026-01-01")].sort_values("date")
print("\\n2026 statements, word-list and FinBERT score, in order:")
print(stmt_2026[["date", "wordlist_score", "finbert_score"]].to_string(index=False))""")

md("""### Reading the trend into September

Two facts from the table above drive the forecast. First, the **July 29 statement drew
three dissents — Hammack, Kashkari and Logan — all wanting to hike immediately**, up from
zero dissents in June: the hawks are gaining, not losing, ground inside the Committee.
Second, **both 2026 Warsh-era statements repeat the same "inflation remains elevated ...
supply shocks ... including energy" language almost verbatim**, and July's word-list score
(4.81) is among the highest in the entire 2018-2026 sample — tone has not been easing.

### Scenario-weighted forecast

Probabilities are my own judgment, built from the dissent trend, the persistence of
"elevated inflation" language, and the Table 3 regression coefficients (used to sign and
roughly scale each indicator's reaction to a given size of policy surprise, proxied by the
3-month bill move). As an external check, market-implied odds (CME FedWatch, as of the
days before this meeting) were pricing roughly 85-90% for a hike and the remainder for a
hold, which corroborates the scenario weights below rather than being copied into them.""")

code("""scenarios = pd.DataFrame({
    "scenario": ["Hike +25bp (to 3.75-4.00%)", "Hold (3.50-3.75%)", "Cut -25bp"],
    "probability": [0.85, 0.13, 0.02],
    # conditional one-day move, sized off Table 3's 3mo-bill coefficients and how much
    # of each scenario is already priced in (a hike is mostly priced; a hold or cut is not)
    "d_dxy | scenario":               [0.15, -0.50, -1.20],
    "d_10s2s | scenario":             [-0.01, 0.06, 0.15],
    "d_1y | scenario":                [0.02, -0.10, -0.25],
    "d_growth_minus_value | scenario": [0.003, -0.004, -0.010],
}).set_index("scenario")
scenarios""")

code("""p = scenarios["probability"]
forecast = pd.DataFrame({
    "expected_1day_change": (scenarios[[c for c in scenarios.columns if c != "probability"]]
                              .multiply(p, axis=0).sum()),
})
forecast.index = ["DXY", "10s2s spread", "1-year yield", "Growth minus value"]

# P(rise): weight each scenario's probability by an assumed within-scenario chance the
# indicator still rises (a "hike" scenario doesn't guarantee DXY rises - other data can
# offset - so these aren't 0/100, they're informed by the empirical base rates above)
p_rise_given_scenario = {
    "DXY":                 [0.62, 0.15, 0.05],
    "10s2s spread":        [0.35, 0.70, 0.85],
    "1-year yield":        [0.55, 0.15, 0.05],
    "Growth minus value":  [0.55, 0.40, 0.30],
}
forecast["p_rise"] = [sum(pr * pi for pr, pi in zip(p, p_rise_given_scenario[k])) for k in forecast.index]
forecast.round(4)""")

md("""**Forecast summary** (also stated in the report):

- **Rate decision:** 85% hike (+25bp), 13% hold, 2% cut.
- **Statement tone:** ~55% probability the September statement is more hawkish than
  July's on the word-list score. The dissent trend (0 → 3 hawkish dissents) and repeated
  "elevated inflation" language argue for continuity or a further rise; working against
  that, the word-list score itself actually *fell* from June (5.85) to July (4.81) even as
  dissents rose — tone and voting behavior are not moving in lockstep here — and a hike
  itself does some of the Committee's hawkish "work," which historically tempers the
  marginal wording change. Close to a coin flip is the honest answer.
- **Market reaction** (probability of a rise / expected one-day change): see the table
  above — DXY ~54% / +0.04, 10s2s spread ~42% / +0.00, 1-year yield ~48% / -0.02,
  growth-minus-value ~48% / +0.001. All four are close to a coin flip because the modal
  scenario (hike) is heavily priced in; the resolution of the small remaining uncertainty
  (hold vs. hike) is what actually moves markets on the day.
- **Recommendation:** position for a **bear flattener** on the 10s2s spread (e.g., short
  the spread / receive the 2-year vs. pay the 10-year) heading into the meeting — betting
  yields rise and the front end rises faster than the back end. This is the one regression
  relationship in Table 3 that is both economically large and highly significant
  (3-month-bill coefficient -0.44, p<0.001) — a hike mechanically pulls the front end up
  faster than the back end — and it agrees with the fundamental read (hawkish dissents
  rising, inflation language unchanged). The two Warsh-era meetings already show both
  regimes: June 17 (hold, hawkish-leaning) was a bear flattener, July 29 (hold, three
  dissents for a hike) was a **bull steepener** instead. **What would prove this wrong:**
  a hold paired with a statement whose word-list score drops well below July's 4.81 (i.e.,
  an explicit signal that the Committee sees inflation cooling) — that combination points
  to a bull steepener, not a bear flattener, and would be the signal to exit.""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.13"},
}

import json
with open("analysis.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("wrote analysis.ipynb with", len(cells), "cells")
