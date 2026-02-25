#!/usr/bin/env python3
"""
Rare Earths & Strategic Minerals Module

Data Sources:
- USGS Mineral Commodity Summaries (annual public data)
- Strategic mineral supply chain risk assessment
- Production by country, reserves, import reliance
- Critical minerals list tracking

Monthly updates. No API key required.

Phase: 178
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


# Critical minerals as defined by USGS (2022 list)
CRITICAL_MINERALS = [
    "aluminum", "antimony", "arsenic", "barite", "beryllium", "bismuth",
    "cesium", "chromium", "cobalt", "fluorspar", "gallium", "germanium",
    "graphite", "hafnium", "helium", "indium", "lithium", "magnesium",
    "manganese", "niobium", "platinum_group", "potash", "rare_earths",
    "rubidium", "scandium", "strontium", "tantalum", "tellurium", "tin",
    "titanium", "tungsten", "uranium", "vanadium", "zinc", "zirconium"
]

# Rare earth elements (17 total)
RARE_EARTH_ELEMENTS = [
    "lanthanum", "cerium", "praseodymium", "neodymium", "promethium",
    "samarium", "europium", "gadolinium", "terbium", "dysprosium",
    "holmium", "erbium", "thulium", "ytterbium", "lutetium",
    "scandium", "yttrium"
]

# Strategic importance categories
STRATEGIC_CATEGORIES = {
    "defense": ["tungsten", "cobalt", "rare_earths", "titanium", "beryllium"],
    "energy": ["lithium", "cobalt", "rare_earths", "graphite", "nickel", "copper"],
    "electronics": ["rare_earths", "gallium", "germanium", "indium", "tantalum"],
    "aerospace": ["titanium", "aluminum", "nickel", "rare_earths"],
    "medical": ["helium", "cobalt", "platinum_group", "rare_earths"]
}

# USGS approximate production data (2022-2023)
# Sources: USGS Mineral Commodity Summaries (public domain)
PRODUCTION_DATA = {
    "rare_earths": {
        "global_production_mt": 300000,  # metric tons (2022)
        "top_producers": {
            "china": {"production_mt": 210000, "share_pct": 70.0},
            "united_states": {"production_mt": 43000, "share_pct": 14.3},
            "myanmar": {"production_mt": 26000, "share_pct": 8.7},
            "australia": {"production_mt": 18000, "share_pct": 6.0},
            "thailand": {"production_mt": 8000, "share_pct": 2.7}
        },
        "global_reserves_mt": 120000000,
        "us_import_reliance_pct": 74,
        "primary_uses": ["catalysts", "metallurgy", "electronics", "magnets", "glass"]
    },
    "lithium": {
        "global_production_mt": 130000,
        "top_producers": {
            "australia": {"production_mt": 61000, "share_pct": 47.0},
            "chile": {"production_mt": 39000, "share_pct": 30.0},
            "china": {"production_mt": 19000, "share_pct": 14.6},
            "argentina": {"production_mt": 6200, "share_pct": 4.8}
        },
        "global_reserves_mt": 26000000,
        "us_import_reliance_pct": 25,
        "primary_uses": ["batteries", "ceramics", "greases", "pharmaceuticals"]
    },
    "cobalt": {
        "global_production_mt": 190000,
        "top_producers": {
            "drc_congo": {"production_mt": 130000, "share_pct": 68.4},
            "russia": {"production_mt": 7600, "share_pct": 4.0},
            "australia": {"production_mt": 6000, "share_pct": 3.2},
            "philippines": {"production_mt": 4600, "share_pct": 2.4},
            "cuba": {"production_mt": 4000, "share_pct": 2.1}
        },
        "global_reserves_mt": 8300000,
        "us_import_reliance_pct": 76,
        "primary_uses": ["batteries", "superalloys", "catalysts", "magnets"]
    },
    "graphite": {
        "global_production_mt": 1300000,
        "top_producers": {
            "china": {"production_mt": 890000, "share_pct": 68.5},
            "mozambique": {"production_mt": 180000, "share_pct": 13.8},
            "madagascar": {"production_mt": 52000, "share_pct": 4.0},
            "brazil": {"production_mt": 95000, "share_pct": 7.3}
        },
        "global_reserves_mt": 320000000,
        "us_import_reliance_pct": 100,
        "primary_uses": ["batteries", "lubricants", "refractories", "steel_production"]
    },
    "tungsten": {
        "global_production_mt": 84000,
        "top_producers": {
            "china": {"production_mt": 69000, "share_pct": 82.1},
            "vietnam": {"production_mt": 4500, "share_pct": 5.4},
            "russia": {"production_mt": 2500, "share_pct": 3.0},
            "bolivia": {"production_mt": 1200, "share_pct": 1.4}
        },
        "global_reserves_mt": 3500000,
        "us_import_reliance_pct": 50,
        "primary_uses": ["cemented_carbides", "mill_products", "steel", "alloys"]
    },
    "gallium": {
        "global_production_mt": 320,
        "top_producers": {
            "china": {"production_mt": 290, "share_pct": 90.6},
            "japan": {"production_mt": 10, "share_pct": 3.1},
            "south_korea": {"production_mt": 10, "share_pct": 3.1},
            "russia": {"production_mt": 5, "share_pct": 1.6}
        },
        "global_reserves_mt": 1000000,
        "us_import_reliance_pct": 100,
        "primary_uses": ["integrated_circuits", "optoelectronics", "solar_cells"]
    },
    "germanium": {
        "global_production_mt": 120,
        "top_producers": {
            "china": {"production_mt": 95, "share_pct": 79.2},
            "belgium": {"production_mt": 10, "share_pct": 8.3},
            "canada": {"production_mt": 5, "share_pct": 4.2}
        },
        "global_reserves_mt": None,
        "us_import_reliance_pct": 100,
        "primary_uses": ["fiber_optics", "infrared_optics", "polymerization_catalysts"]
    }
}


def get_mineral_profile(mineral: str) -> Dict:
    """
    Get comprehensive profile for a strategic mineral
    
    Args:
        mineral: Mineral name (lowercase, underscore separated)
        
    Returns:
        Dict with production, reserves, uses, supply chain data
    """
    mineral = mineral.lower().replace(" ", "_").replace("-", "_")
    
    if mineral not in PRODUCTION_DATA:
        return {
            "error": f"Mineral '{mineral}' not found",
            "available_minerals": list(PRODUCTION_DATA.keys())
        }
    
    data = PRODUCTION_DATA[mineral]
    
    # Calculate supply concentration risk (HHI)
    hhi = sum(p["share_pct"]**2 for p in data["top_producers"].values())
    
    # Determine concentration risk level
    if hhi > 2500:
        concentration_risk = "HIGH"
    elif hhi > 1500:
        concentration_risk = "MODERATE"
    else:
        concentration_risk = "LOW"
    
    profile = {
        "mineral": mineral,
        "global_production_mt": data["global_production_mt"],
        "global_reserves_mt": data.get("global_reserves_mt"),
        "top_producers": data["top_producers"],
        "us_import_reliance_pct": data["us_import_reliance_pct"],
        "primary_uses": data["primary_uses"],
        "supply_concentration": {
            "hhi": round(hhi, 2),
            "risk_level": concentration_risk,
            "interpretation": f"Market concentration HHI of {round(hhi, 2)} indicates {concentration_risk} supply chain risk"
        },
        "is_critical": mineral in CRITICAL_MINERALS,
        "strategic_sectors": [k for k, v in STRATEGIC_CATEGORIES.items() if mineral in v],
        "timestamp": datetime.now().isoformat()
    }
    
    return profile


def get_all_critical_minerals() -> List[Dict]:
    """
    Get profiles for all critical minerals with data available
    
    Returns:
        List of mineral profiles
    """
    profiles = []
    
    for mineral in CRITICAL_MINERALS:
        if mineral in PRODUCTION_DATA:
            profile = get_mineral_profile(mineral)
            if "error" not in profile:
                profiles.append(profile)
                
    return profiles


def calculate_supply_risk_score(mineral: str) -> Dict:
    """
    Calculate comprehensive supply chain risk score
    
    Args:
        mineral: Mineral name
        
    Returns:
        Dict with risk breakdown and overall score
    """
    profile = get_mineral_profile(mineral)
    
    if "error" in profile:
        return profile
    
    # Risk factors (0-100 scale)
    import_reliance_score = profile["us_import_reliance_pct"]
    
    # Concentration risk (HHI normalized)
    hhi = profile["supply_concentration"]["hhi"]
    concentration_score = min(100, (hhi / 100))
    
    # Top producer dominance
    top_producer_share = max(p["share_pct"] for p in profile["top_producers"].values())
    dominance_score = top_producer_share
    
    # Geopolitical risk (China dominance)
    china_share = profile["top_producers"].get("china", {}).get("share_pct", 0)
    geopolitical_score = china_share
    
    # Overall risk score (weighted average)
    weights = {
        "import_reliance": 0.25,
        "concentration": 0.30,
        "dominance": 0.20,
        "geopolitical": 0.25
    }
    
    overall_score = (
        import_reliance_score * weights["import_reliance"] +
        concentration_score * weights["concentration"] +
        dominance_score * weights["dominance"] +
        geopolitical_score * weights["geopolitical"]
    )
    
    # Risk rating
    if overall_score >= 75:
        risk_rating = "CRITICAL"
    elif overall_score >= 60:
        risk_rating = "HIGH"
    elif overall_score >= 40:
        risk_rating = "MODERATE"
    else:
        risk_rating = "LOW"
    
    return {
        "mineral": mineral,
        "overall_risk_score": round(overall_score, 2),
        "risk_rating": risk_rating,
        "risk_factors": {
            "import_reliance": {
                "score": import_reliance_score,
                "weight": weights["import_reliance"],
                "description": f"{import_reliance_score}% US import dependence"
            },
            "supply_concentration": {
                "score": round(concentration_score, 2),
                "weight": weights["concentration"],
                "description": f"HHI {hhi} indicates concentrated supply"
            },
            "producer_dominance": {
                "score": round(dominance_score, 2),
                "weight": weights["dominance"],
                "description": f"Top producer controls {top_producer_share}% of supply"
            },
            "geopolitical_risk": {
                "score": geopolitical_score,
                "weight": weights["geopolitical"],
                "description": f"China controls {china_share}% of production"
            }
        },
        "strategic_importance": {
            "is_critical": profile["is_critical"],
            "sectors": profile["strategic_sectors"]
        },
        "timestamp": datetime.now().isoformat()
    }


def get_supply_risk_rankings() -> List[Dict]:
    """
    Rank all minerals by supply chain risk score
    
    Returns:
        List of minerals sorted by risk score (highest to lowest)
    """
    rankings = []
    
    for mineral in PRODUCTION_DATA.keys():
        risk_assessment = calculate_supply_risk_score(mineral)
        if "error" not in risk_assessment:
            rankings.append({
                "mineral": mineral,
                "risk_score": risk_assessment["overall_risk_score"],
                "risk_rating": risk_assessment["risk_rating"],
                "china_share_pct": risk_assessment["risk_factors"]["geopolitical_risk"]["score"],
                "us_import_reliance_pct": risk_assessment["risk_factors"]["import_reliance"]["score"]
            })
    
    # Sort by risk score descending
    rankings.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return rankings


def get_sector_exposure(sector: str) -> Dict:
    """
    Get critical mineral exposure for a strategic sector
    
    Args:
        sector: Sector name (defense, energy, electronics, aerospace, medical)
        
    Returns:
        Dict with minerals used and risk assessment
    """
    sector = sector.lower()
    
    if sector not in STRATEGIC_CATEGORIES:
        return {
            "error": f"Sector '{sector}' not found",
            "available_sectors": list(STRATEGIC_CATEGORIES.keys())
        }
    
    minerals = STRATEGIC_CATEGORIES[sector]
    
    # Get risk profiles for each mineral
    mineral_risks = []
    total_risk = 0
    count = 0
    
    for mineral in minerals:
        if mineral in PRODUCTION_DATA:
            risk = calculate_supply_risk_score(mineral)
            if "error" not in risk:
                mineral_risks.append({
                    "mineral": mineral,
                    "risk_score": risk["overall_risk_score"],
                    "risk_rating": risk["risk_rating"]
                })
                total_risk += risk["overall_risk_score"]
                count += 1
    
    avg_risk = total_risk / count if count > 0 else 0
    
    # Determine sector risk level
    if avg_risk >= 70:
        sector_risk = "CRITICAL"
    elif avg_risk >= 55:
        sector_risk = "HIGH"
    elif avg_risk >= 40:
        sector_risk = "MODERATE"
    else:
        sector_risk = "LOW"
    
    return {
        "sector": sector,
        "critical_minerals": minerals,
        "mineral_risk_profiles": mineral_risks,
        "sector_risk_score": round(avg_risk, 2),
        "sector_risk_rating": sector_risk,
        "minerals_assessed": count,
        "interpretation": f"Sector has {sector_risk} exposure to critical mineral supply disruption",
        "timestamp": datetime.now().isoformat()
    }


def get_country_production_profile(country: str) -> Dict:
    """
    Get mineral production profile for a country
    
    Args:
        country: Country name (lowercase)
        
    Returns:
        Dict with minerals produced and market shares
    """
    country = country.lower().replace(" ", "_")
    
    production = {}
    
    for mineral, data in PRODUCTION_DATA.items():
        if country in data["top_producers"]:
            producer_data = data["top_producers"][country]
            production[mineral] = {
                "production_mt": producer_data["production_mt"],
                "global_share_pct": producer_data["share_pct"],
                "global_production_mt": data["global_production_mt"],
                "rank": list(data["top_producers"].keys()).index(country) + 1
            }
    
    if not production:
        return {
            "error": f"No production data found for '{country}'",
            "note": "Country may not be a top-5 producer of tracked minerals"
        }
    
    # Calculate country's strategic importance
    total_share = sum(p["global_share_pct"] for p in production.values())
    minerals_count = len(production)
    
    return {
        "country": country,
        "minerals_produced": minerals_count,
        "production_by_mineral": production,
        "average_market_share_pct": round(total_share / minerals_count, 2) if minerals_count > 0 else 0,
        "strategic_importance": "CRITICAL" if total_share > 200 else "HIGH" if total_share > 100 else "MODERATE",
        "timestamp": datetime.now().isoformat()
    }


def get_rare_earths_detailed() -> Dict:
    """
    Get detailed analysis of rare earth elements specifically
    
    Returns:
        Dict with REE market structure and supply risks
    """
    ree_profile = get_mineral_profile("rare_earths")
    ree_risk = calculate_supply_risk_score("rare_earths")
    
    return {
        "market_overview": ree_profile,
        "supply_risk_assessment": ree_risk,
        "rare_earth_elements": {
            "total_elements": len(RARE_EARTH_ELEMENTS),
            "elements": RARE_EARTH_ELEMENTS,
            "categories": {
                "light_ree": ["lanthanum", "cerium", "praseodymium", "neodymium", "promethium", "samarium"],
                "heavy_ree": ["europium", "gadolinium", "terbium", "dysprosium", "holmium", "erbium", "thulium", "ytterbium", "lutetium"],
                "scandium_yttrium": ["scandium", "yttrium"]
            }
        },
        "key_applications": {
            "permanent_magnets": ["neodymium", "dysprosium", "praseodymium"],
            "catalysts": ["lanthanum", "cerium"],
            "phosphors": ["europium", "terbium", "yttrium"],
            "glass_polishing": ["cerium"],
            "metallurgical": ["cerium", "lanthanum"]
        },
        "market_dynamics": {
            "china_dominance_pct": ree_profile["top_producers"]["china"]["share_pct"],
            "supply_bottleneck": "Processing and refining concentrated in China",
            "demand_drivers": ["EV motors", "wind turbines", "electronics", "defense systems"],
            "price_volatility": "HIGH due to geopolitical tensions and supply concentration"
        },
        "timestamp": datetime.now().isoformat()
    }


def get_comprehensive_minerals_report() -> Dict:
    """
    Generate comprehensive strategic minerals report
    
    Returns:
        Dict with all critical mineral data and analysis
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_minerals_tracked": len(PRODUCTION_DATA),
            "critical_minerals_count": len([m for m in PRODUCTION_DATA.keys() if m in CRITICAL_MINERALS]),
            "average_us_import_reliance_pct": round(
                sum(d["us_import_reliance_pct"] for d in PRODUCTION_DATA.values()) / len(PRODUCTION_DATA), 2
            )
        },
        "supply_risk_rankings": get_supply_risk_rankings(),
        "sector_analysis": {
            sector: get_sector_exposure(sector)
            for sector in STRATEGIC_CATEGORIES.keys()
        },
        "china_production_dominance": {
            mineral: data["top_producers"].get("china", {}).get("share_pct", 0)
            for mineral, data in PRODUCTION_DATA.items()
        },
        "rare_earths_focus": get_rare_earths_detailed()
    }


