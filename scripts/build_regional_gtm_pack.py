#!/usr/bin/env python3
"""Build regional GTM packs from RIG Strategy Studio prospect artifacts.

The first use case is Denver / Front Range: rank local accounts, compile the
strategy, and write per-account prompts for CSS design and website setup.

This script is local/A1 only: it reads existing validated Strategy Studio JSON
artifacts and writes local markdown/csv/jsonl files. It does not send outreach,
publish pages, or call external services.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROSPECTS = ROOT / "prospects_2000.jsonl"
DEFAULT_GTM20X = ROOT / "out/ai_gtm_20x"
DEFAULT_STRATEGIES = ROOT / "out/strategies_1783"
DEFAULT_OUTPUT = ROOT / "out/regional_gtm/denver_front_range"

FRONT_RANGE_CITIES = {
    "denver",
    "boulder",
    "aurora",
    "englewood",
    "colorado springs",
    "fort collins",
    "littleton",
    "centennial",
    "greenwood village",
    "arvada",
    "westminster",
    "loveland",
    "longmont",
    "golden",
    "thornton",
    "broomfield",
    "lone tree",
    "lakewood",
    "castle rock",
    "lafayette",
    "louisville",
    "superior",
    "commerce city",
    "highlands ranch",
    "wheat ridge",
    "parker",
    "johnstown",
    "fountain",
    "breckenridge",
}


SEGMENT_ORDER = {
    "legal ops": 1,
    "medspa growth": 2,
    "patient ops": 3,
    "service ops": 4,
    "CPA advisory": 5,
    "portfolio ops": 6,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "account"


def is_front_range(row: dict) -> bool:
    headquarters = (row.get("headquarters") or "").lower()
    return "colorado" in headquarters and any(city in headquarters for city in FRONT_RANGE_CITIES)


def load_gtm20x(gtm_dir: Path, prospect_id: str) -> dict:
    path = gtm_dir / prospect_id / "gtm20x.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_strategy(strategy_dir: Path, prospect_id: str) -> dict:
    path = strategy_dir / prospect_id / "strategy.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def ranked_clients(prospects: list[dict], gtm_dir: Path, strategy_dir: Path) -> list[dict]:
    clients = []
    for row in prospects:
        if not is_front_range(row):
            continue
        gtm = load_gtm20x(gtm_dir, row["prospect_id"])
        strategy = load_strategy(strategy_dir, row["prospect_id"])
        clients.append(
            {
                "prospect_id": row["prospect_id"],
                "company_name": row["company_name"],
                "company_short": row.get("company_short", ""),
                "headquarters": row.get("headquarters", ""),
                "industry_short": row.get("industry_short", ""),
                "industry": row.get("industry", ""),
                "employees": row.get("employees", 0),
                "revenue_usd_m": row.get("revenue_usd_m", 0),
                "wound_months": row.get("wound_months", 0),
                "wound_channel": row.get("wound_channel", ""),
                "wound_trigger": row.get("wound_trigger", ""),
                "mechanism_name": row.get("mechanism_name", ""),
                "cloned_site_url": row.get("cloned_site_url", ""),
                "primary_color": row.get("primary_color", "#1A56DB"),
                "secondary_color": row.get("secondary_color", "#0F172A"),
                "contact_role": row.get("contact_role", ""),
                "confidence": row.get("confidence", "M"),
                "priority_tier": gtm.get("priority_tier") or strategy.get("priority_tier") or "C",
                "priority_score": gtm.get("priority_score") or strategy.get("priority_score") or 0,
                "twenty_x_score": gtm.get("twenty_x_score") or 0,
                "one_big_bet": gtm.get("one_big_bet", ""),
                "wedge_upgrade": gtm.get("wedge_upgrade", ""),
                "brand_upgrade": gtm.get("brand_upgrade", ""),
                "data_system_upgrade": gtm.get("data_system_upgrade", ""),
                "proof_upgrade": gtm.get("proof_upgrade", ""),
                "strategy_path": str(strategy_dir / row["prospect_id"] / "strategy.md"),
                "gtm20x_path": str(gtm_dir / row["prospect_id"] / "gtm20x.md"),
            }
        )
    return sorted(
        clients,
        key=lambda c: (
            SEGMENT_ORDER.get(c["industry_short"], 99),
            -float(c["twenty_x_score"] or 0),
            -float(c["priority_score"] or 0),
            c["company_name"],
        ),
    )


def css_prompt(client: dict) -> str:
    return f"""# CSS Design Prompt — {client['company_name']}

