#!/usr/bin/env python3
"""
Drift Tracker — tracks Build Card drift over time.

Compares current BMS scores against historical baselines.
Flags cells where BMS has shifted beyond threshold.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_rig_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_rig_root.parent))

from strategy_studio.phronema.build_card_generator import (
    generate_all_cards,
    DIAMOND_BMS_DEFAULTS,
    BuildCard,
)

BASELINE_PATH = Path(__file__).resolve().parent / "bms_baseline.json"


# ── Drift detection ───────────────────────────────────────────────────────────

DEFAULT_DRIFT_THRESHOLD = 0.10  # ±10% change triggers alert
DEFAULT_ESCALATION_THRESHOLD = 0.20  # ±20% triggers escalation


def load_baseline(path: Optional[Path] = None) -> dict:
    """Load the BMS baseline from disk."""
    if path is None:
        path = BASELINE_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Baseline not found at {path}. Run build_card_generator first."
        )
    with open(path, "r") as f:
        return json.load(f)


def compute_drift(
    current_cards: list[BuildCard],
    baseline: Optional[dict] = None,
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
    escalation_threshold: float = DEFAULT_ESCALATION_THRESHOLD,
) -> list[dict]:
    """
    Compare current BMS scores against baseline.

    Returns list of drift records for cells exceeding threshold.
    """
    if baseline is None:
        baseline = load_baseline()

    cells = baseline.get("cells", {})
    drift_records: list[dict] = []

    for card in current_cards:
        cell_id = card.cell_id
        baseline_entry = cells.get(cell_id)
        if baseline_entry is None:
            # New cell — no baseline to compare
            drift_records.append({
                "cell_id": cell_id,
                "type": "new_cell",
                "current_score": card.bms_score,
                "baseline_score": None,
                "delta": None,
                "threshold": threshold,
                "escalate": False,
                "message": f"New cell {cell_id} has no baseline",
            })
            continue

        baseline_score = baseline_entry["bms_score"]
        delta = card.bms_score - baseline_score
        abs_delta = abs(delta)

        if abs_delta > escalation_threshold:
            severity = "critical"
            escalate = True
        elif abs_delta > threshold:
            severity = "warning"
            escalate = False
        else:
            continue  # No significant drift

        # Check for mode change
        mode_change = card.bms_mode != baseline_entry.get("bms_mode")
        if mode_change:
            severity = "critical"
            escalate = True

        drift_records.append({
            "cell_id": cell_id,
            "type": "drift",
            "current_score": card.bms_score,
            "baseline_score": baseline_score,
            "delta": round(delta, 4),
            "threshold": threshold,
            "severity": severity,
            "escalate": escalate,
            "mode_change": mode_change,
            "current_mode": card.bms_mode,
            "baseline_mode": baseline_entry.get("bms_mode"),
            "message": (
                f"Cell {cell_id}: BMS drifted from {baseline_score:.4f} "
                f"to {card.bms_score:.4f} (Δ={delta:+.4f})"
                + (f" — MODE CHANGE {baseline_entry.get('bms_mode')}→{card.bms_mode}" if mode_change else "")
            ),
        })

    return drift_records


def write_drift_report(
    drift_records: list[dict],
    path: Optional[Path] = None,
) -> Path:
    """Write drift report to JSON file."""
    if path is None:
        path = Path(__file__).resolve().parent / "drift_report.json"

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cells_checked": 147,
        "drifted_cells": len(drift_records),
        "critical": sum(1 for r in drift_records if r.get("severity") == "critical"),
        "warnings": sum(1 for r in drift_records if r.get("severity") == "warning"),
        "new_cells": sum(1 for r in drift_records if r.get("type") == "new_cell"),
        "records": drift_records,
    }

    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    return path


def check_drift(
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
    escalation_threshold: float = DEFAULT_ESCALATION_THRESHOLD,
    write_report: bool = True,
) -> dict:
    """
    Run full drift check: generate current cards, compare to baseline, report.

    Returns drift summary dict.
    """
    # Generate current cards (read-only, no file writes)
    cards, _ = generate_all_cards(write_yaml=False, write_index=False)

    # Load baseline
    baseline = load_baseline()

    # Compute drift
    records = compute_drift(
        cards, baseline,
        threshold=threshold,
        escalation_threshold=escalation_threshold,
    )

    if write_report and records:
        report_path = write_drift_report(records)
    else:
        report_path = None

    return {
        "total_cells": len(cards),
        "drifted": len(records),
        "critical": sum(1 for r in records if r.get("severity") == "critical"),
        "warnings": sum(1 for r in records if r.get("severity") == "warning"),
        "new_cells": sum(1 for r in records if r.get("type") == "new_cell"),
        "records": records,
        "report_path": str(report_path) if report_path else None,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check Build Card drift against baseline")
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD,
                        help=f"Warn threshold (default: {DEFAULT_DRIFT_THRESHOLD})")
    parser.add_argument("--escalation", type=float, default=DEFAULT_ESCALATION_THRESHOLD,
                        help=f"Escalate threshold (default: {DEFAULT_ESCALATION_THRESHOLD})")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-cell output")
    parser.add_argument("--rebuild-baseline", action="store_true",
                        help="Rebuild baseline from current state (reset drift tracking)")
    args = parser.parse_args()

    if args.rebuild_baseline:
        print("Rebuilding baseline...")
        cards, _ = generate_all_cards(write_yaml=True, write_index=True)
        print(f"Baseline rebuilt with {len(cards)} cells")
        return

    result = check_drift(
        threshold=args.threshold,
        escalation_threshold=args.escalation,
        write_report=True,
    )

    print(f"Drift Check — {len(result['records'])} cells drifted out of {result['total_cells']}")
    print(f"  Critical: {result['critical']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  New cells: {result['new_cells']}")

    if result["records"] and not args.quiet:
        print()
        for rec in result["records"]:
            prefix = "!!" if rec.get("escalate") else "  "
            print(f"  {prefix} {rec['message']}")

    if result["report_path"]:
        print(f"\nFull report: {result['report_path']}")


if __name__ == "__main__":
    main()
