"""B44 — Timeline planning engine for Strategy Studio.

Produces phased implementation timelines for strategic options using:
- Complexity estimation from description keywords
- Dependency analysis
- Critical path identification
- Milestone generation

All deterministic. No LLM in the loop.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Literal

from strategy_studio.core.types import Option


# ── Complexity estimation ───────────────────────────────────────────────────

_COMPLEXITY_KEYWORDS = {
    "simple": {"keywords": ["simple", "basic", "straightforward", "quick win", "easy"], "weeks": 6, "factor": 0.5},
    "moderate": {"keywords": ["moderate", "standard", "typical", "common"], "weeks": 12, "factor": 1.0},
    "complex": {"keywords": ["complex", "multi", "integrated", "enterprise", "cross-functional"], "weeks": 24, "factor": 2.0},
    "strategic": {"keywords": ["strategic", "transformative", "fundamental", "platform"], "weeks": 36, "factor": 3.0},
    "regulatory": {"keywords": ["regulatory", "approval", "compliance", "certified"], "weeks_weeks": 52, "factor": 4.0},
}


def _estimate_complexity(description: str) -> tuple[int, float, str]:  # (weeks, factor, level)
    """Estimate implementation complexity from description."""
    desc_lower = description.lower()

    for level, config in _COMPLEXITY_KEYWORDS.items():
        if level == "regulatory":
            continue
        if any(kw in desc_lower for kw in config["keywords"]):
            return config["weeks"], config["factor"], level

    # Default: moderate complexity
    return 12, 1.0, "moderate"

    # Check for regulatory separately (overrides)
    reg_config = _COMPLEXITY_KEYWORDS.get("regulatory")
    if reg_config and any(kw in desc_lower for kw in reg_config["keywords"]):
        return reg_config.get("weeks_weeks", 52), reg_config["factor"], "regulatory"


def _generate_milestones(option_id: str, weeks: int, start: datetime) -> list[dict]:
    """Generate milestone schedule based on total weeks."""
    milestones: list[dict] = []

    # Phase definitions (% of total timeline)
    phases = [
        ("Discovery & Scoping", 0.1, "Requirements validated"),
        ("Design & Architecture", 0.25, "Technical design approved"),
        ("Core Build", 0.5, "MVP / core deliverable complete"),
        ("Integration & Testing", 0.7, "Integration tests passing"),
        ("Pilot / Validation", 0.85, "Pilot results documented"),
        ("Launch / Deployment", 0.95, "Production deployment"),
        ("Post-Launch Review", 1.0, "Retrospective complete"),
    ]

    for phase_name, pct, deliverable in phases:
        milestone_date = start + timedelta(weeks=int(weeks * pct))
        milestones.append({
            "phase": phase_name,
            "date": milestone_date.isoformat(),
            "week": int(weeks * pct),
            "deliverable": deliverable,
        })

    return milestones


def plan_timeline(
    options: list[Option],
    start_date: datetime | None = None,
) -> list[dict]:
    """Plan implementation timelines for each option.

    Returns list of timeline dicts:
    [
      {
        "option_id": str,
        "start_date": str (ISO),
        "end_date": str (ISO),
        "duration_weeks": int,
        "complexity_level": str,
        "complexity_factor": float,
        "milestones": [{"phase": str, "date": str, "week": int, "deliverable": str}],
        "critical_path": [str],  # milestone names on critical path
        "dependencies": [str],
        "parallelizable": bool,
      }
    ]
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc)

    planned: list[dict] = []

    for i, opt in enumerate(options):
        weeks, factor, level = _estimate_complexity(opt.description)

        # Stagger starts by 2 weeks per option
        option_start = start_date + timedelta(weeks=i * 2)
        option_end = option_start + timedelta(weeks=weeks)

        milestones = _generate_milestones(opt.id, weeks, option_start)

        # Critical path: always includes Core Build, Integration & Testing, Launch
        critical_path = [m["phase"] for m in milestones if m["phase"] in (
            "Core Build", "Integration & Testing", "Launch / Deployment"
        )]

        # Dependencies: stagger based on option index
        dependencies: list[str] = []
        if i > 0:
            dependencies.append(f"option-{options[i-1].id}-launch")

        # Parallelizable if not too complex and no regulatory gate
        parallelizable = factor <= 2.0

        planned.append({
            "option_id": opt.id,
            "start_date": option_start.isoformat(),
            "end_date": option_end.isoformat(),
            "duration_weeks": weeks,
            "complexity_level": level,
            "complexity_factor": factor,
            "milestones": milestones,
            "critical_path": critical_path,
            "dependencies": dependencies,
            "parallelizable": parallelizable,
        })

    return planned


def critical_path_analysis(timelines: list[dict]) -> dict:
    """Identify the critical path across all options."""
    if not timelines:
        return {"critical_path": [], "total_weeks": 0, "bottleneck": None}

    # Find the longest path through all options
    total_weeks = 0
    path: list[str] = []
    bottleneck: str | None = None
    max_duration = 0

    for t in timelines:
        t_weeks = t["duration_weeks"]
        total_weeks += t_weeks
        for m in t.get("critical_path", []):
            path.append(f"{t['option_id']}: {m}")
        if t_weeks > max_duration:
            max_duration = t_weeks
            bottleneck = t["option_id"]

    return {
        "critical_path": path,
        "total_weeks": total_weeks,
        "bottleneck": bottleneck,
        "longest_single_option_weeks": max_duration,
    }


def generate_gantt_data(timelines: list[dict]) -> list[dict]:
    """Generate Gantt-chart-compatible data from timelines."""
    rows: list[dict] = []
    for t in timelines:
        rows.append({
            "task": t["option_id"],
            "start": t["start_date"],
            "end": t["end_date"],
            "duration_weeks": t["duration_weeks"],
            "progress": 0,
            "dependencies": t.get("dependencies", []),
        })
    return rows