Build a refined, high-trust strategy teaser visual system for a passworded RIG proposal page.

## Brand Inputs
- Company: {client['company_name']}
- Segment: {client['industry_short']}
- Primary color: `{client['primary_color']}`
- Secondary color: `{client['secondary_color']}`
- Mechanism: {client['mechanism_name']}

## Design Direction
- Use the prospect's existing colors as accents, but keep the RIG proposal experience restrained, sharp, and executive.
- Avoid generic SaaS gradients, floating blobs, huge marketing hero cards, and vague AI imagery.
- First viewport must show: company name, wound channel, months-to-trigger, named mechanism, and one proof asset.
- Build dense but readable sections: firm, situation, examination, system, approach, prediction, engagement terms, proof.
- Use card components only for repeated proof assets, threat tiers, workflow stages, and no-go tests.
- Use 8px max border radius, crisp borders, strong whitespace, and table-like rhythm for executive scanability.

## Required CSS Tokens
```css
:root {{
  --brand-primary: {client['primary_color']};
  --brand-secondary: {client['secondary_color']};
  --ink: #0F172A;
  --muted: #475569;
  --surface: #FFFFFF;
  --surface-alt: #F8FAFC;
  --border: #CBD5E1;
  --proof: #0F766E;
  --risk: #B91C1C;
  --radius: 8px;
  --max-width: 1180px;
}}
```

## Components To Style
- `.hero-proof`
- `.wound-lockout`
- `.mechanism-map`
- `.system-layer-grid`
- `.deviation-ladder`
- `.expert-lens-table`
- `.proof-ledger`
- `.engagement-tier-table`
- `.no-go-tests`
- `.next-72-hours`

## Quality Bar
- Looks like a confidential strategy brief, not a landing page.
- Mobile view keeps the wound, mechanism, and CTA visible without text overlap.
- Every major claim area has an adjacent proof/source affordance.
"""


def website_setup_prompt(client: dict) -> str:
    return f"""# Website Setup Prompt — {client['company_name']}

Create a passworded, client-specific RIG strategy teaser page using the HED pattern.

## Source Artifacts
- Base strategy: `{client['strategy_path']}`
- 20x GTM strategy: `{client['gtm20x_path']}`
- Existing cloned/proposal URL target: {client['cloned_site_url']}

## Page Goal
Make {client['company_name']} feel accurately seen in under 45 seconds, then make the next step a falsification-oriented reply or password request. Do not publish or send without Mike approval.

## Required Page Structure
1. **Hero:** {client['company_name']} + {client['wound_months']}-month lockout on {client['wound_channel']}
2. **Trigger:** {client['wound_trigger']}
3. **Mirror:** what they already have but have not productized as intelligence
4. **Mechanism:** {client['mechanism_name']}
5. **20x Upgrade:** {client['one_big_bet']}
6. **System:** Solo / Team / Vault / Edge / Sight / Blueprint
7. **RIG Deviate Engine:** -30, -20, -10, 0, +10, +20, +30 ladder
8. **Expert Board:** show 6-8 top lenses, not all 20 unless expandable
9. **AI GTM Workflow:** Capture -> Classify -> Mirror -> Deviate -> Personalize -> Propose -> Pilot -> Proof -> Retarget -> Learn
10. **No-Go Tests:** make scarcity and qualification explicit
11. **Next 72 Hours:** local action checklist for RIG

