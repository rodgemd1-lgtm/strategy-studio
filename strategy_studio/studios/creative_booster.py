"""Creative Booster bridge — Strategy Studio V10's idea-evaluation gate.

Strategy Studio uses the **RIG Creative Booster** to score strategy ideas,
offers, and roadmap candidates across novelty / appropriateness / usefulness /
surprise / proof-density / generic-penalty, then accept / revise / reject them
with a ProofPacket.

The booster is an **optional external dependency** (private package
``rig-creative-booster``). This bridge imports it if installed and **degrades
gracefully** otherwise — callers always get a :class:`BoosterEvaluation`, never
an ``ImportError``. Nothing proprietary lives in this file; it only calls the
booster's public API.

Enable scoring by installing the booster into the Studio environment::

    pip install -e /path/to/rig-creative-booster
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from strategy_studio.core.types import Option

try:  # optional dependency — booster may not be installed
    from rig_creative_booster.formulas.master import score_idea
    from rig_creative_booster.gates.engine import final_verdict, run_gates
    from rig_creative_booster.innovation.roadmap import build_roadmap
    from rig_creative_booster.innovation.vectors import (
        headline,
        innovation_index,
        score_innovation_vectors,
    )
    from rig_creative_booster.lattice import lattice_coord
    from rig_creative_booster.models import Audience, CreativeIdeaPacket, LatticeMode
    from rig_creative_booster.proof.proofpacket import build_proof_packet
    from rig_creative_booster.questions.injection_stack import (
        adversarial_survival_rate,
    )

    _BOOSTER_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when package absent
    _BOOSTER_AVAILABLE = False


def booster_available() -> bool:
    """True if rig-creative-booster is importable in this environment."""
    return _BOOSTER_AVAILABLE


@dataclass(frozen=True)
class BoosterEvaluation:
    """Studio-facing result of a Creative Booster evaluation.

    Always returned (even when the booster is absent) so Studio flows never
    crash on a missing optional dependency.
    """

    available: bool
    verdict: str  # "accept" | "revise" | "reject" | "unavailable"
    creativity_score: float
    deviation_score: float
    adversarial_survival_rate: float
    innovation_index: float
    innovation_headline: str
    failed_gates: list[str] = field(default_factory=list)
    next_tests: list[str] = field(default_factory=list)
    proof_packet: dict | None = None

    def to_option(self, title: str, description: str) -> Option:
        """Map the evaluation into a Strategy Studio :class:`Option`."""
        risks = [f"gate:{g}" for g in self.failed_gates] + list(self.next_tests)
        return Option(
            id=_idea_id(title),
            title=title,
            description=description,
            score=max(0.0, min(1.0, self.creativity_score)),
            risks=risks,
        )


def _idea_id(title: str) -> str:
    """Deterministic id from the title (stable across runs)."""
    return "ss-" + hashlib.md5(title.encode("utf-8")).hexdigest()[:10]


def evaluate_idea(
    title: str,
    content: str,
    context: str = "",
    *,
    sources: list[str] | None = None,
    claims: list[str] | None = None,
    mechanisms: list[str] | None = None,
    corpus: list[str] | None = None,
    audience: str = "internal",
) -> BoosterEvaluation:
    """Score a strategy idea through the Creative Booster.

    Returns a :class:`BoosterEvaluation`. If the booster is not installed,
    ``available`` is False and ``verdict`` is ``"unavailable"`` (no exception).
    Deterministic for a given set of inputs.
    """
    if not _BOOSTER_AVAILABLE:
        return BoosterEvaluation(
            available=False,
            verdict="unavailable",
            creativity_score=0.0,
            deviation_score=0.0,
            adversarial_survival_rate=0.0,
            innovation_index=0.0,
            innovation_headline="rig-creative-booster not installed",
        )

    idea = CreativeIdeaPacket(
        idea_id=_idea_id(title),
        title=title,
        content=content,
        context=context,
        sources=sources or [],
        claims=claims or [],
        mechanisms=mechanisms or [],
    )
    aud = Audience(audience)
    sv = score_idea(idea, corpus or [])
    gates = run_gates(sv, aud)
    verdict = final_verdict(gates)
    asr, _ = adversarial_survival_rate(idea, sv)
    vectors = score_innovation_vectors(idea, sv)
    coord = lattice_coord(level=1, diamond=1, mode=LatticeMode.A1, step="Quality")
    packet = build_proof_packet(
        idea, sv, gates, vectors, asr, audience=aud, lattice_coord=coord
    )

    return BoosterEvaluation(
        available=True,
        verdict=verdict.value,
        creativity_score=sv.creativity_score,
        deviation_score=sv.deviation_score,
        adversarial_survival_rate=asr,
        innovation_index=innovation_index(vectors),
        innovation_headline=headline(vectors),
        failed_gates=[g.gate for g in gates if not g.passed],
        next_tests=list(packet.next_tests),
        proof_packet=packet.model_dump(mode="json"),
    )


def build_strategy_roadmap(
    title: str,
    content: str,
    context: str = "",
    *,
    sources: list[str] | None = None,
    claims: list[str] | None = None,
    mechanisms: list[str] | None = None,
    corpus: list[str] | None = None,
    top: int | None = None,
) -> dict | None:
    """Future-back capability roadmap for a strategy (SS2).

    Scores the idea, derives the 10 innovation vectors, and returns a roadmap
    ranked by leverage × feasibility ÷ time-to-value, bucketed into horizons.
    Returns None if the booster is not installed (graceful).
    """
    if not _BOOSTER_AVAILABLE:
        return None
    idea = CreativeIdeaPacket(
        idea_id=_idea_id(title), title=title, content=content, context=context,
        sources=sources or [], claims=claims or [], mechanisms=mechanisms or [],
    )
    sv = score_idea(idea, corpus or [])
    vectors = score_innovation_vectors(idea, sv)
    roadmap = build_roadmap(idea.idea_id, title, sv, vectors, top=top)
    return roadmap.model_dump(mode="json")
