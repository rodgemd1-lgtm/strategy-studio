#!/usr/bin/env python3
"""
OmniScout arXiv → HEB+ Evidence Pipeline
Fetches recent arXiv papers and inserts evidence into heb_evidence table.
"""

import os, sys, uuid, json
from datetime import datetime, timezone

sys.path.insert(0, os.path.expanduser("~/Desktop/Startup-Intelligence-OS/benchmarks/mirrormind/evaluator"))
from db_helper import sb_insert, sb_count, sb_query

def fetch_arxiv_papers(query: str, max_results: int = 20, category: str = "cs.AI") -> list:
    """Fetch papers from arXiv API."""
    try:
        import arxiv
    except ImportError:
        print("ERROR: arxiv package not installed. Run: pip install arxiv")
        return []

    try:
        search = arxiv.Search(
            query=f"cat:{category} AND ({query})",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        return list(search.results())
    except Exception as e:
        print(f"arXiv API error: {e}")
        return []


def papers_to_evidence(papers: list, research_goal: str) -> list:
    """Convert arXiv papers to HEB+ evidence rows."""
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for paper in papers:
        claim_text = f"arXiv:{paper.title} — {paper.summary[:300]}"
        rows.append({
            "id": str(uuid.uuid4()),
            "evidence_text": claim_text[:1000],
            "source_id": str(uuid.uuid4()),  # placeholder source
            "direction": "supports",
            "reliability_score": 0.8,
            "relevance_score": 0.7,
            "extraction_method": "omniscout_arxiv_v1",
            "metadata": {
                "arxiv_id": paper.entry_id,
                "authors": [a.name for a in paper.authors[:3]],
                "published": paper.published.isoformat() if paper.published else None,
                "research_goal": research_goal[:200],
            },
            "created_at": now,
        })
    return rows


def run_pipeline(queries: list = None, max_per_query: int = 15) -> dict:
    """Run the full arXiv → HEB+ pipeline."""
    if queries is None:
        queries = [
            "AI agent orchestration",
            "multi-agent systems",
            "large language model reasoning",
            "active inference",
            "forecasting prediction markets",
        ]

    results = {"queries": [], "total_papers": 0, "total_stored": 0}

    for query in queries:
        print(f"  Fetching: '{query}'...")
        papers = fetch_arxiv_papers(query, max_results=max_per_query)
        if not papers:
            continue

        evidence_rows = papers_to_evidence(papers, query)
        print(f"    → {len(evidence_rows)} papers")

        # Batch insert
        for i in range(0, len(evidence_rows), 50):
            chunk = evidence_rows[i:i+50]
            inserted = sb_insert("heb_evidence", chunk)
            if inserted:
                results["total_stored"] += len(inserted)

        results["queries"].append({"query": query, "papers": len(papers)})
        results["total_papers"] += len(papers)

    # Verify
    count = sb_count("heb_evidence")
    print(f"\n✓ Total evidence in heb_evidence: {count}")
    print(f"✓ New evidence added: {results['total_stored']}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OmniScout arXiv → HEB+ Pipeline")
    parser.add_argument("--query", type=str, help="Custom search query")
    parser.add_argument("--max", type=int, default=15, help="Max papers per query")
    args = parser.parse_args()

    if args.query:
        queries = [args.query]
    else:
        queries = None  # Use defaults

    results = run_pipeline(queries=queries, max_per_query=args.max)
    print(f"\nResults: {json.dumps(results, indent=2, default=str)}")
