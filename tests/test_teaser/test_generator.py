"""Tests for the teaser generator."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from strategy_studio.teaser.generator import generate_teaser
from strategy_studio.teaser.schema import TeaserInput


_FIXTURES = Path(__file__).parent.parent / "fixtures" / "prospects_sample.jsonl"


@pytest.fixture
def hed_input() -> TeaserInput:
    """Load HED (first prospect) as a known-good fixture."""
    with _FIXTURES.open() as f:
        for line in f:
            d = json.loads(line)
            if d["prospect_id"] == "hed-inc":
                return TeaserInput.model_validate(d)
    raise RuntimeError("hed-inc fixture missing")


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    return tmp_path / "teasers"


def test_generates_all_four_artifacts(hed_input: TeaserInput, out_dir: Path):
    result = generate_teaser(hed_input, out_dir)
    bundle = out_dir / "hed-inc"
    assert (bundle / "index.html").exists()
    assert (bundle / "teaser.md").exists()
    assert (bundle / "teaser_input.json").exists()
    assert (bundle / "proof_packet.json").exists()
    assert result["html_bytes"] > 5000  # non-trivial render
    assert result["md_bytes"] > 1500


def test_html_contains_wound_language(hed_input: TeaserInput, out_dir: Path):
    generate_teaser(hed_input, out_dir)
    html = (out_dir / "hed-inc" / "index.html").read_text()
    assert "18 months" in html
    assert "defense channel" in html
    assert "CMMC" in html


def test_html_contains_all_three_engines(hed_input: TeaserInput, out_dir: Path):
    generate_teaser(hed_input, out_dir)
    html = (out_dir / "hed-inc" / "index.html").read_text()
    assert "Control Modules" in html
    assert "Displays" in html
    assert "Keypads" in html
    assert "$42M" in html


def test_html_contains_all_three_threats(hed_input: TeaserInput, out_dir: Path):
    generate_teaser(hed_input, out_dir)
    html = (out_dir / "hed-inc" / "index.html").read_text()
    assert "Parker Hannifin" in html
    assert "Bosch Rexroth" in html
    assert "Grayhill" in html


def test_proof_packet_has_required_fields(hed_input: TeaserInput, out_dir: Path):
    generate_teaser(hed_input, out_dir)
    proof = json.loads((out_dir / "hed-inc" / "proof_packet.json").read_text())
    assert "proof_packet" in proof
    assert "falsification" in proof
    assert "generated_at" in proof
    assert len(proof["falsification"]) == 3  # one per engine
    for fp in proof["falsification"]:
        assert fp["status"] == "open"
        assert "disproof_test" in fp


def test_intent_is_client_intel(hed_input: TeaserInput, out_dir: Path):
    result = generate_teaser(hed_input, out_dir)
    assert result["intent"] == "client_intel"
    assert result["intent_confidence"] >= 0.5


def test_validation_rejects_too_few_advantages():
    with pytest.raises(Exception):
        TeaserInput.model_validate({
            "prospect_id": "x", "company_name": "X", "company_short": "X",
            "employees": 1, "revenue_usd_m": 1, "years_in_business": 1,
            "headquarters": "X", "industry": "X", "industry_short": "x",
            "wound_months": 12, "wound_channel": "x", "wound_trigger": "x",
            "capability_count": 2, "capability_names": ["a", "b"],
            "capability_gap": "x",
            "mechanism_name": "x", "mechanism_description": "x",
            "advantages": ["only one"],  # too few
            "comparable_company": "x", "comparable_year_start": 2020,
            "comparable_year_end": 2024,
            "comparable_revenue_start_m": 1, "comparable_revenue_end_m": 2,
            "comparable_segment_growth_m": 1,
            "engines": [{"name": "x", "sigma_label": "x", "flywheel_type": "data",
                        "flywheel_loop": "x", "target_revenue_m": 1}] * 3,
            "threats": [{"name": "x", "tier": "Tier 1", "horizon_months": "1",
                        "key_fact": "x", "source_weight": 0.5}] * 3,
            "disqualifiers": ["a", "b", "c"],
            "cloned_site_url": "https://example.com",
            "contact_name": "X", "contact_role": "X",
            "evidence_sources": ["s1", "s2"],
        })


def test_validation_rejects_too_few_evidence_sources():
    with pytest.raises(Exception):
        TeaserInput.model_validate({
            "prospect_id": "x", "company_name": "X", "company_short": "X",
            "employees": 1, "revenue_usd_m": 1, "years_in_business": 1,
            "headquarters": "X", "industry": "X", "industry_short": "x",
            "wound_months": 12, "wound_channel": "x", "wound_trigger": "x",
            "capability_count": 2, "capability_names": ["a", "b"],
            "capability_gap": "x",
            "mechanism_name": "x", "mechanism_description": "x",
            "advantages": ["a", "b", "c"],
            "comparable_company": "x", "comparable_year_start": 2020,
            "comparable_year_end": 2024,
            "comparable_revenue_start_m": 1, "comparable_revenue_end_m": 2,
            "comparable_segment_growth_m": 1,
            "engines": [{"name": "x", "sigma_label": "x", "flywheel_type": "data",
                        "flywheel_loop": "x", "target_revenue_m": 1}] * 3,
            "threats": [{"name": "x", "tier": "Tier 1", "horizon_months": "1",
                        "key_fact": "x", "source_weight": 0.5}] * 3,
            "disqualifiers": ["a", "b", "c"],
            "cloned_site_url": "https://example.com",
            "contact_name": "X", "contact_role": "X",
            "evidence_sources": ["only-one"],  # too few
        })


def test_batch_runner_with_sample_fixtures(out_dir: Path):
    from strategy_studio.teaser.batch import run_batch
    result = run_batch(
        prospects_jsonl=_FIXTURES,
        out_dir=out_dir,
        workers=2,
    )
    s = result["summary"]
    assert s["total"] == 5
    assert s["ok"] == 5
    assert s["validation_errors"] == 0
    assert s["generation_errors"] == 0
