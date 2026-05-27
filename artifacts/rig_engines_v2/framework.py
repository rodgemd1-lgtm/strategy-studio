"""RIG Deviator™ — self-contained framework rebuild (40 engines).

Single-file rebuild after the original src/rig_engines/ was wiped by the
continuous schedulers. Lives in artifacts/rig_engines_v2/ which is cleanup-safe.

Three layers:
- Cognitive 1–20 (output, ±20σ)  → text rewriting agents
- Nature   21–30 (process, ±20σ) → process-level deviation agents
- Physics  31–40 (state, ±30σ HARD GATES) → PASS / HARD_BLOCK gates

Scoring: heuristic MAD-Z proxy. Each engine has a `score(text) -> signed σ` fn.
Agents: each engine has a `+20σ pull` instruction. Dispatched via llama3.3:70b.
"""
from __future__ import annotations
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable
from urllib import request as ur


# ── helpers ─────────────────────────────────────────────────────────────────
def _tl(s: str) -> str: return s.lower()
def _wc(s: str) -> int: return max(len(s.split()), 1)
def _count_any(s: str, tokens: list[str]) -> int:
    sl = _tl(s)
    return sum(sl.count(t.lower()) for t in tokens)
def _count_re(s: str, pat: str) -> int:
    return len(re.findall(pat, s, re.IGNORECASE | re.MULTILINE))


# Word lists — kept compact, doctrine-anchored
CONSULTANT_TOKENS = ["leverage", "synergy", "holistic", "transformative",
    "best practices", "in today's landscape", "it's important to note",
    "we are excited to announce", "furthermore", "moreover", "world-class",
    "cutting-edge", "thought leadership", "seamless", "robust", "Center of Excellence"]
ABSOLUTE_TOKENS = ["zero downtime", "no truck rolls", "guaranteed", "always",
    "never fails", "cannot be argued", "production-or-nothing", "100%", "any time"]
ABSOLUTE_HARD = ["zero ", "perfect ", "always ", "never ", " all ", " every "]
EVIDENCE_TOKENS = ["Research and Markets", "Mordor", "Grand View Research",
    "Helios", "Topcon", "Bosch", "Parker", "10-K", "CMMC", "32 CFR",
    "April 2025", "April 2026", "Q3 FY26", "footnote", "confidence interval",
    "sample size", "n=", "[1]", "[2]", "[3]"]
CAUSAL_TOKENS = ["because", "therefore", "leads to", "→", "Input", "Activity",
    "Behavior", "feedback loop", "compounding", "kill criteria", "falsify",
    "wrong if", "results in", "drives"]
KILL_CRITERIA = ["kill criteria", "terminate", "rescope", "pause, revisit",
    "no daily-active", "no measurable", "no paid OEM", "extend at no additional fee",
    "refund pro-rata", "renegotiate"]
ORTHODOXY_TOKENS = ["AI Center of Excellence", "Copilot bolt-on", "pilot program",
    "strategic partnership", "thought leadership", "AI literacy", "transformation roadmap"]
TIME_TOKENS = ["month 0", "month 1", "month 3", "month 6", "month 9", "month 18",
    "year 1", "year 2", "year 3", "year 5", "year 10", "compounding loop"]
NOVEL_TOKENS = ["fleet intelligence", "operating system", "Bloomberg", "virtual appliance",
    "edge inference", "CAN-bus", "iOS of CAN", "developer platform"]


# ── engine registry ─────────────────────────────────────────────────────────
@dataclass
class Engine:
    slug: str
    codename: str
    layer: str  # "cognitive" | "nature" | "physics"
    axis: str
    pull_plus20: str
    score_fn: Callable[[str], float]
    pole: str = "right"  # gate direction
    is_gate: bool = False


def _z(value: float, median: float, mad: float = 1.0) -> float:
    """Robust-MAD-Z proxy: 0.6745·(value-median)/MAD."""
    return 0.6745 * (value - median) / max(mad, 0.01)


