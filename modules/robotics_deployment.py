"""
Robotics Deployment Tracker — Monitor global robotics adoption across industrial,
service, and humanoid robot categories.

Tracks key companies (Boston Dynamics, Figure, Tesla Optimus), deployment stats,
IFR data, and sector growth. Uses free public data from IFR, BLS, and company reports.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


ROBOTICS_COMPANIES = {
    "Tesla (Optimus)": {
        "category": "Humanoid", "ticker": "TSLA", "status": "Prototype/Testing",
        "units_deployed": 100, "focus": "General-purpose humanoid for factories & homes",
        "target_price_usd": 20000,
    },
    "Figure AI": {
        "category": "Humanoid", "ticker": None, "status": "Pilot Deployments",
        "units_deployed": 50, "focus": "Commercial humanoid (BMW partnership)",
        "funding_m": 754,
    },
    "Boston Dynamics": {
        "category": "Multi-form", "ticker": "HYN.AS", "status": "Commercial",
        "units_deployed": 1500, "focus": "Spot (quadruped), Atlas (humanoid), Stretch (logistics)",
    },
    "Agility Robotics": {
        "category": "Humanoid", "ticker": None, "status": "Pilot (Amazon)",
        "units_deployed": 20, "focus": "Digit humanoid for warehouse logistics",
        "funding_m": 200,
    },
    "Fanuc": {
        "category": "Industrial", "ticker": "6954.T", "status": "Commercial",
        "units_deployed": 800000, "focus": "Industrial arms, CNC, factory automation",
    },
    "ABB Robotics": {
        "category": "Industrial", "ticker": "ABB", "status": "Commercial",
        "units_deployed": 500000, "focus": "Industrial arms, collaborative robots (cobots)",
    },
    "KUKA (Midea)": {
        "category": "Industrial", "ticker": "000333.SZ", "status": "Commercial",
        "units_deployed": 400000, "focus": "Automotive & general industrial robots",
    },
    "Universal Robots": {
        "category": "Collaborative", "ticker": "TER", "status": "Commercial",
        "units_deployed": 75000, "focus": "Cobots for SMEs, flexible manufacturing",
    },
    "Intuitive Surgical": {
        "category": "Medical", "ticker": "ISRG", "status": "Commercial",
        "units_deployed": 9000, "focus": "Da Vinci surgical robots",
    },
    "iRobot": {
        "category": "Consumer", "ticker": "IRBT", "status": "Commercial",
        "units_deployed": 40000000, "focus": "Roomba consumer cleaning robots",
    },
}

GLOBAL_STATS = {
    "industrial_robots_installed_2023": 3900000,
    "new_installations_2023": 540000,
    "top_markets": ["China (52%)", "Japan (9%)", "USA (7%)", "South Korea (7%)", "Germany (6%)"],
    "robot_density_top5": {
        "South Korea": 1012,
        "Singapore": 730,
        "Germany": 415,
        "Japan": 397,
        "China": 392,
    },
    "yoy_growth_pct": 7,
    "source": "International Federation of Robotics (IFR) 2024 Report",
}


def get_robotics_companies(category_filter: Optional[str] = None) -> List[Dict]:
    """
    Get tracked robotics companies with deployment and market data.

    Args:
        category_filter: Optional filter ('Humanoid', 'Industrial', 'Medical', etc.)

    Returns:
        List of robotics company dictionaries
    """
    results = []
    for name, info in ROBOTICS_COMPANIES.items():
        if category_filter and category_filter.lower() != info["category"].lower():
            continue
        results.append({"company": name, **info})
    results.sort(key=lambda x: x["units_deployed"], reverse=True)
    return results


def get_robotics_market_summary() -> Dict:
    """
    Get global robotics market summary with IFR stats and company breakdown.

    Returns:
        Dict with market stats, category breakdown, public tickers
    """
    by_category = {}
    for name, info in ROBOTICS_COMPANIES.items():
        cat = info["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    public = [{"company": n, "ticker": c["ticker"]} for n, c in ROBOTICS_COMPANIES.items() if c.get("ticker")]

    return {
        "global_stats": GLOBAL_STATS,
        "tracked_companies": len(ROBOTICS_COMPANIES),
        "by_category": by_category,
        "public_tickers": public,
        "humanoid_race": [
            {"company": n, "units": c["units_deployed"], "status": c["status"]}
            for n, c in ROBOTICS_COMPANIES.items() if c["category"] == "Humanoid"
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_robot_density_rankings() -> Dict[str, int]:
    """
    Get robot density rankings (robots per 10,000 manufacturing workers) by country.

    Returns:
        Dict mapping country to robot density
    """
    return GLOBAL_STATS["robot_density_top5"].copy()


def get_humanoid_progress() -> List[Dict]:
    """
    Get focused view of humanoid robot development race.

    Returns:
        List of humanoid robot projects with status and deployment numbers
    """
    humanoids = []
    for name, info in ROBOTICS_COMPANIES.items():
        if info["category"] == "Humanoid":
            humanoids.append({
                "company": name,
                "status": info["status"],
                "units_deployed": info["units_deployed"],
                "focus": info["focus"],
                "ticker": info.get("ticker"),
                "funding_m": info.get("funding_m"),
                "target_price": info.get("target_price_usd"),
            })
    humanoids.sort(key=lambda x: x["units_deployed"], reverse=True)
    return humanoids


if __name__ == "__main__":
    summary = get_robotics_market_summary()
    print(f"Global robots installed: {GLOBAL_STATS['industrial_robots_installed_2023']:,}")
    print(f"Tracked companies: {summary['tracked_companies']}")
    print("Humanoid race:")
    for h in get_humanoid_progress():
        print(f"  {h['company']}: {h['units_deployed']} units ({h['status']})")
