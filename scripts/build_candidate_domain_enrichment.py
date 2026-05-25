#!/usr/bin/env python3
"""Build candidate-domain enrichment inputs and sidecar facts.

This bridge lets Strategy Studio use public organization enrichment evidence
before a row becomes a `TeaserInput`. It deliberately exports only company-level
domain facts, not private contact details.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHRONEMA = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/reports/rig-prospects/latest")
APOLLO = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/apollo")
PROSPECT_DB = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/prospects/prospect-database-latest.jsonl")
SOURCE_FILES = (
    PHRONEMA / "rig-prospects-private-latest.jsonl",
    APOLLO / "apollo-contacts-wide-manufacturing.jsonl",
    APOLLO / "apollo-contacts-wide-law.jsonl",
    APOLLO / "apollo-contacts-wide-medspa.jsonl",
    APOLLO / "apollo-contacts-wide-dental.jsonl",
    APOLLO / "apollo-contacts-wide-restoration.jsonl",
    APOLLO / "apollo-contacts-rig-adjacent-50k.jsonl",
    PROSPECT_DB,
)
TODAY = date.today().isoformat()
MIN_EMPLOYEES = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def host(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^https?://", "", text).split("/")[0]
    return text.removeprefix("www.").strip()


def url(domain: str) -> str:
    return f"https://{domain}" if domain else ""


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


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text[:72] or "candidate"


def row_domain(row: dict[str, Any]) -> str:
    return (
        host(row.get("organization_domain"))
        or host(row.get("organization_website"))
        or host(row.get("website_url"))
        or host(row.get("domain"))
    )


def row_company(row: dict[str, Any], domain: str) -> str:
    company = str(row.get("company") or row.get("organization_name") or row.get("company_name") or row.get("account_name") or "").strip()
    if company:
        return company
    return domain.split(".")[0].replace("-", " ").title()


def collect_domains() -> dict[str, dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for path in SOURCE_FILES:
        for row in read_jsonl(path):
            domain = row_domain(row)
            if not domain:
                continue
            current = domains.setdefault(domain, {
                "domain": domain,
                "company_name": row_company(row, domain),
                "website": str(row.get("website_url") or row.get("organization_website") or url(domain)),
                "source_files": [],
                "source_employee_count": None,
                "source_revenue_usd_m": None,
            })
            if path.name not in current["source_files"]:
                current["source_files"].append(path.name)
            employee_count = parse_int(row.get("organization_employee_count") or row.get("employees"))
            if employee_count and (not current["source_employee_count"] or employee_count > current["source_employee_count"]):
                current["source_employee_count"] = employee_count
            revenue_m = parse_revenue_m(row.get("organization_revenue") or row.get("revenue_usd_m"))
            if revenue_m and not current["source_revenue_usd_m"]:
                current["source_revenue_usd_m"] = revenue_m
    return domains


def write_candidate_csv(path: Path, domains: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["prospect_id", "company_name", "website", "industry_hint", "linkedin_url", "cloned_site_url"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for domain, row in sorted(domains.items()):
            candidate_id = slug(domain)
            writer.writerow({
                "prospect_id": candidate_id,
                "company_name": row["company_name"],
                "website": row["website"] or url(domain),
                "industry_hint": "RIG prospect company-level enrichment",
                "linkedin_url": "",
                "cloned_site_url": f"https://{candidate_id}-forge.vercel.app",
            })


def read_apollo_orgs(path: Path) -> dict[str, dict[str, Any]]:
    orgs: dict[str, dict[str, Any]] = {}
    for org in read_jsonl(path):
        domain = host(org.get("primary_domain") or org.get("website_url") or org.get("domain"))
        if domain:
            orgs[domain] = org
    return orgs


def read_scraper_facts(path: Path) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        domain = host(row.get("domain"))
        if domain:
            facts[domain] = row
    return facts


def build_facts(domains: dict[str, dict[str, Any]], apollo_orgs: dict[str, dict[str, Any]], scraper_facts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for domain, base in sorted(domains.items()):
        org = apollo_orgs.get(domain) or {}
        scrape = scraper_facts.get(domain) or {}
        employee_count = (
            parse_int(org.get("estimated_num_employees") or org.get("employee_count"))
            or parse_int(scrape.get("employee_count"))
            or parse_int(base.get("source_employee_count"))
        )
        revenue_m = (
            parse_revenue_m(org.get("annual_revenue"))
            or parse_revenue_m(scrape.get("revenue_usd_m"))
            or parse_revenue_m(base.get("source_revenue_usd_m"))
        )
        sources = []
        if parse_int(org.get("estimated_num_employees") or org.get("employee_count")):
            sources.append(f"Apollo Bulk Organization Enrichment {TODAY} · SW 0.60")
        if scrape.get("source_count"):
            sources.extend(scrape.get("sources") or [f"Scraper company evidence {TODAY} · SW 0.40"])
        if parse_int(base.get("source_employee_count")):
            sources.append(f"Phronema/Apollo source export employee signal {TODAY} · SW 0.50")
        if not employee_count or employee_count < MIN_EMPLOYEES:
            continue
        facts.append({
            "domain": domain,
            "company_name": org.get("name") or base["company_name"],
            "website_url": org.get("website_url") or base.get("website") or url(domain),
            "employee_count": employee_count,
            "revenue_usd_m": revenue_m,
            "industry": org.get("industry") or scrape.get("industry") or "",
            "sources": list(dict.fromkeys(sources))[:8],
            "source_files": base.get("source_files") or [],
            "generated_at": now_iso(),
        })
    return facts


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build candidate-domain enrichment sidecar for Strategy Studio.")
    parser.add_argument("--candidate-csv", type=Path, default=ROOT / "out/teasers_2000/candidate_domain_probe.csv")
    parser.add_argument("--apollo-org-jsonl", type=Path, default=ROOT / "out/teasers_2000/candidate_apollo_org_enrichment.jsonl")
    parser.add_argument("--scraper-facts-jsonl", type=Path, default=ROOT / "out/teasers_2000/candidate_scraper_company_facts.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "out/teasers_2000/company_enrichment_facts.jsonl")
    parser.add_argument("--write-candidate-csv", action="store_true")
    parser.add_argument("--build-facts", action="store_true")
    args = parser.parse_args()

    domains = collect_domains()
    if args.write_candidate_csv:
        write_candidate_csv(args.candidate_csv, domains)
    facts: list[dict[str, Any]] = []
    if args.build_facts:
        facts = build_facts(domains, read_apollo_orgs(args.apollo_org_jsonl), read_scraper_facts(args.scraper_facts_jsonl))
        write_jsonl(args.output, facts)
    report = {
        "ok": True,
        "candidate_domains": len(domains),
        "candidate_csv": str(args.candidate_csv),
        "facts": len(facts),
        "output": str(args.output),
        "generated_at": now_iso(),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
