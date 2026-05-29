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

from pydantic import BaseModel, Field, model_validator

# ═══════════════════════════════════════════════════════════════════════════
# Re-export unified lattice types from lattice_wire
# ═══════════════════════════════════════════════════════════════════════════
from strategy_studio.lattice_wire import (
    Altitude as WireAltitude,
    Diamond as WireDiamond,
    IQRSQPIStep as WireIQRSQPIStep,
    BuildMode as WireBMSMode,
    LatticeCell as WireLatticeCell,
    BuildMode,
    compute_bms,
    LatticeOrchestrator,
    ProofPacket as WireProofPacket,
    GateStatus,
    QualityGate,
    GateResult as WireGateResult,
    run_quality_gates,
    wire_cell_to_engine,
    get_all_588_cells,
    get_all_build_cards,
    generate_lattice_map,
    lattice_summary,
    get_cell as get_lattice_cell,
    generate_build_card,
)

class Level(int, Enum):
    """Backward-compatible altitude enum with L1..L7 members."""
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    L7 = 7

    def to_wire(self) -> WireAltitude:
        return WireAltitude(self.value)


class Diamond(str, Enum):
    """Backward-compatible diamond enum with short D1/D2/D3 members."""
    D1 = "D1"
    D2 = "D2"
    D3 = "D3"

    def to_wire(self) -> WireDiamond:
        return WireDiamond(self.value)


class BMSMode(str, Enum):
    """Backward-compatible BMS enum with short A1/A2/A3/A4 members."""
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"

    def to_wire(self) -> WireBMSMode:
        return WireBMSMode(self.value)


class IQRSQPIStep(str, Enum):
    """Backward-compatible IQRSQPI enum with short step members."""
    I1 = "I1"
    Q1 = "Q1"
    R = "R"
    S = "S"
    Q2 = "Q2"
    P = "P"
    I2 = "I2"

    @property
    def step_name(self) -> str:
        return {
            "I1": "intent", "Q1": "question", "R": "research",
            "S": "solution", "Q2": "quality", "P": "proof", "I2": "integrate",
        }[self.value]

    def to_wire(self) -> WireIQRSQPIStep:
        return WireIQRSQPIStep(self.value)


class LatticeCoordinate:
    """Backward-compatible full lattice coordinate.

    The newer `lattice_wire.LatticeCell` keeps 147-cell and 588-cell IDs
    separate. Older Archon callers expect `cell_id` to be the full 588-cell ID.
    This wrapper preserves that API and converts to the wire type at runtime.
    """

    def __init__(self, level: Level, diamond: Diamond, mode: BMSMode, step: IQRSQPIStep):
        self.level = level
        self.diamond = diamond
        self.mode = mode
        self.step = step

    @property
    def altitude(self) -> WireAltitude:
        return self.level.to_wire()

    @property
    def cell_id(self) -> str:
        return f"L{self.level.value}-{self.diamond.value}-{self.mode.value}-{self.step.value}"

    @property
    def full_cell_id(self) -> str:
        return self.cell_id

    @property
    def archetype_id(self) -> str:
        return f"{self.mode.value}.{list(IQRSQPIStep).index(self.step) + 1}"

    @property
    def altitude_penalty(self) -> float:
        return {
            Level.L1: 0.0,
            Level.L2: 0.0,
            Level.L3: 0.0,
            Level.L4: -0.05,
            Level.L5: -0.10,
            Level.L6: -0.15,
            Level.L7: -0.20,
        }[self.level]

    def to_wire(self) -> WireLatticeCell:
        return WireLatticeCell(
            altitude=self.level.to_wire(),
            diamond=self.diamond.to_wire(),
            mode=self.mode.to_wire(),
            step=self.step.to_wire(),
        )

    def __str__(self) -> str:
        return self.cell_id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LatticeCoordinate) and self.cell_id == other.cell_id

    @classmethod
    def parse(cls, cell_id: str) -> "LatticeCoordinate":
        import re

        match = re.match(r"^L([1-7])-D([1-3])-A([1-4])-(I[12]|Q[12]|[RSP])$", cell_id)
        if not match:
            raise ValueError(f"Invalid cell ID: {cell_id}")

        return cls(
            level=Level(int(match.group(1))),
            diamond=Diamond(f"D{match.group(2)}"),
            mode=BMSMode(f"A{match.group(3)}"),
            step=IQRSQPIStep(match.group(4)),
        )


