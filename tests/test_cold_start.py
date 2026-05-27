"""
Cold-Start Integration Tests.

Proves the system works from a completely clean import with no prior context.
Tests: routing, determinism, BuildCards, orchestrator, quality gates, receipts.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from strategy_studio.lattice_wire import (
    Altitude,
    Diamond,
    IQRSQPIStep,
    BuildMode,
    LatticeCell,
    compute_bms,
    generate_all_build_cards,
    LatticeOrchestrator,
    run_quality_gates,
    lattice_summary,
    get_all_cells,
    route_company,
)
from strategy_studio.receipts import (
    ColdStartReceipt,
    run_with_receipt,
    _receipt_dir,
)


class TestRouteCompany:
    """route_company() maps company characteristics → lattice cells deterministically."""

    def test_saas_startup_routes_to_d1(self):
        r = route_company("Acme Corp", "SaaS", "startup", "go-to-market strategy")
        assert r.diamond == "D1"
        assert r.altitude == 2
        assert r.bms_mode in ("A1", "A2")
        assert len(r.cell_ids) == 7
        assert r.cell_ids[0] == "L2-D1-I1"

    def test_market_research_routes_to_d2(self):
        r = route_company("Insight Co", "market research", "mid-market")
        assert r.diamond == "D2"

    def test_supply_chain_routes_to_d3(self):
        r = route_company("Logistics LLC", "supply chain", "enterprise", "process efficiency")
        assert r.diamond == "D3"

    def test_route_deterministic(self):
        r1 = route_company("TestCo", "tech", "startup", "market entry")
        r2 = route_company("TestCo", "tech", "startup", "market entry")
        assert r1.altitude == r2.altitude
        assert r1.diamond == r2.diamond
        assert r1.cell_ids == r2.cell_ids

    def test_always_7_cells(self):
        r = route_company("AnyCo", "finance", "growth-stage")
        assert len(r.cell_ids) == 7
        for step in IQRSQPIStep:
            assert any(step.value in cid for cid in r.cell_ids)

    def test_enterprise_routes_high_altitude(self):
        r = route_company("FortuneCo", "banking", "enterprise", "multi-jurisdiction regulatory strategy")
        assert r.altitude >= 4

    def test_solo_routes_low_altitude(self):
        r = route_company("SoloCo", "consulting", "micro", "one-time analysis")
        assert r.altitude <= 2


class TestLatticeDeterminism:
    """Core lattice invariants: always true from cold start."""

    def test_all_147_cells_parse(self):
        for cell in get_all_cells():
            parsed = LatticeCell.parse(cell.cell_id)
            assert parsed.altitude == cell.altitude
            assert parsed.diamond == cell.diamond
            assert parsed.step == cell.step

    def test_bms_l1_is_a1(self):
        bms = compute_bms(altitude=Altitude.L1)
        assert bms.final >= 0.75
        assert bms.select_mode() == BuildMode.A1_PYTHON_ONLY

    def test_bms_l7_is_a4(self):
        bms = compute_bms(altitude=Altitude.L7)
        assert bms.final < 0.25
        assert bms.select_mode() == BuildMode.A4_LLM_AGENT_FREE

    def test_bms_l2_is_a1_by_default(self):
        # L2 default BMS = 0.78 → A1 (altitude adjustment adds 0.28 to raw 0.5)
        bms = compute_bms(altitude=Altitude.L2)
        assert bms.final == 0.78
        assert bms.select_mode() == BuildMode.A1_PYTHON_ONLY

    def test_bms_l3_is_a2_by_default(self):
        bms = compute_bms(altitude=Altitude.L3)
        assert 0.45 <= bms.final < 0.75
        assert bms.select_mode() == BuildMode.A2_HYBRID

    def test_bms_pure(self):
        bms1 = compute_bms(failure_cost=0.8, reversibility=0.3, mechanism_clarity=0.6, altitude=Altitude.L3)
        bms2 = compute_bms(failure_cost=0.8, reversibility=0.3, mechanism_clarity=0.6, altitude=Altitude.L3)
        assert bms1.final == bms2.final
        assert bms1.select_mode() == bms2.select_mode()


class TestBuildCards:
    """All 147 BuildCards generate correctly."""

    def test_147_cards(self):
        cards = generate_all_build_cards()
        assert len(cards) == 147

    def test_all_fields_filled(self):
        for card in generate_all_build_cards():
            assert card.cell_id
            assert card.altitude in range(1, 8)
            assert card.diamond in ("D1", "D2", "D3")
            assert card.step in ("I1", "Q1", "R", "S", "Q2", "P", "I2")
            assert card.mode in ("A1", "A2", "A3", "A4")
            assert card.cost_band
            assert card.doctrine

    def test_tools_and_validation(self):
        for card in generate_all_build_cards():
            assert len(card.tools) > 0, f"{card.cell_id} has no tools"
            assert len(card.validation_criteria) > 0, f"{card.cell_id} has no validation criteria"

    def test_mode_distribution(self):
        cards = generate_all_build_cards()
        by_mode = {}
        for c in cards:
            by_mode[c.mode] = by_mode.get(c.mode, 0) + 1
        assert by_mode.get("A1", 0) == 42
        assert by_mode.get("A2", 0) == 42
        assert by_mode.get("A3", 0) == 42
        assert by_mode.get("A4", 0) == 21


class TestOrchestrator:
    """LatticeOrchestrator executes IQRSQPI pipeline correctly."""

    def test_full_pipeline_seven_steps(self):
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline(
            input_data={"query": "test strategy for Acme Corp in SaaS"},
            altitude=Altitude.L2,
            diamond=Diamond.D1_STRATEGY,
        )
        assert result["summary"]["total_steps"] == 7
        assert result["summary"]["passed"] >= 5

    def test_packet_chain(self):
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline(
            input_data={"query": "cold start test"},
            altitude=Altitude.L2,
            diamond=Diamond.D1_STRATEGY,
        )
        log = result["execution_log"]
        assert len(log) == 7
        for pkt in log:
            assert pkt["cell_id"]
            assert pkt["input_hash"]
            assert pkt["output_hash"]

    def test_empty_input_escalation_field_present(self):
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline(
            input_data={"query": ""},
            altitude=Altitude.L1,
            diamond=Diamond.D1_STRATEGY,
        )
        for pkt in result["execution_log"]:
            assert "status" in pkt


class TestQualityGates:
    """Archon quality gates fire correctly."""

    def test_valid_output_passes(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.I1_INTENT)
        output = {"status": "PASS", "rationale": "test", "options": [{"id": "1", "title": "A"}]}
        result = run_quality_gates(cell, output)
        assert result.passed

    def test_error_status_fails_no_errors_gate(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.I1_INTENT)
        output = {"status": "ERROR", "error": "something broke"}
        result = run_quality_gates(cell, output)
        assert not result.passed

    def test_thin_output_warns(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.I1_INTENT)
        output = {"status": "PASS"}
        result = run_quality_gates(cell, output)
        assert any(g.status.value == "WARN" for g in result.gates)


class TestReceipts:
    """ColdStartReceipt system: create, save, load, verify."""

    @pytest.fixture
    def temp_receipt_dir(self, tmp_path):
        receipts_dir = tmp_path / "receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        with patch("strategy_studio.receipts._receipt_dir", return_value=receipts_dir):
            yield receipts_dir

    def test_receipt_created_and_saved(self, temp_receipt_dir):
        receipt, orch = run_with_receipt(
            company_name="ColdStartTest",
            industry="tech",
            context="market strategy",
        )
        path = receipt.save()
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["receipt_id"] == receipt.run_id
        assert data["total_cells"] == 7
        assert len(data["step_statuses"]) == 7

    def test_receipt_loadable(self, temp_receipt_dir):
        receipt, _ = run_with_receipt(company_name="LoadTest", industry="finance")
        path = receipt.save()
        loaded = ColdStartReceipt.load(receipt.run_id)
        assert loaded["receipt_id"] == receipt.run_id
        assert loaded["bms_mode"] == receipt.bms_mode

    def test_hash_chain(self, temp_receipt_dir):
        receipt, _ = run_with_receipt(company_name="HashTest", industry="retail")
        sealed = receipt.seal()
        assert len(sealed["input_hash"]) == 32
        assert len(sealed["output_hash"]) == 32
        assert len(sealed["receipt_hash"]) == 32
        assert sealed["overall_status"] in ("PASS", "PARTIAL", "FAIL")

    def test_list_receipts(self, temp_receipt_dir):
        run_with_receipt(company_name="ListTest1", industry="tech")
        run_with_receipt(company_name="ListTest2", industry="retail")
        receipts = ColdStartReceipt.list_receipts()
        assert len(receipts) >= 2


class TestLatticeSummary:
    """lattice_summary() returns correct structure."""

    def test_structure(self):
        summary = lattice_summary()
        assert summary["total_cells_147"] == 147
        assert summary["total_cells_588"] == 588
        assert "by_mode" in summary
        assert "by_altitude" in summary
        assert summary["archetypes"] == 28

    def test_mode_counts_sum_to_147(self):
        summary = lattice_summary()
        total = sum(summary["by_mode"].values())
        assert total == 147


if __name__ == "__main__":
    pytest.main([__file__, "-v"])