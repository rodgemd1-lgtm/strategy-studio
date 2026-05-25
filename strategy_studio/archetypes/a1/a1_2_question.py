"""
A1.2 — Question (PYTHON_ONLY)
Generates structured research questions from IntentKey + InboundPayload.
Deterministic templates with placeholders. No LLM in decision path.
"""

from __future__ import annotations

import uuid

from strategy_studio.core.types import (
    IntentKey,
    InboundPayload,
    StructuredQuery,
    AuditRow,
)

# ── Question templates ─────────────────────────────────────────────────────────

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
    # Very basic extraction: capitalize any capitalized token >3 chars
    candidates = [w for w in words if len(w) > 3 and w[0].isupper()]

    if entity_type == "company":
        # Return first capitalized word or default
        return candidates[0] if candidates else "RIG"
    elif entity_type == "competitor":
        # Return second capitalized word or default
        return candidates[1] if len(candidates) > 1 else "incumbent"
    elif entity_type == "market":
        # Look for known market keywords
        market_keywords = ["EV", "SaaS", "fintech", "healthcare", "AI", "cloud",
                           "charging", "logistics", "marketplace", "consumer",
                           "smartphone", "mobile", "enterprise", "manufacturing",
                           "automotive", "energy", "retail", "software",
                           "cybersecurity", "biotech", "semiconductor", "defense"]
        for kw in market_keywords:
            if kw.lower() in text.lower():
                return kw
        return "the market"
    return "unknown"


def generate_questions(
    intent: IntentKey, payload: InboundPayload
) -> list[StructuredQuery]:
    """
    Generate 3-5 StructuredQuery objects from intent + payload.
    Templates are filled with entities extracted from raw_text.
    """
    templates = _QUESTION_TEMPLATES.get(intent, _QUESTION_TEMPLATES[IntentKey.UNKNOWN])
    company = _extract_entity(payload.raw_text, "company")
    competitor = _extract_entity(payload.raw_text, "competitor")
    market = _extract_entity(payload.raw_text, "market")

    questions: list[StructuredQuery] = []
    selected = templates[:5]  # max 5
    for idx, tmpl in enumerate(selected):
        text = tmpl.format(company=company, competitor=competitor, market=market)
        questions.append(
            StructuredQuery(
                intent_key=intent.value,
                question_text=text,
                priority=idx + 1,
            )
        )
    return questions
