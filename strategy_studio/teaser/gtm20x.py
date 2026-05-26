"""RIG 20x AI GTM operating system for Strategy Studio prospects.

This module upgrades generated HED-pattern strategy briefs with:
- named expert/process lenses,
- a 100-question operating system with solutions,
- RIG -30/+30 deviation moves,
- AI GTM workflow design for every prospect.

It stays A1 deterministic: it reads validated teaser inputs and strategy briefs,
then writes local artifacts only. No external sends, no model calls.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from strategy_studio.teaser.schema import TeaserInput
from strategy_studio.teaser.strategy import (
    StrategyBrief,
    build_strategy_brief,
    render_strategy_markdown,
)


Audience = Literal["RIG and Mike Rodgers"]
PriorityTier = Literal["A", "B", "C"]


class ExpertLens(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expert: str
    domain: str
    process: str
    applied_question: str
    prospect_application: str


class QuestionSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    question: str
    solution: str
    process_lens: str
    evidence_gate: str


class DeviationMove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deviation_sigma: Literal[-30, -20, -10, 0, 10, 20, 30]
    name: str
    median_behavior: str
    rig_move: str
    required_proof: str
    risk: str


class AIGTMWorkflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str
    agent: str
    input_signal: str
    action: str
    output_artifact: str
    quality_gate: str


class EnhancedGTMStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prospect_id: str
    company_name: str
    generated_for: Audience = "RIG and Mike Rodgers"
    generated_at: str
    base_strategy_hash: str
    strategy_md_path: str
    segment: str
    priority_tier: PriorityTier
    priority_score: float = Field(ge=0.0, le=100.0)
    twenty_x_score: float = Field(ge=0.0, le=100.0)
    expert_lenses: list[ExpertLens] = Field(min_length=10, max_length=20)
    ai_gtm_workflows: list[AIGTMWorkflow] = Field(min_length=8, max_length=12)
    deviation_moves: list[DeviationMove] = Field(min_length=7, max_length=7)
    top_questions: list[QuestionSolution] = Field(min_length=20, max_length=20)
    one_big_bet: str
    wedge_upgrade: str
    brand_upgrade: str
    sales_motion_upgrade: str
    data_system_upgrade: str
    proof_upgrade: str
    next_72_hours: list[str] = Field(min_length=5, max_length=8)
    no_go_tests: list[str] = Field(min_length=3, max_length=5)
    global_question_bank_path: str
    confidence: Literal["H", "M", "L"]


EXPERTS: list[dict[str, str]] = [
    {
        "expert": "Richard Rumelt",
        "domain": "strategy diagnosis",
        "process": "Good Strategy/Bad Strategy kernel: diagnosis, guiding policy, coherent actions",
        "question": "What is the real obstacle, not the stated wish?",
    },
    {
        "expert": "Roger Martin",
        "domain": "strategic choice",
        "process": "Where-to-play / how-to-win choice cascade",
        "question": "Where should this account refuse to play so the first win is sharp?",
    },
    {
        "expert": "Michael Porter",
        "domain": "competitive strategy",
        "process": "Five Forces plus tradeoff discipline",
        "question": "Which structural force is about to make the current model weaker?",
    },
    {
        "expert": "Clayton Christensen",
        "domain": "innovation",
        "process": "Jobs-to-be-done and disruption analysis",
        "question": "What job is the buyer hiring the current process to do badly?",
    },
    {
        "expert": "April Dunford",
        "domain": "positioning",
        "process": "Obviously Awesome: alternatives, attributes, value, who cares, market category",
        "question": "What category should this account believe it is actually buying?",
    },
    {
        "expert": "Andy Raskin",
        "domain": "strategic narrative",
        "process": "Old game/new game narrative with stakes and promised land",
        "question": "What old game is ending for this buyer?",
    },
    {
        "expert": "Christopher Lochhead",
        "domain": "category design",
        "process": "Category POV, enemy, language, lightning strike",
        "question": "What enemy category do we need the buyer to stop accepting?",
    },
    {
        "expert": "Geoffrey Moore",
        "domain": "market entry",
        "process": "Crossing the Chasm beachhead and whole-product strategy",
        "question": "What beachhead makes the first proof feel inevitable?",
    },
    {
        "expert": "Mark Roberge",
        "domain": "sales engineering",
        "process": "Sales Acceleration Formula: data, process, hiring, coaching",
        "question": "Which repeatable sales variable can be measured this week?",
    },
    {
        "expert": "Aaron Ross",
        "domain": "outbound systems",
        "process": "Predictable Revenue specialization and cold outbound sequencing",
        "question": "Which role should receive which message, in which order?",
    },
    {
        "expert": "Matthew Dixon and Brent Adamson",
        "domain": "enterprise sales",
        "process": "Challenger Sale: teach, tailor, take control",
        "question": "What commercial insight should make the buyer uncomfortable?",
    },
    {
        "expert": "Neil Rackham",
        "domain": "sales discovery",
        "process": "SPIN: situation, problem, implication, need-payoff",
        "question": "Which implication question creates urgency without hype?",
    },
    {
        "expert": "David Sandler",
        "domain": "qualification",
        "process": "Pain, budget, decision, upfront contract",
        "question": "What must be true before RIG spends implementation energy?",
    },
    {
        "expert": "Miller Heiman Group",
        "domain": "complex sales",
        "process": "Strategic Selling: economic buyer, technical buyer, coach, red flags",
        "question": "Who is the economic buyer and who can kill the deal?",
    },
    {
        "expert": "Byron Sharp",
        "domain": "brand growth",
        "process": "Mental availability and physical availability",
        "question": "What memory structure should make RIG easy to recall?",
    },
    {
        "expert": "David Aaker",
        "domain": "brand identity",
        "process": "Brand identity system: core, extended, proof, associations",
        "question": "What brand association should the prospect remember after one touch?",
    },
    {
        "expert": "Marty Neumeier",
        "domain": "differentiation",
        "process": "Zag / onlyness statement",
        "question": "What can RIG say that a generic AI consultant cannot say?",
    },
    {
        "expert": "Eugene Schwartz",
        "domain": "copy strategy",
        "process": "Market sophistication and awareness ladder",
        "question": "How aware is the buyer of the wound already?",
    },
    {
        "expert": "Simon Wardley",
        "domain": "systems mapping",
        "process": "Wardley mapping: value chain and evolution",
        "question": "Which capability is custom today but should become infrastructure?",
    },
    {
        "expert": "Hamilton Helmer",
        "domain": "moat design",
        "process": "7 Powers: scale, network, counter-positioning, switching, brand, cornered resource, process power",
        "question": "Which power can this client build instead of buying tools?",
    },
]


QUESTION_CATEGORIES: dict[str, list[tuple[str, str, str, str]]] = {
    "ICP and segmentation": [
        ("Which subsegment feels the trigger most painfully?", "Rank accounts by trigger proximity, revenue capacity, and data access; suppress low-urgency segments.", "Roger Martin choice cascade", "Segment must tie to a named wound channel."),
        ("Which accounts have a budget owner and an operating owner?", "Flag accounts where economic buyer and operator are both visible; route the rest to research.", "Miller Heiman buying influences", "Buyer role must be named."),
        ("Which industries are late enough to need help but mature enough to buy?", "Prioritize mid-adoption categories: med spa, law, CPA, healthcare, service, manufacturing, PE ops.", "Crossing the Chasm beachhead", "Segment must show tech adoption signal."),
        ("Which local accounts can be won with proof before brand trust exists?", "Use cloned-site teardown plus local-market wound as the entry wedge.", "Byron Sharp availability", "Website and geography must be known."),
        ("Which accounts are too small for RIG economics?", "Reject under-10 employee firms and weak revenue proxies before strategy generation.", "Sandler qualification", "Employee floor must pass."),
        ("Which accounts have repeatable work that can become a system?", "Score visible service lines, intake paths, reviews, recurring operations, and content assets.", "Wardley value-chain mapping", "At least two capabilities required."),
        ("Which accounts should get no outreach yet?", "Hold accounts with low proof, no buyer, or weak trigger until enrichment improves.", "Rumelt diagnosis", "Confidence cannot be L."),
        ("Which accounts deserve proposal work first?", "Tier by priority score, wound months, confidence, estimated contract value, and buyer authority.", "Mark Roberge sales formula", "Tier A must exceed threshold."),
        ("Which accounts should be grouped into campaign pods?", "Cluster by segment, wound channel, competitor set, and offer system name.", "Brian Balfour growth loops", "Campaign pod must share message logic."),
        ("Which accounts have category-creation potential?", "Flag accounts where capability names can become a named mechanism and proof loop.", "Lochhead category design", "Named mechanism must be present."),
    ],
    "Wound and trigger": [
        ("What channel will they lose if nothing changes?", "Make every strategy name a procurement, discovery, intake, referral, or value-creation channel.", "Challenger commercial insight", "Wound channel cannot be generic."),
        ("What date makes the wound real?", "Tie urgency to CMMC, EU AI Act, Google AI search/ad changes, budget cycles, or segment-specific events.", "Rumelt diagnosis", "Trigger date/event must be named."),
        ("What happens if the buyer waits six months?", "Write the business consequence in channel, margin, speed, or competitive lockout language.", "SPIN implication", "Consequence must be falsifiable."),
        ("What is the current false comfort?", "Call out tool adoption, dashboards, ads, or Copilot as insufficient when they do not change operations.", "Challenger teach/tailor/control", "False comfort must be specific."),
        ("What metric makes the wound undeniable?", "Pick one first-win metric: lead response, intake conversion, quote cycle, referral leakage, margin, documentation time.", "Mark Roberge data process", "Metric owner required."),
        ("What wound can be shown on their own website?", "Use website copy, service pages, CTAs, reviews, and missing proof assets as the mirror.", "April Dunford positioning", "Public artifact required."),
        ("What competitor can exploit the wound first?", "Attach Tier 1/2/3 competitor ladder to the same channel.", "Porter Five Forces", "Threat must be named."),
        ("What would disprove the wound?", "Define one falsification test per account before any external send.", "RIG ProofPacket discipline", "Disproof condition required."),
        ("What is the smallest painful proof?", "Choose a 10-day audit that exposes money/time leakage before building.", "Sandler pain funnel", "Audit has to produce a number."),
        ("What wound language would the buyer repeat internally?", "Convert the wound into a short phrase a COO/owner can forward.", "Andy Raskin narrative", "Phrase must be under 12 words."),
    ],
    "Offer and productization": [
        ("What is the first productized RIG offer for this account?", "Map every account to Diagnostic, Activation, or Transformation based on tier and evidence.", "RIG HED engagement tiers", "Tier must be explicit."),
        ("What client-owned system would exist after 90 days?", "Name the client system with Solo, Team, Vault, Edge, Sight, Blueprint layers.", "HED FORGE pattern", "System layers must render."),
        ("What is the first workflow RIG should ship?", "Pick the top engine by target revenue and make it the first production workflow.", "Good strategy coherent action", "One first workflow only."),
        ("What should not be in scope?", "Write anti-goals: generic chatbot, generic dashboard, unowned automation, no proof metric.", "Roger Martin tradeoffs", "Anti-goals must be listed."),
        ("What gets delivered in two weeks?", "Diagnostic: teardown, falsification memo, data-access map, GO/NO-GO.", "Sandler upfront contract", "Fixed deliverables required."),
        ("What gets delivered in 30 days?", "Activation foundation: first proof workflow, baseline metric, owner cadence, executive memo.", "Mark Roberge process", "30-day metric required."),
        ("What gets delivered in 90 days?", "Operating system: repeatable workflow, knowledge graph, governance, expansion backlog.", "HED SOW pattern", "Expansion gate required."),
        ("What is the client-owned asset?", "Every proposal must name a durable asset the client owns, not access to a vendor tool.", "Hamilton Helmer process power", "Ownership language required."),
        ("What is the price anchor?", "Use estimated contract value from revenue, employees, urgency, and proof depth.", "Value pricing discipline", "Price must be bounded."),
        ("What makes RIG scarce?", "Use disqualifiers that force a GO/NO-GO read before implementation.", "Marty Neumeier onlyness", "Three stop conditions required."),
    ],
    "Brand and narrative": [
        ("What old game is ending?", "Name the shift from tools/ads/manual follow-up to client-owned intelligence substrate.", "Andy Raskin strategic narrative", "Old game/new game required."),
        ("What new game should they enter?", "Position the client as owning an operating system for its category.", "Category Pirates POV", "New category name required."),
        ("What enemy should the narrative fight?", "Fight generic AI consulting, dashboard theater, and tool-first automation.", "Lochhead category enemy", "Enemy must be named."),
        ("What phrase should stick after one read?", "Use named mechanism plus wound channel as the memory hook.", "Byron Sharp mental availability", "Memory hook required."),
        ("What proof makes the brand credible?", "Attach source weights, cloned-site evidence, and falsification packets.", "David Aaker proof associations", "Proof source count >= 2."),
        ("What should the buyer believe about RIG?", "RIG builds client-owned AI operating systems with proof, not vendor-dependent AI theater.", "Marty Neumeier zag", "Onlyness claim required."),
        ("What should never appear in copy?", "Ban soft-close language, generic AI consultant phrases, and unsupported superlatives.", "Eugene Schwartz sophistication", "Banned phrase scan required."),
        ("What is the visual proof moment?", "Use the cloned site, mechanism map, and lockout timeline as first-view proof.", "HED demo pattern", "Asset URL required."),
        ("What story should the buyer tell their team?", "They found a way to turn existing capabilities into compounding operating memory.", "StoryBrand role clarity", "Client is hero, RIG is guide."),
        ("What is the one sentence version?", "Write: You are X months from Y; Z mechanism turns A into B.", "April Dunford positioning", "Sentence under 28 words."),
    ],
    "Sales motion": [
        ("Who gets the first email?", "Send only to the single most leveraged buyer; suppress broad blasts.", "Miller Heiman economic buyer", "One primary contact required."),
        ("What is the Day 0 message?", "Lead with wound, uncomfortable mirror, mechanism, and proof asset.", "Challenger teach", "No generic opener."),
        ("What is the Day 2 social move?", "Use recognition and mechanism language, not a pitch.", "Aaron Ross outbound sequence", "Social touch distinct from email."),
        ("What is the Day 5 proof move?", "Name the first engine and ask for falsification.", "SPIN need-payoff", "Proof asset attached."),
        ("What is the Day 9 disqualifier move?", "State why RIG would walk away to increase scarcity and qualification.", "Sandler pain/budget/decision", "Disqualifiers included."),
        ("What is the final close-loop move?", "Ask whether the wound is already owned internally; if yes, close the loop.", "Upfront contract", "Binary reply path."),
        ("What should be routed to phone?", "Call only after site engagement, reply, or verified buyer fit.", "Predictable Revenue specialization", "Signal gate required."),
        ("What should be routed to paid retargeting?", "Only lawful, approved audiences from visited/proposal accounts.", "Growth loop retargeting", "Approval required."),
        ("What is the reply classification?", "Classify replies as falsification, interest, referral, no fit, objection, or unsubscribe.", "Revenue operations hygiene", "CRM state required."),
        ("What is the no-send rule?", "Do not send if confidence is L, buyer unknown, or evidence sources under threshold.", "RIG gate discipline", "Pre-send quality gate."),
    ],
    "AI GTM system": [
        ("What should the AI research agent collect first?", "Website, service lines, leaders, reviews, competitors, job posts, tech stack, ads, and trigger evidence.", "A1 research pipeline", "Source path required."),
        ("What should the personalization agent write?", "HED-pattern teaser, day-0 email, mechanism map, and proposal outline.", "A2 bounded drafting", "Schema validation required."),
        ("What should the proof agent verify?", "Sources, source weights, employee floor, buyer role, trigger date, and falsification tests.", "ProofPacket policy", "Proof packet required."),
        ("What should the scoring agent rank?", "Priority score, 20x score, contract value, reply likelihood, and data access risk.", "Mark Roberge data score", "Scores bounded 0-100."),
        ("What should the ads agent build?", "Search/social teaser variants from the same wound and mechanism, not new claims.", "Message-market fit", "Human approval required."),
        ("What should the proposal agent generate?", "Passworded proposal page, SOW draft, proof assets, and 30/60/90 roadmap.", "HED SOW pattern", "No deploy without approval."),
        ("What should the CRM agent update?", "Status, last touch, next touch, confidence, owner, and proof path.", "RevOps system of record", "No private export."),
        ("What should the learning agent improve?", "Winning wounds, losing segments, reply objections, disqualifier accuracy, and proposal conversion.", "Calibration loop", "Outcome feedback required."),
        ("What should the compliance gate block?", "Unapproved public exposure, private data leakage, unsourced claims, and prohibited sends.", "RIG Gate 00-12", "Blocker log required."),
        ("What should the daily operator brief show?", "Top accounts, new triggers, stale follow-ups, blocked data, and best proof assets.", "Operator cadence", "Daily artifact required."),
    ],
    "Data and proof": [
        ("Which source should own the truth?", "LakeOS/QNAP for files and proof, Strategy Studio for generated strategy artifacts.", "Local-first architecture", "Canonical path required."),
        ("Which fields are not trustworthy enough?", "Flag missing employees, weak revenue proxy, unknown buyer, generic capability names, and low source weight.", "Evidence engine", "Quality flags required."),
        ("How do we prevent fake personalization?", "Personalization must reference website capability, wound channel, and proof source.", "A1 schema gate", "No unsupported claims."),
        ("How do we track source weights?", "Carry SW labels through teaser, strategy, proof, and proposal artifacts.", "RIG evidence ledger", "SW required in sources."),
        ("What should be re-scraped before proposal?", "Website pages, leaders, reviews, ads, job posts, and recent news.", "Pre-proposal refresh", "Freshness date required."),
        ("What is the contradiction check?", "Detect mismatched employee/revenue signals and downgrade confidence until resolved.", "Evidence graph", "Contradictions listed."),
        ("What is the privacy boundary?", "No public exposure, external sends, or private data export without approval.", "RIG operator doctrine", "Approval gate required."),
        ("What is the proof of generated work?", "Write local JSON/MD, summary, test output, and source hash.", "ProofPacket or it did not happen", "Artifact hash required."),
        ("What does UNKNOWN do?", "UNKNOWN routes to enrichment/indexing, not invented strategy.", "A1 UNKNOWN policy", "Unknown state visible."),
        ("What makes the strategy deployable?", "Validated schema, proof paths, disqualifiers, next action, and human approval line.", "Ship gate", "No unvalidated markdown only."),
    ],
    "Deviate engine": [
        ("What is the -30 sigma anti-pattern?", "Reject fake AI transformation: chatbot, dashboard, no owner, no data, no metric.", "RIG deviation scale", "No-go move visible."),
        ("What is the -20 sigma warning?", "Expose tool-first thinking before selling implementation.", "RIG rupture", "Warning line required."),
        ("What is the -10 sigma wedge?", "Use the uncomfortable mirror instead of a benefits pitch.", "Deviation mirror", "Mirror line required."),
        ("What is the median behavior?", "Median is an AI audit, generic automation roadmap, and broad nurture.", "Baseline definition", "Median named."),
        ("What is the +10 sigma move?", "Named mechanism plus cloned-site proof asset.", "HED move", "Mechanism present."),
        ("What is the +20 sigma move?", "Passworded proposal with client-owned operating system and first workflow.", "RIG Edge", "Proposal asset required."),
        ("What is the +30 sigma move?", "Category creation and client-owned compounding intelligence substrate.", "RIG category rupture", "Category language required."),
        ("What should be killed even if it seems easy?", "Any work that cannot produce proof, owner, and metric inside 30 days.", "Falsification gate", "Kill criteria required."),
        ("What should be made more extreme?", "Specificity: named channel, named buyer, named proof, named first workflow.", "AntiGenericForce", "Specificity score required."),
        ("What should be protected from over-deviation?", "Do not invent facts, contacts, revenue, or compliance claims to sound clever.", "Evidence discipline", "No source, no number."),
    ],
    "Delivery and implementation": [
        ("What happens after a reply?", "Run teardown, validate data access, create proposal, define pilot owner.", "HED Activation flow", "Reply state required."),
        ("What is the first meeting agenda?", "Falsify wound, inspect data, choose first metric, decide GO/NO-GO.", "Sandler upfront contract", "Agenda under 30 minutes."),
        ("What does the first pilot build?", "One workflow tied to top engine and measurable before/after result.", "Good strategy action", "Pilot scope bounded."),
        ("Who must be in the pilot?", "Economic buyer, operating owner, data owner, daily user, RIG operator.", "Miller Heiman buying roles", "Role map required."),
        ("What gets documented?", "System map, data sources, baseline, decisions, risks, and handoff instructions.", "RIG proof/audit", "Documentation path required."),
        ("What is the day-30 decision?", "Scale, repair, or stop based on proof metric and adoption evidence.", "Production or nothing", "Decision criteria required."),
        ("What is the day-90 decision?", "Expand to system layer or stop with lessons captured.", "HED review", "Expansion criteria required."),
        ("What needs automation first?", "Capture, scoring, follow-up, proposal generation, and proof tracking.", "AI GTM ops", "Workflow owner required."),
        ("What should remain manual?", "Approval, final send, sensitive judgment, pricing exception, public exposure.", "Human-in-loop gate", "Approval state required."),
        ("What is the handoff?", "Client-owned docs, source code, runbook, dashboard, and internal champion training.", "RIG guarantee", "Ownership transfer required."),
    ],
    "Learning and scaling": [
        ("What pattern should RIG learn weekly?", "Which wounds, segments, offers, and disqualifiers create replies.", "Calibration loop", "Outcome data required."),
        ("What should be promoted to a reusable play?", "Any sequence that wins twice in one segment with proof.", "Strategy Studio playbook", "Two wins required."),
        ("What should be retired?", "Messages with low reply, weak proof, or generic copy smell.", "Growth experiment discipline", "Retirement rule required."),
        ("What should be A/B tested?", "Wound phrase, mechanism name, proof asset, disqualifier angle, first metric.", "Growth loops", "One variable per test."),
        ("What should the dashboard show?", "A-tier accounts, active proofs, stale follow-ups, blocked data, conversion by segment.", "RevOps cockpit", "Daily view required."),
        ("What should feed LakeOS?", "All generated strategies, proof packets, replies, outcomes, and learned plays.", "Memory compounding", "Ingestion path required."),
        ("What should improve scoring?", "Reply outcomes, meeting outcomes, data access, close/no-close, and revenue realized.", "Brier calibration", "Closed-loop labels required."),
        ("What should be reviewed by Mike?", "Top 25 A-tier strategies, any public send, any high-dollar proposal, any weak evidence account.", "Human approval", "Review queue required."),
        ("What makes this 20x, not 2x?", "It compounds proof, memory, category language, and delivery assets across every account.", "RIG OS thesis", "Compounding loop required."),
        ("What is the next bottleneck?", "Fresh enrichment credits, verified buyer data, and proposal deployment capacity.", "Theory of constraints", "Bottleneck named."),
    ],
}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_question_bank() -> list[QuestionSolution]:
    questions: list[QuestionSolution] = []
    for category, items in QUESTION_CATEGORIES.items():
        for index, (question, solution, process, gate) in enumerate(items, 1):
            questions.append(
                QuestionSolution(
                    id=f"Q{len(questions)+1:03d}",
                    category=category,
                    question=question,
                    solution=solution,
                    process_lens=process,
                    evidence_gate=gate,
                )
            )
    if len(questions) != 100:
        raise RuntimeError(f"expected exactly 100 questions, got {len(questions)}")
    return questions


def first_proof_workflow(t: TeaserInput) -> str:
    """Return a sharper proof workflow than raw scraped nav/copy phrases."""
    workflow_by_segment = {
        "portfolio ops": "Portfolio Value-Creation Workflow",
        "service ops": "Lead Response and Quote-to-Cash Workflow",
        "patient ops": "Patient Intake and Reactivation Workflow",
        "legal ops": "Matter Intake and Retainer Workflow",
        "medspa growth": "Consultation Booking and Rebooking Workflow",
        "CPA advisory": "Advisory Capacity and Client Intelligence Workflow",
    }
    generic_markers = [
        "trusted by",
        "why choose",
        "about",
        "close",
        "book",
        "pencil",
        "all your needs",
        "confidence is",
        "our power",
        "global leaders",
        "less ego",
    ]
    top = max(t.engines, key=lambda e: e.target_revenue_m).name.strip()
    if not top or any(marker in top.lower() for marker in generic_markers):
        return workflow_by_segment.get(t.industry_short, "Operating Intelligence Workflow")
    return top


def render_question_bank_markdown(questions: list[QuestionSolution]) -> str:
    lines = [
        "# RIG AI GTM 100 Missing Questions",
        "",
        "These are the questions Strategy Studio should ask before a prospect strategy is considered 20x-ready.",
        "Each question includes the deterministic solution and evidence gate.",
        "",
    ]
    current = None
    for q in questions:
        if q.category != current:
            current = q.category
            lines.extend([f"## {current}", ""])
        lines.append(f"### {q.id}. {q.question}")
        lines.append(f"- **Solution:** {q.solution}")
        lines.append(f"- **Process lens:** {q.process_lens}")
        lines.append(f"- **Evidence gate:** {q.evidence_gate}")
        lines.append("")
    return "\n".join(lines)


def render_gtm_system_markdown(questions_path: str) -> str:
    lines = [
        "# RIG AI GTM + Strategy Operating System",
        "",
        "**For:** RIG and Mike Rodgers",
        "",
        "This is the system layer above the 1,783 account strategies. It turns HED-style account strategy into a repeatable AI GTM factory.",
        "",
        "## Expert Board",
        "",
        "| Expert | Domain | Process | Operating Question |",
        "|---|---|---|---|",
    ]
    for e in EXPERTS:
        lines.append(f"| {e['expert']} | {e['domain']} | {e['process']} | {e['question']} |")
    lines.extend(
        [
            "",
            "## AI GTM Workflow",
            "",
            "1. **Capture:** Apollo/LakeOS/scrapers/site clone feed company facts, contacts, site capabilities, and proof sources.",
            "2. **Classify:** A1 routes by segment, trigger, buyer, confidence, employee floor, and source weight.",
            "3. **Mirror:** HED-style wound, capabilities, mechanism, threats, disqualifiers, and proof packet.",
            "4. **Deviate:** Apply -30/+30 RIG moves to reject median AI consulting and create category-level language.",
            "5. **Personalize:** Generate email, LinkedIn, cloned-site teaser, phone prompt, and proposal outline from the same proof.",
            "6. **Gate:** No external send without confidence, proof, buyer, human approval, and privacy check.",
            "7. **Deploy:** Passworded proposal page plus strategy.md/json for the account.",
            "8. **Learn:** Capture replies, objections, no-go reasons, meeting outcomes, and close/no-close into LakeOS.",
            "",
            "## Deviation Scale",
            "",
            "- **-30:** Kill fake transformation: chatbot/dashboard/no owner/no data/no metric.",
            "- **-20:** Expose tool-first thinking before implementation.",
            "- **-10:** Use uncomfortable mirror instead of benefits pitch.",
            "- **0:** Median AI audit and broad automation roadmap.",
            "- **+10:** Named mechanism and cloned-site proof asset.",
            "- **+20:** Passworded proposal and client-owned operating system.",
            "- **+30:** Category creation plus compounding client-owned intelligence substrate.",
            "",
            "## 100-Question Bank",
            "",
            f"Canonical question bank: `{questions_path}`",
        ]
    )
    return "\n".join(lines) + "\n"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def select_questions(t: TeaserInput) -> list[QuestionSolution]:
    bank = get_question_bank()
    categories = [
        "Wound and trigger",
        "Offer and productization",
        "Brand and narrative",
        "Sales motion",
        "AI GTM system",
        "Data and proof",
        "Deviate engine",
        "Delivery and implementation",
        "Learning and scaling",
        "ICP and segmentation",
    ]
    selected: list[QuestionSolution] = []
    for category in categories:
        pool = [q for q in bank if q.category == category]
        selected.extend(pool[:2])
    if t.confidence == "M":
        selected[0] = next(q for q in bank if q.id == "Q062")
    return selected[:20]


def expert_lenses(t: TeaserInput, brief: StrategyBrief) -> list[ExpertLens]:
    first_workflow = first_proof_workflow(t)
    lenses = []
    for e in EXPERTS:
        application = (
            f"Apply {e['process']} to {t.company_short}: center the {t.wound_months}-month "
            f"{t.wound_channel} wound, make {brief.named_mechanism} the mechanism, and use "
            f"{first_workflow} as the first proof workflow."
        )
        lenses.append(
            ExpertLens(
                expert=e["expert"],
                domain=e["domain"],
                process=e["process"],
                applied_question=e["question"],
                prospect_application=application,
            )
        )
    return lenses[:20]


def deviation_moves(t: TeaserInput, brief: StrategyBrief) -> list[DeviationMove]:
    first_workflow = first_proof_workflow(t)
    return [
        DeviationMove(
            deviation_sigma=-30,
            name="Kill AI Theater",
            median_behavior="Sell a chatbot, dashboard, or generic AI audit.",
            rig_move=f"Walk away if {t.company_short} cannot name an owner, data source, and 30-day metric for {first_workflow}.",
            required_proof="Owner, data access, metric, and disqualifier pass.",
            risk="RIG wastes implementation energy on a buyer who wants optics.",
        ),
        DeviationMove(
            deviation_sigma=-20,
            name="Expose Tool-First Thinking",
            median_behavior="Ask which AI tools they use.",
            rig_move=f"Ask who owns {t.wound_channel} and what breaks if the channel shifts before the next budget cycle.",
            required_proof="Named channel owner or explicit UNKNOWN.",
            risk="Buyer hides behind vendor exploration.",
        ),
        DeviationMove(
            deviation_sigma=-10,
            name="Uncomfortable Mirror",
            median_behavior="Open with benefits and case studies.",
            rig_move=f"Open with: {t.capability_gap}",
            required_proof="Website capability evidence and teaser proof packet.",
            risk="Mirror is too sharp for low-authority contacts.",
        ),
        DeviationMove(
            deviation_sigma=0,
            name="Median Baseline",
            median_behavior="AI readiness audit, automation roadmap, generic nurture sequence.",
            rig_move="Use only as baseline to compare against; do not ship as the offer.",
            required_proof="Baseline appears in strategy for contrast only.",
            risk="RIG sounds like every other AI consultant.",
        ),
        DeviationMove(
            deviation_sigma=10,
            name="Named Mechanism",
            median_behavior="Describe a solution category.",
            rig_move=f"Make {brief.named_mechanism} the buyer's internal phrase for the first proof system.",
            required_proof="Mechanism map, cloned-site teaser, and first proof engine.",
            risk="Mechanism fails if not tied to the buyer's actual capabilities.",
        ),
        DeviationMove(
            deviation_sigma=20,
            name="Passworded Proposal System",
            median_behavior="Send a PDF proposal after a call.",
            rig_move=f"Turn {t.cloned_site_url} into a passworded proof page with SOW, 30/60/90 plan, and falsification gate.",
            required_proof="Approved proposal page and no public exposure.",
            risk="Premature deployment without human approval.",
        ),
        DeviationMove(
            deviation_sigma=30,
            name="Category Rupture",
            median_behavior="Sell AI automation services.",
            rig_move=f"Position {t.company_short} as owner of {brief.system_name}: a client-owned intelligence substrate that compounds beyond tools.",
            required_proof="System layers, outcome metric, operating cadence, and handoff plan.",
            risk="Overreach if leadership cannot fund or govern the system.",
        ),
    ]


def ai_gtm_workflows(t: TeaserInput, brief: StrategyBrief) -> list[AIGTMWorkflow]:
    first_workflow = first_proof_workflow(t)
    return [
        AIGTMWorkflow(stage="Capture", agent="LakeOS Research Agent", input_signal="company, site, contact, proof sources", action="Collect source-weighted facts and freshness dates.", output_artifact="research ledger", quality_gate=">=2 sources or UNKNOWN"),
        AIGTMWorkflow(stage="Classify", agent="ICP Scoring Agent", input_signal="segment, employees, revenue, wound, role", action="Rank by priority, confidence, buyer authority, and data risk.", output_artifact="tier score", quality_gate="employee floor and confidence pass"),
        AIGTMWorkflow(stage="Mirror", agent="HED Pattern Agent", input_signal="capabilities and trigger", action=f"Create firm/situation/examination for {t.company_short}.", output_artifact="strategy.md", quality_gate="HED headings present"),
        AIGTMWorkflow(stage="Deviate", agent="RIG Deviate Engine", input_signal="median behavior", action=f"Generate -30/+30 moves around {brief.named_mechanism}.", output_artifact="deviation ladder", quality_gate="all seven sigma moves present"),
        AIGTMWorkflow(stage="Personalize", agent="Outbound Agent", input_signal="buyer role and proof asset", action="Generate day 0/2/5/9/14 sequence from the same evidence.", output_artifact="outbound sequence", quality_gate="no banned phrases"),
        AIGTMWorkflow(stage="Propose", agent="Proposal Agent", input_signal="reply or manual approval", action=f"Convert teaser into passworded {brief.system_name} proposal.", output_artifact="proposal page", quality_gate="human approval required"),
        AIGTMWorkflow(stage="Pilot", agent="Delivery Agent", input_signal=first_workflow, action="Scope first proof workflow and baseline metric.", output_artifact="30-day pilot card", quality_gate="owner, data, metric"),
        AIGTMWorkflow(stage="Proof", agent="ProofPacket Agent", input_signal="sources, claims, generated assets", action="Bind strategy, proof, source weights, and falsification tests.", output_artifact="proof packet", quality_gate="source weights and falsification pass"),
        AIGTMWorkflow(stage="Retarget", agent="Paid GTM Agent", input_signal="approved audience and creative", action="Create search/social variants from the wound and mechanism.", output_artifact="ad brief", quality_gate="approval before spend"),
        AIGTMWorkflow(stage="Learn", agent="Calibration Agent", input_signal="reply, meeting, close, no-go", action="Update segment conversion and disqualifier accuracy.", output_artifact="learning log", quality_gate="outcome label captured"),
    ]


def twenty_x_score(brief: StrategyBrief, t: TeaserInput) -> float:
    tier_bonus = {"A": 12, "B": 7, "C": 3}[brief.priority_tier]
    confidence_bonus = {"H": 10, "M": 5, "L": 0}[t.confidence]
    proof_bonus = min(12, len(t.evidence_sources) * 1.5)
    urgency_bonus = max(0, min(10, 18 - t.wound_months))
    return round(min(100, brief.priority_score + tier_bonus + confidence_bonus + proof_bonus + urgency_bonus), 1)


def build_enhanced_strategy(record: dict, strategy_dir: Path, questions_path: str) -> EnhancedGTMStrategy:
    t = TeaserInput.model_validate(record)
    brief = build_strategy_brief(record)
    first_workflow = first_proof_workflow(t)
    score = twenty_x_score(brief, t)
    strategy_md_path = strategy_dir / t.prospect_id / "strategy.md"
    strategy_text = render_strategy_markdown(brief)
    base_hash = stable_hash(strategy_text)

    return EnhancedGTMStrategy(
        prospect_id=t.prospect_id,
        company_name=t.company_name,
        generated_at=now_iso(),
        base_strategy_hash=base_hash,
        strategy_md_path=str(strategy_md_path),
        segment=brief.segment,
        priority_tier=brief.priority_tier,
        priority_score=brief.priority_score,
        twenty_x_score=score,
        expert_lenses=expert_lenses(t, brief),
        ai_gtm_workflows=ai_gtm_workflows(t, brief),
        deviation_moves=deviation_moves(t, brief),
        top_questions=select_questions(t),
        one_big_bet=f"Make {brief.system_name} the account's internal name for turning {first_workflow} into a proof-backed operating system.",
        wedge_upgrade=f"Replace the base offer with a falsifiable {brief.named_mechanism} proof page for {first_workflow}; no implementation starts until the first metric is agreed.",
        brand_upgrade=f"Replace generic AI language with the sentence: {t.company_short} is {t.wound_months} months from {t.wound_channel}; {brief.named_mechanism} turns {first_workflow} into compounding operating memory.",
        sales_motion_upgrade="Sequence every touch from the same proof: wound, mirror, mechanism, disqualifier, close-loop.",
        data_system_upgrade="Capture every source, touch, reply, objection, proposal, proof packet, and outcome back into LakeOS.",
        proof_upgrade="No claim ships unless it has source weights, a falsification test, and a human approval state.",
        next_72_hours=[
            f"Review {strategy_md_path} for obvious false assumptions.",
            f"Create a one-page {brief.named_mechanism} visual map.",
            "Scrape the current website before any proposal customization.",
            "Verify the buyer role and do not send if the role is weak.",
            "Move the account into the Tier A/B/C outbound queue.",
            "Write the account's first proof metric before sending.",
        ],
        no_go_tests=[
            "No visible buyer authority or sponsor.",
            "No data access path for the first proof workflow.",
            "Buyer wants generic AI tools instead of owned operating capability.",
        ],
        global_question_bank_path=questions_path,
        confidence=t.confidence,
    )


def render_enhanced_markdown(enhanced: EnhancedGTMStrategy) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    expert_rows = "\n".join(
        f"| {e.expert} | {e.domain} | {e.process} | {e.prospect_application} |"
        for e in enhanced.expert_lenses
    )
    workflow_rows = "\n".join(
        f"| {w.stage} | {w.agent} | {w.action} | {w.output_artifact} | {w.quality_gate} |"
        for w in enhanced.ai_gtm_workflows
    )
    deviation_rows = "\n".join(
        f"| {d.deviation_sigma:+d} | {d.name} | {d.median_behavior} | {d.rig_move} | {d.required_proof} |"
        for d in enhanced.deviation_moves
    )
    questions = "\n".join(
        f"### {q.id}. {q.question}\n- **Solution:** {q.solution}\n- **Lens:** {q.process_lens}\n- **Gate:** {q.evidence_gate}\n"
        for q in enhanced.top_questions
    )
    return f"""# {enhanced.company_name} — 20x AI GTM Strategy

