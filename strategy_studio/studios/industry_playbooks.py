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


# ── Additional Industries (added in v2) ────────────────────────────────────

_PLAYBOOKS.update({
    "retail": {
        "key_metrics": [
            {"name": "Same-Store Sales Growth", "unit": "%", "description": "Year-over-year comparable store sales"},
            {"name": "GMV", "unit": "USD", "description": "Gross Merchandise Value"},
            {"name": "Conversion Rate", "unit": "%", "description": "Visitors who make a purchase"},
            {"name": "AOV", "unit": "USD", "description": "Average Order Value"},
            {"name": "CAC", "unit": "USD", "description": "Customer Acquisition Cost"},
            {"name": "Inventory Turns", "unit": "ratio", "description": "COGS / average inventory"},
            {"name": "NPS", "unit": "score", "description": "Net Promoter Score"},
        ],
        "competitive_frameworks": [
            {"name": "Porter's Five Forces", "dimensions": ["supplier_power", "buyer_power", "competitive_rivalry", "threat_of_substitution", "threat_of_new_entry"]},
            {"name": "Omnichannel Assessment", "dimensions": ["online_experience", "store_experience", "fulfillment", "returns", "loyalty"]},
        ],
        "benchmarks": {
            "Same-Store Sales Growth": {"p25": -2, "p50": 3, "p75": 7, "mean": 3, "std": 5},
            "Conversion Rate": {"p25": 1.5, "p50": 3.0, "p75": 5.0, "mean": 3.2, "std": 2.0},
            "AOV": {"p25": 45, "p50": 75, "p75": 120, "mean": 85, "std": 40},
            "NPS": {"p25": 20, "p50": 40, "p75": 60, "mean": 40, "std": 20},
        },
        "strategic_options": {
            "startup": [
                {"name": "DTC First", "description": "Direct-to-consumer, own the relationship", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Marketplace Arbitrage", "description": "Sell through established platforms first", "investment": "low", "timeline": "1-3 months"},
            ],
            "growth": [
                {"name": "Omnichannel Expansion", "description": "Add physical stores, pickup, delivery", "investment": "very_high", "timeline": "12-24 months"},
                {"name": "Private Label", "description": "Launch owned brands for higher margins", "investment": "high", "timeline": "12-18 months"},
                {"name": "Geographic Expansion", "description": "Enter new markets or regions", "investment": "high", "timeline": "12-24 months"},
            ],
            "mature": [
                {"name": "Digital Transformation", "description": "Modernize tech stack, AI personalization", "investment": "very_high", "timeline": "18-36 months"},
                {"name": "M&A Consolidation", "description": "Acquire smaller retailers", "investment": "very_high", "timeline": "6-18 months"},
            ],
            "decline": [
                {"name": "Store Rationalization", "description": "Close underperforming locations", "investment": "medium", "timeline": "6-12 months"},
                {"name": "E-commerce Pivot", "description": "Shift focus to online channels", "investment": "high", "timeline": "12-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Consumer Spending Decline", "probability": "medium", "impact": "high", "mitigation": "Diversify price points, value offerings"},
            {"name": "Supply Chain Disruption", "probability": "high", "impact": "high", "mitigation": "Multi-source suppliers, safety stock"},
            {"name": "Amazon Competition", "probability": "high", "impact": "critical", "mitigation": "Differentiate on experience, curation, service"},
        ],
        "evidence_sources": ["Census Bureau Retail Sales", "NRF State of Retail", "eMarketer Digital Commerce"],
    },
    "energy": {
        "key_metrics": [
            {"name": "Production Volume", "unit": "BOE/day", "description": "Barrels of oil equivalent per day"},
            {"name": "Reserve Replacement Ratio", "unit": "%", "description": "New reserves / production"},
            {"name": "Finding & Development Cost", "unit": "$/BOE", "description": "Cost to find and develop new reserves"},
            {"name": "Operating Cost per BOE", "unit": "$/BOE", "description": "Production cost per barrel"},
            {"name": "Carbon Intensity", "unit": "kgCO2/BOE", "description": "Emissions per unit of production"},
            {"name": "ROACE", "unit": "%", "description": "Return on average capital employed"},
        ],
        "competitive_frameworks": [
            {"name": "Porter's Five Forces", "dimensions": ["supplier_power", "buyer_power", "competitive_rivalry", "threat_of_substitution", "threat_of_new_entry"]},
            {"name": "Energy Transition Readiness", "dimensions": ["renewable_portfolio", "carbon_exposure", "technology_readiness", "regulatory_position"]},
        ],
        "benchmarks": {
            "Reserve Replacement": {"p25": 80, "p50": 100, "p75": 130, "mean": 105, "std": 30},
            "OpCost per BOE": {"p25": 15, "p50": 10, "p75": 7, "mean": 11, "std": 5},
            "ROACE": {"p25": 5, "p50": 10, "p75": 15, "mean": 10, "std": 6},
        },
        "strategic_options": {
            "startup": [
                {"name": "Niche Technology", "description": "Own one breakthrough technology", "investment": "high", "timeline": "12-24 months"},
                {"name": "Service Model", "description": "Provide services to incumbents", "investment": "low", "timeline": "3-6 months"},
            ],
            "growth": [
                {"name": "Renewable Portfolio Build", "description": "Invest in solar, wind, storage", "investment": "very_high", "timeline": "24-48 months"},
                {"name": "Strategic Acquisition", "description": "Acquire reserves or technology", "investment": "very_high", "timeline": "6-18 months"},
            ],
            "mature": [
                {"name": "Energy Transition Pivot", "description": "Shift from fossil to renewable", "investment": "very_high", "timeline": "36-60 months"},
                {"name": "Portfolio Optimization", "description": "Divest non-core assets", "investment": "medium", "timeline": "12-24 months"},
            ],
            "decline": [
                {"name": "Harvest Strategy", "description": "Maximize cash flow from existing assets", "investment": "low", "timeline": "6-12 months"},
                {"name": "Merger or Sale", "description": "Combine with larger player", "investment": "medium", "timeline": "6-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Commodity Price Volatility", "probability": "high", "impact": "critical", "mitigation": "Hedging, diversified portfolio"},
            {"name": "Regulatory Change", "probability": "high", "impact": "high", "mitigation": "Proactive compliance, government relations"},
            {"name": "Energy Transition Risk", "probability": "high", "impact": "critical", "mitigation": "Diversify into renewables early"},
        ],
        "evidence_sources": ["IEA World Energy Outlook", "EIA Annual Energy Review", "OPEC Monthly Report"],
    },
    "biotech": {
        "key_metrics": [
            {"name": "Pipeline Value", "unit": "USD", "description": "NPV of all pipeline assets"},
            {"name": "R&D Spend as % of Revenue", "unit": "%", "description": "Research spend relative to revenue"},
            {"name": "Time to Market", "unit": "years", "description": "Average drug development timeline"},
            {"name": "Clinical Trial Success Rate", "unit": "%", "description": "Phase 1 to approval rate"},
            {"name": "Patent Life Remaining", "unit": "years", "description": "Years of patent protection left"},
            {"name": "Gross Margin", "unit": "%", "description": "Gross profit / revenue"},
        ],
        "competitive_frameworks": [
            {"name": "Pipeline Strength Assessment", "dimensions": ["phase_diversity", "therapeutic_areas", "first_in_class", "market_size"]},
            {"name": "Patent Cliff Analysis", "dimensions": ["patent_expiry_timeline", "generic_threat", "biosimilar_risk"]},
        ],
        "benchmarks": {
            "R&D as % Revenue": {"p25": 15, "p50": 25, "p75": 40, "mean": 28, "std": 15},
            "Clinical Success Rate": {"p25": 5, "p50": 10, "p75": 20, "mean": 12, "std": 10},
            "Gross Margin": {"p25": 60, "p50": 75, "p75": 85, "mean": 73, "std": 12},
        },
        "strategic_options": {
            "startup": [
                {"name": "Platform Technology", "description": "Build a platform, not just a product", "investment": "high", "timeline": "12-24 months"},
                {"name": "Licensing In", "description": "License promising compounds from academia", "investment": "medium", "timeline": "6-12 months"},
            ],
            "growth": [
                {"name": "M&A for Pipeline", "description": "Acquire companies with complementary pipeline", "investment": "very_high", "timeline": "6-18 months"},
                {"name": "Partnership Deals", "description": "Co-develop with big pharma", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Geographic Expansion", "description": "Enter new regulatory markets", "investment": "high", "timeline": "12-24 months"},
            ],
            "mature": [
                {"name": "Biosimilar Defense", "description": "Prepare for patent cliff with next-gen products", "investment": "high", "timeline": "24-48 months"},
                {"name": "Diversification", "description": "Enter adjacent therapeutic areas", "investment": "very_high", "timeline": "24-36 months"},
            ],
            "decline": [
                {"name": "Pipeline Pruning", "description": "Focus on highest-probability assets", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Licensing Out", "description": "Monetize non-core IP", "investment": "low", "timeline": "3-6 months"},
            ],
        },
        "risk_factors": [
            {"name": "Clinical Trial Failure", "probability": "high", "impact": "critical", "mitigation": "Diversified pipeline, adaptive trial design"},
            {"name": "Regulatory Rejection", "probability": "medium", "impact": "critical", "mitigation": "Early FDA engagement, robust data"},
            {"name": "Patent Cliff", "probability": "high", "impact": "high", "mitigation": "Next-gen product pipeline, lifecycle management"},
        ],
        "evidence_sources": ["FDA Orange Book", "ClinicalTrials.gov", "EvaluatePharma", "BIO Industry Analysis"],
    },
    "cybersecurity": {
        "key_metrics": [
            {"name": "ARR", "unit": "USD", "description": "Annual Recurring Revenue"},
            {"name": "NRR", "unit": "%", "description": "Net Revenue Retention"},
            {"name": "MTTR", "unit": "hours", "description": "Mean Time to Respond/Remediate"},
            {"name": "Detection Rate", "unit": "%", "description": "Threats detected / total threats"},
            {"name": "False Positive Rate", "unit": "%", "description": "False alerts / total alerts"},
            {"name": "CAC Payback", "unit": "months", "description": "Customer acquisition cost payback period"},
        ],
        "competitive_frameworks": [
            {"name": "MITRE ATT&CK Coverage", "dimensions": ["technique_coverage", "detection_depth", "response_speed"]},
            {"name": "Zero Trust Maturity", "dimensions": ["identity", "devices", "networks", "applications", "data"]},
        ],
        "benchmarks": {
            "NRR": {"p25": 105, "p50": 115, "p75": 130, "mean": 116, "std": 15},
            "MTTR": {"p25": 48, "p50": 24, "p75": 8, "mean": 25, "std": 20},
            "Detection Rate": {"p25": 85, "p50": 92, "p75": 97, "mean": 91, "std": 8},
            "CAC Payback": {"p25": 18, "p50": 12, "p75": 8, "mean": 13, "std": 6},
        },
        "strategic_options": {
            "startup": [
                {"name": "Point Solution", "description": "Own one security problem completely", "investment": "low", "timeline": "3-6 months"},
                {"name": "Open Source Core", "description": "Build community around open-source tool", "investment": "low", "timeline": "6-12 months"},
            ],
            "growth": [
                {"name": "Platform Consolidation", "description": "Become the single pane of glass", "investment": "high", "timeline": "12-24 months"},
                {"name": "MDR Services", "description": "Add managed detection and response", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Vertical Specialization", "description": "Focus on one industry vertical", "investment": "medium", "timeline": "6-12 months"},
            ],
            "mature": [
                {"name": "XDR Platform", "description": "Extended detection and response across all vectors", "investment": "very_high", "timeline": "18-36 months"},
                {"name": "M&A Rollup", "description": "Acquire point solution companies", "investment": "very_high", "timeline": "6-18 months"},
            ],
            "decline": [
                {"name": "Niche Focus", "description": "Own one underserved segment", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Platform Integration", "description": "Become a feature of larger platform", "investment": "medium", "timeline": "12-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Zero-Day Exploits", "probability": "high", "impact": "critical", "mitigation": "Threat intelligence, rapid patching"},
            {"name": "Platform Consolidation", "probability": "high", "impact": "high", "mitigation": "Differentiate on depth, vertical expertise"},
            {"name": "Talent Shortage", "probability": "high", "impact": "high", "mitigation": "Automation, managed services, training"},
        ],
        "evidence_sources": ["Gartner Magic Quadrant", "MITRE ATT&CK", "NIST Cybersecurity Framework", "CrowdStrike Global Threat Report"],
    },
    "marketplace": {
        "key_metrics": [
            {"name": "GMV", "unit": "USD", "description": "Gross Merchandise Value"},
            {"name": "Take Rate", "unit": "%", "description": "Revenue / GMV"},
            {"name": "Liquidity", "unit": "%", "description": "Supply-demand match rate"},
            {"name": "NPS (Supply)", "unit": "score", "description": "Supplier Net Promoter Score"},
            {"name": "NPS (Demand)", "unit": "score", "description": "Buyer Net Promoter Score"},
            {"name": "CAC (Blended)", "unit": "USD", "description": "Blended customer acquisition cost"},
        ],
        "competitive_frameworks": [
            {"name": "Network Effects Map", "dimensions": ["direct_effects", "indirect_effects", "data_effects", "platform_effects"]},
            {"name": "Liquidity Analysis", "dimensions": ["time_to_fill", "match_rate", "depth_of_supply", "demand_concentration"]},
        ],
        "benchmarks": {
            "Take Rate": {"p25": 10, "p50": 15, "p75": 25, "mean": 17, "std": 8},
            "Liquidity": {"p25": 60, "p50": 75, "p75": 85, "mean": 73, "std": 12},
            "NPS (Demand)": {"p25": 20, "p50": 40, "p75": 60, "mean": 40, "std": 20},
        },
        "strategic_options": {
            "startup": [
                {"name": "Chicken-Egg Solution", "description": "Seed supply or demand side first", "investment": "medium", "timeline": "3-6 months"},
                {"name": "Single-Sided First", "description": "Build value for one side before opening to other", "investment": "low", "timeline": "1-3 months"},
            ],
            "growth": [
                {"name": "Geographic Expansion", "description": "Launch in new cities or markets", "investment": "high", "timeline": "6-12 months"},
                {"name": "Vertical Expansion", "description": "Add adjacent categories", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Supply Investment", "description": "Invest in supply-side quality and depth", "investment": "high", "timeline": "12-18 months"},
            ],
            "mature": [
                {"name": "Platform Ecosystem", "description": "Open platform to third-party developers", "investment": "high", "timeline": "12-24 months"},
                {"name": "Vertical Integration", "description": "Own more of the value chain", "investment": "very_high", "timeline": "18-36 months"},
            ],
            "decline": [
                {"name": "Niche Focus", "description": "Own one high-liquidity vertical", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Marketplace-as-a-Service", "description": "License technology to others", "investment": "medium", "timeline": "12-18 months"},
            ],
        },
        "risk_factors": [
            {"name": "Multi-Tenancy", "probability": "high", "impact": "high", "mitigation": "Lock-in through data, workflow integration"},
            {"name": "Disintermediation", "probability": "medium", "impact": "critical", "mitigation": "Add value beyond matching, escrow, insurance"},
            {"name": "Regulatory Risk", "probability": "medium", "impact": "high", "mitigation": "Proactive compliance, legal framework"},
        ],
        "evidence_sources": ["a16z Marketplace Index", "Bessemer Marketplace Benchmarks", "Platform Hunt Data"],
    },
    "logistics": {
        "key_metrics": [
            {"name": "Cost per Shipment", "unit": "USD", "description": "Total cost / number of shipments"},
            {"name": "On-Time Delivery Rate", "unit": "%", "description": "Shipments delivered on time"},
            {"name": "Capacity Utilization", "unit": "%", "description": "Actual volume / max capacity"},
            {"name": "Damage/Loss Rate", "unit": "%", "description": "Damaged or lost shipments"},
            {"name": "Revenue per Route", "unit": "USD", "description": "Average revenue per delivery route"},
            {"name": "Fleet Utilization", "unit": "%", "description": "Vehicles in use / total fleet"},
        ],
        "competitive_frameworks": [
            {"name": "Network Density Analysis", "dimensions": ["route_coverage", "hub_efficiency", "last_mile_density", "cross_dock_speed"]},
            {"name": "Last-Mile Optimization", "dimensions": ["delivery_speed", "cost_per_drop", "customer_experience", "flexibility"]},
        ],
        "benchmarks": {
            "On-Time Delivery": {"p25": 88, "p50": 94, "p75": 98, "mean": 93, "std": 5},
            "Capacity Utilization": {"p25": 70, "p50": 80, "p75": 90, "mean": 80, "std": 10},
            "Damage Rate": {"p25": 2.0, "p50": 0.8, "p75": 0.3, "mean": 1.0, "std": 1.2},
            "Fleet Utilization": {"p25": 65, "p50": 75, "p75": 85, "mean": 75, "std": 10},
        },
        "strategic_options": {
            "startup": [
                {"name": "Niche Route Focus", "description": "Own one high-value route or lane", "investment": "low", "timeline": "1-3 months"},
                {"name": "Asset-Light Model", "description": "Broker capacity, don't own assets", "investment": "low", "timeline": "1-3 months"},
            ],
            "growth": [
                {"name": "Network Expansion", "description": "Add routes, hubs, and geographies", "investment": "high", "timeline": "12-24 months"},
                {"name": "Technology Platform", "description": "Build proprietary routing and tracking tech", "investment": "high", "timeline": "12-18 months"},
                {"name": "Vertical Specialization", "description": "Focus on one industry vertical", "investment": "medium", "timeline": "6-12 months"},
            ],
            "mature": [
                {"name": "Autonomous Fleet", "description": "Invest in autonomous vehicles and drones", "investment": "very_high", "timeline": "24-48 months"},
                {"name": "Global Expansion", "description": "Enter international markets", "investment": "very_high", "timeline": "24-36 months"},
            ],
            "decline": [
                {"name": "Route Optimization", "description": "Focus on highest-margin routes", "investment": "medium", "timeline": "6-12 months"},
                {"name": "Asset Sale", "description": "Sell fleet and transition to broker model", "investment": "medium", "timeline": "6-12 months"},
            ],
        },
        "risk_factors": [
            {"name": "Fuel Price Volatility", "probability": "high", "impact": "high", "mitigation": "Fuel surcharges, electric fleet transition"},
            {"name": "Driver Shortage", "probability": "high", "impact": "high", "mitigation": "Competitive pay, automation, gig model"},
            {"name": "E-commerce Volume Shifts", "probability": "medium", "impact": "high", "mitigation": "Diversify customer base, flexible capacity"},
        ],
        "evidence_sources": ["ATA Freight Transportation Report", "CBRE Logistics Report", "DHL Global Connectedness Index"],
    },
})

# Update normalization mapping
_NORMALIZE_MAP = {
    "saas": "saas", "software": "saas", "cloud": "saas", "b2b software": "saas",
    "fintech": "fintech", "financial technology": "fintech", "banking": "fintech", "insurance": "fintech",
    "healthcare": "healthcare", "health": "healthcare", "biotech": "biotech", "pharma": "healthcare", "medical": "healthcare",
    "manufacturing": "manufacturing", "industrial": "manufacturing", "factory": "manufacturing",
    "retail": "retail", "ecommerce": "retail", "e-commerce": "retail", "consumer": "retail",
    "energy": "energy", "oil": "energy", "gas": "energy", "utilities": "energy", "renewable": "energy",
    "cybersecurity": "cybersecurity", "security": "cybersecurity", "infosec": "cybersecurity",
    "marketplace": "marketplace", "platform": "marketplace", "two-sided": "marketplace",
    "logistics": "logistics", "shipping": "logistics", "freight": "logistics", "supply chain": "logistics", "delivery": "logistics",
}


def _normalize_industry(industry: str) -> str:
    """Normalize industry string to a known playbook key."""
    lower = industry.lower().strip()
    return _NORMALIZE_MAP.get(lower, "saas")  # default to SaaS