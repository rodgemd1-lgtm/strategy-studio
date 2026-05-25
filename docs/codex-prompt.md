# CODEX PROMPT — Build 2000 Prospect Strategy Teasers

You are Codex working inside `/Users/mikerodgers/strategy-studio`. Your job is to
produce one validated `TeaserInput` JSON record per prospect, append it to
`prospects_2000.jsonl`, and run the batch generator. Mike will deploy each
generated bundle onto the prospect's cloned site.

This is **A1-only work**: deterministic research → structured synthesis → schema
validation. No "happy to" language, no calendar links, no generic AI consultant
copy. Every claim must be evidence-cited with a source weight (SW).

---

## YOUR INPUT

A prospect list file: `inputs/prospect_list.csv` with these columns:

| Column | Required | Example |
|---|---|---|
| `prospect_id` | yes | `hed-inc` (slug, lowercase, dash-separated) |
| `company_name` | yes | `Hydro Electronic Devices, Inc.` |
| `website` | yes | `https://www.hedonline.com` |
| `industry_hint` | optional | `industrial vehicle controls` (your starting search seed) |
| `linkedin_url` | optional | `https://linkedin.com/company/hed-inc` |
| `cloned_site_url` | yes | `https://hed-forge.vercel.app` |

If the column is missing for a row, run the discovery steps below to fill it.

---

## YOUR OUTPUT

For every row in `prospect_list.csv`, you must:

1. Produce one validated `TeaserInput` JSON record
2. Append it to `prospects_2000.jsonl` (one record per line, no trailing comma)
3. Track failures in `prospects_failed.jsonl` with `{prospect_id, error, last_step}`

When the entire list is processed, run:

```bash
python -m strategy_studio.teaser.batch \
  --input prospects_2000.jsonl \
  --output out/teasers_2000/ \
  --workers 16 \
  --summary out/teasers_2000/_summary.jsonl
```

Then post the summary and the per-prospect path to GitHub Issues #1 on
`rodgemd1-lgtm/strategy-studio`.

---

## PER-PROSPECT WORKFLOW

Run these 10 steps **in order** for each prospect. Stop and record the failure
if any step returns insufficient evidence (≥2 sources required).

### Step 1 — LakeOS company lookup

```bash
python3 /Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py agent-query \
  "company facts for ${company_name}: employees, revenue, HQ, years in business, industry classification, founders, ownership structure" \
  --task teaser_research --agent codex
```

Capture: `employees`, `revenue_usd_m`, `years_in_business`, `headquarters`,
`industry` (long-form), `industry_short` (2-3 words), founder/owner names.

If LakeOS returns `UNKNOWN`, fall back to **Step 1b**.

### Step 1b — recall.it card search (fallback)

```bash
curl -s -H "Authorization: Bearer sk_b2cf9f1fcf737f37b2bafb6830c1f846" \
  "https://backend.getrecall.ai/api/v1/search?q=${company_name}+revenue+employees&limit=10"
```

Cross-reference with: SEC filings (10-K), Crunchbase, LinkedIn employee count,
company "About" page. **Require ≥2 sources matching within ±15% for revenue,
within ±5% for employee count.**

### Step 2 — Industry deep research

```bash
python3 /Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py agent-query \
  "industry analysis: ${industry}, TAM, CAGR, competitive landscape, regulatory triggers, AI adoption maturity" \
  --task teaser_research --agent codex
```

Capture:
- **Total addressable market** ($B and CAGR%)
- **Regulatory triggers** with specific dates (CMMC Level 2 Nov 10 2026,
  SEC AI disclosure rules, EU AI Act enforcement, etc.)
- **Top 5 competitors** with public AI strategy status
- **AI maturity gap** in this industry vs adjacent industries

### Step 3 — Wound identification

Find the **specific channel** the prospect risks being locked out of, with
months-to-lockout precision. Examples that worked:

| Industry | Wound channel | Trigger |
|---|---|---|
| Defense controls | defense channel | CMMC Level 2 Nov 10 2026 |
| Payment infra | enterprise AI-spend rails | OpenAI/Anthropic pick default by EOY 2026 |
| Data labeling | F100 fine-tuning workflows | Scale AI / Meta acquisition closes Q4 2026 |
| Commerce | AI-native commerce search | ChatGPT/Perplexity/Rufus reroute 20%+ traffic by H2 2026 |

