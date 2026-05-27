"""
RIG Strategy Studio — Archon Harness System (v10)

Unified with lattice_wire.py — this module provides the Archon harness wrapper
that adds ProcessType routing and HarnessRegistry on top of the lattice.

Every process runs through an Archon harness:
1. Validate inputs against the RIG lattice (L-D-A-step coordinates)
2. Route to the correct archetype (A1/A2/A3/A4) via lattice_wire
3. Enforce quality gates at each step
4. Produce auditable ProofPackets
5. Track calibration and learning

Coordinate formula: Altitude × Diamond × BMS Mode × IQRSQPI Step
  7 levels × 3 diamonds × 4 modes × 7 steps = 588 execution cells
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# Re-export unified lattice types from lattice_wire
# ═══════════════════════════════════════════════════════════════════════════
from strategy_studio.lattice_wire import (
    Altitude,
    Diamond,
    IQRSQPIStep,
    BuildMode as BMSMode,
    LatticeCell,
    BuildMode,
    compute_bms,
    LatticeOrchestrator,
    ProofPacket,
    GateStatus,
    QualityGate,
    GateResult,
    run_quality_gates,
    wire_cell_to_engine,
    get_all_588_cells,
    get_all_build_cards,
    generate_lattice_map,
    lattice_summary,
    get_cell as get_lattice_cell,
    generate_build_card,
)

# Aliases for backward compatibility with old archon code
Level = Altitude
LatticeCoordinate = LatticeCell


# ═══════════════════════════════════════════════════════════════════════════
# ProcessType — extends lattice with process-level routing
# ═══════════════════════════════════════════════════════════════════════════

class ProcessType(str, Enum):
    """All processes that run through Archon harnesses."""
    ANALYZE = "analyze"
    PREDICT = "predict"
    CREATE = "create"
    DECIDE = "decide"
    EVIDENCE = "evidence"
    FORECAST = "forecast"
    CALIBRATE = "calibrate"
    SYNTHESIZE = "synthesize"
    PRESENT = "present"
    WARGAME = "wargame"
    FALSIFY = "falsify"
    NARRATIVE = "narrative"
    BATCH = "batch"
    WIZARD = "wizard"


# ═══════════════════════════════════════════════════════════════════════════
# ArchonHarness — wraps lattice orchestrator with ProcessType routing
# ═══════════════════════════════════════════════════════════════════════════

class ArchonHarness:
    """
    Main harness that wraps every process.
    Delegates to LatticeOrchestrator for lattice-aware execution.
    """

    def __init__(self, coordinate: LatticeCell, process: ProcessType):
        self.coordinate = coordinate
        self.process = process
        self.gate_results: list[GateResult] = []
        self.proof_packet: ProofPacket | None = None
        self._start_time: float = 0

    def execute(self, input_data: dict[str, Any]) -> ProofPacket:
        """Execute the full harness pipeline through the lattice."""
        self._start_time = time.time()

        # Step 1: Validate
        validation = self._validate_input(input_data)
        if not validation.passed:
            return self._make_proof_packet(status="VALIDATION_FAILED", input_data=input_data)

        # Step 2: Execute through lattice orchestrator
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline(
            input_data=input_data,
            altitude=self.coordinate.altitude,
            diamond=self.coordinate.diamond,
        )

        # Step 3: Build ProofPacket from lattice result
        self.proof_packet = self._make_proof_packet(
            status=result["summary"]["overall_status"],
            input_data=input_data,
            result=result,
        )

        return self.proof_packet

    def _validate_input(self, input_data: dict[str, Any]) -> GateResult:
        gates = []
        t0 = time.time()

        gates.append(QualityGate(
            name="input_present",
            status=GateStatus.PASS if input_data else GateStatus.FAIL,
            message="Input data present" if input_data else "No input data provided",
        ))

        required = self._get_required_fields()
        missing = [f for f in required if f not in input_data]
        gates.append(QualityGate(
            name="required_fields",
            status=GateStatus.PASS if not missing else GateStatus.FAIL,
            message=f"All required fields present" if not missing else f"Missing: {', '.join(missing)}",
            details={"missing": missing, "required": required},
        ))

        overall = GateStatus.PASS if all(g.status == GateStatus.PASS for g in gates) else GateStatus.FAIL

        return GateResult(
            cell_id=self.coordinate.cell_id,
            step=self.coordinate.step.step_name,
            mode=self.coordinate.mode.value,
            gates=gates,
            overall=overall,
            duration_ms=int((time.time() - t0) * 1000),
        )

    def _make_proof_packet(
        self, status: str, input_data: dict[str, Any], result: dict[str, Any] | None = None,
    ) -> ProofPacket:
        input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        output_hash = hashlib.md5(json.dumps(result or {}, sort_keys=True, default=str).encode()).hexdigest()[:16]

        return ProofPacket(
            process=self.process.value,
            cell_id=self.coordinate.cell_id,
            full_cell_id=self.coordinate.full_cell_id,
            archetype_id=self.coordinate.archetype_id,
            mode=self.coordinate.mode.value,
            step=self.coordinate.step.step_name,
            input_hash=input_hash,
            output_hash=output_hash,
            gate_results=self.gate_results,
            duration_ms=int((time.time() - self._start_time) * 1000) if self._start_time else 0,
            status=status,
            output=result or {},
        )

    def _get_required_fields(self) -> list[str]:
        base = ["query"]
        process_fields = {
            ProcessType.ANALYZE: ["company_name"],
            ProcessType.PREDICT: ["question"],
            ProcessType.CREATE: ["brief"],
            ProcessType.DECIDE: ["options", "criteria"],
            ProcessType.EVIDENCE: ["claim"],
            ProcessType.FORECAST: ["signals"],
            ProcessType.CALIBRATE: [],
            ProcessType.SYNTHESIZE: ["inputs"],
            ProcessType.PRESENT: ["input_file"],
            ProcessType.WARGAME: ["scenario", "actors"],
            ProcessType.FALSIFY: ["claim"],
            ProcessType.NARRATIVE: ["input_file"],
            ProcessType.BATCH: ["input_csv"],
            ProcessType.WIZARD: [],
        }
        return base + process_fields.get(self.process, [])


# ═══════════════════════════════════════════════════════════════════════════
# HarnessRegistry — tracks all harness executions
# ═══════════════════════════════════════════════════════════════════════════

class HarnessRegistry:
    """Registry of all active harness executions."""
    def __init__(self):
        self.executions: dict[str, ProofPacket] = {}

    def register(self, packet: ProofPacket) -> None:
        self.executions[packet.packet_id] = packet

    def get(self, packet_id: str) -> ProofPacket | None:
        return self.executions.get(packet_id)

    def get_by_process(self, process: ProcessType) -> list[ProofPacket]:
        return [p for p in self.executions.values() if p.process == process.value]

    def get_failed(self) -> list[ProofPacket]:
        return [p for p in self.executions.values() if p.status not in ("PASS", "completed")]

    def get_audit_log(self) -> list[dict[str, Any]]:
        return [p.to_audit_log() for p in self.executions.values()]

    def summary(self) -> dict[str, Any]:
        total = len(self.executions)
        passed = sum(1 for p in self.executions.values() if p.status in ("PASS", "completed"))
        return {
            "total_executions": total, "passed": passed, "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════

def run_harness(
    process: ProcessType,
    input_data: dict[str, Any],
    level: Altitude = Altitude.L2,
    diamond: Diamond = Diamond.D1_STRATEGY,
    mode: BMSMode = BMSMode.A1_PYTHON_ONLY,
    step: IQRSQPIStep = IQRSQPIStep.S_SOLUTION,
) -> ProofPacket:
    """Run a process through an Archon harness."""
    coord = LatticeCell(altitude=level, diamond=diamond, step=step, mode=mode)
    harness = ArchonHarness(coordinate=coord, process=process)
    return harness.execute(input_data)


def get_all_cell_ids() -> list[str]:
    """Return all 588 cell ID strings."""
    return [c.full_cell_id for c in get_all_588_cells()]


def validate_cell_id(cell_id: str) -> bool:
    """Validate a cell ID string (supports both 147 and 588 formats)."""
    try:
        LatticeCell.parse(cell_id)
        return True
    except ValueError:
        return False
