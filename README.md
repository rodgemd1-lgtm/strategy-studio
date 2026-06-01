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

#### 1. AGENTS  `A1`

_A1 · Python-only (deterministic)_

1. LakeOS CLI: /Users/mikerodgers/rig-lab/phronema/scripts/lakeoscli.py
2. LakeOS REST: http://127.0.0.1:8788
3. Recall API: https://backend.getrecall.ai/api/v1
4. QNAP Lake: /Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake

#### 2. AGENTS  `A1`

_A1 · Python-only (deterministic)_

1. Map concepts to shape arrangements (fan-out, timeline, convergence, decision, feedback loops).
2. Embed concrete evidence artifacts (code snippets, JSON payloads, event names, API shapes).
3. After writing the .excalidraw file, run the render pipeline to produce a PNG,
4. Brand colors live in .codex/skills/excalidraw-diagram/references/color-palette.md.

#### 3. AGENTS  `A4`

_A4 · LLM-agent-free (crew)_

1. Evidence required: min 2 cited sources per claim
2. Falsification gate: strategy outputs must have falsification packet
3. Proof packet: every external send needs a strategy proof packet
4. UNKNOWN policy: if LakeOS has no cited result, return UNKNOWN + request indexing

#### 4. Per-prospect Codex workflow  `A4`

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

#### 5. Strategy Process Domain  `A4`

_A4 · LLM-agent-free (crew)_

1. Strategy Synthesis (B29) — evidence → ranked options
2. Market Wargame (B36) — competitor moves → RIG responses
3. Competitor Intelligence (B42) — competitor changes → response options
4. Client Intelligence (B41) — prospect evidence → wedge offers
5. Prediction Crux (B34) — questions → forecast variables
6. Falsification (B33) — beliefs → disprove tests
7. Consensus Delta (B31) — new research → belief updates
8. GTM Planning — strategy → go-to-market plans

#### 6. strategy  `A1`

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

#### 7. teaser-runbook  `A3`

_A3 · Agent-bounded (budget-capped)_

1. Pydantic extra="forbid" rejects unknown fields → no silent typos
2. minlength / maxlength enforces 3 advantages, 3 engines, 3 threats, 3 disqualifiers
3. evidencesources requires at least 2 entries → RIG min-2-source rule
4. confidence must be H/M/L → forces explicit downgrade when evidence is weak
5. ProofPacket auto-generated → every external send has audit trail
6. FalsificationPacket auto-generated per engine → "what would prove this wrong"

#### 8. teaser-runbook  `A1`

_A1 · Python-only (deterministic)_

1. index.html — drops onto the prospect's cloned site as the homepage hero/wedge
2. teaser.md — for cold email body, LinkedIn DM thread starter, or PDF render
3. teaserinput.json — input snapshot (audit trail)
4. proofpacket.json — ProofPacket + FalsificationPacket + quality result

#### 9. lattice-cell-route  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. parse_question
2. classify_altitude
3. classify_diamond
4. map_iqrsqpi_step
5. resolve_cell_id
6. emit_routing_record

#### 10. bms-mode-select  `A1`

_A1 · Python-only (deterministic)_

1. load_cell
2. read_cost_band
3. estimate_complexity
4. check_bms_threshold
5. assign_mode
6. record_decision

#### 11. bms-escalation-ladder  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. run_current_mode
2. check_done_contract
3. on_fail_check_cost_cap
4. escalate_one_band
5. re_run
6. seal_or_halt

#### 12. iqrsqpi-pipeline-run  `A3`

_A3 · Agent-bounded (budget-capped)_

1. intent_capture
2. question_frame
3. research_gather
4. solution_synthesize
5. quality_gate
6. proof_seal
7. integrate_memory

#### 13. archetype-dispatch  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_intent_map
2. select_archetype
3. bind_engines
4. execute_archetype
5. collect_outputs
6. return_envelope

#### 14. run-envelope-create  `A1`

_A1 · Python-only (deterministic)_

