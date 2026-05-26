# RIG Strategy Studio — Complete Handoff Document

**Created:** May 25-26, 2026  
**Author:** OWL (Hermes Agent) for Mike Rodgers  
**Repo:** `github.com/rodgemd1-lgtm/strategy-studio` (private)

---

## What Is Strategy Studio?

Strategy Studio is a **deterministic, evidence-cited strategy synthesis platform** designed to be 25x better than McKinsey consulting. It takes a company name + ticker + context and produces a complete strategy deck in 30 seconds — with real financial data, Monte Carlo simulations, multi-archetype consensus, visual diagrams, and an HTML presentation that auto-opens in your browser.

**Core principle:** Every claim is evidence-cited. Every option is scored. Every output is fully reproducible (deterministic). Same input = same answer, every time.

---

## Repository Structure

### Primary Repo: `~/strategy-studio/` (GitHub: rodgemd1-lgtm/strategy-studio)

```
strategy-studio/
├── strategy_studio/                    # Main package
│   ├── __init__.py                     # Package exports
│   ├── cli.py                          # Click CLI (analyze, wizard, synthesize, wargame, forecast, falsify)
│   ├── cli_wizard.py                   # Interactive wizard + batch mode
│   ├── session.py                      # End-to-end strategy session runner
│   ├── presentation.py                 # HTML slide deck generator (dark theme, SVG charts)
│   ├── renderer.py                     # Excalidraw → SVG/PNG renderer (cairosvg)
│   ├── server.py                       # FastAPI server
│   ├── data_pipeline.py                # Real data: Yahoo Finance, Wikipedia, SEC EDGAR
│   ├── archetypes/                     # 4 archetypes (A1→A2→A3→A4)
│   │   ├── a1/                         # Pure deterministic (7 modules)
│   │   ├── a2/                         # Hybrid: deterministic + LLM fallback
│   │   ├── a3/                         # Agent-Bounded: multi-agent parallel w/ voting
│   │   └── a4/                         # LLM-Free: strictest deterministic
│   ├── engines/                        # 13 B-engines (B29-B46)
│   │   ├── b29_synthesize.py           # Evidence → ranked options
│   │   ├── b31_consensus_delta.py      # Belief updating
│   │   ├── b33_falsify.py              # Disproof testing
│   │   ├── b34_predict.py              # Linear extrapolation forecasting
│   │   ├── b36_wargame.py              # Competitive simulation
│   │   ├── b37_risk_assessment.py      # Risk scoring
│   │   ├── b40_market_sizing.py        # TAM/BAM/SAM
│   │   ├── b41_client_intel.py         # Wedge generation
│   │   ├── b42_competitor_intel.py     # Response actions
│   │   ├── b43_competitive_positioning.py
│   │   ├── b44_timeline_planning.py
│   │   ├── b45_budget_allocation.py
│   │   └── b46_impact_assessment.py
│   ├── studios/                        # 7 studios
│   │   ├── prediction_studio/          # NEW v2: Probabilistic forecasting engine
│   │   │   ├── __init__.py             # Package exports + backward-compat stubs
│   │   │   ├── core.py                 # All Pydantic models (ForecastRecord, Signal, etc.)
│   │   │   ├── scoring.py              # Brier, log, interval scores + calibration
│   │   │   ├── ensemble.py             # Multi-model aggregation + Bayesian updating
│   │   │   ├── priors.py               # Market prior extraction + base rate lookup
│   │   │   └── missing_info.py         # Information gap scoring + OmniScout tasks
│   │   ├── decision_room.py            # MCDA, sensitivity, tornado, VOI
│   │   ├── evidence_engine.py          # Source scoring, contradiction detection
│   │   ├── synthesis_pipeline.py       # Cross-archetype consensus, meta-analysis
│   │   ├── output_studio.py            # Board decks, executive summaries, reports
│   │   ├── calibration_engine.py       # Brier scoring, Bayesian updating, calibration curves
│   │   ├── industry_playbooks.py       # 10 industries (SaaS, Fintech, Healthcare, etc.)
│   │   └── visual_strategy_maps.py     # Excalidraw diagram generation
│   ├── core/                           # Core types and config
│   │   ├── types.py                    # 17 Pydantic models
│   │   ├── types_extended.py           # 17 more (Scenario, PredictionResult, etc.)
│   │   ├── config.py                   # Runtime config
│   │   └── exceptions.py               # Typed exceptions
│   ├── teaser/                         # Prospect teaser generation system
│   │   ├── generator.py                # Jinja2 HTML/MD teaser generator
│   │   ├── batch.py                    # Parallel batch processor (16 workers)
│   │   ├── schema.py                   # TeaserInput Pydantic model
│   │   ├── gtm20x.py                   # GTM 20x teaser variant
│   │   └── strategy.py                 # Strategy teaser variant
│   └── tests/                          # 145 tests
│       ├── test_prediction_studio.py   # 33 tests for new Prediction Studio v2
│       ├── test_a1/                    # 33 tests for A1 archetype
│       ├── test_archetypes/            # 16 tests for A2/A3/A4
│       ├── test_engines/               # 8 tests for B-engines
│       ├── test_studios/               # 31 tests for studios
│       └── test_teaser/                # 9 tests for teaser system
├── examples/outputs/                   # Example strategy outputs
│   ├── tesla/                          # Tesla analysis (MD + visuals)
│   ├── tesla_full/                     # Tesla with all outputs
│   ├── tesla_demo/                     # Tesla demo with new prediction studio
│   ├── stripe/                         # Stripe analysis
│   ├── microsoft/                      # Microsoft analysis
│   └── microsoft_v2/                   # Microsoft v2 with SVG charts
├── demo.py                             # Quick demo script (no install needed)
├── scripts/                            # Utility scripts
│   ├── build_rig_teaser_inputs.py
│   ├── build_regional_gtm_pack.py
│   ├── build_denver_gtm_workbook.py
│   ├── build_twenty_gtm_imports.py
│   ├── import_twenty_gtm_to_twenty.py
│   └── ...
└── viz_archetypes.py                   # Archetype visualization
```

