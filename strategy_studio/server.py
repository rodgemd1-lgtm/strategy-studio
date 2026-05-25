"""FastAPI server for Strategy Studio."""
from __future__ import annotations

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


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "archetype": "A1_FROZEN"}


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


@app.post("/falsify", response_model=FalsificationPacket)
def post_falsify(request: FalsifyRequest) -> FalsificationPacket:
    return falsify_claim(request.claim, request.evidence)
