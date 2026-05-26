"""
rig-strategy-studio CLI — Click-based entrypoint.

Usage:
    rig-strategy-studio --help
    rig-strategy-studio lattice --list-cells
    rig-strategy-studio lattice --execute L2-D1-I1 --query "Should we enter the B2B market?"
    rig-strategy-studio pipeline run --query "..."
    rig-strategy-studio cells --all-cards
    rig-strategy-studio cells --mode A1
    rig-strategy-studio bms --score --failure-cost 0.7 --reversibility 0.3 --altitude L5
    rig-strategy-studio orchestrator traverse --cell L2-D1 --query "..."
    rig-strategy-studio test --quick
"""
from __future__ import annotations

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from strategy_studio.rig_lattice import (
    Altitude, Diamond, IQRSQPIStep, BuildMode,
    LatticeCell, get_all_cells, get_all_cell_ids, get_archetype_cells,
    compute_bms, BMSScore, BMSCriteria,
    generate_build_card, generate_all_build_cards, BuildCard,
    ArchetypeExecutor, LatticeOrchestrator,
)
from strategy_studio.langgraph_executor import (
    LangGraphExecutor, setup_langsmith, BUDGETS,
)


console = Console()


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _mode_color(mode: str) -> str:
    return {"A1": "green", "A2": "yellow", "A3": "blue", "A4": "red"}.get(mode, "white")


def _status_color(status: str) -> str:
    return {"PASS": "green", "FAIL": "red", "ERROR": "red", "QUALITY_FAILED": "yellow", "UNKNOWN": "dim"}.get(status, "white")


def _print_banner():
    console.print("[bold cyan]RIG Strategy Studio[/bold cyan] — Lattice CLI")
    console.print(f"  A1-A4 archetypes | 147 cells | LangGraph executor | BMS scoring\n")


# ═══════════════════════════════════════════════════════════════════════════
# LATTICE GROUP
# ═══════════════════════════════════════════════════════════════════════════

@click.group("lattice")
def lattice():
    """RIG Lattice operations — cells, modes, BMS scoring."""
    pass


@lattice.command("list-cells")
@click.option("--altitude", "-a", type=str, help="Filter by altitude (L1-L7)")
@click.option("--mode", "-m", type=str, help="Filter by build mode (A1/A2/A3/A4)")
@click.option("--format", "-f", type=click.Choice(["table", "json", "ids"]), default="table")
def list_cells(altitude: Optional[str], mode: Optional[str], format: str):
    """List all 147 lattice cells or a filtered subset."""
    cells = get_all_cells()

    if altitude:
        cells = [c for c in cells if c.altitude.value == int(altitude.replace("L", ""))]
    if mode:
        cells = [c for c in cells if compute_bms(altitude=c.altitude).select_mode().value == mode]

    if format == "ids":
        for c in cells:
            console.print(c.cell_id)
        return

    table = Table(title=f"Lattice Cells ({len(cells)} total)")
    table.add_column("Cell ID", style="cyan")
    table.add_column("Alt", justify="center")
    table.add_column("Diamond", justify="center")
    table.add_column("Step", justify="center")
    table.add_column("Mode")
    table.add_column("BMS Raw", justify="right")
    table.add_column("Cost Band", style="dim")

    for cell in cells:
        bms = compute_bms(altitude=cell.altitude)
        mode_str = bms.select_mode().value
        row = [
            cell.cell_id,
            str(cell.altitude.value),
            cell.diamond.value,
            cell.step.value,
            mode_str,
            f"{bms.raw:.3f}",
            bms.select_mode().cost_band,
        ]
        # Color the mode column
        styled = [cell.cell_id, str(cell.altitude.value), cell.diamond.value, cell.step.value]
        styled.append(f"[{_mode_color(mode_str)}]{mode_str}[/{_mode_color(mode_str)}]")
        styled.extend([f"{bms.raw:.3f}", bms.select_mode().cost_band])
        table.add_row(*styled)

    console.print(table)


@lattice.command("bms")
@click.option("--failure-cost", type=float, default=0.5)
@click.option("--reversibility", type=float, default=0.5)
@click.option("--mechanism-clarity", type=float, default=0.5)
@click.option("--past-failure-rate", type=float, default=0.0)
@click.option("--data-volume", type=float, default=0.5)
@click.option("--altitude", "-a", type=str, default="L2", help="Preset from altitude level")
def compute_bms_cmd(failure_cost: float, reversibility: float, mechanism_clarity: float,
                     past_failure_rate: float, data_volume: float, altitude: str):
    """Compute BMS score for given criteria or preset from altitude."""
    alt_map = {
        "L1": Altitude.L1, "L2": Altitude.L2, "L3": Altitude.L3,
        "L4": Altitude.L4, "L5": Altitude.L5, "L6": Altitude.L6, "L7": Altitude.L7,
    }
    preset_alt = alt_map.get(altitude.upper())

    if preset_alt:
        bms = compute_bms(altitude=preset_alt)
    else:
        bms = compute_bms(failure_cost, reversibility, mechanism_clarity, past_failure_rate, data_volume)

    table = Table(title=f"BMS Score — altitude={altitude}")
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Raw Score", f"{bms.raw:.4f}")
    table.add_row("Adj Failure", f"{bms.adj_failure:+.4f}")
    table.add_row("Adj Volume", f"{bms.adj_volume:+.4f}")
    table.add_row("Adj Altitude", f"{bms.adj_altitude:+.4f}")
    table.add_row("Final Score", f"[bold]{bms.final:.4f}[/bold]")
    table.add_row("Selected Mode", f"[{_mode_color(bms.select_mode().value)}]{bms.select_mode().value}[/{_mode_color(bms.select_mode().value)}]")
    table.add_row("Cost Band", bms.select_mode().cost_band)
    table.add_row("Doctrine", bms.select_mode().description[:60] + "...")

    console.print(table)


