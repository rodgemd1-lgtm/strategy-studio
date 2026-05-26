"""Innovation Methodology Ingestion Module.

Catalogues 16 innovation frameworks as package metadata (no network scraping).
Provides retrieval, combination, cross-domain collision analysis, and generic-phrase scoring.
"""

from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Framework catalog — dict comprehension from a structured source list
# ---------------------------------------------------------------------------

_FRAMEWORK_SOURCE: list[dict[str, Any]] = [
    {
        "id": "strategos",
        "name": "Strategy Safari / Henry Mintzberg School",
        "firm": "Strategos / McGill University",
        "year": 1987,
        "creator": "Henry Mintzberg, Bruce Ahlstrand, Joseph Lampel",
        "category": "strategy",
        "steps": [
            "Identify the dominant strategic paradigm in use",
            "Map deliberate vs emergent strategy tensions",
            "Audit the 10 schools of strategic thought present",
            "Synthesize a configuration-matching strategy profile",
            "Stress-test against environmental turbulence",
        ],
        "mechanism": "Meta-framework taxonomy that reveals which strategic lens an organization defaults to, then forces multi-lens triangulation to break strategic monocultures.",
        "evaluation_criteria": [
            "Number of strategic lenses explicitly considered",
            "Deliberate-emergent tension surfaced and managed",
            "Configuration matched to organizational lifecycle stage",
        ],
        "banned_phrases": ["synergy", "core competency", "best practice", "low-hanging fruit"],
        "cross_domain_potential": ["governance", "product", "policy", "culture"],
    },
    {
        "id": "ideo",
        "name": "Design Thinking (IDEO Human-Centered Design)",
        "firm": "IDEO / d.school Stanford",
        "year": 1991,
        "creator": "David Kelley, Tim Brown, Bill Moggridge",
        "category": "design",
        "steps": [
            "Empathize — immerse in user context through observation and interview",
            "Define — synthesize observations into a pointed point-of-view statement",
            "Ideate — diverge with brainstorming, then converge on promising concepts",
            "Prototype — build rapid, low-fidelity representations of ideas",
            "Test — put prototypes in front of real users and iterate",
        ],
        "mechanism": "Human-centered iterative loop that converts latent user needs into validated solution concepts through rapid prototyping and feedback.",
        "evaluation_criteria": [
            "Depth of ethnographic evidence gathered",
            "Point-of-view statement specificity",
            "Prototype fidelity matched to learning stage",
            "Number of test-iterate cycles completed",
        ],
        "banned_phrases": ["think outside the box", "disruption", "innovation", "pivot"],
        "cross_domain_potential": ["service_design", "healthcare", "education", "policy"],
    },
    {
        "id": "frog",
        "name": "Creative Leadership / Frog Design Method",
        "firm": "Frog Design (formerly frog design)",
        "year": 1969,
        "creator": "Hartmut Esslinger",
        "category": "design",
        "steps": [
            "Uncover — research cultural and technological context deeply",
            "Conceive — generate bold design visions aligned to brand essence",
            "Architect — define system-level interaction and experience models",
            "Engineer — build production-ready prototypes with engineering rigor",
            "Evaluate — measure emotional response and usability at scale",
        ],
        "mechanism": "Integrated design-engineering workflow that fuses brand narrative with human factors to produce emotionally resonant, manufacturable products.",
        "evaluation_criteria": [
            "Cultural context research breadth",
            "Design vision boldness score",
            "System-level coherence across touchpoints",
            "Manufacturability and cost feasibility",
        ],
        "banned_phrases": ["user-centric", "seamless experience", "world-class", "cutting-edge"],
        "cross_domain_potential": ["brand", "industrial_design", "ux", "architecture"],
    },
    {
        "id": "sit",
        "name": "Systematic Inventive Thinking (SIT)",
        "firm": "SIT — Systematic Inventive Thinking",
        "year": 1995,
        "creator": "Jacob Goldenberg, Roni Horowitz, Amnon Levav, Gina Colarelli O'Connor",
        "category": "structured_innovation",
        "steps": [
            "Define the closed world — identify only existing components and their relationships",
            "Apply Subtraction — remove an essential component and reassign its functions",
            "Apply Multiplication — duplicate a component but change it in some way",
            "Apply Division — split a component or its functions and re-arrange spatially/temporally",
            "Apply Task Unification — assign a new task to an existing component",
            "Apply Attribute Dependency — link two previously independent attributes",
        ],
        "mechanism": "Constraint-based innovation using five fixed cognitive operators applied inside the 'closed world' of an existing product, ensuring ideas are feasible and novel simultaneously.",
        "evaluation_criteria": [
            "Closed-world constraint respected (no foreign components introduced)",
            "At least three SIT operators applied and documented",
            "Functional viability of resulting virtual product",
            "Novelty relative to existing category offerings",
        ],
        "banned_phrases": ["breakthrough", "paradigm shift", "next-gen", "revolutionary"],
        "cross_domain_potential": ["product", "packaging", "marketing", "process"],
    },
    {
        "id": "board_of_innovation",
        "name": "Business Model Innovation / Board of Innovation Method",
        "firm": "Board of Innovation",
        "year": 2008,
        "creator": "Michael Kleysen",
        "category": "business_model",
        "steps": [
            "Map the current business model canvas in detail",
            "Generate 60+ creative business model ideas using structured brainstorming",
            "Filter ideas through desirability, feasibility, viability lenses",
            "Prototype top 3 models as one-page business model canvases",
            "Test key assumptions with real customers and partners",
            "Pitch and select the winning model for execution",
        ],
        "mechanism": "Divergent-convergent ideation system that generates a large quantity of business model options, then uses structured filters and real-world testing to isolate the most promising model.",
        "evaluation_criteria": [
            "Number of distinct business model ideas generated (>40 minimum)",
            "Customer assumption validation rigor",
            "Feasibility of revenue mechanics",
            "Scalability evidence from prototype tests",
        ],
        "banned_phrases": ["platform", "ecosystem", "network effects", "winner-takes-all"],
        "cross_domain_potential": ["nonprofit", "government", "healthcare", "energy"],
    },
    {
        "id": "innosight",
        "name": "Horizon Model / Three Horizons of Growth",
        "firm": "Innosight (Clayton Christensen)",
        "year": 2000,
        "creator": "Clayton Christensen, Scott Anthony, Erik Roth",
        "category": "strategy",
        "steps": [
            "Map all current initiatives onto Horizon 1 (core), Horizon 2 (emerging), Horizon 3 (experimental)",
            "Assess time-to-materiality and investment level for each horizon",
            "Identify disruption threats and asymmetric competitors in each horizon",
            "Rebalance portfolio to maintain 70/20/10 or appropriate allocation",
            "Kill or accelerate initiatives based on strategic fit and momentum",
        ],
        "mechanism": "Portfolio management framework that categorizes innovation efforts by maturity horizon, enabling simultaneous optimization of today's business and creation of tomorrow's.",
        "evaluation_criteria": [
            "Correct horizon classification of all major initiatives",
            "Portfolio balance aligned to strategic ambition",
            "Evidence of Horizon 3 option creation",
            "Kill/accelerate decisions made on data, not politics",
        ],
        "banned_phrases": ["disruptive innovation", "move fast", "fail fast", "agile"],
        "cross_domain_potential": ["corporate_strategy", "venture", "R&D", "public_sector"],
    },
    {
        "id": "doblin",
        "name": "Ten Types of Innovation (Doblin/Deloitte)",
        "firm": "Doblin (now Deloitte)",
        "year": 2009,
        "creator": "Larry Keeley, Helen Walters, Brian Quinn, Ryan Pikkel",
        "category": "structured_innovation",
        "steps": [
            "Audit current innovation efforts across all 10 types",
            "Score each type on effort and investment level",
            "Identify the 2-3 most under-invested types with highest leverage",
            "Design specific initiatives targeting the gap types",
            "Ensure at least 3 types are active in any innovation portfolio",
        ],
        "mechanism": "Taxonomy of innovation that separates it from pure product R&D, revealing that most organizations over-index on product performance while neglecting business model, organization, and network innovations.",
        "evaluation_criteria": [
            "Audit covers all 10 types (not just product)",
            "Investment gap analysis completed",
            "At least two non-product innovation types activated",
            "Innovation portfolio diversified across type categories",
        ],
        "banned_phrases": ["idea generation", "hackathon", "ideation lab", "brainstorm"],
        "cross_domain_potential": ["corporate", "startup", "government", "social_enterprise"],
    },
    {
        "id": "synectics",
        "name": "Synectics (Making the Strange Familiar)",
        "firm": "Synectics (founded by William J.J. Gordon & George M. Prince)",
        "year": 1961,
        "creator": "William J.J. Gordon, George M. Prince",
        "category": "creative_problem_solving",
        "steps": [
            "Describe the present situation as thoroughly as possible",
            "Make the strange familiar — analyze and define the problem clearly",
            "Create direct analogies — borrow metaphors from distant domains",
            "Create personal analogies — become the object of study",
            "Create compressed contradictions — compress two opposite ideas into one phrase",
            "Re-examine the original problem in light of analogical insights",
        ],
        "mechanism": "Metaphor-driven creative process that uses psychological detachment (making the familiar strange) to bypass habitual thinking and generate novel insights through forced analogy.",
        "evaluation_criteria": [
            "At least two direct analogies from unrelated domains",
            "Personal analogy genuinely experienced (not merely described)",
            "Compressed contradiction yields actionable reframe",
            "Final solution traceable to analogical insight",
        ],
        "banned_phrases": ["creative", "brainstorming", "open mind", "outside the box"],
        "cross_domain_potential": ["engineering", "advertising", "biotech", "music"],
    },
    {
        "id": "brainzooming",
        "name": "Brainzooming — Structured Brainstorming Cascade",
        "firm": "Brainzooming (Brainzooming Group LLC)",
        "year": 2005,
        "creator": "Tristan Kromer",
        "category": "creative_problem_solving",
        "steps": [
            "Define a precise creative question using 'How might we…' format",
            "Generate solo silent ideas (individual divergent phase)",
            "Cascade and build on each other's ideas in structured rounds",
            "Evaluate ideas against clear criteria using dot voting or scoring",
            "Select top concepts and develop mini-proposals",
            "Repeat cascading for top concepts to add depth",
        ],
        "mechanism": "Cascading ideation structure that combines individual creative production with structured group building, ensuring psychological safety and maximum diversity of input before convergence.",
        "evaluation_criteria": [
            "Question framing is specific and actionable",
            "Individual ideation phase truly silent and independent",
            "Cascading builds substantively (not just agreement)",
            "Voting/scoring criteria defined before evaluation",
        ],
        "banned_phrases": ["no bad ideas", "yes and", "let's brainstorm", "green light"],
        "cross_domain_potential": ["product", "marketing", "process_improvement", "culture_change"],
    },
    {
        "id": "cps",
        "name": "Creative Problem Solving (CPS) Osborne-Parnes Model",
        "firm": "Creative Education Foundation / Buffalo State University",
        "year": 1953,
        "creator": "Alex Osborn, Sidney Parnes",
        "category": "creative_problem_solving",
        "steps": [
            "Mess-finding — scan the environment for problem opportunities",
            "Fact-finding — gather all relevant data and perspectives",
            "Problem-finding — frame the most important challenge statements",
            "Idea-finding — generate a large quantity of solution ideas",
            "Solution-finding — evaluate ideas against weighted criteria",
            "Acceptance-finding — plan for adoption and overcoming resistance",
        ],
        "mechanism": "Six-stage analytic-creative process that formalizes the full innovation lifecycle from opportunity detection through implementation planning, alternating between divergent and convergent thinking at each stage.",
        "evaluation_criteria": [
            "Each of the six stages completed with documented output",
            "Divergent phase deliberately separated from convergent phase",
            "Problem statement refined from initial mess",
            "Acceptance plan addresses key stakeholder resistance",
        ],
        "banned_phrases": ["innovation workshop", "creative session", "ideate", "blue sky"],
        "cross_domain_potential": ["education", "healthcare", "social_services", "government"],
    },
    {
        "id": "triz",
        "name": "TRIZ (Theory of Inventive Problem Solving)",
        "firm": "TRIZ (originally USSR / GEN3 Partners / Ideation International)",
        "year": 1946,
        "creator": "Genrich Altshuller",
        "category": "structured_innovation",
        "steps": [
            "Define the Ideal Final Result (IFR) — the perfect solution with no cost",
            "Identify the contradiction — what improves and what worsens",
            "Classify as technical contradiction or physical contradiction",
            "Use the 40 Inventive Principles matched via Contradiction Matrix",
            "Apply standard solutions from the 76 Standard Inventive Solutions",
            "Evaluate solution against known patterns of technology evolution",
        ],
        "mechanism": "Engineering-innovation method based on analysis of 40,000+ patents that reveals recurring inventive principles. Converts vague 'be creative' prompts into systematic contradiction-resolution patterns.",
        "evaluation_criteria": [
            "Contradiction clearly articulated (not just a trade-off)",
            "IFR defined with function, not form",
            "At least 3 of the 40 principles considered",
            "Solution follows known technology evolution patterns",
        ],
        "banned_phrases": ["innovation", "thinking", "idea", "creative"],
        "cross_domain_potential": ["engineering", "software", "manufacturing", "medical_devices"],
    },
    {
        "id": "scamper",
        "name": "SCAMPER",
        "firm": "Eberle / Osborn",
        "year": 1971,
        "creator": "Bob Eberle (based on Alex Osborn's work)",
        "category": "structured_innovation",
        "steps": [
            "Substitute — what components, materials, or processes can be swapped?",
            "Combine — what features, ideas, or steps can be merged?",
            "Adapt — what else is like this? What can be adjusted from another context?",
            "Modify/Magnify/Minimize — change size, shape, form, or other attributes?",
            "Put to other uses — how else can this be used in different contexts?",
            "Eliminate — what can be removed, simplified, or reduced?",
            "Reverse/Rearrange — what happens if flipped, inverted, or re-ordered?",
        ],
        "mechanism": "Checklist-based modifier set that forces systematic variation of an existing product, service, or process by running each of seven transformation verbs against it.",
        "evaluation_criteria": [
            "All seven SCAMPER verbs addressed",
            "At least one actionable concept per verb",
            "Concepts evaluated for feasibility within existing constraints",
            "Winner concepts prototyped or storyboarded",
        ],
        "banned_phrases": ["transformative", "game-changing", "innovative", "best-in-class"],
        "cross_domain_potential": ["product", "content", "process", "service_design"],
    },
    {
        "id": "biomimicry",
        "name": "Biomimicry Thinking",
        "firm": "Biomimicry Institute / Biomimicry 3.8",
        "year": 1997,
        "creator": "Janine Benyus, Dayna Baumeister",
        "category": "nature_inspired",
        "steps": [
            "Define the functional need (what must the solution accomplish?)",
            "Biologize the question — ask 'How does nature do this?'",
            "Discover — research organisms and ecosystems solving analogous challenges",
            "Abstract — extract the underlying biological strategy as a design principle",
            "Emulate — translate the principle into a human technology or process",
            "Evaluate — test against life's principles (nature runs on sunlight, uses only the energy it needs, etc.)",
        ],
        "mechanism": "Translating 3.8 billion years of evolutionary R&D into design solutions by systematically finding biological analogues and abstracting their functional principles.",
        "evaluation_criteria": [
            "Biological analogy genuinely researched (not superficial metaphor)",
            "Design principle abstracted at functional (not aesthetic) level",
            "Emulated solution tested against Life's Principles",
            "Functional equivalence demonstrated, not just inspiration claimed",
        ],
        "banned_phrases": ["natural", "green", "sustainable", "organic"],
        "cross_domain_potential": ["architecture", "materials_science", "agriculture", "robotics"],
    },
    {
        "id": "blue_ocean",
        "name": "Blue Ocean Strategy",
        "firm": "INSEAD",
        "year": 2005,
        "creator": "W. Chan Kim, Renée Mauborgne",
        "category": "strategy",
        "steps": [
            "Map the current industry's factors of competition (Strategy Canvas)",
            "Apply the ERRC Grid: Eliminate, Reduce, Raise, Create factors",
            "Identify the new value curve that breaks the value-cost trade-off",
            "Pioneer the new market space with a focused strategic narrative",
            "Build execution alignment: utility, price, cost, adoption hurdles",
        ],
        "mechanism": "Demand-side innovation framework that creates new market space by simultaneously pursuing differentiation and low cost, breaking the traditional value-cost trade-off through four strategic actions on industry factors.",
        "evaluation_criteria": [
            "Strategy Canvas completed with at least 8 industry factors",
            "ERRC grid produces a genuinely new value curve (not incremental improvement)",
            "Clear non-customer segment identified",
            "Execution plan addresses all four utility/price/cost/adoption hurdles",
        ],
        "banned_phrases": ["competitive advantage", "benchmarking", "market leadership", "dominant player"],
        "cross_domain_potential": ["nonprofit", "government", "education", "healthcare"],
    },
    {
        "id": "jobs_to_be_done",
        "name": "Jobs-to-be-Done (JTBD)",
        "firm": "Clayton Christensen / Bob Moesta / Tony Ulwick (Outcome-Driven Innovation)",
        "year": 1999,
        "creator": "Clayton Christensen, Bob Moesta, Tony Ulwick",
        "category": "customer_insight",
        "steps": [
            "Identify the functional, emotional, and social jobs customers are trying to get done",
            "Map the job-steps of the core functional job",
            "Uncover underserved and overserved outcomes using importance-satisfaction gaps",
            "Segment customers by job, not by demographic",
            "Design solutions that 'hire' to get the job done better",
            "Validate with switch interviewing — why did the customer stop using the old solution?",
        ],
        "mechanism": "Jobs-based market theory that defines markets around the progress a person is trying to make in a given circumstance, replacing demographic segmentation with need-based segmentation to reveal non-obvious innovation opportunities.",
        "evaluation_criteria": [
            "Job statement references circumstance, not solution",
            "Job map has 8-15 defined job steps",
            "Importance-satisfaction gap analysis completed for all outcomes",
            "At least one underserved outcome identified as innovation target",
        ],
        "banned_phrases": ["customer-centric", "pain point", "value proposition", "user story"],
        "cross_domain_potential": ["healthcare", "education", "financial_services", "public_services"],
    },
    {
        "id": "effectuation",
        "name": "Effectuation",
        "firm": "Saras Sarasvathy / University of Virginia",
        "year": 2001,
        "creator": "Saras Sarasvathy",
        "category": "entrepreneurship",
        "steps": [
            "Start with Means — inventory who you are, what you know, whom you know",
            "Set Affordable Loss — decide what you're willing to lose (not expected return)",
            "Leverage Contingencies — treat surprises as opportunities, not problems",
            "Form Partnerships — secure pre-commitments from stakeholders before acting",
            "Control the Future — create new markets rather than predict existing ones",
        ],
        "mechanism": "Expert entrepreneur logic of action under uncertainty that replaces predictive planning with means-based action, affordable loss, stakeholder commitment, and contingency leverage.",
        "evaluation_criteria": [
            "Means inventory completed before opportunity analysis",
            "Affordable loss threshold set (not ROI projection)",
            "At least one stakeholder pre-commitment secured",
            "Plan adapts to contingency inputs during execution",
        ],
        "banned_phrases": ["business plan", "market research", "predictable", "scalable model"],
        "cross_domain_potential": ["social_enterprise", "corporate_intrapreneurship", "art", "research"],
    },
]

