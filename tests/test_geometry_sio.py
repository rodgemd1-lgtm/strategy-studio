"""
Unit tests for BMS scoring engine and cell ID validator.
Day 1 deliverable. ≥6 passing tests for Geometry Gate.
"""

import pytest
from strategy_studio.lattice._types_reexport import (
    Level, Diamond, BMSMode, IQRSQPIStep, LatticeCoordinate
)
from strategy_studio.lattice.validator import parse_cell_id, is_valid_cell_id, is_old_format
from strategy_studio.hermes.bms import calculate_bms, score_workflow


# ─────────────────────────────────────────────
# Cell ID Validator Tests
# ─────────────────────────────────────────────

class TestCellIDValidator:
    def test_valid_cell_id(self):
        """Must accept L2-D1-A1-I1."""
        coord = parse_cell_id("L2-D1-A1-I1")
        assert coord.level == Level.L2
        assert coord.diamond == Diamond.D1
        assert coord.bms_mode == BMSMode.A1
        assert coord.step == IQRSQPIStep.I1

    def test_all_valid_cells(self):
        """All 588 cell IDs should parse cleanly."""
        from strategy_studio.lattice.validator import generate_all_cell_ids
        cells = generate_all_cell_ids()
        assert len(cells) == 588
        for cell_id in cells:
            coord = parse_cell_id(cell_id)
            assert coord.cell_id == cell_id

    def test_reject_old_format(self):
        """Must reject L2-D1-Intent (old format that omits Z-axis)."""
        with pytest.raises(ValueError, match="old format"):
            parse_cell_id("L2-D1-Intent")

    def test_reject_old_format_all_steps(self):
        """All old-format step names should be rejected."""
        old_steps = ["Intent", "Question", "Research", "Solution", "Quality", "Proof", "Integrate"]
        for step in old_steps:
            with pytest.raises(ValueError, match="old format"):
                parse_cell_id(f"L2-D1-{step}")

    def test_is_valid_cell_id(self):
        assert is_valid_cell_id("L1-D1-A1-I1") is True
        assert is_valid_cell_id("L7-D3-A4-I2") is True
        assert is_valid_cell_id("L2-D1-Intent") is False
        assert is_valid_cell_id("invalid") is False

    def test_is_old_format(self):
        assert is_old_format("L2-D1-Intent") is True
        assert is_old_format("L2-D1-A1-I1") is False

    def test_coordinate_properties(self):
        coord = parse_cell_id("L1-D1-A1-I1")
        assert coord.is_a1 is True
        assert coord.requires_approval is False
        assert coord.primary_coordinate == "L1-D1-A1"

    def test_a4_requires_approval(self):
        coord = parse_cell_id("L1-D1-A4-I1")
        assert coord.requires_approval is True
        assert coord.is_a1 is False


# ─────────────────────────────────────────────
# BMS Scoring Engine Tests
# ─────────────────────────────────────────────

