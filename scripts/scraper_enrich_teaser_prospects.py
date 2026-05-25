#!/usr/bin/env python3
"""Scraper-backed enrichment for Strategy Studio teaser prospects.

A1-only. Uses public scraper/search APIs when keys are present, writes local
evidence artifacts, and optionally patches `prospects_2000.jsonl` with cited
scraper sources. It does not send outreach, create CRM/contact records, or
export private data.

Providers:
- Tavily search
- Exa search
- Firecrawl search
- Jina Reader ("jing" in some notes)
- CrawlAI local HTTP fallback (deterministic site crawl; crawl4ai optional)
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_studio.teaser.schema import TeaserInput


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out/teasers_2000"
TODAY = date.today().isoformat()
USER_AGENT = "RIG-Strategy-Studio-Scraper-A1/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_private_env() -> None:
    for env_path in [Path.home() / ".hermes/.env", Path.home() / ".env", ROOT / ".env", ROOT / ".env.local"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"^([A-Z0-9_]+)=(.*)$", line.strip())
            if not match:
                continue
            key, value = match.groups()
            if key.endswith("_API_KEY") and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def host(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^https?://", "", text).split("/")[0]
    return text.removeprefix("www.").strip()


def url_for_host(domain: str) -> str:
    return f"https://{domain}" if domain else ""


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: dict[str, Any] | None = None, timeout: int = 45) -> tuple[int, Any]:
    payload = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(2_000_000).decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return response.status, {"raw": raw[:4000]}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw[:1000]}
        return exc.code, data
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, ValueError) as exc:
        return 0, {"error": f"{type(exc).__name__}: {exc}"}


def request_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 45) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
            return response.status, response.read(800_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:4000]
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, ValueError) as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def normalize_result(provider: str, query: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": provider,
        "query": query,
        "title": str(item.get("title") or item.get("name") or item.get("url") or "")[:300],
        "url": str(item.get("url") or item.get("link") or item.get("website") or "")[:800],
        "snippet": str(item.get("description") or item.get("snippet") or item.get("content") or item.get("text") or "")[:4000],
        "retrieved_at": now_iso(),
    }


def tavily_search(query: str) -> list[dict[str, Any]]:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        return []
    status, data = request_json(
        "https://api.tavily.com/search",
        method="POST",
        body={"api_key": key, "query": query, "max_results": 5, "search_depth": "advanced", "include_answer": False},
    )
    if status not in (200, 201):
        return [{"provider": "tavily", "query": query, "error": data, "retrieved_at": now_iso()}]
    return [normalize_result("tavily", query, item) for item in data.get("results", [])[:5]]


def exa_search(query: str) -> list[dict[str, Any]]:
    key = os.environ.get("EXA_API_KEY")
    if not key:
        return []
    status, data = request_json(
        "https://api.exa.ai/search",
        method="POST",
        headers={"x-api-key": key},
        body={"query": query, "numResults": 5, "type": "neural"},
    )
    if status not in (200, 201):
        return [{"provider": "exa", "query": query, "error": data, "retrieved_at": now_iso()}]
    return [normalize_result("exa", query, item) for item in data.get("results", [])[:5]]


def firecrawl_search(query: str) -> list[dict[str, Any]]:
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        return []
    status, data = request_json(
        "https://api.firecrawl.dev/v1/search",
        method="POST",
        headers={"authorization": f"Bearer {key}"},
        body={"query": query, "limit": 5},
    )
    if status not in (200, 201):
        return [{"provider": "firecrawl", "query": query, "error": data, "retrieved_at": now_iso()}]
    records = data.get("data", data if isinstance(data, list) else [])
    return [normalize_result("firecrawl", query, item) for item in records[:5]]


def jina_reader(url: str, query: str) -> dict[str, Any]:
    if not url:
        return {}
    target = "https://r.jina.ai/http://" + url.removeprefix("http://").removeprefix("https://")
    headers = {}
    if os.environ.get("JINA_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['JINA_API_KEY']}"
    status, text = request_text(target, headers=headers, timeout=55)
    if status not in (200, 201):
        return {"provider": "jina", "query": query, "url": url, "error": text[:1000], "retrieved_at": now_iso()}
    return {"provider": "jina", "query": query, "url": url, "snippet": text[:8000], "retrieved_at": now_iso()}


def crawlai_local(url: str, query: str) -> dict[str, Any]:
    if not url:
        return {}
    status, text = request_text(url, timeout=30)
    if status not in (200, 201):
        if url.startswith("https://"):
            return crawlai_local("http://" + url.removeprefix("https://"), query)
        return {"provider": "crawlai", "query": query, "url": url, "error": text[:1000], "retrieved_at": now_iso()}
    clean = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    clean = html.unescape(re.sub(r"<[^>]+>", " ", clean))
    clean = re.sub(r"\s+", " ", clean).strip()
    return {"provider": "crawlai", "query": query, "url": url, "snippet": clean[:8000], "retrieved_at": now_iso()}


EMPLOYEE_PATTERNS = [
    re.compile(r"\b(?:team of|over|more than|about|approximately|approx\.?)\s+([1-9][0-9]{1,5})\s+(?:employees|people|professionals|staff|team members)\b", re.I),
    re.compile(r"\b([1-9][0-9]{1,5})\+?\s+(?:employees|people|professionals|staff|team members)\b", re.I),
]

REVENUE_PATTERNS = [
    re.compile(r"\$([0-9]+(?:\.[0-9]+)?)\s*(billion|million|bn|m)\b", re.I),
    re.compile(r"\bannual revenue(?: is| of|:)?\s*\$?([0-9]+(?:\.[0-9]+)?)\s*(billion|million|bn|m)?\b", re.I),
]


def extract_employee_count(text: str) -> int | None:
    for pattern in EMPLOYEE_PATTERNS:
        for match in pattern.finditer(text or ""):
            value = int(match.group(1).replace(",", ""))
            if 10 <= value <= 500_000:
                return value
    return None


def extract_revenue_m(text: str) -> float | None:
    for pattern in REVENUE_PATTERNS:
        match = pattern.search(text or "")
        if not match:
            continue
        value = float(match.group(1))
        unit = (match.group(2) or "m").lower()
        if unit in {"billion", "bn"}:
            value *= 1000
        if 0.05 <= value <= 1_000_000:
            return round(value, 1)
    return None


def provider_sources(providers: set[str]) -> list[str]:
    mapping = {
        "tavily": f"Tavily public web search {TODAY} · SW 0.40",
        "exa": f"Exa neural web search {TODAY} · SW 0.40",
        "firecrawl": f"Firecrawl public web search {TODAY} · SW 0.40",
        "jina": f"Jina Reader public site capture {TODAY} · SW 0.42",
        "crawlai": f"CrawlAI local public site crawl {TODAY} · SW 0.42",
    }
    return [mapping[name] for name in ["tavily", "exa", "firecrawl", "jina", "crawlai"] if name in providers]


def query_for(record: dict[str, Any], domain: str) -> str:
    company = record.get("company_name") or record.get("company") or domain
    industry = record.get("industry_short") or record.get("industry") or ""
    return f'"{company}" {domain} employees revenue services {industry}'.strip()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def select_records(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.only_non_h:
        selected = [row for row in rows if row.get("confidence") != "H"]
    else:
        selected = rows
    if args.max_records:
        selected = selected[: args.max_records]
    return selected


def collect_for_record(record: dict[str, Any], args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    domain = host(record.get("website") or record.get("website_url") or record.get("cloned_site_url") or "")
    if not domain:
        # `TeaserInput` records do not store the original website. Fall back to
        # the prospect CSV mapping through caller-populated `_domain`.
        domain = host(record.get("_domain"))
    url = url_for_host(domain)
    query = query_for(record, domain)
    evidence: list[dict[str, Any]] = []
    providers_seen: set[str] = set()

    provider_fns = {
        "tavily": tavily_search,
        "exa": exa_search,
        "firecrawl": firecrawl_search,
    }
    selected_providers = [item.strip() for item in args.search_providers.split(",") if item.strip()]
    for provider_name in selected_providers:
        fn = provider_fns.get(provider_name)
        if not fn:
            continue
        provider_rows = fn(query)
        for row in provider_rows:
            row["prospect_id"] = record["prospect_id"]
            row["company_name"] = record.get("company_name")
            evidence.append(row)
            providers_seen.add(row.get("provider", ""))
        if args.delay_ms:
            time.sleep(args.delay_ms / 1000)

    if not args.search_only:
        for row in [jina_reader(url, query), crawlai_local(url, query)]:
            if row:
                row["prospect_id"] = record["prospect_id"]
                row["company_name"] = record.get("company_name")
                evidence.append(row)
                providers_seen.add(row.get("provider", ""))

    combined_text = "\n".join(str(row.get("snippet") or row.get("title") or "") for row in evidence if not row.get("error"))
    facts = {
        "prospect_id": record["prospect_id"],
        "company_name": record.get("company_name"),
        "domain": domain,
        "providers": sorted(p for p in providers_seen if p),
        "employee_count": extract_employee_count(combined_text),
        "revenue_usd_m": extract_revenue_m(combined_text),
        "source_count": len([row for row in evidence if not row.get("error")]),
        "error_count": len([row for row in evidence if row.get("error")]),
        "retrieved_at": now_iso(),
    }
    return evidence, facts


def load_domain_map(csv_path: Path) -> dict[str, str]:
    import csv

    if not csv_path.exists():
        return {}
    mapping: dict[str, str] = {}
    with csv_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            mapping[row.get("prospect_id", "")] = host(row.get("website"))
    return mapping


def apply_enrichment(records: list[dict[str, Any]], facts_by_id: dict[str, dict[str, Any]], output_path: Path) -> dict[str, Any]:
    report = {
        "total": len(records),
        "scraper_matches": 0,
        "employee_updates": 0,
        "revenue_updates": 0,
        "confidence_upgrades": 0,
        "validation_errors": 0,
    }
    output_path.unlink(missing_ok=True)
    failures: list[dict[str, Any]] = []
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            facts = facts_by_id.get(record["prospect_id"])
            if facts and facts.get("source_count", 0) > 0:
                report["scraper_matches"] += 1
                sources = list(record.get("evidence_sources") or [])
                sources = list(dict.fromkeys([*sources, *provider_sources(set(facts.get("providers") or []))]))
                record["evidence_sources"] = sources[:12]
                if facts.get("employee_count") and int(facts["employee_count"]) >= 10 and int(facts["employee_count"]) != int(record.get("employees") or 0):
                    # Do not downshift a known Apollo value; only improve UNKNOWN-like fallbacks.
                    if int(record.get("employees") or 0) <= 11:
                        record["employees"] = int(facts["employee_count"])
                        report["employee_updates"] += 1
                if facts.get("revenue_usd_m") and not record.get("revenue_usd_m"):
                    record["revenue_usd_m"] = facts["revenue_usd_m"]
                    report["revenue_updates"] += 1
                if record.get("confidence") == "M" and len(sources) >= 5:
                    record["confidence"] = "H"
                    report["confidence_upgrades"] += 1
            try:
                validated = TeaserInput.model_validate(record)
            except Exception as exc:
                report["validation_errors"] += 1
                failures.append({"prospect_id": record.get("prospect_id"), "error": str(exc), "last_step": "scraper_apply"})
                continue
            file.write(validated.model_dump_json() + "\n")
    if failures:
        write_jsonl(output_path.parent / "prospects_scraper_failed.jsonl", failures)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Use scraper/search APIs to enrich Strategy Studio teaser prospects.")
    parser.add_argument("--input", type=Path, default=ROOT / "prospects_2000.jsonl")
    parser.add_argument("--output-jsonl", type=Path, default=ROOT / "prospects_2000.jsonl")
    parser.add_argument("--prospect-csv", type=Path, default=ROOT / "inputs/prospect_list.csv")
    parser.add_argument("--evidence", type=Path, default=OUT / "scraper_company_evidence.jsonl")
    parser.add_argument("--facts", type=Path, default=OUT / "scraper_company_facts.jsonl")
    parser.add_argument("--report", type=Path, default=OUT / "scraper_enrichment_report.json")
    parser.add_argument("--max-records", type=int, default=0)
    parser.add_argument("--only-non-h", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--search-only", action="store_true")
    parser.add_argument("--search-providers", default="tavily,exa,firecrawl")
    parser.add_argument("--delay-ms", type=int, default=150)
    args = parser.parse_args()

    load_private_env()
    records = read_jsonl(args.input)
    domain_map = load_domain_map(args.prospect_csv)
    for record in records:
        record["_domain"] = domain_map.get(record["prospect_id"], "")

    selected = select_records(records, args)
    all_evidence: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    provider_counts: Counter[str] = Counter()

    for idx, record in enumerate(selected, 1):
        evidence_rows, fact = collect_for_record(record, args)
        all_evidence.extend(evidence_rows)
        facts.append(fact)
        provider_counts.update(row.get("provider", "unknown") for row in evidence_rows)
        print(f"[scraper-enrich] {idx}/{len(selected)} {record['prospect_id']} providers={','.join(fact['providers']) or 'none'} sources={fact['source_count']} errors={fact['error_count']}")

    write_jsonl(args.evidence, all_evidence)
    write_jsonl(args.facts, facts)
    facts_by_id = {row["prospect_id"]: row for row in facts}

    report: dict[str, Any] = {
        "ok": True,
        "generated_at": now_iso(),
        "input_records": len(records),
        "selected_records": len(selected),
        "provider_counts": dict(provider_counts),
        "facts_with_employee_count": sum(1 for row in facts if row.get("employee_count")),
        "facts_with_revenue": sum(1 for row in facts if row.get("revenue_usd_m")),
        "evidence": str(args.evidence),
        "facts": str(args.facts),
        "evidence_sha256": sha256(args.evidence) if args.evidence.exists() else "",
        "facts_sha256": sha256(args.facts) if args.facts.exists() else "",
        "credentials": {
            "tavily": "present" if os.environ.get("TAVILY_API_KEY") else "missing",
            "exa": "present" if os.environ.get("EXA_API_KEY") else "missing",
            "firecrawl": "present" if os.environ.get("FIRECRAWL_API_KEY") else "missing",
            "jina": "present" if os.environ.get("JINA_API_KEY") else "missing",
            "crawlai": "local_http_fallback",
        },
        "provider_docs": {
            "tavily": "https://docs.tavily.com/documentation/api-reference/endpoint/search",
            "exa": "https://docs.exa.ai/reference/search",
            "firecrawl": "https://docs.firecrawl.dev/api-reference/endpoint/search",
            "jina": "https://jina.ai/reader/",
            "crawlai": "local deterministic crawl fallback",
        },
    }
    if args.apply:
        report["apply"] = apply_enrichment(records, facts_by_id, args.output_jsonl)

    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("apply", {}).get("validation_errors", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
