#!/usr/bin/env python3
"""Import Strategy Studio GTM rows into the local Twenty CRM.

This script writes only to the local Twenty instance on localhost. It does not
connect email, calendar, ads, Apollo, Clay, or any external CRM. Outbound action
remains human-gated in the imported tasks and opportunity notes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMPORT_ROOT = ROOT / "out/twenty-crm/imports"
DEFAULT_AUTH_STATE = ROOT / "out/twenty-crm/.playwright-auth.json"
DEFAULT_BASE_URL = "http://localhost:3020"


@dataclass
class ImportStats:
    created: int = 0
    skipped: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"created": self.created, "skipped": self.skipped, "failed": self.failed}


class TwentyClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1600]
            raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {detail}") from exc

    def list_objects(self, object_name: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        after: str | None = None
        seen_cursors: set[str] = set()

        while True:
            query = {"limit": "200"}
            if after:
                query["starting_after"] = after
            result = self.request("GET", f"/rest/{object_name}?{urllib.parse.urlencode(query)}")
            rows.extend(result.get("data", {}).get(object_name, []))

            page_info = result.get("pageInfo", {})
            next_cursor = page_info.get("endCursor")
            if not page_info.get("hasNextPage") or not next_cursor:
                break
            if next_cursor in seen_cursors:
                raise RuntimeError(f"Twenty pagination cursor loop while listing {object_name}")
            seen_cursors.add(next_cursor)
            after = next_cursor

        return rows

    def create_object(self, object_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.request("POST", f"/rest/{object_name}", payload)
        singular = object_name[:-3] + "y" if object_name.endswith("ies") else object_name[:-1]
        return result.get("data", {}).get(f"create{singular[:1].upper()}{singular[1:]}", {})

    def delete_object(self, object_name: str, object_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/rest/{object_name}/{object_id}")


def read_token(auth_state: Path) -> str:
    data = json.loads(auth_state.read_text(encoding="utf-8"))
    for cookie in data.get("cookies", []):
        if cookie.get("name") != "tokenPair":
            continue
        token_pair = json.loads(urllib.parse.unquote(cookie["value"]))
        token = token_pair.get("accessOrWorkspaceAgnosticToken", {}).get("token")
        if token:
            return token
    raise RuntimeError(f"No Twenty access token found in {auth_state}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def parse_int(value: str) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        return int(float(text.replace(",", "")))
    except ValueError:
        return None


def parse_money_micros(value: str) -> dict[str, Any]:
    amount = parse_int(value)
    if amount is None:
        return {"amountMicros": None, "currencyCode": None}
    return {"amountMicros": amount * 1_000_000, "currencyCode": "USD"}


def parse_revenue_micros(value: str) -> dict[str, Any]:
    text = clean(value)
    if not text:
        return {"amountMicros": None, "currencyCode": None}
    try:
        revenue_usd = float(text.replace(",", "")) * 1_000_000
    except ValueError:
        return {"amountMicros": None, "currencyCode": None}
    return {"amountMicros": int(revenue_usd * 1_000_000), "currencyCode": "USD"}


def parse_hq(value: str) -> dict[str, Any]:
    city = ""
    state = ""
    country = "United States"
    text = clean(value)
    if text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if parts:
            city = parts[0]
        if len(parts) >= 2:
            state = parts[1]
    return {
        "addressStreet1": "",
        "addressStreet2": "",
        "addressCity": city,
        "addressPostcode": "",
        "addressState": state,
        "addressCountry": country,
        "addressLat": None,
        "addressLng": None,
    }


def date_to_iso(value: str, fallback_days: int = 45) -> str:
    text = clean(value)
    parsed = None
    if text:
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            parsed = None
    if parsed is None:
        parsed = datetime.now(timezone.utc)
        parsed = parsed.replace(day=min(parsed.day, 28))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.combine(parsed.date(), time(hour=12), tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def split_name(full_name: str) -> dict[str, str]:
    parts = clean(full_name).split()
    if not parts:
        return {"firstName": "Unknown", "lastName": ""}
    return {"firstName": parts[0], "lastName": " ".join(parts[1:])}


def link_payload(url: str, label: str = "") -> dict[str, Any]:
    return {"primaryLinkLabel": label, "primaryLinkUrl": clean(url), "secondaryLinks": []}


def company_payload(row: dict[str, str]) -> dict[str, Any]:
    employees = parse_int(row.get("Employees", ""))
    payload: dict[str, Any] = {
        "name": clean(row.get("Name")),
        "domainName": link_payload(row.get("Cloned Proposal URL", ""), "Cloned proposal"),
        "address": parse_hq(row.get("HQ", "")),
        "annualRecurringRevenue": parse_revenue_micros(row.get("Revenue USD M", "")),
        "idealCustomerProfile": row.get("Priority Tier", "").upper() in {"A", "B"},
    }
    if employees is not None:
        payload["employees"] = employees
    return payload


def person_payload(row: dict[str, str], company_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": split_name(row.get("Name", "")),
        "jobTitle": clean(row.get("Job Title")),
        "city": "",
    }
    email = clean(row.get("Email"))
    if email:
        payload["emails"] = {"primaryEmail": email, "additionalEmails": []}
    phone = clean(row.get("Phone"))
    if phone:
        payload["phones"] = {
            "primaryPhoneNumber": re.sub(r"[^\d]", "", phone),
            "primaryPhoneCountryCode": "US",
            "primaryPhoneCallingCode": "+1",
            "additionalPhones": [],
        }
    linkedin = clean(row.get("LinkedIn URL"))
    if linkedin:
        payload["linkedinLink"] = link_payload(linkedin, "LinkedIn")
    if company_id:
        payload["companyId"] = company_id
    return payload


def opportunity_payload(row: dict[str, str], company_id: str | None, person_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": clean(row.get("Name")),
        "amount": parse_money_micros(row.get("Amount", "")),
        "closeDate": date_to_iso(row.get("Close Date", "")),
        "stage": "SCREENING",
    }
    if company_id:
        payload["companyId"] = company_id
    if person_id:
        payload["pointOfContactId"] = person_id
    return payload


def task_payload(row: dict[str, str]) -> dict[str, Any]:
    notes = "\n".join(
        [
            f"Company: {clean(row.get('Company Name'))}",
            f"Prospect ID: {clean(row.get('Prospect ID'))}",
            f"Priority: {clean(row.get('Priority Tier'))}",
            f"Mechanism: {clean(row.get('Mechanism'))}",
            f"Notes: {clean(row.get('Notes'))}",
            f"Strategy: {clean(row.get('Strategy Path'))}",
            "",
            "Human gate: no outbound sends, ad uploads, or external CRM writes without Mike approval.",
        ]
    )
    return {
        "title": clean(row.get("Title")),
        "bodyV2": {"markdown": notes},
        "dueAt": date_to_iso(row.get("Due Date", "")),
        "status": "TODO",
    }


def import_companies(client: TwentyClient, rows: list[dict[str, str]], dry_run: bool) -> tuple[ImportStats, dict[str, str], list[dict[str, Any]]]:
    stats = ImportStats()
    failures: list[dict[str, Any]] = []
    existing = {norm(item.get("name")): item.get("id") for item in client.list_objects("companies")}
    company_ids: dict[str, str] = {}
    for row in rows:
        key = norm(row.get("Name"))
        if not key:
            continue
        if key in existing:
            company_ids[key] = existing[key]
            stats.skipped += 1
            continue
        if dry_run:
            stats.created += 1
            continue
        try:
            created = client.create_object("companies", company_payload(row))
            company_id = created.get("id")
            if company_id:
                existing[key] = company_id
                company_ids[key] = company_id
            stats.created += 1
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            failures.append({"type": "company", "name": row.get("Name"), "error": str(exc)})
    return stats, company_ids, failures


def import_people(
    client: TwentyClient,
    rows: list[dict[str, str]],
    company_ids: dict[str, str],
    dry_run: bool,
) -> tuple[ImportStats, dict[tuple[str, str], str], list[dict[str, Any]]]:
    stats = ImportStats()
    failures: list[dict[str, Any]] = []
    existing = {
        (norm(item.get("name", {}).get("firstName") + " " + item.get("name", {}).get("lastName")), item.get("companyId") or ""): item.get("id")
        for item in client.list_objects("people")
    }
    people_ids: dict[tuple[str, str], str] = {}
    for row in rows:
        name_key = norm(row.get("Name"))
        company_id = company_ids.get(norm(row.get("Company Name")))
        key = (name_key, company_id or "")
        if not name_key:
            continue
        if key in existing:
            people_ids[key] = existing[key]
            stats.skipped += 1
            continue
        if dry_run:
            stats.created += 1
            continue
        try:
            created = client.create_object("people", person_payload(row, company_id))
            person_id = created.get("id")
            if person_id:
                existing[key] = person_id
                people_ids[key] = person_id
            stats.created += 1
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            failures.append({"type": "person", "name": row.get("Name"), "company": row.get("Company Name"), "error": str(exc)})
    return stats, people_ids, failures


def import_opportunities(
    client: TwentyClient,
    rows: list[dict[str, str]],
    company_ids: dict[str, str],
    people_ids: dict[tuple[str, str], str],
    dry_run: bool,
) -> tuple[ImportStats, list[dict[str, Any]]]:
    stats = ImportStats()
    failures: list[dict[str, Any]] = []
    existing = {norm(item.get("name")): item.get("id") for item in client.list_objects("opportunities")}
    for row in rows:
        key = norm(row.get("Name"))
        company_id = company_ids.get(norm(row.get("Company Name")))
        person_id = None
        if company_id:
            for (person_name, person_company_id), candidate_id in people_ids.items():
                if person_company_id == company_id:
                    person_id = candidate_id
                    break
        if not key:
            continue
        if key in existing:
            stats.skipped += 1
            continue
        if dry_run:
            stats.created += 1
            continue
        try:
            client.create_object("opportunities", opportunity_payload(row, company_id, person_id))
            stats.created += 1
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            failures.append({"type": "opportunity", "name": row.get("Name"), "error": str(exc)})
    return stats, failures


def import_tasks(client: TwentyClient, rows: list[dict[str, str]], dry_run: bool) -> tuple[ImportStats, list[dict[str, Any]]]:
    stats = ImportStats()
    failures: list[dict[str, Any]] = []
    existing = {norm(item.get("title")) for item in client.list_objects("tasks")}
    for row in rows:
        key = norm(row.get("Title"))
        if not key:
            continue
        if key in existing:
            stats.skipped += 1
            continue
        if dry_run:
            stats.created += 1
            continue
        try:
            client.create_object("tasks", task_payload(row))
            existing.add(key)
            stats.created += 1
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            failures.append({"type": "task", "title": row.get("Title"), "error": str(exc)})
    return stats, failures


def dedupe_tasks_by_title(client: TwentyClient, dry_run: bool) -> dict[str, Any]:
    tasks = client.list_objects("tasks")
    groups: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        key = norm(task.get("title"))
        if not key:
            continue
        groups.setdefault(key, []).append(task)

    duplicate_groups = {key: rows for key, rows in groups.items() if len(rows) > 1}
    deleted: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for rows in duplicate_groups.values():
        ordered = sorted(rows, key=lambda item: clean(item.get("createdAt")) or "")
        for duplicate in ordered[1:]:
            task_id = duplicate.get("id")
            if not task_id:
                continue
            if dry_run:
                deleted.append({"id": task_id, "title": clean(duplicate.get("title"))})
                continue
            try:
                client.delete_object("tasks", task_id)
                deleted.append({"id": task_id, "title": clean(duplicate.get("title"))})
            except Exception as exc:  # noqa: BLE001
                failures.append({"id": task_id, "title": clean(duplicate.get("title")), "error": str(exc)})

    return {
        "task_count_before": len(tasks),
        "duplicate_title_groups": len(duplicate_groups),
        "deleted": len(deleted),
        "failures": failures,
        "dry_run": dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import local GTM CSVs into local Twenty CRM.")
    parser.add_argument("--scope", default="denver_front_range_78", help="Import scope folder under out/twenty-crm/imports.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--auth-state", type=Path, default=DEFAULT_AUTH_STATE)
    parser.add_argument("--import-root", type=Path, default=DEFAULT_IMPORT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dedupe-tasks-only", action="store_true", help="Delete duplicate local Twenty tasks by exact normalized title.")
    args = parser.parse_args()

    scope_dir = args.import_root / args.scope
    paths = {
        "companies": scope_dir / "twenty_companies.csv",
        "people": scope_dir / "twenty_people.csv",
        "opportunities": scope_dir / "twenty_opportunities.csv",
        "tasks": scope_dir / "twenty_tasks.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing import files: {missing}")

    client = TwentyClient(args.base_url, read_token(args.auth_state))
    proof_path = scope_dir / "twenty_rest_import_proof.json"
    started_at = datetime.now(timezone.utc).isoformat()

    if args.dedupe_tasks_only:
        proof = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "started_at": started_at,
            "generated_for": "RIG and Mike Rodgers",
            "scope": args.scope,
            "base_url": args.base_url,
            "local_only": True,
            "external_side_effects": False,
            "human_gate": "Task dedupe only; no outbound sends, ad uploads, calendar sync, email sync, or external CRM writes were performed.",
            "dedupe": dedupe_tasks_by_title(client, args.dry_run),
        }
        proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(proof, indent=2))
        return 1 if proof["dedupe"]["failures"] else 0

    company_stats, company_ids, company_failures = import_companies(client, read_csv(paths["companies"]), args.dry_run)
    people_stats, people_ids, people_failures = import_people(client, read_csv(paths["people"]), company_ids, args.dry_run)
    opportunity_stats, opportunity_failures = import_opportunities(
        client, read_csv(paths["opportunities"]), company_ids, people_ids, args.dry_run
    )
    task_stats, task_failures = import_tasks(client, read_csv(paths["tasks"]), args.dry_run)

    proof = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_at,
        "generated_for": "RIG and Mike Rodgers",
        "scope": args.scope,
        "base_url": args.base_url,
        "dry_run": args.dry_run,
        "local_only": True,
        "external_side_effects": False,
        "human_gate": "No outbound sends, ad uploads, calendar sync, email sync, or external CRM writes were performed.",
        "stats": {
            "companies": company_stats.as_dict(),
            "people": people_stats.as_dict(),
            "opportunities": opportunity_stats.as_dict(),
            "tasks": task_stats.as_dict(),
        },
        "failures": company_failures + people_failures + opportunity_failures + task_failures,
    }
    proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))
    return 1 if proof["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
