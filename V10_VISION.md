# RIG Strategy Studio — V10 Vision & Archon CLI Harness Design

## V10: The Complete Intelligence Platform

### What V10 Is

V10 is not just a strategy tool — it's an **autonomous intelligence operating system** that combines:

1. **Prediction Studio** — Probabilistic forecasting with proper scoring
2. **Creativity Engine** — 5000 questions from 100 personas, triple diamond process
3. **Narrative Engine** — McKinsey-style story generation
4. **Innovation Methodology Engine** — Ingested frameworks from 20+ firms
5. **Evidence Engine** — Source scoring, contradiction detection, LakeOS integration
6. **Decision Room** — MCDA, sensitivity analysis, tornado diagrams
7. **Synthesis Pipeline** — Cross-archetype consensus, meta-analysis
8. **Output Studio** — Board decks, reports, HTML presentations
9. **Calibration Engine** — Brier scoring, Bayesian updating, learning loops
10. **Missing-Info Engine** — OmniScout integration, active learning

### The Archon Harness Pattern

Each process runs through an **Archon harness** — a deterministic wrapper that:
- Validates inputs against the RIG lattice (L-D-A-step coordinates)
- Routes to the correct archetype (A1/A2/A3/A4)
- Enforces quality gates at each step
- Produces auditable ProofPackets
- Tracks calibration and learning

```
┌─────────────────────────────────────────────────────────────────┐
│                     ARCHON HARNESS                               │
│                                                                  │
│  Input → Validate → Route → Execute → Gate → Output → Learn     │
│                                                                  │
│  Lattice: L{level}-D{diamond}-A{mode}-{step}                    │
│  Modes:   A1 (deterministic) | A2 (hybrid) | A3 (agent) | A4 (free) │
│  Steps:   I1 → Q1 → R → S → Q2 → P → I2                        │
│  Gates:   Evidence | Falsification | Proof | Calibration         │
└─────────────────────────────────────────────────────────────────┘
```

### CLI Command Structure

```
rig-studio                          # Main entry point
├── analyze <company>               # Full strategy analysis
│   ├── --ticker <symbol>           # Enable real data
│   ├── --industry <industry>       # Set industry context
│   ├── --competitors <list>        # Set competitors
│   ├── --mode <A1|A2|A3|A4>        # Archetype mode
│   ├── --output <dir>              # Output directory
│   └── --formats <md|json|html>    # Output formats
│
├── predict <question>              # Prediction Studio
│   ├── --deadline <date>           # Resolution deadline
│   ├── --category <cat>            # Forecast category
│   ├── --market-prior              # Include market priors
│   ├── --ensemble                  # Run full ensemble
│   └── --calibrate                 # Show calibration data
│
├── create <brief>                  # Creativity Engine
│   ├── --personas <n>              # Number of personas (default 100)
│   ├── --questions <n>             # Questions per persona (default 50)
│   ├── --diamond <1|2>             # Double diamond stage
│   ├── --methodologies <list>      # Innovation frameworks to apply
│   └── --tournament                # Run tournament mode
│
├── narrative <analysis>            # Narrative Engine
│   ├── --style <mckinsey|bcg|ideo> # Narrative style
│   ├── --length <short|medium|full># Output length
│   └── --audience <exec|board|team># Target audience
│
├── decide <options>                # Decision Room
│   ├── --criteria <list>           # Decision criteria
│   ├── --weights <list>            # Criteria weights
│   ├── --sensitivity               # Run sensitivity analysis
│   └── --tornado                   # Generate tornado diagram
│
├── evidence <claim>                # Evidence Engine
│   ├── --sources <n>               # Min evidence sources
│   ├── --contradictions            # Check contradictions
│   └── --score                     # Score evidence quality
│
├── forecast <signal>               # Signal → Forecast pipeline
│   ├── --signals <file>            # Signal input file
│   ├── --base-rate                 # Include base rate
│   ├── --bayesian                  # Show Bayesian update trail
│   └── --missing-info              # Generate collection tasks
│
├── calibrate                       # Calibration Engine
│   ├── --show                      # Show calibration curves
│   ├── --brier                     # Show Brier scores
│   ├── --compare                   # Compare human vs model vs market
│   └── --postmortem <forecast_id>  # Generate postmortem
│
├── synthesize                      # Synthesis Pipeline
│   ├── --archetypes <list>         # Archetypes to synthesize
│   ├── --consensus                 # Cross-archetype consensus
│   └── --meta                      # Meta-analysis
│
├── present                         # Output Studio
│   ├── --input <analysis>          # Input analysis
│   ├── --format <html|md|pptx>     # Output format
│   ├── --theme <dark|light>        # Presentation theme
│   └── --open                      # Auto-open in browser
│
├── batch <csv>                     # Batch processing
│   ├── --output <dir>              # Output directory
│   ├── --workers <n>               # Parallel workers
│   └── --resume                    # Resume interrupted batch
│
├── wizard                          # Interactive wizard
│   ├── --mode <full|quick|custom>  # Wizard mode
│   └── --save <file>               # Save session state
│
├── status                          # System status
│   ├── --forecasts                 # Active forecasts
│   ├── --calibration               # Calibration summary
│   ├── --evidence                  # Evidence graph summary
│   └── --health                    # System health check
│
└── config                          # Configuration
    ├── --set <key> <value>         # Set config value
    ├── --get <key>                 # Get config value
    ├── --list                      # List all config
    └── --reset                     # Reset to defaults
```