1. load_context
2. init_run_id
3. define_done_contract
4. set_cost_cap
5. attach_kill_criteria
6. persist_envelope

#### 15. intent-map-resolve  `A1`

_A1 · Python-only (deterministic)_

1. detect_domain
2. load_intent_yaml
3. map_intents_to_engines
4. validate_coverage
5. emit_plan

#### 16. orchestrator-parallel-fanout  `A3`

_A3 · Agent-bounded (budget-capped)_

1. partition_cells
2. spawn_workers
3. run_parallel
4. collect_results
5. reconcile_conflicts
6. merge_envelope

#### 17. omniscout-daily-cycle  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_source_registry
2. run_collectors
3. dedupe_items
4. score_freshness
5. write_adtb
6. emit_digest

#### 18. arxiv-collect  `A1`

_A1 · Python-only (deterministic)_

1. query_arxiv
2. fetch_metadata
3. parse_abstracts
4. tag_topics
5. write_heb
6. register_source

#### 19. github-signal-collect  `A1`

_A1 · Python-only (deterministic)_

1. query_repos
2. fetch_commits_releases
3. extract_signals
4. score_relevance
5. write_adtb
6. register_source

#### 20. web-evidence-collect  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. resolve_urls
2. fetch_pages
3. extract_text
4. cite_sources
5. score_quality
6. write_lake

#### 21. prediction-market-collect  `A1`

_A1 · Python-only (deterministic)_

1. query_markets
2. fetch_contracts
3. normalize_probabilities
4. map_to_questions
5. write_priors
6. register_source

#### 22. internal-docs-ingest  `A1`

_A1 · Python-only (deterministic)_

1. enumerate_docs
2. chunk_content
3. embed_or_index
4. tag_provenance
5. write_lake
6. update_registry

#### 23. lakeos-retrieve  `A1`

_A1 · Python-only (deterministic)_

1. build_query
2. call_lakeos
3. check_results
4. on_empty_return_unknown
5. cite_sources
6. return_evidence

#### 24. recall-evidence-pull  `A1`

_A1 · Python-only (deterministic)_

1. auth_recall
2. fetch_latest_or_ids
3. filter_relevant
4. normalize
5. cite
6. merge_evidence

#### 25. source-registry-sync  `A1`

_A1 · Python-only (deterministic)_

1. load_registry
2. diff_collected
3. add_new_sources
4. flag_stale
5. write_registry
6. emit_report

#### 26. evidence-score  `A1`

_A1 · Python-only (deterministic)_

1. load_items
2. score_authority
3. score_recency
4. score_independence
5. rank_items
6. emit_scores

#### 27. contradiction-detect  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_evidence
2. cluster_claims
3. compare_pairs
4. flag_contradictions
5. rank_severity
6. emit_report

#### 28. evidence-graph-build  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. extract_claims
2. link_evidence
3. build_nodes_edges
4. score_support
5. render_graph
6. persist

#### 29. unknown-policy-enforce  `A1`

_A1 · Python-only (deterministic)_

1. check_claim_citations
2. count_sources
3. if_below_min_flag_unknown
4. emit_indexing_request
5. block_output

#### 30. calibration-curve-build  `A1`

_A1 · Python-only (deterministic)_

1. load_resolved
2. bucket_by_confidence
3. compute_hit_rate
4. fit_curve
5. render_reliability
6. persist

#### 31. brier-monitor  `A1`

_A1 · Python-only (deterministic)_

1. load_scores
2. compute_rolling_brier
3. compare_baseline
4. detect_drift
5. emit_alert
6. log_metric

#### 32. bayesian-update  `A1`

_A1 · Python-only (deterministic)_

1. load_prior
2. ingest_new_evidence
3. compute_likelihood_ratio
4. apply_bayes
5. record_posterior
6. log_delta

#### 33. b29-strategy-synthesize  `A4`

_A4 · LLM-agent-free (crew)_

1. gather_evidence
2. frame_objective
3. generate_options
4. score_options
5. rank
6. seal_synthesis

