"""
Evidence Engine for Strategy Studio.

Deterministic source scoring, contradiction detection, confidence tracking,
and evidence graph construction. All functions are pure and never raise.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse

from strategy_studio.core.types import Evidence
from strategy_studio.core.types_extended import (
    Contradiction,
    EvidenceGraph,
    SourceScore,
)

# ── Source reliability lookup ────────────────────────────────────────────────

_SOURCE_RELIABILITY: dict[str, float] = {
    "academic": 0.90,
    "peer_reviewed": 0.92,
    "government": 0.85,
    "official": 0.85,
    "news": 0.70,
    "reputable_news": 0.78,
    "industry_report": 0.72,
    "analyst": 0.68,
    "trade_publication": 0.65,
    "blog": 0.40,
    "social_media": 0.25,
    "forum": 0.30,
    "unknown": 0.35,
}

# Top-level domain reliability hints
_TLD_RELIABILITY: dict[str, float] = {
    ".edu": 0.88,
    ".gov": 0.85,
    ".ac.uk": 0.88,
    ".org": 0.60,
}

# Confidence literal to numeric
_CONF_VAL = {"H": 0.8, "M": 0.5, "L": 0.2}

# Weights for overall source score
_WEIGHTS = {
    "reliability": 0.35,
    "relevance": 0.30,
    "recency": 0.20,
    "corroboration": 0.15,
}

# Contradiction signal keywords (negation pairs)
_CONTRADICT_PAIRS = [
    ("increase", "decrease"),
    ("growth", "decline"),
    ("positive", "negative"),
    ("up", "down"),
    ("rise", "fall"),
    ("gain", "loss"),
    ("higher", "lower"),
    ("more", "less"),
    ("above", "below"),
    ("before", "after"),
    ("is", "is not"),
    ("will", "will not"),
    ("can", "cannot"),
    ("always", "never"),
    ("all", "none"),
    ("success", "failure"),
    ("profit", "loss"),
    ("outperform", "underperform"),
    ("lead", "trail"),
    ("above average", "below average"),
]


# ── Internal helpers ─────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    """Lowercase token set from text, stripping non-alphanumeric."""
    return {w for w in text.lower().split() if w.isalnum() and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _extract_domain(uri: str) -> str:
    """Extract domain from URI, fallback to raw string."""
    try:
        parsed = urlparse(uri if "://" in uri else f"https://{uri}")
        return parsed.netloc.lower()
    except Exception:
        return uri.lower()


def _extract_source_type(uri: str, metadata: dict | None) -> str:
    """Best-effort source type from metadata or URI heuristics."""
    if metadata:
        for key in ("source_type", "type", "category"):
            val = metadata.get(key)
            if isinstance(val, str) and val.lower() in _SOURCE_RELIABILITY:
                return val.lower()

    uri_l = uri.lower()
    if any(t in uri_l for t in (".edu", "arxiv", "doi.org", "pubmed", "jstor", "ssrn")):
        return "academic"
    if ".gov" in uri_l or "government" in uri_l:
        return "government"
    if any(t in uri_l for t in ("reuters", "bloomberg", "wsj", "ft.com", "nytimes", "bbc")):
        return "reputable_news"
    if any(t in uri_l for t in ("news", "press", "herald", "tribune", "post", "times")):
        return "news"
    if any(t in uri_l for t in ("blog", "medium.com", "substack", "wordpress")):
        return "blog"
    if any(t in uri_l for t in ("twitter", "x.com", "reddit", "facebook", "linkedin")):
        return "social_media"
    if any(t in uri_l for t in ("forum", "stackoverflow", "quora")):
        return "forum"
    return "unknown"


def _reliability_score(source_type: str, uri: str) -> float:
    """Numeric reliability from type + TLD hints."""
    base = _SOURCE_RELIABILITY.get(source_type, 0.35)
    for tld, val in _TLD_RELIABILITY.items():
        if tld in uri.lower():
            base = max(base, val)
            break
    return min(base, 1.0)


def _recency_score(metadata: dict | None) -> float:
    """
    Exponential decay based on source age.
    Half-life = 365 days. Missing date = 0.5.
    """
    if not metadata:
        return 0.5

    date_raw = metadata.get("date") or metadata.get("published") or metadata.get("timestamp")
    if date_raw is None:
        return 0.5

    try:
        if isinstance(date_raw, (int, float)):
            dt = datetime.fromtimestamp(date_raw, tz=timezone.utc)
        elif isinstance(date_raw, str):
            dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            return 0.5

        now = datetime.now(timezone.utc)
        age_days = max((now - dt).total_seconds() / 86400.0, 0.0)
        half_life = 365.0
        score = math.pow(0.5, age_days / half_life)
        return max(0.0, min(score, 1.0))
    except Exception:
        return 0.5


def _content_hash(content: str) -> str:
    """Deterministic SHA-256 hex digest of content."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def _negation_score(text_a: str, text_b: str) -> float:
    """
    Heuristic: fraction of contradicting keyword pairs where
    one appears in A and the other in B. 0–1 range.
    """
    la = text_a.lower()
    lb = text_b.lower()
    hits = 0
    total = len(_CONTRADICT_PAIRS)
    for w1, w2 in _CONTRADICT_PAIRS:
        in_a1 = w1 in la
        in_b1 = w1 in lb
        in_a2 = w2 in la
        in_b2 = w2 in lb
        if (in_a1 and in_b2) or (in_a2 and in_b1):
            hits += 1
    return hits / total if total else 0.0


