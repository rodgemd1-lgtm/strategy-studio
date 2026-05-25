"""Batch runner — process 2000 prospects in parallel.

Codex usage:
    from strategy_studio.teaser.batch import run_batch
    results = run_batch(prospects_jsonl="prospects.jsonl", out_dir="out/", workers=16)

CLI usage:
    python -m strategy_studio.teaser.batch \\
        --input prospects.jsonl \\
        --output ./teasers/ \\
        --workers 16

prospects.jsonl format: one TeaserInput JSON object per line.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError

from strategy_studio.teaser.generator import generate_teaser
from strategy_studio.teaser.schema import TeaserInput


def _process_one(record: dict, out_dir_str: str) -> dict:
    """Worker: validate one record and generate one teaser bundle."""
    out_dir = Path(out_dir_str)
    try:
        t = TeaserInput.model_validate(record)
    except ValidationError as e:
        return {
            "prospect_id": record.get("prospect_id", "<unknown>"),
            "status": "validation_error",
            "errors": e.errors(),
        }
    try:
        result = generate_teaser(t, out_dir)
        result["status"] = "ok"
        return result
    except Exception as e:  # pragma: no cover — defensive
        return {
            "prospect_id": t.prospect_id,
            "status": "generation_error",
            "error": str(e),
            "error_type": type(e).__name__,
        }


def _read_records(path: Path) -> Iterable[dict]:
    """Yield JSON records, one per line."""
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                yield {"prospect_id": f"<line-{ln}>", "_parse_error": str(e)}


def run_batch(
    prospects_jsonl: str | Path,
    out_dir: str | Path,
    workers: int = 8,
    summary_path: str | Path | None = None,
) -> dict:
    """Generate teasers for every prospect in a JSONL file.

    Args:
        prospects_jsonl: Path to a JSONL file (one TeaserInput per line).
        out_dir: Output directory root. Each prospect gets a subdirectory.
        workers: Number of parallel processes. Default 8.
        summary_path: Optional path to write a JSONL summary of every result.

    Returns:
        Dict with totals, error counts, and per-prospect status.
    """
    in_path = Path(prospects_jsonl)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise FileNotFoundError(f"prospects file not found: {in_path}")

    records = list(_read_records(in_path))
    total = len(records)

    started = time.time()
    results: list[dict] = []
    ok = err_val = err_gen = err_parse = 0

    # Filter out parse errors before fanning out
    parseable: list[dict] = []
    for r in records:
        if "_parse_error" in r:
            err_parse += 1
            results.append({
                "prospect_id": r.get("prospect_id", "<unknown>"),
                "status": "parse_error",
                "error": r["_parse_error"],
            })
        else:
            parseable.append(r)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_process_one, r, str(out_path)): r.get("prospect_id", f"row-{i}")
            for i, r in enumerate(parseable)
        }
        for i, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            results.append(res)
            status = res.get("status")
            if status == "ok":
                ok += 1
            elif status == "validation_error":
                err_val += 1
            else:
                err_gen += 1
            if i % 50 == 0 or i == len(futures):
                elapsed = time.time() - started
                rate = i / elapsed if elapsed > 0 else 0
                print(
                    f"[batch] {i}/{len(futures)} "
                    f"ok={ok} val_err={err_val} gen_err={err_gen} "
                    f"parse_err={err_parse} "
                    f"rate={rate:.1f}/s elapsed={elapsed:.0f}s",
                    file=sys.stderr,
                    flush=True,
                )

    elapsed = time.time() - started
    summary = {
        "total": total,
        "ok": ok,
        "validation_errors": err_val,
        "generation_errors": err_gen,
        "parse_errors": err_parse,
        "out_dir": str(out_path),
        "elapsed_seconds": round(elapsed, 2),
        "rate_per_second": round(total / elapsed if elapsed > 0 else 0, 2),
        "workers": workers,
    }

    if summary_path:
        sp = Path(summary_path)
        sp.parent.mkdir(parents=True, exist_ok=True)
        with sp.open("w", encoding="utf-8") as f:
            f.write(json.dumps(summary) + "\n")
            for r in results:
                f.write(json.dumps(r, default=str) + "\n")

    return {"summary": summary, "results": results}


def main() -> int:
    p = argparse.ArgumentParser(description="Generate strategy teasers for many prospects in parallel.")
    p.add_argument("--input", required=True, help="prospects.jsonl path")
    p.add_argument("--output", required=True, help="output directory")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--summary", default=None, help="optional summary JSONL output")
    args = p.parse_args()

    out = run_batch(
        prospects_jsonl=args.input,
        out_dir=args.output,
        workers=args.workers,
        summary_path=args.summary,
    )
    s = out["summary"]
    print(json.dumps(s, indent=2))
    return 0 if s["validation_errors"] == 0 and s["generation_errors"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
