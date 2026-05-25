"""B45 — Budget allocation engine."""
from __future__ import annotations

from strategy_studio.core.types import Option


def allocate_budget(options: list[Option], total_budget: float = 1000000.0) -> list[dict]:
    """Allocate budget among options based on complexity and expected ROI."""
    allocated_options = []
    
    for opt in options:
        # Simple budget allocation based on option description
        desc_lower = opt.description.lower()
        
        # Estimate budget allocation based on keywords
        budget_allocation = 0.0
        roi_estimate = 0.0
        
        if "high impact" in desc_lower or "major" in desc_lower:
            budget_allocation = total_budget * 0.4
            roi_estimate = 0.3
        elif "medium impact" in desc_lower or "moderate" in desc_lower:
            budget_allocation = total_budget * 0.3
            roi_estimate = 0.2
        elif "low impact" in desc_lower or "minor" in desc_lower:
            budget_allocation = total_budget * 0.2
            roi_estimate = 0.1
        elif "rapid" in desc_lower or "quick win" in desc_lower:
            budget_allocation = total_budget * 0.1
            roi_estimate = 0.15
        else:
            # Default allocation
            budget_allocation = total_budget * 0.25
            roi_estimate = 0.15
            
        # Create budget allocation
        allocation = {
            "option_id": opt.id,
            "budget": budget_allocation,
            "roi_estimate": roi_estimate,
            "unit": "USD",
            "allocation_percentage": budget_allocation / total_budget * 100
        }
        allocated_options.append(allocation)
        
    return allocated_options