# Heuristic scorers — proxies of doctrine-grade MAD-Z. Calibrated against LLM
# median behavior (consultant tokens common, evidence rare, causal rare).
def s_graviton(t):    return -_z(_count_any(t, CONSULTANT_TOKENS), 6, 4) * 2  # invert: low = high σ
def s_anchor(t):      return _z(_count_any(t, EVIDENCE_TOKENS) / _wc(t) * 1000, 20, 25)
def s_forge(t):       return _z(_count_any(t, CAUSAL_TOKENS) / _wc(t) * 1000, 8, 8)
def s_breaker(t):     return -_z(_count_any(t, ORTHODOXY_TOKENS), 4, 3)
def s_horizon(t):     return _z(_count_any(t, TIME_TOKENS) + _count_any(t, KILL_CRITERIA), 6, 6)
def s_bayes(t):
    probs = _count_re(t, r"\b\d{1,3}%\b") + _count_re(t, r"\bP\(")
    return _z(probs, 4, 5)
def s_collider(t):    return _z(_count_any(t, NOVEL_TOKENS), 1, 2)
def s_shield(t):
    rebut = _count_re(t, r"(rebuttal|steelman|attack|counter-argument|risk)")
    return _z(rebut, 4, 4)
def s_glyph(t):
    # Kolmogorov originality proxy: token diversity
    words = re.findall(r"\b[A-Za-z]{4,}\b", t)
    if not words: return 0
    return _z(len(set(words)) / len(words), 0.55, 0.1)
def s_xray(t):
    # exposing fake understanding — does it explain HOW, not just WHAT?
    hows = _count_re(t, r"\b(how|why|mechanism|because|the way)\b")
    return _z(hows / _wc(t) * 1000, 12, 8)
def s_volt(t):
    # emotional voltage without manipulation
    voltage = _count_re(t, r"(architecture|inefficiency|legacy|category|moat|window|claim)")
    return _z(voltage / _wc(t) * 1000, 8, 6)
def s_darwin(t):
    # generate-mutate-select markers
    selection = _count_re(t, r"(variant|scenario|alternative|option|tier|downside|upside|base)")
    return _z(selection, 4, 4)
def s_echo(t):
    # what reader remembers in 48hr — concrete nouns + numbers
    concrete = _count_re(t, r"\$\d|\b\d{2,}\b")
    return _z(concrete, 30, 30)
def s_sovereign(t):
    # preserve reader/user agency — questions, optionality
    agency = _count_re(t, r"(your choice|optional|you decide|either|can|may)")
    return _z(agency, 6, 5)
def s_surprise(t):
    # model-update markers
    surprise = _count_re(t, r"(actually|in fact|contrary|surprisingly|unexpectedly|not what)")
    return _z(surprise, 1, 1.5)
def s_loop(t):
    # open loops the reader must close
    loops = _count_re(t, r"(\?|the question|the ask|the choice|the bet)")
    return _z(loops, 4, 4)
def s_viscera(t):
    # embodied stakes
    stakes = _count_re(t, r"(your |our |we will|family|legacy|retirement|career)")
    return _z(stakes, 12, 10)
def s_rebound(t):
    # affective contrast
    contrast = _count_re(t, r"(but|however|on the other hand|despite|whereas|yet)")
    return _z(contrast, 6, 5)
def s_prism(t):
    # signal-to-noise (long words, concrete claims)
    noise = _count_any(t, ["essentially", "basically", "actually", "very", "really"])
    return -_z(noise, 3, 3)
def s_wellspring(t):
    # pays back on reread — footnotes, layered detail
    layers = _count_re(t, r"\[[0-9]+\]|footnote|appendix|see also")
    return _z(layers, 4, 4)


# ── Nature engines (process) ────────────────────────────────────────────────
def s_swarm(t):
    # path diversity — multiple options surfaced
    paths = _count_re(t, r"(option [a-z]|alternative|scenario|path|approach \d)")
    return _z(paths, 5, 4)
def s_albatross(t):
    # heavy-tail jumps — analogies from far domains
    leaps = _count_any(t, ["Bloomberg", "iOS", "App Store", "Stripe", "Tesla", "SaaS", "platform"])
    return _z(leaps, 1, 2)
def s_slime(t):
    # winning-path reinforcement
    reinforced = _count_re(t, r"(double down|focus|prune|cut|kill|deprecate)")
    return _z(reinforced, 3, 3)
def s_clonal(t):
    # winners refine, mediocre mutate
    refined = _count_re(t, r"(refined|tightened|sharpened|narrowed|specified)")
    return _z(refined, 2, 2)
