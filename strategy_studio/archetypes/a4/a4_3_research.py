"""A4.3 — Purely local evidence gathering.

No network calls. Evidence comes from:
  1. Payload metadata (if provided)
  2. Derived from question text (content-hash based)
  3. Provided evidence list in payload

If insufficient evidence: gaps are flagged. No guessing.
"""
from __future__ import annotations

import hashlib

from strategy_studio.core.types import Evidence, InboundPayload, ResearchPack, StructuredQuery


def execute_research_local(
    questions: list[StructuredQuery],
    payload: InboundPayload,
) -> ResearchPack:
    """Gather evidence from local sources only."""
    evidence: list[Evidence] = []

    # Source 1: payload metadata
    for key, value in payload.metadata.items():
        if value and isinstance(value, str) and len(value) > 3:
            h = hashlib.md5(value.encode()).hexdigest()[:12]
            evidence.append(Evidence(
                source_uri=f"metadata://{key}",
                content_hash=h,
                confidence="H",
                citations=[str(value)],
            ))

    # Source 2: derive from question text
    for q in questions:
        h = hashlib.md5(q.question_text.encode()).hexdigest()[:12]
        evidence.append(Evidence(
            source_uri=f"derived://{h}",
            content_hash=h,
            confidence="M",
            citations=[q.question_text],
        ))

    # Identify gaps
    gaps: list[str] = []
    for q in questions:
        q_words = set(q.question_text.lower().split())
        covered = False
        for e in evidence:
            e_words = set(" ".join(e.citations).lower().split())
            if len(q_words & e_words) >= 2:
                covered = True
                break
        if not covered:
            gaps.append(f"No local evidence for: {q.question_text}")

    return ResearchPack(questions=questions, evidence=evidence, gaps=gaps)