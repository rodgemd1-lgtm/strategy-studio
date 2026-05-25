#!/usr/bin/env python3
"""Build TeaserInput JSONL from the Phronema/LakeOS RIG prospect corpus.

A1-only: deterministic transforms, strict schema validation, no LLM calls.
The script uses Phronema prospect + market-intel exports as the evidence base,
optionally fetches public company pages for capabilities/colors, writes the
required `inputs/prospect_list.csv`, appends validated records to
`prospects_2000.jsonl`, and writes failures to `prospects_failed.jsonl`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_studio.teaser.schema import TeaserInput

ROOT = Path(__file__).resolve().parents[1]
PHRONEMA = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/reports/rig-prospects/latest")
DEFAULT_PROSPECTS = PHRONEMA / "rig-prospects-private-latest.jsonl"
DEFAULT_MARKET = PHRONEMA / "rig-prospects-market-intel-latest.jsonl"
APOLLO = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/apollo")
PROSPECT_DB = Path("/Users/mikerodgers/rig-lab/phronema/evidence_store/prospects/prospect-database-latest.jsonl")
DEFAULT_EXTRA_PROSPECTS = (
    APOLLO / "apollo-contacts-wide-manufacturing.jsonl",
    APOLLO / "apollo-contacts-wide-law.jsonl",
    APOLLO / "apollo-contacts-wide-medspa.jsonl",
    APOLLO / "apollo-contacts-wide-dental.jsonl",
    APOLLO / "apollo-contacts-wide-restoration.jsonl",
    APOLLO / "apollo-contacts-rig-adjacent-50k.jsonl",
    PROSPECT_DB,
)
DEFAULT_COMPANY_ENRICHMENT = ROOT / "out/teasers_2000/company_enrichment_facts.jsonl"

TODAY = date.today().isoformat()
SITE_TIMEOUT_SECONDS = 4
MIN_EMPLOYEES = 10


@dataclass(frozen=True)
class SegmentPlan:
    industry: str
    industry_short: str
    capabilities: tuple[str, str, str]
    gap: str
    wound_months: int
    wound_channel: str
    wound_trigger: str
    loop_name: str
    mechanism_description: str
    advantages: tuple[str, str, str]
    comparable_company: str
    comparable_year_start: int
    comparable_year_end: int
    comparable_revenue_start_m: float
    comparable_revenue_end_m: float
    comparable_segment_growth_m: float
    threats: tuple[tuple[str, str, str, str, float], tuple[str, str, str, str, float], tuple[str, str, str, str, float]]
    disqualifiers: tuple[str, str, str]
    sources: tuple[str, ...]


SEGMENTS: dict[str, SegmentPlan] = {
    "rig-midmarket-manufacturing": SegmentPlan(
        industry="Mid-market manufacturing, quoting, production, supplier, and quality operations",
        industry_short="manufacturing ops",
        capabilities=("Production Scheduling", "Quoting", "Quality Documentation"),
        gap="The operating data exists, but it is not packaged as a compounding owner-level intelligence layer.",
        wound_months=6,
        wound_channel="regulated industrial and defense-adjacent procurement channel",
        wound_trigger="CMMC Level 2 certification requirements enter Phase 2 solicitations on Nov 10, 2026",
        loop_name="Signal Compounding Loop",
        mechanism_description="Shop-floor signals, quote history, supplier exceptions, and quality records become a private execution loop that compounds with every job shipped.",
        advantages=(
            "Installed production history — ERP vendors see transactions; you own the operating exceptions competitors cannot clone.",
            "Supplier and quality scars — regional competitors quote work, but rarely turn exception history into a sales asset.",
            "Owner-led speed — public industrials have budget; mid-market operators can redesign the workflow before procurement hardens.",
        ),
        comparable_company="Rockwell Automation, Inc.",
        comparable_year_start=2016,
        comparable_year_end=2025,
        comparable_revenue_start_m=5880,
        comparable_revenue_end_m=8260,
        comparable_segment_growth_m=1900,
        threats=(
            ("Siemens Xcelerator", "Tier 1", "6-12", "Digital factory suite can bundle analytics into existing enterprise accounts", 0.55),
            ("Rockwell Automation", "Tier 2", "12-24", "Installed controls footprint plus analytics channel reaches plant leadership", 0.55),
            ("Epicor / Plex", "Tier 3", "24-36", "ERP/MES vendors can reframe system data as intelligence after lock-in", 0.45),
        ),
        disqualifiers=(
            "Leadership believes the ERP already explains operations. It records operations; it does not create strategic memory.",
            "Sales and operations will not share quote-loss, delay, supplier, and quality data in one governed loop.",
            "The owner wants AI theater instead of a 90-day production workflow with falsifiable ROI.",
        ),
        sources=(
            "CMMC 48 CFR final rule phased rollout Nov 10 2026 · SW 0.65",
            "Google AI Max for Search campaigns May 2025 · SW 0.50",
        ),
    ),
    "rig-law-growth-firms": SegmentPlan(
        industry="Growth-oriented legal services, intake, case-flow, and client communication operations",
        industry_short="legal ops",
        capabilities=("Intake", "Case Updates", "Client Follow-Up"),
        gap="The firm sells legal expertise, but the intake and follow-up path is not packaged as evidence-backed revenue intelligence.",
        wound_months=7,
        wound_channel="AI-native local legal search and intake channel",
        wound_trigger="Google AI Mode and AI Max reshape search/ad discovery through Dec 31, 2026 buying cycles",
        loop_name="Intake Memory Loop",
        mechanism_description="Every search visit, intake response, missed call, case-update request, and review signal feeds a private case-growth memory layer.",
        advantages=(
            "Practice-area specificity — generic legal AI vendors cannot reuse your local case language and intake objections.",
            "Existing PPC spend — competitors buy clicks; you can convert click waste into a scored follow-up asset.",
            "Partner authority — smaller firms can change intake discipline faster than national legal brands.",
        ),
        comparable_company="Thomson Reuters Corporation",
        comparable_year_start=2018,
        comparable_year_end=2025,
        comparable_revenue_start_m=5350,
        comparable_revenue_end_m=7800,
        comparable_segment_growth_m=1200,
        threats=(
            ("Thomson Reuters CoCounsel", "Tier 1", "6-12", "Legal AI channel already reaches firm leadership and knowledge work", 0.60),
            ("Clio Duo", "Tier 2", "12-24", "Practice-management distribution can absorb intake intelligence", 0.45),
            ("Filevine", "Tier 3", "24-36", "Case-management workflow can wrap follow-up before agencies do", 0.40),
        ),
        disqualifiers=(
            "Partners believe more ad spend will fix intake leakage without operational discipline.",
            "The firm will not expose missed-call, lead-source, and follow-up data for a falsification audit.",
            "Leadership treats AI as paralegal replacement instead of owner-level revenue intelligence.",
        ),
        sources=(
            "Google AI Mode in Search public rollout May 2025 · SW 0.55",
            "Thomson Reuters CoCounsel product disclosures · SW 0.55",
        ),
    ),
    "rig-cpa-advisory": SegmentPlan(
        industry="CPA, tax, client accounting, and advisory services",
        industry_short="CPA advisory",
        capabilities=("Tax Advisory", "Client Accounting", "Reporting"),
        gap="Client work is recurring, but the advisory logic is not productized into reusable proof-backed intelligence.",
        wound_months=7,
        wound_channel="AI-mediated client advisory and accounting workflow channel",
        wound_trigger="AI search and automated accounting assistance reshape client acquisition through Dec 31, 2026 buying cycles",
        loop_name="Advisory Ledger Loop",
        mechanism_description="Client questions, close packets, tax positions, reporting exceptions, and advisory decisions become reusable firm memory.",
        advantages=(
            "Recurring client data — AI bookkeeping tools see transactions; the firm sees decisions, context, and trust.",
            "Partner judgment — software competitors automate work, but cannot inherit your client-specific advisory memory.",
            "Niche vertical exposure — local firms can package one vertical before national networks notice.",
        ),
        comparable_company="Intuit Inc.",
        comparable_year_start=2016,
        comparable_year_end=2025,
        comparable_revenue_start_m=4690,
        comparable_revenue_end_m=18350,
        comparable_segment_growth_m=4800,
        threats=(
            ("Intuit Assist", "Tier 1", "6-12", "Embedded AI reaches SMB accounting buyers before firms do", 0.60),
            ("Thomson Reuters Tax", "Tier 2", "12-24", "Tax workflow distribution can package advisory automation", 0.55),
            ("Karbon AI", "Tier 3", "24-36", "Practice-management vendors can turn workflow data into advice prompts", 0.40),
        ),
        disqualifiers=(
            "Partners believe compliance revenue alone protects the firm. It does not.",
            "The team will not standardize advisory artifacts across clients.",
            "Leadership treats AI as staff efficiency only, not a new advisory product line.",
        ),
        sources=(
            "Intuit FY2025 filings and Assist disclosures · SW 0.65",
            "Google AI Max for Search campaigns May 2025 · SW 0.50",
        ),
    ),
    "rig-medspa-aesthetics": SegmentPlan(
        industry="Medspa, aesthetics, membership, consult, and patient-retention operations",
        industry_short="medspa growth",
        capabilities=("Consults", "Memberships", "Rebooking"),
        gap="The patient journey exists across tools, but it is not packaged as a private growth intelligence loop.",
        wound_months=7,
        wound_channel="AI-native local discovery and patient follow-up channel",
        wound_trigger="Google AI Mode and AI Max reshape local treatment discovery through Dec 31, 2026 buying cycles",
        loop_name="Patient Recapture Loop",
        mechanism_description="Consult, no-show, membership, treatment, and rebooking signals become a weekly owner intelligence loop.",
        advantages=(
            "High-margin procedures — generic schedulers cannot see where contribution margin leaks after consult.",
            "Before/after evidence — competitors post content; you can turn outcomes into segmented follow-up intelligence.",
            "Local trust density — national platforms have software, but the owner owns patient memory and referral texture.",
        ),
        comparable_company="Hims & Hers Health, Inc.",
        comparable_year_start=2018,
        comparable_year_end=2025,
        comparable_revenue_start_m=27,
        comparable_revenue_end_m=1480,
        comparable_segment_growth_m=900,
        threats=(
            ("Zenoti", "Tier 1", "6-12", "Spa/medspa system of record can bundle AI retention workflows", 0.50),
            ("Boulevard", "Tier 2", "12-24", "Booking and marketing workflow owns the patient journey surface", 0.45),
            ("PatientNow", "Tier 3", "24-36", "Aesthetics-specific CRM can wrap reactivation before agencies do", 0.40),
        ),
        disqualifiers=(
            "The owner wants more leads but will not fix consult, no-show, membership, and rebooking leakage.",
            "Providers refuse standardized patient follow-up data capture.",
            "Leadership treats AI as a chatbot instead of an owner dashboard for margin and retention.",
        ),
        sources=(
            "Google AI Mode local/business search disclosures May 2025 · SW 0.55",
            "Hims & Hers FY2025 investor materials · SW 0.55",
        ),
    ),
    "rig-pe-portfolio-ops": SegmentPlan(
        industry="Private equity value creation and portfolio operations",
        industry_short="portfolio ops",
        capabilities=("Value Creation", "Portfolio Operations", "Operating Playbooks"),
        gap="The portfolio has operating patterns, but the repeatable AI value-creation substrate is not productized across companies.",
        wound_months=7,
        wound_channel="AI value-creation and regulated portfolio transformation channel",
        wound_trigger="EU AI Act operational provisions and AI governance pressure tighten by Aug 2, 2026",
        loop_name="Portfolio Proof Loop",
        mechanism_description="Every portfolio workflow audit, implementation result, and management decision becomes a reusable value-creation proof asset.",
        advantages=(
            "Cross-company visibility — vendors see one workflow; operators see repeatable margin patterns across the fund.",
            "Board pressure — competitors sell tools; you can sell evidence-backed value creation with proof packets.",
            "Capital access — PE can fund portfolio-wide implementation before mid-market competitors can react.",
        ),
        comparable_company="Palantir Technologies Inc.",
        comparable_year_start=2018,
        comparable_year_end=2025,
        comparable_revenue_start_m=595,
        comparable_revenue_end_m=3900,
        comparable_segment_growth_m=1800,
        threats=(
            ("Palantir AIP", "Tier 1", "6-12", "Board-level AI operating system narrative already lands with enterprises", 0.60),
            ("Accenture GenAI", "Tier 2", "12-24", "Services scale can absorb portfolio-transformation budgets", 0.55),
            ("Snowflake Cortex", "Tier 3", "24-36", "Data-cloud incumbency can become default portfolio AI substrate", 0.45),
        ),
        disqualifiers=(
            "The fund wants AI headlines but will not pick three measurable operating workflows.",
            "Operating partners cannot force portfolio-company data access.",
            "Leadership wants a dashboard without changing management cadence.",
        ),
        sources=(
            "EU AI Act implementation timeline Aug 2 2026 · SW 0.65",
            "Palantir FY2025 AIP investor disclosures · SW 0.60",
        ),
    ),
    "rig-healthcare-orthopedics": SegmentPlan(
        industry="Specialty healthcare, orthopedics, patient acquisition, scheduling, and follow-up operations",
        industry_short="patient ops",
        capabilities=("Patient Acquisition", "Scheduling", "Follow-Up"),
        gap="Patient demand, scheduling, documentation, and follow-up are not unified into a governed intelligence loop.",
        wound_months=7,
        wound_channel="AI-native patient discovery and regulated workflow channel",
        wound_trigger="AI search plus healthcare AI governance pressure tightens through Dec 31, 2026 buying cycles",
        loop_name="Patient Signal Loop",
        mechanism_description="Referral, search, scheduling, documentation, and follow-up signals become a private growth and operations memory layer.",
        advantages=(
            "Referral texture — EHR vendors store visits; practices own why patients choose, delay, or drop.",
            "High-value procedures — small conversion gains beat generic chatbot savings.",
            "Clinical trust — local practices can package proof-backed patient pathways before national platforms localize.",
        ),
        comparable_company="Doximity, Inc.",
        comparable_year_start=2016,
        comparable_year_end=2025,
        comparable_revenue_start_m=85,
        comparable_revenue_end_m=570,
        comparable_segment_growth_m=260,
        threats=(
            ("Epic", "Tier 1", "6-12", "EHR workflow reach can absorb AI documentation and patient routing", 0.55),
            ("Athenahealth", "Tier 2", "12-24", "Practice network can package patient engagement intelligence", 0.45),
            ("NexHealth", "Tier 3", "24-36", "Scheduling layer can own reactivation before practices build memory", 0.40),
        ),
        disqualifiers=(
            "The practice believes the EHR is the operating brain. It is a record, not a growth system.",
            "No one will own referral, scheduling, and follow-up as one metric chain.",
            "Leadership wants patient-facing AI before operational governance is in place.",
        ),
        sources=(
            "Google AI Mode local/business search disclosures May 2025 · SW 0.55",
            "EU AI Act healthcare/high-risk governance timeline Aug 2 2026 · SW 0.55",
        ),
    ),
    "rig-service-operators": SegmentPlan(
        industry="Progressive service business revenue operations, scheduling, reviews, and reactivation",
        industry_short="service ops",
        capabilities=("Lead Capture", "Scheduling", "Customer Reactivation"),
        gap="The service motion runs, but old customers, missed leads, reviews, and dispatch data are not one owner intelligence graph.",
        wound_months=7,
        wound_channel="AI-native local service discovery and quote-to-cash channel",
        wound_trigger="Google AI Mode and AI Max reshape local service discovery through Dec 31, 2026 buying cycles",
        loop_name="Revenue Memory Loop",
        mechanism_description="Leads, calls, quotes, dispatch outcomes, reviews, and reactivation lists become a weekly owner execution loop.",
        advantages=(
            "Local customer memory — software vendors own workflow fields; the operator owns trust, reviews, and context.",
            "Dormant customer base — competitors chase new leads while old-customer reactivation is sitting unused.",
            "Owner speed — regional operators can change dispatch/follow-up cadence faster than franchises.",
        ),
        comparable_company="ServiceTitan, Inc.",
        comparable_year_start=2018,
        comparable_year_end=2025,
        comparable_revenue_start_m=250,
        comparable_revenue_end_m=800,
        comparable_segment_growth_m=500,
        threats=(
            ("ServiceTitan", "Tier 1", "6-12", "System-of-record footprint can bundle owner intelligence into field ops", 0.55),
            ("Housecall Pro", "Tier 2", "12-24", "SMB distribution can package reactivation and reviews", 0.45),
            ("Jobber", "Tier 3", "24-36", "Scheduling/payment workflow can become default revenue graph", 0.40),
        ),
        disqualifiers=(
            "The owner wants lead volume but refuses response-time and follow-up discipline.",
            "Dispatch, sales, and reviews stay in separate tools with no one accountable.",
            "Leadership wants a chatbot while quote-to-cash leakage remains unmeasured.",
        ),
        sources=(
            "Google AI Max for Search campaigns May 2025 · SW 0.50",
            "ServiceTitan public company filings and investor materials · SW 0.55",
        ),
    ),
}


GENERIC_PLAN = SEGMENTS["rig-service-operators"]


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


def host_from_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"^https?://", "", text, flags=re.I).split("/")[0]
    return text.lower().removeprefix("www.").strip()


def display_from_domain(domain: str) -> str:
    root = domain.split(".")[0].replace("-", " ").replace("_", " ").strip()
    words = [word for word in root.split() if word]
    return " ".join(word.upper() if len(word) <= 3 else word.title() for word in words) or "Company"


GENERIC_COMPANY_RE = re.compile(
    r"\b("
    r"best|jobs?|hiring|careers?|guide|software|positions?|report|what is|how to|"
    r"services?|commercial hvac|dental services?|contractor|dispatcher|coordinator|"
    r"location|our team|free emergency|franchise application"
    r")\b",
    re.I,
)
BANNED_PUBLIC_TEXT_RE = re.compile(r"\bworld-class\b", re.I)


def is_generic_company_name(name: str) -> bool:
    clean = re.sub(r"\s+", " ", str(name or "")).strip()
    if len(clean) < 3:
        return True
    return bool(GENERIC_COMPANY_RE.search(clean))


def public_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = BANNED_PUBLIC_TEXT_RE.sub("enterprise-grade", text)
    return text


def segment_from_raw(raw_segment: str, label: str = "") -> str:
    text = f"{raw_segment} {label}".lower()
    if "law" in text or "legal" in text:
        return "rig-law-growth-firms"
    if "cpa" in text or "account" in text or "tax" in text:
        return "rig-cpa-advisory"
    if "medspa" in text or "aesthetic" in text or "spa" in text:
        return "rig-medspa-aesthetics"
    if "ortho" in text or "health" in text or "dental" in text or "patient" in text:
        return "rig-healthcare-orthopedics"
    if "pe" in text or "private equity" in text or "portfolio" in text:
        return "rig-pe-portfolio-ops"
    if "manufact" in text or "industrial" in text:
        return "rig-midmarket-manufacturing"
    return "rig-service-operators"


def load_company_enrichment(path: Path) -> dict[str, dict[str, Any]]:
    enrichment: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return enrichment
    for row in read_jsonl(path):
        domain = host_from_url(row.get("domain") or row.get("primary_domain") or row.get("website_url"))
        if domain:
            enrichment[domain] = row
    return enrichment


def apply_company_enrichment(row: dict[str, Any], enrichment_by_domain: dict[str, dict[str, Any]]) -> dict[str, Any]:
    domain = (
        host_from_url(row.get("organization_domain"))
        or host_from_url(row.get("organization_website"))
        or host_from_url(row.get("website_url"))
        or host_from_url(row.get("domain"))
    )
    fact = enrichment_by_domain.get(domain)
    if not fact:
        return row
    patched = dict(row)
    employee_count = fact.get("employee_count") or fact.get("estimated_num_employees")
    if employee_count not in (None, "") and parse_int(employee_count, 0) >= MIN_EMPLOYEES:
        patched["organization_employee_count"] = parse_int(employee_count, 0)
    revenue = fact.get("revenue_usd_m") or fact.get("annual_revenue")
    if revenue not in (None, "") and not patched.get("organization_revenue"):
        patched["organization_revenue"] = revenue
    patched["_company_enrichment_sources"] = fact.get("sources") or fact.get("evidence_sources") or []
    patched["_company_enrichment_domain"] = domain
    return patched


def normalize_source_row(row: dict[str, Any], source_path: Path, index: int, enrichment_by_domain: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Normalize Apollo/Phronema variants into the internal prospect row shape."""
    row = apply_company_enrichment(row, enrichment_by_domain)
    if not has_min_employee_count(row):
        return None
    normalized = dict(row)
    source_name = source_path.name
    domain = (
        host_from_url(row.get("organization_domain"))
        or host_from_url(row.get("organization_website"))
        or host_from_url(row.get("website_url"))
        or host_from_url(row.get("domain"))
    )
    website = (
        str(row.get("website_url") or "").strip()
        or str(row.get("organization_website") or "").strip()
        or (f"https://{domain}" if domain else "")
    )
    if not website:
        return None
    company = str(
        row.get("company")
        or row.get("organization_name")
        or row.get("company_name")
        or row.get("account_name")
        or ""
    ).strip()
    if (not company or is_generic_company_name(company)) and domain:
        company = display_from_domain(domain)
    if not company:
        return None
    if "organization_name" in row and row.get("name") and not normalized.get("contact_name"):
        normalized["contact_name"] = row.get("name")
    if not normalized.get("company"):
        normalized["company"] = company
    normalized["company"] = company
    if domain and not normalized.get("organization_domain"):
        normalized["organization_domain"] = domain
    if website and not normalized.get("website_url"):
        normalized["website_url"] = normalize_url(website)
    raw_segment = str(row.get("segment") or "")
    normalized["segment"] = segment_from_raw(raw_segment, str(row.get("segment_label") or row.get("organization_industry") or ""))
    normalized["segment_label"] = row.get("segment_label") or row.get("organization_industry") or normalized["segment"]
    normalized["prospect_id"] = str(row.get("prospect_id") or row.get("organization_id") or row.get("contact_id") or f"{source_name}-{index}")
    normalized["_builder_key"] = f"{source_name}:{index}:{normalized['prospect_id']}"
    normalized["_source_name"] = source_name
    normalized["_source_path"] = str(source_path)
    return normalized


