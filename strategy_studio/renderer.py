"""
Excalidraw SVG/PNG Renderer — Pure Python, no Playwright dependency.

Renders Excalidraw JSON to SVG, then optionally to PNG via cairosvg or reportlab.
Falls back gracefully if neither is available (outputs SVG only).
"""
from __future__ import annotations

import json
import math
import html
from pathlib import Path


def _escape(text: str) -> str:
    return html.escape(str(text))


def compute_bounding_box(elements: list[dict], pad: int = 80) -> tuple[int, int, int, int]:
    """Compute bounding box for all elements."""
    min_x = min((el.get("x", 0) for el in elements if not el.get("isDeleted")), default=0)
    min_y = min((el.get("y", 0) for el in elements if not el.get("isDeleted")), default=0)
    max_x = max((el.get("x", 0) + el.get("width", 0) for el in elements if not el.get("isDeleted")), default=400)
    max_y = max((el.get("y", 0) + el.get("height", 0) for el in elements if not el.get("isDeleted")), default=300)
    return int(min_x - pad), int(min_y - pad), int(max_x + pad), int(max_y + pad)


def elements_to_svg(excalidraw_data: dict) -> str:
    """Convert Excalidraw JSON to SVG string."""
    elements = excalidraw_data.get("elements", [])
    if not elements:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="#fff"/><text x="400" y="300" text-anchor="middle" fill="#999" font-size="16">Empty diagram</text></svg>'

    min_x, min_y, max_x, max_y = compute_bounding_box(elements)
    w = max(800, max_x - min_x)
    h = max(600, max_y - min_y)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
    ]

    for el in elements:
        if el.get("isDeleted"):
            continue
        x = el.get("x", 0) - min_x
        y = el.get("y", 0) - min_y
        ew = el.get("width", 0)
        eh = el.get("height", 0)
        stroke = el.get("strokeColor", "#333333")
        fill = el.get("backgroundColor", "transparent")
        text = el.get("text", "")
        font_size = el.get("fontSize", 14)
        el_type = el.get("type", "rectangle")
        opacity = el.get("opacity", 100) / 100.0
        stroke_width = el.get("strokeWidth", 2)
        points = el.get("points", [])

        # Convert fill "transparent" to SVG none
        fill_attr = "none" if fill in ("transparent", "", None) else fill

        if el_type == "rectangle":
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{ew}" height="{eh}" '
                f'fill="{fill_attr}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}" rx="4"/>'
            )
            if text:
                svg_parts.append(
                    f'<text x="{x + ew / 2}" y="{y + eh / 2 + font_size / 3}" '
                    f'text-anchor="middle" fill="{stroke}" font-size="{font_size}" '
                    f'font-family="system-ui, sans-serif">{_escape(text)}</text>'
                )

        elif el_type == "ellipse":
            cx, cy = x + ew / 2, y + eh / 2
            rx, ry = ew / 2, eh / 2
            svg_parts.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                f'fill="{fill_attr}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}"/>'
            )
            if text:
                svg_parts.append(
                    f'<text x="{cx}" y="{cy + font_size / 3}" '
                    f'text-anchor="middle" fill="{stroke}" font-size="{font_size}" '
                    f'font-family="system-ui, sans-serif">{_escape(text)}</text>'
                )

        elif el_type == "diamond":
            cx, cy = x + ew / 2, y + eh / 2
            points_str = f"{x},{cy} {cx},{y} {x + ew},{cy} {cx},{y + eh}"
            svg_parts.append(
                f'<polygon points="{points_str}" '
                f'fill="{fill_attr}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}"/>'
            )
            if text:
                svg_parts.append(
                    f'<text x="{cx}" y="{cy + font_size / 3}" '
                    f'text-anchor="middle" fill="{stroke}" font-size="{font_size}" '
                    f'font-family="system-ui, sans-serif">{_escape(text)}</text>'
                )

        elif el_type == "text":
            svg_parts.append(
                f'<text x="{x}" y="{y + font_size}" '
                f'fill="{stroke}" font-size="{font_size}" '
                f'font-family="system-ui, sans-serif" opacity="{opacity}">{_escape(text)}</text>'
            )

        elif el_type == "arrow":
            if len(points) >= 2:
                x1, y1 = points[0][0] - min_x, points[0][1] - min_y
                x2, y2 = points[-1][0] - min_x, points[-1][1] - min_y

                path_d = f"M {x1} {y1}"
                for px, py in points[1:]:
                    path_d += f" L {px - min_x} {py - min_y}"

                svg_parts.append(
                    f'<defs><marker id="arrowhead_{id(el)}" markerWidth="10" markerHeight="7" '
                    f'refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="{stroke}"/></marker></defs>'
                )
                svg_parts.append(
                    f'<path d="{path_d}" fill="none" stroke="{stroke}" '
                    f'stroke-width="{stroke_width}" marker-end="url(#arrowhead_{id(el)})" '
                    f'opacity="{opacity}"/>'
                )
                if text:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    svg_parts.append(
                        f'<text x="{mid_x}" y="{mid_y - 5}" '
                        f'text-anchor="middle" fill="{stroke}" font-size="{font_size}" '
                        f'font-family="system-ui, sans-serif">{_escape(text)}</text>'
                    )

        elif el_type == "line":
            if len(points) >= 2:
                x1, y1 = points[0][0] - min_x, points[0][1] - min_y
                path_d = f"M {x1} {y1}"
                for px, py in points[1:]:
                    path_d += f" L {px - min_x} {py - min_y}"
                svg_parts.append(
                    f'<path d="{path_d}" fill="none" stroke="{stroke}" '
                    f'stroke-width="{stroke_width}" opacity="{opacity}"/>'
                )

        elif el_type == "freedraw":
            if len(points) >= 2:
                path_d = f"M {points[0][0] - min_x} {points[0][1] - min_y}"
                for px, py in points[1:]:
                    path_d += f" L {px - min_x} {py - min_y}"
                svg_parts.append(
                    f'<path d="{path_d}" fill="none" stroke="{stroke}" '
                    f'stroke-width="{stroke_width}" opacity="{opacity}"/>'
                )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def render_excalidraw_to_svg(excalidraw_data: dict) -> str:
    """Render Excalidraw JSON to SVG string."""
    return elements_to_svg(excalidraw_data)


