"""
RIG Strategy Studio — Archon Harness System

Every process runs through an Archon harness that:
1. Validates inputs against the RIG lattice (L-D-A-step coordinates)
2. Routes to the correct archetype (A1/A2/A3/A4)
3. Enforces quality gates at each step
4. Produces auditable ProofPackets
5. Tracks calibration and learning

Coordinate formula: Level × Diamond × BMS Mode × IQRSQPI Step
  7 levels × 3 diamonds × 4 modes × 7 steps = 588 execution cells
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class IQRSQPIStep(str, Enum):
    """The 7 IQRSQPI steps that run inside each lattice coordinate."""
    I1 = "intent"
    Q1 = "question"
    R = "research"
    S = "solution"
    Q2 = "quality"
    P = "proof"
    I2 = "integrate"


class BMSMode(str, Enum):
    """Z-axis: Build Mode Selection confidence levels."""
    A1 = "A1"  # Pure deterministic (Python only)
    A2 = "A2"  # Hybrid (deterministic + LLM fallback)
    A3 = "A3"  # Agent-bounded (multi-agent parallel)
    A4 = "A4"  # LLM-free (strictest deterministic)


class Diamond(str, Enum):
    """Y-axis: Domain classification."""
    D1 = "D1"  # Strategy synthesis
    D2 = "D2"  # Intelligence & research
    D3 = "D3"  # Operations & execution


class Level(int, Enum):
    """X-axis: Complexity/altitude levels."""
    L1 = 1  # Direct, deterministic, repeatable
    L2 = 2  # Structured but parameterized
    L3 = 3  # Workflow with branches
    L4 = 4  # Bounded agentic with checkpoints
    L5 = 5  # Mechanism + tradeoff reasoning
    L6 = 6  # Strategic synthesis required
    L7 = 7  # Doctrine, exploration, novel frame


class GateStatus(str, Enum):
    """Quality gate outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


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


# ── Lattice Coordinate ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class LatticeCoordinate:
    """Full RIG lattice coordinate: L-D-A-Step."""
    level: Level
    diamond: Diamond
    mode: BMSMode
    step: IQRSQPIStep

    def __str__(self) -> str:
        return f"L{self.level.value}-{self.diamond.value}-{self.mode.value}-{self.step.name}"

    @property
    def cell_id(self) -> str:
        return str(self)

    @property
    def altitude_penalty(self) -> float:
        """BMS altitude adjustment per level."""
        return {
            Level.L1: 0.0, Level.L2: 0.0, Level.L3: 0.0,
            Level.L4: -0.05, Level.L5: -0.10, Level.L6: -0.15, Level.L7: -0.20,
        }[self.level]

    @classmethod
    def parse(cls, cell_id: str) -> "LatticeCoordinate":
        """Parse a cell ID string like 'L2-D1-A1-I1'."""
        import re
        pattern = r"^L(\d+)-(D\d+)-(A\d+)-(I[12]|Q[12]|[RSP])$"
        m = re.match(pattern, cell_id)
        if not m:
            raise ValueError(f"Invalid cell ID: {cell_id}. Expected format: L<level>-D<diamond>-A<mode>-<step>")

        # Map step shortcuts to enum
        step_map = {
            "I1": IQRSQPIStep.I1, "Q1": IQRSQPIStep.Q1, "R": IQRSQPIStep.R,
            "S": IQRSQPIStep.S, "Q2": IQRSQPIStep.Q2, "P": IQRSQPIStep.P, "I2": IQRSQPIStep.I2,
        }
        step_str = m.group(4)
        step = step_map.get(step_str)
        if not step:
            raise ValueError(f"Invalid step: {step_str}")

        return cls(
            level=Level(int(m.group(1))),
            diamond=Diamond(m.group(2)),
            mode=BMSMode(m.group(3)),
            step=step,
        )


# ── Quality Gate ────────────────────────────────────────────────────────────

