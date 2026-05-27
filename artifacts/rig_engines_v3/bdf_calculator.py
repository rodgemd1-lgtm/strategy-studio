"""
bdf_calculator.py — RIG Sovereign Comms Engine · Bipolar Deviation Force Calculator
Lane: H4-BUILD-COMMS-ENGINES | Card: BC-COMMS-DEV-V2

BDF = sign(intent) × |RobustMADZ| × CraftCoefficient × RestraintCoefficient

Gate: |BDF| >= 8.0 to ship.

Baseline population stored at artifacts/rig_engines_v3/baseline_population.json.
Created on first run with sensible defaults (median=0.5, MAD=0.15).

No network calls. stdlib only (+ numpy if available). Safe for any input.
"""
from __future__ import annotations

import json
import unicodedata
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Deferred numpy import (pure-python fallback for median + MAD)
# ---------------------------------------------------------------------------
try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _np = None  # type: ignore
    _HAS_NP = False

# ---------------------------------------------------------------------------
# Engine imports — top-level so the F6 adapter's import-probe works
# ---------------------------------------------------------------------------
from detonation_scorer import score as _det_score  # type: ignore
from erosion_scorer import score as _ero_score  # type: ignore
from craft_archetypes import score as _craft_score, craft_coefficient  # type: ignore
from erosion_scorer import restraint as _restraint_fn  # type: ignore

# ---------------------------------------------------------------------------
# Baseline population file
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).parent
_BASELINE_FILE = _BASE_DIR / "baseline_population.json"

_DEFAULT_BASELINE: dict = {
    "median": 0.5,
    "MAD": 0.15,
    "sample_count": 0,
    "last_updated_iso": "2026-01-01T00:00:00Z",
    "note": "Initialized with sensible defaults. Update via update_population_baseline().",
}


def _load_baseline() -> dict:
    """Load baseline from file; return defaults if missing or corrupt."""
    try:
        if _BASELINE_FILE.exists():
            data = json.loads(_BASELINE_FILE.read_text(encoding="utf-8"))
            med = float(data.get("median", 0.5))
            mad = float(data.get("MAD", 0.15))
            if mad <= 0:
                mad = 0.15
            return {"median": med, "MAD": mad}
    except Exception:
        pass
    return {"median": _DEFAULT_BASELINE["median"], "MAD": _DEFAULT_BASELINE["MAD"]}


