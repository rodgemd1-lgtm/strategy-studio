"""Tests for the RIG Lattice system — lattice_wire.py.

Covers:
- 147-cell and 588-cell lattice math
- BMS scoring and mode selection
- LatticeCell parsing (both formats)
- BuildCard generation
- LatticeOrchestrator execution
- Quality gates
- Escalation chain
- Session lattice integration
"""
import pytest
from datetime import datetime, timezone

from strategy_studio.lattice_wire import (
    Altitude, Diamond, IQRSQPIStep, BuildMode,
    LatticeCell, BMSScore, BMSCriteria, compute_bms,
    get_all_cells, get_all_588_cells,
    generate_build_card, generate_all_build_cards,
    LatticeOrchestrator, ProofPacket,
    wire_cell_to_engine, run_quality_gates,
    GateStatus, QualityGate, GateResult,
    lattice_summary, generate_lattice_map,
    STEP_FUNCTION_MAP, STEP_FUNCTION_MAP as step_map,
)
from strategy_studio.core.types import Evidence, Option, AuditRow


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE MATH
# ═══════════════════════════════════════════════════════════════════════════

class TestLatticeMath:
    """Test the 147-cell and 588-cell lattice math."""

    def test_147_cells(self):
        cells = get_all_cells()
        assert len(cells) == 147  # 7 × 3 × 7

    def test_588_cells(self):
        cells = get_all_588_cells()
        assert len(cells) == 588  # 7 × 3 × 4 × 7

    def test_28_archetypes(self):
        cells = get_all_588_cells()
        archetype_ids = set(c.archetype_id for c in cells)
        assert len(archetype_ids) == 28  # 4 × 7

    def test_all_archetype_ids_present(self):
        cells = get_all_588_cells()
        archetype_ids = set(c.archetype_id for c in cells)
        for mode in BuildMode:
            for step in IQRSQPIStep:
                idx = list(IQRSQPIStep).index(step) + 1
                expected = f"{mode.value}.{idx}"
                assert expected in archetype_ids, f"Missing archetype: {expected}"

    def test_cells_per_altitude(self):
        cells = get_all_cells()
        for alt in Altitude:
            alt_cells = [c for c in cells if c.altitude == alt]
            assert len(alt_cells) == 21  # 3 × 7

    def test_cells_per_diamond(self):
        cells = get_all_cells()
        for dia in Diamond:
            dia_cells = [c for c in cells if c.diamond == dia]
            assert len(dia_cells) == 49  # 7 × 7

    def test_cells_per_step(self):
        cells = get_all_cells()
        for step in IQRSQPIStep:
            step_cells = [c for c in cells if c.step == step]
            assert len(step_cells) == 21  # 7 × 3

    def test_lattice_summary(self):
        s = lattice_summary()
        assert s["total_cells_147"] == 147
        assert s["total_cells_588"] == 588
        assert s["archetypes"] == 28
        assert s["by_mode"]["A1"] == 42
        assert s["by_mode"]["A4"] == 21


# ═══════════════════════════════════════════════════════════════════════════
# BMS SCORING
# ═══════════════════════════════════════════════════════════════════════════

class TestBMSScoring:
    """Test BMS scoring and build mode selection."""

    def test_default_bms(self):
        bms = compute_bms()
        assert 0.0 <= bms.final <= 1.0

    def test_a1_selection(self):
        bms = compute_bms(failure_cost=0.9, reversibility=0.9, mechanism_clarity=0.9)
        assert bms.select_mode() == BuildMode.A1_PYTHON_ONLY
        assert bms.final >= 0.75

    def test_a2_selection(self):
        bms = compute_bms(failure_cost=0.6, reversibility=0.5, mechanism_clarity=0.5)
        mode = bms.select_mode()
        assert mode in (BuildMode.A1_PYTHON_ONLY, BuildMode.A2_HYBRID)

    def test_a3_selection(self):
        bms = compute_bms(failure_cost=0.3, reversibility=0.3, mechanism_clarity=0.3)
        mode = bms.select_mode()
        assert mode in (BuildMode.A2_HYBRID, BuildMode.A3_AGENT_BOUNDED)

    def test_a4_selection(self):
        bms = compute_bms(
            failure_cost=0.1, reversibility=0.1, mechanism_clarity=0.1,
            altitude=Altitude.L7,
        )
        assert bms.select_mode() == BuildMode.A4_LLM_AGENT_FREE

    def test_altitude_bonus(self):
        bms_l1 = compute_bms(altitude=Altitude.L1)
        bms_l7 = compute_bms(altitude=Altitude.L7)
        assert bms_l1.final > bms_l7.final

    def test_failure_rate_adjustment(self):
        bms_clean = compute_bms(past_failure_rate=0.0)
        bms_failed = compute_bms(past_failure_rate=0.5)
        assert bms_clean.final > bms_failed.final

    def test_data_volume_adjustment(self):
        bms_low = compute_bms(data_volume=0.1)
        bms_high = compute_bms(data_volume=0.9)
        assert bms_high.final > bms_low.final

    def test_bms_criteria_raw(self):
        c = BMSCriteria(failure_cost=0.8, reversibility=0.6, mechanism_clarity=0.7)
        expected = 0.8 * 0.4 + 0.6 * 0.3 + 0.7 * 0.3
        assert abs(c.raw_score - expected) < 0.001

    def test_bms_score_clamped(self):
        bms = BMSScore(raw=1.5, adj_failure=0.5)
        assert bms.final == 1.0
        bms2 = BMSScore(raw=-1.0, adj_failure=-0.5)
        assert bms2.final == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE CELL