def s_lumina(t):
    # bioluminescent attraction — visible incentives
    incentives = _count_re(t, r"(roi|revenue|margin|asp|attach|premium|software)")
    return _z(incentives, 12, 10)
def s_coli(t):
    # gradient climbing — concrete next-action steps
    steps = _count_re(t, r"(step \d|month \d|next:|action:|deliverable)")
    return _z(steps, 8, 8)
def s_root(t):
    # hub-feeds-seedling — RIG/HED root mentions
    roots = _count_re(t, r"(RIG|Rodgers Intelligence|HED|Hill family|Gijs)")
    return _z(roots, 8, 6)
def s_humpback(t):
    # spiral tightens around the best — anneal markers
    anneal = _count_re(t, r"(phase \d|foundation|activation|scale|wave \d)")
    return _z(anneal, 4, 3)
def s_cuckoo(t):
    # parasitic high-deviation candidates
    radical = _count_re(t, r"(radical|provoc|first principles|demolish|tear down|reframe)")
    return _z(radical, 1, 2)
def s_reef(t):
    # 5-mode reproduction — composite synthesis
    modes = _count_re(t, r"(combine|synthes|integrate|merge|reproduce)")
    return _z(modes, 2, 2)


# ── Physics gates (HARD constraints) ────────────────────────────────────────
def g_kelvin(t):
    """No claim of unreachable floor (zero/perfect/always)."""
    violations = _count_re(t, r"\b(zero downtime|always works|perfect|100% reliable|never fails)\b")
    return ("HARD_BLOCK", -30) if violations >= 2 else ("PASS", -_z(violations, 0.5, 1) * 10)
def g_pauli(t):
    """No two adjacent identical-phrase blocks (boilerplate detector)."""
    lines = [l.strip() for l in t.split("\n") if len(l.strip()) > 40]
    dupe = len(lines) - len(set(lines))
    return ("HARD_BLOCK", -30) if dupe >= 2 else ("PASS", -_z(dupe, 0, 1) * 5)
def g_lumen(t):
    """Causal ordering: effects can't precede causes. Look for 'we already proved X' before X."""
    bad = _count_re(t, r"(already shown|proven above|as established).+(below|later|will demonstrate)")
    return ("HARD_BLOCK", -30) if bad >= 1 else ("PASS", 0)
def g_critical(t):
    """Phase transition: crossing critical temperature reorganizes regime — does the text commit?"""
    commit = _count_re(t, r"(commit to|cannot retreat|burn the boats|past this point|crossing)")
    return ("PASS", _z(commit, 1, 1) * 5)
def g_tunnel(t):
    """Penetrate impassable barrier — anti-orthodoxy commits."""
    anti = _count_re(t, r"(reject|refuse|will not|do not|stop using|abandon)")
    return ("PASS", _z(anti, 3, 3) * 5)
def g_horizon_gate(t):
    """Info must leak through opaque boundary — proof of access."""
    proof = _count_re(t, r"(we have|we own|we built|we ship|we deliver)")
    return ("PASS", _z(proof, 6, 5) * 5)
def g_parsec(t):
    """Every word load-bearing. Length × concreteness."""
    redundant = _count_re(t, r"(very|really|quite|rather|somewhat|relatively|fairly)")
    return ("PASS", -_z(redundant, 5, 5) * 5)
def g_casimir(t):
    """Constrained empty space generates measurable force — terseness."""
    avg_sent = _wc(t) / max(_count_re(t, r"[.!?]+"), 1)
    return ("PASS", -_z(avg_sent, 25, 8) * 3)  # shorter sentences → higher
def g_bell(t):
    """Non-local correlation — claim + evidence + falsification all linked."""
    linked = _count_re(t, r"(falsif|kill criteria|wrong if|terminate if).+by\s+\w+\s+\d")
    return ("PASS", _z(linked, 2, 2) * 8)
def g_zeropoint(t):
    """Even quiet systems show baseline activity — concrete metrics."""
    metrics = _count_re(t, r"\$\d|\d+%|\d+ days|\d+ months|\d+ hours")
    return ("PASS", _z(metrics, 30, 20) * 4)


