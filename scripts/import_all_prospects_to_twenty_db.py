#!/usr/bin/env python3
"""Bring all Strategy Studio prospects into the local Twenty CRM database.

This is a local-only deterministic import. It writes companies, contacts,
opportunities, tasks, and full strategy notes into the local Dockerized Twenty
Postgres workspace. It does not send emails, sync calendars, upload ad
audiences, call Apollo/Clay, or expose any data publicly.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from sync_strategy_research_to_twenty import build_note_markdown


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "all_1783"
IMPORT_DIR = ROOT / "out/twenty-crm/imports" / SCOPE
PROSPECTS_JSONL = ROOT / "prospects_2000.jsonl"
PROOF_PATH = IMPORT_DIR / "twenty_db_import_proof.json"
DOCKER_DB = "twenty-db-1"
DB_USER = "postgres"
DB_NAME = "default"
WORKSPACE_SCHEMA = "workspace_9n9szi9g3ok7r13ocz40gbvhd"
ARTIFACT_BASE_URL = "http://localhost:8096"
CREATED_BY = "RIG Strategy Studio"


@dataclass
class StagePaths:
    root: Path
    companies: Path
    people: Path
    opportunities: Path
    notes: Path
    tasks: Path


def clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return " ".join(str(value).strip().split())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_jsonl_index(path: Path) -> dict[str, dict]:
    return {
        row["prospect_id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def split_name(full_name: str) -> tuple[str, str]:
    parts = clean(full_name).split()
    if not parts:
        return "Unknown", ""
    return parts[0], " ".join(parts[1:])


def parse_hq(value: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in clean(value).split(",") if part.strip()]
    city = parts[0] if parts else ""
    state = parts[1] if len(parts) > 1 else ""
    return city, state, "United States"


def digits(value: str) -> str:
    return re.sub(r"[^\d]", "", clean(value))


def money_micros_from_amount(value: str) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return str(int(float(text.replace(",", "")) * 1_000_000))
    except ValueError:
        return ""


def revenue_micros_from_millions(value: str) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return str(int(float(text.replace(",", "")) * 1_000_000 * 1_000_000))
    except ValueError:
        return ""


def close_date(days: int = 45) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
            count += 1
    return count


def build_stage_files(stage_root: Path) -> tuple[StagePaths, dict[str, int]]:
    stage = StagePaths(
        root=stage_root,
        companies=stage_root / "companies.csv",
        people=stage_root / "people.csv",
        opportunities=stage_root / "opportunities.csv",
        notes=stage_root / "notes.csv",
        tasks=stage_root / "tasks.csv",
    )
    companies = read_csv(IMPORT_DIR / "twenty_companies.csv")
    people = read_csv(IMPORT_DIR / "twenty_people.csv")
    opportunities = read_csv(IMPORT_DIR / "twenty_opportunities.csv")
    tasks = read_csv(IMPORT_DIR / "twenty_tasks.csv")
    prospects = read_jsonl_index(PROSPECTS_JSONL)

    company_rows = []
    for row in companies:
        city, state, country = parse_hq(row.get("HQ", ""))
        company_rows.append(
            {
                "prospect_id": clean(row.get("Prospect ID")),
                "name": clean(row.get("Name")),
                "cloned_url": clean(row.get("Cloned Proposal URL")) or f"https://local.rig.invalid/prospect/{clean(row.get('Prospect ID'))}",
                "city": city,
                "state": state,
                "country": country,
                "employees": clean(row.get("Employees")),
                "revenue_micros": revenue_micros_from_millions(row.get("Revenue USD M", "")),
                "ideal_customer_profile": "true" if clean(row.get("Priority Tier")).upper() in {"A", "B"} else "false",
            }
        )

    people_rows = []
    for row in people:
        first, last = split_name(row.get("Name", ""))
        phone_digits = digits(row.get("Phone", ""))
        people_rows.append(
            {
                "prospect_id": clean(row.get("Prospect ID")),
                "company_name": clean(row.get("Company Name")),
                "first_name": first,
                "last_name": last,
                "email": clean(row.get("Email")),
                "job_title": clean(row.get("Job Title")),
                "phone": phone_digits,
                "linkedin_url": clean(row.get("LinkedIn URL")),
            }
        )

    opportunity_rows = []
    for row in opportunities:
        opportunity_rows.append(
            {
                "prospect_id": clean(row.get("Prospect ID")),
                "company_name": clean(row.get("Company Name")),
                "name": clean(row.get("Name")),
                "amount_micros": money_micros_from_amount(row.get("Amount", "")),
                "close_date": close_date(45),
            }
        )

    company_by_id = {clean(row.get("Prospect ID")): row for row in companies}
    note_rows = []
    for prospect_id, row in company_by_id.items():
        note_rows.append(
            {
                "prospect_id": prospect_id,
                "company_name": clean(row.get("Name")),
                "opportunity_name": clean(f"{row.get('Name')} - {row.get('Mechanism')}"),
                "title": f"Strategy + Research Packet: {clean(row.get('Name'))}",
                "body_markdown": build_note_markdown(row, prospects.get(prospect_id), ARTIFACT_BASE_URL),
            }
        )

    task_rows = []
    for row in tasks:
        task_rows.append(
            {
                "prospect_id": clean(row.get("Prospect ID")),
                "company_name": clean(row.get("Company Name")),
                "opportunity_name": clean(f"{row.get('Company Name')} - {row.get('Mechanism')}"),
                "title": clean(row.get("Title")),
                "due_at": f"{clean(row.get('Due Date'))}T12:00:00+00:00" if clean(row.get("Due Date")) else close_date(5),
                "body_markdown": "\n".join(
                    [
                        f"Company: {clean(row.get('Company Name'))}",
                        f"Prospect ID: {clean(row.get('Prospect ID'))}",
                        f"Priority: {clean(row.get('Priority Tier'))}",
                        f"Mechanism: {clean(row.get('Mechanism'))}",
                        f"Notes: {clean(row.get('Notes'))}",
                        f"Strategy: {clean(row.get('Strategy Path'))}",
                        "",
                        "Human gate: no outbound sends, ad uploads, calendar sync, email sync, or external CRM writes without Mike approval.",
                    ]
                ),
            }
        )

    counts = {
        "companies": write_csv(
            stage.companies,
            company_rows,
            ["prospect_id", "name", "cloned_url", "city", "state", "country", "employees", "revenue_micros", "ideal_customer_profile"],
        ),
        "people": write_csv(
            stage.people,
            people_rows,
            ["prospect_id", "company_name", "first_name", "last_name", "email", "job_title", "phone", "linkedin_url"],
        ),
        "opportunities": write_csv(
            stage.opportunities,
            opportunity_rows,
            ["prospect_id", "company_name", "name", "amount_micros", "close_date"],
        ),
        "notes": write_csv(
            stage.notes,
            note_rows,
            ["prospect_id", "company_name", "opportunity_name", "title", "body_markdown"],
        ),
        "tasks": write_csv(
            stage.tasks,
            task_rows,
            ["prospect_id", "company_name", "opportunity_name", "title", "due_at", "body_markdown"],
        ),
    }
    return stage, counts


def run(cmd: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout


def psql(sql: str) -> str:
    return run(["docker", "exec", "-i", DOCKER_DB, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"], input_text=sql)


def psql_at(sql: str) -> list[str]:
    out = run(["docker", "exec", "-i", DOCKER_DB, "psql", "-U", DB_USER, "-d", DB_NAME, "-At", "-v", "ON_ERROR_STOP=1"], input_text=sql)
    return [line for line in out.splitlines() if line.strip()]


def copy_to_container(paths: StagePaths) -> dict[str, str]:
    remote_dir = f"/tmp/rig_gtm_import_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    run(["docker", "exec", DOCKER_DB, "mkdir", "-p", remote_dir])
    remote_paths = {}
    for name, path in {
        "companies": paths.companies,
        "people": paths.people,
        "opportunities": paths.opportunities,
        "notes": paths.notes,
        "tasks": paths.tasks,
    }.items():
        remote = f"{remote_dir}/{name}.csv"
        run(["docker", "cp", str(path), f"{DOCKER_DB}:{remote}"])
        remote_paths[name] = remote
    return remote_paths


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_counts() -> dict[str, int]:
    rows = psql_at(
        f"""
        select 'companies_total|' || count(*) from "{WORKSPACE_SCHEMA}".company where "deletedAt" is null;
        select 'prospect_companies|' || count(*) from "{WORKSPACE_SCHEMA}".company
          where "deletedAt" is null and "domainNamePrimaryLinkUrl" like 'https://%-forge.vercel.app';
        select 'people_total|' || count(*) from "{WORKSPACE_SCHEMA}".person where "deletedAt" is null;
        select 'opportunities_total|' || count(*) from "{WORKSPACE_SCHEMA}".opportunity where "deletedAt" is null;
        select 'prospect_opportunities|' || count(*) from "{WORKSPACE_SCHEMA}".opportunity
          where "deletedAt" is null and name like '% × %';
        select 'notes_total|' || count(*) from "{WORKSPACE_SCHEMA}".note where "deletedAt" is null;
        select 'strategy_notes|' || count(*) from "{WORKSPACE_SCHEMA}".note
          where "deletedAt" is null and title like 'Strategy + Research Packet:%';
        select 'tasks_total|' || count(*) from "{WORKSPACE_SCHEMA}".task where "deletedAt" is null;
        """
    )
    return {key: int(value) for key, value in (row.split("|", 1) for row in rows)}


def import_sql(remote_paths: dict[str, str]) -> str:
    return f"""
    begin;
    drop table if exists public.rig_gtm_stage_companies;
    drop table if exists public.rig_gtm_stage_people;
    drop table if exists public.rig_gtm_stage_opportunities;
    drop table if exists public.rig_gtm_stage_notes;
    drop table if exists public.rig_gtm_stage_tasks;

    create table public.rig_gtm_stage_companies (
      prospect_id text, name text, cloned_url text, city text, state text, country text,
      employees text, revenue_micros text, ideal_customer_profile text
    );
    create table public.rig_gtm_stage_people (
      prospect_id text, company_name text, first_name text, last_name text, email text,
      job_title text, phone text, linkedin_url text
    );
    create table public.rig_gtm_stage_opportunities (
      prospect_id text, company_name text, name text, amount_micros text, close_date text
    );
    create table public.rig_gtm_stage_notes (
      prospect_id text, company_name text, opportunity_name text, title text, body_markdown text
    );
    create table public.rig_gtm_stage_tasks (
      prospect_id text, company_name text, opportunity_name text, title text, due_at text, body_markdown text
    );
    commit;

    \\copy public.rig_gtm_stage_companies from '{remote_paths["companies"]}' with (format csv, header true)
    \\copy public.rig_gtm_stage_people from '{remote_paths["people"]}' with (format csv, header true)
    \\copy public.rig_gtm_stage_opportunities from '{remote_paths["opportunities"]}' with (format csv, header true)
    \\copy public.rig_gtm_stage_notes from '{remote_paths["notes"]}' with (format csv, header true)
    \\copy public.rig_gtm_stage_tasks from '{remote_paths["tasks"]}' with (format csv, header true)

    begin;

    insert into "{WORKSPACE_SCHEMA}".company (
      name, "domainNamePrimaryLinkLabel", "domainNamePrimaryLinkUrl", "domainNameSecondaryLinks",
      "addressAddressCity", "addressAddressState", "addressAddressCountry",
      employees, "annualRecurringRevenueAmountMicros", "annualRecurringRevenueCurrencyCode",
      "idealCustomerProfile", position, "createdByName", "updatedByName"
    )
    select
      s.name, 'Cloned proposal', s.cloned_url, '[]'::jsonb,
      s.city, s.state, coalesce(nullif(s.country, ''), 'United States'),
      nullif(s.employees, '')::double precision,
      nullif(s.revenue_micros, '')::numeric,
      case when nullif(s.revenue_micros, '') is null then null else 'USD' end,
      coalesce(nullif(s.ideal_customer_profile, '')::boolean, false),
      row_number() over (order by s.name)::double precision,
      '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_companies s
    where nullif(s.name, '') is not null
    on conflict ("domainNamePrimaryLinkUrl") do update set
      name = excluded.name,
      "domainNamePrimaryLinkLabel" = excluded."domainNamePrimaryLinkLabel",
      "addressAddressCity" = excluded."addressAddressCity",
      "addressAddressState" = excluded."addressAddressState",
      "addressAddressCountry" = excluded."addressAddressCountry",
      employees = excluded.employees,
      "annualRecurringRevenueAmountMicros" = excluded."annualRecurringRevenueAmountMicros",
      "annualRecurringRevenueCurrencyCode" = excluded."annualRecurringRevenueCurrencyCode",
      "idealCustomerProfile" = excluded."idealCustomerProfile",
      "updatedAt" = now(),
      "updatedByName" = '{CREATED_BY}';

    insert into "{WORKSPACE_SCHEMA}".person (
      "nameFirstName", "nameLastName", "emailsPrimaryEmail", "emailsAdditionalEmails",
      "linkedinLinkPrimaryLinkLabel", "linkedinLinkPrimaryLinkUrl", "linkedinLinkSecondaryLinks",
      "jobTitle", "phonesPrimaryPhoneNumber", "phonesPrimaryPhoneCountryCode",
      "phonesPrimaryPhoneCallingCode", "phonesAdditionalPhones", "companyId",
      position, "createdByName", "updatedByName"
    )
    select
      p.first_name,
      p.last_name,
      nullif(p.email, ''),
      '[]'::jsonb,
      case when nullif(p.linkedin_url, '') is null then null else 'LinkedIn' end,
      nullif(p.linkedin_url, ''),
      '[]'::jsonb,
      nullif(p.job_title, ''),
      nullif(p.phone, ''),
      case when nullif(p.phone, '') is null then null else 'US' end,
      case when nullif(p.phone, '') is null then null else '+1' end,
      '[]'::jsonb,
      c.id,
      row_number() over (order by p.company_name, p.first_name, p.last_name)::double precision,
      '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_people p
    join public.rig_gtm_stage_companies sc on sc.prospect_id = p.prospect_id
    join "{WORKSPACE_SCHEMA}".company c on c."domainNamePrimaryLinkUrl" = sc.cloned_url
    where nullif(p.first_name, '') is not null
      and not exists (
        select 1 from "{WORKSPACE_SCHEMA}".person existing
        where existing."deletedAt" is null
          and coalesce(lower(existing."nameFirstName"), '') = coalesce(lower(p.first_name), '')
          and coalesce(lower(existing."nameLastName"), '') = coalesce(lower(p.last_name), '')
          and existing."companyId" = c.id
      )
      and (
        nullif(p.email, '') is null
        or not exists (
          select 1 from "{WORKSPACE_SCHEMA}".person existing_email
          where existing_email."deletedAt" is null
            and lower(existing_email."emailsPrimaryEmail") = lower(p.email)
        )
      );

    insert into "{WORKSPACE_SCHEMA}".opportunity (
      name, "amountAmountMicros", "amountCurrencyCode", "closeDate", stage,
      position, "companyId", "pointOfContactId", "createdByName", "updatedByName"
    )
    select
      o.name,
      nullif(o.amount_micros, '')::numeric,
      case when nullif(o.amount_micros, '') is null then null else 'USD' end,
      nullif(o.close_date, '')::timestamptz,
      'SCREENING'::"{WORKSPACE_SCHEMA}".opportunity_stage_enum,
      row_number() over (order by o.name)::double precision,
      c.id,
      p.id,
      '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_opportunities o
    join public.rig_gtm_stage_companies sc on sc.prospect_id = o.prospect_id
    join "{WORKSPACE_SCHEMA}".company c on c."domainNamePrimaryLinkUrl" = sc.cloned_url
    left join "{WORKSPACE_SCHEMA}".person p on p."companyId" = c.id
      and p."deletedAt" is null
      and p.id = (
        select p2.id from "{WORKSPACE_SCHEMA}".person p2
        where p2."companyId" = c.id and p2."deletedAt" is null
        order by p2."createdAt" asc
        limit 1
      )
    where nullif(o.name, '') is not null
      and not exists (
        select 1 from "{WORKSPACE_SCHEMA}".opportunity existing
        where existing."deletedAt" is null and lower(existing.name) = lower(o.name)
      );

    update "{WORKSPACE_SCHEMA}".note n
    set "bodyV2Markdown" = s.body_markdown,
        "bodyV2Blocknote" = null,
        "updatedAt" = now(),
        "updatedByName" = '{CREATED_BY}'
    from public.rig_gtm_stage_notes s
    where n."deletedAt" is null and lower(n.title) = lower(s.title);

    insert into "{WORKSPACE_SCHEMA}".note (
      title, "bodyV2Markdown", position, "createdByName", "updatedByName"
    )
    select
      s.title,
      s.body_markdown,
      row_number() over (order by s.title)::double precision,
      '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_notes s
    where nullif(s.title, '') is not null
      and not exists (
        select 1 from "{WORKSPACE_SCHEMA}".note existing
        where existing."deletedAt" is null and lower(existing.title) = lower(s.title)
      );

    insert into "{WORKSPACE_SCHEMA}"."noteTarget" (
      "noteId", "targetCompanyId", "createdByName", "updatedByName"
    )
    select n.id, c.id, '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_notes s
    join public.rig_gtm_stage_companies sc on sc.prospect_id = s.prospect_id
    join "{WORKSPACE_SCHEMA}".company c on c."domainNamePrimaryLinkUrl" = sc.cloned_url
    join "{WORKSPACE_SCHEMA}".note n on lower(n.title) = lower(s.title) and n."deletedAt" is null
    where not exists (
      select 1 from "{WORKSPACE_SCHEMA}"."noteTarget" nt
      where nt."deletedAt" is null and nt."noteId" = n.id and nt."targetCompanyId" = c.id
    );

    insert into "{WORKSPACE_SCHEMA}"."noteTarget" (
      "noteId", "targetOpportunityId", "createdByName", "updatedByName"
    )
    select n.id, o.id, '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_notes s
    join "{WORKSPACE_SCHEMA}".opportunity o on lower(o.name) = lower(s.opportunity_name) and o."deletedAt" is null
    join "{WORKSPACE_SCHEMA}".note n on lower(n.title) = lower(s.title) and n."deletedAt" is null
    where not exists (
      select 1 from "{WORKSPACE_SCHEMA}"."noteTarget" nt
      where nt."deletedAt" is null and nt."noteId" = n.id and nt."targetOpportunityId" = o.id
    );

    insert into "{WORKSPACE_SCHEMA}".task (
      title, "bodyV2Markdown", "dueAt", status, position, "createdByName", "updatedByName"
    )
    select
      t.title,
      t.body_markdown,
      nullif(t.due_at, '')::timestamptz,
      'TODO'::"{WORKSPACE_SCHEMA}".task_status_enum,
      row_number() over (order by t.title)::double precision,
      '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_tasks t
    where nullif(t.title, '') is not null
      and not exists (
        select 1 from "{WORKSPACE_SCHEMA}".task existing
        where existing."deletedAt" is null and lower(existing.title) = lower(t.title)
      );

    insert into "{WORKSPACE_SCHEMA}"."taskTarget" (
      "taskId", "targetCompanyId", "createdByName", "updatedByName"
    )
    select task.id, c.id, '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_tasks s
    join public.rig_gtm_stage_companies sc on sc.prospect_id = s.prospect_id
    join "{WORKSPACE_SCHEMA}".company c on c."domainNamePrimaryLinkUrl" = sc.cloned_url
    join "{WORKSPACE_SCHEMA}".task task on lower(task.title) = lower(s.title) and task."deletedAt" is null
    where not exists (
      select 1 from "{WORKSPACE_SCHEMA}"."taskTarget" tt
      where tt."deletedAt" is null and tt."taskId" = task.id and tt."targetCompanyId" = c.id
    );

    insert into "{WORKSPACE_SCHEMA}"."taskTarget" (
      "taskId", "targetOpportunityId", "createdByName", "updatedByName"
    )
    select task.id, o.id, '{CREATED_BY}', '{CREATED_BY}'
    from public.rig_gtm_stage_tasks s
    join "{WORKSPACE_SCHEMA}".opportunity o on lower(o.name) = lower(s.opportunity_name) and o."deletedAt" is null
    join "{WORKSPACE_SCHEMA}".task task on lower(task.title) = lower(s.title) and task."deletedAt" is null
    where not exists (
      select 1 from "{WORKSPACE_SCHEMA}"."taskTarget" tt
      where tt."deletedAt" is null and tt."taskId" = task.id and tt."targetOpportunityId" = o.id
    );

    commit;
    """


def main() -> int:
    required = [
        IMPORT_DIR / "twenty_companies.csv",
        IMPORT_DIR / "twenty_people.csv",
        IMPORT_DIR / "twenty_opportunities.csv",
        IMPORT_DIR / "twenty_tasks.csv",
        PROSPECTS_JSONL,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"ok": False, "missing": missing}, indent=2), file=sys.stderr)
        return 1

    before = snapshot_counts()
    with tempfile.TemporaryDirectory(prefix="rig_gtm_import_") as tmp:
        stage, stage_counts = build_stage_files(Path(tmp))
        remote_paths = copy_to_container(stage)
        psql(import_sql(remote_paths))
        hashes = {
            "companies": hash_file(stage.companies),
            "people": hash_file(stage.people),
            "opportunities": hash_file(stage.opportunities),
            "notes": hash_file(stage.notes),
            "tasks": hash_file(stage.tasks),
        }

    after = snapshot_counts()
    validation_rows = psql_at(
        f"""
        select 'missing_company_urls|' || count(*) from public.rig_gtm_stage_companies s
          where not exists (
            select 1 from "{WORKSPACE_SCHEMA}".company c
            where c."deletedAt" is null and c."domainNamePrimaryLinkUrl" = s.cloned_url
          );
        select 'missing_strategy_notes|' || count(*) from public.rig_gtm_stage_notes s
          where not exists (
            select 1 from "{WORKSPACE_SCHEMA}".note n
            where n."deletedAt" is null and lower(n.title) = lower(s.title)
          );
        select 'missing_opportunities|' || count(*) from public.rig_gtm_stage_opportunities s
          where not exists (
            select 1 from "{WORKSPACE_SCHEMA}".opportunity o
            where o."deletedAt" is null and lower(o.name) = lower(s.name)
          );
        """
    )
    validation = {key: int(value) for key, value in (row.split("|", 1) for row in validation_rows)}
    proof = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_for": "RIG and Mike Rodgers",
        "scope": SCOPE,
        "local_only": True,
        "external_side_effects": False,
        "human_gate": "Imported into local Twenty only. No outbound sends, email/calendar sync, ad upload, Apollo/Clay writeback, or public exposure occurred.",
        "stage_counts": stage_counts,
        "before": before,
        "after": after,
        "delta": {key: after.get(key, 0) - before.get(key, 0) for key in after},
        "validation": validation,
        "hashes": hashes,
        "workspace_schema": WORKSPACE_SCHEMA,
    }
    PROOF_PATH.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))
    return 0 if all(value == 0 for value in validation.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
