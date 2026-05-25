"""
A2 — Strategy Studio Hybrid Pipeline (Deterministic + LLM Fallback)
Orchestrates all 7 hybrid archetypes:
  I1 Intent   -> I2 Question -> I3 Research
  -> I4 Solution -> I5 Quality -> I5 Proof -> I6 Integrate
Deterministic path first. LLM fallback when confidence < 0.7 or evidence insufficient.
Returns AuditRow. Never raises.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from strategy_studio.core.types import (
    InboundPayload,
    AuditRow,
    IntentKey,
)

from .a2_1_intent import classify_intent_hybrid
from .a2_2_question import generate_questions_hybrid
from .a2_3_research import execute_research_hybrid
from .a2_4_solution import synthesize_hybrid
from .a2_5_quality import validate_hybrid
from .a2_6_proof import build_proof_hybrid
from .a2_7_integrate import integrate_hybrid


def run_hybrid(
    payload: InboundPayload,
    llm_fallback: Callable[..., str] | None = None,
) -> AuditRow:
    """
    Orchestrate all 7 hybrid steps:
        intent -> question -> research -> solution -> quality -> proof -> integrate
    Uses deterministic classification first. Falls back to LLM when confidence < 0.7.
    llm_fallback: async/sync callable(prompt: str) -> str, or None for deterministic-only.
    Returns AuditRow. Never raises.
    """
    t0 = time.time()

    # I1 — Hybrid Intent (deterministic + LLM fallback)
    intent_key, intent_confidence = classify_intent_hybrid(
        payload, llm_fallback=llm_fallback
    )

    # I2 — Hybrid Question (templates first, LLM expansion for edge cases)
    questions = generate_questions_hybrid(
        intent_key, payload, llm_fallback=llm_fallback
    )

    # I3 — Hybrid Research (local + API when evidence gaps)
    research_pack = execute_research_hybrid(
        questions,
        llm_fallback=llm_fallback,
        company=payload.metadata.get("company", ""),
        competitor=payload.metadata.get("competitor", ""),
        market=payload.metadata.get("market", ""),
    )

    # I4 — Hybrid Solution (B-engines first, LLM augmentation)
    synthesis = synthesize_hybrid(
        research_pack, llm_fallback=llm_fallback
    )

    # I5 — Hybrid Quality (dual gates: deterministic + evidence-based)
    quality = validate_hybrid(
        synthesis, intent=intent_key, llm_fallback=llm_fallback
    )

    # I6 — Hybrid Proof (deterministic evidence + LLM reasoning chains)
    proof = build_proof_hybrid(
        synthesis, quality, llm_fallback=llm_fallback
    )

    # I7 — Hybrid Integrate (Actions + LLM-generated recommendations)
    action, audit = integrate_hybrid(
        proof, synthesis, intent=intent_key, llm_fallback=llm_fallback
    )

    # Update audit with total pipeline duration and hybrid mode
    audit.duration_ms = int((time.time() - t0) * 1000)
    audit.mode = "HYBRID"
    return audit