# ── Engine table ────────────────────────────────────────────────────────────
ENGINES: list[Engine] = [
    # COGNITIVE 1-20
    Engine("gravity_escape", "GRAVITON", "cognitive", "Generic-AI gravity escape",
        "Banned tokens: 'leverage', 'synergy', 'holistic', 'transformative', 'world-class', "
        "'cutting-edge', 'thought leadership'. Zero use. Every generic noun replaced with HED-specific concrete object.",
        s_graviton),
    Engine("reality_anchor", "ANCHOR", "cognitive", "Sourced + falsifiable evidence",
        "Every numeric claim: primary source + date, sample size, confidence interval, "
        "falsification: 'wrong if X by DATE'. Add Falsification Calendar with 5 dated kill claims.",
        s_anchor),
    Engine("mechanism_furnace", "FORGE", "cognitive", "Causal mechanism chains",
        "For every claim: Input → Activity → Behavior → System → Economic → Loop. "
        "Burn off every adjective that lacks a mechanism.",
        s_forge),
    Engine("rupture", "BREAKER", "cognitive", "Orthodoxy demolition + radical reframe",
        "Identify orthodoxies (OEM-paid attach, hardware-first, consulting-then-handoff, "
        "AI-native vehicle controls category). Demolish ONE and commit to the radical reframe.",
        s_breaker),
    Engine("temporal_horizon_integrity", "HORIZON", "cognitive", "10-year compounding loops",
        "Replace phases with bet structures: leading indicator, lagging indicator, "
        "kill criteria (date+threshold), compounding loop. Architect 2026→2033 arc.",
        s_horizon),
    Engine("bayesian_calibration", "BAYES", "cognitive", "Decomposed probabilities",
        "Every probability decomposed into 2-3 conditional factors. Next update event named. "
        "Base rates anchored (Helios comparable). Brier-score tracking table.",
        s_bayes),
    Engine("frame_collision", "COLLIDER", "cognitive", "Orthogonal frame import",
        "Collide seed with three frames: defense procurement primary, developer platform "
        "(SDK + ARPU), electrification (refuse/ag/construction electrifying). Weave 2 highest-value.",
        s_collider),
    Engine("cognitive_sovereignty", "SHIELD", "cognitive", "Steelmanned attacks pre-empted",
        "Pre-empt attacks: Hill family ('why now'), Gijs ('too much for $60M'), "
        "Customer ('OEMs don't pay'), Engineering ('Forge <50ms fantasy'), Parker ('6 months'). "
        "Add 'attacks survived' index.",
        s_shield),
    Engine("kolmogorov_originality", "GLYPH", "cognitive", "Cannot be compressed to known phrase",
        "Every paragraph passes the test: can it be reduced to a standard consulting phrase? "
        "If yes, rewrite until no. Maximum token diversity.",
        s_glyph),
    Engine("feynman_xray", "XRAY", "cognitive", "Expose fake understanding",
        "For every claim, ask: do I understand HOW this works, or am I name-dropping? "
        "Replace name-drops with mechanism explanations.",
        s_xray),
    Engine("voltage", "VOLT", "cognitive", "Emotional voltage without manipulation",
        "Surface the stakes: legacy, family business risk, category-defining moment. "
        "Tension without hyperbole. The reader feels the cost of inaction.",
        s_volt),
    Engine("darwinian_selection", "DARWIN", "cognitive", "Generate-mutate-select",
        "Show the alternatives that were considered and rejected. Surface the variants. "
        "Make selection visible.",
        s_darwin),
    Engine("memory_residue", "ECHO", "cognitive", "What the reader remembers 48hr later",
        "Concrete, specific, numbered. The reader, asked tomorrow to summarize, "
        "produces 3 sentences with real numbers in them.",
        s_echo),
    Engine("autonomy_calibration", "SOVEREIGN", "cognitive", "Preserve reader/user agency",
        "The reader has explicit choices. No coercive framing. Three tiers, your call. "
        "The proposal hands the decision back, doesn't push.",
        s_sovereign),
    Engine("predictive_surprise", "SURPRISE", "cognitive", "Make reader update their model",
        "At least one claim that, when stated, makes the reader say 'huh, I didn't know that'. "
        "Genuine information injection, not vamping.",
        s_surprise),
    Engine("zeigarnik_residue", "LOOP", "cognitive", "Open loops the reader must close",
        "Each section ends with an implied question the next section answers. "
        "The reader pulls themselves through.",
        s_loop),
    Engine("somatic_stakes", "VISCERA", "cognitive", "Embodied stakes (felt, not described)",
        "The reader feels what's at risk. Not described — embodied. "
        "Specific names, specific futures, specific people.",
        s_viscera),
    Engine("opponent_process", "REBOUND", "cognitive", "Affective contrast and aftertaste",
        "Hard claim immediately followed by its counter. The reader holds both. "
        "Aftertaste is durable.",
        s_rebound),
    Engine("signal_to_noise", "PRISM", "cognitive", "d-prime above 1.8",
        "Zero filler. No 'essentially', 'basically', 'actually'. Every word carries weight.",
        s_prism),
    Engine("hermeneutic_density", "WELLSPRING", "cognitive", "Pays back more on reread",
        "Layered detail. Footnotes that reward. The 2nd read finds things the 1st missed.",
        s_wellspring),
    # NATURE 21-30
    Engine("pheromone_swarm", "SWARM", "nature", "Path diversity, no premature collapse",
        "Surface 3+ distinct strategic paths. Don't collapse to one before evidence justifies.",
        s_swarm),
    Engine("levy_flight", "ALBATROSS", "nature", "Heavy-tail leaps from far domains",
        "Import at least one analogy from a non-adjacent domain (Bloomberg, iOS, Stripe). "
        "The leap is the differentiator.",
        s_albatross),
    Engine("physarum_prune", "SLIME", "nature", "Reinforce winning paths, prune rest",
        "Explicitly kill 2+ paths considered. Show the prune.",
        s_slime),
    Engine("clonal_refinement", "CLONAL", "nature", "Winners refine gently, mediocre mutate hard",
        "Strong sections tightened with specificity. Weak sections fully rewritten.",
        s_clonal),
    Engine("bioluminescent_attraction", "LUMINA", "nature", "Visible economic incentive structure",
        "Money paths visible: ROI math, margin protection, ASP premium, attach rate. "
        "The reader can follow the dollars.",
        s_lumina),
    Engine("chemotaxis_gradient", "COLI", "nature", "Gradient-climb with concrete next steps",
        "Every phase has named, measurable next-action steps. No 'we will explore'.",
        s_coli),
    Engine("mycorrhizal_root", "ROOT", "nature", "Hubs feed seedlings — RIG/HED root system",
        "RIG owns the hub, HED owns the artifact. Roles explicit. Knowledge flows traced.",
        s_root),
    Engine("humpback_spiral", "HUMPBACK", "nature", "Spiral tightens around best, anneal exploration→exploitation",
        "Foundation/Activation/Scale phases. Exploration cost drops over time. "
        "Spiral shape visible in the rollout.",
        s_humpback),
    Engine("cuckoo_parasitic", "CUCKOO", "nature", "Inject parasitic high-deviation candidates",
        "At least one proposal that is uncomfortable to accept but defensible. "
        "Force-feeds an outlier into the proposal.",
        s_cuckoo),
    Engine("coral_reef_synthesis", "REEF", "nature", "5-mode reproduction simultaneously",
        "The mesh combines: broadcast (everyone gets it), brood (internal), bud (clone & extend), "
        "fragment (peel off a piece), deprecate (kill weak). Show the mode.",
        s_reef),
    # PHYSICS 31-40 — HARD GATES
    Engine("absolute_zero", "KELVIN", "physics", "Detect unreachable-floor claims",
        "Strip 'zero downtime', 'perfect', 'always', '100%', 'never fails'.",
        lambda t: g_kelvin(t)[1], pole="gate", is_gate=True),
    Engine("pauli_exclusion", "PAULI", "physics", "No two artifacts may occupy same state",
        "No boilerplate. No identical paragraphs. Each section unique.",
        lambda t: g_pauli(t)[1], pole="gate", is_gate=True),
    Engine("speed_of_lumen", "LUMEN", "physics", "Effects cannot precede causes",
        "Causal ordering preserved. No 'as shown above' for content below.",
        lambda t: g_lumen(t)[1], pole="gate", is_gate=True),
    Engine("critical_phase", "CRITICAL", "physics", "Cross critical temperature, reorganize regime",
        "Commitment statements. Past this point, no retreat. Burn the boats moments.",
        lambda t: g_critical(t)[1], pole="gate", is_gate=True),
    Engine("quantum_tunnel", "TUNNEL", "physics", "Penetrate impassable barrier",
        "Anti-orthodoxy commits. The proposal refuses something the industry accepts.",
        lambda t: g_tunnel(t)[1], pole="gate", is_gate=True),
    Engine("hawking_horizon", "HORIZON-GATE", "physics", "Info leaks through opaque boundary",
        "Proof of access — 'we have', 'we own', 'we built'. Non-Hawking-radiation evidence.",
        lambda t: g_horizon_gate(t)[1], pole="gate", is_gate=True),
    Engine("fine_structure", "PARSEC", "physics", "Every word load-bearing",
        "Strip every adverb that doesn't change meaning. No 'very', 'really', 'quite'.",
        lambda t: g_parsec(t)[1], pole="gate", is_gate=True),
    Engine("casimir_force", "CASIMIR", "physics", "Constrained empty space generates force",
        "Sentence brevity. Short sentences amplify weight. Long sentences only when necessary.",
        lambda t: g_casimir(t)[1], pole="gate", is_gate=True),
    Engine("bell_entanglement", "BELL", "physics", "Genuine non-local correlation |S|>2",
        "Claim + evidence + falsification all linked in one paragraph. The bell is rung.",
        lambda t: g_bell(t)[1], pole="gate", is_gate=True),
    Engine("vacuum_zeropoint", "ZEROPOINT", "physics", "Quiet systems show baseline activity",
        "Concrete metrics throughout — $, %, days, units. No empty assertions.",
        lambda t: g_zeropoint(t)[1], pole="gate", is_gate=True),
]


