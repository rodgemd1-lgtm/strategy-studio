"""B40 — Market sizing engine for Strategy Studio.

Produces TAM/BAM/SAM estimates for strategic options using:
- Keyword-based market classification
- Bottom-up estimation from description parameters
- Top-down estimation from industry benchmarks
- Confidence scoring based on data availability

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

import math
from strategy_studio.core.types import Option


# ── Market size benchmarks by segment (USD) ─────────────────────────────────

_SEGMENT_SIZES: dict[str, dict[str, float]] = {
    # Format: {"tam": float, "bam": float, "sam": float}
    "enterprise": {"tam": 5e9, "bam": 1e9, "sam": 2e8},
    "smb": {"tam": 2e9, "bam": 5e8, "sam": 1e8},
    "consumer": {"tam": 2e10, "bam": 5e9, "sam": 5e8},
    "government": {"tam": 1e10, "bam": 2e9, "sam": 1e8},
    "healthcare": {"tam": 4e10, "bam": 5e9, "sam": 2e8},
    "fintech": {"tam": 3e10, "bam": 3e9, "sam": 1.5e8},
    "marketplace": {"tam": 5e10, "bam": 2e9, "sam": 1e8},
    "platform": {"tam": 1e11, "bam": 5e9, "sam": 2.5e8},
    "api": {"tam": 3e9, "bam": 8e8, "sam": 1.5e8},
    "infrastructure": {"tam": 8e10, "bam": 1e9, "sam": 2e8},
    "default": {"tam": 1e9, "bam": 2e8, "sam": 5e7},
}

# Growth rate estimates by segment (CAGR %)
_SEGMENT_GROWTH: dict[str, float] = {
    "enterprise": 12.0,
    "smb": 15.0,
    "consumer": 8.0,
    "government": 5.0,
    "healthcare": 10.0,
    "fintech": 20.0,
    "marketplace": 18.0,
    "platform": 22.0,
    "api": 25.0,
    "infrastructure": 14.0,
    "default": 10.0,
}

# Keywords to segment mapping
_SEGMENT_KEYWORDS: dict[str, list[str]] = {
    "enterprise": ["enterprise", "corporate", "fortune", "large company", "b2b"],
    "smb": ["smb", "small business", "mid-market", "sme", "startup"],
    "consumer": ["consumer", "b2c", "retail", "individual", "end user", "prosumer"],
    "government": ["government", "public sector", "federal", "state", "municipal", "defense"],
    "healthcare": ["healthcare", "health", "medical", "hospital", "clinical", "patient"],
    "fintech": ["fintech", "financial", "banking", "insurance", "wealth", "payment"],
    "marketplace": ["marketplace", "platform marketplace", "two-sided", "multi-sided"],
    "platform": ["platform", "ecosystem", "developer", "api platform"],
    "api": ["api", "developer tools", "sdk", "integration"],
    "infrastructure": ["infrastructure", "cloud", "devops", "data center", "compute"],
}


def _classify_segment(description: str) -> tuple[str, float]:
    """Classify option into market segment. Returns (segment, confidence)."""
    desc_lower = description.lower()
    best_segment = "default"
    best_score = 0.0

    for segment, keywords in _SEGMENT_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in desc_lower)
        if hits > 0:
            score = hits / len(keywords)
            if score > best_score:
                best_score = score
                best_segment = segment

    confidence = min(1.0, best_score * 2)
    return best_segment, round(confidence, 3)


def _extract_numeric_params(description: str) -> dict[str, float]:
    """Try to extract numeric parameters from description (users, price, etc.)."""
    params: dict[str, float] = {}
    desc_lower = description.lower()

    # Look for user/customer counts
    import re
    user_match = re.search(r'(\d+[,.]?\d*)\s*(?:users|customers|clients|accounts)', desc_lower)
    if user_match:
        params["users"] = float(user_match.group(1).replace(",", ""))

    # Look for price/ARPU
    price_match = re.search(r'\$(\d+[,.]?\d*)\s*(?:price|arpu|acv|arr|per user|per customer)', desc_lower)
    if price_match:
        params["price"] = float(price_match.group(1).replace(",", ""))

    # Look for percentage
    pct_match = re.search(r'(\d+)%', desc_lower)
    if pct_match:
        params["percentage"] = float(pct_match.group(1))

    return params


def size_market(options: list[Option]) -> list[dict]:
    """Size markets for each option.

    Returns list of market sizing dicts:
    [
      {
        "option_id": str,
        "segment": str,
        "tam": float,  # Total Addressable Market
        "bam": float,  # Beatable Addressable Market
        "sam": float,  # Serviceable Addressable Market
        "som": float,  # Serviceable Obtainable Market (realistic capture)
        "cagr": float,  # Compound Annual Growth Rate %
        "unit": str,
        "confidence": str,  # H/M/L based on data availability
        "method": str,  # bottom_up / top_down / hybrid
        "year_5_tam": float,  # Projected TAM in 5 years
      }
    ]
    """
    sized_options: list[dict] = []

    for opt in options:
        segment, seg_confidence = _classify_segment(opt.description)
        params = _extract_numeric_params(description=opt.description)
        benchmarks = _SEGMENT_SIZES.get(segment, _SEGMENT_SIZES["default"])
        growth_rate = _SEGMENT_GROWTH.get(segment, 10.0)

        # Determine method and adjust estimates
        if "users" in params and "price" in params:
            # Bottom-up: users × price
            bottom_up_tam = params["users"] * params["price"]
            tam = (bottom_up_tam + benchmarks["tam"]) / 2  # Hybrid
            method = "hybrid"
        elif "users" in params:
            # Partial bottom-up
            tam = benchmarks["tam"]
            method = "top_down"
        else:
            tam = benchmarks["tam"]
            method = "top_down"

        # BAM = typically 20-30% of TAM
        bam_ratio = benchmarks["bam"] / benchmarks["tam"] if benchmarks["tam"] > 0 else 0.2
        bam = tam * bam_ratio

        # SAM = typically 10-20% of TAM
        sam_ratio = benchmarks["sam"] / benchmarks["tam"] if benchmarks["tam"] > 0 else 0.1
        sam = tam * sam_ratio

        # SOM = realistic Year 1 capture (1-5% of SAM)
        som = sam * 0.03

        # 5-year TAM projection
        year_5_tam = tam * math.pow(1 + growth_rate / 100, 5)

        # Confidence based on data availability
        if seg_confidence > 0.5 and params:
            confidence = "H"
        elif seg_confidence > 0.2:
            confidence = "M"
        else:
            confidence = "L"

        sized_options.append({
            "option_id": opt.id,
            "segment": segment,
            "tam": round(tam, 2),
            "bam": round(bam, 2),
            "sam": round(sam, 2),
            "som": round(som, 2),
            "cagr": growth_rate,
            "unit": "USD",
            "confidence": confidence,
            "method": method,
            "year_5_tam": round(year_5_tam, 2),
        })

    return sized_options


def estimate_som(option: Option, market_share_pct: float = 3.0) -> dict:
    """Estimate Serviceable Obtainable Market for a specific option.

    Args:
        option: The strategic option.
        market_share_pct: Expected market share capture percentage.
    """
    sizing = size_market([option])
    if not sizing:
        return {"som": 0, "unit": "USD"}

    s = sizing[0]
    som = s["sam"] * (market_share_pct / 100)
    return {
        "option_id": option.id,
        "som": round(som, 2),
        "market_share_pct": market_share_pct,
        "sam": s["sam"],
        "unit": "USD",
    }


def market_attractiveness(sizing_results: list[dict]) -> list[dict]:
    """Rank market sizing results by attractiveness.

    Attractiveness = (TAM × CAGR) / 100, normalized to 0-1.
    """
    if not sizing_results:
        return []

    scores: list[dict] = []
    for s in sizing_results:
        raw_score = (s["tam"] * s["cagr"]) / 100
        scores.append({**s, "attractiveness_raw": round(raw_score, 2)})

    # Normalize
    max_raw = max(s["attractiveness_raw"] for s in scores) if scores else 1.0
    if max_raw > 0:
        for s in scores:
            s["attractiveness"] = round(s["attractiveness_raw"] / max_raw, 3)
    else:
        for s in scores:
            s["attractiveness"] = 0.0

    scores.sort(key=lambda s: s["attractiveness"], reverse=True)
    return scores
