"""FastAPI server for Strategy Studio — with RIG Lattice API routes."""

from __future__ import annotations

import argparse
from datetime import datetime

from pydantic import BaseModel, Field

from strategy_studio.core.types import (
    Evidence,
    Synthesis,
    Forecast,
    WargameScenario,
    FalsificationPacket,
    AuditRow,
    IntentKey,
)
from strategy_studio.engines.b29_synthesize import synthesize_evidence
from strategy_studio.engines.b36_wargame import run_wargame
from strategy_studio.engines.b34_predict import build_forecast
from strategy_studio.engines.b33_falsify import falsify_claim
from strategy_studio.lattice_wire import (
    LatticeOrchestrator,
    LatticeCell,
    Altitude,
    Diamond,
    IQRSQPIStep,
    BuildMode,
    compute_bms,
    get_build_card,
    get_all_build_cards,
    lattice_summary,
    generate_lattice_map,
)


class _FastAPIShim:
    def __init__(self, **kw): ...
    def post(self, *a, **kw):
        return lambda f: f
    def get(self, *a, **kw):
        return lambda f: f


try:  # pragma: no cover
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = _FastAPIShim  # type: ignore[misc,assignment]

app = FastAPI(title="Strategy Studio API", version="1.0.0")


# ═══════════════════════════════════════════════════════════════════════════
# B-ENGINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

class SynthesizeRequest(BaseModel):
    evidence: list[Evidence]


class WargameRequest(BaseModel):
    scenario: str
    actors: list[str]


class ForecastRequest(BaseModel):
    question: str
    historical_data: dict[str, float] = Field(default_factory=dict)


class FalsifyRequest(BaseModel):
    claim: str
    evidence: list[Evidence] = Field(default_factory=list)


@app.post("/synthesize", response_model=Synthesis)
def post_synthesize(request: SynthesizeRequest) -> Synthesis:
    return synthesize_evidence(request.evidence)


@app.post("/wargame", response_model=list[WargameScenario])
def post_wargame(request: WargameRequest) -> list[WargameScenario]:
    return run_wargame(request.scenario, request.actors)


@app.post("/forecast", response_model=Forecast)
def post_forecast(request: ForecastRequest) -> Forecast:
    return build_forecast(request.question, request.historical_data)


@app.post("/falsify", response_model=FalsificationPacket)
def post_falsify(request: FalsifyRequest) -> FalsificationPacket:
    return falsify_claim(request.claim, request.evidence)


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

class LatticeTraverseRequest(BaseModel):
    cell_id: str
    query: str = "Strategy analysis"


class LatticePipelineRequest(BaseModel):
    query: str = "Strategy analysis"
    altitude: int = 2
    diamond: str = "D1"


class BMSRequest(BaseModel):
    failure_cost: float = 0.5
    reversibility: float = 0.5
    mechanism_clarity: float = 0.5
    altitude: int = 2
    past_failure_rate: float = 0.0
    data_volume: float = 0.5


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "archetype": "A1_FROZEN", "lattice": "enabled"}


@app.get("/audit")
def get_audit() -> list[AuditRow]:
    return [
        AuditRow(
            id=f"audit-{i}",
            timestamp=datetime.utcnow(),
            intent=IntentKey.SYNTHESIZE,
            payload_summary=f"payload-{i}",
            result_summary="ok",
        )
        for i in range(5)
    ]


@app.get("/lattice/summary")
def get_lattice_summary() -> dict:
    """Return the full lattice summary: 147 cells, 588 with BMS, 28 archetypes."""
    return lattice_summary()


@app.post("/lattice/bms")
def post_lattice_bms(request: BMSRequest) -> dict:
    """Compute BMS score and select build mode."""
    alt = Altitude(request.altitude)
    bms = compute_bms(
        failure_cost=request.failure_cost,
        reversibility=request.reversibility,
        mechanism_clarity=request.mechanism_clarity,
        past_failure_rate=request.past_failure_rate,
        data_volume=request.data_volume,
        altitude=alt,
    )
    mode = bms.select_mode()
    return {
        "bms_score": round(bms.final, 4),
        "bms_mode": mode.value,
        "cost_band": mode.cost_band,
        "altitude": request.altitude,
        "components": {
            "raw": round(bms.raw, 4),
            "adj_failure": round(bms.adj_failure, 4),
            "adj_volume": round(bms.adj_volume, 4),
            "adj_altitude": round(bms.adj_altitude, 4),
        },
    }


@app.get("/lattice/cell/{cell_id}")
def get_lattice_cell(cell_id: str) -> dict:
    """Get BuildCard details for a lattice cell."""
    try:
        card = get_build_card(cell_id)
    except ValueError as e:
        return {"error": str(e)}
    return card.model_dump()


@app.get("/lattice/cards")
def get_lattice_cards() -> list[dict]:
    """Get all 147 Build Cards."""
    cards = get_all_build_cards()
    return [c.model_dump() for c in cards]


@app.post("/lattice/traverse")
def post_lattice_traverse(request: LatticeTraverseRequest) -> dict:
    """Execute a single lattice cell (B-engine execution)."""
    try:
        cell = LatticeCell.parse(request.cell_id)
    except ValueError as e:
        return {"error": str(e)}
    orch = LatticeOrchestrator()
    packet = orch.execute_cell(cell, {"query": request.query})
    return packet.model_dump()


@app.post("/lattice/pipeline")
def post_lattice_pipeline(request: LatticePipelineRequest) -> dict:
    """Run full 7-step IQRSQPI pipeline through the lattice."""
    try:
        alt = Altitude(request.altitude)
        dia = Diamond(request.diamond)
    except (ValueError, KeyError) as e:
        return {"error": str(e)}
    orch = LatticeOrchestrator()
    result = orch.execute_full_pipeline(
        input_data={"query": request.query},
        altitude=alt,
        diamond=dia,
    )
    return result


@app.get("/lattice/map")
def get_lattice_map() -> dict:
    """Generate Excalidraw lattice map."""
    return generate_lattice_map()


def main():
    """Run the Strategy Studio API server."""
    parser = argparse.ArgumentParser(description="Strategy Studio API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")
    args = parser.parse_args()

    import uvicorn
    print(f"Starting Strategy Studio API server on {args.host}:{args.port}")
    print(f"Lattice endpoints: http://{args.host}:{args.port}/lattice/")
    print(f"Health check: http://{args.host}:{args.port}/health")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
