"""A4.2 — Strict template question generation.

Exact template + entity extraction only. No heuristics.
If entity cannot be determined exactly, uses placeholder.
"""
from __future__ import annotations

import re

from strategy_studio.core.types import IntentKey, InboundPayload, StructuredQuery

_TEMPLATES_STRICT: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        "What strategic options exist for {company} in {market}?",
        "How should {company} prioritize investments in {market}?",
        "What are the top 3 risks for {company} competing with {competitor}?",
    ],
    IntentKey.WARGAME: [
        "What is the most likely response from {competitor} to {company} in {market}?",
        "How would {competitor} react if {company} cut prices by 20%?",
        "What counter-moves should {company} prepare for in {market}?",
    ],
    IntentKey.FORECAST: [
        "What is the probability that {market} grows >15% YoY over 2 years?",
        "Which leading indicators best predict shifts in {market}?",
        "What is the base rate of success for {company} entering {market}?",
    ],
    IntentKey.COMPETITOR_INTEL: [
        "What strategic moves has {competitor} made in {market} in the last 6 months?",
        "What is {competitor}'s perceived weakness in {market}?",
        "Which talent moves signal {competitor}'s future direction?",
    ],
    IntentKey.CLIENT_INTEL: [
        "What pain points drive {market} buyers to consider {company}?",
        "What is the ideal customer profile for {company} in {market}?",
        "Which wedge offers convert best for {company} vs {competitor}?",
    ],
    IntentKey.FALSIFY: [
        "What evidence would disprove the belief that {company} can win in {market}?",
        "What is the strongest argument against {company}'s current strategy?",
        "Under what conditions would {company}'s {market} thesis fail?",
    ],
    IntentKey.UNKNOWN: [
        "What is the core request in this input?",
        "What additional context is needed to classify this request?",
    ],
}


def _extract_exact(text: str, entity_type: str) -> str | None:
    """Exact entity extraction. Returns None if not found deterministically."""
    if entity_type == "company":
        # Look for capitalized word that looks like a proper noun (not at start of sentence)
        m = re.search(r'(?<!^)(?<!\.\s)\b([A-Z][a-zA-Z]{1,15})\b', text)
        return m.group(1) if m else None
    elif entity_type == "competitor":
        # Second proper noun
        matches = re.findall(r'(?<!^)(?<!\.\s)\b([A-Z][a-zA-Z]{1,15})\b', text)
        return matches[1] if len(matches) > 1 else None
    elif entity_type == "market":
        known = ["EV", "SaaS", "fintech", "healthcare", "AI", "cloud", "charging",
                 "logistics", "marketplace", "enterprise", "automotive", "energy",
                 "retail", "software", "cybersecurity", "biotech", "semiconductor"]
        for kw in known:
            if kw.lower() in text.lower():
                return kw
        return None
    return None


def generate_questions_strict(
    intent: IntentKey,
    payload: InboundPayload,
) -> list[StructuredQuery]:
    """Strict template generation. Unknown entities become '[UNKNOWN]'."""
    templates = _TEMPLATES_STRICT.get(intent, _TEMPLATES_STRICT[IntentKey.UNKNOWN])
    company = _extract_exact(payload.raw_text, "company") or "[UNKNOWN]"
    competitor = _extract_exact(payload.raw_text, "competitor") or "[UNKNOWN]"
    market = _extract_exact(payload.raw_text, "market") or "[UNKNOWN]"

    questions: list[StructuredQuery] = []
    for idx, tmpl in enumerate(templates):
        text = tmpl.format(company=company, competitor=competitor, market=market)
        questions.append(StructuredQuery(
            intent_key=intent.value,
            question_text=text,
            priority=idx + 1,
        ))
    return questions