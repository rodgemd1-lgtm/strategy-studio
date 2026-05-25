"""Tests for A2, A3, A4 archetypes."""
import pytest
from strategy_studio.archetypes import run_a1, run_a2, run_a3, run_a4
from strategy_studio.core.types import InboundPayload


SYNTHESIZE_PAYLOAD = InboundPayload(
    raw_text="synthesize market options for Tesla in EV charging"
)
WARGAME_PAYLOAD = InboundPayload(
    raw_text="wargame competitor response to Ford's EV price cut"
)
FORECAST_PAYLOAD = InboundPayload(
    raw_text="forecast EV market growth rate for next 2 years"
)
UNKNOWN_PAYLOAD = InboundPayload(
    raw_text="hello what is this"
)


# ── A2 Hybrid ───────────────────────────────────────────────────────────────

class TestA2Hybrid:
    def test_a2_synthesize_returns_audit(self):
        r = run_a2(SYNTHESIZE_PAYLOAD)
        assert r.archetype == "a2"
        assert r.mode == "HYBRID"

    def test_a2_wargame_returns_audit(self):
        r = run_a2(WARGAME_PAYLOAD)
        assert r.archetype == "a2"
        assert r.status in ("PASS", "QUALITY_FAILED", "INCOMPLETE")

    def test_a2_forecast_returns_audit(self):
        r = run_a2(FORECAST_PAYLOAD)
        assert r.archetype == "a2"

    def test_a2_unknown_returns_audit(self):
        r = run_a2(UNKNOWN_PAYLOAD)
        assert r.archetype == "a2"

    def test_a2_without_lllm_is_deterministic(self):
        """A2 works without LLM — deterministic path."""
        r1 = run_a2(SYNTHESIZE_PAYLOAD)
        r2 = run_a2(SYNTHESIZE_PAYLOAD)
        assert r1.status == r2.status
        assert r1.output_hash == r2.output_hash

    def test_a2_has_duration(self):
        r = run_a2(SYNTHESIZE_PAYLOAD)
        assert r.duration_ms >= 0


# ── A3 Agent-Bounded ────────────────────────────────────────────────────────

class TestA3AgentBounded:
    def test_a3_synthesize_returns_audit(self):
        r = run_a3(SYNTHESIZE_PAYLOAD)
        assert r.archetype == "A3"
        assert r.mode == "AGENT_BOUNDED"

    def test_a3_wargame_returns_audit(self):
        r = run_a3(WARGAME_PAYLOAD)
        assert r.archetype == "A3"

    def test_a3_has_duration(self):
        r = run_a3(SYNTHESIZE_PAYLOAD)
        assert r.duration_ms >= 0

    def test_a3_status_completed_or_conflicts(self):
        r = run_a3(SYNTHESIZE_PAYLOAD)
        assert r.status in ("completed", "completed_with_conflicts")

    def test_a3_deterministic_without_llm(self):
        """A3 works without LLM — deterministic path."""
        r1 = run_a3(SYNTHESIZE_PAYLOAD)
        r2 = run_a3(SYNTHESIZE_PAYLOAD)
        assert r1.status == r2.status


# ── A4 LLM-Free ─────────────────────────────────────────────────────────────

class TestA4LLMFree:
    def test_a4_returns_audit(self):
        r = run_a4(SYNTHESIZE_PAYLOAD)
        assert r.archetype == "A4"
        assert r.mode == "LLM_FREE"

    def test_a4_status_is_deterministic(self):
        r = run_a4(SYNTHESIZE_PAYLOAD)
        assert r.status in ("completed", "QUALITY_FAILED", "INCOMPLETE", "UNKNOWN")

    def test_a4_has_duration(self):
        r = run_a4(SYNTHESIZE_PAYLOAD)
        assert r.duration_ms >= 0

    def test_a4_fully_deterministic(self):
        """A4 must be fully deterministic — same input = same output."""
        r1 = run_a4(SYNTHESIZE_PAYLOAD)
        r2 = run_a4(SYNTHESIZE_PAYLOAD)
        assert r1.status == r2.status
        assert r1.output_hash == r2.output_hash

    def test_a4_unknown_input(self):
        r = run_a4(UNKNOWN_PAYLOAD)
        assert r.archetype == "A4"
        assert r.status in ("UNKNOWN", "INCOMPLETE", "QUALITY_FAILED")