"""B37 — Risk assessment engine."""
from __future__ import annotations

from strategy_studio.core.types import Option


def assess_risks(options: list[Option]) -> list[dict]:
    """Assess risks for each option."""
    assessments = []
    
    for opt in options:
        # Simple risk assessment based on option description
        desc_lower = opt.description.lower()
        
        # Identify common risk indicators
        risks = []
        if "capital intensive" in desc_lower or "high investment" in desc_lower:
            risks.append("High upfront capital requirement")
        if "regulatory" in desc_lower or "compliance" in desc_lower:
            risks.append("Regulatory approval risk")
        if "dependence" in desc_lower or "partner" in desc_lower:
            risks.append("Partner dependency risk")
        if "market" in desc_lower and "uncertain" in desc_lower:
            risks.append("Market demand uncertainty")
        if "technology" in desc_lower and "emerging" in desc_lower:
            risks.append("Technology adoption risk")
        if "margin" in desc_lower and "low" in desc_lower:
            risks.append("Margin compression risk")
            
        # Create risk assessment
        assessment = {
            "option_id": opt.id,
            "risks": risks,
            "severity": "high" if len(risks) > 2 else "medium" if len(risks) > 0 else "low",
            "mitigation_strategies": [
                f"Mitigate {risk}" for risk in risks
            ] if risks else []
        }
        assessments.append(assessment)
        
    return assessments