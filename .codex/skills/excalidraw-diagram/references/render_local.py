#!/usr/bin/env python3
"""Render Excalidraw JSON to PNG using Playwright with a self-contained HTML template."""

from __future__ import annotations
import argparse
import json
import base64
import sys
from pathlib import Path


def compute_bounding_box(elements: list[dict], pad: int = 60) -> tuple[int, int, int, int]:
    min_x = min(el.get("x", 0) for el in elements if not el.get("isDeleted"))
    min_y = min(el.get("y", 0) for el in elements if not el.get("isDeleted"))
    max_x = max(el.get("x", 0) + el.get("width", 0) for el in elements if not el.get("isDeleted"))
    max_y = max(el.get("y", 0) + el.get("height", 0) for el in elements if not el.get("isDeleted"))
    return int(min_x - pad), int(min_y - pad), int(max_x + pad), int(max_y + pad)


def elements_to_svg(elements: list[dict], min_x: int, min_y: int, max_x: int, max_y: int) -> str:
    """Convert Excalidraw elements to a simple SVG representation."""
    w = max_x - min_x
    h = max_y - min_y

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
    ]

    for el in elements:
        if el.get("isDeleted"):
            continue
        x = el.get("x", 0) - min_x
        y = el.get("y", 0) - min_y
        w_el = el.get("width", 0)
        h_el = el.get("height", 0)
        stroke = el.get("strokeColor", "#000000")
        fill = el.get("backgroundColor", "transparent")
        text = el.get("text", "")
        font_size = el.get("fontSize", 16)
        text_color = el.get("strokeColor", "#000000")
        el_type = el.get("type", "")
        opacity = el.get("opacity", 100) / 100

        if fill == "transparent" or fill == "none":
            fill_attr = "none"
        else:
            fill_attr = fill

        if el_type == "rectangle":
            rx = 8
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{w_el}" height="{h_el}" rx="{rx}" '
                f'stroke="{stroke}" fill="{fill_attr}" stroke-width="2" opacity="{opacity}"/>'
            )
        elif el_type == "diamond":
            cx, cy = x + w_el / 2, y + h_el / 2
            points = f"{cx},{y} {x + w_el},{cy} {cx},{y + h_el} {x},{cy}"
            svg_parts.append(
                f'<polygon points="{points}" '
                f'stroke="{stroke}" fill="{fill_attr}" stroke-width="2" opacity="{opacity}"/>'
            )
        elif el_type == "ellipse":
            svg_parts.append(
                f'<ellipse cx="{x + w_el / 2}" cy="{y + h_el / 2}" rx="{w_el / 2}" ry="{h_el / 2}" '
                f'stroke="{stroke}" fill="{fill_attr}" stroke-width="1" opacity="{opacity}"/>'
            )
        elif el_type == "arrow":
            points = el.get("points", [[0, 0], [w_el, 0]])
            if len(points) >= 2:
                abs_points = [(p[0] + el.get("x", 0) - min_x, p[1] + el.get("y", 0) - min_y) for p in points]
                d = "M " + " L ".join(f"{px},{py}" for px, py in abs_points)
                svg_parts.append(
                    f'<path d="{d}" stroke="{stroke}" fill="none" stroke-width="2" '
                    f'opacity="{opacity}" marker-end="url(#arrowhead)"/>'
                )
        elif el_type == "line":
            points = el.get("points", [[0, 0], [w_el, 0]])
            if len(points) >= 2:
                abs_points = [(p[0] + el.get("x", 0) - min_x, p[1] + el.get("y", 0) - min_y) for p in points]
                d = "M " + " L ".join(f"{px},{py}" for px, py in abs_points)
                stroke_style = el.get("strokeStyle", "solid")
                dash = ' stroke-dasharray="8,4"' if stroke_style == "dashed" else ""
                svg_parts.append(
                    f'<path d="{d}" stroke="{stroke}" fill="none" stroke-width="2" '
                    f'opacity="{opacity}"{dash}/>'
                )
        elif el_type == "text":
            # Escape XML
            safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            # Handle multiline
            lines = safe_text.split("\n")
            line_height = font_size * 1.25
            text_anchor = "start"
            dominant_baseline = "hanging"
            tx = x
            ty = y
            if el.get("textAlign") == "center":
                text_anchor = "middle"
                tx = x + w_el / 2
            if el.get("verticalAlign") == "middle":
                ty = y + h_el / 2 - (len(lines) - 1) * line_height / 2

            svg_parts.append(
                f'<text x="{tx}" y="{ty}" font-family="Arial,Helvetica,sans-serif" '
                f'font-size="{font_size}" fill="{text_color}" text-anchor="{text_anchor}" '
                f'dominant-baseline="{dominant_baseline}" opacity="{opacity}">'
            )
            for i, line in enumerate(lines):
                dy = i * line_height if i > 0 else 0
                svg_parts.append(f'<tspan x="{tx}" dy="{dy}">{line}</tspan>')
            svg_parts.append('</text>')

    # Arrowhead marker
    svg_parts.insert(2, '''
    <defs>
      <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#1e3a5f"/>
      </marker>
    </defs>
    ''')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def render(input_path: str, output_path: str | None = None, scale: int = 2) -> Path:
    in_path = Path(input_path)
    data = json.loads(in_path.read_text())
    elements = data.get("elements", [])

    min_x, min_y, max_x, max_y = compute_bounding_box(elements)
    svg_content = elements_to_svg(elements, min_x, min_y, max_x, max_y)

    # Write SVG
    svg_path = in_path.with_suffix(".svg")
    svg_path.write_text(svg_content)
    print(f"[render] SVG: {svg_path}")

    # Convert to PNG using Playwright
    from playwright.sync_api import sync_playwright

    w = max_x - min_x
    h = max_y - min_y

    if output_path is None:
        png_path = in_path.with_suffix(".png")
    else:
        png_path = Path(output_path)

    html = f"""<!DOCTYPE html><html><head><style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #fff; display: inline-block; }}
    </style></head><body>
    {svg_content}
    </body></html>"""

    html_path = "/tmp/excalidraw_render.html"
    Path(html_path).write_text(html)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"file://{html_path}", timeout=30000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": w, "height": h})
        browser.close()

    print(f"[render] PNG: {png_path} ({w}x{h})")
    return png_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Path to .excalidraw file")
    p.add_argument("--output", "-o", help="Output PNG path")
    p.add_argument("--scale", type=int, default=2)
    args = p.parse_args()
    render(args.input, args.output, args.scale)


if __name__ == "__main__":
    main()
