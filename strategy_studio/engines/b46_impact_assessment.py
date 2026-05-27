"""B46 — Impact assessment engine for Strategy Studio.

Assesses potential impact of strategic options across multiple dimensions:
- Financial impact (revenue, cost, margin)
- Strategic impact (market position, competitive advantage)
- Operational impact (efficiency, capacity, quality)
- Risk impact (downside exposure, optionality)
- Time-to-impact (speed of value realization)

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

import math
from strategy_studio.core.types import Option


# ── Impact dimension weights ────────────────────────────────────────────────

_DIMENSION_WEIGHTS = {
    "financial": 0.30,
    "strategic": 0.30,
    "operational": 0.20,
    "risk": 0.10,
    "time_to_impact": 0.10,
}

# Keyword patterns for each dimension
_FINANCIAL_KEYWORDS = {
    "revenue": 0.9, "income": 0.85, "profit": 0.85, "growth": 0.7,
    "margin": 0.75, "cost": 0.5, "expense": 0.4, "savings": 0.6,
    "roi": 0.8, "arpu": 0.85, "ltv": 0.8, "cac": 0.6,
}

_STRATEGIC_KEYWORDS = {
    "market": 0.7, "share": 0.75, "position": 0.6, "dominant": 0.9,
    "moat": 0.85, "barrier": 0.8, "platform": 0.75, "ecosystem": 0.8,
    "network": 0.7, "standard": 0.85, "category": 0.65,
}

_OPERATIONAL_KEYWORDS = {
    "efficiency": 0.8, "process": 0.6, "automation": 0.85, "streamline": 0.75,
    "capacity": 0.65, "throughput": 0.7, "quality": 0.6, "scale": 0.7,
    "productivity": 0.8, "reduce": 0.5, "eliminate": 0.6,
}

_RISK_KEYWORDS = {
    "risk": 0.6, "downside": 0.7, "exposure": 0.65, "hedge": 0.7,
    "optionality": 0.8, "insurance": 0.75, "diversify": 0.7,
    "resilience": 0.8, "protect": 0.65,
}

_TIME_KEYWORDS = {
    "immediate": 1.0, "quick": 0.9, "rapid": 0.85, "fast": 0.8,
    "short-term": 0.75, "now": 0.9, "phase 1": 0.7,
    "long-term": 0.3, "multi-year": 0.2, "gradual": 0.3,
}


def _score_dimension(description: str, keyword_scores: dict[str, float]) -> float:
    """Score a single impact dimension based on keyword matches."""
    desc_lower = description.lower()
    total_score = 0.0
    matches = 0

    for keyword, score in keyword_scores.items():
        if keyword in desc_lower:
            total_score += score
            matches += 1

    if matches == 0:
        return 0.3  # Default baseline

    # Average of matched keyword scores, with bonus for multiple matches
    avg = total_score / matches
    match_bonus = min(0.2, matches * 0.05)
    return min(1.0, avg + match_bonus)


def assess_impact(options: list[Option]) -> list[dict]:
    """Assess potential impact for each option across all dimensions.

    Returns list of impact assessment dicts:
    [
      {
        "option_id": str,
        "financial_impact": float,  # 0-1
        "strategic_impact": float,
        "operational_impact": float,
        "risk_impact": float,
        "time_to_impact": float,  # higher = faster
        "overall_impact_score": float,  # weighted average
        "impact_category": str,  # transformative / high / moderate / low
        "primary_dimension": str,  # which dimension drives the score
        "summary": str,
      }
    ]
    """
    assessed: list[dict] = []

    for opt in options:
        financial = _score_dimension(opt.description, _FINANCIAL_KEYWORDS)
        strategic = _score_dimension(opt.description, _STRATEGIC_KEYWORDS)
        operational = _score_dimension(opt.description, _OPERATIONAL_KEYWORDS)
        risk = _score_dimension(opt.description, _RISK_KEYWORDS)
        time_to = _score_dimension(opt.description, _TIME_KEYWORDS)

        # Weighted overall score
        overall = round(
            financial * _DIMENSION_WEIGHTS["financial"]
            + strategic * _DIMENSION_WEIGHTS["strategic"]
            + operational * _DIMENSION_WEIGHTS["operational"]
            + risk * _DIMENSION_WEIGHTS["risk"]
            + time_to * _DIMENSION_WEIGHTS["time_to_impact"],
            3,
        )

        # Impact category
        if overall >= 0.75:
            category = "transformative"
        elif overall >= 0.55:
            category = "high"
        elif overall >= 0.35:
            category = "moderate"
        else:
            category = "low"

        # Primary dimension
        dimensions = {
            "financial": financial,
            "strategic": strategic,
            "operational": operational,
            "risk": risk,
            "time_to_impact": time_to,
        }
        primary = max(dimensions, key=lambda k: dimensions[k])

        summary = (
            f"Financial: {financial:.1f}, Strategic: {strategic:.1f}, "
            f"Operational: {operational:.1f}, Risk: {risk:.1f}, "
            f"Speed: {time_to:.1f} → Overall: {overall:.2f} ({category})"
        )

        assessed.append({
            "option_id": opt.id,
            "financial_impact": round(financial, 3),
            "strategic_impact": round(strategic, 3),
            "operational_impact": round(operational, 3),
            "risk_impact": round(risk, 3),
            "time_to_impact": round(time_to, 3),
            "overall_impact_score": overall,
            "impact_category": category,
            "primary_dimension": primary,
            "summary": summary,
        })

    return assessed


def rank_by_impact(assessments: list[dict]) -> list[dict]:
    """Rank options by overall impact score."""
    ranked = sorted(assessments, key=lambda a: a["overall_impact_score"], reverse=True)
    for i, a in enumerate(ranked):
        a["impact_rank"] = i + 1
    return ranked


def impact_comparison(assessments: list[dict]) -> dict:
    """Generate a comparison matrix across all impact dimensions."""
    if not assessments:
        return {"dimensions": [], "matrix": {}}

    dimensions = ["financial_impact", "strategic_impact", "operational_impact", "risk_impact", "time_to_impact"]
    matrix: dict[str, dict[str, float]] = {}

    for a in assessments:
        matrix[a["option_id"]] = {dim: a[dim] for dim in dimensions}

    # Find best in each dimension
    best: dict[str, str] = {}
    for dim in dimensions:
        best_option = max(assessments, key=lambda a: a[dim])
        best[dim] = best_option["option_id"]

    return {
        "dimensions": dimensions,
        "matrix": matrix,
        "best_per_dimension": best,
    }


def portfolio_impact(assessments: list[dict]) -> dict:
    """Assess combined impact of executing all options as a portfolio."""
    if not assessments:
        return {"portfolio_score": 0, "synergy_estimate": 0}

    n = len(assessments)
    avg_score = sum(a["overall_impact_score"] for a in assessments) / n

    # Synergy estimate: if multiple options score high on different dimensions,
    # portfolio effect is greater than sum of parts
    dim_coverage: dict[str, int] = {}
    for a in assessments:
        primary = a["primary_dimension"]
        dim_coverage[primary] = dim_coverage.get(primary, 0) + 1

    # More unique primary dimensions = more synergy
    unique_dims = len(dim_coverage)
    synergy = round(min(0.3, unique_dims * 0.05), 3)

    portfolio_score = round(min(1.0, avg_score + synergy), 3)

    return {
        "portfolio_score": portfolio_score,
        "average_option_score": round(avg_score, 3),
        "synergy_estimate": synergy,
        "dimension_coverage": dim_coverage,
        "option_count": n,
    }
