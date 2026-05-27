#!/usr/bin/env python3
"""
Build Card Generator — generates all 147 Build Cards for the RIG lattice.

Lattice: 7 altitudes (L1-L7) × 3 diamonds (D1-D3) × 7 steps (I1-I2) = 147 cells.
For each cell: compute BMS → resolve archetype → create BuildCard → persist as YAML.

Output:
  - 147 YAML files under phronema/cards/
  - phronema/cards_index.json manifest
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml

# Ensure rig is on path
_rig_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_rig_root.parent))

from strategy_studio.lattice._types_reexport import (
    Level,
    Diamond,
    BMSMode,
    IQRSQPIStep,
    LatticeCoordinate,
)
from strategy_studio.hermes.bms import calculate_bms, BMSResult
from strategy_studio.resolve_archetype import resolve_archetype, resolve_file

# ── Paths ─────────────────────────────────────────────────────────────────────
CARDS_DIR = Path(__file__).resolve().parent / "cards"
INDEX_PATH = Path(__file__).resolve().parent / "cards_index.json"
BASELINE_PATH = Path(__file__).resolve().parent / "bms_baseline.json"


# ── Build Card model (simplified, per spec) ───────────────────────────────────

@dataclass
class BuildCard:
    """One of 147 Build Cards for a specific lattice cell."""
    cell_id: str
    altitude: str
    diamond: str
    step: str
    archetype: str
    bms_score: float
    bms_mode: str
    generated_at: str
    artifact_path: str
    proof_hash: str


# ── Default BMS parameters per diamond ────────────────────────────────────────
# D1 (Physical):  high reversibility, low failure cost → highest confidence
# D2 (Cognitive): moderate
# D3 (Nature):    low reversibility, high failure cost → lowest confidence

DIAMOND_BMS_DEFAULTS = {
    Diamond.D1: {"c1_failure_cost": 0.30, "c2_reversibility": 0.80, "c10_mechanism_clarity": 0.70},
    Diamond.D2: {"c1_failure_cost": 0.50, "c2_reversibility": 0.60, "c10_mechanism_clarity": 0.55},
    Diamond.D3: {"c1_failure_cost": 0.70, "c2_reversibility": 0.35, "c10_mechanism_clarity": 0.40},
}

# ── Cell title templates ──────────────────────────────────────────────────────

STEP_TITLES = {
    IQRSQPIStep.I1: "Intent Definition",
    IQRSQPIStep.Q1: "Question Framing",
    IQRSQPIStep.R:  "Research Execution",
    IQRSQPIStep.S:  "Solution Design",
    IQRSQPIStep.Q2: "Quality Assessment",
    IQRSQPIStep.P:  "Proof Generation",
    IQRSQPIStep.I2: "Integration & Delivery",
}

DIAMOND_NAMES = {
    Diamond.D1: "Physical",
    Diamond.D2: "Cognitive",
    Diamond.D3: "Nature",
}


def _make_title(level: Level, diamond: Diamond, step: IQRSQPIStep) -> str:
    """Generate a human-readable title for a cell."""
    return (
        f"{level.value} {DIAMOND_NAMES[diamond]} — {STEP_TITLES[step]} "
        f"({level.description.split(',')[0].strip()})"
    )


def _make_acceptance_criteria(level: Level, diamond: Diamond, step: IQRSQPIStep) -> list[str]:
    """Generate acceptance criteria for a cell."""
    criteria = [
        f"Cell {level.value}-{diamond.value}-{step.value} passes all deterministic gates",
        f"Output artifact matches {diamond.value} diamond quality standards",
        f"BMS confidence score computed and within expected band for {level.value}",
    ]
    if level in (Level.L4, Level.L5, Level.L6, Level.L7):
        criteria.append(f"Agent checkpoints verified for altitude {level.value}")
    if diamond == Diamond.D3:
        criteria.append("Adaptive/emergent behavior guardrails active")
    return criteria


def generate_all_cards(
    base_path: Optional[Path] = None,
    write_yaml: bool = True,
    write_index: bool = True,
) -> tuple[list[BuildCard], dict]:
    """
    Generate Build Cards for all 147 cells.

    Args:
        base_path: Where to write cards and index.
        write_yaml: Whether to persist YAML files.
        write_index: Whether to write cards_index.json.

    Returns:
        (list of BuildCard objects, index dict)
    """
    if base_path is None:
        base_path = CARDS_DIR

    all_levels = list(Level)
    all_diamonds = list(Diamond)
    all_steps = IQRSQPIStep.sequence()
    cards: list[BuildCard] = []
    card_entries: list[dict] = []
    baseline_entries: dict[str, dict] = {}

    for level in all_levels:
        for diamond in all_diamonds:
            params = DIAMOND_BMS_DEFAULTS[diamond]
            for step in all_steps:
                # ── Compute BMS ──────────────────────────────────────────────
                bms_result: BMSResult = calculate_bms(
                    c1_failure_cost=params["c1_failure_cost"],
                    c2_reversibility=params["c2_reversibility"],
                    c10_mechanism_clarity=params["c10_mechanism_clarity"],
                    altitude=level,
                )

                # ── Resolve archetype ────────────────────────────────────────
                archetype = resolve_archetype(bms_result.mode.value, step.value)
                file_path = resolve_file(bms_result.mode.value, step.value)

                # ── Build cell_id: L1-D1-I1 format ───────────────────────────
                cell_id = f"{level.value}-{diamond.value}-{step.value}"

                # ── Compute proof hash ───────────────────────────────────────
                proof_payload = json.dumps({
                    "cell_id": cell_id,
                    "bms_score": bms_result.adjusted_score,
                    "bms_mode": bms_result.mode.value,
                    "archetype": archetype,
                }, sort_keys=True)
                proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()[:16]

                # ── Create BuildCard ─────────────────────────────────────────
                card = BuildCard(
                    cell_id=cell_id,
                    altitude=level.value,
                    diamond=diamond.value,
                    step=step.value,
                    archetype=archetype,
                    bms_score=bms_result.adjusted_score,
                    bms_mode=bms_result.mode.value,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    artifact_path=str(file_path.relative_to(_rig_root.parent)),
                    proof_hash=proof_hash,
                )
                cards.append(card)

                # ── Card entry for index ─────────────────────────────────────
                card_entries.append({
                    "cell_id": card.cell_id,
                    "altitude": card.altitude,
                    "diamond": card.diamond,
                    "step": card.step,
                    "archetype": card.archetype,
                    "bms_score": card.bms_score,
                    "bms_mode": card.bms_mode,
                    "file": f"{card.cell_id}.yaml",
                })

                # ── Baseline entry ───────────────────────────────────────────
                baseline_entries[cell_id] = {
                    "bms_score": card.bms_score,
                    "bms_mode": card.bms_mode,
                    "archetype": card.archetype,
                    "computed_at": card.generated_at,
                }

                # ── Write YAML ───────────────────────────────────────────────
                if write_yaml:
                    yaml_data = {
                        "cell_id": card.cell_id,
                        "title": _make_title(level, diamond, step),
                        "altitude": card.altitude,
                        "diamond": card.diamond,
                        "step": card.step,
                        "archetype": card.archetype,
                        "bms_score": card.bms_score,
                        "bms_mode": card.bms_mode,
                        "generated_at": card.generated_at,
                        "artifact_path": card.artifact_path,
                        "proof_hash": card.proof_hash,
                        "acceptance_criteria": _make_acceptance_criteria(level, diamond, step),
                        "estimated_loc": 150,
                        "status": "pending",
                        "bms_inputs": {
                            "c1_failure_cost": params["c1_failure_cost"],
                            "c2_reversibility": params["c2_reversibility"],
                            "c10_mechanism_clarity": params["c10_mechanism_clarity"],
                        },
                        "bms_rationale": bms_result.rationale,
                    }
                    card_path = base_path / f"{card.cell_id}.yaml"
                    card_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(card_path, "w") as f:
                        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False,
                                  width=120, allow_unicode=True)

    # ── Write index ───────────────────────────────────────────────────────────
    index = {
        "total_cells": len(cards),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lattice_version": "2.0",
        "cell_id_format": "L<level>-D<diamond>-<step>",
        "cards": card_entries,
    }

    if write_index:
        with open(INDEX_PATH, "w") as f:
            json.dump(index, f, indent=2)

    # ── Write BMS baseline ───────────────────────────────────────────────────
    with open(BASELINE_PATH, "w") as f:
        json.dump({
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cells": baseline_entries,
        }, f, indent=2)

    return cards, index


def summarize_by_mode(cards: list[BuildCard]) -> dict[str, int]:
    """Count cards per BMS mode."""
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.bms_mode] = counts.get(card.bms_mode, 0) + 1
    return counts


def summarize_by_diamond(cards: list[BuildCard]) -> dict[str, dict[str, int]]:
    """Count cards per diamond per mode."""
    from collections import defaultdict
    summary: dict[str, dict[str, int]] = {}
    for card in cards:
        if card.diamond not in summary:
            summary[card.diamond] = defaultdict(int)
        summary[card.diamond][card.bms_mode] += 1
    return {k: dict(v) for k, v in summary.items()}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate all 147 Build Cards")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate cards without writing files")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary statistics")
    args = parser.parse_args()

    write = not args.dry_run
    cards, index = generate_all_cards(write_yaml=write, write_index=write)

    print(f"Generated {len(cards)} Build Cards")
    print()

    if args.summary or args.dry_run:
        print("── By BMS Mode ──")
        for mode, count in sorted(summarize_by_mode(cards).items()):
            print(f"  {mode}: {count} cards")

        print()
        print("── By Diamond ──")
        for diamond, mode_counts in sorted(summarize_by_diamond(cards).items()):
            print(f"  {diamond}: {sum(mode_counts.values())} cards — "
                  + ", ".join(f"{m}={c}" for m, c in sorted(mode_counts.items())))

    if not args.dry_run:
        print(f"\nCards written to: {CARDS_DIR}")
        print(f"Index written to: {INDEX_PATH}")
        print(f"Baseline written to: {BASELINE_PATH}")


if __name__ == "__main__":
    main()
