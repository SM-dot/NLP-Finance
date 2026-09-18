"""Collects the Iran war-risk news measures from GDELT, Jan 2 - Sep 16 2026.

Design note. The obvious approach - pull a day's headlines for each of the 258 days
and score the text - runs into GDELT's throttle: the article endpoint refuses a
large and fairly random share of requests, so a full sweep takes many hours and is
not reproducible for whoever runs this next. It is also capped at 250 articles per
day, which samples rather than measures the coverage.

So the daily measures come instead from GDELT's *timeline* endpoint, where a single
request returns the whole window. Each query is a themed slice of coverage, and the
slices are built from the same escalation / de-escalation vocabulary as the lexicon
in src/warrisk_lexicon.py:

  war          all Iran war-risk coverage        -> how much attention
  iran         all Iran coverage                 -> war coverage as a share of it
  escalation   strikes, missiles, blockades      -> news pushing war risk up
  deescalation ceasefires, talks, agreements     -> news pushing war risk down
  hormuz       the chokepoint specifically       -> the oil-market channel

That is five requests instead of 258, and each covers every article GDELT saw
rather than a 250-article sample. Headlines are still needed - for Table 1 and for
the FinBERT cross-check - but only for the days the estimator actually uses, which
script 04 fetches once it knows which those are.

Each series is cached in its own CSV, so a refused request costs one retry rather
than the whole run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from config import NEWS, START_DATE, END_DATE, TIMELINE_QUERIES
import gdelt


def collect_series(name: str, query: str, tone: bool = False) -> pd.Series | None:
    kind = "tone" if tone else "vol"
    path = NEWS / f"timeline_{name}_{kind}.csv"
    if path.exists():
        s = pd.read_csv(path, index_col=0).squeeze("columns")
        print(f"  {name} ({kind}): cached, {len(s)} days")
        return s
    try:
        s = (gdelt.timeline_tone if tone else gdelt.timeline_volume)(
            query, START_DATE, END_DATE)
    except RuntimeError as e:
        print(f"  {name} ({kind}): FAILED - {e}")
        return None
    s.to_csv(path)
    print(f"  {name} ({kind}): fetched, {len(s)} days")
    return s


def main():
    print("Collecting GDELT coverage timelines...")
    vols, tones = {}, {}
    for name, query in TIMELINE_QUERIES.items():
        s = collect_series(name, query, tone=False)
        if s is not None:
            vols[name] = s
    # tone is only needed for the overall war-risk slice
    t = collect_series("war", TIMELINE_QUERIES["war"], tone=True)
    if t is not None:
        tones["war_tone"] = t

    missing = [n for n in TIMELINE_QUERIES if n not in vols]
    if missing:
        print(f"\nStill missing: {', '.join(missing)} - re-run this script to retry.")
        return

    df = pd.concat({f"{k}_volume": v for k, v in vols.items()} | tones, axis=1)
    df.index.name = "date"
    df = df.sort_index()
    out = NEWS / "timelines.csv"
    df.to_csv(out)

    print(f"\nSaved {df.shape} -> {out}")
    print(f"Window: {df.index.min()} to {df.index.max()}")
    print("\nPeak coverage days per series:")
    for c in df.columns:
        if c.endswith("_volume"):
            print(f"  {c:22s} peak {df[c].max():7.3f} on {df[c].idxmax()}")
    print("\n", df.describe().round(3).to_string())


if __name__ == "__main__":
    main()
