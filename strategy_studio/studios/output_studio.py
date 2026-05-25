"""
Output Studio — Executive summaries, board decks, strategy reports,
and complete proof-packet documentation.

All functions are deterministic. Uses only Python stdlib + Jinja2.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from strategy_studio.core.types import (
    AuditRow,
    Evidence,
    Option,
    ProofPacket,
    Synthesis,
)
from strategy_studio.core.types_extended import (
    BoardDeck,
    BoardSlide,
    CrossArchetypeConsensus,
    DecisionRoomResult,
    EvidenceGraph,
    ExecutiveSummary,
    MetaAnalysis,
    PredictionResult,
    StrategyReport,
    WargameResult,
)

_TEMPLATE_DIR = Path(__file__).parent / "templates_output"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Fallback inline templates (in case file templates don't exist)
_InlineEnv = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
)


def _get_template(name: str, inline: str) -> Any:
    """Try file template first, fall back to inline string."""
    try:
        return _env.get_template(name)
    except Exception:
        return _InlineEnv.from_string(inline)


# ── Inline fallback templates ────────────────────────────────────────────────

_EXEC_SUMMARY_MD = """# {{ title }}

**Date:** {{ date.strftime('%Y-%m-%d') }}
**Confidence:** {{ confidence }}

## Key Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

## Recommendation
{{ recommendation }}

## Risks
{% for risk in risks %}
- {{ risk }}
{% endfor %}

