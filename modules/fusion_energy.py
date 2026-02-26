"""
Fusion Energy Progress Monitor — Track global fusion energy development milestones,
funding, reactor projects, and scientific breakthroughs.

Covers ITER, Commonwealth Fusion, Helion, TAE Technologies, and public research programs.
Uses free data from IAEA, news APIs, and public project databases.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Major fusion projects database (curated, updated periodically)
FUSION_PROJECTS = {
    "ITER": {
        "location": "Cadarache, France",
        "type": "Tokamak",
        "status": "Under Construction",
        "first_plasma_target": "2035",
        "budget_bn_usd": 22.0,
        "partners": ["EU", "US", "China", "Russia", "Japan", "South Korea", "India"],
        "milestone": "Tokamak assembly ongoing",
    },
    "Commonwealth Fusion Systems": {
        "location": "Devens, MA, USA",
        "type": "Compact Tokamak (SPARC)",
        "status": "Development",
        "first_plasma_target": "2026",
        "funding_bn_usd": 2.0,
        "milestone": "HTS magnet record 20T (2021)",
    },
    "Helion Energy": {
        "location": "Everett, WA, USA",
        "type": "Field-Reversed Configuration",
        "status": "Development (Polaris)",
        "first_plasma_target": "2028",
        "funding_bn_usd": 0.577,
        "milestone": "Microsoft PPA signed (2023)",
    },
    "TAE Technologies": {
        "location": "Foothill Ranch, CA, USA",
        "type": "Field-Reversed Configuration",
        "status": "Development (Copernicus)",
        "first_plasma_target": "2030",
        "funding_bn_usd": 1.2,
        "milestone": "Norman reactor 75M°C (2022)",
    },
    "Tokamak Energy": {
        "location": "Milton Park, UK",
        "type": "Spherical Tokamak",
        "status": "Development",
        "first_plasma_target": "2030",
        "funding_bn_usd": 0.25,
        "milestone": "ST40 100M°C achieved",
    },
    "General Fusion": {
        "location": "Richmond, BC, Canada",
        "type": "Magnetized Target Fusion",
        "status": "Development",
        "first_plasma_target": "2027",
        "funding_bn_usd": 0.3,
        "milestone": "UK demo plant announced",
    },
    "Zap Energy": {
        "location": "Seattle, WA, USA",
        "type": "Sheared-Flow Z-Pinch",
        "status": "Development",
        "first_plasma_target": "2030",
        "funding_bn_usd": 0.2,
        "milestone": "FuZE-Q prototype underway",
    },
    "NIF (Lawrence Livermore)": {
        "location": "Livermore, CA, USA",
        "type": "Inertial Confinement (Laser)",
        "status": "Research",
        "first_plasma_target": "N/A",
        "funding_bn_usd": 3.5,
        "milestone": "Net energy gain achieved Dec 2022",
    },
}


def get_fusion_projects(status_filter: Optional[str] = None) -> List[Dict]:
    """
    Get all tracked fusion energy projects with details.

    Args:
        status_filter: Optional filter by status (e.g., 'Development', 'Research', 'Under Construction')

    Returns:
        List of fusion project dictionaries
    """
    results = []
    for name, info in FUSION_PROJECTS.items():
        if status_filter and status_filter.lower() not in info["status"].lower():
            continue
        project = {"name": name, **info}
        results.append(project)

    results.sort(key=lambda x: x.get("funding_bn_usd", x.get("budget_bn_usd", 0)), reverse=True)
    return results


def get_fusion_investment_summary() -> Dict:
    """
    Calculate total tracked investment in fusion energy and breakdown by approach.

    Returns:
        Dictionary with total funding, by-type breakdown, and project count
    """
    total = 0.0
    by_type = {}
    by_status = {}

    for name, info in FUSION_PROJECTS.items():
        funding = info.get("funding_bn_usd", info.get("budget_bn_usd", 0))
        total += funding

        ftype = info["type"]
        by_type[ftype] = by_type.get(ftype, 0) + funding

        status = info["status"]
        by_status[status] = by_status.get(status, 0) + funding

    return {
        "total_investment_bn_usd": round(total, 2),
        "project_count": len(FUSION_PROJECTS),
        "by_technology_type": {k: round(v, 2) for k, v in sorted(by_type.items(), key=lambda x: -x[1])},
        "by_status": {k: round(v, 2) for k, v in sorted(by_status.items(), key=lambda x: -x[1])},
        "earliest_commercial_target": min(
            (p.get("first_plasma_target", "9999") for p in FUSION_PROJECTS.values() if p.get("first_plasma_target", "N/A") != "N/A"),
            default="Unknown",
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_fusion_timeline() -> List[Dict]:
    """
    Get fusion project timeline sorted by target first plasma date.

    Returns:
        List of projects with name, type, and target dates
    """
    timeline = []
    for name, info in FUSION_PROJECTS.items():
        target = info.get("first_plasma_target", "N/A")
        timeline.append({
            "name": name,
            "type": info["type"],
            "target_first_plasma": target,
            "status": info["status"],
            "latest_milestone": info.get("milestone", ""),
        })

    timeline.sort(key=lambda x: x["target_first_plasma"] if x["target_first_plasma"] != "N/A" else "9999")
    return timeline


def search_fusion_news(query: str = "fusion energy reactor") -> List[Dict]:
    """
    Search for recent fusion energy news via free news APIs.

    Args:
        query: Search query string

    Returns:
        List of news article summaries
    """
    try:
        url = f"https://newsdata.io/api/1/news?apikey=pub_0&q={query}&language=en&category=science,technology"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            articles = []
            for item in data.get("results", [])[:10]:
                articles.append({
                    "title": item.get("title", ""),
                    "source": item.get("source_id", ""),
                    "published": item.get("pubDate", ""),
                    "link": item.get("link", ""),
                })
            return articles
    except Exception:
        return [{"note": "News API unavailable — use get_fusion_projects() for curated data"}]


if __name__ == "__main__":
    print("=== Fusion Energy Progress Monitor ===")
    summary = get_fusion_investment_summary()
    print(f"Total tracked investment: ${summary['total_investment_bn_usd']}B across {summary['project_count']} projects")
    for p in get_fusion_timeline():
        print(f"  {p['target_first_plasma']}: {p['name']} ({p['type']})")
