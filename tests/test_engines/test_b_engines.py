"""Unit tests for new B-engines."""
import pytest
from strategy_studio.core.types import Option, Synthesis
from strategy_studio.engines.b31_consensus_delta import calculate_consensus_delta
from strategy_studio.engines.b37_risk_assessment import assess_risks
from strategy_studio.engines.b40_market_sizing import size_market
from strategy_studio.engines.b43_competitive_positioning import position_competitively
from strategy_studio.engines.b44_timeline_planning import plan_timeline
from strategy_studio.engines.b45_budget_allocation import allocate_budget
from strategy_studio.engines.b46_impact_assessment import assess_impact


def test_consensus_delta():
    """Test consensus delta calculation."""
    # Create sample synthesis
    synthesis = Synthesis(
        options=[
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
    )
    
    # Test consensus delta
    result = calculate_consensus_delta([], synthesis)
    assert isinstance(result, dict)


def test_risk_assessment():
    """Test risk assessment engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Build proprietary charging network capital intensive",
            score=0.92,
            risks=[]
        )
    ]

    result = assess_risks(options)
    assert isinstance(result, list)
    assert len(result) >= 1
    # New format: structured risk dict with categories and mitigations
    assert "option_id" in result[0]
    assert "risks" in result[0]
    assert "overall_risk_level" in result[0]
    assert "overall_risk_score" in result[0]
    # Should detect financial risk from "capital intensive"
    risk_categories = [r["category"] for r in result[0]["risks"]]
    assert "financial" in risk_categories
    # Should have mitigations
    for r in result[0]["risks"]:
        assert "mitigations" in r
        assert "risk_score" in r


def test_market_sizing():
    """Test market sizing engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Enterprise solution",
            score=0.92,
            risks=[]
        )
    ]
    
    result = size_market(options)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "tam" in result[0]


def test_competitive_positioning():
    """Test competitive positioning engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Differentiate from competitors",
            score=0.92,
            risks=[]
        )
    ]

    result = position_competitively(options, ["Competitor A", "Competitor B"])
    assert isinstance(result, list)
    assert len(result) >= 1
    # New format: structured positioning dict
    assert "option_id" in result[0]
    assert "advantages" in result[0]
    assert "moat_score" in result[0]
    assert "competitive_intensity" in result[0]
    assert "recommended_positioning" in result[0]


def test_timeline_planning():
    """Test timeline planning engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Simple implementation",
            score=0.92,
            risks=[]
        )
    ]

    result = plan_timeline(options)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "start_date" in result[0]
    assert "end_date" in result[0]
    assert "duration_weeks" in result[0]
    assert "milestones" in result[0]
    assert "complexity_level" in result[0]


def test_budget_allocation():
    """Test budget allocation engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="High impact strategy",
            score=0.92,
            risks=[]
        )
    ]

    result = allocate_budget(options, 1000000.0)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "budget" in result[0]
    assert "allocation_percentage" in result[0]
    assert "estimated_cost" in result[0]
    assert "roi_estimate" in result[0]
    assert "priority_rank" in result[0]


def test_impact_assessment():
    """Test impact assessment engine."""
    options = [
        Option(
            id="opt-1",
            title="Option A",
            description="Revenue growth strategy",
            score=0.92,
            risks=[]
        )
    ]

    result = assess_impact(options)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "financial_impact" in result[0]
    assert "strategic_impact" in result[0]
    assert "operational_impact" in result[0]
    assert "overall_impact_score" in result[0]
    assert "impact_category" in result[0]
    assert "primary_dimension" in result[0]