def score_all(text: str) -> dict:
    """Score text against all 40 engines. Returns full packet."""
    scores = {}
    statuses = {}
    submetrics = {}
    for e in ENGINES:
        try:
            sigma = round(float(e.score_fn(text)), 3)
        except Exception as ex:
            sigma = 0.0
            submetrics[e.slug] = {"error": str(ex)}
        scores[e.slug] = sigma
        if e.is_gate:
            # Physics gates: hard block if sigma < -10
            statuses[e.slug] = "HARD_BLOCK" if sigma < -10 else ("BLOCK" if sigma < -3 else "PASS")
        else:
            statuses[e.slug] = "BLOCK" if sigma < -3 else "PASS"

    # RIG-L composite: 6 strongest pulls × (1 − risk_penalty)
    cog_nature = sorted([(e.slug, scores[e.slug]) for e in ENGINES if not e.is_gate],
                       key=lambda x: -abs(x[1]))[:6]
    pulls = [s for _, s in cog_nature]
    hard_blocks = sum(1 for s in statuses.values() if s == "HARD_BLOCK")
    risk = min(0.9, hard_blocks * 0.3)
    rig_l = round(sum(pulls) / max(len(pulls), 1) * (1 - risk), 3)

    # BDF: signed σ × craft × restraint
    bdf = round(sum(scores.values()) / len(scores), 3)

    # Weakest gate
    weakest = min(scores.items(), key=lambda x: x[1])
    return {
        "rig_l": rig_l,
        "bdf": bdf,
        "status": "HARD_BLOCK" if hard_blocks > 0 else ("BLOCK" if rig_l < -3 else "PASS"),
        "weakest_gate": weakest[0],
        "hard_blocks": hard_blocks,
        "mad_z": scores,
        "engines": statuses,
        "submetrics": submetrics,
    }


