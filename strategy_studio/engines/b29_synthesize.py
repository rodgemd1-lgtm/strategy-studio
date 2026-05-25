"""B29 — Evidence-weighted synthesis engine."""
from __future__ import annotations

from strategy_studio.core.types import Evidence, Synthesis, Option


def _option_template(label: str, score: float, rationale: str) -> Option:
    return Option(label=label, score=round(score, 4), rationale=rationale)


def synthesize_evidence(evidence: list[Evidence]) -> Synthesis:
    """Takes list of Evidence, produces ranked options with scoring."""
    total_ec = sum(e.evidence_count for e in evidence)
    total_conf = sum(e.confidence_score * e.evidence_count for e in evidence)

    if total_ec == 0:
        score = 0.5
    else:
        score = total_conf / total_ec

    options: list[Option] = []
    options.append(
        _option_template(
            "Primary Recommendation",
            score,
            f"Evidence-weighted score from {len(evidence)} sources."
        )
    )
    options.append(
        _option_template(
            "Conservative Alternative",
            max(0.0, score - 0.15),
            "Down-weighted scenario with lower confidence.",
        )
    )
    options.append(
        _option_template(
            "Aggressive Alternative",
            min(1.0, score + 0.15),
            "Up-weighted scenario accepting higher variance.",
        )
    )
    if len(evidence) >= 3:
        options.append(
            _option_template(
                "Outlier Scenario",
                score * 0.6 if score > 0.5 else score * 1.4,
                "Constructed from weakest evidence sources.",
            )
        )
    if len(evidence) >= 4:
        options.append(
            _option_template(
                "Consensus Blend",
                total_conf / (total_ec + 1),
                "Averaged across all inputs with dampening.",
            )
        )

    # Re-sort descending by score
    options = sorted(options, key=lambda o: o.score, reverse=True)
    winner_index = 0
    return Synthesis(
        question="synthesized",
        options=options,
        winner_index=winner_index,
    )
