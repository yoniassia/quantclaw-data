"""
Carbon Footprint Calculator — Scope 1/2/3 emissions estimation.

Estimates corporate carbon footprints using EPA emission factors,
energy consumption data, and supply chain multipliers.
Free data sources: EPA GHG factors, EIA energy data.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


# EPA emission factors (kg CO2e per unit)
EMISSION_FACTORS = {
    # Scope 1: Direct emissions
    "natural_gas": {"factor": 53.06, "unit": "kg CO2e/MMBtu"},
    "diesel": {"factor": 10.21, "unit": "kg CO2e/gallon"},
    "gasoline": {"factor": 8.887, "unit": "kg CO2e/gallon"},
    "propane": {"factor": 5.72, "unit": "kg CO2e/gallon"},
    "coal_bituminous": {"factor": 93.28, "unit": "kg CO2e/MMBtu"},
    "fuel_oil": {"factor": 10.21, "unit": "kg CO2e/gallon"},
    # Scope 2: Electricity (US average)
    "electricity_us_avg": {"factor": 0.386, "unit": "kg CO2e/kWh"},
    "electricity_eu_avg": {"factor": 0.276, "unit": "kg CO2e/kWh"},
    "electricity_china": {"factor": 0.555, "unit": "kg CO2e/kWh"},
    "electricity_india": {"factor": 0.708, "unit": "kg CO2e/kWh"},
    "electricity_uk": {"factor": 0.212, "unit": "kg CO2e/kWh"},
    # Scope 3: Supply chain multipliers (kg CO2e per $1000 spend)
    "manufacturing": {"factor": 420, "unit": "kg CO2e/$1000"},
    "transportation": {"factor": 580, "unit": "kg CO2e/$1000"},
    "professional_services": {"factor": 120, "unit": "kg CO2e/$1000"},
    "it_services": {"factor": 180, "unit": "kg CO2e/$1000"},
    "construction": {"factor": 350, "unit": "kg CO2e/$1000"},
    "agriculture": {"factor": 680, "unit": "kg CO2e/$1000"},
    "mining": {"factor": 820, "unit": "kg CO2e/$1000"},
}

# GHG Protocol sector benchmarks (tonnes CO2e per $M revenue)
SECTOR_BENCHMARKS = {
    "technology": 25,
    "financial_services": 15,
    "healthcare": 45,
    "manufacturing": 180,
    "energy_oil_gas": 550,
    "utilities": 800,
    "retail": 65,
    "transportation": 320,
    "real_estate": 40,
    "agriculture": 280,
    "mining": 450,
    "construction": 120,
    "telecom": 35,
    "media": 20,
}


def calculate_scope1(
    fuel_consumption: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate Scope 1 (direct) emissions from fuel consumption.

    Args:
        fuel_consumption: Dict mapping fuel type to quantity consumed.
            e.g. {"natural_gas": 1000, "diesel": 500}

    Returns:
        Breakdown of emissions by fuel type + total in kg CO2e.
    """
    breakdown = {}
    total = 0.0

    for fuel, quantity in fuel_consumption.items():
        if fuel in EMISSION_FACTORS:
            factor = EMISSION_FACTORS[fuel]["factor"]
            emissions = quantity * factor
            breakdown[fuel] = {
                "quantity": quantity,
                "factor": factor,
                "unit": EMISSION_FACTORS[fuel]["unit"],
                "emissions_kg_co2e": round(emissions, 2),
            }
            total += emissions

    return {
        "scope": 1,
        "description": "Direct emissions from owned/controlled sources",
        "breakdown": breakdown,
        "total_kg_co2e": round(total, 2),
        "total_tonnes_co2e": round(total / 1000, 2),
    }


def calculate_scope2(
    electricity_kwh: float,
    region: str = "us_avg",
    steam_mmbtu: float = 0,
    cooling_kwh: float = 0,
) -> Dict:
    """
    Calculate Scope 2 (indirect energy) emissions.

    Args:
        electricity_kwh: Annual electricity consumption in kWh.
        region: Grid region for emission factor.
        steam_mmbtu: Purchased steam in MMBtu.
        cooling_kwh: Purchased cooling in kWh equivalent.

    Returns:
        Scope 2 emissions breakdown.
    """
    elec_key = f"electricity_{region}"
    elec_factor = EMISSION_FACTORS.get(elec_key, EMISSION_FACTORS["electricity_us_avg"])["factor"]

    elec_emissions = electricity_kwh * elec_factor
    steam_emissions = steam_mmbtu * 53.06  # natural gas equivalent
    cooling_emissions = cooling_kwh * elec_factor * 0.3  # COP adjustment

    total = elec_emissions + steam_emissions + cooling_emissions

    return {
        "scope": 2,
        "description": "Indirect emissions from purchased energy",
        "electricity": {
            "kwh": electricity_kwh,
            "region": region,
            "factor": elec_factor,
            "emissions_kg_co2e": round(elec_emissions, 2),
        },
        "steam": {
            "mmbtu": steam_mmbtu,
            "emissions_kg_co2e": round(steam_emissions, 2),
        },
        "cooling": {
            "kwh": cooling_kwh,
            "emissions_kg_co2e": round(cooling_emissions, 2),
        },
        "total_kg_co2e": round(total, 2),
        "total_tonnes_co2e": round(total / 1000, 2),
    }


