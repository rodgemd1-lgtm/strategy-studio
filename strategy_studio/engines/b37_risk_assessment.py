"""B37 — Risk assessment engine for Strategy Studio.

Produces structured risk assessments for strategic options using:
- Base-rate risk categories (market, execution, financial, regulatory, technology)
- Option description analysis + known risk patterns
- Risk severity/likelihood matrix
- Mitigation strategy generation

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

import hashlib
from typing import Literal

from strategy_studio.core.types import Option


# ── Risk taxonomy ────────────────────────────────────────────────────────────

_RISK_CATEGORIES = {
    "market": {
        "keywords": ["market", "demand", "customer", "adoption", "competition", "share", "segment"],
        "default_severity": "medium",
        "common_mitigations": [
            "Validate demand with pilot program before full rollout",
            "Diversify customer base to reduce segment concentration",
            "Build switching costs through integration depth",
        ],
    },
    "execution": {
        "keywords": ["build", "implement", "launch", "deploy", "integrate", "migrate", "scale"],
        "default_severity": "medium",
        "common_mitigations": [
            "Define clear milestones with go/no-go gates",
            "Start with minimum viable scope and iterate",
            "Assign dedicated execution owner with authority",
        ],
    },
    "financial": {
        "keywords": ["capital", "investment", "cost", "budget", "revenue", "margin", "cash", "burn"],
        "default_severity": "high",
        "common_mitigations": [
            "Establish stage-gated funding tied to milestones",
            "Maintain 6-month cash reserve buffer",
            "Model downside scenario with 30% cost overrun",
        ],
    },
    "regulatory": {
        "keywords": ["regulatory", "compliance", "legal", "license", "approval", "policy", "government"],
        "default_severity": "high",
        "common_mitigations": [
            "Engage regulatory counsel early in planning phase",
            "Build compliance into design, not as afterthought",
            "Monitor regulatory developments monthly",
        ],
    },
    "technology": {
        "keywords": ["technology", "platform", "system", "architecture", "data", "security", "infrastructure"],
        "default_severity": "medium",
        "common_mitigations": [
            "Conduct technical proof-of-concept before commitment",
        ],
    },
    "talent": {
        "keywords": ["talent", "hire", "team", "skill", "capacity", "workforce", "key person"],
        "default_severity": "medium",
        "common_mitigations": [
            "Identify critical roles and build succession plan",
            "Cross-train team members on critical systems",
        ],
    },
    "timing": {
        "keywords": ["early", "before", "first mover", "ahead", "premature", "too soon"],
        "default_severity": "medium",
        "common_mitigations": [
            "Set clear timing criteria and stick to them",
        ],
    },
}

# Risk severity thresholds
_SEVERITY_SCORES = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 0.95}


def _match_risk_category(description: str) -> list[tuple[str, float]]:
    """Match description to risk categories. Returns [(category, confidence), ...]."""
    desc_lower = description.lower()
    matches: list[tuple[str, float]] = []
    for category, config in _RISK_CATEGORIES.items():
        hit_count = sum(1 for kw in config["keywords"] if kw in desc_lower)
        if hit_count > 0:
            confidence = min(1.0, hit_count / len(config["keywords"]) * 3)
            matches.append((category, round(confidence, 3)))
    return matches


def _estimate_likelihood(option: Option, category: str) -> float:
    """Estimate likelihood of a risk category materializing."""
    score = option.score
    # Lower-option scores = higher-risk = higher likelihood
    base_likelihood = 1.0 - score
    # Adjust by category
    if category in ("financial", "regulatory"):
        base_likelihood = min(1.0, base_likelihood * 1.2)
    elif category == "timing":
        base_likelihood = min(1.0, base_likelihood * 1.1)
    return round(max(0.1, min(0.95, base_likelihood)), 3)


def assess_risks(options: list[Option]) -> list[dict]:
    """Assess risks for each option.

    Returns list of risk assessment dicts, one per option:
    [
      {
        "option_id": str,
        "risks": [{"category": str, "severity": str, "likelihood": float, "score": float, "mitigations": [str]}],
        "overall_risk_level": str,
        "overall_risk_score": float,
        "top_risks": [str],  # top 3 risk descriptions
      }
    ]
    """
    assessments: list[dict] = []

    for opt in options:
        matches = _match_risk_category(opt.description)

        # If no keyword matches, create a generic execution risk
        if not matches:
            matches = [("execution", 0.3)]

        risks: list[dict] = []
        for category, confidence in matches:
            config = _RISK_CATEGORIES[category]
            likelihood = _estimate_likelihood(opt, category)
            severity_label = config["default_severity"]
            severity_score = _SEVERITY_SCORES[severity_label]

            # Risk score = likelihood * severity
            risk_score = round(likelihood * severity_score, 3)

            # Select mitigations based on confidence
            mitigations = config["common_mitigations"][: max(1, int(confidence * 3))]

            risks.append({
                "category": category,
                "severity": severity_label,
                "likelihood": likelihood,
                "severity_score": severity_score,
                "risk_score": risk_score,
                "mitigations": mitigations,
            })

        # Sort by risk score descending
        risks.sort(key=lambda r: r["risk_score"], reverse=True)

        # Overall risk = average of top 3 risk scores
        top_scores = [r["risk_score"] for r in risks[:3]]
        overall_score = round(sum(top_scores) / len(top_scores), 3) if top_scores else 0.0

        if overall_score >= 0.7:
            overall_level = "critical"
        elif overall_score >= 0.5:
            overall_level = "high"
        elif overall_score >= 0.3:
            overall_level = "medium"
        else:
            overall_level = "low"

        top_risks = [
            f"{r['category'].upper()}: {r['severity']} severity, {r['likelihood']:.0%} likelihood"
            for r in risks[:3]
        ]

        assessments.append({
            "option_id": opt.id,
            "risks": risks,
            "overall_risk_level": overall_level,
            "overall_risk_score": overall_score,
            "top_risks": top_risks,
        })

    return assessments


def compare_risk_profiles(assessments: list[dict]) -> dict:
    """Compare risk profiles across options. Returns ranking from lowest to highest risk."""
    if not assessments:
        return {"safest": None, "riskiest": None, "ranking": []}

    ranking = sorted(assessments, key=lambda a: a["overall_risk_score"])
    return {
        "safest": ranking[0]["option_id"] if ranking else None,
        "riskiest": ranking[-1]["option_id"] if ranking else None,
        "ranking": [
            {"option_id": a["option_id"], "risk_level": a["overall_risk_level"], "score": a["overall_risk_score"]}
            for a in ranking
        ],
    }


def generate_risk_matrix(options: list[Option]) -> dict:
    """Generate a full risk matrix (options × categories)."""
    categories = list(_RISK_CATEGORIES.keys())
    matrix: dict[str, dict[str, float]] = {}

    for opt in options:
        matches = {cat: conf for cat, conf in _match_risk_category(opt.description)}
        row: dict[str, float] = {}
        for cat in categories:
            likelihood = _estimate_likelihood(opt, cat)
            severity = _SEVERITY_SCORES[_RISK_CATEGORIES[cat]["default_severity"]]
            keyword_confidence = matches.get(cat, 0.1)
            row[cat] = round(likelihood * severity * (0.5 + 0.5 * keyword_confidence), 3)
        matrix[opt.id] = row

    return {
        "options": [opt.id for opt in options],
        "categories": categories,
        "matrix": matrix,
    }