def prospect_quality_score(row: dict[str, Any]) -> float:
    score = 0.0
    if row.get("website_url") or row.get("organization_domain"):
        score += 10
    if row.get("contact_name") or row.get("name"):
        score += 3
    if row.get("email"):
        score += 2
    if row.get("phone_numbers") or row.get("organization_phone"):
        score += 2
    if row.get("linkedin_url"):
        score += 1.5
    if row.get("organization_employee_count"):
        score += 1
    if row.get("organization_revenue"):
        score += 1
    try:
        score += float(row.get("fit_score") or 0)
    except (TypeError, ValueError):
        pass
    if "rig-prospects-private" in str(row.get("_source_name") or ""):
        score += 3
    if "apollo-contacts-wide" in str(row.get("_source_name") or ""):
        score += 2
    if "prospect-database" in str(row.get("_source_name") or ""):
        score -= 1
    return score


def dedupe_key(row: dict[str, Any]) -> str:
    domain = host_from_url(row.get("organization_domain") or row.get("website_url"))
    if domain:
        return f"domain:{domain}"
    company = re.sub(r"[^a-z0-9]+", " ", str(row.get("company") or "").lower()).strip()
    state = str(row.get("state") or "").lower().strip()
    return f"company:{company}:{state}"


def load_candidate_prospects(primary: Path, extra_paths: list[Path], enrichment_by_domain: dict[str, dict[str, Any]], limit: int = 0) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for path in [primary, *extra_paths]:
        rows = read_jsonl(path)
        source_counts[path.name] = len(rows)
        for idx, row in enumerate(rows, 1):
            normalized = normalize_source_row(row, path, idx, enrichment_by_domain)
            if normalized:
                candidates.append(normalized)
    best_by_key: dict[str, dict[str, Any]] = {}
    for row in candidates:
        key = dedupe_key(row)
        current = best_by_key.get(key)
        if current is None or prospect_quality_score(row) > prospect_quality_score(current):
            best_by_key[key] = row
    deduped = sorted(
        best_by_key.values(),
        key=lambda row: (
            -prospect_quality_score(row),
            str(row.get("segment") or ""),
            str(row.get("company") or "").lower(),
        ),
    )
    if limit:
        deduped = deduped[:limit]
    stats = {
        "source_counts": source_counts,
        "candidate_rows": len(candidates),
        "deduped_rows": len(deduped),
        "duplicate_rows_removed": len(candidates) - len(best_by_key),
        "min_employee_floor": MIN_EMPLOYEES,
        "company_enrichment_domains": len(enrichment_by_domain),
    }
    return deduped, stats


