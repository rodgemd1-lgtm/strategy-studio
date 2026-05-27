"""Layer 9: Budget Governance — cost ceilings and alerts."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class BudgetTier(str, Enum):
    """Budget tier levels."""
    PER_STEP = "per_step"
    PER_RUN = "per_run"
    PER_STUDIO_PER_DAY = "per_studio_per_day"
    GLOBAL_PER_DAY = "global_per_day"


class BudgetExceeded(Exception):
    """Raised when cost would exceed budget ceiling."""
    pass


class BudgetWarning(Exception):
    """Raised at budget warning thresholds."""
    pass


class BudgetCeiling(BaseModel):
    """Budget ceiling configuration."""
    tier: BudgetTier
    studio: str | None = None  # None means all studios
    ceiling_usd: float
    warning_at_pct: float = 80.0
    pause_at_pct: float = 95.0
    halt_at_pct: float = 100.0
    
    def get_warning_threshold(self) -> float:
        """Get warning threshold in USD."""
        return self.ceiling_usd * (self.warning_at_pct / 100.0)
    
    def get_pause_threshold(self) -> float:
        """Get pause threshold in USD."""
        return self.ceiling_usd * (self.pause_at_pct / 100.0)
    
    def get_halt_threshold(self) -> float:
        """Get halt threshold in USD."""
        return self.ceiling_usd * (self.halt_at_pct / 100.0)


def enforce_budget(
    tier: BudgetTier,
    studio: str | None,
    cost_so_far: float,
    new_cost: float,
    ceiling: BudgetCeiling | None = None,
) -> dict[str, Any]:
    """Enforce budget constraints.
    
    Raises:
        BudgetExceeded: When cost would hit or exceed ceiling
        BudgetWarning: At warning thresholds
    
    Returns:
        Dict with action taken: "ok", "warning", "pause", or "halt"
    """
    if ceiling is None:
        # Default ceiling if not provided
        ceiling = BudgetCeiling(
            tier=tier,
            studio=studio,
            ceiling_usd=100.0,
        )
    
    projected_total = cost_so_far + new_cost
    
    if projected_total >= ceiling.get_halt_threshold():
        raise BudgetExceeded(
            f"Budget halt: projected cost ${projected_total:.2f} would exceed "
            f"ceiling ${ceiling.ceiling_usd:.2f} (tier={tier.value}, studio={studio or 'all'}). "
            f"Cost so far: ${cost_so_far:.2f}, new cost: ${new_cost:.2f}"
        )
    
    if projected_total >= ceiling.get_pause_threshold():
        return {
            "action": "pause",
            "projected_total": projected_total,
            "ceiling": ceiling.ceiling_usd,
            "pct_used": (projected_total / ceiling.ceiling_usd) * 100,
            "message": "Budget pause: approaching ceiling",
        }
    
    if projected_total >= ceiling.get_warning_threshold():
        return {
            "action": "warning",
            "projected_total": projected_total,
            "ceiling": ceiling.ceiling_usd,
            "pct_used": (projected_total / ceiling.ceiling_usd) * 100,
            "message": f"Budget warning: {projected_total / ceiling.ceiling_usd * 100:.1f}% of ceiling used",
        }
    
    return {
        "action": "ok",
        "projected_total": projected_total,
        "ceiling": ceiling.ceiling_usd,
        "pct_used": (projected_total / ceiling.ceiling_usd) * 100,
        "message": "Budget check passed",
    }


def get_budget_ceiling(tier: BudgetTier, studio: str | None = None) -> BudgetCeiling:
    """Get the budget ceiling for a tier/studio combination."""
    # Default ceilings per tier
    defaults = {
        BudgetTier.PER_STEP: 1.0,
        BudgetTier.PER_RUN: 50.0,
        BudgetTier.PER_STUDIO_PER_DAY: 500.0,
        BudgetTier.GLOBAL_PER_DAY: 5000.0,
    }
    
    return BudgetCeiling(
        tier=tier,
        studio=studio,
        ceiling_usd=defaults.get(tier, 100.0),
    )