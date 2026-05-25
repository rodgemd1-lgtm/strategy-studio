"""
rig_strategy_studio.py — Strategy Studio entrypoint

Runs strategy synthesis, market wargame, competitor/client intelligence,
prediction crux, falsification, and consensus delta operations.

Usage:
    python3 -m services.rig_commands.rig_strategy_studio synthesize --query "..."
    python3 -m services.rig_commands.rig_strategy_studio wargame --competitor "..."
    python3 -m services.rig_commands.rig_strategy_studio forecast --question "..."
    python3 -m services.rig_commands.rig_strategy_studio audit

Sources:
    - QNAP LakeOS (200K chunks, 3.5M graph edges)
    - recall.it strategy cards (118 cards, backend.getrecall.ai/api/v1)
    - Local artifacts (startup-os/artifacts, control-plane)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import urllib.request
import urllib.error

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]  # Startup-Intelligence-OS/
LAKEOS_CLI = Path("/Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py")
LAKEOS_REST = "http://127.0.0.1:8788"
RECALL_API_BASE = "https://backend.getrecall.ai/api/v1"
RECALL_INDEX = ROOT / "artifacts/recall/index.json"
RECALL_STRATEGY_CARDS = ROOT / "artifacts/recall/strategy_cards"
QNAP_LAKE = Path("/Users/mikerodgers/mnt/RIGQNAP-RIGLake-LAN/RIG/phronema/lake")

# ── Auth ───────────────────────────────────────────────────────────────
def _recall_key() -> str:
    key = os.environ.get("RECALL_API_KEY", "")
    if not key:
        print("ERROR: RECALL_API_KEY env var required", file=sys.stderr)
        sys.exit(2)
    return key

# ── HTTP helpers ───────────────────────────────────────────────────────
def _http_get(url: str, key: str | None = None, timeout: int = 30) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "rig-strategy-studio/1.0"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

# ── LakeOS query ───────────────────────────────────────────────────────
def lakeos_query(query: str, task: str = "strategy", agent: str = "hermes") -> dict:
    """Query LakeOS via CLI (deterministic, no REST dependency)."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(LAKEOS_CLI),
         "agent-query", query,
         "--task", task,
         "--agent", agent],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": result.stdout[:500]}

