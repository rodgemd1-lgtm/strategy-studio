#!/usr/bin/env python3
"""
OmniScout arXiv Collector
Fetches daily arXiv papers via the arXiv API.
Requires: pip install arxiv
"""

import uuid, json
from datetime import datetime, timezone

class ArxivCollector:
    name = "arxiv_collector"
    allowed_source_types = ["academic"]

    # Category mappings
    CATEGORIES = {
        "general_ai": ["cs.AI", "cs.LG"],
        "chemistry": ["cs.AI", "q-bio"],
        "motion": ["cs.CV", "cs.LG"],
        "agriculture": ["cs.AI", "q-bio"],
    }

    def validate_request(self, request: dict) -> dict:
        allowed = request.get("allowed_sources", [])
        if "academic" not in allowed:
            return {"approved": False, "reason": "academic not in allowed_sources"}
        return {"approved": True, "blocked_reasons": [], "required_permissions": []}

    def collect(self, request: dict) -> dict:
        try:
            import arxiv
        except ImportError:
            return {
                "request_id": request.get("request_id", ""),
                "status": "failed",
                "summary": "arxiv package not installed. Run: pip install arxiv",
                "evidence": [],
            }

        goal = request.get("research_goal", "")
        max_results = request.get("budget", {}).get("max_sources", 20)

        # Determine category from request
        category = "general_ai"
        goal_lower = goal.lower()
        if "chemistry" in goal_lower or "chemical" in goal_lower:
            category = "chemistry"
        elif "motion" in goal_lower or "human" in goal_lower:
            category = "motion"
        elif "agriculture" in goal_lower or "farming" in goal_lower:
            category = "agriculture"

        cats = self.CATEGORIES.get(category, ["cs.AI"])
        query = " OR ".join(f"cat:{c}" for c in cats)

        try:
            search = arxiv.Search(
                query=goal,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            results = list(search.results())
        except Exception as e:
            return {
                "request_id": request.get("request_id", ""),
                "status": "failed",
                "summary": f"arXiv API error: {str(e)}",
                "evidence": [],
            }

        evidence = []
        for paper in results:
            evidence.append({
                "evidence_id": str(uuid.uuid4()),
                "source_id": paper.entry_id,
                "source_type": "paper",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "raw_location": paper.pdf_url,
                "summary": paper.summary[:500] if paper.summary else "",
                "claims_extracted": [{"text": paper.title, "keyword": "title"}],
                "entities_extracted": [a.name for a in paper.authors[:5]],
                "confidence": 0.7,
                "source_reliability": 0.8,
                "privacy_level": "public",
                "permission_status": "approved",
            })

        return {
            "request_id": request.get("request_id", ""),
            "status": "complete" if evidence else "partial",
            "summary": f"Found {len(evidence)} papers from arXiv ({category})",
            "evidence": evidence,
        }
