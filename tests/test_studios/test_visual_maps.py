"""Tests for Visual Strategy Maps."""
import json
import pytest
from pathlib import Path
from strategy_studio.core.types import Option, Synthesis
from strategy_studio.core.types_extended import Scenario, EvidenceGraph, SourceScore


class TestVisualStrategyMaps:
    def test_generate_strategy_map(self):
        from strategy_studio.studios.visual_strategy_maps import generate_strategy_map
        opts = [Option(id="a", title="Build", description="...", score=0.8, risks=["High capex"]),
                Option(id="b", title="Buy", description="...", score=0.6, risks=["Integration risk"])]
        syn = Synthesis(options=opts, recommendation=opts[0], rationale="Best value")
        diagram = generate_strategy_map("TestCo", syn)
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 5

    def test_generate_strategy_map_to_file(self):
        from strategy_studio.studios.visual_strategy_maps import generate_strategy_map
        import tempfile
        opts = [Option(id="a", title="Build", description="...", score=0.8, risks=[])]
        syn = Synthesis(options=opts, recommendation=opts[0], rationale="Test")
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "test.excalidraw"
            diagram = generate_strategy_map("TestCo", syn, output_path=p)
            assert p.exists()
            data = json.loads(p.read_text())
            assert data["type"] == "excalidraw"

    def test_generate_decision_tree(self):
        from strategy_studio.studios.visual_strategy_maps import generate_decision_tree
        opts = [Option(id="a", title="Build", description="...", score=0.8, risks=["Risk A"]),
                Option(id="b", title="Buy", description="...", score=0.6, risks=["Risk B"])]
        diagram = generate_decision_tree(opts)
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 3

    def test_generate_competitive_map(self):
        from strategy_studio.studios.visual_strategy_maps import generate_competitive_map
        diagram = generate_competitive_map("TestCo", ["CompA", "CompB", "CompC"])
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 5

    def test_generate_scenario_comparison(self):
        from strategy_studio.studios.visual_strategy_maps import generate_scenario_comparison
        scenarios = [
            Scenario(id="s1", name="Base", description="...", probability=0.5),
            Scenario(id="s2", name="Bull", description="...", probability=0.3),
            Scenario(id="s3", name="Bear", description="...", probability=0.2),
        ]
        diagram = generate_scenario_comparison(scenarios)
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 3

    def test_generate_evidence_graph_diagram(self):
        from strategy_studio.studios.visual_strategy_maps import generate_evidence_graph_diagram
        graph = EvidenceGraph(
            nodes=[
                SourceScore(source_uri="https://nature.com/a", reliability=0.9, relevance=0.8, overall=0.85),
                SourceScore(source_uri="https://bbc.com/b", reliability=0.7, relevance=0.6, overall=0.65),
            ],
            overall_confidence="H",
        )
        diagram = generate_evidence_graph_diagram(graph)
        assert diagram["type"] == "excalidraw"
        assert len(diagram["elements"]) > 3

    def test_generate_full_strategy_visuals(self):
        from strategy_studio.studios.visual_strategy_maps import generate_full_strategy_visuals
        from strategy_studio.core.types_extended import StrategyReport, ExecutiveSummary
        import tempfile
        report = StrategyReport(
            title="Test Report",
            executive_summary=ExecutiveSummary(
                title="Test", key_findings=["Finding 1"], recommendation="Do X",
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_full_strategy_visuals(report, Path(tmpdir))
            # Should at least generate a strategy map
            assert isinstance(paths, dict)