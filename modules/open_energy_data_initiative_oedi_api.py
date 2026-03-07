#!/usr/bin/env python3
"""
Open Energy Data Initiative (OEDI) API Module

OEDI provides open datasets and APIs for energy-related data, including:
- Utility electricity rates and tariffs
- Solar and wind resource data
- Energy datasets search
- Retail electricity prices

Source: https://data.openei.org/ & https://api.openei.org/
Category: Commodities & Energy
Free tier: Requires free API key from openei.org
API Key: Set OPENEI_API_KEY environment variable
Update frequency: Daily for dynamic data, static for historical
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# OpenEI API Configuration
OPENEI_API_BASE = "https://api.openei.org"
OPENEI_API_KEY = os.environ.get("OPENEI_API_KEY", "")
NREL_API_BASE = "https://developer.nrel.gov/api"

# Default timeout for all requests
REQUEST_TIMEOUT = 15


def _make_request(url: str, params: Dict, require_key: bool = True) -> Dict:
    """
    Internal helper to make API requests with error handling
    
    Args:
        url: Full API endpoint URL
        params: Query parameters dict
        require_key: Whether API key is required for this endpoint
    
    Returns:
        Dict with success status and data or error
    """
    try:
        # Add API key if available and required
        if require_key:
            if not OPENEI_API_KEY:
                return {
                    "success": False,
                    "error": "API key required. Set OPENEI_API_KEY environment variable. Get free key at https://openei.org/services/api/signup/",
                    "endpoint": url
                }
            params["api_key"] = OPENEI_API_KEY
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error in response
        if isinstance(data, dict) and "error" in data:
            return {
                "success": False,
                "error": data["error"].get("message", "Unknown API error"),
                "code": data["error"].get("code", "UNKNOWN"),
                "endpoint": url
            }
        
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.Timeout:
        return {
            "success": False,
            "error": "Request timeout",
            "endpoint": url
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "endpoint": url
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON response",
            "endpoint": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "endpoint": url
        }


def get_utility_rates(address: Optional[str] = None, state: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Get electricity utility rates and tariffs
    
    Args:
        address: Address to search rates for (e.g., "Denver, CO")
        state: Two-letter state code (e.g., "CO")
        limit: Maximum number of results (default 10)
    
    Returns:
        Dict with utility rate schedules, prices, and tariff details
    
    Example:
        >>> rates = get_utility_rates(address="Denver, CO", limit=5)
        >>> rates = get_utility_rates(state="CA", limit=20)
    """
    url = f"{OPENEI_API_BASE}/utility_rates"
    params = {
        "version": 8,
        "format": "json",
        "limit": limit
    }
    
    if address:
        params["address"] = address
    if state:
        params["state"] = state
    
    result = _make_request(url, params, require_key=True)
    
    if not result["success"]:
        return result
    
    # Parse and structure the response
    data = result["data"]
    items = data.get("items", [])
    
    rates = []
    for item in items:
        rates.append({
            "utility": item.get("utility", "Unknown"),
            "name": item.get("name", ""),
            "rate_type": item.get("rate_type", ""),
            "sector": item.get("sector", ""),
            "description": item.get("description", ""),
            "fixed_charge": item.get("fixed_charge"),
            "energy_charge": item.get("energy_charge"),
            "demand_charge": item.get("demand_charge"),
            "uri": item.get("uri", ""),
            "source": item.get("source", "")
        })
    
    return {
        "success": True,
        "count": len(rates),
        "rates": rates,
        "metadata": {
            "version": data.get("version"),
            "address": address,
            "state": state,
            "limit": limit
        },
        "timestamp": result["timestamp"]
    }


def search_datasets(query: str = "solar", limit: int = 10) -> Dict:
    """
    Search OEDI energy datasets
    
    Args:
        query: Search query (e.g., "solar", "wind", "electricity")
        limit: Maximum number of results (default 10)
    
    Returns:
        Dict with matching datasets, descriptions, and URLs
    
    Example:
        >>> datasets = search_datasets(query="solar irradiance", limit=5)
        >>> datasets = search_datasets(query="wind resource", limit=20)
    """
    # OEDI uses CKAN-style API for dataset search
    # Note: This is a common pattern but may need API key
    url = f"{OPENEI_API_BASE}/search"
    params = {
        "q": query,
        "limit": limit,
        "format": "json"
    }
    
    result = _make_request(url, params, require_key=False)
    
    if not result["success"]:
        # Try alternative endpoint structure
        return {
            "success": False,
            "error": "Dataset search requires manual exploration at https://data.openei.org/",
            "query": query,
            "note": "Use get_solar_resource() or get_wind_resource() for resource data",
            "timestamp": datetime.now().isoformat()
        }
    
    data = result["data"]
    
    # Parse results (structure may vary)
    datasets = []
    if isinstance(data, dict):
        results = data.get("results", data.get("result", {}).get("results", []))
        for item in results[:limit]:
            datasets.append({
                "title": item.get("title", item.get("name", "")),
                "description": item.get("notes", item.get("description", "")),
                "url": item.get("url", ""),
                "tags": item.get("tags", []),
                "organization": item.get("organization", {}).get("title", ""),
                "modified": item.get("metadata_modified", "")
            })
    
    return {
        "success": True,
        "query": query,
        "count": len(datasets),
        "datasets": datasets,
        "timestamp": datetime.now().isoformat()
    }


