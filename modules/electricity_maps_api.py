"""
Electricity Maps API — Carbon Intensity of Electricity Grids

Real-time and historical data on carbon intensity (gCO2eq/kWh) of electricity production
across global grids. Includes power generation breakdown by source and forecasts.

Source: https://api.electricitymaps.com
Docs: https://static.electricitymaps.com/api/docs/index.html

Use cases:
- ESG & Climate risk assessment for energy-dependent investments
- Carbon footprint analysis of data centers and operations
- Energy transition tracking
- Grid decarbonization monitoring
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json
import os

CACHE_DIR = Path(__file__).parent.parent / "cache" / "electricity_maps"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.electricitymaps.com/v3"

# Optional token from environment for higher rate limits
API_TOKEN = os.getenv("ELECTRICITY_MAPS_TOKEN")


def get_carbon_intensity_latest(zone: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get latest carbon intensity for a specific zone.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR', 'US-TX')
        use_cache: Use cached data if less than 1 hour old
        
    Returns:
        Dict with carbon intensity data or None on error
    """
    cache_path = CACHE_DIR / f"carbon_intensity_latest_{zone}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/carbon-intensity/latest"
    params = {"zone": zone}
    headers = {}
    
    if API_TOKEN:
        headers["auth-token"] = API_TOKEN
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching carbon intensity for {zone}: {e}")
        # Try to return cached data even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_power_breakdown_latest(zone: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get latest power generation breakdown by source for a specific zone.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR')
        use_cache: Use cached data if less than 1 hour old
        
    Returns:
        Dict with power breakdown data or None on error
    """
    cache_path = CACHE_DIR / f"power_breakdown_latest_{zone}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/power-breakdown/latest"
    params = {"zone": zone}
    headers = {}
    
    if API_TOKEN:
        headers["auth-token"] = API_TOKEN
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching power breakdown for {zone}: {e}")
        # Try to return cached data even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_zones(use_cache: bool = True) -> Optional[Dict]:
    """
    Get list of available zones.
    
    Args:
        use_cache: Use cached data if less than 24 hours old
        
    Returns:
        Dict with zones data or None on error
    """
    cache_path = CACHE_DIR / "zones.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/zones"
    headers = {}
    
    if API_TOKEN:
        headers["auth-token"] = API_TOKEN
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching zones: {e}")
        # Try to return cached data even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_carbon_intensity_history(zone: str, start: str, end: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get historical carbon intensity data for a zone.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR')
        start: Start datetime in ISO format (e.g., '2024-01-01T00:00:00Z')
        end: End datetime in ISO format (e.g., '2024-01-31T23:59:59Z')
        use_cache: Use cached data if less than 24 hours old
        
    Returns:
        Dict with historical carbon intensity data or None on error
    """
    cache_key = f"{zone}_{start}_{end}".replace(":", "-").replace("/", "-")
    cache_path = CACHE_DIR / f"carbon_intensity_history_{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/carbon-intensity/history"
    params = {"zone": zone, "start": start, "end": end}
    headers = {}
    
    if API_TOKEN:
        headers["auth-token"] = API_TOKEN
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching carbon intensity history for {zone}: {e}")
        # Try to return cached data even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_carbon_intensity_forecast(zone: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get carbon intensity forecast for a zone.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR')
        use_cache: Use cached data if less than 1 hour old
        
    Returns:
        Dict with carbon intensity forecast or None on error
    """
    cache_path = CACHE_DIR / f"carbon_intensity_forecast_{zone}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/carbon-intensity/forecast"
    params = {"zone": zone}
    headers = {}
    
    if API_TOKEN:
        headers["auth-token"] = API_TOKEN
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching carbon intensity forecast for {zone}: {e}")
        # Try to return cached data even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_carbon_intensity_summary(zone: str) -> Optional[pd.DataFrame]:
    """
    Get carbon intensity summary as DataFrame.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR')
        
    Returns:
        DataFrame with carbon intensity metrics or empty DataFrame on error
    """
    data = get_carbon_intensity_latest(zone)
    if not data:
        return pd.DataFrame()
    
    records = []
    
    # Extract carbon intensity value
    if "carbonIntensity" in data:
        records.append({
            "zone": zone,
            "datetime": data.get("datetime", ""),
            "carbon_intensity_gCO2eq_per_kWh": data["carbonIntensity"],
            "fossil_fuel_percentage": data.get("fossilFuelPercentage"),
            "renewable_percentage": data.get("renewablePercentage"),
        })
    
    return pd.DataFrame(records)


def get_power_breakdown_summary(zone: str) -> Optional[pd.DataFrame]:
    """
    Get power generation breakdown as DataFrame.
    
    Args:
        zone: Zone identifier (e.g., 'US-CA', 'DE', 'FR')
        
    Returns:
        DataFrame with power breakdown by source or empty DataFrame on error
    """
    data = get_power_breakdown_latest(zone)
    if not data or "powerConsumptionBreakdown" not in data:
        return pd.DataFrame()
    
    breakdown = data["powerConsumptionBreakdown"]
    records = []
    
    for source, value in breakdown.items():
        if value is not None:
            records.append({
                "zone": zone,
                "datetime": data.get("datetime", ""),
                "source": source,
                "power_MW": value,
            })
    
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("power_MW", ascending=False)
    
    return df


if __name__ == "__main__":
    # Test the module
    print("Testing Electricity Maps API module...")
    
    # Test carbon intensity
    print("\n1. Testing carbon intensity for Germany (DE):")
    ci_data = get_carbon_intensity_latest("DE", use_cache=False)
    if ci_data:
        print(f"   ✓ Carbon intensity: {ci_data.get('carbonIntensity')} gCO2eq/kWh")
        print(f"   ✓ Fossil fuel: {ci_data.get('fossilFuelPercentage')}%")
    
    # Test power breakdown
    print("\n2. Testing power breakdown for California (US-CA):")
    pb_data = get_power_breakdown_latest("US-CA", use_cache=False)
    if pb_data:
        breakdown = pb_data.get("powerConsumptionBreakdown", {})
        print(f"   ✓ Sources available: {len(breakdown)}")
        for source, value in list(breakdown.items())[:3]:
            print(f"   - {source}: {value} MW")
    
    # Test DataFrame summaries
    print("\n3. Testing DataFrame summaries:")
    df = get_carbon_intensity_summary("DE")
    if not df.empty:
        print(f"   ✓ Carbon intensity DataFrame: {len(df)} rows")
    
    df = get_power_breakdown_summary("US-CA")
    if not df.empty:
        print(f"   ✓ Power breakdown DataFrame: {len(df)} rows")
    
    print("\n✓ Module test complete")