class GateResult(BaseModel):
    cell_id: str = ""
    step: str
    mode: str
    gates: list[QualityGate] = Field(default_factory=list)
    overall: GateStatus = GateStatus.UNKNOWN
    duration_ms: int = 0

    @model_validator(mode="before")
    @classmethod
    def normalize_coordinate(cls, values: Any) -> Any:
        if isinstance(values, dict) and "coordinate" in values and "cell_id" not in values:
            values = dict(values)
            values["cell_id"] = values.pop("coordinate")
        return values

    @property
    def passed(self) -> bool:
        return self.overall in (GateStatus.PASS, GateStatus.SKIPPED)


class ProofPacket(BaseModel):
    packet_id: str = Field(
        default_factory=lambda: hashlib.md5(
            str(datetime.now(timezone.utc).timestamp()).encode()
        ).hexdigest()[:12]
    )
    cell_id: str = ""
    full_cell_id: str = ""
    archetype_id: str = ""
    mode: str = ""
    step: str = ""
    input_hash: str = ""
    output_hash: str = ""
    evidence_sources: list[str] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    duration_ms: int = 0
    status: str = "unknown"
    escalation_required: bool = False
    escalation_reason: str = ""
    escalation_from: str = ""
    process: str = ""
    gate_results: list[GateResult] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def normalize_coordinate(cls, values: Any) -> Any:
        if isinstance(values, dict) and "coordinate" in values:
            values = dict(values)
            coordinate = values.pop("coordinate")
            try:
                parsed = LatticeCoordinate.parse(coordinate)
                values.setdefault("cell_id", parsed.cell_id)
                values.setdefault("full_cell_id", parsed.full_cell_id)
                values.setdefault("archetype_id", parsed.archetype_id)
                values.setdefault("mode", parsed.mode.value)
                values.setdefault("step", parsed.step.step_name)
            except ValueError:
                values.setdefault("cell_id", coordinate)
                values.setdefault("full_cell_id", coordinate)
        return values

    @property
    def all_gates_passed(self) -> bool:
        return all(g.passed for g in self.gate_results)

    def to_audit_log(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "cell_id": self.cell_id,
            "coordinate": self.full_cell_id or self.cell_id,
            "full_cell_id": self.full_cell_id,
            "archetype_id": self.archetype_id,
            "mode": self.mode,
            "step": self.step,
            "status": self.status,
            "process": self.process,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "escalation_required": self.escalation_required,
            "escalation_reason": self.escalation_reason,
            "evidence_count": len(self.evidence_sources),
            "timestamp": self.timestamp.isoformat(),
        }


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

    def __init__(self, coordinate: LatticeCoordinate, process: ProcessType):
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
        wire_coordinate = self.coordinate.to_wire()
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline(
            input_data=input_data,
            altitude=wire_coordinate.altitude,
            diamond=wire_coordinate.diamond,
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
    level: Level = Level.L2,
    diamond: Diamond = Diamond.D1,
    mode: BMSMode = BMSMode.A1,
    step: IQRSQPIStep = IQRSQPIStep.S,
) -> ProofPacket:
    """Run a process through an Archon harness."""
    coord = LatticeCoordinate(level=level, diamond=diamond, mode=mode, step=step)
    harness = ArchonHarness(coordinate=coord, process=process)
    return harness.execute(input_data)


def get_all_cell_ids() -> list[str]:
    """Return all 588 cell ID strings."""
    return [c.full_cell_id for c in get_all_588_cells()]


def validate_cell_id(cell_id: str) -> bool:
    """Validate a cell ID string (supports both 147 and 588 formats)."""
    try:
        LatticeCoordinate.parse(cell_id)
        return True
    except ValueError:
        return False
