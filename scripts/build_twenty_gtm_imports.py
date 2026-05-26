#!/usr/bin/env python3
"""Create Twenty CRM import CSVs from Strategy Studio GTM artifacts.

The exports are local-only. They intentionally do not trigger outbound sends,
CRM writes, or ad uploads. Twenty import remains a human-gated operation unless
Mike explicitly approves API import credentials and side effects.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ALL_PROSPECTS = ROOT / "prospects_2000.jsonl"
DENVER_PROSPECTS = ROOT / "out/regional_gtm/denver_front_range/denver_front_range_clients.jsonl"
DENVER_WORKBOOK = ROOT / "out/regional_gtm/denver_front_range/denver_front_range_gtm_pack.xlsx"
OUTPUT_DIR = ROOT / "out/twenty-crm/imports"
PROOF_PATH = OUTPUT_DIR / "twenty_gtm_imports_proof.json"

TASK_OFFSETS = {
    "Review proof packet and approve/no-go": 0,
    "Verify buyer identity and contact data": 1,
    "Review cloned proposal page": 2,
    "Draft Day 0 email from mechanism/wound": 3,
    "Human gate before any outbound send": 4,
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
            count += 1
    return count


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return " ".join(str(value).split())


def prospect_index(rows: list[dict]) -> dict[str, dict]:
    return {row["prospect_id"]: row for row in rows}


def merge_denver_with_full(denver_rows: list[dict], full_by_id: dict[str, dict]) -> list[dict]:
    merged = []
    for row in denver_rows:
        base = full_by_id.get(row["prospect_id"], {})
        item = {**base, **row}
        if not item.get("contact_name") and base.get("contact_name"):
            item["contact_name"] = base["contact_name"]
        if not item.get("evidence_sources") and base.get("evidence_sources"):
            item["evidence_sources"] = base["evidence_sources"]
        merged.append(item)
    return merged


def tier(row: dict) -> str:
    return clean(row.get("priority_tier") or row.get("tier") or "C")


def score(row: dict) -> str:
    return clean(row.get("twenty_x_score") or row.get("priority_score") or "")


def strategy_path(row: dict) -> str:
    path = row.get("strategy_path")
    if path:
        return clean(path)
    candidate = ROOT / "out/strategies_1783" / row["prospect_id"] / "strategy.md"
    return str(candidate) if candidate.exists() else ""


def gtm20x_path(row: dict) -> str:
    path = row.get("gtm20x_path")
    if path:
        return clean(path)
    candidate = ROOT / "out/ai_gtm_20x" / row["prospect_id"] / "gtm20x.md"
    return str(candidate) if candidate.exists() else ""


def company_rows(rows: list[dict], list_name: str) -> list[dict]:
    out = []
    for row in rows:
        out.append(
            {
                "Name": clean(row.get("company_name")),
                "Prospect ID": clean(row.get("prospect_id")),
                "GTM List": list_name,
                "Segment": clean(row.get("industry_short")),
                "Industry": clean(row.get("industry")),
                "HQ": clean(row.get("headquarters")),
                "Employees": clean(row.get("employees")),
                "Revenue USD M": clean(row.get("revenue_usd_m")),
                "Priority Tier": tier(row),
                "20x Score": score(row),
                "Wound Months": clean(row.get("wound_months")),
                "Wound Channel": clean(row.get("wound_channel")),
                "Wound Trigger": clean(row.get("wound_trigger")),
                "Mechanism": clean(row.get("mechanism_name")),
                "Cloned Proposal URL": clean(row.get("cloned_site_url")),
                "Strategy Path": strategy_path(row),
                "20x GTM Path": gtm20x_path(row),
                "Evidence Sources": clean(row.get("evidence_sources")),
                "Approval Status": "Mike approval required before outbound",
            }
        )
    return out


def people_rows(rows: list[dict], list_name: str) -> list[dict]:
    out = []
    for row in rows:
        contact_name = clean(row.get("contact_name"))
        if not contact_name:
            continue
        parts = contact_name.split()
        out.append(
            {
                "First Name": parts[0],
                "Last Name": " ".join(parts[1:]),
                "Name": contact_name,
                "Company Name": clean(row.get("company_name")),
                "Prospect ID": clean(row.get("prospect_id")),
                "GTM List": list_name,
                "Job Title": clean(row.get("contact_role")),
                "Email": clean(row.get("email") or row.get("contact_email")),
                "Phone": clean(row.get("phone") or row.get("contact_phone")),
                "LinkedIn URL": clean(row.get("linkedin_url") or row.get("contact_linkedin_url")),
                "Persona Notes": clean(
                    f"{row.get('contact_role', '')}; sell the operational delta through "
                    f"{row.get('mechanism_name', '')}; wound: {row.get('wound_channel', '')}"
                ),
                "Approval Status": "Verify identity before outbound",
            }
        )
    return out


def opportunity_rows(rows: list[dict], list_name: str) -> list[dict]:
    out = []
    for row in rows:
        amount = ""
        revenue = row.get("revenue_usd_m")
        if isinstance(revenue, (int, float)):
            amount = int(max(25000, min(450000, revenue * 1000)))
        out.append(
            {
                "Name": clean(f"{row.get('company_name')} - {row.get('mechanism_name')}"),
                "Company Name": clean(row.get("company_name")),
                "Prospect ID": clean(row.get("prospect_id")),
                "GTM List": list_name,
                "Stage": "Research / Approval Required",
                "Amount": amount,
                "Priority Tier": tier(row),
                "20x Score": score(row),
                "Close Date": (datetime.now(timezone.utc) + timedelta(days=45)).date().isoformat(),
                "Offer": clean(row.get("one_big_bet") or row.get("mechanism_description") or row.get("mechanism_name")),
                "Wound": clean(row.get("wound_channel")),
                "Disqualifiers": clean(row.get("disqualifiers")),
                "Next Step": "Review proof, verify buyer, and get Mike approval before outbound.",
                "Strategy Path": strategy_path(row),
                "20x GTM Path": gtm20x_path(row),
            }
        )
    return out


def task_rows(rows: list[dict], list_name: str) -> list[dict]:
    out = []
    now = datetime.now(timezone.utc)
    for row in rows:
        for task, offset in TASK_OFFSETS.items():
            out.append(
                {
                    "Title": clean(f"{task}: {row.get('company_name')}"),
                    "Company Name": clean(row.get("company_name")),
                    "Prospect ID": clean(row.get("prospect_id")),
                    "GTM List": list_name,
                    "Due Date": (now + timedelta(days=offset)).date().isoformat(),
                    "Status": "To Do",
                    "Priority Tier": tier(row),
                    "Mechanism": clean(row.get("mechanism_name")),
                    "Notes": clean(
                        f"{row.get('wound_channel', '')}; trigger: {row.get('wound_trigger', '')}; "
                        "no sends without Mike approval."
                    ),
                    "Strategy Path": strategy_path(row),
                }
            )
    return out


def build_scope(name: str, rows: list[dict]) -> dict:
    scope_dir = OUTPUT_DIR / name
    files = {
        "companies": scope_dir / "twenty_companies.csv",
        "people": scope_dir / "twenty_people.csv",
        "opportunities": scope_dir / "twenty_opportunities.csv",
        "tasks": scope_dir / "twenty_tasks.csv",
    }
    counts = {
        "companies": write_csv(files["companies"], company_rows(rows, name), [
            "Name",
            "Prospect ID",
            "GTM List",
            "Segment",
            "Industry",
            "HQ",
            "Employees",
            "Revenue USD M",
            "Priority Tier",
            "20x Score",
            "Wound Months",
            "Wound Channel",
            "Wound Trigger",
            "Mechanism",
            "Cloned Proposal URL",
            "Strategy Path",
            "20x GTM Path",
            "Evidence Sources",
            "Approval Status",
        ]),
        "people": write_csv(files["people"], people_rows(rows, name), [
            "First Name",
            "Last Name",
            "Name",
            "Company Name",
            "Prospect ID",
            "GTM List",
            "Job Title",
            "Email",
            "Phone",
            "LinkedIn URL",
            "Persona Notes",
            "Approval Status",
        ]),
        "opportunities": write_csv(files["opportunities"], opportunity_rows(rows, name), [
            "Name",
            "Company Name",
            "Prospect ID",
            "GTM List",
            "Stage",
            "Amount",
            "Priority Tier",
            "20x Score",
            "Close Date",
            "Offer",
            "Wound",
            "Disqualifiers",
            "Next Step",
            "Strategy Path",
            "20x GTM Path",
        ]),
        "tasks": write_csv(files["tasks"], task_rows(rows, name), [
            "Title",
            "Company Name",
            "Prospect ID",
            "GTM List",
            "Due Date",
            "Status",
            "Priority Tier",
            "Mechanism",
            "Notes",
            "Strategy Path",
        ]),
    }
    return {
        "scope": name,
        "prospects": len(rows),
        "counts": counts,
        "files": {key: str(path) for key, path in files.items()},
        "hashes": {key: sha256(path) for key, path in files.items()},
    }


def main() -> None:
    full_rows = read_jsonl(ALL_PROSPECTS)
    denver_rows = merge_denver_with_full(read_jsonl(DENVER_PROSPECTS), prospect_index(full_rows))
    proof = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_for": "RIG and Mike Rodgers",
        "source_files": {
            "all_prospects": str(ALL_PROSPECTS),
            "denver_prospects": str(DENVER_PROSPECTS),
            "denver_workbook": str(DENVER_WORKBOOK),
        },
        "scopes": [
            build_scope("all_1783", full_rows),
            build_scope("denver_front_range_78", denver_rows),
        ],
        "human_gate": "These CSVs are safe local imports only; no outbound sends, ad uploads, or public exposure were performed.",
    }
    PROOF_PATH.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
