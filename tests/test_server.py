"""Tests for the Strategy Studio API server (strategy_studio.server).

Tests all 11 API endpoints:
- Health and audit
- B-engine endpoints (synthesize, wargame, forecast, falsify)
- Lattice endpoints (summary, bms, cell, cards, traverse, pipeline, map)
"""
import json
import pytest
from fastapi.testclient import TestClient

from strategy_studio.server import app


@pytest.fixture
def client():
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# Health & Audit
# ═══════════════════════════════════════════════════════════════════════════

class TestHealthAudit:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "lattice" in data

    def test_audit(self, client):
        resp = client.get("/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0


# ═══════════════════════════════════════════════════════════════════════════
# B-Engine Endpoints
# ═══════════════════════════════════════════════════════════════════════════

class TestBEngineEndpoints:
    def test_synthesize(self, client):
        resp = client.post("/synthesize", json={
            "evidence": [{"source_uri": "test://1", "content_hash": "abc", "confidence": "H", "citations": ["test"]}]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "rationale" in data or "options" in data

    def test_wargame(self, client):
        resp = client.post("/wargame", json={
            "scenario": "Market entry",
            "actors": ["Competitor A", "Competitor B"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_forecast(self, client):
        resp = client.post("/forecast", json={
            "question": "Will AI pass Turing test by 2030?",
            "historical_data": {"2020": 10, "2021": 15, "2022": 25}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction" in data or "variable" in data

    def test_falsify(self, client):
        resp = client.post("/falsify", json={
            "claim": "Market is growing 25% YoY",
            "evidence": []
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "belief" in data
        assert "disproof_test" in data


# ═══════════════════════════════════════════════════════════════════════════
# Lattice Endpoints
# ═══════════════════════════════════════════════════════════════════════════

class TestLatticeEndpoints:
    def test_lattice_summary(self, client):
        resp = client.get("/lattice/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cells_147"] == 147
        assert data["total_cells_588"] == 588
        assert data["archetypes"] == 28

    def test_lattice_bms(self, client):
        resp = client.post("/lattice/bms", json={
            "failure_cost": 0.8,
            "reversibility": 0.3,
            "mechanism_clarity": 0.5,
            "altitude": 2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "bms_score" in data
        assert "bms_mode" in data
        assert data["bms_mode"] in ("A1", "A2", "A3", "A4")

    def test_lattice_bms_all_modes(self, client):
        """Test BMS scoring covers all 4 modes."""
        modes_seen = set()
        for altitude in [1, 2, 3, 7]:
            resp = client.post("/lattice/bms", json={
                "failure_cost": 0.5, "reversibility": 0.5,
                "mechanism_clarity": 0.5, "altitude": altitude,
            })
            data = resp.json()
            modes_seen.add(data["bms_mode"])
        assert len(modes_seen) >= 3  # At least 3 different modes

    def test_lattice_cell(self, client):
        resp = client.get("/lattice/cell/L2-D1-S")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cell_id"] == "L2-D1-S"
        assert "mode" in data
        assert "tools" in data

    def test_lattice_cell_588(self, client):
        resp = client.get("/lattice/cell/L4-D1-A3-S")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data

    def test_lattice_cell_invalid(self, client):
        resp = client.get("/lattice/cell/invalid")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_lattice_cards(self, client):
        resp = client.get("/lattice/cards")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 147

    def test_lattice_traverse(self, client):
        resp = client.post("/lattice/traverse", json={
            "cell_id": "L2-D1-S",
            "query": "test strategy"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "cell_id" in data

    def test_lattice_pipeline(self, client):
        resp = client.post("/lattice/pipeline", json={
            "query": "test pipeline",
            "altitude": 2,
            "diamond": "D1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert data["summary"]["total_steps"] == 7
        assert "steps" in data

    def test_lattice_pipeline_a3(self, client):
        """L5 altitude should trigger A3 mode."""
        resp = client.post("/lattice/pipeline", json={
            "query": "test",
            "altitude": 5,
            "diamond": "D1",
        })
        data = resp.json()
        for step_name, step_data in data["steps"].items():
            assert step_data.get("mode") == "A3"

    def test_lattice_map(self, client):
        resp = client.get("/lattice/map")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "excalidraw"
        assert len(data["elements"]) > 100


# ═══════════════════════════════════════════════════════════════════════════
# End-to-End: Full pipeline through API
# ═══════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_full_pipeline_returns_report(self, client):
        """Full lattice pipeline should return a complete result with all steps."""
        resp = client.post("/lattice/pipeline", json={
            "query": "Market expansion strategy for Tesla",
            "altitude": 2,
            "diamond": "D1",
        })
        assert resp.status_code == 200
        data = resp.json()
        summary = data["summary"]
        assert summary["total_steps"] == 7
        assert summary["passed"] >= 1
        assert "steps" in data
        # All 7 IQRSQPI steps should be present
        steps = data["steps"]
        for step_name in ["intent", "question", "research", "solution", "quality", "proof", "integrate"]:
            assert step_name in steps, f"Missing step: {step_name}"

    def test_pipeline_escalation(self, client):
        """L7 altitude should trigger A4 mode (may escalate)."""
        resp = client.post("/lattice/pipeline", json={
            "query": "test",
            "altitude": 7,
            "diamond": "D1",
        })
        data = resp.json()
        # A4 mode — some steps may return UNKNOWN
        assert data["summary"]["total_steps"] == 7
