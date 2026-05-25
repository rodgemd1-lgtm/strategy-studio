"""B46 — Impact assessment engine."""
from __future__ import annotations

from strategy_studio.core.types import Option


def assess_impact(options: list[Option]) -> list[dict]:
    """Assess potential impact for each option."""
    assessed_options = []
    
    for opt in options:
        # Simple impact assessment based on option description
        desc_lower = opt.description.lower()
        
        # Estimate impact factors
        financial_impact = 0.0
        strategic_impact = 0.0
        operational_impact = 0.0
        
        # Financial impact indicators
        if "revenue" in desc_lower or "income" in desc_lower or "profit" in desc_lower:
            financial_impact = 0.8
        elif "cost" in desc_lower or "expense" in desc_lower:
            financial_impact = 0.6
        else:
            financial_impact = 0.4
            
        # Strategic impact indicators
        if "market" in desc_lower or "growth" in desc_lower:
            strategic_impact = 0.9
        elif "innovation" in desc_lower or "differentiate" in desc_lower:
            strategic_impact = 0.7
        else:
            strategic_impact = 0.5
            
        # Operational impact indicators
        if "efficiency" in desc_lower or "process" in desc_lower:
            operational_impact = 0.8
        elif "automation" in desc_lower or "streamline" in desc_lower:
            operational_impact = 0.7
        else:
            operational_impact = 0.4
            
        # Create impact assessment
        impact = {
            "option_id": opt.id,
            "financial_impact": financial_impact,
            "strategic_impact": strategic_impact,
            "operational_impact": operational_impact,
            "overall_impact_score": (financial_impact + strategic_impact + operational_impact) / 3,
            "summary": f"Financial: {financial_impact:.1f}, Strategic: {strategic_impact:.1f}, Operational: {operational_impact:.1f}"
        }
        assessed_options.append(impact)
        
    return assessed_options