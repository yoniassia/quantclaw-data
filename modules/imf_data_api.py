#!/usr/bin/env python3
"""
IMF Data API — International Financial Statistics & Economic Indicators

Access to IMF's DataMapper API for global economic data including:
- GDP, inflation, unemployment, fiscal balance
- Exchange rates and reserves  
- Balance of payments
- World Economic Outlook forecasts

Source: https://www.imf.org/external/datamapper/
Category: Emerging Markets & Global Economics
Free tier: True (no API key required for public data)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# IMF DataMapper API Configuration
BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

# Common country codes (ISO Alpha-3 for IMF)
COUNTRY_CODES = {
    'USA': 'United States', 'CHN': 'China', 'JPN': 'Japan', 'DEU': 'Germany',
    'GBR': 'United Kingdom', 'FRA': 'France', 'IND': 'India', 'BRA': 'Brazil',
    'CAN': 'Canada', 'ITA': 'Italy', 'KOR': 'South Korea', 'ESP': 'Spain',
    'AUS': 'Australia', 'MEX': 'Mexico', 'IDN': 'Indonesia', 'NLD': 'Netherlands',
    'SAU': 'Saudi Arabia', 'TUR': 'Turkey', 'CHE': 'Switzerland', 'POL': 'Poland'
}

# Alpha-2 to Alpha-3 mapping
ALPHA2_TO_ALPHA3 = {
    'US': 'USA', 'CN': 'CHN', 'JP': 'JPN', 'DE': 'DEU', 'GB': 'GBR',
    'FR': 'FRA', 'IN': 'IND', 'BR': 'BRA', 'CA': 'CAN', 'IT': 'ITA',
    'KR': 'KOR', 'ES': 'ESP', 'AU': 'AUS', 'MX': 'MEX', 'ID': 'IDN',
    'NL': 'NLD', 'SA': 'SAU', 'TR': 'TUR', 'CH': 'CHE', 'PL': 'POL'
}

# IMF DataMapper indicator codes
INDICATORS = {
    'NGDP_RPCH': 'Real GDP Growth (%)',
    'NGDPD': 'Nominal GDP (USD billions)',
    'PPPGDP': 'GDP based on PPP (USD billions)',
    'PCPIPCH': 'Inflation Rate (%)',
    'LUR': 'Unemployment Rate (%)',
    'GGXCNL_NGDP': 'General Government Net Lending/Borrowing (% GDP)',
    'GGXWDG_NGDP': 'General Government Gross Debt (% GDP)',
    'BCA_NGDPD': 'Current Account Balance (% GDP)',
    'BCA': 'Current Account Balance (USD billions)',
}

# ========== CORE API FUNCTIONS ==========

def _convert_country_code(country_code: str) -> str:
    """Convert Alpha-2 to Alpha-3 if needed."""
    code = country_code.upper()
    if len(code) == 2:
        return ALPHA2_TO_ALPHA3.get(code, code)
    return code


def get_dataflow_list() -> List[Dict]:
    """
    List all available IMF datasets/indicators.
    
    Returns:
        List of available indicators with codes and descriptions
    """
    result = []
    for code, description in INDICATORS.items():
        result.append({
            'code': code,
            'description': description,
            'source': 'IMF DataMapper'
        })
    return result


def get_ifs_data(country_code: str, indicator: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get International Financial Statistics data for a country and indicator.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code (e.g., 'US', 'USA')
        indicator: IMF indicator code (e.g., 'NGDP_RPCH' for real GDP growth)
        start_period: Start year (optional, e.g., '2020')
        end_period: End year (optional, e.g., '2023')
    
    Returns:
        Dictionary with indicator data and metadata
    
    Example:
        get_ifs_data('US', 'NGDP_RPCH', '2020', '2023')
    """
    try:
        country = _convert_country_code(country_code)
        
        # Build URL with periods if specified
        if start_period and end_period:
            periods = f"{start_period}:{end_period}"
            url = f"{BASE_URL}/{indicator}/{periods}/{country}"
        else:
            url = f"{BASE_URL}/{indicator}/{country}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        result = {
            'country': country_code,
            'indicator': indicator,
            'data': [],
            'metadata': {
                'description': INDICATORS.get(indicator, indicator),
                'source': 'IMF DataMapper'
            }
        }
        
        # Parse DataMapper response
        if 'values' in data and indicator in data['values']:
            country_data = data['values'][indicator].get(country, {})
            for year, value in sorted(country_data.items()):
                if value is not None:
                    result['data'].append({
                        'period': year,
                        'value': value
                    })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch IFS data: {str(e)}', 'country': country_code, 'indicator': indicator}
    except Exception as e:
        return {'error': f'Error processing IFS data: {str(e)}', 'country': country_code, 'indicator': indicator}


