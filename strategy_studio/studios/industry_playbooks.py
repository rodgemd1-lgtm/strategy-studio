"""
Industry Playbooks — Industry-specific strategy templates, KPIs,
competitive frameworks, and benchmarking data.

All data is hardcoded (deterministic). No external API calls.
"""
from __future__ import annotations

import math
from typing import Literal

from strategy_studio.core.types import Option
from strategy_studio.core.types_extended import Scenario


# ── Playbook Data ────────────────────────────────────────────────────────────

_PLAYBOOKS: dict[str, dict] = {
    "saas": {
        "key_metrics": [
            {"name": "ARR", "unit": "USD", "description": "Annual Recurring Revenue"},
            {"name": "NRR", "unit": "%", "description": "Net Revenue Retention"},
            {"name": "CAC", "unit": "USD", "description": "Customer Acquisition Cost"},
            {"name": "LTV", "unit": "USD", "description": "Lifetime Value"},
            {"name": "Gross Margin", "unit": "%", "description": "Gross profit / revenue"},
            {"name": "Rule of 40", "unit": "%", "description": "Growth rate + profit margin"},
            {"name": "Payback Period", "unit": "months", "description": "CAC / monthly gross margin per customer"},
            {"name": "Logo Churn", "unit": "%", "description": "Customer count churn rate"},
            {"name": "Revenue Churn", "unit": "%", "description": "Revenue churn rate"},
            {"name": "Magic Number", "unit": "ratio", "description": "Net new ARR / sales & marketing spend"},
        ],
        "competitive_frameworks": [
            {"name": "Porter's Five Forces", "dimensions": ["supplier_power", "buyer_power", "competitive_rivalry", "threat_of_substitution", "threat_of_new_entry"]},
            {"name": "BCG Matrix", "dimensions": ["market_growth", "market_share"]},
            {"name": "Ansoff Matrix", "dimensions": ["market_familiarity", "product_familiarity"]},
            {"name": "Value Chain Analysis", "dimensions": ["inbound_logistics", "operations", "outbound_logistics", "marketing", "service"]},
        ],
        "benchmarks": {
            "NRR": {"p25": 100, "p50": 110, "p75": 125, "mean": 112, "std": 15},
            "Gross Margin": {"p25": 65, "p50": 72, "p75": 80, "mean": 72, "std": 10},
            "CAC Payback": {"p25": 18, "p50": 12, "p75": 8, "mean": 13, "std": 6},
            "Logo Churn": {"p25": 8, "p50": 5, "p75": 3, "mean": 5.5, "std": 3},
            "Rule of 40": {"p25": 20, "p50": 35, "p75": 50, "mean": 35, "std": 15},
            "Magic Number": {"p25": 0.5, "p50": 0.75, "p75": 1.0, "mean": 0.75, "std": 0.3},
        },
        "strategic_options": {
            "startup": [
                {"name": "Product-Led Growth", "description": "Let product drive adoption", "investment": "low", "timeline": "6-12 months"},
                {"name": "Niche Domination", "description": "Own a specific segment", "investment": "low", "timeline": "3-6 months"},
                {"name": "Freemium Funnel", "description": "Free tier to paid conversion", "investment": "medium", "timeline": "6-12 months"},
            ],
            "growth": [
                {"name": "Land and Expand", "description": "Start small, grow within accounts", "investment": "medium", "timeline": "12-18 months"},
                {"name": "Channel Partnerships", "description": "Reseller and integration partners", "investment": "medium", "timeline": "6-12 months"},
                {"name": "International Expansion", "description": "Enter new geographic markets", "investment": "high", "timeline": "12-24 months"},
                {"name": "Adjacent Product", "description": "Expand to adjacent use cases", "investment": "high", "timeline": "12-18 months"},
            ],
            "mature": [
                {"name": "Platform Strategy", "description": "Become the platform others build on", "investment": "high", "timeline": "18-36 months"},
                {"name": "Acquisition Rollup", "description": "Acquire smaller competitors", "investment": "very_high", "timeline": "6-18 months"},
                {"name": "Operational Excellence", "description": "Optimize margins and efficiency", "investment": "medium", "timeline": "12-24 months"},
            ],
            "decline": [
                {"name": "Harvest and Optimize", "description": "Maximize cash flow from existing base", "investment": "low", "timeline": "6-12 months"},
                {"name": "Pivot to Adjacent", "description": "Enter a growing adjacent market", "investment": "high", "timeline": "12-24 months"},
                {"name": "Merger or Sale", "description": "Combine with or sell to a competitor", "investment": "medium", "timeline": "6-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Platform Risk", "probability": "medium", "impact": "high", "mitigation": "Diversify distribution channels"},
            {"name": "Commoditization", "probability": "high", "impact": "medium", "mitigation": "Build switching costs and data moats"},
            {"name": "Key Person Risk", "probability": "medium", "impact": "high", "mitigation": "Document processes, cross-train team"},
            {"name": "Regulatory Change", "probability": "low", "impact": "high", "mitigation": "Proactive compliance, government relations"},
            {"name": "Technical Debt", "probability": "high", "impact": "medium", "mitigation": "Allocate 20% of engineering to debt reduction"},
        ],
        "evidence_sources": [
            "OpenView SaaS Benchmarks", "Bessemer Cloud Index", "SaaStr Annual Survey",
            "Gartner Magic Quadrant", "Forrester Wave", "Public S-1 filings",
        ],
    },
    "fintech": {
        "key_metrics": [
            {"name": "AUM", "unit": "USD", "description": "Assets Under Management"},
            {"name": "NIM", "unit": "%", "description": "Net Interest Margin"},
            {"name": "Cost-to-Income", "unit": "%", "description": "Operating costs / operating income"},
            {"name": "NPL Ratio", "unit": "%", "description": "Non-performing loans / total loans"},
            {"name": "Customer Acquisition Cost", "unit": "USD", "description": "Cost to acquire one customer"},
            {"name": "Revenue Per User", "unit": "USD", "description": "Average revenue per customer"},
            {"name": "Regulatory Capital Ratio", "unit": "%", "description": "Capital / risk-weighted assets"},
        ],
        "competitive_frameworks": [
            {"name": "Porter's Five Forces", "dimensions": ["supplier_power", "buyer_power", "competitive_rivalry", "threat_of_substitution", "threat_of_new_entry"]},
            {"name": "Regulatory Moat Analysis", "dimensions": ["license_requirements", "compliance_cost", "regulatory_relationships"]},
            {"name": "Network Effects Map", "dimensions": ["direct_network_effects", "indirect_network_effects", "data_network_effects"]},
        ],
        "benchmarks": {
            "NIM": {"p25": 2.5, "p50": 3.5, "p75": 4.5, "mean": 3.5, "std": 1.2},
            "Cost-to-Income": {"p25": 65, "p50": 55, "p75": 45, "mean": 55, "std": 12},
            "NPL Ratio": {"p25": 3.0, "p50": 1.5, "p75": 0.8, "mean": 1.8, "std": 1.5},
        },
        "strategic_options": {
            "startup": [
                {"name": "Vertical Focus", "description": "Own one financial vertical completely", "investment": "low", "timeline": "6-12 months"},
                {"name": "API-First", "description": "Become infrastructure for other fintechs", "investment": "medium", "timeline": "12-18 months"},
            ],
            "growth": [
                {"name": "Banking License", "description": "Obtain full banking license", "investment": "very_high", "timeline": "18-36 months"},
                {"name": "Geographic Expansion", "description": "Enter new regulatory jurisdictions", "investment": "high", "timeline": "12-24 months"},
                {"name": "Product Diversification", "description": "Add lending, insurance, wealth management", "investment": "high", "timeline": "12-18 months"},
            ],
            "mature": [
                {"name": "Embedded Finance", "description": "White-label to non-financial companies", "investment": "medium", "timeline": "12-18 months"},
                {"name": "Acquisition Strategy", "description": "Acquire smaller fintechs and banks", "investment": "very_high", "timeline": "6-24 months"},
            ],
            "decline": [
                {"name": "Niche Specialization", "description": "Focus on underserved segments", "investment": "medium", "timeline": "12-18 months"},
                {"name": "Partnership or Sale", "description": "Merge with larger financial institution", "investment": "medium", "timeline": "6-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Regulatory Action", "probability": "medium", "impact": "critical", "mitigation": "Proactive compliance, regulatory counsel"},
            {"name": "Fraud Losses", "probability": "medium", "impact": "high", "mitigation": "ML-based fraud detection, insurance"},
            {"name": "Interest Rate Risk", "probability": "high", "impact": "medium", "mitigation": "Hedging, diversified revenue"},
            {"name": "Cybersecurity Breach", "probability": "medium", "impact": "critical", "mitigation": "SOC 2, penetration testing, incident response"},
        ],
        "evidence_sources": [
            "FDIC Call Reports", "SEC Filings", "CB Insights Fintech Report",
            "McKinsey Global Banking Review", "BIS Statistics",
        ],
    },
    "healthcare": {
        "key_metrics": [
            {"name": "Patient Volume", "unit": "patients", "description": "Number of patients served"},
            {"name": "Revenue Per Patient", "unit": "USD", "description": "Average revenue per patient encounter"},
            {"name": "Bed Occupancy Rate", "unit": "%", "description": "Beds occupied / total beds"},
            {"name": "Readmission Rate", "unit": "%", "description": "30-day readmission rate"},
            {"name": "Average Length of Stay", "unit": "days", "description": "Average hospital stay duration"},
            {"name": "Margin Per Case", "unit": "USD", "description": "Profit per patient case"},
        ],
        "competitive_frameworks": [
            {"name": "Value-Based Care Analysis", "dimensions": ["quality_scores", "cost_efficiency", "patient_satisfaction"]},
            {"name": "Porter's Five Forces", "dimensions": ["supplier_power", "buyer_power", "competitive_rivalry", "threat_of_substitution", "threat_of_new_entry"]},
        ],
        "benchmarks": {
            "Bed Occupancy": {"p25": 65, "p50": 75, "p75": 85, "mean": 75, "std": 10},
            "Readmission Rate": {"p25": 18, "p50": 15, "p75": 12, "mean": 15, "std": 4},
            "Avg Length of Stay": {"p25": 5.5, "p50": 4.5, "p75": 3.5, "mean": 4.5, "std": 1.5},
        },
        "strategic_options": {
            "startup": [
                {"name": "Telehealth First", "description": "Digital-first care delivery", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Specialty Focus", "description": "Own one specialty completely", "investment": "low", "timeline": "3-6 months"},
            ],
            "growth": [
                {"name": "ACO Formation", "description": "Form Accountable Care Organization", "investment": "high", "timeline": "12-24 months"},
                {"name": "Service Line Expansion", "description": "Add high-margin service lines", "investment": "high", "timeline": "12-18 months"},
                {"name": "Geographic Expansion", "description": "Open new facilities in underserved areas", "investment": "very_high", "timeline": "18-36 months"},
            ],
            "mature": [
                {"name": "Value-Based Care Transition", "description": "Shift from fee-for-service to outcomes-based", "investment": "high", "timeline": "24-48 months"},
                {"name": "M&A Integration", "description": "Acquire and integrate smaller providers", "investment": "very_high", "timeline": "12-24 months"},
            ],
            "decline": [
                {"name": "Service Rationalization", "description": "Focus on highest-margin services", "investment": "medium", "timeline": "6-12 months"},
                {"name": "System Affiliation", "description": "Join a larger health system", "investment": "medium", "timeline": "12-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Regulatory Change", "probability": "high", "impact": "high", "mitigation": "Government affairs team, compliance infrastructure"},
            {"name": "Reimbursement Cuts", "probability": "high", "impact": "high", "mitigation": "Diversify payer mix, cost reduction"},
            {"name": "Malpractice", "probability": "medium", "impact": "high", "mitigation": "Risk management, insurance, protocols"},
            {"name": "Workforce Shortage", "probability": "high", "impact": "high", "mitigation": "Retention programs, training pipelines"},
        ],
        "evidence_sources": [
            "CMS Medicare Data", "AHA Hospital Survey", "IQVIA Healthcare Reports",
            "Kaiser Family Foundation", "WHO Global Health Observatory",
        ],
    },
    "manufacturing": {
        "key_metrics": [
            {"name": "OEE", "unit": "%", "description": "Overall Equipment Effectiveness"},
            {"name": "Inventory Turns", "unit": "ratio", "description": "COGS / average inventory"},
            {"name": "Defect Rate", "unit": "ppm", "description": "Defects per million units"},
            {"name": "On-Time Delivery", "unit": "%", "description": "Orders delivered on time"},
            {"name": "Unit Cost", "unit": "USD", "description": "Cost per unit produced"},
            {"name": "Capacity Utilization", "unit": "%", "description": "Actual output / maximum output"},
        ],
        "competitive_frameworks": [
            {"name": "Value Chain Analysis", "dimensions": ["inbound_logistics", "operations", "outbound_logistics", "marketing", "service"]},
            {"name": "Lean Manufacturing Assessment", "dimensions": ["waste_reduction", "flow_efficiency", "quality", "flexibility"]},
        ],
        "benchmarks": {
            "OEE": {"p25": 65, "p50": 75, "p75": 85, "mean": 75, "std": 10},
            "Inventory Turns": {"p25": 4, "p50": 6, "p75": 10, "mean": 7, "std": 3},
            "Defect Rate": {"p25": 500, "p50": 100, "p75": 50, "mean": 200, "std": 200},
            "On-Time Delivery": {"p25": 85, "p50": 92, "p75": 97, "mean": 91, "std": 7},
        },
        "strategic_options": {
            "startup": [
                {"name": "Contract Manufacturing", "description": "Produce for established brands", "investment": "low", "timeline": "3-6 months"},
                {"name": "Niche Specialization", "description": "Own one product category", "investment": "low", "timeline": "6-12 months"},
            ],
            "growth": [
                {"name": "Vertical Integration", "description": "Bring supply chain in-house", "investment": "high", "timeline": "12-24 months"},
                {"name": "Automation Investment", "description": "Robotics and smart manufacturing", "investment": "very_high", "timeline": "18-36 months"},
                {"name": "Geographic Diversification", "description": "Manufacture in multiple regions", "investment": "very_high", "timeline": "24-48 months"},
            ],
            "mature": [
                {"name": "Industry 4.0 Transformation", "description": "IoT, AI, digital twin", "investment": "very_high", "timeline": "24-48 months"},
                {"name": "Servitization", "description": "Sell outcomes, not products", "investment": "high", "timeline": "18-36 months"},
            ],
            "decline": [
                {"name": "Lean Restructuring", "description": "Radical cost reduction", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Portfolio Rationalization", "description": "Focus on highest-margin products", "investment": "medium", "timeline": "6-12 months"},
            ],
        },
        "risk_factors": [
            {"name": "Supply Chain Disruption", "probability": "high", "impact": "high", "mitigation": "Dual sourcing, safety stock, nearshoring"},
            {"name": "Commodity Price Volatility", "probability": "high", "impact": "medium", "mitigation": "Hedging, long-term contracts"},
            {"name": "Technology Disruption", "probability": "medium", "impact": "high", "mitigation": "R&D investment, technology scouting"},
            {"name": "Trade Policy", "probability": "medium", "impact": "high", "mitigation": "Geographic diversification, government relations"},
        ],
        "evidence_sources": [
            "ISM Manufacturing Report", "BLS Producer Price Index", "WTO Trade Statistics",
            "McKinsey Global Manufacturing Report", "Deloitte Manufacturing Outlook",
        ],
    },
}


def _normalize_industry(industry: str) -> str:
    """Normalize industry string to a known playbook key."""
    lower = industry.lower().strip()
    mapping = {
        "saas": "saas", "software": "saas", "cloud": "saas", "b2b software": "saas",
        "fintech": "fintech", "financial technology": "fintech", "banking": "fintech", "insurance": "fintech",
        "healthcare": "healthcare", "health": "healthcare", "biotech": "healthcare", "pharma": "healthcare", "medical": "healthcare",
        "manufacturing": "manufacturing", "industrial": "manufacturing", "factory": "manufacturing",
        "retail": "manufacturing", "ecommerce": "manufacturing", "e-commerce": "manufacturing",
        "energy": "manufacturing", "oil": "manufacturing", "gas": "manufacturing", "utilities": "manufacturing",
        "cybersecurity": "saas", "security": "saas",
    }
    return mapping.get(lower, "saas")  # default to SaaS


def get_playbook(industry: str) -> dict:
    """Get industry-specific playbook."""
    key = _normalize_industry(industry)
    return _PLAYBOOKS.get(key, _PLAYBOOKS["saas"])


def get_kpis(industry: str) -> list[dict]:
    """Get KPI definitions for an industry."""
    return get_playbook(industry).get("key_metrics", [])


def get_competitive_frameworks(industry: str) -> list[dict]:
    """Get competitive frameworks for an industry."""
    return get_playbook(industry).get("competitive_frameworks", [])


def get_benchmarks(industry: str, metric: str) -> dict:
    """Get benchmark data for a specific metric."""
    benchmarks = get_playbook(industry).get("benchmarks", {})
    return benchmarks.get(metric, {"p25": 0, "p50": 0, "p75": 0, "mean": 0, "std": 0})


def get_strategic_options(industry: str, stage: str) -> list[dict]:
    """Get strategic options for an industry + stage."""
    options = get_playbook(industry).get("strategic_options", {})
    return options.get(stage, [])


def get_risk_factors(industry: str) -> list[dict]:
    """Get industry-specific risk factors."""
    return get_playbook(industry).get("risk_factors", [])


def compare_to_benchmark(company_metrics: dict, industry: str) -> list[dict]:
    """Compare company metrics to industry benchmarks."""
    benchmarks = get_playbook(industry).get("benchmarks", {})
    results = []

    for metric, value in company_metrics.items():
        if metric in benchmarks and isinstance(value, (int, float)):
            b = benchmarks[metric]
            mean = b.get("mean", 0)
            std = b.get("std", 1) or 1

            # Compute percentile (approximate using normal distribution)
            if std > 0:
                z = (value - mean) / std
                # Approximate CDF using error function
                percentile = round(0.5 * (1 + math.erf(z / math.sqrt(2))) * 100, 1)
            else:
                percentile = 50.0

            if percentile >= 75:
                assessment = "above_average"
            elif percentile >= 25:
                assessment = "average"
            else:
                assessment = "below_average"

            results.append({
                "metric": metric,
                "company_value": value,
                "benchmark_p50": b.get("p50", mean),
                "benchmark_mean": mean,
                "percentile": percentile,
                "assessment": assessment,
            })

    return results