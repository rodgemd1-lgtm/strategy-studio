# Strategy Teaser — Codex Runbook

End-to-end runbook for generating **2000 prospect teasers** in one batch.

## What this produces

Per prospect (each in its own subdirectory):

- `index.html` — drops onto the prospect's cloned site as the homepage hero/wedge
- `teaser.md` — for cold email body, LinkedIn DM thread starter, or PDF render
- `teaser_input.json` — input snapshot (audit trail)
- `proof_packet.json` — ProofPacket + FalsificationPacket + quality result

## Quickstart

```bash
cd ~/strategy-studio

# 1. Validate inputs (cheap, ~1 sec/100 records)
python -c "
from strategy_studio.teaser.schema import TeaserInput
import json
errors = 0
with open('prospects_2000.jsonl') as f:
    for ln, line in enumerate(f, 1):
        try:
            TeaserInput.model_validate_json(line)
        except Exception as e:
            print(f'line {ln}: {e}')
            errors += 1
print(f'{errors} validation errors')
"

# 2. Generate (~160 sec for 2000 prospects on 16 workers)
python -m strategy_studio.teaser.batch \\
    --input prospects_2000.jsonl \\
    --output out/teasers_2000/ \\
    --workers 16 \\
    --summary out/teasers_2000/_summary.jsonl

# 3. Verify outputs
ls out/teasers_2000/ | head -10
cat out/teasers_2000/_summary.jsonl | head -1 | python -m json.tool
```

## Input schema — every prospect needs

| Field | Type | Example | Source |
|---|---|---|---|
| `prospect_id` | str slug | `hed-inc` | You assign |
| `company_name` | str | `Hydro Electronic Devices, Inc.` | LakeOS / recall |
| `company_short` | str | `HED` | LakeOS / recall |
| `employees` | int | `224` | LakeOS / LinkedIn |
| `revenue_usd_m` | float | `60` | LakeOS / 10-K / Crunchbase |
| `years_in_business` | int | `35` | LakeOS / wikipedia |
| `headquarters` | str | `Hartford, WI` | LakeOS |
| `industry` | str | `Rugged CAN-based vehicle controls` | LakeOS / GICS |
| `industry_short` | str | `vehicle controls` | derived |
| `wound_months` | int | `18` | Codex research |
| `wound_channel` | str | `defense channel` | Codex research |
| `wound_trigger` | str | `CMMC Level 2 mandatory Nov 10 2026` | Codex research |
| `capability_count` | int 2-20 | `3` | LakeOS product page |
| `capability_names` | list[str] (2-10) | `["Control Modules", "Displays", "Keypads"]` | LakeOS |
| `capability_gap` | str | `None productized as intelligence yet.` | Codex synthesis |
| `mechanism_name` | str | `NVIS Gate × Five-Layer Compounding Loop` | Codex synthesis |
| `mechanism_description` | str | one-sentence | Codex synthesis |
| `advantages` | list[str] exactly 3 | see HED example | Codex synthesis |
| `comparable_company` | str | `Helios Technologies` | LakeOS / S&P |
| `comparable_year_start/end` | int | `2016 / 2025` | 10-K filings |
| `comparable_revenue_start_m/end_m` | float $M | `523 / 839` | 10-K filings |
| `comparable_segment_growth_m` | float $M | `298` | 10-K segment data |
| `engines` | list[EngineInput] exactly 3 | see HED example | Codex synthesis |
| `threats` | list[ThreatInput] exactly 3 | Tier 1/2/3 | Codex research |
| `disqualifiers` | list[str] exactly 3 | reasons RIG says no | Codex synthesis |
| `cloned_site_url` | str | `https://hed-forge.vercel.app` | You provision |
| `primary_color` | hex | `#0066B2` | LakeOS / brand scrape |
| `secondary_color` | hex | `#0F172A` | derived |
| `contact_name` | str | `Gijs Zomer` | LinkedIn / web scrape |
| `contact_role` | str | `VP of Operations` | LinkedIn |
| `evidence_sources` | list[str] >=2 | each cited with SW score | Codex research |
| `confidence` | `H` / `M` / `L` | `H` | derived from evidence count |