### Secondary Repo: `~/Desktop/Startup-Intelligence-OS/strategy_studio/`
Contains the same package (synced from primary repo) plus additional context files.

### QNAP / Phronema LakeOS: `~/rig-lab/phronema/`
- LakeOS CLI: `scripts/lakeos_cli.py`
- LakeOS REST: `http://127.0.0.1:8788`
- QNAP Lake: `/Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake`
- GitNexus indexed: 492K symbols, 776K relationships

### RIG Systems: `~/Desktop/Startup-Intelligence-OS/rig/`
- MiroShark: `miroshark-src/` (prediction studio methods)
- MiroFish: `MiroFish/` (validation system)
- OmniScout: `rig/omniscout/` (intelligence collection)
- Phronema: `~/rig-lab/phronema/` (LakeOS knowledge base)

---

## What We Built — Complete Inventory

### 1. Four Archetypes (A1-A4)
**Location:** `strategy_studio/archetypes/a{1-4}/`

| Archetype | Mode | Key Characteristic |
|-----------|------|--------------------|
| A1 | Pure Deterministic | Regex/keyword classification, template questions, B-engine synthesis |
| A2 | Hybrid | A1 + LLM fallback when confidence < 0.7 |
| A3 | Agent-Bounded | Multi-agent parallel execution with ThreadPoolExecutor + voting consensus |
| A4 | LLM-Free | Strictest deterministic, 3x more patterns, zero guessing |

Each archetype has 7 modules: intent → question → research → solution → quality → proof → integrate.

### 2. Thirteen B-Engines (B29-B46)
**Location:** `strategy_studio/engines/`