#### 34. b31-consensus-delta  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_current_consensus
2. ingest_new_research
3. compute_delta
4. flag_belief_shifts
5. update_consensus
6. log

#### 35. b33-falsify  `A4`

_A4 · LLM-agent-free (crew)_

1. state_belief
2. enumerate_disconfirmers
3. design_tests
4. run_or_simulate
5. score_survival
6. seal_falsification_packet

#### 36. b37-risk-assess  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_strategy
2. enumerate_risks
3. score_likelihood
4. score_impact
5. rank_matrix
6. emit_register

#### 37. b40-market-sizing  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. gather_inputs
2. select_method
3. compute_tam_sam_som
4. sensitivity_bands
5. cite_sources
6. emit_sizing

#### 38. b43-competitive-positioning  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_competitors
2. define_axes
3. plot_positions
4. find_whitespace
5. recommend_position
6. render_map

#### 39. b44-timeline-plan  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_objectives
2. decompose_milestones
3. map_dependencies
4. assign_durations
5. critical_path
6. emit_timeline

#### 40. b45-budget-allocate  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_initiatives
2. estimate_costs
3. set_constraints
4. optimize_allocation
5. sensitivity
6. emit_budget

#### 41. b46-impact-assess  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_decision
2. define_metrics
3. model_impact
4. range_scenarios
5. score_confidence
6. emit_assessment

#### 42. forecast-lifecycle-run  `A3`

_A3 · Agent-bounded (budget-capped)_

1. capture_signals
2. set_priors
3. build_ensemble
4. emit_forecast
5. await_resolution
6. score_record

#### 43. prediction-crux  `A4`

_A4 · LLM-agent-free (crew)_

1. frame_question
2. decompose_cruxes
3. identify_drivers
4. assign_variables
5. rank_sensitivity
6. emit_cruxes

#### 44. market-prior-extract  `A1`

_A1 · Python-only (deterministic)_

1. map_question_to_markets
2. fetch_market_probs
3. blend_priors
4. weight_by_liquidity
5. emit_prior
6. cite

#### 45. ensemble-aggregate  `A3`

_A3 · Agent-bounded (budget-capped)_

1. collect_member_forecasts
2. score_member_track_records
3. weight_members
4. aggregate
5. compute_dispersion
6. emit_ensemble

#### 46. missing-info-score  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_question
2. enumerate_unknowns
3. score_info_value
4. rank_gaps
5. emit_indexing_requests
6. block_if_critical

#### 47. causal-thesis-tree  `A4`

_A4 · LLM-agent-free (crew)_

1. state_thesis
2. build_causal_nodes
3. add_inversion_tests
4. add_friction_points
5. score_fragility
6. render_tree

#### 48. forecast-resolution  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_open_forecast
2. fetch_outcome
3. mark_resolved
4. compute_brier_log
5. write_postmortem
6. update_calibration

#### 49. forecast-postmortem  `A4`

_A4 · LLM-agent-free (crew)_

1. load_resolved
2. diff_prior_vs_outcome
3. identify_errors
4. extract_lessons
5. update_priors
6. log_lessons

#### 50. b36-market-wargame  `A4`

_A4 · LLM-agent-free (crew)_

1. load_market_state
2. enumerate_competitor_moves
3. simulate_rounds
4. generate_rig_responses
5. score_outcomes
6. seal_wargame

#### 51. b42-competitor-intel  `A4`

_A4 · LLM-agent-free (crew)_

1. collect_competitor_signals
2. detect_changes
3. assess_threat
4. generate_response_options
5. rank
6. emit_brief

#### 52. b41-client-intel  `A4`

_A4 · LLM-agent-free (crew)_

1. gather_prospect_evidence
2. identify_pain
3. map_wedge
4. draft_offer_angles
5. score_fit
6. emit_wedge_brief

#### 53. competitor-move-watch  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_watchlist
2. poll_signals
3. diff_state
4. flag_material_moves
5. notify
6. log

