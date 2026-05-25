"""Tests for A1.2 — Question generation."""
from __future__ import annotations

import pytest

from strategy_studio.archetypes.a1.a1_2_question import generate_questions
from strategy_studio.core.types import IntentKey, InboundPayload


@pytest.mark.parametrize(
    "intent",
    [
        IntentKey.SYNTHESIZE,
        IntentKey.WARGAME,
        IntentKey.FORECAST,
        IntentKey.COMPETITOR_INTEL,
        IntentKey.CLIENT_INTEL,
        IntentKey.FALSIFY,
    ],
)
def test_generate_questions_for_all_intents(intent: IntentKey):
    payload = InboundPayload(
        raw_text=f"{intent.name.lower()} market options for Tesla in EV charging",
        source="test",
        metadata={},
    )
    questions = generate_questions(intent, payload)
    assert 3 <= len(questions) <= 5
    for q in questions:
        assert q.intent_key == intent.value
        assert q.question_text
        assert 1 <= q.priority <= 5


def test_generate_questions_with_entity_extraction():
    payload = InboundPayload(
        raw_text="synthesize options for Apple in smartphone market vs Samsung",
        source="test",
        metadata={},
    )
    questions = generate_questions(IntentKey.SYNTHESIZE, payload)
    assert len(questions) >= 3
    # Check that entities were substituted into templates
    texts = [q.question_text for q in questions]
    assert any("Apple" in t for t in texts)
    assert any("Samsung" in t for t in texts)
    assert any("smartphone" in t for t in texts)


def test_generate_questions_ordering():
    payload = InboundPayload(
        raw_text="forecast EV market growth",
        source="test",
        metadata={},
    )
    questions = generate_questions(IntentKey.FORECAST, payload)
    priorities = [q.priority for q in questions]
    assert priorities == sorted(priorities)
    assert priorities[0] == 1


def test_generate_questions_returns_structured_queries():
    payload = InboundPayload(raw_text="wargame competitor response", source="test", metadata={})
    questions = generate_questions(IntentKey.WARGAME, payload)
    assert all(type(q).__name__ == "StructuredQuery" for q in questions)


def test_generate_questions_unknown_fallback():
    payload = InboundPayload(raw_text="random text with no meaning", source="test", metadata={})
    questions = generate_questions(IntentKey.UNKNOWN, payload)
    assert len(questions) >= 1
    assert questions[0].intent_key == IntentKey.UNKNOWN.value
