"""Run v3 strict audit on HED seed + meshed v3, compare to v2 heuristic scores."""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from auditor import audit_all

BASE = Path(__file__).parent
V2 = BASE.parent / "rig_engines_v2"
OUT = BASE / "audits"
OUT.mkdir(exist_ok=True)

# ── Audit both seed and meshed v3 ────────────────────────────────────────
print("Auditing seed (Mike's v2 draft)...")
seed = (V2 / "hed_seed.md").read_text()
seed_audit = audit_all(seed, llm_enabled=False)
(OUT / "seed_audit.json").write_text(json.dumps(seed_audit, indent=2, default=str))
print(f"  RIG-L: {seed_audit['rig_l']:+.2f}  BDF: {seed_audit['bdf']:+.2f}  "
      f"status: {seed_audit['status']}  hard_blocks: {seed_audit['hard_blocks']}")
print()

print("Auditing meshed v3...")
meshed = (V2 / "run" / "mesh" / "meshed.md").read_text()
mesh_audit = audit_all(meshed, llm_enabled=False)
(OUT / "mesh_audit.json").write_text(json.dumps(mesh_audit, indent=2, default=str))
print(f"  RIG-L: {mesh_audit['rig_l']:+.2f}  BDF: {mesh_audit['bdf']:+.2f}  "
      f"status: {mesh_audit['status']}  hard_blocks: {mesh_audit['hard_blocks']}")
print()

# ── Side-by-side comparison ─────────────────────────────────────────────
v2_seed_packet = json.loads((V2 / "run" / "scoring" / "seed_packet.json").read_text())
v2_mesh_packet = json.loads((V2 / "run" / "scoring" / "mesh_packet.json").read_text())

print("=" * 92)
print(f"{'Engine':14} | {'v2 heuristic σ':>16} | {'v3 strict σ':>14} | {'v2 mesh σ':>10} | {'v3 mesh σ':>10}")
print("-" * 92)
for slug, r in sorted(seed_audit['engines'].items(), key=lambda x: -x[1]['sigma']):
    cn = r['codename']
    v2s = v2_seed_packet['mad_z'].get(slug, 0)
    v3s = r['sigma']
    v2m = v2_mesh_packet['mad_z'].get(slug, 0)
    v3m = mesh_audit['engines'][slug]['sigma']
    print(f"{cn:14} | {v2s:+16.2f} | {v3s:+14.2f} | {v2m:+10.2f} | {v3m:+10.2f}")
print("-" * 92)
print(f"{'RIG-L':14} | {v2_seed_packet['rig_l']:+16.2f} | {seed_audit['rig_l']:+14.2f} | "
      f"{v2_mesh_packet['rig_l']:+10.2f} | {mesh_audit['rig_l']:+10.2f}")

print()
print("=== Failed-required questions per engine (BLOCKERS) ===")
for slug, r in seed_audit['engines'].items():
    if r['failed_required']:
        print(f"\n{r['codename']} ({slug}) — {r['status']}")
        for qid in r['failed_required']:
            q = next(x for x in r['questions'] if x['id'] == qid)
            print(f"  ✗ {qid}: {q['question']}")
            if q.get('evidence'):
                print(f"     evidence: {q['evidence'][:120]}")

print()
print(f"Audits saved: {OUT}/")
