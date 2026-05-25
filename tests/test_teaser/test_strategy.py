"""Tests for HED-pattern strategy generation."""
from __future__ import annotations

import json
from pathlib import Path

from strategy_studio.teaser.schema import TeaserInput
from strategy_studio.teaser.strategy import build_strategy_brief, render_strategy_markdown, run_strategy_batch


_FIXTURES = Path(__file__).parent.parent / "fixtures" / "prospects_sample.jsonl"


def _hed_record() -> dict:
    for line in _FIXTURES.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["prospect_id"] == "hed-inc":
            return record
    raise AssertionError("hed-inc fixture missing")


def test_strategy_brief_uses_hed_case_study_spine():
    record = _hed_record()
    brief = build_strategy_brief(record)
    md = render_strategy_markdown(brief)

    assert brief.generated_for == "RIG and Mike Rodgers"
    assert brief.system_name == "HED FORGE"
    assert brief.priority_tier in {"A", "B", "C"}
    assert brief.estimated_contract_value_usd >= 50_000
    assert "THE FIRM" in md
    assert "THE SITUATION" in md
    assert "THE EXAMINATION" in md
    assert "THE SYSTEM: HED FORGE" in md
    assert "THE APPROACH" in md
    assert "THE PREDICTION" in md
    assert "THE ENGAGEMENT TERMS" in md
    assert "THE OUTCOME / NEXT MOVE" in md
    assert "NVIS Gate" in md
    assert "CMMC Level 2" in md


def test_strategy_batch_outputs_json_markdown_and_aggregates(tmp_path: Path):
    out_dir = tmp_path / "strategies"
    summary = tmp_path / "summary.jsonl"
    aggregate_jsonl = tmp_path / "strategies.jsonl"
    aggregate_csv = tmp_path / "strategies.csv"

    result = run_strategy_batch(
        prospects_jsonl=_FIXTURES,
        out_dir=out_dir,
        workers=2,
        summary_path=summary,
        aggregate_jsonl=aggregate_jsonl,
        aggregate_csv=aggregate_csv,
    )

    assert result["summary"]["total"] == 5
    assert result["summary"]["ok"] == 5
    assert result["summary"]["generated_for"] == "RIG and Mike Rodgers"
    assert (out_dir / "hed-inc" / "strategy.json").exists()
    assert (out_dir / "hed-inc" / "strategy.md").exists()
    assert sum(1 for _ in aggregate_jsonl.open()) == 5
    assert sum(1 for _ in aggregate_csv.open()) == 6


def test_strategy_brief_validates_against_teaser_input():
    TeaserInput.model_validate(_hed_record())
    brief = build_strategy_brief(_hed_record())
    assert len(brief.outbound_sequence) == 5
    assert len(brief.delivery_plan) == 3
    assert len(brief.stop_conditions) == 3