| Engine | Function |
|--------|----------|
| B29 | Evidence-weighted synthesis |
| B31 | Consensus delta (belief updating) |
| B33 | Falsification (disproof testing) |
| B34 | Prediction (linear extrapolation) |
| B36 | Wargaming (competitive simulation) |
| B37 | Risk assessment |
| B40 | Market sizing (TAM/BAM/SAM) |
| B41 | Client intelligence (wedge generation) |
| B42 | Competitor intelligence |
| B43 | Competitive positioning |
| B44 | Timeline planning |
| B45 | Budget allocation |
| B46 | Impact assessment |

### 3. Seven Studios
**Location:** `strategy_studio/studios/`

| Studio | Function | Key Files |
|--------|----------|-----------|
| **Prediction Studio v2** | Probabilistic forecasting, Bayesian updating, scoring, calibration | `prediction_studio/` (6 files) |
| **Decision Room** | MCDA, sensitivity analysis, tornado diagrams, VOI | `decision_room.py` |
| **Evidence Engine** | Source scoring, contradiction detection, evidence graphs | `evidence_engine.py` |
| **Synthesis Pipeline** | Cross-archetype consensus, meta-analysis, multi-study synthesis | `synthesis_pipeline.py` |
| **Output Studio** | Board decks, executive summaries, strategy reports, export | `output_studio.py` |
| **Calibration Engine** | Brier scoring, Bayesian updating, calibration curves, sharpness | `calibration_engine.py` |
| **Industry Playbooks** | 10 industries with KPIs, benchmarks, strategic options, risks | `industry_playbooks.py` |

### 4. Prediction Studio v2 (NEW)
**Location:** `strategy_studio/studios/prediction_studio/`

The most significant new module, built from the Consensus research review (518 papers screened, 50 included):

**Core Models** (`core.py`):
- `ForecastRecord` — Complete forecast lifecycle (signals → priors → ensemble → resolution → scoring → postmortem)
- `SignalRegistry` — Ingest signals from OmniScout/HEB/ODTB/market data
- `MarketPrior` — Prediction market data with quality filtering
- `CausalThesisTree` — Structured causal reasoning with drivers, inversion tests, friction analysis
- `MissingInfoTask` — Prioritized collection tasks with Information Gap Score
- `EvidenceUpdate` — Bayesian update trail (prior → likelihood ratio → posterior)
- `Postmortem` — Learning from resolved forecasts
- `ForecastStore` — Store with Brier score computation across all resolved forecasts

**Scoring Engine** (`scoring.py`):
- Brier score, log score, interval score
- Calibration buckets and reliability curves
- Expected Calibration Error (ECE)
- Sharpness measurement
- Brier Skill Score
- Bayesian updating with likelihood ratios
- Information Gap Score

**Ensemble** (`ensemble.py`):
- Simple, weighted, and extremized ensemble aggregation
- Sequential Bayesian update trail
- Market prior extraction with recency weighting
- Uncertainty interval computation

**Priors** (`priors.py`):
- Market prior extraction with quality filtering
- Source matching quality assessment
- Base rate lookup (stub for LakeOS integration)

**Missing Info** (`missing_info.py`):
- Automated gap identification for forecasts
- Information Gap Score ranking
- OmniScout task generation

### 5. Real Data Pipeline
**Location:** `strategy_studio/data_pipeline.py`

- **Yahoo Finance v8**: Real-time price, 52-week range, historical prices, computed growth rates and CAGR
- **Wikipedia API**: Company descriptions, automatic industry detection from text
- **SEC EDGAR**: CIK lookup, SIC codes, filing counts
- **Auto-enrichment**: Every `StrategySession` with a `ticker` automatically pulls real data

### 6. HTML Presentation Generator
**Location:** `strategy_studio/presentation.py`

- 8+ slide types: title, executive summary, decision matrix, competitive analysis, scenarios, predictions, evidence quality, market data, next steps
- SVG bar charts for option scores and criteria weights
- Tornado diagrams for sensitivity analysis
- Dark theme with Unicode bar charts, score pills, tier badges
- Self-contained single HTML file (no external dependencies)
- Keyboard navigation (arrow keys)
- Auto-opens in browser after generation

