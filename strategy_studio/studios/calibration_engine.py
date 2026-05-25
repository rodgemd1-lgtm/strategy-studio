"""
Calibration Engine — Deterministic forecast calibration, scoring, and reporting.

Tracks prediction accuracy over time using Brier scores, calibration curves,
Bayesian prior updating, and feedback loops. All functions are fully
deterministic, use only Python stdlib, and never raise.

References:
    Brier, G.W. (1950). "Verification of forecasts expressed in terms
    of probability". Monthly Weather Review, 78(1), 1-3.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from strategy_studio.core.types_extended import (
    CalibrationRecord,
    CalibrationReport,
)


# ── Brier Score ───────────────────────────────────────────────────────────────

def brier_score(predictions: list[tuple[float, float]]) -> float:
    """Compute the Brier score for a set of probabilistic predictions.

    The Brier score is the mean squared difference between predicted
    probabilities and actual outcomes. It is a proper scoring rule.

    Args:
        predictions: List of (predicted_probability, actual_outcome) pairs.
            predicted_probability: float in [0, 1]
            actual_outcome: float in {0.0, 1.0} (or [0, 1] for soft outcomes)

    Returns:
        Brier score in [0.0, 1.0]. 0.0 = perfect, 1.0 = worst possible.

    Example:
        >>> brier_score([(0.9, 1.0), (0.1, 0.0), (0.8, 1.0)])
        0.02
    """
    try:
        if not predictions:
            return 0.0
        total = 0.0
        count = 0
        for pred, actual in predictions:
            p = float(max(0.0, min(1.0, pred)))
            o = float(max(0.0, min(1.0, actual)))
            total += (p - o) ** 2
            count += 1
        if count == 0:
            return 0.0
        return total / count
    except Exception:
        return 0.0


# ── Calibration Curve ────────────────────────────────────────────────────────

def calibration_curve(
    predictions: list[tuple[float, float]],
    n_bins: int = 10,
) -> list[tuple[float, float, int]]:
    """Compute calibration curve data for a set of predictions.

    Bins predictions by predicted probability and computes the observed
    frequency of positive outcomes in each bin. Perfect calibration means
    observed frequency equals bin center for all bins.

    Args:
        predictions: List of (predicted_probability, actual_outcome) pairs.
        n_bins: Number of equal-width bins in [0, 1]. Default 10.

    Returns:
        List of (bin_center, observed_frequency, count) tuples, one per bin.
        Bins with zero predictions have observed_frequency = 0.0.

    Example:
        >>> calibration_curve([(0.9, 1.0), (0.1, 0.0), (0.8, 1.0)])
        [(0.05, 0.0, 0), (0.15, 0.0, 1), ..., (0.85, 1.0, 1), (0.95, 1.0, 1)]
    """
    try:
        if not predictions or n_bins < 1:
            return []

        bins: list[list[float]] = [[] for _ in range(n_bins)]

        for pred, actual in predictions:
            p = float(max(0.0, min(1.0, pred)))
            o = float(max(0.0, min(1.0, actual)))
            # Clamp to last bin when pred == 1.0
            idx = min(int(p * n_bins), n_bins - 1)
            bins[idx].append(o)

        result: list[tuple[float, float, int]] = []
        for i in range(n_bins):
            bin_center = (i + 0.5) / n_bins
            count = len(bins[i])
            if count == 0:
                observed = 0.0
            else:
                observed = sum(bins[i]) / count
            result.append((round(bin_center, 6), round(observed, 6), count))

        return result
    except Exception:
        return []


# ── Sharpness ─────────────────────────────────────────────────────────────────

def sharpness(predictions: list[float]) -> float:
    """Measure the sharpness (concentration) of a set of predictions.

    Sharpness quantifies how concentrated predictions are around 0 and 1,
    as opposed to clustered near 0.5 (uninformative). Computed as the
    mean of 4 * p * (1 - p) subtracted from 1, so that:
    - All predictions at 0 or 1 => sharpness = 1.0 (maximally sharp)
    - All predictions at 0.5 => sharpness = 0.0 (least sharp)

    This is equivalent to 1 - mean(4 * p * (1 - p)), where 4*p*(1-p)
    is the variance of a Bernoulli(p) random variable (max 1.0 at p=0.5).

    Args:
        predictions: List of predicted probabilities in [0, 1].

    Returns:
        Sharpness in [0.0, 1.0]. Higher = more confident predictions.

    Example:
        >>> sharpness([0.99, 0.01, 0.95, 0.05])
        0.96
        >>> sharpness([0.5, 0.5, 0.5])
        0.0
    """
    try:
        if not predictions:
            return 0.0
        total = 0.0
        count = 0
        for p in predictions:
            p = float(max(0.0, min(1.0, p)))
            # Bernoulli variance = p * (1 - p), max = 0.25 at p = 0.5
            # Normalized: 4 * p * (1 - p), range [0, 1]
            total += 4.0 * p * (1.0 - p)
            count += 1
        if count == 0:
            return 0.0
        mean_variance = total / count
        # Invert: low variance of p (near 0 or 1) => high sharpness
        return round(1.0 - mean_variance, 6)
    except Exception:
        return 0.0


# ── Forecast Tracking ────────────────────────────────────────────────────────

def track_forecast(
    forecast_id: str,
    predicted: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    """Record a forecast vs actual outcome and compute error metrics.

    Compares predicted probabilities against actual outcomes for one or
    more variables, computing per-variable and overall error metrics.

    Args:
        forecast_id: Unique identifier for this forecast.
        predicted: Dict mapping variable names to predicted probabilities.
            Example: {"market_growth": 0.8, "churn_rate": 0.2}
        actual: Dict mapping variable names to actual outcomes (0.0 or 1.0).
            Example: {"market_growth": 1.0, "churn_rate": 0.0}

    Returns:
        Tracking record dict with:
            - forecast_id: str
            - timestamp: ISO-8601 timestamp
            - variables: list of per-variable error dicts
            - overall_brier: float
            - overall_mae: float (mean absolute error)
            - overall_mse: float (mean squared error)
            - n_variables: int
            - predicted: original predicted dict
            - actual: original actual dict

    Example:
        >>> result = track_forecast("fc-001", {"a": 0.9}, {"a": 1.0})
        >>> result["overall_brier"]
        0.01
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        variables: list[dict[str, Any]] = []
        pairs: list[tuple[float, float]] = []

        # Union of all variable names
        all_vars = set(predicted.keys()) | set(actual.keys())

        for var in sorted(all_vars):
            pred_val = float(predicted.get(var, 0.5))
            actual_val = float(actual.get(var, 0.5))
            pred_val = max(0.0, min(1.0, pred_val))
            actual_val = max(0.0, min(1.0, actual_val))

            abs_err = abs(pred_val - actual_val)
            sq_err = (pred_val - actual_val) ** 2
            correct = abs_err < 0.5  # correct if prediction on right side of 0.5

            variables.append({
                "variable": var,
                "predicted": pred_val,
                "actual": actual_val,
                "absolute_error": round(abs_err, 6),
                "squared_error": round(sq_err, 6),
                "correct": correct,
            })
            pairs.append((pred_val, actual_val))

        n = len(pairs)
        overall_brier = brier_score(pairs)
        overall_mae = sum(abs(p - o) for p, o in pairs) / max(n, 1)
        overall_mse = sum((p - o) ** 2 for p, o in pairs) / max(n, 1)

        return {
            "forecast_id": str(forecast_id),
            "timestamp": timestamp,
            "variables": variables,
            "overall_brier": round(overall_brier, 6),
            "overall_mae": round(overall_mae, 6),
            "overall_mse": round(overall_mse, 6),
            "n_variables": n,
            "predicted": dict(predicted),
            "actual": dict(actual),
        }
    except Exception:
        return {
            "forecast_id": str(forecast_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "variables": [],
            "overall_brier": 0.0,
            "overall_mae": 0.0,
            "overall_mse": 0.0,
            "n_variables": 0,
            "predicted": dict(predicted) if predicted else {},
            "actual": dict(actual) if actual else {},
        }


# ── Calibration Report ───────────────────────────────────────────────────────

def calibration_report(
    forecast_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a full calibration report from forecast history.

    Analyzes a history of tracked forecasts to produce a comprehensive
    calibration report including Brier score, calibration curve, sharpness,
    and reliability diagram data.

    Args:
        forecast_history: List of tracking records (as returned by
            track_forecast), each containing at minimum:
            - predicted: dict of variable -> probability
            - actual: dict of variable -> outcome

    Returns:
        Dict with:
            - sample_size: int (number of prediction pairs)
            - brier_score: float
            - brier_skill_score: float or None
            - sharpness: float
            - calibration_curve: list of (bin_center, observed_freq, count)
            - reliability_diagram: list of dicts for plotting
            - mean_absolute_error: float
            - mean_squared_error: float
            - resolution: float (variance of observed outcomes)
            - reliability: float (weighted mean squared calibration error)
            - reference_brier: float or None (Brier score of climatology)
            - generated_at: ISO-8601 timestamp

    Example:
        >>> history = [
        ...     {"predicted": {"a": 0.9}, "actual": {"a": 1.0}},
        ...     {"predicted": {"a": 0.1}, "actual": {"a": 0.0}},
        ... ]
        >>> report = calibration_report(history)
        >>> report["brier_score"]
        0.01
    """
    try:
        # Collect all (predicted, actual) pairs from history
        pairs: list[tuple[float, float]] = []
        for record in forecast_history:
            predicted = record.get("predicted", {})
            actual = record.get("actual", {})
            if isinstance(predicted, dict) and isinstance(actual, dict):
                for var in predicted:
                    if var in actual:
                        p = float(max(0.0, min(1.0, predicted[var])))
                        o = float(max(0.0, min(1.0, actual[var])))
                        pairs.append((p, o))

        n = len(pairs)
        if n == 0:
            return {
                "sample_size": 0,
                "brier_score": 0.0,
                "brier_skill_score": None,
                "sharpness": 0.0,
                "calibration_curve": [],
                "reliability_diagram": [],
                "mean_absolute_error": 0.0,
                "mean_squared_error": 0.0,
                "resolution": 0.0,
                "reliability": 0.0,
                "reference_brier": None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        # Core metrics
        bs = brier_score(pairs)
        preds = [p for p, _ in pairs]
        sh = sharpness(preds)
        curve = calibration_curve(pairs, n_bins=10)

        # Mean absolute error and MSE
        mae = sum(abs(p - o) for p, o in pairs) / n
        mse = sum((p - o) ** 2 for p, o in pairs) / n

        # Climatology reference: Brier score of always predicting base rate
        base_rate = sum(o for _, o in pairs) / n
        ref_brier = sum((base_rate - o) ** 2 for _, o in pairs) / n

        # Brier Skill Score
        bss = brier_skill_score(bs, ref_brier)

        # Resolution: variance of observed outcomes around base rate
        resolution = sum((o - base_rate) ** 2 for _, o in pairs) / n

        # Reliability: weighted average of (bin_center - observed_freq)^2
        reliability = 0.0
        for bin_center, observed_freq, count in curve:
            if count > 0:
                reliability += count * (bin_center - observed_freq) ** 2
        reliability = reliability / n if n > 0 else 0.0

        # Build reliability diagram data for plotting
        reliability_diagram: list[dict[str, Any]] = []
        for bin_center, observed_freq, count in curve:
            reliability_diagram.append({
                "bin_center": bin_center,
                "observed_frequency": observed_freq,
                "count": count,
                "perfect_calibration": bin_center,
                "deviation": round(observed_freq - bin_center, 6),
            })

        return {
            "sample_size": n,
            "brier_score": round(bs, 6),
            "brier_skill_score": round(bss, 6) if bss is not None else None,
            "sharpness": round(sh, 6),
            "calibration_curve": curve,
            "reliability_diagram": reliability_diagram,
            "mean_absolute_error": round(mae, 6),
            "mean_squared_error": round(mse, 6),
            "resolution": round(resolution, 6),
            "reliability": round(reliability, 6),
            "reference_brier": round(ref_brier, 6),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return {
            "sample_size": 0,
            "brier_score": 0.0,
            "brier_skill_score": None,
            "sharpness": 0.0,
            "calibration_curve": [],
            "reliability_diagram": [],
            "mean_absolute_error": 0.0,
            "mean_squared_error": 0.0,
            "resolution": 0.0,
            "reliability": 0.0,
            "reference_brier": None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# ── Bayesian Prior Updating ──────────────────────────────────────────────────

def update_prior(prior: float, likelihood_ratio: float) -> float:
    """Update a prior probability using Bayes' theorem via likelihood ratio.

    Computes the posterior probability given a prior and a likelihood ratio
    (also called the Bayes factor). This is the odds form of Bayes' theorem:

        posterior_odds = likelihood_ratio * prior_odds
        posterior = posterior_odds / (1 + posterior_odds)

    Args:
        prior: Prior probability in (0, 1). Exactly 0 or 1 will be
            clamped to a small epsilon to avoid division issues.
        likelihood_ratio: Likelihood ratio (P(evidence | hypothesis) /
            P(evidence | not hypothesis)). Must be >= 0. Values > 1
            support the hypothesis; values < 1 undermine it.

    Returns:
        Posterior probability in [0, 1].

    Example:
        >>> update_prior(0.5, 3.0)  # 3x more likely if hypothesis true
        0.75
        >>> update_prior(0.1, 10.0)  # Strong evidence
        0.526316
    """
    try:
        # Clamp prior to avoid log(0) / division by zero
        p = float(max(1e-12, min(1.0 - 1e-12, prior)))
        lr = float(max(0.0, likelihood_ratio))

        # Convert to odds
        prior_odds = p / (1.0 - p)
        posterior_odds = lr * prior_odds

        # Convert back to probability
        posterior = posterior_odds / (1.0 + posterior_odds)
        return round(max(0.0, min(1.0, posterior)), 6)
    except Exception:
        return float(prior) if isinstance(prior, (int, float)) else 0.5


# ── Brier Skill Score ────────────────────────────────────────────────────────

def brier_skill_score(brier: float, reference_brier: float) -> float:
    """Compute the Brier Skill Score (BSS) relative to a reference forecast.

    The Brier Skill Score measures the improvement of a forecast over a
    reference forecast (e.g., climatology, persistence, or a baseline model).

        BSS = 1 - (Brier / reference_Brier)

    Interpretation:
        - BSS = 1.0: perfect forecast (Brier = 0)
        - BSS = 0.0: no improvement over reference
        - BSS < 0.0: worse than reference

    Args:
        brier: Brier score of the forecast being evaluated.
        reference_brier: Brier score of the reference forecast.
            Must be > 0 to avoid division by zero.

    Returns:
        Brier Skill Score. Positive = better than reference.
        Returns 0.0 if reference_brier is 0 or invalid.

    Example:
        >>> brier_skill_score(0.05, 0.25)  # Much better than climatology
        0.8
        >>> brier_skill_score(0.3, 0.25)  # Worse than climatology
        -0.2
    """
    try:
        b = float(brier)
        ref = float(reference_brier)
        if ref <= 0.0:
            return 0.0
        return round(1.0 - (b / ref), 6)
    except Exception:
        return 0.0
