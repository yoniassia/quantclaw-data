"""
OpenEI API — Open Energy Information

Open Energy Information (OpenEI) offers datasets and APIs for energy market data, 
including utility rates, renewable energy resources, and EV charging infrastructure.
Data: https://openei.org/developers

Use cases:
- Utility rate comparisons
- EV charging station location
- Energy cost analysis by state
- Utility company research
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache" / "openei"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.openei.org"
# OpenEI is open data - using DEMO_KEY for public access
API_KEY = "DEMO_KEY"


def fetch_utility_rates(zipcode: str, use_cache: bool = True) -> List[Dict]:
    """
    Fetch utility rate structures for a given zipcode.
    
    Args:
        zipcode: 5-digit US zipcode
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        List of utility rate structures with pricing details
    """
    cache_path = CACHE_DIR / f"rates_{zipcode}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/utility_rates"
    params = {
        "version": "latest",
        "format": "json",
        "api_key": API_KEY,
        "address": zipcode,
        "detail": "full"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract items if present
        items = data.get("items", [])
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(items, f, indent=2)
        
        return items
    except Exception as e:
        print(f"Error fetching utility rates for {zipcode}: {e}")
        # Try to return cached data even if expired
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return []


def get_ev_stations(zipcode: str, radius_miles: int = 25, use_cache: bool = True) -> List[Dict]:
    """
    Get electric vehicle charging stations near a zipcode.
    
    Args:
        zipcode: 5-digit US zipcode
        radius_miles: Search radius in miles (default 25)
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        List of EV charging stations with location and connector details
        
    Note:
        Requires NREL API key. DEMO_KEY does not work for this endpoint.
        Get free key at: https://developer.nrel.gov/signup/
    """
    cache_path = CACHE_DIR / f"ev_{zipcode}_{radius_miles}mi.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Check if using DEMO_KEY
    if API_KEY == "DEMO_KEY":
        print("Warning: DEMO_KEY does not work for NREL EV stations API. Get free key at https://developer.nrel.gov/signup/")
        # Try to return cached data if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return []
    
    # Fetch from NREL Alternative Fuels Data Center (used by OpenEI)
    url = "https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json"
    params = {
        "api_key": API_KEY,
        "location": zipcode,
        "radius": radius_miles,
        "fuel_type": "ELEC",
        "limit": 200
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract fuel stations
        stations = data.get("fuel_stations", [])
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(stations, f, indent=2)
        
        return stations
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            print(f"Error: Invalid request to NREL API. Check API key and parameters.")
        else:
            print(f"Error fetching EV stations for {zipcode}: {e}")
        # Try to return cached data even if expired
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error fetching EV stations for {zipcode}: {e}")
        # Try to return cached data even if expired
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return []


def search_utility(utility_name: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Search for utility company information by name.
    
    Args:
        utility_name: Utility company name (e.g., "Con Edison", "PG&E")
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        Dictionary with utility company details
    """
    cache_path = CACHE_DIR / f"utility_{utility_name.replace(' ', '_').lower()}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/utility_companies"
    params = {
        "version": "latest",
        "format": "json",
        "api_key": API_KEY,
        "search": utility_name
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Get first result
        items = data.get("items", [])
        result = items[0] if items else {}
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    except Exception as e:
        print(f"Error searching utility '{utility_name}': {e}")
        # Try to return cached data even if expired
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_energy_costs_by_state(use_cache: bool = True) -> Dict[str, float]:
    """
    Get average electricity costs by US state.
    
    Args:
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        Dictionary mapping state codes to avg cost per kWh
    """
    cache_path = CACHE_DIR / "state_energy_costs.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # This would typically aggregate from utility rates across states
    # For now, using EIA-sourced data via OpenEI
    url = f"{BASE_URL}/utility_rates"
    params = {
        "version": "latest",
        "format": "json",
        "api_key": API_KEY,
        "detail": "minimal",
        "sector": "residential"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Aggregate by state (this is simplified - real impl would process all items)
        state_costs = {}
        items = data.get("items", [])
        
        for item in items:
            state = item.get("state")
            # Try to extract rate - structure varies by utility
            rate = None
            if "flatdemandstructure" in item:
                for tier in item.get("flatdemandstructure", []):
                    rate = tier.get("rate")
                    if rate:
                        break
            
            if state and rate:
                if state not in state_costs:
                    state_costs[state] = []
                state_costs[state].append(float(rate))
        
        # Average rates by state
        result = {state: sum(rates) / len(rates) 
                  for state, rates in state_costs.items() if rates}
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    except Exception as e:
        print(f"Error fetching state energy costs: {e}")
        # Try to return cached data even if expired
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return {}


if __name__ == "__main__":
    print(json.dumps({
        "module": "openei_api",
        "status": "implemented",
        "source": "https://openei.org/developers",
        "functions": [
            "fetch_utility_rates",
            "get_ev_stations",
            "search_utility",
            "get_energy_costs_by_state"
        ]
    }, indent=2))
