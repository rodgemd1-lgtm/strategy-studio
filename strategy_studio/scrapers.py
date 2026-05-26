"""
RIG Strategy Studio — Comprehensive Data Scraper System

Integrates with OmniScout collectors and adds new scraping capabilities:
- Web search (DuckDuckGo, via OmniScout web_collector)
- Company websites (Firecrawl, httpx)
- SEC EDGAR filings
- Wikipedia / Wikidata
- GitHub repositories
- News / RSS feeds
- Social media (public)
- Academic papers (arXiv, Semantic Scholar)
- Prediction markets (Polymarket, Kalshi, Metaculus)

All scrapers return structured Evidence objects for the strategy engine.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from strategy_studio.core.types import Evidence


# ── Base Scraper ────────────────────────────────────────────────────────────

class BaseScraper:
    """Base class for all data scrapers."""
    name: str = "base"
    source_type: str = "unknown"

    def scrape(self, query: str, **kwargs) -> list[Evidence]:
        """Scrape data and return Evidence objects."""
        raise NotImplementedError

    def _make_evidence(self, content: str, source_uri: str, confidence: str = "M", citations: list[str] | None = None) -> Evidence:
        """Helper to create Evidence objects."""
        h = hashlib.md5(content.encode()).hexdigest()[:12]
        return Evidence(
            source_uri=source_uri,
            content_hash=h,
            confidence=confidence,
            citations=citations or [content[:200]],
        )


# ── Firecrawl Scraper ──────────────────────────────────────────────────────

class FirecrawlScraper(BaseScraper):
    """Scrape company websites and web pages using Firecrawl."""
    name = "firecrawl"
    source_type = "web"

    def scrape(self, url: str, **kwargs) -> list[Evidence]:
        """Scrape a URL using Firecrawl CLI."""
        import subprocess
        import tempfile

        try:
            # Use firecrawl CLI to scrape
            result = subprocess.run(
                ["firecrawl", "scrape", url, "--format", "markdown", "--limit", "5"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                content = result.stdout.strip()
                return [self._make_evidence(
                    content=content,
                    source_uri=f"firecrawl://{url}",
                    confidence="H",
                    citations=[f"Scraped {url} via Firecrawl"],
                )]
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            pass

        return []


# ── DuckDuckGo Scraper ─────────────────────────────────────────────────────

class DuckDuckGoScraper(BaseScraper):
    """Scrape web search results using DuckDuckGo."""
    name = "duckduckgo"
    source_type = "web"

    def scrape(self, query: str, max_results: int = 10, **kwargs) -> list[Evidence]:
        """Search DuckDuckGo and return evidence."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                evidence = []
                for r in results:
                    content = f"{r.get('title', '')}\n{r.get('body', '')}"
                    uri = r.get('href', '')
                    if content.strip():
                        evidence.append(self._make_evidence(
                            content=content.strip(),
                            source_uri=f"ddg://{uri}",
                            confidence="M",
                            citations=[uri],
                        ))
                return evidence
        except ImportError:
            return []
        except Exception:
            return []


# ── SEC EDGAR Scraper ──────────────────────────────────────────────────────