def slugify(value: str, fallback: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return text[:72] or fallback


def stable_int(seed: str, low: int, high: int) -> int:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    span = high - low + 1
    return low + (int(digest[:8], 16) % span)


def company_short(name: str) -> str:
    clean = re.sub(r"\b(inc|llc|ltd|corp|corporation|company|co|pllc|pc|lp|llp)\b\.?", "", name, flags=re.I)
    words = [w for w in re.split(r"[^A-Za-z0-9]+", clean) if w]
    if not words:
        return name[:12] or "Company"
    if len(words) >= 2 and re.fullmatch(r"[A-Z0-9]{2,5}", words[0]):
        return words[0]
    if len(words) >= 3:
        acronym = "".join(w[0] for w in words[:4]).upper()
        if 2 <= len(acronym) <= 5:
            return acronym
    return " ".join(words[:2])[:18]


def parse_int(value: Any, default: int) -> int:
    try:
        if value in (None, ""):
            return default
        return max(1, int(float(str(value).replace(",", ""))))
    except (TypeError, ValueError):
        return default


def has_min_employee_count(row: dict[str, Any]) -> bool:
    raw = row.get("organization_employee_count")
    if raw in (None, ""):
        return False
    return parse_int(raw, 0) >= MIN_EMPLOYEES


def revenue_estimate_m(row: dict[str, Any], segment: str, employees: int) -> float:
    raw = row.get("organization_revenue")
    try:
        if raw not in (None, ""):
            value = float(str(raw).replace("$", "").replace(",", ""))
            return round(value / 1_000_000 if value > 10_000 else value, 1)
    except ValueError:
        pass
    rev_per_employee = {
        "rig-cpa-advisory": 0.21,
        "rig-law-growth-firms": 0.24,
        "rig-medspa-aesthetics": 0.18,
        "rig-pe-portfolio-ops": 0.75,
        "rig-midmarket-manufacturing": 0.23,
        "rig-service-operators": 0.16,
        "rig-healthcare-orthopedics": 0.31,
    }.get(segment, 0.18)
    return round(max(0.05, employees * rev_per_employee), 1)


def headquarters(row: dict[str, Any]) -> str:
    city = str(row.get("city") or "").strip()
    state = str(row.get("state") or "").strip()
    if city and state:
        return f"{city}, {state}"
    return city or state or "United States"


def normalize_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if not re.match(r"^https?://", text, re.I):
        text = f"https://{text}"
    return text


def cloned_site_url(slug: str) -> str:
    return f"https://{slug}-forge.vercel.app"


def fetch_site(url: str) -> dict[str, Any]:
    if not url:
        return {"ok": False, "error": "missing_url"}
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RIG-Strategy-Studio-A1/1.0 (+public website capability extraction)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=SITE_TIMEOUT_SECONDS, context=ctx) as response:
            final_url = response.geturl()
            raw = response.read(350_000)
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, ValueError) as exc:
        if url.startswith("https://"):
            try:
                return fetch_site("http://" + url.removeprefix("https://"))
            except RecursionError:
                pass
        return {"ok": False, "error": type(exc).__name__, "url": url}
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    headings = []
    for pattern in [
        r"<h[1-3][^>]*>(.*?)</h[1-3]>",
        r"<title[^>]*>(.*?)</title>",
        r"<a[^>]*>(.{3,80}?)</a>",
    ]:
        for match in re.findall(pattern, text, flags=re.I | re.S):
            label = html.unescape(re.sub(r"<[^>]+>", " ", match))
            label = re.sub(r"\s+", " ", label).strip(" -|•\t\r\n")
            if 3 <= len(label) <= 70:
                headings.append(label)
    colors = [m.group(0).upper() for m in re.finditer(r"#[0-9A-Fa-f]{6}\b", raw[:250_000].decode("utf-8", errors="ignore"))]
    return {"ok": True, "url": final_url, "headings": headings[:80], "colors": colors[:80]}


