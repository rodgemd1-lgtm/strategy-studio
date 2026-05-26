"""Tests for Excalidraw renderer."""
import json
import pytest
from pathlib import Path
from strategy_studio.renderer import (
    render_excalidraw_to_svg,
    render_excalidraw_to_png,
    render_excalidraw_file,
    compute_bounding_box,
)


class TestRenderer:
    def test_render_simple_diagram(self):
        data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"type": "rectangle", "x": 50, "y": 50, "width": 200, "height": 80,
                 "strokeColor": "#333", "backgroundColor": "#e94560", "strokeWidth": 2,
                 "opacity": 100, "text": "Hello"},
                {"type": "text", "x": 100, "y": 150, "width": 100, "height": 20,
                 "strokeColor": "#333", "text": "World", "fontSize": 16},
            ],
        }
        svg = render_excalidraw_to_svg(data)
        assert "<svg" in svg
        assert "Hello" in svg

    def test_render_to_png(self):
        data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"type": "ellipse", "x": 100, "y": 100, "width": 80, "height": 40,
                 "strokeColor": "#333", "backgroundColor": "#2ecc71", "strokeWidth": 2,
                 "opacity": 100},
            ],
        }
        png_bytes = render_excalidraw_to_png(data)
        assert png_bytes is not None
        assert len(png_bytes) > 100
        assert png_bytes[:4] == b'\x89PNG'  # PNG magic bytes

    def test_render_file(self):
        import tempfile
        data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"type": "rectangle", "x": 50, "y": 50, "width": 100, "height": 50,
                 "strokeColor": "#333", "backgroundColor": "#3498db", "strokeWidth": 2,
                 "opacity": 100},
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.excalidraw"
            input_path.write_text(json.dumps(data))

            svg_path = render_excalidraw_file(input_path, format="svg")
            assert svg_path.exists()
            assert svg_path.suffix == ".svg"
            assert "<svg" in svg_path.read_text()

            png_path = render_excalidraw_file(input_path, format="png")
            assert png_path.exists()

    def test_compute_bounding_box(self):
        elements = [
            {"x": 10, "y": 20, "width": 100, "height": 50},
            {"x": 200, "y": 300, "width": 50, "height": 40},
        ]
        min_x, min_y, max_x, max_y = compute_bounding_box(elements)
        assert min_x < 10  # includes padding
        assert min_y < 20
        assert max_x > 250
        assert max_y > 340

    def test_empty_elements(self):
        svg = render_excalidraw_to_svg({"elements": []})
        assert "<svg" in svg
        assert "Empty" in svg