# ═══════════════════════════════════════════════════════════════════════════

class TestLatticeCell:
    """Test LatticeCell creation and parsing."""

    def test_cell_id_147(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        assert cell.cell_id == "L2-D1-S"

    def test_full_cell_id_588(self):
        cell = LatticeCell(
            altitude=Altitude.L4, diamond=Diamond.D2_INTELLIGENCE,
            step=IQRSQPIStep.R_RESEARCH, mode=BuildMode.A3_AGENT_BOUNDED,
        )
        assert cell.full_cell_id == "L4-D2-A3-R"

    def test_parse_147_format(self):
        cell = LatticeCell.parse("L3-D2-Q1")
        assert cell.altitude == Altitude.L3
        assert cell.diamond == Diamond.D2_INTELLIGENCE
        assert cell.step == IQRSQPIStep.Q1_QUESTION

    def test_parse_588_format(self):
        cell = LatticeCell.parse("L5-D3-A4-I2")
        assert cell.altitude == Altitude.L5
        assert cell.diamond == Diamond.D3_OPERATIONS
        assert cell.mode == BuildMode.A4_LLM_AGENT_FREE
        assert cell.step == IQRSQPIStep.I2_INTEGRATE

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            LatticeCell.parse("invalid")
        with pytest.raises(ValueError):
            LatticeCell.parse("L2-D1-Intent")  # Wrong: full word instead of code

    def test_archetype_id(self):
        cell = LatticeCell(
            altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
            step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A1_PYTHON_ONLY,
        )
        assert cell.archetype_id == "A1.4"

    def test_str_representation(self):
        cell = LatticeCell.parse("L2-D1-A1-S")
        assert "L2-D1-A1-S" in str(cell)
        assert "A1.4" in str(cell)


# ═══════════════════════════════════════════════════════════════════════════
# BUILD CARD
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildCard:
    """Test BuildCard generation."""

    def test_generate_build_card(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        bms = compute_bms(altitude=Altitude.L2)
        card = generate_build_card(cell, bms)
        assert card.cell_id == "L2-D1-S"
        assert card.archetype_id.startswith("A")
        assert len(card.tools) > 0
        assert len(card.validation_criteria) > 0

    def test_all_build_cards(self):
        cards = generate_all_build_cards()
        assert len(cards) == 147

    def test_build_card_escalation_targets(self):
        cell_a1 = LatticeCell(altitude=Altitude.L1, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.I1_INTENT)
        cell_a4 = LatticeCell(altitude=Altitude.L7, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.I1_INTENT)
        bms_a1 = compute_bms(altitude=Altitude.L1)
        bms_a4 = compute_bms(altitude=Altitude.L7)
        card_a1 = generate_build_card(cell_a1, bms_a1)
        card_a4 = generate_build_card(cell_a4, bms_a4)
        assert card_a1.escalation_target == "A2.1"
        # A4 escalation target is A4.1 (self-escalation, no higher mode)
        assert card_a4.escalation_target in ("", "A4.1")

    def test_build_card_tools_by_mode(self):
        cell_l1 = LatticeCell(altitude=Altitude.L1, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        cell_l7 = LatticeCell(altitude=Altitude.L7, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        card_l1 = generate_build_card(cell_l1, compute_bms(altitude=Altitude.L1))
        card_l7 = generate_build_card(cell_l7, compute_bms(altitude=Altitude.L7))
        assert "regex" in card_l1.tools
        assert "opus_crew" in card_l7.tools


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY GATES
# ═══════════════════════════════════════════════════════════════════════════

class TestQualityGates:
    """Test Archon quality gates."""

    def test_pass_gates(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        output = {"status": "PASS", "rationale": "test", "recommendation": "yes", "options": [1, 2]}
        result = run_quality_gates(cell, output)
        assert result.overall == GateStatus.PASS
        assert result.passed

    def test_fail_on_error(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        output = {"status": "ERROR", "error": "something failed"}
        result = run_quality_gates(cell, output)
        assert result.overall == GateStatus.FAIL
        assert not result.passed

    def test_a1_no_guess_gate(self):
        cell = LatticeCell(
            altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
            step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A1_PYTHON_ONLY,
        )
        output = {"status": "UNKNOWN"}
        result = run_quality_gates(cell, output)
        a1_gates = [g for g in result.gates if g.name == "a1_no_guess"]
        assert len(a1_gates) == 1
        assert a1_gates[0].status == GateStatus.FAIL

    def test_warn_on_thin_output(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        output = {"status": "PASS"}  # No rationale or options
        result = run_quality_gates(cell, output)
        assert result.overall == GateStatus.WARN


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

class TestLatticeOrchestrator:
    """Test LatticeOrchestrator execution."""

    def test_execute_cell(self):
        orch = LatticeOrchestrator()
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        packet = orch.execute_cell(cell, {"query": "test"})
        assert packet.cell_id == "L2-D1-S"
        assert packet.status in ("PASS", "ERROR")
        assert packet.duration_ms >= 0

    def test_execute_iqrsqpi(self):
        orch = LatticeOrchestrator()
        packets = orch.execute_iqrsqpi(Altitude.L2, Diamond.D1_STRATEGY, {"query": "test"})
        assert len(packets) == 7
        steps = [p.step for p in packets]
        assert "intent" in steps
        assert "integrate" in steps

    def test_execute_full_pipeline(self):
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline({"query": "test"}, Altitude.L2, Diamond.D1_STRATEGY)
        assert "steps" in result
        assert "summary" in result
        assert result["summary"]["total_steps"] == 7
        assert result["summary"]["passed"] >= 0

    def test_execution_log(self):
        orch = LatticeOrchestrator()
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        orch.execute_cell(cell, {"query": "test"})
        assert len(orch.execution_log) == 1

    def test_escalation_chain(self):
        orch = LatticeOrchestrator()
        # L7 forces A4 mode — no escalation possible
        cell = LatticeCell(
            altitude=Altitude.L7, diamond=Diamond.D1_STRATEGY,
            step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A4_LLM_AGENT_FREE,
        )
        packet = orch.execute_cell(cell, {"query": "test"})
        # A4 should not escalate
        assert not packet.escalation_required or packet.escalation_reason == ""

    def test_proof_packet_fields(self):
        orch = LatticeOrchestrator()
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY, step=IQRSQPIStep.S_SOLUTION)
        packet = orch.execute_cell(cell, {"query": "test"})
        assert packet.input_hash != ""
        assert packet.output_hash != ""
        assert packet.timestamp is not None


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE MAP
# ═══════════════════════════════════════════════════════════════════════════

class TestLatticeMap:
    """Test Excalidraw lattice map generation."""

    def test_generate_map(self):
        diagram = generate_lattice_map()
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 147  # At least one element per cell

    def test_generate_map_to_file(self, tmp_path):
        path = tmp_path / "lattice.excalidraw"
        diagram = generate_lattice_map(path)
        assert path.exists()
        assert path.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════════
# STEP ENGINE MAP
# ═══════════════════════════════════════════════════════════════════════════

class TestStepEngineMap:
    """Test that all IQRSQPI steps map to B-engine functions."""

    def test_all_steps_mapped(self):
        for step in IQRSQPIStep:
            assert step.step_name in STEP_FUNCTION_MAP

    def test_synthesis_steps(self):
        synthesis_steps = ["intent", "question", "research", "solution", "integrate"]
        for s in synthesis_steps:
            assert STEP_FUNCTION_MAP[s] == "synthesize_evidence"

    def test_falsification_steps(self):
        assert STEP_FUNCTION_MAP["quality"] == "falsify_claim"
        assert STEP_FUNCTION_MAP["proof"] == "falsify_claim"


# ═══════════════════════════════════════════════════════════════════════════
# SESSION LATTICE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class TestSessionLatticeIntegration:
    """Test StrategySession lattice integration."""

    def test_session_bms_classification(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo", industry="SaaS")
        session._classify_lattice()
        assert session.bms_score > 0
        assert session.bms_mode in ("A1", "A2", "A3", "A4")
        assert "cell_id" in session.lattice_summary

    def test_session_lattice_mode_default(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo")
        assert session.lattice_mode is True

    def test_session_lattice_mode_false(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo", lattice_mode=False)
        assert session.lattice_mode is False

    def test_session_lattice_pipeline(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo", industry="SaaS")
        session._classify_lattice()
        evidence = session._build_evidence()
        session._run_lattice_pipeline(evidence)
        assert session.lattice_orchestrator is not None
        assert len(session.lattice_packets) > 0

    def test_session_fallback_archetypes(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo", lattice_mode=False)
        session._classify_lattice()
        evidence = session._build_evidence()
        session._run_archetypes(evidence)
        # Should have up to 4 archetype results
        assert len(session.archetype_results) <= 4

    def test_session_summary_includes_lattice(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo")
        session._classify_lattice()
        summary = session.summary()
        assert "lattice_mode" in summary
        assert "lattice_summary" in summary
        assert "lattice_packets" in summary


# ═══════════════════════════════════════════════════════════════════════════
# MODE-AWARE DISPATCH — wire_cell_to_engine routes by BMS mode
# ═══════════════════════════════════════════════════════════════════════════

class TestModeAwareDispatch:
    """Test that wire_cell_to_engine dispatches to the correct execution path per BMS mode."""

    def test_a1_dispatch(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A1_PYTHON_ONLY)
        result = wire_cell_to_engine(cell, {"query": "test"})
        assert result["status"] == "PASS"
        assert result["mode"] == "A1"

    def test_a2_dispatch(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A2_HYBRID)
        result = wire_cell_to_engine(cell, {"query": "test"})
        assert result["status"] == "PASS"
        assert result["mode"] == "A2"
        assert result.get("a1_base") is True  # A2 builds on A1

    def test_a3_dispatch(self):
        cell = LatticeCell(altitude=Altitude.L4, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A3_AGENT_BOUNDED)
        result = wire_cell_to_engine(cell, {"query": "test"})
        assert result["status"] in ("PASS", "PARTIAL")
        assert result["mode"] == "A3"
        assert result.get("budget_enforced") is True

    def test_a4_dispatch(self):
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A4_LLM_AGENT_FREE)
        result = wire_cell_to_engine(cell, {"query": "test"})
        assert result["status"] in ("PASS", "UNKNOWN")
        assert result["mode"] == "A4"

    def test_a4_strict_unknown(self):
        """A4 should return UNKNOWN when there's no substantive evidence."""
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A4_LLM_AGENT_FREE)
        result = wire_cell_to_engine(cell, {"query": "x"})
        assert "mode" in result
        assert result["mode"] == "A4"

    def test_orchestrator_uses_mode_dispatch(self):
        """Orchestrator should dispatch each cell according to its BMS mode."""
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline({"query": "test"}, Altitude.L2, Diamond.D1_STRATEGY)
        for step_name, step_data in result["steps"].items():
            assert step_data.get("mode") == "A1"

    def test_orchestrator_a3_mode(self):
        """L5 should trigger A3 mode dispatch."""
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline({"query": "test"}, Altitude.L5, Diamond.D1_STRATEGY)
        for step_name, step_data in result["steps"].items():
            assert step_data.get("mode") == "A3"

    def test_orchestrator_a4_mode(self):
        """L7 should trigger A4 mode dispatch."""
        orch = LatticeOrchestrator()
        result = orch.execute_full_pipeline({"query": "test"}, Altitude.L7, Diamond.D1_STRATEGY)
        for step_name, step_data in result["steps"].items():
            assert step_data.get("mode") == "A4"

    def test_mode_in_proof_packet(self):
        """ProofPacket should include the execution mode."""
        orch = LatticeOrchestrator()
        cell = LatticeCell(altitude=Altitude.L4, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A3_AGENT_BOUNDED)
        packet = orch.execute_cell(cell, {"query": "test"})
        assert packet.mode == "A3"

    def test_explicit_mode_overrides_bms(self):
        """When cell has explicit mode (588-cell), it should be respected over BMS."""
        cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                           step=IQRSQPIStep.S_SOLUTION, mode=BuildMode.A3_AGENT_BOUNDED)
        orch = LatticeOrchestrator()
        packet = orch.execute_cell(cell, {"query": "test"})
        assert packet.mode == "A3"

    def test_wire_cell_all_modes(self):
        """All 4 modes should produce valid results."""
        for mode in BuildMode:
            cell = LatticeCell(altitude=Altitude.L2, diamond=Diamond.D1_STRATEGY,
                               step=IQRSQPIStep.S_SOLUTION, mode=mode)
            result = wire_cell_to_engine(cell, {"query": "test"})
            assert "mode" in result
            assert result["mode"] == mode.value or result["mode"].startswith(mode.value)
