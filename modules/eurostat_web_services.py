#!/usr/bin/env python3
"""
Eurostat Web Services Module

European Union statistical data via SDMX REST API
- Employment rates by country and age group
- Unemployment statistics
- GDP growth (quarterly and annual)
- Harmonized Index of Consumer Prices (HICP)
- Population demographics
- Trade balance and international trade

Data Source: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
Refresh: Quarterly
Coverage: EU27 countries + EFTA, 1990-present
Free tier: Yes, no authentication required

Author: QUANTCLAW DATA NightBuilder
Phase: EUROSTAT_001
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Union
from datetime import datetime

# Eurostat API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Eurostat Dataset Registry
EUROSTAT_DATASETS = {
    'lfsi_emp_a': {
        'name': 'Employment Rate (Annual)',
        'description': 'Employment rates by country (% of population 15-64)',
        'unit': 'percent'
    },
    'une_rt_a': {
        'name': 'Unemployment Rate (Annual)',
        'description': 'Unemployment rate by age group',
        'unit': 'percent'
    },
    'namq_10_gdp': {
        'name': 'GDP Growth (Quarterly)',
        'description': 'GDP and main components (volume growth rate)',
        'unit': 'percent'
    },
    'nama_10_gdp': {
        'name': 'GDP Growth (Annual)',
        'description': 'GDP and main components (annual growth)',
        'unit': 'percent'
    },
    'prc_hicp_aind': {
        'name': 'HICP Inflation (Annual)',
        'description': 'Harmonized Index of Consumer Prices (annual average)',
        'unit': 'index'
    },
    'demo_pjan': {
        'name': 'Population',
        'description': 'Population on 1 January by age and sex',
        'unit': 'number'
    },
    'ext_lt_intertrd': {
        'name': 'Trade Balance',
        'description': 'International trade in goods by partner',
        'unit': 'million EUR'
    }
}


def _fetch_eurostat_data(dataset: str, params: Dict[str, str]) -> Dict:
    """
    Internal function to fetch data from Eurostat SDMX API
    
    Args:
        dataset: Eurostat dataset code (e.g., 'lfsi_emp_a')
        params: Query parameters as dictionary
    
    Returns:
        Dictionary with parsed dimension/value structure
    
    Raises:
        urllib.error.URLError: If network request fails
        json.JSONDecodeError: If response is not valid JSON
    """
    # Build query string
    query_parts = [f"{k}={v}" for k, v in params.items()]
    query_string = '&'.join(query_parts)
    url = f"{EUROSTAT_BASE_URL}/{dataset}?{query_string}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        raise ValueError(f"Eurostat API error for dataset {dataset}: HTTP {e.code}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to connect to Eurostat API: {e.reason}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from Eurostat API: {e}")


def _parse_eurostat_response(data: Dict) -> Dict[str, float]:
    """
    Parse Eurostat SDMX-JSON response into simple key-value pairs
    
    Args:
        data: Raw Eurostat API response
    
    Returns:
        Dictionary with time period as key and value as float
    """
    result = {}
    
    if 'value' not in data or 'dimension' not in data:
        return result
    
    values = data['value']
    dimensions = data['dimension']
    
    # Extract time dimension
    time_dim = dimensions.get('time', {}).get('category', {}).get('index', {})
    
    # Map values to time periods
    for idx_str, value in values.items():
        idx = int(idx_str)
        # Find corresponding time period
        for time_key, time_idx in time_dim.items():
            if time_idx == idx % len(time_dim):
                result[time_key] = float(value)
                break
    
    return result


def get_employment_rate(country: str = 'EU27_2020', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get employment rate (% of population aged 15-64)
    
    Args:
        country: Country code (e.g., 'DE', 'FR', 'EU27_2020')
        year: Specific year (e.g., 2023). If None, returns all available years
    
    Returns:
        Dictionary with year as key and employment rate as value
        
    Example:
        >>> data = get_employment_rate('EU27_2020', 2023)
        >>> data['2023']
        75.3
    """
    params = {
        'geo': country,
        'sex': 'T',  # Total (both sexes)
        'age': 'Y15-64',  # Working age population
        'unit': 'PC_POP'  # Percentage of population
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data('lfsi_emp_a', params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            return {str(year): parsed.get(str(year), 0.0)}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_unemployment_rate(country: str = 'DE', age_group: str = 'Y15-74', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get unemployment rate by age group
    
    Args:
        country: Country code (e.g., 'DE', 'FR', 'EU27_2020')
        age_group: Age group code (e.g., 'Y15-74', 'Y15-24', 'Y25-74')
        year: Specific year. If None, returns all available years
    
    Returns:
        Dictionary with year as key and unemployment rate as value
        
    Example:
        >>> data = get_unemployment_rate('DE', 'Y15-74', 2023)
        >>> data['2023']
        3.1
    """
    params = {
        'geo': country,
        'sex': 'T',
        'age': age_group,
        'unit': 'PC_ACT'  # Percentage of active population
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data('une_rt_a', params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            return {str(year): parsed.get(str(year), 0.0)}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_gdp_growth(country: str = 'EU27_2020', period: str = 'quarterly', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get GDP growth rate
    
    Args:
        country: Country code (e.g., 'DE', 'FR', 'EU27_2020')
        period: 'quarterly' or 'annual'
        year: Specific year. If None, returns all available periods
    
    Returns:
        Dictionary with time period as key and growth rate as value
        
    Example:
        >>> data = get_gdp_growth('EU27_2020', 'quarterly')
        >>> data['2023-Q4']
        0.1
    """
    dataset = 'namq_10_gdp' if period == 'quarterly' else 'nama_10_gdp'
    
    params = {
        'geo': country,
        'unit': 'CLV_PCH_PRE',  # Chain linked volumes, percentage change on previous period
        'na_item': 'B1GQ'  # Gross domestic product at market prices
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data(dataset, params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            # For annual, return specific year
            if period == 'annual':
                return {str(year): parsed.get(str(year), 0.0)}
            # For quarterly, return all quarters of that year
            return {k: v for k, v in parsed.items() if k.startswith(str(year))}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_inflation_hicp(country: str = 'EU27_2020', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get Harmonized Index of Consumer Prices (HICP) - annual average
    
    Args:
        country: Country code (e.g., 'DE', 'FR', 'EU27_2020')
        year: Specific year. If None, returns all available years
    
    Returns:
        Dictionary with year as key and HICP index as value
        
    Example:
        >>> data = get_inflation_hicp('EU27_2020', 2023)
        >>> data['2023']
        123.45
    """
    params = {
        'geo': country,
        'coicop': 'CP00'  # All-items HICP
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data('prc_hicp_aind', params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            return {str(year): parsed.get(str(year), 0.0)}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_population(country: str = 'DE', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get population on 1 January
    
    Args:
        country: Country code (e.g., 'DE', 'FR', 'EU27_2020')
        year: Specific year. If None, returns all available years
    
    Returns:
        Dictionary with year as key and population count as value
        
    Example:
        >>> data = get_population('DE', 2023)
        >>> data['2023']
        84432670
    """
    params = {
        'geo': country,
        'sex': 'T',  # Total
        'age': 'TOTAL'  # All ages
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data('demo_pjan', params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            return {str(year): parsed.get(str(year), 0.0)}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_trade_balance(country: str = 'DE', partner: str = 'WORLD', year: Optional[int] = None) -> Dict[str, Union[float, Dict]]:
    """
    Get trade balance (exports - imports) in million EUR
    
    Args:
        country: Country code (e.g., 'DE', 'FR')
        partner: Partner code (e.g., 'WORLD', 'EU27_2020', 'US', 'CN')
        year: Specific year. If None, returns all available years
    
    Returns:
        Dictionary with year as key and trade balance as value
        
    Example:
        >>> data = get_trade_balance('DE', 'WORLD', 2023)
        >>> data['2023']
        125800.0
    """
    params = {
        'reporter': country,
        'partner': partner,
        'product': 'TOTAL',  # All products
        'indicators': 'BALANCE'  # Trade balance
    }
    
    if year:
        params['time'] = str(year)
    
    try:
        data = _fetch_eurostat_data('ext_lt_intertrd', params)
        parsed = _parse_eurostat_response(data)
        
        if year:
            return {str(year): parsed.get(str(year), 0.0)}
        return parsed
    except Exception as e:
        return {'error': str(e)}


def get_dataset_info() -> Dict[str, Dict]:
    """
    Get information about available Eurostat datasets in this module
    
    Returns:
        Dictionary with dataset codes and metadata
    """
    return EUROSTAT_DATASETS


if __name__ == "__main__":
    # Test basic functionality
    print(json.dumps({
        "module": "eurostat_web_services",
        "status": "active",
        "source": EUROSTAT_BASE_URL,
        "datasets": list(EUROSTAT_DATASETS.keys()),
        "timestamp": datetime.now().isoformat()
    }, indent=2))
