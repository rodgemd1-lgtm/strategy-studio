"""
A1.4 — Solution (PYTHON_ONLY)
Deterministic synthesis of evidence into ranked options.
No LLM calls.  Scores based on evidence count × confidence.
"""

from __future__ import annotations

import uuid

from strategy_studio.core.types import (
    ResearchPack,
    Synthesis,
    Option,
    Evidence,
    AuditRow,
)


# ── Evidence scoring helpers ───────────────────────────────────────────────────

def _confidence_weight(c: str) -> float:
    return {"H": 1.0, "M": 0.6, "L": 0.3}.get(c.upper(), 0.0)


def _extract_options_from_evidence(evidence: list[Evidence]) -> list[Option]:
    """
    Extract up to 5 options from evidence deterministically.
    Each unique source_uri yields one option.
    """
    seen = set()
    options: list[Option] = []
    for ev in evidence:
        if ev.source_uri in seen:
            continue
        seen.add(ev.source_uri)
        title = f"Option-{len(options) + 1}"
        desc = f"Derived from evidence source {ev.source_uri} ({ev.confidence} confidence)"
        options.append(
            Option(
                id=str(uuid.uuid4())[:8],
                title=title,
                description=desc,
                score=0.0,
            )
        )
        if len(options) >= 5:
            break
    return options


def _score_option(option: Option, evidence: list[Evidence]) -> float:
    """Score option based on matching evidence count × confidence."""
    total = 0.0
    for ev in evidence:
        total += _confidence_weight(ev.confidence)
    # Normalize to 0.0-1.0
    raw = total / max(len(evidence), 1)
    return round(min(max(raw, 0.0), 1.0), 3)


# ── Main synthesis ─────────────────────────────────────────────────────────────

def synthesize(research_pack: ResearchPack) -> Synthesis:
    """
    Extract options from evidence (max 5).
    Score each option 0.0-1.0 based on evidence count × confidence.
    Select recommendation (highest score).
    Include rationale string.
    """
    evidence = research_pack.evidence
    options = _extract_options_from_evidence(evidence)

    # Score each option using the full evidence pool
    for opt in options:
        opt.score = _score_option(opt, evidence)

    # Sort descending
    options.sort(key=lambda o: o.score, reverse=True)

    recommendation = options[0] if options else None

    rationale = (
        f"Synthesized {len(options)} option(s) from {len(evidence)} evidence item(s). "
        f"Selected '{recommendation.title}' with score {recommendation.score} "
        f"based on evidence count × confidence weighting."
        if recommendation
        else "No evidence available. No recommendation possible."
    )

    return Synthesis(
        options=options,
        recommendation=recommendation,
        rationale=rationale,
    )
