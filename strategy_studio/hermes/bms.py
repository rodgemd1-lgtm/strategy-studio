"""
RIG BMS (Build Mode Scoring) Engine
Day 1 deliverable. Pure deterministic scoring. No LLM.

Calculates a 0.0-1.0 confidence score from 3 hard factors,
applies adjustments, and selects the BMS mode (A1/A2/A3/A4).

BMS Bands:
  A1 (≥0.75): PYTHON_ONLY — no model in decision path
  A2 (0.45-0.74): HYBRID — Python-gated LLM
  A3 (0.25-0.44): AGENT_BOUNDED — LangGraph/CrewAI, bounded
  A4 (<0.25): LLM_AGENT_FREE — hierarchical CrewAI, human signoff
"""

from __future__ import annotations
from dataclasses import dataclass
from strategy_studio.lattice._types_reexport import BMSMode, Level


# ─────────────────────────────────────────────
# BMS Scoring Engine
# ─────────────────────────────────────────────

@dataclass
class BMSResult:
    """Result of a BMS scoring calculation."""
    raw_score: float
    adjusted_score: float
    mode: BMSMode
    c1_failure_cost: float
    c2_reversibility: float
    c10_mechanism_clarity: float
    adj_failure: float
    adj_volume: float
    adj_altitude: float
    rationale: str


def calculate_bms(
    c1_failure_cost: float,
    c2_reversibility: float,
    c10_mechanism_clarity: float,
    recent_failure: bool = False,
    volume_factor: int = 1,
    altitude: Level = Level.L1,
) -> BMSResult:
    """
    Calculate BMS score from 3 hard factors + adjustments.

    All inputs are 0.0-1.0 where 1.0 = high.
    C1 is reversed: low failure cost = high confidence.

    Args:
        c1_failure_cost: 0.0 (low cost) to 1.0 (high cost). Will be reversed.
        c2_reversibility: 0.0 (irreversible) to 1.0 (easily reversible).
        c10_mechanism_clarity: 0.0 (unclear) to 1.0 (clear cause→effect).
        recent_failure: True if this workflow failed recently (-0.10 penalty).
        volume_factor: Multiplier for transaction volume (+0.05 per 10x, max +0.20).
        altitude: The Level (L1-L7) for altitude penalty.

    Returns:
        BMSResult with score, mode, and rationale.
    """
    # Validate inputs
    for name, val in [("c1_failure_cost", c1_failure_cost),
                       ("c2_reversibility", c2_reversibility),
                       ("c10_mechanism_clarity", c10_mechanism_clarity)]:
        if not 0.0 <= val <= 1.0:
            raise ValueError(f"{name} must be 0.0-1.0, got {val}")

    # Raw score: average of 3 factors (C1 reversed)
    raw = ((1.0 - c1_failure_cost) + c2_reversibility + c10_mechanism_clarity) / 3.0

    # Adjustments
    adj_failure = -0.10 if recent_failure else 0.0
    adj_volume = min(0.05 * (volume_factor // 10), 0.20)
    # Altitude penalty: L1=0, L2=0, L3=0, L4=-0.05, L5=-0.10, L6=-0.15, L7=-0.20
    _penalties = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": -0.05, "L5": -0.10, "L6": -0.15, "L7": -0.20}
    adj_altitude = _penalties.get(altitude.value, 0.0)

    # Clamp to 0.0-1.0
    adjusted = max(0.0, min(1.0, raw + adj_failure + adj_volume + adj_altitude))

    # Select mode
    mode = BMSMode.from_score(adjusted)

    # Build rationale
    rationale_parts = [
        f"Raw={raw:.2f} (C1={1.0-c1_failure_cost:.2f}, C2={c2_reversibility:.2f}, C10={c10_mechanism_clarity:.2f})",
    ]
    if adj_failure:
        rationale_parts.append(f"Failure penalty: {adj_failure:.2f}")
    if adj_volume:
        rationale_parts.append(f"Volume bonus: +{adj_volume:.2f}")
    if adj_altitude:
        rationale_parts.append(f"Altitude penalty ({altitude.value}): {adj_altitude:.2f}")
    rationale_parts.append(f"Final={adjusted:.2f} → {mode.value} ({mode.description})")

    return BMSResult(
        raw_score=round(raw, 4),
        adjusted_score=round(adjusted, 4),
        mode=mode,
        c1_failure_cost=c1_failure_cost,
        c2_reversibility=c2_reversibility,
        c10_mechanism_clarity=c10_mechanism_clarity,
        adj_failure=adj_failure,
        adj_volume=adj_volume,
        adj_altitude=adj_altitude,
        rationale=" | ".join(rationale_parts),
    )


def score_workflow(
    failure_cost: float,
    reversibility: float,
    mechanism_clarity: float,
    recent_failure: bool = False,
    volume: int = 1,
    level: str = "L1",
) -> BMSResult:
    """
    Convenience wrapper for scoring a workflow by string level.

    Args:
        failure_cost: 0.0-1.0 (high cost = 1.0)
        reversibility: 0.0-1.0 (easy rollback = 1.0)
        mechanism_clarity: 0.0-1.0 (clear = 1.0)
        recent_failure: True if recent failure
        volume: Transaction volume multiplier
        level: L1-L7 string

    Returns:
        BMSResult
    """
    try:
        altitude = Level(level)
    except ValueError:
        raise ValueError(f"Invalid level: {level}. Must be L1-L7.")

    return calculate_bms(
        c1_failure_cost=failure_cost,
        c2_reversibility=reversibility,
        c10_mechanism_clarity=mechanism_clarity,
        recent_failure=recent_failure,
        volume_factor=volume,
        altitude=altitude,
    )


# ─────────────────────────────────────────────
# Batch Scoring
# ─────────────────────────────────────────────

def score_workflows_batch(workflows: list[dict]) -> list[BMSResult]:
    """
    Score multiple workflows at once.

    Each workflow dict should have:
      - failure_cost, reversibility, mechanism_clarity (required)
      - recent_failure, volume, level (optional)
    """
    results = []
    for wf in workflows:
        result = score_workflow(
            failure_cost=wf["failure_cost"],
            reversibility=wf["reversibility"],
            mechanism_clarity=wf["mechanism_clarity"],
            recent_failure=wf.get("recent_failure", False),
            volume=wf.get("volume", 1),
            level=wf.get("level", "L1"),
        )
        results.append(result)
    return results
