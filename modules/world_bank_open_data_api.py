#!/usr/bin/env python3
"""
World Bank Open Data API — Global Economic & Demographic Indicators

Access worldwide indicators on labor force participation, demographics, economic inclusion,
youth unemployment, gender gaps in employment, population growth, GDP, inflation, and trade.
Essential for modeling emerging market risks and global economic trends.

Source: https://api.worldbank.org/v2/
Category: Labor & Demographics
Free tier: true - Unlimited queries with no rate limits; open access without API key.
Update frequency: annually
Author: QuantClaw Data NightBuilder
"""

import requests
from typing import Dict, List, Optional, Union
from datetime import datetime

# World Bank API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"

# Common World Bank Indicator Codes
WB_INDICATORS = {
    'GDP': 'NY.GDP.MKTP.CD',  # GDP (current US$)
    'UNEMPLOYMENT': 'SL.UEM.TOTL.ZS',  # Unemployment rate (% of total labor force)
    'POPULATION': 'SP.POP.TOTL',  # Total population
    'INFLATION': 'FP.CPI.TOTL.ZG',  # Inflation, consumer prices (annual %)
    'TRADE_BALANCE': 'NE.RSB.GNFS.ZS',  # External balance on goods and services (% of GDP)
    'GDP_GROWTH': 'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
    'GDP_PER_CAPITA': 'NY.GDP.PCAP.CD',  # GDP per capita (current US$)
}


