"""
Fusion Energy Progress Monitor (Roadmap #392)

Tracks fusion energy R&D milestones, funding, and company progress
toward commercial fusion power generation using public data sources.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Major fusion projects and their public milestones
FUSION_PROJECTS = {
    "ITER": {
        "type": "tokamak",
        "location": "Cadarache, France",
        "status": "under_construction",
        "target_first_plasma": "2035",
        "budget_bn_usd": 22.0,
        "members": ["EU", "US", "China", "India", "Japan", "Korea", "Russia"],
        "url": "https://www.iter.org"
    },
    "Commonwealth Fusion Systems": {
        "type": "compact_tokamak",
        "location": "Devens, MA, USA",
        "status": "development",
        "funding_raised_bn": 2.0,
        "reactor": "SPARC",
        "target_demo": "2028",
    },
    "TAE Technologies": {
        "type": "field_reversed_config",
        "location": "Foothill Ranch, CA, USA",
        "status": "development",
        "funding_raised_bn": 1.2,
    },
    "Helion Energy": {
        "type": "field_reversed_config",
        "location": "Everett, WA, USA",
        "status": "development",
        "funding_raised_bn": 0.6,
        "target_demo": "2028",
    },
    "General Fusion": {
        "type": "magnetized_target",
        "location": "Richmond, BC, Canada",
        "status": "development",
        "funding_raised_bn": 0.3,
    },
    "Tokamak Energy": {
        "type": "spherical_tokamak",
        "location": "Oxfordshire, UK",
        "status": "development",
        "funding_raised_bn": 0.25,
    },
    "Zap Energy": {
        "type": "z_pinch",
        "location": "Everett, WA, USA",
        "status": "development",
        "funding_raised_bn": 0.2,
    },
    "NIF (National Ignition Facility)": {
        "type": "inertial_confinement",
        "location": "Livermore, CA, USA",
        "status": "research",
        "milestone": "Net energy gain achieved Dec 2022",
    },
}

FUSION_APPROACHES = {
    "tokamak": {"description": "Magnetic confinement using toroidal chamber", "maturity": "highest"},
    "stellarator": {"description": "Twisted magnetic confinement", "maturity": "high"},
    "inertial_confinement": {"description": "Laser-driven implosion", "maturity": "high"},
    "compact_tokamak": {"description": "High-field compact magnetic confinement", "maturity": "medium"},
    "field_reversed_config": {"description": "Self-organized plasma confinement", "maturity": "medium"},
    "magnetized_target": {"description": "Hybrid magnetic-inertial", "maturity": "medium"},
    "spherical_tokamak": {"description": "Compact spherical geometry", "maturity": "medium"},
    "z_pinch": {"description": "Axial current pinch confinement", "maturity": "low"},
}


def get_fusion_landscape() -> Dict:
    """
    Get overview of the global fusion energy landscape including
    all tracked projects, approaches, and aggregate funding.
    """
    total_private_funding = sum(
        p.get("funding_raised_bn", 0) for p in FUSION_PROJECTS.values()
    )
    approaches_count = {}
    for proj in FUSION_PROJECTS.values():
        t = proj.get("type", "unknown")
        approaches_count[t] = approaches_count.get(t, 0) + 1

    return {
        "total_projects_tracked": len(FUSION_PROJECTS),
        "total_private_funding_bn_usd": round(total_private_funding, 2),
        "approaches_distribution": approaches_count,
        "approach_details": FUSION_APPROACHES,
        "projects": {k: v for k, v in FUSION_PROJECTS.items()},
        "as_of": datetime.utcnow().isoformat(),
    }


def get_project_detail(project_name: str) -> Optional[Dict]:
    """
    Get detailed info on a specific fusion project by name (case-insensitive partial match).
    """
    for name, data in FUSION_PROJECTS.items():
        if project_name.lower() in name.lower():
            return {"name": name, **data}
    return None


def estimate_fusion_timeline() -> Dict:
    """
    Estimate commercial fusion timeline based on current project targets
    and historical milestone pace.
    """
    milestones = [
        {"year": 1958, "event": "First tokamak concept (Sakharov/Tamm)"},
        {"year": 1968, "event": "T-3 tokamak plasma temperature record"},
        {"year": 1997, "event": "JET 16MW fusion power record"},
        {"year": 2022, "event": "NIF achieves net energy gain (ignition)"},
        {"year": 2025, "event": "Multiple private companies targeting demo reactors"},
    ]

    targets = []
    for name, proj in FUSION_PROJECTS.items():
        if "target_demo" in proj:
            targets.append({"project": name, "demo_target": proj["target_demo"]})
        if "target_first_plasma" in proj:
            targets.append({"project": name, "first_plasma_target": proj["target_first_plasma"]})

    return {
        "historical_milestones": milestones,
        "upcoming_targets": targets,
        "estimated_first_commercial": "2035-2045",
        "key_challenges": [
            "Plasma containment stability at scale",
            "Tritium breeding and supply chain",
            "Material science (neutron-resistant first wall)",
            "Regulatory framework for fusion power plants",
            "Cost competitiveness with renewables + storage",
        ],
    }


def fusion_investment_summary() -> Dict:
    """
    Summarize private and public fusion energy investment trends.
    """
    private = []
    for name, proj in FUSION_PROJECTS.items():
        if "funding_raised_bn" in proj:
            private.append({
                "company": name,
                "funding_bn_usd": proj["funding_raised_bn"],
                "approach": proj.get("type", "unknown"),
            })
    private.sort(key=lambda x: x["funding_bn_usd"], reverse=True)

    return {
        "private_sector": private,
        "total_private_bn": round(sum(p["funding_bn_usd"] for p in private), 2),
        "major_public_programs": [
            {"name": "ITER", "budget_bn_usd": 22.0, "members": 7},
            {"name": "NIF/LLNL", "budget_bn_usd": 3.5, "country": "US"},
            {"name": "Wendelstein 7-X", "budget_bn_usd": 1.1, "country": "Germany"},
            {"name": "JT-60SA", "budget_bn_usd": 0.6, "country": "Japan/EU"},
        ],
        "trend": "Private fusion investment accelerating since 2020, >$6B cumulative by 2025",
    }
