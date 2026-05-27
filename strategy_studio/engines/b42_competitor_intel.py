"""B42 — Competitor intelligence engine for Strategy Studio.

Produces structured competitor intelligence:
- Change classification (pricing, feature, talent, market, partnership, technology)
- Response action generation with priority scoring
- Competitive threat assessment
- Market position tracking
- Counter-strategy recommendations

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

from strategy_studio.core.types import Action


# ── Change classification taxonomy ──────────────────────────────────────────

_CHANGE_PATTERNS = {
    "pricing": {
        "keywords": ["pricing", "discount", "price", "cost", "bundle", "free tier", "undercut"],
        "response": "Re-price bundles and signal anchoring.",
        "urgency": "high",
        "approval_required": True,
    },
    "feature": {
        "keywords": ["feature", "launch", "product", "release", "capability", "integration", "api"],
        "response": "Accelerate roadmap differentiation.",
        "urgency": "high",
        "approval_required": False,
    },
    "talent": {
        "keywords": ["hire", "talent", "acqui-hire", "team", "cto", "vp", "key hire"],
        "response": "Lock key IC retention packages.",
        "urgency": "medium",
        "approval_required": False,
    },
    "market": {
        "keywords": ["expand", "market", "geography", "region", "vertical", "segment"],
        "response": "Preempt adjacency before foothold.",
        "urgency": "medium",
        "approval_required": False,
    },
    "partnership": {
        "keywords": ["partner", "alliance", "integration", "reseller", "channel", "oem"],
        "response": "Strengthen partner lock-in and exclusivity.",
        "urgency": "medium",
        "approval_required": False,
    },
    "technology": {
        "keywords": ["patent", "ip", "acquisition", "ai", "ml", "platform", "architecture"],
        "response": "Accelerate R&D and IP moat.",
        "urgency": "medium",
        "approval_required": False,
    },
    "funding": {
        "keywords": ["raise", "funding", "series", "valuation", "investor", "ipo"],
        "response": "Prepare competitive response to war chest.",
        "urgency": "low",
        "approval_required": False,
    },
}


def _classify_change(change: str) -> tuple[str, str, str, bool]:
    """Classify a competitor change. Returns (category, response, urgency, approval_required)."""
    lower = change.lower()
    for category, config in _CHANGE_PATTERNS.items():
        if any(kw in lower for kw in config["keywords"]):
            return category, config["response"], config["urgency"], config["approval_required"]
    return "general", "Monitor and prepare counter-positioning.", "low", False


def analyze_competitor(competitor_name: str, changes: list[str]) -> list[Action]:
    """For each change, generate a response Action."""
    actions: list[Action] = []
    for change in changes:
        category, description, urgency, approval = _classify_change(change)
        priority = "high" if urgency == "high" else "medium" if urgency == "medium" else "low"
        actions.append(Action(
            action_type=f"competitor_response_{category}",
            payload={
                "competitor": competitor_name,
                "change": change,
                "category": category,
                "description": description,
                "priority": priority,
                "urgency": urgency,
            },
            requires_approval=approval,
        ))
    return actions


def assess_threat_level(competitor_name: str, changes: list[str]) -> dict:
    """Assess overall competitive threat from a set of changes."""
    if not changes:
        return {"level": "low", "score": 0.0, "summary": "No changes detected"}

    actions = analyze_competitor(competitor_name, changes)
    high_count = sum(1 for a in actions if a.payload.get("urgency") == "high")
    medium_count = sum(1 for a in actions if a.payload.get("urgency") == "medium")
    approval_count = sum(1 for a in actions if a.requires_approval)

    # Threat score
    score = min(1.0, high_count * 0.3 + medium_count * 0.1)

    if score >= 0.7:
        level = "critical"
    elif score >= 0.4:
        level = "high"
    elif score >= 0.2:
        level = "medium"
    else:
        level = "low"

    categories = list(set(a.payload.get("category", "general") for a in actions))

    return {
        "competitor": competitor_name,
        "level": level,
        "score": round(score, 2),
        "changes_analyzed": len(changes),
        "high_urgency": high_count,
        "requires_approval": approval_count,
        "categories": categories,
        "summary": f"{competitor_name}: {level} threat ({len(changes)} changes, {high_count} high urgency)",
    }


def compare_competitors(competitor_changes: dict[str, list[str]]) -> list[dict]:
    """Compare threat levels across multiple competitors."""
    assessments = []
    for name, changes in competitor_changes.items():
        assessment = assess_threat_level(name, changes)
        assessments.append(assessment)
    assessments.sort(key=lambda x: x["score"], reverse=True)
    return assessments


def generate_counter_strategy(competitor_name: str, changes: list[str], our_strengths: list[str] | None = None) -> dict:
    """Generate a counter-strategy based on competitor changes and our strengths."""
    actions = analyze_competitor(competitor_name, changes)
    threat = assess_threat_level(competitor_name, changes)

    # Prioritize actions
    high_priority = [a for a in actions if a.payload.get("priority") == "high"]
    medium_priority = [a for a in actions if a.payload.get("priority") == "medium"]

    # Build counter-strategy
    strategy = {
        "competitor": competitor_name,
        "threat_level": threat["level"],
        "immediate_actions": [
            {"type": a.action_type, "description": a.payload.get("description", "")}
            for a in high_priority
        ],
        "planned_actions": [
            {"type": a.action_type, "description": a.payload.get("description", "")}
            for a in medium_priority
        ],
        "requires_approval": [a.action_type for a in actions if a.requires_approval],
    }

    if our_strengths:
        strategy["leverage_strengths"] = our_strengths

    return strategy
