# RIG Strategy Studio v10 — Spec

**Goal:** Deterministic, cold-start reliable, fully verifiable from any new Hermes session with no prior context. Every workflow produces a ProofPacket. No fabrication. No LLM in A1 decision path.

---

## PART 1: ARCHITECTURE

```
Strategy Studio (strategy-studio repo)
├── strategy_studio/
│   ├── __init__.py                  # Re-exports all public types
│   ├── core/
│   │   ├── types.py                 # Frozen types: Evidence, Option, Synthesis, etc.
│   │   └── types_extended.py        # 20 extended types: StrategyReport, EvidenceGraph, etc.
│   ├── lattice_wire.py              # CANONICAL source: 806 lines
│   │       Altitude (L1-L7)
│   │       Diamond (D1-D3)
│   │       IQRSQPIStep (I1,Q1,R,S,Q2,P,I2)
│   │       BuildMode (A1-A4)
│   │       compute_bms()            # BMS rubric scoring
│   │       LatticeCell              # frozen dataclass
│   │       BuildCard               # Pydantic model per cell
│   │       ProofPacket             # audit + output hash + escalation
│   │       LatticeOrchestrator     # executes IQRSQPI pipeline
│   │       route_company()         # NEW: deterministic company→cell routing
│   │       run_quality_gates()     # GateResult per cell
│   │       lattice_summary()        # aggregate stats
│   │       generate_lattice_map()  # Excalidraw JSON export
│   ├── archetypes/
│   │   ├── a1/                     # 7 real sub-modules, no stubs
│   │   ├── a2/                     # Hybrid with LLM fallback
│   │   ├── a3/                     # Agent-bounded with LangGraph
│   │   └── a4/                     # Strict deterministic
│   ├── engines/                    # 13 B-engines, all real
│   │   ├── b29_synthesize.py       # synthesize_evidence()
│   │   ├── b31_consensus_delta.py  # calculate_consensus_delta()
│   │   ├── b33_falsify.py          # falsify_claim()
│   │   ├── b34_predict.py          # build_forecast()
│   │   ├── b36_wargame.py          # run_wargame()
│   │   ├── b37_risk_assessment.py  # assess_risks()
│   │   ├── b40_market_sizing.py    # size_market()
│   │   ├── b41_client_intel.py     # generate_wedge(), score_prospect()
│   │   ├── b42_competitor_intel.py # analyze_competitor(), assess_threat_level()
│   │   ├── b43_competitive_positioning.py # position_competitively()
│   │   ├── b44_timeline_planning.py # plan_timeline()
│   │   ├── b45_budget_allocation.py # allocate_budget()
│   │   └── b46_impact_assessment.py # assess_impact()
│   ├── hermes/                     # BMS, OpenClaw, orchestrator, router, Brier
│   ├── langgraph_executor.py        # A3/A4 StateGraph execution
│   ├── scrapers.py                  # ScraperOrchestrator (real)
│   ├── session.py                   # StrategySession end-to-end
│   ├── data_pipeline.py             # Financial data pipeline
│   ├── resolve_archetype.py         # Resolves company→archetype
│   ├── archon.py                    # Per-cell quality gates
│   ├── validator.py                 # Pydantic validation
│   └── studios/                     # 6 studios + prediction_studio/
│       ├── decision_room.py        # Decision matrix + recommendation
│       ├── evidence_engine.py      # EvidenceGraph, contradictions
│       ├── synthesis_pipeline.py   # Cross-archetype, meta-analysis
│       ├── calibration_engine.py   # Calibration records + Brier scoring
│       ├── output_studio.py        # Report generation + HTML export
│       ├── prediction_studio/      # Core + ensemble + scoring + priors
│       └── prediction_studio_legacy.py # Monte Carlo + scenarios
├── cli.py                           # Click CLI entrypoint
├── server.py                       # FastAPI server
├── tests/                          # 309+ passing tests
│   ├── test_lattice_sio.py         # All 147 cells resolve
│   ├── test_geometry_sio.py        # Geometry gate tests
│   ├── test_system_e2e_sio.py      # E2E integration tests
│   ├── test_archon.py             # Quality gate tests
│   ├── test_prediction_studio.py  # Prediction model tests
│   └── test_scrapers.py           # Scraper tests
└── artifacts/
    ├── build_cards.json           # All 147 BuildCards
    ├── lattice_map.json           # Excalidraw visualization
    └── rig_engines_v3/            # 40 Deviation Engine criteria YAML
```

---

## PART 2: GAPS vs. CURRENT STATE

### G1 — DEDUP: rig_lattice.py duplicates lattice_wire.py
**Status:** Duplicate axis definitions (Altitude, Diamond, IQRSQPIStep, BuildMode, BMS, compute_bms) exist in both files. `rig_lattice.py` also defines `ArchetypeExecutor` which is NOT wired anywhere in the system.
**Fix:** Delete `rig_lattice.py`. `lattice_wire.py` is canonical.
**Risk if not fixed:** Two sources of truth for the lattice coordinate system.