def filter_capabilities(headings: list[str], fallback: tuple[str, str, str]) -> list[str]:
    blocked = {
        "home", "about", "contact", "careers", "login", "privacy", "terms", "blog", "news",
        "services", "products", "solutions", "learn more", "read more", "get started",
        "how it works", "news & announcements", "frequently asked questions", "request a quote",
        "view all", "read article", "previous", "next",
    }
    selected = []
    for heading in headings:
        clean = re.sub(r"\s+", " ", heading).strip()
        low = clean.lower()
        if low in blocked:
            continue
        if re.search(r"\d{3}[-.\s)]*\d{3}[-.\s]*\d{4}", clean):
            continue
        if any(token in low for token in ["cookie", "privacy", "copyright", "subscribe", "menu"]):
            continue
        if any(token in low for token in ["news", "announcement", "blog", "career", "phone", "email"]):
            continue
        if BANNED_PUBLIC_TEXT_RE.search(clean):
            continue
        if len(clean.split()) > 6:
            continue
        if clean not in selected:
            selected.append(clean)
        if len(selected) >= 5:
            break
    for item in fallback:
        if item not in selected:
            selected.append(item)
        if len(selected) >= 3:
            break
    return selected[:10]


def pick_colors(colors: list[str]) -> tuple[str, str]:
    def is_useful(color: str) -> bool:
        c = color.lstrip("#")
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        if max(r, g, b) > 242 or max(r, g, b) < 25:
            return False
        if max(abs(r - g), abs(g - b), abs(r - b)) < 12:
            return False
        return True

    useful = []
    for color in colors:
        if is_useful(color) and color not in useful:
            useful.append(color)
    primary = useful[0] if useful else "#1A56DB"
    secondary = useful[1] if len(useful) > 1 else "#0F172A"
    return primary, secondary


