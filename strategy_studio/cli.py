"""Click CLI for the Strategy Studio."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.json import JSON as RichJSON
from rich.panel import Panel

from strategy_studio.core.types import Evidence, Option
from strategy_studio.engines import (
    synthesize_evidence,
    falsify_claim,
    build_forecast,
    run_wargame,
    calculate_consensus_delta,
    assess_risks,
    size_market,
    position_competitively,
    plan_timeline,
    allocate_budget,
    assess_impact,
)

console = Console()


def _fmt(data: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)
    if fmt == "yaml":
        try:
            import yaml
            return yaml.safe_dump(data, sort_keys=False)
        except Exception:
            return json.dumps(data, indent=2, default=str)
    # markdown
    lines = []
    for k, v in data.items():
        lines.append(f"**{k}**: {v}")
    return "\n".join(lines)


def _make_sample_evidence(raw: str) -> list[Evidence]:
    """Create sample evidence list from raw text."""
    return [
        Evidence(source_uri="cli:input", content_hash=f"cli-{hash(raw) % 10000}", confidence="H", citations=[]),
        Evidence(source_uri="cli:context", content_hash=f"cli-ctx-{hash(raw) % 10000}", confidence="M", citations=[]),
    ]


def _make_sample_options() -> list[Option]:
    """Create sample options for demo/testing."""
    return [
        Option(id="opt-1", title="Primary Strategy", description="Build proprietary platform with network effects", score=0.85, risks=["High capital requirement", "Execution complexity"]),
        Option(id="opt-2", title="Partnership Play", description="Partner with existing platform to accelerate distribution", score=0.72, risks=["Partner dependency", "Margin compression"]),
        Option(id="opt-3", title="Niche Focus", description="Dominate a specific segment before expanding", score=0.68, risks=["Limited TAM", "Slow growth"]),
    ]


@click.group()
@click.option("--verbose", is_flag=True, default=False)
def cli(verbose: bool):
    """Strategy Studio — RIG B-engine CLI."""
    pass


# ── B29: Synthesize ─────────────────────────────────────────────────────────

@cli.command()
@click.option("--input", "raw_input", required=True, help="Raw evidence text (pipe-friendly).")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def synthesize(raw_input: str, output_format: str):
    """Synthesize evidence into ranked options."""
    evidence = _make_sample_evidence(raw_input)
    result = synthesize_evidence(evidence, title=raw_input[:60])
    data = {
        "rationale": result.rationale,
        "recommendation": result.recommendation.title if result.recommendation else None,
        "options": [
            {"id": o.id, "title": o.title, "score": o.score, "risks": o.risks}
            for o in result.options
        ],
    }
    console.print(_fmt(data, output_format))


# ── B31: Consensus Delta ────────────────────────────────────────────────────

@cli.command()
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def consensus(output_format: str):
    """Calculate consensus delta between new research and existing synthesis."""
    evidence = _make_sample_evidence("sample consensus check")
    result = calculate_consensus_delta(evidence)
    console.print(_fmt(result, output_format))


# ── B33: Falsify ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--claim", required=True, help="Claim to falsify.")
@click.option("--evidence-file", default=None, help="Path to JSON evidence array.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def falsify(claim: str, evidence_file: str | None, output_format: str):
    """Falsify a claim using disproof patterns."""
    evidence = []
    if evidence_file:
        try:
            with open(evidence_file) as fh:
                raw = json.load(fh)
            evidence = [Evidence(**item) for item in raw]
        except Exception:
            pass
    result = falsify_claim(claim, evidence)
    data = {
        "belief": result.belief,
        "disproof_test": result.disproof_test,
        "pass_criteria": result.pass_criteria,
        "status": result.status,
    }
    console.print(_fmt(data, output_format))


# ── B34: Forecast ───────────────────────────────────────────────────────────

@cli.command()
@click.option("--question", required=True, help="Forecast question.")
@click.option("--data", default="{}", help="Historical data as JSON dict mapping period names to values.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def forecast(question: str, data: str, output_format: str):
    """Build a forecast from historical data."""
    try:
        hist = json.loads(data)
    except Exception:
        hist = {}
    result = build_forecast(question, hist)
    data_out = {
        "variable": result.variable,
        "prediction": result.prediction,
        "confidence_interval": list(result.confidence_interval),
        "method": result.method,
    }
    console.print(_fmt(data_out, output_format))


# ── B36: Wargame ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--scenario", required=True, help="Wargame scenario description.")
@click.option("--actors", required=True, help="Comma-separated list of actors.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def wargame(scenario: str, actors: str, output_format: str):
    """Run wargame for a scenario against a set of actors."""
    actor_list = [a.strip() for a in actors.split(",") if a.strip()]
    results = run_wargame(scenario, actor_list)
    table = Table(title=f"Wargame: {scenario}")
    table.add_column("Actor", style="cyan")
    table.add_column("Move", style="magenta")
    table.add_column("RIG Response", style="green")
    table.add_column("Impact", style="yellow")
    table.add_column("Probability", justify="right")
    for r in results:
        table.add_row(r.actor, r.move, r.rig_response, r.impact, f"{r.probability:.2%}")
    console.print(table)


# ── B37: Risk Assessment ────────────────────────────────────────────────────

@cli.command("risk")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def risk_assessment(output_format: str):
    """Assess risks for sample strategic options."""
    options = _make_sample_options()
    results = assess_risks(options)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    elif output_format == "yaml":
        try:
            import yaml
            console.print(yaml.safe_dump(results, sort_keys=False))
        except Exception:
            console.print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            table = Table(title=f"Risk: {r['option_id']} ({r['overall_risk_level'].upper()})")
            table.add_column("Category", style="cyan")
            table.add_column("Severity", style="red")
            table.add_column("Likelihood", justify="right")
            table.add_column("Score", justify="right")
            for risk in r["risks"]:
                table.add_row(risk["category"], risk["severity"], f"{risk['likelihood']:.0%}", str(risk["risk_score"]))
            console.print(table)


# ── B40: Market Sizing ──────────────────────────────────────────────────────

@cli.command("market")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def market_sizing(output_format: str):
    """Size markets for sample strategic options."""
    options = _make_sample_options()
    results = size_market(options)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    elif output_format == "yaml":
        try:
            import yaml
            console.print(yaml.safe_dump(results, sort_keys=False))
        except Exception:
            console.print(json.dumps(results, indent=2, default=str))
    else:
        table = Table(title="Market Sizing")
        table.add_column("Option", style="cyan")
        table.add_column("Segment", style="magenta")
        table.add_column("TAM", justify="right")
        table.add_column("SAM", justify="right")
        table.add_column("SOM", justify="right")
        table.add_column("CAGR", justify="right")
        table.add_column("Conf", justify="center")
        for r in results:
            table.add_row(
                r["option_id"], r["segment"],
                f"${r['tam']:,.0f}", f"${r['sam']:,.0f}", f"${r['som']:,.0f}",
                f"{r['cagr']}%", r["confidence"],
            )
        console.print(table)


# ── B43: Competitive Positioning ────────────────────────────────────────────

@cli.command("position")
@click.option("--competitors", default="Competitor A,Competitor B,Competitor C", help="Comma-separated competitors.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def competitive_position(competitors: str, output_format: str):
    """Position options competitively against competitors."""
    options = _make_sample_options()
    comp_list = [c.strip() for c in competitors.split(",") if c.strip()]
    results = position_competitively(options, comp_list)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            console.print(Panel(
                f"**{r['positioning_statement']}**\n\n"
                f"Moat Score: {r['moat_score']} | "
                f"Differentiation: {r['differentiation_score']} | "
                f"Intensity: {r['competitive_intensity']}\n\n"
                f"**Recommendation:** {r['recommended_positioning']}",
                title=f"Position: {r['option_id']}",
            ))


# ── B44: Timeline Planning ──────────────────────────────────────────────────

@cli.command("timeline")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def timeline_planning(output_format: str):
    """Plan implementation timelines for sample options."""
    options = _make_sample_options()
    results = plan_timeline(options)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    else:
        for t in results:
            table = Table(title=f"Timeline: {t['option_id']} ({t['duration_weeks']}w, {t['complexity_level']})")
            table.add_column("Phase", style="cyan")
            table.add_column("Week", justify="right")
            table.add_column("Deliverable", style="green")
            for m in t["milestones"]:
                table.add_row(m["phase"], str(m["week"]), m["deliverable"])
            console.print(table)


# ── B45: Budget Allocation ──────────────────────────────────────────────────

@cli.command("budget")
@click.option("--total", default=1000000.0, help="Total budget in USD.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def budget_allocation(total: float, output_format: str):
    """Allocate budget across sample strategic options."""
    options = _make_sample_options()
    results = allocate_budget(options, total)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    else:
        table = Table(title=f"Budget Allocation (${total:,.0f})")
        table.add_column("Rank", justify="right")
        table.add_column("Option", style="cyan")
        table.add_column("Budget", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Est. Cost", justify="right")
        table.add_column("Gap", justify="right")
        table.add_column("ROI", justify="right")
        for r in results:
            gap_style = "red" if r["funding_gap"] < 0 else "green"
            table.add_row(
                str(r["priority_rank"]), r["option_id"],
                f"${r['budget']:,.0f}", f"{r['allocation_percentage']:.1f}%",
                f"${r['estimated_cost']:,.0f}",
                f"${r['funding_gap']:,.0f}",
                f"{r['roi_estimate']:.2f}",
            )
        console.print(table)


# ── B46: Impact Assessment ──────────────────────────────────────────────────

@cli.command("impact")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def impact_assessment(output_format: str):
    """Assess impact for sample strategic options."""
    options = _make_sample_options()
    results = assess_impact(options)
    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    else:
        table = Table(title="Impact Assessment")
        table.add_column("Option", style="cyan")
        table.add_column("Financial", justify="right")
        table.add_column("Strategic", justify="right")
        table.add_column("Operational", justify="right")
        table.add_column("Overall", justify="right")
        table.add_column("Category", style="magenta")
        for r in results:
            table.add_row(
                r["option_id"],
                f"{r['financial_impact']:.2f}",
                f"{r['strategic_impact']:.2f}",
                f"{r['operational_impact']:.2f}",
                f"{r['overall_impact_score']:.2f}",
                r["impact_category"],
            )
        console.print(table)


# ── Audit ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", default=10, type=int, help="Max rows to show.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def audit(limit: int, output_format: str):
    """Show recent audit rows."""
    rows = [
        {"id": f"audit-{i}", "intent": "synthesize", "payload_summary": f"payload-{i}", "result_summary": "ok"}
        for i in range(min(limit, 5))
    ]
    if output_format in ("json", "yaml"):
        console.print(_fmt({"rows": rows}, output_format))
    else:
        table = Table(title="Recent Audit Rows")
        table.add_column("ID", style="cyan")
        table.add_column("Intent", style="magenta")
        table.add_column("Payload", style="yellow")
        table.add_column("Result", style="green")
        for r in rows:
            table.add_row(r["id"], r["intent"], r["payload"], r["result"])
        console.print(table)


# ── Full Pipeline ───────────────────────────────────────────────────────────

@cli.command("full")
@click.option("--company", required=True, help="Company name.")
@click.option("--competitors", default="", help="Comma-separated competitors.")
@click.option("--budget", default=1000000.0, help="Total budget for allocation.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json", "yaml", "md"]), help="Output format.")
def full_pipeline(company: str, competitors: str, budget: float, output_format: str):
    """Run full B-engine pipeline: synthesize → wargame → risk → market → position → timeline → budget → impact."""
    options = _make_sample_options()
    comp_list = [c.strip() for c in competitors.split(",") if c.strip()] if competitors else ["Competitor A", "Competitor B"]

    console.print(f"\n[bold]═══ Strategy Studio: {company} ═══[/bold]\n")

    # B29: Synthesize
    evidence = _make_sample_evidence(company)
    syn = synthesize_evidence(evidence, title=f"Strategy for {company}")
    console.print(f"[bold]B29 Synthesis:[/bold] {syn.rationale}")
    console.print(f"  Winner: {syn.recommendation.title if syn.recommendation else 'N/A'}")

    # B36: Wargame
    wg = run_wargame(f"{company} market entry", comp_list)
    console.print(f"\n[bold]B36 Wargame:[/bold] {len(wg)} scenarios")
    for w in wg[:3]:
        console.print(f"  {w.actor}: {w.move[:60]}...")

    # B37: Risk
    risks = assess_risks(options)
    console.print(f"\n[bold]B37 Risk:[/bold]")
    for r in risks:
        console.print(f"  {r['option_id']}: {r['overall_risk_level']} ({r['overall_risk_score']})")

    # B40: Market
    markets = size_market(options)
    console.print(f"\n[bold]B40 Market:[/bold]")
    for m in markets:
        console.print(f"  {m['option_id']}: TAM=${m['tam']:,.0f}, SAM=${m['sam']:,.0f} ({m['confidence']})")

    # B43: Position
    positions = position_competitively(options, comp_list)
    console.print(f"\n[bold]B43 Position:[/bold]")
    for p in positions:
        console.print(f"  {p['option_id']}: moat={p['moat_score']}, diff={p['differentiation_score']}")

    # B44: Timeline
    timelines = plan_timeline(options)
    console.print(f"\n[bold]B44 Timeline:[/bold]")
    for t in timelines:
        console.print(f"  {t['option_id']}: {t['duration_weeks']}w ({t['complexity_level']})")

    # B45: Budget
    allocs = allocate_budget(options, budget)
    console.print(f"\n[bold]B45 Budget (${budget:,.0f}):[/bold]")
    for a in allocs:
        console.print(f"  #{a['priority_rank']} {a['option_id']}: ${a['budget']:,.0f} ({a['allocation_percentage']:.1f}%)")

    # B46: Impact
    impacts = assess_impact(options)
    console.print(f"\n[bold]B46 Impact:[/bold]")
    for i in impacts:
        console.print(f"  {i['option_id']}: {i['overall_impact_score']:.2f} ({i['impact_category']})")

    console.print(f"\n[bold green]═══ Pipeline complete ═══[/bold green]")


if __name__ == "__main__":
    cli()


def main():
    """Entry point for the strategy-studio CLI."""
    cli()


def wizard_cmd():
    """Run the interactive strategy session wizard."""
    from strategy_studio.cli_wizard import wizard
    wizard()


def analyze_cmd(
    company: str,
    ticker: str = "",
    industry: str = "",
    competitors: str = "",
    output: str = "",
    formats: str = "md,json",
    no_visual: bool = False,
):
    """Run a complete strategy analysis on a company."""
    from strategy_studio.cli_wizard import analyze
    session = analyze(
        company_name=company,
        ticker=ticker,
        industry=industry,
        competitors=competitors,
        output_dir=output,
        formats=formats,
        visual=not no_visual,
    )
    if session.report:
        print(f"\n✓ Strategy analysis complete: {session.report.title}")
        print(f"  Recommendation: {session.report.executive_summary.recommendation}")
        print(f"  Confidence: {session.report.executive_summary.confidence}")
        if session.exported_paths:
            for fmt, path in session.exported_paths.items():
                print(f"  {fmt.upper()}: {path}")
    else:
        print("✗ Analysis failed to generate report")


# Register additional commands
cli.add_command(click.Command("wizard", callback=wizard_cmd, help="Interactive strategy session"))
