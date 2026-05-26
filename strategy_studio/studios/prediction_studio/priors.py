"""
Prediction Studio — Market Priors and Base Rate Engines.

Handles extraction and validation of:
- Prediction market priors (Kalshi, Polymarket, Metaculus, Manifold)
- Historical base rates from reference classes
- Source matching quality assessment
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Literal

from .core import MarketPrior, ResolutionMatchQuality


def extract_market_prior(
    market_priors: list[MarketPrior],
    min_quality: Literal["exact", "close", "weak"] = "close",
) -> float | None:
    """Extract a single probability from market priors.

    Uses the highest-quality available prior, weighted by recency.
    """
    quality_order = {"exact": 0, "close": 1, "weak": 2}
    min_q = quality_order.get(min_quality, 1)

    valid = [mp for mp in market_priors if quality_order.get(mp.resolution_match_quality, 3) <= min_q]
    if not valid:
        return None

    now = datetime.now(timezone.utc)
    weights = []
    probs = []
    for mp in valid:
        age_hours = (now - mp.timestamp).total_seconds() / 3600
        weight = math.exp(-age_hours / 168)  # 1-week half-life
        weights.append(weight)
        probs.append(mp.probability)

    total_weight = sum(weights)
    if total_weight <= 0:
        return sum(probs) / len(probs)
    return sum(p * w for p, w in zip(probs, weights)) / total_weight


def validate_market_match(
    forecast_question: str,
    market_question: str,
) -> ResolutionMatchQuality:
    """Assess how well a market question matches a forecast question."""
    # Simple keyword overlap — can be enhanced with embeddings
    fq_words = set(forecast_question.lower().split())
    mq_words = set(market_question.lower().split())
    overlap = len(fq_words & mq_words)
    total = len(fq_words | mq_words)
    if total == 0:
        return ResolutionMatchQuality.INVALID
    ratio = overlap / total
    if ratio >= 0.7:
        return ResolutionMatchQuality.EXACT
    elif ratio >= 0.4:
        return ResolutionMatchQuality.CLOSE
    elif ratio >= 0.2:
        return ResolutionMatchQuality.WEAK
    return ResolutionMatchQuality.INVALID


def find_base_rate(
    category: str,
    reference_class: str,
    historical_data: list[dict] | None = None,
) -> float | None:
    """Find base rate from historical reference class.

    In production, this queries LakeOS/Phronema for historical data.
    Stub implementation returns None (unknown).
    """
    # TODO: Query Phronema LakeOS for historical base rates
    # For now, return None to indicate unknown
    return None