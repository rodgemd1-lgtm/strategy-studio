#!/usr/bin/env python3
"""
Hermes Router — expanded intent router for RIG lattice.

Takes an inbound payload → extracts intent → resolves cell coordinate
→ computes BMS → returns archetype dispatch.

Signature: def route(payload: InboundPayload) -> DispatchResult
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_rig_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_rig_root.parent))

from strategy_studio.lattice._types_reexport import (
    Level,
    Diamond,
    BMSMode,
    IQRSQPIStep,
    LatticeCoordinate,
)
from strategy_studio.core.types import (
    InboundPayload,
    IntentKey,
    StructuredQuery,
)
from strategy_studio.hermes.bms import calculate_bms, BMSResult, score_workflow
from strategy_studio.resolve_archetype import (
    resolve_archetype,
    resolve_file,
)


# ── Dispatch Result ───────────────────────────────────────────────────────────

@dataclass
class DispatchResult:
    """Result of routing an inbound payload through the lattice."""
    cell_id: str
    altitude: str
    diamond: str
    step: str
    bms_mode: str
    bms_score: float
    bms_rationale: str
    archetype_cell: str
    archetype_file: str
    dispatch_route: str  # a1 | a2 | a3 | a4
    intent_key: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    escalation: bool = False
    trace: list[str] = field(default_factory=list)


# ── Intent extraction ─────────────────────────────────────────────────────────

# Keyword → IntentKey mapping
INTENT_PATTERNS: list[tuple[re.Pattern, IntentKey]] = [
    # Physical diamond
    (re.compile(r"\b(execute|run|exec|do)\b", re.I), IntentKey.PHYSICAL_EXECUTE),
    (re.compile(r"\b(fetch|get|retrieve|pull|read)\b", re.I), IntentKey.PHYSICAL_FETCH),
    (re.compile(r"\b(write|save|store|persist|create)\b", re.I), IntentKey.PHYSICAL_WRITE),
    (re.compile(r"\b(send|push|publish|dispatch|deliver)\b", re.I), IntentKey.PHYSICAL_SEND),
    (re.compile(r"\b(schedule|plan|queue|delay)\b", re.I), IntentKey.PHYSICAL_SCHEDULE),

    # Cognitive diamond
    (re.compile(r"\b(analyze|break\s*down|dissect|examine)\b", re.I), IntentKey.COGNITIVE_ANALYZE),
    (re.compile(r"\b(synthesize|combine|merge|integrate|weave)\b", re.I), IntentKey.COGNITIVE_SYNTHESIZE),
    (re.compile(r"\b(evaluate|assess|score|rate|judge)\b", re.I), IntentKey.COGNITIVE_EVALUATE),
    (re.compile(r"\b(compare|contrast|diff|versus|vs)\b", re.I), IntentKey.COGNITIVE_COMPARE),
    (re.compile(r"\b(classify|categorize|tag|label|sort)\b", re.I), IntentKey.COGNITIVE_CLASSIFY),

    # Nature diamond
    (re.compile(r"\b(generate|create|produce|build|make)\b", re.I), IntentKey.NATURE_GENERATE),
    (re.compile(r"\b(transform|convert|change|mutate|evolve)\b", re.I), IntentKey.NATURE_TRANSFORM),
    (re.compile(r"\b(optimize|improve|enhance|tune|refine)\b", re.I), IntentKey.NATURE_OPTIMIZE),
    (re.compile(r"\b(simulate|model|predict|forecast)\b", re.I), IntentKey.NATURE_SIMULATE),
    (re.compile(r"\b(discover|explore|find|search|investigate)\b", re.I), IntentKey.NATURE_DISCOVER),
]

# Diamond keywords for fallback diamond detection
DIAMOND_KEYWORDS = {
    Diamond.D1: [
        "physical", "execute", "run", "fetch", "write", "send", "schedule",
        "operation", "deploy", "system", "hardware", "infrastructure",
    ],
    Diamond.D2: [
        "cognitive", "analyze", "synthesize", "evaluate", "compare", "classify",
        "think", "reason", "assess", "strategy", "knowledge", "research",
    ],
    Diamond.D3: [
        "nature", "generate", "transform", "optimize", "simulate", "discover",
        "learn", "adapt", "evolve", "behavior", "pattern", "creative",
    ],
}


def extract_intent(payload: InboundPayload) -> tuple[IntentKey, Diamond]:
    """
    Extract intent key and diamond from raw payload text.

    Uses keyword matching (deterministic, A1-safe).
    """
    text = payload.raw.lower()
    scores: dict[Diamond, int] = {d: 0 for d in Diamond}
    best_intent: Optional[IntentKey] = None
    best_score: int = 0

    for pattern, intent in INTENT_PATTERNS:
        if pattern.search(text):
            if intent.value.startswith("physical"):
                scores[Diamond.D1] += 1
            elif intent.value.startswith("cognitive"):
                scores[Diamond.D2] += 1
            elif intent.value.startswith("nature"):
                scores[Diamond.D3] += 1
            else:
                scores[Diamond.D1] += 1
                scores[Diamond.D2] += 1
                scores[Diamond.D3] += 1

            # Track best intent
            matches = len(pattern.findall(text))
            if matches > best_score:
                best_score = matches
                best_intent = intent

    if best_intent is None:
        best_intent = IntentKey.UNKNOWN

    # Resolve diamond from scores
    max_diamond = max(scores.keys(), key=lambda k: scores[k])
    if scores[max_diamond] == 0:
        # Try keyword fallback
        for diamond in Diamond:
            for kw in DIAMOND_KEYWORDS[diamond]:
                if kw in text:
                    scores[diamond] += 1
        max_diamond = Diamond.D1 if scores[Diamond.D1] >= scores[Diamond.D2] and scores[Diamond.D1] >= scores[Diamond.D3] else (
            Diamond.D2 if scores[Diamond.D2] >= scores[Diamond.D3] else Diamond.D3
        )

    return best_intent, max_diamond


def estimate_level(payload: InboundPayload, intent: IntentKey) -> Level:
    """
    Estimate altitude/level from payload complexity.

    Simple heuristics based on text length, question marks, conditionals.
    """
    text = payload.raw
    length = len(text)
    question_count = text.count("?")
    conditional_indicators = len(re.findall(
        r"\b(if|unless|whether|depending|conditional|contingent|maybe|perhaps)\b",
        text, re.I,
    ))

    # Count distinct concepts (crude: unique nouns)
    words = set(re.findall(r"\b\w{4,}\b", text.lower()))
    complexity_score = (
        (min(length / 100, 3.0))     # Length: 0-300+ → 0-3
        + (question_count * 0.5)      # Each question: +0.5
        + (conditional_indicators * 0.5)  # Each conditional: +0.5
        + (min(len(words) / 10, 2.0))  # Vocabulary breadth: 0-20+ → 0-2
    )

    if intent == IntentKey.UNKNOWN:
        complexity_score += 1.0  # Unknown adds ambiguity

    if complexity_score <= 2.0:
        return Level.L1
    elif complexity_score <= 3.5:
        return Level.L2
    elif complexity_score <= 5.0:
        return Level.L3
    elif complexity_score <= 6.5:
        return Level.L4
    elif complexity_score <= 8.0:
        return Level.L5
    elif complexity_score <= 9.5:
        return Level.L6
    else:
        return Level.L7


def infer_step(payload: InboundPayload, intent: IntentKey) -> IQRSQPIStep:
    """
    Infer which IQRSQPI step the payload targets.

    By default, inbound payloads enter at I1 (Intent) and flow through.
    Some patterns indicate later entry points.
    """
    text = payload.raw.lower()

    if intent == IntentKey.UNKNOWN:
        return IQRSQPIStep.I1  # Always start at I1 for unknown

    # Check for review/quality patterns → Q2
    if re.search(r"\b(review|check|audit|verify|validate|quality)\b", text, re.I):
        return IQRSQPIStep.Q2

    # Check for proof patterns → P
    if re.search(r"\b(proof|prove|certify|attest|evidence)\b", text, re.I):
        return IQRSQPIStep.P

    # Check for integration patterns → I2
    if re.search(r"\b(integrate|deploy|publish|launch|deliver|ship)\b", text, re.I):
        return IQRSQPIStep.I2

    # Default entry point
    return IQRSQPIStep.I1


# ── Diamond-scoped BMS defaults ───────────────────────────────────────────────

DIAMOND_BMS_DEFAULTS = {
    Diamond.D1: {"c1": 0.30, "c2": 0.80, "c10": 0.70},
    Diamond.D2: {"c1": 0.50, "c2": 0.60, "c10": 0.55},
    Diamond.D3: {"c1": 0.70, "c2": 0.35, "c10": 0.40},
}


def route(payload: InboundPayload) -> DispatchResult:
    """
    Route an inbound payload through the lattice.

    1. Extract intent → diamond + intent key
    2. Estimate level (altitude)
    3. Infer step entry point
    4. Compute BMS → resolve mode
    5. Resolve archetype
    6. Return DispatchResult

    Escalation: if intent is UNKNOWN, escalate from A1 → A3.
    """
    trace: list[str] = []

    # Step 1: Extract intent
    intent, diamond = extract_intent(payload)
    trace.append(f"Intent: {intent.value}, Diamond: {diamond.value}")

    # Step 2: Estimate level
    level = estimate_level(payload, intent)
    trace.append(f"Level: {level.value}")

    # Step 3: Infer step
    step = infer_step(payload, intent)
    trace.append(f"Step: {step.value}")

    # Step 4: Compute BMS
    params = DIAMOND_BMS_DEFAULTS[diamond]
    bms_result: BMSResult = calculate_bms(
        c1_failure_cost=params["c1"],
        c2_reversibility=params["c2"],
        c10_mechanism_clarity=params["c10"],
        altitude=level,
    )
    trace.append(f"BMS: {bms_result.adjusted_score:.4f} → {bms_result.mode.value}")

    # Escalation: UNKNOWN → A3
    escalation = False
    resolved_mode = bms_result.mode
    if intent == IntentKey.UNKNOWN:
        resolved_mode = BMSMode.A3
        escalation = True
        trace.append("ESCALATED: UNKNOWN intent → A3")

    # Step 5: Resolve archetype
    archetype_cell = resolve_archetype(resolved_mode.value, step.value)
    archetype_file_path = resolve_file(resolved_mode.value, step.value)
    trace.append(f"Archetype: {archetype_cell}")

    # Step 6: Build cell ID
    cell_id = f"{level.value}-{diamond.value}-{step.value}"

    # Route dispatch
    dispatch_route = f"a{resolved_mode.value[1]}"  # a1, a2, a3, a4

    return DispatchResult(
        cell_id=cell_id,
        altitude=level.value,
        diamond=diamond.value,
        step=step.value,
        bms_mode=resolved_mode.value,
        bms_score=bms_result.adjusted_score,
        bms_rationale=bms_result.rationale,
        archetype_cell=archetype_cell,
        archetype_file=str(archetype_file_path.relative_to(_rig_root.parent)),
        dispatch_route=dispatch_route,
        intent_key=intent.value,
        escalation=escalation,
        trace=trace,
    )


def route_batch(payloads: list[InboundPayload]) -> list[DispatchResult]:
    """Route multiple payloads."""
    return [route(p) for p in payloads]


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Router — route payload through lattice")
    parser.add_argument("text", nargs="?", help="Text to route")
    parser.add_argument("--source", default="cli", help="Source channel")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.text:
        parser.print_help()
        return

    payload = InboundPayload(raw=args.text, source=args.source)
    result = route(payload)

    if args.json:
        from dataclasses import asdict
        output = asdict(result)
        print(json.dumps(output, indent=2))
    else:
        print(f"Dispatch Result:")
        print(f"  Cell:     {result.cell_id}")
        print(f"  BMS:      {result.bms_score:.4f} ({result.bms_mode})")
        print(f"  Archetype: {result.archetype_cell} → {result.archetype_file}")
        print(f"  Route:    {result.dispatch_route}")
        print(f"  Intent:   {result.intent_key}")
        if result.escalation:
            print(f"  ESCALATED: yes")
        print(f"  Trace:")
        for t in result.trace:
            print(f"    {t}")


if __name__ == "__main__":
    main()
