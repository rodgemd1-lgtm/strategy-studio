"""B-engines for Strategy Studio."""

# Import all B-engines
from strategy_studio.engines.b29_synthesize import synthesize_evidence
from strategy_studio.engines.b33_falsify import falsify_claim
from strategy_studio.engines.b34_predict import build_forecast
from strategy_studio.engines.b36_wargame import run_wargame
from strategy_studio.engines.b31_consensus_delta import calculate_consensus_delta
from strategy_studio.engines.b37_risk_assessment import assess_risks
from strategy_studio.engines.b40_market_sizing import size_market
from strategy_studio.engines.b43_competitive_positioning import position_competitively
from strategy_studio.engines.b44_timeline_planning import plan_timeline
from strategy_studio.engines.b45_budget_allocation import allocate_budget
from strategy_studio.engines.b46_impact_assessment import assess_impact

__all__ = [
    "synthesize_evidence",
    "falsify_claim",
    "build_forecast",
    "run_wargame",
    "calculate_consensus_delta",
    "assess_risks",
    "size_market",
    "position_competitively",
    "plan_timeline",
    "allocate_budget",
    "assess_impact",
]