"""Tests for the RIG 20x AI GTM strategy layer."""
from __future__ import annotations

import json
from pathlib import Path

from strategy_studio.teaser.gtm20x import (
    EXPERTS,
    build_enhanced_strategy,
    get_question_bank,
    render_enhanced_markdown,
    run_20x_batch,
)


_FIXTURES = Path(__file__).parent.parent / "fixtures" / "prospects_sample.jsonl"


def _hed_record() -> dict:
    for line in _FIXTURES.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["prospect_id"] == "hed-inc":
            return record
    raise AssertionError("hed-inc fixture missing")


def test_question_bank_has_exactly_100_solutions():
    questions = get_question_bank()
    assert len(questions) == 100
    assert len({q.id for q in questions}) == 100
    assert all(q.solution for q in questions)
    assert all(q.evidence_gate for q in questions)


def test_expert_board_uses_named_processes():
    assert len(EXPERTS) == 20
    names = {e["expert"] for e in EXPERTS}
    assert "April Dunford" in names
    assert "Richard Rumelt" in names
    assert "Matthew Dixon and Brent Adamson" in names
    assert all(e["process"] for e in EXPERTS)


def test_enhanced_strategy_contains_20x_sections():
    enhanced = build_enhanced_strategy(_hed_record(), Path("out/strategies_1783"), "questions_100.md")
    md = render_enhanced_markdown(enhanced)
    assert enhanced.generated_for == "RIG and Mike Rodgers"
    assert enhanced.twenty_x_score >= enhanced.priority_score
    assert len(enhanced.expert_lenses) == 20
    assert len(enhanced.top_questions) == 20
    assert len(enhanced.deviation_moves) == 7
    assert {m.deviation_sigma for m in enhanced.deviation_moves} == {-30, -20, -10, 0, 10, 20, 30}
    assert "Expert Board Lenses" in md
    assert "RIG Deviate Engine: -30/+30" in md
    assert "Top 20 Questions Applied" in md
    assert "NVIS Gate" in md


def test_20x_batch_writes_system_and_account_files(tmp_path: Path):
    out = tmp_path / "gtm20x"
    result = run_20x_batch(
        input_path=_FIXTURES,
        output_dir=out,
        strategy_dir=tmp_path / "strategies",
        workers=2,
    )
    summary = result["summary"]
    assert summary["total"] == 5
    assert summary["ok"] == 5
    assert summary["question_count"] == 100
    assert summary["expert_count"] == 20
    assert (out / "rig_ai_gtm_system.md").exists()
    assert (out / "questions_100.md").exists()
    assert (out / "hed-inc" / "gtm20x.md").exists()
    assert sum(1 for _ in (out / "gtm20x_1783.jsonl").open()) == 5
