"""B45 — Budget allocation engine for Strategy Studio.

Allocates budget across strategic options using:
- Score-weighted proportional allocation
- Complexity-adjusted cost estimation
- ROI-based priority ranking
- Minimum viable investment thresholds

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

import math
from strategy_studio.core.types import Option


# ── Cost estimation ─────────────────────────────────────────────────────────

_COMPLEXITY_COSTS = {
    "simple": {"base": 50000, "per_week": 5000},
    "moderate": {"base": 150000, "per_week": 8000},
    "complex": {"base": 400000, "per_week": 15000},
    "strategic": {"base": 800000, "per_week": 25000},
    "regulatory": {"base": 1200000, "per_week": 30000},
}

_COMPLEXITY_WEEKS = {
    "simple": 6,
    "moderate": 12,
    "complex": 24,
    "strategic": 36,
    "regulatory": 52,
}


def _estimate_complexity(description: str) -> tuple[str, int]:  # (level, weeks)
    """Estimate complexity level and duration."""
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in ["regulatory", "approval", "compliance"]):
        return "regulatory", _COMPLEXITY_WEEKS["regulatory"]
    if any(kw in desc_lower for kw in ["strategic", "transformative", "platform", "fundamental"]):
        return "strategic", _COMPLEXITY_WEEKS["strategic"]
    if any(kw in desc_lower for kw in ["complex", "multi", "integrated", "enterprise"]):
        return "complex", _COMPLEXITY_WEEKS["complex"]
    if any(kw in desc_lower for kw in ["simple", "basic", "quick win", "easy"]):
        return "simple", _COMPLEXITY_WEEKS["simple"]
    return "moderate", _COMPLEXITY_WEEKS["moderate"]


def _estimate_cost(description: str) -> float:
    """Estimate total implementation cost."""
    level, weeks = _estimate_complexity(description)
    config = _COMPLEXITY_COSTS.get(level, _COMPLEXITY_COSTS["moderate"])
    return config["base"] + config["per_week"] * weeks


def allocate_budget(
    options: list[Option],
    total_budget: float = 1_000_000.0,
    min_allocation_pct: float = 0.05,
) -> list[dict]:
    """Allocate budget among options based on score and complexity.

    Uses score-weighted proportional allocation with minimum thresholds.

    Returns list of allocation dicts:
    [
      {
        "option_id": str,
        "budget": float,
        "allocation_percentage": float,
        "estimated_cost": float,
        "funding_gap": float,  # negative = underfunded
        "roi_estimate": float,
        "priority_rank": int,
        "complexity_level": str,
        "unit": str,
      }
    ]
    """
    if not options:
        return []

    # Calculate raw scores
    total_score = sum(opt.score for opt in options)
    if total_score <= 0:
        total_score = 1.0

    # Initial proportional allocation
    raw_allocations: list[dict] = []
    for opt in options:
        proportion = opt.score / total_score
        budget = total_budget * proportion
        estimated = _estimate_cost(opt.description)
        level, _ = _estimate_complexity(opt.description)

        raw_allocations.append({
            "option_id": opt.id,
            "budget": budget,
            "allocation_percentage": round(proportion * 100, 2),
            "estimated_cost": round(estimated, 2),
            "funding_gap": round(budget - estimated, 2),
            "roi_estimate": round((opt.score * estimated * 0.3) / max(budget, 1), 3),
            "complexity_level": level,
            "unit": "USD",
        })

    # Enforce minimum allocation
    min_budget = total_budget * min_allocation_pct
    deficit = 0.0
    surplus_indices: list[int] = []

    for i, alloc in enumerate(raw_allocations):
        if alloc["budget"] < min_budget:
            deficit += min_budget - alloc["budget"]
            alloc["budget"] = min_budget
        else:
            surplus_indices.append(i)

    # Redistribute deficit from surplus options
    if deficit > 0 and surplus_indices:
        total_surplus = sum(raw_allocations[i]["budget"] - min_budget for i in surplus_indices)
        if total_surplus > 0:
            for i in surplus_indices:
                surplus = raw_allocations[i]["budget"] - min_budget
                reduction = deficit * (surplus / total_surplus)
                raw_allocations[i]["budget"] -= reduction

    # Round and recalculate percentages
    total_allocated = sum(a["budget"] for a in raw_allocations)
    for alloc in raw_allocations:
        alloc["budget"] = round(alloc["budget"], 2)
        alloc["allocation_percentage"] = round(alloc["budget"] / total_budget * 100, 2) if total_budget > 0 else 0.0
        alloc["funding_gap"] = round(alloc["budget"] - alloc["estimated_cost"], 2)

    # Rank by ROI
    raw_allocations.sort(key=lambda a: a["roi_estimate"], reverse=True)
    for i, alloc in enumerate(raw_allocations):
        alloc["priority_rank"] = i + 1

    return raw_allocations


def budget_scenarios(
    options: list[Option],
    budgets: list[float] | None = None,
) -> dict[str, list[dict]]:
    """Run multiple budget scenarios."""
    if budgets is None:
        budgets = [250_000, 500_000, 1_000_000, 2_000_000, 5_000_000]

    scenarios: dict[str, list[dict]] = {}
    for budget in budgets:
        label = f"${budget:,.0f}"
        scenarios[label] = allocate_budget(options, budget)

    return scenarios


def funding_efficiency(allocations: list[dict]) -> dict:
    """Analyze funding efficiency across allocations."""
    if not allocations:
        return {"efficiency": 0, "underfunded": [], "overfunded": []}

    total_budget = sum(a["budget"] for a in allocations)
    total_estimated = sum(a["estimated_cost"] for a in allocations)

    underfunded = [a for a in allocations if a["funding_gap"] < 0]
    overfunded = [a for a in allocations if a["funding_gap"] > 0]

    efficiency = round(total_estimated / total_budget, 3) if total_budget > 0 else 0.0

    return {
        "efficiency": efficiency,
        "total_budget": total_budget,
        "total_estimated_cost": round(total_estimated, 2),
        "underfunded_count": len(underfunded),
        "overfunded_count": len(overfunded),
        "underfunded": [a["option_id"] for a in underfunded],
        "overfunded": [a["option_id"] for a in overfunded],
    }
