"""
Prediction Studio — Scoring Engine.

Implements proper scoring rules from the Consensus research review:
- Brier score for binary probabilistic forecasts
- Log score for punishing overconfidence
- Interval scores for range forecasts
- Calibration buckets and reliability curves
- Sharpness/resolution decomposition
- Postmortem analysis

Key sources:
- Gneiting & Raftery (2007): strictly proper scoring rules
- Gneiting, Balabdaoui & Raftery (2007): calibration and sharpness
- Merkle & Steyvers (2013): choosing scoring rules
- Allen, Ferro & Kwasniok (2023): decomposition of proper scores
"""
from __future__ import annotations

import math
from typing import Literal


def brier_score(predictions: list[tuple[float, float]]) -> float:
    """Compute Brier score for binary probabilistic forecasts.

    Args:
        predictions: List of (predicted_probability, actual_outcome) pairs.
                     outcome is 0.0 or 1.0.

    Returns:
        Brier score (lower is better, 0.0 is perfect).
    """
    if not predictions:
        return 0.0
    return sum((p - o) ** 2 for p, o in predictions) / len(predictions)


def log_score(predictions: list[tuple[float, float]]) -> float:
    """Compute log score (negative, higher is better, 0.0 is perfect).

    Punishes overconfident wrong predictions more severely than Brier.
    """
    if not predictions:
        return 0.0
    score = 0.0
    for p, o in predictions:
        p = max(1e-10, min(1 - 1e-10, p))
        score += o * math.log(p) + (1 - o) * math.log(1 - p)
    return -score / len(predictions)


def interval_score(
    predictions: list[tuple[float, float, float, float]],
    alpha: float = 0.1,
) -> float:
    """Compute interval score for range forecasts.

    Args:
        predictions: List of (lower_bound, upper_bound, actual_value, predicted_mean).
        alpha: Significance level (default 0.1 for 90% intervals).

    Returns:
        Interval score (lower is better).
    """
    if not predictions:
        return 0.0
    total = 0.0
    for lower, upper, actual, _ in predictions:
        width = upper - lower
        penalty = 0.0
        if actual < lower:
            penalty = 2 * (lower - actual) / alpha
        elif actual > upper:
            penalty = 2 * (actual - upper) / alpha
        total += width + penalty
    return total / len(predictions)


def sharpness(predictions: list[float]) -> float:
    """Measure concentration of predictions around 0 or 1.

    Higher = more confident predictions.
    Uses mean Bernoulli variance: 4 * mean(p * (1-p)), inverted.
    """
    if not predictions:
        return 0.0
    mean_var = sum(p * (1 - p) for p in predictions) / len(predictions)
    return 1.0 - 4.0 * mean_var  # 1.0 = all 0 or 1, 0.0 = all 0.5


def calibration_buckets(
    predictions: list[tuple[float, float]],
    n_bins: int = 10,
) -> list[tuple[float, float, int]]:
    """Compute calibration curve data.

    Returns:
        List of (bin_center, observed_frequency, count) for each bin.
    """
    if not predictions:
        return []

    bins: list[list[tuple[float, float]]] = [[] for _ in range(n_bins)]
    for p, o in predictions:
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, o))

    result = []
    for i, bin_data in enumerate(bins):
        if bin_data:
            center = (i + 0.5) / n_bins
            obs_freq = sum(o for _, o in bin_data) / len(bin_data)
            result.append((center, obs_freq, len(bin_data)))
        else:
            center = (i + 0.5) / n_bins
            result.append((center, 0.0, 0))

    return result


def expected_calibration_error(
    predictions: list[tuple[float, float]],
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE)."""
    if not predictions:
        return 0.0
    buckets = calibration_buckets(predictions, n_bins)
    total = len(predictions)
    ece = 0.0
    for center, obs_freq, count in buckets:
        if count > 0:
            # Find average predicted probability in this bin
            bin_preds = [(p, o) for p, o in predictions if int(p * n_bins) == buckets.index((center, obs_freq, count))]
            if bin_preds:
                avg_pred = sum(p for p, _ in bin_preds) / len(bin_preds)
                ece += count / total * abs(avg_pred - obs_freq)
    return ece


def brier_skill_score(brier: float, reference_brier: float) -> float:
    """Compute Brier Skill Score.

    BSS = 1 - (brier / reference_brier)
    Positive = better than reference (e.g., climatology).
    """
    if reference_brier <= 0:
        return 0.0
    return 1.0 - (brier / reference_brier)


def bayesian_update(prior: float, likelihood_ratio: float) -> float:
    """Bayesian updating via odds form.

    posterior = LR * prior_odds / (1 + LR * prior_odds)
    """
    if prior <= 0 or prior >= 1:
        return prior
    prior_odds = prior / (1 - prior)
    posterior_odds = likelihood_ratio * prior_odds
    return posterior_odds / (1 + posterior_odds)


def information_gap_score(
    forecast_importance: float,
    current_uncertainty: float,
    expected_probability_shift: float,
    actionability: float,
    collection_cost: float = 1.0,
) -> float:
    """Score for prioritizing missing information collection.

    Higher = more valuable to collect.
    """
    if collection_cost <= 0:
        collection_cost = 1.0
    return (forecast_importance * current_uncertainty * expected_probability_shift * actionability) / collection_cost