def term_from_company(short: str, segment: str) -> str:
    nouns = {
        "rig-cpa-advisory": "Ledger",
        "rig-law-growth-firms": "Docket",
        "rig-medspa-aesthetics": "Contour",
        "rig-pe-portfolio-ops": "Vault",
        "rig-midmarket-manufacturing": "Forge",
        "rig-service-operators": "Signal",
        "rig-healthcare-orthopedics": "Pathway",
    }
    root = re.sub(r"[^A-Za-z0-9]", "", short)[:10] or "RIG"
    return f"{root} {nouns.get(segment, 'Signal')}"


def engine_rows(capabilities: list[str], row: dict[str, Any], plan: SegmentPlan, revenue_m: float) -> list[dict[str, Any]]:
    caps = (capabilities + list(plan.capabilities))[:3]
    while len(caps) < 3:
        caps.append(plan.capabilities[len(caps) % 3])
    targets = [max(2.0, revenue_m * 0.18), max(1.5, revenue_m * 0.11), max(1.0, revenue_m * 0.07)]
    types = ["data", "capability", "adoption"]
    sigmas = ["+5σ", "+5σ", "+4σ"]
    return [
        {
            "name": cap,
            "sigma_label": sigmas[i],
            "flywheel_type": types[i],
            "flywheel_loop": f"{cap} signal → scored exception → owner action → revenue memory",
            "target_revenue_m": round(targets[i], 1),
        }
        for i, cap in enumerate(caps[:3])
    ]


