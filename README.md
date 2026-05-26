# Strategy Studio

**25x better than McKinsey. Deterministic. Evidence-cited. Free.**

Strategy Studio is a fully deterministic strategy synthesis platform. Same input always produces same output. Every claim is cited. Every option is scored. Every risk is tracked.

## Install

```bash
git clone https://github.com/rodgemd1-lgtm/strategy-studio
cd strategy-studio
pip install -e .
```

## Quick Start

### Analyze a company (one command)

```bash
strategy-studio analyze Tesla --industry automotive --competitors "BYD,Ford,VW"
```

This produces:
- `strategy_analysis_tesla.md` — Full strategy report with executive summary, decision matrix, wargame analysis, scenarios, and recommendations
- `strategy_analysis_tesla.json` — Machine-readable output
- Visual diagrams (PNG + SVG): strategy map, competitive positioning, evidence graph

### Interactive wizard

```bash
strategy-studio wizard
```

Step-by-step guided session. Asks for company info, competitors, evidence. Runs full analysis.

### Batch mode

```bash
strategy-studio batch companies.csv --output out/batch
```

CSV columns: `company_name, industry, competitors, context, evidence`

### Individual engines

```bash
strategy-studio synthesize --input "Market growing 25% YoY" --format md
strategy-studio wargame --scenario "Price war" --actors "Competitor A,Competitor B" --format md
strategy-studio forecast --question "Revenue 2025" --data "2022=100,2023=120,2024=145" --format md
strategy-studio falsify --claim "Market will grow 20%" --format md
```

## Architecture

```
strategy_studio/
├── core/
│   ├── types.py              — 17 Pydantic models
│   ├── types_extended.py     — 17 more (scenarios, predictions, decisions)
│   ├── config.py             — Runtime config
│   ├── renderer.py           — Excalidraw → SVG/PNG renderer
│   └── data_pipeline.py      — Real data: Yahoo Finance, Wikipedia, SEC
├── archetypes/
│   ├── a1/  (IQRSQPI)        — Pure deterministic, 7-step pipeline
│   ├── a2/  (Hybrid)         — Deterministic + LLM fallback
│   ├── a3/  (Agent-Bounded)  — Multi-agent parallel w/ consensus
│   └── a4/  (LLM-Free)      — Strictest deterministic
├── engines/                   — 13 B-engines (synthesis → impact)
├── studios/
│   ├── prediction_studio.py  — Monte Carlo, forecasting, wargaming
│   ├── decision_room.py      — MCDA, sensitivity, tornado, VOI
│   ├── evidence_engine.py    — Source scoring, contradiction detection
│   ├── synthesis_pipeline.py — Cross-archetype consensus, meta-analysis
│   ├── output_studio.py      — Board decks, executive summaries, reports
│   ├── calibration_engine.py — Brier scoring, Bayesian updating
│   ├── industry_playbooks.py  — 10 industries with KPIs and benchmarks
│   └── visual_strategy_maps.py — Excalidraw diagram generation
├── session.py                — End-to-end strategy session runner
├── cli.py                    — Click CLI (analyze, wizard, synthesize, etc.)
└── cli_wizard.py             — Interactive wizard + batch mode
```

## Why 25x better than McKinsey

| Dimension | McKinsey | Strategy Studio |
|---|---|---|
| Speed | 6-12 weeks | 30 seconds |
| Cost | $500K-$2M | $0 (open source) |
| Reproducibility | None (different team = different answer) | Full determinism |
| Evidence | Interviews, uncited | Every claim cited + falsification test |
| Scenarios | 3 static | 10,000 Monte Carlo + cross-impact |
| Competitive analysis | 5 interviews | Multi-round wargame + Nash equilibrium |
| Decision analysis | Subjective scorecard | MCDA + sensitivity + tornado + VOI |
| Calibration | None | Brier scoring + Bayesian updating |
| Batch capacity | 1 engagement | Unlimited parallel |

## Example output

See `examples/outputs/tesla/` for a complete Tesla strategy analysis including:
- `strategy_analysis:_tesla.md` — Full report
- `strategy_analysis:_tesla.json` — Machine-readable
- `visuals/strategy_map.png` — Strategy architecture map
- `visuals/competitive_map.png` — Competitive positioning
- `visuals/evidence_graph.png` — Evidence quality visualization

## Tests

```bash
pytest tests/ -q
```

141 tests covering all engines, archetypes, studios, data pipeline, and renderer.

## License

MIT. Use it freely. Build on it. Make McKinsey obsolete.