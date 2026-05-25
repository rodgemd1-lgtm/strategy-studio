"""B44 — Timeline planning engine."""
from __future__ import annotations

from datetime import datetime, timedelta
from strategy_studio.core.types import Option


def plan_timeline(options: list[Option], start_date: datetime = None) -> list[dict]:
    """Plan implementation timelines for each option."""
    if start_date is None:
        start_date = datetime.now()
        
    planned_options = []
    
    for i, opt in enumerate(options):
        # Simple timeline planning based on option complexity
        desc_lower = opt.description.lower()
        
        # Estimate timeline based on description keywords
        weeks = 12  # Default timeline
        if "simple" in desc_lower or "basic" in desc_lower:
            weeks = 6
        elif "complex" in desc_lower or "multi-stage" in desc_lower:
            weeks = 24
        elif "rapid" in desc_lower or "quick" in desc_lower:
            weeks = 4
        elif "long-term" in desc_lower or "strategic" in desc_lower:
            weeks = 36
            
        # Calculate dates
        start = start_date + timedelta(weeks=i*2)  # Staggered starts
        end = start + timedelta(weeks=weeks)
        
        # Create timeline plan
        timeline = {
            "option_id": opt.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "duration_weeks": weeks,
            "milestones": [
                {"phase": "Research", "date": (start + timedelta(weeks=1)).isoformat()},
                {"phase": "Design", "date": (start + timedelta(weeks=3)).isoformat()},
                {"phase": "Implementation", "date": (start + timedelta(weeks=6)).isoformat()},
                {"phase": "Testing", "date": (start + timedelta(weeks=9)).isoformat()},
                {"phase": "Launch", "date": end.isoformat()}
            ]
        }
        planned_options.append(timeline)
        
    return planned_options