# Build canonical METHODOLOGIES dict via comprehension
METHODOLOGIES: dict[str, dict[str, Any]] = {
    fw["id"]: {
        "id": fw["id"],
        "name": fw["name"],
        "firm": fw["firm"],
        "year": fw["year"],
        "creator": fw["creator"],
        "steps": fw["steps"],
        "mechanism": fw["mechanism"],
        "evaluation_criteria": fw["evaluation_criteria"],
        "banned_phrases": fw["banned_phrases"],
        "cross_domain_potential": fw["cross_domain_potential"],
        "category": fw["category"],
    }
    for fw in _FRAMEWORK_SOURCE
}

# Convenience index by category
_CATEGORY_INDEX: dict[str, list[str]] = {}
for _key, _val in METHODOLOGIES.items():
    _cat = _val["category"]
    _CATEGORY_INDEX.setdefault(_cat, []).append(_key)


# ---------------------------------------------------------------------------
# MethodologyLibrary
# ---------------------------------------------------------------------------

class MethodologyLibrary:
    """Retrieve, combine, and score innovation methodology frameworks."""

    def __init__(self, methodologies: dict[str, dict[str, Any]] | None = None) -> None:
        self._data: dict[str, dict[str, Any]] = methodologies if methodologies is not None else deepcopy(METHODOLOGIES)
        self._category_index: dict[str, list[str]] = {}
        for _k, _v in self._data.items():
            self._category_index.setdefault(_v["category"], []).append(_k)

    # -- public API ---------------------------------------------------------

    def get_all(self) -> list[dict[str, Any]]:
        """Return a list of every methodology."""
        return list(self._data.values())

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return methodologies filtered by category (case-insensitive)."""
        cat = category.lower().strip()
        ids = self._category_index.get(cat, [])
        return [self._data[i] for i in ids]

    def get_random(self, n: int, seed: int | None = None) -> list[dict[str, Any]]:
        """Return *n* random methodologies. Deterministic when seed is set."""
        rng = random.Random(seed)
        keys = list(self._data.keys())
        if n >= len(keys):
            chosen = keys
        else:
            chosen = rng.sample(keys, n)
        return [self._data[k] for k in chosen]

    def combine(self, m1_id: str, m2_id: str) -> dict[str, Any]:
        """Cross-domain collision: produce a hybrid framework from two methodologies.

        The hybrid merges steps, evaluation criteria, cross-domain potential,
        and banned phrases while interleaving both mechanisms.
        """
        a = self._data[m1_id]
        b = self._data[m2_id]

        hybrid_key = f"{m1_id}_x_{m2_id}"
        hybrid_name = f"{a['name']} x {b['name']}"
        hybrid_category = f"{a['category']}+{b['category']}"

        # Interleave steps alternately
        merged_steps: list[str] = []
        for i in range(max(len(a["steps"]), len(b["steps"]))):
            if i < len(a["steps"]):
                merged_steps.append(f"[{a['id']}] {a['steps'][i]}")
            if i < len(b["steps"]):
                merged_steps.append(f"[{b['id']}] {b['steps'][i]}")

        merged_criteria = list(dict.fromkeys(a["evaluation_criteria"] + b["evaluation_criteria"]))
        merged_cross_domain = list(dict.fromkeys(a["cross_domain_potential"] + b["cross_domain_potential"]))
        merged_banned = list(dict.fromkeys(a["banned_phrases"] + b["banned_phrases"]))

        return {
            "id": hybrid_key,
            "name": hybrid_name,
            "firm": f"Hybrid: {a['firm']} + {b['firm']}",
            "year": max(a["year"], b["year"]),
            "creator": f"Hybrid: {a['creator']} + {b['creator']}",
            "steps": merged_steps,
            "mechanism": (
                f"Hybrid collision of {a['name']} and {b['name']}.\n"
                f"First lens: {a['mechanism']}\n"
                f"Second lens: {b['mechanism']}\n"
                f"Collision space: The {a['category']} dimension meets the "
                f"{b['category']} dimension, creating novel affordances at the intersection."
            ),
            "evaluation_criteria": merged_criteria,
            "banned_phrases": merged_banned,
            "cross_domain_potential": merged_cross_domain,
            "category": hybrid_category,
            "source_ids": [m1_id, m2_id],
        }

    def find_mouth(self, name: str) -> dict[str, Any]:
        """Return canonical source info for a methodology by id or name (partial match)."""
        # Exact id match
        if name in self._data:
            return self._data[name]

        # Partial name match
        needle = name.lower().strip()
        for _k, _v in self._data.items():
            if needle in _v["name"].lower() or needle in _v["firm"].lower() or needle in _v["creator"].lower():
                return _v

        raise KeyError(f"No methodology found matching '{name}'")

    def score_generic_penalty(self, text: str) -> float:
        """Return a penalty score [0.0, 1.0] for generic/banned phrase usage.

        Fraction of all banned phrases across all methodologies that appear
        in the given text. Higher score = more generic language detected.
        """
        all_banned: set[str] = set()
        for _v in self._data.values():
            for phrase in _v["banned_phrases"]:
                all_banned.add(phrase.lower())

        if not all_banned:
            return 0.0

        text_lower = text.lower()
        hits = sum(1 for phrase in all_banned if phrase in text_lower)
        return hits / len(all_banned)

    def to_json(self, path: str | Path | None = None) -> str:
        """Export all methodologies as JSON string. If *path* is given, write to file."""
        serialized = {_k: _v for _k, _v in sorted(self._data.items())}
        json_str = json.dumps(serialized, indent=2, ensure_ascii=False)
        if path is not None:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json_str, encoding="utf-8")
        return json_str