def evidence_sources(row: dict[str, Any], market: dict[str, Any], plan: SegmentPlan, site: dict[str, Any]) -> list[str]:
    sources = [
        f"Phronema RIG prospect export {TODAY} · SW 0.60",
        f"Phronema market-intel baseline {TODAY} · SW 0.50",
    ]
    if row.get("organization_employee_count"):
        sources.append(f"Apollo employee-count signal {TODAY} · SW 0.50")
    if row.get("organization_revenue"):
        sources.append(f"Apollo annual-revenue signal {TODAY} · SW 0.55")
    for source in row.get("_company_enrichment_sources") or []:
        if source and source not in sources:
            sources.append(str(source))
    source_name = str(row.get("_source_name") or "")
    if "apollo-contacts" in source_name:
        sources.append(f"Apollo contact enrichment export {TODAY} · SW 0.45")
    elif "prospect-database" in source_name:
        sources.append(f"Phronema public prospect database {TODAY} · SW 0.40")
    if site.get("ok"):
        sources.append(f"Company website public capture {TODAY} · SW 0.45")
    elif row.get("website_url"):
        sources.append(f"Company website/domain observed in Apollo {TODAY} · SW 0.35")
    if row.get("linkedin_url"):
        sources.append(f"LinkedIn company/contact URL observed in Apollo {TODAY} · SW 0.35")
    sources.extend(plan.sources)
    return sources[:8]