def get_solar_resource(lat: float, lon: float) -> Dict:
    """
    Get solar irradiance resource data for a location
    
    Args:
        lat: Latitude (decimal degrees)
        lon: Longitude (decimal degrees)
    
    Returns:
        Dict with solar resource metrics (DNI, GHI, DHI)
    
    Example:
        >>> solar = get_solar_resource(lat=39.7392, lon=-104.9903)  # Denver
        >>> solar = get_solar_resource(lat=33.4484, lon=-112.0740)  # Phoenix
    """
    # NREL PVWatts/Solar Resource API
    url = f"{NREL_API_BASE}/solar/solar_resource/v1.json"
    params = {
        "lat": lat,
        "lon": lon
    }
    
    # Try with OPENEI key first, falls back to NREL if separate
    if OPENEI_API_KEY:
        params["api_key"] = OPENEI_API_KEY
    
    result = _make_request(url, params, require_key=True)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    outputs = data.get("outputs", {})
    
    # Parse solar resource data
    annual_avg = outputs.get("avg_dni", {})
    monthly = outputs.get("monthly", {})
    
    solar_data = {
        "location": {
            "latitude": lat,
            "longitude": lon,
            "elevation": outputs.get("elev", 0),
            "timezone": outputs.get("tz", 0),
            "city": outputs.get("city", ""),
            "state": outputs.get("state", ""),
            "county": outputs.get("county", "")
        },
        "annual_average": {
            "dni": annual_avg.get("annual", 0),  # Direct Normal Irradiance
            "ghi": outputs.get("avg_ghi", {}).get("annual", 0),  # Global Horizontal Irradiance
            "dhi": outputs.get("avg_dhi", {}).get("annual", 0),  # Diffuse Horizontal Irradiance
            "tilt": outputs.get("avg_lat_tilt", {}).get("annual", 0)  # Latitude tilt irradiance
        },
        "monthly_dni": monthly.get("dni", []),
        "monthly_ghi": monthly.get("ghi", []),
        "solar_class": _classify_solar_resource(annual_avg.get("annual", 0))
    }
    
    return {
        "success": True,
        "solar_resource": solar_data,
        "timestamp": result["timestamp"]
    }


def get_wind_resource(lat: float, lon: float) -> Dict:
    """
    Get wind resource data for a location
    
    Args:
        lat: Latitude (decimal degrees)
        lon: Longitude (decimal degrees)
    
    Returns:
        Dict with wind speed and power metrics
    
    Example:
        >>> wind = get_wind_resource(lat=41.8781, lon=-87.6298)  # Chicago
        >>> wind = get_wind_resource(lat=32.7767, lon=-96.7970)  # Dallas
    """
    # NREL Wind Toolkit API
    url = f"{NREL_API_BASE}/wind-toolkit/v2/wind/wtk-download.json"
    params = {
        "lat": lat,
        "lon": lon,
        "hubheight": 100,  # Standard 100m hub height
        "year": 2021  # Most recent available year
    }
    
    if OPENEI_API_KEY:
        params["api_key"] = OPENEI_API_KEY
    
    result = _make_request(url, params, require_key=True)
    
    if not result["success"]:
        # If detailed data unavailable, return estimated resource class
        return {
            "success": False,
            "error": result.get("error", "Wind resource data requires API key"),
            "note": "For detailed wind data, get free API key at https://developer.nrel.gov/signup/",
            "location": {"latitude": lat, "longitude": lon},
            "estimated_class": _estimate_wind_class(lat, lon),
            "timestamp": datetime.now().isoformat()
        }
    
    data = result["data"]
    
    # Parse wind resource data (structure varies by API version)
    wind_data = {
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "hub_height_m": 100,
        "annual_average_speed_ms": data.get("avg_windspeed", 0),
        "wind_power_class": data.get("wind_power_class", "Unknown"),
        "capacity_factor": data.get("capacity_factor", 0),
        "note": "Detailed hourly data available via NREL Wind Toolkit"
    }
    
    return {
        "success": True,
        "wind_resource": wind_data,
        "timestamp": datetime.now().isoformat()
    }


