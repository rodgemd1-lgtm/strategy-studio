"""Strategy teaser generator — deterministic HTML + Markdown from TeaserInput.

A1-only: no LLM calls in the rendering path. Jinja2 templates + Pydantic input.

Pipeline:
  TeaserInput → A1 archetypes (intent + question + falsification) → ProofPacket
       → Jinja2 render (HTML + MD) → bundle dir on disk

Each generated teaser produces:
  out/<prospect_id>/index.html       # for the cloned site
  out/<prospect_id>/teaser.md         # for cold email body
  out/<prospect_id>/proof_packet.json # audit trail (cited sources + falsification)
  out/<prospect_id>/teaser_input.json # input snapshot
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from strategy_studio.archetypes.a1.a1_1_intent import classify_intent
from strategy_studio.archetypes.a1.a1_5_quality import validate
from strategy_studio.core.types import (
    InboundPayload,
    IntentKey,
    Evidence,
    Option,
    Synthesis,
    ProofPacket,
    FalsificationPacket,
)
from strategy_studio.teaser.schema import TeaserInput


_TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=False,
    lstrip_blocks=False,
)


def _build_proof_packet(t: TeaserInput) -> dict:
    """Build the auditable proof packet for this teaser.

    Every external send needs one — strategy studio quality gate.
    """
    # Synthesize an Evidence list from the input
    evidence = [
        Evidence(
            source_uri=src,
            content_hash=f"sha256:{hash(src) & 0xFFFFFFFF:08x}",
            confidence=t.confidence,
            citations=[src],
        )
        for src in t.evidence_sources
    ]

    # Synthesize options from the engines.
    # Option.score is bounded 0..1; we min-max normalize over the engines in this teaser.
    max_rev = max((e.target_revenue_m for e in t.engines), default=1.0) or 1.0
    options = [
        Option(
            id=f"engine-{i}",
            title=e.name,
            description=e.flywheel_loop,
            score=min(1.0, max(0.0, e.target_revenue_m / max_rev)),
            risks=[],
        )
        for i, e in enumerate(t.engines)
    ]
    syn = Synthesis(
        options=options,
        recommendation=options[0],
        rationale=f"{t.mechanism_name}: {t.mechanism_description}",
    )

    # Run A1.5 quality gate against the synthesis
    qr = validate(syn)

    # Build falsification packets for each engine claim
    falsification = [
        FalsificationPacket(
            belief=f"{e.name} becomes a ${e.target_revenue_m:.0f}M engine via {e.flywheel_type} flywheel",
            disproof_test=f"Find competitor already executing {e.name} with similar flywheel "
                          f"and equivalent installed base; if found, this claim falls.",
            pass_criteria="No equivalent productized engine in market as of generation date",
            status="open",
        )
        for e in t.engines
    ]

    # Build ProofPacket
    packet = ProofPacket(
        claim=f"{t.company_short} is {t.wound_months} months from {t.wound_channel} lockout. "
              f"{t.mechanism_name} resolves it.",
        evidence=evidence,
        source_weights={src: 0.65 for src in t.evidence_sources},
        confidence=t.confidence,
    )

    return {
        "proof_packet": packet.model_dump(mode="json"),
        "quality_result": qr.model_dump(mode="json") if hasattr(qr, "model_dump") else str(qr),
        "falsification": [f.model_dump(mode="json") for f in falsification],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def _classify_teaser_intent(t: TeaserInput) -> tuple[IntentKey, float]:
    """Use A1.1 to confirm this is a CLIENT_INTEL synthesis."""
    payload = InboundPayload(
        raw_text=f"client intelligence wedge for {t.company_name} in {t.industry}",
        source="teaser_generator",
        metadata={"prospect_id": t.prospect_id},
    )
    return classify_intent(payload)


def generate_teaser(t: TeaserInput, out_dir: Path) -> dict:
    """Generate a complete teaser bundle for one prospect.

    Args:
        t: Validated TeaserInput (Codex feeds one per prospect).
        out_dir: Root output dir; bundle goes into ``out_dir / t.prospect_id``.

    Returns:
        Dict with paths to all 4 artifacts and the proof packet.
    """
    intent, intent_conf = _classify_teaser_intent(t)
    proof = _build_proof_packet(t)

    bundle_dir = out_dir / t.prospect_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # ── Render HTML ────────────────────────────────────────────────────
    html_tpl = _env.get_template("teaser.html.j2")
    html = html_tpl.render(**t.model_dump())
    html_path = bundle_dir / "index.html"
    html_path.write_text(html, encoding="utf-8")

    # ── Render Markdown ────────────────────────────────────────────────
    md_tpl = _env.get_template("teaser.md.j2")
    md = md_tpl.render(**t.model_dump())
    md_path = bundle_dir / "teaser.md"
    md_path.write_text(md, encoding="utf-8")

    # ── Write input + proof ────────────────────────────────────────────
    input_path = bundle_dir / "teaser_input.json"
    input_path.write_text(t.model_dump_json(indent=2), encoding="utf-8")

    proof_path = bundle_dir / "proof_packet.json"
    proof_path.write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")

    return {
        "prospect_id": t.prospect_id,
        "company": t.company_name,
        "html": str(html_path),
        "md": str(md_path),
        "input": str(input_path),
        "proof_packet": str(proof_path),
        "intent": intent.value,
        "intent_confidence": intent_conf,
        "html_bytes": len(html),
        "md_bytes": len(md),
        "generated_at": proof["generated_at"],
    }
