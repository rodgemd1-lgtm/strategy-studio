"""
detonation_scorer.py — RIG Sovereign Comms Engine · Detonation Pole Scorer
Lane: H4-BUILD-COMMS-ENGINES | Card: BC-COMMS-DEV-V2

DetonationScore (positive pole, target ≥+16):
  RuptureForce      × 0.18
  SpecificityWeight × 0.16
  SacredWordFracture× 0.14
  IdentityIndictment× 0.12
  FalsifiableBet    × 0.10
  MechanismDensity  × 0.10
  RecursiveProof    × 0.08
  SaveableSentence  × 0.06
  DefectionTest     × 0.06

Final score is the weighted sum, range 0.0–1.0+.
No network calls. stdlib only. Safe for any input.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Sacred words — high-status terms that gain power when broken/inverted.
# Inverted usage scores higher than reverent usage.
# ---------------------------------------------------------------------------
_SACRED_WORDS: list[str] = [
    "ai", "innovation", "transformation", "disruption", "synergy",
    "alignment", "thought leader", "best practice", "paradigm", "agile",
    "pivot", "ecosystem", "scalable", "leverage", "impact", "visionary",
    "mission-driven", "growth hacking", "north star", "game-changer",
    "cutting-edge", "framework", "guru", "evangelist", "authentic",
]

# Words / phrases that invert / break sacred words (raise score)
_BREAKER_WORDS: list[str] = [
    "hallucinated", "wrong", "failed", "broke", "lied", "waste", "myth",
    "never works", "doesn't work", "doesn't", "didn't", "fired", "lost",
    "mistake", "wrong", "overrated", "hype", "useless", "abandoned",
    "obsolete", "dead", "dying", "discredited", "debunked",
]

_CAUSAL_CONNECTIVES: list[str] = [
    r"\bbecause\b", r"\bso\b", r"\bwhich means\b", r"\btherefore\b",
    r"\bthus\b", r"\bas a result\b", r"\bleads to\b", r"\bcauses\b",
    r"\bdrives\b", r"\benables\b", r"\bpowers\b",
]

_PROCESS_NOUNS: list[str] = [
    r"\bmechanism\b", r"\bprocess\b", r"\bpipeline\b", r"\bworkflow\b",
    r"\bsystem\b", r"\blogic\b", r"\balgorithm\b", r"\bprotocol\b",
    r"\barchitecture\b", r"\bloop\b", r"\bcycle\b",
]

# Crowd-defection phrases
_CROWD_PHRASES: list[str] = [
    r"most (cfo|cto|ceo|vp|manager|operator|founder)s?",
    r"the (trend|consensus|conventional wisdom|playbook|advice) is",
    r"everyone (thinks|believes|assumes|says)",
    r"industry (standard|norm|practice)",
    r"(traditional|legacy|old-school|standard) (approach|method|way)",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Unicode-safe lowercase, strip excess whitespace."""
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


def _sentences(text: str) -> list[str]:
    """Split into sentences on . ! ? boundaries."""
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", _normalise(text))


def _per_100_words(count: int, total_words: int) -> float:
    if total_words == 0:
        return 0.0
    return count / total_words * 100


# ---------------------------------------------------------------------------
# Sub-scorers — each returns float in [0.0, 1.0]
# ---------------------------------------------------------------------------

def rupture_force(text: str) -> float:
    """Surprising juxtaposition: contrast signals, sentence-start reversals."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    contrast_patterns = [
        r"\bbut\b", r"\byet\b", r"\bhowever\b", r"\bnot\b",
        r"\binstead\b", r"\bcontrary\b", r"\bactually\b",
        r"\bdespite\b", r"\balthough\b", r"\beven though\b",
        r"\bironic\b", r"\bunexpected\b", r"\bsurpris",
    ]
    contrast_hits = sum(1 for p in contrast_patterns if re.search(p, norm))
    sentences = _sentences(norm)
    reversals = sum(
        1 for s in sentences
        if re.match(r"^(but|not|yet|however|actually|no,|wrong,|stop\.?|wait)", s)
    )
    score = min(1.0, (contrast_hits * 0.04) + (reversals * 0.12))
    return round(score, 4)


def specificity_weight(text: str) -> float:
    """Count numbers, named entities (proper nouns), dates, places per 100 words."""
    if not text.strip():
        return 0.0
    words_list = _words(text)
    total = max(1, len(words_list))
    # Numbers (including dollar amounts, percentages)
    numbers = len(re.findall(r"\b\d[\d,.%$kmb]*\b", text, re.IGNORECASE))
    # Proper nouns heuristic: words starting with uppercase not at sentence start
    proper = len(re.findall(r"(?<=[a-z.!?]\s)[A-Z][a-z]+", text))
    # Date patterns
    dates = len(re.findall(
        r"\b(\d{4}|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|"
        r"monday|tuesday|wednesday|thursday|friday|Q[1-4])\b",
        text, re.IGNORECASE,
    ))
    specifics = numbers + proper + dates
    per100 = _per_100_words(specifics, total)
    score = min(1.0, per100 / 15.0)  # 15 specifics per 100 words = perfect
    return round(score, 4)


def sacred_word_fracture(text: str) -> float:
    """Sacred words followed by a breaker signal."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    sacred_present = [w for w in _SACRED_WORDS if w in norm]
    if not sacred_present:
        return 0.0
    fractures = 0
    for sacred in sacred_present:
        idx = norm.find(sacred)
        while idx != -1:
            window = norm[max(0, idx - 60): idx + len(sacred) + 60]
            if any(b in window for b in _BREAKER_WORDS):
                fractures += 1
            idx = norm.find(sacred, idx + 1)
    score = min(1.0, fractures * 0.25)
    return round(score, 4)


