"""
erosion_scorer.py — RIG Sovereign Comms Engine · Erosion Pole Scorer
Lane: H4-BUILD-COMMS-ENGINES | Card: BC-COMMS-DEV-V2

ErosionScore (negative pole, target ≤-16):
  Compression         × 0.20
  Restraint           × 0.18
  NegativeSpaceWeight × 0.16
  DurationOfSilence   × 0.14
  SingleWordPrecision × 0.12
  AnonymityForce      × 0.10
  AntiAesthetic       × 0.10

Final score is the weighted sum, range 0.0–1.0+.
No network calls. stdlib only. Safe for any input.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", _normalise(text))


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def _avg_sentence_length(text: str) -> float:
    sents = _sentences(text)
    if not sents:
        return 0.0
    total_words = sum(len(s.split()) for s in sents)
    return total_words / len(sents)


# ---------------------------------------------------------------------------
# Sub-scorers — each returns float in [0.0, 1.0]
# ---------------------------------------------------------------------------

def compression(text: str) -> float:
    """
    Approx ratio of 'cuttable' words to total words.
    Cuttable: adjectives, adverbs, filler phrases, redundant qualifiers.
    Higher = more cuttable = less compressed = LOWER restraint.
    For erosion, high compression score (few cuttable words) is desired.
    """
    if not text.strip():
        return 0.0
    words_list = _words(text)
    total = max(1, len(words_list))

    # Filler / cuttable patterns
    filler = [
        r"\bvery\b", r"\breally\b", r"\bquite\b", r"\brather\b",
        r"\bsomewhat\b", r"\bextremely\b", r"\bhighly\b", r"\bincredibly\b",
        r"\bbasically\b", r"\bliterally\b", r"\bjust\b", r"\bactually\b",
        r"\bof course\b", r"\bit is (worth noting|important to note)\b",
        r"\bin terms of\b", r"\bthe fact that\b", r"\bdue to the fact\b",
        r"\bat the end of the day\b", r"\ball in all\b",
    ]
    norm = _normalise(text)
    cuttable = sum(len(re.findall(p, norm)) for p in filler)
    cuttable_ratio = cuttable / total
    # High compression = low cuttable ratio → higher score
    score = max(0.0, 1.0 - (cuttable_ratio * 8.0))
    return round(min(1.0, score), 4)


def restraint(text: str) -> float:
    """
    Restraint coefficient shared with bdf_calculator.
    Penalises adjective density, adverb density, long avg sentence length.
    Returns 0.0–1.0 (1.0 = maximum restraint = Hemingway-like).
    """
    if not text.strip():
        return 0.5  # neutral default
    words_list = _words(text)
    total = max(1, len(words_list))

    # Adjective heuristic: common English adjective suffixes
    adj_suffixes = re.compile(
        r"\b\w+(ful|less|ous|ive|al|ic|ary|able|ible|ent|ant|ish|like)\b"
    )
    adj_count = len(adj_suffixes.findall(_normalise(text)))

    # Adverb heuristic: -ly words
    adv_count = len(re.findall(r"\b\w+ly\b", _normalise(text)))

    adj_density = adj_count / total
    adv_density = adv_count / total
    avg_len = _avg_sentence_length(text)

    # Score: lower density + shorter sentences = higher restraint
    adj_penalty = min(1.0, adj_density * 10)
    adv_penalty = min(1.0, adv_density * 12)
    len_penalty = min(1.0, max(0.0, (avg_len - 10) / 30))  # 10-40 word range

    raw = 1.0 - (adj_penalty * 0.35 + adv_penalty * 0.35 + len_penalty * 0.30)
    return round(max(0.0, min(1.0, raw)), 4)


def negative_space_weight(text: str) -> float:
    """
    Ratio of pause-indicating characters to total characters.
    Whitespace (beyond single spaces), em dashes, ellipses, line breaks.
    """
    if not text.strip():
        return 0.0
    total = max(1, len(text))

    # Count explicit pause chars
    pause_chars = len(re.findall(r"[\n\r—–…]", text))
    # Extra spaces (double+) signal breath / pause
    extra_spaces = len(re.findall(r"  +", text))
    # Explicit dashes used as pauses
    dashes = len(re.findall(r" [-–—] ", text))

    ratio = (pause_chars + extra_spaces + dashes) / total
    score = min(1.0, ratio * 40)  # calibrated so ~2.5% ratio = score 1.0
    return round(score, 4)


def duration_of_silence(text: str, context: dict | None = None) -> float:
    """
    Not applicable to single-text scoring; returns 0 unless context supplies
    last_post_timestamp indicating meaningful silence between posts.
    context = {"last_post_timestamp": "ISO-8601 string", "now_timestamp": "ISO-8601 string"}
    """
    if not context:
        return 0.0
    try:
        from datetime import datetime, timezone
        fmt = "%Y-%m-%dT%H:%M:%S"
        last = context.get("last_post_timestamp", "")
        now_str = context.get("now_timestamp", "")
        if not last or not now_str:
            return 0.0
        t_last = datetime.fromisoformat(last.replace("Z", "+00:00"))
        t_now = datetime.fromisoformat(now_str.replace("Z", "+00:00"))
        days_silent = max(0.0, (t_now - t_last).total_seconds() / 86400)
        # 7+ days of silence = max score; <1 day = 0
        score = min(1.0, days_silent / 7.0)
        return round(score, 4)
    except Exception:
        return 0.0


def single_word_precision(text: str) -> float:
    """Count of single-word sentences + 1-3-word standalone lines."""
    if not text.strip():
        return 0.0
    sentences = _sentences(text)
    single = [s for s in sentences if 1 <= len(s.split()) <= 3]
    score = min(1.0, len(single) * 0.15)
    return round(score, 4)


def anonymity_force(text: str) -> float:
    """
    Un-attributed claims ratio.
    High anonymity: lots of "they/the data/users" with few "I/we".
    Lower anonymity (more I/we) = LOWER erosion score on this axis.
    """
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    first_person = len(re.findall(r"\b(i|we|my|our|me|us)\b", norm))
    third_impersonal = len(re.findall(
        r"\b(they|the data|users|research|studies|people|everyone|"
        r"most|many|some|it|this|that)\b", norm
    ))
    total = max(1, first_person + third_impersonal)
    # High ratio of impersonal = higher anonymity force
    impersonal_ratio = third_impersonal / total
    score = min(1.0, impersonal_ratio * 1.5)
    return round(score, 4)


def anti_aesthetic(text: str) -> float:
    """
    Detection of deliberately-jarring or anti-design elements.
    ALL-CAPS single words, lowercase-only long sections, deliberate blank lines.
    """
    if not text.strip():
        return 0.0
    # ALL-CAPS single words (not acronyms like FBI) as deliberate emphasis
    allcaps_words = len(re.findall(r"\b[A-Z]{3,}\b", text))
    # Deliberately blank lines (two or more consecutive newlines)
    blank_lines = len(re.findall(r"\n\s*\n", text))
    # Deliberate lowercase-only opening (signals style choice)
    lowercase_open = 1 if text[:50].strip() and text[:50].strip()[0].islower() else 0
    hits = allcaps_words + blank_lines + lowercase_open
    score = min(1.0, hits * 0.12)
    return round(score, 4)


# ---------------------------------------------------------------------------
# Weights per BC-COMMS-DEV-V2
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "compression":           0.20,
    "restraint":             0.18,
    "negative_space_weight": 0.16,
    "duration_of_silence":   0.14,
    "single_word_precision": 0.12,
    "anonymity_force":       0.10,
    "anti_aesthetic":        0.10,
}


def score(draft: str, context: dict | None = None) -> dict:
    """
    Compute ErosionScore for a draft.

    Args:
        draft:   the text to score
        context: optional dict with last_post_timestamp + now_timestamp
                 (enables DurationOfSilence scoring)

    Returns:
        {
          "score": float,   # 0.0–1.0+ weighted sum
          "components": {
            "compression": float,
            "restraint": float,
            "negative_space_weight": float,
            "duration_of_silence": float,
            "single_word_precision": float,
            "anonymity_force": float,
            "anti_aesthetic": float,
          }
        }
    """
    if not isinstance(draft, str):
        draft = ""
    components: dict[str, float] = {
        "compression":           compression(draft),
        "restraint":             restraint(draft),
        "negative_space_weight": negative_space_weight(draft),
        "duration_of_silence":   duration_of_silence(draft, context),
        "single_word_precision": single_word_precision(draft),
        "anonymity_force":       anonymity_force(draft),
        "anti_aesthetic":        anti_aesthetic(draft),
    }
    total = sum(_WEIGHTS[k] * v for k, v in components.items())
    return {"score": round(total, 6), "components": components}
