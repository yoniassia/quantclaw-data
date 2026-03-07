#!/usr/bin/env python3
"""
U.S. Census Bureau API — Demographic and Economic Data Module

The Census Bureau API offers demographic and economic data from surveys like 
the American Community Survey (ACS), including population estimates, age distributions, 
income levels, housing data, and business patterns.

Data Points:
- Population by state and county
- Median household income
- Housing units and values
- Business patterns (County Business Patterns)
- Economic indicators by geography

Updated: Annual (ACS 5-year estimates)
History: 2009-present for ACS 5-year
Source: https://www.census.gov/data/developers.html
Category: Labor & Demographics
Free tier: True (500 calls/day without key, unlimited with free key)
Author: QuantClaw Data NightBuilder
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime

# Base URL for Census API
BASE_URL = "https://api.census.gov/data"

# Common ACS variables
VARIABLES = {
    'population': 'B01003_001E',  # Total population
    'median_income': 'B19013_001E',  # Median household income
    'median_home_value': 'B25077_001E',  # Median home value
    'housing_units': 'B25001_001E',  # Total housing units
    'occupied_units': 'B25002_002E',  # Occupied housing units
    'vacant_units': 'B25002_003E',  # Vacant housing units
    'owner_occupied': 'B25003_002E',  # Owner-occupied units
    'renter_occupied': 'B25003_003E',  # Renter-occupied units
}

# Get API key from environment (optional)
API_KEY = os.environ.get('CENSUS_API_KEY', None)

USER_AGENT = 'QuantClaw-Data/1.0 (Financial Analysis Tool)'


def _make_request(url: str, params: Dict) -> Optional[List]:
    """
    Make request to Census API with error handling
    
    Args:
        url: Full API endpoint URL
        params: Query parameters
        
    Returns:
        List of data rows or None on error
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Add API key if available
        if API_KEY:
            params['key'] = API_KEY
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.RequestException as e:
        return None
    except Exception as e:
        return None


def _parse_census_response(data: List, variable_map: Dict) -> List[Dict]:
    """
    Parse Census API response into list of dicts
    
    Args:
        data: Raw API response (list of lists)
        variable_map: Mapping of variable codes to friendly names
        
    Returns:
        List of dicts with parsed data
    """
    if not data or len(data) < 2:
        return []
    
    headers = data[0]
    rows = data[1:]
    
    results = []
    for row in rows:
        record = {}
        for i, value in enumerate(row):
            if i < len(headers):
                header = headers[i]
                # Convert to friendly name if available
                friendly_name = variable_map.get(header, header)
                
                # Try to convert to numeric
                try:
                    if value is not None and value != 'null':
                        numeric_value = float(value)
                        record[friendly_name] = int(numeric_value) if numeric_value.is_integer() else numeric_value
                    else:
                        record[friendly_name] = None
                except (ValueError, TypeError):
                    record[friendly_name] = value
        
        results.append(record)
    
    return results


def get_population_by_state(year: int = 2022) -> List[Dict]:
    """
    Get population estimates for all U.S. states
    
    Args:
        year: Data year (default 2022, uses ACS 5-year estimates)
        
    Returns:
        List of dicts with state name, FIPS code, and population
        
    Example:
        >>> data = get_population_by_state(2022)
        >>> print(data[0])
        {'name': 'Alabama', 'state': '01', 'population': 5024279}
    """
    # Use ACS 5-year estimates (most reliable)
    url = f"{BASE_URL}/{year}/acs/acs5"
    
    params = {
        'get': f"NAME,{VARIABLES['population']}",
        'for': 'state:*'
    }
    
    data = _make_request(url, params)
    
    if not data:
        return [{
            "success": False,
            "error": "Failed to fetch population data",
            "note": "Check year availability or API key if rate limited"
        }]
    
    variable_map = {
        'NAME': 'name',
        VARIABLES['population']: 'population',
        'state': 'state_fips'
    }
    
    results = _parse_census_response(data, variable_map)
    
    # Sort by population descending
    results.sort(key=lambda x: x.get('population', 0) if x.get('population') else 0, reverse=True)
    
    return results


