"""Word-list (phrase-count) hawkish/dovish scoring, in the spirit of
Apel & Blix Grimaldi (2012) and Correa et al. (2021): a hand-built list of
monetary-policy phrases, each tagged hawkish (+1) or dovish (-1), counted
against document length.
"""
import re
from pathlib import Path

import pandas as pd


def load_wordlist(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df[df["polarity"] != 0].reset_index(drop=True)


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def score_document(text: str, wordlist: pd.DataFrame) -> dict:
    norm = _normalize(text)
    n_words = max(len(norm.split()), 1)
    hawk_hits, dove_hits = 0, 0
    for _, row in wordlist.iterrows():
        phrase = _normalize(row["phrase"])
        count = norm.count(phrase)
        if count == 0:
            continue
        if row["polarity"] > 0:
            hawk_hits += count
        else:
            dove_hits += count
    # net score per 1,000 words, following the standard normalization used
    # for word-list tone measures (e.g. Loughran-McDonald style scaling)
    net_score = (hawk_hits - dove_hits) / n_words * 1000
    return dict(hawk_hits=hawk_hits, dove_hits=dove_hits, n_words=n_words,
                wordlist_score=net_score)
