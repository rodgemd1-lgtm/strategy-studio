"""B-engines for Strategy Studio."""
# Import all B-engines
from strategy_studio.engines.b29_synthesize import synthesize_evidence
from strategy_studio.engines.b33_falsify import falsify_claim
from strategy_studio.engines.b34_predict import build_forecast
from strategy_studio.engines.b36_wargame import run_wargame
from strategy_studio.engines.b31_consensus_delta import calculate_consensus_delta
from strategy_studio.engines.b37_risk_assessment import assess_risks, compare_risk_profiles, generate_risk_matrix
from strategy_studio.engines.b40_market_sizing import size_market, estimate_som, market_attractiveness
from strategy_studio.engines.b43_competitive_positioning import (
    position_competitively,
    compute_competitive_advantage_score,
    five_forces_assessment,
)
from strategy_studio.engines.b44_timeline_planning import (
    plan_timeline,
    critical_path_analysis,
    generate_gantt_data,
)
from strategy_studio.engines.b45_budget_allocation import (
    allocate_budget,
    budget_scenarios,
    funding_efficiency,
)
from strategy_studio.engines.b46_impact_assessment import (
    assess_impact,
    rank_by_impact,
    impact_comparison,
    portfolio_impact,
)

__all__ = [
    # B29
    "synthesize_evidence",
    # B31
    "calculate_consensus_delta",
    # B33
    "falsify_claim",
    # B34
    "build_forecast",
    # B36
    "run_wargame",
    # B37
    "assess_risks",
    "compare_risk_profiles",
    "generate_risk_matrix",
    # B40
    "size_market",
    "estimate_som",
    "market_attractiveness",
    # B43
    "position_competitively",
    "compute_competitive_advantage_score",
    "five_forces_assessment",
    # B44
    "plan_timeline",
    "critical_path_analysis",
    "generate_gantt_data",
    # B45
    "allocate_budget",
    "budget_scenarios",
    "funding_efficiency",
    # B46
    "assess_impact",
    "rank_by_impact",
    "impact_comparison",
    "portfolio_impact",
]
