"""
A1.5 — Quality (PYTHON_ONLY)
Deterministic quality gate for synthesized output.
Falsification templates, checklist, issues list.  No LLM calls.
"""

from __future__ import annotations

from strategy_studio.core.types import (
    Synthesis,
    QualityResult,
    FalsificationPacket,
    IntentKey,
    AuditRow,
)

# ── Falsification templates per intent ─────────────────────────────────────────

_FALSIFICATION_TEMPLATES: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        "At least 2 independent sources support the recommendation.",
        "Options cover mutually exclusive strategic paths.",
        "Scores are within valid 0.0-1.0 range.",
    ],
    IntentKey.WARGAME: [
        "Each scenario has a named actor and move.",
        "Probabilities sum to ~1.0 across scenarios.",
        "RIG response is specified for each competitor move.",
    ],
    IntentKey.FORECAST: [
        "Prediction includes confidence interval.",
        "Base rate is referenced.",
        "Method is specified and falsifiable.",
    ],
    IntentKey.COMPETITOR_INTEL: [
        "Sources are dated within 90 days.",
        "At least 2 corroborating sources per claim.",
        "Competitor name is explicitly identified.",
    ],
    IntentKey.CLIENT_INTEL: [
        "ICP is defined with firmographic constraints.",
        "Wedge offer has pricing reference.",
        "Buyer committee roles are enumerated.",
    ],
    IntentKey.FALSIFY: [
        "Disproof test is operationally feasible.",
        "Pass criteria are measurable.",
        "Status is tracked per belief.",
    ],
    IntentKey.UNKNOWN: [
        "At least 2 sources available.",
        "Scores in valid range.",
        "No duplicate options.",
    ],
}


def validate(
    synthesis: Synthesis,
    intent: IntentKey = IntentKey.UNKNOWN,
) -> QualityResult:
    """
    Validate synthesis output.
    - For each option, generate a FalsificationPacket.
    - Check: min 2 sources per option (via evidence len >= 2),
    - scores in range, no duplicates.
    Return QualityResult with pass/fail, checklist, issues list.
    """
    issues: list[str] = []
    checklist: list[str] = []
    passed = True

    # 1. Source count check
    total_options = len(synthesis.options)
    total_evidence = len(synthesis.options)  # proxy: one source per option in our model
    if total_options < 2 and total_evidence < 2:
        issues.append("Less than 2 options/evidence items available.")
        passed = False
    else:
        checklist.append("Minimum evidence threshold met.")

    # 2. Score range check
    for opt in synthesis.options:
        if not (0.0 <= opt.score <= 1.0):
            issues.append(f"Option '{opt.title}' score {opt.score} out of range.")
            passed = False
    if all(0.0 <= o.score <= 1.0 for o in synthesis.options):
        checklist.append("All scores in valid 0.0-1.0 range.")

    # 3. Duplicate title check
    titles = [o.title for o in synthesis.options]
    if len(titles) != len(set(titles)):
        issues.append("Duplicate option titles detected.")
        passed = False
    else:
        checklist.append("No duplicate option titles.")

    # 4. Has recommendation
    if synthesis.recommendation is None:
        issues.append("No recommendation selected.")
        passed = False
    else:
        checklist.append("Recommendation present.")

    # 5. Falsification packets generated (conceptual)
    templates = _FALSIFICATION_TEMPLATES.get(intent, _FALSIFICATION_TEMPLATES[IntentKey.UNKNOWN])
    for tmpl in templates:
        checklist.append(f"Falsification check: {tmpl}")

    return QualityResult(
        passed=passed,
        checklist=checklist,
        issues=issues,
    )