def get_median_income_by_state(year: int = 2022) -> List[Dict]:
    """
    Get median household income for all U.S. states
    
    Args:
        year: Data year (default 2022, uses ACS 5-year estimates)
        
    Returns:
        List of dicts with state name, FIPS code, and median household income
        
    Example:
        >>> data = get_median_income_by_state(2022)
        >>> print(data[0])
        {'name': 'Maryland', 'state_fips': '24', 'median_income': 97332}
    """
    url = f"{BASE_URL}/{year}/acs/acs5"
    
    params = {
        'get': f"NAME,{VARIABLES['median_income']}",
        'for': 'state:*'
    }
    
    data = _make_request(url, params)
    
    if not data:
        return [{
            "success": False,
            "error": "Failed to fetch income data",
            "note": "Check year availability or API key if rate limited"
        }]
    
    variable_map = {
        'NAME': 'name',
        VARIABLES['median_income']: 'median_income',
        'state': 'state_fips'
    }
    
    results = _parse_census_response(data, variable_map)
    
    # Sort by income descending
    results.sort(key=lambda x: x.get('median_income', 0) if x.get('median_income') else 0, reverse=True)
    
    return results


def get_housing_data(state_fips: Optional[str] = None, year: int = 2022) -> List[Dict]:
    """
    Get housing statistics (units, values, occupancy)
    
    Args:
        state_fips: Optional state FIPS code (e.g., '06' for California)
                   If None, returns data for all states
        year: Data year (default 2022, uses ACS 5-year estimates)
        
    Returns:
        List of dicts with housing statistics
        
    Example:
        >>> data = get_housing_data(state_fips='06')  # California
        >>> print(data[0])
        {'name': 'California', 'housing_units': 14372151, 'median_value': 659300}
    """
    url = f"{BASE_URL}/{year}/acs/acs5"
    
    # Get multiple housing variables
    variables = [
        'NAME',
        VARIABLES['housing_units'],
        VARIABLES['median_home_value'],
        VARIABLES['occupied_units'],
        VARIABLES['vacant_units'],
        VARIABLES['owner_occupied'],
        VARIABLES['renter_occupied']
    ]
    
    params = {
        'get': ','.join(variables),
        'for': f"state:{state_fips}" if state_fips else 'state:*'
    }
    
    data = _make_request(url, params)
    
    if not data:
        return [{
            "success": False,
            "error": "Failed to fetch housing data",
            "note": "Check parameters or API key if rate limited"
        }]
    
    variable_map = {
        'NAME': 'name',
        VARIABLES['housing_units']: 'housing_units',
        VARIABLES['median_home_value']: 'median_home_value',
        VARIABLES['occupied_units']: 'occupied_units',
        VARIABLES['vacant_units']: 'vacant_units',
        VARIABLES['owner_occupied']: 'owner_occupied',
        VARIABLES['renter_occupied']: 'renter_occupied',
        'state': 'state_fips'
    }
    
    results = _parse_census_response(data, variable_map)
    
    # Calculate derived metrics
    for record in results:
        if record.get('housing_units') and record.get('occupied_units'):
            occupancy_rate = (record['occupied_units'] / record['housing_units']) * 100
            record['occupancy_rate'] = round(occupancy_rate, 1)
        
        if record.get('occupied_units') and record.get('owner_occupied'):
            ownership_rate = (record['owner_occupied'] / record['occupied_units']) * 100
            record['ownership_rate'] = round(ownership_rate, 1)
    
    return results


def get_business_patterns(state_fips: Optional[str] = None, naics: Optional[str] = None, year: int = 2021) -> List[Dict]:
    """
    Get County Business Patterns data
    
    Args:
        state_fips: Optional state FIPS code
        naics: Optional NAICS industry code (e.g., '23' for construction)
        year: Data year (default 2021, CBP usually lags by 1-2 years)
        
    Returns:
        List of dicts with business establishment counts and employment
        
    Note:
        County Business Patterns (CBP) data is typically 1-2 years behind.
        2021 is the most recent available as of 2024.
        
    Example:
        >>> data = get_business_patterns(state_fips='06', naics='23')
        >>> print(data[0])  # Construction businesses in California
    """
    # CBP endpoint structure is different
    url = f"{BASE_URL}/{year}/cbp"
    
    params = {
        'get': 'NAME,ESTAB,EMP',  # Establishments and employees
        'for': f"state:{state_fips}" if state_fips else 'state:*'
    }
    
    if naics:
        params['NAICS2017'] = naics
    
    data = _make_request(url, params)
    
    if not data:
        return [{
            "success": False,
            "error": "Failed to fetch business patterns data",
            "note": "CBP data typically lags 1-2 years. Try year=2021 or 2020.",
            "attempted_year": year
        }]
    
    variable_map = {
        'NAME': 'name',
        'ESTAB': 'establishments',
        'EMP': 'employees',
        'state': 'state_fips',
        'NAICS2017': 'naics_code'
    }
    
    results = _parse_census_response(data, variable_map)
    
    return results


