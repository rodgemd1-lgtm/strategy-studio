"""Render full-40 HED Forge v3 proposal HTML — self-contained.

Reads: artifacts/rig_engines_v2/run/{agents,mesh,scoring}/
Writes: artifacts/rig_engines_v2/hed_forge_v3_full40.html
        ~/Desktop/HED-Forge-v3-FULL40.html
"""
from __future__ import annotations
import html, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from framework import ENGINES

BASE = Path(__file__).parent
RUN = BASE / "run"


def _safe(s: str) -> str:
    return html.escape(s or "")


def _sigma_bar(z: float, max_abs: float = 20.0) -> str:
    pct = max(-1.0, min(1.0, z / max_abs))
    if pct >= 0:
        left, width, color = "50%", f"{pct*50:.1f}%", "var(--good)"
    else:
        left, width, color = f"{50+pct*50:.1f}%", f"{-pct*50:.1f}%", "var(--bad)"
    return (
        f'<span class="sigbar" title="σ={z:+.2f}">'
        f'<span class="sigbar-track"></span>'
        f'<span class="sigbar-mid"></span>'
        f'<span class="sigbar-fill" style="left:{left};width:{width};background:{color};"></span>'
        f'</span>'
    )


MERMAID_BLOCKS = [
    ("Pipeline overview", """
flowchart LR
  S[Seed v2] --> SC[Score 40 engines]
  SC --> A[30 LLM agents @ +20σ<br/>5 batches × 6 parallel]
  SC --> G[10 physics gates<br/>PASS / HARD_BLOCK]
  A --> M[Coral Reef Mesh]
  G --> M
  M --> R[v3 candidate]
  R --> SC2[Re-score 40]
  SC2 --> H[HTML proposal]
"""),
    ("Three-layer engine stack", """
flowchart TB
  subgraph C[Cognitive 1-20 · OUTPUT · ±20σ]
    GRAVITON --> ANCHOR --> FORGE --> BREAKER --> HORIZON
    BAYES --> COLLIDER --> SHIELD --> GLYPH --> XRAY
    VOLT --> DARWIN --> ECHO --> SOVEREIGN --> SURPRISE
    LOOP --> VISCERA --> REBOUND --> PRISM --> WELLSPRING
  end
  subgraph N[Nature 21-30 · PROCESS · ±20σ]
    SWARM --> ALBATROSS --> SLIME --> CLONAL --> LUMINA
    COLI --> ROOT --> HUMPBACK --> CUCKOO --> REEF
  end
  subgraph P[Physics 31-40 · STATE · ±30σ HARD GATES]
    KELVIN --> PAULI --> LUMEN --> CRITICAL --> TUNNEL
    HG[HORIZON-GATE] --> PARSEC --> CASIMIR --> BELL --> ZEROPOINT
  end
  C --> Mesh
  N --> Mesh
  P --> Mesh
  Mesh --> v3[HED Forge v3]
"""),
]


