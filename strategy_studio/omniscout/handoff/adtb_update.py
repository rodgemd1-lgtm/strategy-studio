#!/usr/bin/env python3
"""
OmniScout → ADTB+ Handoff
Proposes signal updates to ADTB+ (renamed SYNTHESIS).
All writes are proposal-only by default.
"""

import json, uuid
from datetime import datetime, timezone

class ADTBUpdate:
    """Proposes signal updates to ADTB+ / SYNTHESIS."""

    def propose(self, evidence_bundle: dict) -> dict:
        """Extract weak signals from evidence and propose ADTB+ updates."""
        proposals = []
        evidence_items = evidence_bundle.get("evidence", [])

        for ev in evidence_items:
            claims = ev.get("claims_extracted", [])
            for claim in claims:
                signal = {
                    "proposal_id": str(uuid.uuid4()),
                    "target_table": "adtb_signals",
                    "operation": "insert",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "signal_type": "weak_signal",
                        "domain": ev.get("source_type", "unknown"),
                        "extracted_claim": claim.get("text", "")[:500],
                        "source_url": ev.get("raw_location", ""),
                        "anomaly_score": ev.get("confidence", 0.5),
                        "entities": [],
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "collector": evidence_bundle.get("collector", ""),
                            "request_id": evidence_bundle.get("request_id", ""),
                            "evidence_id": ev.get("evidence_id", ""),
                        }
                    },
                    "status": "proposed",
                    "approved_by": None,
                    "applied_at": None,
                }
                proposals.append(signal)

        return {
            "handoff_id": str(uuid.uuid4()),
            "target_system": "ADTB+",
            "evidence_bundle_id": evidence_bundle.get("request_id", ""),
            "proposed_writes": proposals,
            "status": "proposed",
            "approved_by": None,
            "applied_at": None,
        }