**Rules:**
- `wound_months` must be 3-60, derived from a known calendar date
- `wound_channel` must be a real procurement / distribution channel they
  currently access
- `wound_trigger` must cite a specific date or named event

Reject and re-research if your wound is generic ("falling behind on AI",
"competitors moving faster"). It must be **channel-specific and date-specific.**

### Step 4 — Mirror (capabilities mapping)

Visit the prospect's website (`website` column) and identify their **2-10
product lines / service capabilities**. Use:

```bash
curl -s "${website}" | python3 -c "
import sys, re
html = sys.stdin.read()
# Extract h1/h2/h3 + nav items
for m in re.finditer(r'<(h[1-3])[^>]*>([^<]+)</\1>', html):
    print(m.group(2).strip())
"
```

Or use the `rig-asset-scraper` if available:

```bash
python3 services/rig_commands/rig_asset_scraper.py --url ${website} --extract capabilities
```

Capture `capability_names` (2-10 items, exact product/service names) and
`capability_count`. Write a **single-sentence `capability_gap`** that names
what they have NOT done with these capabilities. Examples:

- "None productized as intelligence yet."
- "Each platform sells, but the substrate underneath them isn't packaged
  as an enterprise sale to allies."
- "Your AI features are merchant-side; you haven't packaged the buyer-side
  AI rails yet."

### Step 5 — Named mechanism

Generate a **specific named mechanism** for what RIG would build. Format:

```
{NamedTerm} × {LoopName} → {one-sentence what it does}
```

Examples:
- `NVIS Gate × Five-Layer Compounding Loop` — defense-grade AI substrate
  that compounds with every shipped unit
- `Lattice Sovereign Tier` — ally-grade sovereign substrate licensed
  per-nation, not per-seat
- `AI-Native Metering Rails` — Visa for inference: token billing across
  every model provider and enterprise buyer

**Rules:**
- Must be 2-4 words, capitalized, never seen before in market
- Must reference the prospect's actual tech stack or product naming
- Must NOT contain "AI", "platform", "solution", "framework"

### Step 6 — Three structural advantages

Find **three things the prospect has but doesn't know are advantages**.
Each must:
- Cite at least one specific fact (date, count, certification, year)
- Reference a competitor weakness
- Fit on one line (max 200 chars)

Bad: "Strong brand reputation in their industry."
Good: "CMMC Level 2 compliance — mandatory for DoD primes by Nov 10, 2026.
Most competitors are 12–24 months behind."

### Step 7 — Comparable transaction (the analog)

Find one **public company** that made the same pivot 5-10 years ago. Use
LakeOS first, fall back to SEC EDGAR 10-K filings:

```bash
python3 /Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py agent-query \
  "company that pivoted from ${industry_short} to ${industry_short} + AI/software over the last 10 years, with segment revenue breakdown" \
  --task teaser_research --agent codex
```

Capture:
- `comparable_company` (full legal name)
- `comparable_year_start` (year of pivot, ≥1990)
- `comparable_year_end` (most recent fiscal year)
- `comparable_revenue_start_m` and `comparable_revenue_end_m`
- `comparable_segment_growth_m` (the NEW segment value, not total)

Cite source: 10-K filing year + page reference.

### Step 8 — Three category engines

For each of 3 product lines, build one engine entry:

```json
{
  "name": "Control Modules",
  "sigma_label": "+5σ",
  "flywheel_type": "data" | "capability" | "adoption",
  "flywheel_loop": "CL-4002 drift → on-device inference → cross-OEM fleet learning → attached AI revenue",
  "target_revenue_m": 42
}
```

**Rules:**
- `sigma_label` ranges from `+4σ` (incremental) to `+6σ` (category-defining)
- `flywheel_type` exactly one of: `data` / `capability` / `adoption`
- `flywheel_loop` must be 4 arrow-separated stages naming **specific product
  SKUs or feature names**
- `target_revenue_m` must be evidence-anchored to a market sizing or comparable

### Step 9 — Three competitive threats

