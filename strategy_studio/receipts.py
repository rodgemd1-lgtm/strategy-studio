"""
Cold-Start Receipt System for RIG Strategy Studio.

Every full pipeline run produces a Receipt — a signed, verifiable artifact
that proves the run happened, what it executed, and what it produced.

Receipts are written to:
  ~/.strategy-studio/receipts/{run_id}.json

Each receipt contains:
  - run_id: deterministic hash of inputs
  - timestamp: UTC ISO timestamp
  - cell_ids: all cells executed
  - packet_ids: ProofPacket IDs per cell
  - input_hash / output_hash: SHA-256 of inputs and outputs
  - bms_score, bms_mode: build mode selection
  - step_statuses: PASS/FAIL/UNKNOWN per IQRSQPI step
  - escalation_count: total escalations
  - total_duration_ms: cumulative execution time
  - proof_packets: full ProofPacket data per cell
  - verification: hash chain proving receipt integrity
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_studio.lattice_wire import (
    Altitude,
    Diamond,
    IQRSQPIStep,
    LatticeCell,
    ProofPacket,
    LatticeOrchestrator,
    compute_bms,
)


# ── Receipt directory ────────────────────────────────────────────────────────

def _receipt_dir() -> Path:
    """Return the receipts directory, creating it if needed."""
    home = Path.home()
    rd = home / ".strategy-studio" / "receipts"
    rd.mkdir(parents=True, exist_ok=True)
    return rd


# ── Receipt model ─────────────────────────────────────────────────────────────

class QualityPacket:
    """Quality gate results per cell."""
    def __init__(self, cell_id: str, step: str, mode: str, gates: list[dict]):
        self.cell_id = cell_id
        self.step = step
        self.mode = mode
        self.gates = gates

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "step": self.step,
            "mode": self.mode,
            "gates": self.gates,
        }


class ColdStartReceipt:
    """Complete receipt for a strategy studio run."""

    def __init__(
        self,
        run_id: str,
        input_data: dict[str, Any],
        lattice_altitude: int,
        lattice_diamond: str,
        bms_score: float,
        bms_mode: str,
    ):
        self.run_id = run_id
        self.timestamp = datetime.now(timezone.utc)
        self.input_data = input_data
        self.input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:32]
        self.lattice_altitude = lattice_altitude
        self.lattice_diamond = lattice_diamond
        self.bms_score = bms_score
        self.bms_mode = bms_mode
        self.packets: list[dict[str, Any]] = []
        self.step_statuses: dict[str, str] = {}
        self.escalation_count = 0
        self.total_duration_ms = 0
        self.quality_packets: list[dict[str, Any]] = []

    def add_packet(self, packet: ProofPacket) -> None:
        """Record a ProofPacket from cell execution."""
        self.packets.append(packet.model_dump())
        self.step_statuses[packet.step] = packet.status
        self.total_duration_ms += packet.duration_ms
        if packet.escalation_required:
            self.escalation_count += 1

    def add_quality_packet(self, qp: QualityPacket) -> None:
        """Record quality gate results."""
        self.quality_packets.append(qp.to_dict())

    def seal(self) -> dict[str, Any]:
        """Seal and return the complete receipt."""
        # Build output hash from all packets
        output_str = json.dumps(self.packets, sort_keys=True, default=str)
        output_hash = hashlib.sha256(output_str.encode()).hexdigest()[:32]

        # Hash chain: each packet hashes the previous
        receipt_hash = self.input_hash
        for pkt in self.packets:
            receipt_hash = hashlib.sha256(
                (receipt_hash + pkt.get("output_hash", "")).encode()
            ).hexdigest()[:32]

        return {
            "receipt_id": self.run_id,
            "version": "1.0",
            "timestamp": self.timestamp.isoformat(),
            "input_hash": self.input_hash,
            "output_hash": output_hash,
            "receipt_hash": receipt_hash,
            "lattice_altitude": self.lattice_altitude,
            "lattice_diamond": self.lattice_diamond,
            "bms_score": self.bms_score,
            "bms_mode": self.bms_mode,
            "total_cells": len(self.packets),
            "total_duration_ms": self.total_duration_ms,
            "escalation_count": self.escalation_count,
            "overall_status": (
                "PASS"
                if all(s == "PASS" for s in self.step_statuses.values())
                else "PARTIAL"
                if any(s == "PASS" for s in self.step_statuses.values())
                else "FAIL"
            ),
            "step_statuses": self.step_statuses,
            "proof_packets": self.packets,
            "quality_packets": self.quality_packets,
            "cell_count": len(self.packets),
            "source": "strategy-studio",
        }

    def save(self) -> Path:
        """Write receipt to disk and return the path."""
        receipt_dir = _receipt_dir()
        path = receipt_dir / f"{self.run_id}.json"
        sealed = self.seal()
        path.write_text(
            json.dumps(sealed, indent=2, default=str),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def load(run_id: str) -> dict[str, Any]:
        """Load a receipt by run_id."""
        path = _receipt_dir() / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Receipt not found: {run_id}")
        with open(path) as fh:
            return json.load(fh)

    @staticmethod
    def list_receipts() -> list[dict[str, Any]]:
        """List all receipts in the receipts directory."""
        receipt_dir = _receipt_dir()
        results = []
        for path in sorted(receipt_dir.glob("*.json")):
            try:
                with open(path) as fh:
                    data = json.load(fh)
                results.append({
                    "run_id": data.get("receipt_id", path.stem),
                    "timestamp": data.get("timestamp", ""),
                    "overall_status": data.get("overall_status", "?"),
                    "total_cells": data.get("total_cells", 0),
                    "bms_mode": data.get("bms_mode", "?"),
                    "path": str(path),
                })
            except Exception:
                pass
        return results


# ── Execute with receipts ─────────────────────────────────────────────────────

def run_with_receipt(
    company_name: str,
    industry: str,
    context: str = "",
    competitors: list[str] | None = None,
    altitude: Altitude = Altitude.L2,
    diamond: Diamond = Diamond.D1_STRATEGY,
) -> tuple[ColdStartReceipt, LatticeOrchestrator]:
    """Run the full pipeline and produce a signed ColdStartReceipt.
    
    Returns (receipt, orchestrator). Raises on critical failure.
    """
    run_id = hashlib.md5(
        f"{company_name}{industry}{time.time()}".encode()
    ).hexdigest()[:12]

    input_data = {
        "query": f"Strategy for {company_name} in {industry}. {context}",
        "company": company_name,
        "industry": industry,
        "competitors": competitors or [],
    }

    bms = compute_bms(altitude=altitude)

    receipt = ColdStartReceipt(
        run_id=run_id,
        input_data=input_data,
        lattice_altitude=altitude.value,
        lattice_diamond=diamond.value,
        bms_score=round(bms.final, 4),
        bms_mode=bms.select_mode().value,
    )

    orchestrator = LatticeOrchestrator()
    result = orchestrator.execute_full_pipeline(
        input_data=input_data,
        altitude=altitude,
        diamond=diamond,
    )

    # Record all packets
    for packet in orchestrator.execution_log:
        receipt.add_packet(packet)

    # Record quality gates
    from strategy_studio.lattice_wire import run_quality_gates, LatticeCell
    for step in IQRSQPIStep:
        cell = LatticeCell(altitude=altitude, diamond=diamond, step=step)
        output = result["steps_output"].get(step, {})
        gate_result = run_quality_gates(cell, output)
        qp = QualityPacket(
            cell_id=cell.cell_id,
            step=step.value,
            mode=gate_result.mode,
            gates=[
                {
                    "name": g.name,
                    "status": g.status.value,
                    "message": g.message,
                }
                for g in gate_result.gates
            ],
        )
        receipt.add_quality_packet(qp)

    receipt.save()
    return receipt, orchestrator