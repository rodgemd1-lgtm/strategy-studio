"""
A2.3 — Hybrid Research (Local + API)
Deterministic evidence retrieval from LakeOS / recall.it first.
Calls external APIs when local evidence is insufficient (gaps remain).
LLM can be used to formulate better queries for external APIs.
Never raises. Returns ResearchPack always.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable

from strategy_studio.core.types import (
    StructuredQuery,
    Evidence,
    ResearchPack,
    AuditRow,
    IntentKey,
)

# ── Stub LakeOS query ─────────────────────────────────────────────────────────

def query_lakeos(query: str) -> list[Evidence]:
    """Stub: query LakeOS for evidence. In production hits LakeOS REST API."""
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
    """Stub: query recall.it for evidence. In production hits recall API."""
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


# ── Stub external API query ────────────────────────────────────────────────────

def query_external_api(
    query: str,
    company: str = "",
    competitor: str = "",
    market: str = "",
) -> list[Evidence]:
    """
    Stub: query external APIs (e.g., web search, market data).
    In production this would hit actual external APIs.
    """
    hash_input = f"external:{query}:{company}:{competitor}:{market}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    return [
        Evidence(
            source_uri=f"external://api/{uuid.uuid4().hex[:8]}",
            content_hash=content_hash,
            confidence="M",
            citations=["external_api"],
        )
    ]


def _improve_query_with_llm(
    gap_question: str,
    llm_fallback: Callable[..., str],
    company: str = "",
    competitor: str = "",
    market: str = "",
) -> str:
    """
    Use LLM to reformulate a gap question for better external API results.
    Returns original query if LLM fails.
    """
    prompt = (
        f"Reformulate this research question to be more specific and searchable. "
        f"Company: {company}. Competitor: {competitor}. Market: {market}.\n\n"
        f"Original question: {gap_question}\n\n"
        f"Improved question (one line only):"
    )
    try:
        improved = llm_fallback(prompt)
        if improved and isinstance(improved, str) and len(improved.strip()) > 10:
            return improved.strip()
    except Exception:
        pass
    return gap_question


def execute_research_hybrid(
    questions: list[StructuredQuery],
    llm_fallback: Callable[..., str] | None = None,
    company: str = "",
    competitor: str = "",
    market: str = "",
) -> ResearchPack:
    """
    Hybrid research execution.
    1. Deterministic pass: query LakeOS + recall.it for each question.
    2. Identify gaps (questions with <2 evidence items).
    3. For gaps: if LLM available, reformulate query, then call external APIs.
    4. Never raises. Returns ResearchPack always.
    """
    try:
        all_evidence: list[Evidence] = []
        gaps: list[str] = []

        # Step 1: Deterministic evidence collection
        for sq in questions:
            try:
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
            except Exception:
                gaps.append(sq.question_text)

        # Step 2: Gap filling with external APIs + LLM query improvement
        if gaps and llm_fallback is not None:
            for gap_question in gaps[:3]:  # max 3 gap fills to limit API calls
                try:
                    # Use LLM to improve the query
                    improved_query = _improve_query_with_llm(
                        gap_question, llm_fallback,
                        company=company, competitor=competitor, market=market,
                    )
                    # Call external API with improved query
                    external_evidence = query_external_api(
                        improved_query,
                        company=company,
                        competitor=competitor,
                        market=market,
                    )
                    for ev in external_evidence:
                        ev.confidence = "M"
                    all_evidence.extend(external_evidence)
                except Exception:
                    pass  # External API failed, continue

        # Step 3: If still no evidence at all, add a stub
        if not all_evidence:
            all_evidence.append(
                Evidence(
                    source_uri=f"stub://fallback/{uuid.uuid4().hex[:8]}",
                    content_hash="stub",
                    confidence="L",
                    citations=["no_sources_available"],
                )
            )

        return ResearchPack(
            questions=questions,
            evidence=all_evidence,
            gaps=gaps,
        )

    except Exception:
        return ResearchPack(
            questions=questions,
            evidence=[
                Evidence(
                    source_uri="stub://error",
                    content_hash="error",
                    confidence="L",
                    citations=["research_error"],
                )
            ],
            gaps=[q.question_text for q in questions],
        )
