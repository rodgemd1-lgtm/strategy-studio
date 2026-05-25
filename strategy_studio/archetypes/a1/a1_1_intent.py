"""
A1.1 — Intent (PYTHON_ONLY)
Deterministic classification of InboundPayload -> IntentKey.
Uses regex, keyword lists, Pydantic validation. No model in decision path.
On no match: return (IntentKey.UNKNOWN, 0.0). Never raises.
"""

from __future__ import annotations

import re
from typing import Optional

from strategy_studio.core.types import (
    InboundPayload,
    IntentKey,
    AuditRow,
)

# ── Intent patterns (regex) ────────────────────────────────────────────────────

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

# ── Intent keywords (fallback) ─────────────────────────────────────────────────

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


def _classify_from_patterns(text: str) -> Optional[tuple[IntentKey, float]]:
    """Regex-based intent classification. Returns first match or None."""
    text_lower = text.lower().strip()
    for intent_key, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Confidence based on exactness
                confidence = 0.95 if len(text_lower) < 80 else 0.85
                return (intent_key, confidence)
    return None


def _classify_from_keywords(text: str) -> Optional[tuple[IntentKey, float]]:
    """Keyword-based intent classification. Returns best match or None."""
    text_lower = text.lower().strip()
    best_match: Optional[tuple[IntentKey, float]] = None
    # Check narrower/smore-specific intents first to avoid broad matches winning ties
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


def classify_intent(payload: InboundPayload) -> tuple[IntentKey, float]:
    """
    Deterministic intent classification.
    Returns (IntentKey, confidence).  UNKNOWN + 0.0 if no match.
    Never raises.
    """
    text = payload.raw_text

    # 1. Try regex patterns first
    result = _classify_from_patterns(text)
    if result is not None:
        return result

    # 2. Fallback to keyword matching
    result = _classify_from_keywords(text)
    if result is not None:
        return result

    # 3. Default to UNKNOWN
    return (IntentKey.UNKNOWN, 0.0)
