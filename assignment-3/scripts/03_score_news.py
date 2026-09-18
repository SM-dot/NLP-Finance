"""Turns raw coverage volumes into the daily war-risk news measures.

Three quantities come out of this, one for each thing the estimator needs to know
about a day's war news.

  attention     how much war-risk coverage there was, as a share of all coverage
                GDELT monitored. Used in logs, because coverage is right-skewed.

  direction     (escalation - de-escalation) / (escalation + de-escalation), from
                the two themed coverage slices. Bounded in [-1, 1]: +1 is a day
                where the war-risk vocabulary is all strikes and ultimatums, -1 a
                day where it is all ceasefires and talks. This is the analogue of
                Rigobon and Sack's hand-assigned "Increased / Decreased" column.

  contest       how *split* the day's coverage was between the two vocabularies,
                weighted by how much coverage there was:
                    (1 - |direction|) x log(1 + war coverage)
                A day when the wires carry heavy escalation and heavy de-escalation
                coverage at once is a high-variance news day even though the two
                cancel in the average - which is exactly the case Rigobon and Sack
                tag "Unclear", and exactly what identification needs. A perfectly
                balanced but quiet day scores near zero because of the volume term.

Output: data/interim/news_daily.csv, one row per calendar day.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from config import NEWS, INTERIM, START_DATE, END_DATE


def main():
    df = pd.read_csv(NEWS / "timelines.csv", index_col="date", parse_dates=True)
    df = df[(df.index.date >= START_DATE) & (df.index.date <= END_DATE)]

    esc = df["escalation_volume"]
    des = df["deescalation_volume"]
    total = (esc + des).replace(0, np.nan)

    df["direction"] = (esc - des) / total
    df["contest"] = (1 - df["direction"].abs()) * np.log1p(df["war_volume"])
    df["war_share"] = df["war_volume"] / df["iran_volume"].replace(0, np.nan)
    df["hormuz_share"] = df["hormuz_volume"] / df["iran_volume"].replace(0, np.nan)

    out = INTERIM / "news_daily.csv"
    df.to_csv(out)

    print(f"Saved {df.shape} -> {out}")
    print(f"Window: {df.index.min().date()} to {df.index.max().date()}, "
          f"{len(df)} calendar days\n")

    print("Ten days of heaviest war-risk coverage:")
    top = df["war_volume"].nlargest(10)
    for d, v in top.items():
        print(f"  {d.date()}  coverage {v:6.3f}  direction {df.loc[d, 'direction']:+.2f}"
              f"  contest {df.loc[d, 'contest']:.2f}")

    print("\nTen most escalatory and ten most de-escalatory days by direction:")
    print("  most escalatory:  " +
          ", ".join(f"{d.date()}" for d in df["direction"].nlargest(5).index))
    print("  most conciliatory:" +
          ", ".join(f" {d.date()}" for d in df["direction"].nsmallest(5).index))

    print("\nSummary:")
    print(df[["war_volume", "war_share", "direction", "contest", "war_tone"]]
          .describe().round(3).to_string())
    print("\nCorrelation of direction with GDELT's own tone measure: "
          f"{df['direction'].corr(df['war_tone']):+.3f}")
    print("(negative is the expected sign: escalation coverage reads as more "
          "negative news)")


if __name__ == "__main__":
    main()
