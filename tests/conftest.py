"""pytest fixtures for the Strategy Studio test suite."""
from __future__ import annotations

import json
import pytest

from strategy_studio.core.types import (
    Evidence,
    Synthesis,
    InboundPayload,
    IntentKey,
    Option,
)


@pytest.fixture
def sample_payload() -> InboundPayload:
    return InboundPayload(
        raw_text="synthesize market options for Tesla in EV charging",
        source="cli",
        metadata={"client": "tesla", "domain": "ev"},
    )


@pytest.fixture
def sample_evidence() -> list[Evidence]:
    return [
        Evidence(
            source_uri="file://reports/q3_ev.pdf",
            content_hash="a1b2c3",
            confidence="H",
            citations=["McKinsey 2024", "IEA Global EV Outlook 2025"],
        ),
        Evidence(
            source_uri="https://recall.ai/card/12345",
            content_hash="d4e5f6",
            confidence="M",
            citations=["Bloomberg NEF"],
        ),
        Evidence(
            source_uri="https://lakeos.local/query?topic=competitor",
            content_hash="g7h8i9",
            confidence="L",
            citations=["SEC filing"],
        ),
    ]


@pytest.fixture
def sample_synthesis() -> Synthesis:
    return Synthesis(
        options=[
            Option(
                id="opt-1",
                title="Option A",
                description="Build proprietary charging network",
                score=0.92,
                risks=["Capital intensive", "Regulatory uncertainty"],
            ),
            Option(
                id="opt-2",
                title="Option B",
                description="Partner with existing network",
                score=0.78,
                risks=["Dependency on partner", "Revenue share dilution"],
            ),
            Option(
                id="opt-3",
                title="Option C",
                description="White-label technology to OEMs",
                score=0.65,
                risks=[" commoditization", "Low margin"],
            ),
        ],
        recommendation=None,
        rationale="EV charging market growing at 28% CAGR; proprietary network captures 40% more margin than partnership",
    )


@pytest.fixture
def mock_lakeos_response():
    return {
        "status": "ok",
        "data": {
            "records": [
                {"id": "r1", "category": "financial", "value": 1200000},
                {"id": "r2", "category": "operational", "value": 800000},
            ]
        },
    }