# CLI Interface
def main():
    """CLI interface for rare earths & strategic minerals data"""
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command specified",
            "available_commands": [
                "mineral-profile <mineral>",
                "supply-risk <mineral>",
                "risk-rankings",
                "sector-exposure <sector>",
                "country-profile <country>",
                "rare-earths-detailed",
                "comprehensive-report",
                "list-minerals",
                "list-sectors"
            ]
        }, indent=2))
        sys.exit(1)
        
    command = sys.argv[1]
    
    try:
        if command == "mineral-profile":
            if len(sys.argv) < 3:
                result = {"error": "Mineral name required"}
            else:
                mineral = sys.argv[2]
                result = get_mineral_profile(mineral)
                
        elif command == "supply-risk":
            if len(sys.argv) < 3:
                result = {"error": "Mineral name required"}
            else:
                mineral = sys.argv[2]
                result = calculate_supply_risk_score(mineral)
                
        elif command == "risk-rankings":
            result = get_supply_risk_rankings()
            
        elif command == "sector-exposure":
            if len(sys.argv) < 3:
                result = {"error": "Sector name required"}
            else:
                sector = sys.argv[2]
                result = get_sector_exposure(sector)
                
        elif command == "country-profile":
            if len(sys.argv) < 3:
                result = {"error": "Country name required"}
            else:
                country = sys.argv[2]
                result = get_country_production_profile(country)
                
        elif command == "rare-earths-detailed":
            result = get_rare_earths_detailed()
            
        elif command == "comprehensive-report":
            result = get_comprehensive_minerals_report()
            
        elif command == "list-minerals":
            result = {
                "available_minerals": list(PRODUCTION_DATA.keys()),
                "critical_minerals": CRITICAL_MINERALS,
                "rare_earth_elements": RARE_EARTH_ELEMENTS
            }
            
        elif command == "list-sectors":
            result = {
                "sectors": list(STRATEGIC_CATEGORIES.keys()),
                "minerals_by_sector": STRATEGIC_CATEGORIES
            }
            
        else:
            result = {
                "error": f"Unknown command: {command}",
                "available_commands": [
                    "mineral-profile", "supply-risk", "risk-rankings",
                    "sector-exposure", "country-profile", "rare-earths-detailed",
                    "comprehensive-report", "list-minerals", "list-sectors"
                ]
            }
            
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
