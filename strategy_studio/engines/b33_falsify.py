"""B33 — Falsification engine."""
from __future__ import annotations

from strategy_studio.core.types import Evidence, FalsificationPacket, IntentKey

_DISPROOF_PATTERNS = {
    IntentKey.SYNTHESIZE: "Find data showing opposite trend",
    IntentKey.WARGAME: "Find competitor already executing variant",
    IntentKey.FORECAST: "Find historical data contradicting baseline assumption",
    IntentKey.FALSIFY: "Find direct counter-evidence or logical contradiction",
    IntentKey.COMPETITOR_INTEL: "Find competitor move that invalidates the thesis",
    IntentKey.CLIENT_INTEL: "Find segment data showing negative willingness-to-pay",
}


def _detect_intent(claim: str) -> IntentKey:
    lower = claim.lower()
    for intent in (IntentKey.SYNTHESIZE, IntentKey.WARGAME, IntentKey.FORECAST,
                   IntentKey.COMPETITOR_INTEL, IntentKey.CLIENT_INTEL, IntentKey.FALSIFY):
        if intent.name.lower().replace("_", " ") in lower or intent.name.lower() in lower:
            return intent
    return IntentKey.SYNTHESIZE


def falsify_claim(claim: str, evidence: list[Evidence]) -> FalsificationPacket:
    intent = _detect_intent(claim)
    disproof_test = _DISPROOF_PATTERNS.get(
        intent, "Find direct counter-evidence or logical contradiction"
    )
    verdict = "untested"
    if not evidence:
        verdict = "insufficient_evidence"
    elif any(e.confidence_score < 0.3 for e in evidence):
        verdict = "risky"

    return FalsificationPacket(
        claim=claim,
        intent=intent,
        disproof_test=disproof_test,
        verdict=verdict,
    )
