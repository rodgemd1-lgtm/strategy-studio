"""
craft_archetypes.py — RIG Sovereign Comms Engine · Craft Style Scorer
Lane: H4-BUILD-COMMS-ENGINES | Card: BC-COMMS-DEV-V2

5 craft archetypes — each scored 0.0–1.0:
  eminem_density      — internal rhyme density, semantic inversions
  hemingway_compression — short-sentence ratio, S-V-O simplicity, readability
  didion_cadence      — long-buildup → short-landing rhythm
  mccarthy_rhythm     — run-on prose, conjunction chains, no dialog quotes
  wallace_recursion   — footnote parentheticals, nested clauses, meta-commentary

craft_coefficient(scores) → float  MAX of the 5 (best-archetype-wins).

No network calls. stdlib only. Safe for any input.
"""
from __future__ import annotations

import re
import unicodedata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", _normalise(text))


def _word_count(text: str) -> int:
    return len(text.split())


def _syllable_count(word: str) -> int:
    """Very rough syllable estimate (Flesch proxy)."""
    word = word.lower().rstrip(".,!?;:")
    if len(word) <= 3:
        return 1
    count = len(re.findall(r"[aeiou]+", word))
    if word.endswith(("es", "ed", "e")):
        count = max(1, count - 1)
    return max(1, count)


def _flesch_kincaid_ease(text: str) -> float:
    """
    Simplified Flesch Reading Ease (0-100; higher = easier).
    206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    Clamped to [0, 100].
    """
    sentences = _sentences(text)
    words = _words(text)
    if not sentences or not words:
        return 50.0
    avg_sent = len(words) / len(sentences)
    avg_syl = sum(_syllable_count(w) for w in words) / len(words)
    ease = 206.835 - 1.015 * avg_sent - 84.6 * avg_syl
    return round(max(0.0, min(100.0, ease)), 2)


