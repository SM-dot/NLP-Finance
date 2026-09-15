"""FinBERT (ProsusAI/finbert) sentence-level sentiment, aggregated to a
document tone score. This is the "language model" method the assignment
asks for, run alongside the word list (Step 2).

Note on interpretation: FinBERT's positive/negative axis is generic
financial-news sentiment, not hawkish/dovish per se. We report both the raw
sentiment score and its correlation with the word-list score, and discuss
the gap in the report (this mirrors a finding in "Parsing the Fed" 2021).
"""
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "ProsusAI/finbert"
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
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


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sents if len(s.split()) >= 4]


@torch.no_grad()
def score_document(text: str, batch_size: int = 16) -> dict:
    tok, model = _load()
    sents = split_sentences(text)
    if not sents:
        return dict(finbert_score=0.0, n_sentences=0, mean_pos=0.0, mean_neg=0.0, mean_neu=0.0)

    labels = model.config.id2label  # {0: positive, 1: negative, 2: neutral}
    probs_all = []
    for i in range(0, len(sents), batch_size):
        batch = sents[i:i + batch_size]
        inputs = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        logits = model(**inputs).logits.cpu()
        probs = torch.softmax(logits, dim=-1)
        probs_all.append(probs)
    probs_all = torch.cat(probs_all, dim=0)

    idx = {v.lower(): k for k, v in labels.items()}
    pos = probs_all[:, idx["positive"]].mean().item()
    neg = probs_all[:, idx["negative"]].mean().item()
    neu = probs_all[:, idx["neutral"]].mean().item()

    return dict(finbert_score=pos - neg, n_sentences=len(sents),
                mean_pos=pos, mean_neg=neg, mean_neu=neu)
