# Strategy Studio — Agent Context

## Project
Strategy Studio — RIG Deviator strategy synthesis, wargame, forecasting, and decision room engine.
Owns the strategy process end-to-end: evidence ingestion, synthesis, wargaming, forecasting,GTM planning.

## Operator
Mike Rodgers. Execution-first. No "let me". Act then report.

## Strategy Process Domain
- Strategy Synthesis (B29) — evidence → ranked options
- Market Wargame (B36) — competitor moves → RIG responses  
- Competitor Intelligence (B42) — competitor changes → response options
- Client Intelligence (B41) — prospect evidence → wedge offers
- Prediction Crux (B34) — questions → forecast variables
- Falsification (B33) — beliefs → disprove tests
- Consensus Delta (B31) — new research → belief updates
- GTM Planning — strategy → go-to-market plans

## Quality Gates
- Evidence required: min 2 cited sources per claim
- Falsification gate: strategy outputs must have falsification packet
- Proof packet: every external send needs a strategy proof packet
- UNKNOWN policy: if LakeOS has no cited result, return UNKNOWN + request indexing

## Key Paths
- LakeOS CLI: `/Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py`
- LakeOS REST: `http://127.0.0.1:8788`
- Recall API: `https://backend.getrecall.ai/api/v1`
- QNAP Lake: `/Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake`

## Excalidraw Diagrams

When the user asks for an Excalidraw diagram, a visual explainer, an
architecture diagram, or anything that should ship as a `.excalidraw` file,
follow the instructions in `.codex/skills/excalidraw-diagram/SKILL.md`
verbatim.

Key rules from that skill:
- Map concepts to shape arrangements (fan-out, timeline, convergence, decision, feedback loops).
  Never use a uniform card grid.
- Embed concrete evidence artifacts (code snippets, JSON payloads, event names, API shapes).
- After writing the `.excalidraw` file, run the render pipeline to produce a PNG,
  inspect it, and iterate until layout issues (overlap, misalignment, spacing) are resolved.
- Brand colors live in `.codex/skills/excalidraw-diagram/references/color-palette.md`.

Render command:
```
cd .codex/skills/excalidraw-diagram/references && uv run python render_excalidraw.py <path-to.excalidraw>
```
