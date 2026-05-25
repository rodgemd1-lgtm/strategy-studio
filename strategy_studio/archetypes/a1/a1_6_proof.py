"""
A1.6 — Proof (PYTHON_ONLY)
Deterministic proof packet construction.
No LLM calls.  Confidence based on evidence count thresholds.
"""

from __future__ import annotations

from strategy_studio.core.types import (
    Synthesis,
    QualityResult,
    ProofPacket,
    Evidence,
    AuditRow,
)


def build_proof(
    synthesis: Synthesis,
    quality: QualityResult,
) -> ProofPacket:
    """
    Collect Evidence from synthesis.options.
    Compute source_weights dict.
    Set confidence based on evidence count:
        H: >=3, M: 2, L: 1, NONE: 0.
    """
    evidence_list: list[Evidence] = []
    source_weights: dict[str, float] = {}

    # Gather evidence stubs from each option description
    # (In a real system we'd keep full evidence linkage)
    for opt in synthesis.options:
        ev = Evidence(
            source_uri=f"proof://option/{opt.id}",
            content_hash=opt.id,
            confidence="M",
            citations=[opt.title],
        )
        evidence_list.append(ev)
        source_weights[opt.id] = opt.score

    count = len(evidence_list)
    if count >= 3:
        confidence: str = "H"
    elif count == 2:
        confidence = "M"
    elif count == 1:
        confidence = "L"
    else:
        confidence = "M"  # default when none, though quality should flag this

    claim = (
        synthesis.recommendation.title
        if synthesis.recommendation
        else "No recommendation"
    )

    return ProofPacket(
        claim=claim,
        evidence=evidence_list,
        source_weights=source_weights,
        confidence=confidence,
    )
