"""
Layer 11: Approval Timeout Halt.

on_timeout: auto_ship is a FORBIDDEN value — rejected at YAML parse time.
All approval gates must have a real timeout and escalation chain.
"""
from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class AutoShipError(Exception):
    """Raised when on_timeout is set to auto_ship — hard block."""

    def __init__(self, gate_id: str) -> None:
        self.gate_id = gate_id
        super().__init__(
            f"Approval gate '{gate_id}' has on_timeout=auto_ship — "
            f"FROBIDDEN. Approval timeouts MUST halt, never auto-ship."
        )


class TimeoutConfig(BaseModel):
    """Configuration for human approval gate."""
    model_config = {"frozen": True}

    gate_id: str
    timeout_hours: Annotated[int, Field(gt=0, le=168)] = Field(
        default=48, description="Hours until timeout fires"
    )
    route: str = Field(
        default="aionui://pi-96/queue",
        description="Routing destination for approval request"
    )
    escalation_chain: list[EscalationStep] = Field(default_factory=list)
    on_timeout: str = Field(default="halt", description="halt | escalate | block")

    @field_validator("on_timeout")
    @classmethod
    def no_auto_ship(cls, v: str) -> str:
        if v.strip().lower() == "auto_ship":
            raise AutoShipError(gate_id="unknown")
        return v


class EscalationStep(BaseModel):
    """Single step in the escalation chain."""
    model_config = {"frozen": True}

    notify: str = Field(..., description="Notification target (telegram-mike, email-mike, etc.)")
    after_hours: Annotated[int, Field(gt=0)] = Field(
        ..., description="Hours after approval gate opened"
    )
    action: str = Field(
        default="notify",
        description="notify | halt | escalate"
    )


def validate_approval_config(config: dict) -> None:
    """
    Validate an approval gate YAML node.

    Raises AutoShipError if on_timeout == "auto_ship".
    Raises ValueError if timeout < 1h or > 168h.
    """
    gate_id = config.get("id", "unknown")
    on_timeout = config.get("on_timeout", "")

    if on_timeout.strip().lower() == "auto_ship":
        raise AutoShipError(gate_id=gate_id)

    timeout_raw = config.get("timeout", "48h")
    if isinstance(timeout_raw, str) and timeout_raw.endswith("h"):
        timeout_hours = int(timeout_raw.rstrip("h"))
    elif isinstance(timeout_raw, (int, float)):
        timeout_hours = int(timeout_raw)
    else:
        timeout_hours = 48

    if not (1 <= timeout_hours <= 168):
        raise ValueError(
            f"Approval gate '{gate_id}' timeout {timeout_hours}h must be 1–168h"
        )

    # Validate escalation chain if present
    escalation = config.get("escalation_chain", [])
    if escalation:
        for step in escalation:
            if step.get("after") and step["after"] >= timeout_hours:
                raise ValueError(
                    f"Escalation step '{step.get('notify')}' at "
                    f"{step['after']}h fires AFTER timeout at {timeout_hours}h — "
                    f"it will never execute."
                )


def parse_timeout_string(timeout_str: str) -> int:
    """Parse '48h', '12h', '1w' etc. into hours."""
    timeout_str = timeout_str.strip().lower()
    if timeout_str.endswith("h"):
        return int(timeout_str.rstrip("h"))
    if timeout_str.endswith("d"):
        return int(timeout_str.rstrip("d")) * 24
    if timeout_str.endswith("w"):
        return int(timeout_str.rstrip("w")) * 24 * 7
    return int(timeout_str)


def get_escalation_at(escalation_chain: list[EscalationStep], hours_elapsed: float) -> EscalationStep | None:
    """Return the escalation step that should fire given hours elapsed."""
    for step in sorted(escalation_chain, key=lambda s: s.after_hours, reverse=True):
        if hours_elapsed >= step.after_hours:
            return step
    return None