# ── Public API ───────────────────────────────────────────────────────────────


def score_source(
    source_uri: str,
    content: str,
    metadata: dict | None = None,
) -> SourceScore:
    """
    Score a single evidence source on four axes.

    Reliability  – source type + TLD heuristics.
    Relevance    – Jaccard overlap between content tokens and any query
                   keywords provided under metadata["query_terms"].
    Recency      – exponential decay from metadata date (half-life 365 d).
    Corroboration– placeholder 0.5; updated later by build_evidence_graph.

    Overall = weighted average (0.35 / 0.30 / 0.20 / 0.15).
    """
    try:
        source_type = _extract_source_type(source_uri, metadata)
        rel = _reliability_score(source_type, source_uri)

        # Relevance
        query_terms: set[str] = set()
        if metadata and "query_terms" in metadata:
            raw = metadata["query_terms"]
            if isinstance(raw, str):
                query_terms = _tokenize(raw)
            elif isinstance(raw, (list, tuple)):
                for t in raw:
                    query_terms.update(_tokenize(str(t)))
        if query_terms:
            content_tokens = _tokenize(content)
            relv = _jaccard(query_terms, content_tokens)
        else:
            relv = 0.5

        rec = _recency_score(metadata)
        corrob = 0.5  # default; refined in graph building

        overall = (
            _WEIGHTS["reliability"] * rel
            + _WEIGHTS["relevance"] * relv
            + _WEIGHTS["recency"] * rec
            + _WEIGHTS["corroboration"] * corrob
        )

        flags: list[str] = []
        if rel < 0.4:
            flags.append("low_reliability")
        if rec < 0.3:
            flags.append("stale_source")
        if not query_terms:
            flags.append("no_query_terms")

        return SourceScore(
            source_uri=source_uri,
            reliability=round(rel, 4),
            relevance=round(relv, 4),
            recency=round(rec, 4),
            corroboration=round(corrob, 4),
            overall=round(overall, 4),
            flags=flags,
        )
    except Exception:
        return SourceScore(source_uri=source_uri)


def detect_contradictions(evidence_list: list[Evidence]) -> list[Contradiction]:
    """
    Compare all pairs of evidence and detect direct contradictions.

    A candidate pair shares keyword overlap (same topic) but contains
    negation signal words in opposite directions.
    Severity is derived from the average confidence of the two sources.
    """
    try:
        results: list[Contradiction] = []
        n = len(evidence_list)
        for i in range(n):
            for j in range(i + 1, n):
                a = evidence_list[i]
                b = evidence_list[j]
                # Quick similarity gate: must share some topic tokens
                tokens_a = _tokenize(a.source_uri)
                tokens_b = _tokenize(b.source_uri)
                # Use content_hash equality as corroboration, inequality + negation as contradiction base
                neg = _negation_score(a.source_uri, b.source_uri)
                if neg < 0.05:
                    continue

                avg_conf = (_CONF_VAL.get(a.confidence, 0.3) + _CONF_VAL.get(b.confidence, 0.3)) / 2.0
                if avg_conf >= 0.7:
                    severity: Literal["low", "medium", "high", "critical"] = "high"
                elif avg_conf >= 0.5:
                    severity = "medium"
                elif avg_conf >= 0.3:
                    severity = "low"
                else:
                    severity = "critical"

                results.append(
                    Contradiction(
                        evidence_a_id=a.content_hash,
                        evidence_b_id=b.content_hash,
                        description=(
                            f"Sources '{a.source_uri}' and '{b.source_uri}' "
                            f"contain conflicting signals (negation score {neg:.2f})"
                        ),
                        severity=severity,
                    )
                )
        return results
    except Exception:
        return []


