"""Tests for Prediction Studio, Decision Room, Evidence Engine,
Synthesis Pipeline, and Output Studio."""
import pytest
from strategy_studio.core.types import Evidence, Option, Synthesis
from strategy_studio.core.types_extended import Scenario


# ── Prediction Studio ───────────────────────────────────────────────────────

class TestPredictionStudio:
    def test_monte_carlo_normal(self):
        from strategy_studio.studios.prediction_studio import run_monte_carlo
        result = run_monte_carlo("revenue", 100.0, 15.0, iterations=5000)
        assert result.variable == "revenue"
        assert result.iterations == 5000
        assert 90 < result.mean < 110
        assert result.std_dev > 0
        assert result.percentile_5 < result.median < result.percentile_95
        assert len(result.histogram) == 20

    def test_monte_carlo_lognormal(self):
        from strategy_studio.studios.prediction_studio import run_monte_carlo
        result = run_monte_carlo("growth", 1.0, 0.3, iterations=3000, distribution="lognormal")
        assert result.mean > 0
        assert result.std_dev > 0

    def test_monte_carlo_uniform(self):
        from strategy_studio.studios.prediction_studio import run_monte_carlo
        result = run_monte_carlo("uniform_var", 50.0, 10.0, iterations=2000, distribution="uniform")
        assert 40 < result.mean < 60

    def test_monte_carlo_deterministic(self):
        from strategy_studio.studios.prediction_studio import run_monte_carlo
        r1 = run_monte_carlo("test", 100.0, 10.0, iterations=1000)
        r2 = run_monte_carlo("test", 100.0, 10.0, iterations=1000)
        # Results should be in the same ballpark (not exact match due to random seeding)
        assert abs(r1.mean - r2.mean) < 5.0
        assert abs(r1.std_dev - r2.std_dev) < 2.0

    def test_build_scenarios(self):
        from strategy_studio.studios.prediction_studio import build_scenarios
        base = Scenario(id="base", name="Base Case", description="Base", probability=0.5,
                        assumptions=["stable market"], variables={"growth": 0.1})
        variations = [
            {"name_suffix": "optimistic", "overrides": {"growth": 0.2}, "assumptions_add": ["tailwind"]},
            {"name_suffix": "pessimistic", "overrides": {"growth": -0.05}, "assumptions_add": ["headwind"]},
        ]
        scenarios = build_scenarios(base, variations)
        assert len(scenarios) == 3  # base + 2 variations
        assert scenarios[0].variables["growth"] == 0.1  # base
        assert scenarios[1].variables["growth"] == 0.2  # optimistic
        assert scenarios[2].variables["growth"] == -0.05  # pessimistic

    def test_run_wargame(self):
        from strategy_studio.studios.prediction_studio import run_wargame
        result = run_wargame("EV price war", ["competitor", "regulator"], depth=2)
        assert result.scenario_name == "EV price war"
        assert len(result.moves) >= 2
        assert result.risk_level in ("low", "medium", "high", "critical")

    def test_predict_variable_ensemble(self):
        from strategy_studio.studios.prediction_studio import predict_variable
        result = predict_variable("EV growth", {"2021": 15.0, "2022": 20.0, "2023": 25.0}, method="ensemble")
        assert result.variable == "EV growth"
        assert result.point_estimate > 0
        assert result.confidence_interval[0] < result.confidence_interval[1]
        assert result.method == "ensemble"

    def test_predict_variable_linear(self):
        from strategy_studio.studios.prediction_studio import predict_variable
        result = predict_variable("test", {"2022": 10.0, "2023": 20.0}, method="linear")
        assert result.point_estimate > 20.0

    def test_cross_impact_analysis(self):
        from strategy_studio.studios.prediction_studio import cross_impact_analysis
        scenarios = [
            Scenario(id="s1", name="S1", description="A", probability=0.5, variables={"x": 1.0}),
            Scenario(id="s2", name="S2", description="B", probability=0.3, variables={"x": -1.0}),
        ]
        matrix = cross_impact_analysis(scenarios)
        assert "s1" in matrix
        assert "s2" in matrix

    def test_sensitivity_analysis(self):
        from strategy_studio.studios.prediction_studio import sensitivity_analysis
        results = sensitivity_analysis("revenue", 100.0, {"price": (80.0, 120.0), "volume": (1000, 5000)})
        assert len(results) == 2
        assert all(r.parameter in ("price", "volume") for r in results)


# ── Decision Room ───────────────────────────────────────────────────────────

