"""
A2.6 — Hybrid Proof Packets
Deterministic evidence collection (same as A1).
Adds LLM reasoning chains for each evidence item.
Includes both deterministic evidence + LLM reasoning in proof packet.
Never raises. Returns ProofPacket always.
"""

from __future__ import annotations

from collections.abc import Callable

from strategy_studio.core.types import (
    Synthesis,
    QualityResult,
    ProofPacket,
    Evidence,
    AuditRow,
)


def _build_deterministic_evidence(
    synthesis: Synthesis,
) -> tuple[list[Evidence], dict[str, float]]:
    """
    Build evidence list and source_weights from synthesis (same as A1).
    Returns (evidence_list, source_weights).
    """
    evidence_list: list[Evidence] = []
    source_weights: dict[str, float] = {}

    for opt in synthesis.options:
        ev = Evidence(
            source_uri=f"proof://option/{opt.id}",
            content_hash=opt.id,
            confidence="M",
            citations=[opt.title],
        )
        evidence_list.append(ev)
        source_weights[opt.id] = opt.score

    return evidence_list, source_weights


def _generate_llm_reasoning(
    claim: str,
    evidence: list[Evidence],
    llm_fallback: Callable[..., str],
) -> str:
    """
    Generate LLM reasoning chain for a claim given evidence.
    Returns reasoning string. Falls back to empty string on error.
    """
    evidence_summary = "\n".join(
        f"- {ev.source_uri} (confidence: {ev.confidence})" for ev in evidence[:5]
    )
    prompt = (
        f"Given the following claim and evidence, provide a brief reasoning chain "
        f"(2-3 sentences) explaining how the evidence supports or contradicts the claim.\n\n"
        f"Claim: {claim}\n\n"
        f"Evidence:\n{evidence_summary}\n\n"
        f"Reasoning:"
    )
    try:
        reasoning = llm_fallback(prompt)
        if reasoning and isinstance(reasoning, str):
            return reasoning.strip()
    except Exception:
        pass
    return ""


def build_proof_hybrid(
    synthesis: Synthesis,
    quality: QualityResult,
    llm_fallback: Callable[..., str] | None = None,
) -> ProofPacket:
    """
    Hybrid proof packet construction.
    1. Deterministic evidence collection (same as A1).
    2. If LLM available, generate reasoning chains for evidence.
    3. Include reasoning in evidence citations.
    4. Never raises. Returns ProofPacket always.
    """
    try:
        # Step 1: Deterministic evidence
        evidence_list, source_weights = _build_deterministic_evidence(synthesis)

        # Step 2: Determine confidence
        count = len(evidence_list)
        if count >= 3:
            confidence: str = "H"
        elif count == 2:
            confidence = "M"
        elif count == 1:
            confidence = "L"
        else:
            confidence = "M"

        # Step 3: Build claim
        claim = (
            synthesis.recommendation.title
            if synthesis.recommendation
            else "No recommendation"
        )

        # Step 4: LLM reasoning chains
        if llm_fallback is not None and evidence_list:
            reasoning = _generate_llm_reasoning(
                claim, evidence_list, llm_fallback
            )
            if reasoning:
                # Add reasoning as an additional evidence item
                reasoning_ev = Evidence(
                    source_uri="llm://reasoning_chain",
                    content_hash=str(hash(reasoning) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                    confidence="M",
                    citations=[reasoning[:200]],  # truncate for citation
                )
                evidence_list.append(reasoning_ev)
                source_weights["llm_reasoning"] = 0.5

        return ProofPacket(
            claim=claim,
            evidence=evidence_list,
            source_weights=source_weights,
            confidence=confidence,
        )

    except Exception:
        return ProofPacket(
            claim="Error in proof construction",
            evidence=[],
            source_weights={},
            confidence="L",
        )
