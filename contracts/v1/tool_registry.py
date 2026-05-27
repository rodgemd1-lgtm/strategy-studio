"""Layer 1: Tool Registry with Pydantic v2 frozen contracts."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ToolCapability(str, Enum):
    """Tool capability flags."""
    ACCEPTS_SOUL_ID = "accepts_soul_id"
    REQUIRES_APPROVAL = "requires_approval"
    SIDE_EFFECTS = "side_effects"


class UnregisteredToolError(Exception):
    """Raised when an unregistered tool is called."""
    pass


class UnknownFlagError(Exception):
    """Raised when an unknown flag is passed to a tool."""
    pass


class ToolCall(BaseModel):
    """Validated tool call."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str
    flags: dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_tool_and_flags(self) -> ToolCall:
        """Validate tool is registered and flags are allowed."""
        if self.tool_name not in REGISTRY:
            raise UnregisteredToolError(
                f"Tool '{self.tool_name}' is not registered. "
                f"Available: {list(REGISTRY.keys())}"
            )

        tool_def = REGISTRY[self.tool_name]
        allowed_flags = tool_def.get("accepted_flags", set())
        
        for flag in self.flags:
            if flag not in allowed_flags:
                raise UnknownFlagError(
                    f"Flag '{flag}' is not allowed for tool '{self.tool_name}'. "
                    f"Allowed flags: {allowed_flags or 'none'}"
                )

        # Check soul_id constraint for cinema_studio_2_5
        if self.tool_name == "cinema_studio_2_5" and "soul_id" in self.flags:
            raise UnknownFlagError(
                "cinema_studio_2_5 does not accept soul_id flag. "
                "This tool is explicitly soul_id=False."
            )

        # Check soul_id acceptance
        if "soul_id" in self.flags:
            if not REGISTRY[self.tool_name].get("accepts_soul_id", False):
                raise UnknownFlagError(
                    f"Tool '{self.tool_name}' does not accept soul_id flag."
                )

        return self


# Tool Registry — defines capabilities per tool
REGISTRY: dict[str, dict[str, Any]] = {
    "text2image_soul_v2": {
        "accepts_soul_id": True,
        "accepted_flags": {"soul_id", "prompt", "seed", "width", "height"},
        "requires_approval": True,
        "side_effects": False,
        "cost_per_call_usd_max": 0.05,
        "timeout_seconds_max": 120,
    },
    "cinema_studio_2_5": {
        "accepts_soul_id": False,  # KEY DISTINCTION — no soul_id allowed
        "accepted_flags": {"prompt", "duration", "style", "resolution"},
        "requires_approval": False,
        "side_effects": True,
        "cost_per_call_usd_max": 2.50,
        "timeout_seconds_max": 300,
    },
    "generic_image_gen": {
        "accepts_soul_id": False,
        "accepted_flags": {"prompt", "model", "quality"},
        "requires_approval": False,
        "side_effects": False,
        "cost_per_call_usd_max": 0.02,
        "timeout_seconds_max": 60,
    },
    "vision_analyze": {
        "accepts_soul_id": False,
        "accepted_flags": {"image_ref", "task", "detail_level"},
        "requires_approval": False,
        "side_effects": False,
        "cost_per_call_usd_max": 0.01,
        "timeout_seconds_max": 30,
    },
    "web_search": {
        "accepts_soul_id": False,
        "accepted_flags": {"query", "max_results", "domain_filter"},
        "requires_approval": False,
        "side_effects": False,
        "cost_per_call_usd_max": 0.005,
        "timeout_seconds_max": 15,
    },
    "terminal": {
        "accepts_soul_id": False,
        "accepted_flags": {"command", "cwd", "timeout"},
        "requires_approval": True,
        "side_effects": True,
        "cost_per_call_usd_max": 0.001,
        "timeout_seconds_max": 60,
    },
    "execute_code": {
        "accepts_soul_id": False,
        "accepted_flags": {"language", "code", "sandbox"},
        "requires_approval": True,
        "side_effects": True,
        "cost_per_call_usd_max": 0.01,
        "timeout_seconds_max": 60,
    },
    "delegate_task": {
        "accepts_soul_id": False,
        "accepted_flags": {"task", "priority", "callback"},
        "requires_approval": True,
        "side_effects": True,
        "cost_per_call_usd_max": 0.10,
        "timeout_seconds_max": 3600,
    },
}