#### 54. wargame-counter-move-tree  `A4`

_A4 · LLM-agent-free (crew)_

1. define_actors
2. set_payoffs
3. expand_move_tree
4. prune_dominated
5. find_equilibria
6. render_tree

#### 55. client-account-dossier  `A3`

_A3 · Agent-bounded (budget-capped)_

1. gather_firmographics
2. pull_evidence
3. map_stakeholders
4. identify_triggers
5. synthesize_dossier
6. cite

#### 56. mcda-decision-run  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_options
2. define_criteria
3. weight_criteria
4. score_matrix
5. rank_options
6. emit_recommendation

#### 57. sensitivity-tornado  `A1`

_A1 · Python-only (deterministic)_

1. load_decision_model
2. vary_inputs
3. measure_swing
4. rank_drivers
5. render_tornado
6. emit_report

#### 58. value-of-information  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_decision
2. enumerate_info_items
3. model_outcome_shift
4. compute_voi
5. rank_items
6. recommend_gather

#### 59. decision-record-seal  `A1`

_A1 · Python-only (deterministic)_

1. load_decision
2. capture_rationale
3. attach_evidence
4. record_dissent
5. seal_record
6. persist

#### 60. decision-room-session  `A3`

_A3 · Agent-bounded (budget-capped)_

1. frame_decision
2. load_options
3. run_mcda
4. run_sensitivity
5. run_voi
6. seal_decision_record

#### 61. board-deck-generate  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_analysis
2. outline_narrative
3. select_slide_types
4. generate_charts
5. assemble_deck
6. export_html

#### 62. exec-summary-generate  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_analysis
2. extract_key_points
3. draft_summary
4. tighten_length
5. cite_sources
6. emit_doc

#### 63. pptx-export  `A1`

_A1 · Python-only (deterministic)_

1. load_deck_spec
2. map_to_slides
3. build_pptx
4. embed_charts
5. validate_file
6. write_output

#### 64. excalidraw-strategy-map  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. map_concepts_to_shapes
2. place_evidence_artifacts
3. write_excalidraw
4. render_png
5. inspect_layout
6. iterate_fix

#### 65. hed-walkthrough-build  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_topic
2. outline_hierarchy
3. write_sections
4. embed_diagrams
5. cross_link
6. emit_hed

#### 66. visual-strategy-map-render  `A1`

_A1 · Python-only (deterministic)_

1. select_layout_archetype
2. bind_data
3. compute_positions
4. render_svg
5. export_png
6. persist

#### 67. output-studio-bundle  `A1`

_A1 · Python-only (deterministic)_

1. collect_artifacts
2. validate_completeness
3. bundle_manifest
4. attach_proofpacket
5. zip_bundle
6. emit_path

#### 68. teaser-generate  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_prospect
2. pull_wedge_brief
3. fill_templates
4. render_assets
5. validate
6. emit_teaser

#### 69. teaser-batch-run  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_prospect_jsonl
2. partition_batches
3. run_per_prospect
4. collect_outputs
5. write_failed_log
6. emit_summary

#### 70. gtm-pack-build  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_strategy
2. segment_prospects
3. generate_messaging
4. assemble_pack
5. attach_evidence
6. emit_pack

#### 71. regional-gtm-pack  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_region_inputs
2. filter_prospects
3. localize_messaging
4. build_workbook
5. validate
6. emit_workbook

#### 72. industry-playbook-apply  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. select_industry
2. load_playbook_kpis
3. benchmark_target
4. select_strategic_options
5. tailor
6. emit_plan

#### 73. gtm-campaign-generate  `A3`

_A3 · Agent-bounded (budget-capped)_

1. load_context
2. create_run_envelope
3. create_done_contract
4. generate_campaign
5. kill_criteria_check
6. seal_proofpacket
7. approval_gate
8. memory_update

#### 74. twenty-crm-sync  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_records
2. map_to_twenty_schema
3. diff_existing
4. upsert_records
5. verify_write
6. log_sync

