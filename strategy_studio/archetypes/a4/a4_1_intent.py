"""A4.1 — Strict deterministic intent classification.

3x more patterns than A1. Exact matching only — no heuristics.
If no exact match: returns UNKNOWN immediately. Never guesses.
"""
from __future__ import annotations

import re

from strategy_studio.core.types import InboundPayload, IntentKey

# Exact regex patterns — no fuzzy matching
_PATTERNS_STRICT: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        r"\bsynthesi[sz]e\b",
        r"\bsynthesi[sz]e\s+market\s+option",
        r"\bsynthesi[sz]e\s+strategic\s+option",
        r"\bbuild\s+(?:a\s+)?strateg(?:y|ic)\b",
        r"\bstrategic\s+plan\b",
        r"\bstrategic\s+option[s]?\b",
        r"\bdevelop\s+(?:a\s+)?plan\b",
        r"\bcreate\s+(?:a\s+)?strategy\b",
        r"\bmarket\s+entry\s+strategy\b",
        r"\bpriorit(?:y|ies)\b",
        r"\brank\s+option[s]?\b",
        r"\boption[s]?\s+(?:for|analysis)\b",
    ],
    IntentKey.WARGAME: [
        r"\bwargame[s]?\b",
        r"\bwargaming\b",
        r"\bcompetitor\s+move[s]?\b",
        r"\bcompetitor\s+response\b",
        r"\bmarket\s+simulation\b",
        r"\bred\s+team\b",
        r"\bwar[\s.-]?game\b",
        r"\bscenario\s+planning\b",
        r"\bprice\s+war\b",
        r"\bcounter[\s-]?move\b",
        r"\bcompetitive\s+simulation\b",
        r"\bbattle\s+plan\b",
    ],
    IntentKey.FORECAST: [
        r"\bforecast[s]?\b",
        r"\bforecasting\b",
        r"\bpredict(?:ion|s|ive)?\b",
        r"\bcrux\b",
        r"\bprobability\s+of\b",
        r"\bwill\s+(?:the\s+)?market\b",
        r"\bmarket\s+growth\b",
        r"\bestimate\b",
        r"\bproject(?:ed|ion)?\b",
        r"\btrend\s+analysis\b",
        r"\boutlook\b",
        r"\bfuture\s+performance\b",
    ],
    IntentKey.COMPETITOR_INTEL: [
        r"\bcompetitor\s+intel\b",
        r"\bcompetitor\s+intelligence\b",
        r"\brival\s+analysis\b",
        r"\bcompetitive\s+landscape\b",
        r"\bcompetitive\s+analysis\b",
        r"\bcompetitor\s+tracking\b",
        r"\bwhat\s+are\s+competitors\b",
        r"\bmoves?\s+by\s+competitors\b",
        r"\bcompetitive\s+positioning\b",
        r"\bmarket\s+share\b",
        r"\bcompetitor\s+(?:product|roadmap|strategy)\b",
    ],
    IntentKey.CLIENT_INTEL: [
        r"\bclient\s+intel\b",
        r"\bclient\s+intelligence\b",
        r"\bprospect\s+analysis\b",
        r"\bwedge\s+offer[s]?\b",
        r"\bicp\s+analysis\b",
        r"\bideal\s+customer\s+profile\b",
        r"\bbuyer\s+(?:persona|analysis)\b",
        r"\bprospect\s+needs\b",
        r"\bwhat\s+do\s+buyers\b",
        r"\bentry\s+wedge\b",
    ],
    IntentKey.FALSIFY: [
        r"\bfalsif(y|ication|ied)\b",
        r"\bdisprove\b",
        r"\bnull\s+hypothesis\b",
        r"\btest\s+(?:the\s+)?(?:belief|assumption)\b",
        r"\bstress\s+test\b",
        r"\binvalidate\b",
        r"\bdebunk\b",
        r"\bcounter[\s-]?evidence\b",
        r"\bwhat\s+would\s+disprove\b",
        r"\bhow\s+could\s+(?:this|we)\s+(?:fail|be\s+wrong)\b",
        r"\bprove\s+(?:me\s+)?wrong\b",
    ],
}

# Exact keyword match — word boundaries required
_KEYWORD_SETS: dict[IntentKey, set[str]] = {
    IntentKey.SYNTHESIZE: {"synthesize", "strategy", "strategic", "options", "prioritize", "plan", "direction", "recommendation"},
    IntentKey.WARGAME: {"wargame", "wargaming", "competitor", "response", "simulation", "red team", "scenario", "counter", "battle"},
    IntentKey.FORECAST: {"forecast", "predict", "prediction", "crux", "estimate", "projection", "trend", "outlook", "probability"},
    IntentKey.COMPETITOR_INTEL: {"competitor", "rival", "competitive", "landscape", "market share", "tracking"},
    IntentKey.CLIENT_INTEL: {"client", "prospect", "customer", "icp", "wedge", "buyer", "stakeholder"},
    IntentKey.FALSIFY: {"falsify", "disprove", "invalidate", "debunk", "counter-evidence", "null hypothesis"},
}


def classify_intent_strict(payload: InboundPayload) -> tuple[IntentKey, float]:
    """Strict deterministic intent. Exact patterns only. UNKNOWN if no match."""
    text = payload.raw_text.lower().strip()

    # Phase 1: exact regex match
    for intent, patterns in _PATTERNS_STRICT.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                confidence = 0.95 if len(text) < 60 else 0.85
                return (intent, confidence)

    # Phase 2: exact keyword match (2+ keywords required)
    best: tuple[IntentKey, float] = (IntentKey.UNKNOWN, 0.0)
    words = set(re.findall(r'\b\w+\b', text))
    for intent in (IntentKey.FALSIFY, IntentKey.WARGAME, IntentKey.FORECAST,
                   IntentKey.COMPETITOR_INTEL, IntentKey.CLIENT_INTEL, IntentKey.SYNTHESIZE):
        hits = words & _KEYWORD_SETS[intent]
        if len(hits) >= 2:
            conf = min(0.5 + len(hits) * 0.08, 0.75)
            if conf > best[1]:
                best = (intent, conf)

    return best