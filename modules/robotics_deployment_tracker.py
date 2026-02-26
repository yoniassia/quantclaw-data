"""
Robotics Deployment Tracker — Monitor industrial and humanoid robotics adoption,
key manufacturers, deployment metrics, and market forecasts using public data.
Roadmap #395.
"""

import datetime
from typing import Dict, List, Optional

ROBOTICS_COMPANIES = [
    {"name": "Fanuc", "ticker": "6954.T", "hq": "Japan", "segment": "industrial", "est_installed_base": 900000, "revenue_bn": 5.5},
    {"name": "ABB Robotics", "ticker": "ABB", "hq": "Switzerland", "segment": "industrial", "est_installed_base": 500000, "revenue_bn": 3.2},
    {"name": "KUKA", "ticker": None, "hq": "Germany", "segment": "industrial", "est_installed_base": 400000, "revenue_bn": 2.8},
    {"name": "Yaskawa", "ticker": "6506.T", "hq": "Japan", "segment": "industrial", "est_installed_base": 500000, "revenue_bn": 3.0},
    {"name": "Universal Robots", "ticker": None, "hq": "Denmark", "segment": "cobots", "est_installed_base": 75000, "revenue_bn": 0.4},
    {"name": "Boston Dynamics", "ticker": None, "hq": "USA", "segment": "humanoid_quadruped", "est_installed_base": 2000, "revenue_bn": 0.15},
    {"name": "Tesla Optimus", "ticker": "TSLA", "hq": "USA", "segment": "humanoid", "est_installed_base": 1000, "revenue_bn": 0.0},
    {"name": "Figure AI", "ticker": None, "hq": "USA", "segment": "humanoid", "est_installed_base": 100, "revenue_bn": 0.0},
    {"name": "Agility Robotics", "ticker": None, "hq": "USA", "segment": "humanoid", "est_installed_base": 50, "revenue_bn": 0.0},
    {"name": "1X Technologies", "ticker": None, "hq": "Norway", "segment": "humanoid", "est_installed_base": 20, "revenue_bn": 0.0},
]

IFR_STATS = {
    "year": 2025,
    "global_industrial_robots_installed": 4000000,
    "new_installations_annual": 590000,
    "top_markets": ["China", "Japan", "USA", "South Korea", "Germany"],
    "china_share_pct": 52,
    "robot_density_top5": [
        {"country": "South Korea", "robots_per_10k_workers": 1012},
        {"country": "Singapore", "robots_per_10k_workers": 730},
        {"country": "Germany", "robots_per_10k_workers": 415},
        {"country": "Japan", "robots_per_10k_workers": 399},
        {"country": "China", "robots_per_10k_workers": 392},
    ],
}


def get_robotics_landscape() -> Dict:
    """Get overview of global robotics industry — companies, installations, density."""
    by_segment = {}
    for c in ROBOTICS_COMPANIES:
        by_segment.setdefault(c["segment"], []).append(c["name"])

    public = [{"name": c["name"], "ticker": c["ticker"]} for c in ROBOTICS_COMPANIES if c.get("ticker")]
    total_installed = sum(c["est_installed_base"] for c in ROBOTICS_COMPANIES)

    return {
        "total_companies_tracked": len(ROBOTICS_COMPANIES),
        "by_segment": by_segment,
        "public_tickers": public,
        "tracked_installed_base": total_installed,
        "ifr_global_stats": IFR_STATS,
    }


def get_company_detail(name: str) -> Optional[Dict]:
    """Get detail on a specific robotics company."""
    for c in ROBOTICS_COMPANIES:
        if c["name"].lower() == name.lower():
            return c
    return None


def get_humanoid_progress() -> Dict:
    """Track the humanoid robotics race — units deployed, companies, timelines."""
    humanoids = [c for c in ROBOTICS_COMPANIES if "humanoid" in c["segment"]]
    total_units = sum(c["est_installed_base"] for c in humanoids)
    return {
        "humanoid_companies": len(humanoids),
        "total_units_deployed_est": total_units,
        "companies": [{"name": c["name"], "units": c["est_installed_base"], "hq": c["hq"]} for c in humanoids],
        "market_stage": "pre_commercial" if total_units < 10000 else "early_commercial",
    }
