"""
LatticeWire — The complete RIG Lattice execution system for Strategy Studio.

Connects the 147-cell lattice (7 Altitudes × 3 Diamonds × 7 IQRSQPI steps)
to the B-engine execution layer (B29-B46) with BMS scoring, escalation,
Build Card generation, and ProofPacket audit trails.

Architecture:
  InboundPayload → LatticeOrchestrator → BMS scoring → cell routing
  → B-engine execution → ArchetypeResult → ProofPacket → audit trail

Coordinate system: L{1-7}-D{1-3}-{I1,Q1,R,S,Q2,P,I2} → A{1-4}.{1-7}
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
    L1 = 1  # Direct, deterministic, repeatable
    L2 = 2  # Structured but parameterized
    L3 = 3  # Workflow with branches
    L4 = 4  # Bounded agentic with checkpoints
    L5 = 5  # Mechanism + tradeoff reasoning
    L6 = 6  # Strategic synthesis required
    L7 = 7  # Doctrine, exploration, novel frame

    @property
    def altitude_bonus(self) -> float:
        return {
            Altitude.L1: 0.35,
            Altitude.L2: 0.28,
            Altitude.L3: 0.12,
            Altitude.L4: 0.0,
            Altitude.L5: -0.08,
            Altitude.L6: -0.20,
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
    A1_PYTHON_ONLY = "A1"       # BMS >= 0.75
    A2_HYBRID = "A2"            # BMS 0.45-0.74
    A3_AGENT_BOUNDED = "A3"     # BMS 0.25-0.44
    A4_LLM_AGENT_FREE = "A4"    # BMS < 0.25

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
        return self.failure_cost * 0.4 + self.reversibility * 0.3 + self.mechanism_clarity * 0.3


@dataclass
class BMSScore:
    """Full BMS scoring with adjustments."""
    raw: float = 0.5
    adj_failure: float = 0.0
    adj_volume: float = 0.0
    adj_altitude: float = 0.0

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
        return f"{self.cell_id} -> {self.archetype_id}"

    @classmethod
    def parse(cls, cell_id: str) -> "LatticeCell":
        """Parse cell ID like 'L2-D1-I1' -> LatticeCell."""
        import re
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
    """Return all 147 cells: 7 altitudes x 3 diamonds x 7 steps."""
    cells = []
    for alt in Altitude:
        for dia in Diamond:
            for step in IQRSQPIStep:
                cells.append(LatticeCell(altitude=alt, diamond=dia, step=step))
    return cells


# ═══════════════════════════════════════════════════════════════════════════
# BUILD CARD — The contract per cell
# ═══════════════════════════════════════════════════════════════════════════

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
    escalation_target: str = ""
    bms_score: float = 0.5
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def generate_build_card(cell: LatticeCell, bms: BMSScore) -> BuildCard:
    """Generate a Build Card for a lattice cell."""
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
        cell_id=cell.cell_id,
        altitude=cell.altitude.value,
        diamond=cell.diamond.value,
        step=cell.step.value,
        step_name=cell.step.step_name,
        mode=mode.value,
        archetype_id=f"{mode.value}.{step_idx}",
        cost_band=mode.cost_band,
        doctrine=mode.description,
        tools=tools_map.get(mode, []),
        validation_criteria=validation_map.get(mode, []),
        escalation_target=escalation_map.get(mode.value, ""),
        bms_score=round(bms.final, 4),
    )


def generate_all_build_cards() -> list[BuildCard]:
    """Generate all 147 Build Cards."""
    cards = []
    for cell in get_all_cells():
        bms = compute_bms(altitude=cell.altitude)
        cards.append(generate_build_card(cell, bms))
    return cards


# ═══════════════════════════════════════════════════════════════════════════
# PROOF PACKET — Auditable result per cell execution
# ═══════════════════════════════════════════════════════════════════════════

class ProofPacket(BaseModel):
    """Auditable proof packet for every lattice cell execution."""
    packet_id: str = Field(
        default_factory=lambda: hashlib.md5(
            str(datetime.now(timezone.utc).timestamp()).encode()
        ).hexdigest()[:12]
    )
    cell_id: str
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE WIRE — Connects lattice cells to B-engine execution
# ═══════════════════════════════════════════════════════════════════════════

# Step -> B-engine function mapping
STEP_ENGINE_MAP: dict[str, str] = {
    "intent": "b29_synthesize",      # I1: Intent classification -> synthesis
    "question": "b29_synthesize",    # Q1: Question generation -> synthesis
    "research": "b29_synthesize",    # R: Research -> synthesis
    "solution": "b29_synthesize",    # S: Solution synthesis
    "quality": "b33_falsify",        # Q2: Quality -> falsification
    "proof": "b33_falsify",          # P: Proof -> falsification
    "integrate": "b29_synthesize",   # I2: Integration -> synthesis
}

# Step -> B-engine function name for import
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
    """Wire a lattice cell to its corresponding B-engine function.

    Returns the raw output from the B-engine.
    """
    step_name = cell.step.step_name
    func_name = STEP_FUNCTION_MAP.get(step_name, "synthesize_evidence")

    try:
        from strategy_studio.engines import synthesize_evidence, falsify_claim
        func_map = {
            "synthesize_evidence": synthesize_evidence,
            "falsify_claim": falsify_claim,
        }
        func = func_map.get(func_name)

        if func is None:
            return {"status": "ERROR", "error": f"Engine function {func_name} not found"}

        # Prepare arguments based on step
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
                "status": "PASS",
                "rationale": result.rationale,
                "recommendation": result.recommendation.title if result.recommendation else "",
                "options_count": len(result.options),
                "options": [
                    {"id": o.id, "title": o.title, "score": o.score}
                    for o in result.options
                ],
            }
        elif func_name == "falsify_claim":
            claim = input_data.get("query", input_data.get("claim", ""))
            result = func(claim, [])
            return {
                "status": "PASS",
                "belief": result.belief,
                "disproof_test": result.disproof_test,
                "falsification_status": result.status,
            }
        else:
            return {"status": "PASS", "note": f"Executed {func_name}"}

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE ORCHESTRATOR — Full IQRSQPI pipeline with escalation
# ═══════════════════════════════════════════════════════════════════════════

class LatticeOrchestrator:
    """
    Traverses the RIG Lattice given an input.
    Resolves (altitude, diamond, step) -> BMS mode -> B-engine -> ProofPacket.
    """

    def __init__(self):
        self._execution_log: list[ProofPacket] = []

    def execute_cell(
        self,
        cell: LatticeCell,
        input_data: dict[str, Any],
        escalate_on_failure: bool = True,
    ) -> ProofPacket:
        """Execute a single lattice cell, with optional escalation."""
        bms = compute_bms(altitude=cell.altitude)
        mode = bms.select_mode()
        t0 = time.time()

        # Wire to B-engine
        output = wire_cell_to_engine(cell, input_data)

        # Build ProofPacket
        input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        output_hash = hashlib.md5(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()[:16]

        status = output.get("status", "UNKNOWN")
        duration_ms = int((time.time() - t0) * 1000)

        packet = ProofPacket(
            cell_id=cell.cell_id,
            archetype_id=cell.archetype_id,
            mode=mode.value,
            step=cell.step.step_name,
            input_hash=input_hash,
            output_hash=output_hash,
            output=output,
            confidence=bms.final,
            duration_ms=duration_ms,
            status=status,
        )

        # Escalation
        if status in ("ERROR", "UNKNOWN") and escalate_on_failure:
            escalation_mode = self._get_escalation(mode)
            if escalation_mode and escalation_mode != mode:
                packet.escalation_required = True
                packet.escalation_reason = f"{mode.value} returned {status}, escalating to {escalation_mode.value}"
                packet.escalation_from = mode.value

                # Re-esecute at higher mode
                escalated_cell = LatticeCell(
                    altitude=cell.altitude,
                    diamond=cell.diamond,
                    step=cell.step,
                    mode=escalation_mode,
                )
                return self.execute_cell(escalated_cell, input_data, escalate_on_failure=False)

        self._execution_log.append(packet)
        return packet

    def execute_iqrsqpi(
        self,
        altitude: Altitude,
        diamond: Diamond,
        input_data: dict[str, Any],
    ) -> list[ProofPacket]:
        """Execute all 7 IQRSQPI steps in sequence (I1->Q1->R->S->Q2->P->I2)."""
        packets: list[ProofPacket] = []
        data = dict(input_data)

        for step in IQRSQPIStep:
            cell = LatticeCell(altitude=altitude, diamond=diamond, step=step)
            packet = self.execute_cell(cell, data)
            packets.append(packet)

            # Pass output to next step
            if packet.status not in ("ERROR", "UNKNOWN"):
                data[f"step_{step.step_name}"] = packet.output

        return packets

    def execute_diamond(
        self,
        altitude: Altitude,
        diamond: Diamond,
        input_data: dict[str, Any],
    ) -> dict[str, list[ProofPacket]]:
        """Execute all 7 steps for a diamond, keyed by step."""
        packets = self.execute_iqrsqpi(altitude, diamond, input_data)
        return {p.step: [p] for p in packets}

    def execute_full_pipeline(
        self,
        input_data: dict[str, Any],
        altitude: Altitude = Altitude.L2,
        diamond: Diamond = Diamond.D1_STRATEGY,
    ) -> dict[str, Any]:
        """Run the full 7-step IQRSQPI pipeline and return consolidated results."""
        packets = self.execute_iqrsqpi(altitude, diamond, input_data)

        steps_output: dict[str, Any] = {}
        for p in packets:
            steps_output[p.step] = p.output

        passed = sum(1 for p in packets if p.status == "PASS")
        escalations = [p for p in packets if p.escalation_required]

        return {
            "cell_id": f"L{altitude.value}-{diamond.value}",
            "steps": {p.step: p.model_dump() for p in packets},
            "steps_output": steps_output,
            "summary": {
                "total_steps": len(packets),
                "passed": passed,
                "failed": len(packets) - passed,
                "escalations": len(escalations),
                "total_duration_ms": sum(p.duration_ms for p in packets),
                "overall_status": "PASS" if passed == len(packets) else "PARTIAL" if passed > 0 else "FAIL",
            },
            "execution_log": [p.model_dump() for p in self._execution_log],
        }

    def _get_escalation(self, mode: BuildMode) -> BuildMode | None:
        """Get escalation target for a mode."""
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
# LATTICE VISUALIZATION — Excalidraw lattice map
# ═══════════════════════════════════════════════════════════════════════════

def generate_lattice_map(output_path: Path | None = None) -> dict:
    """Generate an Excalidraw visualization of the full 147-cell lattice."""
    import json as _json

    elements: list[dict] = []
    cell_width = 160
    cell_height = 40
    col_gap = 20
    row_gap = 15

    # Color by mode
    mode_colors = {
        "A1": "#2ecc71",  # green
        "A2": "#3498db",  # blue
        "A3": "#f39c12",  # orange
        "A4": "#e74c3c",  # red
    }

    cells = get_all_cells()
    bms_default = compute_bms()

    # Group by altitude (rows) and diamond (columns within row)
    for alt in Altitude:
        alt_cells = [c for c in cells if c.altitude == alt]
        y = (alt.value - 1) * (cell_height + row_gap) + 60

        # Altitude label
        elements.append({
            "type": "text", "x": 10, "y": y + 10,
            "text": f"L{alt.value}", "fontSize": 14, "fontFamily": 3,
            "strokeColor": "#1a1a2e", "backgroundColor": "",
        })

        for dia in Diamond:
            dia_cells = [c for c in alt_cells if c.diamond == dia]
            x_offset = 60 + (list(Diamond).index(dia)) * 7 * (cell_width + col_gap)

            for step in IQRSQPIStep:
                step_idx = list(IQRSQPIStep).index(step)
                x = x_offset + step_idx * (cell_width + col_gap)
                cell = LatticeCell(altitude=alt, diamond=dia, step=step)
                bms = compute_bms(altitude=alt)
                mode = bms.select_mode()
                color = mode_colors.get(mode.value, "#95a5a6")

                elements.append({
                    "type": "rectangle",
                    "x": x, "y": y, "width": cell_width, "height": cell_height,
                    "strokeColor": color, "backgroundColor": color + "33",
                    "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
                    "text": f"{step.value}", "fontSize": 10, "fontFamily": 3,
                    "textAlign": "center", "verticalAlign": "middle",
                })

    # Legend
    legend_y = len(Altitude) * (cell_height + row_gap) + 100
    for i, (mode, color) in enumerate(mode_colors.items()):
        elements.append({
            "type": "rectangle",
            "x": 60 + i * 120, "y": legend_y, "width": 20, "height": 15,
            "strokeColor": color, "backgroundColor": color,
        })
        elements.append({
            "type": "text", "x": 85 + i * 120, "y": legend_y + 2,
            "text": mode, "fontSize": 11, "fontFamily": 3, "strokeColor": "#1a1a2e",
        })

    diagram = {
        "type": "excalidraw", "version": 2,
        "source": "rig-strategy-studio",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
        "files": {},
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_json.dumps(diagram, indent=2), encoding="utf-8")

    return diagram


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_cell(cell_id: str) -> LatticeCell:
    """Get a lattice cell by ID."""
    return LatticeCell.parse(cell_id)


def get_build_card(cell_id: str) -> BuildCard:
    """Get a Build Card for a cell ID."""
    cell = LatticeCell.parse(cell_id)
    bms = compute_bms(altitude=cell.altitude)
    return generate_build_card(cell, bms)


def get_all_build_cards() -> list[BuildCard]:
    """Get all 147 Build Cards."""
    return generate_all_build_cards()


def lattice_summary() -> dict[str, Any]:
    """Summary of the full lattice."""
    cards = generate_all_build_cards()
    by_mode: dict[str, int] = {}
    by_altitude: dict[str, int] = {}
    by_diamond: dict[str, int] = {}
    for card in cards:
        by_mode[card.mode] = by_mode.get(card.mode, 0) + 1
        by_altitude[f"L{card.altitude}"] = by_altitude.get(f"L{card.altitude}", 0) + 1
        by_diamond[card.diamond] = by_diamond.get(card.diamond, 0) + 1
    return {
        "total_cells": len(cards),
        "by_mode": by_mode,
        "by_altitude": by_altitude,
        "by_diamond": by_diamond,
        "by_step": {s.value: 21 for s in IQRSQPIStep},
    }