class QualityGate(BaseModel):
    """A single quality gate check."""
    name: str
    status: GateStatus
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GateResult(BaseModel):
    """Result of running all quality gates for a step."""
    coordinate: str
    step: str
    mode: str
    gates: list[QualityGate] = Field(default_factory=list)
    overall: GateStatus = GateStatus.UNKNOWN
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed(self) -> bool:
        return self.overall in (GateStatus.PASS, GateStatus.SKIPPED)

    @property
    def failed_gates(self) -> list[QualityGate]:
        return [g for g in self.gates if g.status == GateStatus.FAIL]


# ── Proof Packet ────────────────────────────────────────────────────────────

class ProofPacket(BaseModel):
    """Auditable proof packet for every process execution."""
    packet_id: str = Field(default_factory=lambda: hashlib.md5(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()[:12])
    process: str
    coordinate: str
    input_hash: str = ""
    output_hash: str = ""
    evidence_sources: list[str] = Field(default_factory=list)
    gate_results: list[GateResult] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)  # file paths
    duration_ms: int = 0
    status: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def all_gates_passed(self) -> bool:
        return all(gr.passed for gr in self.gate_results)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_sources)

    def to_audit_log(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "process": self.process,
            "coordinate": self.coordinate,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "evidence_count": self.evidence_count,
            "gates_passed": self.all_gates_passed,
            "gate_summary": {gr.step: gr.overall for gr in self.gate_results},
            "artifacts": self.artifacts,
            "timestamp": self.timestamp.isoformat(),
        }


# ── Archon Harness ─────────────────────────────────────────────────────────