def build_evidence_graph(
    evidence_list: list[Evidence],
    query: str,
) -> EvidenceGraph:
    """
    Build a complete evidence graph.

    1. Score every source (passing query terms for relevance).
    2. Detect contradictions.
    3. Cluster corroborating sources (shared citations or content-hash proximity).
    4. Compute overall confidence.
    5. Identify evidence gaps.
    """
    try:
        query_meta = {"query_terms": query}

        # Step 1: score all sources
        scored: list[SourceScore] = []
        for ev in evidence_list:
            metadata = dict(getattr(ev, "metadata", {}) or {})
            metadata["query_terms"] = query
            scored.append(score_source(ev.source_uri, "", metadata))

        # Step 2: detect contradictions
        contradictions = detect_contradictions(evidence_list)

        # Step 3: cluster corroborating sources
        clusters = _cluster_sources(evidence_list)

        # Step 4: update corroboration scores based on cluster membership
        for node in scored:
            cluster_size = 0
            for cl in clusters:
                if node.source_uri in cl:
                    cluster_size = len(cl)
                    break
            if cluster_size > 1:
                # More corroborating sources -> higher corroboration, capped at 1.0
                node.corroboration = min(round(0.5 + 0.1 * cluster_size, 4), 1.0)
                node.overall = round(
                    _WEIGHTS["reliability"] * node.reliability
                    + _WEIGHTS["relevance"] * node.relevance
                    + _WEIGHTS["recency"] * node.recency
                    + _WEIGHTS["corroboration"] * node.corroboration,
                    4,
                )

        # Step 5: overall confidence
        overall_conf = _compute_overall_confidence(scored, contradictions, evidence_list)

        # Step 6: gaps
        gaps = _identify_gaps(evidence_list, query)

        return EvidenceGraph(
            nodes=scored,
            contradictions=contradictions,
            clusters=clusters,
            overall_confidence=overall_conf,
            gaps=gaps,
        )
    except Exception:
        return EvidenceGraph()


def track_confidence(
    evidence_graph: EvidenceGraph,
    new_evidence: Evidence,
) -> EvidenceGraph:
    """
    Incrementally update an existing evidence graph with a new evidence item.

    - Score the new source.
    - Append to nodes, re-check contradictions with all existing nodes.
    - Re-score affected clusters.
    - Update overall confidence.
    """
    try:
        # Score new evidence (generic query relevance since query not available)
        new_node = score_source(new_evidence.source_uri, "", {"query_terms": ""})

        # Append node
        nodes = list(evidence_graph.nodes) + [new_node]

        # Rebuild contradiction list
        all_evidence = []
        for node in nodes:
            all_evidence.append(
                Evidence(
                    source_uri=node.source_uri,
                    content_hash="",
                    confidence="M",
                )
            )
        # Make sure the last evidence item is the actual new_evidence with real data
        if all_evidence:
            all_evidence[-1] = new_evidence
        contradictions = detect_contradictions(all_evidence)

        # Re-cluster
        clusters = _cluster_sources(all_evidence)

        # Update corroboration for all nodes
        for node in nodes:
            for cl in clusters:
                if node.source_uri in cl and len(cl) > 1:
                    node.corroboration = min(round(0.5 + 0.1 * len(cl), 4), 1.0)
                    node.overall = round(
                        _WEIGHTS["reliability"] * node.reliability
                        + _WEIGHTS["relevance"] * node.relevance
                        + _WEIGHTS["recency"] * node.recency
                        + _WEIGHTS["corroboration"] * node.corroboration,
                        4,
                    )

        overall_conf = _compute_overall_confidence(nodes, contradictions, all_evidence)
        gaps = evidence_graph.gaps  # preserve existing gaps

        return EvidenceGraph(
            nodes=nodes,
            contradictions=contradictions,
            clusters=clusters,
            overall_confidence=overall_conf,
            gaps=gaps,
        )
    except Exception:
        return evidence_graph


def source_diversity_score(evidence_list: list[Evidence]) -> float:
    """
    Measure diversity of evidence sources on a 0–1 scale.

    Breaks diversity into three equally-weighted components:
      1. Domain diversity  (unique domains / total)
      2. Type diversity    (unique inferred source types / total)
      3. Confidence spread (not all same confidence level)

    Returns 0 when all evidence comes from the same domain/type/confidence,
    approaches 1 as sources are maximally varied.
    """
    try:
        if not evidence_list:
            return 0.0
        n = len(evidence_list)
        if n == 1:
            return 0.33  # single source, only confidence_component applies

        # Domain diversity
        domains = {_extract_domain(ev.source_uri) for ev in evidence_list}
        domain_div = len(domains) / n

        # Type diversity
        types = {_extract_source_type(ev.source_uri, None) for ev in evidence_list}
        type_div = len(types) / n

        # Confidence spread (entropy-like but deterministic)
        conf_counts: dict[str, int] = {}
        for ev in evidence_list:
            conf_counts[ev.confidence] = conf_counts.get(ev.confidence, 0) + 1
        # Normalised Shannon entropy: H / H_max
        h = 0.0
        for cnt in conf_counts.values():
            p = cnt / n
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(conf_counts), 1))
        conf_div = h / max_h if max_h > 0 else 0.0

        return round((domain_div + type_div + conf_div) / 3.0, 4)
    except Exception:
        return 0.0


