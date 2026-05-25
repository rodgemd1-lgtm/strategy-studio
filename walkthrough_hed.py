#!/usr/bin/env python3
"""HED Engagement — Step by Step Walkthrough"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

console.print(Panel(
    "[bold blue]HED ENGAGEMENT — STEP BY STEP WALKTHROUGH[/]\n\n"
    "Hydro Electronic Devices, Inc. | Hartford, WI\n"
    "224 employees | ~$60M revenue | 35+ years in rugged CAN-based controls\n"
    "Defense contractor | CMMC Level 2 | Family-owned | Made in USA",
    title="[bold]THE FIRM[/]",
    border_style="blue",
    box=box.DOUBLE,
))

console.print()
console.print("[bold]━━━ STEP 1: THE SITUATION ━━━[/]")
console.print("""
Microsoft Copilot deployed to office employees. VP of Operations (Gijs Zomer)
tasked with increasing AI literacy for FY26 Hoshin Kanri strategy deployment.

[bold red]The wound:[/] They had the tool (Copilot) and the mandate (Hoshin Kanri).
What they lacked was a [bold]roadmap for value[/].
The owner was pushing for "more" — but more of what?
""")

console.print()
console.print("[bold]━━━ STEP 2: THE EXAMINATION (QRSQPI Intelligence Process) ━━━[/]")
console.print("""
100 structured audience questions. 8 data collections (~975KB raw).
Leadership mapping. Competitive landscape. Financial modeling.

[bold green]What the analysis revealed:[/]
  • Mobile vehicle controls market: [bold]$10.4B, 7.8% CAGR[/]
  • [bold]No incumbent[/] in the AI-native sub-segment
  • Parker Hannifin: IoT but [bold]no edge-AI controller in production[/]
  • Bosch Rexroth + Trackunit: OTA services but [bold]no defense qualification[/]
  • Grayhill (most direct competitor): [bold]no public AI strategy[/]

[bold yellow]HED's structural advantage (unrecognized):[/]
  1. CMMC Level 2 compliance (mandatory for all DoD primes by Nov 10, 2026)
  2. 35-year installed base
  3. Defense-qualified portfolio
  4. Family-owned governance (long-term decision horizon)
  5. Hoshin Kanri methodology

[bold]Comparable transaction:[/] Helios Technologies (formerly Sun Hydraulics)
  2016: Hydraulic manufacturer begins acquiring electronics
  FY25: Electronics grew from $0 → [bold]$298M[/] (35.5% of revenue)
  Revenue: $523M → $839M, gross margins held in low 30s

