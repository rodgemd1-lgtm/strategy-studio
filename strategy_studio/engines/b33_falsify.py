"""B33 — Falsification engine."""
from __future__ import annotations

from typing import Literal

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
    status: Literal["open", "passed", "failed"] = "open"
    if not evidence:
        status = "open"
    elif any(e.confidence == "L" for e in evidence):
        status = "failed"

    return FalsificationPacket(
        belief=claim,
        disproof_test=disproof_test,
        pass_criteria=f"Must find 2+ credible sources contradicting: {claim}",
        status=status,
    )