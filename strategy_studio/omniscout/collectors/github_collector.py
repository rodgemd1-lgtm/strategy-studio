#!/usr/bin/env python3
"""
OmniScout GitHub Collector
Searches cloned GitHub repos for evidence relevant to research requests.
Only reads local files — no network calls to GitHub API.
"""

import os, json, re, uuid
from pathlib import Path
from datetime import datetime, timezone

REPOS_DIR = os.path.expanduser("~/rig-lab/omniscout-external-repos")

class GitHubCollector:
    name = "github_collector"
    allowed_source_types = ["github"]

    def validate_request(self, request: dict) -> dict:
        allowed = request.get("allowed_sources", [])
        if "github" not in allowed:
            return {"approved": False, "reason": "github not in allowed_sources"}
        privacy = request.get("privacy_level", "public")
        if privacy == "private":
            return {"approved": False, "reason": "github collector only handles public sources"}
        return {"approved": True, "blocked_reasons": [], "required_permissions": []}

    def collect(self, request: dict) -> dict:
        """Search local cloned repos for evidence matching the research goal."""
        goal = request.get("research_goal", "")
        keywords = self._extract_keywords(goal)
        evidence = []

        for repo_name in os.listdir(REPOS_DIR):
            repo_path = os.path.join(REPOS_DIR, repo_name)
            if not os.path.isdir(repo_path):
                continue
            # Search README and markdown files
            for md_file in Path(repo_path).rglob("*.md"):
                if ".git" in str(md_file):
                    continue
                try:
                    content = md_file.read_text(errors="ignore")
                    score = self._relevance_score(content, keywords)
                    if score > 0.1:
                        evidence.append({
                            "evidence_id": str(uuid.uuid4()),
                            "source_id": repo_name,
                            "source_type": "github",
                            "retrieved_at": datetime.now(timezone.utc).isoformat(),
                            "raw_location": str(md_file),
                            "summary": content[:500],
                            "claims_extracted": self._extract_claims(content, keywords),
                            "entities_extracted": [],
                            "confidence": min(score, 1.0),
                            "source_reliability": 0.6,
                            "privacy_level": "public",
                            "permission_status": "approved",
                        })
                except:
                    pass

        return {
            "request_id": request.get("request_id", ""),
            "status": "complete" if evidence else "partial",
            "summary": f"Found {len(evidence)} evidence items from {len(os.listdir(REPOS_DIR))} repos",
            "evidence": evidence,
        }

    def _extract_keywords(self, text: str) -> list:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "shall", "can", "need", "dare", "ought",
                      "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
                      "as", "into", "through", "during", "before", "after", "above", "below",
                      "between", "out", "off", "over", "under", "again", "further", "then",
                      "once", "here", "there", "when", "where", "why", "how", "all", "both",
                      "each", "few", "more", "most", "other", "some", "such", "no", "nor",
                      "not", "only", "own", "same", "so", "than", "too", "very", "just",
                      "because", "but", "and", "or", "if", "while", "about", "what", "which",
                      "who", "whom", "this", "that", "these", "those", "am", "it", "its"}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in stop_words][:10]

    def _relevance_score(self, content: str, keywords: list) -> float:
        if not keywords:
            return 0.0
        content_lower = content.lower()
        matches = sum(1 for kw in keywords if kw in content_lower)
        return matches / len(keywords)

    def _extract_claims(self, content: str, keywords: list) -> list:
        sentences = re.split(r'[.\n]', content)
        claims = []
        for s in sentences:
            s = s.strip()
            if len(s) > 20 and len(s) < 300:
                for kw in keywords:
                    if kw in s.lower():
                        claims.append({"text": s, "keyword": kw})
                        break
        return claims[:5]