## Copy Rules
- Use mechanism language, not generic AI automation.
- Avoid soft-close phrasing.
- Every metric or trigger must map to a source/proof line from the strategy artifacts.
- Contact-specific content should stay local/private until manually approved.

## CTA
Primary CTA: "Send the falsification"  
Secondary CTA: "Request the passworded proposal"

## Build Rules
- Keep all assets local-first.
- No public exposure unless approved.
- No outbound email, ad pixel, analytics, or CRM write from this setup prompt.
"""


def proposal_build_prompt(client: dict) -> str:
    return f"""# Proposal Build Prompt — {client['company_name']}

Turn the strategy artifacts into a passworded proposal bundle.

## Inputs
- Strategy: `{client['strategy_path']}`
- 20x GTM: `{client['gtm20x_path']}`
- Brand colors: `{client['primary_color']}` / `{client['secondary_color']}`

## Output Bundle
- `index.html` passworded teaser/proposal page
- `strategy.md` copied from the source artifact
- `gtm20x.md` copied from the source artifact
- `proof_packet.json`
- `sow_draft.md`
- `css/prompt.css` or `styles.css`

## SOW Draft Shape
- Diagnostic: 2 weeks, proof/falsification, GO/NO-GO
- Activation: 3 months, first workflow, baseline metric, Day-90 ROI
- Transformation: 9-18 months, client-owned system, handoff, governance