### G2 — MISSING: route_company()
**Status:** Referenced in tests but never existed.
**Fix:** Build deterministic function: company name + industry + size → LatticeCell + BMSScore.
**Signature:** `def route_company(name: str, industry: str, size: str) -> RouteResult`
**Implementation:** Keyword classifiers for industry → Diamond mapping; size + industry keywords → Altitude mapping; Altitude → BMS mode selection.

### G3 — COLD-START RECEIPT SYSTEM
**Status:** `LatticeOrchestrator` builds `ProofPacket` per cell execution but nothing persists across sessions. No receipt per run.
**Fix:** Build `ColdStartReceipt` — written to `~/.strategy-studio/receipts/{run_id}.json` on every full pipeline run. Contains: run_id, cell_ids executed, BMS score, ProofPacket IDs, output hashes, status per step, escalation count.

### G4 — DETERMINISTIC CLI
**Status:** `cli.py` uses sample data (`_make_sample_evidence`, `_make_sample_options`) for most commands. No real input path.
**Fix:** `cli.py` → `--input-file` flag for real evidence JSON. `full` command wires to real `StrategySession` with actual inputs. Add `--no-sample` guard that errors if no real input provided.

### G5 — COLD-START INTEGRATION TEST
**Status:** No test that proves the system works from a completely clean import.
**Fix:** `tests/test_cold_start.py` — imports the package fresh, calls `route_company()` on 3 test inputs, verifies cell IDs, verifies BMS scores, verifies `LatticeOrchestrator.execute_full_pipeline()` returns consistent output, verifies receipts written to disk.

### G6 — ARCHON QUALITY GATE WIRING
**Status:** `lattice_wire.py` has `run_quality_gates()` but `session.py` never calls it in the lattice pipeline.
**Fix:** Wire `run_quality_gates()` into `LatticeOrchestrator.execute_cell()` — already there, but `session.py` doesn't use the orchestrator's gate results. Fix session to surface gate results in the final report.

### G7 — PREDICTION STUDIO WIRING
**Status:** `session.py` references `predict_variable` but the import comment says "replaced by new v2 module". Check if the v2 module has it.
**Fix:** Verify `prediction_studio/core.py` has `predict_variable`. If not, use `prediction_studio_legacy.py`'s `predict_variable`. Wire correctly.

### G8 — SCRAPER GRACEFUL DEGRADATION
**Status:** `session.py` wraps scraper calls in `try/except pass` — this is correct for degradation, but not documented. Add `--no-enrich` flag to CLI to disable scraping.
**Fix:** Add `--no-enrich` to CLI. Document scraper fallback behavior.

---

## PART 3: DETERMINISTIC INVARIANTS

These must hold in EVERY session from cold start:

1. **Cell ID consistency:** `LatticeCell.parse(cell.cell_id) == cell` for all 147 cells
2. **BMS mode determinism:** `compute_bms(altitude=L1).select_mode() == A1` always
3. **IQRSQPI order:** pipeline always executes [I1, Q1, R, S, Q2, P, I2] in that order
4. **No fabrication:** A1 never returns content it didn't derive from input
5. **ProofPacket traceable:** every packet has input_hash + output_hash
6. **Receipt persistence:** every full pipeline run writes a receipt JSON
7. **Escalation path:** A1.UNK → A2 → A3 → A4 (never skips)
8. **BuildCard completeness:** all 147 cells have a BuildCard with tools + validation criteria

---

## PART 4: TEST COVERAGE TARGETS

| Layer | Test Count | Target |
|-------|-----------|--------|
| Types (core + extended) | 20+ tests | Every type instantiates, serializes, deserializes |
| Lattice (axes) | 21 tests | Every Altitude/Diamond/IQRSQPI/BuildMode combination |
| BMS scoring | 15 tests | All threshold boundaries (0.25, 0.45, 0.75) |
| Cell parsing | 147 tests | Every cell ID roundtrips correctly |
| BuildCard generation | 147 tests | All 147 BuildCards generated with correct fields |
| Quality gates | 10 tests | PASS/FAIL/WARN/UNKNOWN paths |
| Archetypes (a1) | 49 tests | All 7 steps × 7 cells |
| B-engines | 13 tests | All 13 engines return valid output |
| Orchestrator | 7 tests | IQRSQPI pipeline per cell |
| Cold-start | 5 tests | Clean import → receipt |
| E2E | 10 tests | Full pipeline, no sample data |

**Total target:** 500+ tests, all deterministic, 0 LLM calls in test path.

---

## PART 5: BUILD ORDER

1. **DEDUP** → delete `rig_lattice.py`
2. **route_company** → build and test
3. **Cold-start receipts** → receipt system
4. **Archon wiring** → gate results in report
5. **Deterministic CLI** → real input path
6. **Cold-start test** → integration test
7. **Prediction studio** → verify wiring
8. **Build cards export** → write `artifacts/build_cards.json`
9. **Full test suite** → push to GitHub