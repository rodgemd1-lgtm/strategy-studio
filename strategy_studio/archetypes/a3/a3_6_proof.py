"""A3.6 — Multi-agent proof building.

Runs multiple proof builders in parallel:
  - evidence_agent: builds evidence list from synthesis
  - weight_agent: computes source weights
  - confidence_agent: determines overall confidence

Merges into a single ProofPacket.
Never raises.
"""
from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor

from strategy_studio.core.types import Evidence, ProofPacket, QualityResult, Synthesis


def _evidence_agent(synthesis: Synthesis) -> list[Evidence]:
    """Build evidence list from synthesis options."""
    evidence = []
    for opt in synthesis.options:
        content_hash = hashlib.md5(opt.description.encode()).hexdigest()[:12]
        evidence.append(Evidence(
            source_uri=f"synthesis://{opt.id}",
            content_hash=content_hash,
            confidence="H" if opt.score > 0.7 else "M" if opt.score > 0.4 else "L",
            citations=[opt.title, opt.description],
        ))
    return evidence


def _weight_agent(evidence: list[Evidence]) -> dict[str, float]:
    """Compute source weights from evidence."""
    weights: dict[str, float] = {}
    for e in evidence:
        uri = e.source_uri
        val = {"H": 0.8, "M": 0.5, "L": 0.2}.get(e.confidence, 0.3)
        weights[uri] = max(weights.get(uri, 0.0), val)
    return weights


def _confidence_agent(evidence: list[Evidence]) -> str:
    """Determine overall confidence from evidence."""
    if not evidence:
        return "L"
    avg = sum({"H": 0.8, "M": 0.5, "L": 0.2}.get(e.confidence, 0.3) for e in evidence) / len(evidence)
    if avg >= 0.65:
        return "H"
    elif avg >= 0.4:
        return "M"
    return "L"


def build_proof_merged(
    synthesis: Synthesis,
    quality: QualityResult,
    agent_budget: int = 3,
) -> ProofPacket:
    """Run proof agents in parallel, merge into ProofPacket."""
    evidence: list[Evidence] = []
    weights: dict[str, float] = {}
    confidence = "L"

    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            f1 = ex.submit(_evidence_agent, synthesis)
            try:
                evidence = f1.result(timeout=2.0)
            except Exception:
                evidence = []
            f2 = ex.submit(_weight_agent, evidence)
            f3 = ex.submit(_confidence_agent, evidence)
            try:
                weights = f2.result(timeout=2.0)
            except Exception:
                weights = {}
            try:
                confidence = f3.result(timeout=2.0)
            except Exception:
                confidence = "L"
    except Exception:
        evidence = _evidence_agent(synthesis)
        weights = _weight_agent(evidence)
        confidence = _confidence_agent(evidence)

    claim = synthesis.recommendation.description if synthesis.recommendation else "No recommendation"
    return ProofPacket(
        claim=claim,
        evidence=evidence,
        source_weights=weights,
        confidence=confidence,
    )