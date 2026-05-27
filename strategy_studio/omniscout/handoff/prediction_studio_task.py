#!/usr/bin/env python3
"""
OmniScout → Prediction Studio Handoff
Proposes forecast tasks and evidence links to Prediction Studio.
All writes are proposal-only by default.
"""

import json, uuid
from datetime import datetime, timezone

class PredictionStudioTask:
    """Proposes forecast tasks to Prediction Studio based on OmniScout evidence."""

    def propose(self, evidence_bundle: dict) -> dict:
        """Extract forecast implications from evidence bundle."""
        proposals = []
        evidence_items = evidence_bundle.get("evidence", [])

        # Look for forecast-relevant signals
        forecast_keywords = ["forecast", "prediction", "market", "probability", "outcome",
                            "trend", "growth", "decline", "opportunity", "risk"]
        forecast_evidence = []
        for ev in evidence_items:
            summary = ev.get("summary", "").lower()
            for kw in forecast_keywords:
                if kw in summary:
                    forecast_evidence.append(ev)
                    break

        if forecast_evidence:
            proposals.append({
                "proposal_id": str(uuid.uuid4()),
                "target_table": "pred_studio_tasks",
                "operation": "insert",
                "data": {
                    "id": str(uuid.uuid4()),
                    "task_type": "forecast_update",
                    "title": f"OmniScout forecast evidence from {evidence_bundle.get('request_id', 'unknown')[:8]}",
                    "evidence_count": len(forecast_evidence),
                    "source_evidence_ids": [e.get("evidence_id", "") for e in forecast_evidence[:10]],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "pending_review",
                    "metadata": {
                        "request_id": evidence_bundle.get("request_id", ""),
                        "collector": evidence_bundle.get("collector", ""),
                        "forecast_keywords_matched": len(forecast_evidence),
                    }
                },
                "status": "proposed",
                "approved_by": None,
                "applied_at": None,
            })

        return {
            "handoff_id": str(uuid.uuid4()),
            "target_system": "Prediction Studio",
            "evidence_bundle_id": evidence_bundle.get("request_id", ""),
            "proposed_writes": proposals,
            "status": "proposed",
            "approved_by": None,
            "applied_at": None,
        }
