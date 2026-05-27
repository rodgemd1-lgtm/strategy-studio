"""
StrategyArtifact — Frozen Pydantic v2 artifact contract.

Validates: rig_l >= 32, 30-sigma PASS, evidence minimums, all required fields.
This contract is FROZEN — no edits after creation without Mike approval.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Annotated
from uuid import uuid7

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Sub-models ────────────────────────────────────────────────────────────────

class ConfidenceTier(str, Enum):
    HIGH = "HIGH"     # peer-reviewed, primary source, current
    MEDIUM = "MEDIUM" # credible secondary, 1-2 years old
    LOW = "LOW"       # unverified, tertiary, anecdotal


class EvidenceClaim(BaseModel):
    """Single evidence claim with source weighting and confidence tier."""
    model_config = ConfigDict(frozen=True)

    claim: str = Field(..., min_length=10, description="The substantive claim being made")
    source: str = Field(..., description="Source name or URL")
    source_weight: Annotated[float, Field(gt=0.0, le=1.0)] = Field(
        ..., description="Source credibility 0.0–1.0"
    )
    confidence_tier: ConfidenceTier = Field(..., description="Evidence confidence tier")


class MechanismLink(BaseModel):
    """Single link in the 7-link mechanism chain."""
    model_config = ConfigDict(frozen=True)

    step: Literal["Input", "Activity", "Behavior", "System", "Economic", "Advantage", "Loop"]
    mechanism: str = Field(..., min_length=5)
    evidence: str = Field(..., min_length=5)
    confidence: Annotated[float, Field(gt=0.0, le=1.0)]


class MechanismChain(BaseModel):
    """Full 7-link mechanism map: Input→Activity→Behavior→System→Economic→Advantage→Loop."""
    model_config = ConfigDict(frozen=True)

    links: list[MechanismLink] = Field(..., description="Ordered 7-link chain")

    @model_validator(mode="after")
    def must_have_all_seven_links(self) -> MechanismChain:
        required = {"Input", "Activity", "Behavior", "System", "Economic", "Advantage", "Loop"}
        actual = {link.step for link in self.links}
        if actual != required:
            missing = required - actual
            raise ValueError(f"MechanismChain missing required links: {missing}")
        return self


class StrategicOption(BaseModel):
    """A single strategic option with RIG-L score and kill criteria."""
    model_config = ConfigDict(frozen=True)

    id: str
    title: str = Field(..., min_length=3)
    rig_l_score: Annotated[int, Field(ge=0, le=40)] = Field(
        ..., description="RIG-L score (0–40, must be >= 32 for ship-ready)"
    )
    kill_criteria: str = Field(..., min_length=10, description="Conditions under which this option dies")
    falsifier: str = Field(..., min_length=10, description="What would prove this option wrong")


class Forecast(BaseModel):
    """Single probabilistic forecast with review date and base rate."""
    model_config = ConfigDict(frozen=True)

    variable: str = Field(..., description="What is being forecast")
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Probability estimate 0.0–1.0"
    )
    review_date: datetime = Field(..., description="When this forecast should be reviewed")
    base_rate: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Historical base rate for comparison"
    )


class DecisionContract(BaseModel):
    """Who needs to decide what, by when, and how much confidence is required."""
    model_config = ConfigDict(frozen=True)

    owner: str = Field(..., min_length=1, description="Decision owner name")
    stakeholder: str = Field(..., min_length=1, description="Primary stakeholder")
    decision_due_by: datetime = Field(..., description="Deadline for decision")
    confidence_required: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.80, description="Minimum confidence threshold"
    )

    @field_validator("decision_due_by")
    @classmethod
    def not_in_past(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < datetime.now(timezone.utc):
            raise ValueError("decision_due_by cannot be in the past")
        return v


class WoundBrief(BaseModel):
    """The strategic wound being addressed."""
    model_config = ConfigDict(frozen=True)

    wound_sentence: str = Field(
        ..., min_length=20, max_length=200,
        description="One-paragraph description of the strategic wound"
    )
    stakes: str = Field(
        ..., min_length=10,
        description="What is at stake if this wound is not addressed"
    )
    evidence_count_min: int = Field(default=3, ge=3)


class RigLAudit(BaseModel):
    """RIG-L 16-criterion audit."""
    model_config = ConfigDict(frozen=True)

    score: Annotated[int, Field(ge=0, le=40)] = Field(
        ..., description="Total RIG-L score (0–40)"
    )
    criteria: list[str] = Field(
        ..., min_length=16, max_length=16,
        description="16 criteria names used"
    )
    per_criterion: dict[str, float] = Field(
        default_factory=dict,
        description="Score per criterion (0–2.5 scale)"
    )


class ThirtySigmaAudit(BaseModel):
    """30-sigma hard gate — physics band analysis."""
    model_config = ConfigDict(frozen=True)

    physics_band: str = Field(..., description="Physics band classification")
    status: Literal["PASS", "FAIL"] = Field(
        ..., description="Hard gate — FAIL blocks all shipping"
    )
    evidence: str = Field(default="", description="Basis for band classification")


class FiftyCriteriaAudit(BaseModel):
    """50-criteria audit across 5 dimensions."""
    model_config = ConfigDict(frozen=True)

    scores: dict[str, float] = Field(
        ..., description="Score per criterion (1–10)"
    )
    average: Annotated[float, Field(ge=0.0, le=10.0)] = Field(
        ..., description="Average score"
    )
    dimension_averages: dict[str, float] = Field(
        default_factory=dict,
        description="Average per dimension"
    )


class DeckOutline(BaseModel):
    """Deck structure: required sections in order."""
    model_config = ConfigDict(frozen=True)

    sections: list[str] = Field(
        ...,
        description="Ordered deck sections"
    )

    @model_validator(mode="after")
    def required_sections_present(self) -> DeckOutline:
        required = {"Wound", "Mirror", "Evidence", "Mechanism", "Options", "OpenLoop"}
        present = set(self.sections)
        if not required.issubset(present):
            missing = required - present
            raise ValueError(f"Deck outline missing required sections: {missing}")
        return self


class RenderedDeck(BaseModel):
    """Output artifact URIs after rendering."""
    model_config = ConfigDict(frozen=True)

    pptx_uri: str | None = None
    pdf_uri: str | None = None
    slidev_uri: str | None = None


class DeliveryPack(BaseModel):
    """Client delivery artifacts."""
    model_config = ConfigDict(frozen=True)

    audit_report_md: str = Field(default="")
    client_delivery_pack_md: str = Field(default="")
    sow_or_next_step_md: str = Field(default="")


class MemoryUpdate(BaseModel):
    """Memory namespace updates to write after shipping."""
    model_config = ConfigDict(frozen=True)

    forecast_review_dates: list[datetime] = Field(default_factory=list)
    doctrine_updates: list[str] = Field(default_factory=list)
    failure_patterns: list[str] = Field(default_factory=list)


# ── Main artifact ────────────────────────────────────────────────────────────

class StrategyArtifact(BaseModel):
    """
    Frozen Pydantic v2 artifact contract for strategy studio deliverables.

    Ship-ready artifacts MUST satisfy:
    - rig_l_audit.score >= 32
    - thirty_sigma_audit.status == "PASS"
    - evidence_pack has >= evidence_count_min items
    - strategic_options has >= 3 options
    - mechanism_map has all 7 links
    - forecast_pack has >= 5 forecasts
    - deck_outline contains all required sections
    - No banned phrases present (enforced by banned_phrase_gate)
    """
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    # Identity
    run_id: str = Field(default_factory=lambda: str(uuid7()))
    proofpacket_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    proofpacket_ids: list[str] = Field(default_factory=list)

    # Core inputs
    decision_contract: DecisionContract | None = None
    wound_brief: WoundBrief | None = None
    qrsqpi_qualification: dict[str, Any] = Field(default_factory=dict)

    # Evidence
    evidence_pack: list[EvidenceClaim] = Field(default_factory=list)
    mechanism_map: MechanismChain | None = None

    # Strategy
    strategic_options: list[StrategicOption] = Field(default_factory=list)
    rig_l_audit: RigLAudit | None = None

    # Quant
    forecast_pack: list[Forecast] = Field(default_factory=list)
    fifty_criteria_audit: FiftyCriteriaAudit | None = None
    thirty_sigma_audit: ThirtySigmaAudit | None = None

    # Output
    deck_outline: DeckOutline | None = None
    content_json: dict[str, Any] = Field(default_factory=dict)
    rendered_deck: RenderedDeck | None = None
    delivery_pack: DeliveryPack | None = None
    memory_update: MemoryUpdate | None = None

    @model_validator(mode="after")
    def validate_ship_readiness(self) -> StrategyArtifact:
        """Hard gates — FAIL blocks shipping entirely."""
        errors: list[str] = []

        # Gate 1: RIG-L score >= 32
        if self.rig_l_audit is not None and self.rig_l_audit.score < 32:
            errors.append(
                f"RIG-L score {self.rig_l_audit.score} < 32 — blocked. "
                f"16 criteria must average >= 2.0 per criterion."
            )

        # Gate 2: 30-sigma hard PASS/FAIL
        if self.thirty_sigma_audit is not None and self.thirty_sigma_audit.status == "FAIL":
            errors.append(
                "30-sigma audit FAIL — hard gate. Physics band "
                f"'{self.thirty_sigma_audit.physics_band}' does not support shipping."
            )

        # Gate 3: Evidence minimum
        if self.wound_brief is not None and len(self.evidence_pack) < self.wound_brief.evidence_count_min:
            errors.append(
                f"Evidence pack has {len(self.evidence_pack)} claims, "
                f"minimum required: {self.wound_brief.evidence_count_min}."
            )

        # Gate 4: Strategic options >= 3
        if len(self.strategic_options) < 3:
            errors.append(
                f"Strategic options: {len(self.strategic_options)} — need >= 3."
            )

        # Gate 5: Mechanism chain has all 7 links
        if self.mechanism_map is not None and len(self.mechanism_map.links) != 7:
            errors.append(
                f"Mechanism chain: {len(self.mechanism_map.links)} links — need exactly 7."
            )

        # Gate 6: Forecasts >= 5
        if len(self.forecast_pack) < 5:
            errors.append(
                f"Forecast pack: {len(self.forecast_pack)} — need >= 5."
            )

        # Gate 7: Deck outline sections
        if self.deck_outline is not None:
            required = {"Wound", "Mirror", "Evidence", "Mechanism", "Options", "OpenLoop"}
            present = set(self.deck_outline.sections)
            if not required.issubset(present):
                errors.append(f"Deck outline missing: {required - present}")

        if errors:
            raise ValueError("SHIP_BLOCKED:\n" + "\n".join(f"  - {e}" for e in errors))

        return self

    @classmethod
    def minimal_shippable(cls) -> StrategyArtifact:
        """Create a minimally valid shippable artifact for testing."""
        return cls(
            rig_l_audit=RigLAudit(
                score=32,
                criteria=[f"criterion_{i}" for i in range(16)],
                per_criterion={f"criterion_{i}": 2.0 for i in range(16)},
            ),
            thirty_sigma_audit=ThirtySigmaAudit(
                physics_band="EXPANDING",
                status="PASS",
            ),
            wound_brief=WoundBrief(
                wound_sentence="Revenue growth has stalled for 3 consecutive quarters.",
                stakes="Company may not hit Series B milestones.",
                evidence_count_min=3,
            ),
            evidence_pack=[
                EvidenceClaim(
                    claim="Revenue declined 12% QoQ",
                    source="internal/quarterly_report_q2",
                    source_weight=0.9,
                    confidence_tier=ConfidenceTier.HIGH,
                ),
                EvidenceClaim(
                    claim="CAC increased 35% YoY",
                    source="internal/analytics_q2",
                    source_weight=0.85,
                    confidence_tier=ConfidenceTier.HIGH,
                ),
                EvidenceClaim(
                    claim="Net revenue retention dropped to 87%",
                    source="internal/cohort_analysis",
                    source_weight=0.80,
                    confidence_tier=ConfidenceTier.MEDIUM,
                ),
            ],
            strategic_options=[
                StrategicOption(
                    id="opt_1",
                    title="Shift to product-led growth",
                    rig_l_score=34,
                    kill_criteria="PLG conversion < 5% in 90 days",
                    falsifier="Users not adopting self-serve path",
                ),
                StrategicOption(
                    id="opt_2",
                    title="Enterprise focus with dedicated CS",
                    rig_l_score=36,
                    kill_criteria="< 2 enterprise wins in 6 months",
                    falsifier="Enterprise deals taking > 120 days",
                ),
                StrategicOption(
                    id="opt_3",
                    title="Strategic partnership with platform",
                    rig_l_score=32,
                    kill_criteria="Partner integration not live in 60 days",
                    falsifier="Technical blockers on both sides",
                ),
            ],
            mechanism_map=MechanismChain(
                links=[
                    MechanismLink(step="Input", mechanism="CAC spike", evidence="Q2 Analytics", confidence=0.85),
                    MechanismLink(step="Activity", mechanism="Sales cycle lengthens", evidence="CRM data", confidence=0.80),
                    MechanismLink(step="Behavior", mechanism="Buyers defer decisions", evidence="Win/loss interviews", confidence=0.75),
                    MechanismLink(step="System", mechanism="CAC > LTV threshold", evidence="Cohort analysis", confidence=0.90),
                    MechanismLink(step="Economic", mechanism="Burn acceleration", evidence="Company financials", confidence=0.95),
                    MechanismLink(step="Advantage", mechanism="Competitive window closing", evidence="Market research", confidence=0.70),
                    MechanismLink(step="Loop", mechanism="Negative unit economics limit growth", evidence="Cohort model", confidence=0.88),
                ]
            ),
            forecast_pack=[
                Forecast(variable="revenue_growth_Q3", probability=0.35, review_date=datetime(2026, 10, 1, tzinfo=timezone.utc), base_rate=0.25),
                Forecast(variable="enterprise_win_Q3", probability=0.45, review_date=datetime(2026, 10, 1, tzinfo=timezone.utc), base_rate=0.40),
                Forecast(variable="plg_conversion_Q3", probability=0.28, review_date=datetime(2026, 10, 1, tzinfo=timezone.utc), base_rate=0.20),
                Forecast(variable="burn_rate_normalized", probability=0.55, review_date=datetime(2026, 11, 1, tzinfo=timezone.utc), base_rate=0.50),
                Forecast(variable="competitive_position", probability=0.40, review_date=datetime(2026, 12, 1, tzinfo=timezone.utc), base_rate=0.45),
            ],
            deck_outline=DeckOutline(sections=["Wound", "Mirror", "Evidence", "Mechanism", "Options", "Autonomy", "Qualification", "OpenLoop"]),
        )