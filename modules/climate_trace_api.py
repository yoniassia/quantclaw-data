#!/usr/bin/env python3
"""
Climate TRACE API — Greenhouse Gas Emissions Data Module

Climate TRACE provides granular, asset-level greenhouse gas emissions data from various 
sectors like power, aviation, shipping, and more using satellite imagery and AI. 
Enables tracking of global emissions hotspots and trends for climate risk assessment.

Key Features:
- Emissions by sector (CO2, CH4, N2O)
- Asset-level data (power plants, ships, facilities)
- Historical trends (2015-2025)
- Geographic breakdowns by country/region
- Multiple greenhouse gases

Source: https://climatetrace.org/api
Category: ESG & Climate
Free tier: Up to 1,000 requests/month, no cost for non-commercial use
Update frequency: Quarterly
Author: QuantClaw Data NightBuilder
Phase: Climate Module
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

# Climate TRACE API Configuration
CLIMATE_TRACE_BASE_URL = "https://api.climatetrace.org/v1"
CLIMATE_TRACE_API_KEY = os.environ.get("CLIMATE_TRACE_API_KEY", "")

# Sector definitions
SECTORS = [
    "power",
    "oil-and-gas",
    "coal-mining",
    "steel",
    "cement",
    "aluminum",
    "chemicals",
    "pulp-and-paper",
    "cropland-fires",
    "forestland-fires",
    "forest-land-clearing",
    "cropland",
    "rice-cultivation",
    "enteric-fermentation",
    "manure-management",
    "other-agriculture",
    "domestic-aviation",
    "international-aviation",
    "domestic-shipping",
    "international-shipping",
    "rail",
    "on-road",
    "waste",
    "other-manufacturing"
]

# Gas types
GAS_TYPES = ["co2", "ch4", "n2o", "co2e_100yr", "co2e_20yr"]


def _make_request(endpoint: str, params: Optional[Dict] = None, timeout: int = 15) -> Dict:
    """
    Internal helper for making API requests
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        timeout: Request timeout in seconds
    
    Returns:
        Dict with response data or error
    """
    try:
        url = f"{CLIMATE_TRACE_BASE_URL}/{endpoint}"
        headers = {}
        
        if CLIMATE_TRACE_API_KEY:
            headers["Authorization"] = f"Bearer {CLIMATE_TRACE_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        return {
            "success": True,
            "data": response.json(),
            "status_code": response.status_code
        }
    
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {str(e)}",
            "status_code": e.response.status_code if hasattr(e, 'response') else None
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout - API may be slow or unavailable"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_emissions_by_sector(
    sector: str,
    year: Optional[int] = None,
    country: Optional[str] = None,
    gas: str = "co2e_100yr"
) -> Dict:
    """
    Get emissions data for a specific sector
    
    Args:
        sector: Sector name (e.g., "power", "transportation", "oil-and-gas")
        year: Year for data (default: latest available)
        country: ISO 3-letter country code (e.g., "USA", "CHN")
        gas: Gas type (co2, ch4, n2o, co2e_100yr, co2e_20yr)
    
    Returns:
        Dict with emissions data, totals, and trends
    """
    if sector not in SECTORS and sector != "all":
        return {
            "success": False,
            "error": f"Invalid sector. Valid sectors: {', '.join(SECTORS[:10])}..."
        }
    
    params = {
        "sector": sector,
        "gas": gas
    }
    
    if year:
        params["year"] = year
    if country:
        params["country"] = country
    
    result = _make_request("emissions", params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    # Parse and structure response
    emissions_data = {
        "sector": sector,
        "gas": gas,
        "year": year or "latest",
        "country": country or "global",
        "total_emissions": data.get("total_emissions", 0),
        "unit": data.get("unit", "tonnes"),
        "timestamp": datetime.now().isoformat()
    }
    
    # Add breakdown if available
    if "breakdown" in data:
        emissions_data["breakdown"] = data["breakdown"]
    
    if "subsectors" in data:
        emissions_data["subsectors"] = data["subsectors"]
    
    return {
        "success": True,
        **emissions_data,
        "source": "Climate TRACE API"
    }


def get_sector_trends(
    sector: str,
    start_year: int = 2015,
    end_year: Optional[int] = None,
    gas: str = "co2e_100yr"
) -> Dict:
    """
    Get historical emissions trends for a sector
    
    Args:
        sector: Sector name
        start_year: Starting year (default 2015)
        end_year: Ending year (default current year)
        gas: Gas type
    
    Returns:
        Dict with time series data and trend analysis
    """
    if not end_year:
        end_year = datetime.now().year
    
    years = range(start_year, end_year + 1)
    time_series = []
    
    for year in years:
        result = get_emissions_by_sector(sector=sector, year=year, gas=gas)
        
        if result["success"]:
            time_series.append({
                "year": year,
                "emissions": result.get("total_emissions", 0)
            })
    
    if not time_series:
        return {
            "success": False,
            "error": "No data retrieved for time series"
        }
    
    # Calculate trends
    first_year_emissions = time_series[0]["emissions"]
    last_year_emissions = time_series[-1]["emissions"]
    
    total_change = last_year_emissions - first_year_emissions
    pct_change = (total_change / first_year_emissions * 100) if first_year_emissions > 0 else 0
    
    return {
        "success": True,
        "sector": sector,
        "gas": gas,
        "period": f"{start_year}-{end_year}",
        "time_series": time_series,
        "analysis": {
            "first_year": {"year": start_year, "emissions": first_year_emissions},
            "last_year": {"year": end_year, "emissions": last_year_emissions},
            "total_change": total_change,
            "percent_change": round(pct_change, 2),
            "trend": "increasing" if total_change > 0 else "decreasing"
        },
        "timestamp": datetime.now().isoformat()
    }


def get_country_emissions(
    country: str,
    year: Optional[int] = None,
    sectors: Optional[List[str]] = None
) -> Dict:
    """
    Get emissions breakdown for a specific country across sectors
    
    Args:
        country: ISO 3-letter country code (USA, CHN, IND, etc.)
        year: Year for data (default: latest)
        sectors: List of sectors to include (default: all major sectors)
    
    Returns:
        Dict with country emissions by sector
    """
    if not sectors:
        # Focus on major emitting sectors
        sectors = ["power", "oil-and-gas", "steel", "cement", "on-road", 
                   "domestic-aviation", "domestic-shipping", "agriculture"]
    
    country_data = {
        "country": country,
        "year": year or "latest",
        "sectors": {}
    }
    
    total_emissions = 0
    
    for sector in sectors:
        result = get_emissions_by_sector(sector=sector, year=year, country=country)
        
        if result["success"]:
            emissions = result.get("total_emissions", 0)
            country_data["sectors"][sector] = {
                "emissions": emissions,
                "unit": result.get("unit", "tonnes")
            }
            total_emissions += emissions
    
    if not country_data["sectors"]:
        return {
            "success": False,
            "error": f"No data available for country {country}"
        }
    
    # Calculate sector shares
    for sector in country_data["sectors"]:
        emissions = country_data["sectors"][sector]["emissions"]
        share_pct = (emissions / total_emissions * 100) if total_emissions > 0 else 0
        country_data["sectors"][sector]["share_percent"] = round(share_pct, 2)
    
    # Rank sectors by emissions
    ranked_sectors = sorted(
        country_data["sectors"].items(),
        key=lambda x: x[1]["emissions"],
        reverse=True
    )
    
    return {
        "success": True,
        **country_data,
        "total_emissions": total_emissions,
        "top_sectors": [{"sector": s[0], **s[1]} for s in ranked_sectors[:5]],
        "timestamp": datetime.now().isoformat()
    }


def get_asset_emissions(
    asset_type: str,
    country: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get asset-level emissions data (power plants, ships, facilities)
    
    Args:
        asset_type: Type of asset (power-plant, ship, facility)
        country: Filter by country (optional)
        limit: Maximum number of assets to return
    
    Returns:
        Dict with asset-level emissions data
    """
    params = {
        "asset_type": asset_type,
        "limit": limit
    }
    
    if country:
        params["country"] = country
    
    result = _make_request("assets", params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    assets = data.get("assets", [])
    
    # Calculate summary statistics
    if assets:
        total_emissions = sum(a.get("emissions", 0) for a in assets)
        avg_emissions = total_emissions / len(assets)
        
        # Find top emitters
        top_emitters = sorted(
            assets,
            key=lambda x: x.get("emissions", 0),
            reverse=True
        )[:10]
    else:
        total_emissions = 0
        avg_emissions = 0
        top_emitters = []
    
    return {
        "success": True,
        "asset_type": asset_type,
        "country": country or "all",
        "asset_count": len(assets),
        "total_emissions": total_emissions,
        "average_emissions": avg_emissions,
        "top_emitters": top_emitters,
        "all_assets": assets if len(assets) <= 50 else assets[:50],
        "timestamp": datetime.now().isoformat()
    }


def get_global_emissions_summary(year: Optional[int] = None) -> Dict:
    """
    Get global emissions summary across all major sectors
    
    Args:
        year: Year for data (default: latest)
    
    Returns:
        Dict with global emissions breakdown and top emitting sectors
    """
    major_sectors = [
        "power", "oil-and-gas", "steel", "cement", "on-road",
        "international-aviation", "international-shipping",
        "forestland-fires", "agriculture"
    ]
    
    global_data = {
        "year": year or "latest",
        "sectors": {}
    }
    
    total_emissions = 0
    
    for sector in major_sectors:
        result = get_emissions_by_sector(sector=sector, year=year)
        
        if result["success"]:
            emissions = result.get("total_emissions", 0)
            global_data["sectors"][sector] = {
                "emissions": emissions,
                "gas": result.get("gas", "co2e_100yr")
            }
            total_emissions += emissions
    
    # Calculate shares
    for sector in global_data["sectors"]:
        emissions = global_data["sectors"][sector]["emissions"]
        share_pct = (emissions / total_emissions * 100) if total_emissions > 0 else 0
        global_data["sectors"][sector]["share_percent"] = round(share_pct, 2)
    
    # Rank sectors
    ranked = sorted(
        global_data["sectors"].items(),
        key=lambda x: x[1]["emissions"],
        reverse=True
    )
    
    return {
        "success": True,
        **global_data,
        "total_emissions": total_emissions,
        "unit": "tonnes CO2e",
        "top_sectors": [{"sector": s[0], **s[1]} for s in ranked[:5]],
        "sector_count": len(global_data["sectors"]),
        "timestamp": datetime.now().isoformat(),
        "source": "Climate TRACE API"
    }


def compare_countries(
    countries: List[str],
    year: Optional[int] = None,
    sector: str = "all"
) -> Dict:
    """
    Compare emissions across multiple countries
    
    Args:
        countries: List of ISO 3-letter country codes
        year: Year for comparison (default: latest)
        sector: Sector to compare (default: all sectors)
    
    Returns:
        Dict with country comparison data
    """
    comparison = {
        "year": year or "latest",
        "sector": sector,
        "countries": {}
    }
    
    for country in countries:
        if sector == "all":
            result = get_country_emissions(country=country, year=year)
        else:
            result = get_emissions_by_sector(sector=sector, year=year, country=country)
        
        if result["success"]:
            emissions = result.get("total_emissions", 0)
            comparison["countries"][country] = {
                "emissions": emissions,
                "unit": result.get("unit", "tonnes")
            }
    
    if not comparison["countries"]:
        return {
            "success": False,
            "error": "No data retrieved for any country"
        }
    
    # Rank countries by emissions
    ranked = sorted(
        comparison["countries"].items(),
        key=lambda x: x[1]["emissions"],
        reverse=True
    )
    
    total_emissions = sum(c[1]["emissions"] for c in ranked)
    
    # Add rankings and shares
    for i, (country, data) in enumerate(ranked):
        comparison["countries"][country]["rank"] = i + 1
        share_pct = (data["emissions"] / total_emissions * 100) if total_emissions > 0 else 0
        comparison["countries"][country]["share_percent"] = round(share_pct, 2)
    
    return {
        "success": True,
        **comparison,
        "total_emissions": total_emissions,
        "ranked_countries": [{"country": c[0], **c[1]} for c in ranked],
        "timestamp": datetime.now().isoformat()
    }


def list_available_sectors() -> Dict:
    """
    List all available sectors in Climate TRACE
    
    Returns:
        Dict with all available sectors categorized
    """
    categories = {
        "Energy": ["power", "oil-and-gas", "coal-mining"],
        "Manufacturing": ["steel", "cement", "aluminum", "chemicals", "pulp-and-paper", "other-manufacturing"],
        "Agriculture": ["cropland-fires", "forestland-fires", "forest-land-clearing", 
                       "cropland", "rice-cultivation", "enteric-fermentation", 
                       "manure-management", "other-agriculture"],
        "Transportation": ["domestic-aviation", "international-aviation", "domestic-shipping", 
                          "international-shipping", "rail", "on-road"],
        "Waste": ["waste"]
    }
    
    return {
        "success": True,
        "total_sectors": len(SECTORS),
        "sectors": SECTORS,
        "categories": categories,
        "gas_types": GAS_TYPES,
        "module": "climate_trace_api"
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Climate TRACE API - Greenhouse Gas Emissions Data")
    print("=" * 70)
    
    # List available sectors
    sectors = list_available_sectors()
    print(f"\nTotal Sectors: {sectors['total_sectors']}")
    print("\nSector Categories:")
    for category, sector_list in sectors['categories'].items():
        print(f"  {category}: {len(sector_list)} sectors")
    
    print("\n" + json.dumps(sectors, indent=2))
