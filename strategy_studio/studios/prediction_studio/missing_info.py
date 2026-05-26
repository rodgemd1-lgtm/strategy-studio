"""
Prediction Studio — Missing Information Engine.

Ranks missing information by value and generates OmniScout collection tasks.

Information Gap Score = (Forecast Importance × Current Uncertainty × Expected Probability Shift × Actionability) / Collection Cost
"""
from __future__ import annotations

from .core import ForecastRecord, MissingInfoTask


def compute_information_gap_score(
    forecast_importance: float,
    current_uncertainty: float,
    expected_probability_shift: float,
    actionability: float,
    collection_cost: float = 1.0,
) -> float:
    """Score for prioritizing missing information collection. Higher = more valuable."""
    if collection_cost <= 0:
        collection_cost = 1.0
    return (forecast_importance * current_uncertainty * expected_probability_shift * actionability) / collection_cost


def identify_missing_information(forecast: ForecastRecord) -> list[MissingInfoTask]:
    """Identify and rank missing information for a forecast.

    Analyzes the forecast's causal tree, evidence gaps, and uncertainty
    to generate prioritized collection tasks.
    """
    tasks = []

    # Check for missing base rate
    if forecast.base_rate is None:
        tasks.append(MissingInfoTask(
            forecast_id=forecast.forecast_id,
            information_needed=f"Base rate for: {forecast.question}",
            why_it_matters="Base rate anchors the forecast and prevents base-rate neglect",
            collection_targets=["historical_data", "industry_benchmarks", "academic_research"],
            allowed_sources=["openalex", "semantic_scholar", "google_scholar", "lakeos"],
            priority="high",
            information_gap_score=compute_information_gap_score(
                forecast_importance=0.8,
                current_uncertainty=0.7,
                expected_probability_shift=0.3,
                actionability=0.9,
                collection_cost=2.0,
            ),
        ))

    # Check for missing market prior
    if not forecast.market_priors:
        tasks.append(MissingInfoTask(
            forecast_id=forecast.forecast_id,
            information_needed=f"Market probability for: {forecast.question}",
            why_it_matters="Prediction markets aggregate dispersed information",
            collection_targets=["kalshi", "polymarket", "metaculus", "manifold"],
            allowed_sources=["market_apis"],
            priority="medium",
            information_gap_score=compute_information_gap_score(
                forecast_importance=0.6,
                current_uncertainty=0.5,
                expected_probability_shift=0.2,
                actionability=0.7,
                collection_cost=1.0,
            ),
        ))

    # Check evidence balance
    evidence_for = len(forecast.evidence_for)
    evidence_against = len(forecast.evidence_against)
    if evidence_for > 0 and evidence_against == 0:
        tasks.append(MissingInfoTask(
            forecast_id=forecast.forecast_id,
            information_needed=f"Evidence against: {forecast.question}",
            why_it_matters="One-sided evidence risks confirmation bias. Need adversarial evidence.",
            collection_targets=["contrarian_sources", "competitor_analysis", "risk_factors"],
            allowed_sources=["web", "omniscout", "lakeos"],
            priority="high",
            information_gap_score=compute_information_gap_score(
                forecast_importance=0.9,
                current_uncertainty=0.6,
                expected_probability_shift=0.4,
                actionability=0.8,
                collection_cost=1.5,
            ),
        ))

    # Check for missing causal drivers
    if forecast.causal_tree_id is None:
        tasks.append(MissingInfoTask(
            forecast_id=forecast.forecast_id,
            information_needed=f"Causal drivers for: {forecast.question}",
            why_it_matters="Causal thesis tree makes reasoning explicit and testable",
            collection_targets=["domain_experts", "industry_reports", "academic_papers"],
            allowed_sources=["openalex", "web", "omniscout"],
            priority="medium",
            information_gap_score=compute_information_gap_score(
                forecast_importance=0.7,
                current_uncertainty=0.5,
                expected_probability_shift=0.2,
                actionability=0.6,
                collection_cost=3.0,
            ),
        ))

    # Sort by information gap score
    tasks.sort(key=lambda t: t.information_gap_score, reverse=True)
    return tasks