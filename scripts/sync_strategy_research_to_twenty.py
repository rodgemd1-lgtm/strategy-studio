#!/usr/bin/env python3
"""Sync Strategy Studio research artifacts into local Twenty CRM notes.

Twenty is the operating cockpit; Strategy Studio remains the source of
strategy/research/proof artifacts. This script links them by creating one
approval-gated note per prospect and attaching it to the matching company and
opportunity in the local Twenty instance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TWENTY_TOKEN_PATH = ROOT / "out/twenty-crm/.local-token.json"
IMPORT_ROOT = ROOT / "out/twenty-crm/imports"
DEFAULT_SCOPE = "denver_front_range_78"
DEFAULT_BASE_URL = "http://localhost:3020"
DEFAULT_ARTIFACT_BASE_URL = "http://localhost:8096"
MAX_INLINE_CHARS = 90_000


@dataclass
class SyncStats:
    created_notes: int = 0
    updated_notes: int = 0
    skipped_notes: int = 0
    linked_companies: int = 0
    linked_opportunities: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "created_notes": self.created_notes,
            "updated_notes": self.updated_notes,
            "skipped_notes": self.skipped_notes,
            "linked_companies": self.linked_companies,
            "linked_opportunities": self.linked_opportunities,
            "failed": self.failed,
        }


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
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1200]
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
            cursor = page_info.get("endCursor")
            if not page_info.get("hasNextPage") or not cursor:
                break
            if cursor in seen_cursors:
                raise RuntimeError(f"Twenty pagination cursor loop while listing {object_name}")
            seen_cursors.add(cursor)
            after = cursor
        return rows

    def create_note(self, title: str, markdown: str) -> dict[str, Any]:
        result = self.request("POST", "/rest/notes", {"title": title, "bodyV2": {"markdown": markdown}})
        return result.get("data", {}).get("createNote", {})

    def update_note(self, note_id: str, title: str, markdown: str) -> dict[str, Any]:
        result = self.request(
            "PATCH",
            f"/rest/notes/{note_id}",
            {"title": title, "bodyV2": {"markdown": markdown}},
        )
        return result.get("data", {}).get("updateNote", {})

    def create_note_target(
        self,
        note_id: str,
        *,
        company_id: str | None = None,
        opportunity_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"noteId": note_id}
        if company_id:
            payload["targetCompanyId"] = company_id
        if opportunity_id:
            payload["targetOpportunityId"] = opportunity_id
        result = self.request("POST", "/rest/noteTargets", payload)
        return result.get("data", {}).get("createNoteTarget", {})


def read_token(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    token = data.get("token")
    if not token:
        raise RuntimeError(f"No token found in {path}. Refresh the local Twenty token first.")
    return token


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_jsonl_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {row["prospect_id"]: row for row in (json.loads(line) for line in path.read_text().splitlines() if line.strip())}


def norm(value: object) -> str:
    return " ".join(str(value or "").lower().strip().split())


def clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_url(path: Path, artifact_base_url: str) -> str | None:
    try:
        rel = path.resolve().relative_to((ROOT / "out").resolve())
    except ValueError:
        return None
    return f"{artifact_base_url.rstrip('/')}/{urllib.parse.quote(str(rel).replace(chr(92), '/'))}"


def md_link(label: str, path: Path, artifact_base_url: str) -> str:
    url = artifact_url(path, artifact_base_url)
    if url:
        return f"- {label}: [open]({url}) | local `{path}`"
    return f"- {label}: `{path}`"


def artifact_paths(prospect_id: str) -> dict[str, Path]:
    teaser_dir = ROOT / "out/teasers_2000" / prospect_id
    strategy_dir = ROOT / "out/strategies_1783" / prospect_id
    gtm_dir = ROOT / "out/ai_gtm_20x" / prospect_id
    prompt_dir = ROOT / "out/regional_gtm/denver_front_range/prompts" / prospect_id
    return {
        "teaser_html": teaser_dir / "index.html",
        "teaser_md": teaser_dir / "teaser.md",
        "teaser_input": teaser_dir / "teaser_input.json",
        "strategy_md": strategy_dir / "strategy.md",
        "strategy_json": strategy_dir / "strategy.json",
        "bundle_strategy_md": teaser_dir / "strategy.md",
        "bundle_strategy_json": teaser_dir / "strategy.json",
        "gtm20x_md": gtm_dir / "gtm20x.md",
        "gtm20x_json": gtm_dir / "gtm20x.json",
        "bundle_gtm20x_md": teaser_dir / "gtm20x.md",
        "proof_packet": teaser_dir / "proof_packet.json",
        "css_prompt": prompt_dir / "css_design_prompt.md",
        "website_prompt": prompt_dir / "website_setup_prompt.md",
        "proposal_prompt": prompt_dir / "proposal_build_prompt.md",
    }


def compact_json_field(value: Any) -> str:
    if value in (None, "", []):
        return ""
    if isinstance(value, str):
        return clean(value)
    return clean(json.dumps(value, ensure_ascii=True))


def read_text(path: Path, *, max_chars: int = MAX_INLINE_CHARS) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED IN CRM NOTE: open the linked artifact for the full file.]"


def proof_summary(path: Path) -> str:
    if not path.exists():
        return "ProofPacket not found."
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "ProofPacket JSON could not be parsed. Open the linked file."
    packet = data.get("proof_packet", data)
    lines = []
    claim = packet.get("claim")
    if claim:
        lines.append(f"- Claim: {claim}")
    evidence = packet.get("evidence") or []
    if evidence:
        lines.append("- Evidence ledger:")
        for item in evidence[:10]:
            source = clean(item.get("source_uri") or item.get("source") or item)
            confidence = clean(item.get("confidence") or "")
            lines.append(f"  - {source}" + (f" ({confidence})" if confidence else ""))
    falsification = packet.get("falsification") or packet.get("falsification_packet") or data.get("falsification")
    if falsification:
        lines.append(f"- Falsification: {compact_json_field(falsification)}")
    return "\n".join(lines) if lines else "Open the linked ProofPacket for details."


def section(title: str, body: str) -> list[str]:
    if not body.strip():
        return [f"## {title}", "", "Missing or not generated yet.", ""]
    return [f"## {title}", "", body.strip(), ""]


def build_note_markdown(row: dict[str, str], prospect: dict[str, Any] | None, artifact_base_url: str) -> str:
    prospect_id = clean(row.get("Prospect ID"))
    paths = artifact_paths(prospect_id)
    company = clean(row.get("Name"))
    mechanism = clean(row.get("Mechanism"))
    wound = clean(row.get("Wound Channel"))
    trigger = clean(row.get("Wound Trigger"))
    score = clean(row.get("20x Score"))
    tier = clean(row.get("Priority Tier"))
    cloned = clean(row.get("Cloned Proposal URL"))
    evidence = compact_json_field((prospect or {}).get("evidence_sources") or row.get("Evidence Sources"))
    disqualifiers = compact_json_field((prospect or {}).get("disqualifiers"))

    artifact_lines = [md_link(label, path, artifact_base_url) for label, path in paths.items() if path.exists()]
    hash_lines = [
        f"- {label}: `{digest}`"
        for label, path in paths.items()
        if path.exists() and (digest := sha256(path))
    ]
    strategy_body = read_text(paths["strategy_md"]) or read_text(paths["bundle_strategy_md"])
    gtm_body = read_text(paths["gtm20x_md"]) or read_text(paths["bundle_gtm20x_md"])
    teaser_body = read_text(paths["teaser_md"])
    css_prompt = read_text(paths["css_prompt"], max_chars=30_000)
    website_prompt = read_text(paths["website_prompt"], max_chars=30_000)
    proposal_prompt = read_text(paths["proposal_prompt"], max_chars=30_000)

    lines = [
        f"# Strategy + Research Packet: {company}",
        "",
        "## Account Cockpit",
        f"- Prospect ID: `{prospect_id}`",
        f"- Priority: `{tier}`",
        f"- 20x score: `{score}`",
        f"- Mechanism: {mechanism}",
        f"- Wound channel: {wound}",
        f"- Wound trigger: {trigger}",
        f"- Cloned proposal: {cloned or 'UNKNOWN'}",
        "",
        "## Use This First",
        "- Read the Account Strategy Brief below before writing outreach.",
        "- Use the 20x AI GTM Strategy for channel plan, sequence, objections, and proof gates.",
        "- Open the teaser HTML link only when you need the rendered proposal page.",
        "- Human approval is required before outbound sends, ad uploads, public exposure, or external CRM writes.",
        "",
        "## Openable Artifacts",
        *artifact_lines,
        "",
        "## Evidence / Research",
        f"- Evidence sources: {evidence or 'See ProofPacket and Strategy JSON'}",
        f"- Disqualifiers: {disqualifiers or 'See generated strategy packet'}",
        proof_summary(paths["proof_packet"]),
        "",
        *section("Account Strategy Brief", strategy_body),
        *section("20x AI GTM Strategy", gtm_body),
        *section("Teaser / Email Copy", teaser_body),
        *section("CSS Design Prompt", css_prompt),
        *section("Website Setup Prompt", website_prompt),
        *section("Proposal Build Prompt", proposal_prompt),
        "## Gate",
        "- Human approval required before any outbound send, ad upload, public exposure, or external CRM write.",
        "- Use this note as the account cockpit: read strategy, inspect proof, verify buyer, then move the opportunity stage.",
        "",
        "## Artifact Hashes",
        *hash_lines,
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Strategy Studio artifacts into local Twenty notes.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--artifact-base-url", default=DEFAULT_ARTIFACT_BASE_URL)
    parser.add_argument("--token-path", type=Path, default=TWENTY_TOKEN_PATH)
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scope_dir = IMPORT_ROOT / args.scope
    companies_path = scope_dir / "twenty_companies.csv"
    if not companies_path.exists():
        raise SystemExit(f"Missing company import file: {companies_path}")

    client = TwentyClient(args.base_url, read_token(args.token_path))
    stats = SyncStats()
    failures: list[dict[str, str]] = []

    companies = {norm(item.get("name")): item.get("id") for item in client.list_objects("companies")}
    opportunities = {norm(item.get("name")): item.get("id") for item in client.list_objects("opportunities")}
    existing_notes = {norm(item.get("title")): item.get("id") for item in client.list_objects("notes")}
    prospects = read_jsonl_index(ROOT / "out/regional_gtm/denver_front_range/denver_front_range_clients.jsonl")

    for row in read_csv(companies_path):
        company_name = clean(row.get("Name"))
        prospect_id = clean(row.get("Prospect ID"))
        title = f"Strategy + Research Packet: {company_name}"
        title_key = norm(title)
        company_id = companies.get(norm(company_name))
        opportunity_id = None
        for opportunity_name, candidate_id in opportunities.items():
            if opportunity_name.startswith(norm(company_name)):
                opportunity_id = candidate_id
                break

        if not company_id:
            stats.failed += 1
            failures.append({"prospect_id": prospect_id, "company": company_name, "error": "company not found in Twenty"})
            continue

        if title_key in existing_notes:
            if not args.update_existing:
                stats.skipped_notes += 1
                continue
            markdown = build_note_markdown(row, prospects.get(prospect_id), args.artifact_base_url)
            if args.dry_run:
                stats.updated_notes += 1
                continue
            try:
                client.update_note(existing_notes[title_key], title, markdown)
                stats.updated_notes += 1
            except Exception as exc:  # noqa: BLE001
                stats.failed += 1
                failures.append({"prospect_id": prospect_id, "company": company_name, "error": str(exc)})
            continue

        markdown = build_note_markdown(row, prospects.get(prospect_id), args.artifact_base_url)
        if args.dry_run:
            stats.created_notes += 1
            if company_id:
                stats.linked_companies += 1
            if opportunity_id:
                stats.linked_opportunities += 1
            continue

        try:
            note = client.create_note(title, markdown)
            note_id = note.get("id")
            if not note_id:
                raise RuntimeError("note create returned no id")
            existing_notes[title_key] = note_id
            stats.created_notes += 1
            client.create_note_target(note_id, company_id=company_id)
            stats.linked_companies += 1
            if opportunity_id:
                client.create_note_target(note_id, opportunity_id=opportunity_id)
                stats.linked_opportunities += 1
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            failures.append({"prospect_id": prospect_id, "company": company_name, "error": str(exc)})

    proof = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_for": "RIG and Mike Rodgers",
        "scope": args.scope,
        "base_url": args.base_url,
        "artifact_base_url": args.artifact_base_url,
        "update_existing": args.update_existing,
        "dry_run": args.dry_run,
        "local_only": True,
        "external_side_effects": False,
        "stats": stats.as_dict(),
        "failures": failures,
        "human_gate": "Strategy/research artifacts were linked inside local Twenty only. No outbound sends, calendar sync, ads, or external CRM writes were performed.",
    }
    proof_path = scope_dir / "twenty_strategy_research_sync_proof.json"
    proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
