# Strategy Studio

**RIG Strategy Studio** — a deterministic, LLM-free strategy synthesis engine for building high-confidence strategic plans.

## Overview

Strategy Studio is a collection of deterministic engines designed to synthesize strategy without LLMs. It implements the RIG architecture with:

- **A1 Archetypes**: Intent, Question, Research, Solution, Quality, Proof, Integration
- **B-Engines**: Specialized engines for evidence synthesis, forecasting, wargames, and strategic planning
- **Teaser System**: Generates 2000 prospect teasers in parallel using Codex

## Core Components

### A1 Archetypes

The A1 archetypes form the foundation of deterministic strategy:

1. **Intent** - Establish strategic purpose
2. **Question** - Formulate precise research questions
3. **Research** - Collect and organize evidence
4. **Solution** - Synthesize strategic options
5. **Quality** - Apply quality gates
6. **Proof** - Build evidence-based arguments
7. **Integration** - Connect to broader strategy

### B-Engines

Specialized engines for strategic analysis:

- **B29 Synthesize** - Evidence synthesis engine
- **B33 Falsify** - Claim falsification engine  
- **B34 Predict** - Forecasting engine
- **B36 Wargame** - Competitive scenario engine
- **B31 Consensus Delta** - Research consensus engine
- **B37 Risk Assessment** - Risk analysis engine
- **B40 Market Sizing** - Market opportunity engine
- **B43 Competitive Positioning** - Competitive advantage engine
- **B44 Timeline Planning** - Implementation planning engine
- **B45 Budget Allocation** - Resource allocation engine
- **B46 Impact Assessment** - Strategic impact engine

### Teaser System

The teaser system generates 2000 prospect teasers in parallel using Codex:

- Generates HTML, Markdown, and PDF-ready outputs
- Follows the HED proven wedge format (10 sections)
- Enforces evidence citation and quality gates
- Supports batch processing with 16 workers

## Quick Start

```bash
# Install the package
pip install -e .

# Generate a teaser for a prospect
strategy-studio teaser --input-file inputs/sample_prospect.json

# Run batch processing for 2000 prospects
strategy-studio batch --input-file inputs/prospects_2000.jsonl

# Run a synthesis engine
strategy-studio synthesize --input "analyze market options for Tesla in EV charging"

# Run a wargame engine
strategy-studio wargame --scenario "Competitive moves in EV charging" --actors "competitor,regulator"

# Run a forecast engine
strategy-studio forecast --question "EV market growth rate" --data '{"2023": 20.0, "2024": 25.0}'
```

## Development

### Installation

```bash
# Clone the repository
git clone https://github.com/rodgemd1-lgtm/strategy-studio.git
cd strategy-studio

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_a1/
pytest tests/test_engines/
pytest tests/test_teaser/
```

### Structure

```
strategy_studio/
├── __init__.py           # Main package exports
├── core/                 # Core types and utilities
│   ├── __init__.py
│   └── types.py          # Pydantic models
├── archetypes/           # A1 deterministic archetypes
│   └── a1/
│       ├── __init__.py
│       ├── a1_1_intent.py
│       ├── a1_2_question.py
│       ├── a1_3_research.py
│       ├── a1_4_solution.py
│       ├── a1_5_quality.py
│       ├── a1_6_proof.py
│       └── a1_7_integrate.py
├── engines/              # B-engines for strategic analysis
│   ├── __init__.py
│   ├── b29_synthesize.py
│   ├── b33_falsify.py
│   ├── b34_predict.py
│   ├── b36_wargame.py
│   ├── b31_consensus_delta.py
│   ├── b37_risk_assessment.py
│   ├── b40_market_sizing.py
│   ├── b43_competitive_positioning.py
│   ├── b44_timeline_planning.py
│   ├── b45_budget_allocation.py
│   └── b46_impact_assessment.py
├── teaser/               # Teaser generation system
│   ├── __init__.py
│   ├── schema.py         # Teaser input/output schema
│   ├── generator.py      # Jinja2 template engine
│   ├── batch.py          # Parallel processing engine
│   └── templates/        # HTML/Markdown templates
├── cli.py                # Command-line interface
└── server.py             # FastAPI web server
```

## Key Features

- **Deterministic**: No LLMs in the decision path
- **Evidence-based**: All claims must be cited with source weights
- **Parallel processing**: Batch processing with 16 workers for 2000 prospects
- **Quality gates**: Pydantic validation, 2+ evidence sources, falsification packets
- **Modular design**: Each engine can be used independently or in combination
- **Production ready**: Used for generating 2000 prospect teasers in parallel

## License

MIT License