class ArchonHarness:
    """
    Main harness that wraps every process.
    
    Execution flow:
    1. Validate input against lattice coordinate
    2. Route to correct archetype based on BMS mode
    3. Execute the step (I1→Q1→R→S→Q2→P→I2)
    4. Run quality gates
    5. Produce ProofPacket
    6. Track calibration
    """

    def __init__(self, coordinate: LatticeCoordinate, process: ProcessType):
        self.coordinate = coordinate
        self.process = process
        self.gate_results: list[GateResult] = []
        self.proof_packet: Optional[ProofPacket] = None
        self._start_time: float = 0

    def execute(self, input_data: dict[str, Any]) -> ProofPacket:
        """Execute the full harness pipeline."""
        self._start_time = time.time()

        # Step 1: Validate
        validation = self._validate_input(input_data)
        if not validation.passed:
            return self._make_proof_packet(
                status="VALIDATION_FAILED",
                input_data=input_data,
            )

        # Step 2: Route to archetype
        archetype_fn = self._route_archetype()

        # Step 3: Execute
        try:
            result = archetype_fn(input_data)
        except Exception as e:
            return self._make_proof_packet(
                status=f"EXECUTION_ERROR: {e}",
                input_data=input_data,
            )

        # Step 4: Run quality gates
        gate_result = self._run_gates(result)
        self.gate_results.append(gate_result)

        # Step 5: Build ProofPacket
        self.proof_packet = self._make_proof_packet(
            status=gate_result.overall,
            input_data=input_data,
            result=result,
        )

        return self.proof_packet

    def _validate_input(self, input_data: dict[str, Any]) -> GateResult:
        """Validate input data against the lattice coordinate."""
        gates = []
        t0 = time.time()

        # Gate: Input is not empty
        has_input = bool(input_data)
        gates.append(QualityGate(
            name="input_present",
            status=GateStatus.PASS if has_input else GateStatus.FAIL,
            message="Input data present" if has_input else "No input data provided",
        ))

        # Gate: Required fields present
        required = self._get_required_fields()
        missing = [f for f in required if f not in input_data]
        gates.append(QualityGate(
            name="required_fields",
            status=GateStatus.PASS if not missing else GateStatus.FAIL,
            message=f"Required fields: {', '.join(required)}" if missing else "All required fields present",
            details={"missing": missing, "required": required},
        ))

        # Gate: Coordinate is valid
        try:
            LatticeCoordinate.parse(str(self.coordinate))
            gates.append(QualityGate(
                name="coordinate_valid",
                status=GateStatus.PASS,
                message=f"Coordinate {self.coordinate} is valid",
            ))
        except ValueError as e:
            gates.append(QualityGate(
                name="coordinate_valid",
                status=GateStatus.FAIL,
                message=str(e),
            ))

        overall = GateStatus.PASS if all(g.status == GateStatus.PASS for g in gates) else GateStatus.FAIL

        return GateResult(
            coordinate=str(self.coordinate),
            step=self.coordinate.step.value,
            mode=self.coordinate.mode.value,
            gates=gates,
            overall=overall,
            duration_ms=int((time.time() - t0) * 1000),
        )

    def _route_archetype(self):
        """Route to the correct archetype function based on BMS mode."""
        mode = self.coordinate.mode
        step = self.coordinate.step

        # Import the correct archetype module
        archetype_map = {
            BMSMode.A1: "strategy_studio.archetypes.a1",
            BMSMode.A2: "strategy_studio.archetypes.a2",
            BMSMode.A3: "strategy_studio.archetypes.a3",
            BMSMode.A4: "strategy_studio.archetypes.a4",
        }

        module_path = archetype_map.get(mode, "strategy_studio.archetypes.a1")

        # Map step to function
        step_fn_map = {
            IQRSQPIStep.I1: "classify_intent",
            IQRSQPIStep.Q1: "generate_questions",
            IQRSQPIStep.R: "execute_research",
            IQRSQPIStep.S: "synthesize",
            IQRSQPIStep.Q2: "validate_quality",
            IQRSQPIStep.P: "build_proof",
            IQRSQPIStep.I2: "integrate",
        }

        # For now, return a generic executor
        # In production, this dynamically imports the correct module/function
        return self._generic_execute

    def _generic_execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generic executor that dispatches to the correct archetype."""
        mode = self.coordinate.mode

        try:
            if mode == BMSMode.A1:
                from strategy_studio.archetypes import run_a1
                from strategy_studio.core.types import InboundPayload
                payload = InboundPayload(raw_text=input_data.get("query", str(input_data)))
                result = run_a1(payload)
                return {"status": result.status, "archetype": result.archetype, "mode": result.mode}

            elif mode == BMSMode.A2:
                from strategy_studio.archetypes import run_a2
                from strategy_studio.core.types import InboundPayload
                payload = InboundPayload(raw_text=input_data.get("query", str(input_data)))
                result = run_a2(payload)
                return {"status": result.status, "archetype": result.archetype, "mode": result.mode}

            elif mode == BMSMode.A3:
                from strategy_studio.archetypes import run_a3
                from strategy_studio.core.types import InboundPayload
                payload = InboundPayload(raw_text=input_data.get("query", str(input_data)))
                result = run_a3(payload)
                return {"status": result.status, "archetype": result.archetype, "mode": result.mode}

            elif mode == BMSMode.A4:
                from strategy_studio.archetypes import run_a4
                from strategy_studio.core.types import InboundPayload
                payload = InboundPayload(raw_text=input_data.get("query", str(input_data)))
                result = run_a4(payload)
                return {"status": result.status, "archetype": result.archetype, "mode": result.mode}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

        return {"status": "UNKNOWN"}

    def _run_gates(self, result: dict[str, Any]) -> GateResult:
        """Run quality gates on the execution result."""
        gates = []
        t0 = time.time()

        # Gate: Execution completed
        status = result.get("status", "UNKNOWN")
        is_complete = status in ("PASS", "completed")
        gates.append(QualityGate(
            name="execution_complete",
            status=GateStatus.PASS if is_complete else GateStatus.FAIL,
            message=f"Execution status: {status}",
        ))

        # Gate: No errors
        has_error = "error" in result
        gates.append(QualityGate(
            name="no_errors",
            status=GateStatus.FAIL if has_error else GateStatus.PASS,
            message=result.get("error", "No errors"),
        ))

        # Gate: Archetype matches mode
        expected_archetype = self.coordinate.mode.value.lower().replace("4", "4").replace("3", "3")
        actual_archetype = result.get("archetype", "")
        archetype_match = expected_archetype in actual_archetype.lower() or actual_archetype.lower() in expected_archetype
        gates.append(QualityGate(
            name="archetype_match",
            status=GateStatus.PASS if archetype_match else GateStatus.WARN,
            message=f"Expected: {expected_archetype}, Got: {actual_archetype}",
        ))

        # Gate: Evidence present (if applicable)
        if "evidence" in result:
            has_evidence = len(result["evidence"]) > 0
            gates.append(QualityGate(
                name="evidence_present",
                status=GateStatus.PASS if has_evidence else GateStatus.WARN,
                message=f"{len(result['evidence'])} evidence items" if has_evidence else "No evidence",
            ))

        overall = GateStatus.PASS
        if any(g.status == GateStatus.FAIL for g in gates):
            overall = GateStatus.FAIL
        elif any(g.status == GateStatus.WARN for g in gates):
            overall = GateStatus.WARN

        return GateResult(
            coordinate=str(self.coordinate),
            step=self.coordinate.step.value,
            mode=self.coordinate.mode.value,
            gates=gates,
            overall=overall,
            duration_ms=int((time.time() - t0) * 1000),
        )

    def _make_proof_packet(
        self,
        status: str,
        input_data: dict[str, Any],
        result: dict[str, Any] | None = None,
    ) -> ProofPacket:
        """Build the ProofPacket for this execution."""
        input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        output_hash = hashlib.md5(json.dumps(result or {}, sort_keys=True, default=str).encode()).hexdigest()[:16]

        return ProofPacket(
            process=self.process.value,
            coordinate=str(self.coordinate),
            input_hash=input_hash,
            output_hash=output_hash,
            gate_results=self.gate_results,
            duration_ms=int((time.time() - self._start_time) * 1000) if self._start_time else 0,
            status=status,
        )

    def _get_required_fields(self) -> list[str]:
        """Get required input fields for this process."""
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


# ── Harness Registry ───────────────────────────────────────────────────────

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
        return [p for p in self.executions.values() if not p.all_gates_passed]

    def get_audit_log(self) -> list[dict[str, Any]]:
        return [p.to_audit_log() for p in self.executions.values()]

    def summary(self) -> dict[str, Any]:
        total = len(self.executions)
        passed = sum(1 for p in self.executions.values() if p.all_gates_passed)
        failed = total - passed
        return {
            "total_executions": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_process": {
                pt.value: len(self.get_by_process(pt))
                for pt in ProcessType
            },
        }


# ── Convenience Functions ──────────────────────────────────────────────────

def run_harness(
    process: ProcessType,
    input_data: dict[str, Any],
    level: Level = Level.L2,
    diamond: Diamond = Diamond.D1,
    mode: BMSMode = BMSMode.A1,
    step: IQRSQPIStep = IQRSQPIStep.S,
) -> ProofPacket:
    """Convenience function to run a process through an Archon harness."""
    coord = LatticeCoordinate(level=level, diamond=diamond, mode=mode, step=step)
    harness = ArchonHarness(coordinate=coord, process=process)
    return harness.execute(input_data)


def get_all_cell_ids() -> list[str]:
    """Return all 588 cell IDs: 7 levels × 3 diamonds × 4 modes × 7 steps."""
    cells = []
    for level in Level:
        for diamond in Diamond:
            for mode in BMSMode:
                for step in IQRSQPIStep:
                    coord = LatticeCoordinate(level=level, diamond=diamond, mode=mode, step=step)
                    cells.append(str(coord))
    return cells


def validate_cell_id(cell_id: str) -> bool:
    """Validate a cell ID string."""
    try:
        LatticeCoordinate.parse(cell_id)
        return True
    except ValueError:
        return False