def get_economic_indicators(variables: Optional[List[str]] = None, geo: str = "us", year: int = 2022) -> Dict:
    """
    Get custom economic indicators from ACS
    
    Args:
        variables: List of ACS variable codes (e.g., ['B01003_001E', 'B19013_001E'])
                  If None, returns common economic indicators
        geo: Geography level ('us' for national, 'state:*' for all states)
        year: Data year (default 2022)
        
    Returns:
        Dict with requested variables and metadata
        
    Example:
        >>> data = get_economic_indicators(['B01003_001E', 'B19013_001E'], geo='us')
        >>> print(data)
        {'population': 331449281, 'median_income': 69021}
    """
    url = f"{BASE_URL}/{year}/acs/acs5"
    
    # Default to common indicators
    if not variables:
        variables = [
            VARIABLES['population'],
            VARIABLES['median_income'],
            VARIABLES['median_home_value']
        ]
    
    params = {
        'get': 'NAME,' + ','.join(variables),
        'for': geo if ':' in geo else f"{geo}:*"
    }
    
    data = _make_request(url, params)
    
    if not data:
        return {
            "success": False,
            "error": "Failed to fetch economic indicators",
            "requested_variables": variables,
            "geography": geo
        }
    
    # For national data, return single dict
    if geo == "us" and len(data) > 1:
        headers = data[0]
        values = data[1]
        
        result = {
            "success": True,
            "geography": "United States",
            "year": year,
            "timestamp": datetime.now().isoformat()
        }
        
        for i, header in enumerate(headers):
            if i < len(values):
                value = values[i]
                # Try to convert to number
                try:
                    if value is not None and value != 'null':
                        numeric_value = float(value)
                        result[header] = int(numeric_value) if numeric_value.is_integer() else numeric_value
                    else:
                        result[header] = None
                except (ValueError, TypeError):
                    result[header] = value
        
        return result
    
    # For state/county data, return list
    variable_map = {var: f"variable_{i}" for i, var in enumerate(variables)}
    variable_map['NAME'] = 'name'
    
    results = _parse_census_response(data, variable_map)
    
    return {
        "success": True,
        "geography": geo,
        "year": year,
        "data": results,
        "timestamp": datetime.now().isoformat()
    }


def get_state_fips_codes() -> Dict[str, str]:
    """
    Get mapping of state names to FIPS codes
    
    Returns:
        Dict mapping state names to 2-digit FIPS codes
    """
    return {
        'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05',
        'California': '06', 'Colorado': '08', 'Connecticut': '09', 'Delaware': '10',
        'Florida': '12', 'Georgia': '13', 'Hawaii': '15', 'Idaho': '16',
        'Illinois': '17', 'Indiana': '18', 'Iowa': '19', 'Kansas': '20',
        'Kentucky': '21', 'Louisiana': '22', 'Maine': '23', 'Maryland': '24',
        'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27', 'Mississippi': '28',
        'Missouri': '29', 'Montana': '30', 'Nebraska': '31', 'Nevada': '32',
        'New Hampshire': '33', 'New Jersey': '34', 'New Mexico': '35', 'New York': '36',
        'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39', 'Oklahoma': '40',
        'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45',
        'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49',
        'Vermont': '50', 'Virginia': '51', 'Washington': '53', 'West Virginia': '54',
        'Wisconsin': '55', 'Wyoming': '56', 'District of Columbia': '11',
        'Puerto Rico': '72'
    }


# Convenience aliases
get_population = get_population_by_state
get_income = get_median_income_by_state
get_housing = get_housing_data


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("U.S. Census Bureau API - Demographic & Economic Data Module")
    print("=" * 70)
    
    # Test population
    print("\n1. Population by State (Top 5):")
    pop_data = get_population_by_state(2022)
    for state in pop_data[:5]:
        if state.get('name'):
            print(f"   {state['name']}: {state.get('population', 'N/A'):,}")
    
    # Test income
    print("\n2. Median Income by State (Top 5):")
    income_data = get_median_income_by_state(2022)
    for state in income_data[:5]:
        if state.get('name'):
            print(f"   {state['name']}: ${state.get('median_income', 0):,}")
    
    # Test housing for California
    print("\n3. California Housing Data:")
    ca_housing = get_housing_data(state_fips='06', year=2022)
    if ca_housing and ca_housing[0].get('name'):
        print(json.dumps(ca_housing[0], indent=2))
    
    print("\n" + "=" * 70)
    print("Module test complete!")
