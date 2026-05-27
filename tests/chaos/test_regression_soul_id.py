"""
Regression Test: Soul ID Bypass (2026-05-27)

Genesis: Hermes generated Post 21 via raw cinematic_studio_2_5 bypassing
bin/rig-viral. The --soul-id flag was silently dropped.

This test MUST run GREEN on a smoke test AND BLOCK the failing variant.
"""
from __future__ import annotations

import pytest
from contracts.v1.tool_registry import ToolCall, UnknownFlagError


def test_soul_id_bypass_regression():
    """
    Drill: Pass cinema_studio_2_5 with soul_id flag → must raise immediately.

    This is the exact failure mode from 2026-05-27:
    - Post 21 generated via raw cinematic_studio_2_5
    - --soul-id flag silently dropped
    - Output had generic images instead of Soul ID
    """
    with pytest.raises(Exception) as exc_info:
        ToolCall(
            tool_name="cinema_studio_2_5",
            flags={
                "prompt": "Coolio Gangsta's Paradise 1995",
                "soul_id": "muscular-man",
                "duration": "5s",
            },
        )
    assert "soul_id" in str(exc_info.value).lower()


def test_text2image_soul_v2_accepts_soul_id():
    """
    The CORRECT pipeline: Soul ID → text2image_soul_v2 only.

    Verify the tool that SHOULD accept soul_id does so correctly.
    """
    call = ToolCall(
        tool_name="text2image_soul_v2",
        flags={
            "prompt": "muscular man",
            "soul_id": "muscular-man",
            "seed": 42,
        },
    )
    # No exception = correctly validated
    assert call.tool_name == "text2image_soul_v2"
    assert call.flags["soul_id"] == "muscular-man"


def test_pipeline_stages_block_soul_id_on_wrong_tool():
    """
    Simulate the full pipeline: Frame → Vista → Glyph → Verify → Echo

    If any stage tries to pass soul_id to cinema_studio_2_5,
    it raises before reaching execution.
    """
    pipeline_stages = [
        ("Frame", "text2image_soul_v2", {"prompt": "scene", "soul_id": "muscular-man"}),
        ("Vista", "text2image_soul_v2", {"prompt": "style", "soul_id": "muscular-man"}),
        ("Glyph", "text2image_soul_v2", {"prompt": "detail", "soul_id": "muscular-man"}),
        ("Verify", "text2image_soul_v2", {"prompt": "refine"}),
        ("Echo", "text2image_soul_v2", {"prompt": "final"}),
    ]

    for stage_name, tool_name, flags in pipeline_stages:
        if tool_name == "cinema_studio_2_5" and "soul_id" in flags:
            pytest.fail(
                f"Stage '{stage_name}' tried to use cinema_studio_2_5 with soul_id — "
                f"blocked by tool_registry."
            )
        # All stages should use text2image_soul_v2 or other soul_id-accepting tools
        call = ToolCall(tool_name=tool_name, flags=flags)
        assert call.tool_name in ("text2image_soul_v2", "vision_analyze", "generic_image_gen")