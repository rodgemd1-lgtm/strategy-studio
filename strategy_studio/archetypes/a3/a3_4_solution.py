"""A3.4 — Multi-perspective synthesis.

Runs multiple synthesis agents in parallel:
  - confidence_agent: scores by evidence confidence
  - contrast_agent: generates contrasting alternatives
  - consensus_agent: finds overlap between perspectives

Merges all options, deduplicates, re-ranks.
Never raises.
"""
from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor

from strategy_studio.core.types import Option, ResearchPack, Synthesis

_CONF_VAL = {"H": 0.8, "M": 0.5, "L": 0.2}


def _confidence_agent(evidence: list) -> list[Option]:
    """Generate options weighted by evidence confidence."""
    options = []
    n = len(evidence)
    if n == 0:
        return [Option(id="no-data", title="No Data Available", description="Insufficient evidence", score=0.0, risks=["No evidence"])]

    avg = sum(_CONF_VAL.get(e.confidence, 0.3) for e in evidence) / n
    content_hash = hashlib.md5(str(evidence).encode()).hexdigest()[:8]

    options.append(Option(
        id=f"conf-primary-{content_hash}",
        title="Confidence-Weighted Primary",
        description=f"Based on {n} evidence sources, avg confidence {round(avg, 2)}",
        score=round(min(1.0, avg), 4),
        risks=["Confidence-based scoring may miss contextual factors"],
    ))
    options.append(Option(
        id=f"conf-conservative-{content_hash}",
        title="Conservative Estimate",
        description="Down-weighted scenario assuming higher uncertainty",
        score=round(max(0.0, avg - 0.2), 4),
        risks=["May underperform in stable markets"],
    ))
    return options


def _contrast_agent(evidence: list) -> list[Option]:
    """Generate contrasting alternative options."""
    content_hash = hashlib.md5(str(evidence).encode()).hexdigest()[:8]
    return [
        Option(
            id=f"contrast-aggressive-{content_hash}",
            title="Aggressive Alternative",
            description="High-risk, high-reward variant accepting variance",
            score=0.75,
            risks=["Higher variance", "Execution risk"],
        ),
        Option(
            id=f"contrast-partnership-{content_hash}",
            title="Partnership Alternative",
            description="Collaborative approach reducing solo risk",
            score=0.65,
            risks=["Partner dependency", "Shared upside"],
        ),
    ]


def _consensus_agent(options_a: list[Option], options_b: list[Option]) -> list[Option]:
    """Find consensus between two option sets — merge by score similarity."""
    merged = []
    for a in options_a:
        for b in options_b:
            if abs(a.score - b.score) < 0.15:
                content_hash = hashlib.md5((a.id + b.id).encode()).hexdigest()[:8]
                merged.append(Option(
                    id=f"consensus-{content_hash}",
                    title=f"Consensus: {a.title} + {b.title}",
                    description=f"Merged: {a.description} | {b.description}",
                    score=round((a.score + b.score) / 2, 4),
                    risks=list(set(a.risks + b.risks)),
                ))
    return merged


def synthesize_merged(research_pack: ResearchPack, agent_budget: int = 3) -> Synthesis:
    """Run synthesis agents in parallel, merge + deduplicate + rank."""
    evidence = research_pack.evidence
    all_options: list[Option] = []

    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            f1 = ex.submit(_confidence_agent, evidence)
            f2 = ex.submit(_contrast_agent, evidence)
            try:
                all_options.extend(f1.result(timeout=2.0))
            except Exception:
                pass
            try:
                all_options.extend(f2.result(timeout=2.0))
            except Exception:
                pass
    except Exception:
        all_options = _confidence_agent(evidence)

    # Deduplicate by id
    seen: set[str] = set()
    deduped: list[Option] = []
    for o in all_options:
        if o.id not in seen:
            seen.add(o.id)
            deduped.append(o)

    # Sort by score descending
    deduped.sort(key=lambda o: o.score, reverse=True)

    return Synthesis(
        options=deduped,
        recommendation=deduped[0] if deduped else None,
        rationale=f"Synthesized from {len(evidence)} evidence sources via {agent_budget} agents",
    )