"""B36 — Wargame engine."""
from __future__ import annotations

from strategy_studio.core.types import WargameScenario

_WARGAME_RESPONSES = {
    "default": {
        "move": "Increase market pressure through pricing or feature acceleration.",
        "response": "RIG stabilizes core offering and monitors early warning signals.",
        "impact": "Moderate revenue compression; talent retention risk.",
    },
    "competitor": {
        "move": "Launch aggressive feature set or bundled pricing.",
        "response": "RIG differentiates on data moat and integration depth.",
        "impact": "Market share erosion unless switching costs prove sticky.",
    },
    "regulator": {
        "move": "Initiate compliance review or enforcement probe.",
        "response": "RIG pre-buffers with policy drafts and external counsel.",
        "impact": "Operating cost increase; launch delay risk.",
    },
    "customer": {
        "move": "Demand portability, audit rights, or steep discount.",
        "response": "RIG offers transparent SLA and staged rollout.",
        "impact": "Margin compression offset by trust premium.",
    },
    "investor": {
        "move": "Push for faster growth or cost reduction.",
        "response": "RIG presents disciplined roadmap with milestone gates.",
        "impact": "Valuation tension; potential cap-table conflict.",
    },
}


def _lookup_response(actor: str) -> dict[str, str]:
    lower = actor.lower()
    for key in ("competitor", "regulator", "customer", "investor"):
        if key in lower:
            return _WARGAME_RESPONSES[key]
    return _WARGAME_RESPONSES["default"]


def run_wargame(scenario: str, actors: list[str]) -> list[WargameScenario]:
    """Generate WargameScenario for each actor."""
    scenarios: list[WargameScenario] = []
    for actor in actors:
        tmpl = _lookup_response(actor)
        prob = min(1.0, 0.4 + 0.12 * len(actors))
        scenarios.append(
            WargameScenario(
                actor=actor,
                move=tmpl["move"],
                rig_response=tmpl["response"],
                impact=tmpl["impact"],
                probability=round(prob, 4),
            )
        )
    return scenarios
