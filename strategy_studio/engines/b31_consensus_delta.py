"""B31 — Consensus delta engine."""
from __future__ import annotations

from strategy_studio.core.types import Evidence, Synthesis

_CONF_VAL = {"H": 0.8, "M": 0.5, "L": 0.2}


def calculate_consensus_delta(
    new_research: list[Evidence],
    existing_synthesis: Synthesis | None = None,
) -> dict[str, float]:
    """Calculate consensus deltas between new research and existing synthesis."""
    if not new_research and not existing_synthesis:
        return {"consensus_delta": 0.0, "evidence_count": 0.0, "avg_confidence": 0.0}

    if existing_synthesis is None or not existing_synthesis.options:
        n = len(new_research)
        if n == 0:
            return {"consensus_delta": 0.0, "evidence_count": 0.0, "avg_confidence": 0.0}
        avg = sum(_CONF_VAL.get(e.confidence, 0.3) for e in new_research) / n
        return {"consensus_delta": avg, "evidence_count": float(n), "avg_confidence": round(avg, 4)}

    # Compare new research confidence vs existing synthesis option scores
    existing_avg = (
        sum(o.score for o in existing_synthesis.options) / len(existing_synthesis.options)
        if existing_synthesis.options else 0.0
    )
    n = len(new_research)
    new_avg = sum(_CONF_VAL.get(e.confidence, 0.3) for e in new_research) / n if n else 0.0

    return {
        "consensus_delta": round(new_avg - existing_avg, 4),
        "evidence_count": float(n),
        "avg_confidence": round(new_avg, 4),
        "existing_confidence": round(existing_avg, 4),
    }