"""
swarm_bipolar.py — RIG Sovereign Comms Engine · 12-Persona Bipolar Prediction Swarm
Lane: H4-BUILD-COMMS-ENGINES | Card: BC-COMMS-DEV-V2

12-persona prediction swarm with Brier-calibrated weights.
Persistent weight storage: services/memory/brier_calibration.db

No network calls. stdlib only. Safe for any input.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 12 Personas
# ---------------------------------------------------------------------------
PERSONAS: list[str] = [
    "Founder", "CFO", "CMO", "Operator", "Skeptic", "Engineer",
    "Designer", "Customer", "Competitor", "Investor", "Press", "Mike-himself",
]

_PUBLISH_THRESHOLD: float = 0.55
_LEARNING_RATE: float = 0.10
_WEIGHT_FLOOR: float = 0.10
_DEFAULT_WEIGHT: float = 1.0

# ---------------------------------------------------------------------------
# Brier calibration DB path
# ---------------------------------------------------------------------------

def _brier_db_path() -> Path:
    """Locate services/memory/brier_calibration.db relative to this file."""
    base = Path(__file__).resolve().parent
    # Walk up to repo root (find CLAUDE.md)
    candidate = base
    for _ in range(8):
        if (candidate / "CLAUDE.md").exists():
            return candidate / "services" / "memory" / "brier_calibration.db"
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return base.parent.parent / "services" / "memory" / "brier_calibration.db"


def _ensure_brier_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS persona_weights (
            persona          TEXT PRIMARY KEY,
            current_weight   REAL NOT NULL,
            last_updated_iso TEXT NOT NULL,
            update_count     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS outcomes (
            outcome_id           TEXT PRIMARY KEY,
            run_id               TEXT NOT NULL,
            draft_hash_first8    TEXT NOT NULL,
            channel              TEXT NOT NULL,
            predicted_avg        REAL NOT NULL,
            actual_engagement    REAL,
            measured_at_iso      TEXT,
            brier_loss           REAL
        );
    """)
    conn.commit()


def _get_brier_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or _brier_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_brier_schema(conn)
    return conn


def _load_weights(db_path: Path | None = None) -> dict[str, float]:
    """Load per-persona weights from brier_calibration.db. Defaults to 1.0."""
    try:
        conn = _get_brier_conn(db_path)
        rows = conn.execute("SELECT persona, current_weight FROM persona_weights").fetchall()
        conn.close()
        weights = {r["persona"]: float(r["current_weight"]) for r in rows}
    except Exception:
        weights = {}
    # Fill any missing personas with default
    for p in PERSONAS:
        if p not in weights:
            weights[p] = _DEFAULT_WEIGHT
    return weights