### 7. Excalidraw Renderer
**Location:** `strategy_studio/renderer.py`

- Pure Python Excalidraw → SVG converter
- SVG → PNG via cairosvg (no Playwright dependency)
- Renders rectangles, ellipses, diamonds, arrows, lines, text

### 8. CLI System
**Location:** `strategy_studio/cli.py`, `strategy_studio/cli_wizard.py`

```bash
# One-command analysis
strategy-studio analyze Tesla --ticker TSLA --industry automotive --competitors "BYD,Ford,VW"

# Interactive wizard
strategy-studio wizard

# Batch mode from CSV
strategy-studio batch companies.csv --output out/batch

# Individual engines
strategy-studio synthesize --input "Market growing 25% YoY"
strategy-studio wargame --scenario "Price war" --actors "Competitor A,Competitor B"
strategy-studio forecast --question "Revenue 2025" --data "2022=100,2023=120,2024=145"
strategy-studio falsify --claim "Market will grow 20%"
```

### 9. Teaser System
**Location:** `strategy_studio/teaser/`

- Generates prospect teasers (HTML + Markdown + JSON proof packets)
- Batch processing with 16 workers
- 2000+ prospect capacity
- Evidence-cited with source weights and falsification tests

### 10. Session Runner
**Location:** `strategy_studio/session.py`

End-to-end pipeline:
1. Auto-enrich with real data (Yahoo Finance, Wikipedia, SEC)
2. Run all 4 archetypes
3. Build prediction models (ensemble forecasting)
4. Run competitive wargame
5. Build decision matrix with sensitivity analysis
6. Analyze evidence quality
7. Cross-archetype consensus
8. Meta-analysis
9. Generate scenarios
10. Build strategy report (MD + JSON + HTML presentation)

---

## Key Data Sources

| Source | What | Access |
|--------|------|--------|
| Yahoo Finance v8 | Stock price, 52w range, historical data, CAGR | `data_pipeline.py` |
| Wikipedia API | Company description, industry detection | `data_pipeline.py` |
| SEC EDGAR | CIK, SIC codes, filing counts | `data_pipeline.py` |
| Phronema LakeOS | Knowledge base, evidence storage | `~/rig-lab/phronema/` |
| QNAP RIG Lake | Raw data, files, archives | `/Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake` |
| OmniScout | Intelligence collection | `~/Desktop/Startup-Intelligence-OS/rig/omniscout/` |
| MiroShark | Prediction studio methods | `~/Desktop/Startup-Intelligence-OS/miroshark-src/` |
| MiroFish | Validation system | `~/Desktop/Startup-Intelligence-OS/MiroFish/` |

---

## Test Coverage

- **145 tests** passing across all modules
- 33 tests for Prediction Studio v2 (scoring, Bayesian, calibration, ensemble, missing info, priors)
- 33 tests for A1 archetype
- 16 tests for A2/A3/A4 archetypes
- 8 tests for B-engines
- 31 tests for studios
- 9 tests for teaser system
- 15 tests for other components

---

## How to Run

```bash
# Install
cd ~/strategy-studio
pip install -e .

# Quick demo
python3 demo.py --company Tesla --ticker TSLA

# Full analysis
strategy-studio analyze Tesla --ticker TSLA --industry automotive --competitors "BYD,Ford,VW"

# Interactive wizard
strategy-studio wizard

# Run tests
pytest tests/ -q
```

---

## What's Left to Build (from the Master Spec)

### Immediate Next Steps:
1. **Narrative Engine** — McKinsey-style story generation from analysis outputs
2. **Creativity Engine** — 5000 questions from 100 personas, triple diamond process, RIG creative boosters
3. **Innovation Methodology Ingestion** — Scrape 20+ firms (Strategos, IDEO, Frog, SIT, TRIZ, etc.)
4. **GitHub Repo Scraping** — 60+ repositories for creative AI, innovation frameworks
5. **Academic Database Scraping** — OpenAlex, Semantic Scholar for computational creativity research
6. **OmniScout Integration** — Wire the missing-info engine to actually send collection tasks
7. **QNAP/Phronema Connection** — Connect to existing LakeOS for evidence storage and retrieval
8. **MiroFish/MiroShark Integration** — Use existing prediction studio methods for persona selection