```json
[
  {"name": "Parker Hannifin", "tier": "Tier 1", "horizon_months": "6-12", "key_fact": "Public AI strategy plus capital to acquire a tier-2 competitor", "source_weight": 0.45},
  {"name": "Bosch Rexroth + Trackunit", "tier": "Tier 2", "horizon_months": "12-24", "key_fact": "3.5M connected assets; CMMC qualification trails HED by 12-24 months", "source_weight": 0.40},
  {"name": "Grayhill / APEM", "tier": "Tier 3", "horizon_months": "24-36", "key_fact": "IoT framing exists but no edge-AI narrative or dedicated R&D", "source_weight": 0.30}
]
```

**Rules:**
- Tier 1 = 6-12 months out, real and capital-armed
- Tier 2 = 12-24 months out, slower but credible
- Tier 3 = 24-36 months out, structural laggard
- `source_weight` 0.0–1.0, calibrated against evidence quality
- `key_fact` ≤120 chars, must be falsifiable

### Step 10 — Three disqualifiers

The reasons RIG would walk away. **These are the most important part of
the teaser** — they create scarcity and qualify the prospect to themselves.

Bad: "You're not a good fit for our services."
Good: "You believe Microsoft Copilot alone will close the AI gap. It will not."
Good: "Engineering leadership treats AI as a threat instead of a force
multiplier — and won't move."

Each disqualifier must:
- Name a specific belief, behavior, or organizational reality
- Be true for ~30% of prospects in this industry
- Force a binary GO / NO-GO read from the contact

---

## CONTACT IDENTIFICATION

For each prospect, find the **single most-leveraged buyer** by name and role.
Hierarchy of preference:

1. VP of Operations / COO (operational buyer, has FY26 mandate)
2. Chief Strategy Officer / VP Strategy (cross-cutting authority)
3. CTO / Head of AI (if AI is their stated mandate)
4. Founder / CEO (only for sub-200 employee companies)

```bash
python3 /Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py agent-query \
  "leadership team for ${company_name}: VP Operations or COO or Chief Strategy Officer, current title, LinkedIn URL, tenure" \
  --task teaser_research --agent codex
```

Fallback to LinkedIn scraping (use the rig-asset-scraper):

```bash
python3 services/rig_commands/rig_asset_scraper.py --url ${linkedin_url} --extract leadership
```

Capture `contact_name` (real name, properly capitalized) and `contact_role`
(exact title from their profile).

---

## BRAND COLOR EXTRACTION

```bash
python3 services/rig_commands/rig_asset_scraper.py --url ${website} --extract brand_colors
```

Extract `primary_color` (hex) and `secondary_color` (hex, dark accent).
If extraction fails, use defaults:
- `primary_color`: `#1A56DB` (RIG blue)
- `secondary_color`: `#0F172A` (slate-900)

---

## EVIDENCE LEDGER

For EVERY teaser, `evidence_sources` must contain ≥2 cited sources in this
format:

```
"McKinsey Mobile Hydraulics 2025 · SW 0.55"
"Bosch+Trackunit press release Apr 2025 · SW 0.45"
"Helios FY25 10-K · SW 0.65"
"Parker Hannifin AI strategy Q1 2025 earnings call · SW 0.50"
```

**Source weight calibration:**
- 0.65–1.0 — primary docs (10-K, earnings transcripts, government filings)
- 0.45–0.65 — major analyst reports (McKinsey, Gartner, IDC, CB Insights)
- 0.30–0.45 — press releases, vendor blogs, LinkedIn posts
- <0.30 — speculation / single-source rumors → **do not use**

Confidence label rules:
- `H` — 4+ sources, all SW ≥0.50, at least 2 primary docs
- `M` — 3+ sources, mixed SW, at least 1 primary
- `L` — 2 sources, no primary — should rarely ship

---

## VALIDATION & WRITE

Before appending each record to `prospects_2000.jsonl`:

```python
from strategy_studio.teaser.schema import TeaserInput
import json

record = { ... your built dict ... }
try:
    validated = TeaserInput.model_validate(record)
    with open("prospects_2000.jsonl", "a") as f:
        f.write(validated.model_dump_json() + "\n")
    print(f"OK {record['prospect_id']}")
except Exception as e:
    with open("prospects_failed.jsonl", "a") as f:
        f.write(json.dumps({
            "prospect_id": record.get("prospect_id"),
            "error": str(e),
            "last_step": "validation",
            "record": record,
        }) + "\n")
    print(f"FAIL {record['prospect_id']} → {e}")
```

