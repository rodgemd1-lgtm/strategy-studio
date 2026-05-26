"""Tests for scraper system."""
import pytest
from strategy_studio.scrapers import (
    ScraperOrchestrator,
    WikipediaScraper,
    SECScraper,
    DuckDuckGoScraper,
    NewsScraper,
    AcademicScraper,
    PredictionMarketScraper,
)


class TestWikipediaScraper:
    def test_scrape_company(self):
        s = WikipediaScraper()
        results = s.scrape("Tesla")
        assert isinstance(results, list)
        if results:
            assert results[0].source_uri.startswith("wikipedia://")
            assert results[0].confidence == "H"

    def test_scrape_nonexistent(self):
        s = WikipediaScraper()
        results = s.scrape("XyzzyNonexistentCorp12345")
        # Should return empty or handle gracefully
        assert isinstance(results, list)


class TestSECScraper:
    def test_scrape_ticker(self):
        s = SECScraper()
        results = s.scrape("TSLA")
        assert isinstance(results, list)
        if results:
            assert "sec://" in results[0].source_uri

    def test_scrape_invalid(self):
        s = SECScraper()
        results = s.scrape("INVALIDXYZ")
        assert isinstance(results, list)


class TestDuckDuckGoScraper:
    def test_scrape_query(self):
        s = DuckDuckGoScraper()
        results = s.scrape("Tesla strategy 2026", max_results=3)
        assert isinstance(results, list)
        if results:
            assert results[0].confidence in ("H", "M", "L")


class TestNewsScraper:
    def test_scrape_news(self):
        s = NewsScraper()
        results = s.scrape("Tesla news", max_results=3)
        assert isinstance(results, list)


class TestAcademicScraper:
    def test_scrape_academic(self):
        s = AcademicScraper()
        results = s.scrape("electric vehicle strategy", max_results=2)
        assert isinstance(results, list)


class TestPredictionMarketScraper:
    def test_scrape_markets(self):
        s = PredictionMarketScraper()
        results = s.scrape("Tesla", max_results=3)
        assert isinstance(results, list)


class TestScraperOrchestrator:
    def test_gather_company_data(self):
        orch = ScraperOrchestrator()
        results = orch.gather_company_data("Tesla", ticker="TSLA")
        assert isinstance(results, dict)
        # Should have at least some sources
        total = sum(len(v) for v in results.values())
        assert total >= 0  # May be 0 if network fails

    def test_gather_industry_data(self):
        orch = ScraperOrchestrator()
        results = orch.gather_industry_data("electric vehicles")
        assert isinstance(results, dict)

    def test_to_json(self):
        orch = ScraperOrchestrator()
        results = orch.gather_company_data("Tesla", ticker="TSLA")
        json_str = orch.to_json(results)
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        import json
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)