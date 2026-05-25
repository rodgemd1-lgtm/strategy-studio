"""
A1.3 — Research (PYTHON_ONLY)
Deterministic evidence retrieval from LakeOS / recall.it.
No LLM calls.  Uses stubs / heuristics for source count confidence.
"""

from __future__ import annotations

import hashlib
import uuid

from strategy_studio.core.types import (
    StructuredQuery,
    Evidence,
    ResearchPack,
    AuditRow,
    IntentKey,
)

# ── Stub LakeOS query ─────────────────────────────────────────────────────────

def query_lakeos(query: str) -> list[Evidence]:
    """
    Stub: query LakeOS for evidence.
    In production this hits the LakeOS REST API.
    """
    hash_input = f"lakeos:{query}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    return [
        Evidence(
            source_uri=f"lakeos://query/{uuid.uuid4().hex[:8]}",
            content_hash=content_hash,
            confidence="H",
            citations=["lakeos_primary"],
        )
    ]


# ── Stub recall query ──────────────────────────────────────────────────────────

def query_recall(query: str, limit: int = 5) -> list[Evidence]:
    """
    Stub: query recall.it for evidence.
    In production this hits recall API.
    """
    count = max(1, min(limit, 5))
    results: list[Evidence] = []
    for i in range(count):
        hash_input = f"recall:{query}:{i}"
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        confidence: str = "H" if i == 0 else "M" if i == 1 else "L"
        results.append(
            Evidence(
                source_uri=f"recall://result/{uuid.uuid4().hex[:8]}",
                content_hash=content_hash,
                confidence=confidence,
                citations=["recall_search"],
            )
        )
    return results


# ── Research execution ─────────────────────────────────────────────────────────

def execute_research(questions: list[StructuredQuery]) -> ResearchPack:
    """
    For EACH question, query LakeOS and recall.it.
    Collect evidence, mark confidence H/M/L based on source count.
    Identify gaps (questions with <2 evidence items).
    """
    all_evidence: list[Evidence] = []
    gaps: list[str] = []

    for sq in questions:
        lake_evidence = query_lakeos(sq.question_text)
        recall_evidence = query_recall(sq.question_text, limit=3)
        combined = lake_evidence + recall_evidence

        # Mark confidence based on source count
        if len(combined) >= 3:
            for ev in combined:
                ev.confidence = "H"
        elif len(combined) == 2:
            for ev in combined:
                ev.confidence = "M"
        else:
            for ev in combined:
                ev.confidence = "L"

        all_evidence.extend(combined)

        if len(combined) < 2:
            gaps.append(sq.question_text)

    return ResearchPack(
        questions=questions,
        evidence=all_evidence,
        gaps=gaps,
    )
