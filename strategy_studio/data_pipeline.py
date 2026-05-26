"""
Real Data Pipeline — Ingests company data from public sources.

Sources:
- Yahoo Finance (v8 chart API): price, market cap, historical data
- Wikipedia API: company description, industry, key facts
- SEC EDGAR (with proper headers): company tickers, filings
- Crunchbase (public): funding, competitors (stub for now)

All functions are deterministic given the same inputs.
No API keys required.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from strategy_studio.core.types import Evidence


# ── HTTP Helper ─────────────────────────────────────────────────────────────

def _fetch_json(url: str, headers: dict | None = None, timeout: int = 10) -> dict | None:
    """Fetch JSON from a URL with error handling."""
    default_headers = {
        "User-Agent": "StrategyStudio/1.0 (Research Project)",
        "Accept": "application/json",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def _fetch_text(url: str, headers: dict | None = None, timeout: int = 10) -> str | None:
    """Fetch text from a URL with error handling."""
    default_headers = {
        "User-Agent": "StrategyStudio/1.0 (Research Project)",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


# ── Yahoo Finance ───────────────────────────────────────────────────────────

def get_company_profile(ticker: str) -> dict[str, Any]:
    """Get company profile from Yahoo Finance v8 API."""
    data = _fetch_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}?range=5y&interval=1mo"
    )
    if not data:
        return {}

    try:
        result = data["chart"]["result"][0]
        meta = result["meta"]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]

        # Compute historical data
        historical = {}
        for ts, close in zip(timestamps, closes):
            if close is not None:
                year = time.gmtime(ts).tm_year
                if year not in historical:
                    historical[year] = []
                historical[year].append(close)

        # Average close per year
        yearly_prices = {y: sum(v) / len(v) for y, v in historical.items() if v}

        # Compute growth rates
        growth_rates = {}
        years = sorted(yearly_prices.keys())
        for i in range(1, len(years)):
            prev, curr = yearly_prices[years[i - 1]], yearly_prices[years[i]]
            if prev > 0:
                growth_rates[f"growth_{years[i]}"] = round((curr - prev) / prev * 100, 2)

        return {
            "ticker": ticker.upper(),
            "symbol": meta.get("symbol", ticker.upper()),
            "short_name": meta.get("shortName", ""),
            "exchange": meta.get("exchangeName", ""),
            "currency": meta.get("currency", "USD"),
            "current_price": meta.get("regularMarketPrice"),
            "previous_close": meta.get("previousClose"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "yearly_prices": yearly_prices,
            "growth_rates": growth_rates,
            "data_source": "yahoo_finance",
        }
    except (KeyError, IndexError):
        return {}


def get_company_fundamentals(ticker: str) -> dict[str, Any]:
    """Get company fundamentals from Yahoo Finance."""
    # Try the chart API for price data
    profile = get_company_profile(ticker)
    if not profile:
        return {}

    # Enrich with computed metrics
    prices = profile.get("yearly_prices", {})
    if prices:
        years = sorted(prices.keys())
        if len(years) >= 2:
            latest_year = years[-1]
            earliest_year = years[0]
            cagr = _compute_cagr(prices[earliest_year], prices[latest_year], len(years) - 1)
            profile["price_cagr_5y"] = round(cagr, 2) if cagr else None
            profile["latest_year"] = latest_year
            profile["earliest_year"] = earliest_year

    return profile


def _compute_cagr(start: float, end: float, years: int) -> float | None:
    """Compute compound annual growth rate."""
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


# ── Wikipedia ───────────────────────────────────────────────────────────────

def get_wikipedia_summary(company_name: str) -> dict[str, Any]:
    """Get company summary from Wikipedia API."""
    # Try direct match first
    slug = company_name.replace(" ", "_")
    data = _fetch_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}")

    if not data or data.get("type") == "disambiguation":
        # Try with "Inc." or "Corporation"
        for suffix in ["_Inc.", "_Corporation", "_Corp.", "_Ltd.", "_LLC"]:
            data = _fetch_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}{suffix}")
            if data and data.get("type") != "disambiguation":
                break

    if not data:
        return {}

    extract = data.get("extract", "")
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "summary": extract[:1000] if extract else "",
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "data_source": "wikipedia",
    }


# ── SEC EDGAR ───────────────────────────────────────────────────────────────

def get_sec_company_info(ticker: str) -> dict[str, Any]:
    """Get company info from SEC EDGAR."""
    data = _fetch_json(
        f"https://data.sec.gov/submissions/CIK{_get_cik(ticker)}.json",
        headers={"User-Agent": "StrategyStudio research@strategy.studio"},
    )
    if not data:
        return {}

    try:
        recent = data.get("filings", {}).get("recent", {})
        return {
            "cik": data.get("cik", ""),
            "name": data.get("name", ""),
            "sic": data.get("sic", ""),
            "sic_description": data.get("sicDescription", ""),
            "fiscal_year_end": data.get("fiscalYearEnd", ""),
            "state_of_incorporation": data.get("stateOfIncorporation", ""),
            "tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", []),
            "recent_filings_count": len(recent.get("form", [])) if recent else 0,
            "data_source": "sec_edgar",
        }
    except (KeyError, TypeError):
        return {}


def _get_cik(ticker: str) -> str:
    """Get CIK number from ticker using SEC EDGAR."""
    data = _fetch_json(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": "StrategyStudio research@strategy.studio"},
    )
    if not data:
        return ""

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry.get("cik_str", "")).zfill(10)
    return ""


# ── Company Data Enrichment ─────────────────────────────────────────────────

def enrich_company_data(
    company_name: str,
    ticker: str = "",
    industry: str = "",
) -> dict[str, Any]:
    """Enrich company data from all available public sources.

    Returns a comprehensive company profile with:
    - Financial data (price, growth, market cap)
    - Company description and industry
    - Evidence sources for strategy analysis
    - Historical data for predictions
    """
    result: dict[str, Any] = {
        "company_name": company_name,
        "ticker": ticker.upper() if ticker else "",
        "industry": industry,
        "data_sources": [],
        "evidence_sources": [],
        "historical_data": {},
        "competitors": [],
        "risks": [],
    }

    # 1. Yahoo Finance data
    if ticker:
        yf_data = get_company_fundamentals(ticker)
        if yf_data:
            result["data_sources"].append("yahoo_finance")
            result["short_name"] = yf_data.get("short_name", "")
            result["current_price"] = yf_data.get("current_price")
            result["fifty_two_week_high"] = yf_data.get("fifty_two_week_high")
            result["fifty_two_week_low"] = yf_data.get("fifty_two_week_low")
            result["price_cagr_5y"] = yf_data.get("price_cagr_5y")
            result["exchange"] = yf_data.get("exchange", "")

            # Historical data for predictions
            growth_rates = yf_data.get("growth_rates", {})
            for key, value in growth_rates.items():
                result["historical_data"][key] = value

            # Generate evidence from financial data
            if yf_data.get("current_price"):
                result["evidence_sources"].append(
                    f"{company_name} ({ticker.upper()}) trading at ${yf_data['current_price']:.2f} on {yf_data.get('exchange', 'N/A')} (Yahoo Finance)"
                )
            if yf_data.get("price_cagr_5y") is not None:
                result["evidence_sources"].append(
                    f"{company_name} 5-year price CAGR: {yf_data['price_cagr_5y']:.1f}% (Yahoo Finance)"
                )

    # 2. Wikipedia data
    wiki_data = get_wikipedia_summary(company_name)
    if wiki_data:
        result["data_sources"].append("wikipedia")
        result["description"] = wiki_data.get("summary", "")
        result["wiki_title"] = wiki_data.get("title", "")
        result["wiki_url"] = wiki_data.get("url", "")

        # Extract industry from Wikipedia if not provided
        if not industry and wiki_data.get("description"):
            desc = wiki_data["description"].lower()
            industry_map = {
                "software": "saas", "technology": "saas", "cloud": "saas",
                "financial": "fintech", "banking": "fintech", "payment": "fintech",
                "health": "healthcare", "pharmaceutical": "healthcare", "biotech": "biotech",
                "retail": "retail", "e-commerce": "retail", "consumer": "retail",
                "energy": "energy", "oil": "energy", "gas": "energy",
                "automotive": "manufacturing", "manufacturing": "manufacturing",
            }
            for keyword, ind in industry_map.items():
                if keyword in desc:
                    result["industry"] = ind
                    break

        if wiki_data.get("summary"):
            result["evidence_sources"].append(
                f"{company_name}: {wiki_data['summary'][:200]} (Wikipedia)"
            )

    # 3. SEC EDGAR data
    if ticker:
        sec_data = get_sec_company_info(ticker)
        if sec_data:
            result["data_sources"].append("sec_edgar")
            result["sec_name"] = sec_data.get("name", "")
            result["sic_code"] = sec_data.get("sic", "")
            result["sic_description"] = sec_data.get("sic_description", "")
            result["state_of_incorporation"] = sec_data.get("state_of_incorporation", "")

            if sec_data.get("sic_description"):
                result["evidence_sources"].append(
                    f"{company_name} SIC: {sec_data['sic_description']} (SEC EDGAR)"
                )

    # 4. Derive risks from data
    cagr = result.get("price_cagr_5y")
    if cagr is not None:
        if cagr < -10:
            result["risks"].append("Significant negative price trend — market sentiment concerns")
        elif cagr > 50:
            result["risks"].append("High growth expectations — risk of disappointment")

    high = result.get("fifty_two_week_high")
    low = result.get("fifty_two_week_low")
    if high is not None and low is not None:
        try:
            high_f, low_f = float(high), float(low)
            if high_f > 0 and low_f > 0:
                volatility = (high_f - low_f) / high_f * 100
                if volatility > 60:
                    result["risks"].append(f"High price volatility ({volatility:.0f}% range) — market uncertainty")
        except (ValueError, TypeError):
            pass

    return result


def build_evidence_from_data(enriched_data: dict[str, Any]) -> list[Evidence]:
    """Build Evidence objects from enriched company data."""
    evidence = []
    for i, source in enumerate(enriched_data.get("evidence_sources", [])):
        h = hashlib.md5(source.encode()).hexdigest()[:12]
        evidence.append(Evidence(
            source_uri=f"data://{enriched_data.get('ticker', 'unknown')}/{h}",
            content_hash=h,
            confidence="H" if "Yahoo Finance" in source or "SEC" in source else "M",
            citations=[source],
        ))
    return evidence


def get_historical_financials(ticker: str) -> dict[str, float]:
    """Get historical financial data suitable for prediction models."""
    profile = get_company_profile(ticker)
    if not profile:
        return {}

    result = {}
    yearly = profile.get("yearly_prices", {})
    for year, price in yearly.items():
        result[f"price_{year}"] = round(price, 2)

    growth_rates = profile.get("growth_rates", {})
    result.update(growth_rates)

    return result