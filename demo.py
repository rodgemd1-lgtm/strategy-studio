#!/usr/bin/env python3
"""Demonstration script for Strategy Studio."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from strategy_studio.core.types import Option
from strategy_studio.engines.b31_consensus_delta import calculate_consensus_delta
from strategy_studio.engines.b33_falsify import falsify_claim
from strategy_studio.engines.b34_predict import build_forecast
from strategy_studio.engines.b36_wargame import run_wargame
from strategy_studio.engines.b37_risk_assessment import assess_risks
from strategy_studio.engines.b40_market_sizing import size_market
from strategy_studio.engines.b43_competitive_positioning import position_competitively
from strategy_studio.engines.b44_timeline_planning import plan_timeline
from strategy_studio.engines.b45_budget_allocation import allocate_budget
from strategy_studio.engines.b46_impact_assessment import assess_impact


def main():
    print("Strategy Studio Demo")
    print("=" * 50)

    options = [
        Option(id="opt-1", title="Build proprietary charging network", description="...", score=0.92, risks=["High capex", "Regulatory delays"]),
        Option(id="opt-2", title="Partner with existing network", description="...", score=0.78, risks=["Partner dependency"]),
        Option(id="opt-3", title="Hybrid approach", description="...", score=0.85, risks=["Complex implementation"]),
    ]

    # B31
    print("\nB31 Consensus Delta:", calculate_consensus_delta([], None))

    # B33
    f = falsify_claim("EV charging market growing", [])
    print(f"B33 Falsification: belief={f.belief}, test={f.disproof_test}")

    # B34
    fc = build_forecast("EV market growth rate", {"2023": 20.0, "2024": 25.0})
    print(f"B34 Forecast: var={fc.variable}, pred={fc.prediction}, ci={fc.confidence_interval}")

    # B36
    wg = run_wargame("Competitive moves in EV charging", ["competitor", "regulator"])
    for s in wg:
        print(f"B36 Wargame: actor={s.actor}, prob={s.probability}")

    # B37
    risks = assess_risks(options)
    print(f"B37 Risks: {len(risks)} options assessed")

    # B40
    sizes = size_market(options)
    print(f"B40 Market Sizing: {sizes[0]}")

    # B43
    pos = position_competitively(options, ["Tesla", "Nissan"])
    print(f"B43 Competitive Positioning: {len(pos)} options")

    # B44
    timeline = plan_timeline(options)
    print(f"B44 Timeline: {len(timeline)} plans, first duration={timeline[0]['duration_weeks']}w")

    # B45
    budget = allocate_budget(options, 1_000_000)
    print(f"B45 Budget: {len(budget)} allocations, first=${budget[0]['budget']:,.0f}")

    # B46
    impact = assess_impact(options)
    print(f"B46 Impact: {len(impact)} assessments, first score={impact[0]['overall_impact_score']}")

    print("\nAll 11 B-engines operational.")

if __name__ == "__main__":
    main()