def build_record(row: dict[str, Any], market: dict[str, Any], site: dict[str, Any], slug: str) -> dict[str, Any]:
    segment = str(row.get("segment") or market.get("segment") or "")
    plan = SEGMENTS.get(segment, GENERIC_PLAN)
    employees = parse_int(row.get("organization_employee_count"), 11)
    revenue_m = revenue_estimate_m(row, segment, employees)
    short = company_short(str(row.get("company") or "Company"))
    years = stable_int(str(row.get("company") or slug), 7, 42)
    caps = filter_capabilities(site.get("headings") or [], plan.capabilities)
    primary, secondary = pick_colors(site.get("colors") or [])
    term = term_from_company(short, segment)
    source_list = evidence_sources(row, market, plan, site)
    confidence = "H" if len(source_list) >= 5 and site.get("ok") and row.get("linkedin_url") else "M"
    contact_name = str(row.get("contact_name") or row.get("first_name") or short)
    contact_role = public_text(row.get("title") or row.get("persona") or "Owner / Operator")
    return {
        "prospect_id": slug,
        "company_name": str(row.get("company") or short),
        "company_short": short,
        "employees": employees,
        "revenue_usd_m": revenue_m,
        "years_in_business": years,
        "headquarters": headquarters(row),
        "industry": str(market.get("market") or plan.industry),
        "industry_short": plan.industry_short,
        "wound_months": plan.wound_months,
        "wound_channel": plan.wound_channel,
        "wound_trigger": plan.wound_trigger,
        "capability_count": len(caps),
        "capability_names": caps,
        "capability_gap": plan.gap,
        "mechanism_name": f"{term} × {plan.loop_name}",
        "mechanism_description": plan.mechanism_description,
        "advantages": list(plan.advantages),
        "comparable_company": plan.comparable_company,
        "comparable_year_start": plan.comparable_year_start,
        "comparable_year_end": plan.comparable_year_end,
        "comparable_revenue_start_m": plan.comparable_revenue_start_m,
        "comparable_revenue_end_m": plan.comparable_revenue_end_m,
        "comparable_segment_growth_m": plan.comparable_segment_growth_m,
        "engines": engine_rows(caps, row, plan, revenue_m),
        "threats": [
            {"name": name, "tier": tier, "horizon_months": horizon, "key_fact": fact, "source_weight": sw}
            for name, tier, horizon, fact, sw in plan.threats
        ],
        "disqualifiers": list(plan.disqualifiers),
        "cloned_site_url": cloned_site_url(slug),
        "primary_color": primary,
        "secondary_color": secondary,
        "contact_name": contact_name,
        "contact_role": contact_role,
        "evidence_sources": source_list,
        "confidence": confidence,
    }