class TestBMSEngine:
    def test_a1_high_confidence(self):
        """Low failure cost + high reversibility + clear mechanism = A1."""
        result = calculate_bms(
            c1_failure_cost=0.1,   # low cost (reversed: 0.9)
            c2_reversibility=0.9,
            c10_mechanism_clarity=0.9,
        )
        assert result.mode == BMSMode.A1
        assert result.adjusted_score >= 0.75

    def test_a2_medium_confidence(self):
        """Medium factors = A2."""
        result = calculate_bms(
            c1_failure_cost=0.4,
            c2_reversibility=0.5,
            c10_mechanism_clarity=0.5,
        )
        assert result.mode == BMSMode.A2
        assert 0.45 <= result.adjusted_score < 0.75

    def test_a3_low_confidence(self):
        """Low factors = A3."""
        result = calculate_bms(
            c1_failure_cost=0.7,
            c2_reversibility=0.3,
            c10_mechanism_clarity=0.3,
        )
        assert result.mode == BMSMode.A3
        assert 0.25 <= result.adjusted_score < 0.45

    def test_a4_very_low_confidence(self):
        """Very low factors = A4."""
        result = calculate_bms(
            c1_failure_cost=0.9,
            c2_reversibility=0.1,
            c10_mechanism_clarity=0.1,
        )
        assert result.mode == BMSMode.A4
        assert result.adjusted_score < 0.25

    def test_recent_failure_penalty(self):
        """Recent failure should reduce score by 0.10."""
        without = calculate_bms(0.2, 0.8, 0.8, recent_failure=False)
        with_fail = calculate_bms(0.2, 0.8, 0.8, recent_failure=True)
        assert with_fail.adjusted_score == pytest.approx(without.adjusted_score - 0.10)

    def test_altitude_penalty(self):
        """Higher levels should have altitude penalty."""
        l1 = calculate_bms(0.2, 0.8, 0.8, altitude=Level.L1)
        l7 = calculate_bms(0.2, 0.8, 0.8, altitude=Level.L7)
        assert l7.adjusted_score < l1.adjusted_score
        assert l7.adjusted_score == pytest.approx(l1.adjusted_score - 0.20)

    def test_volume_bonus(self):
        """Higher volume should increase score."""
        low = calculate_bms(0.2, 0.8, 0.8, volume_factor=1)
        high = calculate_bms(0.2, 0.8, 0.8, volume_factor=100)
        assert high.adjusted_score > low.adjusted_score

    def test_score_clamping(self):
        """Score must be clamped to 0.0-1.0."""
        # Extreme low: high failure cost, no reversibility, no clarity
        result = calculate_bms(1.0, 0.0, 0.0)
        assert result.adjusted_score == 0.0
        # Extreme high: low failure cost, full reversibility, full clarity
        result = calculate_bms(0.0, 1.0, 1.0)
        assert result.adjusted_score == 1.0

    def test_invalid_input(self):
        """Invalid inputs should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bms(1.5, 0.5, 0.5)
        with pytest.raises(ValueError):
            calculate_bms(0.5, -0.1, 0.5)

    def test_score_workflow_wrapper(self):
        """score_workflow should work with string level."""
        result = score_workflow(
            failure_cost=0.2,
            reversibility=0.8,
            mechanism_clarity=0.8,
            level="L3",
        )
        assert result.mode == BMSMode.A1

    def test_rationale_not_empty(self):
        """Every result should have a non-empty rationale."""
        result = calculate_bms(0.3, 0.6, 0.7)
        assert len(result.rationale) > 0
        assert "Raw=" in result.rationale
        assert "Final=" in result.rationale


# ─────────────────────────────────────────────
# Type System Tests
# ─────────────────────────────────────────────

class TestTypeSystem:
    def test_level_count(self):
        assert len(Level) == 7

    def test_diamond_count(self):
        assert len(Diamond) == 3

    def test_bms_mode_count(self):
        assert len(BMSMode) == 4

    def test_iqrsqpi_step_count(self):
        assert len(IQRSQPIStep) == 7

    def test_iqrsqpi_sequence(self):
        seq = IQRSQPIStep.sequence()
        assert len(seq) == 7
        assert seq[0] == IQRSQPIStep.I1
        assert seq[-1] == IQRSQPIStep.I2

    def test_bms_mode_from_score(self):
        assert BMSMode.from_score(0.9) == BMSMode.A1
        assert BMSMode.from_score(0.75) == BMSMode.A1
        assert BMSMode.from_score(0.5) == BMSMode.A2
        assert BMSMode.from_score(0.3) == BMSMode.A3
        assert BMSMode.from_score(0.1) == BMSMode.A4

    def test_a1_no_model(self):
        assert BMSMode.A1.model_in_decision_path is False

    def test_a2_a3_a4_have_model(self):
        assert BMSMode.A2.model_in_decision_path is True
        assert BMSMode.A3.model_in_decision_path is True
        assert BMSMode.A4.model_in_decision_path is True

    def test_lattice_coordinate_str(self):
        coord = LatticeCoordinate(
            level=Level.L2,
            diamond=Diamond.D1,
            bms_mode=BMSMode.A1,
            step=IQRSQPIStep.I1,
        )
        assert str(coord) == "L2-D1-A1-I1"
