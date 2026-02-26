"""
Lithium / Battery Metals Index (Roadmap #373)
Tracks lithium, cobalt, nickel, manganese, and graphite prices,
supply/demand dynamics, and EV demand forecasting using free data.
"""

import datetime
import math
from typing import Dict, List, Optional, Tuple


# Battery metals and their ETF/stock proxies for price tracking
BATTERY_METALS = {
    "lithium": {
        "etf": "LIT",
        "miners": ["ALB", "SQM", "LTHM", "PLL", "LAC"],
        "unit": "$/tonne",
        "battery_share_pct": 12,
        "description": "Primary cathode material for Li-ion batteries",
    },
    "cobalt": {
        "etf": None,
        "miners": ["GLNCY", "VALE"],
        "unit": "$/lb",
        "battery_share_pct": 5,
        "description": "Cathode stabilizer (NMC/NCA chemistries)",
    },
    "nickel": {
        "etf": None,
        "miners": ["VALE", "BHP", "GLNCY"],
        "unit": "$/tonne",
        "battery_share_pct": 8,
        "description": "High energy density cathode material",
    },
    "manganese": {
        "etf": None,
        "miners": ["MNXXF", "EMN.AX"],
        "unit": "$/tonne",
        "battery_share_pct": 3,
        "description": "Cathode material (LMO/NMC chemistries)",
    },
    "graphite": {
        "etf": None,
        "miners": ["SYA.AX", "NOU.V"],
        "unit": "$/tonne",
        "battery_share_pct": 28,
        "description": "Primary anode material",
    },
}

# Battery chemistry market shares (approximate 2025)
BATTERY_CHEMISTRIES = {
    "LFP": {"share_pct": 45, "metals": ["lithium"], "trend": "growing"},
    "NMC_811": {"share_pct": 25, "metals": ["lithium", "nickel", "manganese", "cobalt"], "trend": "stable"},
    "NMC_622": {"share_pct": 12, "metals": ["lithium", "nickel", "manganese", "cobalt"], "trend": "declining"},
    "NCA": {"share_pct": 10, "metals": ["lithium", "nickel", "cobalt"], "trend": "stable"},
    "NMC_532": {"share_pct": 5, "metals": ["lithium", "nickel", "manganese", "cobalt"], "trend": "declining"},
    "sodium_ion": {"share_pct": 3, "metals": [], "trend": "growing"},
}


def get_battery_metal_overview() -> Dict[str, Dict]:
    """
    Get overview of all tracked battery metals with key metrics.
    
    Returns:
        Dict of metal name -> details including proxies and battery relevance
    """
    return {
        name: {
            "tracking_etf": info["etf"],
            "key_miners": info["miners"],
            "price_unit": info["unit"],
            "battery_cost_share_pct": info["battery_share_pct"],
            "description": info["description"],
        }
        for name, info in BATTERY_METALS.items()
    }


def calculate_battery_cost_index(metal_prices: Dict[str, float]) -> Dict:
    """
    Calculate a composite battery cost index from metal prices.
    Uses approximate metal content per kWh for NMC811 chemistry.
    
    Args:
        metal_prices: Dict of metal name -> current price in standard units
        
    Returns:
        Cost breakdown and total $/kWh for raw materials
    """
    # Approximate kg of metal per kWh (NMC 811 pouch cell)
    kg_per_kwh = {
        "lithium": 0.11,
        "nickel": 0.75,
        "cobalt": 0.09,
        "manganese": 0.08,
        "graphite": 1.0,
    }
    
    cost_breakdown = {}
    total = 0.0
    
    for metal, kg in kg_per_kwh.items():
        price = metal_prices.get(metal, 0)
        # Convert $/tonne to $/kg for tonne-priced metals
        if BATTERY_METALS[metal]["unit"] == "$/tonne":
            price_per_kg = price / 1000
        elif BATTERY_METALS[metal]["unit"] == "$/lb":
            price_per_kg = price * 2.20462
        else:
            price_per_kg = price
        
        cost = round(kg * price_per_kg, 2)
        cost_breakdown[metal] = {
            "kg_per_kwh": kg,
            "price_per_kg": round(price_per_kg, 2),
            "cost_per_kwh": cost,
        }
        total += cost
    
    return {
        "chemistry": "NMC_811",
        "breakdown": cost_breakdown,
        "total_materials_per_kwh": round(total, 2),
        "currency": "USD",
    }