## Per-prospect Codex workflow

For each of the 2000, Codex runs this loop:

```
1. LakeOS query   → company facts (employees, revenue, HQ, industry, capabilities)
2. recall.it search → industry analog + comparable transaction
3. Web research    → CEO / strategy lead / functional buyer (contact_name + role)
4. Synthesis       → wound, mechanism_name, mechanism_description (NEVER generic)
5. Three engines  → product line × flywheel type × revenue target (must cite source)
6. Three threats  → Tier 1/2/3 with horizon + key_fact + SW score
7. Three disqualifiers → reasons RIG would walk
8. Three advantages → things they don't see in themselves
9. Validate against TeaserInput schema
10. Append to prospects_2000.jsonl
```

## Quality gates (auto-enforced by the schema)

- Pydantic `extra="forbid"` rejects unknown fields → no silent typos
- `min_length` / `max_length` enforces 3 advantages, 3 engines, 3 threats, 3 disqualifiers
- `evidence_sources` requires at least 2 entries → RIG min-2-source rule
- `confidence` must be H/M/L → forces explicit downgrade when evidence is weak
- ProofPacket auto-generated → every external send has audit trail
- FalsificationPacket auto-generated per engine → "what would prove this wrong"

## Scale targets

| Workers | Throughput | 2000 prospects |
|---|---|---|
| 1 | ~10/s | 200s |
| 4 | ~13/s | 160s |
| 8 | ~25/s | 80s |
| 16 | ~40/s | 50s |
| 32 | ~50/s | 40s |

Tested at 12.6/s on 4 workers locally. Real throughput is bounded by disk I/O on the bundle write, not template render.

## Deploy pattern

```bash
# After batch generation, deploy each bundle to its prospect's site
for prospect in out/teasers_2000/*/; do
  pid=$(basename "$prospect")
  # rsync to the cloned site root
  rsync -av "$prospect/index.html" "deploys/$pid/public/index.html"
done

# Or batch-upload to Vercel with `vercel deploy` per directory
```

## Cron-job pattern (refresh weekly)

```bash
# /etc/cron.d/strategy-teasers
0 6 * * 1 /Users/mikerodgers/.venvs/sio/bin/python -m strategy_studio.teaser.batch \\
    --input /Users/mikerodgers/strategy-studio/prospects_2000.jsonl \\
    --output /Users/mikerodgers/strategy-studio/out/teasers_$(date +\%Y\%m\%d)/ \\
    --workers 16 \\
    --summary /Users/mikerodgers/strategy-studio/out/teasers_$(date +\%Y\%m\%d)/_summary.jsonl
```

## Troubleshooting

**`validation_errors > 0`** — Codex emitted a record with a missing/wrong field. The summary line shows exact pydantic errors. Fix the upstream pipeline, don't patch the schema.

**`generation_errors > 0`** — Generator raised an exception. Most likely cause is the score normalization bug (already fixed) or a Jinja template variable that doesn't exist. Re-render with one prospect in isolation:

```python
from strategy_studio.teaser.generator import generate_teaser
from strategy_studio.teaser.schema import TeaserInput
from pathlib import Path

import json
t = TeaserInput.model_validate(json.loads(open('prospect.json').read()))
result = generate_teaser(t, Path('out/single'))
print(result)
```

**`confidence='L'` everywhere** — your evidence_sources lists are too short. Codex needs to enrich the research step (more LakeOS hits, more recall.it cards).

## Reference: 5 working sample prospects

`tests/fixtures/prospects_sample.jsonl` — HED, Anduril, Stripe, Snorkel, Shopify. Use these as input shape templates for Codex.
