#!/usr/bin/env python3
"""
OmniScout → ODTB Handoff Writer
Proposes decision records to ODTB (OmniScout Decision Tracking Base).
All writes are proposal-only by default.
"""

import json, uuid
from datetime import datetime, timezone

class ODTBHandoffWriter:
    """Proposes decision records and evidence links to ODTB."""

    def propose(self, evidence_bundle: dict) -> dict:
        """Convert evidence bundle into proposed ODTB decision records."""
        proposals = []

        # Create a decision record for the research request
        proposals.append({
            "proposal_id": str(uuid.uuid4()),
            "target_table": "odtb_decisions",
            "operation": "insert",
            "data": {
                "id": str(uuid.uuid4()),
                "decision_title": f"OmniScout research: {evidence_bundle.get('request_id', 'unknown')[:8]}",
                "evidence_summary": evidence_bundle.get("summary", ""),
                "evidence_count": len(evidence_bundle.get("evidence", [])),
                "source_types": list(set(e.get("source_type", "") for e in evidence_bundle.get("evidence", []))),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "research_complete",
                "metadata": {
                    "request_id": evidence_bundle.get("request_id", ""),
                    "collector": evidence_bundle.get("collector", ""),
                }
            },
            "status": "proposed",
            "approved_by": None,
            "applied_at": None,
        })

        return {
            "handoff_id": str(uuid.uuid4()),
            "target_system": "ODTB",
            "evidence_bundle_id": evidence_bundle.get("request_id", ""),
            "proposed_writes": proposals,
            "status": "proposed",
            "approved_by": None,
            "applied_at": None,
        }