def _save_baseline(median: float, mad: float, sample_count: int) -> None:
    """Atomically save updated baseline to file."""
    tmp = _BASELINE_FILE.with_suffix(".json.tmp")
    data = {
        "median": round(median, 6),
        "MAD": round(mad, 6),
        "sample_count": sample_count,
        "last_updated_iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(_BASELINE_FILE)


def _ensure_baseline() -> None:
    """Create baseline file with defaults if it doesn't exist."""
    if not _BASELINE_FILE.exists():
        _save_baseline(
            _DEFAULT_BASELINE["median"],
            _DEFAULT_BASELINE["MAD"],
            0,
        )


# ---------------------------------------------------------------------------
# RobustMADZ calculation
# ---------------------------------------------------------------------------

def _pure_median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def _robust_mad_z(x: float, median: float, mad: float) -> float:
    """
    Compute RobustMADZ: 0.6745 × (x - median) / MAD
    If MAD = 0, return 0.
    """
    if mad == 0:
        return 0.0
    return 0.6745 * (x - median) / mad


# ---------------------------------------------------------------------------
# Restraint coefficient
# ---------------------------------------------------------------------------

def _restraint_coefficient(text: str) -> float:
    """
    0.5–1.5 range mapping of erosion_scorer.restraint().
    restraint() returns 0.0–1.0; scale to [0.5, 1.5].
    """
    if not text.strip():
        return 1.0
    r = _restraint_fn(text)
    # Map [0, 1] → [0.5, 1.5]
    return round(0.5 + r, 4)


# ---------------------------------------------------------------------------
# Public: update_population_baseline
# ---------------------------------------------------------------------------

def update_population_baseline(new_scores: list[float]) -> dict:
    """
    Update the population baseline with new raw scores.

    Args:
        new_scores: list of float raw detonation/erosion scores (0.0-1.0 range)

    Returns updated baseline dict.
    """
    if not new_scores:
        return _load_baseline()
    _ensure_baseline()

    if _HAS_NP:
        arr = _np.array(new_scores, dtype=float)
        new_median = float(_np.median(arr))
        new_mad = float(_np.median(_np.abs(arr - new_median)))
    else:
        new_median = _pure_median(new_scores)
        new_mad = _pure_median([abs(x - new_median) for x in new_scores])

    if new_mad <= 0:
        new_mad = 0.15  # floor

    _save_baseline(new_median, new_mad, len(new_scores))
    return {"median": new_median, "MAD": new_mad}


# ---------------------------------------------------------------------------
# Main compute function
# ---------------------------------------------------------------------------

def compute(draft: str, channel: str, intent: int = 1) -> dict:
    """
    Compute the Bipolar Deviation Force score for a draft.

    Args:
        draft:   the text to score
        channel: "linkedin-post" | "substack" | "email-cold" | etc.
        intent:  1 for detonation intent, -1 for erosion intent. Default 1.

    Returns:
        {
          "bdf_score": float,           # signed; |bdf_score| >= 8.0 is ship-worthy
          "sign": int,                  # +1 or -1
          "robust_mad_z": float,        # |RobustMADZ|
          "craft_coef": float,          # 0.0-1.5 from craft_archetypes
          "restraint_coef": float,      # 0.5-1.5
          "direction": str,             # "detonation" | "erosion" | "neutral"
          "gate": str,                  # "pass" | "fail"
          "components": {
            "detonation_raw": float,
            "erosion_raw": float,
            "craft_scores": dict,
          }
        }
    """
    # Guard inputs
    if not isinstance(draft, str):
        draft = ""
    intent = 1 if intent >= 0 else -1

    _ensure_baseline()
    baseline = _load_baseline()
    median = baseline["median"]
    mad = baseline["MAD"]

    # Run sub-scorers
    det_result = _det_score(draft)
    ero_result = _ero_score(draft)
    craft_result = _craft_score(draft)

    det_raw: float = det_result["score"]
    ero_raw: float = ero_result["score"]
    craft_scores: dict = craft_result["scores"]

    # Craft coefficient: 0.0–1.0 → scaled to 0.0–1.5
    # MAX of 5 archetypes, then scale: [0, 1] → [0.5, 1.5]
    raw_craft_coef = craft_coefficient(craft_scores)
    craft_coef = round(0.5 + raw_craft_coef, 4)

    # Restraint coefficient: 0.5–1.5
    restraint_coef = _restraint_coefficient(draft)

    # Combined raw score: use the pole-appropriate scorer
    if intent >= 0:
        x = det_raw
    else:
        x = ero_raw

    # Signed RobustMADZ of the raw score against population baseline.
    # Positive = text scores ABOVE population median (deviation toward detonation).
    # Negative = text scores BELOW population median (eroded, not detonation-worthy).
    signed_mad_z = _robust_mad_z(x, median, mad)
    abs_mad_z = abs(signed_mad_z)

    # BDF = sign(intent) × signed_mad_z × CraftCoef × RestraintCoef
    # When intent=+1 and signed_mad_z < 0 (text below median), BDF is negative → gate=fail.
    # When intent=-1 and signed_mad_z < 0 (erosion text below median), BDF is positive → potential pass.
    sign = int(intent)
    bdf_score = sign * signed_mad_z * craft_coef * restraint_coef

    # Direction — based on the polarity of the final score
    if abs_mad_z < 0.01:
        direction = "neutral"
    elif bdf_score > 0:
        direction = "detonation"
    elif bdf_score < 0:
        direction = "erosion"
    else:
        direction = "neutral"

    # Gate: the SIGNED BDF must exceed +8.0 (for detonation) or be below -8.0 (for erosion).
    # |BDF| >= 8.0 is a shorthand for "strong pole signal in the intended direction."
    # We check the signed value: pass if bdf_score >= 8.0 OR bdf_score <= -8.0.
    gate = "pass" if abs(bdf_score) >= 8.0 and (
        (sign > 0 and bdf_score > 0) or (sign < 0 and bdf_score < 0) or (bdf_score > 0)
    ) else "fail"

    return {
        "bdf_score": round(bdf_score, 4),
        "sign": sign,
        "robust_mad_z": round(abs_mad_z, 4),  # magnitude of deviation from population median
        "craft_coef": craft_coef,
        "restraint_coef": restraint_coef,
        "direction": direction,
        "gate": gate,
        "components": {
            "detonation_raw": round(det_raw, 6),
            "erosion_raw": round(ero_raw, 6),
            "craft_scores": {k: round(v, 4) for k, v in craft_scores.items()},
        },
    }
