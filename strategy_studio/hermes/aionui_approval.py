"""
RIG Lattice — AionUI Approval Integration
Conditional approval at A1, mandatory at A3+, 24h timeout.
"""
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ApprovalRequest:
    approval_id: str
    execution_id: str
    cell_id: str
    archetype: str
    bms_mode: str
    requires_approval: bool
    status: str = "pending"  # pending, approved, rejected, reworked, timeout
    requested_at: str = ""
    responded_at: Optional[str] = None
    approver_notes: str = ""
    timeout_hours: int = 24
    
    def is_timed_out(self) -> bool:
        if self.status != "pending":
            return False
        requested = datetime.fromisoformat(self.requested_at)
        return datetime.now(timezone.utc) > requested + timedelta(hours=self.timeout_hours)


class AionUIApproval:
    """Approval surface for RIG Lattice cell executions."""
    
    def __init__(self, policy: dict = None):
        self.policy = policy or {
            "A1": "conditional",   # Only flagged actions require approval
            "A2": "conditional",
            "A3": "mandatory",     # All A3 executions require approval
            "A4": "mandatory",     # All A4 executions require approval
        }
        self.pending: dict[str, ApprovalRequest] = {}
        self.history: list[ApprovalRequest] = []
    
    def requires_approval(self, bms_mode: str, flagged: bool = False) -> bool:
        """Check if this execution requires approval."""
        mode_prefix = bms_mode.split("_")[0] if "_" in bms_mode else bms_mode
        # Map mode to A1-A4 prefix
        prefix_map = {"PYTHON": "A1", "HYBRID": "A2", "AGENT": "A3", "LLM": "A4"}
        prefix = prefix_map.get(mode_prefix, "A2")
        policy = self.policy.get(prefix, "conditional")
        
        if policy == "mandatory":
            return True
        elif policy == "conditional":
            return flagged
        return False
    
    def request_approval(self, execution_id: str, cell_id: str, archetype: str, bms_mode: str,
                         flagged: bool = False) -> Optional[ApprovalRequest]:
        """Create an approval request if required."""
        if not self.requires_approval(bms_mode, flagged):
            return None
        
        approval_id = hashlib.sha256(f"{execution_id}:{cell_id}".encode()).hexdigest()[:16]
        req = ApprovalRequest(
            approval_id=approval_id,
            execution_id=execution_id,
            cell_id=cell_id,
            archetype=archetype,
            bms_mode=bms_mode,
            requires_approval=True,
            requested_at=datetime.now(timezone.utc).isoformat(),
        )
        self.pending[approval_id] = req
        return req
    
    def approve(self, approval_id: str, notes: str = "") -> bool:
        """Approve a pending request."""
        req = self.pending.get(approval_id)
        if not req:
            return False
        req.status = "approved"
        req.responded_at = datetime.now(timezone.utc).isoformat()
        req.approver_notes = notes
        self.history.append(req)
        del self.pending[approval_id]
        return True
    
    def reject(self, approval_id: str, notes: str = "") -> bool:
        """Reject a pending request."""
        req = self.pending.get(approval_id)
        if not req:
            return False
        req.status = "rejected"
        req.responded_at = datetime.now(timezone.utc).isoformat()
        req.approver_notes = notes
        self.history.append(req)
        del self.pending[approval_id]
        return True
    
    def check_timeouts(self) -> list[ApprovalRequest]:
        """Check for timed-out requests."""
        timed_out = []
        for aid, req in list(self.pending.items()):
            if req.is_timed_out():
                req.status = "timeout"
                req.responded_at = datetime.now(timezone.utc).isoformat()
                timed_out.append(req)
                self.history.append(req)
                del self.pending[aid]
        return timed_out
    
    def summary(self) -> dict:
        return {
            "pending": len(self.pending),
            "history": len(self.history),
            "approved": sum(1 for r in self.history if r.status == "approved"),
            "rejected": sum(1 for r in self.history if r.status == "rejected"),
            "timed_out": sum(1 for r in self.history if r.status == "timeout"),
        }


# ─── CLI ───

if __name__ == "__main__":
    aion = AionUIApproval()
    
    # Test: A1 conditional (not flagged) → no approval
    req1 = aion.request_approval("exec-001", "L1-D1-I1", "A1.1", "PYTHON_ONLY", flagged=False)
    print(f"A1 (not flagged): approval_required={req1 is not None}")
    
    # Test: A1 conditional (flagged) → approval required
    req2 = aion.request_approval("exec-002", "L1-D1-S", "A1.4", "PYTHON_ONLY", flagged=True)
    print(f"A1 (flagged): approval_required={req2 is not None}")
    if req2:
        aion.approve(req2.approval_id, "Looks good")
    
    # Test: A3 mandatory → approval required
    req3 = aion.request_approval("exec-003", "L5-D2-S", "A3.4", "AGENT_BOUNDED")
    print(f"A3 (mandatory): approval_required={req3 is not None}")
    if req3:
        aion.reject(req3.approval_id, "Needs more evidence")
    
    print(f"\nAionUI Summary: {aion.summary()}")