## Human Gate
Stop before deploy. Report the generated local path and wait for Mike approval.
"""


def render_all_strategy(all_clients: list[dict], regional_clients: list[dict]) -> str:
    counts = Counter(c["industry_short"] for c in all_clients)
    tier_counts = Counter(c["priority_tier"] for c in all_clients)
    regional_counts = Counter(c["industry_short"] for c in regional_clients)
    total_pipeline = len(all_clients)
    lines = [
        "# RIG Potential Client Strategy",
        "",
        f"Generated: {now_iso()}",
        "",
        "## All-Prospect Strategy",
        "",
        "The full 1,783-account corpus should run as one operating system, not one-off outreach. Use the existing HED-pattern strategy, then the 20x layer, then deploy only approved account pages.",
        "",
        "### Campaign Architecture",
        "- **Tier A:** build proposal pages first; use proof-led, account-specific outreach.",
        "- **Tier B:** run teardown-first email/LinkedIn sequence; proposal only after reply or strong signal.",
        "- **Tier C:** nurture with segment-specific proof assets until better buyer/data evidence appears.",
        "",
        "### Segment Plays",
        "- **Law:** Matter Intake and Authority Engine; lead with intake-to-retainer leakage and AI search changes.",
        "- **Med spa:** Aesthetic Demand and Retention System; lead with consultation, rebooking, and treatment-plan leakage.",
        "- **Healthcare/orthopedics:** Patient Conversion and Capacity System; lead with referral, scheduling, and reactivation.",
        "- **Service businesses:** Field Ops AI Growth System; lead with quote-to-cash and review/reactivation loops.",
        "- **CPA/advisory:** Advisory Capacity and Client Intelligence System; lead with trapped tax-season knowledge.",
        "- **PE/portfolio/manufacturing:** Portfolio AI Value-Creation Sprint; lead with repeatable workflow proof across operating companies.",
        "",
        "### AI GTM Operating Loop",
        "Capture -> Classify -> Mirror -> Deviate -> Personalize -> Propose -> Pilot -> Proof -> Retarget -> Learn.",
        "",
        "### Full Corpus Mix",
        f"- Accounts: {total_pipeline}",
        f"- Segment mix: {dict(counts)}",
        f"- Tier mix: {dict(tier_counts)}",
        "",
        "### Denver/Front Range First Slice",
        f"- Accounts: {len(regional_clients)}",
        f"- Segment mix: {dict(regional_counts)}",
        "",
        "Denver should start with law firms because the corpus has the strongest local density there, then med spa/patient ops, then service/CPA/portfolio accounts.",
    ]
    return "\n".join(lines) + "\n"


def render_denver_strategy(clients: list[dict]) -> str:
    counts = Counter(c["industry_short"] for c in clients)
    tier_counts = Counter(c["priority_tier"] for c in clients)
    top = sorted(clients, key=lambda c: (-float(c["twenty_x_score"] or 0), c["company_name"]))[:25]
    lines = [
        "# Denver / Front Range Enhanced GTM Strategy",
        "",
        f"Generated: {now_iso()}",
        "",
        f"Accounts: {len(clients)}",
        "",
        "## Strategic Thesis",
        "",
        "Denver should be RIG's first local proof market: close enough for high-trust local presence, dense enough in law/medspa/healthcare/CPA/service to run segment plays, and fragmented enough that a proof-led AI operating-system wedge can stand out quickly.",
        "",
        "## Segment Mix",
    ]
    lines.extend(f"- {k}: {v}" for k, v in counts.most_common())
    lines.extend(["", "## Tier Mix"])
    lines.extend(f"- Tier {k}: {v}" for k, v in sorted(tier_counts.items()))
    lines.extend(
        [
            "",
            "## First 30-Day Move",
            "",
            "1. Build 10 passworded proposal pages for the highest 20x-score Denver accounts.",
            "2. Run one local legal-ops campaign and one medspa/patient-ops campaign.",
            "3. Use the same pattern for every account: wound, mirror, mechanism, no-go tests, proof, next 72 hours.",
            "4. Do not send until the website/proposal page and proof packet are reviewed.",
            "5. Feed replies, objections, and no-go outcomes back into LakeOS.",
            "",
            "## Top 25 Denver / Front Range Accounts",
            "",
            "| Rank | Score | Tier | Company | Segment | HQ | Mechanism | Prompt Folder |",
            "|---:|---:|---|---|---|---|---|---|",
        ]
    )
    for i, c in enumerate(top, 1):
        folder = f"out/regional_gtm/denver_front_range/prompts/{c['prospect_id']}"
        lines.append(
            f"| {i} | {float(c['twenty_x_score'] or 0):.1f} | {c['priority_tier']} | {c['company_name']} | {c['industry_short']} | {c['headquarters']} | {c['mechanism_name']} | `{folder}` |"
        )
    lines.extend(
        [
            "",
            "## Denver Campaigns",
            "",
            "### Campaign 1: Legal Ops Intake Authority",
            "- Target: Denver/Boulder/Aurora/Colorado Springs law firms.",
            "- Wound: AI-native local legal search and intake channel shifts before firms have proof-backed intake systems.",
            "- Offer: Matter Intake and Authority Engine.",
            "- Asset: passworded site teardown + intake memory loop map.",
            "",
            "### Campaign 2: Medspa / Patient Demand Retention",
            "- Target: med spa, aesthetics, orthopedic, dental, and patient ops accounts.",
            "- Wound: treatment discovery, consult booking, and reactivation leakage.",
            "- Offer: Aesthetic Demand and Retention System or Patient Conversion and Capacity System.",
            "- Asset: patient journey revenue map + proof workflow.",
            "",
            "### Campaign 3: Local Field Ops",
            "- Target: restoration, home service, and field operations accounts.",
            "- Wound: local discovery, quote-to-cash, review, and dispatch leakage.",
            "- Offer: Field Ops AI Growth System.",
            "- Asset: field ops leakage map.",
            "",
            "### Campaign 4: CPA / Advisory",
            "- Target: Denver CPA/advisory and client-service firms.",
            "- Wound: tax-season knowledge trapped outside scalable advisory products.",
            "- Offer: Advisory Capacity and Client Intelligence System.",
            "- Asset: advisory revenue expansion map.",
            "",
            "## Required Human Gate",
            "",
            "No outbound send, ad audience upload, analytics pixel, public deploy, or CRM write happens from these prompts without Mike approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(clients: list[dict], all_clients: list[dict], output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = output_dir / "prompts"
    if prompts_dir.exists():
        shutil.rmtree(prompts_dir)
    prompts_dir.mkdir(exist_ok=True)

    (output_dir / "all_potential_clients_strategy.md").write_text(render_all_strategy(all_clients, clients), encoding="utf-8")
    (output_dir / "denver_front_range_strategy.md").write_text(render_denver_strategy(clients), encoding="utf-8")

    jsonl_path = output_dir / "denver_front_range_clients.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for c in clients:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    csv_path = output_dir / "denver_front_range_clients.csv"
    fields = [
        "prospect_id",
        "company_name",
        "headquarters",
        "industry_short",
        "employees",
        "revenue_usd_m",
        "priority_tier",
        "priority_score",
        "twenty_x_score",
        "wound_months",
        "wound_channel",
        "mechanism_name",
        "cloned_site_url",
        "strategy_path",
        "gtm20x_path",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in clients:
            writer.writerow({k: c.get(k, "") for k in fields})

    aggregate_prompts = []
    for c in clients:
        folder = prompts_dir / c["prospect_id"]
        folder.mkdir(exist_ok=True)
        css = css_prompt(c)
        setup = website_setup_prompt(c)
        proposal = proposal_build_prompt(c)
        (folder / "css_design_prompt.md").write_text(css, encoding="utf-8")
        (folder / "website_setup_prompt.md").write_text(setup, encoding="utf-8")
        (folder / "proposal_build_prompt.md").write_text(proposal, encoding="utf-8")
        aggregate_prompts.append(f"# {c['company_name']}\n\n## CSS\n{css}\n\n## Website Setup\n{setup}\n\n## Proposal Build\n{proposal}\n")
    (output_dir / "all_denver_prompts.md").write_text("\n---\n\n".join(aggregate_prompts), encoding="utf-8")

    summary = {
        "generated_at": now_iso(),
        "generated_for": "RIG and Mike Rodgers",
        "region": "Denver / Front Range",
        "accounts": len(clients),
        "segment_mix": dict(Counter(c["industry_short"] for c in clients).most_common()),
        "tier_mix": dict(Counter(c["priority_tier"] for c in clients).most_common()),
        "output_dir": str(output_dir),
        "strategy": str(output_dir / "denver_front_range_strategy.md"),
        "all_strategy": str(output_dir / "all_potential_clients_strategy.md"),
        "csv": str(csv_path),
        "jsonl": str(jsonl_path),
        "prompts": str(prompts_dir),
        "aggregate_prompts": str(output_dir / "all_denver_prompts.md"),
    }
    (output_dir / "_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Denver/Front Range RIG GTM strategy and website prompt pack.")
    parser.add_argument("--prospects", default=str(DEFAULT_PROSPECTS))
    parser.add_argument("--gtm20x-dir", default=str(DEFAULT_GTM20X))
    parser.add_argument("--strategy-dir", default=str(DEFAULT_STRATEGIES))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    prospects = read_jsonl(Path(args.prospects))
    all_clients = []
    for row in prospects:
        gtm = load_gtm20x(Path(args.gtm20x_dir), row["prospect_id"])
        strategy = load_strategy(Path(args.strategy_dir), row["prospect_id"])
        all_clients.append(
            {
                "prospect_id": row["prospect_id"],
                "company_name": row["company_name"],
                "industry_short": row.get("industry_short", ""),
                "priority_tier": gtm.get("priority_tier") or strategy.get("priority_tier") or "C",
            }
        )
    clients = ranked_clients(prospects, Path(args.gtm20x_dir), Path(args.strategy_dir))
    summary = write_outputs(clients, all_clients, Path(args.output))
    print(json.dumps(summary, indent=2))
    return 0 if clients else 2


if __name__ == "__main__":
    raise SystemExit(main())
