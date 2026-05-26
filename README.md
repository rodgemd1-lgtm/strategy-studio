# RIG Strategy Studio

**25x better than McKinsey. Deterministic. Evidence-cited. Free.**

Strategy Studio is a fully deterministic strategy synthesis platform. Same input always produces same output. Every claim is evidence-cited with falsification tests. Every option is scored. Every risk is tracked.

## Quick Start

```bash
# Install
git clone https://github.com/rodgemd1-lgtm/strategy-studio
cd strategy-studio
pip install -e .

# Analyze a company (one command)
strategy-studio analyze Tesla --ticker TSLA --industry automotive --competitors "BYD,Ford,VW"

# Interactive wizard
strategy-studio wizard

# Run tests
pytest tests/ -q
# 145 tests passing
```

## What It Does

You give it a company name + ticker. In 30 seconds it produces:

1. **Executive Summary** — Key findings, recommendation, confidence level
2. **Decision Matrix** — All options scored, ranked, tiered (A/B/C/D) with sensitivity analysis and tornado diagrams
3. **Competitive Analysis** — Multi-round wargame with Nash equilibrium detection
4. **Scenario Analysis** — 4+ scenarios with probability-weighted outcomes
5. **Predictions** — Ensemble forecasts (linear + moving average + exponential smoothing) with Monte Carlo confidence intervals
6. **Prediction Studio v2** — Probabilistic forecasting with Brier/log scoring, Bayesian updating, calibration tracking, and missing-information engine
7. **Evidence Quality** — Every claim cited, sources scored, contradictions detected
8. **HTML Presentation** — Board-ready slide deck with SVG charts that auto-opens in your browser

## Architecture

```
strategy_studio/
├── archetypes/          # 4 archetypes (A1→A2→A3→A4)
│   ├── a1/              # Pure deterministic
│   ├── a2/              # Hybrid (deterministic + LLM fallback)
│   ├── a3/              # Agent-Bounded (multi-agent parallel)
│   └── a4/              # LLM-Free (strictest deterministic)
├── engines/             # 13 B-engines (B29-B46)
├── studios/             # 7 studios
│   ├── prediction_studio/    # NEW v2: Probabilistic forecasting
│   │   ├── core.py           # All Pydantic models
│   │   ├── scoring.py        # Brier, log, interval scores
│   │   ├── ensemble.py       # Multi-model aggregation
│   │   ├── priors.py         # Market prior extraction
│   │   └── missing_info.py   # Information gap scoring
│   ├── decision_room.py      # MCDA, sensitivity, tornado
│   ├── evidence_engine.py    # Source scoring, contradictions
│   ├── synthesis_pipeline.py # Cross-archetype consensus
│   ├── output_studio.py      # Board decks, reports
│   ├── calibration_engine.py # Brier scoring, calibration
│   ├── industry_playbooks.py # 10 industries
│   └── visual_strategy_maps.py # Excalidraw diagrams
├── core/                # Types, config, exceptions
├── data_pipeline.py     # Real data (Yahoo Finance, Wikipedia, SEC)
├── session.py           # End-to-end pipeline
├── presentation.py      # HTML slide deck generator
├── renderer.py          # Excalidraw → SVG/PNG
├── cli.py               # Click CLI
└── teaser/              # Prospect teaser generation
```

## Prediction Studio v2

The most significant module, built from a Consensus research review (518 papers screened, 50 included):

- **Proper scoring rules**: Brier, log, interval scores (Gneiting & Raftery 2007)
- **Bayesian updating**: Sequential evidence incorporation with likelihood ratios
- **Calibration tracking**: Reliability curves, ECE, sharpness measurement
- **Prediction market priors**: Real-time market data as probability priors
- **Missing information engine**: Ranks information gaps by value, generates OmniScout tasks
- **Causal thesis trees**: Structured reasoning with inversion tests and friction analysis
- **Ensemble forecasting**: Multi-model aggregation with uncertainty quantification

## Real Data Integration

- **Yahoo Finance**: Real-time price, 52-week range, historical data, CAGR
- **Wikipedia**: Company descriptions, automatic industry detection
- **SEC EDGAR**: CIK lookup, SIC codes, filing counts
- **Phronema LakeOS**: Knowledge base integration (LAN-only)

## Tests

145 tests covering all engines, archetypes, studios, data pipeline, and renderer.

## License

MIT. Use it freely. Build on it. Make McKinsey obsolete.