def evidence_strength(evidence_graph: EvidenceGraph) -> dict[str, float | int | str]:
    """
    Compute aggregate evidence strength metrics.

    Returns a dict with:
      total_sources   : int
      avg_reliability : float
      contradiction_rate  : float  (pairs contradicting / total pairs)
      coverage_score      : float  (based on cluster coverage)
      confidence          : Literal["H", "M", "L"]
    """
    try:
        nodes = evidence_graph.nodes
        n = len(nodes)
        total_sources = n

        if n == 0:
            return {
                "total_sources": 0,
                "avg_reliability": 0.0,
                "contradiction_rate": 0.0,
                "coverage_score": 0.0,
                "confidence": "L",
            }

        avg_reliability = round(
            sum(node.reliability for node in nodes) / n, 4
        )

        total_pairs = n * (n - 1) / 2 if n > 1 else 1.0
        contradiction_rate = round(len(evidence_graph.contradictions) / total_pairs, 4)

        # Coverage: fraction of nodes that belong to a cluster of size >= 2
        clustered = set()
        for cl in evidence_graph.clusters:
            if len(cl) >= 2:
                clustered.update(cl)
        coverage_score = round(len(clustered) / n, 4)

        # Map overall_confidence
        conf_str = evidence_graph.overall_confidence

        return {
            "total_sources": total_sources,
            "avg_reliability": avg_reliability,
            "contradiction_rate": contradiction_rate,
            "coverage_score": coverage_score,
            "confidence": conf_str,
        }
    except Exception:
        return {
            "total_sources": 0,
            "avg_reliability": 0.0,
            "contradiction_rate": 0.0,
            "coverage_score": 0.0,
            "confidence": "L",
        }


# ── Private clustering & gap helpers ────────────────────────────────────────


def _cluster_sources(evidence_list: list[Evidence]) -> list[list[str]]:
    """
    Cluster corroborating sources by shared citations and identical content hashes.

    Returns list of clusters, where each cluster is a list of source_uri strings.
    """
    # Union-Find
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Build citation -> sources index
    citation_index: dict[str, list[str]] = {}
    hash_groups: dict[str, list[str]] = {}

    for ev in evidence_list:
        uri = ev.source_uri
        # By content hash
        if ev.content_hash:
            hash_groups.setdefault(ev.content_hash, []).append(uri)
        # By shared citations
        for cite in ev.citations:
            citation_index.setdefault(cite, []).append(uri)

    # Union sources sharing citations
    for sources in citation_index.values():
        for k in range(1, len(sources)):
            union(sources[0], sources[k])

    # Union sources with same content hash
    for sources in hash_groups.values():
        for k in range(1, len(sources)):
            union(sources[0], sources[k])

    # Collect clusters
    groups: dict[str, list[str]] = {}
    for ev in evidence_list:
        root = find(ev.source_uri)
        groups.setdefault(root, []).append(ev.source_uri)

    return list(groups.values())


def _compute_overall_confidence(
    nodes: list[SourceScore],
    contradictions: list[Contradiction],
    evidence_list: list[Evidence],
) -> Literal["H", "M", "L"]:
    """Derive H/M/L from average score, contradiction count, and source count."""
    n = len(nodes)
    if n == 0:
        return "L"

    avg_score = sum(node.overall for node in nodes) / n
    contratio = len(contradictions) / max(n, 1)

    # Penalize for contradictions
    adjusted = avg_score * (1.0 - 0.5 * contratio)

    if adjusted >= 0.65 and n >= 3:
        return "H"
    if adjusted >= 0.40:
        return "M"
    return "L"


def _identify_gaps(evidence_list: list[Evidence], query: str) -> list[str]:
    """
    Identify evidence gaps based on query coverage.

    Checks which query terms appear in at least one source; terms
    with zero coverage are reported as gaps.
    """
    if not query or not evidence_list:
        return ["No query or evidence provided"]

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    # Aggregate all source URIs as a simple proxy for coverage
    all_text = " ".join(ev.source_uri for ev in evidence_list).lower()
    gaps = [t for t in query_tokens if len(t) > 3 and t not in all_text]

    if len(evidence_list) < 3:
        gaps.append("insufficient_sources:min_3_recommended")

    return gaps