def calculate_scope3(
    supply_chain_spend: Dict[str, float],
    employee_commute_km: float = 0,
    business_travel_km: float = 0,
    waste_tonnes: float = 0,
) -> Dict:
    """
    Calculate Scope 3 (value chain) emissions using spend-based method.

    Args:
        supply_chain_spend: Dict mapping category to annual spend in $1000s.
        employee_commute_km: Total annual employee commute km.
        business_travel_km: Total annual business travel km (air).
        waste_tonnes: Annual waste generated in tonnes.

    Returns:
        Scope 3 emissions breakdown.
    """
    breakdown = {}
    total = 0.0

    # Purchased goods & services (spend-based)
    for category, spend_k in supply_chain_spend.items():
        if category in EMISSION_FACTORS:
            factor = EMISSION_FACTORS[category]["factor"]
            emissions = spend_k * factor
            breakdown[category] = {
                "spend_k_usd": spend_k,
                "factor": factor,
                "emissions_kg_co2e": round(emissions, 2),
            }
            total += emissions

    # Employee commuting (avg 0.21 kg CO2e/km for mixed mode)
    commute_emissions = employee_commute_km * 0.21
    if employee_commute_km > 0:
        breakdown["employee_commute"] = {
            "km": employee_commute_km,
            "emissions_kg_co2e": round(commute_emissions, 2),
        }
        total += commute_emissions

    # Business travel (avg 0.255 kg CO2e/km for air)
    travel_emissions = business_travel_km * 0.255
    if business_travel_km > 0:
        breakdown["business_travel"] = {
            "km": business_travel_km,
            "emissions_kg_co2e": round(travel_emissions, 2),
        }
        total += travel_emissions

    # Waste (avg 460 kg CO2e/tonne for mixed waste)
    waste_emissions = waste_tonnes * 460
    if waste_tonnes > 0:
        breakdown["waste"] = {
            "tonnes": waste_tonnes,
            "emissions_kg_co2e": round(waste_emissions, 2),
        }
        total += waste_emissions

    return {
        "scope": 3,
        "description": "Value chain emissions (upstream + downstream)",
        "method": "spend-based + activity-based hybrid",
        "breakdown": breakdown,
        "total_kg_co2e": round(total, 2),
        "total_tonnes_co2e": round(total / 1000, 2),
    }


def full_carbon_footprint(
    fuel_consumption: Optional[Dict[str, float]] = None,
    electricity_kwh: float = 0,
    region: str = "us_avg",
    supply_chain_spend: Optional[Dict[str, float]] = None,
    employee_commute_km: float = 0,
    business_travel_km: float = 0,
    waste_tonnes: float = 0,
    revenue_millions: Optional[float] = None,
    sector: Optional[str] = None,
) -> Dict:
    """
    Calculate complete carbon footprint across all scopes.

    Returns total emissions with sector benchmark comparison.
    """
    scope1 = calculate_scope1(fuel_consumption or {})
    scope2 = calculate_scope2(electricity_kwh, region)
    scope3 = calculate_scope3(
        supply_chain_spend or {},
        employee_commute_km,
        business_travel_km,
        waste_tonnes,
    )

    total_tonnes = scope1["total_tonnes_co2e"] + scope2["total_tonnes_co2e"] + scope3["total_tonnes_co2e"]

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "total_tonnes_co2e": round(total_tonnes, 2),
        "scope_percentages": {
            "scope1": round(scope1["total_tonnes_co2e"] / max(total_tonnes, 0.01) * 100, 1),
            "scope2": round(scope2["total_tonnes_co2e"] / max(total_tonnes, 0.01) * 100, 1),
            "scope3": round(scope3["total_tonnes_co2e"] / max(total_tonnes, 0.01) * 100, 1),
        },
    }

    if revenue_millions and sector and sector in SECTOR_BENCHMARKS:
        benchmark = SECTOR_BENCHMARKS[sector]
        intensity = total_tonnes / revenue_millions
        result["benchmark"] = {
            "sector": sector,
            "sector_avg_tonnes_per_m_revenue": benchmark,
            "company_tonnes_per_m_revenue": round(intensity, 2),
            "vs_benchmark": f"{'above' if intensity > benchmark else 'below'} sector average",
            "percentile_estimate": round(min(100, max(0, (1 - intensity / benchmark) * 50 + 50)), 0),
        }

    return result


def get_emission_factors() -> Dict:
    """Return all available emission factors with units."""
    return EMISSION_FACTORS


def sector_benchmark_comparison(
    total_tonnes: float, revenue_millions: float
) -> List[Dict]:
    """
    Compare a company's carbon intensity against all sector benchmarks.

    Returns ranked list of sectors with intensity comparison.
    """
    intensity = total_tonnes / max(revenue_millions, 0.01)
    results = []
    for sector, benchmark in sorted(SECTOR_BENCHMARKS.items(), key=lambda x: x[1]):
        results.append({
            "sector": sector,
            "benchmark_tonnes_per_m": benchmark,
            "company_intensity": round(intensity, 2),
            "ratio": round(intensity / benchmark, 2),
            "status": "cleaner" if intensity < benchmark else "dirtier",
        })
    return results