# ── Agent dispatch ──────────────────────────────────────────────────────────
LLM_URL = "http://100.91.39.12:11434/v1/chat/completions"
LLM_MODEL = "llama3.3:70b"


def dispatch_agent(seed: str, engine: Engine, target_sigma: int = 20,
                    max_tokens: int = 2400, timeout: int = 600) -> dict:
    """Run a single +Nσ agent against the seed. Returns variant dict."""
    prompt = (
        f"You are RIG-{engine.codename}, agent for the {engine.slug} engine at σ=+{target_sigma}.\n\n"
        f"UNIVERSAL +{target_sigma}σ RUNG: Civilization-grade. New formal system. Doctrine-anchored.\n\n"
        f"ENGINE AXIS: {engine.axis}\n\n"
        f"PULL INSTRUCTION: {engine.pull_plus20}\n\n"
        f"ORIGINAL HED FORGE PROPOSAL (v2 — Mike's draft for Gijs Zomer + Hill family):\n"
        f"---\n{seed}\n---\n\n"
        f"Rewrite at +{target_sigma}σ along your axis only. Don't try to be perfect on other axes. "
        f"Preserve the proposal's existing strengths (Helios comparable, 3 engagement tiers, "
        f"production-or-nothing guarantee, exec letter framing). 700-1100 words. "
        f"Output ONLY the rewritten strategy. No preamble, no commentary."
    )
    t0 = time.time()
    payload = {"model": LLM_MODEL,
               "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.5, "max_tokens": max_tokens}
    try:
        req = ur.Request(LLM_URL, data=json.dumps(payload).encode("utf-8"),
                         headers={"Content-Type": "application/json"}, method="POST")
        with ur.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8"))
        msg = body["choices"][0]["message"]
        content = (msg.get("content") or msg.get("reasoning") or "").strip()
        return {"engine_slug": engine.slug, "codename": engine.codename,
                "layer": engine.layer, "target_sigma": target_sigma,
                "content": content, "elapsed_s": round(time.time()-t0, 1),
                "char_len": len(content), "status": "ok"}
    except Exception as ex:
        return {"engine_slug": engine.slug, "codename": engine.codename,
                "layer": engine.layer, "target_sigma": target_sigma,
                "content": f"[{engine.codename} failed: {ex}]",
                "elapsed_s": round(time.time()-t0, 1), "char_len": 0,
                "status": "error", "error": str(ex)}


def dispatch_batch(seed: str, engines: list[Engine], target_sigma: int = 20,
                    max_workers: int = 6) -> dict[str, dict]:
    """Dispatch multiple agents in parallel. Returns {codename: variant_dict}."""
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(dispatch_agent, seed, e, target_sigma): e for e in engines}
        for f in as_completed(futs):
            v = f.result()
            results[v["codename"]] = v
            print(f"  {'✓' if v['status']=='ok' else '✗'} {v['codename']:9} "
                  f"{v['elapsed_s']}s · {v['char_len']:>5} chars", flush=True)
    # Preserve ENGINES order
    order = [e.codename for e in engines]
    return {k: results[k] for k in order if k in results}


