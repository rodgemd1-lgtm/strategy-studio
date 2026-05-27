"""B41 — Client intelligence / wedge generator for Strategy Studio.

Produces structured client intelligence from prospect data:
- ICP (Ideal Customer Profile) extraction and scoring
- Entry wedge identification from pain points
- TAM/SAM/SOM estimation from company attributes
- Buying committee mapping
- Engagement priority scoring

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

from strategy_studio.core.types import Segment


# ── ICP scoring patterns ────────────────────────────────────────────────────

_ICP_KEYWORDS = {
    "enterprise": ["enterprise", "fortune", "large", "corporate", "global"],
    "mid_market": ["mid-market", "growth", "scale-up", "expansion"],
    "smb": ["small business", "startup", "smb", "sme", "local"],
    "technical": ["cto", "vp engineering", "developer", "technical", "architect"],
    "business": ["ceo", "cfo", "coo", "vp", "director", "head of"],
}

_WEDGE_PATTERNS = {
    "cost_reduction": ["cost", "expensive", "budget", "roi", "savings", "efficiency"],
    "revenue_growth": ["revenue", "growth", "sales", "pipeline", "conversion"],
    "risk_mitigation": ["risk", "compliance", "security", "audit", "regulation"],
    "speed": ["slow", "manual", "bottleneck", "delay", "time-to-market"],
    "innovation": ["innovate", "modernize", "transform", "digital", "ai"],
}

_SIZING_MULTIPLIERS = {
    "enterprise": 50000,
    "mid_market": 15000,
    "smb": 3000,
    "default": 8000,
}


def _classify_company_size(employees: int | str | None) -> str:
    """Classify company size from employee count."""
    if employees is None:
        return "unknown"
    try:
        n = int(str(employees).replace(",", ""))
    except (ValueError, TypeError):
        return "unknown"
    if n >= 1000:
        return "enterprise"
    elif n >= 100:
        return "mid_market"
    else:
        return "smb"


def _extract_icp(prospect_data: dict) -> dict:
    """Extract and score ICP from prospect data."""
    icp_raw = prospect_data.get("icp") or prospect_data.get("ideal_customer_profile", "")
    if icp_raw:
        return {"profile": icp_raw, "confidence": "high", "source": "explicit"}

    # Build ICP from available fields
    title = prospect_data.get("title", "")
    dept = prospect_data.get("department", "")
    company_size = prospect_data.get("company_size", "")
    industry = prospect_data.get("industry", "")

    parts = [p for p in (title, dept, company_size, industry) if p]
    icp_str = "; ".join(parts) if parts else "Unspecified ICP"

    # Score ICP quality
    confidence = "low"
    if title and dept:
        confidence = "medium"
    if title and dept and company_size:
        confidence = "high"

    return {"profile": icp_str, "confidence": confidence, "source": "inferred"}


def _identify_wedge(prospect_data: dict) -> dict:
    """Identify the best entry wedge from prospect data."""
    explicit = prospect_data.get("entry_wedge") or prospect_data.get("pain_point", "")
    if explicit:
        return {"wedge": explicit, "type": "explicit", "confidence": "high"}

    # Infer from description
    description = prospect_data.get("description", "") + " " + prospect_data.get("notes", "")
    desc_lower = description.lower()

    best_type = "general"
    best_score = 0
    for wedge_type, keywords in _WEDGE_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > best_score:
            best_score = score
            best_type = wedge_type

    wedge_map = {
        "cost_reduction": "Reduce operational costs through automation",
        "revenue_growth": "Accelerate revenue growth with better tooling",
        "risk_mitigation": "Mitigate compliance and security risks",
        "speed": "Eliminate bottlenecks and accelerate delivery",
        "innovation": "Enable next-generation capabilities",
        "general": "Operational inefficiency or compliance gap",
    }

    return {
        "wedge": wedge_map[best_type],
        "type": best_type,
        "confidence": "medium" if best_score > 0 else "low",
    }


def _estimate_sizing(prospect_data: dict) -> dict:
    """Estimate TAM/SAM/SOM from prospect data."""
    explicit = prospect_data.get("sizing") or prospect_data.get("tam", "")
    if explicit:
        return {"sizing": explicit, "confidence": "high", "source": "explicit"}

    employees = prospect_data.get("employees")
    size_class = _classify_company_size(employees)
    multiplier = _SIZING_MULTIPLIERS.get(size_class, _SIZING_MULTIPLIERS["default"])

    try:
        n = int(str(employees).replace(",", ""))
        arr_potential = n * multiplier
        return {
            "sizing": f"~${arr_potential:,.0f} ARR potential",
            "confidence": "medium",
            "source": "estimated",
            "size_class": size_class,
        }
    except (ValueError, TypeError):
        return {
            "sizing": "Sizing undefined",
            "confidence": "low",
            "source": "unknown",
            "size_class": size_class,
        }


def generate_wedge(prospect_data: dict) -> Segment:
    """Extract ICP, entry_wedge, sizing from prospect data into a Segment."""
    icp = _extract_icp(prospect_data)
    wedge = _identify_wedge(prospect_data)
    sizing = _estimate_sizing(prospect_data)

    name = prospect_data.get("name") or prospect_data.get("segment_name", "Default Segment")
    return Segment(
        name=name,
        icp=icp["profile"],
        sizing=sizing["sizing"],
        entry_wedge=wedge["wedge"],
    )


def score_prospect(prospect_data: dict) -> dict:
    """Score a prospect's quality and priority."""
    icp = _extract_icp(prospect_data)
    wedge = _identify_wedge(prospect_data)
    sizing = _estimate_sizing(prospect_data)

    # Composite score
    score = 0.0
    if icp["confidence"] == "high":
        score += 0.4
    elif icp["confidence"] == "medium":
        score += 0.2

    if wedge["confidence"] == "high":
        score += 0.3
    elif wedge["confidence"] == "medium":
        score += 0.15

    if sizing["confidence"] == "high":
        score += 0.3
    elif sizing["confidence"] == "medium":
        score += 0.15

    if score >= 0.8:
        priority = "high"
    elif score >= 0.5:
        priority = "medium"
    else:
        priority = "low"

    return {
        "score": round(score, 2),
        "priority": priority,
        "icp_confidence": icp["confidence"],
        "wedge_confidence": wedge["confidence"],
        "sizing_confidence": sizing["confidence"],
        "wedge_type": wedge["type"],
        "size_class": sizing.get("size_class", "unknown"),
    }


def batch_score_prospects(prospects: list[dict]) -> list[dict]:
    """Score and rank multiple prospects."""
    scored = []
    for p in prospects:
        score = score_prospect(p)
        scored.append({**score, "name": p.get("name", "Unknown")})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
