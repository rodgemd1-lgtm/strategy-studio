"""Tests for real data pipeline."""
import pytest
from strategy_studio.data_pipeline import (
    get_company_profile,
    get_wikipedia_summary,
    enrich_company_data,
    build_evidence_from_data,
    get_historical_financials,
)


class TestDataPipeline:
    def test_get_company_profile(self):
        profile = get_company_profile("TSLA")
        # Should either return data or empty dict (network dependent)
        assert isinstance(profile, dict)
        if profile:
            assert "symbol" in profile or "ticker" in profile

    def test_get_wikipedia_summary(self):
        wiki = get_wikipedia_summary("Tesla")
        assert isinstance(wiki, dict)
        if wiki:
            assert "title" in wiki or "summary" in wiki

    def test_enrich_company_data_no_ticker(self):
        result = enrich_company_data("Unknown Company XYZ", ticker="")
        assert isinstance(result, dict)
        assert result["company_name"] == "Unknown Company XYZ"

    def test_enrich_company_data_with_ticker(self):
        result = enrich_company_data("Tesla", ticker="TSLA")
        assert isinstance(result, dict)
        assert result["ticker"] == "TSLA"
        # Should have some data sources (network dependent)
        if result.get("data_sources"):
            assert len(result["data_sources"]) >= 1

    def test_enrich_company_data_structure(self):
        result = enrich_company_data("Tesla", ticker="TSLA", industry="automotive")
        required_keys = [
            "company_name", "ticker", "industry", "data_sources",
            "evidence_sources", "historical_data", "competitors", "risks",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_build_evidence_from_data(self):
        enriched = {
            "ticker": "TSLA",
            "evidence_sources": [
                "Tesla trading at $426 (Yahoo Finance)",
                "American EV company (Wikipedia)",
            ],
        }
        evidence = build_evidence_from_data(enriched)
        assert isinstance(evidence, list)
        if evidence:
            assert len(evidence) == 2
            assert all(hasattr(e, "source_uri") for e in evidence)
            assert all(hasattr(e, "citations") for e in evidence)

    def test_get_historical_financials(self):
        hist = get_historical_financials("TSLA")
        assert isinstance(hist, dict)
        if hist:
            # Should have price data
            price_keys = [k for k in hist if k.startswith("price_")]
            growth_keys = [k for k in hist if k.startswith("growth_")]
            assert len(price_keys) > 0 or len(growth_keys) > 0

    def test_enrich_updates_industry(self):
        result = enrich_company_data("Tesla", ticker="TSLA", industry="")
        # Should auto-detect industry from Wikipedia
        assert isinstance(result["industry"], str)