def _word_end_sound(word: str) -> str:
    """Last 2-3 characters as a rhyme proxy (phonetic simplification)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    return w[-3:] if len(w) >= 3 else w


# ---------------------------------------------------------------------------
# 1. Eminem Density
#    Internal rhyme density + semantic inversions + multi-syllable rhymes within sentences.
# ---------------------------------------------------------------------------

def eminem_density(text: str) -> float:
    """
    Scores 0.0-1.0.
    High score: lots of internal/end rhymes, semantic inversions,
    multi-syllable matching word-end sounds within sentences.
    """
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    sentences = _sentences(norm)
    if not sentences:
        return 0.0

    total_rhyme_pairs = 0
    for sent in sentences:
        words_in_sent = re.findall(r"[a-z']+", sent)
        if len(words_in_sent) < 2:
            continue
        sounds = [_word_end_sound(w) for w in words_in_sent]
        # Count matching end-sounds within same sentence (internal rhyme)
        seen: dict[str, int] = {}
        for s in sounds:
            if len(s) >= 2:
                seen[s] = seen.get(s, 0) + 1
        for cnt in seen.values():
            if cnt >= 2:
                total_rhyme_pairs += cnt - 1

    # Semantic inversions: "not X but Y" or "less X more Y" patterns
    inversions = len(re.findall(
        r"(not\s+\w+\s+but|less\s+\w+\s+more|no\s+\w+\s+just|"
        r"never\s+\w+\s+always|instead of\s+\w+)",
        norm,
    ))

    total_words = max(1, len(_words(text)))
    rhyme_density = total_rhyme_pairs / total_words
    inversion_density = inversions / max(1, len(sentences))

    score = min(1.0, rhyme_density * 8 + inversion_density * 0.25)
    return round(score, 4)


# ---------------------------------------------------------------------------
# 2. Hemingway Compression
#    Short-sentence ratio, S-V-O simplicity, low adjective/adverb load, high readability.
# ---------------------------------------------------------------------------

def hemingway_compression(text: str) -> float:
    """
    Scores 0.0-1.0.
    High score: short sentences, simple verb-first constructions,
    few adjectives/adverbs, high Flesch ease.
    """
    if not text.strip():
        return 0.0
    sentences = _sentences(text)
    if not sentences:
        return 0.0

    total = len(sentences)
    short = sum(1 for s in sentences if len(s.split()) <= 12)
    short_ratio = short / total

    norm = _normalise(text)
    words_list = _words(norm)
    word_count = max(1, len(words_list))

    # Adjective/adverb count (rough)
    adj_count = len(re.findall(r"\b\w+(ful|less|ous|ive|al|ic|able|ible)\b", norm))
    adv_count = len(re.findall(r"\b\w+ly\b", norm))
    density = (adj_count + adv_count) / word_count

    flesch = _flesch_kincaid_ease(text) / 100.0  # normalise to 0-1

    # Combine: short_ratio 40%, flesch 40%, low density bonus 20%
    density_score = max(0.0, 1.0 - density * 8)
    score = short_ratio * 0.40 + flesch * 0.40 + density_score * 0.20
    return round(min(1.0, score), 4)


# ---------------------------------------------------------------------------
# 3. Didion Cadence
#    Long buildup → short landing. Detect long sentence followed by 1-3-word sentence.
# ---------------------------------------------------------------------------

def didion_cadence(text: str) -> float:
    """
    Scores 0.0-1.0.
    High score: pattern of long sentence (8+ words) followed by very short
    sentence (1-3 words). Higher variance in sentence lengths.
    """
    if not text.strip():
        return 0.0
    sentences = _sentences(text)
    if len(sentences) < 2:
        return 0.0

    lengths = [len(s.split()) for s in sentences]
    n = len(lengths)

    # Count buildup-then-landing pairs
    pairs = 0
    for i in range(n - 1):
        if lengths[i] >= 8 and lengths[i + 1] <= 3:
            pairs += 1

    # Sentence length variance (normalised)
    mean_len = sum(lengths) / n
    variance = sum((l - mean_len) ** 2 for l in lengths) / n
    # Normalise variance: stdev of 8 is excellent
    stdev = variance ** 0.5
    variance_score = min(1.0, stdev / 8.0)

    pair_score = min(1.0, pairs * 0.25)
    score = pair_score * 0.55 + variance_score * 0.45
    return round(score, 4)


# ---------------------------------------------------------------------------
# 4. McCarthy Rhythm
#    Run-on prose: long comma/conjunction chains, semicolons, absent dialog marks.
# ---------------------------------------------------------------------------

def mccarthy_rhythm(text: str) -> float:
    """
    Scores 0.0-1.0.
    High score: long comma-chains, conjunction repetition (polysyndeton),
    semicolons joining clauses, no quotation marks.
    """
    if not text.strip():
        return 0.0
    norm = _normalise(text)
    words_list = _words(norm)
    total = max(1, len(words_list))

    # Polysyndeton: repetitive "and" / "but" / "or" conjunctions
    and_count = len(re.findall(r"\band\b", norm))
    but_count = len(re.findall(r"\bbut\b", norm))
    polysynd = (and_count + but_count) / total

    # Comma density (run-on indicator)
    comma_density = len(re.findall(r",", text)) / total

    # Semicolons
    semicolon_density = len(re.findall(r";", text)) / total

    # Absence of quotation marks (dialog-free long passages)
    has_dialog = 1 if re.search(r'[""\'\'"]', text) else 0
    dialog_penalty = 0.0 if not has_dialog else 0.2

    score = (
        min(0.4, polysynd * 4) +
        min(0.3, comma_density * 6) +
        min(0.3, semicolon_density * 15) -
        dialog_penalty
    )
    return round(max(0.0, min(1.0, score)), 4)


# ---------------------------------------------------------------------------
# 5. Wallace Recursion
#    Footnote parentheticals, nested clauses, meta-commentary.
# ---------------------------------------------------------------------------

def wallace_recursion(text: str) -> float:
    """
    Scores 0.0-1.0.
    High score: parenthetical asides (nested), meta-commentary phrases,
    footnote-style interruptions, self-aware prose signals.
    """
    if not text.strip():
        return 0.0
    norm = _normalise(text)

    # Parenthetical asides
    parens = len(re.findall(r"\([^)]{5,}\)", text))

    # Nested dashes used as asides
    dashes = len(re.findall(r"—[^—]{5,40}—", text))

    # Meta-commentary phrases
    meta_patterns = [
        r"\(though (one might|it'?s? worth|to be fair)\b",
        r"\bwhich is (to say|another way of)\b",
        r"\bor rather\b",
        r"\bmore (precisely|accurately|honestly)\b",
        r"\bit'?s? (worth noting|fair to say|perhaps)\b",
        r"\bin (other words|a sense)\b",
    ]
    meta = sum(len(re.findall(p, norm)) for p in meta_patterns)

    # Nested clause depth: count "that ... that" or "which ... which"
    nested = len(re.findall(r"\bthat\b.{5,60}\bthat\b", norm))

    total_words = max(1, len(_words(text)))
    hits = parens + dashes + meta + nested
    density = hits / total_words

    score = min(1.0, density * 20 + hits * 0.05)
    return round(score, 4)


# ---------------------------------------------------------------------------
# Aggregate: craft_coefficient
# ---------------------------------------------------------------------------

def all_scores(text: str) -> dict[str, float]:
    """Compute all 5 craft archetype scores."""
    return {
        "eminem_density":        eminem_density(text),
        "hemingway_compression": hemingway_compression(text),
        "didion_cadence":        didion_cadence(text),
        "mccarthy_rhythm":       mccarthy_rhythm(text),
        "wallace_recursion":     wallace_recursion(text),
    }


def craft_coefficient(scores: dict[str, float]) -> float:
    """
    Returns the MAX of the 5 archetype scores (best-archetype-wins).
    Input: dict of {archetype_name: 0.0-1.0 float}.
    """
    if not scores:
        return 0.0
    return round(max(scores.values()), 4)


def score(text: str) -> dict:
    """
    Compute all 5 craft archetype scores + aggregate craft coefficient.

    Returns:
        {
          "craft_coefficient": float,   # MAX of 5 scores
          "best_archetype": str,        # name of archetype with highest score
          "scores": {
            "eminem_density": float,
            "hemingway_compression": float,
            "didion_cadence": float,
            "mccarthy_rhythm": float,
            "wallace_recursion": float,
          }
        }
    """
    if not isinstance(text, str):
        text = ""
    scores = all_scores(text)
    coef = craft_coefficient(scores)
    best = max(scores, key=lambda k: scores[k]) if scores else "hemingway_compression"
    return {
        "craft_coefficient": coef,
        "best_archetype": best,
        "scores": scores,
    }
