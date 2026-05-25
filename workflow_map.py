#!/usr/bin/env python3
"""RIG Workflow Map — All Python Scripts and Processes"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box

console = Console()

console.print(Panel(
    "[bold blue]RIG WORKFLOW MAP — ALL PYTHON SCRIPTS & PROCESSES[/]\n\n"
    "Complete inventory of workflows, engines, and automation across the RIG stack.",
    border_style="blue",
    box=box.DOUBLE,
))

# ── SECTION 1: RIG COMMANDS (113 modules) ──
console.print()
console.print("[bold]━━━ 1. RIG COMMANDS (113 modules) ━━━[/]")
console.print("[dim]Location: services/rig_commands/[/]")

commands = Table(box=box.ROUNDED, show_lines=True)
commands.add_column("Category", style="bold", width=20)
commands.add_column("Commands", width=70)

commands.add_row(
    "Core Engine",
    "rig_agent, rig_audit, rig_anchor, rig_bayes, rig_bell, rig_breaker, rig_casimir, rig_chorus, rig_clonal, rig_coli, rig_collider, rig_critical, rig_cuckoo, rig_darwin, rig_deviate, rig_echo, rig_forge, rig_glyph, rig_graviton, rig_horizon, rig_humpback, rig_kelvin, rig_loop, rig_lumen, rig_lumina, rig_parsec, rig_pauli, rig_prism, rig_rebound, rig_reef, rig_referral, rig_root, rig_score, rig_shield, rig_slime, rig_sovereign, rig_surprise, rig_swarm, rig_tunnel, rig_viscera, rig_volt, rig_wellspring, rig_witness, rig_xray, rig_zeropoint",
)
commands.add_row(
    "Studios",
    "rig_app_studio, rig_design_studio, rig_engineering_studio, rig_gtm_studio, rig_instagram_studio, rig_linkedin_studio, rig_product_studio, rig_proposal-studio, rig_research-studio, rig_strategy-studio, rig_website-studio",
)
commands.add_row(
    "Operations",
    "rig_buildout_orchestration, rig_business_analyst, rig_business_intelligence, rig_capability_foundry, rig_chief_os, rig_competitive_intel, rig_content_strategist, rig_devops_automator, rig_financial_analyst, rig_forecast_studio, rig_gtm_strategist, rig_intake, rig_kanban, rig_memory_lens, rig_omniscout, rig_ops_studio, rig_product_manager, rig_prospect, rig_rag, rig_route, rig_security, rig_security_engineer, rig_senior_developer, rig_studios, rig_ui_designer, rig_ux_researcher",
)
commands.add_row(
    "Infrastructure",
    "rig_albatross, rig_asset_scraper, rig_backend_architect, rig_cockpit, rig_comfyui, rig_fleet_management, rig_infrastructure, rig_lattice, rig_mesh, rig_oss_upgrade_scan, rig_patch, rig_portal, rig_spend_audit, rig_web_buildout, rig_website, rig_workflow",
)
commands.add_row(
    "Support",
    "aionui_operator, rig_help, rig_models, rig_monte_carlo, rig_status, _codegen, _cost_ledger, _hermes_swarm, _router, _runner, _template",
)
console.print(commands)

# ── SECTION 2: RIG ARCHETYPES (28 files) ──
console.print()
console.print("[bold]━━━ 2. RIG ARCHETYPES (28 files) ━━━[/]")
console.print("[dim]Location: rig/archetypes/ — 4 modes × 7 IQRSQPI steps[/]")

archetypes = Table(box=box.ROUNDED, show_lines=True)
archetypes.add_column("Mode", style="bold", width=12)
archetypes.add_column("Steps (I1→I2)", width=70)

for mode_id, mode_name, color in [("A1", "Python Only", "green"), ("A2", "Hybrid", "yellow"), ("A3", "Agent Bounded", "orange"), ("A4", "LLM Agent Free", "red")]:
    steps = []
    for i, step in enumerate(["I1_intent", "Q1_question", "R_research", "S_solution", "Q2_quality", "P_proof", "I2_integrate"]):
        cell = f"{mode_id}.{i+1}_{step}"
        steps.append(cell)
    archetypes.add_row(f"[{color}]{mode_id} {mode_name}[/]", " → ".join(steps))

console.print(archetypes)

# ── SECTION 3: LATTICE ENGINE ──
console.print()
console.print("[bold]━━━ 3. LATTICE ENGINE (8 modules) ━━━[/]")
console.print("[dim]Location: rig-systems-engineering-studio/lattice/[/]")

lattice = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
lattice.add_column("Module", style="bold", width=25)
lattice.add_column("Purpose", width=60)
lattice.add_row("generator.py", "Generates all 588 BuildCards → viz/lattice_index.json")
lattice.add_row("build_card.py", "BuildCard data class + serialization")
lattice.add_row("altitude_semantics.py", "7 altitudes: L1 Artifacts → L7 Vision")
lattice.add_row("step_semantics.py", "21 diamond-step semantics (Triple Diamond)")
lattice.add_row("question_bank.py", "30 questions per cell (588 × 30 = 17,640)")
lattice.add_row("score.py", "BMS scoring: raw + adj_failure + adj_volume + adj_altitude")
lattice.add_row("render.py", "Renders per-cell Markdown pages (3,087 pages)")
lattice.add_row("integrations/dv_engines.py", "40 deviation engines integration")
lattice.add_row("integrations/predictions.py", "MiroShark + MilkyWay prediction engines")
console.print(lattice)

# ── SECTION 4: RUNTIME SERVICES ──
console.print()
console.print("[bold]━━━ 4. RUNTIME SERVICES (5 services) ━━━[/]")
console.print("[dim]Location: rig/runtime/ — production services[/]")

runtime = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
runtime.add_column("Service", style="bold", width=20)
runtime.add_column("Purpose", width=65)
runtime.add_row("llm.py", "MeshClient — LM Studio + LiteLLM + Anthropic, round-robin 8 nodes")
runtime.add_row("approval.py", "AionUIClient — SQLite queue + auto-approve fallback")
runtime.add_row("audit.py", "AuditStore — Postgres/SQLite append-only audit trail")
runtime.add_row("predictions.py", "MiroShark + MilkyWay — logistic + 3-forecaster ensemble")
runtime.add_row("scheduler.py", "ReviewScheduler — APScheduler-backed SQLite jobstore")
runtime.add_row("server.py", "FastAPI on :8765 — UI + /approval + /audit + /reviews")
runtime.add_row("config.py", "RuntimeConfig — env-driven paths under ~/.rig/")
console.print(runtime)

# ── SECTION 5: KEY WORKFLOW SCRIPTS ──
console.print()
console.print("[bold]━━━ 5. KEY WORKFLOW SCRIPTS ━━━[/]")
console.print("[dim]Location: scripts/ — top-level automation[/]")

scripts = Table(box=box.ROUNDED, show_lines=True)
scripts.add_column("Script", style="bold", width=35)
scripts.add_column("Purpose", width=55)

key_scripts = [
    ("ai_intel_feed.py", "AI intelligence feed ingestion"),
    ("aop-evaluate.py", "AOP evaluation engine"),
    ("auto-apply-jobs.py", "Automated job application"),
    ("automation_reporter.py", "Automation status reporting"),
    ("batch_harvest.py", "Batch content harvesting"),
    ("build_native_paperclip_company.py", "Paperclip company builder"),
    ("chase_ui_level_scrape.py", "Chase UI level scraping"),
    ("check-mcp-status.py", "MCP server status check"),
    ("chrome-job-controller.py", "Chrome browser job controller"),
    ("deploy_fleet.py", "Fleet deployment automation"),
    ("dream_weaver_studio.py", "Dream Weaver studio"),
    ("dspy-optimize.py", "DSPy optimization"),
    ("export_agents_to_paperclip.py", "Export agents to Paperclip"),
    ("firehose_consumer.py", "Firehose event consumer"),
    ("firehose_setup.py", "Firehose setup"),
    ("fleet_manager.py", "Fleet management"),
    ("goal_daily_checkin.py", "Daily goal check-in"),
    ("health-check.py", "System health check"),
    ("ingest_harvested_content.py", "Content ingestion"),
    ("jake_auto_updater.py", "Jake auto-updater"),
    ("jake_company_ops.py", "Jake company operations"),
    ("jake_morning_debrief.py", "Jake morning debrief"),
    ("knowledge_ingest.py", "Knowledge base ingestion"),
    ("pull_recall.py", "Pull recall.it cards via API"),
    ("live_mesh_smoke.py", "Live mesh smoke test (A1-A4 × D1-D3)"),
    ("weekly_brief.py", "Weekly brief generation"),
    ("phronema.py", "Phronema unified store (7 stores)"),
    ("composio_bridge.py", "Composio bridge (6 publishers)"),
    ("sow_generator.py", "SOW generation"),
]
for name, purpose in key_scripts:
    scripts.add_row(name, purpose)

console.print(scripts)

# ── SECTION 6: IQRSQPI PROCESS ──
console.print()
console.print("[bold]━━━ 6. IQRSQPI PROCESS (10-Phase Master Flow) ━━━[/]")

iqrsqpi = Table(box=box.ROUNDED, show_lines=True)
iqrsqpi.add_column("Phase", style="bold", width=25)
iqrsqpi.add_column("Duration", width=12)
iqrsqpi.add_column("Output", width=50)

phases = [
    ("Phase 0: Pre-Flight", "5 min", "Skills loaded, brain_search, Susan RAG check"),
    ("Phase 1: Deep Research", "30-90 min", "10-target parallel scrape, 1-2MB+ raw data"),
    ("Phase 2: QRSQPI Analysis", "60-120 min", "100 Q's, 12-part dossier, strategy V3"),
    ("Phase 3: Deviation Engine V3", "30-60 min", "12 stages, ethical clearance, ≥+5 score"),
    ("Phase 4: McKinsey-Bar 30", "20-40 min", "30 criteria scored, target 27+/30"),
    ("Phase 5: Website + AI Demo", "60-180 min", "DESIGN.md, clone, AI tabs, Vercel deploy"),
    ("Phase 6: 200+ Questions", "30-60 min", "100 audience + 100 client questions"),
    ("Phase 7: Pricing & Engagement", "20-30 min", "3-tier pricing, SOW generation"),
    ("Phase 8: Proposal + SOW", "20-30 min", "Same-day-send package"),
    ("Phase 9: Onboarding", "15 min", "Engagement letter, kickoff call"),
]
for phase, duration, output in phases:
    iqrsqpi.add_row(phase, duration, output)

console.print(iqrsqpi)

# ── SECTION 7: FLEET MESH ──
console.print()
console.print("[bold]━━━ 7. FLEET MESH (6 nodes) ━━━[/]")

fleet = Table(box=box.ROUNDED, show_lines=True)
fleet.add_column("Node", style="bold", width=25)
fleet.add_column("IP", width=18)
fleet.add_column("RAM", width=10)
fleet.add_column("Models", width=40)
fleet.add_column("Tier", width=20)

fleet.add_row("rig-256gb-mac-studio", "100.91.39.12", "256 GB", "18 models (qwen3.6-27b ×8, hermes-4-405b)", "a4_strategic")
fleet.add_row("rig-96gb-mac-studio-1", "100.102.142.84", "96 GB", "8 models (qwen3.5-35b, hermes-4-70b)", "a3_agent")
fleet.add_row("rig-48gb-mbp", "100.76.209.22", "48 GB", "18 models (qwen3.6-27b ×8, gemma-4-31b)", "a2_synth")
fleet.add_row("rig-36gb-mac-studio-1", "100.89.143.27", "36 GB", "18 models (qwen3.6-27b ×8, qwen3-8b)", "a2_judge")
fleet.add_row("rig-28gb-mbp", "100.103.237.24", "28 GB", "2 models (qwen3-8b, nomic-embed)", "a1_fast")
fleet.add_row("blackwell", "100.67.126.117", "GPU", "vLLM :8000 (qwen2.5-coder-32b)", "coding")
console.print(fleet)

# ── SECTION 8: VERIFICATION COMMANDS ──
console.print()
console.print("[bold]━━━ 8. VERIFICATION COMMANDS ━━━[/]")

verify = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
verify.add_column("Command", style="bold", width=60)
verify.add_column("Purpose", width=40)
verify.add_row("curl localhost:1234/v1/models | jq .data[].id", "Check mesh models")
verify.add_row("python3 -c 'from rig.runtime import healthcheck; ...'", "Health check")
verify.add_row("RIG_AIONUI_AUTO_APPROVE=1 python3 scripts/live_mesh_smoke.py", "Full smoke test")
verify.add_row("sqlite3 ~/.rig/audit.sqlite 'SELECT archetype, count(*)...'", "Audit rows by archetype")
verify.add_row("sqlite3 ~/.rig/scheduler.sqlite 'SELECT status, count(*)...'", "Scheduled reviews")
verify.add_row("sqlite3 ~/.rig/miroshark.sqlite 'SELECT count(*) FROM forecasts'", "Forecasts count")
verify.add_row("uvicorn rig.runtime.server:app --host 0.0.0.0 --port 8765", "Start AionUI server")
console.print(verify)

console.print()
console.print("[dim]Source: ~/strategy-studio/ | GitHub: github.com/rodgemd1-lgtm/strategy-studio[/]")
