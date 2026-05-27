#!/usr/bin/env python3
"""
OmniScout → HEB Handoff Writer
Proposes evidence writes to HEB+ belief system.
All writes are proposal-only by default — never auto-applied.
"""

import json, uuid
from datetime import datetime, timezone

class HEBHandoffWriter:
    """Proposes evidence and belief updates to HEB+."""

    def propose(self, evidence_bundle: dict) -> dict:
        """Convert evidence bundle into proposed HEB+ writes."""
        proposals = []
        evidence_items = evidence_bundle.get("evidence", [])

        for ev in evidence_items:
            proposal = {
                "proposal_id": str(uuid.uuid4()),
                "target_table": "heb_evidence",
                "operation": "insert",
                "data": {
                    "id": ev.get("evidence_id", str(uuid.uuid4())),
                    "evidence_text": ev.get("summary", "")[:1000],
                    "source_url": ev.get("raw_location", ""),
                    "reliability_score": ev.get("source_reliability", 0.5),
                    "evidence_direction": "supports",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source_type": ev.get("source_type", ""),
                        "collector": evidence_bundle.get("collector", "unknown"),
                        "request_id": evidence_bundle.get("request_id", ""),
                    }
                },
                "status": "proposed",
                "approved_by": None,
                "applied_at": None,
            }
            proposals.append(proposal)

        # Also propose new hypotheses if strong claims found
        claims = []
        for ev in evidence_items:
            claims.extend(ev.get("claims_extracted", []))

        if len(claims) >= 3:
            proposals.append({
                "proposal_id": str(uuid.uuid4()),
                "target_table": "heb_hypotheses",
                "operation": "insert",
                "data": {
                    "id": str(uuid.uuid4()),
                    "title": f"OmniScout hypothesis from {evidence_bundle.get('request_id', 'unknown')[:8]}",
                    "current_probability": 0.5,
                    "confidence": 0.3,
                    "domain": "omniscout",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"source": "omniscout_auto", "claim_count": len(claims)},
                },
                "status": "proposed",
                "approved_by": None,
                "applied_at": None,
            })

        return {
            "handoff_id": str(uuid.uuid4()),
            "target_system": "HEB",
            "evidence_bundle_id": evidence_bundle.get("request_id", ""),
            "proposed_writes": proposals,
            "status": "proposed",
            "approved_by": None,
            "applied_at": None,
        }

    def apply(self, proposal: dict, approved_by: str) -> dict:
        """Apply an approved proposal to HEB+. Requires explicit approval."""
        if proposal.get("status") != "approved":
            return {"error": "Proposal not approved", "proposal_id": proposal.get("proposal_id")}
        # In production: insert into Supabase heb_evidence table
        # For now, return the write plan
        return {
            "status": "would_apply",
            "proposal_id": proposal.get("proposal_id"),
            "table": proposal.get("target_table"),
            "data": proposal.get("data"),
            "approved_by": approved_by,
            "note": "Actual Supabase write requires approval workflow",
        }