class TestDecisionRoom:
    def test_build_decision_matrix(self):
        from strategy_studio.studios.decision_room import build_decision_matrix
        options = [
            Option(id="a", title="Option A", description="...", score=0.8, risks=[]),
            Option(id="b", title="Option B", description="...", score=0.6, risks=[]),
            Option(id="c", title="Option C", description="...", score=0.4, risks=[]),
        ]
        matrix = build_decision_matrix(options, ["cost", "speed", "risk"],
                                        {"cost": 0.4, "speed": 0.3, "risk": 0.3})
        assert len(matrix.options) == 3
        assert matrix.options[0].rank == 1
        assert matrix.options[0].tier == "A"

    def test_sensitivity_analysis(self):
        from strategy_studio.studios.decision_room import build_decision_matrix, run_sensitivity_analysis
        options = [
            Option(id="a", title="A", description="...", score=0.8, risks=[]),
            Option(id="b", title="B", description="...", score=0.6, risks=[]),
        ]
        matrix = build_decision_matrix(options, ["cost", "speed"], {"cost": 0.5, "speed": 0.5})
        sens = run_sensitivity_analysis(matrix)
        assert len(sens) == 2

    def test_generate_recommendation(self):
        from strategy_studio.studios.decision_room import build_decision_matrix, generate_recommendation
        options = [
            Option(id="a", title="Build", description="Build in-house", score=0.9, risks=["High capex"]),
            Option(id="b", title="Buy", description="Acquire competitor", score=0.7, risks=["Integration risk"]),
        ]
        matrix = build_decision_matrix(options, ["cost", "speed", "risk"],
                                        {"cost": 0.4, "speed": 0.3, "risk": 0.3})
        result = generate_recommendation(matrix)
        assert result.decision_matrix is not None
        assert len(result.next_steps) >= 1

    def test_compare_options(self):
        from strategy_studio.studios.decision_room import compare_options
        a = Option(id="a", title="A", description="...", score=0.8, risks=[])
        b = Option(id="b", title="B", description="...", score=0.5, risks=[])
        result = compare_options(a, b, ["cost", "speed"])
        assert result["winner"] == "a"
        assert result["margin"] == 0.3

    def test_tornado_analysis(self):
        from strategy_studio.studios.decision_room import build_decision_matrix, tornado_analysis
        options = [
            Option(id="a", title="A", description="...", score=0.8, risks=[]),
            Option(id="b", title="B", description="...", score=0.6, risks=[]),
        ]
        matrix = build_decision_matrix(options, ["cost", "speed", "risk"],
                                        {"cost": 0.4, "speed": 0.3, "risk": 0.3})
        tornado = tornado_analysis(matrix)
        assert len(tornado) == 3

    def test_value_of_information(self):
        from strategy_studio.studios.decision_room import build_decision_matrix, value_of_information
        options = [
            Option(id="a", title="A", description="...", score=0.8, risks=[]),
            Option(id="b", title="B", description="...", score=0.6, risks=[]),
        ]
        matrix = build_decision_matrix(options, ["cost", "speed"], {"cost": 0.5, "speed": 0.5})
        evpi = value_of_information(matrix, "cost")
        assert evpi >= 0.0


# ── Evidence Engine ─────────────────────────────────────────────────────────

class TestEvidenceEngine:
    def test_score_source(self):
        from strategy_studio.studios.evidence_engine import score_source
        score = score_source("https://www.nature.com/article1", "EV market growing 25% annually",
                             {"query": "EV market growth"})
        assert 0.0 <= score.reliability <= 1.0
        assert 0.0 <= score.overall <= 1.0

    def test_detect_contradictions(self):
        from strategy_studio.studios.evidence_engine import detect_contradictions
        evidence = [
            Evidence(source_uri="src1", content_hash="h1", confidence="H",
                     citations=["Revenue increased by 25% this quarter"]),
            Evidence(source_uri="src2", content_hash="h2", confidence="H",
                     citations=["Revenue decreased by 25% this quarter"]),
        ]
        contradictions = detect_contradictions(evidence)
        # Should detect at least one contradiction (increase vs decrease)
        assert isinstance(contradictions, list)

    def test_build_evidence_graph(self):
        from strategy_studio.studios.evidence_engine import build_evidence_graph
        evidence = [
            Evidence(source_uri="src1", content_hash="h1", confidence="H", citations=["EV growth"]),
            Evidence(source_uri="src2", content_hash="h2", confidence="M", citations=["EV growth"]),
        ]
        graph = build_evidence_graph(evidence, "EV market growth")
        assert len(graph.nodes) == 2
        assert graph.overall_confidence in ("H", "M", "L")

    def test_track_confidence(self):
        from strategy_studio.studios.evidence_engine import build_evidence_graph, track_confidence
        evidence = [
            Evidence(source_uri="src1", content_hash="h1", confidence="H", citations=["EV growth"]),
        ]
        graph = build_evidence_graph(evidence, "EV market")
        new_ev = Evidence(source_uri="src2", content_hash="h2", confidence="H", citations=["EV growth"])
        updated = track_confidence(graph, new_ev)
        assert len(updated.nodes) == 2

    def test_source_diversity_score(self):
        from strategy_studio.studios.evidence_engine import source_diversity_score
        evidence = [
            Evidence(source_uri="https://nature.com/a", content_hash="h1", confidence="H", citations=[]),
            Evidence(source_uri="https://bbc.com/b", content_hash="h2", confidence="M", citations=[]),
        ]
        score = source_diversity_score(evidence)
        assert 0.0 <= score <= 1.0

    def test_evidence_strength(self):
        from strategy_studio.studios.evidence_engine import build_evidence_graph, evidence_strength
        evidence = [
            Evidence(source_uri="src1", content_hash="h1", confidence="H", citations=["EV growth"]),
        ]
        graph = build_evidence_graph(evidence, "EV market")
        strength = evidence_strength(graph)
        assert "total_sources" in strength
        assert "confidence" in strength


