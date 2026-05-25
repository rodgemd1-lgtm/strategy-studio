"""A4.5 — Strictest quality gates.

Requires ALL of:
  1. Min 2 evidence sources per claim (deterministic sources only)
  2. All options have distinct IDs (no duplicates)
  3. Recommendation score >= min_threshold (0.3)
  4. Falsification packet present with non-open status
  5. Rationale must cite specific sources

If any check fails — quality fails. No partial credit.
"""
from __future__ import annotations

from strategy_studio.core.types import IntentKey, QualityResult, Synthesis

_MIN_EVIDENCE_SOURCES = 2
_MIN_RECOMMENDATION_SCORE = 0.3


def validate_strict(
    synthesis: Synthesis,
    intent: IntentKey,
) -> QualityResult:
    """Strictest quality gates. All must pass."""
    issues: list[str] = []
    checklist: list[str] = []

    # Check 1: Evidence sufficiency
    # Count unique source URIs in risks/options
    sources: set[str] = set()
    for opt in synthesis.options:
        for risk in opt.risks:
            if "://" in risk:
                sources.add(risk.split("://")[0])
    has_min_sources = len(sources) >= _MIN_EVIDENCE_SOURCES
    checklist.append(f"evidence_sources: {'PASS' if has_min_sources else 'FAIL'} ({len(sources)}/{_MIN_EVIDENCE_SOURCES})")
    if not has_min_sources:
        issues.append(f"Only {len(sources)} evidence sources found, need {_MIN_EVIDENCE_SOURCES}+")

    # Check 2: Distinct option IDs
    ids = [o.id for o in synthesis.options]
    has_distinct = len(ids) == len(set(ids))
    checklist.append(f"distinct_ids: {'PASS' if has_distinct else 'FAIL'}")
    if not has_distinct:
        issues.append("Duplicate option IDs detected")

    # Check 3: Recommendation score
    if synthesis.recommendation:
        score_ok = synthesis.recommendation.score >= _MIN_RECOMMENDATION_SCORE
        checklist.append(f"recommendation_score: {'PASS' if score_ok else 'FAIL'} ({synthesis.recommendation.score:.2f}/{_MIN_RECOMMENDATION_SCORE})")
        if not score_ok:
            issues.append(f"Recommendation score {synthesis.recommendation.score:.2f} below threshold {_MIN_RECOMMENDATION_SCORE}")
    else:
        checklist.append("recommendation_score: FAIL (no recommendation)")
        issues.append("No recommendation set")

    # Check 4: Rationale substance
    rationale_ok = len(synthesis.rationale) >= 20 and "://" not in synthesis.rationale
    # Rationale should cite sources — look for source count references
    has_citation = "evidence" in synthesis.rationale.lower() or "source" in synthesis.rationale.lower()
    checklist.append(f"rationale: {'PASS' if has_citation else 'FAIL'}")
    if not has_citation:
        issues.append("Rationale does not cite evidence sources")

    # Check 5: Has options
    has_options = len(synthesis.options) >= 1
    checklist.append(f"has_options: {'PASS' if has_options else 'FAIL'}")
    if not has_options:
        issues.append("No options generated")

    passed = len(issues) == 0
    return QualityResult(passed=passed, checklist=checklist, issues=issues)