#### 75. prospect-import-bulk  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_prospect_jsonl
2. validate_rows
3. dedupe_against_crm
4. batch_upsert
5. verify_counts
6. emit_report

#### 76. gtm-crm-launch  `A1`

_A1 · Python-only (deterministic)_

1. check_env
2. start_service
3. health_probe
4. seed_data
5. confirm_ready
6. log_launch

#### 77. artifact-serve  `A1`

_A1 · Python-only (deterministic)_

1. collect_artifacts
2. build_index
3. start_server
4. expose_url
5. log_access
6. on_stop_teardown

#### 78. external-send-gate  `A4`

_A4 · LLM-agent-free (crew)_

1. load_deliverable
2. verify_proofpacket
3. verify_falsification
4. human_approval_gate
5. send
6. log_receipt

#### 79. proofpacket-seal  `A1`

_A1 · Python-only (deterministic)_

1. collect_inputs
2. hash_artifacts
3. attach_citations
4. record_costs
5. sign_packet
6. persist

#### 80. falsification-packet-build  `A4`

_A4 · LLM-agent-free (crew)_

1. state_claim
2. list_disconfirmers
3. design_tests
4. record_results
5. score_survival
6. seal_packet

#### 81. kill-criteria-check  `A1`

_A1 · Python-only (deterministic)_

1. load_kill_criteria
2. measure_signals
3. compare_thresholds
4. decide_continue_or_kill
5. log_decision
6. on_kill_halt

#### 82. approval-gate  `A4`

_A4 · LLM-agent-free (crew)_

1. assemble_review_bundle
2. present_to_human
3. capture_decision
4. on_approve_proceed
5. on_reject_loopback
6. log

#### 83. drift-track  `A1`

_A1 · Python-only (deterministic)_

1. load_baseline
2. load_current
3. compute_drift
4. flag_material_drift
5. emit_drift_report
6. update_baseline

#### 84. memory-update  `A1`

_A1 · Python-only (deterministic)_

1. collect_decisions
2. dedupe_against_memory
3. write_records
4. update_index
5. confirm_persisted
6. log

#### 85. quality-gate-run  `A1`

_A1 · Python-only (deterministic)_

1. load_output
2. check_evidence_min
3. check_falsification
4. check_proofpacket
5. score_quality
6. pass_or_block

#### 86. config-manage  `A1`

_A1 · Python-only (deterministic)_

1. load_config
2. validate_keys
3. apply_change
4. persist
5. emit_effective_config

#### 87. cli-command-dispatch  `A1`

_A1 · Python-only (deterministic)_

1. parse_args
2. resolve_command
3. bind_options
4. invoke_handler
5. format_output
6. return_json

#### 88. cli-wizard-session  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. greet
2. collect_intent
3. suggest_archetype
4. confirm_options
5. run_session
6. present_results

#### 89. session-lifecycle-run  `A3`

_A3 · Agent-bounded (budget-capped)_

1. init_session
2. resolve_intent_map
3. run_pipeline
4. collect_deliverables
5. seal_proofpacket
6. close_session

#### 90. eval-harness-run  `A2`

_A2 · Hybrid (schema-constrained LLM)_

1. load_eval_cases
2. run_engines
3. score_outputs
4. compare_baseline
5. emit_eval_report
6. flag_regressions

#### 91. build-card-generate  `A1`

_A1 · Python-only (deterministic)_

1. load_cells
2. resolve_engine_bindings
3. render_card_spec
4. validate_schema
5. write_cards
6. emit_index

#### 92. card-workflow-verify  `A1`

_A1 · Python-only (deterministic)_

1. load_cards
2. load_workflows
3. match_steps
4. flag_mismatches
5. emit_verification_report
6. exit_code

#### 93. contract-version-bump  `A1`

_A1 · Python-only (deterministic)_

1. load_current_contract
2. diff_schema
3. bump_version
4. write_migration
5. validate_back_compat
6. publish
<!-- AGENTFORGE:WORKFLOWS END -->
