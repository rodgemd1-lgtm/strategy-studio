"""A3.1 — Intent via multi-agent voting.

Runs 3 classifier agents in parallel:
  - regex_agent: pattern-based (same as A1)
  - keyword_agent: keyword-overlap (same as A1, different weights)
  - decomposition_agent: decomposes text into sub-intents, then votes

Final decision: majority vote with confidence = avg of agreeing agents.
Never raises.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple

from strategy_studio.core.types import InboundPayload, IntentKey

# Same patterns/keywords as A1 — reused here for the regex and keyword agents
_PATTERNS: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: [
        r"synthesi[sz]e", r"build\s+(?:a\s+)?strategy", r"strategic\s+option",
        r"option[s]?\s+for", r"strategy\s+for", r"develop\s+(?:a\s+)?plan",
    ],
    IntentKey.WARGAME: [
        r"wargame", r"competitor\s+move", r"market\s+simulation",
        r"red\s+team", r"war.?game", r"scenario\s+planning", r"price\s+war",
    ],
    IntentKey.FORECAST: [
        r"forecast", r"predict", r"prediction", r"crux",
        r"probability\s+of", r"estimate", r"project",
    ],
    IntentKey.COMPETITOR_INTEL: [
        r"competitor\s+intel", r"competitor\s+intelligence",
        r"rival\s+analysis", r"competitive\s+landscape",
    ],
    IntentKey.CLIENT_INTEL: [
        r"client\s+intel", r"prospect\s+analysis",
        r"wedge\s+offer", r"icp\s+analysis",
    ],
    IntentKey.FALSIFY: [
        r"falsif", r"disprove", r"null\s+hypothesis",
        r"test\s+(?:the\s+)?belief", r"stress\s+test", r"invalidate",
    ],
}

_KEYWORDS: dict[IntentKey, list[str]] = {
    IntentKey.SYNTHESIZE: ["synthesize", "strategy", "options", "plan", "prioritize", "rank"],
    IntentKey.WARGAME: ["wargame", "competitor move", "red team", "simulation", "price war"],
    IntentKey.FORECAST: ["forecast", "predict", "estimate", "projection", "probability", "trend"],
    IntentKey.COMPETITOR_INTEL: ["competitor", "rival", "competitive", "market share"],
    IntentKey.CLIENT_INTEL: ["client", "prospect", "customer", "icp", "wedge", "buyer"],
    IntentKey.FALSIFY: ["falsify", "disprove", "invalidate", "debunk", "counter-evidence"],
}


def _regex_classify(text: str) -> Tuple[IntentKey, float]:
    """Agent 1: regex-pattern classifier."""
    text_lower = text.lower()
    for intent, patterns in _PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                return (intent, 0.9 if len(text_lower) < 80 else 0.8)
    return (IntentKey.UNKNOWN, 0.0)


def _keyword_classify(text: str) -> Tuple[IntentKey, float]:
    """Agent 2: keyword-overlap classifier."""
    text_lower = text.lower()
    best: Tuple[IntentKey, float] = (IntentKey.UNKNOWN, 0.0)
    for intent in (IntentKey.FALSIFY, IntentKey.WARGAME, IntentKey.FORECAST,
                   IntentKey.COMPETITOR_INTEL, IntentKey.CLIENT_INTEL, IntentKey.SYNTHESIZE):
        words = _KEYWORDS[intent]
        hits = sum(1 for w in words if w in text_lower)
        if hits > 0:
            conf = min(0.5 + hits * 0.1, 0.7)
            if conf > best[1]:
                best = (intent, conf)
    return best


def _decomposition_classify(text: str) -> Tuple[IntentKey, float]:
    """Agent 3: decomposes text into clauses, classifies each, votes."""
    clauses = [c.strip() for c in re.split(r'[.,;!?]', text) if len(c.strip()) > 5]
    if not clauses:
        return (IntentKey.UNKNOWN, 0.0)
    votes: dict[IntentKey, int] = {}
    for clause in clauses:
        intent, _ = _regex_classify(clause)
        if intent != IntentKey.UNKNOWN:
            votes[intent] = votes.get(intent, 0) + 1
    if not votes:
        return (IntentKey.UNKNOWN, 0.0)
    winner = max(votes, key=lambda k: votes[k])
    confidence = min(0.5 + votes[winner] * 0.15, 0.8)
    return (winner, confidence)


def classify_intent_voted(
    payload: InboundPayload,
    agent_budget: int = 3,
) -> Tuple[IntentKey, float]:
    """
    Run `agent_budget` classifier agents in parallel.
    Majority vote wins. Confidence = average of agreeing agents.
    Falls back to A1 regex on tie. Never raises.
    """
    agents = [_regex_classify, _keyword_classify, _decomposition_classify]
    results: list[Tuple[IntentKey, float]] = []

    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            futures = [ex.submit(a, payload.raw_text) for a in agents[:agent_budget]]
            for f in futures:
                try:
                    results.append(f.result(timeout=2.0))
                except Exception:
                    results.append((IntentKey.UNKNOWN, 0.0))
    except Exception:
        # Sequential fallback
        results = [a(payload.raw_text) for a in agents[:agent_budget]]

    # Count votes
    tally: dict[IntentKey, list[float]] = {}
    for intent, conf in results:
        if intent not in tally:
            tally[intent] = []
        tally[intent].append(conf)

    if not tally or all(k == IntentKey.UNKNOWN for k in tally):
        return (IntentKey.UNKNOWN, 0.0)

    # Exclude UNKNOWN from vote, include only if no other option
    known = {k: v for k, v in tally.items() if k != IntentKey.UNKNOWN}
    if not known:
        return (IntentKey.UNKNOWN, 0.0)

    winner = max(known, key=lambda k: (len(known[k]), sum(known[k]) / len(known[k])))
    avg_conf = sum(known[winner]) / len(known[winner])
    return (winner, round(avg_conf, 4))