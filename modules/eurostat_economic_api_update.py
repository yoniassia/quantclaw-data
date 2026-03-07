#!/usr/bin/env python3
"""
Eurostat Economic API Update — 2026 Updated API Module

Eurostat updated its API in 2026 to include new free tiers for EU-wide macroeconomic data,
covering inflation, growth, and central bank-aligned indicators in SDMX-JSON format.
This module focuses on economic indicators (CPI, GDP, unemployment, interest rates).

Source: https://ec.europa.eu/eurostat/web/api
Base URL: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
Category: Macro / Central Banks
Free tier: True (1000 queries per day, no registration required)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Eurostat API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# ========== DATASET CODES FOR ECONOMIC INDICATORS ==========

ECONOMIC_DATASETS = {
    'CPI': 'ei_cphi_m',           # Consumer Price Index (monthly)
    'HICP': 'prc_hicp_midx',      # Harmonised Index of Consumer Prices
    'GDP': 'namq_10_gdp',         # GDP and main components (quarterly)
    'UNEMPLOYMENT': 'une_rt_m',   # Unemployment rate (monthly)
    'INTEREST': 'irt_st_m',       # Interest rates (monthly)
    'SENTIMENT': 'ei_bssi_m_r2',  # Economic sentiment indicator
}


def _get_recent_period(years_back: int = 3) -> str:
    """Generate startPeriod parameter for recent data (default: last 3 years)"""
    date = datetime.now() - timedelta(days=years_back * 365)
    return date.strftime("%Y-%m")


def _fetch_eurostat_data(
    dataset_code: str,
    geo: str = "EU",
    params: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Internal helper to fetch data from Eurostat API.
    
    Args:
        dataset_code: Eurostat dataset code (e.g., 'ei_cphi_m')
        geo: Geographic area code (EU, DE, FR, etc.)
        params: Additional URL parameters
        timeout: Request timeout in seconds
    
    Returns:
        Dict with API response or error information
    """
    url = f"{EUROSTAT_BASE_URL}/{dataset_code}"
    
    # Build query parameters with time filtering to avoid 413 errors
    query_params = {
        'format': 'JSON',
        'lang': 'EN',
        'geo': geo,
        'sinceTimePeriod': _get_recent_period(3)  # Last 3 years by default
    }
    
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'dataset': dataset_code,
            'geo': geo
        }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'dataset': dataset_code,
            'geo': geo
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON decode error: {str(e)}',
            'dataset': dataset_code,
            'geo': geo
        }


