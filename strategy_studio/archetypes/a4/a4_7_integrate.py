"""A4.7 — Committed actions only.

Integration produces ONLY committed Actions with:
  - action_type: must be from explicit allowlist
  - payload: must contain specific assignable fields
  - requires_approval: always True for external-facing actions

No recommendations. Only committed actions.
AuditRow always produced. Never raises.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from strategy_studio.core.types import Action, AuditRow, IntentKey, ProofPacket, Synthesis

_ALLOWED_ACTION_TYPES = {
    IntentKey.SYNTHESIZE: "strategy_execute",
    IntentKey.WARGAME: "wargame_execute",
    IntentKey.FORECAST: "forecast_execute",
    IntentKey.COMPETITOR_INTEL: "competitor_response",
    IntentKey.CLIENT_INTEL: "client_outreach",
    IntentKey.FALSIFY: "falsification_test",
    IntentKey.UNKNOWN: "review_needed",
}


def integrate_deterministic(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey,
) -> tuple[Action, AuditRow]:
    """Produce committed Action + AuditRow. Only allowed action types."""
    action_type = _ALLOWED_ACTION_TYPES.get(intent, "review_needed")

    # Payload must contain specific fields
    payload = {
        "claim": proof.claim,
        "evidence_count": len(proof.evidence),
        "source_weights": proof.source_weights,
        "recommendation_id": synthesis.recommendation.id if synthesis.recommendation else "none",
        "option_count": len(synthesis.options),
    }

    # All A4 actions require approval (stricter than A1)
    action = Action(
        action_type=action_type,
        payload=payload,
        requires_approval=True,
    )

    # Audit: append-only
    input_hash = hashlib.md5(proof.claim.encode()).hexdigest()[:16]
    output_hash = hashlib.md5(str(payload).encode()).hexdigest()[:16]

    audit = AuditRow(
        archetype="A4",
        mode="LLM_FREE",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=0,  # filled by orchestrator
        status="completed",
    )

    return (action, audit)