## Next Steps
{% for step in next_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
"""

_BOARD_SLIDE_HTML = """<!DOCTYPE html>
<html><head><style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:auto;padding:40px}
h1{color:#1a1a2e;border-bottom:3px solid #e94560;padding-bottom:10px}
.slide{background:#f8f9fa;border-left:4px solid #e94560;padding:20px;margin:20px 0}
.meta{color:#666;font-size:0.85em}
</style></head><body>
<h1>{{ title }}</h1>
<p class="meta">Generated {{ date.strftime('%Y-%m-%d %H:%M UTC') }}</p>
{% for slide in slides %}
<div class="slide">
<h2>{{ slide.slide_number }}. {{ slide.title }}</h2>
{{ slide.content }}
</div>
{% endfor %}
</body></html>
"""


def build_executive_summary(
    title: str,
    synthesis: Synthesis,
    quality_passed: bool,
    risks: list[str] | None = None,
    confidence: str = "M",
) -> ExecutiveSummary:
    """Build executive summary from synthesis result."""
    findings: list[str] = []

    if synthesis.recommendation:
        findings.append(
            f"Primary recommendation: {synthesis.recommendation.title} "
            f"(score: {round(synthesis.recommendation.score, 2)})"
        )

    if synthesis.options:
        findings.append(f"Evaluated {len(synthesis.options)} strategic options")
        top_3 = sorted(synthesis.options, key=lambda o: o.score, reverse=True)[:3]
        for i, opt in enumerate(top_3):
            findings.append(f"  #{i+1}: {opt.title} (score: {round(opt.score, 2)})")

    if synthesis.rationale:
        findings.append(f"Analysis rationale: {synthesis.rationale[:200]}")

    if quality_passed:
        findings.append("Quality gate: PASSED")
    else:
        findings.append("Quality gate: FAILED — results should be interpreted with caution")

    next_steps: list[str] = []
    if synthesis.recommendation:
        next_steps.append(f"Proceed with: {synthesis.recommendation.title}")
        if synthesis.recommendation.risks:
            for risk in synthesis.recommendation.risks[:3]:
                next_steps.append(f"Mitigate risk: {risk}")

    return ExecutiveSummary(
        title=title,
        key_findings=findings,
        recommendation=synthesis.recommendation.title if synthesis.recommendation else "No recommendation",
        confidence=confidence,  # type: ignore[arg-type]
        risks=risks or [],
        next_steps=next_steps,
    )


def build_board_deck(
    title: str,
    summary: ExecutiveSummary,
    decision_room: DecisionRoomResult | None = None,
    prediction: PredictionResult | None = None,
    wargame: WargameResult | None = None,
) -> BoardDeck:
    """Build a board deck (slide deck) from analysis results."""
    slides: list[BoardSlide] = []
    slide_num = 1

    # Slide 1: Title
    slides.append(BoardSlide(
        slide_number=slide_num,
        title=title,
        content=f"**Confidence:** {summary.confidence}\n\n**Date:** {summary.date.strftime('%Y-%m-%d')}",
        chart_type="none",
    ))
    slide_num += 1

    # Slide 2: Key Findings
    content = "\n".join(f"- {f}" for f in summary.key_findings)
    slides.append(BoardSlide(
        slide_number=slide_num,
        title="Key Findings",
        content=content,
        chart_type="none",
    ))
    slide_num += 1

    # Slide 3: Decision Matrix (if available)
    if decision_room and decision_room.decision_matrix:
        dm = decision_room.decision_matrix
        table_rows = []
        for os in dm.options[:5]:
            table_rows.append(f"| {os.rank} | {os.option_title} | {os.total_score} | {os.tier} |")
        table = "| Rank | Option | Score | Tier |\n|------|--------|-------|------|\n" + "\n".join(table_rows)
        slides.append(BoardSlide(
            slide_number=slide_num,
            title="Decision Matrix",
            content=table,
            chart_type="table",
            chart_data={"headers": ["Rank", "Option", "Score", "Tier"],
                        "rows": [[os.rank, os.option_title, os.total_score, os.tier] for os in dm.options[:5]]},
        ))
        slide_num += 1

    # Slide 4: Prediction (if available)
    if prediction:
        content = (
            f"**Variable:** {prediction.variable}\n\n"
            f"**Point Estimate:** {prediction.point_estimate}\n\n"
            f"**95% CI:** [{prediction.confidence_interval[0]}, {prediction.confidence_interval[1]}]\n\n"
            f"**Method:** {prediction.method}"
        )
        if prediction.monte_carlo:
            mc = prediction.monte_carlo
            content += f"\n\n**Monte Carlo ({mc.iterations} iter):** mean={round(mc.mean, 2)}, std={round(mc.std_dev, 2)}"
        slides.append(BoardSlide(
            slide_number=slide_num,
            title="Prediction",
            content=content,
            chart_type="bar" if prediction.monte_carlo else "none",
        ))
        slide_num += 1

    # Slide 5: Wargame (if available)
    if wargame:
        content = f"**Scenario:** {wargame.scenario_name}\n\n**Risk Level:** {wargame.risk_level.upper()}\n\n"
        if wargame.equilibrium:
            content += f"**Equilibrium:** {wargame.equilibrium}\n\n"
        content += f"**Recommended Response:** {wargame.recommended_response}\n\n"
        for move in wargame.moves[:3]:
            content += f"- **{move.actor}:** {move.move} (prob: {move.probability})\n"
        slides.append(BoardSlide(
            slide_number=slide_num,
            title="Wargame Analysis",
            content=content,
            chart_type="none",
        ))
        slide_num += 1

    # Slide 6: Risks
    if summary.risks:
        content = "\n".join(f"- {r}" for r in summary.risks)
        slides.append(BoardSlide(
            slide_number=slide_num,
            title="Key Risks",
            content=content,
            chart_type="none",
        ))
        slide_num += 1

    # Slide 7: Next Steps
    content = "\n".join(f"{i+1}. {s}" for i, s in enumerate(summary.next_steps))
    slides.append(BoardSlide(
        slide_number=slide_num,
        title="Recommended Next Steps",
        content=content,
        chart_type="none",
    ))

    return BoardDeck(title=title, slides=slides)


def build_strategy_report(
    title: str,
    synthesis: Synthesis,
    quality_passed: bool,
    decision_room: DecisionRoomResult | None = None,
    prediction: PredictionResult | None = None,
    wargame: WargameResult | None = None,
    evidence_graph: EvidenceGraph | None = None,
    cross_archetype: CrossArchetypeConsensus | None = None,
    meta_analysis: MetaAnalysis | None = None,
    audit_trail: list[AuditRow] | None = None,
) -> StrategyReport:
    """Build a complete strategy report."""
    summary = build_executive_summary(
        title=title,
        synthesis=synthesis,
        quality_passed=quality_passed,
        risks=decision_room.risks if decision_room else [],
        confidence=decision_room.confidence if decision_room else "M",
    )

    deck = build_board_deck(
        title=title,
        summary=summary,
        decision_room=decision_room,
        prediction=prediction,
        wargame=wargame,
    )

    proof_packets: list[ProofPacket] = []
    if cross_archetype and cross_archetype.recommended_synthesis:
        # Build proof packet from consensus
        if cross_archetype.consensus_options:
            top = cross_archetype.consensus_options[0]
            proof_packets.append(ProofPacket(
                claim=f"Cross-archetype consensus: {top.title}",
                evidence=[],
                source_weights={},
                confidence=cross_archetype.confidence,
            ))

    return StrategyReport(
        title=title,
        executive_summary=summary,
        board_deck=deck,
        decision_room=decision_room,
        prediction_result=prediction,
        wargame_result=wargame,
        evidence_graph=evidence_graph,
        cross_archetype=cross_archetype,
        meta_analysis=meta_analysis,
        proof_packets=proof_packets,
        audit_trail=audit_trail or [],
    )


def render_report_markdown(report: StrategyReport) -> str:
    """Render a strategy report as Markdown."""
    lines: list[str] = []
    lines.append(f"# {report.title}\n")
    lines.append(f"**Date:** {report.executive_summary.date.strftime('%Y-%m-%d')}")
    lines.append(f"**Confidence:** {report.executive_summary.confidence}\n")

    lines.append("## Executive Summary\n")
    for f in report.executive_summary.key_findings:
        lines.append(f"- {f}")
    lines.append(f"\n**Recommendation:** {report.executive_summary.recommendation}\n")

    if report.decision_room:
        lines.append("## Decision Room\n")
        dm = report.decision_room.decision_matrix
        if dm:
            lines.append("| Rank | Option | Score | Tier |")
            lines.append("|------|--------|-------|------|")
            for os in dm.options:
                lines.append(f"| {os.rank} | {os.option_title} | {os.total_score} | {os.tier} |")
            lines.append("")

    if report.prediction_result:
        p = report.prediction_result
        lines.append("## Prediction\n")
        lines.append(f"- **Variable:** {p.variable}")
        lines.append(f"- **Estimate:** {p.point_estimate}")
        lines.append(f"- **95% CI:** [{p.confidence_interval[0]}, {p.confidence_interval[1]}]")
        lines.append(f"- **Method:** {p.method}")
        lines.append("")

    if report.wargame_result:
        w = report.wargame_result
        lines.append("## Wargame\n")
        lines.append(f"- **Scenario:** {w.scenario_name}")
        lines.append(f"- **Risk Level:** {w.risk_level}")
        lines.append(f"- **Response:** {w.recommended_response}")
        lines.append("")

    if report.cross_archetype:
        ca = report.cross_archetype
        lines.append("## Cross-Archetype Consensus\n")
        lines.append(f"- **Agreement Score:** {ca.agreement_score}")
        lines.append(f"- **Confidence:** {ca.confidence}")
        if ca.consensus_options:
            lines.append("- **Consensus Options:**")
            for opt in ca.consensus_options[:3]:
                lines.append(f"  - {opt.title} (score: {opt.score})")
        lines.append("")

    if report.meta_analysis:
        ma = report.meta_analysis
        lines.append("## Meta-Analysis\n")
        lines.append(f"- **Pooled Effect:** {ma.pooled_effect}")
        lines.append(f"- **Heterogeneity:** {ma.heterogeneity}")
        lines.append(f"- **Robustness:** {ma.robustness}")
        for f in ma.key_findings:
            lines.append(f"- {f}")
        lines.append("")

    lines.append("## Risks\n")
    for r in report.executive_summary.risks:
        lines.append(f"- {r}")

    lines.append("\n## Next Steps\n")
    for i, step in enumerate(report.executive_summary.next_steps):
        lines.append(f"{i+1}. {step}")

    return "\n".join(lines)


def render_board_html(report: StrategyReport) -> str:
    """Render board deck as HTML."""
    if report.board_deck:
        tpl = _get_template("board_deck.html", _BOARD_SLIDE_HTML)
        return tpl.render(
            title=report.title,
            date=report.executive_summary.date,
            slides=report.board_deck.slides,
        )
    return f"<html><body><h1>{report.title}</h1><p>No board deck available.</p></body></html>"


def export_report(
    report: StrategyReport,
    output_dir: Path,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Export report in multiple formats. Returns {format: path}."""
    formats = formats or ["md", "html", "json"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    base_name = report.title.lower().replace(" ", "_")[:40]

    if "md" in formats:
        md_path = output_dir / f"{base_name}.md"
        md_path.write_text(render_report_markdown(report), encoding="utf-8")
        paths["md"] = md_path

    if "html" in formats:
        html_path = output_dir / f"{base_name}.html"
        html_path.write_text(render_board_html(report), encoding="utf-8")
        paths["html"] = html_path

    if "json" in formats:
        json_path = output_dir / f"{base_name}.json"
        json_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, default=str),
            encoding="utf-8",
        )
        paths["json"] = json_path

    return paths