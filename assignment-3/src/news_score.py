"""FinBERT (ProsusAI/finbert) sentiment over news headlines.

The unit of text here is a headline, not a sentence of a policy document, and the
quantity that matters for the estimator is not only the average sentiment of a day's
coverage but its *dispersion*: Rigobon and Sack select days on which the variance of
war-related news was high, which includes days when the news was large but its sign
was ambiguous (three of their seventeen dates are tagged "Unclear").

So each day gets both moments back:
    mean   - how negative the day's war coverage was on average
    sd     - how much the day's headlines disagreed with one another

Caveat carried into the report: FinBERT is trained on financial text, so it reads
"oil surges on Hormuz closure" through a markets lens rather than a geopolitical one.
That is why it is run alongside, not instead of, the hand-built war-risk lexicon.
"""
from __future__ import annotations

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "ProsusAI/finbert"
DEVICE = ("mps" if torch.backends.mps.is_available()
          else "cuda" if torch.cuda.is_available() else "cpu")

_tokenizer = None
_model = None


def _load():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()
        _model.to(DEVICE)
    return _tokenizer, _model


@torch.no_grad()
def score_headlines(headlines: list[str], batch_size: int = 64) -> np.ndarray:
    """Per-headline sentiment, P(positive) - P(negative), one value per headline."""
    if not headlines:
        return np.array([])
    tok, model = _load()
    idx = {v.lower(): k for k, v in model.config.id2label.items()}
    out = []
    for i in range(0, len(headlines), batch_size):
        batch = headlines[i:i + batch_size]
        inputs = tok(batch, return_tensors="pt", padding=True,
                     truncation=True, max_length=64)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        probs = torch.softmax(model(**inputs).logits.float().cpu(), dim=-1)
        out.append((probs[:, idx["positive"]] - probs[:, idx["negative"]]).numpy())
    return np.concatenate(out)


def daily_moments(scores: np.ndarray) -> dict[str, float]:
    """Mean and dispersion of one day's headline scores."""
    if len(scores) == 0:
        return {"mean": np.nan, "sd": np.nan, "n": 0}
    return {
        "mean": float(np.mean(scores)),
        "sd": float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0,
        "n": int(len(scores)),
    }
