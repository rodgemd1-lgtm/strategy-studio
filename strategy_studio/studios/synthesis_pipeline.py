"""
Synthesis Pipeline — Cross-archetype consensus, meta-analysis,
and multi-study evidence synthesis.

All functions are deterministic. Uses only Python stdlib.
"""
from __future__ import annotations

import hashlib
import math
from typing import Literal

from strategy_studio.core.types import (
    AuditRow,
    Option,
    ProofPacket,
    QualityResult,
    Synthesis,
)
from strategy_studio.core.types_extended import (
    ArchetypeResult,
    CrossArchetypeConsensus,
    MetaAnalysis,
)


def run_cross_archetype(
    results: list[ArchetypeResult],
) -> CrossArchetypeConsensus:
    """Run consensus analysis across multiple archetype results."""
    if not results:
        return CrossArchetypeConsensus(
            archetype_results=[],
            consensus_options=[],
            agreement_score=0.0,
            confidence="L",
        )

    # Collect all options from all archetype results
    all_options: list[Option] = []
    for ar in results:
        if ar.synthesis and ar.synthesis.options:
            all_options.extend(ar.synthesis.options)

    if not all_options:
        return CrossArchetypeConsensus(
            archetype_results=results,
            consensus_options=[],
            agreement_score=0.0,
            confidence="L",
        )

    # Group similar options (by score proximity)
    clusters: list[list[Option]] = []
    used = set()
    for i, opt_a in enumerate(all_options):
        if i in used:
            continue
        cluster = [opt_a]
        used.add(i)
        for j, opt_b in enumerate(all_options):
            if j in used:
                continue
            if abs(opt_a.score - opt_b.score) < 0.15:
                cluster.append(opt_b)
                used.add(j)
        clusters.append(cluster)

    # Consensus options: highest-scored option from each cluster
    consensus: list[Option] = []
    for cluster in clusters:
        best = max(cluster, key=lambda o: o.score)
        # Merge descriptions
        merged_desc = " | ".join(set(o.description for o in cluster))
        h = hashlib.md5(merged_desc.encode()).hexdigest()[:8]
        consensus.append(Option(
            id=f"consensus-{h}",
            title=best.title,
            description=merged_desc[:200],
            score=round(sum(o.score for o in cluster) / len(cluster), 4),
            risks=list(set(r for o in cluster for r in o.risks)),
        ))

    consensus.sort(key=lambda o: o.score, reverse=True)

    # Agreement score: what fraction of archetypes agree on top option
    if consensus and results:
        top_id = consensus[0].id
        agreeing = sum(
            1 for ar in results
            if ar.synthesis and ar.synthesis.recommendation
            and ar.synthesis.recommendation.score >= consensus[0].score - 0.15
        )
        agreement = agreeing / len(results)
    else:
        agreement = 0.0

    # Dissenting options: options that disagree with consensus
    dissenting: list[Option] = []
    if consensus:
        top_score = consensus[0].score
        for opt in all_options:
            if opt.score < top_score - 0.2:
                dissenting.append(opt)

    # Recommended synthesis from consensus
    recommended = None
    if consensus:
        recommended = Synthesis(
            options=consensus,
            recommendation=consensus[0],
            rationale=f"Cross-archetype consensus from {len(results)} archetypes, agreement={round(agreement, 2)}",
        )

    return CrossArchetypeConsensus(
        archetype_results=results,
        consensus_options=consensus,
        agreement_score=round(agreement, 4),
        dissenting_options=dissenting[:5],
        recommended_synthesis=recommended,
        confidence="H" if agreement > 0.7 else "M" if agreement > 0.4 else "L",
    )


