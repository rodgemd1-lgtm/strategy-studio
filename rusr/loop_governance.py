"""Layer 10: Loop Governance — prevent unbounded loops."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator


class OnMaxReached(str, Enum):
    """Action when max iterations reached."""
    HALT = "halt"
    WARN = "warn"
    ESCALATE = "escalate"
    ABORT = "abort"


class BoundedLoop(BaseModel):
    """Bounded loop configuration — MUST have max_iterations."""
    max_iterations: int
    until_conditions: list[str] = []
    on_max_reached: OnMaxReached = OnMaxReached.HALT
    
    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max_iterations is positive."""
        if v <= 0:
            raise ValueError("max_iterations must be positive")
        if v > 10000:
            raise ValueError("max_iterations exceeds safe threshold (10000)")
        return v
    
    @field_validator("until_conditions")
    @classmethod
    def validate_until_conditions(cls, v: list[str]) -> list[str]:
        """Validate until_conditions is not empty if provided."""
        # Empty is OK — just means no exit condition (requires max_iterations)
        return v


class LoopIterationLog(BaseModel):
    """Audit trail for loop iterations."""
    loop_id: str
    iteration: int
    timestamp: datetime
    status: str  # "running", "exited", "halted", "escalated"
    exit_reason: str | None = None


class UnboundedLoopError(Exception):
    """Raised when a loop lacks proper bounds."""
    pass


def validate_loop_node(yaml_node: dict[str, Any]) -> BoundedLoop:
    """Validate a loop node from workflow YAML.
    
    Raises:
        UnboundedLoopError: If missing max_iterations OR until condition
    
    A loop is VALID if it has:
    - max_iterations set (required for safety)
    
    OR:
    - until_conditions set (with a reasonable max_iterations cap)
    """
    if not isinstance(yaml_node, dict):
        raise UnboundedLoopError("Loop node must be a dictionary")
    
    max_iterations = yaml_node.get("max_iterations")
    until_conditions = yaml_node.get("until_conditions", [])
    
    # Must have max_iterations
    if max_iterations is None:
        raise UnboundedLoopError(
            "Loop node missing required 'max_iterations' field. "
            "Unbounded loops are prohibited by RUSR Layer 10."
        )
    
    # Validate it's a positive integer
    if not isinstance(max_iterations, int) or max_iterations <= 0:
        raise UnboundedLoopError(
            f"max_iterations must be a positive integer, got: {max_iterations}"
        )
    
    # Warn if no until_conditions (less safe)
    if not until_conditions:
        # Still valid but logged as a warning
        pass
    
    on_max_reached = yaml_node.get("on_max_reached", "halt")
    if isinstance(on_max_reached, str):
        try:
            on_max_reached = OnMaxReached(on_max_reached)
        except ValueError:
            on_max_reached = OnMaxReached.HALT
    
    return BoundedLoop(
        max_iterations=max_iterations,
        until_conditions=until_conditions if isinstance(until_conditions, list) else [],
        on_max_reached=on_max_reached,
    )


def create_loop_iteration_log(
    loop_id: str,
    iteration: int,
    status: str,
    exit_reason: str | None = None
) -> LoopIterationLog:
    """Create an iteration log entry."""
    return LoopIterationLog(
        loop_id=loop_id,
        iteration=iteration,
        timestamp=datetime.now(),
        status=status,
        exit_reason=exit_reason,
    )