[bold]Quality score:[/] 30/30 on McKinsey internal quality rubric
[bold]Top risk:[/] Engineering team resistance (probability 0.25)
""")

console.print()
console.print("[bold]━━━ STEP 3: THE SYSTEM — FORGE (6 Tiers) ━━━[/]")

forge = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
forge.add_column("Tier", style="bold", width=10)
forge.add_column("Name", width=18)
forge.add_column("Function", width=50)
forge.add_row("Solo", "Forge Solo", "Personal AI copilot for VP of Operations")
forge.add_row("Team", "Forge Team", "Shared knowledge graph (15+ engineers)")
forge.add_row("Vault", "Forge Vault", "35 years tribal knowledge, captured + queryable")
forge.add_row("Edge", "Forge Edge", "AI-native features shipped in vehicle controllers")
forge.add_row("Sight", "Forge Sight", "Competitive intelligence dashboard")
forge.add_row("Blueprint", "Forge Blueprint", "Full AI strategy + governance framework")
console.print(forge)

console.print()
console.print("[bold]━━━ STEP 4: THE APPROACH — 3 PHASES ━━━[/]")

phases = Table(box=box.ROUNDED, show_lines=True)
phases.add_column("Phase", style="bold", width=14)
phases.add_column("Months", width=12)
phases.add_column("Key Deliverables", width=45)
phases.add_column("Mike's Role", width=20)
phases.add_row(
    "[green]1 — Foundation[/]",
    "1–3",
    "Discovery audit, AI literacy, Solo deploy, pilot workflow, CMMC governance, Day-90 ROI",
    "2 days/week on-site",
)
phases.add_row(
    "[yellow]2 — Activation[/]",
    "4–6",
    "Full-team rollout (25 engineers), knowledge graph, firmware feature, 3 champions",
    "1–2 days/week + async",
)
phases.add_row(
    "[red]3 — Hand-Off[/]",
    "7–9",
    "Ownership transfer, team certification, production-or-nothing review, Y1 projections",
    "Monthly advisory",
)
console.print(phases)

console.print()
console.print("[bold]━━━ STEP 5: THE PREDICTION ━━━[/]")

pred = Table(box=box.SIMPLE)
pred.add_column("System", style="bold")
pred.add_column("Score", justify="center")
pred.add_column("Gate", justify="center")
pred.add_row("[green]MiroFish (quality)[/]", "[green]82/100[/]", ">=75 PASS")
pred.add_row("[green]MilkyWay (deviation)[/]", "[green]4.2σ[/]", ">=3.0σ PASS")
pred.add_row("[green]MiroShark (success)[/]", "[green]0.82[/]", ">=0.80 PASS")
pred.add_row("[green]Swarm Consensus[/]", "[green]0.78[/]", ">=0.65 PASS")
console.print(pred)

console.print()
console.print("[bold]━━━ STEP 6: ENGAGEMENT TERMS ━━━[/]")

terms = Table(box=box.SIMPLE)
terms.add_column("Item", style="bold")
terms.add_column("Value", style="cyan")
terms.add_row("Total Investment", "$357,500")
terms.add_row("Fixed Fee", "$185,000")
terms.add_row("Retainer (mo 1-6)", "$22,000/month")
terms.add_row("Retainer (mo 7-9)", "$13,500/month")
terms.add_row("Signing (50% fixed)", "$92,500")
terms.add_row("End Phase 1 (50% fixed)", "$92,500")
terms.add_row("Payment Terms", "Net 30, Wire/ACH")
terms.add_row("Late Fee", "1.5%/month after 30 days")
console.print(terms)

console.print()
console.print(Panel(
    "[bold red]RIG GUARANTEE: Production or nothing.[/]\n\n"
    "If Month 9 doesn't show measurable ROI against defined metrics, RIG will "
    "either make it right at no additional cost or terminate with a prorated "
    "refund of unearned fees. HED retains all work product produced to date.",
    title="Guarantee",
    border_style="red",
    box=box.DOUBLE,
))

console.print()
console.print("[bold]━━━ STEP 7: SUCCESS METRICS ━━━[/]")

metrics = Table(box=box.ROUNDED, show_lines=True)
metrics.add_column("Metric", style="bold", width=35)
metrics.add_column("Baseline", width=15)
metrics.add_column("Target", width=20)
metrics.add_column("Method", width=25)
metrics.add_row("Doc cycle time", "TBD (Phase 1)", "30-50% reduction", "10 doc sample audit")
metrics.add_row("AI literacy adoption", "0%", "80%+ leadership", "Survey + daily usage")
metrics.add_row("Production workflows live", "0", "4+", "System inventory")
metrics.add_row("Customer AI feature shipped", "No", "Yes", "Firmware version control")
metrics.add_row("Internal champions trained", "0", "3+", "Certification + observation")
metrics.add_row("Day-90 ROI", "TBD", "Positive", "Comparable to baseline")
console.print(metrics)

console.print()
console.print("[bold]━━━ STEP 8: THE DEVIATION ENGINE (10 Moves) ━━━[/]")

moves = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
moves.add_column("Move", style="bold", width=8)
moves.add_column("Description", width=80)
moves.add_row("Move 1", "Wound naming: '18 months from being locked out of defense channel'")
moves.add_row("Move 2", "Mirror before mechanism: '3 product lines, none productized as intelligence'")
moves.add_row("Move 3", "Named mechanism: NVIS Gate, Helios Curve, Five-Layer Compounding Loop")
moves.add_row("Move 4", "Source weights on every number: 'Bosch+Trackunit · SW 0.45 · press release Apr 2025'")
moves.add_row("Move 5", "Confidence tiers (H/M/L badge) on every recommendation")
moves.add_row("Move 6", "Falsification criteria named explicitly")
moves.add_row("Move 7", "Qualification — three disqualifiers")
moves.add_row("Move 8", "Open-loop close")
moves.add_row("Move 9", "Banned-phrase discipline: no 'would love to', 'happy to', 'world-class'")
moves.add_row("Move 10", "Mechanism over feature: not 'AI assistant' but 'VP query → synthesis → 3-min decisions → compounds'")
console.print(moves)

console.print()
console.print("[bold]━━━ STEP 9: CATEGORY ENGINES (3 Product Lines) ━━━[/]")

engines = Table(box=box.ROUNDED, show_lines=True)
engines.add_column("Engine", style="bold", width=20)
engines.add_column("Product", width=15)
engines.add_column("Flywheel", width=20)
engines.add_column("Target Revenue", width=15)
engines.add_row("[green]Engine 1 (+5σ)[/]", "Control Modules", "Data flywheel", "$42M")
engines.add_row("[yellow]Engine 2 (+5σ)[/]", "Displays", "Capability flywheel", "$26M")
engines.add_row("[red]Engine 3 (+5σ)[/]", "Keypads", "Adoption flywheel", "$14M")
engines.add_row("[bold]TOTAL[/]", "", "", "[bold]$82M[/]")
console.print(engines)

console.print()
console.print("[bold]━━━ STEP 10: COMPETITIVE INTELLIGENCE ━━━[/]")

comp = Table(box=box.ROUNDED, show_lines=True)
comp.add_column("Threat", style="bold", width=25)
comp.add_column("Level", width=12)
comp.add_column("Key Fact", width=45)
comp.add_row("[red]Parker Hannifin[/]", "Tier 1 (6-12mo)", "Public AI strategy, capital to acquire tier-2")
comp.add_row("[yellow]Bosch Rexroth[/]", "Tier 2 (12-24mo)", "3.5M connected assets, CMMC trailing 12-24mo")
comp.add_row("[green]Grayhill/APEM[/]", "Tier 3 (24-36mo)", "No edge-AI narrative, smaller R&D")
console.print(comp)

console.print()
console.print("[bold]━━━ STEP 11: RIG OS (Extracted from HED) ━━━[/]")

rig = Table(box=box.SIMPLE)
rig.add_column("Layer", style="bold", width=15)
rig.add_column("RIG Equivalent", width=25)
rig.add_column("Mirrors HED's", width=20)
rig.add_row("RIG Solo", "Mike's personal AI", "Forge Solo")
rig.add_row("RIG Team", "Engagement knowledge graph", "Forge Team")
rig.add_row("RIG Vault", "Tribal knowledge engine", "Forge Vault")
rig.add_row("RIG Edge", "AI in demo product", "Forge Edge")
rig.add_row("RIG Sight", "Competitive intel agent", "Forge Sight")
console.print(rig)

console.print()
console.print(Panel(
    "[bold]RIG Core Doctrine[/]\n\n"
    "RIG sells the difference between [bold]looking like you're using AI[/] and "
    "[bold]operating an AI substrate[/].\n\n"
    "The substrate is owned by the client, not the vendor. "
    "The vendor is the instrument that builds it, not the system that owns it.",
    title="Doctrine",
    border_style="blue",
    box=box.DOUBLE,
))

console.print()
console.print("[bold]━━━ ARTIFACTS PRODUCED ━━━[/]")

artifacts = Table(box=box.SIMPLE)
artifacts.add_column("Category", style="bold", width=20)
artifacts.add_column("Artifacts", width=60)
artifacts.add_row("Strategy + Intel", "50MB+ raw scrape, 47KB master strategy, 30/30 McKinsey-bar, competitive intel")
artifacts.add_row("Live Demo", "hed-forge.vercel.app (14-panel SPA), V2 functional (gated), strategy deck site")
artifacts.add_row("PDFs", "One-Page Memo, Transformation Proposal (9pg), Strategy Deck (12pg), Per-Product (24 SKUs)")
artifacts.add_row("SOW", "RIG-2026-HED-001, $357K, 9 months, 3 phases, production guarantee")
artifacts.add_row("Process", "10-phase master flow, QRSQPI, Deviation Engine V3, 200+ questions")
console.print(artifacts)

console.print()
console.print("[dim]Source: ~/strategy-studio/docs/hed/ | GitHub: github.com/rodgemd1-lgtm/strategy-studio[/]")