def render_excalidraw_to_png(excalidraw_data: dict) -> bytes | None:
    """Render Excalidraw JSON to PNG bytes. Requires cairosvg or Pillow."""
    svg_content = render_excalidraw_to_svg(excalidraw_data)

    # Try cairosvg first (better quality)
    try:
        import cairosvg
        return cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
    except ImportError:
        pass

    # Try Pillow (renders at lower quality)
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        # Parse SVG dimensions
        import re
        w_match = re.search(r'width="(\d+)"', svg_content)
        h_match = re.search(r'height="(\d+)"', svg_content)
        w = int(w_match.group(1)) if w_match else 800
        h = int(h_match.group(1)) if h_match else 600

        img = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(img)
        # Simple rendering: extract rectangles and text
        for m in re.finditer(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="([^"]+)"/>', svg_content):
            x, y, rw, rh, fill = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5)
            if fill and fill != "transparent" and fill != "none":
                draw.rectangle([x, y, x + rw, y + rh], fill=fill)
        for m in re.finditer(r'<text[^>]*x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]+)</text>', svg_content):
            x, y, text = float(m.group(1)), float(m.group(2)), m.group(3)
            draw.text((x, y), text, fill="#333333")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pass

    return None  # Neither cairosvg nor Pillow available


def render_excalidraw_file(
    input_path: str | Path,
    output_path: str | Path | None = None,
    format: str = "svg",
) -> Path:
    """Render an .excalidraw file to SVG or PNG."""
    input_path = Path(input_path)
    data = json.loads(input_path.read_text(encoding="utf-8"))

    if format == "svg":
        output_path = Path(output_path) if output_path else input_path.with_suffix(".svg")
        svg = render_excalidraw_to_svg(data)
        output_path.write_text(svg, encoding="utf-8")
        return output_path

    if format == "png":
        output_path = Path(output_path) if output_path else input_path.with_suffix(".png")
        png_bytes = render_excalidraw_to_png(data)
        if png_bytes:
            output_path.write_bytes(png_bytes)
            return output_path
        else:
            # Fallback to SVG
            svg_path = input_path.with_suffix(".svg")
            svg = render_excalidraw_to_svg(data)
            svg_path.write_text(svg, encoding="utf-8")
            return svg_path

    raise ValueError(f"Unknown format: {format}. Use 'svg' or 'png'.")