def identity_indictment(text: str) -> float:
    """Density of reader-identity pronouns naming them in context."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    words_list = _words(norm)
    total = max(1, len(words_list))
    identity_patterns = [
        r"\byour\b", r"\byou\b", r"\byour (cfo|cto|ceo|team|company|org)\b",
        r"\byour (boss|manager|vp|founder)\b",
    ]
    hits = sum(len(re.findall(p, norm)) for p in identity_patterns)
    per100 = _per_100_words(hits, total)
    score = min(1.0, per100 / 12.0)
    return round(score, 4)


def falsifiable_bet(text: str) -> float:
    """Forward-looking statements with concrete numbers or dates."""
    if not text.strip():
        return 0.0
    forward_patterns = [
        r"\bby (q[1-4]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|20\d\d)",
        r"\bwill (reach|hit|grow|exceed|generate|return|save|cut|reduce)",
        r"\b(predict|forecast|expect)\b",
        r"\bwithin (\d+ (day|week|month|year))",
        r"\bin the next (\d+|few|six|twelve)",
    ]
    hits = sum(
        len(re.findall(p, text, re.IGNORECASE))
        for p in forward_patterns
    )
    # Only count if a number accompanies the forward claim
    number_adjacent = len(re.findall(
        r"(will|by|forecast|predict|expect).{0,40}\d[\d,.%$kmb]*",
        text, re.IGNORECASE,
    ))
    score = min(1.0, (hits + number_adjacent) * 0.15)
    return round(score, 4)


def mechanism_density(text: str) -> float:
    """Causal connectives + concrete process nouns per 100 words."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    words_list = _words(norm)
    total = max(1, len(words_list))
    causal = sum(1 for p in _CAUSAL_CONNECTIVES if re.search(p, norm))
    process = sum(1 for p in _PROCESS_NOUNS if re.search(p, norm))
    per100 = _per_100_words(causal + process, total)
    score = min(1.0, per100 / 10.0)
    return round(score, 4)


def recursive_proof(text: str) -> float:
    """Self-referential proof signals within the text body."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    proof_patterns = [
        r"\bhere'?s? (the )?(data|proof|result|evidence|number)\b",
        r"\bwe (measured|tested|shipped|deployed|found|ran)\b",
        r"\bthe (data|result|number|metric|evidence) show",
        r"\b(actual|real|measured|verified) (result|impact|data|outcome)\b",
        r"\bproof:",
        r"\b\$[\d,]+\b",  # dollar amounts as proof anchors
    ]
    hits = sum(len(re.findall(p, norm)) for p in proof_patterns)
    score = min(1.0, hits * 0.18)
    return round(score, 4)


def saveable_sentence(text: str) -> float:
    """Standalone sentences ≤ 120 chars that could be screenshot-quoted."""
    if not text.strip():
        return 0.0
    sentences = _sentences(text)
    saveable = [
        s for s in sentences
        if 20 <= len(s) <= 120 and not re.search(r"\b(this|it|they|these|those)\b",
                                                   s.lower().split()[0] if s else "")
    ]
    score = min(1.0, len(saveable) * 0.1)
    return round(score, 4)


def defection_test(text: str) -> float:
    """Statements positioning reader against their current crowd."""
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    hits = sum(len(re.findall(p, norm)) for p in _CROWD_PHRASES)
    # Look for "but we found / but our data / but the reality"
    counter_patterns = [
        r"but (we|our|the reality|the data|what we|what i)",
        r"(instead|actually|in fact|turns out),? (we|the)",
        r"(our data|our results|our experiment|our test)",
    ]
    counter_hits = sum(len(re.findall(p, norm)) for p in counter_patterns)
    score = min(1.0, (hits + counter_hits) * 0.15)
    return round(score, 4)


# ---------------------------------------------------------------------------
# Weights per BC-COMMS-DEV-V2
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "rupture_force":      0.18,
    "specificity_weight": 0.16,
    "sacred_word_fracture": 0.14,
    "identity_indictment": 0.12,
    "falsifiable_bet":    0.10,
    "mechanism_density":  0.10,
    "recursive_proof":    0.08,
    "saveable_sentence":  0.06,
    "defection_test":     0.06,
}


def score(draft: str) -> dict:
    """
    Compute DetonationScore for a draft.

    Returns:
        {
          "score": float,          # 0.0–1.0+ weighted sum
          "components": {
            "rupture_force": float,
            "specificity_weight": float,
            "sacred_word_fracture": float,
            "identity_indictment": float,
            "falsifiable_bet": float,
            "mechanism_density": float,
            "recursive_proof": float,
            "saveable_sentence": float,
            "defection_test": float,
          }
        }
    """
    if not isinstance(draft, str):
        draft = ""
    components: dict[str, float] = {
        "rupture_force":        rupture_force(draft),
        "specificity_weight":   specificity_weight(draft),
        "sacred_word_fracture": sacred_word_fracture(draft),
        "identity_indictment":  identity_indictment(draft),
        "falsifiable_bet":      falsifiable_bet(draft),
        "mechanism_density":    mechanism_density(draft),
        "recursive_proof":      recursive_proof(draft),
        "saveable_sentence":    saveable_sentence(draft),
        "defection_test":       defection_test(draft),
    }
    total = sum(_WEIGHTS[k] * v for k, v in components.items())
    return {"score": round(total, 6), "components": components}
