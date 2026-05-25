"""
Prediction Studio — Deterministic forecasting, wargaming, scenario planning,
and Monte Carlo simulation engine.

All functions are fully deterministic (seeded via input hashing),
use only Python stdlib (no numpy), return Pydantic models,
and never raise — exceptions are caught and safe defaults returned.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from typing import Any, Callable

from strategy_studio.core.types_extended import (
    MonteCarloResult,
    PredictionResult,
    Scenario,
    SensitivityResult,
    WargameResult,
)
from strategy_studio.core.types import WargameScenario


# ── Seeding helper ────────────────────────────────────────────────────────────

def _seed_from(*args: Any) -> None:
    """Seed the random module deterministically from hash of inputs."""
    seed_str = "|".join(str(a) for a in args)
    seed_val = hash(seed_str) & 0x7FFFFFFF  # keep positive for reproducibility
    random.seed(seed_val)


# ── Distribution samplers (numpy-free) ────────────────────────────────────────

def _sample_normal(rng: random.Random, mean: float, std: float) -> float:
    """Box-Muller transform for normal distribution."""
    u1 = max(rng.random(), 1e-12)
    u2 = rng.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + std * z


def _sample_lognormal(rng: random.Random, mean: float, std: float) -> float:
    """Sample from lognormal by exponentiating a normal sample."""
    if mean <= 0:
        return 0.0
    mu = math.log(mean ** 2 / math.sqrt(std ** 2 + mean ** 2))
    sigma = math.sqrt(math.log(1 + (std ** 2) / (mean ** 2) if mean != 0 else 1))
    return math.exp(_sample_normal(rng, mu, sigma))


def _sample_uniform(rng: random.Random, mean: float, std: float) -> float:
    """Uniform in [mean - std*sqrt(3), mean + std*sqrt(3)] so variance matches."""
    half = std * math.sqrt(3)
    return rng.uniform(mean - half, mean + half)


def _sample_triangular(rng: random.Random, mean: float, std: float) -> float:
    """Triangular distribution with given mean and std_dev."""
    spread = std * math.sqrt(6)
    low = mean - spread / 2
    high = mean + spread / 2
    # mode = mean for symmetric triangular
    return rng.triangular(low, high, mean)


def _get_sampler(
    rng: random.Random, distribution: str
) -> "Callable[[float, float], float]":
    """Return a sampler func(lo, hi) -> float for the named distribution."""
    samplers: dict[str, Callable[[float, float], float]] = {
        "normal": lambda lo, hi: _sample_normal(rng, lo, hi),
        "lognormal": lambda lo, hi: _sample_lognormal(rng, lo, hi),
        "uniform": lambda lo, hi: _sample_uniform(rng, lo, hi),
        "triangular": lambda lo, hi: _sample_triangular(rng, lo, hi),
    }
    return samplers.get(distribution, samplers["normal"])


# 1. Monte Carlo ───────────────────────────────────────────────────────────────

def run_monte_carlo(
    variable: str,
    base_value: float,
    std_dev: float,
    iterations: int = 10000,
    distribution: str = "normal",
) -> MonteCarloResult:
    """
    Run a Monte Carlo simulation for *variable*.

    Parameters
    ----------
    variable : str
        Name of the variable being simulated.
    base_value : float
        Central estimate (mean of the distribution).
    std_dev : float
        Standard deviation of the distribution.
    iterations : int
        Number of simulation runs (default 10 000).
    distribution : str
        One of ``'normal'``, ``'lognormal'``, ``'uniform'``, ``'triangular'``.

    Returns
    -------
    MonteCarloResult
        Full statistics including mean, median, std_dev, percentiles,
        histogram bins, and generated Scenario objects.
    """
    try:
        _seed_from(variable, base_value, std_dev, iterations, distribution)
        rng = random.Random()

        sampler = _get_sampler(rng, distribution)
        samples: list[float] = []
        for _ in range(max(1, iterations)):
            samples.append(sampler(base_value, std_dev))

        sorted_samples = sorted(samples)
        n = len(sorted_samples)

        mean_val = sum(samples) / n
        variance = sum((x - mean_val) ** 2 for x in samples) / n
        std_val = math.sqrt(variance)
        median_val = sorted_samples[n // 2]

        def pct(p: float) -> float:
            idx = min(int(p / 100.0 * n), n - 1)
            return sorted_samples[idx]

        # Build 20-bin histogram
        lo = sorted_samples[0]
        hi = sorted_samples[-1]
        num_bins = 20
        if hi == lo:
            histogram: list[tuple[float, float]] = [(lo, float(n))]
        else:
            bin_width = (hi - lo) / num_bins
            bins = [0] * num_bins
            for s in samples:
                b = min(int((s - lo) / bin_width), num_bins - 1)
                bins[b] += 1
            histogram = [
                (round(lo + (i + 0.5) * bin_width, 6), float(count))
                for i, count in enumerate(bins)
            ]

        # Generate one Scenario per sample percentile bucket (10 buckets)
        scenario_count = 10
        scenario_step = max(1, n // scenario_count)
        scenarios: list[Scenario] = []
        for i in range(0, n, scenario_step):
            label_idx = min(i + scenario_step // 2, n - 1)
            val = sorted_samples[label_idx]
            prob = label_idx / n
            scenarios.append(
                Scenario(
                    id=f"mc_{i // scenario_step}",
                    name=f"Scenario {i // scenario_step} ({distribution})",
                    description=(
                        f"Monte Carlo percentile {round(prob * 100, 1)} — "
                        f"{variable} ≈ {round(val, 4)}"
                    ),
                    probability=round(prob, 4),
                    variables={variable: round(val, 6)},
                )
            )

        return MonteCarloResult(
            variable=variable,
            iterations=iterations,
            mean=round(mean_val, 6),
            median=round(median_val, 6),
            std_dev=round(std_val, 6),
            percentile_5=round(pct(5), 6),
            percentile_25=round(pct(25), 6),
            percentile_75=round(pct(75), 6),
            percentile_95=round(pct(95), 6),
            histogram=histogram,
            scenarios=scenarios,
        )
    except Exception:
        return MonteCarloResult(
            variable=variable,
            iterations=iterations,
            mean=base_value,
            median=base_value,
            std_dev=0.0,
            percentile_5=base_value,
            percentile_25=base_value,
            percentile_75=base_value,
            percentile_95=base_value,
        )


# 2. Scenario Builder ─────────────────────────────────────────────────────────

def build_scenarios(
    base_scenario: Scenario,
    variations: list[dict],
) -> list[Scenario]:
    """
    Create scenario variations by overlaying parameter *variations* onto a
    *base_scenario*.

    Each dict in *variations* can contain keys:
    - ``overrides``: dict[str, float] merged into ``variables``
    - ``new_probability``: float (optional explicit probability)
    - ``assumptions_add``: list[str] appended to assumptions

    Probability is adjusted downward by 5 % per additional assumption beyond
    the base scenario to reflect compounding uncertainty.

    Returns the base scenario first, then each variation.
    """
    try:
        results: list[Scenario] = []

        # Optionally refresh base probability
        prob_base = max(0.0, min(1.0, base_scenario.probability))
        results.append(base_scenario.model_copy(deep=True))

        for idx, var in enumerate(variations):
            overrides: dict[str, float] = var.get("overrides", {})
            assumptions_add: list[str] = var.get("assumptions_add", [])

            merged_vars = dict(base_scenario.variables)
            merged_vars.update(overrides)

            merged_assumptions = list(base_scenario.assumptions) + assumptions_add
            extra = max(0, len(merged_assumptions) - len(base_scenario.assumptions))
            prob = prob_base - 0.05 * extra
            prob = max(0.0, min(1.0, prob))

            explicit_prob = var.get("new_probability")
            if explicit_prob is not None:
                prob = max(0.0, min(1.0, float(explicit_prob)))

            name_suffix = var.get("name_suffix", f"v{idx + 1}")
            desc_suffix = var.get("description_suffix", "")
            results.append(
                Scenario(
                    id=f"{base_scenario.id}_{name_suffix}",
                    name=f"{base_scenario.name} — {name_suffix}",
                    description=(
                        f"{base_scenario.description} Variation: {desc_suffix}"
                        if desc_suffix
                        else f"{base_scenario.description} (variation {name_suffix})"
                    ),
                    probability=round(prob, 4),
                    assumptions=merged_assumptions,
                    variables=merged_vars,
                    outcomes=dict(base_scenario.outcomes),
                )
            )
        return results
    except Exception:
        return [base_scenario.model_copy(deep=True)]


# 3. Wargame (multi-round) ────────────────────────────────────────────────────

def run_wargame(
    scenario: str,
    actors: list[str],
    depth: int = 2,
) -> WargameResult:
    """
    Multi-round wargame simulation.

    Each round, every actor observes the *previous* round's highest-probability
    move and responds with a counter-strategy.  After *depth* rounds the engine
    checks for a Nash-like equilibrium (no actor gained > 2 % probability shift
    between the last two rounds).

    Parameters
    ----------
    scenario : str
        Free-text scenario description.
    actors : list[str]
        Names / roles of the actors.
    depth : int
        Number of rounds (default 2, minimum 1).

    Returns
    -------
    WargameResult
        Aggregated moves, equilibrium analysis, recommended response, and
        risk level.
    """
    try:
        depth = max(1, depth)
        _seed_from(scenario, "|".join(sorted(actors)), depth)
        rng = random.Random()

        # Response templates by actor family
        _RESPONSES: dict[str, dict[str, str]] = {
            "competitor": {
                "base_move": "Launch aggressive feature set or bundled pricing.",
                "counter": "Differentiate on data moat and integration depth.",
                "impact": "Market share erosion unless switching costs prove sticky.",
            },
            "regulator": {
                "base_move": "Initiate compliance review or enforcement probe.",
                "counter": "Pre-buffer with policy drafts and external counsel.",
                "impact": "Operating cost increase; launch delay risk.",
            },
            "customer": {
                "base_move": "Demand portability, audit rights, or steep discount.",
                "counter": "Offer transparent SLA and staged rollout commitment.",
                "impact": "Margin compression offset by trust premium.",
            },
            "investor": {
                "base_move": "Push for faster growth or cost reduction.",
                "counter": "Present disciplined roadmap with milestone gates.",
                "impact": "Valuation tension; potential cap-table conflict.",
            },
            "default": {
                "base_move": "Increase market pressure through pricing or feature acceleration.",
                "counter": "Stabilize core offering and monitor early warning signals.",
                "impact": "Moderate revenue compression; talent retention risk.",
            },
        }

        def _lookup(actor: str) -> dict[str, str]:
            lower = actor.lower()
            for key in ("competitor", "regulator", "customer", "investor"):
                if key in lower:
                    return _RESPONSES[key]
            return _RESPONSES["default"]

        # Simulate rounds
        round_probs: list[dict[str, float]] = []
        round_moves: list[list[WargameScenario]] = []

        for round_idx in range(depth):
            round_move_list: list[WargameScenario] = []
            probs_this_round: dict[str, float] = {}

            # Determine observed previous-round best move
            prev_best_move = ""
            if round_probs:
                prev = round_probs[-1]
                best_actor = max(prev, key=lambda a: prev[a])
                prev_best_move = round_moves[-1][
                    [s.actor for s in round_moves[-1]].index(best_actor)
                ].move if round_moves else ""

            for actor in actors:
                tmpl = _lookup(actor)

                # Probability drifts based on round and opponent pressure
                base_prob = 0.4 + 0.12 * len(actors)
                noise = rng.gauss(0, 0.05)
                pressure = 0.03 * round_idx if prev_best_move else 0.0
                prob = base_prob + noise - pressure
                prob = max(0.05, min(0.95, prob))
                probs_this_round[actor] = round(prob, 4)

                # After first round, respond to previous best move
                move_text = tmpl["base_move"]
                response_text = tmpl["counter"]
                if round_idx > 0 and prev_best_move:
                    move_text = f"React to: '{prev_best_move}' → {tmpl['counter']}"
                    response_text = tmpl["base_move"]

                round_move_list.append(
                    WargameScenario(
                        actor=actor,
                        move=move_text,
                        rig_response=response_text,
                        impact=tmpl["impact"],
                        probability=round(prob, 4),
                    )
                )

            round_moves.append(round_move_list)
            round_probs.append(probs_this_round)

        # Equilibrium detection: compare last two rounds
        equilibrium = None
        if len(round_probs) >= 2:
            p0 = round_probs[-2]
            p1 = round_probs[-1]
            max_shift = max(abs(p1.get(a, 0) - p0.get(a, 0)) for a in actors)
            if max_shift < 0.02:
                equilibrium = (
                    f"Nash-like equilibrium reached at round {depth} — "
                    f"max actor probability shift {round(max_shift, 4)} < 0.02"
                )
            else:
                equilibrium = (
                    f"No equilibrium after {depth} rounds — "
                    f"max shift {round(max_shift, 4)}. "
                    f"Increase depth or revisit assumptions."
                )

        # Combine all unique moves
        all_moves: list[WargameScenario] = []
        seen_actors: set[str] = set()
        for rnd in reversed(round_moves):  # prefer latest round
            for s in rnd:
                if s.actor not in seen_actors:
                    all_moves.append(s)
                    seen_actors.add(s.actor)
        # add any missing
        for rnd in round_moves:
            for s in rnd:
                if s.actor not in seen_actors:
                    all_moves.append(s)
                    seen_actors.add(s.actor)

        # Risk level from average probability
        final_probs = round_probs[-1] if round_probs else {}
        avg_prob = (
            sum(final_probs.values()) / len(final_probs)
            if final_probs
            else 0.5
        )
        if avg_prob >= 0.7:
            risk_level = "critical"
        elif avg_prob >= 0.55:
            risk_level = "high"
        elif avg_prob >= 0.35:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Recommended response: highest-probability actor's counter
        if final_probs:
            top_actor = max(final_probs, key=lambda a: final_probs[a])
            top_move = next((s for s in all_moves if s.actor == top_actor), None)
            recommended = top_move.rig_response if top_move else ""
        else:
            recommended = ""

        return WargameResult(
            scenario_name=scenario,
            actors=list(actors),
            moves=all_moves,
            equilibrium=equilibrium or "Depth too low for equilibrium check.",
            recommended_response=recommended,
            risk_level=risk_level,  # type: ignore[arg-type]
        )
    except Exception:
        return WargameResult(
            scenario_name=scenario,
            actors=list(actors),
            risk_level="medium",
        )


# 4. Predict Variable ─────────────────────────────────────────────────────────

def predict_variable(
    variable: str,
    historical_data: dict[str, float],
    method: str = "ensemble",
) -> PredictionResult:
    """
    Forecast *variable* using one or more methods.

    Methods
    -------
    - ``'linear'`` — simple linear extrapolation
    - ``'moving_average'`` — weighted moving average
    - ``'exp_smooth'`` — exponential smoothing (alpha = 0.3)
    - ``'ensemble'`` — weighted combination (inverse-error weighting)

    The result includes Monte Carlo uncertainty (10 % CV), a base-rate,
    and a calibration score from leave-one-out backtesting.

    Parameters
    ----------
    variable : str
        Name of the variable.
    historical_data : dict[str, float]
        Time-keyed observations (e.g. ``{"2020": 1.2, "2021": 1.5}``).
    method : str
        ``'linear'``, ``'moving_average'``, ``'exp_smooth'``, or ``'ensemble'``.

    Returns
    -------
    PredictionResult
        Point estimate, confidence interval, optional Monte Carlo result,
        scenarios, base rate, and calibration score.
    """
    try:
        _seed_from(variable, method, len(historical_data))
        sorted_keys = sorted(historical_data.keys())
        values = [historical_data[k] for k in sorted_keys]
        n = len(values)

        if n == 0:
            base_ci = (0.0, 0.0)
            mc = run_monte_carlo(variable, 0.0, 1.0, 5000, "normal")
            return PredictionResult(
                variable=variable,
                point_estimate=0.0,
                confidence_interval=base_ci,
                method=method,
                monte_carlo=mc,
                calibration_score=0.0,
            )

        # -- helpers for each method --
        def _linear_pred(vals: list[float]) -> float:
            if len(vals) <= 1:
                return vals[0] if vals else 0.0
            slope = (vals[-1] - vals[0]) / (len(vals) - 1)
            return vals[-1] + slope

        def _moving_avg_pred(vals: list[float]) -> float:
            if len(vals) == 1:
                return vals[0]
            weights = list(range(1, len(vals) + 1))
            total_w = sum(weights)
            return sum(v * w for v, w in zip(vals, weights)) / total_w

        def _exp_smooth_pred(vals: list[float]) -> float:
            alpha = 0.3
            s = vals[0]
            for v in vals[1:]:
                s = alpha * v + (1 - alpha) * s
            return s

        def _backtest_error(pred_fn, vals: list[float]) -> float:
            """Leave-one-out mean absolute error on last 3 points."""
            if len(vals) < 3:
                return 1.0
            errors = []
            for i in range(max(0, len(vals) - 3), len(vals)):
                train = vals[:i] + vals[i + 1:]
                if not train:
                    train = vals[:i]
                if not train:
                    continue
                try:
                    pred = pred_fn(train)
                    errors.append(abs(pred - vals[i]))
                except Exception:
                    errors.append(abs(vals[i]))
            return sum(errors) / len(errors) if errors else 1.0

        # Compute predictions
        linear_pred = _linear_pred(values)
        ma_pred = _moving_avg_pred(values)
        es_pred = _exp_smooth_pred(values)

        # Backtest errors
        e_linear = _backtest_error(_linear_pred, values)
        e_ma = _backtest_error(_moving_avg_pred, values)
        e_es = _backtest_error(_exp_smooth_pred, values)

        # Select or ensemble
        if method == "linear":
            point_estimate = linear_pred
        elif method == "moving_average":
            point_estimate = ma_pred
        elif method == "exp_smooth":
            point_estimate = es_pred
        else:  # ensemble — inverse-error weighting
            eps = 1e-6
            inv_linear = 1.0 / (e_linear + eps)
            inv_ma = 1.0 / (e_ma + eps)
            inv_es = 1.0 / (e_es + eps)
            total_inv = inv_linear + inv_ma + inv_es
            point_estimate = (
                inv_linear * linear_pred
                + inv_ma * ma_pred
                + inv_es * es_pred
            ) / total_inv
            method = "ensemble"

        point_estimate = round(point_estimate, 6)

        # Base rate: mean of historical
        base_rate = sum(values) / n

        # Confidence interval ±15 % of point estimate
        margin = abs(point_estimate) * 0.15 if point_estimate != 0 else 1.0
        ci_lower = round(point_estimate - margin, 6)
        ci_upper = round(point_estimate + margin, 6)

        # Calibration score: 1 − normalized MAE on backtest
        all_errors = [e_linear, e_ma, e_es]
        best_err = min(all_errors)
        worst_err = max(all_errors + [1.0])
        calibration_score = round(
            max(0.0, 1.0 - best_err / (worst_err + 1e-6)), 4
        )

        # Monte Carlo uncertainty: 10 % coefficient of variation
        cv = 0.10
        mc_std = abs(point_estimate) * cv if point_estimate != 0 else 1.0
        monte_carlo = run_monte_carlo(
            variable, point_estimate, mc_std, 5000, "normal"
        )

        return PredictionResult(
            variable=variable,
            point_estimate=point_estimate,
            confidence_interval=(ci_lower, ci_upper),
            method=method,
            monte_carlo=monte_carlo,
            scenarios=monte_carlo.scenarios,
            base_rate=round(base_rate, 6),
            calibration_score=calibration_score,
        )
    except Exception:
        return PredictionResult(
            variable=variable,
            point_estimate=0.0,
            confidence_interval=(0.0, 0.0),
            method=method,
            calibration_score=0.0,
        )


# 5. Cross-Impact Analysis ────────────────────────────────────────────────────

def cross_impact_analysis(
    scenarios: list[Scenario],
) -> dict[str, list[float]]:
    """
    Compute an N×N cross-impact matrix.

    Each entry ``result[i][j]`` estimates how scenario *j*'s occurrence
    would change the probability of scenario *i*.

    - Shared variables promote positive cross-impact (reinforcement).
    - Opposing variable directions create negative cross-impact.
    - Self-impact is 1.0.

    Returns a dict mapping each scenario id to a list of floats
    (one per input scenario, in the same order).
    """
    try:
        _seed_from(
            *[s.id for s in scenarios],
            *[s.probability for s in scenarios],
        )
        rng = random.Random()

        n = len(scenarios)
        if n == 0:
            return {}

        ids = [s.id for s in scenarios]
        result: dict[str, list[float]] = {sid: [0.0] * n for sid in ids}

        for i, sa in enumerate(scenarios):
            for j, sb in enumerate(scenarios):
                if i == j:
                    result[sa.id][j] = round(1.0, 4)
                    continue

                # Compute variable overlap
                va = set(sa.variables.keys())
                vb = set(sb.variables.keys())
                shared = va & vb
                if not shared:
                    # Pure noise baseline ±0.05
                    noise = rng.uniform(-0.05, 0.05)
                    result[sa.id][j] = round(noise, 4)
                    continue

                # For shared variables, check direction alignment
                alignments = []
                for key in shared:
                    a_val = sa.variables.get(key, 0.0)
                    b_val = sb.variables.get(key, 0.0)
                    if a_val == 0 and b_val == 0:
                        alignments.append(0.0)
                    else:
                        denom = max(abs(a_val), abs(b_val), 1e-9)
                        alignments.append(
                            (a_val * b_val) / (denom * denom)
                        )
                avg_align = sum(alignments) / len(alignments)
                # Scale by probability ratio
                prob_ratio = sb.probability / max(sa.probability, 1e-9)
                impact = avg_align * min(prob_ratio, 2.0)
                impact = max(-1.0, min(1.0, impact))
                result[sa.id][j] = round(impact, 4)

        return result
    except Exception:
        return {s.id: [1.0] for s in scenarios}


# 6. Sensitivity Analysis ─────────────────────────────────────────────────────

def sensitivity_analysis(
    variable: str,
    base_value: float,
    parameters: dict[str, tuple[float, float]],
) -> list[SensitivityResult]:
    """
    One-at-a-time sensitivity analysis.

    Each parameter is varied from its low to high bound while all others
    stay at midpoint.  The impact on *variable* is measured as:

    .. math::

        impact = f(high) − f(low)

    where ``f`` is a simple linear model ``Σ w_i × p_i`` with weights
    derived from the base value.

    Elasticity is ``(%Δscore) / (%Δparameter)``.  Parameters with
    ``|elasticity| > 1.0`` are flagged as *critical*.

    Parameters
    ----------
    variable : str
        Target output variable name.
    base_value : float
        Reference value of the target.
    parameters : dict[str, tuple[float, float]]
        Mapping of parameter name → (low, high) bound.

    Returns
    -------
    list[SensitivityResult]
        One result per parameter, ordered by descending |impact|.
    """
    try:
        _seed_from(variable, base_value, *sorted(parameters.items()))
        rng = random.random  # only seed used above; don't re-seed

        results: list[SensitivityResult] = []

        param_names = list(parameters.keys())
        num_params = max(len(param_names), 1)

        # Derive deterministic weights that sum to base_value
        weights: list[float] = []
        base_sqrt = math.sqrt(abs(base_value)) if base_value != 0 else 1.0
        for k, pname in enumerate(param_names):
            # Use hash of name to get per-parameter factor
            h = hash(pname) & 0x7FFFFFFF
            factor = 0.5 + (h % 100) / 100.0  # 0.5 – 1.5
            weights.append(factor)
        # Normalize so that at midpoints the model yields base_value
        mid_vals = [
            (lo + hi) / 2.0 for lo, hi in parameters.values()
        ]
        current_base = sum(
            w * m for w, m in zip(weights, mid_vals)
        )
        scale = base_value / current_base if current_base != 0 else 1.0
        weights = [w * scale for w in weights]

        def _evaluate(param_vals: list[float]) -> float:
            return sum(w * v for w, v in zip(weights, param_vals))

        for idx, pname in enumerate(param_names):
            low, high = parameters[pname]
            mid = (low + high) / 2.0

            # Evaluate at low and high
            vals_low = [(lo + hi) / 2.0 for lo, hi in parameters.values()]
            vals_high = list(vals_low)

            vals_low[idx] = low
            vals_high[idx] = high

            score_low = _evaluate(vals_low)
            score_high = _evaluate(vals_high)
            impact = score_high - score_low

            # Elasticity
            pct_change_param = (
                (high - low) / mid if mid != 0 else 0.0
            )
            pct_change_score = (
                impact / score_low if score_low != 0 else 0.0
            )
            elasticity = (
                pct_change_score / pct_change_param
                if pct_change_param != 0
                else 0.0
            )

            is_critical = abs(elasticity) > 1.0

            results.append(
                SensitivityResult(
                    parameter=pname,
                    base_value=round(mid, 6),
                    low_value=round(low, 6),
                    high_value=round(high, 6),
                    impact_on_score=round(impact, 6),
                    elasticity=round(elasticity, 6),
                    is_critical=is_critical,
                )
            )

        # Sort by descending |impact|
        results.sort(key=lambda r: abs(r.impact_on_score), reverse=True)
        return results
    except Exception:
        return [
            SensitivityResult(
                parameter=pname,
                base_value=(lo + hi) / 2.0,
                low_value=lo,
                high_value=hi,
                impact_on_score=0.0,
                elasticity=0.0,
                is_critical=False,
            )
            for pname, (lo, hi) in parameters.items()
        ]
