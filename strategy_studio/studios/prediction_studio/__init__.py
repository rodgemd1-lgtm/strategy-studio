"""Prediction Studio — Closed-loop probabilistic decision system."""
from .core import (
    ForecastRecord,
    ForecastStore,
    SignalRegistry,
    Signal,
    MarketPrior,
    CausalThesisTree,
    CausalDriver,
    FrictionAnalysis,
    MissingInfoTask,
    EvidenceUpdate,
    Postmortem,
    ForecastCategory,
    ForecastStatus,
    ResolutionMatchQuality,
)
from .scoring import (
    brier_score,
    log_score,
    interval_score,
    sharpness,
    calibration_buckets,
    expected_calibration_error,
    bayesian_update,
    brier_skill_score,
    information_gap_score,
)
from .ensemble import (
    simple_ensemble,
    weighted_ensemble,
    extremized_ensemble,
    compute_ensemble,
    compute_uncertainty_interval,
    sequential_bayesian_update,
    compute_likelihood_ratio,
)
from .priors import (
    extract_market_prior,
    validate_market_match,
    find_base_rate,
)
from .missing_info import (
    identify_missing_information,
)

# ── Stub functions for backward compatibility with session.py ──

def build_scenarios(base, variations):
    """Stub: Build strategic scenarios."""
    return []

def cross_impact_analysis(scenarios):
    """Stub: Cross-impact analysis."""
    return {}

def predict_variable(variable, data, method="ensemble"):
    """Stub: Predict a variable."""
    return {"variable": variable, "point_estimate": 0.0, "confidence_interval": (0.0, 0.0), "method": method}

def run_monte_carlo(variable, base_value, std_dev, iterations=10000, distribution="normal"):
    """Stub: Monte Carlo simulation."""
    return {"variable": variable, "iterations": iterations, "mean": base_value, "std_dev": std_dev}

def run_wargame(scenario, actors, depth=2):
    """Stub: Run competitive wargame."""
    return {"scenario_name": scenario, "actors": actors, "moves": [], "risk_level": "medium", "recommended_response": ""}

def sensitivity_analysis(variable, base_value, parameters):
    """Stub: Sensitivity analysis."""
    return [{"parameter": k, "impact_on_score": 0.0, "elasticity": 0.0, "is_critical": False} for k in parameters]
