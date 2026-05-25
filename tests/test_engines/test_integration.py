"""Integration tests for Strategy Studio engines."""
import pytest
from strategy_studio.core.types import (
    Option,
)
from strategy_studio.engines.b31_consensus_delta import calculate_consensus_delta
from strategy_studio.engines.b37_risk_assessment import assess_risks
from strategy_studio.engines.b40_market_sizing import size_market
from strategy_studio.engines.b43_competitive_positioning import position_competitively
from strategy_studio.engines.b44_timeline_planning import plan_timeline
from strategy_studio.engines.b45_budget_allocation import allocate_budget
from strategy_studio.engines.b46_impact_assessment import assess_impact


def test_new_b_engines():
    """Test the newly implemented B-engines."""
    # Create sample options for testing
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Build proprietary charging network",
            score=0.92,
            risks=[]
        ),
        Option(
            id="opt-2",
            title="Option B", 
            description="Partner with existing network",
            score=0.78,
            risks=[]
        )
    ]
    
    # Test consensus delta engine
    delta = calculate_consensus_delta([], None)
    assert isinstance(delta, dict)

    # Test risk assessment engine
    risks = assess_risks(options)
    assert isinstance(risks, list)
    assert len(risks) >= 1

    # Test market sizing engine
    market_sizes = size_market(options)
    assert isinstance(market_sizes, list)
    assert len(market_sizes) >= 1

    # Test competitive positioning engine
    positioning = position_competitively(options, ["Tesla", "Nissan"])
    assert isinstance(positioning, list)
    assert len(positioning) >= 1

    # Test timeline planning engine
    timeline = plan_timeline(options)
    assert isinstance(timeline, list)
    assert len(timeline) >= 1

    # Test budget allocation engine
    budget = allocate_budget(options, 1000000.0)
    assert isinstance(budget, list)
    assert len(budget) >= 1

    # Test impact assessment engine
    impact = assess_impact(options)
    assert isinstance(impact, list)
    assert len(impact) >= 1

    print("All new B-engines working correctly!")