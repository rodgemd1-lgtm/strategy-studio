"""
Prediction Studio — Bayesian Updating, Priors, and Ensemble Forecasting.

Implements:
- Sequential Bayesian updating with likelihood ratios
- Prediction market prior extraction and validation
- Multi-model ensemble aggregation (simple, weighted, recalibrated)
- Base-rate lookup from historical reference classes

Key sources:
- Martin et al. (2022): Bayesian forecasting in economics and finance
- Atanasov et al. (2017): prediction markets vs prediction polls
- Turner et al. (2014): forecast aggregation via recalibration
- Gruen et al. (2023): ML augmentation of collective forecasts
"""
from __future__ import annotations

import math
from typing import Literal

from .core import (
    EvidenceUpdate,
    ForecastRecord,
    MarketPrior,
)


def update_prior(prior: float, likelihood_ratio: float) -> float:
    """Bayesian updating via odds form.

    posterior_odds = likelihood_ratio * prior_odds
    posterior = posterior_odds / (1 + posterior_odds)
    """
    if prior <= 0 or prior >= 1:
        return prior
    prior_odds = prior / (1 - prior)
    posterior_odds = likelihood_ratio * prior_odds
    return posterior_odds / (1 + posterior_odds)


def compute_likelihood_ratio(evidence_probability_if_true: float, evidence_probability_if_false: float) -> float:
    """Compute likelihood ratio from conditional probabilities.

    LR = P(evidence | hypothesis_true) / P(evidence | hypothesis_false)
    """
    if evidence_probability_if_false <= 0:
        return 10.0  # Cap at 10x to avoid division by zero
    return evidence_probability_if_true / evidence_probability_if_false


def sequential_bayesian_update(
    prior: float,
    evidence_items: list[tuple[float, float]],
) -> list[EvidenceUpdate]:
    """Apply sequential Bayesian updates for multiple evidence items.

    Args:
        prior: Initial probability.
        evidence_items: List of (P(evidence|true), P(evidence|false)) pairs.

    Returns:
        List of EvidenceUpdate records showing the update path.
    """
    updates = []
    current = prior
    for p_true, p_false in evidence_items:
        lr = compute_likelihood_ratio(p_true, p_false)
        posterior = update_prior(current, lr)
        updates.append(EvidenceUpdate(
            prior_probability=current,
            evidence=f"LR={lr:.2f}",
            likelihood_ratio=lr,
            posterior_probability=posterior,
            reasoning=f"Prior {current:.3f} × LR {lr:.2f} → Posterior {posterior:.3f}",
        ))
        current = posterior
    return updates


def extract_market_prior(
    market_priors: list[MarketPrior],
    min_quality: Literal["exact", "close", "weak"] = "close",
) -> float | None:
    """Extract a single probability from market priors.

    Uses the highest-quality available prior, averaged if multiple match.
    """
    quality_order = {"exact": 0, "close": 1, "weak": 2}
    min_q = quality_order.get(min_quality, 1)

    valid = [mp for mp in market_priors if quality_order.get(mp.resolution_match_quality, 3) <= min_q]
    if not valid:
        return None

    # Weighted average by recency (more recent = higher weight)
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
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


def simple_ensemble(forecasts: list[float]) -> float:
    """Simple average of all forecasts."""
    if not forecasts:
        return 0.5
    return sum(forecasts) / len(forecasts)


def weighted_ensemble(
    forecasts: list[tuple[float, float]],
) -> float:
    """Weighted average of forecasts.

    Args:
        forecasts: List of (probability, weight) pairs.
    """
    if not forecasts:
        return 0.5
    total_weight = sum(w for _, w in forecasts)
    if total_weight <= 0:
        return sum(p for p, _ in forecasts) / len(forecasts)
    return sum(p * w for p, w in forecasts) / total_weight


def extremized_ensemble(
    forecasts: list[float],
    alpha: float = 0.5,
) -> float:
    """Extremized aggregate for potentially underconfident ensembles.

    Moves aggregate away from 0.5 toward extremes.
    """
    if not forecasts:
        return 0.5
    avg = sum(forecasts) / len(forecasts)
    if avg > 0.5:
        return 0.5 + (avg - 0.5) ** (1 - alpha)
    else:
        return 0.5 - (0.5 - avg) ** (1 - alpha)


def compute_ensemble(
    forecast: ForecastRecord,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute ensemble probability from all available forecasts.

    Combines: human, LLM (average), market prior, base rate, model forecasts.
    """
    components: list[tuple[float, float]] = []

    # Human forecast
    if forecast.human_forecast is not None:
        w = (weights or {}).get("human", 1.0)
        components.append((forecast.human_forecast, w))

    # LLM forecasts (average)
    if forecast.llm_forecasts:
        llm_avg = sum(f.probability for f in forecast.llm_forecasts) / len(forecast.llm_forecasts)
        w = (weights or {}).get("llm", 0.8)
        components.append((llm_avg, w))

    # Market prior
    if forecast.market_priors:
        from .priors import extract_market_prior
        mp = extract_market_prior(forecast.market_priors)
        if mp is not None:
            w = (weights or {}).get("market", 1.2)
            components.append((mp, w))

    # Base rate
    if forecast.base_rate is not None:
        w = (weights or {}).get("base_rate", 0.5)
        components.append((forecast.base_rate, w))

    # Model forecasts
    for model_name, prob in forecast.model_forecasts.items():
        w = (weights or {}).get(model_name, 1.0)
        components.append((prob, w))

    if not components:
        return 0.5

    return weighted_ensemble(components)


def compute_uncertainty_interval(
    forecasts: list[float],
    confidence: float = 0.9,
) -> tuple[float, float]:
    """Compute uncertainty interval from ensemble spread."""
    if not forecasts:
        return (0.0, 1.0)
    sorted_f = sorted(forecasts)
    n = len(sorted_f)
    lower_idx = max(0, int(n * (1 - confidence) / 2))
    upper_idx = min(n - 1, int(n * (1 + confidence) / 2))
    return (sorted_f[lower_idx], sorted_f[upper_idx])