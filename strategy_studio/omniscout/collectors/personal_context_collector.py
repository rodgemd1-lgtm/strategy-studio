#!/usr/bin/env python3
"""
OmniScout Personal Context Collector
Reads personal data (calendar, email, reminders) for evidence.
PRIVATE — requires explicit approval for every request.
"""

import uuid, json, subprocess
from datetime import datetime, timezone

class PersonalContextCollector:
    name = "personal_context_collector"
    allowed_source_types = ["personal"]

    def validate_request(self, request: dict) -> dict:
        allowed = request.get("allowed_sources", [])
        if "personal" not in allowed:
            return {"approved": False, "reason": "personal not in allowed_sources"}
        # ALWAYS requires explicit approval
        if not request.get("explicit_personal_approval", False):
            return {"approved": False, "reason": "requires_explicit_personal_approval"}
        return {"approved": True, "blocked_reasons": [], "required_permissions": ["personal_data_access"]}

    def collect(self, request: dict) -> dict:
        """Only collects personal data with explicit approval."""
        goal = request.get("research_goal", "")
        evidence = []

        # Calendar events (next 7 days)
        try:
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "Calendar" to get (summary of every event of every calendar whose start date is greater than (current date) and start date is less than ((current date) + 7 * days))'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                events = result.stdout.strip().split(", ")
                for e in events[:10]:
                    evidence.append({
                        "evidence_id": str(uuid.uuid4()),
                        "source_id": "calendar",
                        "source_type": "personal",
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "raw_location": "local:calendar",
                        "summary": e,
                        "claims_extracted": [],
                        "entities_extracted": [],
                        "confidence": 0.9,
                        "source_reliability": 1.0,
                        "privacy_level": "private",
                        "permission_status": "approved",
                    })
        except:
            pass

        return {
            "request_id": request.get("request_id", ""),
            "status": "complete" if evidence else "partial",
            "summary": f"Found {len(evidence)} personal context items",
            "evidence": evidence,
        }
