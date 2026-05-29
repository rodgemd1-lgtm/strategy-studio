# RIG Verification Doctrine

Strategy Studio is governed as a deterministic RIG strategy application.
The local verification path must prove core code, lattice behavior, Archon
compatibility, and tests without contacting LakeOS, Recall, QNAP, CRM, or any
external publishing surface.

## Operating laws

- No ProofPacket, no PASS.
- No DoneContract, no production code.
- No external side effects without explicit human approval.
- Missing evidence is BLOCKED, not PASS.
- If a compatibility failure returns twice, it must become a regression test.

## Local verification

Run:

```bash
make verify
```

This performs:

- Python syntax compilation for maintained package surfaces.
- Local pytest suite, excluding the external-runtime e2e suite by default.
- Local proof stub at `proof/local-verification-proof.json`.

This repo requires Python 3.11 or newer.

## External-runtime verification

The system e2e suite touches OpenClaw, local fleet nodes, launchd/crontab state,
and machine-specific runtime configuration. It is therefore blocked by default:

```bash
make test-e2e
```

To run it, first capture an OpenClaw/fleet runtime ProofPacket, then execute:

```bash
RIG_ALLOW_EXTERNAL_RUNTIME=YES make test-e2e
```

Without that approval flag, `make test-e2e` writes
`proof/external-runtime-blocked-proof.json` and exits blocked instead of
silently treating missing runtime evidence as success.

Adler and CI can prove the guard exists without running the external suite:

```bash
make verify-external-runtime-gate
```

## GO / NO-GO

GO requires:

- `make verify` completes successfully.
- The Archon compatibility tests pass.
- A proof artifact exists.
- No external data source, QNAP mount, Recall API, CRM write, or publication
  action was executed.

NO-GO is required when:

- Any test fails.
- Python version support is violated.
- A proof artifact is missing.
- Any external-side-effect path is invoked without human approval.
- External-runtime e2e runs without `RIG_ALLOW_EXTERNAL_RUNTIME=YES` and
  OpenClaw/fleet runtime proof.

## Proof artifacts

Adler workflow proof for this repository is written outside the product repo:

```text
/Users/mikerodgers/Documents/RIG Coder Setup/proof/multi-repo-adler/strategy-studio/
```
