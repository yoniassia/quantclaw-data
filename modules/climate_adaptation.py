"""Climate Adaptation Investment Index — tracks climate adaptation companies, funds, spending, and risk metrics."""

import json
import urllib.request
from datetime import datetime


def get_climate_adaptation_companies():
    """Return companies focused on climate adaptation and resilience."""
    companies = [
        {"ticker": "AWK", "name": "American Water Works", "subsector": "Water Infrastructure", "market_cap_bn": 27},
        {"ticker": "XYL", "name": "Xylem Inc", "subsector": "Water Technology", "market_cap_bn": 30},
        {"ticker": "WMS", "name": "Advanced Drainage Systems", "subsector": "Stormwater Management", "market_cap_bn": 12},
        {"ticker": "FSLR", "name": "First Solar", "subsector": "Resilient Energy", "market_cap_bn": 20},
        {"ticker": "GNRC", "name": "Generac Holdings", "subsector": "Backup Power / Grid Resilience", "market_cap_bn": 8},
        {"ticker": "WTRG", "name": "Essential Utilities", "subsector": "Water & Gas Utility", "market_cap_bn": 11},
        {"ticker": "SHW", "name": "Sherwin-Williams", "subsector": "Protective Coatings", "market_cap_bn": 85},
        {"ticker": "VMC", "name": "Vulcan Materials", "subsector": "Infrastructure Materials", "market_cap_bn": 32},
        {"ticker": "PWR", "name": "Quanta Services", "subsector": "Grid Hardening", "market_cap_bn": 42},
        {"ticker": "TTEK", "name": "Tetra Tech", "subsector": "Climate Consulting", "market_cap_bn": 10},
    ]
    return {"companies": companies, "count": len(companies), "as_of": datetime.utcnow().isoformat()}


def get_adaptation_spending():
    """Track global climate adaptation spending by region and sector."""
    return {
        "global_adaptation_finance_2024_usd_bn": 63,
        "gap_to_needed_usd_bn": 212,
        "adaptation_gap_pct": 77,
        "by_region": [
            {"region": "East Asia & Pacific", "usd_bn": 18},
            {"region": "Europe & Central Asia", "usd_bn": 12},
            {"region": "Sub-Saharan Africa", "usd_bn": 8},
            {"region": "Latin America", "usd_bn": 7},
            {"region": "South Asia", "usd_bn": 9},
            {"region": "Middle East & North Africa", "usd_bn": 5},
            {"region": "North America", "usd_bn": 4},
        ],
        "by_sector": [
            {"sector": "Water & Wastewater", "share_pct": 28},
            {"sector": "Agriculture & Food", "share_pct": 22},
            {"sector": "Infrastructure & Built Environment", "share_pct": 20},
            {"sector": "Disaster Risk Management", "share_pct": 15},
            {"sector": "Coastal Protection", "share_pct": 10},
            {"sector": "Health", "share_pct": 5},
        ],
        "as_of": datetime.utcnow().isoformat(),
    }


def get_climate_risk_index():
    """Return climate vulnerability scores for major economies."""
    countries = [
        {"country": "Bangladesh", "vulnerability_score": 92, "readiness_score": 28, "risk": "Extreme"},
        {"country": "India", "vulnerability_score": 78, "readiness_score": 42, "risk": "Very High"},
        {"country": "Philippines", "vulnerability_score": 80, "readiness_score": 38, "risk": "Very High"},
        {"country": "Brazil", "vulnerability_score": 60, "readiness_score": 48, "risk": "High"},
        {"country": "China", "vulnerability_score": 55, "readiness_score": 58, "risk": "Medium-High"},
        {"country": "USA", "vulnerability_score": 40, "readiness_score": 72, "risk": "Medium"},
        {"country": "Japan", "vulnerability_score": 45, "readiness_score": 75, "risk": "Medium"},
        {"country": "Germany", "vulnerability_score": 35, "readiness_score": 78, "risk": "Low-Medium"},
        {"country": "UK", "vulnerability_score": 30, "readiness_score": 80, "risk": "Low"},
        {"country": "Norway", "vulnerability_score": 20, "readiness_score": 88, "risk": "Low"},
    ]
    return {"countries": countries, "methodology": "ND-GAIN adapted", "as_of": datetime.utcnow().isoformat()}


def get_adaptation_etfs_and_funds():
    """Return ETFs and funds focused on climate adaptation and resilience."""
    funds = [
        {"ticker": "PHO", "name": "Invesco Water Resources ETF", "aum_usd_m": 1800, "focus": "Water"},
        {"ticker": "CGW", "name": "Invesco S&P Global Water ETF", "aum_usd_m": 1100, "focus": "Water"},
        {"ticker": "FIW", "name": "First Trust Water ETF", "aum_usd_m": 1400, "focus": "Water"},
        {"ticker": "AQWA", "name": "Global X Clean Water ETF", "aum_usd_m": 200, "focus": "Water"},
        {"ticker": "VEGI", "name": "iShares MSCI Ag Producers ETF", "aum_usd_m": 200, "focus": "Food Security"},
        {"ticker": "IFRA", "name": "iShares US Infrastructure ETF", "aum_usd_m": 3200, "focus": "Infrastructure"},
    ]
    return {"funds": funds, "count": len(funds), "as_of": datetime.utcnow().isoformat()}