---

## BATCH GENERATION

When all prospects are processed:

```bash
cd /Users/mikerodgers/strategy-studio
python -m strategy_studio.teaser.batch \
  --input prospects_2000.jsonl \
  --output out/teasers_2000/ \
  --workers 16 \
  --summary out/teasers_2000/_summary.jsonl
```

Expected: 2000 bundles in ~50 seconds. Each bundle contains:
- `index.html` — drop onto the cloned site
- `teaser.md` — cold email body
- `teaser_input.json` — audit snapshot
- `proof_packet.json` — ProofPacket + FalsificationPackets

---

## FAILURE HANDLING

If `_summary.jsonl` shows any `validation_errors > 0` or
`generation_errors > 0`:

1. Open `prospects_failed.jsonl` and inspect the top 5 failures
2. Fix the upstream research (do NOT patch the schema)
3. Re-run the failed prospects only:

```bash
cat prospects_failed.jsonl | jq -c '.record' > prospects_retry.jsonl
python -m strategy_studio.teaser.batch \
  --input prospects_retry.jsonl \
  --output out/teasers_2000/ \
  --workers 8
```

---

## QUALITY GATES (DO NOT SKIP)

Before declaring done, verify:

1. `out/teasers_2000/_summary.jsonl` shows `ok == total`
2. Open 5 random bundles and read the HTML — wound naming must be specific,
   mechanism must be unique, no generic AI consultant phrases
3. `grep -c "happy to" out/teasers_2000/*/teaser.md` returns 0
4. `grep -c "world-class" out/teasers_2000/*/teaser.md` returns 0
5. `grep -c "calendar" out/teasers_2000/*/teaser.md` returns 0 (no calendar links)
6. Every `proof_packet.json` has `falsification` with `len == 3`
7. Every `confidence` ≠ `"L"` (downgrade research if you hit L)

---

## REFERENCE SAMPLES

Five working teasers are already generated:

```bash
ls /Users/mikerodgers/strategy-studio/out/teasers/
# anduril-industries  hed-inc  shopify-inc  snorkel-ai  stripe-inc

# Open HED as the canonical example:
open /Users/mikerodgers/strategy-studio/out/teasers/hed-inc/index.html
```

Sample inputs are in:
```
/Users/mikerodgers/strategy-studio/tests/fixtures/prospects_sample.jsonl
```

**Use these five as your shape templates.** When in doubt about whether your
synthesis is sharp enough, compare against the HED record's `mechanism_name`,
`advantages`, `disqualifiers`, and `wound_trigger`. If your output is more
generic than HED's, redo the research.

---

## REPORT BACK

When complete, post to GitHub Issues #1 on `rodgemd1-lgtm/strategy-studio`:

```markdown
## 2000-prospect teaser batch — complete

- Total: 2000
- OK: <N>
- Validation errors: <N>
- Generation errors: <N>
- Confidence H: <N>
- Confidence M: <N>
- Confidence L: <N>  (target: 0)
- Time: <seconds>
- Workers: 16

Output: `out/teasers_2000/`
Summary: `out/teasers_2000/_summary.jsonl`
Failed: `prospects_failed.jsonl` (<N> records)

Top 5 cited sources across all 2000 prospects:
1. ...
2. ...
3. ...
4. ...
5. ...

Sample best teaser (highest confidence + sharpest mechanism):
- prospect_id: <id>
- mechanism: <name>
- wound: <months> months / <channel>

Sample weakest teaser (lowest confidence, flagged for redo):
- prospect_id: <id>
- issues: <list>
```

Then assign the issue to Mike Rodgers for deploy approval.

---

## YOUR EXECUTION PLAN

1. Read `inputs/prospect_list.csv`
2. For each row, run the 10-step workflow + contact + brand color steps
3. Validate against the TeaserInput schema
4. Append to `prospects_2000.jsonl` (or `prospects_failed.jsonl`)
5. When the CSV is exhausted, run the batch generator
6. Report back to GitHub Issues #1

Don't ask for clarification. The schema, the samples, and the runbook contain
every constraint. If a prospect can't pass the quality gates, mark it failed
and move on.

Mike will review the first 50 bundles and either approve the deploy or send
back specific corrections. You will not deploy any bundle yourself.
