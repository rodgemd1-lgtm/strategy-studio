"""A4.6 — Fully deterministic proof packets.

Every field is computed from rules:
  - claim: recommendation.description (or explicit placeholder)
  - evidence: from synthesis options only
  - source_weights: from evidence confidence
  - confidence: from majority vote of evidence confidence

No external lookups. No defaults that aren't rule-derived.
"""
from __future__ import annotations

import hashlib

from strategy_studio.core.types import Evidence, ProofPacket, QualityResult, Synthesis

_CONF_VAL = {"H": 0.8, "M": 0.5, "L": 0.2}


def build_proof_strict(
    synthesis: Synthesis,
    quality: QualityResult,
) -> ProofPacket:
    """Build proof packet from deterministic rules only."""
    # Claim from recommendation
    claim = (
        synthesis.recommendation.description
        if synthesis.recommendation
        else "No recommendation available"
    )

    # Evidence from synthesis options
    evidence: list[Evidence] = []
    for opt in synthesis.options:
        h = hashlib.md5(opt.description.encode()).hexdigest()[:12]
        conf = "H" if opt.score > 0.7 else "M" if opt.score > 0.4 else "L"
        evidence.append(Evidence(
            source_uri=f"synthesis://{opt.id}",
            content_hash=h,
            confidence=conf,
            citations=[opt.title, opt.description],
        ))

    # Source weights from confidence
    weights: dict[str, float] = {}
    for e in evidence:
        weights[e.source_uri] = _CONF_VAL.get(e.confidence, 0.3)

    # Overall confidence: majority vote
    if not evidence:
        overall = "L"
    else:
        avg = sum(_CONF_VAL.get(e.confidence, 0.3) for e in evidence) / len(evidence)
        overall = "H" if avg >= 0.65 else "M" if avg >= 0.4 else "L"

    return ProofPacket(
        claim=claim,
        evidence=evidence,
        source_weights=weights,
        confidence=overall,
    )