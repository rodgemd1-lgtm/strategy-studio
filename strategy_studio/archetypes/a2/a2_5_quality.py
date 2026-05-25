"""
A2.5 — Hybrid Quality Gates (Dual Validation)
Requires BOTH deterministic checks AND evidence-based proof.
Stricter than A1: both gates must pass for overall pass.
LLM can provide additional quality assessment.
Never raises. Returns QualityResult always.
"""

from __future__ import annotations

from collections.abc import Callable

from strategy_studio.core.types import (
    Synthesis,
    QualityResult,
    FalsificationPacket,
    IntentKey,
    AuditRow,
)

# ── Falsification templates per intent (same as A1) ─────────────────────────────

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


def _deterministic_checks(synthesis: Synthesis) -> tuple[list[str], list[str]]:
    """
    Run deterministic quality checks (same as A1).
    Returns (checklist, issues).
    """
    issues: list[str] = []
    checklist: list[str] = []

    # 1. Source count check
    total_options = len(synthesis.options)
    if total_options < 2:
        issues.append("Less than 2 options available.")
    else:
        checklist.append("Minimum option threshold met.")

    # 2. Score range check
    all_valid = True
    for opt in synthesis.options:
        if not (0.0 <= opt.score <= 1.0):
            issues.append(f"Option '{opt.title}' score {opt.score} out of range.")
            all_valid = False
    if all_valid:
        checklist.append("All scores in valid 0.0-1.0 range.")

    # 3. Duplicate title check
    titles = [o.title for o in synthesis.options]
    if len(titles) != len(set(titles)):
        issues.append("Duplicate option titles detected.")
    else:
        checklist.append("No duplicate option titles.")

    # 4. Has recommendation
    if synthesis.recommendation is None:
        issues.append("No recommendation selected.")
    else:
        checklist.append("Recommendation present.")

    return checklist, issues


def _evidence_based_checks(synthesis: Synthesis) -> tuple[list[str], list[str]]:
    """
    Evidence-based quality checks.
    Requires evidence-backed scoring (not just template defaults).
    """
    issues: list[str] = []
    checklist: list[str] = []

    # 1. Recommendation must have non-zero score
    if synthesis.recommendation is not None:
        if synthesis.recommendation.score <= 0.0:
            issues.append("Recommendation has zero score — no evidence backing.")
        else:
            checklist.append(f"Recommendation has evidence-backed score: {synthesis.recommendation.score}.")

    # 2. At least one option with score > 0.3 (meaningful evidence)
    high_score_options = [o for o in synthesis.options if o.score > 0.3]
    if not high_score_options:
        issues.append("No options with score > 0.3. Evidence may be insufficient.")
    else:
        checklist.append(f"{len(high_score_options)} option(s) with score > 0.3.")

    # 3. Rationale must be non-empty
    if not synthesis.rationale or len(synthesis.rationale) < 10:
        issues.append("Rationale is missing or too short.")
    else:
        checklist.append("Rationale present and substantive.")

    return checklist, issues


def _llm_quality_assessment(
    synthesis: Synthesis,
    llm_fallback: Callable[..., str],
) -> tuple[list[str], list[str]]:
    """
    Use LLM for additional quality assessment.
    Returns (checklist_additions, issue_additions).
    """
    issues: list[str] = []
    checklist: list[str] = []

    options_summary = "\n".join(
        f"- {o.title}: {o.description} (score: {o.score})"
        for o in synthesis.options
    )
    prompt = (
        f"Review the following strategy synthesis for quality. "
        f"Check: (1) Are options distinct and actionable? "
        f"(2) Is the recommendation well-supported? "
        f"(3) Are there obvious gaps or risks?\n\n"
        f"Options:\n{options_summary}\n\n"
        f"Rationale: {synthesis.rationale}\n\n"
        f"Respond with 'PASS' if acceptable, or list specific issues."
    )
    try:
        llm_response = llm_fallback(prompt)
        if llm_response and isinstance(llm_response, str):
            response_lower = llm_response.lower()
            if "pass" in response_lower and "fail" not in response_lower:
                checklist.append("LLM quality assessment: PASS")
            else:
                # Extract issues from LLM response
                for line in llm_response.strip().split("\n"):
                    cleaned = line.strip().lstrip("-*0123456789.) \t")
                    if cleaned and len(cleaned) > 5:
                        issues.append(f"LLM: {cleaned}")
                if not any("LLM:" in i for i in issues):
                    checklist.append("LLM quality assessment: reviewed")
    except Exception:
        checklist.append("LLM quality assessment: unavailable")

    return checklist, issues


def validate_hybrid(
    synthesis: Synthesis,
    intent: IntentKey = IntentKey.UNKNOWN,
    llm_fallback: Callable[..., str] | None = None,
) -> QualityResult:
    """
    Hybrid quality gate — dual validation.
    Requires BOTH deterministic AND evidence-based checks to pass.
    LLM provides additional assessment when available.
    Stricter than A1: both gates must pass.
    Never raises.
    """
    try:
        # Gate 1: Deterministic checks
        det_checklist, det_issues = _deterministic_checks(synthesis)
        det_passed = len(det_issues) == 0

        # Gate 2: Evidence-based checks
        ev_checklist, ev_issues = _evidence_based_checks(synthesis)
        ev_passed = len(ev_issues) == 0

        # Combine
        checklist = det_checklist + ev_checklist
        issues = det_issues + ev_issues

        # Falsification templates
        templates = _FALSIFICATION_TEMPLATES.get(
            intent, _FALSIFICATION_TEMPLATES[IntentKey.UNKNOWN]
        )
        for tmpl in templates:
            checklist.append(f"Falsification check: {tmpl}")

        # LLM assessment (supplementary)
        if llm_fallback is not None:
            llm_checklist, llm_issues = _llm_quality_assessment(
                synthesis, llm_fallback
            )
            checklist.extend(llm_checklist)
            issues.extend(llm_issues)

        # Both gates must pass
        passed = det_passed and ev_passed

        return QualityResult(
            passed=passed,
            checklist=checklist,
            issues=issues,
        )

    except Exception:
        return QualityResult(
            passed=False,
            checklist=["Quality gate error — manual review required."],
            issues=["Quality gate encountered an exception."],
        )
