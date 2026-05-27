"""
RIG Lattice Cell ID Validator
Day 1 deliverable. Pure deterministic parsing. No models.

Validates cell IDs in format: L<level>-D<diamond>-A<mode>-<step>
Rejects old format: L<level>-D<diamond>-<step> (missing Z-axis)

Also validates workflow classification YAML and BMS scoring inputs.
"""

import re
from typing import Optional
from strategy_studio.lattice._types_reexport import (
    LatticeCoordinate,
    Level,
    Diamond,
    BMSMode,
    IQRSQPIStep,
    CELL_ID_PATTERN_STRICT,
    OLD_CELL_ID_PATTERN,
)


# ─────────────────────────────────────────────
# Cell ID Parser
# ─────────────────────────────────────────────

def parse_cell_id(cell_id: str) -> LatticeCoordinate:
    """
    Parse a cell ID string into a LatticeCoordinate.

    Accepts: L2-D1-A1-I1
    Rejects: L2-D1-Intent (old format that omits the Z-axis)

    Args:
        cell_id: The cell ID string to parse.

    Returns:
        LatticeCoordinate with all four axes resolved.

    Raises:
        ValueError: If the cell ID is invalid or uses the old format.
    """
    # First check if it matches the old format — reject explicitly
    if re.match(OLD_CELL_ID_PATTERN, cell_id):
        raise ValueError(
            f"Invalid cell ID (old format, missing Z-axis): {cell_id}. "
            f"Expected format: L<level>-D<diamond>-A<mode>-<step> "
            f"(e.g., L2-D1-A1-I1)"
        )

    m = re.match(CELL_ID_PATTERN_STRICT, cell_id)
    if not m:
        raise ValueError(
            f"Invalid cell ID: {cell_id}. "
            f"Expected format: L<level>-D<diamond>-A<mode>-<step> "
            f"(e.g., L2-D1-A1-I1)"
        )

    l, d, a, s = m.groups()
    # Regex captures digits (1-7, 1-3, 1-4, step code) — must construct
    # full enum value strings: "L2", "D1", "A1", "I1"/"Q1"/"R"/etc.
    return LatticeCoordinate(
        level=Level(f"L{l}"),
        diamond=Diamond(f"D{d}"),
        bms_mode=BMSMode(f"A{a}"),
        step=IQRSQPIStep(s),  # step codes already include the letter
    )


def is_valid_cell_id(cell_id: str) -> bool:
    """Check if a cell ID is valid without raising."""
    try:
        parse_cell_id(cell_id)
        return True
    except ValueError:
        return False


def is_old_format(cell_id: str) -> bool:
    """Check if a cell ID uses the old (pre-Z-axis) format."""
    return bool(re.match(OLD_CELL_ID_PATTERN, cell_id))


# ─────────────────────────────────────────────
# Workflow Classification Validator
# ─────────────────────────────────────────────

def validate_workflow_classification(
    workflow_id: str,
    description: str,
    level: str,
    diamond: str,
    bms_score: float,
    mode: str,
    rationale: str,
) -> dict:
    """
    Validate a workflow classification entry.

    Returns a dict with 'valid' bool and 'errors' list.
    """
    errors = []

    # Validate level
    try:
        Level(level)
    except ValueError:
        errors.append(f"Invalid level: {level}. Must be L1-L7.")

    # Validate diamond
    try:
        Diamond(diamond)
    except ValueError:
        errors.append(f"Invalid diamond: {diamond}. Must be D1, D2, or D3.")

    # Validate BMS score
    if not 0.0 <= bms_score <= 1.0:
        errors.append(f"Invalid BMS score: {bms_score}. Must be 0.0-1.0.")

    # Validate mode matches score
    expected_mode = BMSMode.from_score(bms_score)
    if mode != expected_mode.value:
        errors.append(
            f"Mode {mode} doesn't match score {bms_score}. "
            f"Expected {expected_mode.value}."
        )

    # Validate rationale is not generic
    if not rationale or len(rationale) < 10:
        errors.append("Rationale too short or empty.")

    generic_phrases = [
        "this is a workflow",
        "standard process",
        "typical approach",
        "best practice",
        "industry standard",
    ]
    rationale_lower = rationale.lower()
    for phrase in generic_phrases:
        if phrase in rationale_lower:
            errors.append(f"Rationale contains generic phrase: '{phrase}'")
            break

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "workflow_id": workflow_id,
    }


# ─────────────────────────────────────────────
# Build Card ID Generator
# ─────────────────────────────────────────────

def generate_build_card_id(
    level: Level,
    diamond: Diamond,
    bms_mode: BMSMode,
    step: IQRSQPIStep,
) -> str:
    """Generate a build card ID from its components."""
    return f"{level.value}-{diamond.value}-{bms_mode.value}-{step.value}"

def generate_all_cell_ids() -> list[str]:
    """Generate all 588 process-expanded cell IDs."""
    cells = []
    for level in Level:
        for diamond in Diamond:
            for mode in BMSMode:
                for step in IQRSQPIStep.sequence():
                    cells.append(f"{level.value}-{diamond.value}-{mode.value}-{step.value}")
    return cells

def generate_primary_coordinates() -> list[str]:
    """Generate all 84 primary coordinates (without IQRSQPI steps)."""
    coords = []
    for level in Level:
        for diamond in Diamond:
            for mode in BMSMode:
                coords.append(f"{level.value}-{diamond.value}-{mode.value}")
    return coords