def _make_request(endpoint: str, params: dict = None) -> Optional[List]:
    """
    Internal helper to make World Bank API requests.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
    
    Returns:
        List of data records or None on error
    """
    url = f"{WB_BASE_URL}/{endpoint}"
    default_params = {'format': 'json', 'per_page': 1000}
    if params:
        default_params.update(params)
    
    try:
        response = requests.get(url, params=default_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # World Bank API returns [metadata, data] array
        if isinstance(data, list) and len(data) > 1:
            return data[1]  # Return the actual data array
        return None
    except requests.exceptions.RequestException as e:
        print(f"World Bank API request failed: {e}")
        return None
    except (ValueError, IndexError) as e:
        print(f"Failed to parse World Bank API response: {e}")
        return None


def get_indicator_data(
    indicator: str = "NY.GDP.MKTP.CD",
    country: str = "US",
    start_year: int = 2015,
    end_year: Optional[int] = None
) -> Dict:
    """
    Get any World Bank indicator data for a country.
    
    Args:
        indicator: World Bank indicator code (e.g., NY.GDP.MKTP.CD for GDP)
        country: ISO 2-letter country code (e.g., US, CN, DE)
        start_year: Start year for data
        end_year: End year for data (defaults to current year)
    
    Returns:
        Dict with indicator metadata and time series data
    """
    if end_year is None:
        end_year = datetime.now().year
    
    endpoint = f"country/{country}/indicator/{indicator}"
    params = {'date': f"{start_year}:{end_year}"}
    
    data = _make_request(endpoint, params)
    
    if not data:
        return {'error': 'No data returned', 'indicator': indicator, 'country': country}
    
    # Extract and structure the data
    series = []
    for entry in data:
        if entry.get('value') is not None:
            series.append({
                'date': entry.get('date'),
                'value': entry.get('value'),
                'country': entry.get('country', {}).get('value'),
                'countryiso3code': entry.get('countryiso3code')
            })
    
    return {
        'indicator': indicator,
        'indicator_name': data[0].get('indicator', {}).get('value') if data else None,
        'country': country,
        'start_year': start_year,
        'end_year': end_year,
        'data': sorted(series, key=lambda x: x['date'])
    }


def get_gdp_data(country: str = "US", start_year: int = 2015) -> Dict:
    """
    Get GDP (current US$) data for a country.
    
    Args:
        country: ISO 2-letter country code
        start_year: Start year for data
    
    Returns:
        Dict with GDP time series data
    """
    return get_indicator_data(
        indicator=WB_INDICATORS['GDP'],
        country=country,
        start_year=start_year
    )


def get_unemployment(country: str = "US", start_year: int = 2015) -> Dict:
    """
    Get unemployment rate (% of total labor force) for a country.
    
    Args:
        country: ISO 2-letter country code
        start_year: Start year for data
    
    Returns:
        Dict with unemployment rate time series data
    """
    return get_indicator_data(
        indicator=WB_INDICATORS['UNEMPLOYMENT'],
        country=country,
        start_year=start_year
    )


def get_population(country: str = "US", start_year: int = 2015) -> Dict:
    """
    Get total population data for a country.
    
    Args:
        country: ISO 2-letter country code
        start_year: Start year for data
    
    Returns:
        Dict with population time series data
    """
    return get_indicator_data(
        indicator=WB_INDICATORS['POPULATION'],
        country=country,
        start_year=start_year
    )


def get_inflation(country: str = "US", start_year: int = 2015) -> Dict:
    """
    Get CPI inflation (annual %) for a country.
    
    Args:
        country: ISO 2-letter country code
        start_year: Start year for data
    
    Returns:
        Dict with inflation time series data
    """
    return get_indicator_data(
        indicator=WB_INDICATORS['INFLATION'],
        country=country,
        start_year=start_year
    )


def get_trade_balance(country: str = "US", start_year: int = 2015) -> Dict:
    """
    Get external balance on goods and services (% of GDP) for a country.
    
    Args:
        country: ISO 2-letter country code
        start_year: Start year for data
    
    Returns:
        Dict with trade balance time series data
    """
    return get_indicator_data(
        indicator=WB_INDICATORS['TRADE_BALANCE'],
        country=country,
        start_year=start_year
    )


def search_indicators(query: str = "gdp", limit: int = 50) -> List[Dict]:
    """
    Search available World Bank indicators by keyword.
    
    Args:
        query: Search query (e.g., "gdp", "unemployment", "population")
        limit: Maximum number of results to return
    
    Returns:
        List of indicator metadata dicts
    """
    endpoint = "indicator"
    params = {'per_page': limit}
    
    data = _make_request(endpoint, params)
    
    if not data:
        return []
    
    # Filter results by query
    query_lower = query.lower()
    results = []
    
    for indicator in data:
        name = indicator.get('name', '').lower()
        source_note = indicator.get('sourceNote', '').lower()
        
        if query_lower in name or query_lower in source_note:
            results.append({
                'id': indicator.get('id'),
                'name': indicator.get('name'),
                'source': indicator.get('source', {}).get('value'),
                'sourceNote': indicator.get('sourceNote', '')[:200] + '...' if len(indicator.get('sourceNote', '')) > 200 else indicator.get('sourceNote', ''),
                'topics': [t.get('value') for t in indicator.get('topics', [])]
            })
    
    return results[:limit]


def get_country_info(country: str = "US") -> Dict:
    """
    Get country metadata including region, income level, and capital city.
    
    Args:
        country: ISO 2-letter country code
    
    Returns:
        Dict with country metadata
    """
    endpoint = f"country/{country}"
    
    data = _make_request(endpoint)
    
    if not data or len(data) == 0:
        return {'error': 'Country not found', 'country': country}
    
    country_data = data[0]
    
    return {
        'id': country_data.get('id'),
        'iso2Code': country_data.get('iso2Code'),
        'name': country_data.get('name'),
        'region': country_data.get('region', {}).get('value'),
        'adminregion': country_data.get('adminregion', {}).get('value'),
        'incomeLevel': country_data.get('incomeLevel', {}).get('value'),
        'lendingType': country_data.get('lendingType', {}).get('value'),
        'capitalCity': country_data.get('capitalCity'),
        'longitude': country_data.get('longitude'),
        'latitude': country_data.get('latitude')
    }


def compare_countries(
    countries: List[str] = ["US", "CN", "DE"],
    indicator: str = "NY.GDP.MKTP.CD",
    start_year: int = 2015,
    end_year: Optional[int] = None
) -> Dict:
    """
    Compare an indicator across multiple countries.
    
    Args:
        countries: List of ISO 2-letter country codes
        indicator: World Bank indicator code
        start_year: Start year for data
        end_year: End year for data (defaults to current year)
    
    Returns:
        Dict with comparative data for all countries
    """
    if end_year is None:
        end_year = datetime.now().year
    
    # Join country codes with semicolon for multi-country query
    country_string = ";".join(countries)
    endpoint = f"country/{country_string}/indicator/{indicator}"
    params = {'date': f"{start_year}:{end_year}"}
    
    data = _make_request(endpoint, params)
    
    if not data:
        return {'error': 'No data returned', 'countries': countries, 'indicator': indicator}
    
    # Organize data by country
    by_country = {}
    indicator_name = None
    
    for entry in data:
        if entry.get('value') is None:
            continue
        
        country_code = entry.get('countryiso3code')
        if not indicator_name:
            indicator_name = entry.get('indicator', {}).get('value')
        
        if country_code not in by_country:
            by_country[country_code] = {
                'country_name': entry.get('country', {}).get('value'),
                'country_code': country_code,
                'data': []
            }
        
        by_country[country_code]['data'].append({
            'date': entry.get('date'),
            'value': entry.get('value')
        })
    
    # Sort each country's data by date
    for country_code in by_country:
        by_country[country_code]['data'] = sorted(
            by_country[country_code]['data'],
            key=lambda x: x['date']
        )
    
    return {
        'indicator': indicator,
        'indicator_name': indicator_name,
        'start_year': start_year,
        'end_year': end_year,
        'countries': by_country
    }


if __name__ == "__main__":
    import json
    
    # Test the module
    print("=== World Bank Open Data API Module ===\n")
    
    # Test get_gdp_data
    print("1. Testing get_gdp_data('US')...")
    gdp = get_gdp_data("US", start_year=2020)
    print(f"   Retrieved {len(gdp.get('data', []))} data points")
    if gdp.get('data'):
        print(f"   Latest: {gdp['data'][-1]}")
    
    # Test search_indicators
    print("\n2. Testing search_indicators('gdp')...")
    indicators = search_indicators("gdp", limit=5)
    print(f"   Found {len(indicators)} indicators")
    if indicators:
        print(f"   First: {indicators[0]['name']}")
    
    print("\n✅ Module tests complete")
