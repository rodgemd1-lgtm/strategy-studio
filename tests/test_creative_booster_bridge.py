"""Tests for the Creative Booster bridge (Strategy Studio V10 idea-evaluation gate).

The bridge must (a) never raise on a missing optional dependency, and (b) when
the booster IS installed, discriminate a proof-bound idea from a generic one.
"""
from __future__ import annotations

import pytest

from strategy_studio.core.types import Option
from strategy_studio.studios import creative_booster as cb


def test_evaluate_always_returns_evaluation_and_maps_to_option() -> None:
    # Arrange / Act
    ev = cb.evaluate_idea(
        "Outcome-priced audit underwriting",
        "Replace hourly billing with a fee indexed to verified tax savings, "
        "underwritten by an AI risk model that prices each engagement.",
        "SMB accounting firm wants to escape commodity hourly billing.",
    )

    # Assert — contract holds regardless of whether the booster is installed.
    assert isinstance(ev, cb.BoosterEvaluation)
    opt = ev.to_option("Outcome-priced audit underwriting", "Outcome pricing for SMB audits")
    assert isinstance(opt, Option)
    assert 0.0 <= opt.score <= 1.0


def test_graceful_fallback_when_booster_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange — simulate the booster not being installed.
    monkeypatch.setattr(cb, "_BOOSTER_AVAILABLE", False)

    # Act
    ev = cb.evaluate_idea("x", "y", "z")

    # Assert — no exception, flagged unavailable.
    assert ev.available is False
    assert ev.verdict == "unavailable"
    assert ev.proof_packet is None


@pytest.mark.skipif(not cb.booster_available(), reason="rig-creative-booster not installed")
def test_available_path_accepts_proofbound_and_revises_generic() -> None:
    # Arrange
    corpus = [
        "AI-powered platform that leverages synergies to deliver best-in-class outcomes",
        "data-driven insights to optimize your business and unlock growth",
    ]
    strong = cb.evaluate_idea(
        "Outcome-priced audit underwriting",
        "Replace hourly CPA billing with a fee indexed to verified tax savings, "
        "underwritten by an AI risk model that prices each engagement from the "
        "client's prior filings and refunds if savings miss the modeled floor.",
        "SMB accounting firm wants to escape commodity hourly billing and differentiate.",
        sources=["IRS SOI tax-stats 2024", "Firm P&L", "Actuarial model v2"],
        claims=["Savings measurable within 0.5%", "Refund floor caps downside at 8%", "AUC>0.82"],
        mechanisms=["actuarial pricing", "refund-floor risk transfer", "feature extraction", "risk pooling"],
        corpus=corpus,
    )
    generic = cb.evaluate_idea(
        "AI-powered growth platform",
        "A best-in-class, end-to-end AI-powered platform that leverages synergies to unlock growth.",
        "SMB accounting firm wants to grow.",
        corpus=corpus,
    )

    # Assert
    assert strong.available is True
    assert strong.verdict == "accept"
    assert strong.proof_packet is not None
    assert generic.verdict in {"revise", "reject"}
    assert strong.creativity_score > generic.creativity_score


def test_roadmap_fallback_when_booster_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cb, "_BOOSTER_AVAILABLE", False)
    assert cb.build_strategy_roadmap("t", "c", "x") is None


@pytest.mark.skipif(not cb.booster_available(), reason="rig-creative-booster not installed")
def test_roadmap_is_future_back_and_leverage_ordered() -> None:
    rm = cb.build_strategy_roadmap(
        "Outcome-priced audit underwriting",
        "Replace hourly billing with a fee indexed to verified savings, underwritten by a risk model.",
        "Mid-market CPA firm wants to escape hourly billing.",
        sources=["a", "b", "c"], claims=["x", "y", "z"],
        mechanisms=["actuarial pricing", "risk transfer", "feature extraction", "risk pooling"],
        top=5,
    )
    assert rm is not None
    items = rm["items"]
    assert len(items) == 5
    prios = [it["priority"] for it in items]
    assert prios == sorted(prios, reverse=True)
    assert items[0]["horizon"] == "now (≤90d)"
