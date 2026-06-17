# RIG Strategy Studio

**A 147-cell deterministic routing engine that maps any strategic question to the cheapest execution mode that can answer it — from a $0.001 rules-only pass to a full agent crew — with evidence-weighted synthesis at every step.**

![License](https://img.shields.io/badge/license-teaser%20(source%20private)-blue.svg)
![Tests](https://img.shields.io/badge/tests-371%20collected-brightgreen.svg)
![Status](https://img.shields.io/badge/status-private%20beta-orange.svg)

> This is the **public teaser**. It shows you what the engine does and proves it with real output. The full, production source lives in a private repo — see [Get full access](#get-full-access).

## The problem

Most "AI strategy" tooling sends every question to the most expensive model in the rack. A question a deterministic rule could answer for a fraction of a cent gets routed to an Opus crew anyway — slow, costly, and impossible to audit. There is no cost floor, no cost ceiling, and no record of *why* a given question cost what it cost.

And when the answer comes back, you can't tell which claims were grounded in evidence and which the model invented. "The model said so" is not a strategy artifact you can defend in a board meeting. You need a decision you can trace to its sources, priced before it runs, with a hard cap you set.

## What it does

RIG Strategy Studio fixes the routing problem *first*, before any model touches the question.

- **Classifies every strategic intent onto a 147-cell lattice** — `L{altitude}-D{diamond}-{IQRSQPI step}` — 7 altitudes × 3 domains × 7 process steps. Each cell is a resolvable, inspectable Build Card.
- **Binds each cell to one of four cost-capped build modes**, A1 through A4. The caps are *binding ceilings*, not suggestions: `<=$0.001 / <=$0.05 / <=$1 / <=$50+4h`.
- **Auto-selects the mode with a Build-Mode Score (BMS)** from altitude + complexity, then picks the cheapest mode that can actually answer — and only escalates A1→A2→A3→A4 on failure.
- **Refuses to guess.** A1 never invents an answer; if it can't resolve deterministically it returns `UNKNOWN` and escalates instead of hallucinating. Uncited claims surface as `UNKNOWN` with an indexing request, not a confident lie.
- **Runs the strategy engines on the same binary** — synthesis, market wargame, forecasting, falsification, competitor/client intelligence, and a decision room (MCDA + sensitivity + value-of-information).
- **Ships a FastAPI service** (`/synthesize`, `/wargame`, `/forecast`, `/falsify`, `/lattice/*`) and two CLIs over the same core.
- **Stamps external-facing deliverables with a ProofPacket + FalsificationPacket** — every send carries an audit trail.

## Proof

These numbers come straight out of the real repo, not a pitch deck.

**The lattice is real and the math checks out.** `strategy-studio lattice summary` prints:

```
RIG Lattice Summary (147 cells / 588 with BMS modes)
┌──────────────────────────────┬───────────┬───────┐
│ Dimension                    │ Breakdown │ Count │
├──────────────────────────────┼───────────┼───────┤
│ 147-cell (L×D×Step)          │           │   147 │
│ 588-cell (L×D×A×Step)        │           │   588 │
│ Reusable archetypes (A×Step) │           │    28 │
│ Build Mode                   │ A1        │    42 │
│ Build Mode                   │ A2        │    42 │
│ Build Mode                   │ A3        │    42 │
│ Build Mode                   │ A4        │    21 │
│ Altitude                     │ L1…L7     │ 21 ea │
│ Diamond                      │ D1/D2/D3  │ 49 ea │
└──────────────────────────────┴───────────┴───────┘
```

**The cost caps are enforced in code, not the README.** From the build-mode definition:

| Mode | Cap | BMS threshold | Executor |
|------|-----|---------------|----------|
| A1 PYTHON_ONLY | `<=$0.001` | BMS ≥ 0.75 | Pydantic + Jinja2 + regex — no model in the decision path |
| A2 HYBRID | `<=$0.05` | BMS ≥ 0.45 | A1 + Haiku/Sonnet shims |
| A3 AGENT_BOUNDED | `<=$1` | BMS ≥ 0.25 | LangGraph + CrewAI + guardrails |
| A4 LLM_AGENT_FREE | `<=$50+4h` | otherwise | Opus / hierarchical crews + falsification |

**371 tests collected**, covering the lattice, BMS routing, the engines, the teaser pipeline, and the tool registry:

```
$ python3 -m pytest tests/ --collect-only -q
371 tests collected in 0.30s
```

**92 named workflows** are defined (each a `WorkflowDoc`: name · BMS mode · ordered steps) spanning evidence collection, lattice routing, the engines, GTM packaging, and proof/approval gates — a 1,026-line reference, round-tripping with a visual designer.

We don't oversell what isn't finished: a handful of tests assert against a live private fleet/tailnet and a few in-progress mode-dispatch behaviors. Those are documented known-reds. **The deterministic A1 lattice, the engines, the FastAPI service, and the CLI work today and run standalone with no external services.**

## Who it's for

- **Strategy & corp-dev teams** who want repeatable, citeable decisions instead of one-off model chats.
- **Operators wiring LLMs into a pipeline** who need a hard cost cap *per decision* and a deterministic floor under it.
- **Anyone tired of "the model said so"** — every output here is mode-tagged, cost-bounded, and evidence-scored.

## A peek

Inspect any single cell and see exactly how it will run *before* you run it — mode, cost band, tools, validation gates, and the escalation target if it fails. This is real output from `strategy-studio lattice cell L2-D1-I1`:

```
╭───────────────── Lattice Cell: L2-D1-A1-I1 ─────────────────╮
│ Cell:        L2-D1-I1                                        │
│ Altitude:    L2 — Structured but parameterized              │
│ Step:        I1 (intent) — Classify intent and scope it     │
│ BMS Score:   0.78                                           │
│ Build Mode:  A1 — No model in decision path. Pydantic +     │
│              Jinja + regex.                                  │
│ Cost Band:   <=$0.001                                       │
│ Tools:       regex, jinja2, pydantic, httpx                 │
│ Validation:  rule_gates, pydantic_validation, sha256_audit  │
│ Escalation:  A2.1                                           │
╰─────────────────────────────────────────────────────────────╯
```

A BMS score is fully decomposed — you see why a cell landed in the mode it did:

```
$ strategy-studio lattice bms --altitude 3
              BMS Score — A2 (<=$0.05)
  Raw Score (C1/C2/C10)          0.5000
  Altitude Adj (L3)             +0.1200
  Final BMS                      0.6200  →  Build Mode A2
```

That's the engine deciding, deterministically, that this question is worth at most five cents to answer — and telling you why.

## What you'd get with full access

The private repo ships the complete, runnable system:

- the full **147-cell lattice + BMS router** (`rig_lattice.py`, `lattice_wire.py`, `langgraph_executor.py`)
- all **strategy engines** (synthesis, wargame, forecast, falsification, decision room, intelligence)
- the **FastAPI service** and both CLIs (`strategy-studio` + `rig-strategy-studio`, ~30 subcommands)
- the **evidence-weighting + ProofPacket/FalsificationPacket** layer
- the **92-workflow library** and the visual workflow designer
- the **371-test suite** and the install path (`pip install -e .`)

## Get full access

This public repo is the teaser. The complete, production source lives in a private repo.

**Want it?** ⭐ Star this repo, then email **mike@rodgersintelligence.com** or DM **Mike Rodgers** on LinkedIn — say which product and your use case. You'll get pricing + a private-repo invite.
