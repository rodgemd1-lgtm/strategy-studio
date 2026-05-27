"""
Strategy Studio Lattice Type System — Frozen Schema
Canonical home for all lattice types: Level, Diamond, BMSMode, IQRSQPIStep, LatticeCoordinate.
Re-exports shared types from strategy_studio.core.types.
"""
from strategy_studio.core.types import (
    Action,
    ActionResult,
    AuditRow,
    InboundPayload,
    IntentKey,
    ProofPacket,
    QualityGateResult,
    QualityResult,
    ResearchPack,
    Source,
    StructuredQuery,
    Draft,
)

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import re
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Cell ID Regex Patterns
# ─────────────────────────────────────────────

# Strict: L<level>-D<diamond>-A<mode>-<step>
CELL_ID_PATTERN_STRICT = re.compile(
    r"^L([1-7])-D([1-3])-A([1-4])-([A-Z][0-9]?)$"
)

# Old format (pre-Z-axis): L<level>-D<diamond>-<step>
OLD_CELL_ID_PATTERN = re.compile(
    r"^L([1-7])-D([1-3])-([A-Za-z][A-Za-z0-9]+)$"
)


# ─────────────────────────────────────────────
# Level — 7 lattice levels
# ─────────────────────────────────────────────

class Level(str, Enum):
    """Seven lattice levels (L1..L7)."""
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"


# ─────────────────────────────────────────────
# Diamond — with short-name aliases
# ─────────────────────────────────────────────

class Diamond(str, Enum):
    """Three diamonds of the RIG lattice. Short-name aliases D1/D2/D3."""
    D1 = "D1"   # PHYSICAL
    D2 = "D2"   # COGNITIVE
    D3 = "D3"   # NATURE

    @property
    def long_name(self) -> str:
        return {
            Diamond.D1: "PHYSICAL",
            Diamond.D2: "COGNITIVE",
            Diamond.D3: "NATURE",
        }[self]


# ─────────────────────────────────────────────
# BMSMode — with from_score and convenience properties
# ─────────────────────────────────────────────

class BMSMode(str, Enum):
    """Four BMS build modes (Z-axis of the lattice)."""
    A1 = "A1"       # >= 0.75 confidence, no model
    A2 = "A2"        # 0.45-0.74, Python-gated LLM
    A3 = "A3"     # 0.25-0.44, LangGraph bounded
    A4 = "A4"    # < 0.25, free-form multi-agent

    @property
    def threshold_range(self) -> str:
        return {
            BMSMode.A1: ">=0.75",
            BMSMode.A2: "0.45-0.74",
            BMSMode.A3: "0.25-0.44",
            BMSMode.A4: "<0.25",
        }[self]

    @property
    def model_in_decision_path(self) -> bool:
        return {
            BMSMode.A1: False,
            BMSMode.A2: True,
            BMSMode.A3: True,
            BMSMode.A4: True,
        }[self]

    @property
    def description(self) -> str:
        return {
            BMSMode.A1: "PYTHON_ONLY",
            BMSMode.A2: "HYBRID",
            BMSMode.A3: "AGENT_BOUNDED",
            BMSMode.A4: "LLM_AGENT_FREE",
        }[self]

    @property
    def approval_required(self) -> bool:
        return {
            BMSMode.A1: False,
            BMSMode.A2: False,
            BMSMode.A3: True,
            BMSMode.A4: True,
        }[self]

    @classmethod
    def from_score(cls, score: float) -> "BMSMode":
        if score >= 0.75:
            return cls.A1
        elif score >= 0.45:
            return cls.A2
        elif score >= 0.25:
            return cls.A3
        else:
            return cls.A4


# ─────────────────────────────────────────────
# IQRSQPIStep — with sequence() classmethod
# ─────────────────────────────────────────────

class IQRSQPIStep(str, Enum):
    """Seven IQRSQPI process steps."""
    I1 = "I1"    # Intent
    Q1 = "Q1"    # Question
    R = "R"      # Research
    S = "S"      # Solution
    Q2 = "Q2"    # Quality
    P = "P"      # Proof
    I2 = "I2"    # Integrate

    @classmethod
    def sequence(cls) -> list["IQRSQPIStep"]:
        """Return steps in canonical IQRSQPI order."""
        return [cls.I1, cls.Q1, cls.R, cls.S, cls.Q2, cls.P, cls.I2]


# ─────────────────────────────────────────────
# LatticeCoordinate — with cell_id, is_a1, requires_approval, primary_coordinate
# ─────────────────────────────────────────────

class LatticeCoordinate(BaseModel):
    """A single cell in the 7L x 3D x 4BMS lattice."""
    level: Level
    diamond: Diamond
    bms_mode: BMSMode
    step: IQRSQPIStep

    @property
    def cell_id(self) -> str:
        """Full cell ID string, e.g. L2-D1-A1-I1."""
        return f"{self.level.value}-{self.diamond.value}-{self.bms_mode.value}-{self.step.value}"

    @property
    def primary_coordinate(self) -> str:
        """Primary (3-axis) coordinate, e.g. L1-D1-A1."""
        return f"{self.level.value}-{self.diamond.value}-{self.bms_mode.value}"

    @property
    def is_a1(self) -> bool:
        """True if BMS mode is A1 (PYTHON_ONLY)."""
        return self.bms_mode == BMSMode.A1

    @property
    def requires_approval(self) -> bool:
        """True if archetype requires human signoff (A3, A4)."""
        return self.bms_mode.approval_required

    def __str__(self) -> str:
        return self.cell_id


# Re-export lightweight coordinate
@dataclass(frozen=True)
class LatticeCoord:
    """Lightweight lattice coordinate (no bms_mode required)."""
    level: Level
    diamond: Diamond
    step: IQRSQPIStep

    def __str__(self) -> str:
        return f"{self.level.value}-{self.diamond.value}-{self.step.value}"

    @property
    def cell_id(self) -> str:
        return str(self)


LATTICE_VERSION = "2.0"

# BuildCard lives in phronema — lazy import to avoid circular dependency
def __getattr__(name: str):
    if name == "BuildCard":
        from strategy_studio.phronema.build_card_generator import BuildCard
        return BuildCard
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Action", "ActionResult", "AuditRow", "BuildCard", "BMSMode",
    "Diamond", "Draft", "InboundPayload", "IntentKey", "IQRSQPIStep",
    "Level", "LatticeCoord", "LatticeCoordinate", "ProofPacket",
    "QualityGateResult", "QualityResult", "ResearchPack", "Source",
    "StructuredQuery", "LATTICE_VERSION",
]