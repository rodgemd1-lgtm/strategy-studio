"""
A2.7 — Hybrid Integration (Actions + LLM Recommendations)
Deterministic Action + AuditRow construction (same as A1).
Adds LLM-generated recommendations alongside Actions.
Never raises. Returns (Action, AuditRow) always.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from datetime import datetime, timezone

from strategy_studio.core.types import (
    ProofPacket,
    Synthesis,
    Action,
    AuditRow,
    IntentKey,
)


def _build_action(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey,
) -> Action:
    """Build deterministic Action (same as A1)."""
    return Action(
        action_type=intent.value,
        payload={
            "claim": proof.claim,
            "recommendation": (
                synthesis.recommendation.model_dump()
                if synthesis.recommendation
                else {}
            ),
            "rationale": synthesis.rationale,
            "confidence": proof.confidence,
        },
        requires_approval=(proof.confidence == "L" or intent == IntentKey.UNKNOWN),
    )


def _build_audit(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey,
) -> AuditRow:
    """Build deterministic AuditRow (same as A1)."""
    now = datetime.now(timezone.utc)

    input_str = f"{intent.value}:{proof.claim}"
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()[:16]
    output_str = synthesis.rationale
    output_hash = hashlib.sha256(output_str.encode()).hexdigest()[:16]

    status = (
        "PASS"
        if proof.confidence in ("H", "M") and intent != IntentKey.UNKNOWN
        else "REVIEW"
    )

    return AuditRow(
        timestamp=now,
        archetype="a2",
        mode="HYBRID",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=0,  # will be set by orchestrator
        status=status,
    )


def _generate_llm_recommendations(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey,
    llm_fallback: Callable[..., str],
) -> list[str]:
    """
    Generate LLM recommendations alongside the deterministic Action.
    Returns list of recommendation strings.
    """
    options_summary = "\n".join(
        f"- {o.title}: {o.description} (score: {o.score})"
        for o in synthesis.options
    )
    prompt = (
        f"Based on the following strategy analysis, provide 2-3 actionable recommendations. "
        f"Intent: {intent.value}. Confidence: {proof.confidence}.\n\n"
        f"Recommendation: {proof.claim}\n\n"
        f"Options:\n{options_summary}\n\n"
        f"Rationale: {synthesis.rationale}\n\n"
        f"Recommendations (one per line):"
    )
    try:
        response = llm_fallback(prompt)
        if response and isinstance(response, str):
            recommendations: list[str] = []
            for line in response.strip().split("\n"):
                cleaned = line.strip().lstrip("-*0123456789.) \t")
                if cleaned and len(cleaned) > 5:
                    recommendations.append(cleaned)
            return recommendations[:5]
    except Exception:
        pass
    return []


def integrate_hybrid(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey = IntentKey.UNKNOWN,
    llm_fallback: Callable[..., str] | None = None,
) -> tuple[Action, AuditRow]:
    """
    Hybrid integration.
    1. Deterministic Action + AuditRow (same as A1).
    2. If LLM available, generate additional recommendations.
    3. Attach LLM recommendations to Action payload.
    4. Never raises. Returns (Action, AuditRow) always.
    """
    try:
        # Step 1: Deterministic Action + AuditRow
        action = _build_action(proof, synthesis, intent)
        audit = _build_audit(proof, synthesis, intent)

        # Step 2: LLM recommendations
        if llm_fallback is not None:
            try:
                recommendations = _generate_llm_recommendations(
                    proof, synthesis, intent, llm_fallback
                )
                if recommendations:
                    action.payload["llm_recommendations"] = recommendations
            except Exception:
                pass  # LLM recommendations failed, continue without them

        return (action, audit)

    except Exception:
        # Safe fallback
        fallback_action = Action(
            action_type="error",
            payload={"error": "Integration failed"},
            requires_approval=True,
        )
        fallback_audit = AuditRow(
            timestamp=datetime.now(timezone.utc),
            archetype="a2",
            mode="HYBRID",
            input_hash="error",
            output_hash="error",
            duration_ms=0,
            status="ERROR",
        )
        return (fallback_action, fallback_audit)
