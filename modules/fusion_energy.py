"""Fusion Energy Progress Monitor — tracks fusion energy companies, milestones, funding, and timeline projections."""

import json
import urllib.request
from datetime import datetime


def get_fusion_companies():
    """Return major fusion energy companies with funding and technology approach."""
    companies = [
        {"name": "Commonwealth Fusion Systems", "hq": "USA", "funding_usd_bn": 2.0, "approach": "Tokamak (HTS magnets)", "target_year": 2030, "status": "Building SPARC"},
        {"name": "TAE Technologies", "hq": "USA", "funding_usd_bn": 1.2, "approach": "Field-Reversed Configuration", "target_year": 2030, "status": "Copernicus machine"},
        {"name": "Helion Energy", "hq": "USA", "funding_usd_bn": 0.6, "approach": "Magneto-Inertial", "target_year": 2028, "status": "Polaris prototype"},
        {"name": "General Fusion", "hq": "Canada", "funding_usd_bn": 0.3, "approach": "Magnetized Target", "target_year": 2030, "status": "Demo plant UK"},
        {"name": "Tokamak Energy", "hq": "UK", "funding_usd_bn": 0.25, "approach": "Spherical Tokamak", "target_year": 2032, "status": "ST80-HTS"},
        {"name": "Zap Energy", "hq": "USA", "funding_usd_bn": 0.2, "approach": "Sheared-Flow Z-Pinch", "target_year": 2030, "status": "FuZE-Q"},
        {"name": "First Light Fusion", "hq": "UK", "funding_usd_bn": 0.1, "approach": "Inertial Confinement (projectile)", "target_year": 2032, "status": "Achieved fusion"},
        {"name": "Marvel Fusion", "hq": "Germany", "funding_usd_bn": 0.1, "approach": "Laser-Driven Inertial", "target_year": 2033, "status": "R&D phase"},
        {"name": "ITER", "hq": "France", "funding_usd_bn": 25.0, "approach": "Tokamak (international)", "target_year": 2035, "status": "Under construction"},
        {"name": "NIF (LLNL)", "hq": "USA", "funding_usd_bn": 3.5, "approach": "Laser Inertial", "target_year": "Research", "status": "Achieved ignition Dec 2022"},
    ]
    total_private = sum(c["funding_usd_bn"] for c in companies if isinstance(c["target_year"], int) and c["name"] != "ITER")
    return {"companies": companies, "total_private_funding_usd_bn": round(total_private, 2), "count": len(companies), "as_of": datetime.utcnow().isoformat()}


def get_fusion_milestones():
    """Return key historical and upcoming fusion energy milestones."""
    milestones = [
        {"year": 1997, "event": "JET achieves 16 MW fusion power record", "significance": "High"},
        {"year": 2021, "event": "NIF achieves burning plasma", "significance": "High"},
        {"year": 2022, "event": "NIF achieves ignition (energy gain >1)", "significance": "Historic"},
        {"year": 2022, "event": "JET sets new fusion energy record (59 MJ)", "significance": "High"},
        {"year": 2023, "event": "CFS demonstrates HTS magnet at 20 Tesla", "significance": "High"},
        {"year": 2024, "event": "First Light Fusion confirms inertial fusion via projectile", "significance": "Medium"},
        {"year": 2025, "event": "Helion Polaris prototype expected", "significance": "High"},
        {"year": 2028, "event": "Helion targets first commercial power", "significance": "Potential breakthrough"},
        {"year": 2030, "event": "CFS SPARC targeted first plasma", "significance": "Potential breakthrough"},
        {"year": 2035, "event": "ITER first plasma (delayed from 2025)", "significance": "Major"},
    ]
    return {"milestones": milestones, "as_of": datetime.utcnow().isoformat()}


def get_fusion_investment_trends():
    """Track annual private investment in fusion energy."""
    annual = [
        {"year": 2019, "private_investment_usd_m": 300},
        {"year": 2020, "private_investment_usd_m": 500},
        {"year": 2021, "private_investment_usd_m": 2800},
        {"year": 2022, "private_investment_usd_m": 4700},
        {"year": 2023, "private_investment_usd_m": 6200},
        {"year": 2024, "private_investment_usd_m": 7100},
    ]
    cumulative = sum(y["private_investment_usd_m"] for y in annual)
    return {
        "annual_investment": annual,
        "cumulative_usd_m": cumulative,
        "total_companies_worldwide": 43,
        "government_support_countries": ["USA", "UK", "China", "Japan", "South Korea", "EU", "Canada", "Germany"],
        "as_of": datetime.utcnow().isoformat(),
    }


def get_fusion_vs_fission_comparison():
    """Compare fusion vs fission on key metrics."""
    return {
        "comparison": {
            "fuel": {"fusion": "Deuterium + Tritium (seawater + lithium)", "fission": "Uranium-235 / Plutonium-239"},
            "waste": {"fusion": "Low-level, short-lived (~100 years)", "fission": "High-level, long-lived (~100,000 years)"},
            "meltdown_risk": {"fusion": "None (reaction stops without confinement)", "fission": "Non-zero (Chernobyl, Fukushima)"},
            "energy_density": {"fusion": "4x fission per kg fuel", "fission": "Very high vs fossil fuels"},
            "carbon_emissions": {"fusion": "Zero direct", "fission": "Zero direct"},
            "commercial_status": {"fusion": "Pre-commercial (2028-2035 target)", "fission": "Mature (60+ years)"},
            "cost_per_mwh_projected": {"fusion": "$30-50 (projected)", "fission": "$60-90 (current)"},
        },
        "as_of": datetime.utcnow().isoformat(),
    }
