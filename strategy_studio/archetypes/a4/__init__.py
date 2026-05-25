"""
A4 — LLM-Free Pure Deterministic Pipeline
Orchestrates all 7 steps with ZERO tolerance for non-deterministic behavior.
Every output is traceable to a specific rule + input. No guessing.
If any step cannot complete deterministically, returns UNKNOWN status.
"""
from __future__ import annotations

import time

from strategy_studio.core.types import (
    InboundPayload,
    AuditRow,
    IntentKey,
)

from .a4_1_intent import classify_intent_strict
from .a4_2_question import generate_questions_strict
from .a4_3_research import execute_research_local
from .a4_4_solution import synthesize_deterministic
from .a4_5_quality import validate_strict
from .a4_6_proof import build_proof_strict
from .a4_7_integrate import integrate_deterministic


def run_llm_free(payload: InboundPayload) -> AuditRow:
    """
    Orchestrate all 7 steps with pure deterministic execution.
    If any step fails to complete deterministically, status = 'UNKNOWN'.
    Returns final AuditRow.
    """
    t0 = time.time()

    # A4.1 — Intent (strict)
    intent_key, intent_confidence = classify_intent_strict(payload)
    if intent_key == IntentKey.UNKNOWN:
        return AuditRow(
            archetype="A4", mode="LLM_FREE",
            input_hash=str(hash(payload.raw_text))[:16],
            output_hash="unknown",
            duration_ms=int((time.time() - t0) * 1000),
            status="UNKNOWN",
        )

    # A4.2 — Question (strict templates only)
    questions = generate_questions_strict(intent_key, payload)
    if not questions:
        return AuditRow(
            archetype="A4", mode="LLM_FREE",
            input_hash=str(hash(payload.raw_text))[:16],
            output_hash="no_questions",
            duration_ms=int((time.time() - t0) * 1000),
            status="INCOMPLETE",
        )

    # A4.3 — Research (local only)
    research_pack = execute_research_local(questions, payload)

    # A4.4 — Solution (B-engines only)
    synthesis = synthesize_deterministic(research_pack)

    # A4.5 — Quality (strictest gates)
    quality = validate_strict(synthesis, intent_key)
    if not quality.passed:
        return AuditRow(
            archetype="A4", mode="LLM_FREE",
            input_hash=str(hash(payload.raw_text))[:16],
            output_hash="quality_failed",
            duration_ms=int((time.time() - t0) * 1000),
            status="QUALITY_FAILED",
        )

    # A4.6 — Proof (fully deterministic)
    proof = build_proof_strict(synthesis, quality)

    # A4.7 — Integrate (committed actions only)
    action, audit = integrate_deterministic(proof, synthesis, intent_key)

    audit.duration_ms = int((time.time() - t0) * 1000)
    return audit