def get_electricity_prices(state: Optional[str] = None) -> Dict:
    """
    Get retail electricity prices by state or nationwide
    
    Args:
        state: Two-letter state code (e.g., "CA", "TX"). If None, returns all states.
    
    Returns:
        Dict with electricity prices by sector (residential, commercial, industrial)
    
    Example:
        >>> prices = get_electricity_prices(state="CA")
        >>> prices = get_electricity_prices()  # All states
    """
    # OpenEI Utility Rates can provide pricing data
    url = f"{OPENEI_API_BASE}/utility_rates"
    params = {
        "version": 8,
        "format": "json",
        "limit": 100 if not state else 50
    }
    
    if state:
        params["state"] = state.upper()
    
    result = _make_request(url, params, require_key=True)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    items = data.get("items", [])
    
    # Aggregate pricing by sector
    pricing = {
        "residential": [],
        "commercial": [],
        "industrial": []
    }
    
    for item in items:
        sector = item.get("sector", "").lower()
        if sector in pricing:
            price_info = {
                "utility": item.get("utility", ""),
                "state": item.get("state", ""),
                "energy_rate_cents_kwh": item.get("energy_charge", 0) * 100 if item.get("energy_charge") else None,
                "fixed_charge_month": item.get("fixed_charge"),
                "rate_name": item.get("name", "")
            }
            pricing[sector].append(price_info)
    
    # Calculate averages by sector
    averages = {}
    for sector, prices in pricing.items():
        valid_prices = [p["energy_rate_cents_kwh"] for p in prices if p["energy_rate_cents_kwh"]]
        if valid_prices:
            averages[sector] = {
                "avg_cents_kwh": round(sum(valid_prices) / len(valid_prices), 2),
                "min_cents_kwh": round(min(valid_prices), 2),
                "max_cents_kwh": round(max(valid_prices), 2),
                "sample_size": len(valid_prices)
            }
    
    return {
        "success": True,
        "state": state,
        "electricity_prices": pricing,
        "averages_by_sector": averages,
        "total_rates": len(items),
        "timestamp": datetime.now().isoformat()
    }


# ========== HELPER FUNCTIONS ==========

def _classify_solar_resource(dni_annual: float) -> str:
    """Classify solar resource quality based on DNI"""
    if dni_annual >= 7.0:
        return "Excellent (Class 1)"
    elif dni_annual >= 6.0:
        return "Very Good (Class 2)"
    elif dni_annual >= 5.0:
        return "Good (Class 3)"
    elif dni_annual >= 4.0:
        return "Fair (Class 4)"
    else:
        return "Marginal (Class 5+)"


def _estimate_wind_class(lat: float, lon: float) -> str:
    """Rough wind class estimation based on geography (very approximate)"""
    # This is a simplified heuristic - real data requires API access
    # High wind areas: Great Plains, coastal regions, mountain passes
    
    # Great Plains (roughly)
    if 35 <= lat <= 50 and -105 <= lon <= -95:
        return "Class 3-5 (Good to Excellent) - Great Plains region"
    # Coastal areas
    elif abs(lat) > 40 or abs(lon) > 100:
        return "Class 3-4 (Good) - Coastal influence possible"
    else:
        return "Class 2-3 (Moderate) - Requires site assessment"


def get_module_info() -> Dict:
    """
    Get information about this module and available functions
    
    Returns:
        Dict with module metadata and function list
    """
    return {
        "module": "open_energy_data_initiative_oedi_api",
        "version": "1.0.0",
        "source": "https://data.openei.org/ & https://api.openei.org/",
        "category": "Commodities & Energy",
        "requires_api_key": True,
        "api_key_env_var": "OPENEI_API_KEY",
        "api_key_signup": "https://openei.org/services/api/signup/",
        "functions": [
            {
                "name": "get_utility_rates",
                "description": "Get electricity utility rates and tariffs",
                "params": ["address", "state", "limit"]
            },
            {
                "name": "search_datasets",
                "description": "Search OEDI energy datasets",
                "params": ["query", "limit"]
            },
            {
                "name": "get_solar_resource",
                "description": "Get solar irradiance data for location",
                "params": ["lat", "lon"]
            },
            {
                "name": "get_wind_resource",
                "description": "Get wind resource data for location",
                "params": ["lat", "lon"]
            },
            {
                "name": "get_electricity_prices",
                "description": "Get retail electricity prices by state",
                "params": ["state"]
            }
        ],
        "api_key_configured": bool(OPENEI_API_KEY),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Open Energy Data Initiative (OEDI) API Module")
    print("=" * 70)
    
    info = get_module_info()
    print(f"\nModule: {info['module']}")
    print(f"Version: {info['version']}")
    print(f"API Key Configured: {info['api_key_configured']}")
    
    if not info['api_key_configured']:
        print(f"\n⚠️  API key not found. Set OPENEI_API_KEY environment variable.")
        print(f"   Get free key at: {info['api_key_signup']}")
    
    print(f"\nAvailable Functions ({len(info['functions'])}):")
    for func in info['functions']:
        print(f"  • {func['name']}({', '.join(func['params'])})")
        print(f"    {func['description']}")
    
    print("\n" + "=" * 70)
    print("\nExample Usage:")
    print("  from modules.open_energy_data_initiative_oedi_api import *")
    print("  rates = get_utility_rates(state='CA', limit=5)")
    print("  solar = get_solar_resource(lat=39.7392, lon=-104.9903)")
    print("  wind = get_wind_resource(lat=41.8781, lon=-87.6298)")
    print("  prices = get_electricity_prices(state='TX')")
    print("=" * 70)
    
    # Print full module info as JSON
    print("\nModule Info:")
    print(json.dumps(info, indent=2))
