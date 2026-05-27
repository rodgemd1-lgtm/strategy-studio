"""
RIG Lattice — Brier Score Drift Monitor
Tracks cell output accuracy over time. Auto-demote/promote BMS modes.

Doctrine: If a cell consistently scores below its BMS confidence,
the mode is too permissive → demote (more human gates).
If a cell consistently scores above  → promote (less overhead).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import json
from pathlib import Path


@dataclass
class BrierCheck:
    cell_id: str
    forecast_prob: float
    actual_outcome: float
    brier_score: float = 0.0
    drift_detected: bool = False
    action: str = ""


@dataclass 
class DriftReport:
    checks: list[BrierCheck] = field(default_factory=list)
    cells_to_promote: list[str] = field(default_factory=list)
    cells_to_demote: list[str] = field(default_factory=list)
    generated_at: str = ""


def compute_brier(forecast_prob: float, actual_outcome: float) -> float:
    """Compute Brier score: BS = (p - o)²"""
    return (forecast_prob - actual_outcome) ** 2


def check_cell(cell_id: str, forecast_prob: float, actual_outcome: float,
               bms_score: float, current_mode: str) -> BrierCheck:
    """Check a single cell for Brier drift."""
    bs = compute_brier(forecast_prob, actual_outcome)
    
    # Brier score thresholds
    # < 0.05 = excellent calibration
    # 0.05-0.15 = acceptable
    # 0.15-0.25 = concerning
    # > 0.25 = poor — mode may need adjustment
    
    check = BrierCheck(
        cell_id=cell_id,
        forecast_prob=forecast_prob,
        actual_outcome=actual_outcome,
        brier_score=round(bs, 4),
    )
    
    if bs > 0.25:
        check.drift_detected = True
        
        # Decision: is the cell overconfident or underconfident?
        if forecast_prob > actual_outcome:
            # Overconfident — downgrade mode (add more gates)
            modes = ["LLM_AGENT_FREE", "AGENT_BOUNDED", "HYBRID", "PYTHON_ONLY"]
            idx = modes.index(current_mode) if current_mode in modes else 1
            new_mode = modes[min(idx + 1, 3)] if idx < 3 else "PYTHON_ONLY"
            check.action = f"DEMOTE: {current_mode} → {new_mode} (overconfident, BS={bs:.3f})"
        else:
            # Underconfident — might upgrade if BMS supports it
            modes = ["LLM_AGENT_FREE", "AGENT_BOUNDED", "HYBRID", "PYTHON_ONLY"]
            idx = modes.index(current_mode) if current_mode in modes else 1
            new_mode = modes[max(idx - 1, 0)] if idx > 0 else "LLM_AGENT_FREE"
            check.action = f"PROMOTE: {current_mode} → {new_mode} (underconfident, BS={bs:.3f})"
    
    elif bs < 0.05:
        # Excellent calibration — candidate for promotion
        if current_mode != "PYTHON_ONLY":
            modes = ["LLM_AGENT_FREE", "AGENT_BOUNDED", "HYBRID", "PYTHON_ONLY"]
            idx = modes.index(current_mode) if current_mode in modes else 1
            new_mode = modes[max(idx - 1, 0)] if idx > 0 else "LLM_AGENT_FREE"
            check.action = f"CANDIDATE_PROMOTE: {current_mode} → {new_mode} (excellent calibration, BS={bs:.3f})"
    
    return check


def monitor_lattice(cells: list[dict]) -> DriftReport:
    """Run Brier monitoring across all cells."""
    report = DriftReport(generated_at=datetime.now(timezone.utc).isoformat())
    
    for cell in cells:
        cell_id = cell.get("cell_id", "")
        forecast = cell.get("forecast_prob", 0.5)
        actual = cell.get("actual_outcome", 0.5)
        bms = cell.get("bms_score", 0.5)
        mode = cell.get("bms_mode", "HYBRID")
        
        check = check_cell(cell_id, forecast, actual, bms, mode)
        report.checks.append(check)
        
        if "PROMOTE" in check.action:
            report.cells_to_promote.append(cell_id)
        elif "DEMOTE" in check.action:
            report.cells_to_demote.append(cell_id)
    
    return report


if __name__ == "__main__":
    # Demo: simulate monitoring across sample cells
    sample_cells = [
        {"cell_id": "L1-D1-I1", "forecast_prob": 0.95, "actual_outcome": 0.92, "bms_score": 0.95, "bms_mode": "PYTHON_ONLY"},
        {"cell_id": "L3-D2-R",  "forecast_prob": 0.70, "actual_outcome": 0.30, "bms_score": 0.52, "bms_mode": "HYBRID"},
        {"cell_id": "L5-D2-S",  "forecast_prob": 0.85, "actual_outcome": 0.82, "bms_score": 0.31, "bms_mode": "AGENT_BOUNDED"},
        {"cell_id": "L7-D3-Q2", "forecast_prob": 0.60, "actual_outcome": 0.10, "bms_score": 0.18, "bms_mode": "LLM_AGENT_FREE"},
    ]
    
    report = monitor_lattice(sample_cells)
    
    print(f"BRIER DRIFT MONITOR — {report.generated_at}")
    for c in report.checks:
        flag = "⚠️ " if c.drift_detected else "✓ "
        print(f"  {flag}{c.cell_id}: BS={c.brier_score:.4f} (forecast {c.forecast_prob:.2f} vs actual {c.actual_outcome:.2f})")
        if c.action:
            print(f"    → {c.action}")
    
    if report.cells_to_promote:
        print(f"\n  PROMOTE candidates: {', '.join(report.cells_to_promote)}")
    if report.cells_to_demote:
        print(f"\n  DEMOTE candidates: {', '.join(report.cells_to_demote)}")
