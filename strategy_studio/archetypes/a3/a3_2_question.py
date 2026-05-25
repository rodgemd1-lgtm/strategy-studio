"""A3.2 — Parallel question generation.

Runs multiple question generators in parallel:
  - template_agent: fills templates (same as A1)
  - perspective_agent: generates from buyer/competitor/investor POV
  - edge_case_agent: generates boundary/edge-case questions

Merges, deduplicates, returns top queries.
Never raises.
"""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor

from strategy_studio.core.types import IntentKey, InboundPayload, StructuredQuery

from strategy_studio.archetypes.a1.a1_2_question import (
    _QUESTION_TEMPLATES,
    _extract_entity,
)


def _template_agent(intent: IntentKey, payload: InboundPayload) -> list[StructuredQuery]:
    """Same template-based generation as A1."""
    templates = _QUESTION_TEMPLATES.get(intent, _QUESTION_TEMPLATES[IntentKey.UNKNOWN])
    company = _extract_entity(payload.raw_text, "company")
    competitor = _extract_entity(payload.raw_text, "competitor")
    market = _extract_entity(payload.raw_text, "market")
    queries = []
    for idx, tmpl in enumerate(templates[:3]):
        text = tmpl.format(company=company, competitor=competitor, market=market)
        queries.append(StructuredQuery(
            intent_key=intent.value, question_text=text, priority=idx + 1,
        ))
    return queries


def _perspective_agent(intent: IntentKey, payload: InboundPayload) -> list[StructuredQuery]:
    """Generate questions from buyer/competitor/investor perspectives."""
    perspectives = ["buyer", "competitor", "investor"]
    company = _extract_entity(payload.raw_text, "company")
    queries = []
    for i, perspective in enumerate(perspectives):
        if intent == IntentKey.WARGAME:
            text = f"How would a {perspective} view {company}'s market move?"
        elif intent == IntentKey.FORECAST:
            text = f"What does the {perspective} model predict for this market?"
        elif intent == IntentKey.COMPETITOR_INTEL:
            text = f"What signals would a {perspective} track about competitor moves?"
        else:
            text=f"What questions would a {perspective} ask about {company}'s strategy?"
        queries.append(StructuredQuery(
            intent_key=intent.value, question_text=text, priority=i + 4,
        ))
    return queries


def _edge_case_agent(intent: IntentKey, payload: InboundPayload) -> list[StructuredQuery]:
    """Generate boundary/edge-case questions."""
    return [
        StructuredQuery(
            intent_key=intent.value,
            question_text=f"What is the worst-case scenario for: {payload.raw_text[:60]}?",
            priority=7,
        ),
        StructuredQuery(
            intent_key=intent.value,
            question_text=f"What assumption, if wrong, would invalidate the entire strategy?",
            priority=8,
        ),
    ]


def generate_questions_parallel(
    intent: IntentKey,
    payload: InboundPayload,
    agent_budget: int = 3,
) -> list[StructuredQuery]:
    """Run question agents in parallel, merge + deduplicate results."""
    agents = [_template_agent, _perspective_agent, _edge_case_agent]
    all_queries: list[StructuredQuery] = []
    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            futures = [ex.submit(a, intent, payload) for a in agents[:agent_budget]]
            for f in futures:
                try:
                    all_queries.extend(f.result(timeout=2.0))
                except Exception:
                    pass
    except Exception:
        for a in agents[:agent_budget]:
            try:
                all_queries.extend(a(intent, payload))
            except Exception:
                pass

    # Deduplicate by question text
    seen: set[str] = set()
    deduped: list[StructuredQuery] = []
    for q in all_queries:
        key = q.question_text.lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(q)

    # Re-priority
    for i, q in enumerate(deduped):
        q.priority = i + 1

    return deduped[:8]  # max 8 questions