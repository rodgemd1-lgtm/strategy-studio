"""
Visual Strategy Map Generator — Creates Excalidraw diagrams from strategy analysis.

Generates:
- Strategy architecture maps
- Decision trees
- Competitive positioning maps
- Scenario comparison diagrams
- Evidence graphs
- Wargame flow diagrams

All deterministic. Outputs .excalidraw JSON files.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from strategy_studio.core.types import Option, Synthesis
from strategy_studio.core.types_extended import (
    DecisionRoomResult,
    EvidenceGraph,
    Scenario,
    StrategyReport,
    WargameResult,
)

# ── Color Palette (RIG brand) ───────────────────────────────────────────────

COLORS = {
    "primary_fill": "#1a1a2e",
    "primary_stroke": "#16213e",
    "secondary_fill": "#0f3460",
    "secondary_stroke": "#e94560",
    "accent_fill": "#e94560",
    "accent_stroke": "#c62a40",
    "success_fill": "#2ecc71",
    "success_stroke": "#27ae60",
    "warning_fill": "#f39c12",
    "warning_stroke": "#e67e22",
    "danger_fill": "#e74c3c",
    "danger_stroke": "#c0392b",
    "neutral_fill": "#ecf0f1",
    "neutral_stroke": "#bdc3c7",
    "text_dark": "#1a1a2e",
    "text_light": "#ffffff",
    "text_muted": "#7f8c8d",
    "evidence_bg": "#2c3e50",
    "evidence_text": "#3498db",
    "arrow_primary": "#e94560",
    "arrow_secondary": "#0f3460",
    "arrow_neutral": "#95a5a6",
}


def _uid(prefix: str, *parts: Any) -> str:
    """Generate a deterministic unique ID."""
    h = hashlib.md5(str(parts).encode()).hexdigest()[:8]
    return f"{prefix}_{h}"


def _text_element(
    x: float, y: float, text: str,
    font_size: int = 16,
    color: str = COLORS["text_dark"],
    bold: bool = False,
    width: float = 200,
    prefix: str = "txt",
) -> dict:
    """Create an Excalidraw text element."""
    return {
        "id": _uid(prefix, x, y, text[:20]),
        "type": "text",
        "x": x, "y": y,
        "width": width, "height": font_size * 1.5,
        "text": text,
        "fontSize": font_size,
        "fontFamily": 3,
        "textAlign": "center",
        "verticalAlign": "middle",
        "strokeColor": color,
        "backgroundColor": "",
        "fillStyle": "solid",
        "strokeWidth": 0,
        "roughness": 0,
        "opacity": 100,
        "seed": hash(text) % 100000,
        "version": 1,
    }


def _rect_element(
    x: float, y: float, w: float, h: float,
    text: str = "",
    fill: str = COLORS["primary_fill"],
    stroke: str = COLORS["primary_stroke"],
    font_size: int = 14,
    text_color: str = COLORS["text_light"],
    prefix: str = "rect",
    roughness: int = 0,
) -> dict:
    """Create an Excalidraw rectangle element."""
    el = {
        "id": _uid(prefix, x, y, w, h),
        "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "roughness": roughness,
        "opacity": 100,
        "seed": hash(f"{x}{y}{w}{h}") % 100000,
        "version": 1,
    }
    if text:
        el["text"] = text
        el["fontSize"] = font_size
        el["fontFamily"] = 3
        el["textAlign"] = "center"
        el["verticalAlign"] = "middle"
        el["strokeColor"] = text_color
    return el


def _diamond_element(
    x: float, y: float, w: float, h: float,
    text: str = "",
    fill: str = COLORS["warning_fill"],
    stroke: str = COLORS["warning_stroke"],
    prefix: str = "dia",
) -> dict:
    """Create an Excalidraw diamond element."""
    return {
        "id": _uid(prefix, x, y),
        "type": "diamond",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "roughness": 0,
        "opacity": 100,
        "text": text,
        "fontSize": 13,
        "fontFamily": 3,
        "textAlign": "center",
        "verticalAlign": "middle",
        "seed": hash(f"{x}{y}") % 100000,
        "version": 1,
    }


def _ellipse_element(
    x: float, y: float, w: float, h: float,
    text: str = "",
    fill: str = COLORS["secondary_fill"],
    stroke: str = COLORS["secondary_stroke"],
    prefix: str = "ell",
) -> dict:
    """Create an Excalidraw ellipse element."""
    return {
        "id": _uid(prefix, x, y),
        "type": "ellipse",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "roughness": 0,
        "opacity": 100,
        "text": text,
        "fontSize": 12,
        "fontFamily": 3,
        "textAlign": "center",
        "verticalAlign": "middle",
        "seed": hash(f"{x}{y}") % 100000,
        "version": 1,
    }


def _arrow_element(
    x1: float, y1: float, x2: float, y2: float,
    label: str = "",
    color: str = COLORS["arrow_primary"],
    prefix: str = "arr",
) -> dict:
    """Create an Excalidraw arrow element."""
    el_id = _uid(prefix, x1, y1, x2, y2)
    return {
        "id": el_id,
        "type": "arrow",
        "x": x1, "y": y1,
        "width": abs(x2 - x1), "height": abs(y2 - y1),
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "strokeColor": color,
        "backgroundColor": "",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "roughness": 0,
        "opacity": 100,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "text": label,
        "fontSize": 11,
        "fontFamily": 3,
        "seed": hash(f"{x1}{y1}{x2}{y2}") % 100000,
        "version": 1,
    }


def _dot_element(
    x: float, y: float,
    fill: str = COLORS["accent_fill"],
    size: float = 12,
    prefix: str = "dot",
) -> dict:
    """Create a small dot element."""
    return {
        "id": _uid(prefix, x, y),
        "type": "ellipse",
        "x": x - size / 2, "y": y - size / 2,
        "width": size, "height": size,
        "strokeColor": fill,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": 0,
        "roughness": 0,
        "opacity": 100,
        "seed": hash(f"{x}{y}") % 100000,
        "version": 1,
    }


def _wrap_excalidraw(elements: list[dict]) -> dict:
    """Wrap elements in Excalidraw JSON format."""
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": 20,
            "currentItemStrokeColor": COLORS["text_dark"],
            "currentItemBackgroundColor": COLORS["primary_fill"],
        },
        "files": {},
    }


# ── Generators ───────────────────────────────────────────────────────────────

def generate_strategy_map(
    company_name: str,
    synthesis: Synthesis,
    decision_room: DecisionRoomResult | None = None,
    output_path: Path | None = None,
) -> dict:
    """Generate a strategy architecture map."""
    elements: list[dict] = []
    y_offset = 50

    # Title
    elements.append(_text_element(400, y_offset, f"Strategy Map: {company_name}",
                                   font_size=24, bold=True, width=600, prefix="title"))
    y_offset += 60

    # Archetype results bar
    elements.append(_text_element(100, y_offset, "ARCHETYPES", font_size=12,
                                   color=COLORS["text_muted"], width=120, prefix="lbl_a"))
    archetypes = ["A1 Deterministic", "A2 Hybrid", "A3 Agent-Bounded", "A4 LLM-Free"]
    colors = [COLORS["success_fill"], COLORS["secondary_fill"], COLORS["primary_fill"], COLORS["accent_fill"]]
    for i, (name, color) in enumerate(zip(archetypes, colors)):
        x = 80 + i * 140
        elements.append(_rect_element(x, y_offset + 20, 120, 30, text=name, fill=color,
                                       font_size=10, prefix=f"arch_{i}"))
    y_offset += 80

    # Main strategy options (fan-out from center)
    center_x, center_y = 400, y_offset + 80
    elements.append(_diamond_element(center_x - 60, center_y - 25, 120, 50,
                                      "Strategy?", fill=COLORS["accent_fill"],
                                      prefix="decision"))

    if synthesis.options:
        n = min(len(synthesis.options), 5)
        for i, opt in enumerate(synthesis.options[:n]):
            angle = (2 * math.pi * i / n) - math.pi / 2
            radius = 180
            ox = center_x + radius * math.cos(angle) - 70
            oy = center_y + radius * math.sin(angle) - 25

            is_top = opt == synthesis.recommendation
            fill = COLORS["success_fill"] if is_top else COLORS["secondary_fill"]
            elements.append(_rect_element(ox, oy, 140, 50, text=opt.title[:20],
                                           fill=fill, font_size=11, prefix=f"opt_{i}"))
            elements.append(_text_element(ox + 70, oy + 58, f"Score: {opt.score:.2f}",
                                           font_size=10, color=COLORS["text_muted"],
                                           width=140, prefix=f"score_{i}"))
            elements.append(_arrow_element(center_x, center_y + 25, ox + 70, oy + 50,
                                           color=COLORS["arrow_primary"], prefix=f"arr_{i}"))

    y_offset += 280

    # Decision matrix summary (if available)
    if decision_room and decision_room.decision_matrix:
        dm = decision_room.decision_matrix
        elements.append(_text_element(100, y_offset, "DECISION MATRIX", font_size=12,
                                       color=COLORS["text_muted"], width=150, prefix="lbl_dm"))
        y_offset += 25
        for i, os in enumerate(dm.options[:4]):
            x = 80 + i * 130
            tier_color = {"A": COLORS["success_fill"], "B": COLORS["secondary_fill"],
                          "C": COLORS["warning_fill"], "D": COLORS["danger_fill"]}.get(os.tier, COLORS["neutral_fill"])
            elements.append(_rect_element(x, y_offset, 120, 60,
                                           text=f"{os.option_title[:15]}\n{os.total_score}",
                                           fill=tier_color, font_size=10, prefix=f"dm_{i}"))
        y_offset += 100

    # Risks at bottom
    if decision_room and decision_room.risks:
        elements.append(_text_element(100, y_offset, "KEY RISKS", font_size=12,
                                       color=COLORS["danger_stroke"], width=100, prefix="lbl_risk"))
        y_offset += 25
        for i, risk in enumerate(decision_room.risks[:3]):
            elements.append(_text_element(120, y_offset + i * 20, f"• {risk[:80]}",
                                           font_size=11, color=COLORS["text_dark"],
                                           width=500, prefix=f"risk_{i}"))

    diagram = _wrap_excalidraw(elements)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


def generate_decision_tree(
    options: list[Option],
    title: str = "Decision Tree",
    output_path: Path | None = None,
) -> dict:
    """Generate a decision tree diagram."""
    elements: list[dict] = []

    elements.append(_text_element(400, 30, title, font_size=22, bold=True, width=500, prefix="title"))

    root_x, root_y = 400, 100
    elements.append(_diamond_element(root_x - 50, root_y - 20, 100, 40,
                                      "Decision", prefix="root"))

    n = min(len(options), 4)
    for i, opt in enumerate(options[:n]):
        angle = (2 * math.pi * i / n) - math.pi / 2
        radius = 160
        ox = root_x + radius * math.cos(angle) - 60
        oy = root_y + radius * math.sin(angle) - 30

        color = COLORS["success_fill"] if i == 0 else COLORS["secondary_fill"]
        elements.append(_rect_element(ox, oy, 120, 60, text=f"{opt.title[:18]}\nScore: {opt.score:.2f}",
                                       fill=color, font_size=11, prefix=f"opt_{i}"))
        elements.append(_arrow_element(root_x, root_y + 20, ox + 60, oy + 60,
                                       color=COLORS["arrow_secondary"], prefix=f"arr_{i}"))

        # Risk leaves
        for j, risk in enumerate(opt.risks[:2]):
            ry = oy + 70 + j * 18
            elements.append(_text_element(ox + 60, ry, f"⚠ {risk[:25]}",
                                           font_size=9, color=COLORS["danger_stroke"],
                                           width=110, prefix=f"risk_{i}_{j}"))
            elements.append(_dot_element(ox + 5, oy + 30, fill=color, prefix=f"dot_{i}_{j}"))

    diagram = _wrap_excalidraw(elements)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


def generate_competitive_map(
    company_name: str,
    competitors: list[str],
    wargame: WargameResult | None = None,
    output_path: Path | None = None,
) -> dict:
    """Generate a competitive positioning map."""
    elements: list[dict] = []

    elements.append(_text_element(400, 30, f"Competitive Map: {company_name}",
                                   font_size=22, bold=True, width=500, prefix="title"))

    # Draw axes
    cx, cy = 400, 300
    # X axis (Market Share Low -> High)
    elements.append(_arrow_element(100, cy, 700, cy, color=COLORS["arrow_neutral"], prefix="axis_x"))
    elements.append(_text_element(700, cy + 20, "Market Share →", font_size=11,
                                   color=COLORS["text_muted"], width=120, prefix="lbl_x"))
    # Y axis (Innovation Low -> High)
    elements.append(_arrow_element(cx, 80, cx, 520, color=COLORS["arrow_neutral"], prefix="axis_y"))
    elements.append(_text_element(cx + 10, 60, "Innovation ↑", font_size=11,
                                   color=COLORS["text_muted"], width=100, prefix="lbl_y"))

    # Quadrant labels
    elements.append(_text_element(cx - 150, cy - 120, "Niche Players", font_size=10,
                                   color=COLORS["text_muted"], width=100, prefix="q1"))
    elements.append(_text_element(cx + 150, cy - 120, "Leaders", font_size=10,
                                   color=COLORS["success_stroke"], width=80, prefix="q2"))
    elements.append(_text_element(cx - 150, cy + 120, "Challengers", font_size=10,
                                   color=COLORS["warning_stroke"], width=100, prefix="q3"))
    elements.append(_text_element(cx + 150, cy + 120, "Dominant", font_size=10,
                                   color=COLORS["accent_stroke"], width=80, prefix="q4"))

    # Plot company (center-top)
    elements.append(_ellipse_element(cx - 40, cy - 100, 80, 40, text=company_name,
                                      fill=COLORS["accent_fill"], prefix="company"))

    # Plot competitors
    n = min(len(competitors), 6)
    for i, comp in enumerate(competitors[:n]):
        angle = (2 * math.pi * i / n)
        radius = 120 + (i % 2) * 60
        cx_pos = cx + radius * math.cos(angle) - 40
        cy_pos = cy + radius * math.sin(angle) - 15
        elements.append(_ellipse_element(cx_pos, cy_pos, 80, 30, text=comp[:12],
                                          fill=COLORS["secondary_fill"], prefix=f"comp_{i}"))
        elements.append(_arrow_element(cx + 20, cy - 80, cx_pos + 40, cy_pos + 30,
                                       color=COLORS["arrow_neutral"], prefix=f"arr_{i}"))

    # Wargame moves (if available)
    if wargame and wargame.moves:
        y_start = 540
        elements.append(_text_element(100, y_start, "COMPETITIVE MOVES", font_size=11,
                                       color=COLORS["text_muted"], width=150, prefix="lbl_wg"))
        for i, move in enumerate(wargame.moves[:4]):
            elements.append(_text_element(120, y_start + 20 + i * 18,
                                           f"{move.actor}: {move.move[:50]}",
                                           font_size=9, color=COLORS["text_dark"],
                                           width=500, prefix=f"move_{i}"))

    diagram = _wrap_excalidraw(elements)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


def generate_scenario_comparison(
    scenarios: list[Scenario],
    title: str = "Scenario Comparison",
    output_path: Path | None = None,
) -> dict:
    """Generate a scenario comparison diagram."""
    elements: list[dict] = []

    elements.append(_text_element(400, 30, title, font_size=22, bold=True, width=500, prefix="title"))

    n = min(len(scenarios), 4)
    col_width = 180
    start_x = 100

    for i, sc in enumerate(scenarios[:n]):
        x = start_x + i * (col_width + 20)
        y = 80

        # Probability bar
        prob_pct = int(sc.probability * 100)
        bar_color = COLORS["success_fill"] if sc.probability > 0.5 else COLORS["warning_fill"] if sc.probability > 0.25 else COLORS["danger_fill"]
        elements.append(_rect_element(x, y, col_width, 50, text=sc.name[:20],
                                       fill=bar_color, font_size=12, prefix=f"sc_{i}"))
        elements.append(_text_element(x + col_width / 2, y + 65, f"P={sc.probability:.0%}",
                                       font_size=10, color=COLORS["text_muted"],
                                       width=col_width, prefix=f"prob_{i}"))

        # Assumptions
        y += 90
        for j, assumption in enumerate(sc.assumptions[:3]):
            elements.append(_text_element(x + 5, y + j * 16, f"• {assumption[:25]}",
                                           font_size=9, color=COLORS["text_dark"],
                                           width=col_width - 10, prefix=f"asm_{i}_{j}"))

        # Variables
        y += 70
        for j, (var, val) in enumerate(list(sc.variables.items())[:3]):
            elements.append(_text_element(x + 5, y + j * 16, f"{var}: {val:.2f}",
                                           font_size=9, color=COLORS["secondary_stroke"],
                                           width=col_width - 10, prefix=f"var_{i}_{j}"))

    # Comparison arrows at bottom
    y_bottom = 350
    elements.append(_text_element(100, y_bottom, "COMPARISON", font_size=11,
                                   color=COLORS["text_muted"], width=100, prefix="lbl_cmp"))
    if n >= 2:
        p1, p2 = scenarios[0].probability, scenarios[1].probability
        winner = scenarios[0].name if p1 >= p2 else scenarios[1].name
        elements.append(_text_element(200, y_bottom + 20, f"Highest probability: {winner}",
                                       font_size=11, color=COLORS["text_dark"],
                                       width=400, prefix="winner"))

    diagram = _wrap_excalidraw(elements)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


def generate_evidence_graph_diagram(
    evidence_graph: EvidenceGraph,
    title: str = "Evidence Graph",
    output_path: Path | None = None,
) -> dict:
    """Generate an evidence graph visualization."""
    elements: list[dict] = []

    elements.append(_text_element(400, 30, title, font_size=22, bold=True, width=500, prefix="title"))

    # Source nodes
    n = min(len(evidence_graph.nodes), 8)
    for i, node in enumerate(evidence_graph.nodes[:n]):
        angle = (2 * math.pi * i / n)
        radius = 150
        x = 400 + radius * math.cos(angle) - 50
        y = 280 + radius * math.sin(angle) - 20

        rel = node.reliability
        color = COLORS["success_fill"] if rel > 0.7 else COLORS["warning_fill"] if rel > 0.4 else COLORS["danger_fill"]
        elements.append(_rect_element(x, y, 100, 40,
                                       text=node.source_uri[:15],
                                       fill=color, font_size=9, prefix=f"src_{i}"))
        elements.append(_text_element(x + 50, y + 48, f"R:{node.reliability:.1f} M:{node.relevance:.1f}",
                                       font_size=8, color=COLORS["text_muted"],
                                       width=100, prefix=f"score_{i}"))

    # Center: overall confidence
    conf_color = {"H": COLORS["success_fill"], "M": COLORS["warning_fill"], "L": COLORS["danger_fill"]}.get(
        evidence_graph.overall_confidence, COLORS["neutral_fill"])
    elements.append(_ellipse_element(370, 260, 60, 30,
                                      text=evidence_graph.overall_confidence,
                                      fill=conf_color, prefix="conf_center"))

    # Contradictions
    if evidence_graph.contradictions:
        y_off = 480
        elements.append(_text_element(100, y_off, "CONTRADICTONS", font_size=11,
                                       color=COLORS["danger_stroke"], width=120, prefix="lbl_contra"))
        for i, c in enumerate(evidence_graph.contradictions[:3]):
            elements.append(_text_element(120, y_off + 18 + i * 16,
                                           f"⚠ {c.description[:60]}",
                                           font_size=9, color=COLORS["danger_stroke"],
                                           width=500, prefix=f"contra_{i}"))

    # Gaps
    if evidence_graph.gaps:
        y_off = 560
        elements.append(_text_element(100, y_off, "GAPS", font_size=11,
                                       color=COLORS["text_muted"], width=60, prefix="lbl_gaps"))
        for i, gap in enumerate(evidence_graph.gaps[:3]):
            elements.append(_text_element(120, y_off + 18 + i * 16,
                                           f"? {gap[:60]}",
                                           font_size=9, color=COLORS["text_muted"],
                                           width=500, prefix=f"gap_{i}"))

    diagram = _wrap_excalidraw(elements)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return diagram


def generate_full_strategy_visuals(
    report: StrategyReport,
    output_dir: Path,
) -> dict[str, Path]:
    """Generate all visual diagrams for a strategy report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # Strategy map
    if report.executive_summary:
        p = output_dir / "strategy_map.excalidraw"
        # Build a minimal synthesis from the report
        dm_options = []
        if report.decision_room and report.decision_room.decision_matrix:
            dm_options = [Option(id=o.option_id, title=o.option_title, description="", score=o.total_score, risks=[])
                          for o in report.decision_room.decision_matrix.options]
        synthesis = Synthesis(
            options=dm_options,
            recommendation=dm_options[0] if dm_options else None,
            rationale=report.executive_summary.recommendation,
        )
        generate_strategy_map(
            report.title.replace("Strategy Analysis: ", ""),
            synthesis,
            report.decision_room,
            output_path=p,
        )
        paths["strategy_map"] = p

    # Competitive map
    if report.wargame_result:
        p = output_dir / "competitive_map.excalidraw"
        generate_competitive_map(
            report.title.replace("Strategy Analysis: ", ""),
            report.wargame_result.actors,
            report.wargame_result,
            output_path=p,
        )
        paths["competitive_map"] = p

    # Scenario comparison
    if report.decision_room and report.decision_room.scenarios_considered:
        p = output_dir / "scenarios.excalidraw"
        generate_scenario_comparison(
            report.decision_room.scenarios_considered,
            output_path=p,
        )
        paths["scenarios"] = p

    # Evidence graph
    if report.evidence_graph:
        p = output_dir / "evidence_graph.excalidraw"
        generate_evidence_graph_diagram(
            report.evidence_graph,
            output_path=p,
        )
        paths["evidence_graph"] = p

    # Auto-render all .excalidraw files to SVG + PNG
    try:
        from strategy_studio.renderer import render_excalidraw_file
        for excalidraw_file in output_dir.glob("*.excalidraw"):
            svg_path = render_excalidraw_file(excalidraw_file, format="svg")
            png_path = render_excalidraw_file(excalidraw_file, format="png")
            paths[f"{excalidraw_file.stem}_svg"] = svg_path
            if png_path.suffix == ".png":
                paths[f"{excalidraw_file.stem}_png"] = png_path
    except Exception:
        pass  # Renderer is optional

    return paths