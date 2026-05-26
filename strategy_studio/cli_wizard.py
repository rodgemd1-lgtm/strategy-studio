"""
Interactive CLI Wizard — Guided strategy session walkthrough.

Usage:
    strategy-studio wizard
    strategy-studio analyze <company_name> [--industry <industry>] [--competitors <csv>]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from strategy_studio.session import run_strategy_session, StrategySession
from strategy_studio.studios.visual_strategy_maps import generate_full_strategy_visuals
from strategy_studio.studios.industry_playbooks import get_playbook, get_kpis


def _print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def _print_step(step: int, total: int, text: str) -> None:
    print(f"\n[{step}/{total}] {text}")


def _print_success(text: str) -> None:
    print(f"  ✓ {text}")


def _print_info(text: str) -> None:
    print(f"  → {text}")


def _input_default(prompt: str, default: str = "") -> str:
    if default:
        result = input(f"  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  {prompt}: ").strip()


def _input_list(prompt: str) -> list[str]:
    print(f"  {prompt} (comma-separated, or 'skip'):")
    raw = input("  > ").strip()
    if raw.lower() == "skip" or not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _input_float(prompt: str, default: float = 0.0) -> float:
    raw = input(f"  {prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def wizard() -> StrategySession:
    """Run an interactive strategy session wizard."""
    _print_header("STRATEGY STUDIO — Interactive Strategy Session")
    print("\n  Welcome. I'll guide you through a complete strategy analysis.")
    print("  This will generate a McKinsey-quality strategy deck in seconds.\n")

    total_steps = 8

    # Step 1: Company
    _print_step(1, total_steps, "Company Information")
    company_name = _input_default("Company name", "Acme Corp")
    industry = _input_default("Industry", "saas")

    # Step 2: Context
    _print_step(2, total_steps, "Strategic Context")
    print("  What's the key strategic question or challenge?")
    context = input("  > ").strip()
    if not context:
        context = f"Strategic options for {company_name} in {industry}"

    # Step 3: Competitors
    _print_step(3, total_steps, "Competitive Landscape")
    competitors = _input_list("Who are the main competitors?")

    # Step 4: Historical Data
    _print_step(4, total_steps, "Historical Performance (optional)")
    historical_data = {}
    print("  Enter key metrics (year_value format, e.g., revenue_2023=15000)")
    print("  Press Enter with empty input when done.")
    while True:
        raw = input("  metric=value: ").strip()
        if not raw:
            break
        if "=" in raw:
            key, val = raw.split("=", 1)
            try:
                historical_data[key.strip()] = float(val.strip())
            except ValueError:
                _print_info(f"Skipping non-numeric value for {key}")

    # Step 5: Evidence
    _print_step(5, total_steps, "Evidence Sources (optional)")
    evidence_sources = _input_list("Key data points or sources (e.g., 'Market growing 25% YoY')")

    # Step 6: Industry Playbook Preview
    _print_step(6, total_steps, "Industry Playbook")
    playbook = get_playbook(industry)
    kpis = get_kpis(industry)
    _print_info(f"Industry: {industry}")
    _print_info(f"Key metrics: {', '.join(k['name'] for k in kpis[:5])}")
    if playbook.get("risk_factors"):
        _print_info(f"Top risks: {', '.join(r['name'] for r in playbook['risk_factors'][:3])}")

    # Step 7: Output
    _print_step(7, total_steps, "Output Configuration")
    output_dir = _input_default("Output directory", f"out/sessions/{company_name.lower().replace(' ', '_')}")
    formats = _input_default("Output formats (comma-separated)", "md,json")
    export_formats = [f.strip() for f in formats.split(",")]

    # Step 8: Run
    _print_step(8, total_steps, "Running Strategy Analysis...")
    print()

    start_time = time.time()

    session = run_strategy_session(
        company_name=company_name,
        industry=industry,
        context=context,
        competitors=competitors,
        historical_data=historical_data,
        evidence_sources=evidence_sources,
        output_dir=Path(output_dir),
        export_formats=export_formats,
    )

    elapsed = time.time() - start_time

    # Generate visuals
    if session.report:
        _print_info("Generating visual strategy maps...")
        viz_paths = generate_full_strategy_visuals(session.report, Path(output_dir) / "visuals")
        for name, path in viz_paths.items():
            _print_success(f"Visual: {name} → {path}")

    # Summary
    _print_header("STRATEGY SESSION COMPLETE")
    summary = session.summary()
    print(f"\n  Company: {summary['company']}")
    print(f"  Session: {summary['session_id']}")
    print(f"  Time: {elapsed:.1f} seconds")
    print(f"\n  Archetypes:")
    for arch, status in summary['archetype_statuses'].items():
        _print_success(f"{arch}: {status}")
    print(f"\n  Predictions: {summary['predictions']}")
    print(f"  Scenarios: {summary['scenarios']}")
    print(f"  Wargame: {'Yes' if summary['has_wargame'] else 'No'}")
    print(f"  Decision Room: {'Yes' if summary['has_decision_room'] else 'No'}")
    print(f"  Evidence Graph: {'Yes' if summary['has_evidence_graph'] else 'No'}")
    print(f"\n  Exported files:")
    for fmt, path in summary['exported_files'].items():
        _print_success(f"{fmt}: {path}")

    if session.report and session.report.executive_summary:
        print(f"\n  Key Findings:")
        for f in session.report.executive_summary.key_findings[:5]:
            _print_info(f)
        print(f"\n  Recommendation: {session.report.executive_summary.recommendation}")
        print(f"\n  Next Steps:")
        for step in session.report.executive_summary.next_steps[:3]:
            _print_info(step)

    print(f"\n{'=' * 60}")
    print(f"  Strategy Studio — 25x better than McKinsey")
    print(f"{'=' * 60}\n")

    return session


def analyze(
    company_name: str,
    industry: str = "",
    competitors: str = "",
    historical: str = "",
    evidence: str = "",
    output_dir: str = "",
    formats: str = "md,json",
    visual: bool = True,
) -> StrategySession:
    """Run a non-interactive strategy analysis."""
    comp_list = [c.strip() for c in competitors.split(",") if c.strip()] if competitors else []
    ev_list = [e.strip() for e in evidence.split(",") if e.strip()] if evidence else []

    hist_data = {}
    if historical:
        for item in historical.split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                try:
                    hist_data[k.strip()] = float(v.strip())
                except ValueError:
                    pass

    out = Path(output_dir) if output_dir else None
    fmt_list = [f.strip() for f in formats.split(",")]

    session = run_strategy_session(
        company_name=company_name,
        industry=industry,
        competitors=comp_list,
        historical_data=hist_data,
        evidence_sources=ev_list,
        output_dir=out,
        export_formats=fmt_list,
    )

    if visual and session.report:
        viz_dir = (out or Path(f"out/sessions/{company_name.lower().replace(' ', '_')}")) / "visuals"
        generate_full_strategy_visuals(session.report, viz_dir)

    return session


def batch_analyze(
    input_csv: str,
    output_dir: str = "out/batch",
    formats: str = "md,json",
) -> list[dict]:
    """Run batch strategy analysis from a CSV file.

    CSV columns: company_name, industry, competitors, context, evidence
    """
    import csv

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    with open(input_csv, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    _print_header(f"BATCH STRATEGY ANALYSIS — {len(rows)} companies")

    for i, row in enumerate(rows):
        company = row.get("company_name", f"Company_{i}")
        industry = row.get("industry", "")
        competitors = [c.strip() for c in row.get("competitors", "").split(";") if c.strip()]
        context = row.get("context", "")
        evidence = [e.strip() for e in row.get("evidence", "").split(";") if e.strip()]

        _print_step(i + 1, len(rows), f"Analyzing {company}...")

        try:
            session = run_strategy_session(
                company_name=company,
                industry=industry,
                context=context,
                competitors=competitors,
                evidence_sources=evidence,
                output_dir=output_dir / company.lower().replace(" ", "_"),
                export_formats=[f.strip() for f in formats.split(",")],
            )
            summary = session.summary()
            results.append({"company": company, "status": "success", "summary": summary})
            _print_success(f"{company}: {summary['archetype_statuses']}")
        except Exception as e:
            results.append({"company": company, "status": "error", "error": str(e)})
            print(f"  ✗ {company}: {e}")

    # Write batch report
    report_path = output_dir / "batch_report.json"
    report_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    _print_success(f"Batch report: {report_path}")

    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="strategy-studio",
        description="Strategy Studio — 25x better than McKinsey",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Wizard
    wizard_parser = subparsers.add_parser("wizard", help="Interactive strategy session")
    wizard_parser.set_defaults(func=lambda args: wizard())

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a company")
    analyze_parser.add_argument("company", help="Company name")
    analyze_parser.add_argument("--industry", default="", help="Industry")
    analyze_parser.add_argument("--competitors", default="", help="Comma-separated competitors")
    analyze_parser.add_argument("--historical", default="", help="Historical data (key=val,key=val)")
    analyze_parser.add_argument("--evidence", default="", help="Evidence sources (comma-separated)")
    analyze_parser.add_argument("--output", default="", help="Output directory")
    analyze_parser.add_argument("--formats", default="md,json", help="Output formats")
    analyze_parser.add_argument("--no-visual", action="store_true", help="Skip visual generation")
    analyze_parser.set_defaults(func=lambda args: analyze(
        company_name=args.company,
        industry=args.industry,
        competitors=args.competitors,
        historical=args.historical,
        evidence=args.evidence,
        output_dir=args.output,
        formats=args.formats,
        visual=not args.no_visual,
    ))

    # Batch
    batch_parser = subparsers.add_parser("batch", help="Batch analysis from CSV")
    batch_parser.add_argument("input_csv", help="Input CSV file")
    batch_parser.add_argument("--output", default="out/batch", help="Output directory")
    batch_parser.add_argument("--formats", default="md,json", help="Output formats")
    batch_parser.set_defaults(func=lambda args: batch_analyze(
        input_csv=args.input_csv,
        output_dir=args.output,
        formats=args.formats,
    ))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()