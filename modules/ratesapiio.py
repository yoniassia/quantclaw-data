#!/usr/bin/env python3
"""
RatesAPI.io / Frankfurter Exchange Rates Module

Free forex exchange rates with historical data
- Latest currency exchange rates
- Historical rates by date
- Time series data
- 30+ currencies supported

Data Sources:
- api.frankfurter.app (primary - free, no API key)
- ratesapi.io (fallback - if available)

Refresh: Real-time for spot rates
Coverage: Global forex markets

Author: QUANTCLAW DATA Build Agent - NightBuilder
Built: 2026-03-07
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# API Configuration - Frankfurter as primary (free, no key needed)
PRIMARY_BASE_URL = "https://api.frankfurter.app"
FALLBACK_BASE_URL = "https://api.ratesapi.io/api"

# Default timeout for requests
REQUEST_TIMEOUT = 10


def _make_request(endpoint: str, params: Optional[Dict] = None, use_fallback: bool = False) -> Dict:
    """
    Make HTTP request to exchange rate API with automatic fallback
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        use_fallback: If True, try fallback API first
        
    Returns:
        dict: API response data
        
    Raises:
        Exception: If both primary and fallback APIs fail
    """
    base_url = FALLBACK_BASE_URL if use_fallback else PRIMARY_BASE_URL
    
    try:
        url = f"{base_url}/{endpoint}"
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Try the other API if first one fails
        if not use_fallback:
            try:
                return _make_request(endpoint, params, use_fallback=True)
            except:
                pass
        raise Exception(f"Failed to fetch data from both APIs: {str(e)}")


def get_latest_rates(base: str = 'USD', symbols: Optional[List[str]] = None) -> Dict:
    """
    Get latest exchange rates for a base currency
    
    Args:
        base: Base currency code (e.g., 'USD', 'EUR')
        symbols: List of target currency codes (e.g., ['EUR', 'GBP'])
                If None, returns all available currencies
        
    Returns:
        dict: {
            'base': str,
            'date': str (YYYY-MM-DD),
            'rates': {currency: rate, ...}
        }
        
    Example:
        >>> rates = get_latest_rates('USD', ['EUR', 'GBP'])
        >>> rates['rates']['EUR']
        0.92
    """
    try:
        params = {'from': base}
        
        if symbols:
            params['to'] = ','.join(symbols)
        
        data = _make_request('latest', params)
        
        return {
            'base': data.get('base', base),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'rates': data.get('rates', {})
        }
    except Exception as e:
        raise Exception(f"Error fetching latest rates: {str(e)}")


def get_historical_rates(date: str, base: str = 'USD', symbols: Optional[List[str]] = None) -> Dict:
    """
    Get historical exchange rates for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency code
        symbols: List of target currency codes (optional)
        
    Returns:
        dict: {
            'base': str,
            'date': str,
            'rates': {currency: rate, ...}
        }
        
    Example:
        >>> rates = get_historical_rates('2024-01-15', 'USD', ['EUR'])
        >>> rates['rates']['EUR']
        0.91
    """
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        
        params = {'from': base}
        
        if symbols:
            params['to'] = ','.join(symbols)
        
        data = _make_request(date, params)
        
        return {
            'base': data.get('base', base),
            'date': data.get('date', date),
            'rates': data.get('rates', {})
        }
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    except Exception as e:
        raise Exception(f"Error fetching historical rates: {str(e)}")


def get_rate_timeseries(start_date: str, end_date: str, base: str = 'USD', 
                        symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Get exchange rate time series between two dates
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base: Base currency code
        symbols: List of target currency codes (optional)
        
    Returns:
        list: [{
            'date': str,
            'base': str,
            'rates': {currency: rate, ...}
        }, ...]
        
    Example:
        >>> series = get_rate_timeseries('2024-01-01', '2024-01-07', 'USD', ['EUR'])
        >>> len(series)
        7
    """
    try:
        # Validate dates
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
        
        params = {'from': base}
        
        if symbols:
            params['to'] = ','.join(symbols)
        
        # Frankfurter uses format: /start_date..end_date
        endpoint = f"{start_date}..{end_date}"
        data = _make_request(endpoint, params)
        
        # Convert to list of daily records
        result = []
        rates_data = data.get('rates', {})
        
        for date_str, rates in rates_data.items():
            result.append({
                'date': date_str,
                'base': data.get('base', base),
                'rates': rates
            })
        
        # Sort by date
        result.sort(key=lambda x: x['date'])
        
        return result
    except ValueError:
        raise ValueError("Dates must be in YYYY-MM-DD format")
    except Exception as e:
        raise Exception(f"Error fetching timeseries data: {str(e)}")


def get_supported_currencies() -> List[str]:
    """
    Get list of all supported currency codes
    
    Returns:
        list: List of currency codes (e.g., ['USD', 'EUR', 'GBP', ...])
        
    Example:
        >>> currencies = get_supported_currencies()
        >>> 'USD' in currencies
        True
    """
    try:
        data = _make_request('currencies')
        
        # Frankfurter returns {code: name, ...}
        if isinstance(data, dict):
            return sorted(list(data.keys()))
        
        return []
    except Exception as e:
        raise Exception(f"Error fetching supported currencies: {str(e)}")


def get_currency_info() -> Dict[str, str]:
    """
    Get detailed information about all supported currencies
    
    Returns:
        dict: {currency_code: currency_name, ...}
        
    Example:
        >>> info = get_currency_info()
        >>> info['USD']
        'United States Dollar'
    """
    try:
        data = _make_request('currencies')
        return data if isinstance(data, dict) else {}
    except Exception as e:
        raise Exception(f"Error fetching currency info: {str(e)}")


if __name__ == "__main__":
    # Test module functionality
    print("Testing ratesapiio module...")
    
    try:
        # Test 1: Latest rates
        latest = get_latest_rates('USD', ['EUR', 'GBP'])
        print(f"\n✓ Latest rates: {json.dumps(latest, indent=2)}")
        
        # Test 2: Supported currencies
        currencies = get_supported_currencies()
        print(f"\n✓ Supported currencies ({len(currencies)}): {', '.join(currencies[:10])}...")
        
        # Test 3: Historical rate
        historical = get_historical_rates('2024-01-15', 'USD', ['EUR'])
        print(f"\n✓ Historical rate: {json.dumps(historical, indent=2)}")
        
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)
