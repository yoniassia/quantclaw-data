"""
Climate Adaptation Investment Index (Roadmap #399)

Tracks climate adaptation investment flows, resilience infrastructure
spending, and climate risk metrics using public data sources.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


ADAPTATION_SECTORS = {
    "flood_defense": {
        "description": "Sea walls, levees, flood barriers, drainage systems",
        "annual_investment_bn": 25,
        "growth_rate_pct": 8,
        "key_regions": ["Netherlands", "US Gulf Coast", "Bangladesh", "Japan"],
    },
    "drought_resilience": {
        "description": "Desalination, water recycling, drought-resistant crops",
        "annual_investment_bn": 12,
        "growth_rate_pct": 12,
        "key_regions": ["Middle East", "California", "Australia", "Sub-Saharan Africa"],
    },
    "heat_resilience": {
        "description": "Urban cooling, heat-resistant infrastructure, green roofs",
        "annual_investment_bn": 5,
        "growth_rate_pct": 15,
        "key_regions": ["India", "Middle East", "Southern Europe", "US Southwest"],
    },
    "wildfire_defense": {
        "description": "Fire-resistant building, forest management, early warning",
        "annual_investment_bn": 4,
        "growth_rate_pct": 20,
        "key_regions": ["California", "Australia", "Mediterranean", "Canada"],
    },
    "coastal_retreat": {
        "description": "Managed retreat, relocation programs, coastal restoration",
        "annual_investment_bn": 3,
        "growth_rate_pct": 10,
        "key_regions": ["Pacific Islands", "Florida", "Southeast Asia"],
    },
    "crop_adaptation": {
        "description": "Climate-resilient seeds, precision agriculture, vertical farms",
        "annual_investment_bn": 8,
        "growth_rate_pct": 14,
        "key_regions": ["Global"],
    },
    "climate_insurance": {
        "description": "Parametric insurance, catastrophe bonds, risk transfer",
        "annual_investment_bn": 40,
        "growth_rate_pct": 7,
        "key_regions": ["Global"],
    },
    "early_warning_systems": {
        "description": "Weather prediction, disaster alerting, climate monitoring",
        "annual_investment_bn": 2,
        "growth_rate_pct": 18,
        "key_regions": ["Global"],
    },
}

CLIMATE_RISK_INDICATORS = {
    "global_avg_temp_anomaly_c": 1.45,
    "sea_level_rise_mm_per_year": 4.5,
    "annual_climate_disasters": 400,
    "annual_climate_damage_bn_usd": 380,
    "insured_losses_pct": 40,
    "adaptation_gap_bn_usd": 194,
}


def get_adaptation_index() -> Dict:
    """
    Get the Climate Adaptation Investment Index showing sector-level
    investment flows and growth rates.
    """
    total_investment = sum(s["annual_investment_bn"] for s in ADAPTATION_SECTORS.values())
    weighted_growth = sum(
        s["annual_investment_bn"] * s["growth_rate_pct"]
        for s in ADAPTATION_SECTORS.values()
    ) / total_investment

    sectors_ranked = sorted(
        [{"sector": k, **v} for k, v in ADAPTATION_SECTORS.items()],
        key=lambda x: x["annual_investment_bn"],
        reverse=True,
    )

    return {
        "total_annual_investment_bn": total_investment,
        "weighted_avg_growth_pct": round(weighted_growth, 1),
        "sectors_by_investment": sectors_ranked,
        "risk_indicators": CLIMATE_RISK_INDICATORS,
        "as_of": datetime.utcnow().isoformat(),
    }


def get_sector_detail(sector_name: str) -> Optional[Dict]:
    """
    Get detailed investment data for a specific adaptation sector.
    """
    for name, data in ADAPTATION_SECTORS.items():
        if sector_name.lower().replace(" ", "_") in name.lower() or sector_name.lower() in data["description"].lower():
            return {"sector": name, **data}
    return None


def adaptation_gap_analysis() -> Dict:
    """
    Analyze the gap between needed and actual climate adaptation spending.
    """
    return {
        "annual_adaptation_spending_bn": 99,
        "estimated_annual_need_bn": 293,
        "adaptation_gap_bn": 194,
        "gap_by_region": [
            {"region": "Sub-Saharan Africa", "need_bn": 50, "actual_bn": 5, "gap_pct": 90},
            {"region": "South Asia", "need_bn": 45, "actual_bn": 8, "gap_pct": 82},
            {"region": "Southeast Asia", "need_bn": 35, "actual_bn": 7, "gap_pct": 80},
            {"region": "Latin America", "need_bn": 25, "actual_bn": 6, "gap_pct": 76},
            {"region": "Small Island States", "need_bn": 8, "actual_bn": 1, "gap_pct": 88},
        ],
        "funding_sources": {
            "public_domestic_pct": 45,
            "multilateral_development_banks_pct": 25,
            "bilateral_aid_pct": 15,
            "private_sector_pct": 10,
            "philanthropic_pct": 5,
        },
        "key_insight": "Private capital accounts for only 10% of adaptation finance vs 60% for mitigation",
    }


def climate_resilience_etfs() -> Dict:
    """
    Track climate adaptation and resilience-focused investment vehicles.
    """
    return {
        "etfs_and_funds": [
            {"name": "First Trust Water ETF", "ticker": "FIW", "aum_mn": 1200, "focus": "water infrastructure"},
            {"name": "Invesco Water Resources ETF", "ticker": "PHO", "aum_mn": 2100, "focus": "water"},
            {"name": "iShares Global Clean Energy ETF", "ticker": "ICLN", "aum_mn": 3000, "focus": "clean energy"},
            {"name": "Global X CleanTech ETF", "ticker": "CTEC", "aum_mn": 100, "focus": "cleantech"},
        ],
        "cat_bond_market": {
            "outstanding_bn": 45,
            "annual_issuance_bn": 16,
            "avg_spread_bps": 850,
            "trend": "Record issuance as climate losses increase",
        },
        "green_bond_adaptation_share_pct": 8,
        "note": "Most green bonds fund mitigation; adaptation-labeled bonds are emerging",
    }
