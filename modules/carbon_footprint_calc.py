"""Carbon Footprint Calculator — estimates Scope 1/2/3 emissions for companies.

Uses EPA emission factors, IEA grid intensity data, and industry benchmarks
to estimate carbon footprints across all three GHG Protocol scopes.
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional

# EPA emission factors (kg CO2e per unit)
EMISSION_FACTORS = {
    "natural_gas_mmbtu": 53.06,
    "diesel_gallon": 10.21,
    "gasoline_gallon": 8.78,
    "propane_gallon": 5.72,
    "coal_short_ton": 2408.0,
    "electricity_kwh_us_avg": 0.386,  # US grid average
    "jet_fuel_gallon": 9.75,
    "marine_fuel_gallon": 11.24,
}

# Grid emission factors by region (kg CO2e / kWh) — IEA 2024 approx
GRID_FACTORS = {
    "us_avg": 0.386, "us_california": 0.210, "us_texas": 0.410,
    "us_northeast": 0.280, "us_midwest": 0.480, "us_southeast": 0.400,
    "eu_avg": 0.230, "uk": 0.207, "germany": 0.350, "france": 0.052,
    "china": 0.555, "india": 0.708, "japan": 0.457, "australia": 0.510,
    "canada": 0.120, "brazil": 0.074, "south_korea": 0.415,
}

# Industry avg Scope 1+2 intensity (tonnes CO2e per $M revenue)
INDUSTRY_INTENSITY = {
    "technology": 15, "financials": 8, "healthcare": 25,
    "consumer_discretionary": 35, "energy": 450, "utilities": 800,
    "industrials": 120, "materials": 280, "real_estate": 40,
    "consumer_staples": 55, "telecom": 20,
}


def calculate_scope1(
    natural_gas_mmbtu: float = 0,
    diesel_gallons: float = 0,
    gasoline_gallons: float = 0,
    propane_gallons: float = 0,
    coal_short_tons: float = 0,
    custom_sources: Optional[dict[str, tuple[float, float]]] = None,
) -> dict:
    """Calculate Scope 1 (direct) emissions from fuel combustion.

    Args:
        natural_gas_mmbtu: Natural gas consumed in MMBtu.
        diesel_gallons: Diesel fuel consumed.
        gasoline_gallons: Gasoline consumed.
        propane_gallons: Propane consumed.
        coal_short_tons: Coal consumed.
        custom_sources: Dict of {"name": (quantity, kg_co2e_per_unit)}.

    Returns:
        Dict with total Scope 1 in tonnes CO2e and per-source breakdown.
    """
    breakdown = {}
    if natural_gas_mmbtu:
        breakdown["natural_gas"] = round(natural_gas_mmbtu * EMISSION_FACTORS["natural_gas_mmbtu"] / 1000, 2)
    if diesel_gallons:
        breakdown["diesel"] = round(diesel_gallons * EMISSION_FACTORS["diesel_gallon"] / 1000, 2)
    if gasoline_gallons:
        breakdown["gasoline"] = round(gasoline_gallons * EMISSION_FACTORS["gasoline_gallon"] / 1000, 2)
    if propane_gallons:
        breakdown["propane"] = round(propane_gallons * EMISSION_FACTORS["propane_gallon"] / 1000, 2)
    if coal_short_tons:
        breakdown["coal"] = round(coal_short_tons * EMISSION_FACTORS["coal_short_ton"] / 1000, 2)
    if custom_sources:
        for name, (qty, factor) in custom_sources.items():
            breakdown[name] = round(qty * factor / 1000, 2)

    total = round(sum(breakdown.values()), 2)
    return {"scope": 1, "total_tonnes_co2e": total, "breakdown": breakdown}


def calculate_scope2(
    electricity_kwh: float = 0,
    grid_region: str = "us_avg",
    steam_mmbtu: float = 0,
    cooling_kwh: float = 0,
) -> dict:
    """Calculate Scope 2 (indirect energy) emissions.

    Args:
        electricity_kwh: Total electricity consumed.
        grid_region: Grid region for emission factor lookup.
        steam_mmbtu: Purchased steam in MMBtu.
        cooling_kwh: Purchased cooling in kWh.

    Returns:
        Dict with total Scope 2 in tonnes CO2e.
    """
    grid_factor = GRID_FACTORS.get(grid_region, GRID_FACTORS["us_avg"])
    breakdown = {}
    if electricity_kwh:
        breakdown["electricity"] = round(electricity_kwh * grid_factor / 1000, 2)
    if steam_mmbtu:
        breakdown["steam"] = round(steam_mmbtu * 66.33 / 1000, 2)  # avg steam factor
    if cooling_kwh:
        breakdown["cooling"] = round(cooling_kwh * grid_factor * 0.5 / 1000, 2)

    total = round(sum(breakdown.values()), 2)
    return {
        "scope": 2,
        "total_tonnes_co2e": total,
        "grid_region": grid_region,
        "grid_factor_kg_per_kwh": grid_factor,
        "breakdown": breakdown,
    }


def estimate_scope3(
    revenue_million_usd: float,
    industry: str = "technology",
    employee_count: int = 0,
    business_travel_miles: float = 0,
) -> dict:
    """Estimate Scope 3 (value chain) emissions using industry benchmarks.

    Args:
        revenue_million_usd: Annual revenue in $M.
        industry: Industry for intensity benchmarks.
        employee_count: Number of employees (for commuting estimate).
        business_travel_miles: Annual air travel miles.

    Returns:
        Dict with estimated Scope 3 in tonnes CO2e by category.
    """
    intensity = INDUSTRY_INTENSITY.get(industry, 50)
    # Scope 3 is typically 5-10x Scope 1+2 for most industries
    scope3_multiplier = {"energy": 3, "technology": 8, "financials": 15, "materials": 4}.get(industry, 6)

    purchased_goods = round(revenue_million_usd * intensity * scope3_multiplier * 0.4, 1)
    capital_goods = round(revenue_million_usd * intensity * 0.15, 1)
    commuting = round(employee_count * 2.4, 1) if employee_count else 0  # ~2.4 tonnes/employee/yr
    travel = round(business_travel_miles * 0.000255, 1) if business_travel_miles else 0  # kg CO2e/mile air

    breakdown = {
        "purchased_goods_services": purchased_goods,
        "capital_goods": capital_goods,
        "employee_commuting": commuting,
        "business_travel": travel,
        "use_of_sold_products": round(purchased_goods * 0.3, 1),
    }
    total = round(sum(breakdown.values()), 1)

    return {"scope": 3, "total_tonnes_co2e": total, "industry": industry, "breakdown": breakdown}


def full_footprint(
    scope1_kwargs: Optional[dict] = None,
    scope2_kwargs: Optional[dict] = None,
    scope3_kwargs: Optional[dict] = None,
) -> dict:
    """Calculate complete carbon footprint across all 3 scopes.

    Args:
        scope1_kwargs: Args for calculate_scope1.
        scope2_kwargs: Args for calculate_scope2.
        scope3_kwargs: Args for estimate_scope3.

    Returns:
        Complete footprint with scope breakdown and total.
    """
    s1 = calculate_scope1(**(scope1_kwargs or {}))
    s2 = calculate_scope2(**(scope2_kwargs or {}))
    s3 = estimate_scope3(**(scope3_kwargs or {"revenue_million_usd": 100}))

    total = round(s1["total_tonnes_co2e"] + s2["total_tonnes_co2e"] + s3["total_tonnes_co2e"], 1)

    return {
        "total_tonnes_co2e": total,
        "scope1": s1,
        "scope2": s2,
        "scope3": s3,
        "scope3_pct": round(s3["total_tonnes_co2e"] / total * 100, 1) if total > 0 else 0,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
