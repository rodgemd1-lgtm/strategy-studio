"""B29 — Evidence-weighted synthesis engine."""
from __future__ import annotations

from strategy_studio.core.types import Evidence, Synthesis, Option


def _confidence_val(c: str) -> float:
    return {"H": 0.8, "M": 0.5, "L": 0.2}.get(c, 0.3)


def synthesize_evidence(evidence: list[Evidence], title: str = "Synthesized Strategy") -> Synthesis:
    """Takes list of Evidence, produces ranked options with scoring."""
    n = len(evidence)
    avg_conf = sum(_confidence_val(e.confidence) for e in evidence) / n if n else 0.6

    def opt(id_: str, label: str, score: float, rationale: str) -> Option:
        return Option(id=id_, title=label, description=rationale, score=round(score, 4), risks=[])

    options: list[Option] = [
        opt("primary", "Primary Recommendation", round(min(1.0, avg_conf), 4),
            f"Evidence-weighted score from {n} sources."),
        opt("conservative", "Conservative Alternative", round(max(0.0, avg_conf - 0.15), 4),
            "Down-weighted scenario with lower confidence."),
        opt("aggressive", "Aggressive Alternative", round(min(1.0, avg_conf + 0.15), 4),
            "Up-weighted scenario accepting higher variance."),
    ]
    if n >= 3:
        outlier = avg_conf * 0.6 if avg_conf > 0.5 else avg_conf * 1.4
        opt("outlier", "Outlier Scenario", round(min(1.0, outlier), 4),
            "Constructed from weakest evidence sources.")

    options.sort(key=lambda o: o.score, reverse=True)
    return Synthesis(
        options=options,
        recommendation=options[0],
        rationale=f"Synthesized from {n} evidence sources with avg confidence {round(avg_conf, 2)}",
    )