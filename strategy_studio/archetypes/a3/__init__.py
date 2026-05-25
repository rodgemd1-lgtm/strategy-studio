"""
A3 — Agent-Bounded Multi-Agent Coordination
Orchestrates all 7 steps with bounded parallel sub-agents.
Each step runs N agents in parallel and merges via deterministic consensus.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from strategy_studio.core.types import (
    InboundPayload,
    AuditRow,
    IntentKey,
)

from .a3_1_intent import classify_intent_voted
from .a3_2_question import generate_questions_parallel
from .a3_3_research import execute_research_parallel
from .a3_4_solution import synthesize_merged
from .a3_5_quality import validate_consensus
from .a3_6_proof import build_proof_merged
from .a3_7_integrate import integrate_consensus


def run_agent_bounded(
    payload: InboundPayload,
    agent_budget: int = 3,
    max_workers: int = 4,
) -> AuditRow:
    """
    Orchestrate all 7 steps with bounded multi-agent execution.
    Each step runs `agent_budget` sub-agents in parallel and merges results.
    Returns final AuditRow.
    """
    t0 = time.time()

    # A3.1 — Intent (voted)
    intent_key, intent_confidence = classify_intent_voted(payload, agent_budget)

    # A3.2 — Question (parallel)
    questions = generate_questions_parallel(intent_key, payload, agent_budget)

    # A3.3 — Research (parallel evidence gathering)
    research_pack = execute_research_parallel(questions, agent_budget, max_workers)

    # A3.4 — Solution (multi-perspective synthesis)
    synthesis = synthesize_merged(research_pack, agent_budget)

    # A3.5 — Quality (parallel gate consensus)
    quality = validate_consensus(synthesis, intent_key, agent_budget)

    # A3.6 — Proof (multi-agent proof)
    proof = build_proof_merged(synthesis, quality, agent_budget)

    # A3.7 — Integrate (conflict resolution)
    action, audit = integrate_consensus(proof, synthesis, intent_key)

    audit.duration_ms = int((time.time() - t0) * 1000)
    return audit