#!/usr/bin/env python3
"""
IMF World Economic Outlook Data Module

International Monetary Fund economic indicators via DataMapper API
- GDP growth forecasts
- Inflation rates (CPI)
- Current account balances
- Unemployment rates
- Balance of payments
- International financial statistics

Data Source: https://www.imf.org/external/datamapper/api/v1/
Refresh: Quarterly (World Economic Outlook updates)
Coverage: 190+ countries, 2000-present + forecasts to 2029
Free tier: Yes, no authentication required

Author: QUANTCLAW DATA NightBuilder
Phase: IMF_001
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Union
from datetime import datetime

# IMF DataMapper API Configuration
IMF_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

# Core IMF Indicator Registry
IMF_INDICATORS = {
    'NGDP_RPCH': {
        'name': 'Real GDP Growth',
        'description': 'Real GDP growth rate (annual percent change)',
        'unit': 'percent'
    },
    'PCPIPCH': {
        'name': 'Inflation Rate',
        'description': 'Consumer prices, average inflation (annual percent change)',
        'unit': 'percent'
    },
    'BCA_NGDPD': {
        'name': 'Current Account Balance',
        'description': 'Current account balance (percent of GDP)',
        'unit': 'percent of GDP'
    },
    'LUR': {
        'name': 'Unemployment Rate',
        'description': 'Unemployment rate (percent of labor force)',
        'unit': 'percent'
    },
    'NGDPD': {
        'name': 'Nominal GDP',
        'description': 'Nominal GDP (billions of current US dollars)',
        'unit': 'USD billions'
    },
    'NGDPDPC': {
        'name': 'GDP Per Capita',
        'description': 'GDP per capita (current US dollars)',
        'unit': 'USD'
    },
    'PPPGDP': {
        'name': 'GDP PPP',
        'description': 'GDP based on purchasing power parity (billions of current international dollars)',
        'unit': 'Int$ billions'
    },
    'GGXWDG_NGDP': {
        'name': 'Government Debt',
        'description': 'General government gross debt (percent of GDP)',
        'unit': 'percent of GDP'
    },
    'GGXCNL_NGDP': {
        'name': 'Government Balance',
        'description': 'General government net lending/borrowing (percent of GDP)',
        'unit': 'percent of GDP'
    },
    'TM_RPCH': {
        'name': 'Import Volume Growth',
        'description': 'Import volume of goods and services (annual percent change)',
        'unit': 'percent'
    },
    'TX_RPCH': {
        'name': 'Export Volume Growth',
        'description': 'Export volume of goods and services (annual percent change)',
        'unit': 'percent'
    }
}


def _fetch_imf_data(indicator: str, periods: Optional[List[int]] = None) -> Dict:
    """
    Internal function to fetch data from IMF DataMapper API
    
    Args:
        indicator: IMF indicator code (e.g., 'NGDP_RPCH')
        periods: List of years to retrieve (e.g., [2024, 2025, 2026])
    
    Returns:
        Dictionary with nested structure: {indicator: {country_code: {year: value}}}
    
    Raises:
        urllib.error.URLError: If network request fails
        json.JSONDecodeError: If response is not valid JSON
    """
    url = f"{IMF_BASE_URL}/{indicator}"
    
    if periods:
        period_str = ','.join(map(str, periods))
        url += f"?periods={period_str}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('values', {})
    except urllib.error.HTTPError as e:
        raise ValueError(f"IMF API error for indicator {indicator}: HTTP {e.code}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to connect to IMF API: {e.reason}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from IMF API: {e}")


def get_gdp_growth(country_codes: Optional[List[str]] = None, 
                   years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get real GDP growth rates
    
    Args:
        country_codes: List of ISO 3-letter country codes (e.g., ['USA', 'CHN', 'DEU'])
                      If None, returns all countries
        years: List of years to retrieve (e.g., [2024, 2025, 2026])
              If None, returns all available years
    
    Returns:
        Dictionary: {country_code: {year: growth_rate}}
        
    Example:
        >>> data = get_gdp_growth(['USA', 'CHN'], [2024, 2025])
        >>> data['USA']['2024']
        2.8
    """
    data = _fetch_imf_data('NGDP_RPCH', years)
    indicator_data = data.get('NGDP_RPCH', {})
    
    if country_codes:
        return {code: indicator_data.get(code, {}) for code in country_codes}
    return indicator_data


