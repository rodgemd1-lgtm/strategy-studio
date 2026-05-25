# RIG Lattice Visualization System — Design

The lattice has 3,087 cells (`7 × 21 × 21`). No single view shows all of them well. The viz system is therefore a **set of complementary lenses** sharing one source of truth (`viz/lattice_index.json`). Each lens optimizes for one job.

## Source of truth

```
lattice/generator.py
        ↓ emits
viz/lattice_index.json   (3,087 cells, ~800 KB)
        ↓ feeds all six views
```

Edit a card → regenerate → every view auto-updates. No view holds its own state.

## The six views

| # | View | Job | Audience | Surface | Status |
|---|------|-----|----------|---------|--------|
| 1 | **Streamlit Plotly 3D** | Analyst workbench — rotate, filter, hover, slice | Mike (operator) | `streamlit run viz/streamlit_plotly_app.py` | ✅ Live |
| 2 | **R3F web viewer** | Public 3D Excel — the canonical view | Outside world | `rodgersintelligence.github.io/rig-systems-engineering-studio/` | 🟡 Scaffolded |
| 3 | **Per-cell deep page** | Read one BuildCard with question bank + engines | Mike + dev | `lattice/cards/<cell_id>.md` (3,087 pages) | ✅ Generated |
| 4 | **2D matrix slices** | Heatmap of one fixed axis (e.g., altitude L4) | Quick scan | Embedded in Streamlit + R3F | 🟡 In Streamlit only |
| 5 | **Coverage overlay** | "Which archetypes are actually built?" — A1 ✅, A2/A3/A4 ⚪ | Mike (status) | Streamlit sidebar + R3F badge | ⚪ Planned |
| 6 | **CLI Rich table** | Terminal view for SSH / pipeline output | Hermes/Jake/agents | `rig-lattice show --altitude L4` | ⚪ Planned |

### View 1 — Streamlit Plotly 3D (live)

- Already scaffolded at [viz/streamlit_plotly_app.py](../viz/streamlit_plotly_app.py).
- **Local-only.** Optimized for Mike's analyst workflow.
- Rotate via Plotly OrbitControls; filter via sidebar; hover for cell summary.
- "Mode distribution heatmap" expander shows altitude × Y-position pivot with red-yellow-green gradient.

### View 2 — R3F web viewer (the canonical 3D Excel)

This is the centerpiece. Scaffolded at [viz/lattice_r3f/](../viz/lattice_r3f/).

**Tech stack:**
- Vite + React 18 + TypeScript
- `@react-three/fiber` for the canvas, `@react-three/drei` for OrbitControls + Html overlays
- `zustand` for filter state (lightweight, ~1 KB)
- GitHub Pages deploy via `.github/workflows/deploy-viz.yml`

**Geometry:**
- Each cell = an `InstancedMesh` cube at `(altitude_index, y_pos, z_pos)`.
- X axis: 7 altitude positions, spacing 1 unit.
- Y axis: 21 diamond-step positions, spacing 1 unit.
- Z axis: 21 confidence-step positions, spacing 1 unit.
- Total grid: 7 × 21 × 21 = 3,087 cubes.

**Encoding:**
- **Color** = mode (green PYTHON_ONLY → yellow HYBRID → orange AGENT_BOUNDED → red LLM_AGENT_FREE).
- **Scale** = BMS (linear 0..1 → cube edge 0.2..0.9).
- **Opacity** = filter alpha (filtered-out cells dim to 0.1).
- **Hover** = HTML overlay (drei `<Html>`) with cell_id, mode, BMS, semantics.
- **Click** = open `/cards/<cell_id>.md` in a side panel.

**Performance:**
- Single `InstancedMesh` for all 3,087 cubes → one draw call.
- Color/scale instance attributes packed in a `Float32Array`.
- ~60fps on M1 Mac, ~30fps on iPhone (per Plotly benchmarks of equivalent counts).

**Filters (sidebar):**
- Mode multiselect (4)
- Altitude multiselect (7)
- Diamond multiselect (3)
- Confidence element multiselect (3)
- BMS range slider

Filtered cells dim to 0.1 alpha rather than disappear — preserves spatial context.

**Camera:**
- Initial: isometric-ish (position [12, 12, 12], looking at center `[3, 10, 10]`).
- OrbitControls with damping, max distance 50, min distance 5.
- "Reset view" button restores initial pose.

**Axis labels:**
- 3D text labels via drei `<Text>` at axis ends and major ticks.
- Sticky 2D legend overlay (HTML, top-right) lists mode→color mapping.

### View 3 — Per-cell deep page (generated)

Each cell has a Markdown file at `lattice/cards/<cell_id>.md` rendered by `lattice/render.py`. Includes:

- BMS breakdown table (RAW / ADJ_failure / ADJ_volume / ADJ_altitude)
- Y-axis + Z-axis semantics
- Stack + Gates
- **Engines wired** (DV research engines, DV quality gates, prediction engines, diamond σ target)
- **Question bank** (first 10 of 30 in MD; full 30 in YAML)
- Governance metadata

Linked from View 1 (table column) and View 2 (click handler).

### View 4 — 2D matrix slices

Sometimes a 21×21 grid at fixed altitude is more legible than full 3D. Render as:
- Heatmap (rows = Y-position D1.I1..D3.I2, columns = Z-position RAW.I1..ADJ_VOLUME.I2)
- Cell color = mode
- Cell text = BMS (3 decimals)
- Available in Streamlit (expander) and as a planned R3F overlay mode.

### View 5 — Coverage overlay

Status of *implementation* on top of the lattice. Each cell gets a build state:

```
implementation_status: implemented | scaffolded | planned | not_started
```

A1 archetype (private repo) covers ~30 cells → those render with a green halo. A2/A3/A4 cells get a gray halo until their archetype repos exist. Toggle via R3F sidebar.

### View 6 — CLI Rich table

For Hermes/Jake/agents running in SSH or background processes:

```bash
$ rig-lattice show --altitude L4 --mode HYBRID
┌──────────┬──────────────────────┬────────────────────────┬───────┬────────┐
│ Cell ID  │ Y (Diamond.Step)     │ Z (Confidence.Step)    │ BMS   │ Mode   │
├──────────┼──────────────────────┼────────────────────────┼───────┼────────┤
│ L4-D2.S- │ Schema-Bound Synth   │ Failure-cost @ Solution│ 0.565 │ HYBRID │
│ L4-D2.Q2-│ Gate Stack Run       │ Volume lift @ Quality  │ 0.605 │ HYBRID │
│ ...      │ ...                  │ ...                    │ ...   │ ...    │
└──────────┴──────────────────────┴────────────────────────┴───────┴────────┘
3,087 cells · 21 shown · cumulative BMS 0.587
```

Powered by `rich` library. Wired into `pyproject.toml` as `rig-lattice` CLI script.

---

## Shared design choices

### Mode color palette (locked)

```
PYTHON_ONLY     #22c55e   green-500
HYBRID          #eab308   yellow-500
AGENT_BOUNDED   #f97316   orange-500
LLM_AGENT_FREE  #ef4444   red-500
UNKNOWN/STUB    #6b7280   gray-500
```

### Axis tick labels (locked)

```
X (altitude)        L1   L2   L3   L4   L5   L6   L7
Y (diamond.step)    D1.I1 D1.Q1 D1.R D1.S D1.Q2 D1.P D1.I2  D2.I1 ... D3.I2
Z (confidence.step) RAW.I1 RAW.Q1 RAW.R RAW.S RAW.Q2 RAW.P RAW.I2  ADJ_FAILURE.I1 ... ADJ_VOLUME.I2
```

### URL scheme (public viewer)

```
/                          # 3D lattice view (default)
/cell/L4-D2.S-RAW.S        # deep page for one cell
/slice/altitude/L4         # 21×21 slice at fixed L4
/coverage                  # implementation status overlay
```

Hash routing in R3F to keep it static-deployable on GitHub Pages.

### Performance budget

- Initial load: < 2s on 4G
- Frame rate: ≥ 30fps on iPhone 12+, ≥ 60fps on M1 Mac
- Bundle size: < 500 KB gzipped (React + R3F + lattice_index.json)
- Card MD generation: < 30s for all 3,087

---

## What you SEE vs what you DECIDE

**Seeing** the lattice is half the value. The other half is **deciding**:

- Looking at View 2 (R3F): "Why is L7 mostly red?" → answer: vision-level decisions are LLM_AGENT_FREE by construction.
- Looking at View 4 (slice L4): "Why does D3 column trend lower than D2?" → answer: evolution cells lose ADJ_volume because they're rare-run.
- Looking at View 5 (coverage): "Why is L3 mostly gray?" → answer: A2 HYBRID archetype isn't built yet — that's the next phase.

The viz is the **operating cockpit** for the lattice. Mike + Jake should be able to glance at View 2 and instantly answer: *what's the system shaped like, where are the gaps, where's the next phase?*

---

## Build order

1. ✅ View 1 (Streamlit Plotly) — shipped
2. ✅ View 3 (per-cell Markdown pages) — generated automatically
3. 🟡 View 2 (R3F web) — scaffolding now
4. ⚪ View 4 (2D slices in R3F) — add after View 2 ships
5. ⚪ View 5 (coverage overlay) — add when A2 archetype ships
6. ⚪ View 6 (CLI Rich) — add when there are 2+ archetypes built and operators need an SSH lens
