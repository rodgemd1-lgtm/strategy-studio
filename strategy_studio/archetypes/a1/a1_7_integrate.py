"""
A1.7 — Integrate (PYTHON_ONLY)
Deterministic integration of ProofPacket + Synthesis -> Action + AuditRow.
No LLM calls.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone

from strategy_studio.core.types import (
    ProofPacket,
    Synthesis,
    Action,
    AuditRow,
    IntentKey,
)


def integrate(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey = IntentKey.UNKNOWN,
) -> tuple[Action, AuditRow]:
    """
    Build Action with action_type from IntentKey.
    Build AuditRow with timestamp, archetype, hashes, duration.
    Returns (Action, AuditRow).
    """
    now = datetime.now(timezone.utc)
    start = time.time()

    action = Action(
        action_type=intent.value,
        payload={
            "claim": proof.claim,
            "recommendation": synthesis.recommendation.model_dump() if synthesis.recommendation else {},
            "rationale": synthesis.rationale,
            "confidence": proof.confidence,
        },
        requires_approval=(proof.confidence == "L" or intent == IntentKey.UNKNOWN),
    )

    input_str = f"{intent.value}:{proof.claim}"
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()[:16]
    output_str = synthesis.rationale
    output_hash = hashlib.sha256(output_str.encode()).hexdigest()[:16]

    duration_ms = int((time.time() - start) * 1000)

    status = "PASS" if proof.confidence in ("H", "M") and intent != IntentKey.UNKNOWN else "REVIEW"

    audit = AuditRow(
        timestamp=now,
        archetype="a1",
        mode="PYTHON_ONLY",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=duration_ms,
        status=status,
    )

    return (action, audit)