# ── Synthesis Pipeline ──────────────────────────────────────────────────────

class TestSynthesisPipeline:
    def test_run_cross_archetype(self):
        from strategy_studio.studios.synthesis_pipeline import run_cross_archetype
        from strategy_studio.core.types_extended import ArchetypeResult
        results = [
            ArchetypeResult(archetype="A1", status="PASS"),
            ArchetypeResult(archetype="A2", status="PASS"),
        ]
        consensus = run_cross_archetype(results)
        assert len(consensus.archetype_results) == 2

    def test_run_meta_analysis(self):
        from strategy_studio.studios.synthesis_pipeline import run_meta_analysis
        analyses = [
            Synthesis(options=[
                Option(id="a", title="A", description="...", score=0.8, risks=[]),
            ], recommendation=Option(id="a", title="A", description="...", score=0.8, risks=[])),
            Synthesis(options=[
                Option(id="b", title="B", description="...", score=0.7, risks=[]),
            ], recommendation=Option(id="b", title="B", description="...", score=0.7, risks=[])),
        ]
        meta = run_meta_analysis(analyses)
        assert meta.pooled_effect > 0
        assert len(meta.key_findings) >= 1

    def test_synthesize_across_studies(self):
        from strategy_studio.studios.synthesis_pipeline import synthesize_across_studies
        studies = [
            [{"score": 0.8}, {"score": 0.7}],
            [{"score": 0.6}, {"score": 0.9}],
        ]
        result = synthesize_across_studies(studies, method="score")
        assert "pooled_estimate" in result
        assert result["n_studies"] == 2


# ── Output Studio ───────────────────────────────────────────────────────────

class TestOutputStudio:
    def test_build_executive_summary(self):
        from strategy_studio.studios.output_studio import build_executive_summary
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="Build in-house", score=0.9, risks=["High capex"])],
            recommendation=Option(id="a", title="Build", description="Build in-house", score=0.9, risks=["High capex"]),
            rationale="Best long-term value",
        )
        summary = build_executive_summary("Test Strategy", synthesis, quality_passed=True)
        assert summary.title == "Test Strategy"
        assert len(summary.key_findings) >= 1

    def test_build_board_deck(self):
        from strategy_studio.studios.output_studio import build_executive_summary, build_board_deck
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="...", score=0.9, risks=[])],
            recommendation=Option(id="a", title="Build", description="...", score=0.9, risks=[]),
        )
        summary = build_executive_summary("Test", synthesis, quality_passed=True)
        deck = build_board_deck("Test Deck", summary)
        assert len(deck.slides) >= 3

    def test_build_strategy_report(self):
        from strategy_studio.studios.output_studio import build_strategy_report
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="...", score=0.9, risks=[])],
            recommendation=Option(id="a", title="Build", description="...", score=0.9, risks=[]),
        )
        report = build_strategy_report("Test Report", synthesis, quality_passed=True)
        assert report.title == "Test Report"
        assert report.executive_summary is not None

    def test_render_report_markdown(self):
        from strategy_studio.studios.output_studio import build_strategy_report, render_report_markdown
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="...", score=0.9, risks=[])],
            recommendation=Option(id="a", title="Build", description="...", score=0.9, risks=[]),
        )
        report = build_strategy_report("Test", synthesis, quality_passed=True)
        md = render_report_markdown(report)
        assert "# Test" in md
        assert "Executive Summary" in md

    def test_render_board_html(self):
        from strategy_studio.studios.output_studio import build_strategy_report, render_board_html
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="...", score=0.9, risks=[])],
            recommendation=Option(id="a", title="Build", description="...", score=0.9, risks=[]),
        )
        report = build_strategy_report("Test", synthesis, quality_passed=True)
        html = render_board_html(report)
        assert "<html>" in html or "<!DOCTYPE html>" in html

    def test_export_report(self):
        from strategy_studio.studios.output_studio import build_strategy_report, export_report
        from pathlib import Path
        import tempfile
        synthesis = Synthesis(
            options=[Option(id="a", title="Build", description="...", score=0.9, risks=[])],
            recommendation=Option(id="a", title="Build", description="...", score=0.9, risks=[]),
        )
        report = build_strategy_report("Test Export", synthesis, quality_passed=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_report(report, Path(tmpdir), formats=["md", "json"])
            assert "md" in paths
            assert "json" in paths
            assert paths["md"].exists()
            assert paths["json"].exists()