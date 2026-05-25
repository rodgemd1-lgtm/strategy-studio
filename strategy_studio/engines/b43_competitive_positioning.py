"""B43 — Competitive positioning engine."""
from __future__ import annotations

from strategy_studio.core.types import Option


def position_competitively(options: list[Option], competitors: list[str]) -> list[dict]:
    """Position options competitively against competitors."""
    positioned_options = []
    
    for opt in options:
        # Simple competitive positioning based on option description
        desc_lower = opt.description.lower()
        
        # Determine competitive advantages
        advantages = []
        if "differentiate" in desc_lower or "unique" in desc_lower:
            advantages.append("Differentiation advantage")
        if "moat" in desc_lower or "barrier" in desc_lower:
            advantages.append("Barrier to entry")
        if "integration" in desc_lower or "ecosystem" in desc_lower:
            advantages.append("Ecosystem advantage")
        if "data" in desc_lower and "insight" in desc_lower:
            advantages.append("Data-driven advantage")
        if "speed" in desc_lower or "efficiency" in desc_lower:
            advantages.append("Operational efficiency")
            
        # Create competitive positioning
        positioning = {
            "option_id": opt.id,
            "competitors": competitors,
            "advantages": advantages,
            "positioning_statement": f"Positioning for {opt.title}: {', '.join(advantages) if advantages else 'No specific competitive advantages identified'}"
        }
        positioned_options.append(positioning)
        
    return positioned_options