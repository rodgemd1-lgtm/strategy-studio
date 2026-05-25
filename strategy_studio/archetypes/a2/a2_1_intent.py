"""
A2.1 — Hybrid Intent Classification
Deterministic classification first (regex + keywords).
Falls back to LLM when confidence < 0.7.
Never raises. Returns (IntentKey, confidence) always.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Optional

from strategy_studio.core.types import (
    InboundPayload,
    IntentKey,
    AuditRow,
)

# ── Deterministic patterns (same as A1) ────────────────────────────────────────

_INTENT_PATTERNS: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        r"synthesi[sz]e\s+(?:market\s+)?option[s]?",
        r"build\s+(?:a\s+)?strategy",
        r"strategic\s+option[s]?",
        r"option[s]?\s+for",
        r"strategy\s+for",
        r"develop\s+(?:a\s+)?plan",
    ],
    IntentKey.WARGAME: [
        r"wargame[s]?",
        r"competitor\s+move[s]?",
        r"market\s+simulation",
        r"red\s+team",
        r"war.?game",
        r"scenario\s+planning",
        r"price\s+war",
    ],
    IntentKey.FORECAST: [
        r"forecast[s]?",
        r"predict[s]?",
        r"prediction",
        r"crux",
        r"scenario[s]?\s+planning",
        r"probability\s+of",
    ],
    IntentKey.COMPETITOR_INTEL: [
        r"competitor\s+intel",
        r"competitor\s+intelligence",
        r"competitor\s+change[s]?",
        r"rival\s+analysis",
        r"competitive\s+landscape",
    ],
    IntentKey.CLIENT_INTEL: [
        r"client\s+intel",
        r"client\s+intelligence",
        r"prospect\s+analysis",
        r"wedge\s+offer[s]?",
        r"icp\s+analysis",
    ],
    IntentKey.FALSIFY: [
        r"falsif[y|ication]",
        r"disprove",
        r"null\s+hypothesis",
        r"test\s+(?:the\s+)?belief",
        r" stress\s+test",
        r"invalidate",
    ],
}

_INTENT_KEYWORDS: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        "synthesize", "strategy", "options", "prioritize", "rank",
        "recommendation", "strategic", "plan", "direction",
    ],
    IntentKey.WARGAME: [
        "wargame", "wargaming", "competitor move", "competitor response",
        "countermove", "simulation", "red team", "scenario planning",
        "maneuver", "battle", "market war", "price war",
        "planning",
    ],
    IntentKey.FORECAST: [
        "forecast", "forecasting", "predict", "prediction",
        "scenario", "estimate", "project", "crux", "probability",
        "trend", "outlook", "projection", "next quarter",
        "year performance", "annual outlook", "quarterly",
    ],
    IntentKey.COMPETITOR_INTEL: [
        "competitor", "competition", "competitors", "rival", "competitive",
        "market share", "competitor intel", "competitive analysis",
        "competitive intelligence",
    ],
    IntentKey.CLIENT_INTEL: [
        "client", "prospect", "customer", "icp", "wedge",
        "buyer", "stakeholder", "champion",
    ],
    IntentKey.FALSIFY: [
        "falsify", "disprove", "null hypothesis", "stress test",
        "invalidate", "debunk", "challenge", "hypothesis", "test",
        "prove wrong", "counter-evidence",
    ],
}

# Valid intent values for LLM parsing
_VALID_INTENTS = {ik.value for ik in IntentKey}


def _classify_from_patterns(text: str) -> Optional[tuple[IntentKey, float]]:
    """Regex-based intent classification. Returns first match or None."""
    text_lower = text.lower().strip()
    for intent_key, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                confidence = 0.95 if len(text_lower) < 80 else 0.85
                return (intent_key, confidence)
    return None


def _classify_from_keywords(text: str) -> Optional[tuple[IntentKey, float]]:
    """Keyword-based intent classification. Returns best match or None."""
    text_lower = text.lower().strip()
    best_match: Optional[tuple[IntentKey, float]] = None
    _KEYWORD_ORDER = [
        IntentKey.FALSIFY,
        IntentKey.WARGAME,
        IntentKey.FORECAST,
        IntentKey.COMPETITOR_INTEL,
        IntentKey.CLIENT_INTEL,
        IntentKey.SYNTHESIZE,
    ]
    for intent_key in _KEYWORD_ORDER:
        words = _INTENT_KEYWORDS[intent_key]
        hits = sum(1 for word in words if word.lower() in text_lower)
        if hits > 0:
            confidence = min(0.5 + (hits * 0.1), 0.75)
            if best_match is None or confidence > best_match[1]:
                best_match = (intent_key, confidence)
    return best_match


def _classify_deterministic(text: str) -> tuple[IntentKey, float]:
    """Pure deterministic classification. Same as A1."""
    result = _classify_from_patterns(text)
    if result is not None:
        return result
    result = _classify_from_keywords(text)
    if result is not None:
        return result
    return (IntentKey.UNKNOWN, 0.0)


def _parse_llm_intent(llm_text: str) -> tuple[IntentKey, float]:
    """
    Parse LLM response into IntentKey.
    Looks for intent keywords in the LLM output.
    Returns (IntentKey, confidence) with confidence reflecting LLM certainty.
    """
    text_lower = llm_text.lower().strip()

    # Direct match: LLM returns the intent value
    for intent_value in _VALID_INTENTS:
        if intent_value in text_lower:
            # Map back to IntentKey enum
            for ik in IntentKey:
                if ik.value == intent_value:
                    return (ik, 0.72)

    # Keyword scan of LLM output
    _LLM_KEYWORDS: dict[IntentKey, list[str]] = {
        IntentKey.SYNTHESIZE: ["synthesize", "strategy synthesis", "strategic option", "build strategy"],
        IntentKey.WARGAME: ["wargame", "war game", "competitive simulation", "red team", "competitor move"],
        IntentKey.FORECAST: ["forecast", "predict", "prediction", "crux", "probability"],
        IntentKey.COMPETITOR_INTEL: ["competitor intel", "competitor intelligence", "competitive analysis", "rival"],
        IntentKey.CLIENT_INTEL: ["client intel", "client intelligence", "prospect", "icp", "wedge offer"],
        IntentKey.FALSIFY: ["falsify", "falsification", "disprove", "null hypothesis", "stress test"],
    }

    best_key = IntentKey.UNKNOWN
    best_score = 0
    for ik, keywords in _LLM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_key = ik

    if best_score > 0:
        return (best_key, min(0.70 + (best_score * 0.05), 0.85))

    return (IntentKey.UNKNOWN, 0.0)


def classify_intent_hybrid(
    payload: InboundPayload,
    llm_fallback: Callable[..., str] | None = None,
) -> tuple[IntentKey, float]:
    """
    Hybrid intent classification.
    1. Deterministic pass (regex + keywords).
    2. If confidence < 0.7 and llm_fallback provided, call LLM.
    3. Parse LLM response, return if valid.
    4. Never raises. Falls back to (UNKNOWN, 0.0) on any error.
    """
    try:
        # Step 1: Deterministic classification
        intent_key, confidence = _classify_deterministic(payload.raw_text)

        # Step 2: If confidence is sufficient, return immediately
        if confidence >= 0.7:
            return (intent_key, confidence)

        # Step 3: LLM fallback if available
        if llm_fallback is not None:
            prompt = (
                f"Classify the following request into one of these intents: "
                f"{', '.join(ik.value for ik in IntentKey)}. "
                f"Respond with ONLY the intent label.\n\n"
                f"Request: {payload.raw_text}"
            )
            try:
                llm_response = llm_fallback(prompt)
                if llm_response and isinstance(llm_response, str):
                    llm_intent, llm_confidence = _parse_llm_intent(llm_response)
                    # Use LLM result if it found something
                    if llm_intent != IntentKey.UNKNOWN and llm_confidence > confidence:
                        return (llm_intent, llm_confidence)
            except Exception:
                pass  # LLM call failed, fall through to deterministic result

        # Step 4: Return deterministic result (even if low confidence)
        return (intent_key, confidence)

    except Exception:
        return (IntentKey.UNKNOWN, 0.0)
