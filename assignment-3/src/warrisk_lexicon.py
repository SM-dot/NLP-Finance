"""A purpose-built escalation / de-escalation lexicon for war-risk headlines.

Why not an off-the-shelf dictionary: Loughran-McDonald scores financial disclosure
language and has no notion of military escalation ("ceasefire" and "airstrike" are
both simply absent), and general-purpose sentiment lexicons score "peace talks
collapse" as positive because "peace" is positive. The axis that matters for this
assignment is whether a day's news made war more or less likely, so the list is
built on that axis directly, in the spirit of the hand-built policy-tone lists of
Apel & Blix Grimaldi (2012) and Correa et al. (2021).

Scoring is phrase-level and longest-match-first, so "peace talks collapse" is scored
once as escalating rather than as "peace" (de-escalating) plus "collapse".

Signs follow the direction of *war risk*, not of market sentiment:
  +1  the news makes conflict more likely or more intense
  -1  the news makes conflict less likely or less intense

Rigobon and Sack are explicit that their estimator does not need the sign of the
news - only the days on which its variance was high. The sign is scored here anyway
because it makes the event table readable and because the cross-headline dispersion
of these signed scores is itself the news-variance measure the estimator does need.
"""
from __future__ import annotations

import re

ESCALATION = [
    # kinetic action
    "air strike", "airstrike", "air strikes", "airstrikes", "missile strike",
    "missile attack", "drone attack", "drone strike", "bombing", "bombard",
    "shelling", "launched strikes", "launches strikes", "struck", "strikes on",
    "attack on", "attacks on", "retaliate", "retaliation", "retaliatory",
    "counterattack", "offensive", "invasion", "ground operation", "incursion",
    "killed", "assassinated", "assassination", "casualties", "death toll",
    # escalation language
    "escalate", "escalates", "escalation", "escalating", "widening conflict",
    "wider war", "all-out war", "full-scale war", "spillover", "no longer immune",
    "state of emergency", "war footing", "mobilise", "mobilize", "mobilisation",
    "mobilization", "reinforcements", "carrier strike group", "deploys troops",
    "troop deployment", "evacuate embassy", "embassy evacuation",
    # threats and ultimatums
    "ultimatum", "deadline expires", "deadline expired", "final warning",
    "threatens", "threatened to", "vows revenge", "warns of war", "red line",
    "unconditional surrender", "refuses to negotiate", "rejects proposal",
    "rejects offer", "talks collapse", "talks collapsed", "talks fail",
    "talks failed", "negotiations break down", "peace talks collapse",
    "walks out of talks", "ceasefire collapses", "ceasefire collapsed",
    "ceasefire violation", "truce broken", "breaks ceasefire",
    # maritime and energy chokepoints
    "closes the strait", "close the strait", "strait closure", "blockade",
    "blockades", "mines the strait", "naval mines", "seizes tanker",
    "seized tanker", "tanker attack", "attacks vessels", "attacks shipping",
    "shipping disrupted", "halts oil exports", "oil facility attacked",
    "refinery attacked", "energy infrastructure attacked", "supply disruption",
    # nuclear
    "weapons-grade", "weapons grade", "enrichment breakout", "breakout time",
    "non-compliance", "noncompliance", "snapback", "sanctions reimposed",
    "nuclear test", "withdraws from treaty", "iaea inspectors expelled",
    "inspectors barred",
]

DE_ESCALATION = [
    # agreements and pauses
    "ceasefire agreement", "ceasefire deal", "ceasefire begins", "agrees to ceasefire",
    "ceasefire holds", "ceasefire extended", "truce", "armistice", "stand down",
    "halts strikes", "halt strikes", "pauses strikes", "suspends strikes",
    "de-escalate", "de-escalation", "deescalate", "deescalation", "defuse",
    "restraint", "calm returns", "tensions ease", "tensions easing", "easing tensions",
    # diplomacy
    "peace talks", "peace deal", "peace process", "negotiations resume",
    "talks resume", "resume negotiations", "back channel", "backchannel",
    "mediation", "mediated by", "diplomatic breakthrough", "breakthrough",
    "memorandum of understanding", "framework agreement", "preliminary agreement",
    "deal reached", "agreement reached", "signs agreement", "signed agreement",
    "concession", "concessions", "compromise", "willing to negotiate",
    "returns to the table", "return to talks", "constructive talks",
    "productive talks", "within reach",
    # unwinding
    "sanctions relief", "lifts sanctions", "eases sanctions", "prisoner exchange",
    "prisoner swap", "withdraws troops", "troop withdrawal", "pulls back",
    "reopens the strait", "reopen the strait", "strait reopened", "safe passage",
    "shipping corridor", "maritime corridor", "resumes exports", "oil flows resume",
    "inspectors return", "inspections resume", "monitoring restored",
]

_ALL = ([(p, 1) for p in ESCALATION] + [(p, -1) for p in DE_ESCALATION])
# Longest phrase first so multi-word phrases win over their own substrings.
_ALL.sort(key=lambda t: -len(t[0]))
_PATTERNS = [(re.compile(r"\b" + re.escape(p) + r"\b"), p, s) for p, s in _ALL]

_TOKEN = re.compile(r"[a-z']+")


def score_text(text: str) -> dict[str, float]:
    """Score one headline. Matched spans are blanked out so each word is used once."""
    if not text:
        return {"escalation": 0, "de_escalation": 0, "net": 0.0, "n_words": 0, "hits": ""}
    work = " " + text.lower() + " "
    esc = deesc = 0
    hits: list[str] = []
    for pat, phrase, sign in _PATTERNS:
        n = len(pat.findall(work))
        if n:
            work = pat.sub(" ", work)
            hits.extend([phrase] * n)
            if sign > 0:
                esc += n
            else:
                deesc += n
    n_words = len(_TOKEN.findall(text.lower()))
    return {
        "escalation": esc,
        "de_escalation": deesc,
        "net": float(esc - deesc),
        "n_words": n_words,
        "hits": "|".join(hits),
    }


def polarity(text: str) -> float:
    """Signed war-risk polarity of one headline, bounded to [-1, 1].

    Bounded rather than a raw count so that one long headline stuffed with
    escalation words cannot dominate a day's average.
    """
    s = score_text(text)
    total = s["escalation"] + s["de_escalation"]
    return 0.0 if total == 0 else s["net"] / total