def render():
    seed = (BASE / "hed_seed.md").read_text()
    seed_packet = json.loads((RUN / "scoring" / "seed_packet.json").read_text())
    mesh_packet = json.loads((RUN / "scoring" / "mesh_packet.json").read_text())
    variants = json.loads((RUN / "agents" / "all_variants.json").read_text())
    meshed = (RUN / "mesh" / "meshed.md").read_text()

    # Engine table — all 40
    by_layer = {"cognitive": [], "nature": [], "physics": []}
    for e in ENGINES:
        sz = seed_packet["mad_z"][e.slug]
        mz = mesh_packet["mad_z"][e.slug]
        delta = mz - sz
        s_st = seed_packet["engines"][e.slug]
        m_st = mesh_packet["engines"][e.slug]
        dcls = "delta-good" if delta > 0 else ("delta-bad" if delta < 0 else "delta-neutral")
        by_layer[e.layer].append(
            f"<tr><td><strong>{_safe(e.codename)}</strong></td>"
            f"<td><code>{_safe(e.slug)}</code></td>"
            f"<td>{_sigma_bar(sz)} <span class='z'>{sz:+.2f}</span></td>"
            f"<td>{_sigma_bar(mz)} <span class='z'>{mz:+.2f}</span></td>"
            f"<td class='{dcls}'>{delta:+.2f}σ</td>"
            f"<td><span class='status-{s_st.lower()}'>{s_st}</span> → "
            f"<span class='status-{m_st.lower()}'>{m_st}</span></td></tr>"
        )

    cog_rows = "\n".join(by_layer["cognitive"])
    nat_rows = "\n".join(by_layer["nature"])
    phys_rows = "\n".join(by_layer["physics"])

    # Variant blocks — all 30 LLM outputs
    variant_blocks = []
    for codename, v in variants.items():
        if v.get("status") != "ok":
            continue
        slug = v["engine_slug"]
        sigma = v.get("target_sigma", 20)
        content = v["content"]
        chars = len(content)
        # Find this engine's seed→mesh delta
        sz = seed_packet["mad_z"].get(slug, 0)
        mz = mesh_packet["mad_z"].get(slug, 0)
        delta = mz - sz
        variant_blocks.append(f"""
<details class="variant-block">
  <summary><strong>RIG-{_safe(codename)}</strong>
   <span class="meta">engine: <code>{_safe(slug)}</code> · σ: +{sigma} · {chars:,} chars · seed→mesh Δ {delta:+.2f}σ</span>
  </summary>
  <div class="variant-body"><pre>{_safe(content)}</pre></div>
</details>""")
    variants_html = "\n".join(variant_blocks)

    # Top movers
    deltas = sorted(
        [(e.codename, e.slug, mesh_packet["mad_z"][e.slug] - seed_packet["mad_z"][e.slug])
         for e in ENGINES],
        key=lambda x: -x[2]
    )
    top_up = deltas[:5]
    top_down = sorted(deltas, key=lambda x: x[2])[:5]

    def _mover_rows(rows):
        return "\n".join(
            f"<tr><td><strong>{_safe(cn)}</strong></td><td><code>{_safe(sl)}</code></td>"
            f"<td class='{'delta-good' if d > 0 else 'delta-bad'}'>{d:+.2f}σ</td></tr>"
            for cn, sl, d in rows
        )

    diagram_html = "\n".join(
        f'<div class="diagram-block"><h3>{_safe(t)}</h3><pre class="mermaid">{_safe(c.strip())}</pre></div>'
        for t, c in MERMAID_BLOCKS
    )

    seed_rl = seed_packet["rig_l"]; mesh_rl = mesh_packet["rig_l"]
    seed_bdf = seed_packet["bdf"]; mesh_bdf = mesh_packet["bdf"]

    css = """
:root{--bg:#0d1117;--panel:#161b22;--muted:#8b949e;--text:#c9d1d9;--accent:#58a6ff;--good:#3fb950;--bad:#f85149;--warn:#d29922}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 -apple-system,'Segoe UI',sans-serif}
.container{max-width:1300px;margin:0 auto;padding:32px 24px}
h1{margin:0 0 4px;font-size:30px;letter-spacing:-0.02em}
h2{margin-top:36px;font-size:18px;border-bottom:1px solid #30363d;padding-bottom:6px}
h3{margin-top:24px;font-size:14px}
.subtitle{color:var(--muted);font-size:13px}
.banner{background:linear-gradient(180deg,#1f2937,#0f172a);border:1px solid #30363d;border-radius:8px;padding:18px 22px;margin-top:18px}
.banner strong{color:var(--accent)}
.callout{background:#0f1419;border-left:4px solid var(--good);border-radius:6px;padding:14px 18px;margin:16px 0}
.callout strong{color:var(--good)}
.tile-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.tile{background:var(--panel);border:1px solid #30363d;border-radius:8px;padding:16px}
.tile .label{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:0.04em}
.tile .value{font-size:24px;font-weight:600;margin-top:4px}
.tile.bad .value{color:var(--bad)}.tile.good .value{color:var(--good)}.tile.warn .value{color:var(--warn)}
table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:8px;overflow:hidden;margin:8px 0}
th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #21262d;font-size:12.5px;vertical-align:middle}
th{background:#1c2128;color:var(--muted);text-transform:uppercase;font-size:11px;letter-spacing:0.04em}
code{background:#21262d;padding:2px 6px;border-radius:4px;font:11px/1 'SF Mono','Monaco',monospace;color:#79c0ff}
pre{margin:0;font:13px/1.5 'SF Mono','Monaco',monospace;color:var(--text);white-space:pre-wrap;background:transparent;padding:0}
pre.mermaid{font:13px/1.4 monospace;background:#0d1117;padding:12px;border-radius:6px;min-height:80px}
.sigbar{display:inline-block;position:relative;width:160px;height:8px;vertical-align:middle;margin-right:6px}
.sigbar-track{position:absolute;inset:3px 0;background:#21262d;border-radius:2px}
.sigbar-mid{position:absolute;top:0;left:50%;width:1px;height:8px;background:#30363d}
.sigbar-fill{position:absolute;top:1px;height:6px;border-radius:2px}
.z{font:11px/1 'SF Mono','Monaco',monospace;color:var(--muted)}
.status-pass{color:var(--good);font-weight:600}.status-block{color:var(--warn);font-weight:600}.status-hard_block{color:var(--bad);font-weight:700;text-transform:uppercase}
.delta-good{color:var(--good);font-weight:600}.delta-bad{color:var(--bad);font-weight:600}.delta-neutral{color:var(--muted)}
section{margin:32px 0}
.seed-box{background:var(--panel);border:1px solid #30363d;border-radius:8px;padding:16px;max-height:340px;overflow:auto}
.meshed-output{background:var(--panel);border:2px solid var(--good);border-radius:8px;padding:18px}
details.variant-block{background:var(--panel);border:1px solid #30363d;border-radius:8px;margin:6px 0;padding:6px 12px}
details.variant-block summary{cursor:pointer;font-size:13px;list-style:none}
details.variant-block summary::-webkit-details-marker{display:none}
details.variant-block summary::before{content:"▸ ";color:var(--muted)}
details.variant-block[open] summary::before{content:"▾ "}
.meta{color:var(--muted);font-size:11px;margin-left:8px}
.variant-body{margin-top:8px;padding:12px;background:#0d1117;border-radius:6px;max-height:420px;overflow:auto}
.diagram-block{background:var(--panel);border:1px solid #30363d;border-radius:8px;padding:14px 16px;margin:12px 0}
.diagram-block h3{margin:0 0 10px}
footer{margin-top:48px;padding-top:24px;border-top:1px solid #30363d;color:var(--muted);font-size:12px}
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HED Forge v3 · Full-40 RIG Deviator</title><style>{css}</style></head>
<body><div class="container">

<h1>HED Forge v3 — Full-40 RIG Deviator™</h1>
<p class="subtitle">Generated {_safe(time.strftime("%Y-%m-%d %H:%M %Z"))} · Source: <code>hed-forge.vercel.app/v2</code> (Mike's v2 draft) · 30 LLM agents @ +20σ · 10 physics gates · Coral Reef mesh · llama3.3:70b on rig-256gb</p>

<div class="banner">
  <p style="margin:0"><strong>This is the full-40 run.</strong> 20 Cognitive engines + 10 Nature engines fired LLM agents at +20σ. 10 Physics engines ran as hard pass/block gates. The mesh combined the strongest pull from every successful variant.</p>
  <p style="margin:8px 0 0;color:var(--muted)">Sample proposal artifact: this is what HED clients receive. The scoring is RIG marking its own homework. Every claim that survives passes 40 doctrine-anchored gates.</p>
</div>

<section>
  <h2>1. Headline scorecard</h2>
  <div class="tile-grid">
    <div class="tile {'good' if seed_rl>=0 else 'bad'}"><div class="label">Seed RIG-L</div><div class="value">{seed_rl:+.2f}</div></div>
    <div class="tile {'good' if mesh_rl>=0 else 'bad'}"><div class="label">Mesh RIG-L</div><div class="value">{mesh_rl:+.2f}</div></div>
    <div class="tile {'good' if mesh_rl-seed_rl>=0 else 'bad'}"><div class="label">Δ RIG-L</div><div class="value">{mesh_rl-seed_rl:+.2f}</div></div>
    <div class="tile {'good' if mesh_bdf>=seed_bdf else 'bad'}"><div class="label">Δ BDF</div><div class="value">{mesh_bdf-seed_bdf:+.2f}</div></div>
    <div class="tile"><div class="label">Hard blocks</div><div class="value">{seed_packet['hard_blocks']} → {mesh_packet['hard_blocks']}</div></div>
  </div>
</section>

<section>
  <h2>2. Top movers</h2>
  <h3>Engines that gained σ (mesh outperformed seed)</h3>
  <table><tr><th>Codename</th><th>Engine</th><th>Δσ</th></tr>{_mover_rows(top_up)}</table>
  <h3>Engines that lost σ (mesh underperformed seed)</h3>
  <table><tr><th>Codename</th><th>Engine</th><th>Δσ</th></tr>{_mover_rows(top_down)}</table>
</section>

<section>
  <h2>3. Cognitive layer 1–20 (output, ±20σ)</h2>
  <table><tr><th>Codename</th><th>Engine</th><th>Seed σ</th><th>Mesh σ</th><th>Δ</th><th>Status</th></tr>{cog_rows}</table>
</section>

<section>
  <h2>4. Nature layer 21–30 (process, ±20σ)</h2>
  <table><tr><th>Codename</th><th>Engine</th><th>Seed σ</th><th>Mesh σ</th><th>Δ</th><th>Status</th></tr>{nat_rows}</table>
</section>

<section>
  <h2>5. Physics layer 31–40 (state, HARD GATES, ±30σ)</h2>
  <p style="color:var(--muted)">These gates are PASS/HARD_BLOCK. A HARD_BLOCK on any of these prevents ship.</p>
  <table><tr><th>Codename</th><th>Engine</th><th>Seed σ</th><th>Mesh σ</th><th>Δ</th><th>Status</th></tr>{phys_rows}</table>
</section>

<section>
  <h2>6. Meshed v3 — the synthesized proposal</h2>
  <div class="callout"><strong>Synthesized from all successful +20σ variants.</strong> If Mike's v2 already passes (RIG-L {seed_rl:+.2f}), v3 is the refinement candidate. Read it before lifting anything into hed-forge.vercel.app/v2.</div>
  <div class="meshed-output"><pre>{_safe(meshed)}</pre></div>
</section>

<section>
  <h2>7. The 30 agent variants (one per axis)</h2>
  <p>Every variant rewrote the seed at +20σ along ONE axis. Click to expand.</p>
  {variants_html}
</section>

<section>
  <h2>8. Seed (Mike's v2 draft)</h2>
  <div class="seed-box"><pre>{_safe(seed)}</pre></div>
</section>

<section>
  <h2>9. How RIG Deviator works</h2>
  {diagram_html}
</section>

<footer>
RIG Deviator™ Full-40 · Rodgers Intelligence Group · 2026-05-15 · The framework just scored its own ship-list across 40 doctrine gates. Sample proposal artifact for client engagements.
</footer>

</div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
  mermaid.initialize({{ startOnLoad: true, theme: "dark", fontFamily: "monospace" }});
</script>
</body></html>
"""

    out = BASE / "hed_forge_v3_full40.html"
    out.write_text(html_doc)
    print(f"Wrote: {out} ({len(html_doc):,} bytes)")
    desktop = Path.home() / "Desktop" / "HED-Forge-v3-FULL40.html"
    desktop.write_text(html_doc)
    print(f"Wrote: {desktop}")


if __name__ == "__main__":
    render()
