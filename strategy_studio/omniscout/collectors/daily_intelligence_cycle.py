#!/usr/bin/env python3
"""
OmniScout Daily Intelligence Cycle
Runs every hour via Hermes cron.
1. Scans cloned GitHub repos for new signals → ADTB+
2. Fetches recent arXiv papers → HEB+ evidence
3. Runs HEB+ cognitive security scan
4. Updates MirrorMind dashboard cache
5. Logs results
"""

import os, sys, json, subprocess
from datetime import datetime, timezone

SIO = os.path.expanduser("~/Desktop/Startup-Intelligence-OS")
LOG_DIR = os.path.expanduser("~/.hermes/cron/output/omniscout-daily")
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

def run_pipeline():
    results = {"started": datetime.now(timezone.utc).isoformat()}

    # Step 1: GitHub → ADTB+ signals
    log("Step 1: Scanning GitHub repos for signals...")
    try:
        r = subprocess.run(
            f"cd {SIO} && python3 rig/omniscout/collectors/github_adtb_pipeline.py",
            shell=True, capture_output=True, text=True, timeout=180
        )
        results["github_pipeline"] = r.stdout[-500:] if r.stdout else "(no output)"
        log(f"  GitHub pipeline done (rc={r.returncode})")
    except Exception as e:
        results["github_pipeline_error"] = str(e)[:200]
        log(f"  GitHub pipeline error: {e}")

    # Step 2: arXiv → HEB+ evidence
    log("Step 2: Fetching arXiv papers...")
    try:
        r = subprocess.run(
            f"cd {SIO} && python3 rig/omniscout/collectors/arxiv_heb_pipeline.py --max 10",
            shell=True, capture_output=True, text=True, timeout=120
        )
        results["arxiv_pipeline"] = r.stdout[-500:] if r.stdout else "(no output)"
        log(f"  arXiv pipeline done (rc={r.returncode})")
    except Exception as e:
        results["arxiv_pipeline_error"] = str(e)[:200]
        log(f"  arXiv pipeline error: {e}")

    # Step 3: HEB+ cognitive security scan
    log("Step 3: Running HEB+ security scan...")
    try:
        r = subprocess.run(
            f"cd {SIO} && python3 benchmarks/mirrormind/mirrormind.py heb run",
            shell=True, capture_output=True, text=True, timeout=120
        )
        results["heb_scan"] = r.stdout[-500:] if r.stdout else "(no output)"
        log(f"  HEB+ scan done (rc={r.returncode})")
    except Exception as e:
        results["heb_scan_error"] = str(e)[:200]
        log(f"  HEB+ scan error: {e}")

    # Step 4: Refresh MirrorMind dashboard cache
    log("Step 4: Refreshing MirrorMind dashboard...")
    try:
        r = subprocess.run(
            f"cd {SIO} && python3 benchmarks/mirrormind/scripts/dashboard_server.py &",
            shell=True, capture_output=True, text=True, timeout=5
        )
        log("  Dashboard server restarted")
    except:
        pass  # Server likely already running

    results["completed"] = datetime.now(timezone.utc).isoformat()

    # Write log
    log_file = os.path.join(LOG_DIR, f"cycle_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    log(f"Cycle complete. Log: {log_file}")
    return results

if __name__ == "__main__":
    results = run_pipeline()
    print(json.dumps(results, indent=2, default=str))
