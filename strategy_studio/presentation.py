"""
HTML Presentation Generator — Consulting-grade slide deck output.

Generates a single, self-contained HTML file with:
- Executive summary slide
- Strategic options comparison (scored table)
- Competitive positioning visualization
- Scenario analysis with probability bars
- Prediction charts (ASCII/Unicode bar charts)
- Wargame results
- Evidence quality dashboard
- Risk matrix
- Recommended next steps

Styled like a real consulting deck. No external dependencies.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from strategy_studio.core.types_extended import (
    CrossArchetypeConsensus,
    DecisionRoomResult,
    EvidenceGraph,
    ExecutiveSummary,
    MetaAnalysis,
    PredictionResult,
    Scenario,
    StrategyReport,
    WargameResult,
)


def _bar(value: float, max_val: float = 1.0, width: int = 20) -> str:
    """Generate a Unicode bar chart."""
    filled = int(value / max_val * width) if max_val > 0 else 0
    filled = max(0, min(filled, width))
    return "█" * filled + "░" * (width - filled)


def _pct(value: float) -> str:
    """Format as percentage."""
    return f"{value * 100:.1f}%" if value is not None else "N/A"


def _score_color(score: float) -> str:
    """Get color for a score."""
    if score >= 0.7:
        return "#27ae60"
    elif score >= 0.4:
        return "#f39c12"
    return "#e74c3c"


def _tier_color(tier: str) -> str:
    return {"A": "#27ae60", "B": "#3498db", "C": "#f39c12", "D": "#e74c3c"}.get(tier, "#95a5a6")


def _risk_color(level: str) -> str:
    return {"low": "#27ae60", "medium": "#f39c12", "high": "#e67e22", "critical": "#e74c3c"}.get(level, "#95a5a6")


def generate_html_presentation(report: StrategyReport, enriched_data: dict | None = None) -> str:
    """Generate a complete HTML presentation from a StrategyReport."""
    parts: list[str] = []

    global _slide_counter
    _slide_counter = 0

    # ── Header / CSS ─────────────────────────────────────────────────────
    parts.append(_html_header(report.title))

    # ── Slide 1: Title ───────────────────────────────────────────────────
    parts.append(_slide("title", f"""
        <div class="title-slide">
            <h1>{html.escape(report.title)}</h1>
            <p class="subtitle">Strategy Analysis & Recommendations</p>
            <p class="date">{report.executive_summary.date.strftime('%B %d, %Y') if hasattr(report.executive_summary, 'date') else ''}</p>
            <div class="confidence-badge" style="background: {_score_color({'H': 0.9, 'M': 0.5, 'L': 0.2}.get(report.executive_summary.confidence, 0.5))}">
                Confidence: {report.executive_summary.confidence}
            </div>
        </div>
    """))

    # ── Slide 2: Executive Summary ───────────────────────────────────────
    sections = []
    for finding in report.executive_summary.key_findings:
        sections.append(f"<li>{html.escape(finding)}</li>")

    risks_html = ""
    if report.executive_summary.risks:
        risk_items = "".join(f'<li class="risk-item">{html.escape(r)}</li>' for r in report.executive_summary.risks)
        risks_html = f'<div class="risks-section"><h3>Key Risks</h3><ul>{risk_items}</ul></div>'

    parts.append(_slide("executive-summary", f"""
        <h2>Executive Summary</h2>
        <div class="two-col">
            <div class="col">
                <h3>Key Findings</h3>
                <ul>{''.join(sections)}</ul>
            </div>
            <div class="col">
                <div class="recommendation-box">
                    <h3>Recommendation</h3>
                    <p class="recommendation">{html.escape(report.executive_summary.recommendation)}</p>
                </div>
                {risks_html}
            </div>
        </div>
    """))

    # ── Slide 3: Decision Matrix ──────────────────────────────────────────
    if report.decision_room and report.decision_room.decision_matrix and report.decision_room.decision_matrix.options:
        rows = ""
        for opt in report.decision_room.decision_matrix.options:
            bar = _bar(opt.total_score)
            color = _tier_color(opt.tier)
            rows += f"""
            <tr>
                <td><span class="rank">#{opt.rank}</span></td>
                <td><strong>{html.escape(opt.option_title)}</strong></td>
                <td><span class="score-pill" style="background:{color}">{opt.total_score:.2f}</span></td>
                <td><div class="bar-cell"><span class="bar" style="background:{color}">{bar}</span></div></td>
                <td><span class="tier-pill" style="background:{color}">{opt.tier}</span></td>
                <td><span class="confidence">{opt.confidence}</span></td>
            </tr>"""

        criteria_weights = ""
        if report.decision_room.decision_matrix.weights:
            for crit, weight in report.decision_room.decision_matrix.weights.items():
                w_bar = _bar(weight, max(report.decision_room.decision_matrix.weights.values()) if report.decision_room.decision_matrix.weights else 1.0)
                criteria_weights += f'<div class="weight-row"><span>{html.escape(crit)}</span><span class="weight-bar">{w_bar}</span><span>{_pct(weight)}</span></div>'

        sensitivity_html = ""
        if report.decision_room and report.decision_room.decision_matrix.sensitivity:
            top_sens = sorted(report.decision_room.decision_matrix.sensitivity, key=lambda s: abs(s.impact_on_score), reverse=True)[:5]
            sens_rows = ""
            for s in top_sens:
                impact_bar = _bar(abs(s.impact_on_score), max(abs(s.impact_on_score) for s in top_sens) if top_sens else 1.0)
                critical = "critical" if s.is_critical else ""
                sens_rows += f'<tr class="{critical}"><td>{html.escape(s.parameter)}</td><td>{impact_bar}</td><td>{s.elasticity:.2f}</td></tr>'
            sensitivity_html = f"""
            <div class="sensitivity-section">
                <h3>Sensitivity Analysis (Tornado)</h3>
                <table><thead><tr><th>Parameter</th><th>Impact</th><th>Elasticity</th></tr></thead>
                <tbody>{sens_rows}</tbody></table>
            </div>"""

        parts.append(_slide("decision-matrix", f"""
            <h2>Decision Matrix</h2>
            <div class="two-col">
                <div class="col">
                    <table class="data-table">
                        <thead><tr><th>Rank</th><th>Option</th><th>Score</th><th></th><th>Tier</th><th>Conf.</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                <div class="col">
                    <h3>Criteria Weights</h3>
                    {criteria_weights}
                    {sensitivity_html}
                </div>
            </div>
        """))

    # ── Slide 4: Competitive Landscape ────────────────────────────────────
    if report.wargame_result:
        wg = report.wargame_result
        moves_html = ""
        for move in wg.moves[:5]:
            prob_bar = _bar(move.probability)
            moves_html += f"""
            <div class="move-row">
                <span class="actor">{html.escape(move.actor)}</span>
                <span class="move-text">{html.escape(move.move[:60])}</span>
                <span class="prob-bar">{prob_bar}</span>
                <span class="prob-pct">{_pct(move.probability)}</span>
            </div>"""

        risk_badge = f'<span class="risk-badge" style="background:{_risk_color(wg.risk_level)}">{wg.risk_level.upper()}</span>' if wg.risk_level else ""

        parts.append(_slide("competitive", f"""
            <h2>Competitive Analysis</h2>
            <div class="scenario-header">
                <h3>{html.escape(wg.scenario_name)}</h3>
                {risk_badge}
            </div>
            <div class="moves-section">
                <h3>Competitive Moves</h3>
                {moves_html}
            </div>
            <div class="response-section">
                <h3>Recommended Response</h3>
                <p>{html.escape(wg.recommended_response)}</p>
            </div>
            {f'<div class="equilibrium"><h3>Equilibrium</h3><p>{html.escape(wg.equilibrium)}</p></div>' if wg.equilibrium else ''}
        """))

    # ── Slide 5: Scenarios ────────────────────────────────────────────────
    if report.decision_room.scenarios_considered:
        scenario_cards = ""
        for sc in report.decision_room.scenarios_considered[:6]:
            prob_bar = _bar(sc.probability, 1.0, 30)
            assumptions = "".join(f"<li>{html.escape(a[:50])}</li>" for a in sc.assumptions[:3])
            variables = "".join(f"<li>{html.escape(k)}: {v:.2f}</li>" for k, v in list(sc.variables.items())[:3])
            scenario_cards += f"""
            <div class="scenario-card">
                <h4>{html.escape(sc.name)}</h4>
                <div class="prob-display">
                    <span class="prob-bar">{prob_bar}</span>
                    <span class="prob-value">{_pct(sc.probability)}</span>
                </div>
                <div class="scenario-details">
                    <div><strong>Assumptions:</strong><ul>{assumptions}</ul></div>
                    <div><strong>Key Variables:</strong><ul>{variables}</ul></div>
                </div>
            </div>"""

        parts.append(_slide("scenarios", f"""
            <h2>Scenario Analysis</h2>
            <div class="scenario-grid">{scenario_cards}</div>
        """))

    # ── Slide 6: Predictions ──────────────────────────────────────────────
    if session_predictions := _get_predictions(report):
        pred_slides = ""
        for pred in session_predictions:
            ci_low, ci_high = pred.confidence_interval if pred.confidence_interval else (0, 0)
            point = pred.point_estimate if pred.point_estimate else 0
            scale = abs(ci_high - ci_low) if ci_high != ci_low else 1
            bar_width = min(40, int(abs(point) / scale * 40)) if scale > 0 else 20

            pred_slides += f"""
            <div class="prediction-card">
                <h4>{html.escape(pred.variable)}</h4>
                <div class="prediction-main">
                    <span class="point-estimate">{point:,.2f}</span>
                    <span="ci-range">[{ci_low:,.2f} — {ci_high:,.2f}]</span>
                </div>
                <div class="prediction-bar-wrap">
                    <div class="prediction-bar" style="width:{bar_width}%"></div>
                </div>
                <span class="method">Method: {html.escape(pred.method)}</span>
                {f'<span class="calibration">Calibration: {pred.calibration_score:.2f}</span>' if pred.calibration_score else ''}
            </div>"""

        parts.append(_slide("predictions", f"""
            <h2>Predictions</h2>
            <div class="prediction-grid">{pred_slides}</div>
        """))

    # ── Slide 7: Evidence Quality ─────────────────────────────────────────
    if report.evidence_graph:
        eg = report.evidence_graph
        nodes_html = ""
        for node in eg.nodes[:10]:
            rel_bar = _bar(node.reliability if hasattr(node, 'reliability') else 0.5, 1.0, 15)
            nodes_html += f"""
            <div class="source-node">
                <span class="source-uri">{html.escape(str(node.source_uri)[:40])}</span>
                <span class="source-bar">{rel_bar}</span>
                <span class="source-score">{node.overall:.2f}</span>
            </div>"""

        contradictions_html = ""
        if eg.contradictions:
            contra_items = "".join(
                f'<li class="contradiction">{html.escape(c.description[:80])}</li>'
                for c in eg.contradictions[:5]
            )
            contradictions_html = f'<div class="contradictions"><h3>Contradictions Detected</h3><ul>{contra_items}</ul></div>'

        gaps_html = ""
        if eg.gaps:
            gap_items = "".join(f'<li class="gap">{html.escape(g[:80])}</li>' for g in eg.gaps[:5])
            gaps_html = f'<div class="gaps"><h3>Evidence Gaps</h3><ul>{gap_items}</ul></div>'

        parts.append(_slide("evidence", f"""
            <h2>Evidence Quality</h2>
            <div class="evidence-summary">
                <span class="confidence-badge large" style="background:{_score_color({'H': 0.9, 'M': 0.5, 'L': 0.2}.get(eg.overall_confidence, 0.5))}">
                    Overall: {eg.overall_confidence}
                </span>
                <span>{len(eg.nodes)} sources scored</span>
            </div>
            <div class="two-col">
                <div class="col"><h3>Sources</h3>{nodes_html}</div>
                <div class="col">{contradictions_html}{gaps_html}</div>
            </div>
        """))

    # ── Slide 8: Cross-Archetype Consensus ───────────────────────────────
    if report.cross_archetype and report.cross_archetype.consensus_options:
        ca = report.cross_archetype
        consensus_rows = ""
        for opt in ca.consensus_options[:5]:
            bar = _bar(opt.score if hasattr(opt, 'score') else 0.5)
            consensus_rows += f"<tr><td>{html.escape(opt.title if hasattr(opt, 'title') else str(opt.id)[:30])}</td><td>{bar}</td><td>{opt.score:.2f}</td></tr>"

        agreement = ca.agreement_score if hasattr(ca, 'agreement_score') else 0
        parts.append(_slide("consensus", f"""
            <h2>Cross-Archetype Consensus</h2>
            <div class="agreement-display">
                <span>Agreement Score: <strong>{_pct(agreement)}</strong></span>
                <span>Confidence: <strong>{ca.confidence}</strong></span>
            </div>
            <table class="data-table">
                <thead><tr><th>Option</th><th></th><th>Score</th></tr></thead>
                <tbody>{consensus_rows}</tbody>
            </table>
            {f'<p class="dissent"><strong>Dissent:</strong> {len(ca.dissent_options)} options with significantly different scores</p>' if hasattr(ca, 'dissent_options') and ca.dissent_options else ''}
        """))

    # ── Slide 9: Enriched Data (Real Market Data) ─────────────────────────
    if enriched_data and enriched_data.get("data_sources"):
        data_rows = ""
        for src in enriched_data.get("data_sources", []):
            data_rows += f"<tr><td>{html.escape(src)}</td><td>✓</td></tr>"

        price_html = ""
        if enriched_data.get("current_price"):
            price_html = f"""
            <div class="price-display">
                <span class="price">${enriched_data['current_price']:,.2f}</span>
                {f'<span class="range">52w: ${enriched_data["fifty_two_week_low"]:,.2f} — ${enriched_data["fifty_two_week_high"]:,.2f}</span>' if enriched_data.get("fifty_two_week_low") else ''}
                {f'<span class="cagr">5y CAGR: {enriched_data["price_cagr_5y"]:.1f}%</span>' if enriched_data.get("price_cagr_5y") is not None else ''}
            </div>"""

        parts.append(_slide("data", f"""
            <h2>Market Data</h2>
            {price_html}
            <table class="data-table">
                <thead><tr><th>Source</th><th>Status</th></tr></thead>
                <tbody>{data_rows}</tbody>
            </table>
            {f'<p class="description">{html.escape(enriched_data.get("description", "")[:300])}</p>' if enriched_data.get("description") else ''}
        """))

    # ── Slide 10: Next Steps ───────────────────────────────────────────────
    next_steps_html = ""
    for i, step in enumerate(report.executive_summary.next_steps[:6]):
        next_steps_html += f'<div class="step"><span class="step-num">{i + 1}</span><span class="step-text">{html.escape(step)}</span></div>'

    parts.append(_slide("next-steps", f"""
        <h2>Next Steps</h2>
        <div class="steps-list">{next_steps_html}</div>
        <div class="footer-note">
            <p>Generated by Strategy Studio — Deterministic strategy synthesis</p>
            <p>Every claim is evidence-cited. Every option is scored. Fully reproducible.</p>
        </div>
    """))

    # ── Footer ────────────────────────────────────────────────────────────
    parts.append("""
    </div><!-- .slides -->
    <script>
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        const slides = document.querySelectorAll('.slide');
        let current = parseInt(document.querySelector('.slide.active')?.dataset?.slide || 0);
        if (e.key === 'ArrowRight' || e.key === ' ') {
            e.preventDefault();
            slides[current]?.classList.remove('active');
            current = Math.min(current + 1, slides.length - 1);
            slides[current]?.classList.add('active');
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            slides[current]?.classList.remove('active');
            current = Math.max(current - 1, 0);
            slides[current]?.classList.add('active');
        }
    });
    </script>
    </body></html>""")

    return "\n".join(parts)


def _get_predictions(report: StrategyReport) -> list:
    """Extract predictions from report."""
    predictions = []
    if report.prediction_result:
        predictions = [report.prediction_result]
    return predictions


_slide_counter = 0

def _slide(slide_id: str, content: str) -> str:
    global _slide_counter
    active = " active" if _slide_counter == 0 else ""
    _slide_counter += 1
    return f'<div class="slide{active}" id="{slide_id}" data-slide="{_slide_counter - 1}">{content}</div>'


def _next_slide() -> str:
    """Advance to the next slide marker (for internal use)."""
    return ""


def _html_header(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #0a0a1a;
    color: #e0e0e0;
    overflow: hidden;
}}
.slides-container {{ height: 100vh; }}
.slide {{
    display: none;
    height: 100vh;
    padding: 60px 80px;
    flex-direction: column;
    justify-content: center;
    page-break-after: always;
}}
.slide.active {{ display: flex; }}
.slide h1 {{ font-size: 3em; margin-bottom: 20px; color: #fff; }}
.slide h2 {{ font-size: 2em; margin-bottom: 30px; color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 10px; }}
.slide h3 {{ font-size: 1.3em; margin: 20px 0 15px; color: #3498db; }}
.slide h4 {{ font-size: 1.1em; margin: 15px 0 10px; color: #fff; }}
.slide p {{ font-size: 1.1em; line-height: 1.6; margin: 10px 0; }}
.slide ul {{ list-style: none; padding: 0; }}
.slide ul li {{ padding: 8px 0; padding-left: 20px; position: relative; }}
.slide ul li::before {{ content: "→"; position: absolute; left: 0; color: #e94560; }}

.title-slide {{ text-align: center; }}
.title-slide h1 {{ font-size: 4em; }}
.title-slide .subtitle {{ font-size: 1.5em; color: #95a5a6; margin-top: 20px; }}
.title-slide .date {{ color: #7f8c8d; margin-top: 10px; }}
.confidence-badge {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 1.1em; margin-top: 20px; color: #fff; }}
.confidence-badge.large {{ font-size: 1.5em; padding: 12px 30px; }}

.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; background: inherit; }}
.col {{ background: inherit; }}

.recommendation-box {{ background: rgba(233,69,96,0.1); border: 1px solid #e94560; border-radius: 12px; padding: 20px; margin: 20px 0; }}
.recommendation-box .recommendation {{ font-size: 1.4em; font-weight: bold; color: #e94560; }}

.data-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: inherit; }}
.data-table th {{ text-align: left; padding: 10px; border-bottom: 2px solid #333; color: #3498db; font-size: 0.9em; }}
.data-table td {{ padding: 10px; border-bottom: 1px solid #222; vertical-align: middle; }}
.data-table tr:hover {{ background: rgba(255,255,255,0.03); }}

.rank {{ background: #3498db; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 0.85em; }}
.score-pill {{ padding: 4px 12px; border-radius: 12px; font-weight: bold; color: #fff; font-size: 0.9em; }}
.tier-pill {{ padding: 4px 12px; border-radius: 12px; font-weight: bold; color: #fff; font-size: 0.9em; }}
.bar-cell {{ width: 120px; }}
.bar {{ font-size: 0.8em; letter-spacing: 1px; background: inherit; display: inline-block; }}
.confidence {{ color: #95a5a6; }}

.risks-section {{ background: rgba(231,76,60,0.1); border: 1px solid #e74c3c; border-radius: 12px; padding: 20px; margin-top: 20px; }}
.risk-item {{ color: #e74c3c; }}

.scenario-header {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
.risk-badge {{ padding: 6px 16px; border-radius: 12px; font-weight: bold; font-size: 0.9em; color: #fff; }}

.moves-section {{ background: rgba(52,152,219,0.05); border-radius: 12px; padding: 20px; }}
.move-row {{ display: flex; align-items: center; gap: 15px; padding: 10px 0; border-bottom: 1px solid #222; }}
.move-row .actor {{ font-weight: bold; color: #3498db; min-width: 100px; }}
.move-row .move-text {{ flex: 1; font-size: 0.9em; }}
.move-row .prob-bar {{ font-size: 0.7em; color: #27ae60; }}
.move-row .prob-pct {{ color: #95a5a6; min-width: 50px; text-align: right; }}

.response-section {{ background: rgba(46,204,113,0.1); border-left: 4px solid #2ecc71; padding: 15px 20px; margin-top: 20px; border-radius: 0 8px 8px 0; }}
.equilibrium {{ background: rgba(243,156,18,0.1); border-left: 4px solid #f39c12; padding: 15px 20px; margin-top: 15px; border-radius: 0 8px 8px 0; }}

.scenario-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
.scenario-card {{ background: rgba(255,255,255,0.03); border: 1px solid #333; border-radius: 12px; padding: 20px; }}
.scenario-card h4 {{ color: #3498db; margin-bottom: 10px; }}
.prob-display {{ display: flex; align-items: center; gap: 10px; margin: 10px 0; }}
.prob-bar {{ font-size: 0.8em; color: #2ecc71; }}
.proc-value {{ font-weight: bold; color: #2ecc71; }}
.scenario-details {{ font-size: 0.85em; color: #95a5a6; margin-top: 10px; }}
.scenario-details li {{ padding: 3px 0; }}

.prediction-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
.prediction-card {{ background: rgba(255,255,255,0.03); border: 1px solid #333; border-radius: 12px; padding: 20px; }}
.prediction-card h4 {{ color: #3498db; }}
.prediction-main {{ display: flex; align-items: baseline; gap: 15px; margin: 10px 0; }}
.point-estimate {{ font-size: 2em; font-weight: bold; color: #fff; }}
.ci-range {{ color: #95a5a6; font-size: 0.9em; }}
.prediction-bar-wrap {{ height: 8px; background: #222; border-radius: 4px; margin: 10px 0; }}
.prediction-bar {{ height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); border-radius: 4px; }}
.method {{ color: #7f8c8d; font-size: 0.8em; }}
.calibration {{ color: #f39c12; font-size: 0.8em; margin-left: 10px; }}

.evidence-summary {{ display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }}
.source-node {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #222; }}
.source-uri {{ flex: 1; font-size: 0.85em; color: #95a5a6; }}
.source-bar {{ font-size: 0.7em; color: #27ae60; }}
.source-score {{ font-weight: bold; color: #27ae60; min-width: 40px; text-align: right; }}
.contradictions {{ background: rgba(231,76,60,0.1); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
.contradictions h3 {{ color: #e74c3c; }}
.contradiction {{ color: #e74c3c; }}
.gaps {{ background: rgba(243,156,18,0.1); border-radius: 8px; padding: 15px; }}
.gaps h3 {{ color: #f39c12; }}
.gap {{ color: #f39c12; }}

.agreement-display {{ display: flex; gap: 30px; margin-bottom: 20px; font-size: 1.2em; }}
.dissent {{ color: #e74c3c; margin-top: 15px; }}

.price-display {{ text-align: center; margin: 20px 0; }}
.price {{ font-size: 3em; font-weight: bold; color: #2ecc71; display: block; }}
.range {{ color: #95a5a6; display: block; margin-top: 5px; }}
.cagr {{ color: #3498db; display: block; margin-top: 5px; }}
.description {{ color: #95a5a6; font-size: 0.9em; margin-top: 15px; line-height: 1.6; }}

.steps-list {{ display: flex; flex-direction: column; gap: 15px; }}
.step {{ display: flex; align-items: center; gap: 20px; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 10px; }}
.step-num {{ background: #e94560; color: #fff; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2em; flex-shrink: 0; }}
.step-text {{ font-size: 1.1em; }}

.footer-note {{ margin-top: 40px; text-align: center; color: #555; font-size: 0.85em; }}

.weight-row {{ display: flex; align-items: center; gap: 10px; padding: 5px 0; }}
.weight-row span:first-child {{ min-width: 150px; }}
.weight-bar {{ font-size: 0.7em; color: #3498db; }}

.sensitivity-section {{ margin-top: 20px; }}
.sensitivity-section table {{ font-size: 0.85em; }}
.sensitivity-section .critical {{ background: rgba(231,76,60,0.1); }}

/* Print styles */
@media print {{
    .slide {{ display: block; page-break-after: always; height: auto; padding: 40px; }}
    body {{ background: #fff; color: #000; }}
    .nav-bar {{ display: none; }}
}}

/* Nav bar */
.nav-bar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: rgba(10, 10, 26, 0.95);
    border-bottom: 1px solid #333;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 30px;
    z-index: 1000;
    font-size: 0.85em;
    color: #666;
}}
.nav-left {{
    color: #e94560;
    font-weight: bold;
}}
.nav-right {{
    color: #666;
}}
.slide {{
    padding-top: 40px;
}}
</style>
</head>
<body>
<div class="nav-bar">
    <div class="nav-left">Strategy Studio</div>
    <div class="nav-right"><span id="slide-num">1</span> / <span id="slide-total">8</span></div>
</div>
<div class="slides-container">"""


def export_presentation(
    report: StrategyReport,
    output_path: Path,
    enriched_data: dict | None = None,
) -> Path:
    """Export a strategy report as an HTML presentation."""
    html_content = generate_html_presentation(report, enriched_data)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path