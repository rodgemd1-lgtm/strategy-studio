"""
A2.4 — Hybrid Solution Synthesis (B-engines + LLM Augmentation)
Deterministic synthesis first (same as A1 scoring logic).
LLM augmentation for edge cases: low evidence, UNKNOWN intent, or low scores.
Never raises. Returns Synthesis always.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from strategy_studio.core.types import (
    ResearchPack,
    Synthesis,
    Option,
    Evidence,
    AuditRow,
)


def _confidence_weight(c: str) -> float:
    return {"H": 1.0, "M": 0.6, "L": 0.3}.get(c.upper(), 0.0)


def _extract_options_from_evidence(evidence: list[Evidence]) -> list[Option]:
    """Extract up to 5 options from evidence deterministically."""
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
    raw = total / max(len(evidence), 1)
    return round(min(max(raw, 0.0), 1.0), 3)


def _parse_llm_options(llm_text: str) -> list[Option]:
    """
    Parse LLM response into Option objects.
    Expects format: Title: Description (one per line) or numbered list.
    """
    options: list[Option] = []
    lines = llm_text.strip().split("\n")
    for line in lines:
        cleaned = line.strip().lstrip("0123456789.-) \t")
        if not cleaned or len(cleaned) < 5:
            continue
        # Try to split on colon or dash
        if ":" in cleaned:
            parts = cleaned.split(":", 1)
            title = parts[0].strip()
            desc = parts[1].strip()
        elif " - " in cleaned:
            parts = cleaned.split(" - ", 1)
            title = parts[0].strip()
            desc = parts[1].strip()
        else:
            title = cleaned[:50]
            desc = cleaned
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


def synthesize_hybrid(
    research_pack: ResearchPack,
    llm_fallback: Callable[..., str] | None = None,
) -> Synthesis:
    """
    Hybrid solution synthesis.
    1. Deterministic pass: extract options from evidence, score, rank.
    2. If <2 options or all scores <0.3, use LLM to augment.
    3. Merge deterministic + LLM options, deduplicate, re-rank.
    4. Never raises. Returns Synthesis always.
    """
    try:
        evidence = research_pack.evidence

        # Step 1: Deterministic synthesis
        options = _extract_options_from_evidence(evidence)
        for opt in options:
            opt.score = _score_option(opt, evidence)
        options.sort(key=lambda o: o.score, reverse=True)

        # Step 2: Check if LLM augmentation is needed
        needs_augmentation = (
            len(options) < 2
            or all(o.score < 0.3 for o in options)
            or len(evidence) < 2
        )

        if needs_augmentation and llm_fallback is not None:
            evidence_summary = "\n".join(
                f"- {ev.source_uri} ({ev.confidence})" for ev in evidence[:10]
            )
            prompt = (
                f"Based on the following evidence, generate 2-5 strategic options. "
                f"Format each as 'Title: Description'.\n\n"
                f"Evidence:\n{evidence_summary}\n\n"
                f"Options:"
            )
            try:
                llm_response = llm_fallback(prompt)
                if llm_response and isinstance(llm_response, str):
                    llm_options = _parse_llm_options(llm_response)
                    # Score LLM options using same evidence pool
                    for opt in llm_options:
                        opt.score = _score_option(opt, evidence)
                    # Merge: deduplicate by title
                    existing_titles = {o.title for o in options}
                    for lo in llm_options:
                        if lo.title not in existing_titles:
                            options.append(lo)
                            existing_titles.add(lo.title)
                    # Re-sort
                    options.sort(key=lambda o: o.score, reverse=True)
            except Exception:
                pass  # LLM augmentation failed, use deterministic only

        # Step 3: Ensure at least 1 option
        if not options:
            options.append(
                Option(
                    id=str(uuid.uuid4())[:8],
                    title="Default Strategy",
                    description="No evidence available. Recommend further research.",
                    score=0.1,
                )
            )

        options = options[:5]  # cap at 5
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

    except Exception:
        return Synthesis(
            options=[
                Option(
                    id="error",
                    title="Error Recovery",
                    description="Synthesis failed. Manual review required.",
                    score=0.0,
                )
            ],
            recommendation=None,
            rationale="Synthesis error. Manual review required.",
        )