def _save_weights(weights: dict[str, float], db_path: Path | None = None) -> None:
    """Persist updated weights to brier_calibration.db."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        conn = _get_brier_conn(db_path)
        for persona, w in weights.items():
            conn.execute(
                """INSERT INTO persona_weights (persona, current_weight, last_updated_iso, update_count)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(persona) DO UPDATE SET
                     current_weight=excluded.current_weight,
                     last_updated_iso=excluded.last_updated_iso,
                     update_count=persona_weights.update_count + 1""",
                (persona, round(w, 6), now),
            )
        conn.commit()
        conn.close()
    except Exception:
        pass  # DB write failure is non-fatal


# ---------------------------------------------------------------------------
# Editorial doctrine signal phrases (for Mike-himself persona)
# ---------------------------------------------------------------------------
_MIKE_SIGNAL_PHRASES: list[str] = [
    "proof", "shipped", "measured", "deployed", "operator", "rig",
    "mechanism", "we tested", "actual", "result", "revenue", "leakage",
    "jake", "mike", "rodgers", "intelligence", "builder",
]

_BANNED_PHRASES: list[str] = [
    "game-changer", "synergy", "leverage", "best practices", "thought leader",
    "guru", "paradigm", "disruption", "ecosystem", "scalable",
    "fast-paced", "innovative", "cutting-edge", "visionary",
]


# ---------------------------------------------------------------------------
# Per-persona scoring heuristics
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


def _word_count(text: str) -> int:
    return len(text.split())


def _has_keywords(norm: str, keywords: list[str]) -> float:
    """Fraction of keywords present, scaled to 0–1."""
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in norm)
    return min(1.0, hits / len(keywords) * 2)


def _score_founder(norm: str) -> float:
    kw = ["revenue", "shipped", "built", "rig", "startup", "raised",
          "mrr", "arr", "grew", "launched", "proof", "measured"]
    breakthrough = len(re.findall(
        r"\b(first|new|breakthrough|announced|launched|revealed)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.7 + min(0.3, breakthrough * 0.1))


def _score_cfo(norm: str) -> float:
    kw = ["revenue", "cost", "burn", "runway", "roi", "profit",
          "margin", "leakage", "recovery", "payback", "dollar",
          "savings", "loss", "gain"]
    numbers = len(re.findall(r"\$[\d,]+|\b\d+%|\b\d+x\b", norm))
    return min(1.0, _has_keywords(norm, kw) * 0.6 + min(0.4, numbers * 0.08))


def _score_cmo(norm: str) -> float:
    kw = ["brand", "audience", "content", "post", "reach",
          "positioning", "message", "pipeline", "engagement", "viral"]
    virality = len(re.findall(
        r"\b(spread|share|viral|narrative|story|hook)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.7 + min(0.3, virality * 0.1))


def _score_operator(norm: str) -> float:
    kw = ["shipped", "deployed", "workflow", "automation", "system",
          "pipeline", "ops", "process", "built", "run", "configured"]
    how = len(re.findall(
        r"\b(how (we|i|it)|step|configure|install|run|execute|wire)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.65 + min(0.35, how * 0.07))


def _score_skeptic(norm: str) -> float:
    kw = ["proof", "measured", "actual", "evidence", "data",
          "tested", "result", "verified", "confirmed", "showed"]
    evidence = len(re.findall(r"\b\d[\d,.%$kmb]*\b", norm))
    return min(1.0, _has_keywords(norm, kw) * 0.6 + min(0.4, evidence * 0.06))


def _score_engineer(norm: str) -> float:
    kw = ["code", "api", "deploy", "sqlite", "python", "service",
          "architecture", "function", "query", "endpoint", "schema",
          "database", "test", "module"]
    tech = len(re.findall(
        r"\b(import|def |class |function|async|await|sql|json|yaml|http)\b",
        norm,
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.65 + min(0.35, tech * 0.08))


def _score_designer(norm: str) -> float:
    kw = ["design", "ui", "visual", "layout", "motion", "figma",
          "studio", "color", "spacing", "font", "style", "aesthetic"]
    visual = len(re.findall(
        r"\b(look|feel|space|white|dark|light|clean|minimal)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.7 + min(0.3, visual * 0.07))


def _score_customer(norm: str) -> float:
    kw = ["problem", "solution", "result", "saved", "recovered",
          "worked", "fixed", "pain", "frustration", "finally", "helped"]
    empathy = len(re.findall(r"\b(you|your|you've|you're|when you)\b", norm))
    return min(1.0, _has_keywords(norm, kw) * 0.65 + min(0.35, empathy * 0.04))


def _score_competitor(norm: str) -> float:
    kw = ["market", "position", "advantage", "faster", "better",
          "cheaper", "alternative", "versus", "compared", "outperform"]
    position = len(re.findall(
        r"\b(than|over|unlike|instead of|replace|beat)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.65 + min(0.35, position * 0.08))


def _score_investor(norm: str) -> float:
    kw = ["growth", "revenue", "traction", "mrr", "arr", "deal",
          "pipeline", "tam", "cac", "ltv", "payback", "unit economics"]
    financial = len(re.findall(r"\$[\d,]+|\b\d+%|\b\d+x|\barr\b|\bmrr\b", norm))
    return min(1.0, _has_keywords(norm, kw) * 0.6 + min(0.4, financial * 0.08))


def _score_press(norm: str) -> float:
    kw = ["first", "new", "announced", "launched", "revealed",
          "breakthrough", "according", "source", "said", "story"]
    headline_quality = len(re.findall(
        r"\b(why|how|what|the case for|the truth about)\b", norm
    ))
    return min(1.0, _has_keywords(norm, kw) * 0.65 + min(0.35, headline_quality * 0.08))


def _score_mike(norm: str) -> float:
    """Signal-phrase density from editorial doctrine + Mike-narrative resonance."""
    # Check for banned phrases (reduces score)
    banned_hits = sum(1 for b in _BANNED_PHRASES if b in norm)
    signal_hits = sum(1 for s in _MIKE_SIGNAL_PHRASES if s in norm)
    # Mike-narrative
    mike_narrative = len(re.findall(
        r"\b(rig|jake|mike|james|rodgers|avis|operator|shipped|proof)\b", norm
    ))
    base = _has_keywords(norm, _MIKE_SIGNAL_PHRASES) * 0.7
    narrative_boost = min(0.3, mike_narrative * 0.05)
    ban_penalty = min(0.5, banned_hits * 0.15)
    return max(0.0, min(1.0, base + narrative_boost - ban_penalty))


_PERSONA_SCORERS = {
    "Founder":    _score_founder,
    "CFO":        _score_cfo,
    "CMO":        _score_cmo,
    "Operator":   _score_operator,
    "Skeptic":    _score_skeptic,
    "Engineer":   _score_engineer,
    "Designer":   _score_designer,
    "Customer":   _score_customer,
    "Competitor": _score_competitor,
    "Investor":   _score_investor,
    "Press":      _score_press,
    "Mike-himself": _score_mike,
}

# Channel affinity base modifiers
_CHANNEL_AFFINITY: dict[str, dict[str, float]] = {
    "linkedin-post":      {"Founder": 0.8, "CFO": 0.6, "CMO": 0.75, "Operator": 0.8,
                           "Skeptic": 0.55, "Engineer": 0.5, "Designer": 0.45,
                           "Customer": 0.55, "Competitor": 0.7, "Investor": 0.65,
                           "Press": 0.6, "Mike-himself": 0.85},
    "substack":           {"Founder": 0.7, "CFO": 0.5, "CMO": 0.6, "Operator": 0.65,
                           "Skeptic": 0.7, "Engineer": 0.65, "Designer": 0.45,
                           "Customer": 0.55, "Competitor": 0.5, "Investor": 0.65,
                           "Press": 0.8, "Mike-himself": 0.85},
    "email-cold":         {"Founder": 0.5, "CFO": 0.55, "CMO": 0.45, "Operator": 0.6,
                           "Skeptic": 0.3, "Engineer": 0.4, "Designer": 0.35,
                           "Customer": 0.5, "Competitor": 0.2, "Investor": 0.45,
                           "Press": 0.35, "Mike-himself": 0.6},
    "x-twitter":          {"Founder": 0.65, "CFO": 0.4, "CMO": 0.6, "Operator": 0.55,
                           "Skeptic": 0.5, "Engineer": 0.6, "Designer": 0.5,
                           "Customer": 0.45, "Competitor": 0.6, "Investor": 0.55,
                           "Press": 0.65, "Mike-himself": 0.7},
    "morning-brief-tile": {"Founder": 0.9, "CFO": 0.85, "CMO": 0.8, "Operator": 0.9,
                           "Skeptic": 0.7, "Engineer": 0.75, "Designer": 0.6,
                           "Customer": 0.5, "Competitor": 0.4, "Investor": 0.8,
                           "Press": 0.5, "Mike-himself": 0.95},
}
_DEFAULT_AFFINITY: dict[str, float] = {p: 0.5 for p in PERSONAS}


def _score_persona(norm: str, channel: str, persona: str) -> float:
    affinity_map = _CHANNEL_AFFINITY.get(channel, _DEFAULT_AFFINITY)
    channel_base = affinity_map.get(persona, 0.5)
    content_score = _PERSONA_SCORERS[persona](norm)
    # Blend: 50% channel affinity, 50% content-specific score
    raw = channel_base * 0.5 + content_score * 0.5
    return round(max(0.0, min(1.0, raw)), 4)


# ---------------------------------------------------------------------------
# Public: score
# ---------------------------------------------------------------------------

def score(
    draft: str,
    channel: str,
    persona_weights: dict[str, float] | None = None,
    *,
    db_path: Path | None = None,
) -> dict:
    """
    Run 12-persona bipolar prediction swarm.

    Returns:
        {
          "persona_scores": {persona: float (0-1)},
          "weighted_avg": float,
          "weighted_avg_normalized": float,
          "brier_baseline": float,
          "would_publish": bool,
          "std_dev": float,
          "unanimity_score": float,
        }
    """
    if not isinstance(draft, str):
        draft = ""
    norm = _normalise(draft)

    weights = persona_weights if persona_weights is not None else _load_weights(db_path)
    active_weights = {p: max(_WEIGHT_FLOOR, weights.get(p, _DEFAULT_WEIGHT)) for p in PERSONAS}

    persona_scores: dict[str, float] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for persona in PERSONAS:
        ps = _score_persona(norm, channel, persona)
        persona_scores[persona] = ps
        w = active_weights[persona]
        weighted_sum += ps * w
        weight_total += w

    brier_baseline = round(weight_total, 4)
    weighted_avg = round(weighted_sum / max(1e-6, weight_total), 4)
    would_publish = weighted_avg >= _PUBLISH_THRESHOLD

    # Std dev of persona scores (unweighted, measures disagreement)
    scores_list = list(persona_scores.values())
    mean_s = sum(scores_list) / len(scores_list)
    variance = sum((s - mean_s) ** 2 for s in scores_list) / len(scores_list)
    std_dev = round(variance ** 0.5, 4)
    unanimity_score = round(max(0.0, 1.0 - std_dev * 2), 4)

    return {
        "persona_scores": persona_scores,
        "weighted_avg": weighted_avg,
        "weighted_avg_normalized": weighted_avg,  # already 0-1
        "brier_baseline": brier_baseline,
        "would_publish": would_publish,
        "std_dev": std_dev,
        "unanimity_score": unanimity_score,
    }


# ---------------------------------------------------------------------------
# Public: record_outcome (feed back actual engagement for Brier update)
# ---------------------------------------------------------------------------

def record_outcome(
    run_id: str,
    draft: str,
    channel: str,
    predicted_avg: float,
    actual_engagement: float,
    *,
    db_path: Path | None = None,
) -> str:
    """
    Record an observed engagement outcome for Brier calibration.

    actual_engagement: 0-1 normalised post-fact engagement signal.
    Returns outcome_id.
    """
    brier_loss = round((predicted_avg - actual_engagement) ** 2, 6)
    draft_hash = hashlib.sha256(draft.encode("utf-8", errors="replace")).hexdigest()[:8]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    outcome_id = str(uuid.uuid4())
    try:
        conn = _get_brier_conn(db_path)
        conn.execute(
            """INSERT INTO outcomes
               (outcome_id, run_id, draft_hash_first8, channel,
                predicted_avg, actual_engagement, measured_at_iso, brier_loss)
               VALUES (?,?,?,?,?,?,?,?)""",
            (outcome_id, run_id, draft_hash, channel,
             round(predicted_avg, 6), round(actual_engagement, 6),
             now, brier_loss),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return outcome_id


# ---------------------------------------------------------------------------
# Public: weekly_brier_update
# ---------------------------------------------------------------------------

def weekly_brier_update(*, db_path: Path | None = None) -> dict:
    """
    Read outcomes from last 7 days. For each persona, compute Brier-loss-weighted
    weight update: new_weight = old_weight × (1 - learning_rate × avg_loss).
    Floor at 0.1. Persist updated weights.

    Returns summary dict of weight changes.
    """
    from datetime import timedelta
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        conn = _get_brier_conn(db_path)
        rows = conn.execute(
            "SELECT * FROM outcomes WHERE measured_at_iso >= ?", (cutoff,)
        ).fetchall()
        conn.close()
    except Exception:
        rows = []

    if not rows:
        return {
            "status": "no_outcomes",
            "outcomes_evaluated": 0,
            "weight_changes": {},
            "note": "No outcomes in last 7 days. Weights unchanged.",
        }

    # Compute average Brier loss per persona (simplified: global loss applied per-persona)
    # In a full implementation, track per-persona predictions; here use global average
    losses = [float(r["brier_loss"] or 0.0) for r in rows]
    avg_loss = sum(losses) / max(1, len(losses))

    old_weights = _load_weights(db_path)
    new_weights: dict[str, float] = {}
    changes: dict[str, dict] = {}

    for persona in PERSONAS:
        old_w = old_weights.get(persona, _DEFAULT_WEIGHT)
        new_w = max(_WEIGHT_FLOOR, old_w * (1.0 - _LEARNING_RATE * avg_loss))
        new_weights[persona] = round(new_w, 6)
        changes[persona] = {
            "old": round(old_w, 6),
            "new": round(new_w, 6),
            "delta": round(new_w - old_w, 6),
        }

    _save_weights(new_weights, db_path)

    return {
        "status": "updated",
        "outcomes_evaluated": len(rows),
        "avg_brier_loss": round(avg_loss, 6),
        "weight_changes": changes,
        "learning_rate": _LEARNING_RATE,
    }