**For:** {enhanced.generated_for}  
**Tier:** {enhanced.priority_tier}  
**Base priority:** {enhanced.priority_score:.1f}/100  
**20x score:** {enhanced.twenty_x_score:.1f}/100  
**Segment:** {enhanced.segment}  
**Confidence:** {enhanced.confidence}  
**Generated:** {enhanced.generated_at}

## One Big Bet
{enhanced.one_big_bet}

## 20x Upgrades
- **Wedge:** {enhanced.wedge_upgrade}
- **Brand:** {enhanced.brand_upgrade}
- **Sales motion:** {enhanced.sales_motion_upgrade}
- **Data system:** {enhanced.data_system_upgrade}
- **Proof:** {enhanced.proof_upgrade}

## Expert Board Lenses
| Expert | Domain | Process | Application |
|---|---|---|---|
{expert_rows}

## AI GTM Workflows
| Stage | Agent | Action | Artifact | Gate |
|---|---|---|---|---|
{workflow_rows}

## RIG Deviate Engine: -30/+30
| Sigma | Move | Median Behavior | RIG Move | Required Proof |
|---:|---|---|---|---|
{deviation_rows}

## Top 20 Questions Applied
{questions}

## Next 72 Hours
{bullets(enhanced.next_72_hours)}

## No-Go Tests
{bullets(enhanced.no_go_tests)}

