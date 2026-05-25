"""Input schema for strategy teaser generation.

Codex feeds one TeaserInput per prospect (2000 total).
Every field is required — UNKNOWN values must be marked explicitly so the
generator can substitute the falsification gate language.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class TeaserInput(BaseModel):
    """One prospect → one teaser. All evidence-cited fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # ── Identity ──────────────────────────────────────────────────────────
    prospect_id: str = Field(..., description="Stable slug, e.g. 'hed-inc'")
    company_name: str = Field(..., description="Hydro Electronic Devices, Inc.")
    company_short: str = Field(..., description="HED")
    employees: int = Field(..., ge=1, le=10_000_000)
    revenue_usd_m: float = Field(..., ge=0, description="Annual revenue in $M")
    years_in_business: int = Field(..., ge=0)
    headquarters: str = Field(..., description="Hartford, WI")
    industry: str = Field(..., description="Rugged CAN-based vehicle controls")
    industry_short: str = Field(..., description="vehicle controls")

    # ── Wound (what they don't know they're losing) ──────────────────────
    wound_months: int = Field(..., ge=3, le=60, description="Months until lockout")
    wound_channel: str = Field(..., description="defense channel / enterprise procurement")
    wound_trigger: str = Field(..., description="CMMC Level 2 mandatory Nov 10 2026")

    # ── Mirror (what RIG sees that they haven't named) ────────────────────
    capability_count: int = Field(..., ge=2, le=20)
    capability_names: list[str] = Field(..., min_length=2, max_length=10)
    capability_gap: str = Field(..., description="None productized as intelligence yet")

    # ── Named mechanism (specific to their industry) ──────────────────────
    mechanism_name: str = Field(..., description="NVIS Gate, Helios Curve, etc.")
    mechanism_description: str = Field(..., description="One-sentence what it does")

    # ── Three structural advantages (unrecognized) ────────────────────────
    advantages: list[str] = Field(..., min_length=3, max_length=3)

    # ── Comparable transaction ────────────────────────────────────────────
    comparable_company: str = Field(..., description="Helios Technologies")
    comparable_year_start: int = Field(..., ge=1990, le=2025)
    comparable_year_end: int = Field(..., ge=2000, le=2030)
    comparable_revenue_start_m: float = Field(..., ge=0)
    comparable_revenue_end_m: float = Field(..., ge=0)
    comparable_segment_growth_m: float = Field(..., ge=0, description="New segment value $M")

    # ── Three category engines ────────────────────────────────────────────
    engines: list["EngineInput"] = Field(..., min_length=3, max_length=3)

    # ── Competitive threats (3 tiers) ─────────────────────────────────────
    threats: list["ThreatInput"] = Field(..., min_length=3, max_length=3)

    # ── Three disqualifiers ───────────────────────────────────────────────
    disqualifiers: list[str] = Field(..., min_length=3, max_length=3)

    # ── Site cloning metadata ─────────────────────────────────────────────
    cloned_site_url: str = Field(..., description="https://hed-forge.vercel.app")
    primary_color: str = Field(default="#1A56DB", description="Hex, prospect brand")
    secondary_color: str = Field(default="#0F172A", description="Hex, dark accent")

    # ── Contact wedge ─────────────────────────────────────────────────────
    contact_name: str = Field(..., description="Gijs Zomer")
    contact_role: str = Field(..., description="VP of Operations")

    # ── Confidence audit ──────────────────────────────────────────────────
    evidence_sources: list[str] = Field(..., min_length=2, description="Source weights cited")
    confidence: Literal["H", "M", "L"] = Field(default="M")


class EngineInput(BaseModel):
    """One product line → one category engine."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Control Modules")
    sigma_label: str = Field(..., description="+5σ")
    flywheel_type: Literal["data", "capability", "adoption"] = Field(...)
    flywheel_loop: str = Field(..., description="CL-4002 drift → inference → fleet → revenue")
    target_revenue_m: float = Field(..., ge=0)


class ThreatInput(BaseModel):
    """One competitive threat tier."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Parker Hannifin")
    tier: Literal["Tier 1", "Tier 2", "Tier 3"] = Field(...)
    horizon_months: str = Field(..., description="6-12")
    key_fact: str = Field(..., max_length=120)
    source_weight: float = Field(..., ge=0, le=1, description="SW score 0.0-1.0")


TeaserInput.model_rebuild()
