"""B43 — Competitive positioning engine for Strategy Studio.

Produces competitive positioning analysis using:
- Advantage identification from option descriptions
- Competitive moat assessment
- Porter's Five Forces-style scoring
- Positioning statement generation

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

from strategy_studio.core.types import Option


# ── Advantage taxonomy ──────────────────────────────────────────────────────

_ADVANTAGE_PATTERNS = {
    "differentiation": {
        "keywords": ["differentiate", "unique", "only", "exclusive", "first", "best", "superior"],
        "weight": 0.9,
        "moat_type": "product",
    },
    "cost_leadership": {
        "keywords": ["cost", "cheap", "affordable", "efficient", "lean", "automated", "scale"],
        "weight": 0.7,
        "moat_type": "cost",
    },
    "network_effects": {
        "keywords": ["network", "community", "platform", "marketplace", "ecosystem", "viral"],
        "weight": 0.95,
        "moat_type": "network",
    },
    "switching_costs": {
        "keywords": ["integration", "lock-in", "embedded", "workflow", "data migration", "switching"],
        "weight": 0.85,
        "moat_type": "retention",
    },
    "data_moat": {
        "keywords": ["data", "insights", "proprietary", "predictive", "ml", "ai", "learn"],
        "weight": 0.8,
        "moat_type": "data",
    },
    "brand": {
        "keywords": ["brand", "trust", "reputation", "recognition", "loyalty", "premium"],
        "weight": 0.75,
        "moat_type": "brand",
    },
    "regulatory": {
        "keywords": ["license", "patent", "certification", "approval", "compliance", "regulation"],
        "weight": 0.8,
        "moat_type": "regulatory",
    },
    "speed": {
        "keywords": ["fast", "rapid", "real-time", "instant", "quick", "agile", "iterate"],
        "weight": 0.6,
        "moat_type": "execution",
    },
}


def _identify_advantages(description: str) -> list[dict]:
    """Identify competitive advantages from description."""
    desc_lower = description.lower()
    advantages: list[dict] = []

    for adv_type, config in _ADVANTAGE_PATTERNS.items():
        hits = [kw for kw in config["keywords"] if kw in desc_lower]
        if hits:
            confidence = min(1.0, len(hits) / len(config["keywords"]) * 2)
            advantages.append({
                "type": adv_type,
                "weight": config["weight"],
                "moat_type": config["moat_type"],
                "confidence": round(confidence, 3),
                "matched_keywords": hits,
            })

    return advantages


def position_competitively(
    options: list[Option],
    competitors: list[str],
) -> list[dict]:
    """Position options competitively against competitors.

    Returns list of positioning dicts:
    [
      {
        "option_id": str,
        "competitors": [str],
        "advantages": [{"type": str, "weight": float, "moat_type": str, "confidence": float}],
        "positioning_statement": str,
        "moat_score": float,  # 0-1 overall moat strength
        "competitive_intensity": str,  # low/medium/high
        "differentiation_score": float,  # 0-1
        "recommended_positioning": str,
      }
    ]
    """
    positioned: list[dict] = []

    for opt in options:
        advantages = _identify_advantages(opt.description)
        comp_count = len(competitors) if competitors else 3

        # Moat score: average of top 3 advantage weights
        top_weights = sorted([a["weight"] for a in advantages], reverse=True)[:3]
        moat_score = round(sum(top_weights) / len(top_weights), 3) if top_weights else 0.3

        # Differentiation: based on advantage count and uniqueness
        unique_moat_types = set(a["moat_type"] for a in advantages)
        diff_score = round(min(1.0, len(unique_moat_types) / 4.0), 3)

        # Competitive intensity based on competitor count
        if comp_count <= 2:
            intensity = "low"
        elif comp_count <= 5:
            intensity = "medium"
        else:
            intensity = "high"

        # Generate positioning statement
        if advantages:
            top_adv = advantages[0]
            statement = (
                f"{opt.title} competes via {top_adv['moat_type']} moat "
                f"({top_adv['type']}) against {comp_count} known competitors"
            )
        else:
            statement = f"{opt.title}: no specific competitive advantages identified from description"

        # Recommended positioning
        if moat_score > 0.7:
            rec = "Strong position — lead with strength, accelerate differentiation"
        elif moat_score > 0.5:
            rec = "Moderate position — invest in deepening primary moat"
        elif diff_score > 0.5:
            rec = "Niche position — differentiate hard, avoid head-to-head competition"
        else:
            rec = "Weak position — need to build at least one durable advantage"

        positioned.append({
            "option_id": opt.id,
            "competitors": competitors,
            "advantages": advantages,
            "positioning_statement": statement,
            "moat_score": moat_score,
            "competitive_intensity": intensity,
            "differentiation_score": diff_score,
            "recommended_positioning": rec,
        })

    return positioned


def compute_competitive_advantage_score(positioning_results: list[dict]) -> list[dict]:
    """Score and rank competitive positions.

    Advantage score = moat_score × 0.4 + differentiation × 0.4 + (1 / competitive_intensity_penalty) × 0.2
    """
    intensity_penalty = {"low": 1.0, "medium": 0.7, "high": 0.4}

    scored: list[dict] = []
    for p in positioning_results:
        penalty = intensity_penalty.get(p["competitive_intensity"], 0.5)
        score = round(
            p["moat_score"] * 0.4 + p["differentiation_score"] * 0.4 + penalty * 0.2,
            3,
        )
        scored.append({**p, "competitive_advantage_score": score})

    scored.sort(key=lambda s: s["competitive_advantage_score"], reverse=True)
    return scored


def five_forces_assessment(industry: str, option_description: str) -> dict:
    """Quick Porter's Five Forces assessment based on keywords.

    Returns scores 0-1 (higher = more threat/pressure) for each force.
    """
    desc_lower = option_description.lower()

    # Threat of new entry
    entry_keywords = ["platform", "network", "scale", "capital", "regulation", "patent"]
    entry_score = round(min(1.0, sum(1 for k in entry_keywords if k in desc_lower) / 4), 3)

    # Buyer power
    buyer_keywords = ["price sensitive", "commodity", "switching", "many suppliers", "negotiation"]
    buyer_score = round(min(1.0, sum(1 for k in buyer_keywords if k in desc_lower) / 3), 3)

    # Supplier power
    supplier_keywords = ["single source", "proprietary", "rare", "specialized", "vendor lock"]
    supplier_score = round(min(1.0, sum(1 for k in supplier_keywords if k in desc_lower) / 3), 3)

    # Threat of substitution
    sub_keywords = ["replace", "alternative", "substitute", "obsolete", "legacy", "shift"]
    sub_score = round(min(1.0, sum(1 for k in sub_keywords if k in desc_lower) / 3), 3)

    # Competitive rivalry
    rivalry_keywords = ["competition", "market share", "price war", "fragmented", "race", "crowded"]
    rivalry_score = round(min(1.0, sum(1 for k in rivalry_keywords if k in desc_lower) / 3), 3)

    overall = round((entry_score + buyer_score + supplier_score + sub_score + rivalry_score) / 5, 3)

    return {
        "industry": industry,
        "threat_of_new_entry": entry_score,
        "buyer_power": buyer_score,
        "supplier_power": supplier_score,
        "threat_of_substitution": sub_score,
        "competitive_rivalry": rivalry_score,
        "overall_industry_attractiveness": round(1.0 - overall, 3),  # lower threat = more attractive
    }
