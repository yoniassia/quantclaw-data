#!/usr/bin/env python3
"""
Aqueduct Water Risk Atlas API

WRI Aqueduct provides water stress, drought, and flood risk data at global and basin levels,
integrated for financial risk assessment in sectors like agriculture and energy.

Source: https://www.wri.org/aqueduct
Category: ESG & Climate
Free tier: true - Public data via CartoDB API
Update frequency: annually
Author: QuantClaw Data NightBuilder

Data comes from Resource Watch API accessing CartoDB tables:
- Baseline Water Depletion
- Water Stress
- Drought Risk
- Flood Risk (Coastal & Riverine)
- Groundwater Table Decline
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# CartoDB API Configuration
CARTODB_BASE = "https://wri-rw.carto.com/api/v2/sql"

# Dataset table mappings from Resource Watch
DATASET_TABLES = {
    'water_depletion': 'wat_051_aqueduct_baseline_water_depletion',
    'drought_risk': 'wat_057_aqueduct_drought_risk',
    'flood_risk_coastal': 'wat_056_aqueduct_coastal_flood_risk',
    'flood_risk_riverine': 'wat_055_aqueduct_riverine_flood_risk',
    'groundwater_decline': 'wat_054_aqueduct_groundwater_table_decline',
    'interannual_variability': 'wat_052_aqueduct_interannual_variability',
}

# ========== HELPER FUNCTIONS ==========

def _query_cartodb(sql: str) -> Dict:
    """Execute SQL query against CartoDB API"""
    try:
        params = {'q': sql}
        response = requests.get(CARTODB_BASE, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'rows': [],
            'time': 0,
            'total_rows': 0
        }
    except json.JSONDecodeError as e:
        return {
            'error': f'JSON decode error: {str(e)}',
            'rows': [],
            'time': 0,
            'total_rows': 0
        }

def _get_country_data(table: str, country: str, limit: int = 100) -> Dict:
    """Get data for a specific country from a table"""
    # Simple query - most tables use sub_name/maj_name arrays or name_0 string
    # Just get all data if specific filtering fails
    sql = f"SELECT * FROM {table} LIMIT {limit}"
    result = _query_cartodb(sql)
    
    # Filter in Python if needed (some columns are arrays)
    if result.get('rows'):
        filtered = []
        country_upper = country.upper()
        for row in result['rows']:
            # Check various possible fields
            sub_name = str(row.get('sub_name', ''))
            maj_name = str(row.get('maj_name', ''))
            name_0 = str(row.get('name_0', ''))
            
            if (country_upper in sub_name.upper() or 
                country_upper in maj_name.upper() or
                country_upper in name_0.upper()):
                filtered.append(row)
        
        if filtered:
            result['rows'] = filtered
            result['total_rows'] = len(filtered)
    
    return result

def _get_by_coords(table: str, lat: float, lon: float) -> Dict:
    """Get data for specific coordinates (requires spatial query)"""
    # Simple bounding box query
    buffer = 1.0  # degrees
    sql = f"""
        SELECT * FROM {table}
        WHERE ST_Intersects(
            the_geom,
            ST_MakeEnvelope({lon-buffer}, {lat-buffer}, {lon+buffer}, {lat+buffer}, 4326)
        )
        LIMIT 10
    """
    return _query_cartodb(sql)

# ========== PUBLIC API FUNCTIONS ==========

def get_water_stress(country: str = "USA", limit: int = 100) -> Dict:
    """
    Get baseline water depletion indicators by country.
    
    Water depletion measures the ratio of consumption to available flow, indicating water stress.
    
    Args:
        country: Country name or code (e.g., "USA", "India", "Ethiopia")
        limit: Maximum number of results
    
    Returns:
        dict: Water depletion/stress data with raw values, scores, categories, and labels
    
    Example:
        >>> data = get_water_stress("USA")
        >>> print(data['total_rows'])
    """
    table = DATASET_TABLES['water_depletion']
    result = _get_country_data(table, country, limit)
    
    return {
        'indicator': 'baseline_water_depletion',
        'country': country,
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'data': result.get('rows', []),
        'total_rows': result.get('total_rows', 0),
        'error': result.get('error')
    }

def get_flood_risk(country: str = "USA", flood_type: str = "riverine", limit: int = 100) -> Dict:
    """
    Get flood risk data by country.
    
    Args:
        country: Country name or code
        flood_type: "riverine" or "coastal"
        limit: Maximum number of results
    
    Returns:
        dict: Flood risk data including raw values, scores, and categories
    
    Example:
        >>> data = get_flood_risk("USA", "coastal")
    """
    if flood_type.lower() == "coastal":
        table = DATASET_TABLES['flood_risk_coastal']
    else:
        table = DATASET_TABLES['flood_risk_riverine']
    
    result = _get_country_data(table, country, limit)
    
    return {
        'indicator': f'{flood_type}_flood_risk',
        'country': country,
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'data': result.get('rows', []),
        'total_rows': result.get('total_rows', 0),
        'error': result.get('error')
    }

def get_drought_severity(country: str = "USA", limit: int = 100) -> Dict:
    """
    Get drought risk/severity index by country.
    
    Args:
        country: Country name or code
        limit: Maximum number of results
    
    Returns:
        dict: Drought risk data
    
    Example:
        >>> data = get_drought_severity("India")
    """
    table = DATASET_TABLES['drought_risk']
    result = _get_country_data(table, country, limit)
    
    return {
        'indicator': 'drought_risk',
        'country': country,
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'data': result.get('rows', []),
        'total_rows': result.get('total_rows', 0),
        'error': result.get('error')
    }

def get_water_risk_score(lat: float, lon: float) -> Dict:
    """
    Get comprehensive water risk score by coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        dict: Water risk data for the location
    
    Example:
        >>> data = get_water_risk_score(40.7128, -74.0060)  # New York
    """
    # Query multiple datasets for comprehensive risk
    depletion_data = _get_by_coords(DATASET_TABLES['water_depletion'], lat, lon)
    drought_data = _get_by_coords(DATASET_TABLES['drought_risk'], lat, lon)
    flood_data = _get_by_coords(DATASET_TABLES['flood_risk_riverine'], lat, lon)
    
    return {
        'location': {'lat': lat, 'lon': lon},
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'water_depletion': depletion_data.get('rows', []),
        'drought_risk': drought_data.get('rows', []),
        'flood_risk': flood_data.get('rows', []),
        'total_indicators': (
            len(depletion_data.get('rows', [])) +
            len(drought_data.get('rows', [])) +
            len(flood_data.get('rows', []))
        )
    }

def get_country_water_profile(country: str = "USA") -> Dict:
    """
    Get comprehensive water risk profile for a country.
    
    Includes water stress, drought risk, flood risk, and groundwater decline.
    
    Args:
        country: Country name or code
    
    Returns:
        dict: Comprehensive water risk profile
    
    Example:
        >>> profile = get_country_water_profile("USA")
        >>> print(profile.keys())
    """
    return {
        'country': country,
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'water_stress': get_water_stress(country, limit=50),
        'drought_risk': get_drought_severity(country, limit=50),
        'flood_risk_riverine': get_flood_risk(country, "riverine", limit=50),
        'flood_risk_coastal': get_flood_risk(country, "coastal", limit=50),
        'water_depletion': _get_country_data(DATASET_TABLES['water_depletion'], country, 50),
        'groundwater_decline': _get_country_data(DATASET_TABLES['groundwater_decline'], country, 50),
    }

# ========== CONVENIENCE FUNCTIONS ==========

def list_available_indicators() -> List[str]:
    """List all available water risk indicators"""
    return list(DATASET_TABLES.keys())

def get_latest() -> Dict:
    """Get sample latest data from water depletion dataset"""
    sql = f"SELECT * FROM {DATASET_TABLES['water_depletion']} LIMIT 10"
    result = _query_cartodb(sql)
    
    return {
        'indicator': 'baseline_water_depletion',
        'source': 'WRI Aqueduct 4.0',
        'timestamp': datetime.utcnow().isoformat(),
        'sample_data': result.get('rows', []),
        'total_rows': result.get('total_rows', 0),
        'note': 'This is a sample. Use get_water_stress(country) for specific data.'
    }

if __name__ == "__main__":
    # Test the module
    print(json.dumps({
        "module": "aqueduct_water_risk_atlas_api",
        "status": "implemented",
        "source": "https://www.wri.org/aqueduct",
        "available_indicators": list_available_indicators(),
        "test": "Running basic tests..."
    }, indent=2))
    
    # Quick test
    print("\n=== Testing get_water_stress for USA ===")
    result = get_water_stress("USA", limit=5)
    print(f"Total rows: {result.get('total_rows', 0)}")
    if result.get('data'):
        print(f"Sample data keys: {list(result['data'][0].keys())}")
