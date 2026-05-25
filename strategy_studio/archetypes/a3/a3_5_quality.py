"""A3.5 — Parallel quality gate consensus.

Runs multiple quality checkers in parallel:
  - structure_agent: validates schema completeness
  - evidence_agent: checks evidence sufficiency
  - logic_agent: checks for contradictions

All must pass. Returns QualityResult with consensus.
Never raises.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from strategy_studio.core.types import IntentKey, QualityResult, Synthesis


def _structure_agent(synthesis: Synthesis) -> tuple[bool, list[str]]:
    """Check schema completeness."""
    issues = []
    if not synthesis.options:
        issues.append("No options generated")
    if synthesis.recommendation is None:
        issues.append("No recommendation set")
    if not synthesis.rationale or len(synthesis.rationale) < 10:
        issues.append("Rationale too short or missing")
    for opt in synthesis.options:
        if not opt.id or not opt.title:
            issues.append(f"Option missing id or title: {opt}")
    return (len(issues) == 0, issues)


def _evidence_agent(synthesis: Synthesis) -> tuple[bool, list[str]]:
    """Check evidence sufficiency."""
    issues = []
    if synthesis.recommendation and synthesis.recommendation.score < 0.2:
        issues.append("Recommendation score too low (<0.2)")
    high_opts = [o for o in synthesis.options if o.score > 0.5]
    if not high_opts:
        issues.append("No options with score > 0.5")
    return (len(issues) == 0, issues)


def _logic_agent(synthesis: Synthesis) -> tuple[bool, list[str]]:
    """Check for logical contradictions."""
    issues = []
    if synthesis.recommendation:
        # Recommendation should be the highest-scored option
        if synthesis.options:
            top = max(synthesis.options, key=lambda o: o.score)
            if synthesis.recommendation.id != top.id:
                issues.append("Recommendation is not the top-scored option")
    return (len(issues) == 0, issues)


def validate_consensus(
    synthesis: Synthesis,
    intent: IntentKey,
    agent_budget: int = 3,
) -> QualityResult:
    """Run quality agents in parallel. All must pass for overall pass."""
    agents = [_structure_agent, _evidence_agent, _logic_agent]
    all_issues: list[str] = []
    passed_count = 0

    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            futures = [ex.submit(a, synthesis) for a in agents[:agent_budget]]
            for f in futures:
                try:
                    passed, issues = f.result(timeout=2.0)
                    if passed:
                        passed_count += 1
                    all_issues.extend(issues)
                except Exception as e:
                    all_issues.append(f"Agent error: {e}")
    except Exception:
        for a in agents[:agent_budget]:
            try:
                passed, issues = a(synthesis)
                if passed:
                    passed_count += 1
                all_issues.extend(issues)
            except Exception as e:
                all_issues.append(f"Agent error: {e}")

    return QualityResult(
        passed=(passed_count == agent_budget),
        checklist=[f"structure: {'pass' if passed_count >= 1 else 'fail'}",
                    f"evidence: {'pass' if passed_count >= 2 else 'fail'}",
                    f"logic: {'pass' if passed_count >= 3 else 'fail'}"],
        issues=all_issues,
    )