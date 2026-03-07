#!/usr/bin/env python3
"""
Electricity Maps Carbon Intensity API Module — Phase NightBuilder

Real-time and historical carbon intensity data for electricity grids worldwide.
ESG/climate alternative data for energy-dependent trading strategies.

Key Metrics:
- Carbon intensity (gCO2eq/kWh) by grid zone
- Power generation breakdown by source
- Historical carbon intensity trends
- 200+ grid zones worldwide

Data Sources: 
- api.electricitymaps.com (Electricity Maps API)

Refresh: Real-time (5-minute updates)
Coverage: Global electricity grid zones

Author: NightBuilder (Quant Subagent)
Phase: NightBuilder-001
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# API Configuration
API_BASE_URL = "https://api.electricitymaps.com/v3"
API_KEY = os.environ.get('ELECTRICITY_MAPS_API_KEY', '')

# Request timeout in seconds
TIMEOUT = 10

# Common headers
def _get_headers() -> Dict[str, str]:
    """Get request headers with API key if available."""
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'QuantClaw-Data/1.0'
    }
    if API_KEY:
        headers['auth-token'] = API_KEY
    return headers


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make API request with error handling.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        API response as dict
        
    Raises:
        Exception on API errors
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(
            url,
            headers=_get_headers(),
            params=params or {},
            timeout=TIMEOUT
        )
        
        # Handle rate limits
        if response.status_code == 429:
            return {
                'error': 'Rate limit exceeded',
                'status_code': 429,
                'message': 'API rate limit reached. Try again later or add ELECTRICITY_MAPS_API_KEY env var.'
            }
        
        # Handle unauthorized
        if response.status_code == 401:
            return {
                'error': 'Unauthorized',
                'status_code': 401,
                'message': 'API key required. Set ELECTRICITY_MAPS_API_KEY environment variable.'
            }
        
        # Handle not found
        if response.status_code == 404:
            return {
                'error': 'Not found',
                'status_code': 404,
                'message': f'Endpoint not found: {endpoint}'
            }
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        return {
            'error': 'Timeout',
            'message': f'Request timed out after {TIMEOUT} seconds'
        }
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'message': str(e)
        }
    except json.JSONDecodeError:
        return {
            'error': 'Invalid JSON',
            'message': 'API returned invalid JSON response'
        }


def get_carbon_intensity(zone: str = 'US-CAL-CISO') -> Dict:
    """
    Get latest carbon intensity for a grid zone.
    
    Carbon intensity measures grams of CO2 equivalent emitted per kilowatt-hour
    of electricity consumed. Lower values indicate cleaner electricity.
    
    Args:
        zone: Grid zone code (e.g., 'US-CAL-CISO', 'FR', 'DE', 'GB')
        
    Returns:
        Dict with:
            - zone: Grid zone code
            - carbonIntensity: gCO2eq/kWh
            - datetime: ISO timestamp
            - updatedAt: Last update timestamp
            - emissionFactorType: Calculation methodology
            
    Example:
        >>> data = get_carbon_intensity('US-CAL-CISO')
        >>> print(f"Carbon intensity: {data.get('carbonIntensity')} gCO2eq/kWh")
    """
    params = {'zone': zone}
    result = _make_request('carbon-intensity/latest', params)
    
    # Add zone to response for clarity
    if 'error' not in result:
        result['zone'] = zone
    
    return result


def get_power_breakdown(zone: str = 'US-CAL-CISO') -> Dict:
    """
    Get current power generation breakdown by source.
    
    Shows the mix of energy sources (solar, wind, coal, gas, nuclear, etc.)
    currently powering the grid zone.
    
    Args:
        zone: Grid zone code (e.g., 'US-CAL-CISO', 'FR', 'DE', 'GB')
        
    Returns:
        Dict with:
            - zone: Grid zone code
            - datetime: ISO timestamp
            - powerConsumptionBreakdown: Power consumption by source (MW)
            - powerProductionBreakdown: Power production by source (MW)
            - powerImportBreakdown: Imports by source (MW)
            - powerExportBreakdown: Exports by source (MW)
            - fossilFreePercentage: % renewable + nuclear
            - renewablePercentage: % renewable only
            
    Example:
        >>> data = get_power_breakdown('US-CAL-CISO')
        >>> renewable_pct = data.get('renewablePercentage', 0)
        >>> print(f"Renewable: {renewable_pct:.1f}%")
    """
    params = {'zone': zone}
    result = _make_request('power-breakdown/latest', params)
    
    # Add zone to response for clarity
    if 'error' not in result:
        result['zone'] = zone
    
    return result


def get_zones() -> List[str]:
    """
    Get list of available grid zones.
    
    Returns list of zone codes that can be queried for carbon intensity
    and power breakdown data.
    
    Returns:
        List of zone code strings
        
    Example:
        >>> zones = get_zones()
        >>> print(f"Available zones: {len(zones)}")
        >>> print(zones[:5])  # First 5 zones
    """
    result = _make_request('zones')
    
    # API returns dict of zone code -> zone info
    # Extract just the zone codes
    if 'error' in result:
        return []
    
    # If result is a dict, return the keys as zone codes
    if isinstance(result, dict):
        return list(result.keys())
    
    # Fallback: return empty list
    return []


def get_carbon_intensity_history(
    zone: str = 'US-CAL-CISO',
    start: Optional[Union[str, datetime]] = None,
    end: Optional[Union[str, datetime]] = None
) -> List[Dict]:
    """
    Get historical carbon intensity data for a zone.
    
    Retrieves time-series carbon intensity data within the specified date range.
    Useful for analyzing trends, correlations with energy prices, and ESG metrics.
    
    Args:
        zone: Grid zone code (e.g., 'US-CAL-CISO', 'FR', 'DE', 'GB')
        start: Start datetime (ISO string or datetime object). Default: 24 hours ago
        end: End datetime (ISO string or datetime object). Default: now
        
    Returns:
        List of dicts, each containing:
            - zone: Grid zone code
            - carbonIntensity: gCO2eq/kWh
            - datetime: ISO timestamp
            - updatedAt: Last update timestamp
            
    Example:
        >>> # Last 24 hours
        >>> history = get_carbon_intensity_history('US-CAL-CISO')
        >>> 
        >>> # Specific date range
        >>> history = get_carbon_intensity_history(
        ...     'FR',
        ...     start='2026-03-01T00:00:00Z',
        ...     end='2026-03-07T00:00:00Z'
        ... )
    """
    # Default to last 24 hours if not specified
    if end is None:
        end = datetime.utcnow()
    elif isinstance(end, str):
        end = datetime.fromisoformat(end.replace('Z', '+00:00'))
    
    if start is None:
        start = end - timedelta(hours=24)
    elif isinstance(start, str):
        start = datetime.fromisoformat(start.replace('Z', '+00:00'))
    
    # Format as ISO strings
    params = {
        'zone': zone,
        'start': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end': end.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    result = _make_request('carbon-intensity/history', params)
    
    # API returns dict with 'history' key containing list of data points
    if 'error' in result:
        return [result]  # Return error as single-item list for consistency
    
    # Extract history array if present
    if isinstance(result, dict) and 'history' in result:
        history = result['history']
        # Add zone to each data point
        for item in history:
            item['zone'] = zone
        return history
    
    # If result is already a list, return it
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                item['zone'] = zone
        return result
    
    # Fallback: return empty list
    return []


def get_zone_info(zone: str = 'US-CAL-CISO') -> Dict:
    """
    Get detailed information about a grid zone.
    
    Args:
        zone: Grid zone code
        
    Returns:
        Dict with zone metadata (name, country, coordinates, etc.)
    """
    zones = _make_request('zones')
    
    if 'error' in zones:
        return zones
    
    if isinstance(zones, dict) and zone in zones:
        info = zones[zone]
        info['zone'] = zone
        return info
    
    return {
        'error': 'Zone not found',
        'message': f'Zone {zone} not found in available zones',
        'zone': zone
    }


# Module metadata
__version__ = '1.0.0'
__author__ = 'NightBuilder'
__api_version__ = 'v3'
__functions__ = [
    'get_carbon_intensity',
    'get_power_breakdown',
    'get_zones',
    'get_carbon_intensity_history',
    'get_zone_info'
]


if __name__ == "__main__":
    # Self-test
    print(json.dumps({
        'module': 'electricity_maps_carbon_intensity_api',
        'version': __version__,
        'functions': __functions__,
        'api_key_set': bool(API_KEY),
        'status': 'ready'
    }, indent=2))
    
    # Test get_zones if API key is available
    if API_KEY:
        print("\nTesting get_zones()...")
        zones = get_zones()
        if zones:
            print(f"✓ Found {len(zones)} zones")
            print(f"  Sample zones: {zones[:5]}")
        else:
            print("✗ No zones returned (may need API key)")
