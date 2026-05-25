#!/usr/bin/env python3
"""A1-A4 Archetype Workflow — Terminal Visualization

Rich-based interactive display of the 28 archetypes, lattice structure,
workflows, and escalation paths. No browser needed.

Usage:
    python3 viz_archetypes.py
    python3 viz_archetypes.py --mode A1
    python3 viz_archetypes.py --step S
    python3 viz_archetypes.py --lattice
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.tree import Tree
from rich import box

console = Console()

# ── Data ──

MODES = {
    "A1": {
        "name": "Python Only",
        "color": "green",
        "fill": "#3b82f6",
        "stroke": "#1e3a5f",
        "desc": "Deterministic. Regex, YAML, Pydantic. No model in decision path.",
        "cost": "$0 – $0.001",
        "stack": ["pydantic", "jinja2", "httpx", "sqlalchemy", "MCP clients", "Haiku/MLX"],
        "gates": ["physics_33", "cognitive_12", "anti_slop", "rig_l_lite"],
        "approval": "conditional",
        "escalate_to": "A2.1 (UNKNOWN intent)",
    },
    "A2": {
        "name": "Hybrid",
        "color": "yellow",
        "fill": "#60a5fa",
        "stroke": "#1e3a5f",
        "desc": "Deterministic first, schema-constrained LLM assist. Python validates all output.",
        "cost": "$0.01 – $0.30",
        "stack": ["LangGraph", "Sonnet (in nodes)", "NeMo Guardrails", "Pydantic + Outlines", "Temporal/Prefect"],
        "gates": ["physics_31", "cognitive_07_voltage", "nature_22", "anti_slop", "rig_l"],
        "approval": "risk-classified conditional",
        "escalate_to": "A3.1 (confidence < 0.8 or gate fail)",
    },
    "A3": {
        "name": "Agent Bounded",
        "color": "orange",
        "fill": "#93c5fd",
        "stroke": "#1e3a5f",
        "desc": "LangGraph intent node. Bounded reasoning with declared rails. Tool allowlist enforced.",
        "cost": "$0.30 – $1.00",
        "stack": ["Sonnet/Opus agents", "Mem0", "MCP tool ring", "Promptfoo", "AionUI (72h signoff)"],
        "gates": ["physics_31", "physics_35_bell", "cognitive_01_rupture", "nature_22", "rig_l_composite"],
        "approval": "mandatory (72h timeout)",
        "escalate_to": "A4.1 (budget cap or quality fail)",
    },
    "A4": {
        "name": "LLM Agent Free",
        "color": "red",
        "fill": "#ddd6fe",
        "stroke": "#6d28d9",
        "desc": "Open-ended intent framing. Multiple competing interpretations. Downstream narrowing.",
        "cost": "$1 – $50 + 4h wall clock",
        "stack": ["CrewAI hierarchical", "Opus", "OR-Tools/PuLP", "Brier prediction loop", "AionUI (no timeout)"],
        "gates": ["physics_31", "physics_35_bell", "cognitive_01_rupture", "nature_22", "rig_l_composite"],
        "approval": "mandatory (no timeout) + post-mortem",
        "escalate_to": "Cannot escalate (top of lattice)",
    },
}

STEPS = {
    "I1": {"name": "Intent", "diamond": "D1/D2/D3", "semantic": "Divergent Intent Capture"},
    "Q1": {"name": "Question", "diamond": "D1/D2/D3", "semantic": "Open-Frame Questioning"},
    "R":  {"name": "Research", "diamond": "D1/D2/D3", "semantic": "Wide-Aperture Research"},
    "S":  {"name": "Solution", "diamond": "D1/D2/D3", "semantic": "Schema-Bound Synthesis"},
    "Q2": {"name": "Quality", "diamond": "D1/D2/D3", "semantic": "Coverage Check"},
    "P":  {"name": "Proof", "diamond": "D1/D2/D3", "semantic": "Exploration Receipt"},
    "I2": {"name": "Integrate", "diamond": "D1/D2/D3", "semantic": "Frame Selection"},
}

ALTITUDES = {
    "L1": {"name": "Artifacts", "horizon": "seconds", "volume": "1000s/day", "reversibility": "high"},
    "L2": {"name": "Tasks", "horizon": "minutes", "volume": "100s/day", "reversibility": "medium-high"},
    "L3": {"name": "Workflows", "horizon": "minutes-hours", "volume": "10s/day", "reversibility": "medium"},
    "L4": {"name": "Systems", "horizon": "hours-days", "volume": "few/day", "reversibility": "medium-low"},
    "L5": {"name": "Programs", "horizon": "days-weeks", "volume": "1/day", "reversibility": "low"},
    "L6": {"name": "Platforms", "horizon": "weeks-months", "volume": "1/week", "reversibility": "very low"},
    "L7": {"name": "Vision", "horizon": "months-quarters", "volume": "1/month", "reversibility": "identity-level"},
}

STEP_DETAIL = {
    ("A1", "I1"): "classify_intent() → Regex + YAML lookup → Pydantic validation → UNKNOWN on no match",
    ("A1", "Q1"): "generate_questions() → Template-driven → Schema-bound output → No LLM reasoning",
    ("A1", "R"):  "execute_research() → Deterministic scrape → Structured extraction → Claim-source binding",
    ("A1", "S"):  "build_solution() → Jinja2 templates → Schema validation → Retry on fail",
    ("A1", "Q2"): "run_quality_gates() → Physics + cognitive → Anti-slop checks → Pass/fail scoring",
    ("A1", "P"):  "create_proof_packet() → Content-addressed → Signed hash → Append-only audit",
    ("A1", "I2"): "integrate_output() → DAG-acyclic check → Approval policy → Dispatch or escalate",
    ("A2", "I1"): "classify_intent() → Deterministic pre-check → LLM assist if needed → Python validates",
    ("A2", "Q1"): "generate_questions() → 5+ distinct framings → Contrarian sources → Deviation >= +3σ",
    ("A2", "R"):  "execute_research() → Wide-aperture → 3+ epistemic tiers → Contradiction pairs",
    ("A2", "S"):  "build_solution() → 5-10 shapes → Falsifiable sketches → No mechanism lock",
    ("A2", "Q2"): "run_quality_gates() → Coverage check → Adversarial sweep → Anti-slop probing",
    ("A2", "P"):  "create_proof_packet() → Exploration receipt → Dead ends logged → Phronema-compatible",
    ("A2", "I2"): "integrate_output() → Frame selection → Human-in-loop L5+ → Deterministic shortlist",
    ("A3", "I1"): "classify_intent() → LangGraph node → Bounded reasoning → Tool allowlist",
    ("A3", "Q1"): "generate_questions() → Ambiguous/UNKNOWN → Frame collision → Orthodoxy rupture",
    ("A3", "R"):  "execute_research() → Agent-driven → MCP tool ring → Mem0 memory",
    ("A3", "S"):  "build_solution() → Sonnet/Opus nodes → Promptfoo eval → AionUI 72h signoff",
    ("A3", "Q2"): "run_quality_gates() → Physics 31+35 → Cognitive rupture → RIG-L composite",
    ("A3", "P"):  "create_proof_packet() → Mandatory 72h → Budget cap check → Quality gate",
    ("A3", "I2"): "integrate_output() → Escalate to A4.1 if budget/quality fail → Post-mortem required",
    ("A4", "I1"): "classify_intent() → Open-ended framing → Multiple interpretations → Premature certainty banned",
    ("A4", "Q1"): "generate_questions() → Novel/ambiguous → Competing frames → No narrowing yet",
    ("A4", "R"):  "execute_research() → CrewAI hierarchical → OR-Tools/PuLP → Brier prediction loop",
    ("A4", "S"):  "build_solution() → Opus reasoning → Multi-agent debate → AionUI no timeout",
    ("A4", "Q2"): "run_quality_gates() → Full physics stack → Bell inequality → Nature 22",
    ("A4", "P"):  "create_proof_packet() → No timeout → Mandatory post-mortem → Top of lattice",
    ("A4", "I2"): "integrate_output() → Cannot escalate → Block and resolve → Identity-level decision",
}


def show_full_grid():
    """Show the 4×7 archetype grid."""
    table = Table(
        title="A1 A2 A3 A4 — 28 Archetypes (4 BMS Modes × 7 IQRSQPI Steps)",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold blue",
    )

    # Header
    table.add_column("Mode", style="bold", width=12, justify="center")
    for step_id, step in STEPS.items():
        table.add_column(f"{step_id}\n{step['name']}", width=22, justify="center")

    # Rows
    for mode_id, mode in MODES.items():
        row = [f"[bold {mode['color']}]{mode_id}[/]\n{mode['name']}"]
        for step_id in STEPS:
            cell_id = f"{mode_id}.{list(STEPS.keys()).index(step_id) + 1}"
            detail = STEP_DETAIL.get((mode_id, step_id), "")
            # Truncate to first line
            first_line = detail.split("→")[0].strip() if "→" in detail else detail[:20]
            row.append(f"[{mode['color']}]{cell_id}[/]\n{first_line}")
        table.add_row(*row)

    console.print(table)


def show_mode_detail(mode_id: str):
    """Show detailed view of one mode."""
    mode = MODES[mode_id]

    # Header panel
    header = Panel(
        f"[bold]{mode['name']}[/]\n"
        f"[dim]{mode['desc']}[/]\n\n"
        f"Cost: [bold]{mode['cost']}[/]  |  "
        f"Approval: [bold]{mode['approval']}[/]  |  "
        f"Escalates to: [bold red]{mode['escalate_to']}[/]",
        title=f"[bold {mode['color']}]{mode_id}[/]",
        border_style=mode["color"],
        box=box.DOUBLE,
    )
    console.print(header)

    # Stack
    stack_table = Table(title="Tech Stack", box=box.SIMPLE, show_header=False, padding=(0, 2))
    stack_table.add_column("Stack", style="cyan")
    for s in mode["stack"]:
        stack_table.add_row(f"  • {s}")
    console.print(stack_table)

    # Quality Gates
    gates_table = Table(title="Quality Gates", box=box.SIMPLE, show_header=False, padding=(0, 2))
    gates_table.add_column("Gate", style="yellow")
    for g in mode["gates"]:
        gates_table.add_row(f"  ✓ {g}")
    console.print(gates_table)

    # Steps detail
    steps_table = Table(title="IQRSQPI Steps", box=box.ROUNDED, show_lines=True)
    steps_table.add_column("Step", style="bold", width=6)
    steps_table.add_column("Cell", width=8)
    steps_table.add_column("Function", width=30)
    steps_table.add_column("Key Operations", width=50)

    for step_id, step in STEPS.items():
        cell_id = f"{mode_id}.{list(STEPS.keys()).index(step_id) + 1}"
        detail = STEP_DETAIL.get((mode_id, step_id), "")
        parts = [p.strip() for p in detail.split("→")]
        func = parts[0] if parts else ""
        ops = " → ".join(parts[1:]) if len(parts) > 1 else ""
        steps_table.add_row(
            f"[bold {mode['color']}]{step_id}[/]",
            f"[{mode['color']}]{cell_id}[/]",
            func,
            ops,
        )

    console.print(steps_table)


def show_step_detail(step_id: str):
    """Show one step across all 4 modes."""
    step = STEPS[step_id]

    table = Table(
        title=f"Step {step_id} — {step['name']} ({step['semantic']})",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold blue",
    )
    table.add_column("Mode", style="bold", width=12, justify="center")
    table.add_column("Cell", width=8, justify="center")
    table.add_column("Implementation", width=60)
    table.add_column("Key Difference", width=30)

    for mode_id, mode in MODES.items():
        cell_id = f"{mode_id}.{list(STEPS.keys()).index(step_id) + 1}"
        detail = STEP_DETAIL.get((mode_id, step_id), "")

        # Determine key difference
        if mode_id == "A1":
            diff = "No LLM in decision path"
        elif mode_id == "A2":
            diff = "LLM assist, Python validates"
        elif mode_id == "A3":
            diff = "LangGraph + tool allowlist"
        else:
            diff = "Open-ended, multi-interpretation"

        table.add_row(
            f"[bold {mode['color']}]{mode_id}[/]",
            f"[{mode['color']}]{cell_id}[/]",
            detail,
            diff,
        )

    console.print(table)


def show_lattice():
    """Show the 3,087-cell lattice structure."""
    tree = Tree("[bold blue]RIG Lattice — 3,087 cells (7 × 21 × 21)[/]")

    for alt_id, alt in ALTITUDES.items():
        alt_tree = tree.add(
            f"[bold]{alt_id}: {alt['name']}[/] "
            f"[dim]({alt['horizon']} | {alt['volume']} | {alt['reversibility']})[/]"
        )
        # Show mode distribution
        for mode_id, mode in MODES.items():
            cells_per_mode = 3  # 3 diamonds per altitude per mode
            alt_tree.add(
                f"[{mode['color']}]{mode_id} {mode['name']}[/]: "
                f"{cells_per_mode} cells — {mode['cost']}"
            )

    console.print(tree)

    # Summary stats
    console.print()
    stats = Table(title="Lattice Statistics", box=box.SIMPLE)
    stats.add_column("Metric", style="bold")
    stats.add_column("Value", style="cyan")
    stats.add_row("Total Cells", "3,087 (7 × 21 × 21)")
    stats.add_row("Primary Coordinates", "84 (7 × 3 × 4)")
    stats.add_row("Process-Expanded Cells", "588 (84 × 7)")
    stats.add_row("Archetypes", "28 (4 modes × 7 steps)")
    stats.add_row("Altitudes", "7 (L1 Artifacts → L7 Vision)")
    stats.add_row("Diamonds", "3 (D1 Discovery, D2 Development, D3 Delivery)")
    stats.add_row("IQRSQPI Steps", "7 (I1, Q1, R, S, Q2, P, I2)")
    stats.add_row("Deviation Engines", "40")
    console.print(stats)


def show_escalation():
    """Show the escalation flow between modes."""
    console.print(Panel(
        "[bold]Escalation Flow[/]\n\n"
        "When an archetype cannot complete its work within its constraints,\n"
        "it escalates to the next higher mode.\n\n"
        "[green]A1 Python Only[/] → [yellow]A2 Hybrid[/] → [orange]A3 Agent Bounded[/] → [red]A4 LLM Agent Free[/]\n\n"
        "[dim]A4 is the top of the lattice — cannot escalate further.[/]",
        title="Mode Escalation",
        border_style="blue",
        box=box.DOUBLE,
    ))

    table = Table(title="Escalation Triggers", box=box.ROUNDED, show_lines=True)
    table.add_column("From", style="bold", width=15)
    table.add_column("Trigger", width=40)
    table.add_column("To", style="bold", width=15)

    table.add_row(
        "[green]A1[/]",
        "UNKNOWN intent, schema validation fail, no match",
        "[yellow]A2.1[/]",
    )
    table.add_row(
        "[yellow]A2[/]",
        "Confidence < 0.8, quality gate fail, LLM assist insufficient",
        "[orange]A3.1[/]",
    )
    table.add_row(
        "[orange]A3[/]",
        "Budget cap exceeded, quality fail, 72h timeout",
        "[red]A4.1[/]",
    )
    table.add_row(
        "[red]A4[/]",
        "Cannot escalate — top of lattice. Block and resolve.",
        "—",
    )

    console.print(table)


def show_iqrsqpi_flow():
    """Show the IQRSQPI flow within an archetype."""
    console.print(Panel(
        "[bold]IQRSQPI — The 7-Step Process Within Each Archetype[/]\n\n"
        "Every archetype (A1.1 through A4.7) follows the same 7-step process.\n"
        "The difference is HOW each step is executed (deterministic vs agentic).",
        title="IQRSQPI Flow",
        border_style="blue",
        box=box.DOUBLE,
    ))

    steps = [
        ("I1", "Intent", "Divergent Intent Capture", "What is this? Open the problem space."),
        ("Q1", "Question", "Open-Frame Questioning", "Generate widest set of questions before narrowing."),
        ("R", "Research", "Wide-Aperture Research", "Source diversity > depth. Contrarian sources."),
        ("S", "Solution", "Schema-Bound Synthesis", "Generate 5-10 distinct solution shapes."),
        ("Q2", "Quality", "Coverage Check", "Did we explore the actual problem space?"),
        ("P", "Proof", "Exploration Receipt", "Audit-grade record of what was explored + abandoned."),
        ("I2", "Integrate", "Frame Selection", "Narrow to 1-3 frames. Human-in-loop at L5+."),
    ]

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Step", style="bold", width=6, justify="center")
    table.add_column("Name", width=12)
    table.add_column("Semantic", width=25)
    table.add_column("Purpose", width=45)

    colors = ["green", "yellow", "orange", "red", "blue", "magenta", "cyan"]
    for i, (step_id, name, semantic, purpose) in enumerate(steps):
        table.add_row(
            f"[bold {colors[i]}]{step_id}[/]",
            name,
            semantic,
            purpose,
        )

    console.print(table)


def show_workflow_diagram():
    """Show the end-to-end workflow as a text diagram."""
    console.print(Panel(
        "[bold]RIG Systems Engineering — End-to-End Workflow[/]",
        border_style="blue",
        box=box.DOUBLE,
    ))

    diagram = """
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         INBOUND PAYLOAD                                     │
    │  (email, form, API call, scraper output, user message, build card)         │
    └──────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                      HERMES ROUTER (rig.hermes.router)                      │
    │                                                                              │
    │  1. Resolve coordinate: L × D × A × step                                   │
    │  2. Compute BMS: raw + adj_failure + adj_volume + adj_altitude              │
    │  3. Route to mode based on BMS score                                        │
    └──────┬──────────────┬──────────────┬──────────────┬─────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
    │  A1        │ │  A2        │ │  A3        │ │  A4        │
    │  Python    │ │  Hybrid    │ │  Agent     │ │  LLM       │
    │  Only      │ │            │ │  Bounded   │ │  Agent Free│
    │  BMS ≥ 0.75│ │  0.45-0.74 │ │  0.25-0.44 │ │  < 0.25    │
    └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         IQRSQPI × 7 STEPS                                   │
    │                                                                              │
    │  I1 Intent → Q1 Question → R Research → S Solution → Q2 Quality → P Proof → I2 Integrate  │
    │                                                                              │
    │  Each step: 40 DV engines score → physics/cognitive/nature gates → Brier    │
    └──────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         OUTPUT                                              │
    │                                                                              │
    │  ProofPacket → AuditStore (append-only) → Scheduled Reviews → AionUI       │
    │                                                                              │
    │  A4 only: cascade_to_lower_altitudes (L5 Programs, L4 Systems)             │
    └─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         ESCALATION                                          │
    │                                                                              │
    │  A1 ──UNKNOWN──→ A2 ──confidence<0.8──→ A3 ──budget/quality──→ A4         │
    │                                                                              │
    │  A4 = top of lattice. Cannot escalate. Block and resolve.                   │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    console.print(diagram)


def main():
    parser = argparse.ArgumentParser(description="A1-A4 Archetype Workflow Visualization")
    parser.add_argument("--mode", choices=["A1", "A2", "A3", "A4"], help="Show detail for one mode")
    parser.add_argument("--step", choices=["I1", "Q1", "R", "S", "Q2", "P", "I2"], help="Show one step across all modes")
    parser.add_argument("--lattice", action="store_true", help="Show lattice structure")
    parser.add_argument("--escalation", action="store_true", help="Show escalation flow")
    parser.add_argument("--iqrsqpi", action="store_true", help="Show IQRSQPI flow")
    parser.add_argument("--workflow", action="store_true", help="Show end-to-end workflow")
    args = parser.parse_args()

    if args.mode:
        show_mode_detail(args.mode)
    elif args.step:
        show_step_detail(args.step)
    elif args.lattice:
        show_lattice()
    elif args.escalation:
        show_escalation()
    elif args.iqrsqpi:
        show_iqrsqpi_flow()
    elif args.workflow:
        show_workflow_diagram()
    else:
        # Default: show everything
        show_workflow_diagram()
        console.print()
        show_iqrsqpi_flow()
        console.print()
        show_escalation()
        console.print()
        show_full_grid()


if __name__ == "__main__":
    main()
