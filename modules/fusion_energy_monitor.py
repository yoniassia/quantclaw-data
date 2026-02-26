"""
Fusion Energy Progress Monitor — Track fusion energy research milestones,
funding, key companies/projects, and timeline estimates using public data.
Roadmap #392.
"""

import json
import datetime
from typing import Dict, List, Optional

FUSION_PROJECTS = [
    {"name": "ITER", "type": "tokamak", "location": "France", "status": "under_construction", "target_year": 2035, "budget_bn": 22.0, "org": "International"},
    {"name": "SPARC", "type": "tokamak", "location": "USA", "status": "under_construction", "target_year": 2027, "budget_bn": 2.0, "org": "Commonwealth Fusion Systems"},
    {"name": "NIF", "type": "inertial_confinement", "location": "USA", "status": "operational", "target_year": None, "budget_bn": 3.5, "org": "Lawrence Livermore"},
    {"name": "JET", "type": "tokamak", "location": "UK", "status": "decommissioned", "target_year": None, "budget_bn": 1.0, "org": "UKAEA"},
    {"name": "STEP", "type": "spherical_tokamak", "location": "UK", "status": "design", "target_year": 2040, "budget_bn": 2.5, "org": "UKAEA"},
    {"name": "TAE Technologies", "type": "field_reversed", "location": "USA", "status": "r_and_d", "target_year": 2030, "budget_bn": 1.2, "org": "TAE Technologies"},
    {"name": "Helion Energy", "type": "field_reversed", "location": "USA", "status": "r_and_d", "target_year": 2028, "budget_bn": 0.6, "org": "Helion Energy"},
    {"name": "General Fusion", "type": "magnetized_target", "location": "Canada", "status": "r_and_d", "target_year": 2030, "budget_bn": 0.3, "org": "General Fusion"},
    {"name": "Zap Energy", "type": "z_pinch", "location": "USA", "status": "r_and_d", "target_year": 2030, "budget_bn": 0.2, "org": "Zap Energy"},
    {"name": "First Light Fusion", "type": "inertial_confinement", "location": "UK", "status": "r_and_d", "target_year": 2032, "budget_bn": 0.1, "org": "First Light Fusion"},
]

MILESTONES = [
    {"date": "2022-12-05", "project": "NIF", "event": "First net energy gain from fusion (Q>1)", "significance": "high"},
    {"date": "2023-10-01", "project": "SPARC", "event": "HTS magnet achieves 20T field", "significance": "high"},
    {"date": "2024-06-15", "project": "ITER", "event": "First plasma delayed to 2035", "significance": "medium"},
    {"date": "2023-05-10", "project": "Helion Energy", "event": "Microsoft PPA signed for fusion power", "significance": "high"},
    {"date": "2024-03-01", "project": "TAE Technologies", "event": "Copernicus machine operational", "significance": "medium"},
]


def get_fusion_landscape() -> Dict:
    """Get overview of all tracked fusion energy projects with status and timelines."""
    now = datetime.datetime.now().year
    projects = []
    for p in FUSION_PROJECTS:
        entry = {**p}
        if p["target_year"]:
            entry["years_to_target"] = p["target_year"] - now
        projects.append(entry)

    total_funding = sum(p["budget_bn"] for p in FUSION_PROJECTS)
    by_status = {}
    for p in FUSION_PROJECTS:
        by_status.setdefault(p["status"], []).append(p["name"])

    return {
        "total_projects": len(FUSION_PROJECTS),
        "total_funding_bn_usd": round(total_funding, 1),
        "by_status": by_status,
        "projects": projects,
        "milestones_recent": sorted(MILESTONES, key=lambda m: m["date"], reverse=True)[:5],
    }


def get_project_detail(project_name: str) -> Optional[Dict]:
    """Get detailed info for a specific fusion project."""
    for p in FUSION_PROJECTS:
        if p["name"].lower() == project_name.lower():
            milestones = [m for m in MILESTONES if m["project"].lower() == project_name.lower()]
            return {**p, "milestones": milestones}
    return None


def fusion_timeline_summary() -> List[Dict]:
    """Return projected commercialization timeline for all projects with target years."""
    now = datetime.datetime.now().year
    timeline = []
    for p in sorted(FUSION_PROJECTS, key=lambda x: x.get("target_year") or 9999):
        if p["target_year"]:
            timeline.append({
                "project": p["name"],
                "target_year": p["target_year"],
                "years_away": p["target_year"] - now,
                "type": p["type"],
                "status": p["status"],
            })
    return timeline