def get_inflation(country_codes: Optional[List[str]] = None,
                  years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get inflation rates (CPI, annual percent change)
    
    Args:
        country_codes: List of ISO 3-letter country codes
        years: List of years to retrieve
    
    Returns:
        Dictionary: {country_code: {year: inflation_rate}}
        
    Example:
        >>> data = get_inflation(['USA', 'CHN'], [2024, 2025])
        >>> data['USA']['2024']
        3.2
    """
    data = _fetch_imf_data('PCPIPCH', years)
    indicator_data = data.get('PCPIPCH', {})
    
    if country_codes:
        return {code: indicator_data.get(code, {}) for code in country_codes}
    return indicator_data


def get_current_account(country_codes: Optional[List[str]] = None,
                        years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get current account balance (percent of GDP)
    
    Args:
        country_codes: List of ISO 3-letter country codes
        years: List of years to retrieve
    
    Returns:
        Dictionary: {country_code: {year: current_account_pct_gdp}}
        
    Example:
        >>> data = get_current_account(['USA', 'DEU'], [2024])
        >>> data['DEU']['2024']
        7.2
    """
    data = _fetch_imf_data('BCA_NGDPD', years)
    indicator_data = data.get('BCA_NGDPD', {})
    
    if country_codes:
        return {code: indicator_data.get(code, {}) for code in country_codes}
    return indicator_data


def get_unemployment(country_codes: Optional[List[str]] = None,
                     years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get unemployment rates (percent of labor force)
    
    Args:
        country_codes: List of ISO 3-letter country codes
        years: List of years to retrieve
    
    Returns:
        Dictionary: {country_code: {year: unemployment_rate}}
        
    Example:
        >>> data = get_unemployment(['USA', 'JPN'], [2024, 2025])
        >>> data['USA']['2024']
        4.1
    """
    data = _fetch_imf_data('LUR', years)
    indicator_data = data.get('LUR', {})
    
    if country_codes:
        return {code: indicator_data.get(code, {}) for code in country_codes}
    return indicator_data


def get_weo_indicators(indicator: str, 
                       country_codes: Optional[List[str]] = None,
                       years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get any World Economic Outlook indicator by code
    
    Args:
        indicator: IMF indicator code (e.g., 'NGDPD', 'PPPGDP', 'GGXWDG_NGDP')
        country_codes: List of ISO 3-letter country codes
        years: List of years to retrieve
    
    Returns:
        Dictionary: {country_code: {year: value}}
        
    Example:
        >>> data = get_weo_indicators('NGDPD', ['USA', 'CHN'], [2024])
        >>> data['USA']['2024']  # Nominal GDP in USD billions
        27974.0
    """
    data = _fetch_imf_data(indicator, years)
    indicator_data = data.get(indicator, {})
    
    if country_codes:
        return {code: indicator_data.get(code, {}) for code in country_codes}
    return indicator_data


def get_available_indicators() -> Dict[str, Dict[str, str]]:
    """
    List all available IMF indicators with descriptions
    
    Returns:
        Dictionary of indicators with metadata
        
    Example:
        >>> indicators = get_available_indicators()
        >>> indicators['NGDP_RPCH']['name']
        'Real GDP Growth'
    """
    return IMF_INDICATORS


def get_country_data(country_code: str, 
                     years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """
    Get all key economic indicators for a single country
    
    Args:
        country_code: ISO 3-letter country code (e.g., 'USA', 'CHN', 'DEU')
        years: List of years to retrieve (defaults to [2024, 2025, 2026])
    
    Returns:
        Dictionary: {indicator_code: {year: value}}
        
    Example:
        >>> data = get_country_data('USA', [2024, 2025])
        >>> data['NGDP_RPCH']['2024']  # GDP growth
        2.8
        >>> data['PCPIPCH']['2024']     # Inflation
        3.2
    """
    if years is None:
        years = [2024, 2025, 2026]
    
    result = {}
    
    # Fetch key indicators
    key_indicators = ['NGDP_RPCH', 'PCPIPCH', 'BCA_NGDPD', 'LUR', 
                      'NGDPD', 'NGDPDPC', 'GGXWDG_NGDP']
    
    for indicator in key_indicators:
        try:
            data = _fetch_imf_data(indicator, years)
            country_data = data.get(indicator, {}).get(country_code, {})
            if country_data:
                result[indicator] = country_data
        except Exception:
            # Skip indicators that fail (some countries don't have all data)
            continue
    
    return result


def get_latest_data(indicator: str, country_code: str) -> Optional[Dict]:
    """
    Get the most recent data point for a specific indicator and country
    
    Args:
        indicator: IMF indicator code
        country_code: ISO 3-letter country code
    
    Returns:
        Dictionary with {year: value, timestamp: datetime} or None if no data
        
    Example:
        >>> latest = get_latest_data('NGDP_RPCH', 'USA')
        >>> latest['year']
        '2024'
        >>> latest['value']
        2.8
    """
    try:
        data = _fetch_imf_data(indicator)
        country_data = data.get(indicator, {}).get(country_code, {})
        
        if not country_data:
            return None
        
        # Find the most recent year with data
        years_sorted = sorted(country_data.keys(), reverse=True)
        if not years_sorted:
            return None
        
        latest_year = years_sorted[0]
        return {
            'year': latest_year,
            'value': country_data[latest_year],
            'indicator': indicator,
            'country': country_code,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return None


# CLI Test Interface
if __name__ == "__main__":
    print(json.dumps({
        "module": "imf_data",
        "status": "active",
        "source": "https://www.imf.org/external/datamapper/api/v1/",
        "indicators_available": len(IMF_INDICATORS),
        "coverage": "190+ countries",
        "auth_required": False
    }, indent=2))
    
    # Quick test
    print("\n=== Testing GDP Growth (USA, CHN) ===")
    try:
        gdp_data = get_gdp_growth(['USA', 'CHN'], [2024, 2025])
        print(json.dumps(gdp_data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
