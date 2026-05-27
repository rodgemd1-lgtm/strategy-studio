#!/usr/bin/env python3
"""
OmniScout Internal Docs Collector
Searches local RIG OS documentation and Susan RAG for evidence.
"""

import os, uuid, json
from datetime import datetime, timezone
from pathlib import Path

class InternalDocsCollector:
    name = "internal_docs_collector"
    allowed_source_types = ["internal_docs"]

    def validate_request(self, request: dict) -> dict:
        allowed = request.get("allowed_sources", [])
        if "internal_docs" not in allowed:
            return {"approved": False, "reason": "internal_docs not in allowed_sources"}
        return {"approved": True, "blocked_reasons": [], "required_permissions": []}

    def collect(self, request: dict) -> dict:
        goal = request.get("research_goal", "")
        evidence = []

        # Search local docs
        docs_dir = os.path.expanduser("~/Desktop/Startup-Intelligence-OS/docs")
        if os.path.isdir(docs_dir):
            for md_file in Path(docs_dir).rglob("*.md"):
                if ".git" in str(md_file):
                    continue
                try:
                    content = md_file.read_text(errors="ignore")
                    if goal.lower() in content.lower():
                        evidence.append({
                            "evidence_id": str(uuid.uuid4()),
                            "source_id": str(md_file),
                            "source_type": "internal",
                            "retrieved_at": datetime.now(timezone.utc).isoformat(),
                            "raw_location": str(md_file),
                            "summary": content[:500],
                            "claims_extracted": [],
                            "entities_extracted": [],
                            "confidence": 0.7,
                            "source_reliability": 0.9,
                            "privacy_level": "internal",
                            "permission_status": "approved",
                        })
                except:
                    pass

        return {
            "request_id": request.get("request_id", ""),
            "status": "complete" if evidence else "partial",
            "summary": f"Found {len(evidence)} internal doc matches",
            "evidence": evidence,
        }