def _parse_sdmx_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse SDMX-JSON format response into simple records.
    Handles both SDMX 2.0 and 2.1 structures.
    
    Args:
        data: Raw SDMX-JSON response
    
    Returns:
        List of dicts with date, value, and metadata (sorted newest first)
    """
    try:
        records = []
        
        # Try to find values and dimensions in various SDMX formats
        values_dict = data.get('value', {})
        
        if not values_dict:
            # Alternative structure
            if 'dataSets' in data and len(data['dataSets']) > 0:
                dataset = data['dataSets'][0]
                values_dict = dataset.get('series', {})
        
        # Get dimension information
        dimension_data = data.get('dimension', {})
        
        # Find time dimension
        time_values = []
        if 'time' in dimension_data:
            time_cat = dimension_data['time'].get('category', {})
            if 'label' in time_cat:
                time_values = list(time_cat['label'].values())
            elif 'index' in time_cat:
                time_values = list(time_cat['index'].keys())
        
        # If we have simple value dict and time values match
        if values_dict and time_values:
            # Try to match indices
            for idx, (key, value) in enumerate(values_dict.items()):
                if value is not None and idx < len(time_values):
                    try:
                        records.append({
                            'time': time_values[idx],
                            'value': float(value) if isinstance(value, (int, float, str)) else value,
                            'key': key
                        })
                    except (ValueError, TypeError):
                        continue
        
        # Sort by time (newest first) - handle various time formats
        def parse_time(rec):
            """Parse time string to sortable format"""
            time_str = str(rec['time'])
            # Handle YYYY, YYYY-MM, YYYY-Qn formats
            if 'M' in time_str:  # Monthly: 2024-M01
                return time_str.replace('M', '-')
            elif 'Q' in time_str:  # Quarterly: 2024-Q1
                quarter = time_str.split('-Q')[1]
                year = time_str.split('-Q')[0]
                month = str(int(quarter) * 3).zfill(2)
                return f"{year}-{month}"
            return time_str
        
        records.sort(key=lambda x: parse_time(x), reverse=True)
        
        return records
        
    except Exception as e:
        # Return empty list on parse errors
        return []


def get_eu_cpi(geo: str = "EU", start_period: Optional[str] = None) -> Dict[str, Any]:
    """
    Get EU Consumer Price Index (CPI) data.
    
    Args:
        geo: Geographic area code (EU, DE, FR, IT, ES, etc.)
        start_period: Start period in format YYYY-MM (e.g., '2024-01')
    
    Returns:
        Dict with CPI data, latest value, and year-over-year change
    """
    params = {}
    if start_period:
        params['sinceTimePeriod'] = start_period
    
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['CPI'], geo=geo, params=params)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No data found or unable to parse response',
            'dataset': 'CPI',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate YoY change if enough data
    yoy_change = None
    yoy_change_pct = None
    if len(records) >= 12:
        year_ago = records[11]
        if isinstance(latest['value'], (int, float)) and isinstance(year_ago['value'], (int, float)):
            yoy_change = latest['value'] - year_ago['value']
            yoy_change_pct = (yoy_change / year_ago['value']) * 100 if year_ago['value'] != 0 else 0
    
    return {
        'success': True,
        'indicator': 'Consumer Price Index',
        'geo': geo,
        'latest_value': latest['value'],
        'latest_period': latest['time'],
        'yoy_change': yoy_change,
        'yoy_change_pct': yoy_change_pct,
        'records_count': len(records),
        'recent_data': records[:12],  # Last 12 months
        'timestamp': datetime.now().isoformat()
    }


def get_eu_gdp_growth(geo: str = "EU", freq: str = "Q") -> Dict[str, Any]:
    """
    Get EU GDP growth rates.
    
    Args:
        geo: Geographic area code (EU, EA (Euro Area), DE, FR, etc.)
        freq: Frequency - 'Q' for quarterly, 'A' for annual
    
    Returns:
        Dict with GDP growth data and trends
    """
    params = {}
    if freq == "Q":
        params['freq'] = 'Q'
    
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['GDP'], geo=geo, params=params)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No GDP data found',
            'dataset': 'GDP',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate quarter-over-quarter or year-over-year growth
    qoq_growth = None
    if len(records) >= 2 and isinstance(latest['value'], (int, float)) and isinstance(records[1]['value'], (int, float)):
        prev_val = records[1]['value']
        qoq_growth = ((latest['value'] - prev_val) / prev_val) * 100 if prev_val != 0 else 0
    
    return {
        'success': True,
        'indicator': 'GDP Growth',
        'geo': geo,
        'frequency': freq,
        'latest_value': latest['value'],
        'latest_period': latest['time'],
        'qoq_growth_pct': qoq_growth,
        'records_count': len(records),
        'recent_data': records[:8],  # Last 2 years of quarters
        'timestamp': datetime.now().isoformat()
    }


def get_eu_unemployment(geo: str = "EU") -> Dict[str, Any]:
    """
    Get EU unemployment rates.
    
    Args:
        geo: Geographic area code (EU, EA, DE, FR, etc.)
    
    Returns:
        Dict with unemployment rate data and trends
    """
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['UNEMPLOYMENT'], geo=geo)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No unemployment data found',
            'dataset': 'Unemployment',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate month-over-month and year-over-year changes
    mom_change = None
    yoy_change = None
    
    if len(records) >= 2 and isinstance(latest['value'], (int, float)) and isinstance(records[1]['value'], (int, float)):
        mom_change = latest['value'] - records[1]['value']
    
    if len(records) >= 12 and isinstance(latest['value'], (int, float)) and isinstance(records[11]['value'], (int, float)):
        yoy_change = latest['value'] - records[11]['value']
    
    return {
        'success': True,
        'indicator': 'Unemployment Rate',
        'geo': geo,
        'latest_value': latest['value'],
        'latest_period': latest['time'],
        'mom_change': mom_change,
        'yoy_change': yoy_change,
        'records_count': len(records),
        'recent_data': records[:12],  # Last 12 months
        'timestamp': datetime.now().isoformat()
    }


def get_eu_interest_rates(geo: str = "EU") -> Dict[str, Any]:
    """
    Get ECB interest rates and money market rates.
    
    Args:
        geo: Geographic area code (EU, EA for Euro Area)
    
    Returns:
        Dict with interest rate data
    """
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['INTEREST'], geo=geo)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No interest rate data found',
            'dataset': 'Interest Rates',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate changes
    mom_change = None
    yoy_change = None
    
    if len(records) >= 2 and isinstance(latest['value'], (int, float)) and isinstance(records[1]['value'], (int, float)):
        mom_change = latest['value'] - records[1]['value']
    
    if len(records) >= 12 and isinstance(latest['value'], (int, float)) and isinstance(records[11]['value'], (int, float)):
        yoy_change = latest['value'] - records[11]['value']
    
    return {
        'success': True,
        'indicator': 'Interest Rates',
        'geo': geo,
        'latest_value': latest['value'],
        'latest_period': latest['time'],
        'mom_change': mom_change,
        'yoy_change': yoy_change,
        'records_count': len(records),
        'recent_data': records[:12],
        'timestamp': datetime.now().isoformat()
    }


def get_eu_hicp(geo: str = "EU") -> Dict[str, Any]:
    """
    Get Harmonised Index of Consumer Prices (HICP).
    
    Args:
        geo: Geographic area code (EU, EA, DE, FR, etc.)
    
    Returns:
        Dict with HICP index data and inflation rates
    """
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['HICP'], geo=geo)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No HICP data found',
            'dataset': 'HICP',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate inflation rate (YoY change)
    inflation_rate = None
    if len(records) >= 12 and isinstance(latest['value'], (int, float)) and isinstance(records[11]['value'], (int, float)):
        year_ago = records[11]['value']
        inflation_rate = ((latest['value'] - year_ago) / year_ago) * 100 if year_ago != 0 else 0
    
    # Month-over-month change
    mom_change_pct = None
    if len(records) >= 2 and isinstance(latest['value'], (int, float)) and isinstance(records[1]['value'], (int, float)):
        prev_val = records[1]['value']
        mom_change_pct = ((latest['value'] - prev_val) / prev_val) * 100 if prev_val != 0 else 0
    
    return {
        'success': True,
        'indicator': 'Harmonised Index of Consumer Prices',
        'geo': geo,
        'latest_index': latest['value'],
        'latest_period': latest['time'],
        'inflation_rate_yoy': inflation_rate,
        'mom_change_pct': mom_change_pct,
        'records_count': len(records),
        'recent_data': records[:12],
        'timestamp': datetime.now().isoformat()
    }


def get_economic_sentiment(geo: str = "EU") -> Dict[str, Any]:
    """
    Get Economic Sentiment Indicator (ESI).
    Composite indicator of economic confidence across sectors.
    
    Args:
        geo: Geographic area code (EU, EA, DE, FR, etc.)
    
    Returns:
        Dict with economic sentiment data and trends
    """
    result = _fetch_eurostat_data(ECONOMIC_DATASETS['SENTIMENT'], geo=geo)
    
    if not result['success']:
        return result
    
    records = _parse_sdmx_json(result['data'])
    
    if not records:
        return {
            'success': False,
            'error': 'No sentiment data found',
            'dataset': 'Economic Sentiment',
            'geo': geo
        }
    
    latest = records[0]
    
    # Calculate changes and trend
    mom_change = None
    yoy_change = None
    
    if len(records) >= 2 and isinstance(latest['value'], (int, float)) and isinstance(records[1]['value'], (int, float)):
        mom_change = latest['value'] - records[1]['value']
    
    if len(records) >= 12 and isinstance(latest['value'], (int, float)) and isinstance(records[11]['value'], (int, float)):
        yoy_change = latest['value'] - records[11]['value']
    
    # Interpret sentiment (100 = long-term average)
    interpretation = "Neutral"
    if isinstance(latest['value'], (int, float)):
        if latest['value'] > 105:
            interpretation = "Strong positive sentiment"
        elif latest['value'] > 100:
            interpretation = "Positive sentiment"
        elif latest['value'] < 95:
            interpretation = "Weak sentiment"
        elif latest['value'] < 100:
            interpretation = "Below average sentiment"
    
    return {
        'success': True,
        'indicator': 'Economic Sentiment Indicator',
        'geo': geo,
        'latest_value': latest['value'],
        'latest_period': latest['time'],
        'interpretation': interpretation,
        'mom_change': mom_change,
        'yoy_change': yoy_change,
        'records_count': len(records),
        'recent_data': records[:12],
        'timestamp': datetime.now().isoformat()
    }


def get_economic_snapshot(geo: str = "EU") -> Dict[str, Any]:
    """
    Get comprehensive economic snapshot for a region.
    Includes CPI, GDP, unemployment, HICP, and sentiment.
    
    Args:
        geo: Geographic area code (EU, EA, DE, FR, etc.)
    
    Returns:
        Dict with all key economic indicators
    """
    snapshot = {
        'geo': geo,
        'timestamp': datetime.now().isoformat(),
        'indicators': {}
    }
    
    # Fetch all indicators
    indicators = [
        ('cpi', get_eu_cpi),
        ('gdp_growth', get_eu_gdp_growth),
        ('unemployment', get_eu_unemployment),
        ('hicp', get_eu_hicp),
        ('sentiment', get_economic_sentiment),
    ]
    
    for name, func in indicators:
        try:
            result = func(geo=geo)
            snapshot['indicators'][name] = result
        except Exception as e:
            snapshot['indicators'][name] = {
                'success': False,
                'error': str(e)
            }
    
    # Add summary
    successful = sum(1 for v in snapshot['indicators'].values() if v.get('success'))
    snapshot['summary'] = {
        'total_indicators': len(indicators),
        'successful': successful,
        'failed': len(indicators) - successful
    }
    
    return snapshot


def list_available_indicators() -> Dict[str, Any]:
    """
    List all available economic indicators in this module.
    
    Returns:
        Dict with indicator names and dataset codes
    """
    return {
        'success': True,
        'module': 'eurostat_economic_api_update',
        'indicators': [
            {'name': 'Consumer Price Index', 'function': 'get_eu_cpi()', 'dataset': ECONOMIC_DATASETS['CPI']},
            {'name': 'GDP Growth', 'function': 'get_eu_gdp_growth()', 'dataset': ECONOMIC_DATASETS['GDP']},
            {'name': 'Unemployment Rate', 'function': 'get_eu_unemployment()', 'dataset': ECONOMIC_DATASETS['UNEMPLOYMENT']},
            {'name': 'Interest Rates', 'function': 'get_eu_interest_rates()', 'dataset': ECONOMIC_DATASETS['INTEREST']},
            {'name': 'HICP', 'function': 'get_eu_hicp()', 'dataset': ECONOMIC_DATASETS['HICP']},
            {'name': 'Economic Sentiment', 'function': 'get_economic_sentiment()', 'dataset': ECONOMIC_DATASETS['SENTIMENT']},
        ],
        'common_geo_codes': ['EU', 'EA', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'GR', 'IE'],
        'free_tier': True,
        'rate_limit': '1000 queries per day'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Eurostat Economic API Update - 2026")
    print("=" * 70)
    
    # List available indicators
    indicators_info = list_available_indicators()
    print(f"\nAvailable Indicators: {len(indicators_info['indicators'])}")
    for ind in indicators_info['indicators']:
        print(f"  • {ind['name']}: {ind['function']}")
    
    print(f"\nCommon Geographic Codes: {', '.join(indicators_info['common_geo_codes'])}")
    print(f"Free Tier: {indicators_info['free_tier']}")
    print(f"Rate Limit: {indicators_info['rate_limit']}")
    
    print("\n" + json.dumps(indicators_info, indent=2))
