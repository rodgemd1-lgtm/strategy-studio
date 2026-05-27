"""Copy-paste-ready edit suggestions per failed criterion.

Used by `rig-strict fix`. Returns a short snippet a user can drop into their doc
to address a specific failed required question.
"""
from __future__ import annotations


# Map (slug, question_id_prefix) → suggestion snippet
SUGGESTIONS = {
    ("gravity_escape", "g1"): "Remove 'leverage' from the doc (Cmd-F → delete).",
    ("gravity_escape", "g2"): "Remove 'synergy' / 'holistic'.",
    ("gravity_escape", "g3"): "Replace 'in today's landscape' / 'rapidly evolving' with a specific year and trend.",
    ("gravity_escape", "g4"): "Remove 'we are excited to announce' / 'pleased to share'.",
    ("gravity_escape", "g5"): "Remove 'thought leadership', 'best practices', 'world-class', 'cutting-edge'.",
    ("gravity_escape", "g6"): "Remove 'furthermore' / 'moreover' — restructure sentence flow.",

    ("reality_anchor", "a1"): "Add ≥3 primary sources by name: 'Research and Markets (Jan 2025)', 'Mordor Intelligence (Q2 2025)', 'Helios Technologies 10-K (FY25)'.",
    ("reality_anchor", "a2"): "Date every source: 'April 2025', 'Q3 FY26', 'Nov 10 2026'.",
    ("reality_anchor", "a8"): "Add a 'Falsification Calendar' section with ≥3 dated kill criteria.",
    ("reality_anchor", "a10"): "Name the load-bearing claim: 'If [metric] fails, the whole thesis collapses'.",

    ("mechanism_furnace", "f1"): "Insert ≥4 causal connectives per 1000 words ('because', 'leads to', '→').",
    ("mechanism_furnace", "f2"): "Add a chain: 'Input → Activity → Behavior → System → Economic → Loop' for the core capability.",
    ("mechanism_furnace", "f5"): "Name 2 compounding loops: 'each new OEM brings 200-2000 vehicles into the learning loop'.",

    ("temporal_horizon_integrity", "h2"): "Add a 'leading indicator' line: 'Weekly: stakeholder interviews completed'.",
    ("temporal_horizon_integrity", "h4"): "Sharpen kill criteria: 'No paid OEM by Month 8 → rescope to Forge Vault internal-only by Q3 2027'.",
    ("temporal_horizon_integrity", "h6"): "Add Year-by-year revenue: 'Year 1 $68M → Year 2 $90M → Year 3 $130M'.",

    ("rupture", "b1"): "Add explicit refusal: 'We will not deploy a Copilot bolt-on. We will not run an AI Center of Excellence'.",
    ("rupture", "b2"): "Name the orthodoxy being demolished: 'The conventional move is X. We refuse.'",
    ("rupture", "b3"): "Add 'from first principles' reset: 'What if [industry-default] didn't exist? What would we build?'",
    ("rupture", "b10"): "Add a radical reframe: 'HED is not a controller OEM. HED is the Bloomberg of fleet intelligence.'",

    ("bayesian_calibration", "y2"): "Add a conditional probability: 'P(Parker accelerates | Camgian closes ≥2 OEMs by Q3 2026) = 60%'.",
    ("bayesian_calibration", "y3"): "Anchor to base rate: 'Helios Technologies grew Electronics from $0 to $298M in 9 years — base rate for this category transformation'.",
    ("bayesian_calibration", "y7"): "Name a next-update event: 'This probability updates when Camgian closes its first integrated OEM (expected Q3 2026)'.",
    ("bayesian_calibration", "y10"): "Add: 'We maintain a Brier-score log of every dated prediction in this document. Calibration table publishes at Month 9.'",

    ("bell_entanglement", "bl1"): "Co-locate claim + evidence: 'Y3 base $68M (Helios 10-K FY15-25 base rate) [...]'.",
    ("bell_entanglement", "bl2"): "Add kill text within 800 chars of every revenue claim: 'Kill criterion: if attach <8% by Month 18 → rescope by Q3 2027'.",
    ("bell_entanglement", "bl4"): "Add a Falsification Calendar table.",
    ("bell_entanglement", "bl5"): "Name the load-bearing assumption: 'If the AI feature attach rate fails, the whole Y3 projection collapses.'",
    ("bell_entanglement", "bl6"): "In executive summary: put claim + source + kill criterion in the same sentence.",

    ("absolute_zero", "k1"): "Remove 'zero downtime' — replace with 'OTA-delivered firmware reduces field-service visits by 40%'.",
    ("absolute_zero", "k2"): "Remove 'perfect uptime' / 'perfectly reliable' — qualify with conditions.",
    ("absolute_zero", "k3"): "Remove 'always works' / 'never fails' — say 'fails open under condition X'.",
    ("absolute_zero", "k4"): "Remove unqualified '100%' — bound to a scope.",

    ("pauli_exclusion", "p1"): "Remove duplicated section headers.",
    ("pauli_exclusion", "p3"): "Remove 'In conclusion' / 'To summarize' / 'In summary'.",
    ("pauli_exclusion", "p5"): "Remove duplicated paragraphs (≥80 chars appearing twice).",

    ("critical_phase", "c1"): "Add 2+ commitment phrases: 'We commit to X by Y'. 'Past this point, no retreat'.",
    ("critical_phase", "c4"): "Add skin-in-the-game: 'Production-or-nothing guarantee — extend at no fee or refund pro-rata'.",

    ("cognitive_sovereignty", "sh1"): "Add an 'Attacks Survived' section with 5 explicit attacks + rebuttals.",
    ("cognitive_sovereignty", "sh2"): "Add 'Hill family attack — why now?' rebuttal section.",
    ("cognitive_sovereignty", "sh7"): "Title the rebuttal index: 'Attacks Survived'.",
    ("cognitive_sovereignty", "sh10"): "Add: 'Your choice. Your call. The board approves.'",

    ("frame_collision", "co1"): "Add a 'Frame: Defense procurement' header.",
    ("frame_collision", "co2"): "Add a 'Frame: Developer platform economics' header.",
    ("frame_collision", "co3"): "Add a 'Frame: Electrification' header.",
    ("frame_collision", "co5"): "Add an explicit mechanism import: 'Like Bloomberg, Forge Net aggregates anonymized signals'.",
    ("frame_collision", "co6"): "Use literal 'Frame:' prefix in section headers (the colon matters for detection).",

    ("hawking_horizon", "hg1"): "Add ≥6 'we have / we own / we built / we deliver / we ship' statements.",
    ("hawking_horizon", "hg2"): "Name specific assets: 'CMMC Level 2 certification, $10.4M federal contracts, 24 shipping SKUs, CL-4002 silicon'.",

    ("fine_structure", "pa1"): "Remove 'very', 'really', 'quite' as intensifiers.",
    ("fine_structure", "pa2"): "Remove 'plans and strategies' / 'goals and objectives' (redundant pairings).",

    ("vacuum_zeropoint", "zp1"): "Add more specific dollar amounts (target: ≥15 in the doc).",
    ("vacuum_zeropoint", "zp2"): "Add more specific percentages (target: ≥10).",
    ("vacuum_zeropoint", "zp3"): "Add more specific time units (target: ≥8).",

    ("predictive_surprise", "su1"): "Add: 'Most assume X, but Y' — at least one counter-intuitive finding.",
    ("predictive_surprise", "su4"): "Add: 'Contrary to industry consensus, we believe X'.",

    ("levy_flight", "al1"): "Add ≥2 cross-domain analogies (Bloomberg, iOS, Stripe, Tesla, Topcon).",

    ("pheromone_swarm", "sw4"): "Compare paths on ≥2 dimensions: 'Path A is faster but riskier than Path B'.",
    ("pheromone_swarm", "sw5"): "Add per-path kill: 'Path A kill: no defense AI pilot by Month 8 → switch to Path B'.",

    ("physarum_prune", "sl1"): "Explicitly kill ≥2 paths: 'We killed the chatbot-bolt-on approach because [...]'.",
    ("physarum_prune", "sl2"): "Add 'killed because' / 'abandoned because' phrasing.",

    ("clonal_refinement", "cl1"): "Add 'refined / tightened / sharpened' markers describing what improved.",
    ("clonal_refinement", "cl4"): "Add 'What changed from v1' note.",

    ("zeigarnik_residue", "z3"): "Add phase transition hook: 'Phase 1 sets up Phase 2: capacity defines who can build'.",
    ("zeigarnik_residue", "z4"): "Put a question in the first 500 chars: 'The real question is whether HED names this category — or explains, in 18 months, why Grayhill did.'",

    ("memory_residue", "e8"): "Add concrete examples: 'For example, the CL-714 in a Pierce fire truck...' (≥3 such examples).",

    ("opponent_process", "r1"): "Add ≥6 contrast connectives ('but', 'however', 'yet', 'whereas').",
    ("opponent_process", "r3"): "Acknowledge specific risk per bet: 'Risk: Path A could fail if [X]; mitigation: [Y]'.",
    ("opponent_process", "r4"): "Add a concession: 'We accept that Bosch wins commercial telematics — acceptable tradeoff.'",

    ("somatic_stakes", "vi2"): "Weave 'your team / your engineers / your customers / your moat' throughout (≥3 mentions).",

    ("kolmogorov_originality", "gl6"): "Add an extended metaphor: 'Forge is the Bloomberg of fleet intelligence' or 'the iOS of CAN-bus'.",
    ("kolmogorov_originality", "gl9"): "Add a $ amount in the first 500 chars: 'The ask: $185K Activation'.",

    ("bioluminescent_attraction", "lu1"): "Add $/unit attach lines per capability: 'predictive diagnostics: $30/unit; OTA: $20/mo per fleet'.",
    ("bioluminescent_attraction", "lu3"): "Add software ARR path: 'Software ARR Y3 $8-10M from 40 OEMs'.",

    ("chemotaxis_gradient", "ch4"): "Add cadence markers: 'weekly review', 'monthly cadence', 'quarterly review'.",
    ("chemotaxis_gradient", "ch5"): "Add per-phase decision: 'Phase 2 decision: go/no-go on first OEM pilot'.",
    ("chemotaxis_gradient", "ch6"): "Add pivot rule: 'If signal weak by Month 8, pivot to Forge Vault internal-only'.",

    ("mycorrhizal_root", "rt1"): "Add 'we embed / we run with you / we build the system'.",
    ("mycorrhizal_root", "rt2"): "Add 'HED owns the system / you own the data / the platform stays yours'.",
    ("mycorrhizal_root", "rt3"): "Add hand-off stages: 'Build 100% → Hand-off 62% → Advisory 33% → System owner optional'.",

    ("humpback_spiral", "hu2"): "Add 'narrow from broad', 'consolidate', 'productize' language describing phase tightening.",
    ("humpback_spiral", "hu5"): "Show retainer step-down: 'Retainer $22K/mo m1-6 → $13.5K/mo m7-9 → $14K/mo m10-15'.",

    ("cuckoo_parasitic", "cu2"): "Name the orthodoxy demolished: 'industry assumes X. We reject that orthodoxy'.",
    ("cuckoo_parasitic", "cu3"): "Add 'from first principles' reset language.",
    ("cuckoo_parasitic", "cu6"): "Reframe explicitly: 'The real category is X' (not just 'a better controller').",

    ("coral_reef_synthesis", "re2"): "Name 2 combination modes: 'broadcast' (mass-distribute) and 'brood' (keep internal).",
    ("coral_reef_synthesis", "re5"): "Add: 'We prune the chatbot-bolt-on offering because it's stale, low signal, and consultant theater'.",

    ("quantum_tunnel", "tu2"): "Avoid literal 'Copilot bolt-on' / 'AI Center of Excellence' even when refusing them. Rephrase as 'chatbot overlay' / 'excellence program'.",
    ("quantum_tunnel", "tu4"): "Add: 'Contrary to industry consensus, we believe Parker cannot ship Camgian AI in 6 months.'",

    ("feynman_xray", "x1"): "Increase how/why/because density (target: ≥8 per 1000 words).",
    ("feynman_xray", "x3"): "Name specific signals: 'J1939 PGN deltas, hydraulic pressure variance, current draw skew'.",
    ("feynman_xray", "x6"): "Add inference latency: '<50ms p99 on CL-4002 silicon'.",
    ("feynman_xray", "x7"): "Add failure mode: 'The model could fail if [scenario]; we handle it via [mitigation]'.",

    ("voltage", "v2"): "Name the cost of NOT moving: 'margin compression 35% → 30-32% by 2028, moat dissipation'.",
    ("voltage", "v3"): "Add operational drain: '14-day proposal cycle costs you RFQs you never see lost'.",

    ("darwinian_selection", "d1"): "Add ≥2 named alternatives: 'Option A: defense-first. Option B: commercial platform.'",
    ("darwinian_selection", "d5"): "Add counterfactual: 'Do nothing → Y3 $63-67M with margin compression'.",
    ("darwinian_selection", "d7"): "Add pre-mortem with 3+ ranked failure modes.",
    ("darwinian_selection", "d8"): "Each phase gets its own kill: 'Month 8: no paid pilot → rescope'.",

    ("autonomy_calibration", "so1"): "Add 'your choice' / 'opt-out' language.",
    ("autonomy_calibration", "so2"): "Add 3 priced tiers (Diagnostic $95K, Activation $185K, Transformation $485K).",
    ("autonomy_calibration", "so7"): "Avoid 'exclusive' / 'irrevocable' / 'locked in'.",

    ("signal_to_noise", "ps3"): "Remove 'clearly' / 'obviously' / 'as everyone knows'.",
    ("signal_to_noise", "ps5"): "Remove 'It should be noted' / 'It is worth mentioning' throat-clearing.",

    ("hermeneutic_density", "w1"): "Add ≥3 numbered footnotes [1] [2] [3] with full source details.",
    ("hermeneutic_density", "w6"): "Show methodology: 'triangulated from 3 sources', 'bottom-up TAM derivation'.",
    ("hermeneutic_density", "w7"): "Add sensitivity bands: 'downside $58M / base $68M / upside $83M'.",

    ("casimir_force", "cs2"): "Break paragraphs >800 chars — add line breaks.",
    ("casimir_force", "cs3"): "Add 4+ short standalone paragraphs (≤200 chars each).",
    ("casimir_force", "cs4"): "Add 4+ bullet/numbered list items (use literal '- item' or '1. item' at line start).",
}


def suggest_for(slug: str, qid: str, q: dict) -> str | None:
    """Return a copy-paste-ready edit for this failed criterion, or None."""
    # Try exact match first
    qid_prefix = qid.split("_")[0]
    key = (slug, qid_prefix)
    if key in SUGGESTIONS:
        return SUGGESTIONS[key]
    # Fall back to first 2-char prefix
    return None