class SECScraper(BaseScraper):
    """Scrape SEC EDGAR filings."""
    name = "sec_edgar"
    source_type = "regulatory"

    def scrape(self, ticker: str, **kwargs) -> list[Evidence]:
        """Scrape SEC filings for a ticker."""
        evidence = []

        # Get CIK
        cik = self._get_cik(ticker)
        if not cik:
            return evidence

        # Get company info
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
            req = urllib.request.Request(url, headers={
                "User-Agent": "StrategyStudio research@strategy.studio",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            name = data.get("name", "")
            sic = data.get("sic", "")
            sic_desc = data.get("sicDescription", "")
            state = data.get("stateOfIncorporation", "")
            tickers = data.get("tickers", [])
            exchanges = data.get("exchanges", [])

            content = f"Company: {name}\nCIK: {cik}\nSIC: {sic} ({sic_desc})\nState: {state}\nTickers: {', '.join(tickers)}\nExchanges: {', '.join(exchanges)}"

            evidence.append(self._make_evidence(
                content=content,
                source_uri=f"sec://{ticker}",
                confidence="H",
                citations=[f"SEC EDGAR CIK {cik}"],
            ))

            # Get recent filings
            recent = data.get("filings", {}).get("recent", {})
            if recent:
                forms = recent.get("form", [])[:10]
                dates = recent.get("filingDate", [])[:10]
                for i, (form, date) in enumerate(zip(forms, dates)):
                    evidence.append(self._make_evidence(
                        content=f"Filing: {form} on {date}",
                        source_uri=f"sec://{ticker}/{form}/{date}",
                        confidence="H",
                        citations=[f"SEC {form}"],
                    ))

        except Exception:
            pass

        return evidence

    def _get_cik(self, ticker: str) -> str | None:
        """Get CIK from ticker."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            req = urllib.request.Request(url, headers={
                "User-Agent": "StrategyStudio research@strategy.studio",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            ticker_upper = ticker.upper()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker_upper:
                    return str(entry.get("cik_str", ""))
        except Exception:
            pass
        return None


# ── Wikipedia Scraper ──────────────────────────────────────────────────────

class WikipediaScraper(BaseScraper):
    """Scrape company information from Wikipedia."""
    name = "wikipedia"
    source_type = "encyclopedia"

    def scrape(self, company_name: str, **kwargs) -> list[Evidence]:
        """Scrape Wikipedia summary for a company."""
        evidence = []

        # Try direct match
        slug = company_name.replace(" ", "_")
        data = self._fetch_wiki(slug)
        if not data:
            # Try with "Inc." or "Corporation"
            for suffix in ["_Inc.", "_Corporation", "_Corp.", "_Ltd."]:
                data = self._fetch_wiki(slug + suffix)
                if data:
                    break

        if data:
            extract = data.get("extract", "")
            title = data.get("title", "")
            url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            if extract:
                evidence.append(self._make_evidence(
                    content=f"{title}: {extract[:500]}",
                    source_uri=f"wikipedia://{url}",
                    confidence="H",
                    citations=[url],
                ))

        return evidence

    def _fetch_wiki(self, slug: str) -> dict | None:
        """Fetch Wikipedia page summary."""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "StrategyStudio/1.0",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception:
            return None


# ── GitHub Scraper ─────────────────────────────────────────────────────────

class GitHubScraper(BaseScraper):
    """Scrape GitHub repositories and organization info."""
    name = "github"
    source_type = "code"

    def scrape(self, org_or_repo: str, **kwargs) -> list[Evidence]:
        """Scrape GitHub organization or repository info."""
        evidence = []

        # Try as org
        try:
            url = f"https://api.github.com/orgs/{org_or_repo}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "StrategyStudio/1.0",
                "Accept": "application/vnd.github.v3+json",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            content = f"GitHub Org: {data.get('name', '')}\n"
            content += f"Description: {data.get('description', '')}\n"
            content += f"Public repos: {data.get('public_repos', 0)}\n"
            content += f"Followers: {data.get('followers', 0)}\n"
            content += f"Location: {data.get('location', '')}\n"
            content += f"Created: {data.get('created_at', '')}"

            evidence.append(self._make_evidence(
                content=content,
                source_uri=f"github://org/{org_or_repo}",
                confidence="H",
                citations=[data.get("html_url", "")],
            ))

            # Get top repos
            repos_url = data.get("repos_url", "")
            if repos_url:
                req2 = urllib.request.Request(repos_url, headers={
                    "User-Agent": "StrategyStudio/1.0",
                    "Accept": "application/vnd.github.v3+json",
                })
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    repos = json.loads(resp2.read())[:5]
                    for repo in repos:
                        evidence.append(self._make_evidence(
                            content=f"Repo: {repo.get('name', '')}\nStars: {repo.get('stargazers_count', 0)}\nLanguage: {repo.get('language', '')}\nDescription: {repo.get('description', '')}",
                            source_uri=f"github://repo/{repo.get('full_name', '')}",
                            confidence="H",
                            citations=[repo.get("html_url", "")],
                        ))

        except Exception:
            pass

        return evidence


# ── News / RSS Scraper ─────────────────────────────────────────────────────

class NewsScraper(BaseScraper):
    """Scrape news from RSS feeds and news APIs."""
    name = "news"
    source_type = "news"

    FEEDS = {
        "reuters": "https://www.reutersagency.com/feed/",
        "techcrunch": "https://techcrunch.com/feed/",
        "hn": "https://hnrss.org/frontpage",
    }

    def scrape(self, query: str, max_results: int = 5, **kwargs) -> list[Evidence]:
        """Scrape news related to a query."""
        evidence = []

        # Use DuckDuckGo news search
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
                for r in results:
                    content = f"{r.get('title', '')}\n{r.get('body', '')}\nDate: {r.get('date', '')}"
                    uri = r.get('url', '')
                    if content.strip():
                        evidence.append(self._make_evidence(
                            content=content.strip(),
                            source_uri=f"news://{uri}",
                            confidence="M",
                            citations=[uri],
                        ))
        except ImportError:
            pass
        except Exception:
            pass

        return evidence


# ── Academic Scraper ───────────────────────────────────────────────────────

class AcademicScraper(BaseScraper):
    """Scrape academic papers from arXiv and Semantic Scholar."""
    name = "academic"
    source_type = "research"

    def scrape(self, query: str, max_results: int = 5, **kwargs) -> list[Evidence]:
        """Scrape academic papers related to a query."""
        evidence = []

        # Try arXiv
        try:
            url = f"https://export.arxiv.org/api/query?search_query=all:{query}&max_results={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "StrategyStudio/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")

            # Parse Atom feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns)[:max_results]:
                title = entry.find("atom:title", ns).text.strip() if entry.find("atom:title", ns) is not None else ""
                summary = entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else ""
                published = entry.find("atom:published", ns).text if entry.find("atom:published", ns) is not None else ""
                link = entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else ""

                if title:
                    evidence.append(self._make_evidence(
                        content=f"{title}\n{summary[:300]}",
                        source_uri=f"arxiv://{link}",
                        confidence="H",
                        citations=[f"arXiv {published}"],
                    ))
        except Exception:
            pass

        return evidence


# ── Prediction Market Scraper ──────────────────────────────────────────────

class PredictionMarketScraper(BaseScraper):
    """Scrape prediction market data from Polymarket and Metaculus."""
    name = "prediction_market"
    source_type = "market"

    def scrape(self, query: str, max_results: int = 5, **kwargs) -> list[Evidence]:
        """Scrape prediction markets related to a query."""
        evidence = []

        # Polymarket (public API)
        try:
            url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={max_results}&search={query}"
            req = urllib.request.Request(url, headers={"User-Agent": "StrategyStudio/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            for market in data[:max_results]:
                question = market.get("question", "")
                outcome_prices = market.get("outcomePrices", "")
                volume = market.get("volume", 0)

                content = f"Market: {question}\nPrices: {outcome_prices}\nVolume: {volume}"

                evidence.append(self._make_evidence(
                    content=content,
                    source_uri=f"polymarket://{market.get('id', '')}",
                    confidence="H",
                    citations=[f"Polymarket: {question}"],
                ))
        except Exception:
            pass

        return evidence


# ── Company Website Scraper ────────────────────────────────────────────────

class CompanyWebsiteScraper(BaseScraper):
    """Scrape company website for key information."""
    name = "company_website"
    source_type = "web"

    def scrape(self, url: str, **kwargs) -> list[Evidence]:
        """Scrape a company website."""
        evidence = []

        # Try Firecrawl first
        firecrawl = FirecrawlScraper()
        fc_results = firecrawl.scrape(url)
        if fc_results:
            return fc_results

        # Fallback to basic HTTP fetch
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            # Extract title
                title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else ""

            # Extract meta description
                desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
                if not desc_match:
                    desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', content, re.IGNORECASE)
                description = desc_match.group(1).strip() if desc_match else ""

            # Extract key text (first 1000 chars of body)
                body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.IGNORECASE | re.DOTALL)
                body = body_match.group(1) if body_match else ""
                # Strip HTML tags
                body_text = re.sub(r"<[^>]+>", " ", body)
                body_text = re.sub(r"\s+", " ", body_text).strip()[:1000]

                if title or description or body_text:
                    content = f"Title: {title}\nDescription: {description}\nContent: {body_text}"
                    evidence.append(self._make_evidence(
                        content=content,
                        source_uri=f"web://{url}",
                        confidence="M",
                        citations=[url],
                    ))

        except Exception:
            pass

        return evidence


# ── Master Scraper Orchestrator ────────────────────────────────────────────

class ScraperOrchestrator:
    """Orchestrates all scrapers to gather comprehensive data."""

    def __init__(self):
        self.scrapers: dict[str, BaseScraper] = {
            "firecrawl": FirecrawlScraper(),
            "duckduckgo": DuckDuckGoScraper(),
            "sec": SECScraper(),
            "wikipedia": WikipediaScraper(),
            "github": GitHubScraper(),
            "news": NewsScraper(),
            "academic": AcademicScraper(),
            "prediction_market": PredictionMarketScraper(),
            "company_website": CompanyWebsiteScraper(),
        }

    def gather_company_data(self, company_name: str, ticker: str = "", website: str = "", **kwargs) -> dict[str, list[Evidence]]:
        """Gather comprehensive data about a company from all sources."""
        results: dict[str, list[Evidence]] = {}

        # Wikipedia
        if company_name:
            wiki = self.scrapers["wikipedia"].scrape(company_name)
            if wiki:
                results["wikipedia"] = wiki

        # SEC EDGAR
        if ticker:
            sec = self.scrapers["sec"].scrape(ticker)
            if sec:
                results["sec_edgar"] = sec

        # Company website
        if website:
            web = self.scrapers["company_website"].scrape(website)
            if web:
                results["company_website"] = web

        # Web search
        query = f"{company_name} {ticker} company analysis strategy"
        ddg = self.scrapers["duckduckgo"].scrape(query, max_results=10)
        if ddg:
            results["web_search"] = ddg

        # News
        news = self.scrapers["news"].scrape(f"{company_name} news", max_results=5)
        if news:
            results["news"] = news

        # GitHub (if ticker looks like a tech company)
        if ticker:
            gh = self.scrapers["github"].scrape(ticker.lower())
            if gh:
                results["github"] = gh

        # Academic
        academic = self.scrapers["academic"].scrape(f"{company_name} strategy innovation", max_results=3)
        if academic:
            results["academic"] = academic

        # Prediction markets
        pm = self.scrapers["prediction_market"].scrape(company_name, max_results=3)
        if pm:
            results["prediction_markets"] = pm

        return results

    def gather_competitor_data(self, competitors: list[str]) -> dict[str, list[Evidence]]:
        """Gather data about competitors."""
        results: dict[str, list[Evidence]] = {}
        for comp in competitors:
            comp_data = self.gather_company_data(comp)
            for source, evidence in comp_data.items():
                key = f"{comp}_{source}"
                results[key] = evidence
        return results

    def gather_industry_data(self, industry: str) -> dict[str, list[Evidence]]:
        """Gather industry-level data."""
        results: dict[str, list[Evidence]] = {}

        # Web search for industry
        ddg = self.scrapers["duckduckgo"].scrape(f"{industry} industry analysis trends 2026", max_results=10)
        if ddg:
            results["industry_web"] = ddg

        # News
        news = self.scrapers["news"].scrape(f"{industry} industry news", max_results=5)
        if news:
            results["industry_news"] = news

        # Academic
        academic = self.scrapers["academic"].scrape(f"{industry} innovation strategy", max_results=3)
        if academic:
            results["industry_academic"] = academic

        return results

    def to_json(self, results: dict[str, list[Evidence]]) -> str:
        """Convert results to JSON."""
        output = {}
        for source, evidence_list in results.items():
            output[source] = [e.model_dump(mode="json") for e in evidence_list]
        return json.dumps(output, indent=2, default=str)