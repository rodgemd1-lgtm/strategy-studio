"""Tests for Prediction Studio."""
import pytest
from strategy_studio.studios.prediction_studio import (
    ForecastRecord,
    ForecastStore,
    SignalRegistry,
    Signal,
    MarketPrior,
    CausalThesisTree,
    MissingInfoTask,
    EvidenceUpdate,
    ForecastCategory,
    ForecastStatus,
)
from strategy_studio.studios.prediction_studio.scoring import (
    brier_score,
    log_score,
    interval_score,
    sharpness,
    calibration_buckets,
    expected_calibration_error,
    bayesian_update,
    brier_skill_score,
)
from strategy_studio.studios.prediction_studio.ensemble import (
    simple_ensemble,
    weighted_ensemble,
    extremized_ensemble,
    compute_ensemble,
    compute_uncertainty_interval,
)
from strategy_studio.studios.prediction_studio.missing_info import (
    identify_missing_information,
    compute_information_gap_score,
)
from strategy_studio.studios.prediction_studio.priors import (
    validate_market_match,
)


class TestBrierScore:
    def test_perfect_predictions(self):
        preds = [(1.0, 1.0), (0.0, 0.0), (1.0, 1.0)]
        assert brier_score(preds) == 0.0

    def test_worst_predictions(self):
        preds = [(1.0, 0.0), (0.0, 1.0)]
        assert brier_score(preds) == 1.0

    def test_moderate(self):
        preds = [(0.8, 1.0), (0.3, 0.0), (0.9, 1.0), (0.2, 0.0)]
        score = brier_score(preds)
        assert 0.0 < score < 0.1

    def test_empty(self):
        assert brier_score([]) == 0.0


class TestLogScore:
    def test_perfect(self):
        preds = [(0.99, 1.0), (0.01, 0.0)]
        score = log_score(preds)
        assert score > -0.1

    def test_overconfident_wrong(self):
        preds = [(0.99, 0.0)]
        score = log_score(preds)
        # Log score is negative (higher is better). Overconfident wrong = large positive (bad)
        assert score > 2.0


class TestBayesianUpdate:
    def test_lr_greater_than_1(self):
        posterior = bayesian_update(0.3, 2.0)
        assert posterior > 0.3

    def test_lr_less_than_1(self):
        posterior = bayesian_update(0.3, 0.5)
        assert posterior < 0.3

    def test_lr_1_no_change(self):
        posterior = bayesian_update(0.3, 1.0)
        assert abs(posterior - 0.3) < 0.001

    def test_edge_prior_0(self):
        assert bayesian_update(0.0, 2.0) == 0.0

    def test_edge_prior_1(self):
        assert bayesian_update(1.0, 2.0) == 1.0


class TestCalibration:
    def test_perfectly_calibrated(self):
        preds = [(0.5, 1.0), (0.5, 0.0), (0.5, 1.0), (0.5, 0.0)]
        buckets = calibration_buckets(preds)
        assert len(buckets) > 0

    def test_ece_perfect(self):
        # Perfect calibration: 50% predictions resolve 50%
        preds = [(0.5, 1.0), (0.5, 0.0)] * 10
        ece = expected_calibration_error(preds)
        assert ece < 0.01

    def test_sharpness_confident(self):
        s = sharpness([0.95, 0.05, 0.99, 0.01])
        assert s > 0.8

    def test_sharpness_uncertain(self):
        s = sharpness([0.5, 0.5, 0.5, 0.5])
        assert s == 0.0


class TestEnsemble:
    def test_simple(self):
        assert simple_ensemble([0.6, 0.8]) == 0.7

    def test_weighted(self):
        result = weighted_ensemble([(0.6, 2.0), (0.8, 1.0)])
        assert abs(result - 0.6667) < 0.01

    def test_empty(self):
        assert simple_ensemble([]) == 0.5

    def test_extremized(self):
        result = extremized_ensemble([0.6, 0.7, 0.65], alpha=0.3)
        assert result > 0.65  # Should push away from 0.5


class TestForecastRecord:
    def test_create(self):
        f = ForecastRecord(question="Will X happen by 2026?")
        assert f.forecast_id is not None
        assert f.status == ForecastStatus.DRAFT
        assert f.final_probability is None

    def test_with_category(self):
        f = ForecastRecord(question="Test", category=ForecastCategory.TECH)
        assert f.category == ForecastCategory.TECH


class TestForecastStore:
    def test_add_and_get(self):
        store = ForecastStore()
        f = ForecastRecord(question="Test")
        store.add_forecast(f)
        assert store.get_forecast(f.forecast_id) is not None

    def test_get_active(self):
        store = ForecastStore()
        f = ForecastRecord(question="Test")
        f.status = ForecastStatus.ACTIVE
        store.add_forecast(f)
        assert len(store.get_active()) == 1

    def test_brier_score_empty(self):
        store = ForecastStore()
        assert store.get_brier_score() is None

    def test_brier_score_with_data(self):
        store = ForecastStore()
        f = ForecastRecord(question="Test", final_probability=0.8)
        f.status = ForecastStatus.RESOLVED
        f.outcome = True
        store.add_forecast(f)
        score = store.get_brier_score()
        assert score is not None
        assert abs(score - 0.04) < 0.01  # (0.8 - 1.0)^2 = 0.04


class TestMissingInfo:
    def test_identify_tasks(self):
        f = ForecastRecord(question="Will AI pass Turing test by 2030?")
        tasks = identify_missing_information(f)
        assert len(tasks) > 0
        # Should include base rate task
        assert any("Base rate" in t.information_needed for t in tasks)

    def test_gap_score(self):
        score = compute_information_gap_score(0.8, 0.7, 0.4, 0.9, 1.5)
        assert score > 0

    def test_gap_score_zero_cost(self):
        score = compute_information_gap_score(0.8, 0.7, 0.4, 0.9, 0.0)
        assert score > 0


class TestMarketPrior:
    def test_validate_exact_match(self):
        q = "Will AI pass Turing test by 2030?"
        m = "Will AI pass Turing test by 2030?"
        assert validate_market_match(q, m).value == "exact"

    def test_validate_invalid(self):
        q = "Will AI pass Turing test?"
        m = "Will it rain tomorrow?"
        assert validate_market_match(q, m).value == "invalid"


class TestBrierSkillScore:
    def test_better_than_reference(self):
        bss = brier_skill_score(0.15, 0.25)
        assert bss > 0

    def test_worse_than_reference(self):
        bss = brier_skill_score(0.30, 0.20)
        assert bss < 0

    def test_perfect(self):
        bss = brier_skill_score(0.0, 0.25)
        assert bss == 1.0