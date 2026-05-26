# RIG GTM CRM — All Prospects Import

**Updated:** 2026-05-26  
**Owner:** RIG / Mike Rodgers  
**System:** Strategy Studio -> local Twenty CRM -> RIG GTM operations  
**Scope:** all `prospects_2000.jsonl` records currently generated for RIG prospecting

## What Changed

Strategy Studio now has a deterministic local import path that brings the full RIG prospect universe into the local Twenty CRM workspace.

The latest verified import loaded:

| Object | Count |
| --- | ---: |
| Prospect companies | 1,783 |
| People / contact records | 1,783 |
| Opportunities | 1,783 |
| Strategy notes | 1,783 |
| GTM follow-up tasks | 8,915 |

The import is local-only. It does not send email, sync calendars, upload ad audiences, call Apollo or Clay, write back to external systems, or expose private data publicly.

## Source Artifacts

The import pulls from the generated Strategy Studio prospect bundle:

- `prospects_2000.jsonl`
- `out/twenty-crm/imports/all_1783/twenty_companies.csv`
- `out/twenty-crm/imports/all_1783/twenty_people.csv`
- `out/twenty-crm/imports/all_1783/twenty_opportunities.csv`
- `out/twenty-crm/imports/all_1783/twenty_tasks.csv`
- `out/strategies_1783/*/strategy.md`
- `out/ai_gtm_20x/*/gtm20x.md`
- `out/teasers_2000/*/index.html`

The `out/` directory is intentionally gitignored because it contains generated bulk data and client/prospect artifacts. Keep durable process documentation in `docs/` and regenerate output artifacts locally when needed.

## Import Script

Use:

```bash
cd /Users/mikerodgers/strategy-studio
python3 scripts/import_all_prospects_to_twenty_db.py
```

The script writes directly to the local Dockerized Twenty Postgres database because the local Twenty REST token can expire during long-running local operator sessions.

The script stages CSV files, copies them into the `twenty-db-1` container, and inserts or updates:

- `company`
- `person`
- `opportunity`
- `note`
- `noteTarget`
- `task`
- `taskTarget`

It targets the local Twenty workspace schema:

```text
workspace_9n9szi9g3ok7r13ocz40gbvhd
```

## What Each Account Gets

Each prospect company receives a full `Strategy + Research Packet` note containing:

- Account strategy brief
- 20x AI GTM strategy
- Teaser / outbound email copy
- CSS design prompt
- Website setup prompt
- Proposal build prompt
- Proof summary
- Local artifact links served from `http://localhost:8096`

Each prospect also gets a corresponding opportunity and five GTM follow-up tasks.

## Verified Result

Latest verified local Twenty counts after import:

```text
prospect_companies|1783
strategy_notes|1783
opportunities|1783
people|1808
tasks|8915
```

Two sample notes were verified to contain full strategy content:

```text
Strategy + Research Packet: Argosy Private Equity
Strategy + Research Packet: Haskins Law Firm
```

Both sample notes included:

- `## Account Strategy Brief`
- `## 20x AI GTM Strategy`
- local teaser artifact links under `http://localhost:8096/teasers_2000/`

The artifact server was also checked with:

```bash
curl -fsS -I http://127.0.0.1:8096/teasers_2000/argosy-private-equity/index.html
```

Expected: HTTP 200.

## Proof

The local import writes proof files to:

```text
out/twenty-crm/imports/all_1783/twenty_db_import_proof.json
out/twenty-crm/imports/all_1783/twenty_db_import_run.log
```

The proof JSON records:

- generated timestamp
- scope
- local-only flag
- human gate
- stage counts
- before / after object counts
- deltas
- validation checks
- input hashes
- target workspace schema

## Human Gate

This import prepares RIG and Mike Rodgers for GTM execution, but it does not authorize external action.

Still requires Mike approval before:

- outbound emails
- phone/SMS outreach
- LinkedIn or social automation
- Apollo or Clay writeback
- ad audience upload
- calendar operations
- public proposal deployment
- public tunnel or QNAP/LakeOS exposure

## Recovery

If the local CRM UI is already open at `http://localhost:3020`, refresh it after running the import.

If the REST API token expires, use the deterministic DB import path above. Do not patch around auth by storing tokens in the repository.

