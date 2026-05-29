# RIG V10 Readiness Design (Planning-Only)

Status: design/proof only. This does **not** claim final PASS.

## 1) V10 Product Promise

`strategy-studio` is the deterministic strategy core that can be operated four ways from one repo surface:
- as a local CLI (`strategy-studio`, `rig-strategy-studio`)
- as an agent-executable repo with explicit guardrails (`AGENTS.md`)
- as an MCP-capable future surface (defined below)
- as a weekly self-improving repo with rerunnable proof outputs

## 2) CLI Surface + First Deterministic Smoke Command

Current CLI surface signals:
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/pyproject.toml` (`project.scripts`)
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/bin/strategy-studio`
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/bin/rig-strategy-studio`
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/strategy_studio/cli.py`

First deterministic local smoke command:

```bash
python -m strategy_studio.cli lattice summary
```

Why this command:
- local-only, no secrets required
- exercises CLI parser + lattice deterministic layer
- suitable as a low-cost pre-edit gate for humans and agents

## 3) MCP Surface Decision

MCP is intentionally **deferred** for product implementation in this issue (planning boundary only).

Required MCP contract to implement later:
- Tools: `lattice_summary`, `lattice_cell`, `forecast_question`, `falsify_claim`
- Resources: `build_cards/*`, `docs/rig-lattice-architecture.md`, generated proof packets
- Prompts: `strategy-intake`, `forecast-calibration`, `falsification-check`
- Auth boundary: local-first, no secret emission, no private export logging
- Local MCP smoke target: tool listing + one deterministic read-only tool call

## 4) Agent Roles, Routing, and Quality Gates

Role split for V10 looper runs:
- Planner: scope, blockers, proof paths
- Reviewer: contract/readiness validation + security boundary checks
- Fixer: deterministic doc/script/test updates only
- QA: rerun smoke checks + proof count updates

Model-routing expectations:
- deterministic checks first (CLI + tests)
- bounded coding model for edits/tests
- escalate to larger reasoning model only for unresolved design contradictions

Quality gates (must be explicit in each run):
- Evidence gate: cite repo files and command outputs
- Falsification gate: record unknowns/blockers explicitly
- Proof gate: write sanitized artifacts under `proof/looper-v10-cockpit/`
- Security gate: no secrets/tokens/private exports in outputs

## 5) Weekly Improvement Loop + Human Approval Boundaries

Weekly loop behavior:
1. Run deterministic smoke command.
2. Run targeted cheap readiness tests.
3. Refresh this proof area with deltas, counts, and blockers.
4. Keep unresolved blockers grouped by “next safe action.”

Must never run without human approval:
- deploy/publish/release actions
- secret provisioning or secret rotation
- external messaging or schedule activation
- destructive repo cleanup/reset operations

## 6) Blockers / Missing Items

Current blockers and gaps:
- MCP server/client implementation missing (design-only defined)
- no dedicated deterministic looper smoke script wrapper yet (command exists, wrapper missing)
- no proof trend index file yet (single-run proof only)
- many baseline tests are environment-coupled and fail in sandbox

Environment-coupled baseline findings (captured, not fixed in this issue):
- `pytest -q` summary observed: `41 failed, 391 passed, 2 skipped`
- failures include missing local/OpenClaw/QNAP-style paths and network reachability assumptions

## 7) Required Proof Paths + Test Commands

Proof root:
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/proof/looper-v10-cockpit/`

This run output:
- `/tmp/workspace/rodgemd1-lgtm/strategy-studio/proof/looper-v10-cockpit/2026-05-29-rig-v10-readiness-design.md`

Deterministic commands to use in future weekly runs:

```bash
python -m strategy_studio.cli lattice summary
pytest -q tests/contracts/test_tool_registry.py
```
