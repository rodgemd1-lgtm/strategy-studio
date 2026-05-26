# RIG Lattice Architecture

## Overview

The RIG Lattice is a **147-cell decision matrix** that routes every strategy question to the right execution mode — no more, no less. Each cell is fully addressable, scored, and executable.

```
147 cells = 7 Altitudes × 3 Diamonds × 7 IQRSQPI steps
```

## Three Axes

### Axis 1: Altitude (Complexity → Cost Band)

7 levels from deterministic to novel:

| Altitude | Label | Doctrine | Cost Cap | BMS Range |
|----------|-------|----------|---------|-----------|
| L1 | Direct | Deterministic, fully reversible | ≤$0.001 | ≥0.75 → A1 |
| L2 | Structured | Parameterized, rule-bound | ≤$0.001 | ≥0.75 → A1 |
| L3 | Workflow | Branching paths | ≤$0.05 | ≥0.45 → A2 |
| L4 | Bounded Agentic | Checkpoints, tool budgets | ≤$1 | ≥0.25 → A3 |
| L5 | Mechanism | Tradeoff reasoning | ≤$1 | ≥0.25 → A3 |
| L6 | Strategic Synthesis | High failure cost | ≤$50 | <0.25 → A4 |
| L7 | Doctrine/Exploration | Novel frames, irreducible | ≤$50+4h | <0.25 → A4 |

### Axis 2: Diamond (Domain)

| Diamond | Domain | Doctrine |
|---------|--------|----------|
| D1 | Strategy Synthesis | Outcome ranking, competitive response |
| D2 | Intelligence & Research | Evidence gathering, falsification |
| D3 | Operations & Execution | Action planning, GTM execution |

### Axis 3: IQRSQPI Steps (Process)

7 sequential steps per cell, each producing output consumed by the next:

```
I1 → Q1 → R → S → Q2 → P → I2
│    │    │    │    │    │    │
│    │    │    │    │    │    └─ Integrate: Action + Audit
│    │    │    │    │    └─ Proof: Evidence trail + sources
│    │    │    │    └─ Quality: Falsification gates (A2 minimal)
│    │    │    └─ Solution: Ranked options
│    │    └─ Research: Evidence collection
│    └─ Question: StructuredQuery generation
└─ Intent: IntentKey classification
```

## Each Cell = L{A}-{D[123]}-{IQRSQPI}

**L2-D1-Q1** = Altitude 2 (Structured), Diamond 1 (Strategy), Step Q1 (Question)

## Build Modes (A1-A4)

Not a recommendation — a **binding budget constraint**:

| Mode | Cost Band | Executor | Doctrine |
|------|----------|----------|----------|
| **A1 PYTHON_ONLY** | ≤$0.001 | Direct `strategy_studio.archetypes.a1.*` | Pydantic validation, Jinja2 templates, regex. No model in decision path. |
| **A2 HYBRID** | ≤$0.05 | A1 + PythonLLM shims (Haiku/Sonnet) | Rubric + signed packet + source trace. LLM assists, Python gates. |
| **A3 AGENT_BOUNDED** | ≤$1 | LangGraph/CrewAI | Hard tool budgets, mandatory NeMo Guardrails, audit trail. |
| **A4 LLM_AGENT_FREE** | ≤$50+4h | Hierarchical Opus crews | 10 rubrics, 20 adversarial tests, Brier score, falsification charter. |

## BMS Scoring

BMS (Build Mode Selector) auto-routes each cell based on:

```
C1 = failure_cost    (weight 0.40 — consequences of wrong answer)
C2 = reversibility   (weight 0.30 — how fixable is a mistake)
C10 = mechanism_clarity (weight 0.30 — do we know the因果?)

raw_score = 0.4*C1 + 0.3*C2 + 0.3*C10
adjusted  = raw_score - past_failure_adjustment + altitude_bonus
```

BMS thresholds:
- **≥0.75** → A1 (high confidence, reversible)
- **≥0.45** → A2 (moderate confidence)
- **≥0.25** → A3 (agentic territory)
- **<0.25** → A4 (full autonomous reasoning)

## Escalation Paths

When a mode fails, it escalates to the next:

```
A1 → A2 → A3 → A4
  │     │     │
  └─────┴─────┘ (escalation_reason stored in ArchetypeResult)
```