def run_meta_analysis(analyses: list[Synthesis]) -> MetaAnalysis:
    """Meta-analysis across multiple synthesis results."""
    if not analyses:
        return MetaAnalysis(
            analyses=[],
            pooled_effect=0.0,
            heterogeneity=0.0,
            robustness=0.0,
            key_findings=["No analyses provided"],
            limitations=["Insufficient data for meta-analysis"],
        )

    # Collect all option scores
    all_scores: list[float] = []
    for syn in analyses:
        for opt in syn.options:
            all_scores.append(opt.score)

    if not all_scores:
        return MetaAnalysis(
            analyses=analyses,
            pooled_effect=0.0,
            heterogeneity=0.0,
            robustness=0.0,
            key_findings=["No options found in analyses"],
            limitations=["Empty analyses"],
        )

    # Pooled effect: weighted mean of all option scores
    n = len(all_scores)
    mean_score = sum(all_scores) / n

    # Heterogeneity: I²-like statistic based on variance
    if n > 1:
        variance = sum((s - mean_score) ** 2 for s in all_scores) / (n - 1)
        # I² = (variance - expected_sampling_variance) / variance
        # Simplified: use coefficient of variation
        cv = math.sqrt(variance) / mean_score if mean_score > 0 else 0.0
        heterogeneity = min(1.0, cv ** 2)
    else:
        heterogeneity = 0.0

    # Robustness: how consistent are the findings
    # High robustness = low heterogeneity + many analyses
    robustness = round(
        (1.0 - heterogeneity) * min(1.0, len(analyses) / 5.0),
        4,
    )

    # Key findings
    findings: list[str] = []
    top_options: list[Option] = []
    for syn in analyses:
        if syn.recommendation:
            top_options.append(syn.recommendation)

    if top_options:
        best = max(top_options, key=lambda o: o.score)
        findings.append(f"Highest-scored option across all analyses: {best.title} ({round(best.score, 2)})")

    if heterogeneity < 0.25:
        findings.append("Low heterogeneity — analyses are consistent")
    elif heterogeneity < 0.5:
        findings.append("Moderate heterogeneity — some variation between analyses")
    else:
        findings.append("High heterogeneity — analyses disagree significantly")

    if robustness > 0.7:
        findings.append("High robustness — findings are reliable")
    elif robustness > 0.4:
        findings.append("Moderate robustness — interpret with caution")
    else:
        findings.append("Low robustness — more analysis needed")

    # Limitations
    limitations: list[str] = []
    if len(analyses) < 3:
        limitations.append(f"Only {len(analyses)} analyses — need 3+ for reliable meta-analysis")
    if heterogeneity > 0.5:
        limitations.append("High heterogeneity reduces confidence in pooled estimate")
    if any(not syn.rationale for syn in analyses):
        limitations.append("Some analyses missing rationale")

    return MetaAnalysis(
        analyses=analyses,
        pooled_effect=round(mean_score, 4),
        heterogeneity=round(heterogeneity, 4),
        robustness=robustness,
        key_findings=findings,
        limitations=limitations,
    )


def synthesize_across_studies(
    evidence_sets: list[list[dict]],
    method: Literal["vote", "score", "bayesian"] = "score",
) -> dict:
    """Synthesize evidence across multiple studies/datasets."""
    if not evidence_sets:
        return {"pooled_estimate": 0.0, "confidence": "L", "n_studies": 0}

    # Extract scores from each study
    study_estimates: list[float] = []
    for evidence in evidence_sets:
        scores = [e.get("score", 0.5) for e in evidence if isinstance(e, dict)]
        if scores:
            study_estimates.append(sum(scores) / len(scores))

    if not study_estimates:
        return {"pooled_estimate": 0.0, "confidence": "L", "n_studies": 0}

    n = len(study_estimates)

    if method == "vote":
        # Majority vote: median
        sorted_est = sorted(study_estimates)
        pooled = sorted_est[n // 2]
    elif method == "bayesian":
        # Bayesian pooling: precision-weighted average
        # Assume each study has precision = 1/variance (use uniform prior)
        precisions = [1.0 / max(0.01, (est - sum(study_estimates) / n) ** 2) for est in study_estimates]
        total_precision = sum(precisions) or 1.0
        pooled = sum(e * p for e, p in zip(study_estimates, precisions)) / total_precision
    else:
        # Score: simple mean
        pooled = sum(study_estimates) / n

    # Confidence based on agreement
    if n > 1:
        variance = sum((e - pooled) ** 2 for e in study_estimates) / (n - 1)
        std_err = math.sqrt(variance / n)
        ci_width = 1.96 * std_err
    else:
        ci_width = 0.5

    confidence = "H" if ci_width < 0.1 else "M" if ci_width < 0.25 else "L"

    return {
        "pooled_estimate": round(pooled, 4),
        "confidence": confidence,
        "n_studies": n,
        "ci_95": (round(pooled - ci_width, 4), round(pooled + ci_width, 4)),
        "method": method,
        "study_estimates": [round(e, 4) for e in study_estimates],
    }