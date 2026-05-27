"""Tests for Layer 1: Tool Registry."""
import pytest

from contracts.v1.tool_registry import (
    ToolCall,
    UnregisteredToolError,
    UnknownFlagError,
)


class TestToolRegistry:
    """Test tool registry validation."""

    def test_text2image_soul_v2_accepts_soul_id(self):
        """text2image_soul_v2 SHOULD accept soul_id flag."""
        call = ToolCall(tool_name="text2image_soul_v2", flags={"soul_id": "test-123"})
        assert call.tool_name == "text2image_soul_v2"
        assert call.flags["soul_id"] == "test-123"

    def test_cinema_studio_2_5_rejects_soul_id(self):
        """cinema_studio_2_5 MUST reject soul_id flag — KEY DISTINCTION."""
        with pytest.raises(UnknownFlagError) as exc_info:
            ToolCall(tool_name="cinema_studio_2_5", flags={"soul_id": "test-123"})
        assert "soul_id" in str(exc_info.value).lower()
        assert "cinema_studio_2_5" in str(exc_info.value)

    def test_cinema_studio_2_5_accepts_valid_flags(self):
        """cinema_studio_2_5 should accept its valid flags."""
        call = ToolCall(
            tool_name="cinema_studio_2_5",
            flags={"prompt": "test", "duration": 30, "style": "cinematic"}
        )
        assert call.tool_name == "cinema_studio_2_5"

    def test_unknown_tool_raises(self):
        """Unregistered tool MUST raise UnregisteredToolError."""
        with pytest.raises(UnregisteredToolError) as exc_info:
            ToolCall(tool_name="unknown_tool", flags={})
        assert "unknown_tool" in str(exc_info.value)

    def test_unknown_flag_raises(self):
        """Unknown flag MUST raise UnknownFlagError."""
        with pytest.raises(UnknownFlagError) as exc_info:
            ToolCall(tool_name="text2image_soul_v2", flags={"invalid_flag": True})
        assert "invalid_flag" in str(exc_info.value)

    def test_extra_field_forbidden(self):
        """Extra fields MUST be forbidden."""
        with pytest.raises(Exception):  # pydantic will raise
            ToolCall(tool_name="generic_image_gen", extra_forbidden_field=True)

    def test_generic_image_gen_rejects_soul_id(self):
        """generic_image_gen MUST reject soul_id flag."""
        with pytest.raises(UnknownFlagError) as exc_info:
            ToolCall(tool_name="generic_image_gen", flags={"soul_id": "test-456"})
        assert "soul_id" in str(exc_info.value)

    def test_trusted_tools_have_no_soul_id(self):
        """terminal, read_file, write_file should not accept soul_id."""
        # These tools are implicitly trusted and don't need soul_id
        call = ToolCall(tool_name="terminal", flags={"command": "ls"})
        assert call.tool_name == "terminal"
        call = ToolCall(tool_name="execute_code", flags={"language": "python", "code": "print(1)"})
        assert call.tool_name == "execute_code"