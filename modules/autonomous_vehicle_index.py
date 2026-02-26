"""
Autonomous Vehicle Adoption Index — Track AV deployment, regulatory progress,
key companies, and adoption metrics using public data sources.
Roadmap #394.
"""

import datetime
from typing import Dict, List, Optional

AV_COMPANIES = [
    {"name": "Waymo", "parent": "Alphabet", "level": 4, "status": "commercial", "cities": ["Phoenix", "San Francisco", "Los Angeles", "Austin"], "rides_per_week_est": 150000},
    {"name": "Cruise", "parent": "GM", "level": 4, "status": "suspended", "cities": [], "rides_per_week_est": 0},
    {"name": "Tesla FSD", "parent": "Tesla", "ticker": "TSLA", "level": 3, "status": "beta", "cities": ["nationwide_US"], "rides_per_week_est": None},
    {"name": "Baidu Apollo", "parent": "Baidu", "ticker": "BIDU", "level": 4, "status": "commercial", "cities": ["Beijing", "Wuhan", "Shenzhen"], "rides_per_week_est": 80000},
    {"name": "Pony.ai", "parent": None, "ticker": "PONY", "level": 4, "status": "commercial", "cities": ["Beijing", "Guangzhou"], "rides_per_week_est": 20000},
    {"name": "Mobileye", "parent": "Intel", "ticker": "MBLY", "level": 3, "status": "testing", "cities": ["Munich", "Detroit"], "rides_per_week_est": 0},
    {"name": "Aurora", "parent": None, "ticker": "AUR", "level": 4, "status": "commercial_trucking", "cities": ["Dallas-Houston corridor"], "rides_per_week_est": 5000},
    {"name": "Zoox", "parent": "Amazon", "level": 4, "status": "testing", "cities": ["Las Vegas", "Foster City"], "rides_per_week_est": 0},
    {"name": "Nuro", "parent": None, "level": 4, "status": "commercial_delivery", "cities": ["Houston", "Mountain View"], "rides_per_week_est": 3000},
]

REGULATORY_STATUS = [
    {"jurisdiction": "California", "robotaxi_permitted": True, "trucking_permitted": True, "notes": "Post-Cruise review ongoing"},
    {"jurisdiction": "Arizona", "robotaxi_permitted": True, "trucking_permitted": True, "notes": "Most permissive US state"},
    {"jurisdiction": "Texas", "robotaxi_permitted": True, "trucking_permitted": True, "notes": "No special AV permit required"},
    {"jurisdiction": "China", "robotaxi_permitted": True, "trucking_permitted": True, "notes": "City-by-city permits, 20+ cities"},
    {"jurisdiction": "EU", "robotaxi_permitted": False, "trucking_permitted": False, "notes": "Framework expected 2026"},
    {"jurisdiction": "UK", "robotaxi_permitted": False, "trucking_permitted": False, "notes": "Automated Vehicles Act 2024"},
]


def get_av_landscape() -> Dict:
    """Get overview of autonomous vehicle industry — companies, status, regulations."""
    commercial = [c for c in AV_COMPANIES if "commercial" in c["status"]]
    total_rides = sum(c["rides_per_week_est"] or 0 for c in AV_COMPANIES)
    public_tickers = [{"name": c["name"], "ticker": c.get("ticker")} for c in AV_COMPANIES if c.get("ticker")]

    return {
        "total_companies": len(AV_COMPANIES),
        "commercial_operators": len(commercial),
        "est_weekly_rides_global": total_rides,
        "public_tickers": public_tickers,
        "regulatory_summary": REGULATORY_STATUS,
        "companies": AV_COMPANIES,
    }


def get_company_detail(name: str) -> Optional[Dict]:
    """Get detailed info on a specific AV company."""
    for c in AV_COMPANIES:
        if c["name"].lower() == name.lower():
            return c
    return None


def get_adoption_metrics() -> Dict:
    """Calculate aggregate adoption metrics for the AV sector."""
    total_cities = set()
    for c in AV_COMPANIES:
        for city in c.get("cities", []):
            if city != "nationwide_US":
                total_cities.add(city)

    commercial = [c for c in AV_COMPANIES if "commercial" in c["status"]]
    total_weekly = sum(c["rides_per_week_est"] or 0 for c in AV_COMPANIES)

    return {
        "unique_cities_with_av": len(total_cities),
        "commercial_operators": len(commercial),
        "est_weekly_autonomous_rides": total_weekly,
        "est_annual_rides": total_weekly * 52,
        "jurisdictions_permitting_robotaxi": sum(1 for r in REGULATORY_STATUS if r["robotaxi_permitted"]),
    }
