"""B34 — Forecast engine (linear extrapolation)."""
from __future__ import annotations

from strategy_studio.core.types import Forecast


def build_forecast(question: str, historical_data: dict[str, float]) -> Forecast:
    """Simple linear extrapolation from historical data points."""
    if not historical_data:
        return Forecast(
            question=question,
            prediction=0.0,
            confidence_low=0.0,
            confidence_high=0.0,
            confidence=0.0,
            method="linear_extrapolation",
            evidence_count=0,
        )

    sorted_keys = sorted(historical_data.keys())
    values = [historical_data[k] for k in sorted_keys]

    n = len(values)
    if n == 1:
        prediction = values[0]
    else:
        # Linear fit: slope between first and last point projected one step forward
        slope = (values[-1] - values[0]) / (n - 1)
        prediction = values[-1] + slope

    confidence = 0.6 if n >= 3 else 0.4
    margin = abs(prediction) * 0.15
    confidence_low = prediction - margin
    confidence_high = prediction + margin

    return Forecast(
        question=question,
        prediction=round(prediction, 4),
        confidence_low=round(confidence_low, 4),
        confidence_high=round(confidence_high, 4),
        confidence=round(confidence, 4),
        method="linear_extrapolation",
        evidence_count=n,
    )
