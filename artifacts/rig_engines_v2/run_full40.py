"""Run all 40 engines on HED seed: score → dispatch 30 LLM agents → mesh → re-score → render."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from framework import ENGINES, score_all, dispatch_batch, mesh_variants

BASE = Path(__file__).parent
OUT = BASE / "run"
OUT.mkdir(exist_ok=True)
(OUT / "agents").mkdir(exist_ok=True)
(OUT / "mesh").mkdir(exist_ok=True)
(OUT / "scoring").mkdir(exist_ok=True)

seed = (BASE / "hed_seed.md").read_text()
print(f"Seed: {len(seed.split())} words · {len(seed)} chars\n")

# ── Step 1: Score seed against all 40 engines (instant) ─────────────────────
print("[1/6] Scoring seed against all 40 engines (heuristic)...")
t0 = time.time()
seed_packet = score_all(seed)
(OUT / "scoring" / "seed_packet.json").write_text(json.dumps(seed_packet, indent=2))
print(f"      done · {time.time()-t0:.2f}s")
print(f"      RIG-L: {seed_packet['rig_l']:+.2f}  BDF: {seed_packet['bdf']:+.2f}  "
      f"status: {seed_packet['status']}  hard_blocks: {seed_packet['hard_blocks']}")
print()

# ── Step 2: Dispatch 30 LLM agents (20 cognitive + 10 nature) in batches ────
non_gate_engines = [e for e in ENGINES if not e.is_gate]
print(f"[2/6] Dispatching {len(non_gate_engines)} LLM agents at +20σ in parallel batches of 6...")
print(f"      Batches of 6 to avoid 70B model contention. ETA ~25-35 min total.\n")

all_variants: dict[str, dict] = {}
batch_size = 6
batches = [non_gate_engines[i:i+batch_size] for i in range(0, len(non_gate_engines), batch_size)]
for bi, batch in enumerate(batches, 1):
    names = ", ".join(e.codename for e in batch)
    print(f"  Batch {bi}/{len(batches)}: {names}")
    bt = time.time()
    variants = dispatch_batch(seed, batch, target_sigma=20, max_workers=len(batch))
    print(f"  Batch {bi} done · {time.time()-bt:.0f}s\n")
    all_variants.update(variants)
    # Persist as we go
    for codename, v in variants.items():
        if v.get("status") == "ok":
            (OUT / "agents" / f"{codename.lower()}_plus20.md").write_text(v["content"])
    (OUT / "agents" / "all_variants.json").write_text(json.dumps(all_variants, indent=2, default=str))

succ = sum(1 for v in all_variants.values() if v.get("status") == "ok")
print(f"  → {succ}/{len(non_gate_engines)} agents succeeded\n")

# ── Step 3: Physics gates already in scoring; print summary ─────────────────
print("[3/6] Physics gates on seed (10 hard constraints):")
for e in ENGINES:
    if e.is_gate:
        z = seed_packet["mad_z"][e.slug]
        st = seed_packet["engines"][e.slug]
        marker = "✓" if st == "PASS" else ("⚠" if st == "BLOCK" else "✗")
        print(f"  {marker} {e.codename:13} {z:+7.2f}σ  {st}")
print()

# ── Step 4: Coral Reef mesh ─────────────────────────────────────────────────
print("[4/6] Coral Reef mesh of successful variants...")
t0 = time.time()
ok_variants = {k: v for k, v in all_variants.items() if v.get("status") == "ok"}
meshed = mesh_variants(ok_variants, seed)
(OUT / "mesh" / "meshed.md").write_text(meshed)
print(f"      meshed v3: {len(meshed.split())} words · {len(meshed)} chars\n")

# ── Step 5: Re-score the mesh ───────────────────────────────────────────────
print("[5/6] Re-scoring meshed v3 against all 40 engines...")
mesh_packet = score_all(meshed)
(OUT / "scoring" / "mesh_packet.json").write_text(json.dumps(mesh_packet, indent=2))
print(f"      RIG-L: {mesh_packet['rig_l']:+.2f}  BDF: {mesh_packet['bdf']:+.2f}  "
      f"status: {mesh_packet['status']}  hard_blocks: {mesh_packet['hard_blocks']}")
print()

# Delta summary
print("[6/6] DELTAS (seed → meshed):")
print(f"  RIG-L: {seed_packet['rig_l']:+.2f} → {mesh_packet['rig_l']:+.2f}  Δ {mesh_packet['rig_l']-seed_packet['rig_l']:+.2f}")
print(f"  BDF:   {seed_packet['bdf']:+.2f} → {mesh_packet['bdf']:+.2f}  Δ {mesh_packet['bdf']-seed_packet['bdf']:+.2f}")
print()
deltas = sorted(
    [(slug, mesh_packet["mad_z"][slug] - seed_packet["mad_z"][slug])
     for slug in seed_packet["mad_z"]],
    key=lambda x: -x[1]
)[:5]
print("  Top 5 engines that moved UP (gained σ):")
for slug, d in deltas:
    print(f"    {slug:32} Δ {d:+.2f}σ")
worst = sorted(
    [(slug, mesh_packet["mad_z"][slug] - seed_packet["mad_z"][slug])
     for slug in seed_packet["mad_z"]],
    key=lambda x: x[1]
)[:5]
print()
print("  Top 5 engines that moved DOWN (lost σ):")
for slug, d in worst:
    print(f"    {slug:32} Δ {d:+.2f}σ")
print()
print(f"DONE · artifacts at {OUT}/")
