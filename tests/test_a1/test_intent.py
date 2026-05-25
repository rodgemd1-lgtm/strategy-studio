"""Tests for A1.1 — Intent classification."""
from __future__ import annotations

import pytest

from strategy_studio.archetypes.a1.a1_1_intent import classify_intent
from strategy_studio.core.types import IntentKey, InboundPayload


@pytest.mark.parametrize(
    "raw_text, expected_intent, min_confidence",
    [
        # Synthesize patterns
        ("synthesize market options for Tesla", IntentKey.SYNTHESIZE, 0.5),
        ("build a strategic plan for EV charging", IntentKey.SYNTHESIZE, 0.5),
        ("generate options from research data", IntentKey.SYNTHESIZE, 0.5),
        # Wargame patterns
        ("wargame competitor response to our launch", IntentKey.WARGAME, 0.5),
        ("simulate competitor moves in the market", IntentKey.WARGAME, 0.5),
        ("scenario planning for price war", IntentKey.WARGAME, 0.5),
        # Forecast patterns
        ("forecast Q4 revenue based on pipeline", IntentKey.FORECAST, 0.5),
        ("predict market share growth", IntentKey.FORECAST, 0.5),
        ("estimate next quarter performance", IntentKey.FORECAST, 0.5),
        # Competitor intel patterns
        ("analyze competitor AI strategy", IntentKey.COMPETITOR_INTEL, 0.5),
        ("competitive intelligence on Rivian", IntentKey.COMPETITOR_INTEL, 0.5),
        ("track what competitors are building", IntentKey.COMPETITOR_INTEL, 0.5),
        # Client intel patterns
        ("client intelligence prospect needs", IntentKey.CLIENT_INTEL, 0.5),
        ("prospect research for enterprise deals", IntentKey.CLIENT_INTEL, 0.5),
        ("ICP analysis for manufacturing buyers", IntentKey.CLIENT_INTEL, 0.5),
        # Falsify patterns
        ("falsify the assumption that EV is saturated", IntentKey.FALSIFY, 0.5),
        ("test the hypothesis that price elasticity is low", IntentKey.FALSIFY, 0.5),
        # Unknown / vague input
        ("hello", IntentKey.UNKNOWN, 0.0),
        ("what is this", IntentKey.UNKNOWN, 0.0),
        ("", IntentKey.UNKNOWN, 0.0),
    ],
)
def test_classify_intent(raw_text: str, expected_intent: IntentKey, min_confidence: float):
    payload = InboundPayload(raw_text=raw_text, source="test", metadata={})
    intent, confidence = classify_intent(payload)
    assert intent == expected_intent
    assert confidence >= min_confidence


def test_classify_intent_returns_tuple():
    payload = InboundPayload(raw_text="synthesize options", source="test", metadata={})
    result = classify_intent(payload)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_classify_intent_confidence_range():
    payload = InboundPayload(raw_text="wargame scenario", source="test", metadata={})
    intent, confidence = classify_intent(payload)
    assert 0.0 <= confidence <= 1.0


def test_classify_intent_unknown():
    payload = InboundPayload(raw_text="random unrelated text", source="test", metadata={})
    intent, confidence = classify_intent(payload)
    assert intent == IntentKey.UNKNOWN
    assert confidence == 0.0
