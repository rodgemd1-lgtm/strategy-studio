#!/usr/bin/env python3
"""Enrich Strategy Studio teaser prospects with Apollo organization data.

A1-only. Reads final prospect domains, calls Apollo Bulk Organization
Enrichment in 10-domain batches, writes local audit artifacts, and optionally
patches `prospects_2000.jsonl` with Apollo-sourced company fields.

This is read-only against Apollo except for API credit consumption. It does not
create contacts, send outreach, enroll sequences, or export private data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import re
import time
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_studio.teaser.schema import TeaserInput


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out/teasers_2000"
APOLLO_BULK_ORG_PATH = "/api/v1/organizations/bulk_enrich"
TODAY = date.today().isoformat()
MIN_EMPLOYEES = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_private_env() -> None:
    for env_path in [Path.home() / ".hermes/.env", Path.home() / ".env", ROOT / ".env"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"^([A-Z0-9_]+)=(.*)$", line.strip())
            if not match:
                continue
            key, value = match.groups()
            if key.startswith("APOLLO_") and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def api_key() -> str:
    load_private_env()
    key = os.environ.get("APOLLO_ENRICHMENT_API_KEY") or os.environ.get("APOLLO_MASTER_API_KEY") or os.environ.get("APOLLO_API_KEY")
    if not key:
        raise SystemExit("Missing APOLLO_ENRICHMENT_API_KEY, APOLLO_MASTER_API_KEY, or APOLLO_API_KEY.")
    return key


def host(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^https?://", "", text).split("/")[0]
    return text.removeprefix("www.").strip()


def parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def parse_revenue_m(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        raw = float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None
    if raw <= 0:
        return None
    return round(raw / 1_000_000 if raw > 10_000 else raw, 1)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def request_bulk_org(domains: list[str], key: str) -> tuple[int, dict[str, Any]]:
    params = urllib.parse.urlencode({"domains[]": domains}, doseq=True)
    conn = http.client.HTTPSConnection("api.apollo.io", timeout=90)
    conn.request(
        "POST",
        f"{APOLLO_BULK_ORG_PATH}?{params}",
        body=b"{}",
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "User-Agent": "RIG-Strategy-Studio-A1/1.0",
            "X-Api-Key": key,
        },
    )
    response = conn.getresponse()
    text = response.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(text) if text else {}
    except json.JSONDecodeError:
        data = {"raw": text[:2000]}
    return response.status, data


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def load_domains(csv_path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    domains: dict[str, str] = {}
    for row in rows:
        domain = host(row.get("website"))
        if domain:
            domains[row["prospect_id"]] = domain
    return domains


def read_existing(raw_path: Path) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    if not raw_path.exists():
        return existing
    for line in raw_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        domain = host(row.get("primary_domain") or row.get("website_url") or row.get("domain"))
        if domain:
            existing[domain] = row
    return existing


def org_domain(org: dict[str, Any]) -> str:
    return host(org.get("primary_domain") or org.get("website_url") or org.get("domain"))


def enrich_domains(domains: list[str], args: argparse.Namespace) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    key = api_key()
    raw_path = args.output
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    organizations = read_existing(raw_path)
    failures: list[dict[str, Any]] = []
    pending = [domain for domain in domains if domain not in organizations]

    if not pending:
        return organizations, failures

    with raw_path.open("a", encoding="utf-8") as raw_file:
        for batch_index, batch in enumerate(chunked(pending[: args.max_domains or None], args.batch_size), 1):
            status, data = request_bulk_org(batch, key)
            if status not in (200, 201):
                failures.append({
                    "batch_index": batch_index,
                    "status": status,
                    "domain_count": len(batch),
                    "error": data.get("error_message") or data.get("error") or data.get("message") or data,
                    "at": now_iso(),
                })
                if status in (401, 403, 429):
                    break
                continue
            orgs = data.get("organizations") or data.get("accounts") or data.get("matches") or []
            if not isinstance(orgs, list):
                failures.append({"batch_index": batch_index, "status": status, "error": "unexpected_response_shape", "at": now_iso()})
                continue
            returned_domains = set()
            for org in orgs:
                if not isinstance(org, dict):
                    continue
                domain = org_domain(org)
                if not domain:
                    continue
                returned_domains.add(domain)
                org["_apollo_org_enriched_at"] = now_iso()
                org["_apollo_org_source"] = "https://docs.apollo.io/reference/bulk-organization-enrichment"
                raw_file.write(json.dumps(org, sort_keys=True) + "\n")
                organizations[domain] = org
            for domain in batch:
                if domain not in returned_domains and domain not in organizations:
                    failures.append({"batch_index": batch_index, "status": status, "domain": domain, "error": "apollo_missing_record", "at": now_iso()})
            print(f"[apollo-org] batch={batch_index} requested={len(batch)} returned={len(orgs)} cached_total={len(organizations)}")
            time.sleep(args.delay_ms / 1000)
    return organizations, failures


def apply_to_prospects(input_path: Path, output_path: Path, domains_by_id: dict[str, str], orgs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    output_path.unlink(missing_ok=True)
    report = {
        "total": len(source),
        "apollo_org_matches": 0,
        "employee_updates": 0,
        "annual_revenue_updates": 0,
        "below_employee_floor": 0,
        "validation_errors": 0,
        "generated_at": now_iso(),
    }
    failures: list[dict[str, Any]] = []

    with output_path.open("w", encoding="utf-8") as file:
        for record in source:
            domain = domains_by_id.get(record["prospect_id"], "")
            org = orgs.get(domain)
            if org:
                report["apollo_org_matches"] += 1
                record["evidence_sources"] = list(dict.fromkeys([
                    *record.get("evidence_sources", []),
                    f"Apollo Bulk Organization Enrichment {TODAY} · SW 0.60",
                ]))
                employee_count = parse_int(org.get("estimated_num_employees") or org.get("employee_count"))
                if employee_count is not None:
                    if employee_count < MIN_EMPLOYEES:
                        report["below_employee_floor"] += 1
                    if employee_count >= MIN_EMPLOYEES and employee_count != record.get("employees"):
                        record["employees"] = employee_count
                        report["employee_updates"] += 1
                        record["evidence_sources"] = list(dict.fromkeys([
                            *record["evidence_sources"],
                            f"Apollo organization employee count {TODAY} · SW 0.60",
                        ]))
                revenue_m = parse_revenue_m(org.get("annual_revenue"))
                if revenue_m is not None and revenue_m != record.get("revenue_usd_m"):
                    record["revenue_usd_m"] = revenue_m
                    report["annual_revenue_updates"] += 1
                    record["evidence_sources"] = list(dict.fromkeys([
                        *record["evidence_sources"],
                        f"Apollo organization annual revenue {TODAY} · SW 0.60",
                    ]))
                if org.get("industry") and str(org.get("industry")).lower() not in str(record.get("industry", "")).lower():
                    record["industry"] = f"{record['industry']} / Apollo: {org['industry']}"

            try:
                validated = TeaserInput.model_validate(record)
            except Exception as exc:
                report["validation_errors"] += 1
                failures.append({"prospect_id": record.get("prospect_id"), "error": str(exc), "last_step": "apollo_org_apply"})
                continue
            file.write(validated.model_dump_json() + "\n")

    if failures:
        (output_path.parent / "prospects_apollo_org_failed.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in failures),
            encoding="utf-8",
        )
    report["output_sha256"] = sha256(output_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Apollo organization-enrich Strategy Studio teaser prospects.")
    parser.add_argument("--prospect-csv", type=Path, default=ROOT / "inputs/prospect_list.csv")
    parser.add_argument("--input", type=Path, default=ROOT / "prospects_2000.jsonl")
    parser.add_argument("--output-jsonl", type=Path, default=ROOT / "prospects_2000.jsonl")
    parser.add_argument("--output", type=Path, default=OUT / "apollo_org_enrichment.jsonl")
    parser.add_argument("--failures", type=Path, default=OUT / "apollo_org_enrichment_failures.jsonl")
    parser.add_argument("--report", type=Path, default=OUT / "apollo_org_enrichment_report.json")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--delay-ms", type=int, default=350)
    parser.add_argument("--max-domains", type=int, default=0)
    parser.add_argument("--allow-credit-use", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.allow_credit_use:
        raise SystemExit("Refusing Apollo organization enrichment without --allow-credit-use.")
    if args.batch_size < 1 or args.batch_size > 10:
        raise SystemExit("--batch-size must be 1..10 per Apollo bulk organization enrichment limits.")

    domains_by_id = load_domains(args.prospect_csv)
    unique_domains = sorted(set(domains_by_id.values()))
    orgs, failures = enrich_domains(unique_domains, args)
    args.failures.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in failures), encoding="utf-8")

    report: dict[str, Any] = {
        "ok": True,
        "domains_requested": len(unique_domains[: args.max_domains or None]),
        "organizations_cached": len(orgs),
        "failures": len(failures),
        "raw_output": str(args.output),
        "failures_path": str(args.failures),
        "generated_at": now_iso(),
        "source": "Apollo Bulk Organization Enrichment",
        "source_url": "https://docs.apollo.io/reference/bulk-organization-enrichment",
    }
    if args.apply:
        report["apply"] = apply_to_prospects(args.input, args.output_jsonl, domains_by_id, orgs)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures and report.get("apply", {}).get("validation_errors", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