### Harness Execution Flow

```
User Command
    ↓
┌──────────────────┐
│  Input Validator  │ ← Lattice coordinate validation
│  (deterministic)  │ ← BMS mode + IQRSQPI step
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Archetype Router │ ← A1/A2/A3/A4 selection
│  (deterministic)  │ ← Based on mode + confidence
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Step Executor    │ ← I1→Q1→R→S→Q2→P→I2
│  (mode-dependent) │ ← Deterministic or agent or hybrid
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Quality Gate     │ ← Evidence | Falsification | Proof
│  (deterministic)  │ ← UNKNOWN policy if insufficient
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Output Builder   │ ← MD + JSON + HTML + ProofPacket
│  (deterministic)  │ ← Audit trail included
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Calibration Log  │ ← Brier/log scores tracked
│  (deterministic)  │ ← Model weights updated
└──────────────────┘
```

### V10 Modules to Build

| Module | File | Description |
|--------|------|-------------|
| CLI Harness | `cli_harness.py` | Main CLI with Archon pattern |
| Lattice Router | `lattice_router.py` | L-D-A-step coordinate routing |
| Archetype Executor | `archetype_executor.py` | Step execution with mode selection |
| Quality Gates | `quality_gates.py` | Evidence/falsification/proof gates |
| Proof Packet | `proof_packet.py` | Audit trail generation |
| Calibration Tracker | `calibration_tracker.py` | Brier/log score tracking |
| Missing Info Engine | `missing_info_engine.py` | OmniScout task generation |
| Creativity Engine | `creativity_engine.py` | Persona questions + tournament |
| Narrative Engine | `narrative_engine.py` | Story generation from analysis |
| Innovation Ingestion | `innovation_ingestion.py` | Framework scraping + absorption |
| Ensemble Manager | `ensemble_manager.py` | Multi-model forecast aggregation |
| Output Builder | `output_builder.py` | MD/JSON/HTML/PPTX generation |

### Implementation Priority

**Phase 1 (This Session):**
1. CLI Harness — Main entry point with all commands
2. Lattice Router — Coordinate-based routing
3. Archetype Executor — Step execution framework
4. Quality Gates — Evidence/falsification/proof

**Phase 2 (Next Session):**
5. Creativity Engine — Persona questions + tournament
6. Narrative Engine — Story generation
7. Innovation Ingestion — Framework scraping
8. Missing Info Engine — OmniScout integration

**Phase 3 (Future):**
9. Calibration Tracker — Full learning loop
10. Ensemble Manager — Multi-model aggregation
11. Output Builder — PPTX generation
12. V10 Singularity — Self-evolving methodology engine
"""