def get_bop_data(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get Balance of Payments (Current Account) data for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code (e.g., 'US', 'USA')
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with BOP data and metadata
    """
    # Use Current Account Balance indicator
    return get_ifs_data(country_code, 'BCA_NGDPD', start_period, end_period)


def get_weo_data(country_code: str, subject: Optional[str] = None) -> Dict:
    """
    Get World Economic Outlook forecasts for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code (e.g., 'US', 'USA')
        subject: WEO subject code (defaults to 'NGDP_RPCH' for real GDP growth)
    
    Returns:
        Dictionary with WEO forecast data
    """
    if not subject:
        subject = 'NGDP_RPCH'  # Real GDP growth
    
    return get_ifs_data(country_code, subject)


def get_exchange_rates(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get GDP data as proxy for exchange rate trends (DataMapper doesn't have direct FX rates).
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code (e.g., 'GB', 'JP')
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with GDP data (proxy for economic trends affecting exchange rates)
    
    Note: For real-time exchange rates, use forex APIs. IMF DataMapper focuses on macroeconomic indicators.
    """
    result = get_ifs_data(country_code, 'NGDPD', start_period, end_period)
    if 'metadata' in result:
        result['metadata']['note'] = 'GDP data returned (DataMapper API does not provide direct FX rates)'
    return result


def get_reserves(country_code: str) -> Dict:
    """
    Get current account balance as proxy for reserves position.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code (e.g., 'CN', 'JP')
    
    Returns:
        Dictionary with current account data
    
    Note: For detailed reserves data, use IMF's International Reserves and Foreign Currency Liquidity dataset.
    """
    result = get_ifs_data(country_code, 'BCA')
    if 'metadata' in result:
        result['metadata']['note'] = 'Current Account Balance (proxy for reserves position)'
    return result


def search_indicators(keyword: str) -> List[Dict]:
    """
    Search for available indicators by keyword.
    
    Args:
        keyword: Search term (e.g., 'GDP', 'inflation', 'debt')
    
    Returns:
        List of matching indicators with codes and descriptions
    """
    keyword_lower = keyword.lower()
    results = []
    
    for code, description in INDICATORS.items():
        if keyword_lower in description.lower() or keyword_lower in code.lower():
            results.append({
                'code': code,
                'description': description,
                'source': 'IMF DataMapper'
            })
    
    return results


def get_gdp_data(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get GDP data for a country (nominal and real growth).
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with GDP data
    """
    return get_ifs_data(country_code, 'NGDPD', start_period, end_period)


def get_inflation_data(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get inflation rate data for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with inflation data
    """
    return get_ifs_data(country_code, 'PCPIPCH', start_period, end_period)


def get_unemployment_data(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get unemployment rate data for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with unemployment data
    """
    return get_ifs_data(country_code, 'LUR', start_period, end_period)


def get_fiscal_balance(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get government fiscal balance data for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with fiscal balance data
    """
    return get_ifs_data(country_code, 'GGXCNL_NGDP', start_period, end_period)


def get_government_debt(country_code: str, start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    """
    Get government gross debt data for a country.
    
    Args:
        country_code: ISO Alpha-2 or Alpha-3 country code
        start_period: Start year (optional)
        end_period: End year (optional)
    
    Returns:
        Dictionary with government debt data
    """
    return get_ifs_data(country_code, 'GGXWDG_NGDP', start_period, end_period)


# ========== UTILITY FUNCTIONS ==========

def get_country_name(country_code: str) -> str:
    """Get country name from ISO code."""
    code = _convert_country_code(country_code)
    return COUNTRY_CODES.get(code, code)


def get_countries() -> Dict:
    """
    Get list of all available countries.
    
    Returns:
        Dictionary mapping country codes to names
    """
    try:
        url = f"{BASE_URL}/countries"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('countries', {})
        
    except Exception as e:
        return {'error': f'Failed to fetch countries: {str(e)}'}


if __name__ == "__main__":
    # Test module
    print(json.dumps({
        "module": "imf_data_api",
        "status": "active",
        "base_url": BASE_URL,
        "functions": [
            "get_dataflow_list",
            "get_ifs_data",
            "get_bop_data",
            "get_weo_data",
            "get_exchange_rates",
            "get_reserves",
            "search_indicators",
            "get_gdp_data",
            "get_inflation_data",
            "get_unemployment_data",
            "get_fiscal_balance",
            "get_government_debt",
            "get_countries"
        ],
        "available_indicators": list(INDICATORS.keys())
    }, indent=2))