def mesh_variants(variants: dict[str, dict], seed: str,
                   max_tokens: int = 3500, timeout: int = 720) -> str:
    """Coral Reef mesh of variants → synthesized v3."""
    parts = []
    for codename, v in variants.items():
        if v.get("status") != "ok":
            continue
        parts.append(
            f"### Variant from RIG-{codename} (engine: {v['engine_slug']}, layer: {v['layer']}, σ: +{v['target_sigma']})\n\n"
            f"{v['content']}\n"
        )
    block = "\n---\n".join(parts)

    prompt = f"""You are the RIG Coral Reef Mesher.

You take many variants of the HED Manufacturing Forge proposal — each produced by a different RIG Deviation Agent operating at +20σ on its engine's axis — and synthesize them into a single new strategy candidate.

Your job: combine the strongest element from EACH variant. Preserve the seed's existing strengths (Helios comparable, three engagement tiers, exec letter framing, production-or-nothing guarantee, falsifiable bets).

VARIANTS (each pulled along one axis):

{block}

ORIGINAL SEED (for reference — preserve specific numbers, dates, named programs, citations):

{seed[:3000]}...

Synthesize HED Forge Proposal v3. Write as operating doctrine, not deck. 1400-1800 words minimum — do not compress; the v2 is already 1962 words and we need to preserve evidence depth. Output ONLY the synthesized strategy. No preamble.
"""
    t0 = time.time()
    payload = {"model": LLM_MODEL,
               "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.4, "max_tokens": max_tokens}
    req = ur.Request(LLM_URL, data=json.dumps(payload).encode("utf-8"),
                     headers={"Content-Type": "application/json"}, method="POST")
    with ur.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read().decode("utf-8"))
    msg = body["choices"][0]["message"]
    content = (msg.get("content") or msg.get("reasoning") or "").strip()
    print(f"  Mesh complete · {time.time()-t0:.0f}s · {len(content)} chars", flush=True)
    return content


__all__ = ["Engine", "ENGINES", "score_all", "dispatch_agent", "dispatch_batch",
           "mesh_variants", "LLM_URL", "LLM_MODEL"]
