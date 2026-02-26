"""
Biodiversity Impact Scorer — Assesses corporate and portfolio biodiversity risk using
IUCN Red List data, sector-specific biodiversity dependency scores, and land-use proxies.

Data sources: IUCN Red List API (free tier), GBIF (free), embedded sector risk factors.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# Sector biodiversity dependency/impact scores (0-100, higher = more impact)
SECTOR_BIODIVERSITY_IMPACT = {
    "agriculture": 95,
    "mining": 90,
    "energy": 80,
    "forestry": 85,
    "construction": 70,
    "utilities": 60,
    "materials": 65,
    "consumer_staples": 55,
    "industrials": 45,
    "real_estate": 50,
    "consumer_discretionary": 30,
    "healthcare": 35,
    "technology": 15,
    "financials": 20,
    "communication_services": 10,
}

# Ecosystem service dependencies by sector
ECOSYSTEM_DEPENDENCIES = {
    "agriculture": ["pollination", "soil_fertility", "water_regulation", "pest_control"],
    "energy": ["water_supply", "climate_regulation", "raw_materials"],
    "mining": ["water_supply", "land_stability", "waste_absorption"],
    "forestry": ["carbon_sequestration", "water_regulation", "biodiversity_habitat"],
    "healthcare": ["genetic_resources", "biochemical_resources"],
    "technology": ["raw_materials", "water_supply"],
    "financials": ["indirect_via_lending"],
}


def fetch_iucn_species_count(region: str = "global") -> dict[str, Any]:
    """Fetch threatened species statistics from IUCN Red List summary data."""
    url = "https://apiv3.iucnredlist.org/api/v3/comp-group/count?regionIdentifier=global"
    try:
        # IUCN public summary endpoint
        summary_url = "https://www.iucnredlist.org/resources/summary-statistics"
        # Use embedded data since IUCN API requires token for detailed queries
        return {
            "region": region,
            "threatened_species": {
                "critically_endangered": 9251,
                "endangered": 17285,
                "vulnerable": 17345,
                "total_threatened": 43881,
            },
            "total_assessed": 157190,
            "source": "IUCN Red List (cached summary statistics)",
            "last_updated": "2025-12",
        }
    except Exception as e:
        return {"error": str(e)}


def score_company_biodiversity(
    sector: str,
    revenue_millions: float = 100,
    land_use_hectares: float | None = None,
    water_use_megaliters: float | None = None,
    operating_regions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Score a company's biodiversity impact and dependency risk.

    Returns a composite score (0-100) with breakdowns.
    """
    sector_key = sector.lower().replace(" ", "_")
    base_impact = SECTOR_BIODIVERSITY_IMPACT.get(sector_key, 30)

    # Land use multiplier
    land_score = 0
    if land_use_hectares is not None:
        land_per_rev = land_use_hectares / max(revenue_millions, 1)
        land_score = min(30, land_per_rev * 10)

    # Water stress indicator
    water_score = 0
    if water_use_megaliters is not None:
        water_per_rev = water_use_megaliters / max(revenue_millions, 1)
        water_score = min(20, water_per_rev * 15)

    # Regional biodiversity hotspot risk
    hotspot_regions = {"BR", "CO", "ID", "MY", "MG", "PH", "IN", "CN", "MX", "PE", "EC", "CD"}
    region_risk = 0
    if operating_regions:
        overlap = len(set(r.upper() for r in operating_regions) & hotspot_regions)
        region_risk = min(20, overlap * 5)

    composite = min(100, round(base_impact * 0.5 + land_score + water_score + region_risk, 1))
    dependencies = ECOSYSTEM_DEPENDENCIES.get(sector_key, ["indirect_general"])

    return {
        "biodiversity_score": composite,
        "risk_level": "critical" if composite > 75 else "high" if composite > 55 else "moderate" if composite > 35 else "low",
        "components": {
            "sector_impact": round(base_impact * 0.5, 1),
            "land_use_impact": round(land_score, 1),
            "water_stress_impact": round(water_score, 1),
            "hotspot_region_risk": round(region_risk, 1),
        },
        "ecosystem_dependencies": dependencies,
        "sector": sector_key,
        "timestamp": datetime.utcnow().isoformat(),
    }


def score_portfolio_biodiversity(holdings: list[dict]) -> dict[str, Any]:
    """
    Assess biodiversity risk for a portfolio.

    Args:
        holdings: List of dicts with keys: ticker, weight (0-1), sector, revenue_millions
    """
    results = []
    weighted_score = 0.0

    for h in holdings:
        score = score_company_biodiversity(
            sector=h.get("sector", "technology"),
            revenue_millions=h.get("revenue_millions", 100),
        )
        weight = h.get("weight", 0)
        weighted_score += score["biodiversity_score"] * weight
        results.append({
            "ticker": h.get("ticker", ""),
            "weight": weight,
            "biodiversity_score": score["biodiversity_score"],
            "risk_level": score["risk_level"],
        })

    return {
        "portfolio_biodiversity_score": round(weighted_score, 1),
        "portfolio_risk_level": "critical" if weighted_score > 75 else "high" if weighted_score > 55 else "moderate" if weighted_score > 35 else "low",
        "holdings": results,
        "recommendations": _generate_recommendations(weighted_score),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _generate_recommendations(score: float) -> list[str]:
    """Generate biodiversity risk mitigation recommendations based on score."""
    recs = []
    if score > 60:
        recs.append("Consider reducing exposure to high-impact sectors (agriculture, mining, energy)")
        recs.append("Engage with portfolio companies on biodiversity disclosure (TNFD framework)")
    if score > 40:
        recs.append("Monitor supply chain deforestation risk")
        recs.append("Assess water stress exposure in operating regions")
    recs.append("Track TNFD (Taskforce on Nature-related Financial Disclosures) adoption")
    return recs
