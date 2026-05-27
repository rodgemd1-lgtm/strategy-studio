"""
LatticeWire — Complete RIG Lattice Execution System for Strategy Studio.

Full 588-cell lattice: 7 Altitudes × 3 Diamonds × 4 BMS Modes × 7 IQRSQPI steps
28 reusable archetypes: 4 Build Modes × 7 IQRSQPI steps
147 Build Cards: one per altitude/diamond/step (BMS mode derived from altitude)

Architecture:
  InboundPayload → LatticeOrchestrator → BMS scoring → cell routing
  → B-engine execution → ArchetypeResult → ProofPacket → audit trail

Coordinate system: L{1-7}-D{1-3}-{I1,Q1,R,S,Q2,P,I2} → A{1-4}.{1-7}
Full 588-cell: L{1-7}-D{1-3}-A{1-4}-{I1,Q1,R,S,Q2,P,I2}
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# AXIS 1: ALTITUDE (X) — 7 levels of complexity
# ═══════════════════════════════════════════════════════════════════════════

class Altitude(int, Enum):
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    L7 = 7

    @property
    def altitude_bonus(self) -> float:
        return {
            Altitude.L1: 0.35, Altitude.L2: 0.28, Altitude.L3: 0.12,
            Altitude.L4: 0.0, Altitude.L5: -0.08, Altitude.L6: -0.20,
            Altitude.L7: -0.35,
        }[self]

    @property
    def description(self) -> str:
        return {
            1: "Direct, deterministic, repeatable",
            2: "Structured but parameterized",
            3: "Workflow with branches",
            4: "Bounded agentic with checkpoints",
            5: "Mechanism + tradeoff reasoning",
            6: "Strategic synthesis required",
            7: "Doctrine, exploration, novel frame",
        }[self.value]


# ═══════════════════════════════════════════════════════════════════════════
# AXIS 2: DIAMOND (Y) — 3 domain classifications
# ═══════════════════════════════════════════════════════════════════════════

class Diamond(str, Enum):
    D1_STRATEGY = "D1"
    D2_INTELLIGENCE = "D2"
    D3_OPERATIONS = "D3"


# ═══════════════════════════════════════════════════════════════════════════
# AXIS 3: IQRSQPI STEP — 7 steps per cell
# ═══════════════════════════════════════════════════════════════════════════

class IQRSQPIStep(str, Enum):
    I1_INTENT = "I1"
    Q1_QUESTION = "Q1"
    R_RESEARCH = "R"
    S_SOLUTION = "S"
    Q2_QUALITY = "Q2"
    P_PROOF = "P"
    I2_INTEGRATE = "I2"

    @property
    def step_name(self) -> str:
        return {
            "I1": "intent", "Q1": "question", "R": "research",
            "S": "solution", "Q2": "quality", "P": "proof", "I2": "integrate",
        }[self.value]

    @property
    def description(self) -> str:
        return {
            "I1": "Classify intent and scope the problem",
            "Q1": "Generate research questions",
            "R": "Gather evidence from sources",
            "S": "Synthesize solution options",
            "Q2": "Validate quality and falsify",
            "P": "Build proof packet with sources",
            "I2": "Integrate into final recommendation",
        }[self.value]


# ═══════════════════════════════════════════════════════════════════════════
# AXIS 4: BUILD MODE (Z) — 4 confidence levels (BMS)
# ═══════════════════════════════════════════════════════════════════════════

class BuildMode(str, Enum):
    A1_PYTHON_ONLY = "A1"
    A2_HYBRID = "A2"
    A3_AGENT_BOUNDED = "A3"
    A4_LLM_AGENT_FREE = "A4"

    @property
    def cost_band(self) -> str:
        return {"A1": "<=$0.001", "A2": "<=$0.05", "A3": "<=$1", "A4": "<=$50+4h"}[self.value]

    @property
    def description(self) -> str:
        return {
            "A1": "No model in decision path. Pydantic + Jinja + regex.",
            "A2": "Python gates + small LLM shims (Haiku/Sonnet).",
            "A3": "LangGraph/CrewAI with hard tool + cost budgets.",
            "A4": "Opus + hierarchical crews, NeMo Guardrails, falsification.",
        }[self.value]


# ═══════════════════════════════════════════════════════════════════════════
# BMS SCORING
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BMSCriteria:
    failure_cost: float = 0.5
    reversibility: float = 0.5
    mechanism_clarity: float = 0.5

    @property
    def raw_score(self) -> float:
        return self.failure_cost * 0.4 + self.reversibility * 0.3 + self.mechanism_clarity * 0.3


@dataclass
class BMSScore:
    raw: float = 0.5
    adj_failure: float = 0.0
    adj_volume: float = 0.0
    adj_altitude: float = 0.0

    @property
    def final(self) -> float:
        return max(0.0, min(1.0, self.raw + self.adj_failure + self.adj_volume + self.adj_altitude))

    def select_mode(self) -> BuildMode:
        bms = self.final
        if bms >= 0.75: return BuildMode.A1_PYTHON_ONLY
        elif bms >= 0.45: return BuildMode.A2_HYBRID
        elif bms >= 0.25: return BuildMode.A3_AGENT_BOUNDED
        else: return BuildMode.A4_LLM_AGENT_FREE


def compute_bms(
    failure_cost: float = 0.5, reversibility: float = 0.5,
    mechanism_clarity: float = 0.5, past_failure_rate: float = 0.0,
    data_volume: float = 0.5, altitude: Altitude = Altitude.L2,
) -> BMSScore:
    criteria = BMSCriteria(failure_cost, reversibility, mechanism_clarity)
    return BMSScore(
        raw=criteria.raw_score,
        adj_failure=-past_failure_rate * 0.2,
        adj_volume=(data_volume - 0.5) * 0.1,
        adj_altitude=altitude.altitude_bonus,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE CELL — Full coordinate (147 cells: 7×3×7)
# For 588-cell: add mode axis → L{1-7}-D{1-3}-A{1-4}-{step}
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LatticeCell:
    altitude: Altitude
    diamond: Diamond
    step: IQRSQPIStep
    mode: BuildMode = BuildMode.A1_PYTHON_ONLY

    @property
    def cell_id(self) -> str:
        """147-cell format: L2-D1-S"""
        return f"L{self.altitude.value}-{self.diamond.value}-{self.step.value}"

    @property
    def full_cell_id(self) -> str:
        """588-cell format: L2-D1-A1-S"""
        return f"L{self.altitude.value}-{self.diamond.value}-{self.mode.value}-{self.step.value}"

    @property
    def archetype_id(self) -> str:
        return f"{self.mode.value}.{list(IQRSQPIStep).index(self.step) + 1}"

    def __str__(self) -> str:
        return f"{self.full_cell_id} -> {self.archetype_id}"

    @classmethod
    def parse(cls, cell_id: str) -> "LatticeCell":
        """Parse cell ID. Supports both 147-cell (L2-D1-S) and 588-cell (L2-D1-A1-S)."""
        import re
        # Try 588-cell format first
        m = re.match(r"^L(\d+)-(D[123])-(A\d+)-(I[12]|Q[12]|[RSP])$", cell_id)
        if m:
            return cls(
                altitude=Altitude(int(m.group(1))),
                diamond=Diamond(f"D{m.group(2)[1]}"),
                mode=BuildMode(f"A{m.group(3)[1]}"),
                step=IQRSQPIStep(m.group(4)),
            )
        # Try 147-cell format
        m = re.match(r"^L(\d+)-(D[123])-(I[12]|Q[12]|[RSP])$", cell_id)
        if m:
            return cls(
                altitude=Altitude(int(m.group(1))),
                diamond=Diamond(f"D{m.group(2)[1]}"),
                step=IQRSQPIStep(m.group(3)),
            )
        raise ValueError(f"Invalid cell ID: {cell_id}")


def get_all_cells() -> list[LatticeCell]:
    """Return all 147 cells: 7 altitudes × 3 diamonds × 7 steps."""
    cells = []
    for alt in Altitude:
        for dia in Diamond:
            for step in IQRSQPIStep:
                cells.append(LatticeCell(altitude=alt, diamond=dia, step=step))
    return cells


def get_all_588_cells() -> list[LatticeCell]:
    """Return all 588 cells: 7 × 3 × 4 × 7."""
    cells = []
    for alt in Altitude:
        for dia in Diamond:
            for mode in BuildMode:
                for step in IQRSQPIStep:
                    cells.append(LatticeCell(altitude=alt, diamond=dia, step=step, mode=mode))
    return cells


# ═══════════════════════════════════════════════════════════════════════════
# BUILD CARD
# ═══════════════════════════════════════════════════════════════════════════

class BuildCard(BaseModel):
    cell_id: str
    full_cell_id: str = ""
    altitude: int
    diamond: str
    step: str
    step_name: str
    mode: str
    archetype_id: str
    cost_band: str
    doctrine: str
    tools: list[str] = Field(default_factory=list)
    validation_criteria: list[str] = Field(default_factory=list)
    escalation_target: str = ""
    bms_score: float = 0.5
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def generate_build_card(cell: LatticeCell, bms: BMSScore) -> BuildCard:
    mode = bms.select_mode()
    step_idx = list(IQRSQPIStep).index(cell.step) + 1
    tools_map = {
        BuildMode.A1_PYTHON_ONLY: ["regex", "jinja2", "pydantic", "httpx"],
        BuildMode.A2_HYBRID: ["regex", "haiku_classifier", "sonnet_drafter", "pydantic"],
        BuildMode.A3_AGENT_BOUNDED: ["langgraph", "crewai", "nemo_guardrails", "tool_budget"],
        BuildMode.A4_LLM_AGENT_FREE: ["opus_crew", "hierarchical_crew", "falsifier", "brier_eval"],
    }
    validation_map = {
        BuildMode.A1_PYTHON_ONLY: ["rule_gates", "pydantic_validation", "sha256_audit"],
        BuildMode.A2_HYBRID: ["rubric_combo", "signed_packet", "source_trace"],
        BuildMode.A3_AGENT_BOUNDED: ["mechanism_map", "proof_check", "mandatory_approval", "audit_trail"],
        BuildMode.A4_LLM_AGENT_FREE: ["10_rubrics", "20_adversarial", "brier_score", "falsification_charter"],
    }
    escalation_map = {"A1": "A2.1", "A2": "A3.1", "A3": "A4.1", "A4": "A4.1"}
    return BuildCard(
        cell_id=cell.cell_id, full_cell_id=cell.full_cell_id,
        altitude=cell.altitude.value, diamond=cell.diamond.value,
        step=cell.step.value, step_name=cell.step.step_name, mode=mode.value,
        archetype_id=f"{mode.value}.{step_idx}", cost_band=mode.cost_band,
        doctrine=mode.description, tools=tools_map.get(mode, []),
        validation_criteria=validation_map.get(mode, []),
        escalation_target=escalation_map.get(mode.value, ""),
        bms_score=round(bms.final, 4),
    )


def generate_all_build_cards() -> list[BuildCard]:
    return [generate_build_card(cell, compute_bms(altitude=cell.altitude)) for cell in get_all_cells()]


# ═══════════════════════════════════════════════════════════════════════════
# PROOF PACKET
# ═══════════════════════════════════════════════════════════════════════════

class ProofPacket(BaseModel):
    packet_id: str = Field(
        default_factory=lambda: hashlib.md5(
            str(datetime.now(timezone.utc).timestamp()).encode()
        ).hexdigest()[:12]
    )
    cell_id: str
    full_cell_id: str = ""
    archetype_id: str
    mode: str
    step: str
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
    gate_results: list = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_audit_log(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "cell_id": self.cell_id,
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


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE WIRE — Connects cells to B-engines
# ═══════════════════════════════════════════════════════════════════════════

STEP_FUNCTION_MAP: dict[str, str] = {
    "intent": "synthesize_evidence",
    "question": "synthesize_evidence",
    "research": "synthesize_evidence",
    "solution": "synthesize_evidence",
    "quality": "falsify_claim",
    "proof": "falsify_claim",
    "integrate": "synthesize_evidence",
}


def wire_cell_to_engine(cell: LatticeCell, input_data: dict[str, Any]) -> dict[str, Any]:
    """Wire a lattice cell to its corresponding execution path based on BMS mode.

    A1 (Python Only): Direct B-engine call — deterministic, no LLM.
    A2 (Hybrid): B-engine + LLM shim for drafting/transformation.
    A3 (Agent Bounded): LangGraph state machine with tool budgets.
    A4 (LLM Agent Free): Deterministic-only, strictest. Returns UNKNOWN if can't complete.
    """
    step_name = cell.step.step_name
    mode = cell.mode

    try:
        # ── A4: LLM-Free (strictest deterministic) ──────────────────────────
        if mode == BuildMode.A4_LLM_AGENT_FREE:
            return _execute_a4(step_name, cell, input_data)

        # ── A3: Agent Bounded (LangGraph + tool budgets) ────────────────────
        if mode == BuildMode.A3_AGENT_BOUNDED:
            return _execute_a3(step_name, cell, input_data)

        # ── A2: Hybrid (B-engine + LLM shim) ────────────────────────────────
        if mode == BuildMode.A2_HYBRID:
            return _execute_a2(step_name, cell, input_data)

        # ── A1: Python Only (default, deterministic) ────────────────────────
        return _execute_a1(step_name, cell, input_data)

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def _execute_a1(step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> dict[str, Any]:
    """A1: Python Only — direct B-engine call, no LLM in decision path."""
    func_name = STEP_FUNCTION_MAP.get(step_name, "synthesize_evidence")
    from strategy_studio.engines import synthesize_evidence, falsify_claim
    func_map = {"synthesize_evidence": synthesize_evidence, "falsify_claim": falsify_claim}
    func = func_map.get(func_name)
    if func is None:
        return {"status": "ERROR", "error": f"Engine function {func_name} not found"}

    if func_name == "synthesize_evidence":
        from strategy_studio.core.types import Evidence
        evidence = [
            Evidence(
                source_uri=f"lattice:{cell.cell_id}",
                content_hash=hashlib.md5(str(input_data).encode()).hexdigest()[:16],
                confidence="H",
                citations=[str(input_data.get("query", ""))[:100]],
            )
        ]
        result = func(evidence, title=input_data.get("query", cell.cell_id)[:60])
        return {
            "status": "PASS", "rationale": result.rationale,
            "recommendation": result.recommendation.title if result.recommendation else "",
            "options_count": len(result.options),
            "options": [{"id": o.id, "title": o.title, "score": o.score} for o in result.options],
            "mode": "A1",
        }
    elif func_name == "falsify_claim":
        claim = input_data.get("query", input_data.get("claim", ""))
        result = func(claim, [])
        return {
            "status": "PASS", "belief": result.belief,
            "disproof_test": result.disproof_test, "falsification_status": result.status,
            "mode": "A1",
        }
    return {"status": "PASS", "note": f"A1 executed {func_name}", "mode": "A1"}


def _execute_a2(step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> dict[str, Any]:
    """A2: Hybrid — B-engine result + LLM shim for enhancement.

    A2 runs the deterministic A1 path first, then applies an LLM shim
    for drafting/transformation if confidence is sufficient.
    Falls back to A1 result if LLM shim fails.
    """
    # Run A1 deterministic path first
    a1_result = _execute_a1(step_name, cell, input_data)
    a1_result["mode"] = "A2"
    a1_result["a1_base"] = True

    # LLM shim: enhance the rationale/recommendation if A1 succeeded
    if a1_result.get("status") == "PASS":
        try:
            enhanced = _a2_llm_shim(step_name, cell, input_data, a1_result)
            if enhanced:
                a1_result["llm_enhanced"] = True
                a1_result["enhanced_rationale"] = enhanced.get("rationale", "")
        except Exception:
            pass  # A2 falls back to A1 result — never fails

    return a1_result


def _a2_llm_shim(step_name: str, cell: LatticeCell, input_data: dict[str, Any], a1_result: dict) -> dict | None:
    """A2 LLM shim: enhance A1 output with LLM assistance.

    In production, this calls a small LLM (Haiku/Sonnet) with:
    - Temperature 0
    - Forced JSON output
    - Pydantic validation
    - Deterministic fallback to A1 result

    Stub implementation returns None (A1 result stands).
    """
    # TODO: Integrate LLM call here when model provider is configured
    # For now, return None to indicate no enhancement (A1 result stands)
    return None


def _execute_a3(step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> dict[str, Any]:
    """A3: Agent Bounded — LangGraph state machine with tool budgets.

    A3 runs the step through a LangGraph StateGraph with:
    - Explicit state object
    - Tool allowlist and cost/runtime budgets
    - Mandatory checkpoints
    - Audit row per transition
    """
    try:
        from strategy_studio.langgraph_executor import LangGraphExecutor
        from strategy_studio.rig_lattice import IQRSQPIStep as StepEnum

        step_map = {
            "intent": StepEnum.I1_INTENT, "question": StepEnum.Q1_QUESTION,
            "research": StepEnum.R_RESEARCH, "solution": StepEnum.S_SOLUTION,
            "quality": StepEnum.Q2_QUALITY, "proof": StepEnum.P_PROOF,
            "integrate": StepEnum.I2_INTEGRATE,
        }
        step_enum = step_map.get(step_name)
        if step_enum is None:
            return {"status": "UNKNOWN", "error": f"Unknown step: {step_name}", "mode": "A3"}

        ex = LangGraphExecutor()
        result = ex.execute_a3(step_enum, input_data)
        output = result.output
        output["mode"] = "A3"
        output["archetype_id"] = result.archetype_id
        output["budget_enforced"] = True
        # Normalize status from LangGraph result
        if "status" not in output:
            output["status"] = "PASS" if result.status == "PASS" else "PARTIAL"
        return output
    except ImportError:
        # Fallback to A1 if LangGraph not available
        result = _execute_a1(step_name, cell, input_data)
        result["mode"] = "A3_fallback"
        result["fallback_reason"] = "LangGraph not available"
        return result
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "mode": "A3"}


def _execute_a4(step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> dict[str, Any]:
    """A4: LLM-Free — strictest deterministic. Returns UNKNOWN if can't complete.

    A4 uses only the A1 deterministic path but with stricter validation:
    - Any step that can't complete deterministically returns UNKNOWN
    - No guessing, no LLM fallback
    - UNKNOWN triggers escalation per doctrine
    """
    result = _execute_a1(step_name, cell, input_data)
    result["mode"] = "A4"

    # A4 strict: if the result has no substantive content, return UNKNOWN
    has_content = bool(
        result.get("rationale") or
        result.get("recommendation") or
        result.get("options") or
        result.get("disproof_test")
    )
    if not has_content:
        result["status"] = "UNKNOWN"
        result["reason"] = "A4: insufficient deterministic evidence"

    return result


# ═══════════════════════════════════════════════════════════════════════════
# ARCHON HARNESS — Per-cell quality gates
# ═══════════════════════════════════════════════════════════════════════════

class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


class QualityGate(BaseModel):
    name: str
    status: GateStatus
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GateResult(BaseModel):
    cell_id: str
    step: str
    mode: str
    gates: list[QualityGate] = Field(default_factory=list)
    overall: GateStatus = GateStatus.UNKNOWN
    duration_ms: int = 0

    @property
    def passed(self) -> bool:
        return self.overall in (GateStatus.PASS, GateStatus.SKIPPED)


def run_quality_gates(cell: LatticeCell, output: dict[str, Any]) -> GateResult:
    """Run quality gates on cell execution output."""
    gates: list[QualityGate] = []
    status = output.get("status", "UNKNOWN")

    # Gate: Execution completed
    gates.append(QualityGate(
        name="execution_complete",
        status=GateStatus.PASS if status == "PASS" else GateStatus.FAIL,
        message=f"Execution status: {status}",
    ))

    # Gate: No errors
    has_error = "error" in output
    gates.append(QualityGate(
        name="no_errors",
        status=GateStatus.FAIL if has_error else GateStatus.PASS,
        message=output.get("error", "No errors"),
    ))

    # Gate: Output has content
    has_content = bool(output.get("rationale") or output.get("recommendation") or output.get("options"))
    gates.append(QualityGate(
        name="output_has_content",
        status=GateStatus.PASS if has_content else GateStatus.WARN,
        message="Output contains substantive content" if has_content else "Output may be thin",
    ))

    # Gate: A1 never guesses — if UNKNOWN, must escalate
    if cell.mode == BuildMode.A1_PYTHON_ONLY and status == "UNKNOWN":
        gates.append(QualityGate(
            name="a1_no_guess",
            status=GateStatus.FAIL,
            message="A1 returned UNKNOWN — must escalate, not guess",
        ))

    overall = GateStatus.PASS
    if any(g.status == GateStatus.FAIL for g in gates):
        overall = GateStatus.FAIL
    elif any(g.status == GateStatus.WARN for g in gates):
        overall = GateStatus.WARN

    return GateResult(
        cell_id=cell.cell_id, step=cell.step.step_name,
        mode=cell.mode.value, gates=gates, overall=overall,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE ORCHESTRATOR — Full IQRSQPI pipeline with escalation
# ═══════════════════════════════════════════════════════════════════════════

class LatticeOrchestrator:
    """Traverses the RIG Lattice. Resolves cells → BMS mode → B-engine → ProofPacket."""

    def __init__(self):
        self._execution_log: list[ProofPacket] = []

    def execute_cell(
        self, cell: LatticeCell, input_data: dict[str, Any],
        escalate_on_failure: bool = True,
    ) -> ProofPacket:
        """Execute a single lattice cell with quality gates and optional escalation."""
        bms = compute_bms(altitude=cell.altitude)
        # 147-cell (mode==A1 default) → BMS-select. 588-cell (explicit mode) → use it.
        mode = bms.select_mode() if cell.mode == BuildMode.A1_PYTHON_ONLY else cell.mode
        t0 = time.time()

        # Wire to B-engine
        output = wire_cell_to_engine(cell, input_data)

        # Run quality gates
        gate_result = run_quality_gates(cell, output)

        # Build ProofPacket
        input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        output_hash = hashlib.md5(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()[:16]
        status = output.get("status", "UNKNOWN")
        duration_ms = int((time.time() - t0) * 1000)

        packet = ProofPacket(
            cell_id=cell.cell_id, full_cell_id=cell.full_cell_id,
            archetype_id=cell.archetype_id, mode=mode.value,
            step=cell.step.step_name, input_hash=input_hash,
            output_hash=output_hash, output=output,
            confidence=bms.final, duration_ms=duration_ms, status=status,
        )

        # Escalation: A1 UNKNOWN → A3.1 per doctrine
        if status in ("ERROR", "UNKNOWN") and escalate_on_failure:
            escalation_mode = self._get_escalation(mode)
            if escalation_mode and escalation_mode != mode:
                packet.escalation_required = True
                packet.escalation_reason = f"{mode.value} returned {status}, escalating to {escalation_mode.value}"
                packet.escalation_from = mode.value
                escalated_cell = LatticeCell(
                    altitude=cell.altitude, diamond=cell.diamond,
                    step=cell.step, mode=escalation_mode,
                )
                return self.execute_cell(escalated_cell, input_data, escalate_on_failure=False)

        self._execution_log.append(packet)
        return packet

    def execute_iqrsqpi(
        self, altitude: Altitude, diamond: Diamond, input_data: dict[str, Any],
    ) -> list[ProofPacket]:
        """Execute all 7 IQRSQPI steps in sequence."""
        packets: list[ProofPacket] = []
        data = dict(input_data)
        for step in IQRSQPIStep:
            cell = LatticeCell(altitude=altitude, diamond=diamond, step=step)
            packet = self.execute_cell(cell, data)
            packets.append(packet)
            if packet.status not in ("ERROR", "UNKNOWN"):
                data[f"step_{step.step_name}"] = packet.output
        return packets

    def execute_full_pipeline(
        self, input_data: dict[str, Any],
        altitude: Altitude = Altitude.L2, diamond: Diamond = Diamond.D1_STRATEGY,
    ) -> dict[str, Any]:
        """Run full 7-step IQRSQPI pipeline."""
        packets = self.execute_iqrsqpi(altitude, diamond, input_data)
        passed = sum(1 for p in packets if p.status == "PASS")
        escalations = [p for p in packets if p.escalation_required]
        steps_output = {p.step: p.output for p in packets}
        return {
            "cell_id": f"L{altitude.value}-{diamond.value}",
            "steps": {p.step: p.model_dump() for p in packets},
            "steps_output": steps_output,
            "summary": {
                "total_steps": len(packets), "passed": passed,
                "failed": len(packets) - passed, "escalations": len(escalations),
                "total_duration_ms": sum(p.duration_ms for p in packets),
                "overall_status": "PASS" if passed == len(packets) else "PARTIAL" if passed > 0 else "FAIL",
            },
            "execution_log": [p.model_dump() for p in self._execution_log],
        }

    def _get_escalation(self, mode: BuildMode) -> BuildMode | None:
        return {
            BuildMode.A1_PYTHON_ONLY: BuildMode.A2_HYBRID,
            BuildMode.A2_HYBRID: BuildMode.A3_AGENT_BOUNDED,
            BuildMode.A3_AGENT_BOUNDED: BuildMode.A4_LLM_AGENT_FREE,
            BuildMode.A4_LLM_AGENT_FREE: None,
        }.get(mode)

    @property
    def execution_log(self) -> list[ProofPacket]:
        return self._execution_log


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_lattice_map(output_path: Path | None = None) -> dict:
    """Generate Excalidraw visualization of the 147-cell lattice."""
    elements: list[dict] = []
    cell_width, cell_height, col_gap, row_gap = 160, 40, 20, 15
    mode_colors = {"A1": "#2ecc71", "A2": "#3498db", "A3": "#f39c12", "A4": "#e74c3c"}

    for alt in Altitude:
        y = (alt.value - 1) * (cell_height + row_gap) + 60
        elements.append({"type": "text", "x": 10, "y": y + 10, "text": f"L{alt.value}",
            "fontSize": 14, "fontFamily": 3, "strokeColor": "#1a1a2e", "backgroundColor": ""})
        for dia in Diamond:
            x_offset = 60 + list(Diamond).index(dia) * 7 * (cell_width + col_gap)
            for step in IQRSQPIStep:
                x = x_offset + list(IQRSQPIStep).index(step) * (cell_width + col_gap)
                bms = compute_bms(altitude=alt)
                color = mode_colors.get(bms.select_mode().value, "#95a5a6")
                elements.append({"type": "rectangle", "x": x, "y": y,
                    "width": cell_width, "height": cell_height,
                    "strokeColor": color, "backgroundColor": color + "33",
                    "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
                    "text": step.value, "fontSize": 10, "fontFamily": 3,
                    "textAlign": "center", "verticalAlign": "middle"})

    legend_y = len(Altitude) * (cell_height + row_gap) + 100
    for i, (mode, color) in enumerate(mode_colors.items()):
        elements.append({"type": "rectangle", "x": 60 + i * 120, "y": legend_y,
            "width": 20, "height": 15, "strokeColor": color, "backgroundColor": color})
        elements.append({"type": "text", "x": 85 + i * 120, "y": legend_y + 2,
            "text": mode, "fontSize": 11, "fontFamily": 3, "strokeColor": "#1a1a2e"})

    diagram = {"type": "excalidraw", "version": 2, "source": "rig-strategy-studio",
        "elements": elements, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
        "files": {}}

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE
# ═══════════════════════════════════════════════════════════════════════════

def get_cell(cell_id: str) -> LatticeCell:
    return LatticeCell.parse(cell_id)

def get_build_card(cell_id: str) -> BuildCard:
    cell = LatticeCell.parse(cell_id)
    bms = compute_bms(altitude=cell.altitude)
    return generate_build_card(cell, bms)

def get_all_build_cards() -> list[BuildCard]:
    return generate_all_build_cards()

def lattice_summary() -> dict[str, Any]:
    cards = generate_all_build_cards()
    by_mode: dict[str, int] = {}
    by_altitude: dict[str, int] = {}
    by_diamond: dict[str, int] = {}
    for card in cards:
        by_mode[card.mode] = by_mode.get(card.mode, 0) + 1
        by_altitude[f"L{card.altitude}"] = by_altitude.get(f"L{card.altitude}", 0) + 1
        by_diamond[card.diamond] = by_diamond.get(card.diamond, 0) + 1
    return {
        "total_cells_147": len(cards), "total_cells_588": 588,
        "by_mode": by_mode, "by_altitude": by_altitude, "by_diamond": by_diamond,
        "by_step": {s.value: 21 for s in IQRSQPIStep},
        "archetypes": 28, "doctrine": "7×3×4×7=588 cells, 4×7=28 archetypes",
    }
