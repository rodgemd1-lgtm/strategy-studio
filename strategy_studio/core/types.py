"""
Strategy Studio core types.
Frozen, deterministic, no LLM in decision path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Intent keys ──────────────────────────────────────────────────────────────

class IntentKey(str, Enum):
    """Strategy-specific intent keys for deterministic routing."""

    SYNTHESIZE = "synthesize"
    WARGAME = "wargame"
    FORECAST = "forecast"
    COMPETITOR_INTEL = "competitor_intel"
    CLIENT_INTEL = "client_intel"
    FALSIFY = "falsify"
    UNKNOWN = "unknown"


# ── Evidence ─────────────────────────────────────────────────────────────────

class Evidence(BaseModel):
    """A single piece of evidence with provenance."""

    source_uri: str
    content_hash: str
    confidence: Literal["H", "M", "L"]
    citations: list[str] = Field(default_factory=list)


# ── Structured query ─────────────────────────────────────────────────────────

class StructuredQuery(BaseModel):
    """A structured research question."""

    intent_key: str
    question_text: str
    priority: int = Field(default=3, ge=1, le=5)


# ── Option & Synthesis ─────────────────────────────────────────────────────

class Option(BaseModel):
    """A strategic option."""

    id: str
    title: str
    description: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    risks: list[str] = Field(default_factory=list)


class Synthesis(BaseModel):
    """Strategy synthesis result."""

    options: list[Option] = Field(default_factory=list)
    recommendation: Option | None = None
    rationale: str = ""


# ── Wargame ──────────────────────────────────────────────────────────────────

class WargameScenario(BaseModel):
    """Market wargame scenario."""

    actor: str
    move: str
    impact: str
    rig_response: str
    probability: float = Field(default=0.5, ge=0.0, le=1.0)


# ── Forecast ─────────────────────────────────────────────────────────────────

class Forecast(BaseModel):
    """Prediction crux forecast."""

    variable: str
    prediction: float
    confidence_interval: tuple[float, float]
    method: str


# ── GTM Planning ─────────────────────────────────────────────────────────────

class Segment(BaseModel):
    """Go-to-market segment."""

    name: str
    icp: str
    sizing: str
    entry_wedge: str


class Channel(BaseModel):
    """Go-to-market channel."""

    name: str
    tactic: str
    budget: float = Field(default=0.0, ge=0.0)
    expected_cac: float = Field(default=0.0, ge=0.0)


class GTMPlan(BaseModel):
    """Go-to-market plan."""

    segments: list[Segment] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)
    timeline: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)


# ── Falsification ────────────────────────────────────────────────────────────

class FalsificationPacket(BaseModel):
    """Test to falsify a belief."""

    belief: str
    disproof_test: str
    pass_criteria: str
    status: Literal["open", "passed", "failed"] = "open"


# ── Quality ────────────────────────────────────────────────────────────────────

class QualityResult(BaseModel):
    """Quality gate result."""

    passed: bool = False
    checklist: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


# ── Proof ────────────────────────────────────────────────────────────────────

class ProofPacket(BaseModel):
    """Proof packet for external sends."""

    claim: str
    evidence: list[Evidence] = Field(default_factory=list)
    source_weights: dict[str, float] = Field(default_factory=dict)
    confidence: Literal["H", "M", "L"] = "M"


# ── Action ───────────────────────────────────────────────────────────────────

class Action(BaseModel):
    """Executable action."""

    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


# ── Audit ────────────────────────────────────────────────────────────────────

class AuditRow(BaseModel):
    """Append-only audit row."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    archetype: str
    mode: str
    input_hash: str
    output_hash: str
    duration_ms: int = Field(default=0, ge=0)
    status: str


# ── Research pack ────────────────────────────────────────────────────────────

class ResearchPack(BaseModel):
    """Collected research pack."""

    questions: list[StructuredQuery] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


# ── Inbound payload ──────────────────────────────────────────────────────────

class InboundPayload(BaseModel):
    """Any inbound payload to Strategy Studio."""

    raw_text: str
    source: str = Field(default="unknown")
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Source ─────────────────────────────────────────────────────────────────

class Source(BaseModel):
    """A cited source with provenance."""

    uri: str
    title: str = ""
    credibility: Literal["H", "M", "L"] = "M"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Draft ──────────────────────────────────────────────────────────────────

class Draft(BaseModel):
    """An intermediate draft document."""

    content: str
    version: int = Field(default=1, ge=1)
    status: str = "draft"
    review_notes: list[str] = Field(default_factory=list)


# ── QualityGateResult ──────────────────────────────────────────────────────

class QualityGateResult(BaseModel):
    """Result of a quality gate check."""

    gate_name: str
    passed: bool
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    details: str = ""
    violations: list[str] = Field(default_factory=list)


# ── ActionResult ────────────────────────────────────────────────────────────

class ActionResult(BaseModel):
    """Result of executing an action."""

    action: Action
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(default=0, ge=0)
