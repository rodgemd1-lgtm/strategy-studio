"""Tests for Calibration Engine, Industry Playbooks, and Strategy Session."""
import pytest
import tempfile
from pathlib import Path
from strategy_studio.core.types import Option


# ── Calibration Engine ──────────────────────────────────────────────────────

class TestCalibrationEngine:
    def test_brier_score_perfect(self):
        from strategy_studio.studios.calibration_engine import brier_score
        predictions = [(1.0, 1.0), (0.0, 0.0), (1.0, 1.0)]
        score = brier_score(predictions)
        assert score == 0.0

    def test_brier_score_worst(self):
        from strategy_studio.studios.calibration_engine import brier_score
        predictions = [(1.0, 0.0), (0.0, 1.0)]
        score = brier_score(predictions)
        assert score == 1.0

    def test_brier_score_moderate(self):
        from strategy_studio.studios.calibration_engine import brier_score
        predictions = [(0.8, 1.0), (0.3, 0.0), (0.6, 1.0)]
        score = brier_score(predictions)
        assert 0.0 < score < 1.0

    def test_calibration_curve(self):
        from strategy_studio.studios.calibration_engine import calibration_curve
        predictions = [(0.1, 0.0), (0.3, 0.0), (0.5, 1.0), (0.7, 1.0), (0.9, 1.0)] * 10
        curve = calibration_curve(predictions, n_bins=5)
        assert len(curve) == 5

    def test_sharpness(self):
        from strategy_studio.studios.calibration_engine import sharpness
        confident = [0.95, 0.05, 0.99, 0.01]
        uncertain = [0.5, 0.5, 0.5, 0.5]
        assert sharpness(confident) > sharpness(uncertain)
        assert 0.0 <= sharpness(confident) <= 1.0

    def test_track_forecast(self):
        from strategy_studio.studios.calibration_engine import track_forecast
        result = track_forecast("test-1", {"growth": 0.15}, {"growth": 0.12})
        assert result["forecast_id"] == "test-1"
        assert "overall_brier" in result

    def test_calibration_report(self):
        from strategy_studio.studios.calibration_engine import calibration_report
        history = [
            {"predicted": {"growth": 0.15}, "actual": {"growth": 0.12}},
            {"predicted": {"growth": 0.20}, "actual": {"growth": 0.25}},
            {"predicted": {"growth": 0.10}, "actual": {"growth": 0.08}},
        ]
        report = calibration_report(history)
        assert "brier_score" in report
        assert "sample_size" in report

    def test_update_prior(self):
        from strategy_studio.studios.calibration_engine import update_prior
        posterior = update_prior(0.3, 2.0)
        assert 0.0 < posterior < 1.0
        # Prior should increase with LR > 1
        assert posterior > 0.3

    def test_brier_skill_score(self):
        from strategy_studio.studios.calibration_engine import brier_skill_score
        bss = brier_skill_score(0.15, 0.25)
        assert bss > 0  # Better than reference
        assert abs(bss - 0.4) < 0.01  # 1 - 0.15/0.25 = 0.4


# ── Industry Playbooks ──────────────────────────────────────────────────────

class TestIndustryPlaybooks:
    def test_get_playbook_saas(self):
        from strategy_studio.studios.industry_playbooks import get_playbook
        pb = get_playbook("saas")
        assert "key_metrics" in pb
        assert len(pb["key_metrics"]) >= 5

    def test_get_playbook_fintech(self):
        from strategy_studio.studios.industry_playbooks import get_playbook
        pb = get_playbook("fintech")
        assert "benchmarks" in pb

    def test_get_playbook_normalization(self):
        from strategy_studio.studios.industry_playbooks import get_playbook
        pb1 = get_playbook("SaaS")
        pb2 = get_playbook("software")
        assert pb1 == pb2

    def test_get_kpis(self):
        from strategy_studio.studios.industry_playbooks import get_kpis
        kpis = get_kpis("saas")
        assert len(kpis) >= 5
        assert all("name" in k for k in kpis)

    def test_get_benchmarks(self):
        from strategy_studio.studios.industry_playbooks import get_benchmarks
        bench = get_benchmarks("saas", "NRR")
        assert "p50" in bench
        assert bench["p50"] > 0

    def test_get_strategic_options(self):
        from strategy_studio.studios.industry_playbooks import get_strategic_options
        opts = get_strategic_options("saas", "growth")
        assert len(opts) >= 2
        assert all("name" in o for o in opts)

    def test_get_risk_factors(self):
        from strategy_studio.studios.industry_playbooks import get_risk_factors
        risks = get_risk_factors("fintech")
        assert len(risks) >= 2
        assert all("name" in r for r in risks)

    def test_compare_to_benchmark(self):
        from strategy_studio.studios.industry_playbooks import compare_to_benchmark
        results = compare_to_benchmark({"NRR": 115, "Gross Margin": 75}, "saas")
        assert len(results) == 2
        assert all("assessment" in r for r in results)


# ── Strategy Session ────────────────────────────────────────────────────────

class TestStrategySession:
    def test_session_creation(self):
        from strategy_studio.session import StrategySession
        session = StrategySession(company_name="TestCo", industry="SaaS")
        assert session.company_name == "TestCo"
        assert session.session_id is not None

    def test_session_run_minimal(self):
        from strategy_studio.session import run_strategy_session
        session = run_strategy_session(
            company_name="TestCo",
            industry="SaaS",
            export_formats=["md"],
        )
        assert session.report is not None
        assert "md" in session.exported_paths

    def test_session_run_full(self):
        from strategy_studio.session import run_strategy_session
        session = run_strategy_session(
            company_name="Tesla",
            industry="Electric Vehicles",
            competitors=["BYD", "Ford"],
            historical_data={"revenue_2023": 96800, "growth_2023": 19},
            evidence_sources=["EV market growing 25% YoY"],
            export_formats=["md", "json"],
        )
        summary = session.summary()
        # Lattice mode: 7 IQRSQPI steps (or 4 archetypes in fallback mode)
        assert summary["archetypes_run"] >= 4
        assert summary["report_generated"] is True
        # Lattice-specific checks
        assert session.bms_mode in ("A1", "A2", "A3", "A4")
        assert session.bms_score > 0
        assert len(session.lattice_packets) > 0

    def test_session_summary(self):
        from strategy_studio.session import run_strategy_session
        session = run_strategy_session(company_name="Acme")
        summary = session.summary()
        assert "session_id" in summary
        assert "archetype_statuses" in summary
        assert "exported_files" in summary