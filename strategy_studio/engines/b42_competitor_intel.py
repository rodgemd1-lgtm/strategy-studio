"""B42 — Competitor intelligence engine."""
from __future__ import annotations

from strategy_studio.core.types import Action


def _classify_change(change: str) -> tuple[str, str]:
    lower = change.lower()
    if "pricing" in lower or "discount" in lower or "price" in lower:
        return "pricing", "Re-price bundles and signal anchoring."
    if "feature" in lower or "launch" in lower or "product" in lower:
        return "feature", "Accelerate roadmap differentiation."
    if "talent" in lower or "hire" in lower:
        return "talent", "Lock key IC retention packages."
    if "market" in lower or "expand" in lower:
        return "market", "Preempt adjacency before foothold."
    return "general", "Monitor and prepare counter-positioning."


def analyze_competitor(competitor_name: str, changes: list[str]) -> list[Action]:
    """For each change, generate a response Action."""
    actions: list[Action] = []
    for change in changes:
        category, description = _classify_change(change)
        priority = "high" if category in ("pricing", "feature") else "medium"
        actions.append(Action(
            action_type=f"competitor_response_{category}",
            payload={
                "competitor": competitor_name,
                "change": change,
                "category": category,
                "description": description,
                "priority": priority,
            },
            requires_approval=(category == "pricing"),
        ))
    return actions