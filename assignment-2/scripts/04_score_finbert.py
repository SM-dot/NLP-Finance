import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from tqdm import tqdm

from config import INTERIM
import finbert_score as fb


def main():
    docs = pd.read_csv(INTERIM / "documents.csv")
    print(f"Device: {fb.DEVICE}")

    scores = []
    for _, row in tqdm(docs.iterrows(), total=len(docs)):
        text = Path(row["path"]).read_text(encoding="utf-8")
        s = fb.score_document(text)
        scores.append(s)

    scores_df = pd.DataFrame(scores)
    out = pd.concat([docs.reset_index(drop=True), scores_df], axis=1)
    out.to_csv(INTERIM / "documents_finbert_scored.csv", index=False)
    print(f"Saved -> {INTERIM / 'documents_finbert_scored.csv'}")
    print(out.groupby("chair")["finbert_score"].describe()[["count", "mean", "std"]])


if __name__ == "__main__":
    main()
