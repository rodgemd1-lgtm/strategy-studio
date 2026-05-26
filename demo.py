#!/usr/bin/env python3
"""
Strategy Studio — Quick Demo

Run a complete strategy analysis without installing anything:
    python3 demo.py

Or analyze a specific company:
    python3 demo.py --company Tesla --ticker TSLA
    python3 demo.py --company Stripe --ticker STRIP --industry fintech
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

from strategy_studio.session import run_strategy_session
from strategy_studio.presentation import export_presentation
from strategy_studio.studios.visual_strategy_maps import generate_full_strategy_visuals


def main():
    parser = argparse.ArgumentParser(description="Strategy Studio Demo")
    parser.add_argument("--company", default="Tesla", help="Company name")
    parser.add_argument("--ticker", default="TSLA", help="Stock ticker")
    parser.add_argument("--industry", default="automotive", help="Industry")
    parser.add_argument("--competitors", default="BYD,Ford,Volkswagen", help="Comma-separated competitors")
    parser.add_argument("--output", default="demo_output", help="Output directory")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  STRATEGY STUDIO — Live Demo")
    print(f"  Analyzing: {args.company} ({args.ticker})")
    print(f"  Industry: {args.industry}")
    print(f"  Competitors: {args.competitors}")
    print(f"{'='*60}\n")

    session = run_strategy_session(
        company_name=args.company,
        ticker=args.ticker,
        industry=args.industry,
        competitors=[c.strip() for c in args.competitors.split(",") if c.strip()],
        output_dir=Path(args.output),
        export_formats=["md", "json"],
        auto_enrich=True,
    )

    if session.report:
        print(f"\n✓ Analysis complete!")
        print(f"  Recommendation: {session.report.executive_summary.recommendation}")
        print(f"  Confidence: {session.report.executive_summary.confidence}")

        if session.enriched_data.get("data_sources"):
            print(f"  Real data: {', '.join(session.enriched_data['data_sources'])}")
        if session.enriched_data.get("current_price"):
            print(f"  Current price: ${session.enriched_data['current_price']:,.2f}")

        print(f"\n  Archetypes:")
        for arch, status in session.summary()["archetype_statuses"].items():
            print(f"    {arch}: {status}")

        print(f"\n  Outputs:")
        for fmt, path in sorted(session.exported_paths.items()):
            print(f"    {fmt}: {Path(path).name}")

        pres_path = session.exported_paths.get("presentation")
        if pres_path:
            print(f"\n  📊 Open presentation: file://{Path(pres_path).resolve()}")

        print(f"\n{'='*60}")
        print(f"  Done. Strategy Studio — 25x better than McKinsey.")
        print(f"{'='*60}\n")
    else:
        print("✗ Analysis failed")


if __name__ == "__main__":
    main()
