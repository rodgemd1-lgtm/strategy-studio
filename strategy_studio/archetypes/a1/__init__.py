"""
A1 — Strategy Studio IQRSQPI Pipeline (PYTHON_ONLY)
Orchestrates all 7 deterministic archetypes:
  I1 Intent   -> I2 Question -> I3 Research
  -> I4 Solution -> I5 Quality -> I5 Proof -> I6 Integrate
No LLM calls in decision path.  Pure regex / rules / Pydantic.
"""

from __future__ import annotations

import time

from strategy_studio.core.types import (
    InboundPayload,
    AuditRow,
    IntentKey,
)

from .a1_1_intent import classify_intent
from .a1_2_question import generate_questions
from .a1_3_research import execute_research
from .a1_4_solution import synthesize
from .a1_5_quality import validate
from .a1_6_proof import build_proof
from .a1_7_integrate import integrate


def run_iqrsqpi(payload: InboundPayload) -> AuditRow:
    """
    Orchestrate all 7 steps:
        intent -> question -> research -> solution -> quality -> proof -> integrate
    Returns final AuditRow.
    """
    t0 = time.time()

    # I1 — Intent
    intent_key, intent_confidence = classify_intent(payload)

    # I2 — Question
    questions = generate_questions(intent_key, payload)

    # I3 — Research
    research_pack = execute_research(questions)

    # I4 — Solution
    synthesis = synthesize(research_pack)

    # I5 — Quality
    quality = validate(synthesis, intent=intent_key)

    # I6 — Proof
    proof = build_proof(synthesis, quality)

    # I7 — Integrate
    action, audit = integrate(proof, synthesis, intent=intent_key)

    # Update audit with total pipeline duration
    audit.duration_ms = int((time.time() - t0) * 1000)
    return audit
