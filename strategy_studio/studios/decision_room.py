"""
Decision Room — Multi-criteria decision analysis, sensitivity analysis,
recommendation generation, and option comparison.

All functions are deterministic. Uses only Python stdlib.
"""
from __future__ import annotations

import math
from typing import Callable

from strategy_studio.core.types import Option
from strategy_studio.core.types_extended import (
    DecisionMatrix,
    DecisionRoomResult,
    OptionScore,
    SensitivityResult,
)


def build_decision_matrix(
    options: list[Option],
    criteria: list[str],
    weights: dict[str, float],
    scoring_func: Callable[[Option, str], float] | None = None,
) -> DecisionMatrix:
    """Multi-criteria decision analysis (MCDA).

    Scores each option on each criterion, applies weights, ranks, and tiers.
    """
    if not options or not criteria:
        return DecisionMatrix(options=[], criteria=criteria, weights=weights)

    # Default scoring: derive from option score + small variation per criterion
    def _default_score(opt: Option, criterion: str) -> float:
        h = hash((opt.id, criterion)) % 1000 / 1000.0
        return round(opt.score * 0.8 + h * 0.2, 4)

    score_fn = scoring_func or _default_score

    # Normalize weights
    total_w = sum(weights.values()) or 1.0
    norm_weights = {k: v / total_w for k, v in weights.items()}

    option_scores: list[OptionScore] = []
    for opt in options:
        crit_scores: dict[str, float] = {}
        weighted: dict[str, float] = {}
        for c in criteria:
            s = score_fn(opt, c)
            crit_scores[c] = round(max(0.0, min(1.0, s)), 4)
            weighted[c] = round(crit_scores[c] * norm_weights.get(c, 0.0), 4)

        total = sum(weighted.values())

        option_scores.append(OptionScore(
            option_id=opt.id,
            option_title=opt.title,
            total_score=round(total, 4),
            criteria_scores=crit_scores,
            weighted_scores=weighted,
            confidence="H" if total > 0.7 else "M" if total > 0.4 else "L",
        ))

    # Rank
    option_scores.sort(key=lambda o: o.total_score, reverse=True)
    for i, os in enumerate(option_scores):
        os.rank = i + 1
        os.tier = "A" if i == 0 else "B" if i <= 2 else "C" if i <= 4 else "D"

    return DecisionMatrix(
        options=option_scores,
        criteria=criteria,
        weights=norm_weights,
    )


def run_sensitivity_analysis(
    matrix: DecisionMatrix,
    perturbation: float = 0.1,
) -> list[SensitivityResult]:
    """One-at-a-time sensitivity analysis on each weight."""
    results: list[SensitivityResult] = []
    base_scores = {os.option_id: os.total_score for os in matrix.options}
    if not matrix.options or not matrix.criteria:
        return results

    for criterion in matrix.criteria:
        base_w = matrix.weights.get(criterion, 0.0)
        # Perturb weight up
        new_w_low = max(0.0, base_w - perturbation)
        new_w_high = min(1.0, base_w + perturbation)

        # Recompute scores with perturbed weight
        low_total = 0.0
        high_total = 0.0
        for os in matrix.options:
            ws_low = os.criteria_scores.get(criterion, 0.0) * new_w_low
            ws_high = os.criteria_scores.get(criterion, 0.0) * new_w_high
            base_ws = os.weighted_scores.get(criterion, 0.0)
            low_total += (os.total_score - base_ws + ws_low)
            high_total += (os.total_score - base_ws + ws_high)

        avg_base = sum(base_scores.values()) / len(base_scores) if base_scores else 0.0
        impact = max(abs(high_total - low_total), 0.0)

        elasticity = 0.0
        if avg_base > 0 and base_w > 0:
            pct_change_score = (high_total - low_total) / avg_base
            pct_change_param = (new_w_high - new_w_low) / base_w
            elasticity = pct_change_score / pct_change_param if pct_change_param > 0 else 0.0

        results.append(SensitivityResult(
            parameter=criterion,
            base_value=base_w,
            low_value=new_w_low,
            high_value=new_w_high,
            impact_on_score=round(impact, 4),
            elasticity=round(elasticity, 4),
            is_critical=(abs(elasticity) > 1.0),
        ))

    results.sort(key=lambda r: abs(r.impact_on_score), reverse=True)
    return results


def generate_recommendation(matrix: DecisionMatrix) -> DecisionRoomResult:
    """Generate recommendation from decision matrix."""
    if not matrix.options:
        return DecisionRoomResult(
            title="No options available",
            decision_matrix=matrix,
            confidence="L",
        )

    top = matrix.options[0]
    runner_up = matrix.options[1] if len(matrix.options) > 1 else None

    margin = (top.total_score - runner_up.total_score) if runner_up else 1.0

    risks: list[str] = []
    if margin < 0.05 and runner_up:
        risks.append(f"Close decision: {top.option_title} leads {runner_up.option_title} by only {round(margin, 3)}")
    if top.total_score < 0.4:
        risks.append("Low overall scores — none of the options are strong")
    if len(matrix.options) > 2:
        scores_range = matrix.options[0].total_score - matrix.options[-1].total_score
        if scores_range < 0.1:
            risks.append("All options score similarly — decision may not matter")

    next_steps: list[str] = [
        f"Proceed with {top.option_title} (score: {top.total_score})",
    ]
    if runner_up and margin < 0.1:
        next_steps.append(f"Consider {runner_up.option_title} as backup (score: {runner_up.total_score})")

    return DecisionRoomResult(
        title=f"Recommendation: {top.option_title}",
        decision_matrix=matrix,
        risks=risks,
        next_steps=next_steps,
        confidence="H" if margin > 0.15 and top.total_score > 0.6 else "M",
    )


def compare_options(option_a: Option, option_b: Option, criteria: list[str]) -> dict:
    """Head-to-head comparison of two options."""
    diff = option_a.score - option_b.score
    winner = option_a if diff >= 0 else option_b
    loser = option_b if diff >= 0 else option_a

    return {
        "winner": winner.id,
        "winner_title": winner.title,
        "loser": loser.id,
        "margin": round(abs(diff), 4),
        "criteria": criteria,
        "option_a_score": option_a.score,
        "option_b_score": option_b.score,
    }


def tornado_analysis(matrix: DecisionMatrix) -> list[SensitivityResult]:
    """Tornado diagram — rank parameters by impact."""
    return run_sensitivity_analysis(matrix, perturbation=0.15)


def value_of_information(matrix: DecisionMatrix, parameter: str) -> float:
    """Expected value of perfect information for a parameter."""
    sensitivity = run_sensitivity_analysis(matrix)
    for s in sensitivity:
        if s.parameter == parameter:
            # EVPI = |impact| * elasticity
            return round(abs(s.impact_on_score) * abs(s.elasticity), 4)
    return 0.0