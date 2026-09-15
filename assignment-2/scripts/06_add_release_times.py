"""Fixes a real gap: the assignment says "record each document's release
date and time," and the original collection pass only recorded the date.
This reads the already-downloaded raw text (no re-scraping needed) and
extracts the actual release time where the Fed publishes one.

Statements: 100% carry "For release at H:MM a.m./p.m." boilerplate.
Minutes: most do; the rest are, by longstanding Fed convention, released at
2:00 p.m. ET same as the statement, so that's used as a documented fallback.
Press conferences: begin per the FOMC statement release, ~2:30 p.m. ET
(no per-document boilerplate; convention noted as such).
Speeches/testimony: the Fed does not consistently publish an intraday
timestamp on these pages, so time is recorded as "unspecified" - this
was already the case for the market-reaction convention documented in
scripts/05_build_dataset.py, which assumes same trading day either way.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from config import INTERIM

TIME_RE = re.compile(r"[Ff]or release at (\d{1,2}:\d{2}\s*[ap]\.?m\.?)")


def extract_time(text: str) -> str | None:
    m = TIME_RE.search(text)
    if not m:
        return None
    return m.group(1).upper().replace(".", "") + " ET"


def main():
    docs = pd.read_csv(INTERIM / "documents.csv")
    times, sources = [], []
    for _, row in docs.iterrows():
        text = Path(row["path"]).read_text(encoding="utf-8")
        t = extract_time(text)
        if t:
            times.append(t)
            sources.append("published in document text")
        elif row["doc_type"] in ("statement", "minutes"):
            times.append("2:00 PM ET")
            sources.append("Fed standard release convention (not in text)")
        elif row["doc_type"] == "presser":
            times.append("~2:30 PM ET")
            sources.append("standard post-statement press conference start (not in text)")
        else:
            times.append("unspecified")
            sources.append("Fed does not publish an intraday timestamp for this document type")

    docs["release_time"] = times
    docs["release_time_source"] = sources
    docs.to_csv(INTERIM / "documents.csv", index=False)
    print(f"Updated -> {INTERIM / 'documents.csv'}")
    print(docs.groupby(["doc_type", "release_time_source"]).size())


if __name__ == "__main__":
    main()
