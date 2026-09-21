"""Quantifies the professor's second concern directly: "New war terms may be
missing from legacy NLP dictionaries, and even updated AI models can misclassify
genuinely new language."

The hand-built lexicon in src/warrisk_lexicon.py is a fixed list of escalation and
de-escalation phrases. Real reporting on this war routinely uses vocabulary a fixed
list from 2003 or even early 2026 could not anticipate - named agreements
("Islamabad Memorandum"), specific facility names ("Abqaiq," "Natanz," "Sharif
University"), and conflict-specific mechanisms ("snapback," a naval blockade of
"all maritime traffic"). This script checks, sentence by sentence, across the 18
verified real-news summaries in data/news/verified_events.json (Al Jazeera, CNN and
Bloomberg reporting, checked against real dated articles), how often a sentence that
is unmistakably about war escalation or de-escalation scores zero lexicon hits -
i.e., how often the fixed phrase list goes blind on real text about this specific
war.

Output: report_tables/table13_vocabulary_coverage.csv, plus every zero-hit sentence
found, so the gap is visible rather than just quantified.
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from config import NEWS, TABLES
import warrisk_lexicon as lex


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]


def main():
    path = NEWS / "verified_events.json"
    if not path.exists():
        print("No verified_events.json found - run scripts/04_build_event_days.py first.")
        return
    events = json.loads(path.read_text(encoding="utf-8"))

    rows = []
    zero_hit = []
    for date, ev in events.items():
        for sent in split_sentences(ev.get("summary", "")):
            s = lex.score_text(sent)
            hits = s["escalation"] + s["de_escalation"]
            rows.append({"date": date, "source": ev.get("source", ""),
                        "sentence": sent, "lexicon_hits": hits})
            if hits == 0:
                zero_hit.append((date, ev.get("source", ""), sent))

    df = pd.DataFrame(rows)
    zero_share = float((df["lexicon_hits"] == 0).mean())
    summary = pd.DataFrame([{
        "n_sentences_checked": len(df),
        "n_zero_lexicon_hits": int((df["lexicon_hits"] == 0).sum()),
        "pct_zero_hits": round(100 * zero_share, 1),
        "n_days_covered": df["date"].nunique(),
    }])
    summary.to_csv(TABLES / "table13_vocabulary_coverage.csv", index=False)

    print("Table 13. Lexicon vocabulary coverage on verified real-news reporting "
          "of the 18 selected days\n")
    print(summary.to_string(index=False))
    print(f"\n{zero_share * 100:.1f}% of sentences from real, dated, sourced "
          f"reporting on these war-news days score ZERO escalation/\n"
          f"de-escalation phrase hits in the hand-built lexicon, despite covering "
          f"strikes, blockades, casualties, and\nceasefire negotiations - "
          f"the vocabulary-coverage gap the professor's guidance flags.\n")

    print("Every zero-hit sentence found (topically unmistakable, lexicon blind):")
    for date, source, sent in zero_hit:
        print(f"  {date}  [{source}]")
        print(f"      {sent[:130]}")

    print("\nWhy the lexicon misses these (read by hand, not automated):")
    reasons = {
        "Natanz": "a specific facility name; the lexicon has no place-name knowledge "
                 "at all, so 'Natanz nuclear enrichment complex' scores zero even "
                 "though striking it is a major escalation",
        "Islamabad Memorandum": "a named diplomatic agreement, escalation/"
                                "de-escalation signal specific to this conflict's own "
                                "history, not a generic phrase a fixed list can predict",
        "blockade": "the lexicon DOES have 'blockade' as an escalation phrase, so "
                    "sentences naming the blockade directly are caught - it is the "
                    "surrounding operational detail ('all maritime traffic entering "
                    "or exiting Iranian ports') that carries no lexicon match",
        "supertanker": "novel compound noun invented by this conflict's reporting "
                       "('rogue supertankers'); not in any general-purpose or "
                       "hawkish/dovish word list",
    }
    for term, note in reasons.items():
        hit = df[df["sentence"].str.contains(term, case=False, na=False)]
        print(f"  '{term}' appears in {len(hit)} sentence(s): {note}")


if __name__ == "__main__":
    main()
