# strategy-studio

![status](https://img.shields.io/badge/status-active-public-blue) ![lane](https://img.shields.io/badge/lane-rig-core-purple) ![visibility](https://img.shields.io/badge/visibility-public-lightgrey) ![qnap](https://img.shields.io/badge/qnap-qnap-verified-green) ![proof](https://img.shields.io/badge/proof-required-red)

## 30-Second Pitch

RIG Strategy Studio - A1-A4 archetype workflows, Excalidraw diagrams, HED docs, terminal visualization Evidence from the tracked tree: Documentation corpus, FastAPI service, Scripted automation.

## RIG Lattice — Core Architecture

The RIG Lattice is a **147-cell decision matrix** routing every strategy question to the right execution mode.

```
147 cells = 7 Altitudes × 3 Diamonds × 7 IQRSQPI steps
L{A}-{D[123]}-{I1|Q1|R|S|Q2|P|I2}
```

| Axis | Values | Doctrine |
|------|--------|----------|
| Altitude | L1–L7 | Deterministic → Novel frame. Sets cost band + BMS threshold. |
| Diamond | D1 (Strategy), D2 (Intelligence), D3 (Operations) | Domain classification |
| IQRSQPI | I1→Q1→R→S→Q2→P→I2 | Sequential process: Intent → Question → Research → Solution → Quality → Proof → Integrate |

Four build modes — not recommendations, **binding cost constraints**:

| Mode | Cap | Executor | Cells |
|------|-----|----------|-------|
| A1 PYTHON_ONLY | ≤$0.001 | Pyd+Jinja2+regex, no model in path | 42 |
| A2 HYBRID | ≤$0.05 | A1 + Haiku/Sonnet shims | 42 |
| A3 AGENT_BOUNDED | ≤$1 | LangGraph + CrewAI + guardrails | 42 |
| A4 LLM_AGENT_FREE | ≤$50+4h | Opus crews + falsification | 21 |

BMS auto-selects mode per cell. Escalation: A1→A2→A3→A4 on failure.

Full reference: [`docs/rig-lattice-architecture.md→`](docs/rig-lattice-architecture.md)

**CLI:**
```bash
rig-strategy-studio lattice modes          # A1-A4 cost bands
rig-strategy-studio lattice list-cells     # List cell IDs
rig-strategy-studio cells all-cards        # All 147 Build Cards
rig-strategy-studio orchestrator pipeline   # Full IQRSQPI run
```

## Live State

| Field | Value |
| --- | --- |
| GitHub | https://github.com/rodgemd1-lgtm/strategy-studio |
| QNAP canonical/mirror | `ssh://git@nas94f2ae.tail4d96b3.ts.net:2222/rig/strategy-studio.git` |
| Lane | `rig-core` - RIG/Jake/Hermes/Deviator operating system |
| Visibility | `public` |
| Primary language | `Python` |
| Last pushed | `2026-05-26T02:34:27Z` |
| QNAP status | `imported_to_qnap_gitea` |
| QNAP HEAD | `340b4e41f406` |
| Consolidation action | `keep-separate-public` |
| Canonical target | `strategy-studio` |

## Doctrine Spine

- README standard: [github-readme-standard.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/github-readme-standard.md)
- Repo deep dive: [strategy-studio](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-deep-dives/strategy-studio.md)
- GitHub estate map: [github-estate.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/github-estate.md)
- Source of truth: [source-of-truth.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/source-of-truth.md)
- Consolidation queue: [repo-consolidation-plan.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-consolidation-plan.md)
- Source-truth hygiene: [source-truth-hygiene.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/operator/source-truth-hygiene.md)

## What This Repo Contains

37 data/config/knowledge-like files; 22 docs/notes; 24 media/design assets; 0 sensitive-path-name matches.

Detected manifests:

- `pyproject.toml`

Detected runtime/build signals:

- Documentation corpus
- FastAPI service
- Scripted automation

## File Map

199 tracked files across 44 directories. Code files: 121. Test files: 16. 37 data/config/knowledge-like files; 23 docs/notes; 24 media/design assets; 0 sensitive-path-name matches.

Aggregate GitHub tree size: `9.4 MB` across `203` blobs.
GitHub recursive tree truncated: `false`.

Top directory size map:

| Root | Bytes | Files |
| --- | ---: | ---: |
| `.` | 6.5 MB | 15 |
| `apps` | 830.4 KB | 19 |
| `strategy_studio` | 581.5 KB | 83 |
| `docs` | 520.3 KB | 15 |
| `inputs` | 322.3 KB | 2 |
| `examples` | 289.2 KB | 22 |
| `scripts` | 214.6 KB | 14 |
| `tests` | 61.5 KB | 16 |
| `.codex` | 50.0 KB | 10 |
| `demo_output` | 27.2 KB | 3 |
| `services` | 13.4 KB | 1 |
| `startup-os` | 8.5 KB | 3 |

Top tracked directories or roots:

- `strategy_studio (83)`
- `examples (22)`
- `apps (19)`
- `tests (16)`
- `docs (14)`
- `scripts (13)`
- `. (12)`
- `.codex (10)`
- `demo_output (3)`
- `startup-os (3)`
- `inputs (2)`
- `services (1)`

Dominant file extensions:

- `.py`: 113
- `.md`: 22
- `.png`: 19
- `.json`: 8
- `.html`: 5
- `.excalidraw`: 5
- `.svg`: 5
- `[none]`: 4
- `.jsonl`: 3
- `.sh`: 3
- `.toml`: 2
- `.icns`: 2

Full public inventory: [strategy-studio.txt](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-file-inventories/strategy-studio.txt)

Private repo note: central public estate docs must not expose raw private paths. This repo README uses aggregate counts, categories, and proof links unless Mike approves deeper disclosure.

## Runtime / Topology

```text
                 Blackwell GPU lane
                        |
rig-256gb ---- rig-48gb cockpit ---- rig-28gb audit
    |              |                  |
rig-96gb ----- QNAP / Gitea ----- rig-36gb sensor
                        |
                 GitHub mirror
```

## Provider And Fallback Protocol

| Rank | Provider / lane | Use | Proof needed |
| ---: | --- | --- | --- |
| 1 | A1 deterministic Python | Known, repeatable decisions | tests + ProofPacket |
| 2 | Local RIG mesh via LiteLLM/Open WebUI | Default coding/orchestration | health check + route log |
| 3 | Blackwell vLLM | Deep local reasoning/build review | model health + smoke proof |
| 4 | QNAP/Phronema LakeOS | Private context and retrieval | cited source paths |
| 5 | Susan specialist roster | Capability/team routing | agent transcript + decision proof |
| 6 | OpenClaw/Jake bounded agent lane | Governed execution | queue row + proof packet |
| 7 | Pi/PyCoding lane | Local coding helper | diff + test output |
| 8 | Claude/Codex paid burst | Frontier reasoning when needed | prompt, result, validation |
| 9 | OpenRouter/free fallback | Low-cost exploration | model ID + validation |
| 10 | Browser/Playwright tools | UI verification | screenshot/log artifact |
| 11 | Human approval | Public/destructive/sensitive actions | approval note + audit row |

## Setup

```bash
git clone ssh://git@nas94f2ae.tail4d96b3.ts.net:2222/rig/strategy-studio.git
cd strategy-studio
# Install using the package manager or runtime detected above.
```

## Verify

```bash
# Run repo-specific tests, lint, typecheck, build, or smoke commands.
# If no command exists yet, add one before promoting this README to final.
```

## Release And Proof Protocol

1. Work on a branch with a clear prefix.
2. Run setup and verification commands.
3. Record a ProofPacket with commit SHA, checks, artifacts, and rollback path.
4. Push to QNAP Gitea first.
5. Verify GitHub mirrors the same result.

## Data And Security Boundary

- Visibility: `public`.
- Never commit secrets, tokens, cookies, browser state, raw credentials, or unapproved private exports.
- Private data should be referenced by source path, count, category, or fingerprint unless the repo itself is the approved private home.

## Roadmap

- V0: Repo exists and is mirrored.
- V1: Cold-reader README explains purpose, setup, verification, and proof.
- V2: File map, data boundary, and branch policy are documented.
- V3: CLI/MCP contracts are explicit where the repo owns tools.
- V4: Tests, smoke checks, and deployment protocol are reproducible.
- V5: ProofPacket path records every release or meaningful migration.
- V6: Consolidation action is resolved: `keep-separate-public`.
- V7: Source cards and capability manifests feed Jake/Susan routing.
- V8: Monitoring and branch hygiene are automated.
- V9: Repo is boring to operate because all paths are canonical.
- V10: Repo is either a clean canonical product surface or archived with proof.

## What Is Left

- Add or maintain a cold-reader README, setup command, test command, and ProofPacket path.
- Keep GitHub topics, description, QNAP mirror, and consolidation status current.

---

README applied from the central RIG blueprint.
- Blueprint source: `https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-readme-blueprints/strategy-studio.md`
- Applied target: `strategy-studio`
- Source of truth: QNAP Gitea first, GitHub mirror second.

<!-- RIG-CLI:START -->
## Install The CLI

This repo exposes a standard RIG command so it can be installed, inspected,
cloned, and routed into future studio/MCP workflows without guessing its
internal layout.

Install without cloning:

```bash
curl -fsSL https://github.com/rodgemd1-lgtm/strategy-studio/raw/main/install.sh | bash
```

Install and clone the source-of-truth repo:

```bash
curl -fsSL https://github.com/rodgemd1-lgtm/strategy-studio/raw/main/install.sh | RIG_CLI_CLONE=1 bash
```

Use it:

```bash
strategy-studio info
strategy-studio capabilities
strategy-studio services
strategy-studio clone
strategy-studio doctor
```

Clone manually:

```bash
git clone ssh://git@nas94f2ae.tail4d96b3.ts.net:2222/rig/strategy-studio.git
git clone https://github.com/rodgemd1-lgtm/strategy-studio.git
```

CLI contract:

- Command: `strategy-studio`
- Manifest: `cli/manifest.json`
- Installer: `install.sh`
- Source of truth: QNAP Gitea first, GitHub mirror second
- Standard: [https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-cli-standard.md](https://github.com/rodgemd1-lgtm/Startup-Intelligence-OS/blob/claude/rig-sovereign-audit-mesh/docs/repositories/repo-cli-standard.md)

<!-- RIG-CLI:END -->

<!-- AGENTFORGE:WORKFLOWS START -->
## AgentForge Workflows

**Repo maturity:** `86.32 / 100`

### 10x Plan


**Visual workflow designer:** [.agentforge/workflows.html](.agentforge/workflows.html)

### Workflows (editable)

> These workflows live in the README and are editable here. Each is a `WorkflowDoc` (`name` · BMS mode · ordered steps) that round-trips losslessly with the visual designer and the agent IR.

#### 1. AGENTS  `A4`

_A4 · LLM-agent-free (crew)_

1. Evidence required: min 2 cited sources per claim
2. Falsification gate: strategy outputs must have falsification packet
3. Proof packet: every external send needs a strategy proof packet
4. UNKNOWN policy: if LakeOS has no cited result, return UNKNOWN + request indexing

#### 2. AGENTS  `A1`

_A1 · Python-only (deterministic)_

1. LakeOS CLI: /Users/mikerodgers/rig-lab/phronema/scripts/lakeoscli.py
2. LakeOS REST: http://127.0.0.1:8788
3. Recall API: https://backend.getrecall.ai/api/v1
4. QNAP Lake: /Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake

#### 3. AGENTS  `A1`

_A1 · Python-only (deterministic)_

1. Map concepts to shape arrangements (fan-out, timeline, convergence, decision, feedback loops).
2. Embed concrete evidence artifacts (code snippets, JSON payloads, event names, API shapes).
3. After writing the .excalidraw file, run the render pipeline to produce a PNG,
4. Brand colors live in .codex/skills/excalidraw-diagram/references/color-palette.md.

#### 4. Strategy Process Domain  `A4`

_A4 · LLM-agent-free (crew)_

1. Strategy Synthesis (B29) — evidence → ranked options
2. Market Wargame (B36) — competitor moves → RIG responses
3. Competitor Intelligence (B42) — competitor changes → response options
4. Client Intelligence (B41) — prospect evidence → wedge offers
5. Prediction Crux (B34) — questions → forecast variables
6. Falsification (B33) — beliefs → disprove tests
7. Consensus Delta (B31) — new research → belief updates
8. GTM Planning — strategy → go-to-market plans

#### 5. Per-prospect Codex workflow  `A4`

_A4 · LLM-agent-free (crew)_

1. LakeOS query   → company facts (employees, revenue, HQ, industry, capabilities)
2. recall.it search → industry analog + comparable transaction
3. Web research    → CEO / strategy lead / functional buyer (contactname + role)
4. Synthesis       → wound, mechanismname, mechanismdescription (NEVER generic)
5. Three engines  → product line × flywheel type × revenue target (must cite source)
6. Three threats  → Tier 1/2/3 with horizon + keyfact + SW score
7. Three disqualifiers → reasons RIG would walk
8. Three advantages → things they don't see in themselves
9. Validate against TeaserInput schema
10. Append to prospects2000.jsonl

#### 6. teaser-runbook  `A1`

_A1 · Python-only (deterministic)_

1. index.html — drops onto the prospect's cloned site as the homepage hero/wedge
2. teaser.md — for cold email body, LinkedIn DM thread starter, or PDF render
3. teaserinput.json — input snapshot (audit trail)
4. proofpacket.json — ProofPacket + FalsificationPacket + quality result

#### 7. teaser-runbook  `A3`

_A3 · Agent-bounded (budget-capped)_

1. Pydantic extra="forbid" rejects unknown fields → no silent typos
2. minlength / maxlength enforces 3 advantages, 3 engines, 3 threats, 3 disqualifiers
3. evidencesources requires at least 2 entries → RIG min-2-source rule
4. confidence must be H/M/L → forces explicit downgrade when evidence is weak
5. ProofPacket auto-generated → every external send has audit trail
6. FalsificationPacket auto-generated per engine → "what would prove this wrong"

#### 8. strategy  `A1`

_A1 · Python-only (deterministic)_

1. S0
2. S1
3. S2
4. S3
5. S4
6. S5
7. S6
8. S7
9. S8
10. S9
11. S10
12. S11
13. S12
14. S13
15. S14
16. S15
17. S16
18. S17
19. S18
20. S19
21. S20
22. S21
23. S22
24. S23
25. S24
26. S25
<!-- AGENTFORGE:WORKFLOWS END -->
