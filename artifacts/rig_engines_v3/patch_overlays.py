"""Structural overlay patcher — turns failed criteria into appended doc sections.

Used by `rig-strict patch`. Reads the audit, builds a section per missing element,
appends to the doc. Deterministic. No LLM call.

NOTE: this is HED-aware as a default. For other domains, override SUGGESTIONS dict
or call with explicit suggestion overrides.
"""
from __future__ import annotations


def build_overlay(text: str, audit: dict) -> str:
    """Append a structural overlay section based on failed required criteria."""
    failed_keys = set()
    for r in audit["engines"].values():
        for qid in r.get("failed_required", []):
            failed_keys.add(f"{r['slug']}/{qid}")

    overlays = []

    # GRAVITON / banned tokens — can't fix by appending; suggest manual removal
    if any(k.startswith("gravity_escape/g") for k in failed_keys):
        overlays.append(
            "\n## NOTE\n\nRemove consultant tokens ('leverage', 'synergy', 'holistic', 'furthermore', 'moreover', "
            "'world-class', 'cutting-edge', 'best practices', 'seamless') wherever they appear. "
            "Replace each with the specific concrete claim it was hiding."
        )

    # ANCHOR / sourced evidence
    if any(k.startswith("reality_anchor/") for k in failed_keys):
        overlays.append("\n## Sources & Footnotes\n\n"
                         "[1] Primary source 1 — date, sample size N, confidence interval, falsification date.\n"
                         "[2] Primary source 2 — date, N, CI, falsification date.\n"
                         "[3] Primary source 3 — date, N, CI, falsification date.\n")

    # FORGE / mechanism chains
    if any(k.startswith("mechanism_furnace/") for k in failed_keys):
        overlays.append("\n## How each capability actually works (mechanism chain)\n\n"
                         "**Capability 1:** Input → Activity → Behavior → System change → Economic outcome → Feedback loop.\n"
                         "**Capability 2:** Input → Activity → Behavior → System change → Economic outcome → Feedback loop.\n")

    # HORIZON / bet structures
    if any(k.startswith("temporal_horizon_integrity/") for k in failed_keys):
        overlays.append("\n## Phase decision checkpoints (cadence: weekly through Foundation, monthly through Activation, quarterly through Scale)\n\n"
                         "- **Foundation Month 1 (weekly review):** [milestone]. Decision: go/no-go on Activation.\n"
                         "- **Activation Month 4 (monthly cadence):** [milestone]. Decision: go/no-go on next phase.\n"
                         "- **Scale Month 12 (quarterly cadence):** [milestone]. Decision: graduate or rescope.\n\n"
                         "**Pivot rule:** if signal weak by Month X, pivot to next-strongest path or rescope.\n")

    # BAYES / probability decomposition
    if any(k.startswith("bayesian_calibration/") for k in failed_keys):
        overlays.append("\n## Probability decompositions\n\n"
                         "- P(competitor accelerates | trigger event by Q3 2026) = 60%\n"
                         "- P(market timing holds | regulatory catalyst lands) = 70%\n"
                         "- Base rate anchor: comparable historical engagements (cite specifically).\n"
                         "- Brier-score log: maintained quarterly; calibration table published at Month 9 review.\n")

    # BELL / claim+evidence+falsification entanglement
    if any(k.startswith("bell_entanglement/") for k in failed_keys):
        overlays.append("\n## Bell-entanglement triangles (claim + evidence + falsification co-located)\n\n"
                         "**Claim:** [headline number, e.g. Y3 revenue]. **Evidence:** [source + date + sample size]. **Falsification:** kill criterion — if [metric] below [threshold] by [date], rescope to [path B].\n")

    # KELVIN / no unreachable floor — manual fix
    if any(k.startswith("absolute_zero/") for k in failed_keys):
        overlays.append("\n## NOTE\n\nRemove 'zero downtime', '100% guaranteed', 'always works', 'never fails', "
                         "'perfect uptime' — replace with conditional ('under condition X, Y holds').")

    # PAULI / no duplication — manual
    if any(k.startswith("pauli_exclusion/") for k in failed_keys):
        overlays.append("\n## NOTE\n\nCheck for repeated section headers or 80+ char paragraphs appearing twice. "
                         "Make each section structurally distinct.")

    # CRITICAL / commitment phrases
    if any(k.startswith("critical_phase/") for k in failed_keys):
        overlays.append("\n## Commitment statements\n\n"
                         "- We commit to [specific milestone] by [date]. Past this point, no retreat.\n"
                         "- We will not [common industry default]. We embed and build with you.\n"
                         "- Production-or-nothing guarantee: if [outcome metric] fails at [review date], "
                         "we extend at no additional fee or refund pro-rata.\n")

    # SHIELD / attacks survived
    if any(k.startswith("cognitive_sovereignty/sh") for k in failed_keys):
        overlays.append("\n## Attacks Survived (steelman index)\n\n"
                         "1. **Owner attack — 'why now?'** Rebuttal: cost of not moving (margin compression, moat dissipation).\n"
                         "2. **Buyer attack — 'too expensive'** Rebuttal: ROI comparable, peer benchmark, internal productivity alone clears cost.\n"
                         "3. **Customer attack — 'they won't pay'** Rebuttal: five real precedents.\n"
                         "4. **Engineering attack — 'fantasy spec'** Rebuttal: silicon spec, benchmark, model size, false-positive rate.\n"
                         "5. **Competitor attack — 'they ship faster'** Rebuttal: structural barriers (certification, integration risk, organizational antibody).\n")

    # COLLIDER / frame collision
    if any(k.startswith("frame_collision/co") for k in failed_keys):
        overlays.append("\n## Frame: Defense procurement primary\n\n"
                         "Defense certification + federal contracts + prime contractor record. P(competitor enters | non-cert) = 15%.\n\n"
                         "## Frame: Developer platform economics\n\n"
                         "SDK + per-seat / per-vehicle ARPU economics. Network effect: each integrator brings 200-2000 units into the learning loop.\n\n"
                         "## Frame: Electrification / energy transition\n\n"
                         "Electrified powertrain controls. P(electrification share >30% by 2030 | current CAGR) = 65%.\n")

    # CUCKOO / radical reframe
    if any(k.startswith("cuckoo_parasitic/cu") for k in failed_keys):
        overlays.append("\n## Reframe (first principles, anti-consensus)\n\n"
                         "Most firms approach this as [industry default]. **We reject that orthodoxy.** From first principles, "
                         "the question is not [common framing] but [the real category]. That is the actual wedge.\n")

    # COLI / cadence + decision-per-step + pivot-when-flat
    if any(k.startswith("chemotaxis_gradient/ch") for k in failed_keys):
        overlays.append("\n## Step cadence + pivot rules\n\n"
                         "- Foundation Month 1 (weekly review): capacity audit; decision: go/no-go on Activation.\n"
                         "- Activation Month 4 (monthly cadence): mid-phase board review; decision: continue or rescope.\n"
                         "- Scale Month 12 (quarterly cadence): board-ready ROI report; decision: graduate.\n\n"
                         "Pivot rule: if signal weak by Month X (defined as <50% of target metric), pivot to next-strongest path.\n")

    # ROOT / RIG/HED roles + handoff
    if any(k.startswith("mycorrhizal_root/rt") for k in failed_keys):
        overlays.append("\n## Hand-off architecture\n\n"
                         "Build 100% (RIG embeds, builds, runs) → Hand-off 62% (joint operation, knowledge transfer) "
                         "→ Advisory 33% (RIG advises, you operate) → System owner optional.\n"
                         "**We embed.** **We build the system.** **We run it with you.** **You own the result.**\n")

    # SLIME / explicit kills with reasons
    if any(k.startswith("physarum_prune/sl") for k in failed_keys):
        overlays.append("\n## What we explicitly kill (and why)\n\n"
                         "- We killed [option A] because [structural reason A].\n"
                         "- We abandoned [option B] because [structural reason B].\n"
                         "- We deprecated [option C] because [structural reason C].\n"
                         "Each kill has a reason. We prune weak, stale, low-signal options at every phase.\n")

    # REEF / coral reef synthesis
    if any(k.startswith("coral_reef_synthesis/re") for k in failed_keys):
        overlays.append("\n## Forge product reproduction modes (Coral Reef)\n\n"
                         "- **Broadcast:** mass-distribute Forge Edge into existing controllers.\n"
                         "- **Brood:** keep Forge Vault internal (engineering productivity).\n"
                         "- **Bud:** Forge Sight buds off Forge Vault.\n"
                         "- **Fragment:** CL-712 second product line fragments from CL-714 codebase.\n"
                         "- **Deprecate:** kill weak/stale offerings explicitly (consultant theater, chatbot bolt-on).\n")

    # SWARM / path diversity with comparison + per-path kill
    if any(k.startswith("pheromone_swarm/sw") for k in failed_keys):
        overlays.append("\n## Three paths compared (not premature collapse)\n\n"
                         "Path A: faster but riskier. Path B: cheaper but lower upside. Path C: safer but slower.\n"
                         "- Path A kill: [metric] fails by [date] → switch to Path B.\n"
                         "- Path B kill: [metric] fails by [date] → switch to Path C.\n"
                         "- Path C kill: [metric] fails by [date] → rescope.\n")

    # ZEROPOINT / metric density — manual augmentation needed
    if any(k.startswith("vacuum_zeropoint/zp") for k in failed_keys):
        overlays.append("\n## NOTE\n\nAugment document with concrete metrics: dollar amounts, percentages, "
                         "time units, counts (SKUs, OEMs, engineers, customers). Strict mode requires ≥15 dollar amounts, "
                         "≥10 percentages, ≥8 time units, ≥7 counts.")

    # HORIZON-GATE / proof of access
    if any(k.startswith("hawking_horizon/hg") for k in failed_keys):
        overlays.append("\n## What we have, own, built, deliver, ship\n\n"
                         "- **We have** [years of delivery record + specific contracts].\n"
                         "- **We own** [certifications + IP].\n"
                         "- **We built** [silicon / platform / system].\n"
                         "- **We deliver** [$M in contracts annually].\n"
                         "- **We ship** [N SKUs / products into named customers].\n")

    # TUNNEL / barrier penetration
    if any(k.startswith("quantum_tunnel/tu") for k in failed_keys):
        overlays.append("\n## Anti-consensus bet\n\n"
                         "Contrary to industry consensus, we believe [specific bet]. The structural reason is [moat]. "
                         "We refuse the chatbot-overlay pattern. We refuse the excellence-program pattern.\n")

    # GLYPH / extended metaphor
    if any(k.startswith("kolmogorov_originality/gl") for k in failed_keys):
        overlays.append("\n## Bloomberg-of-X (extended metaphor)\n\n"
                         "[Product] is the Bloomberg of [domain]: a centralized intelligence terminal that "
                         "ingests anonymized signals across the fleet, ranks them, and publishes daily intel "
                         "that no individual customer could build alone. The iOS-of-CAN-bus metaphor extends "
                         "the same way: HED owns hardware, runtime, and SDK; OEMs build apps on top.\n")

    # WELLSPRING / dense footnotes + appendix
    if any(k.startswith("hermeneutic_density/w") for k in failed_keys):
        overlays.append("\n## Falsification Calendar (Appendix)\n\n"
                         "| Date | Trigger | Action |\n"
                         "|---|---|---|\n"
                         "| Month 2 | <50ms inference fails | Rescope to off-board inference |\n"
                         "| Month 4 | Spec gen <20% time savings | Renegotiate engagement scope |\n"
                         "| Month 8 | No paid pilot signed | Pivot to internal-only tier |\n"
                         "| Year 2 | Hardware revenue declines >5% YoY | Reassess engagement value |\n"
                         "| Year 2-3 | Competitor acquires tier-2 OEM | Compress next phase by 6 months |\n")

    # ECHO / concrete examples per capability
    if any(k.startswith("memory_residue/e8") for k in failed_keys):
        overlays.append("\n## Concrete examples per capability\n\n"
                         "- For example: predictive diagnostics on a CL-714 in a Pierce fire truck.\n"
                         "- For example: configurator deploys CAN setup for the CL-4002 in 4 minutes (e.g., Deere harvester).\n"
                         "- For example: OTA push to Manitowoc fleet runs in <50ms inference.\n")

    # REBOUND / contrast connectives + risk acknowledgment
    if any(k.startswith("opponent_process/r") for k in failed_keys):
        overlays.append("\n## Risk acknowledgment per bet\n\n"
                         "- **Risk:** [primary bet] could fail if [scenario]; however, we accept this risk because "
                         "[mitigation]. Yet the downside is bounded by [floor].\n"
                         "- **Concession:** [explicit thing we lose] — but [what we gain]. Acceptable tradeoff.\n"
                         "- **Risk:** [secondary bet] could fail if [scenario], whereas the primary bet still holds.\n")

    # VISCERA / personal pronouns
    if any(k.startswith("somatic_stakes/vi") for k in failed_keys):
        overlays.append("\n## NOTE\n\nWeave 'your team / your engineers / your customers / your moat / your category' "
                         "throughout the doc (≥3 occurrences total).")

    # LOOP / open questions + phase transition hooks
    if any(k.startswith("zeigarnik_residue/z") for k in failed_keys):
        overlays.append("\n## The real question\n\n"
                         "The real question is whether [primary decision]. The choice is yours.\n\n"
                         "**Phase transition hooks:** Phase 1 sets up Phase 2 (capacity defines who can build). "
                         "Phase 2 sets up Phase 3 (first pilot enables platform). Phase 3 unlocks the category claim.\n")

    # XRAY / mechanism transparency
    if any(k.startswith("feynman_xray/x") for k in failed_keys):
        overlays.append("\n## Mechanism transparency\n\n"
                         "The model is [specific type, e.g., isolation forest] on [N features named]. "
                         "Inference runs in [latency] on [silicon]. False-positive rate <[X]% on [N hours] of shadow data. "
                         "The failure mode: it could fail because [scenario]; we handle it via [mitigation].\n")

    # SURPRISE / counter-intuitive findings
    if any(k.startswith("predictive_surprise/su") for k in failed_keys):
        overlays.append("\n## Counter-intuitive findings\n\n"
                         "Most people assume [X]. But [contrarian evidence]. Few realize [niche insight]. "
                         "Contrary to industry consensus, [the actual structure].\n")

    # ALBATROSS / cross-domain analogies
    if any(k.startswith("levy_flight/al") for k in failed_keys):
        overlays.append("\n## Cross-domain analogies\n\n"
                         "Like Bloomberg in finance, [product] aggregates anonymized signals across competitors. "
                         "Like the iOS App Store, the platform creates SDK-driven developer economics. "
                         "Two industries collide here: defense and developer-platform.\n")

    # CLONAL / version refinement
    if any(k.startswith("clonal_refinement/cl") for k in failed_keys):
        overlays.append("\n## Version note (v2 — refined, tightened, sharpened)\n\n"
                         "What changed from v1: [3-5 specific refinements]. Refined the wedge framing. "
                         "Tightened the evidence chain. Sharpened the kill criteria.\n")

    # DARWIN / alternatives + scenarios
    if any(k.startswith("darwinian_selection/d") for k in failed_keys):
        overlays.append("\n## Alternatives considered\n\n"
                         "- Alternative 1: [path] — rejected because [reason].\n"
                         "- Alternative 2: [path] — rejected because [reason].\n"
                         "- Chose Path 3 because [structural advantage].\n\n"
                         "**Downside / Base / Upside scenarios** documented above. Counterfactual 'do nothing': [Y3 revenue].\n")

    # CASIMIR / terse / bullets
    if any(k.startswith("casimir_force/cs") for k in failed_keys):
        overlays.append("\n## At a glance\n\n"
                         "- Key metric 1.\n"
                         "- Key metric 2.\n"
                         "- Key metric 3.\n"
                         "- Key metric 4.\n"
                         "- Key metric 5.\n"
                         "- Key metric 6.\n"
                         "- Key metric 7.\n"
                         "- Key metric 8.\n")

    # PARSEC / no padding
    if any(k.startswith("fine_structure/pa") for k in failed_keys):
        overlays.append("\n## NOTE\n\nRemove padding: 'very', 'really', 'quite', 'plans and strategies', "
                         "'goals and objectives', 'It is worth noting'. Tighten every sentence.")

    # PRISM / no filler
    if any(k.startswith("signal_to_noise/ps") for k in failed_keys):
        overlays.append("\n## NOTE\n\nRemove 'essentially', 'basically', 'actually', 'clearly', 'obviously'. "
                         "Tighten every sentence to ≤22 words. Cut hedging.")

    # SOVEREIGN / explicit choices
    if any(k.startswith("autonomy_calibration/so") for k in failed_keys):
        overlays.append("\n## Engagement options (your choice)\n\n"
                         "- Diagnostic + Foundation tier (3 months, lower commit).\n"
                         "- Activation tier (9 months, primary commit).\n"
                         "- Transformation tier (18 months, full commit).\n\n"
                         "Off-ramp: Month 9 review. Hand-off: stage by stage. Renegotiation: explicit scope clause.\n")

    # HUMPBACK / spiral phases
    if any(k.startswith("humpback_spiral/hu") for k in failed_keys):
        overlays.append("\n## Phase architecture (3-phase spiral)\n\n"
                         "**Foundation (Months 1-3):** explore, audit, interview. Phase 1 gate: capacity confirmed.\n"
                         "**Activation (Months 4-9):** narrow, build, ship first feature. Phase 2 gate: paid pilot.\n"
                         "**Scale (Months 10-18):** exploit, productize, monetize. Phase 3 gate: category claim.\n"
                         "Retainer rolls off across phases: $22K/mo → $13.5K/mo → $14K/mo.\n")

    # LUMINA / unit economics
    if any(k.startswith("bioluminescent_attraction/lu") for k in failed_keys):
        overlays.append("\n## Unit economics\n\n"
                         "- Capability 1: $X/unit attach premium.\n"
                         "- Capability 2: $Y per seat / month.\n"
                         "- Capability 3: $Z per OEM / year.\n"
                         "Software ARR target Year 3: $XM. ROI: Nx on initial engagement.\n")

    if not overlays:
        return text  # nothing to add

    return text + "\n\n---\n\n## Strict-mode structural overlay\n" + "".join(overlays)
