#!/usr/bin/env python3
"""
OmniScout Web Collector
Searches the web for evidence using DuckDuckGo Lite (no API key required).
Requires: pip install duckduckgo-search
"""

import uuid
from datetime import datetime, timezone

class WebCollector:
    name = "web_collector"
    allowed_source_types = ["web"]

    def validate_request(self, request: dict) -> dict:
        allowed = request.get("allowed_sources", [])
        if "web" not in allowed:
            return {"approved": False, "reason": "web not in allowed_sources"}
        privacy = request.get("privacy_level", "public")
        if privacy == "private":
            return {"approved": False, "reason": "web collector only handles public sources"}
        return {"approved": True, "blocked_reasons": [], "required_permissions": []}

    def collect(self, request: dict) -> dict:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {
                "request_id": request.get("request_id", ""),
                "status": "failed",
                "summary": "duckduckgo-search not installed. Run: pip install duckduckgo-search",
                "evidence": [],
            }

        goal = request.get("research_goal", "")
        max_results = request.get("budget", {}).get("max_sources", 10)

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(goal, max_results=max_results))
        except Exception as e:
            return {
                "request_id": request.get("request_id", ""),
                "status": "failed",
                "summary": f"Web search error: {str(e)}",
                "evidence": [],
            }

        evidence = []
        for r in results:
            evidence.append({
                "evidence_id": str(uuid.uuid4()),
                "source_id": r.get("href", ""),
                "source_type": "web",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "raw_location": r.get("href", ""),
                "summary": r.get("body", "")[:500],
                "claims_extracted": [{"text": r.get("title", ""), "keyword": "title"}],
                "entities_extracted": [],
                "confidence": 0.5,
                "source_reliability": 0.5,
                "privacy_level": "public",
                "permission_status": "approved",
            })

        return {
            "request_id": request.get("request_id", ""),
            "status": "complete" if evidence else "partial",
            "summary": f"Found {len(evidence)} web results",
            "evidence": evidence,
        }