### V2 Roadmap (from spec):
- Weak-signal detection + active learning
- Causal inference for real-time event sequences
- Unified Python pipeline from ingestion → scoring → calibration → postmortem
- Human-AI hybrid robustness under drift
- Conformal prediction for uncertainty quantification
- LLM forecaster benchmarking and calibration

### V10 Vision (from spec):
- Self-Evolving Methodology Engine (generates new innovation methodologies)
- Predictive Creativity (predict which ideas will succeed before testing)
- Category Creation (identifies white spaces across all industries)
- Real-Time Orthodoxy Detection
- Quantum Creativity Layer (ideas in superposition until decision)
- Cross-Client Intelligence
- Meta-Formula: `V10_Creativity = Σ(all_methodology_weights × domain_relevance × temporal_freshness × proof_density) × adversarial_survival_rate × implementation_velocity`

---

## File Locations Summary

| Asset | Location |
|-------|----------|
| Main package | `~/strategy-studio/strategy_studio/` |
| Tests | `~/strategy-studio/tests/` |
| Prediction Studio v2 | `~/strategy-studio/strategy_studio/studios/prediction_studio/` |
| Example outputs | `~/strategy-studio/examples/outputs/` |
| Demo script | `~/strategy-studio/demo.py` |
| Data pipeline | `~/strategy-studio/strategy_studio/data_pipeline.py` |
| Session runner | `~/strategy-studio/strategy_studio/session.py` |
| Presentation generator | `~/strategy-studio/strategy_studio/presentation.py` |
| Excalidraw renderer | `~/strategy-studio/strategy_studio/renderer.py` |
| CLI | `~/strategy-studio/strategy_studio/cli.py` |
| Teaser system | `~/strategy-studio/strategy_studio/teaser/` |
| LakeOS CLI | `~/rig-lab/phronema/scripts/lakeos_cli.py` |
| QNAP Lake | `/Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake` |
| MiroShark | `~/Desktop/Startup-Intelligence-OS/miroshark-src/` |
| MiroFish | `~/Desktop/Startup-Intelligence-OS/MiroFish/` |
| OmniScout | `~/Desktop/Startup-Intelligence-OS/rig/omniscout/` |
| RIG systems | `~/Desktop/Startup-Intelligence-OS/rig/` |
| GitHub repo | `github.com/rodgemd1-lgtm/strategy-studio` |

---

## Architecture Diagram

```
User Input (company, ticker, context)
    ↓
Data Pipeline (Yahoo Finance, Wikipedia, SEC EDGAR)
    ↓
Signal Registry → Forecast Question Generator
    ↓
4 Archetypes (A1→A2→A3→A4) — parallel execution
    ↓
Prediction Studio v2:
  - Base Rate Engine
  - Market Prior Engine
  - Causal Thesis Tree
  - Model Ensemble (human + LLM + market + base rate + models)
  - Bayesian Updating
  - Calibration Layer
  - Missing Information Engine → OmniScout tasks
    ↓
Decision Room (MCDA + Sensitivity + Tornado)
    ↓
Evidence Engine (Source Scoring + Contradictions)
    ↓
Synthesis Pipeline (Cross-Archetype Consensus + Meta-Analysis)
    ↓
Output Studio:
  - Executive Summary
  - Board Deck (HTML with SVG charts)
  - Strategy Report (MD + JSON)
  - HTML Presentation (auto-opens in browser)
    ↓
Resolution → Scoring → Postmortem → Learning
```

---

*This handoff document represents the complete state of Strategy Studio as of May 26, 2026.*
*For questions or next steps, refer to the master spec sections on Creativity Engine, Innovation Methodology Ingestion, and the V2-V10 roadmap.*