@lattice.command("modes")
def list_modes():
    """List all four build modes with their doctrine."""
    table = Table(title="Build Modes")
    table.add_column("Mode", style="bold")
    table.add_column("Cost Band", justify="center")
    table.add_column("Cell Count", justify="right")
    table.add_column("Doctrine", style="dim")

    for mode in BuildMode:
        cells = get_archetype_cells(mode)
        table.add_row(
            mode.value,
            mode.cost_band,
            str(len(cells)),
            mode.description[:70],
        )
    console.print(table)


# ═══════════════════════════════════════════════════════════════════════════
# CELLS GROUP
# ═══════════════════════════════════════════════════════════════════════════

@click.group("cells")
def cells():
    """Build Card inspection and generation."""
    pass


@cells.command("all-cards")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def all_cards(output: str):
    """Generate all 147 Build Cards."""
    cards = generate_all_build_cards()

    if output == "json":
        data = [c.model_dump(mode="json") for c in cards]
        console.print(json.dumps(data, indent=2, default=str))
        return

    table = Table(title=f"Build Cards ({len(cards)} total)")
    table.add_column("Cell ID", style="cyan")
    table.add_column("Mode")
    table.add_column("Archetype", justify="center")
    table.add_column("Cost", style="dim")
    table.add_column("Escalation", style="dim")
    table.add_column("Tools", style="dim")

    for card in cards:
        mode_color = _mode_color(card.mode)
        table.add_row(
            card.cell_id,
            f"[{mode_color}]{card.mode}[/{mode_color}]",
            card.archetype_id,
            card.cost_band,
            card.escalation_target or "—",
            ", ".join(card.tools[:3]) + ("..." if len(card.tools) > 3 else ""),
        )
    console.print(table)


