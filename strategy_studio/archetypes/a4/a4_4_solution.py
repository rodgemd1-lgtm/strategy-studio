"""A4.4 — B-engine exclusive synthesis.

Uses only deterministic B-engines:
  - B29 (synthesize_evidence): evidence → ranked options
  - B33 (falsify_claim): build falsification packet
  - B45 (allocate_budget): budget allocation per option

No LLM. No heuristics. Pure B-engine pipeline.
"""
from __future__ import annotations

import hashlib

from strategy_studio.core.types import Option, ResearchPack, Synthesis, FalsificationPacket
from strategy_studio.engines.b29_synthesize import synthesize_evidence
from strategy_studio.engines.b33_falsify import falsify_claim
from strategy_studio.engines.b45_budget_allocation import allocate_budget


def synthesize_deterministic(research_pack: ResearchPack) -> Synthesis:
    """Pure B-engine synthesis path."""
    evidence = research_pack.evidence

    # B29: evidence synthesis
    synthesis = synthesize_evidence(evidence)

    # B33: falsification packet on recommendation
    if synthesis.recommendation:
        fp = falsify_claim(synthesis.recommendation.description, evidence)
        # Attach falsification to synthesis rationale
        synthesis.rationale += f" | Falsification: {fp.disproof_test}"

    # B45: budget allocation per option
    budget_alloc = allocate_budget(synthesis.options, total_budget=1_000_000.0)
    for i, alloc in enumerate(budget_alloc):
        if i < len(synthesis.options):
            synthesis.options[i].risks.append(
                f"Budget: ${alloc.get('budget', 0):,.0f} ({alloc.get('allocation_percentage', 0)}%)"
            )

    return synthesis