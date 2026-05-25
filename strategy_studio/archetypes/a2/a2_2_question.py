"""
A2.2 — Hybrid Question Generation
Uses deterministic templates first (same as A1).
Falls back to LLM expansion for edge cases (UNKNOWN intent, low template coverage).
Never raises. Returns list[StructuredQuery] always.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from strategy_studio.core.types import (
    IntentKey,
    InboundPayload,
    StructuredQuery,
    AuditRow,
)

# ── Question templates (same as A1) ────────────────────────────────────────────

_QUESTION_TEMPLATES: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        "What strategic options exist for {company} in {market}?",
        "How should {company} prioritize investments in {market}?",
        "What are the top 3 risks and mitigations for {company} competing with {competitor}?",
        "Which market segments offer the highest ROI for {company}?",
        "What distribution channels should {company} expand in {market}?",
    ],
    IntentKey.WARGAME: [
        "What is the most likely competitive response from {competitor} to {company}'s move in {market}?",
        "How would {competitor} react if {company} cut prices by 20% in {market}?",
        "What counter-moves should {company} prepare for in {market}?",
        "What asymmetric advantages does {company} hold over {competitor}?",
        "If {competitor} launches a major initiative, how should {company} respond?",
    ],
    IntentKey.FORECAST: [
        "What is the probability that {market} grows >15% YoY over the next 2 years?",
        "Which leading indicators best predict shifts in {market}?",
        "How will {competitor}'s strategy affect {market} dynamics?",
        "What is the base rate of success for {company} entering {market}?",
        "What are the key uncertainty drivers for {company} in {market}?",
    ],
    IntentKey.COMPETITOR_INTEL: [
        "What recent strategic moves has {competitor} made in {market}?",
        "How has {competitor}'s product roadmap shifted in the last 6 months?",
        "What is {competitor}'s perceived weakness in {market}?",
        "Which talent moves signal {competitor}'s future direction?",
        "What partnerships has {competitor} formed in {market}?",
    ],
    IntentKey.CLIENT_INTEL: [
        "What pain points drive {market} buyers to consider {company}?",
        "What is the ideal customer profile (ICP) for {company} in {market}?",
        "Which wedge offers convert best for {company} vs {competitor}?",
        "What is the buyer committee composition in {market}?",
        "What ROI arguments resonate most with {market} decision-makers?",
    ],
    IntentKey.FALSIFY: [
        "What evidence would disprove the belief that {company} can win in {market}?",
        "What is the strongest argument against {company}'s current strategy?",
        "Under what conditions would {company}'s {market} thesis fail?",
        "What data would convince you {company} should exit {market}?",
        "What experiments could invalidate {company}'s core assumption about {competitor}?",
    ],
    IntentKey.UNKNOWN: [
        "What does the incoming request imply about {company}'s intent in {market}?",
        "What clarifying questions should be asked about this request?",
        "Which archetype should handle this request?",
    ],
}


def _extract_entity(text: str, entity_type: str) -> str:
    """Extract named-like entity from text. Deterministic heuristics."""
    words = text.split()
    candidates = [w for w in words if len(w) > 3 and w[0].isupper()]

    if entity_type == "company":
        return candidates[0] if candidates else "RIG"
    elif entity_type == "competitor":
        return candidates[1] if len(candidates) > 1 else "incumbent"
    elif entity_type == "market":
        market_keywords = [
            "EV", "SaaS", "fintech", "healthcare", "AI", "cloud",
            "charging", "logistics", "marketplace", "consumer",
            "smartphone", "mobile", "enterprise", "manufacturing",
            "automotive", "energy", "retail", "software",
            "cybersecurity", "biotech", "semiconductor", "defense",
        ]
        for kw in market_keywords:
            if kw.lower() in text.lower():
                return kw
        return "the market"
    return "unknown"


def _parse_llm_questions(llm_text: str, intent_key: str) -> list[StructuredQuery]:
    """
    Parse LLM response into StructuredQuery objects.
    Expects one question per line. Filters empty lines.
    """
    queries: list[StructuredQuery] = []
    lines = llm_text.strip().split("\n")
    priority = 1
    for line in lines:
        cleaned = line.strip().lstrip("0123456789.-) \t")
        if cleaned and len(cleaned) > 10:
            queries.append(
                StructuredQuery(
                    intent_key=intent_key,
                    question_text=cleaned,
                    priority=priority,
                )
            )
            priority += 1
            if priority > 5:
                break
    return queries


def generate_questions_hybrid(
    intent: IntentKey,
    payload: InboundPayload,
    llm_fallback: Callable[..., str] | None = None,
) -> list[StructuredQuery]:
    """
    Hybrid question generation.
    1. Deterministic template fill (same as A1).
    2. If intent is UNKNOWN or templates yield <2 questions, use LLM expansion.
    3. Never raises. Returns at least 1 question.
    """
    try:
        templates = _QUESTION_TEMPLATES.get(intent, _QUESTION_TEMPLATES[IntentKey.UNKNOWN])
        company = _extract_entity(payload.raw_text, "company")
        competitor = _extract_entity(payload.raw_text, "competitor")
        market = _extract_entity(payload.raw_text, "market")

        # Step 1: Deterministic template generation
        questions: list[StructuredQuery] = []
        selected = templates[:5]
        for idx, tmpl in enumerate(selected):
            text = tmpl.format(company=company, competitor=competitor, market=market)
            questions.append(
                StructuredQuery(
                    intent_key=intent.value,
                    question_text=text,
                    priority=idx + 1,
                )
            )

        # Step 2: LLM expansion for edge cases
        needs_llm = (
            intent == IntentKey.UNKNOWN
            or len(questions) < 2
            or llm_fallback is not None  # always try LLM if available for hybrid mode
        )

        if needs_llm and llm_fallback is not None:
            prompt = (
                f"Generate 3-5 specific research questions for the following request. "
                f"Intent: {intent.value}. "
                f"Company: {company}. Competitor: {competitor}. Market: {market}.\n\n"
                f"Request: {payload.raw_text}\n\n"
                f"Output one question per line, numbered."
            )
            try:
                llm_response = llm_fallback(prompt)
                if llm_response and isinstance(llm_response, str):
                    llm_questions = _parse_llm_questions(llm_response, intent.value)
                    # Merge: use LLM questions to supplement (not replace) template questions
                    existing_texts = {q.question_text for q in questions}
                    for lq in llm_questions:
                        if lq.question_text not in existing_texts:
                            lq.priority = len(questions) + 1
                            questions.append(lq)
                            existing_texts.add(lq.question_text)
                            if len(questions) >= 5:
                                break
            except Exception:
                pass  # LLM failed, use template questions only

        # Ensure at least 1 question
        if not questions:
            questions.append(
                StructuredQuery(
                    intent_key=intent.value,
                    question_text=f"What is the best approach for {company} in {market}?",
                    priority=1,
                )
            )

        return questions[:5]

    except Exception:
        return [
            StructuredQuery(
                intent_key=IntentKey.UNKNOWN.value,
                question_text="What is the core strategic question to answer?",
                priority=1,
            )
        ]
