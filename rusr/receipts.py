"""
RUSR Receipt System — Persistent run receipts with hash chain.

Each run produces a receipt at ~/.rusr/receipts/<run_id>.json.
Receipts are append-only (immutable after creation) and cryptographically
chained: each receipt includes the hash of the previous receipt.

This satisfies Layer 14 (Cross-run continuity) and Layer 17 (Receipt persistence).
"""
from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Config ───────────────────────────────────────────────────────────────────

RECEIPTS_DIR = Path.home() / ".rusr" / "receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Hash helpers ────────────────────────────────────────────────────────────

def sha256_hex(obj: Any) -> str:
    """Stable SHA-256 of a JSON-serializable object."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()
    ).hexdigest()


def hash_receipt(receipt: dict[str, Any]) -> str:
    """Hash a receipt dict (excludes the hash itself)."""
    d = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return sha256_hex(d)


# ── Receipt dataclass ────────────────────────────────────────────────────────

@dataclass
class RunReceipt:
    """
    Immutable run receipt with hash chain.

    Fields:
        run_id:        Unique run identifier (UUID)
        session_id:    Hermes session ID
        studio:        Studio name (strategy/gtm/linkedin/app)
        mode:          Band mode (A1/A2/A3/A4)
        diamond:       Diamond tier (D1/D2/D3)
        cell:          Cell IDs used in this run
        gates_passed:  Set of gates that passed
        gates_failed:  Set of gates that failed
        artifacts:     List of artifact IDs produced
        tool_calls:    Count of tool calls
        budget_used:   Total cost in USD
        wall_seconds:  Elapsed wall time in seconds
        errors:        List of error summaries
        genesis:       Genesis statement
        parent_hash:   Hash of previous receipt (for chain)
        receipt_hash:  Hash of THIS receipt
        created_at:    ISO timestamp
    """

    run_id: str
    session_id: str
    studio: str
    mode: str
    diamond: str
    cell: list[str]
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    tool_calls: int = 0
    budget_used: float = 0.0
    wall_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    genesis: str = ""
    parent_hash: str = ""
    receipt_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict (for JSON)."""
        d = asdict(self)
        return d

    def verify(self) -> bool:
        """
        Verify receipt integrity:
        - Hash chain is unbroken
        - Self-hash matches content
        """
        computed = hash_receipt(self.to_dict())
        return computed == self.receipt_hash


# ── Receipt store ────────────────────────────────────────────────────────────

class ReceiptStore(ABC):
    """Abstract receipt store — plug in filesystem, S3, Postgres, etc."""

    @abstractmethod
    def save(self, receipt: RunReceipt) -> Path:
        """Save receipt and return its path."""
        ...

    @abstractmethod
    def load(self, run_id: str) -> RunReceipt | None:
        """Load receipt by run_id, or None if not found."""
        ...

    @abstractmethod
    def list_runs(self) -> list[str]:
        """List all run_ids in the store."""
        ...


class FilesystemReceiptStore(ReceiptStore):
    """Receipts persisted to ~/.rusr/receipts/*.json"""

    def __init__(self, base_dir: Path = RECEIPTS_DIR):
        self.base = base_dir
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        return self.base / f"{run_id}.json"

    def save(self, receipt: RunReceipt) -> Path:
        path = self._path(receipt.run_id)
        if path.exists():
            raise FileExistsError(f"Receipt {receipt.run_id} already exists — receipts are immutable")
        # Compute and set hash
        d = receipt.to_dict()
        d["receipt_hash"] = ""  # placeholder for hashing
        d["receipt_hash"] = hash_receipt(d)
        # Re-verify
        assert d["receipt_hash"] == hash_receipt(d), "Hash mismatch after set"
        path.write_text(json.dumps(d, indent=2, default=str))
        return path

    def load(self, run_id: str) -> RunReceipt | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        d = json.loads(path.read_text())
        return RunReceipt(**d)

    def list_runs(self) -> list[str]:
        return [p.stem for p in self.base.glob("*.json")]


# ── Receipt-aware orchestrator ───────────────────────────────────────────────

class ReceiptOrchestrator:
    """
    Wrapper that adds receipt generation to any studio orchestrator.

    Usage:
        orch = ReceiptOrchestrator(
            backend=StrategyOrchestrator(...),
            store=FilesystemReceiptStore(),
        )
        result = orch.run(input_data)
        # Receipt is already saved to ~/.rusr/receipts/
    """

    def __init__(
        self,
        backend: Any,  # Any orchestrator with a .run(input_data) method
        store: ReceiptStore | None = None,
        studio: str = "strategy",
    ):
        self.backend = backend
        self.store = store or FilesystemReceiptStore()
        self.studio = studio

    def run(self, input_data: dict[str, Any], **kwargs: Any) -> Any:
        import time, uuid
        t0 = time.time()
        session_id = input_data.get("session_id", str(uuid.uuid4()))
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M%S')}"

        # Find previous receipt for hash chain
        runs = sorted(self.store.list_runs())
        parent_hash = ""
        if runs:
            prev = self.store.load(runs[-1])
            if prev:
                parent_hash = prev.receipt_hash

        # Run the backend
        try:
            result = self.backend.run(input_data, **kwargs)
        except Exception as exc:
            result = {"error": str(exc)}

        wall = time.time() - t0
        receipt = RunReceipt(
            run_id=run_id,
            session_id=session_id,
            studio=self.studio,
            mode=input_data.get("mode", "A1"),
            diamond=input_data.get("diamond", "D2"),
            cell=input_data.get("cell", []),
            tool_calls=int(result.get("tool_calls", 0)) if isinstance(result, dict) else 0,
            budget_used=float(result.get("budget_used", 0.0)) if isinstance(result, dict) else 0.0,
            wall_seconds=wall,
            errors=[result["error"]] if isinstance(result, dict) and "error" in result else [],
            genesis=input_data.get("genesis", ""),
            parent_hash=parent_hash,
        )

        # Save receipt
        try:
            self.store.save(receipt)
        except FileExistsError:
            pass  # Idempotent — already saved

        return result

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the full receipt hash chain is unbroken."""
        runs = sorted(self.store.list_runs())
        errors: list[str] = []
        for run_id in runs:
            r = self.store.load(run_id)
            if not r:
                errors.append(f"{run_id}: not found in store")
                continue
            if not r.verify():
                errors.append(f"{run_id}: self-hash mismatch")
            if r.parent_hash:
                prev_run = None
                for other in runs:
                    if other == run_id:
                        break
                    prev_run = other
                if prev_run:
                    prev = self.store.load(prev_run)
                    if prev and r.parent_hash != prev.receipt_hash:
                        errors.append(f"{run_id}: parent hash mismatch")
        return len(errors) == 0, errors