Escalation triggers: `status in ("UNKNOWN", "failed", "QUALITY_FAILED")`

## Orchestration Modes

The `LatticeOrchestrator` offers three traversal modes:

| Method | Scope | Use Case |
|--------|-------|----------|
| `traverse(cell_id, data)` | 1 cell | Single cell inspection |
| `traverse_diamond(alt, dia, data)` | 7 cells (I1→I2) | Full IQRSQPI pipeline |
| `traverse_altitude(alt, data)` | 21 cells (3×7) | Domain deep-dive |
| `run_full_pipeline(data)` | 7 cells (L2-D1) | Default strategy run |

Each step's output is passed forward as input to the next step: `data["step_{step_name}"] = result.output`

## Build Cards

Each cell has a **Build Card** — the immutable contract that specifies:
- Mode (which A-number)
- Cost band
- Doctrine
- Tools required
- Validation criteria
- Escalation target

Generated via `BuildCardGenerator.generate_all()` → outputs `phronema/{cell_id}.yaml`

The card is the **single source of truth** for what a cell must do, what it costs, and what happens if it fails.

## Quality Gates

| Mode | Gate |
|------|------|
| A1 | rule_gates + pydantic_validation + sha256_audit |
| A2 | rubric_combo + signed_packet + source_trace |
| A3 | mechanism_map + proof_check + mandatory_approval + audit_trail |
| A4 | 10_rubrics + 20_adversarial + brier_score + falsification_charter |

## CLI Reference

```bash
rig-strategy-studio lattice modes          # Show all 4 modes with cost bands
rig-strategy-studio lattice list-cells     # List all cell IDs (--altitude L2)
rig-strategy-studio lattice bms            # Compute BMS ratings
rig-strategy-studio cells all-cards        # Show all 147 Build Cards
rig-strategy-studio cells card L2-D1-I1    # Inspect one Build Card
rig-strategy-studio orchestrator traverse  # Single cell execution
rig-strategy-studio orchestrator pipeline  # Full IQRSQPI diamond run
rig-strategy-studio executor a3            # Direct LangGraph A3 execution
rig-strategy-studio test --quick           # Run test suite
```

## Architecture Diagram

```
                    ┌─────────────────────────────────┐
                    │     LatticeOrchestrator         │
                    │  traverse / traverse_diamond /   │
                    │  traverse_altitude / pipeline     │
                    └──────────────┬──────────────────┘
                                   │ dispatch
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
        ┌──────────┐        ┌──────────┐        ┌──────────┐
        │ Archetype│        │ Archetype│        │ Archetype│
        │ Executor │─A3───▶│ Executor │─A4───▶│ Executor │
        │ (A1/A2)  │        │ (A3)     │        │ (A4)     │
        └──────────┘        └──────────┘        └──────────┘
              │                   │                   │
              ▼                   ▼                   ▼
     strategy_studio.       LangGraph +          Opus crews +
     archetypes.a1.*        CrewAI +             falsification
                            guardrails           Brier score
```

## Valid Cell IDs

All 147 cells follow: `L{1-7}-D{1-3}-{I1|Q1|R|S|Q2|P|I2}`

Examples:
- `L1-D1-I1` through `L1-D1-I2` (D1 cells at L1)
- `L2-D2-Q1` through `L2-D2-I2` (D2 cells at L2)
- `L7-D3-R` (Research at highest altitude in Operations domain)

Pattern regex: `^L(\d+)-(D[123])-(I[12]|Q[12]|[RSP])$`

## Cell Counts by Mode

BMS-based routing produces the following cell counts per mode:

| Mode | Cell Count | Altitudes |
|------|-----------|-----------|
| A1 | 42 | L1 (21) + L1-D*D* (21) |
| A2 | 42 | L2 (21) + L3 (21) |
| A3 | 42 | L4 (21) + L5 (21) |
| A4 | 21 | L6 (21) |

## Running a Full Pipeline

```python
from strategy_studio.rig_lattice import LatticeOrchestrator

orch = LatticeOrchestrator()
results = orch.traverse_diamond(
    altitude=Altitude.L2,
    diamond=Diamond.D1_STRATEGY,
    input_data={"query": "Should we enter the B2B market?"}
)

for cell_id, result in results.items():
    print(f"{cell_id}: {result.status} — {result.output}")
```
