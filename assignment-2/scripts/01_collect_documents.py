"""Collects FOMC statements, minutes, Chair speeches, Chair testimony and
press conference transcripts from federalreserve.gov, Feb 2018 - present.

Saves raw text under data/raw/<type>/<date>_<slug>.txt and a metadata table
at data/interim/documents.csv. Re-run is safe: existing files are skipped.
"""
import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from config import RAW, INTERIM, START_DATE, END_DATE, chair_for_date
import fed_scraper as fs


def save_text(path: Path, text: str) -> int:
    path.write_text(text, encoding="utf-8")
    return len(text.split())


def main():
    rows = []

    # 1. Statements + minutes
    print("Collecting FOMC meeting calendar...")
    meetings = fs.collect_meeting_links()
    for date_str in sorted(meetings):
        d = dt.date.fromisoformat(date_str)
        if not (START_DATE <= d <= END_DATE):
            continue
        chair = chair_for_date(d)
        for doc_type, key, dirname in [("statement", "statement", "statements"), ("minutes", "minutes", "minutes")]:
            url = meetings[date_str].get(key)
            if not url:
                continue
            out = RAW / dirname / f"{date_str}.txt"
            if out.exists():
                text = out.read_text(encoding="utf-8")
            else:
                print(f"  {doc_type} {date_str}")
                text = fs.fetch_document_text(url)
                if not text:
                    continue
                save_text(out, text)
            rows.append(dict(doc_type=doc_type, date=date_str, chair=chair,
                              speaker=chair, title=f"FOMC {doc_type} {date_str}",
                              url=url, n_words=len(text.split()), path=str(out)))

    # 2. Press conference transcripts (post-meeting, mostly 2019+)
    print("Collecting press conference transcripts...")
    for date_str in sorted({r["date"] for r in rows if r["doc_type"] == "statement"}):
        d = dt.date.fromisoformat(date_str)
        out = RAW / "speeches" / f"presconf_{date_str}.txt"
        url = fs.presconf_url_for(date_str)
        if out.exists():
            text = out.read_text(encoding="utf-8")
            if not text:
                continue
        else:
            text = fs.fetch_document_text(url)
            if not text or len(text.split()) < 100:
                continue
            print(f"  presconf {date_str}")
            save_text(out, text)
        chair = chair_for_date(d)
        rows.append(dict(doc_type="presser", date=date_str, chair=chair, speaker=chair,
                          title=f"FOMC press conference {date_str}", url=url,
                          n_words=len(text.split()), path=str(out)))

    # 3. Chair speeches + testimony (Powell, Warsh only)
    print("Collecting Chair speeches and testimony...")
    speaker_keys = ["powell", "warsh"]
    for section, years in [("speech", range(2018, 2027)), ("testimony", range(2018, 2027))]:
        links = fs.collect_speaker_links(section, speaker_keys, years)
        for date_str, url in links:
            d = dt.date.fromisoformat(date_str)
            if not (START_DATE <= d <= END_DATE):
                continue
            slug = url.rstrip("/").split("/")[-1].replace(".htm", "")
            doc_type = "speech" if section == "speech" else "testimony"
            out = RAW / "speeches" / f"{doc_type}_{date_str}_{slug}.txt"
            if out.exists():
                text = out.read_text(encoding="utf-8")
            else:
                print(f"  {doc_type} {date_str} {slug}")
                text = fs.fetch_document_text(url)
                if not text or len(text.split()) < 100:
                    continue
                save_text(out, text)
            rows.append(dict(doc_type=doc_type, date=date_str, chair=chair_for_date(d),
                              speaker=chair_for_date(d), title=slug, url=url,
                              n_words=len(text.split()), path=str(out)))

    df = pd.DataFrame(rows).drop_duplicates(subset=["doc_type", "date", "path"])
    df = df.sort_values(["date", "doc_type"]).reset_index(drop=True)
    df.to_csv(INTERIM / "documents.csv", index=False)
    print(f"\nSaved {len(df)} documents -> {INTERIM / 'documents.csv'}")
    print(df.groupby(["chair", "doc_type"]).size())


if __name__ == "__main__":
    main()
