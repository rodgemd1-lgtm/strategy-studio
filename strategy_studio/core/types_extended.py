"""
Strategy Studio — Extended types for Prediction Studio, Decision Room,
Evidence Engine, Synthesis Pipeline, and Output Studio.

All types are Pydantic BaseModel, fully typed, deterministic.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from strategy_studio.core.types import (
    AuditRow,
    Option,
    ProofPacket,
    QualityResult,
    Synthesis,
    WargameScenario,
)


# ── Prediction Studio ────────────────────────────────────────────────────────

class Scenario(BaseModel):
    """A single scenario for prediction/wargame analysis."""
    id: str
    name: str
    description: str
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    variables: dict[str, float] = Field(default_factory=dict)
    outcomes: dict[str, float] = Field(default_factory=dict)


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation result."""
    variable: str
    iterations: int
    mean: float
    median: float
    std_dev: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    histogram: list[tuple[float, float]] = Field(default_factory=list)  # (bin_center, count)
    scenarios: list[Scenario] = Field(default_factory=list)


class PredictionResult(BaseModel):
    """Complete prediction result combining multiple methods."""
    variable: str
    point_estimate: float
    confidence_interval: tuple[float, float]
    method: str
    monte_carlo: MonteCarloResult | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    base_rate: float | None = None
    calibration_score: float | None = None


class WargameResult(BaseModel):
    """Complete wargame result."""
    scenario_name: str
    actors: list[str] = Field(default_factory=list)
    moves: list[WargameScenario] = Field(default_factory=list)
    equilibrium: str | None = None
    recommended_response: str = ""
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"


# ── Decision Room ────────────────────────────────────────────────────────────

class OptionScore(BaseModel):
    """Scored option with multi-criteria breakdown."""
    option_id: str
    option_title: str
    total_score: float = Field(default=0.0, ge=0.0, le=1.0)
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    weighted_scores: dict[str, float] = Field(default_factory=dict)
    rank: int = 0
    tier: Literal["A", "B", "C", "D"] = "C"
    confidence: Literal["H", "M", "L"] = "M"


class SensitivityResult(BaseModel):
    """Sensitivity analysis result for one parameter."""
    parameter: str
    base_value: float
    low_value: float
    high_value: float
    impact_on_score: float  # change in total score
    elasticity: float  # % change in score / % change in parameter
    is_critical: bool = False


class DecisionMatrix(BaseModel):
    """Complete decision matrix."""
    options: list[OptionScore] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)
    sensitivity: list[SensitivityResult] = Field(default_factory=list)
    recommendation: OptionScore | None = None
    rationale: str = ""


class DecisionRoomResult(BaseModel):
    """Complete Decision Room output."""
    title: str
    decision_matrix: DecisionMatrix
    scenarios_considered: list[Scenario] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    confidence: Literal["H", "M", "L"] = "M"


# ── Evidence Engine ──────────────────────────────────────────────────────────

class SourceScore(BaseModel):
    """Score for a single evidence source."""
    source_uri: str
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    recency: float = Field(default=0.5, ge=0.0, le=1.0)
    corroboration: float = Field(default=0.5, ge=0.0, le=1.0)
    overall: float = Field(default=0.5, ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    """Detected contradiction between evidence sources."""
    evidence_a_id: str
    evidence_b_id: str
    description: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    resolution: str | None = None


class EvidenceGraph(BaseModel):
    """Evidence graph showing relationships between sources."""
    nodes: list[SourceScore] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    clusters: list[list[str]] = Field(default_factory=list)  # groups of corroborating sources
    overall_confidence: Literal["H", "M", "L"] = "M"
    gaps: list[str] = Field(default_factory=list)


# ── Synthesis Pipeline ──────────────────────────────────────────────────────

class ArchetypeResult(BaseModel):
    """Result from a single archetype run."""
    archetype: str
    status: str
    synthesis: Synthesis | None = None
    quality: QualityResult | None = None
    proof: ProofPacket | None = None
    duration_ms: int = 0


class CrossArchetypeConsensus(BaseModel):
    """Consensus across multiple archetype runs."""
    archetype_results: list[ArchetypeResult] = Field(default_factory=list)
    consensus_options: list[Option] = Field(default_factory=list)
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dissenting_options: list[Option] = Field(default_factory=list)
    recommended_synthesis: Synthesis | None = None
    confidence: Literal["H", "M", "L"] = "M"


class MetaAnalysis(BaseModel):
    """Meta-analysis across multiple analyses."""
    analyses: list[Synthesis] = Field(default_factory=list)
    pooled_effect: float = 0.0
    heterogeneity: float = 0.0  # I² statistic
    robustness: float = Field(default=0.5, ge=0.0, le=1.0)
    key_findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


# ── Output Studio ────────────────────────────────────────────────────────────

class ExecutiveSummary(BaseModel):
    """Executive summary output."""
    title: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    key_findings: list[str] = Field(default_factory=list)
    recommendation: str = ""
    confidence: Literal["H", "M", "L"] = "M"
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    appendices: list[str] = Field(default_factory=list)


class BoardSlide(BaseModel):
    """Single board slide."""
    slide_number: int
    title: str
    content: str
    chart_type: Literal["none", "bar", "line", "table", "matrix", "flow"] = "none"
    chart_data: dict[str, Any] = Field(default_factory=dict)
    speaker_notes: str = ""


class BoardDeck(BaseModel):
    """Complete board deck."""
    title: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    slides: list[BoardSlide] = Field(default_factory=list)
    appendix: list[str] = Field(default_factory=list)


class StrategyReport(BaseModel):
    """Complete strategy report."""
    title: str
    executive_summary: ExecutiveSummary
    board_deck: BoardDeck | None = None
    decision_room: DecisionRoomResult | None = None
    prediction_result: PredictionResult | None = None
    wargame_result: WargameResult | None = None
    evidence_graph: EvidenceGraph | None = None
    cross_archetype: CrossArchetypeConsensus | None = None
    meta_analysis: MetaAnalysis | None = None
    proof_packets: list[ProofPacket] = Field(default_factory=list)
    audit_trail: list[AuditRow] = Field(default_factory=list)


# ── Calibration Engine ───────────────────────────────────────────────────────

class CalibrationRecord(BaseModel):
    """Single forecast-vs-actual tracking record."""
    forecast_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    predicted: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    brier_score: float = 0.0
    absolute_error: float = 0.0
    squared_error: float = 0.0
    predicted_probability: float = 0.0
    actual_outcome: float = 0.0
    correct: bool = False
    notes: str = ""


class CalibrationReport(BaseModel):
    """Full calibration report from forecast history."""
    sample_size: int = 0
    brier_score: float = 0.0
    brier_skill_score: float | None = None
    sharpness: float = 0.0
    calibration_curve: list[tuple[float, float, int]] = Field(default_factory=list)
    reliability_diagram: list[dict[str, Any]] = Field(default_factory=list)
    records: list[CalibrationRecord] = Field(default_factory=list)
    reference_brier: float | None = None
    mean_absolute_error: float = 0.0
    mean_squared_error: float = 0.0
    resolution: float = 0.0
    reliability: float = 0.0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))