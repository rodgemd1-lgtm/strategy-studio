"""
Archetype resolver: maps BMS mode + IQRSQPI step -> archetype file.
28 reusable archetypes = 4 BMS modes × 7 IQRSQPI steps.
"""
from __future__ import annotations

import os
from pathlib import Path

from strategy_studio.lattice._types_reexport import BMSMode, IQRSQPIStep

# ── Mode prefix mapping ──────────────────────────────────────────────────────

MODE_DIR: dict[str, str] = {
    "A1": "a1_python_only",
    "A2": "a2_hybrid",
    "A3": "a3_agent_bounded",
    "A4": "a4_llm_agent_free",
}

MODE_PREFIX: dict[str, str] = {
    "A1": "a1",
    "A2": "a2",
    "A3": "a3",
    "A4": "a4",
}

STEP_NUMBER: dict[str, str] = {
    "I1": "1",
    "Q1": "2",
    "R": "3",
    "S": "4",
    "Q2": "5",
    "P": "6",
    "I2": "7",
}

STEP_NAME: dict[str, str] = {
    "I1": "intent",
    "Q1": "question",
    "R": "research",
    "S": "solution",
    "Q2": "quality",
    "P": "proof",
    "I2": "integrate",
}

ARCHETYPES_DIR = Path(__file__).resolve().parent.parent / "archetypes"


def resolve_archetype(mode: str, step: str) -> str:
    """
    Resolve BMS mode + IQRSQPI step to archetype cell ID.
    E.g., resolve_archetype("A1", "I1") -> "A1.1"
    """
    mode_number = mode.replace("A", "")  # "A1" -> "1"
    step_num = STEP_NUMBER.get(step, "0")
    return f"A{mode_number}.{step_num}"


def resolve_file(mode: str, step: str) -> Path:
    """
    Resolve BMS mode + IQRSQPI step to file path.
    E.g., resolve_file("A1", "I1") -> rig/archetypes/a1_python_only/a1_1_intent.py
    """
    mode_dir = MODE_DIR.get(mode, "a1_python_only")
    prefix = MODE_PREFIX.get(mode, "a1")
    step_num = STEP_NUMBER.get(step, "0")
    step_name = STEP_NAME.get(step, "unknown")
    filename = f"{prefix}_{step_num}_{step_name}.py"
    return ARCHETYPES_DIR / mode_dir / filename


def resolve_cell_id(mode: str, step: str) -> str:
    """Get the cell ID string: A1.1 through A4.7."""
    return resolve_archetype(mode, step)


def get_all_cell_ids() -> list[str]:
    """Return all 28 cell IDs: A1.1-A1.7, A2.1-A2.7, A3.1-A3.7, A4.1-A4.7."""
    cells = []
    for mode in ["A1", "A2", "A3", "A4"]:
        for step in ["I1", "Q1", "R", "S", "Q2", "P", "I2"]:
            cells.append(resolve_archetype(mode, step))
    return cells


def check_all_files_exist() -> dict[str, bool]:
    """Check which archetype files exist on disk."""
    results = {}
    for mode in ["A1", "A2", "A3", "A4"]:
        for step in ["I1", "Q1", "R", "S", "Q2", "P", "I2"]:
            cell_id = resolve_archetype(mode, step)
            file_path = resolve_file(mode, step)
            results[cell_id] = file_path.exists()
    return results


if __name__ == "__main__":
    print("All 28 archetype cell IDs:")
    for cell_id in get_all_cell_ids():
        print(f"  {cell_id}")

    print("\nFile existence check:")
    for cell_id, exists in check_all_files_exist().items():
        status = "OK" if exists else "MISSING"
        print(f"  {status}: {cell_id}")
