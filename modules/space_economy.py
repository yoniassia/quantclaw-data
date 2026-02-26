"""
Space Economy Index (Roadmap #390)

Tracks the space economy including launch activity, satellite deployments,
space tourism, in-space manufacturing, and investment flows.
Uses free data from launch databases, NASA APIs, and space industry trackers.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Public space companies
SPACE_COMPANIES = {
    "pure_play": {
        "RKLB": {"name": "Rocket Lab", "focus": "Small launch + spacecraft"},
        "SPCE": {"name": "Virgin Galactic", "focus": "Suborbital tourism"},
        "ASTS": {"name": "AST SpaceMobile", "focus": "Space-based cellular broadband"},
        "LUNR": {"name": "Intuitive Machines", "focus": "Lunar landers/services"},
        "RDW": {"name": "Redwire", "focus": "Space infrastructure/manufacturing"},
        "MNTS": {"name": "Momentus", "focus": "In-space transportation"},
        "BKSY": {"name": "BlackSky", "focus": "Geospatial intelligence satellites"},
        "PL": {"name": "Planet Labs", "focus": "Earth observation satellites"},
    },
    "diversified": {
        "BA": {"name": "Boeing", "focus": "SLS, Starliner, satellites"},
        "LMT": {"name": "Lockheed Martin", "focus": "Orion, GPS, military space"},
        "NOC": {"name": "Northrop Grumman", "focus": "Cygnus, solid rockets, satellites"},
        "RTX": {"name": "RTX (Raytheon)", "focus": "Space sensors, missile warning"},
    },
    "private": {
        "SpaceX": {"name": "SpaceX", "focus": "Falcon 9, Starship, Starlink", "valuation_B": 200},
        "BlueOrigin": {"name": "Blue Origin", "focus": "New Glenn, New Shepard"},
        "Relativity": {"name": "Relativity Space", "focus": "3D-printed rockets"},
    },
}

# Space economy segments
SEGMENTS = {
    "launch_services": {"size_B": 10, "growth_pct": 15, "key_players": ["SpaceX", "RKLB", "BlueOrigin"]},
    "satellite_manufacturing": {"size_B": 15, "growth_pct": 8, "key_players": ["LMT", "NOC", "BA"]},
    "satellite_services": {"size_B": 130, "growth_pct": 5, "key_players": ["SpaceX (Starlink)", "ASTS", "PL"]},
    "ground_equipment": {"size_B": 70, "growth_pct": 6, "key_players": ["RTX", "L3Harris"]},
    "space_tourism": {"size_B": 1, "growth_pct": 40, "key_players": ["SpaceX", "SPCE", "BlueOrigin"]},
    "in_space_economy": {"size_B": 2, "growth_pct": 25, "key_players": ["RDW", "LUNR"]},
}


def get_recent_launches(days: int = 30) -> Dict:
    """
    Fetch recent orbital launches from the Launch Library 2 API (free tier).

    Args:
        days: Number of days to look back

    Returns:
        Dict with launch count, success rate, and details
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    url = (
        f"https://ll.thespacedevs.com/2.2.0/launch/"
        f"?net__gte={start_str}&net__lte={end_str}"
        f"&limit=50&ordering=-net"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        launches = []
        success_count = 0
        for launch in data.get("results", []):
            status_name = launch.get("status", {}).get("name", "Unknown")
            is_success = status_name in ["Launch Successful", "Success"]
            if is_success:
                success_count += 1
            launches.append({
                "name": launch.get("name", "Unknown"),
                "date": launch.get("net", ""),
                "provider": launch.get("launch_service_provider", {}).get("name", "Unknown"),
                "status": status_name,
                "pad": launch.get("pad", {}).get("location", {}).get("name", "Unknown"),
            })

        total = len(launches)
        return {
            "period_days": days,
            "total_launches": total,
            "successful": success_count,
            "success_rate_pct": round((success_count / total) * 100, 1) if total > 0 else 0,
            "launches": launches[:10],  # Top 10 most recent
            "source": "Launch Library 2",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "total_launches": 0}


def get_space_economy_overview() -> Dict:
    """
    Provide a comprehensive overview of the space economy including
    market size, growth rates, and investment themes.

    Returns:
        Dict with segment breakdown, total market size, and trends
    """
    total_market = sum(seg["size_B"] for seg in SEGMENTS.values())
    weighted_growth = sum(
        seg["size_B"] * seg["growth_pct"] for seg in SEGMENTS.values()
    ) / total_market

    return {
        "total_market_size_B": total_market,
        "weighted_avg_growth_pct": round(weighted_growth, 1),
        "segments": SEGMENTS,
        "investment_themes": [
            "Starlink/satellite broadband → ASTS, SpaceX",
            "Launch cost reduction → RKLB, SpaceX reusability",
            "Earth observation data → PL, BKSY",
            "Lunar economy → LUNR, NASA Artemis contractors",
            "Space-based solar/manufacturing → RDW, emerging",
            "National security space → LMT, NOC, RTX",
        ],
        "public_tickers": list(SPACE_COMPANIES["pure_play"].keys()),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_upcoming_launches(limit: int = 10) -> Dict:
    """
    Fetch upcoming scheduled launches.

    Args:
        limit: Max number of upcoming launches to return

    Returns:
        Dict with scheduled launches and providers
    """
    url = f"https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit={limit}&ordering=net"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        upcoming = []
        for launch in data.get("results", []):
            upcoming.append({
                "name": launch.get("name", "Unknown"),
                "date": launch.get("net", ""),
                "provider": launch.get("launch_service_provider", {}).get("name", "Unknown"),
                "mission_type": launch.get("mission", {}).get("type", "Unknown") if launch.get("mission") else "Unknown",
                "orbit": launch.get("mission", {}).get("orbit", {}).get("name", "Unknown") if launch.get("mission") and launch.get("mission", {}).get("orbit") else "Unknown",
            })

        return {
            "upcoming_launches": upcoming,
            "count": len(upcoming),
            "source": "Launch Library 2",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "upcoming_launches": []}


def calculate_space_index() -> Dict:
    """
    Calculate a composite Space Economy Index based on launch cadence,
    market valuations, and sector momentum.

    Returns:
        Dict with index value and component scores
    """
    launch_data = get_recent_launches(days=30)
    launch_cadence = launch_data.get("total_launches", 0)

    # Normalize launch cadence (historical avg ~10-15/month)
    launch_score = min(100, (launch_cadence / 15) * 100)

    # Market growth score from segment data
    growth_scores = [seg["growth_pct"] for seg in SEGMENTS.values()]
    avg_growth = sum(growth_scores) / len(growth_scores)
    growth_score = min(100, avg_growth * 5)  # 20% growth = 100

    # Composite
    composite = round(0.4 * launch_score + 0.6 * growth_score, 1)

    return {
        "space_economy_index": composite,
        "components": {
            "launch_cadence_score": round(launch_score, 1),
            "market_growth_score": round(growth_score, 1),
        },
        "monthly_launches": launch_cadence,
        "avg_sector_growth_pct": round(avg_growth, 1),
        "trend": "EXPANDING" if composite >= 60 else "STABLE" if composite >= 40 else "CONTRACTING",
        "timestamp": datetime.utcnow().isoformat(),
    }