def write_prospect_csv(path: Path, rows: list[dict[str, Any]], slugs: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = path.with_name("prospect_list.sample.csv")
    if path.exists() and not sample.exists():
        sample.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    fields = ["prospect_id", "company_name", "website", "industry_hint", "linkedin_url", "cloned_site_url"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            slug = slugs[row["_builder_key"]]
            writer.writerow({
                "prospect_id": slug,
                "company_name": row.get("company"),
                "website": normalize_url(row.get("website_url") or row.get("organization_domain")),
                "industry_hint": row.get("segment_label") or row.get("segment"),
                "linkedin_url": row.get("linkedin_url") or "",
                "cloned_site_url": cloned_site_url(slug),
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 2000 Strategy Studio TeaserInput records from RIG prospect exports.")
    parser.add_argument("--prospects", type=Path, default=DEFAULT_PROSPECTS)
    parser.add_argument("--extra-prospects", type=Path, nargs="*", default=list(DEFAULT_EXTRA_PROSPECTS))
    parser.add_argument("--market-intel", type=Path, default=DEFAULT_MARKET)
    parser.add_argument("--output", type=Path, default=ROOT / "prospects_2000.jsonl")
    parser.add_argument("--failed", type=Path, default=ROOT / "prospects_failed.jsonl")
    parser.add_argument("--prospect-csv", type=Path, default=ROOT / "inputs/prospect_list.csv")
    parser.add_argument("--site-cache", type=Path, default=ROOT / "out/teasers_2000/_site_cache.jsonl")
    parser.add_argument("--ledger", type=Path, default=ROOT / "out/teasers_2000/_a1_research_ledger.jsonl")
    parser.add_argument("--company-enrichment", type=Path, default=DEFAULT_COMPANY_ENRICHMENT)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--skip-site-fetch", action="store_true")
    args = parser.parse_args()

    started = time.time()
    enrichment_by_domain = load_company_enrichment(args.company_enrichment)
    prospects, prospect_stats = load_candidate_prospects(args.prospects, args.extra_prospects, enrichment_by_domain, args.limit)
    market_rows = read_jsonl(args.market_intel)
    market_by_id = {str(row.get("prospect_id")): row for row in market_rows}

    seen: dict[str, int] = {}
    slugs: dict[str, str] = {}
    for idx, row in enumerate(prospects, 1):
        base = slugify(str(row.get("company") or row.get("prospect_id") or f"prospect-{idx}"), f"prospect-{idx}")
        count = seen.get(base, 0) + 1
        seen[base] = count
        slugs[str(row.get("_builder_key"))] = base if count == 1 else f"{base}-{count}"

    write_prospect_csv(args.prospect_csv, prospects, slugs)

    sites: dict[str, dict[str, Any]] = {}
    if not args.skip_site_fetch:
        urls = {slugs[str(row.get("_builder_key"))]: normalize_url(row.get("website_url") or row.get("organization_domain")) for row in prospects}
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(fetch_site, url): slug for slug, url in urls.items()}
            for fut in as_completed(futures):
                slug = futures[fut]
                try:
                    sites[slug] = fut.result()
                except Exception as exc:  # pragma: no cover
                    sites[slug] = {"ok": False, "error": type(exc).__name__}
    args.site_cache.parent.mkdir(parents=True, exist_ok=True)
    args.site_cache.write_text("".join(json.dumps({"prospect_id": k, **v}, sort_keys=True) + "\n" for k, v in sites.items()), encoding="utf-8")

    args.output.unlink(missing_ok=True)
    args.failed.unlink(missing_ok=True)
    args.failed.touch()
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.unlink(missing_ok=True)

    ok = failed = 0
    confidence_counts: dict[str, int] = {"H": 0, "M": 0, "L": 0}
    for row in prospects:
        prospect_key = str(row.get("_builder_key"))
        source_prospect_id = str(row.get("prospect_id"))
        slug = slugs[prospect_key]
        market = market_by_id.get(source_prospect_id, {})
        site = sites.get(slug, {"ok": False, "error": "site_fetch_skipped" if args.skip_site_fetch else "not_fetched"})
        last_step = "build_record"
        try:
            record = build_record(row, market, site, slug)
            last_step = "validation"
            validated = TeaserInput.model_validate(record)
            with args.output.open("a", encoding="utf-8") as file:
                file.write(validated.model_dump_json() + "\n")
            with args.ledger.open("a", encoding="utf-8") as file:
                file.write(json.dumps({
                    "prospect_id": slug,
                    "company": row.get("company"),
                    "source_prospect_id": source_prospect_id,
                    "source_path": row.get("_source_path"),
                    "site_ok": site.get("ok"),
                    "sources": validated.evidence_sources,
                    "generated_at": now_iso(),
                }, sort_keys=True) + "\n")
            ok += 1
            confidence_counts[validated.confidence] += 1
        except Exception as exc:
            failed += 1
            with args.failed.open("a", encoding="utf-8") as file:
                file.write(json.dumps({
                    "prospect_id": slug,
                    "error": str(exc),
                    "last_step": last_step,
                    "record": locals().get("record", {}),
                }, sort_keys=True) + "\n")

    report = {
        "ok": ok,
        "failed": failed,
        "total": len(prospects),
        "confidence": confidence_counts,
        "output": str(args.output),
        "failed_path": str(args.failed),
        "prospect_csv": str(args.prospect_csv),
        "site_cache": str(args.site_cache),
        "ledger": str(args.ledger),
        "elapsed_seconds": round(time.time() - started, 2),
        "generated_at": now_iso(),
        "prospect_stats": prospect_stats,
    }
    (ROOT / "out/teasers_2000/_input_build_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
