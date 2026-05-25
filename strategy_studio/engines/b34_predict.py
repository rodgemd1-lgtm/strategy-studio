"""B34 — Forecast engine (linear extrapolation)."""
from __future__ import annotations

from strategy_studio.core.types import Forecast


def build_forecast(question: str, historical_data: dict[str, float]) -> Forecast:
    """Simple linear extrapolation from historical data points."""
    if not historical_data:
        return Forecast(
            variable=question,
            prediction=0.0,
            confidence_interval=(0.0, 0.0),
            method="linear_extrapolation",
        )

    sorted_keys = sorted(historical_data.keys())
    values = [historical_data[k] for k in sorted_keys]

    n = len(values)
    if n == 1:
        prediction = values[0]
    else:
        slope = (values[-1] - values[0]) / (n - 1)
        prediction = values[-1] + slope

    margin = abs(prediction) * 0.15

    return Forecast(
        variable=question,
        prediction=round(prediction, 4),
        confidence_interval=(round(prediction - margin, 4), round(prediction + margin, 4)),
        method="linear_extrapolation",
    )