@cells.command("card")
@click.argument("cell_id")
def show_card(cell_id: str):
    """Show Build Card for a specific cell (e.g. L2-D1-I1)."""
    try:
        cell = LatticeCell.parse(cell_id)
        bms = compute_bms(altitude=cell.altitude)
        card = generate_build_card(cell, bms)
        console.print(f"\n[bold cyan]{card.cell_id}[/bold cyan] — {card.archetype_id}\n")
        console.print(f"  Mode: [bold]{card.mode}[/bold] | Cost: {card.cost_band}")
        console.print(f"  Doctrine: {card.doctrine}\n")
        console.print(f"  Tools: {', '.join(card.tools)}")
        console.print(f"  Validation: {', '.join(card.validation_criteria)}")
        console.print(f"  Escalation: {card.escalation_target or 'none'}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR GROUP
# ═══════════════════════════════════════════════════════════════════════════

@click.group("orchestrator")
def orchestrator():
    """Traverse lattice cells and the full IQRSQPI pipeline."""
    pass


@orchestrator.command("traverse")
@click.option("--cell", "-c", required=True, help="Cell ID (e.g. L2-D1-I1)")
@click.option("--query", "-q", required=True, help="Strategy query")
@click.option("--force-mode", "-m", type=str, help="Force build mode (A1/A2/A3/A4)")
def traverse_cell(cell: str, query: str, force_mode: Optional[str]):
    """Execute a single lattice cell."""
    orch = LatticeOrchestrator()
    mode = None
    if force_mode:
        mode = BuildMode(force_mode.upper())

    result = orch.traverse(cell, {"query": query}, mode=mode)

    status_color = _status_color(result.status)
    console.print(f"\n[bold]{result.archetype_id}[/bold] | [{status_color}]{result.status}[/{status_color}] | {result.step}")
    console.print(f"  Cell: {result.cell_id} | Mode: {result.mode}\n")
    console.print(f"  Output keys: {list(result.output.keys())}")

    if result.escalation_required:
        console.print(f"\n  [yellow]Escalation:[/yellow] {result.escalation_reason}")
    if result.duration_ms:
        console.print(f"  Duration: {result.duration_ms}ms")

    console.print(f"\n  Confidence: {result.confidence:.3f}")


@orchestrator.command("pipeline")
@click.option("--query", "-q", required=True, help="Strategy question")
@click.option("--altitude", "-a", type=int, default=2, help="Altitude level (1-7)")
@click.option("--diamond", "-d", type=int, default=1, help="Diamond (1-3)")
def run_pipeline(query: str, altitude: int, diamond: int):
    """Run the full 7-step IQRSQPI pipeline at given altitude/diamond."""
    from rich.panel import Panel

    orch = LatticeOrchestrator()
    alt = Altitude(altitude)
    dia = Diamond(f"D{diamond}")

    console.print(f"\n[bold cyan]Running pipeline:[/bold cyan] L{altitude}-D{diamond} | query: {query[:50]}...\n")

    results = orch.traverse_diamond(alt, dia, {"query": query})

    table = Table(title=f"IQRSQPI Pipeline — L{altitude}-D{diamond}")
    table.add_column("Step", style="bold")
    table.add_column("Cell", style="cyan")
    table.add_column("Mode")
    table.add_column("Status")
    table.add_column("Key Output", style="dim")

    for step in IQRSQPIStep:
        cell_id = f"L{altitude}-D{diamond}-{step.value}"
        r = results.get(cell_id)
        if r:
            mode_color = _mode_color(r.mode)
            status_color = _status_color(r.status)
            table.add_row(
                step.name,
                r.cell_id,
                f"[{mode_color}]{r.mode}[/{mode_color}]",
                f"[{status_color}]{r.status}[/{status_color}]",
                str(list(r.output.keys())[:3]),
            )

    console.print(table)
    console.print(f"\n  [dim]Total cells executed: {len(orch.executor.execution_log)}[/dim]")


@orchestrator.command("full")
@click.option("--query", "-q", required=True, help="Strategy question")
def run_full(query: str):
    """Run the full orchestrator pipeline end-to-end."""
    orch = LatticeOrchestrator()
    result = orch.run_full_pipeline({"query": query})

    console.print(f"\n[bold cyan]Full Pipeline Complete[/bold cyan]")
    console.print(f"  Cells executed: {result['cells_executed']}")
    console.print(f"  Steps covered: {', '.join(result['steps_covered'])}")


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTOR GROUP
# ═══════════════════════════════════════════════════════════════════════════

@click.group("executor")
def executor():
    """Direct archetype execution via LangGraph."""
    pass


@executor.command("a3")
@click.argument("step", type=str)
@click.option("--query", "-q", default="Should we enter the B2B SaaS market?", help="Strategy query")
def exec_a3(step: str, query: str):
    """Execute an A3 archetype step via LangGraph StateGraph."""
    step_enum = IQRSQPIStep(step.upper())
    ex = LangGraphExecutor()
    result = ex.execute_a3(step_enum, {"query": query})

    console.print(f"\n[bold]{result.archetype_id}[/bold] | {result.status}")
    console.print(f"  Output: {json.dumps(result.output, indent=2, default=str)}")


@executor.command("a4")
@click.argument("step", type=str)
@click.option("--query", "-q", default="Should we pivot to a PLG motion?", help="Strategy query")
def exec_a4(step: str, query: str):
    """Execute an A4 archetype step via LangGraph hierarchical graph."""
    step_enum = IQRSQPIStep(step.upper())
    ex = LangGraphExecutor()
    result = ex.execute_a4(step_enum, {"query": query})

    console.print(f"\n[bold]{result.archetype_id}[/bold] | {result.status}")
    console.print(f"  Output: {json.dumps(result.output, indent=2, default=str)}")


@executor.command("budgets")
def show_budgets():
    """Show A3/A4 budget limits."""
    table = Table(title="Budget Limits")
    table.add_column("Mode", style="bold")
    table.add_column("Cost", justify="right")
    table.add_column("Tool Calls", justify="right")
    table.add_column("Wall Clock", justify="right")

    for mode, budget in BUDGETS.items():
        table.add_row(mode, f"${budget['cost']}", str(budget["tool_calls"]), f"{budget['wall_clock_s']}s")
    console.print(table)


# ═══════════════════════════════════════════════════════════════════════════
# TEST COMMAND
# ═══════════════════════════════════════════════════════════════════════════

@click.command()
@click.option("--quick", is_flag=True, help="Run only lattice/BMS tests")
def test(quick: bool):
    """Run the test suite."""
    import subprocess
    if quick:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd="/Users/mikerodgers/strategy-studio",
        )
    else:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "strategy_studio/tests/", "-q"],
            cwd="/Users/mikerodgers/strategy-studio",
        )
    sys.exit(result.returncode)


# ═══════════════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════════════

@click.group("rig-strategy-studio")
@click.option("--setup-langsmith", is_flag=True, help="Configure LangSmith tracing")
@click.option("--langsmith-key", type=str, help="LangSmith API key")
def main(setup_langsmith: bool, langsmith_key: Optional[str]):
    """RIG Strategy Studio — A1-A4 archetype lattice with LangGraph execution."""
    _print_banner()

    if setup_langsmith:
        setup_langsmith(api_key=langsmith_key or None)
        console.print("[green]LangSmith tracing enabled[/green]\n")


main.add_command(lattice)
main.add_command(cells)
main.add_command(orchestrator)
main.add_command(executor)
main.add_command(test)


if __name__ == "__main__":
    main()