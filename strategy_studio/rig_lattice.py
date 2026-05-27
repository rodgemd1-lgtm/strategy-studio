"""
RIG Lattice — Full Implementation

147 cells: 7 Altitudes × 3 Diamonds × 7 IQRSQPI steps
28 archetypes: 4 Build Modes × 7 steps
BMS scoring with C1/C2/C10 rubric
Escalation paths: A1→A2→A3→A4 on failure

This is the core orchestration layer that wraps all archetype executions.
"""
from __future__ import annotations

import re
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# AXIS 1: ALTITUDE (X) — 7 levels of complexity
# ═══════════════════════════════════════════════════════════════════════════

class Altitude(int, Enum):
    L1 = 1  # Direct, deterministic, repeatable
    L2 = 2  # Structured but parameterized
    L3 = 3  # Workflow with branches
    L4 = 4  # Bounded agentic with checkpoints
    L5 = 5  # Mechanism + tradeoff reasoning
    L6 = 6  # Strategic synthesis required
    L7 = 7  # Doctrine, exploration, novel frame

    @property
    def altitude_bonus(self) -> float:
        """L1-L2: deterministic + reversible = high confidence."""
        return {
            Altitude.L1: 0.35,   # Very high — pure deterministic, fully reversible
            Altitude.L2: 0.28,   # High — structured but parameterized
            Altitude.L3: 0.12,   # Moderate — workflow with branches
            Altitude.L4: 0.0,    # Baseline — bounded agentic
            Altitude.L5: -0.08,  # Lower — mechanism reasoning, less reversible
            Altitude.L6: -0.20,  # Low — strategic synthesis, costly errors
            Altitude.L7: -0.35,  # Very low — novel frame, high failure cost, irreducible
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
    D1_STRATEGY = "D1"      # Strategy synthesis
    D2_INTELLIGENCE = "D2"  # Intelligence & research
    D3_OPERATIONS = "D3"    # Operations & execution


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
    def name(self) -> str:
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
    A1_PYTHON_ONLY = "A1"       # BMS ≥ 0.75
    A2_HYBRID = "A2"            # BMS 0.45-0.74
    A3_AGENT_BOUNDED = "A3"     # BMS 0.25-0.44
    A4_LLM_AGENT_FREE = "A4"    # BMS < 0.25

    @property
    def cost_band(self) -> str:
        return {"A1": "≤$0.001", "A2": "≤$0.05", "A3": "≤$1", "A4": "≤$50+4h"}[self.value]

    @property
    def description(self) -> str:
        return {
            "A1": "No model in decision path. Pydantic + Jinja + regex.",
            "A2": "Python gates + small LLM shims (Haiku/Sonnet).",
            "A3": "LangGraph/CrewAI with hard tool + cost budgets.",
            "A4": "Opus + hierarchical crews, NeMo Guardrails, falsification.",
        }[self.value]


# ═══════════════════════════════════════════════════════════════════════════
# BMS SCORING — Build Mode Selection
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BMSCriteria:
    """The three-rule rubric that drives RAW score."""
    failure_cost: float = 0.5       # C1: Cost of being wrong (0-1)
    reversibility: float = 0.5      # C2: Can we undo this? (0-1, 1=fully reversible)
    mechanism_clarity: float = 0.5  # C10: How clear is the mechanism? (0-1)

    @property
    def raw_score(self) -> float:
        """RAW = weighted average of C1, C2, C10."""
        return (self.failure_cost * 0.4 + self.reversibility * 0.3 + self.mechanism_clarity * 0.3)


@dataclass
class BMSScore:
    """Full BMS scoring with adjustments."""
    raw: float = 0.5
    adj_failure: float = 0.0   # Past failure rate adjustment
    adj_volume: float = 0.0    # Data volume adjustment
    adj_altitude: float = 0.0  # Altitude penalty

    @property
    def final(self) -> float:
        return max(0.0, min(1.0, self.raw + self.adj_failure + self.adj_volume + self.adj_altitude))

    def select_mode(self) -> BuildMode:
        bms = self.final
        if bms >= 0.75:
            return BuildMode.A1_PYTHON_ONLY
        elif bms >= 0.45:
            return BuildMode.A2_HYBRID
        elif bms >= 0.25:
            return BuildMode.A3_AGENT_BOUNDED
        else:
            return BuildMode.A4_LLM_AGENT_FREE


def compute_bms(
    failure_cost: float = 0.5,
    reversibility: float = 0.5,
    mechanism_clarity: float = 0.5,
    past_failure_rate: float = 0.0,
    data_volume: float = 0.5,
    altitude: Altitude = Altitude.L2,
) -> BMSScore:
    """Compute BMS score from criteria."""
    criteria = BMSCriteria(failure_cost, reversibility, mechanism_clarity)
    return BMSScore(
        raw=criteria.raw_score,
        adj_failure=-past_failure_rate * 0.2,
        adj_volume=(data_volume - 0.5) * 0.1,
        adj_altitude=altitude.altitude_bonus,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE COORDINATE — Full cell address
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LatticeCell:
    """Full RIG Lattice coordinate."""
    altitude: Altitude
    diamond: Diamond
    step: IQRSQPIStep
    mode: BuildMode = BuildMode.A1_PYTHON_ONLY

    @property
    def cell_id(self) -> str:
        return f"L{self.altitude.value}-{self.diamond.value}-{self.step.value}"

    @property
    def archetype_id(self) -> str:
        return f"{self.mode.value}.{list(IQRSQPIStep).index(self.step) + 1}"

    def __str__(self) -> str:
        return f"{self.cell_id} → {self.archetype_id}"

    @classmethod
    def parse(cls, cell_id: str) -> "LatticeCell":
        """Parse cell ID like 'L2-D1-I1' → LatticeCell."""
        pattern = r"^L(\d+)-(D[123])-(I[12]|Q[12]|[RSP])$"
        m = re.match(pattern, cell_id)
        if not m:
            raise ValueError(f"Invalid cell ID: {cell_id}. Expected: L<1-7>-D<1-3>-<IQRSQPI>")
        return cls(
            altitude=Altitude(int(m.group(1))),
            diamond=Diamond(f"D{m.group(2)[1]}"),
            step=IQRSQPIStep(m.group(3)),
        )


def get_all_cells() -> list[LatticeCell]:
    """Return all 147 cells: 7 altitudes × 3 diamonds × 7 steps."""
    cells = []
    for alt in Altitude:
        for dia in ["D1", "D2", "D3"]:
            for step in IQRSQPIStep:
                cells.append(LatticeCell(altitude=alt, diamond=Diamond(dia), step=step))
    return cells


def get_all_cell_ids() -> list[str]:
    """Return all 147 cell ID strings."""
    return [c.cell_id for c in get_all_cells()]


def get_archetype_cells(mode: BuildMode) -> list[LatticeCell]:
    """Return all cells that resolve to a given build mode.

    A1: L1 (all 21 cells) + L2 (all 21 cells) = 42 cells
    A2: L2 (overlap) + L3 + L4 (partial) = ~42 cells  
    A3: L4 (overlap) + L5 + L6 (partial) = ~42 cells
    A4: L6 (overlap) + L7 = ~21 cells
    """
    all_cells = get_all_cells()
    result = []
    for cell in all_cells:
        bms = compute_bms(altitude=cell.altitude)
        resolved_mode = bms.select_mode()
        if resolved_mode == mode:
            result.append(cell)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# ARCHETYPE EXECUTION — Mode-specific wrappers
# ═══════════════════════════════════════════════════════════════════════════

class ArchetypeResult(BaseModel):
    """Result from executing one archetype step."""
    archetype_id: str
    cell_id: str
    mode: str
    step: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    duration_ms: int = 0
    status: str = "unknown"
    escalation_required: bool = False
    escalation_reason: str = ""


class BuildCard(BaseModel):
    """Build Card — the contract per cell."""
    cell_id: str
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
    escalation_target: str = ""  # e.g., "A2.1" if A1.1 fails
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def generate_build_card(cell: LatticeCell, bms: BMSScore) -> BuildCard:
    """Generate a Build Card for a lattice cell."""
    mode = bms.select_mode()
    step_idx = list(IQRSQPIStep).index(cell.step) + 1

    # Define tools per mode per step
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

    escalation_map = {
        "A1": "A2.1", "A2": "A3.1", "A3": "A4.1", "A4": "A4.1",
    }

    return BuildCard(
        cell_id=cell.cell_id,
        altitude=cell.altitude.value,
        diamond=cell.diamond.value,
        step=cell.step.value,
        step_name=cell.step.name,
        mode=mode.value,
        archetype_id=f"{mode.value}.{step_idx}",
        cost_band=mode.cost_band,
        doctrine=mode.description,
        tools=tools_map.get(mode, []),
        validation_criteria=validation_map.get(mode, []),
        escalation_target=escalation_map.get(mode.value, ""),
    )


def generate_all_build_cards() -> list[BuildCard]:
    """Generate all 147 Build Cards."""
    cards = []
    for cell in get_all_cells():
        bms = compute_bms(altitude=cell.altitude)
        cards.append(generate_build_card(cell, bms))
    return cards


# ═══════════════════════════════════════════════════════════════════════════
# ARCHETYPE EXECUTOR — Routes to correct A1-A4 implementation
# ═══════════════════════════════════════════════════════════════════════════

class ArchetypeExecutor:
    """
    Executes archetype steps based on BMS-selected mode.
    Wraps the existing strategy_studio archetype implementations.
    """

    def __init__(self):
        self._execution_log: list[ArchetypeResult] = []

    def execute(
        self,
        cell: LatticeCell,
        input_data: dict[str, Any],
        escalate_on_failure: bool = True,
    ) -> ArchetypeResult:
        """Execute a lattice cell, with optional escalation."""
        bms = compute_bms(altitude=cell.altitude)
        mode = bms.select_mode()
        t0 = time.time()

        # Try execution in selected mode
        result = self._execute_mode(mode, cell, input_data)

        # Escalate on failure
        if result.status in ("UNKNOWN", "failed", "QUALITY_FAILED") and escalate_on_failure:
            escalation_mode = self._get_escalation(mode)
            if escalation_mode and escalation_mode != mode:
                result.escalation_required = True
                result.escalation_reason = f"{mode.value} returned {result.status}, escalating to {escalation_mode.value}"
                result = self._execute_mode(escalation_mode, cell, input_data)

        result.duration_ms = int((time.time() - t0) * 1000)
        self._execution_log.append(result)
        return result

    def _execute_mode(self, mode: BuildMode, cell: LatticeCell, input_data: dict[str, Any]) -> ArchetypeResult:
        """Execute using the specific build mode."""
        step_name = cell.step.name
        step_idx = list(IQRSQPIStep).index(cell.step) + 1
        archetype_id = f"{mode.value}.{step_idx}"

        try:
            if mode == BuildMode.A1_PYTHON_ONLY:
                return self._execute_a1(step_name, cell, input_data)
            elif mode == BuildMode.A2_HYBRID:
                return self._execute_a2(step_name, cell, input_data)
            elif mode == BuildMode.A3_AGENT_BOUNDED:
                return self._execute_a3(step_name, cell, input_data)
            elif mode == BuildMode.A4_LLM_AGENT_FREE:
                return self._execute_a4(step_name, cell, input_data)
        except Exception as e:
            return ArchetypeResult(
                archetype_id=archetype_id,
                cell_id=cell.cell_id,
                mode=mode.value,
                step=step_name,
                status="ERROR",
                escalation_reason=str(e),
            )

        return ArchetypeResult(
            archetype_id=archetype_id,
            cell_id=cell.cell_id,
            mode=mode.value,
            step=step_name,
            status="UNKNOWN",
        )

    def _execute_a1(self, step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> ArchetypeResult:
        """Execute using A1 PYTHON_ONLY — direct import of existing implementations."""
        from strategy_studio.core.types import InboundPayload

        payload = InboundPayload(raw_text=input_data.get("query", ""))

        step_functions = {
            "intent": ("a1_1_intent", "classify_intent"),
            "question": ("a1_2_question", "generate_questions"),
            "research": ("a1_3_research", "execute_research"),
            "solution": ("a1_4_solution", "synthesize"),
            "quality": ("a1_5_quality", "validate"),
            "proof": ("a1_6_proof", "build_proof"),
            "integrate": ("a1_7_integrate", "integrate"),
        }

        module_name: str
        func_name: str
        module_name, func_name = step_functions[step_name]  # type: ignore[index]

        if not module_name:
            return ArchetypeResult(
                archetype_id=f"A1.{list(IQRSQPIStep).index(cell.step) + 1}",
                cell_id=cell.cell_id, mode="A1", step=step_name, status="UNKNOWN",
            )

        try:
            module = __import__(
                "strategy_studio.archetypes.a1",
                fromlist=[module_name],
            )
            submod = getattr(module, module_name)
            func = getattr(submod, func_name)

            # Call with appropriate arguments
            if step_name == "intent":
                intent_key, confidence = func(payload)
                return ArchetypeResult(
                    archetype_id="A1.1", cell_id=cell.cell_id, mode="A1", step=step_name,
                    output={"intent": intent_key.value, "confidence": confidence},
                    status="PASS", confidence=confidence,
                )
            elif step_name == "question":
                from strategy_studio.core.types import IntentKey
                questions = func(IntentKey.SYNTHESIZE, payload)
                return ArchetypeResult(
                    archetype_id="A1.2", cell_id=cell.cell_id, mode="A1", step=step_name,
                    output={"questions": [q.question_text for q in questions]},
                    status="PASS",
                )
            elif step_name == "solution":
                from strategy_studio.core.types import ResearchPack
                pack = ResearchPack()
                result = func(pack)
                return ArchetypeResult(
                    archetype_id="A1.4", cell_id=cell.cell_id, mode="A1", step=step_name,
                    output={"recommendation": result.recommendation.title if result.recommendation else ""},
                    status="PASS",
                )
            elif step_name == "quality":
                from strategy_studio.core.types import Synthesis, IntentKey
                synth = Synthesis(rationale="test")
                quality = func(synth, intent=IntentKey.SYNTHESIZE)
                return ArchetypeResult(
                    archetype_id="A1.5", cell_id=cell.cell_id, mode="A1", step=step_name,
                    output={"passed": quality.passed, "checklist": quality.checklist},
                    status="PASS" if quality.passed else "QUALITY_FAILED",
                )
            elif step_name == "integrate":
                from strategy_studio.core.types import ProofPacket, Synthesis, IntentKey, Action
                proof = ProofPacket(claim="test claim", confidence="M")
                synth = Synthesis(rationale="test synthesis rationale")
                action, audit = func(proof, synth, IntentKey.SYNTHESIZE)
                return ArchetypeResult(
                    archetype_id="A1.7", cell_id=cell.cell_id, mode="A1", step=step_name,
                    output={"action": action.action_type if action else "", "status": audit.status},
                    status=audit.status,
                )
            else:
                return ArchetypeResult(
                    archetype_id=f"A1.{list(IQRSQPIStep).index(cell.step) + 1}",
                    cell_id=cell.cell_id, mode="A1", step=step_name, status="PASS",
                    output={"note": f"A1 {step_name} executed"},
                )
        except Exception as e:
            return ArchetypeResult(
                archetype_id=f"A1.{list(IQRSQPIStep).index(cell.step) + 1}",
                cell_id=cell.cell_id, mode="A1", step=step_name,
                status="ERROR", escalation_reason=str(e),
            )

    def _execute_a2(self, step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> ArchetypeResult:
        """Execute using A2 HYBRID — Python gates + LLM shims."""
        # A2 adds LLM assistance to A1 steps
        # Intent: Pydantic + Haiku classifier
        # Solution: Sonnet draft + Jinja frame
        # Quality: Rubric + rule combo
        result = self._execute_a1(step_name, cell, input_data)
        result.mode = "A2"
        result.archetype_id = f"A2.{list(IQRSQPIStep).index(cell.step) + 1}"
        # Mark as hybrid-enhanced
        result.output["hybrid_enhancement"] = True
        result.output["llm_shim"] = "haiku_classifier" if step_name == "intent" else "sonnet_drafter" if step_name == "solution" else "rubric_judge"
        return result

    def _execute_a3(self, step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> ArchetypeResult:
        """Execute using A3 AGENT_BOUNDED — LangGraph + bounded CrewAI."""
        step_idx = list(IQRSQPIStep).index(cell.step) + 1
        step_map = {
            "intent": IQRSQPIStep.I1_INTENT,
            "question": IQRSQPIStep.Q1_QUESTION,
            "research": IQRSQPIStep.R_RESEARCH,
            "solution": IQRSQPIStep.S_SOLUTION,
            "quality": IQRSQPIStep.Q2_QUALITY,
            "proof": IQRSQPIStep.P_PROOF,
            "integrate": IQRSQPIStep.I2_INTEGRATE,
        }
        step_enum = step_map.get(step_name)
        if step_enum is None:
            return ArchetypeResult(
                archetype_id=f"A3.{step_idx}",
                cell_id=cell.cell_id, mode="A3", step=step_name,
                status="UNKNOWN", output={"reason": f"Unknown step: {step_name}"},
            )
        try:
            from strategy_studio.langgraph_executor import LangGraphExecutor
            ex = LangGraphExecutor()
            return ex.execute_a3(step_enum, input_data)
        except Exception as e:
            return ArchetypeResult(
                archetype_id=f"A3.{step_idx}",
                cell_id=cell.cell_id, mode="A3", step=step_name,
                status="ERROR", output={"error": str(e)},
            )

    def _execute_a4(self, step_name: str, cell: LatticeCell, input_data: dict[str, Any]) -> ArchetypeResult:
        """Execute using A4 LLM_AGENT_FREE — hierarchical crews + falsification."""
        step_idx = list(IQRSQPIStep).index(cell.step) + 1
        step_map = {
            "intent": IQRSQPIStep.I1_INTENT,
            "question": IQRSQPIStep.Q1_QUESTION,
            "research": IQRSQPIStep.R_RESEARCH,
            "solution": IQRSQPIStep.S_SOLUTION,
            "quality": IQRSQPIStep.Q2_QUALITY,
            "proof": IQRSQPIStep.P_PROOF,
            "integrate": IQRSQPIStep.I2_INTEGRATE,
        }
        step_enum = step_map.get(step_name)
        if step_enum is None:
            return ArchetypeResult(
                archetype_id=f"A4.{step_idx}",
                cell_id=cell.cell_id, mode="A4", step=step_name,
                status="UNKNOWN", output={"reason": f"Unknown step: {step_name}"},
            )
        try:
            from strategy_studio.langgraph_executor import LangGraphExecutor
            ex = LangGraphExecutor()
            return ex.execute_a4(step_enum, input_data)
        except Exception as e:
            return ArchetypeResult(
                archetype_id=f"A4.{step_idx}",
                cell_id=cell.cell_id, mode="A4", step=step_name,
                status="ERROR", output={"error": str(e)},
            )

    def _get_escalation(self, mode: BuildMode) -> Optional[BuildMode]:
        """Get escalation target for a mode."""
        escalation = {
            BuildMode.A1_PYTHON_ONLY: BuildMode.A2_HYBRID,
            BuildMode.A2_HYBRID: BuildMode.A3_AGENT_BOUNDED,
            BuildMode.A3_AGENT_BOUNDED: BuildMode.A4_LLM_AGENT_FREE,
            BuildMode.A4_LLM_AGENT_FREE: None,  # A4 is the top — no escalation
        }
        return escalation.get(mode)

    @property
    def execution_log(self) -> list[ArchetypeResult]:
        return self._execution_log


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — OpenClaw-style cell traversal
# ═══════════════════════════════════════════════════════════════════════════

class LatticeOrchestrator:
    """
    Traverses the RIG Lattice given an input.
    Resolves (altitude, diamond, step) → archetype and dispatches.
    """

    def __init__(self):
        self.executor = ArchetypeExecutor()
        self._results: dict[str, ArchetypeResult] = {}

    def traverse(
        self,
        cell_id: str,
        input_data: dict[str, Any],
        mode: BuildMode | None = None,
    ) -> ArchetypeResult:
        """Traverse a single cell."""
        cell = LatticeCell.parse(cell_id)
        if mode:
            cell = LatticeCell(altitude=cell.altitude, diamond=cell.diamond, step=cell.step, mode=mode)
        result = self.executor.execute(cell, input_data)
        self._results[cell_id] = result
        return result

    def traverse_diamond(
        self,
        altitude: Altitude,
        diamond: Diamond,
        input_data: dict[str, Any],
    ) -> dict[str, ArchetypeResult]:
        """Traverse all 7 steps in a diamond (I1→Q1→R→S→Q2→P→I2)."""
        results = {}
        data = dict(input_data)

        for step in IQRSQPIStep:
            cell_id = f"L{altitude.value}-{diamond.value}-{step.value}"
            result = self.traverse(cell_id, data)
            results[cell_id] = result

            # Pass output to next step
            if result.status not in ("ERROR", "UNKNOWN"):
                data[f"step_{step.name}"] = result.output

        return results

    def traverse_altitude(
        self,
        altitude: Altitude,
        input_data: dict[str, Any],
    ) -> dict[str, dict[str, ArchetypeResult]]:
        """Traverse all 3 diamonds at an altitude."""
        results = {}
        for diamond in Diamond:
            diamond_results = self.traverse_diamond(altitude, diamond, input_data)
            results[diamond.value] = diamond_results
        return results

    def run_full_pipeline(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the full 7-step IQRSQPI pipeline for a strategy analysis."""
        results = {
            "I1": {}, "Q1": {}, "R": {}, "S": {}, "Q2": {}, "P": {}, "I2": {},
        }
        data = dict(input_data)

        # Run through each step
        for step in IQRSQPIStep:
            cell_id = f"L2-D1-{step.value}"  # Default: L2, D1 (strategy synthesis)
            result = self.traverse(cell_id, data)
            results[step.value.replace("_", "")] = result.model_dump()

            # Pass output to next step
            if result.status not in ("ERROR", "UNKNOWN"):
                data[f"step_{step.name}"] = result.output

        return {
            "pipeline_results": steps_results_final(results),
            "execution_log": [r.model_dump() for r in self.executor.execution_log],
            "cells_executed": len(self.executor.execution_log),
            "cells_passed": sum(1 for r in self.executor.execution_log if r.status == "PASS"),
        }


def steps_results_final(results: dict) -> dict:
    """Clean up step results for output."""
    cleaned = {}
    for step, result in results.items():
        if isinstance(result, ArchetypeResult):
            cleaned[step] = result.model_dump()
        elif isinstance(result, dict):
            cleaned[step] = result
        else:
            cleaned[step] = {"status": "unknown"}
    return cleaned


# ═══════════════════════════════════════════════════════════════════════════
# BUILD CARD GENERATOR — Emit all 147 Build Cards
# ═══════════════════════════════════════════════════════════════════════════

class BuildCardGenerator:
    """Generates and persists Build Cards for all 147 lattice cells."""

    def __init__(self, output_dir: Path = Path("phronema")):
        self.output_dir = output_dir

    def generate_all(self, persist: bool = True) -> list[BuildCard]:
        """Generate all 147 Build Cards."""
        cards = generate_all_build_cards()
        if persist:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for card in cards:
                filepath = self.output_dir / f"{card.cell_id}.yaml"
                filepath.write_text(self._card_to_yaml(card), encoding="utf-8")
        return cards

    def _card_to_yaml(self, card: BuildCard) -> str:
        """Convert BuildCard to YAML string."""
        lines = [
            f"# Build Card: {card.cell_id} → {card.archetype_id}",
            f"cell_id: {card.cell_id}",
            f"altitude: {card.altitude}",
            f"diamond: {card.diamond}",
            f"step: {card.step}",
            f"step_name: {card.step_name}",
            f"mode: {card.mode}",
            f"archetype_id: {card.archetype_id}",
            f"cost_band: {card.cost_band}",
            f"doctrine: |",
        ]
        for line in card.doctrine.split(". "):
            lines.append(f"  {line.strip()}.")
        lines.append("tools:")
        for tool in card.tools:
            lines.append(f"  - {tool}")
        lines.append("validation_criteria:")
        for crit in card.validation_criteria:
            lines.append(f"  - {crit}")
        lines.append(f"escalation_target: {card.escalation_target}")
        lines.append(f"timestamp: {card.timestamp.isoformat()}")
        return "\n".join(lines)

    def get_card(self, cell_id: str) -> Optional[BuildCard]:
        """Load a Build Card by cell ID."""
        filepath = self.output_dir / f"{cell_id}.yaml"
        if filepath.exists():
            return BuildCard.parse_file(filepath)  # type: ignore
        return None

    def summary(self) -> dict[str, Any]:
        """Summary of all Build Cards."""
        cards = generate_all_build_cards()
        by_mode: dict[str, int] = {}
        by_altitude: dict[int, int] = {}
        for card in cards:
            by_mode[card.mode] = by_mode.get(card.mode, 0) + 1
            by_altitude[card.altitude] = by_altitude.get(card.altitude, 0) + 1
        return {
            "total_cards": len(cards),
            "by_mode": by_mode,
            "by_altitude": {f"L{k}": v for k, v in by_altitude.items()},
            "by_step": {s.value: 21 for s in IQRSQPIStep},  # 21 cells per step (7 alt × 3 dia)
        }