"""Deterministic RIG strategy briefs from validated teaser inputs.

This is A1-only: no model calls, no external sends, and no private data export.
The strategy layer turns each validated ``TeaserInput`` into an operational
account plan that Mike/RIG can use after the teaser bundle is generated.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from strategy_studio.teaser.schema import TeaserInput


Audience = Literal["RIG and Mike Rodgers"]
PriorityTier = Literal["A", "B", "C"]
CadenceDay = Literal[0, 2, 5, 9, 14]


class ChannelMove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str
    objective: str
    message: str
    asset: str
    success_signal: str


class OutboundStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: CadenceDay
    channel: str
    subject_or_hook: str
    body: str
    required_asset: str
    proof_to_attach: str


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    window: str
    objective: str
    work: list[str] = Field(min_length=2, max_length=6)
    evidence_needed: list[str] = Field(min_length=1, max_length=5)
    exit_criteria: str


class StrategyBrief(BaseModel):
    """One complete strategy brief for one prospect."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: str
    company_name: str
    generated_for: Audience = "RIG and Mike Rodgers"
    generated_at: str
    source_hash: str
    segment: str
    priority_tier: PriorityTier
    priority_score: float = Field(ge=0.0, le=100.0)
    estimated_contract_value_usd: int = Field(ge=0)
    account_thesis: str
    wedge_offer: str
    named_mechanism: str
    system_name: str
    system_layers: list[str] = Field(min_length=5, max_length=6)
    buyer_persona: str
    trigger_timeline: str
    firm_snapshot: str
    situation: str
    examination: str
    prediction_scorecard: dict[str, str]
    engagement_terms: dict[str, str]
    channel_strategy: list[ChannelMove] = Field(min_length=4, max_length=6)
    outbound_sequence: list[OutboundStep] = Field(min_length=5, max_length=5)
    delivery_plan: list[PlanStep] = Field(min_length=3, max_length=3)
    proposal_outline: list[str] = Field(min_length=6, max_length=10)
    discovery_questions: list[str] = Field(min_length=6, max_length=10)
    intelligence_to_collect: list[str] = Field(min_length=6, max_length=12)
    proof_assets: list[str] = Field(min_length=4, max_length=8)
    competitor_watchlist: list[str] = Field(min_length=3, max_length=3)
    conversion_prediction: str
    success_metrics: list[str] = Field(min_length=5, max_length=8)
    risk_register: list[str] = Field(min_length=3, max_length=8)
    stop_conditions: list[str] = Field(min_length=3, max_length=3)
    next_actions: list[str] = Field(min_length=5, max_length=8)
    evidence_sources: list[str] = Field(min_length=2)
    confidence: Literal["H", "M", "L"]


SEGMENT_PLAYS = {
    "portfolio ops": {
        "segment": "Private equity / portfolio operations",
        "offer": "Portfolio AI Value-Creation Sprint",
        "hook": "portfolio-wide margin proof",
        "asset": "portfolio value-creation teardown",
        "buyer": "operating partner, value creation lead, or founder-CEO sponsor",
    },
    "service ops": {
        "segment": "Local and regional service operators",
        "offer": "Field Ops AI Growth System",
        "hook": "dispatch, quoting, and follow-up leakage",
        "asset": "field ops leakage map",
        "buyer": "owner, COO, GM, or operations leader",
    },
    "patient ops": {
        "segment": "Healthcare and orthopedic operators",
        "offer": "Patient Conversion and Capacity System",
        "hook": "referral, scheduling, and patient reactivation gaps",
        "asset": "patient journey revenue map",
        "buyer": "practice administrator, COO, growth lead, or physician-owner",
    },
    "legal ops": {
        "segment": "Law firms and legal operations",
        "offer": "Matter Intake and Authority Engine",
        "hook": "intake-to-retainer conversion leakage",
        "asset": "matter intake and authority teardown",
        "buyer": "managing partner, COO, practice chair, or growth director",
    },
    "medspa growth": {
        "segment": "Med spa and aesthetics growth",
        "offer": "Aesthetic Demand and Retention System",
        "hook": "consultation, rebooking, and treatment-plan leakage",
        "asset": "medspa revenue-loop teardown",
        "buyer": "owner, medical director, GM, or growth operator",
    },
    "CPA advisory": {
        "segment": "CPA and advisory firms",
        "offer": "Advisory Capacity and Client Intelligence System",
        "hook": "tax-season knowledge trapped outside advisory products",
        "asset": "advisory revenue expansion map",
        "buyer": "managing partner, advisory lead, COO, or growth partner",
    },
}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug_to_segment(industry_short: str) -> dict[str, str]:
    return SEGMENT_PLAYS.get(
        industry_short,
        {
            "segment": industry_short or "RIG priority account",
            "offer": "AI Strategy and Automation Sprint",
            "hook": "unpriced operating intelligence",
            "asset": "operating intelligence teardown",
            "buyer": "owner, COO, VP operations, or strategy sponsor",
        },
    )