def ev_demand_forecast(year: int = 2026) -> Dict:
    """
    Forecast battery metal demand based on EV adoption projections.
    
    Args:
        year: Target year for forecast (2024-2035)
        
    Returns:
        Demand forecast by metal in tonnes
    """
    # Base: 2024 ~14M EVs sold, ~700 GWh battery demand
    base_year = 2024
    base_ev_sales = 14_000_000
    base_gwh = 700
    growth_rate = 0.22  # ~22% CAGR
    
    years_out = year - base_year
    if years_out < 0:
        years_out = 0
    
    projected_ev_sales = int(base_ev_sales * (1 + growth_rate) ** years_out)
    projected_gwh = round(base_gwh * (1 + growth_rate) ** years_out)
    
    # Tonnes of metal per GWh (weighted average across chemistries)
    tonnes_per_gwh = {
        "lithium": 110,
        "nickel": 400,
        "cobalt": 45,
        "manganese": 50,
        "graphite": 800,
    }
    
    demand = {}
    for metal, tpg in tonnes_per_gwh.items():
        demand[metal] = {
            "tonnes_needed": round(projected_gwh * tpg),
            "tonnes_per_gwh": tpg,
        }
    
    return {
        "year": year,
        "projected_ev_sales": projected_ev_sales,
        "projected_battery_gwh": projected_gwh,
        "metal_demand_tonnes": demand,
    }


def supply_risk_matrix() -> List[Dict]:
    """
    Generate supply risk matrix for all battery metals.
    
    Returns:
        Sorted list of metals by risk score (highest first)
    """
    risks = {
        "lithium": {"geographic_concentration": 65, "processing_bottleneck": 70, "demand_growth": 95, "recycling_rate": 5},
        "cobalt": {"geographic_concentration": 90, "processing_bottleneck": 85, "demand_growth": 60, "recycling_rate": 10},
        "nickel": {"geographic_concentration": 55, "processing_bottleneck": 60, "demand_growth": 80, "recycling_rate": 15},
        "manganese": {"geographic_concentration": 45, "processing_bottleneck": 40, "demand_growth": 50, "recycling_rate": 8},
        "graphite": {"geographic_concentration": 80, "processing_bottleneck": 90, "demand_growth": 85, "recycling_rate": 2},
    }
    
    results = []
    for metal, factors in risks.items():
        score = round(
            factors["geographic_concentration"] * 0.3 +
            factors["processing_bottleneck"] * 0.3 +
            factors["demand_growth"] * 0.25 +
            (100 - factors["recycling_rate"]) * 0.15,
            1
        )
        results.append({
            "metal": metal,
            "risk_score": score,
            "risk_level": "critical" if score >= 75 else "high" if score >= 60 else "moderate",
            **factors,
        })
    
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)


def chemistry_shift_impact() -> Dict[str, Dict]:
    """
    Analyze how battery chemistry shifts affect metal demand.
    
    Returns:
        Impact analysis for each metal based on chemistry trends
    """
    impacts = {}
    for metal in BATTERY_METALS:
        exposure = []
        growing = 0
        declining = 0
        for chem, info in BATTERY_CHEMISTRIES.items():
            if metal in info["metals"]:
                exposure.append(chem)
                if info["trend"] == "growing":
                    growing += info["share_pct"]
                elif info["trend"] == "declining":
                    declining += info["share_pct"]
        
        net_trend = growing - declining
        impacts[metal] = {
            "exposed_chemistries": exposure,
            "growing_share_pct": growing,
            "declining_share_pct": declining,
            "net_trend_impact": "positive" if net_trend > 5 else "negative" if net_trend < -5 else "neutral",
            "lfp_threat": metal != "lithium" and "LFP" not in exposure,
            "sodium_ion_threat": metal == "lithium",
        }
    
    return impacts