def lakeos_search(query: str, limit: int = 10) -> dict:
    """Search LakeOS RAG index directly."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(LAKEOS_CLI),
         "search", query,
         "--limit", str(limit)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": result.stdout[:500]}

# ── Recall.it ──────────────────────────────────────────────────────────
def recall_search(query: str, limit: int = 20) -> list[dict]:
    """Search recall.it for strategy-relevant cards."""
    key = _recall_key()
    resp = _http_get(f"{RECALL_API_BASE}/search?q={urlencode({'': query})}&limit={limit}", key)
    return resp.get("documents", [])

def recall_fetch_card(card_id: str) -> dict:
    """Fetch full card content from recall.it."""
    key = _recall_key()
    return _http_get(f"{RECALL_API_BASE}/cards/{card_id}", key)

def recall_list_strategy_cards() -> list[dict]:
    """List all locally cached strategy cards."""
    cards = []
    if RECALL_STRATEGY_CARDS.exists():
        for f in RECALL_STRATEGY_CARDS.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                cards.append({
                    "id": data.get("id", f.stem),
                    "title": data.get("title", ""),
                    "tags": [t.get("name", "") for t in data.get("tags", [])],
                    "content_preview": str(data.get("content", ""))[:200],
                })
            except Exception:
                pass
    return cards

# ── QNAP packet reader ─────────────────────────────────────────────────
def read_qnap_packet(packet_name: str) -> dict:
    """Read a B-packet from the QNAP lake."""
    engine_dir = QNAP_LAKE / "a3-a4-workflow-engine/a3a4-engine-20260524T211522Z"
    path = engine_dir / packet_name
    if not path.exists():
        return {"ok": False, "error": f"Packet not found: {packet_name}"}
    return {"ok": True, "data": json.loads(path.read_text())}

# ── Strategy operations ────────────────────────────────────────────────
def op_synthesize(query: str, depth: str = "standard") -> dict:
    """
    Strategy Synthesis (B29): Combine LakeOS + recall evidence into ranked options.
    """
    print(f"[synthesize] Query: {query}")
    print(f"[synthesize] Depth: {depth}")

    # 1. LakeOS evidence
    lake_result = lakeos_query(query, task="strategy_synthesis")
    print(f"[synthesize] LakeOS: {lake_result.get('retrieval', {}).get('results', []).__len__()} results")

    # 2. Recall strategy cards
    recall_results = recall_search(query, limit=20)
    print(f"[synthesize] Recall: {len(recall_results)} cards")

    # 3. Read B29 packet for methodology
    packet = read_qnap_packet("B29-strategy_synthesist_packet.json")
    iqrsqpi = packet.get("data", {}).get("iqrsqpi", [])

    # 4. Build synthesis
    synthesis = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "iqrsqpi_stages": iqrsqpi,
        "lakeos_evidence": lake_result.get("retrieval", {}).get("results", []),
        "recall_cards": [{"id": r.get("card_id"), "title": r.get("title")} for r in recall_results[:10]],
        "strategy_options": [],
        "confidence": "low",
        "missing_evidence": [],
    }

    # Determine confidence from evidence volume
    total_evidence = len(lake_result.get("retrieval", {}).get("results", [])) + len(recall_results)
    if total_evidence >= 10:
        synthesis["confidence"] = "medium"
    if total_evidence >= 20:
        synthesis["confidence"] = "high"

    if total_evidence < 5:
        synthesis["missing_evidence"].append("Insufficient indexed evidence for this query. Consider: web research, competitor scrape, or manual card creation.")

    return synthesis

def op_wargame(competitor: str, scenario: str = "default") -> dict:
    """
    Market Wargame (B36): Model competitor moves and RIG responses.
    """
    print(f"[wargame] Competitor: {competitor}")
    print(f"[wargame] Scenario: {scenario}")

    # Read B36 packet
    packet = read_qnap_packet("B36-market_wargame_packet.json")

    # Search for competitor in LakeOS + recall
    lake_result = lakeos_search(f"competitor {competitor}", limit=10)
    recall_results = recall_search(f"competitor {competitor}", limit=10)

    return {
        "competitor": competitor,
        "scenario": scenario,
        "packet_methodology": packet.get("data", {}).get("iqrsqpi", []),
        "lakeos_intel": lake_result.get("results", []),
        "recall_intel": [{"id": r.get("card_id"), "title": r.get("title")} for r in recall_results[:10]],
        "wargame_scenarios": [],
        "rigg_responses": [],
        "falsification_required": True,
    }

def op_forecast(question: str, horizon: str = "6m") -> dict:
    """
    Prediction Crux (B34): Turn strategic question into forecast variables.
    """
    print(f"[forecast] Question: {question}")
    print(f"[forecast] Horizon: {horizon}")

    packet = read_qnap_packet("B34-prediction_crux_packet.json")
    lake_result = lakeos_search(question, limit=15)
    recall_results = recall_search(question, limit=15)

    return {
        "question": question,
        "horizon": horizon,
        "packet_methodology": packet.get("data", {}).get("iqrsqpi", []),
        "lakeos_evidence": lake_result.get("results", []),
        "recall_evidence": [{"id": r.get("card_id"), "title": r.get("title")} for r in recall_results[:10]],
        "forecast_variables": [],
        "cruxes": [],
        "brier_tracking": True,
    }

def op_audit() -> dict:
    """
    Audit: Check strategy studio health — sources, packets, cards, LakeOS status.
    """
    print("[audit] Running strategy studio audit...")

    # LakeOS status
    lake_status = lakeos_query("status check", task="audit")

    # QNAP packets
    packets_ok = {}
    for name in ["B29", "B36", "B42", "B41", "B34", "B33", "B31"]:
        pkt = read_qnap_packet(f"{name}-*_packet.json".replace("*", "strategy_synthesist" if name=="B29" else "market_wargame" if name=="B36" else "competitor_intelligence" if name=="B42" else "client_intelligence" if name=="B41" else "prediction_crux" if name=="B34" else "falsification" if name=="B33" else "consensus_delta"))
        packets_ok[name] = pkt.get("ok", False)

    # Recall cards
    strategy_cards = recall_list_strategy_cards()

    # Registration
    reg_path = ROOT / "startup-os/runtime/studios/strategy-studio/studio-registration.json"
    reg_ok = reg_path.exists()

    # Build spec
    spec_path = ROOT / "startup-os/runtime/studios/strategy-studio/build_spec.yaml"
    spec_ok = spec_path.exists()

    audit = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "studio": "strategy-studio",
        "status": "healthy" if all(packets_ok.values()) and reg_ok else "degraded",
        "sources": {
            "lakeos": {"ok": lake_status.get("ok", False), "status": lake_status},
            "qnap_packets": packets_ok,
            "recall_strategy_cards": len(strategy_cards),
            "recall_api": "configured" if os.environ.get("RECALL_API_KEY") else "MISSING_KEY",
        },
        "artifacts": {
            "registration": reg_ok,
            "build_spec": spec_ok,
            "goal_cards": (ROOT / "startup-os/runtime/studios/strategy-studio/goals-queue-dirs/strategy-studio.json").exists(),
        },
        "recommendations": [],
    }

    if not all(packets_ok.values()):
        audit["recommendations"].append("Some QNAP B-packets are missing or unreadable. Check mount.")
    if len(strategy_cards) < 50:
        audit["recommendations"].append(f"Only {len(strategy_cards)} strategy cards cached. Run: RECALL_API_KEY=sk_... python3 scripts/book/pull_recall.py")
    if not os.environ.get("RECALL_API_KEY"):
        audit["recommendations"].append("RECALL_API_KEY not in environment. Set it for recall.it access.")

    return audit

# ── CLI ────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="RIG Strategy Studio")
    sub = parser.add_subparsers(dest="command")

    # synthesize
    p_synth = sub.add_parser("synthesize", help="Strategy synthesis from evidence")
    p_synth.add_argument("--query", required=True, help="Strategic question or topic")
    p_synth.add_argument("--depth", default="standard", choices=["quick", "standard", "deep"])

    # wargame
    p_wargame = sub.add_parser("wargame", help="Market wargame simulation")
    p_wargame.add_argument("--competitor", required=True, help="Competitor name or domain")
    p_wargame.add_argument("--scenario", default="default", help="Scenario type")

    # forecast
    p_forecast = sub.add_parser("forecast", help="Prediction crux / forecast")
    p_forecast.add_argument("--question", required=True, help="Strategic question to forecast")
    p_forecast.add_argument("--horizon", default="6m", help="Forecast horizon (3m, 6m, 12m, 2y)")

    # audit
    sub.add_parser("audit", help="Run studio health audit")

    # list-cards
    sub.add_parser("list-cards", help="List cached strategy cards")

    args = parser.parse_args()

    if args.command == "synthesize":
        result = op_synthesize(args.query, args.depth)
    elif args.command == "wargame":
        result = op_wargame(args.competitor, args.scenario)
    elif args.command == "forecast":
        result = op_forecast(args.question, args.horizon)
    elif args.command == "audit":
        result = op_audit()
    elif args.command == "list-cards":
        result = {"strategy_cards": recall_list_strategy_cards()}
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, indent=2, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