def _stable_hash(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _contract_value(t: TeaserInput) -> int:
    revenue_component = t.revenue_usd_m * 1_000_000 * 0.012
    employee_component = t.employees * 1_500
    wound_multiplier = 1.35 if t.wound_months <= 12 else 1.0
    raw = max(50_000, min(450_000, (revenue_component + employee_component) * wound_multiplier))
    return int(round(raw / 5_000) * 5_000)


def _priority_score(t: TeaserInput) -> float:
    confidence = {"H": 18, "M": 10, "L": 0}[t.confidence]
    urgency = max(0, 24 - t.wound_months) * 1.1
    size = min(24, (t.revenue_usd_m / 8) + (t.employees / 80))
    engine_value = min(22, sum(e.target_revenue_m for e in t.engines) / 8)
    contact = 8 if any(term in t.contact_role.lower() for term in ["owner", "founder", "ceo", "coo", "partner", "operations", "strategy"]) else 3
    return round(min(100, confidence + urgency + size + engine_value + contact + 8), 1)


def _priority_tier(score: float) -> PriorityTier:
    if score >= 72:
        return "A"
    if score >= 55:
        return "B"
    return "C"


def _clean_sentence(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return value if value.endswith((".", "?", "!")) else value + "."


def _system_name(t: TeaserInput) -> str:
    first = re.sub(r"[^A-Za-z0-9]", "", t.company_short or t.company_name.split()[0]).upper()
    if not first:
        first = "RIG"
    suffix_by_segment = {
        "portfolio ops": "VALUE",
        "service ops": "FIELD",
        "patient ops": "CARE",
        "legal ops": "MATTER",
        "medspa growth": "AURA",
        "CPA advisory": "LEDGER",
    }
    return f"{first} {suffix_by_segment.get(t.industry_short, 'FORGE')}"


def _system_layers(t: TeaserInput, system_name: str) -> list[str]:
    first_engine = t.engines[0].name
    second_engine = t.engines[1].name
    third_engine = t.engines[2].name
    return [
        f"{system_name} Solo — personal AI copilot for {t.contact_role}",
        f"{system_name} Team — shared operating memory for the leadership team",
        f"{system_name} Vault — source-of-truth knowledge graph for {', '.join(t.capability_names[:3])}",
        f"{system_name} Edge — first production workflow around {first_engine}",
        f"{system_name} Sight — competitive watchtower for {', '.join(x.name for x in t.threats[:2])}",
        f"{system_name} Blueprint — 90-day expansion path into {second_engine} and {third_engine}",
    ]


def _engagement_terms(contract_value: int) -> dict[str, str]:
    activation = max(95_000, contract_value)
    transformation = max(185_000, min(1_080_000, int(round(activation * 3.0 / 5_000) * 5_000)))
    retainer = max(9_500, min(35_000, int(round(activation / 12 / 500) * 500)))
    return {
        "Diagnostic": "2 weeks · $14,000 fixed · teardown, falsification, GO/NO-GO",
        "Activation": f"3 months · ${activation:,} estimated · foundation, copilot, first production workflow, Day-90 ROI",
        "Transformation": f"9-18 months · ${transformation:,}+ · full system, knowledge graph, operating cadence, handoff",
        "Retainer": f"${retainer:,}/month estimated during active build; taper during handoff",
    }


def _prediction_scorecard(t: TeaserInput, score: float) -> dict[str, str]:
    quality = min(96, max(75, int(round(score + 12))))
    deviation = 3.2 + min(2.8, max(0.0, (score - 55) / 20))
    success = min(0.89, max(0.64, score / 100))
    consensus = min(0.86, max(0.62, (score + 5) / 100))
    return {
        "MiroFish quality": f"{quality}/100",
        "MilkyWay deviation": f"{deviation:.1f}σ",
        "MiroShark success probability": f"{success:.2f}",
        "Swarm consensus": f"{consensus:.2f}",
        "Primary risk": t.disqualifiers[0],
    }


def _proof_asset(t: TeaserInput, play: dict[str, str]) -> list[str]:
    return [
        f"Cloned-site teaser at {t.cloned_site_url}",
        f"{play['asset'].title()} for {t.company_short}",
        f"{t.mechanism_name} one-page mechanism map",
        f"{t.wound_months}-month {t.wound_channel} lockout timeline",
        f"Three-engine revenue case: {', '.join(e.name for e in t.engines)}",
        f"Competitive threat ladder: {', '.join(x.name for x in t.threats)}",
    ]


def _first_source(t: TeaserInput) -> str:
    return t.evidence_sources[0] if t.evidence_sources else "Strategy Studio evidence ledger"


def build_strategy_brief(record: dict) -> StrategyBrief:
    """Build one deterministic RIG account strategy from a teaser record."""
    t = TeaserInput.model_validate(record)
    play = _slug_to_segment(t.industry_short)
    score = _priority_score(t)
    tier = _priority_tier(score)
    contract_value = _contract_value(t)
    top_engine = max(t.engines, key=lambda e: e.target_revenue_m)
    source = _first_source(t)
    system_name = _system_name(t)
    system_layers = _system_layers(t, system_name)
    engagement_terms = _engagement_terms(contract_value)
    prediction_scorecard = _prediction_scorecard(t, score)

    account_thesis = (
        f"{t.company_name} is a {t.employees}-employee {play['segment'].lower()} account with "
        f"an estimated ${t.revenue_usd_m:.1f}M revenue base and a {t.wound_months}-month trigger around "
        f"{t.wound_channel}. RIG should lead with {t.mechanism_name}, not generic AI consulting."
    )
    wedge_offer = (
        f"{play['offer']}: turn {', '.join(t.capability_names[:3])} into a proof-backed operating system "
        f"anchored on {top_engine.name} and a first quantified win inside 30 days."
    )
    buyer_persona = (
        f"Primary buyer is {t.contact_role}: sell the operational delta, not tools. "
        f"Assume {play['buyer']} economics and make the first ask a teardown review."
    )
    firm_snapshot = (
        f"{t.company_name} is based in {t.headquarters}, has {t.employees} employees, "
        f"estimated ${t.revenue_usd_m:.1f}M revenue, and {t.years_in_business} years in business. "
        f"It operates in {t.industry}."
    )
    situation = (
        f"{t.contact_role} is the highest-leverage entry point. The company has visible capabilities "
        f"({', '.join(t.capability_names[:4])}) but has not turned them into a named operating substrate. "
        f"The trigger is {t.wound_trigger}."
    )
    examination = (
        f"Strategy Studio mapped the public capability set, three category engines, three threats, "
        f"and a comparable transaction ({t.comparable_company}, {t.comparable_year_start}-{t.comparable_year_end}). "
        f"The strongest wedge is {top_engine.name}: {top_engine.flywheel_loop}."
    )

    channel_strategy = [
        ChannelMove(
            channel="personal email",
            objective="Earn a reply from the named buyer without calendar-link softness.",
            message=f"Lead with the {t.wound_months}-month {t.wound_channel} wound and one falsifiable line from the teaser.",
            asset=f"{t.cloned_site_url} plus {play['asset']}",
            success_signal="Reply challenges the wound, asks for the password, or forwards internally.",
        ),
        ChannelMove(
            channel="LinkedIn",
            objective="Create recognition before or after email.",
            message=f"Post/comment angle: {t.company_short} already has the ingredients for {t.mechanism_name}.",
            asset=f"{t.mechanism_name} mechanism map",
            success_signal="Profile view, connection acceptance, or reply from the target role.",
        ),
        ChannelMove(
            channel="cloned-site teaser",
            objective="Make the account feel seen before any sales call.",
            message=f"Show the gap between their current capabilities and {t.mechanism_name}.",
            asset=t.cloned_site_url,
            success_signal="Page visit, password request, or mention of a specific section.",
        ),
        ChannelMove(
            channel="paid retargeting seed",
            objective="Reinforce the same wedge across search/social once audience is lawful and approved.",
            message=f"{play['hook'].capitalize()} is visible before competitors name it.",
            asset=f"{play['asset']} creative variant",
            success_signal="Retargeted click-through or branded search lift.",
        ),
        ChannelMove(
            channel="phone/direct",
            objective="Use only after digital proof has created context.",
            message=f"Ask who owns {t.wound_channel} risk and {top_engine.name} economics.",
            asset="two-sentence operator brief",
            success_signal="Routed to buyer or verified no-go.",
        ),
    ]

    outbound_sequence = [
        OutboundStep(
            day=0,
            channel="email",
            subject_or_hook=f"{t.company_short}: {t.wound_months} months on {t.wound_channel}",
            body=(
                f"{t.contact_name} - I mapped {t.company_name}'s public capabilities against the "
                f"{t.wound_channel} shift. The uncomfortable part: {t.capability_gap} "
                f"The teaser shows how {t.mechanism_name} turns {top_engine.name} into the first proof engine."
            ),
            required_asset=t.cloned_site_url,
            proof_to_attach=source,
        ),
        OutboundStep(
            day=2,
            channel="LinkedIn",
            subject_or_hook=f"{t.mechanism_name} angle",
            body=(
                f"Short note: {t.company_short} looks closer to a category engine than a services/tools story. "
                f"The gap is packaging {', '.join(t.capability_names[:2])} as compounding intelligence."
            ),
            required_asset=f"{t.mechanism_name} one-page map",
            proof_to_attach=t.evidence_sources[min(1, len(t.evidence_sources) - 1)],
        ),
        OutboundStep(
            day=5,
            channel="email",
            subject_or_hook=f"Three engines, one first move",
            body=(
                f"The first move I would test is {top_engine.name}: {top_engine.flywheel_loop}. "
                f"If that does not produce a measurable win, the broader strategy should stop."
            ),
            required_asset="three-engine revenue case",
            proof_to_attach=source,
        ),
        OutboundStep(
            day=9,
            channel="email",
            subject_or_hook=f"Reasons this is a no-go",
            body=(
                f"Three reasons RIG would walk away: {t.disqualifiers[0]} "
                f"{t.disqualifiers[1]} {t.disqualifiers[2]}"
            ),
            required_asset="disqualifier memo",
            proof_to_attach="Strategy Studio falsification packet",
        ),
        OutboundStep(
            day=14,
            channel="direct phone / final email",
            subject_or_hook="Close the loop",
            body=(
                f"If {t.wound_channel} is already owned internally, this is a pass. "
                f"If not, the next move is a 30-minute teardown of {top_engine.name} economics and proof gaps."
            ),
            required_asset="operator teardown agenda",
            proof_to_attach="Strategy Studio proof packet",
        ),
    ]

    delivery_plan = [
        PlanStep(
            window="Days 1-10",
            objective="Prove the wound and quantify the first revenue or margin pool.",
            work=[
                f"Audit {t.capability_names[0]} and {t.capability_names[1]} against the public website and teaser evidence.",
                f"Map {t.wound_channel} ownership, current process, and buying trigger.",
                f"Build one dashboard around {top_engine.name} leakage and conversion.",
            ],
            evidence_needed=[
                "Current funnel/process metrics",
                "CRM or intake sample",
                "Leadership owner for implementation",
            ],
            exit_criteria="One quantified first-win model and one named internal sponsor.",
        ),
        PlanStep(
            window="Days 11-30",
            objective="Ship the first proof asset and operator workflow.",
            work=[
                f"Build the {t.mechanism_name} pilot around {top_engine.name}.",
                "Install measurement: baseline, leading indicator, lagging indicator, and owner.",
                "Write the internal executive memo that explains why this beats tool adoption.",
            ],
            evidence_needed=[
                "Before/after operating metric",
                "User/operator feedback",
                "Cost-to-serve or revenue-lift evidence",
            ],
            exit_criteria="Pilot produces a decision-grade proof packet or fails explicitly.",
        ),
        PlanStep(
            window="Days 31-90",
            objective="Turn the pilot into a repeatable operating system.",
            work=[
                f"Expand from {top_engine.name} into {t.engines[1].name} and {t.engines[2].name}.",
                "Create executive operating cadence, backlog, and governance rules.",
                "Package the mechanism as a repeatable internal capability, not a one-off automation.",
            ],
            evidence_needed=[
                "Second use-case result",
                "Executive adoption signal",
                "Governance and risk sign-off",
            ],
            exit_criteria="A 90-day expansion decision with proof, budget, owner, and no-go conditions.",
        ),
    ]

    discovery_questions = [
        f"Who owns {t.wound_channel} risk today?",
        f"What metric would make {top_engine.name} impossible to ignore within 30 days?",
        f"Where does {t.company_short} lose demand, margin, or speed between first contact and delivered work?",
        f"Which part of {', '.join(t.capability_names[:3])} is already repeatable but not productized?",
        "What data can RIG inspect without creating security or privacy friction?",
        "Which leader can approve a pilot and kill it if the proof does not show up?",
        f"Which competitor in the threat ladder worries {t.contact_role} most?",
    ]

    intelligence_to_collect = [
        "Website conversion path and primary calls to action",
        "CRM/intake stages and drop-off points",
        "Top three revenue lines by margin and growth",
        "Current automation and AI vendor footprint",
        "Decision-maker map and economic buyer",
        "Competitive proof claims in market",
        "Compliance, data, or privacy constraints",
        "Paid search/social keyword and retargeting opportunity",
        "Customer review language and objection patterns",
        "Internal owner, budget window, and urgency trigger",
    ]

    success_metrics = [
        "Named buyer replies or forwards internally",
        "Password request or cloned-site engagement",
        "Pilot sponsor identified",
        "One quantified 30-day proof metric selected",
        f"{top_engine.name} pilot scoped with owner and data access",
        "Disqualifier check passes before implementation work starts",
    ]

    risk_register = [
        f"{t.company_short} treats this as tool procurement instead of operating-system design.",
        f"{t.contact_role} lacks authority to fund or staff the pilot.",
        "Public evidence overstates actual revenue, headcount, or capability maturity.",
        "Data access is too weak to create a proof-backed pilot.",
        f"A Tier 1 threat moves faster on {t.wound_channel} before RIG gets sponsor access.",
    ]

    next_actions = [
        f"Open {t.cloned_site_url} and verify the teaser renders correctly.",
        f"Send the day-0 email to {t.contact_name} only after final human approval.",
        f"Create a one-page {t.mechanism_name} map from the strategy brief.",
        "Add the account to the RIG outbound tracker with tier, owner, and follow-up date.",
        "Run a website scrape before proposal creation to confirm offers and claims.",
        "If reply lands, convert this brief into a passworded proposal page.",
    ]

    brief = StrategyBrief(
        prospect_id=t.prospect_id,
        company_name=t.company_name,
        generated_at=_now_iso(),
        source_hash=_stable_hash(record),
        segment=play["segment"],
        priority_tier=tier,
        priority_score=score,
        estimated_contract_value_usd=contract_value,
        account_thesis=_clean_sentence(account_thesis),
        wedge_offer=_clean_sentence(wedge_offer),
        named_mechanism=t.mechanism_name,
        system_name=system_name,
        system_layers=system_layers,
        buyer_persona=_clean_sentence(buyer_persona),
        trigger_timeline=f"{t.wound_months} months until the named trigger: {t.wound_trigger}",
        firm_snapshot=_clean_sentence(firm_snapshot),
        situation=_clean_sentence(situation),
        examination=_clean_sentence(examination),
        prediction_scorecard=prediction_scorecard,
        engagement_terms=engagement_terms,
        channel_strategy=channel_strategy,
        outbound_sequence=outbound_sequence,
        delivery_plan=delivery_plan,
        proposal_outline=[
            f"Why {t.company_short} is exposed on {t.wound_channel}",
            f"What {t.company_short} already owns: {', '.join(t.capability_names[:4])}",
            f"The named mechanism: {t.mechanism_name}",
            f"First proof engine: {top_engine.name}",
            f"Competitive threat ladder: {', '.join(x.name for x in t.threats)}",
            "30/60/90-day delivery model",
            "Disqualifiers and no-go conditions",
            "Evidence ledger and falsification packet",
        ],
        discovery_questions=discovery_questions,
        intelligence_to_collect=intelligence_to_collect,
        proof_assets=_proof_asset(t, play),
        competitor_watchlist=[f"{x.name} ({x.tier}, {x.horizon_months} months): {x.key_fact}" for x in t.threats],
        conversion_prediction=(
            f"{tier}-tier account at {score:.1f}/100. Highest-conversion path is a proof-led teardown for "
            f"{t.contact_role}, anchored on {top_engine.name}, with estimated initial contract value "
            f"${contract_value:,}."
        ),
        success_metrics=success_metrics,
        risk_register=risk_register,
        stop_conditions=t.disqualifiers,
        next_actions=next_actions,
        evidence_sources=t.evidence_sources,
        confidence=t.confidence,
    )
    return brief


def render_strategy_markdown(brief: StrategyBrief) -> str:
    """Render a strategy brief in the HED case-study/proposal style."""
    b = brief

    def bullets(items: Iterable[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    channel = "\n".join(
        f"- **{m.channel}:** {m.objective} Message: {m.message} Asset: {m.asset} Signal: {m.success_signal}"
        for m in b.channel_strategy
    )
    outbound = "\n".join(
        f"- **Day {s.day} / {s.channel}:** {s.subject_or_hook}\n  {s.body}\n  Asset: {s.required_asset}. Proof: {s.proof_to_attach}"
        for s in b.outbound_sequence
    )
    delivery = "\n".join(
        f"### {p.window}: {p.objective}\n{bullets(p.work)}\n\nEvidence needed:\n{bullets(p.evidence_needed)}\n\nExit: {p.exit_criteria}"
        for p in b.delivery_plan
    )
    scorecard = "\n".join(f"| {k} | {v} |" for k, v in b.prediction_scorecard.items())
    terms = "\n".join(f"| {k} | {v} |" for k, v in b.engagement_terms.items())
    sources = bullets(b.evidence_sources)

    return f"""# {b.company_name} — RIG Strategy Brief

## HED-Pattern Account Strategy

**For:** {b.generated_for}  
**Priority:** {b.priority_tier} ({b.priority_score:.1f}/100)  
**Segment:** {b.segment}  
**Estimated initial contract value:** ${b.estimated_contract_value_usd:,}  
**Confidence:** {b.confidence}  
**Generated:** {b.generated_at}

---

# THE FIRM
{b.firm_snapshot}

# THE SITUATION
{b.situation}

# THE EXAMINATION
{b.examination}

## Account Thesis
{b.account_thesis}

# THE SYSTEM: {b.system_name}

{bullets(b.system_layers)}

## Wedge Offer
{b.wedge_offer}

## Named Mechanism
**{b.named_mechanism}**

## Buyer Persona
{b.buyer_persona}

## Trigger Timeline
{b.trigger_timeline}

# THE APPROACH

## Channel Strategy
{channel}

## Outbound Sequence
{outbound}

## Delivery Plan
{delivery}

## Proposal Outline
{bullets(b.proposal_outline)}

## Discovery Questions
{bullets(b.discovery_questions)}

## Intelligence To Collect
{bullets(b.intelligence_to_collect)}

# THE PREDICTION

| System | Score |
|---|---|
{scorecard}

## Conversion Prediction
{b.conversion_prediction}

# THE ENGAGEMENT TERMS

| Tier | Terms |
|---|---|
{terms}

## Proof Assets
{bullets(b.proof_assets)}

## Competitor Watchlist
{bullets(b.competitor_watchlist)}

## Success Metrics
{bullets(b.success_metrics)}

## Risk Register
{bullets(b.risk_register)}

## Stop Conditions
{bullets(b.stop_conditions)}

# THE OUTCOME / NEXT MOVE
{bullets(b.next_actions)}

## Evidence Sources
{sources}
"""


def _read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                records.append({"prospect_id": f"line-{line_no}", "_parse_error": str(exc)})
    return records


def _write_one_strategy(record: dict, out_dir: str, mirror_teaser_dir: str | None) -> dict:
    try:
        brief = build_strategy_brief(record)
    except ValidationError as exc:
        return {
            "prospect_id": record.get("prospect_id", "<unknown>"),
            "status": "validation_error",
            "errors": exc.errors(),
        }
    except Exception as exc:  # pragma: no cover
        return {
            "prospect_id": record.get("prospect_id", "<unknown>"),
            "status": "generation_error",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

    root = Path(out_dir)
    bundle = root / brief.prospect_id
    bundle.mkdir(parents=True, exist_ok=True)
    strategy_json = bundle / "strategy.json"
    strategy_md = bundle / "strategy.md"
    strategy_json.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    strategy_md.write_text(render_strategy_markdown(brief), encoding="utf-8")

    if mirror_teaser_dir:
        mirror = Path(mirror_teaser_dir) / brief.prospect_id
        if mirror.exists():
            (mirror / "strategy.json").write_text(brief.model_dump_json(indent=2), encoding="utf-8")
            (mirror / "strategy.md").write_text(render_strategy_markdown(brief), encoding="utf-8")

    return {
        "prospect_id": brief.prospect_id,
        "company": brief.company_name,
        "status": "ok",
        "priority_tier": brief.priority_tier,
        "priority_score": brief.priority_score,
        "segment": brief.segment,
        "estimated_contract_value_usd": brief.estimated_contract_value_usd,
        "confidence": brief.confidence,
        "strategy_json": str(strategy_json),
        "strategy_md": str(strategy_md),
    }


def run_strategy_batch(
    prospects_jsonl: str | Path,
    out_dir: str | Path,
    workers: int = 8,
    summary_path: str | Path | None = None,
    aggregate_jsonl: str | Path | None = None,
    aggregate_csv: str | Path | None = None,
    mirror_teaser_dir: str | Path | None = None,
) -> dict:
    """Generate strategy briefs for every validated prospect."""
    in_path = Path(prospects_jsonl)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    records = _read_jsonl(in_path)
    started = time.time()
    ok = err_val = err_gen = err_parse = 0
    results: list[dict] = []
    strategy_rows: list[dict] = []

    parseable = []
    for r in records:
        if "_parse_error" in r:
            err_parse += 1
            results.append({"prospect_id": r["prospect_id"], "status": "parse_error", "error": r["_parse_error"]})
        else:
            parseable.append(r)

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                _write_one_strategy,
                r,
                str(out_path),
                str(mirror_teaser_dir) if mirror_teaser_dir else None,
            )
            for r in parseable
        ]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if res["status"] == "ok":
                ok += 1
                strategy_rows.append(res)
            elif res["status"] == "validation_error":
                err_val += 1
            else:
                err_gen += 1

    elapsed = time.time() - started
    by_segment = Counter(r["segment"] for r in strategy_rows)
    by_tier = Counter(r["priority_tier"] for r in strategy_rows)
    by_confidence = Counter(r["confidence"] for r in strategy_rows)
    estimated_pipeline = sum(r["estimated_contract_value_usd"] for r in strategy_rows)
    summary = {
        "total": len(records),
        "ok": ok,
        "validation_errors": err_val,
        "generation_errors": err_gen,
        "parse_errors": err_parse,
        "out_dir": str(out_path),
        "elapsed_seconds": round(elapsed, 2),
        "rate_per_second": round(len(records) / elapsed if elapsed > 0 else 0, 2),
        "workers": workers,
        "generated_for": "RIG and Mike Rodgers",
        "estimated_pipeline_usd": estimated_pipeline,
        "by_segment": dict(by_segment.most_common()),
        "by_priority_tier": dict(sorted(by_tier.items())),
        "by_confidence": dict(sorted(by_confidence.items())),
    }

    if aggregate_jsonl:
        ag = Path(aggregate_jsonl)
        ag.parent.mkdir(parents=True, exist_ok=True)
        with ag.open("w", encoding="utf-8") as f:
            for res in sorted(strategy_rows, key=lambda x: (-x["priority_score"], x["company"])):
                full = json.loads(Path(res["strategy_json"]).read_text(encoding="utf-8"))
                f.write(json.dumps(full, ensure_ascii=False) + "\n")

    if aggregate_csv:
        csv_path = Path(aggregate_csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "prospect_id",
            "company",
            "segment",
            "priority_tier",
            "priority_score",
            "estimated_contract_value_usd",
            "confidence",
            "strategy_md",
            "strategy_json",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in sorted(strategy_rows, key=lambda x: (-x["priority_score"], x["company"])):
                writer.writerow({k: row.get(k, "") for k in fields})

    if summary_path:
        sp = Path(summary_path)
        sp.parent.mkdir(parents=True, exist_ok=True)
        with sp.open("w", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    return {"summary": summary, "results": results}


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Generate RIG account strategies for validated teaser prospects.")
    p.add_argument("--input", required=True, help="prospects JSONL path")
    p.add_argument("--output", required=True, help="strategy output directory")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--summary", default=None)
    p.add_argument("--aggregate-jsonl", default=None)
    p.add_argument("--aggregate-csv", default=None)
    p.add_argument("--mirror-teaser-dir", default=None)
    args = p.parse_args()

    out = run_strategy_batch(
        prospects_jsonl=args.input,
        out_dir=args.output,
        workers=args.workers,
        summary_path=args.summary,
        aggregate_jsonl=args.aggregate_jsonl,
        aggregate_csv=args.aggregate_csv,
        mirror_teaser_dir=args.mirror_teaser_dir,
    )
    print(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    s = out["summary"]
    return 0 if s["validation_errors"] == 0 and s["generation_errors"] == 0 and s["parse_errors"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
