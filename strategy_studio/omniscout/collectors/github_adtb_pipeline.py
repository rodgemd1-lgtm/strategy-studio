#!/usr/bin/env python3
"""
OmniScout → ADTB+ Batch Signal Pipeline
Extracts signals from cloned GitHub repos and batch-inserts into adtb_signals.
Uses chunked inserts for speed.
"""

import os, sys, json, uuid, re
from datetime import datetime, timezone
from pathlib import Path

REPOS_DIR = os.path.expanduser("~/rig-lab/omniscout-external-repos")

sys.path.insert(0, os.path.expanduser("~/Desktop/Startup-Intelligence-OS/benchmarks/mirrormind/evaluator"))
from db_helper import sb_insert, sb_batch_insert, sb_count

def extract_signals_from_repo(repo_name: str, repo_path: str) -> list:
    """Extract weak signals from a cloned GitHub repo."""
    signals = []
    repo_path = Path(repo_path)
    if not repo_path.exists():
        return signals

    # Read README
    for readme in repo_path.glob("README*"):
        try:
            text = readme.read_text(errors="ignore")
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 30 and len(line) < 300:
                    if line.startswith('#') and len(line) < 60:
                        title = line.lstrip('#').strip()
                        if title and not title.lower().startswith(('table of contents', 'license', 'contributing', 'acknowledg', 'getting started', 'installation')):
                            signals.append(f"[{repo_name}] {title}")
                    elif line.startswith(('- ', '* ', '• ')):
                        content = line[2:].strip()
                        if len(content) > 20:
                            signals.append(f"[{repo_name}] {content[:200]}")
        except:
            break  # Only read first README

    # Key capability files
    key_files = {
        'Dockerfile': 'containerized',
        'docker-compose.yml': 'multi-service',
        'package.json': 'nodejs',
        'pyproject.toml': 'python-package',
        'requirements.txt': 'python-app',
    }
    for fname, cap in key_files.items():
        if (repo_path / fname).exists():
            signals.append(f"[{repo_name}] Has {fname} — {cap}")

    # Scan Python files for capability patterns
    for py_file in list(repo_path.glob("*.py"))[:3]:
        try:
            content = py_file.read_text(errors="ignore")[:2000].lower()
            for pattern, label in [('arxiv', 'arxiv'), ('requests.get', 'web_api'), ('agent', 'agent_capability'),
                                    ('prediction', 'prediction'), ('forecast', 'forecasting'), ('scraper', 'scraping'),
                                    ('benchmark', 'benchmarking'), ('evaluation', 'evaluation'), ('swarm', 'swarm')]:
                if pattern in content:
                    signals.append(f"[{repo_name}] {py_file.name} → {label}")
        except:
            pass

    return signals


def classify_domain(repo_name: str) -> str:
    n = repo_name.lower()
    if any(k in n for k in ['osint', 'intelligence', 'search']): return 'osint'
    if any(k in n for k in ['predict', 'market', 'forecast', 'betting']): return 'prediction_markets'
    if any(k in n for k in ['agent', 'ai_agent']): return 'ai_agents'
    if any(k in n for k in ['arxiv', 'paper', 'research', 'academic']): return 'academic'
    if any(k in n for k in ['knowledge', 'memory', 'rag']): return 'knowledge'
    if any(k in n for k in ['bayesian', 'conformal', 'modeling']): return 'forecasting'
    if any(k in n for k in ['agriculture', 'motion']): return 'domain_specific'
    return 'general'


def run_pipeline():
    repos = sorted([d for d in os.listdir(REPOS_DIR)
                    if os.path.isdir(os.path.join(REPOS_DIR, d)) and not d.startswith('.')])

    all_signals = []
    for repo_name in repos:
        repo_path = os.path.join(REPOS_DIR, repo_name)
        try:
            sigs = extract_signals_from_repo(repo_name, repo_path)
            domain = classify_domain(repo_name)
            for claim in sigs:
                all_signals.append({
                    "claim": claim[:500],
                    "domain": domain,
                    "signal_type": "weak_signal" if claim.startswith(f"[{repo_name}]") and '→' not in claim else "capability_signal",
                    "confidence": 0.55 if '→' in claim else 0.4,
                })
        except:
            pass

    # Deduplicate
    seen = set()
    unique = []
    for s in all_signals:
        key = s["claim"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(s)

    print(f"Extracted {len(unique)} unique signals from {len(repos)} repos")

    # Batch insert into adtb_signals
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for s in unique:
        rows.append({
            "id": str(uuid.uuid4()),
            "signal_type": s["signal_type"],
            "domain": s["domain"],
            "extracted_claim": s["claim"],
            "source_url": "https://github.com/omniscout-scan",
            "anomaly_score": s["confidence"],
            "entities": [],
            "extracted_at": now,
            "metadata": {"pipeline": "omniscout_github_v1", "batch_size": len(unique)}
        })

    # Insert in chunks of 50
    total = 0
    for i in range(0, len(rows), 50):
        chunk = rows[i:i+50]
        result = sb_insert("adtb_signals", chunk)
        if result:
            total += len(result)
        print(f"  Chunk {i//50 + 1}: inserted {len(result) if result else 0}/{len(chunk)}")

    # Verify
    count = sb_count("adtb_signals")
    print(f"\n✓ Total signals in adtb_signals: {count}")
    print(f"✓ New signals added: {total}")
    return total


if __name__ == "__main__":
    run_pipeline()
