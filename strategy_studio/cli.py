"""Click CLI for the Strategy Studio."""
from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.json import JSON as RichJSON

from strategy_studio.core.types import Evidence, Option, WargameScenario, Forecast, FalsificationPacket
from strategy_studio.engines.b29_synthesize import synthesize_evidence
from strategy_studio.engines.b36_wargame import run_wargame
from strategy_studio.engines.b34_predict import build_forecast
from strategy_studio.engines.b33_falsify import falsify_claim

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


@click.group()
@click.option("--verbose", is_flag=True, default=False)
def cli(verbose: bool):
    """Strategy Studio — RIG B-engine CLI."""
    pass


@cli.command()
@click.option("--input", "raw_input", required=True, help="Raw evidence text (pipe-friendly).")
@click.option("--format", "output_format", default="md", type=click.Choice(["json","yaml","md"]), help="Output format.")
def synthesize(raw_input: str, output_format: str):
    """Synthesize evidence into ranked options."""
    evidence = [
        Evidence(claim=raw_input, source="cli", confidence_score=0.8, evidence_count=1)
    ]
    result = synthesize_evidence(evidence)
    data = {
        "question": result.question,
        "winner_index": result.winner_index,
        "options": [
            {"label": o.label, "score": o.score, "rationale": o.rationale}
            for o in result.options
        ],
    }
    console.print(_fmt(data, output_format))


@cli.command()
@click.option("--scenario", required=True, help="Wargame scenario description.")
@click.option("--actors", required=True, help="Comma-separated list of actors.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json","yaml","md"]), help="Output format.")
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
        table.add_row(r.actor, r.move, r.response, r.impact, f"{r.probability:.2%}")
    console.print(table)


@cli.command()
@click.option("--question", required=True, help="Forecast question.")
@click.option("--data", default="{}", help="Historical data as JSON dict mapping period names to values.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json","yaml","md"]), help="Output format.")
def forecast(question: str, data: str, output_format: str):
    """Build a forecast from historical data."""
    try:
        hist = json.loads(data)
    except Exception:
        hist = {}
    result = build_forecast(question, hist)
    data_out = {
        "question": result.question,
        "prediction": result.prediction,
        "confidence_low": result.confidence_low,
        "confidence_high": result.confidence_high,
        "confidence": result.confidence,
        "method": result.method,
        "evidence_count": result.evidence_count,
    }
    console.print(_fmt(data_out, output_format))


@cli.command()
@click.option("--claim", required=True, help="Claim to falsify.")
@click.option("--evidence-file", default=None, help="Path to JSON evidence array.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json","yaml","md"]), help="Output format.")
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
        "claim": result.claim,
        "intent": result.intent.value,
        "disproof_test": result.disproof_test,
        "verdict": result.verdict,
    }
    console.print(_fmt(data, output_format))


@cli.command()
@click.option("--limit", default=10, type=int, help="Max rows to show.")
@click.option("--format", "output_format", default="md", type=click.Choice(["json","yaml","md"]), help="Output format.")
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


if __name__ == "__main__":
    cli()