## Global Question Bank
`{enhanced.global_question_bank_path}`
"""


def process_one(record: dict, output_dir: str, strategy_dir: str, teaser_dir: str | None, questions_path: str) -> dict:
    try:
        enhanced = build_enhanced_strategy(record, Path(strategy_dir), questions_path)
    except ValidationError as exc:
        return {"prospect_id": record.get("prospect_id", "<unknown>"), "status": "validation_error", "errors": exc.errors()}
    except Exception as exc:  # pragma: no cover
        return {"prospect_id": record.get("prospect_id", "<unknown>"), "status": "generation_error", "error": str(exc), "error_type": type(exc).__name__}

    bundle = Path(output_dir) / enhanced.prospect_id
    bundle.mkdir(parents=True, exist_ok=True)
    json_path = bundle / "gtm20x.json"
    md_path = bundle / "gtm20x.md"
    json_path.write_text(enhanced.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_enhanced_markdown(enhanced), encoding="utf-8")

    if teaser_dir:
        mirror = Path(teaser_dir) / enhanced.prospect_id
        if mirror.exists():
            (mirror / "gtm20x.json").write_text(enhanced.model_dump_json(indent=2), encoding="utf-8")
            (mirror / "gtm20x.md").write_text(render_enhanced_markdown(enhanced), encoding="utf-8")

    return {
        "prospect_id": enhanced.prospect_id,
        "company": enhanced.company_name,
        "status": "ok",
        "segment": enhanced.segment,
        "priority_tier": enhanced.priority_tier,
        "priority_score": enhanced.priority_score,
        "twenty_x_score": enhanced.twenty_x_score,
        "confidence": enhanced.confidence,
        "gtm20x_json": str(json_path),
        "gtm20x_md": str(md_path),
    }


def run_20x_batch(
    input_path: str | Path,
    output_dir: str | Path,
    strategy_dir: str | Path,
    teaser_dir: str | Path | None = None,
    workers: int = 8,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    questions = get_question_bank()
    questions_md = output / "questions_100.md"
    questions_jsonl = output / "questions_100.jsonl"
    system_md = output / "rig_ai_gtm_system.md"
    aggregate_jsonl = output / "gtm20x_1783.jsonl"
    aggregate_csv = output / "gtm20x_1783.csv"
    summary_path = output / "_summary.jsonl"

    questions_md.write_text(render_question_bank_markdown(questions), encoding="utf-8")
    with questions_jsonl.open("w", encoding="utf-8") as f:
        for q in questions:
            f.write(q.model_dump_json() + "\n")
    system_md.write_text(render_gtm_system_markdown(str(questions_md)), encoding="utf-8")

    records = read_jsonl(Path(input_path))
    started = time.time()
    results: list[dict] = []
    ok = err_val = err_gen = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(process_one, r, str(output), str(strategy_dir), str(teaser_dir) if teaser_dir else None, str(questions_md))
            for r in records
        ]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if res["status"] == "ok":
                ok += 1
            elif res["status"] == "validation_error":
                err_val += 1
            else:
                err_gen += 1

    good = [r for r in results if r["status"] == "ok"]
    by_segment = Counter(r["segment"] for r in good)
    by_tier = Counter(r["priority_tier"] for r in good)
    by_conf = Counter(r["confidence"] for r in good)
    elapsed = time.time() - started
    summary = {
        "total": len(records),
        "ok": ok,
        "validation_errors": err_val,
        "generation_errors": err_gen,
        "out_dir": str(output),
        "elapsed_seconds": round(elapsed, 2),
        "rate_per_second": round(len(records) / elapsed if elapsed else 0, 2),
        "workers": workers,
        "generated_for": "RIG and Mike Rodgers",
        "question_count": len(questions),
        "expert_count": len(EXPERTS),
        "by_segment": dict(by_segment.most_common()),
        "by_priority_tier": dict(sorted(by_tier.items())),
        "by_confidence": dict(sorted(by_conf.items())),
        "questions_md": str(questions_md),
        "questions_jsonl": str(questions_jsonl),
        "system_md": str(system_md),
        "aggregate_jsonl": str(aggregate_jsonl),
        "aggregate_csv": str(aggregate_csv),
    }

    with aggregate_jsonl.open("w", encoding="utf-8") as f:
        for row in sorted(good, key=lambda x: (-x["twenty_x_score"], x["company"])):
            full = json.loads(Path(row["gtm20x_json"]).read_text(encoding="utf-8"))
            f.write(json.dumps(full, ensure_ascii=False) + "\n")

    fields = [
        "prospect_id",
        "company",
        "segment",
        "priority_tier",
        "priority_score",
        "twenty_x_score",
        "confidence",
        "gtm20x_md",
        "gtm20x_json",
    ]
    with aggregate_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in sorted(good, key=lambda x: (-x["twenty_x_score"], x["company"])):
            writer.writerow({field: row.get(field, "") for field in fields})

    with summary_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    report = output / "_gtm20x_report.md"
    top = sorted(good, key=lambda x: (-x["twenty_x_score"], x["company"]))[:30]
    lines = [
        "# RIG 20x AI GTM Batch Report",
        "",
        f"- Total: {summary['total']}",
        f"- OK: {summary['ok']}",
        f"- Validation errors: {summary['validation_errors']}",
        f"- Generation errors: {summary['generation_errors']}",
        f"- Expert lenses: {summary['expert_count']}",
        f"- Missing questions with solutions: {summary['question_count']}",
        f"- Generated for: {summary['generated_for']}",
        "",
        "## Top 30 20x Accounts",
        "| Score | Tier | Company | Segment | Path |",
        "|---:|---|---|---|---|",
    ]
    for row in top:
        lines.append(f"| {row['twenty_x_score']:.1f} | {row['priority_tier']} | {row['company']} | {row['segment']} | `{row['gtm20x_md']}` |")
    lines.extend(["", "## System Files", f"- `{system_md}`", f"- `{questions_md}`", f"- `{aggregate_jsonl}`", f"- `{aggregate_csv}`"])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary["report"] = str(report)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False) + "\n" + "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in results) + "\n", encoding="utf-8")
    return {"summary": summary, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RIG 20x AI GTM strategies for all prospects.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strategy-dir", required=True)
    parser.add_argument("--teaser-dir")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    result = run_20x_batch(args.input, args.output, args.strategy_dir, args.teaser_dir, args.workers)
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    s = result["summary"]
    return 0 if s["validation_errors"] == 0 and s["generation_errors"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
