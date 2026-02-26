"""
Carbon Footprint Calculator — Estimates Scope 1/2/3 carbon emissions for companies
and portfolios using EPA emission factors, IEA data proxies, and sector benchmarks.

Data sources: EPA eGRID (free), FRED energy data (free), sector emission factors (embedded).
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# Sector average tCO2e per $1M revenue (approximate, based on CDP/EPA data)
SECTOR_EMISSION_FACTORS = {
    "energy": 850.0,
    "utilities": 720.0,
    "materials": 450.0,
    "industrials": 180.0,
    "consumer_discretionary": 55.0,
    "consumer_staples": 95.0,
    "healthcare": 40.0,
    "financials": 12.0,
    "technology": 18.0,
    "communication_services": 22.0,
    "real_estate": 65.0,
}

# Scope 2 electricity emission factors by region (tCO2e per MWh)
GRID_EMISSION_FACTORS = {
    "US_avg": 0.386,
    "EU_avg": 0.231,
    "CN": 0.555,
    "IN": 0.708,
    "JP": 0.457,
    "UK": 0.193,
    "DE": 0.311,
    "FR": 0.052,
    "BR": 0.074,
    "AU": 0.656,
}


def estimate_company_emissions(
    revenue_millions: float,
    sector: str,
    employees: int = 0,
    electricity_mwh: float | None = None,
    region: str = "US_avg",
) -> dict[str, Any]:
    """
    Estimate a company's carbon footprint across Scope 1, 2, and 3.

    Args:
        revenue_millions: Annual revenue in millions USD
        sector: Industry sector (see SECTOR_EMISSION_FACTORS keys)
        employees: Number of employees (for office emissions estimate)
        electricity_mwh: Known electricity consumption in MWh (optional)
        region: Grid region for Scope 2 calculation
    """
    sector_key = sector.lower().replace(" ", "_")
    factor = SECTOR_EMISSION_FACTORS.get(sector_key, 100.0)

    # Scope 1: Direct emissions (estimated as % of total based on sector)
    scope1_ratio = {"energy": 0.45, "utilities": 0.55, "materials": 0.35, "industrials": 0.25}.get(sector_key, 0.10)
    total_estimated = revenue_millions * factor
    scope1 = round(total_estimated * scope1_ratio, 2)

    # Scope 2: Electricity / purchased energy
    grid_factor = GRID_EMISSION_FACTORS.get(region, 0.386)
    if electricity_mwh is not None:
        scope2 = round(electricity_mwh * grid_factor, 2)
    elif employees > 0:
        # Average office: ~7 MWh per employee per year
        scope2 = round(employees * 7.0 * grid_factor, 2)
    else:
        scope2 = round(total_estimated * 0.15, 2)

    # Scope 3: Supply chain + product use (typically largest)
    scope3 = round(total_estimated - scope1 - scope2, 2)
    if scope3 < 0:
        scope3 = round(total_estimated * 0.5, 2)

    total = round(scope1 + scope2 + scope3, 2)
    intensity = round(total / revenue_millions, 2) if revenue_millions > 0 else 0

    return {
        "company_estimate": {
            "scope1_tco2e": scope1,
            "scope2_tco2e": scope2,
            "scope3_tco2e": scope3,
            "total_tco2e": total,
            "intensity_per_million_rev": intensity,
        },
        "sector": sector_key,
        "sector_avg_factor": factor,
        "region": region,
        "grid_emission_factor": grid_factor,
        "methodology": "Sector-average with EPA/IEA factors",
        "timestamp": datetime.utcnow().isoformat(),
    }


def estimate_portfolio_footprint(holdings: list[dict]) -> dict[str, Any]:
    """
    Estimate carbon footprint for a portfolio of holdings.

    Args:
        holdings: List of dicts with keys: ticker, weight (0-1), revenue_millions, sector
    """
    results = []
    total_weighted_emissions = 0.0
    total_weighted_intensity = 0.0

    for h in holdings:
        est = estimate_company_emissions(
            revenue_millions=h.get("revenue_millions", 100),
            sector=h.get("sector", "technology"),
        )
        weight = h.get("weight", 0)
        co2 = est["company_estimate"]["total_tco2e"]
        intensity = est["company_estimate"]["intensity_per_million_rev"]
        total_weighted_emissions += co2 * weight
        total_weighted_intensity += intensity * weight
        results.append({
            "ticker": h.get("ticker", ""),
            "weight": weight,
            "estimated_tco2e": co2,
            "intensity": intensity,
        })

    return {
        "portfolio_footprint": {
            "weighted_tco2e": round(total_weighted_emissions, 2),
            "weighted_intensity": round(total_weighted_intensity, 2),
            "holdings_analyzed": len(results),
        },
        "holdings": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_emission_factors() -> dict[str, Any]:
    """Return all available emission factors for sectors and grid regions."""
    return {
        "sector_factors_tco2e_per_million_usd": SECTOR_EMISSION_FACTORS,
        "grid_factors_tco2e_per_mwh": GRID_EMISSION_FACTORS,
        "source": "EPA eGRID + IEA + CDP sector averages",
    }
