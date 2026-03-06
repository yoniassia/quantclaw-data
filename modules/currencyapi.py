#!/usr/bin/env python3
"""
CurrencyAPI — Real-time FX Rates with Volatility Metrics

CurrencyAPI delivers real-time and historical forex rates for 170+ currencies,
with features for conversion and fluctuation tracking. Optimized for quantitative
analysis, including volatility metrics derived from rate changes.

Source: https://currencyapi.com/
Category: FX & Rates
Free tier: 300 requests/month, no credit card required
Update frequency: Real-time
Built by: NightBuilder
Date: 2026-03-06

Functions:
- get_latest_rates(base='USD', currencies=None) -> dict: Latest FX rates
- get_historical_rates(date, base='USD', currencies=None) -> dict: Historical rates
- convert(amount, from_currency, to_currency) -> dict: Currency conversion
- get_fluctuation(start_date, end_date, base='USD', currencies=None) -> dict: Volatility metrics
- get_supported_currencies() -> dict: All supported currency metadata
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

BASE_URL = "https://api.currencyapi.com/v3"
API_KEY = os.environ.get('CURRENCYAPI_KEY', '')

def _make_request(endpoint: str, params: Dict) -> Dict:
    """Internal helper for API requests."""
    if not API_KEY:
        return {
            'error': 'CURRENCYAPI_KEY environment variable not set',
            'note': 'Get free API key at https://currencyapi.com/signup'
        }
    
    try:
        params['apikey'] = API_KEY
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return {'error': 'Rate limit exceeded (300 req/month on free tier)'}
        return {'error': f'HTTP {e.response.status_code}: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}


def get_latest_rates(base: str = 'USD', currencies: Optional[List[str]] = None) -> Dict:
    """
    Get latest exchange rates for all currencies against a base currency.
    
    Args:
        base: Base currency code (default: USD)
        currencies: Optional list of target currencies (e.g. ['EUR', 'GBP'])
    
    Returns:
        dict: {
            'meta': {'last_updated_at': '2026-03-06T05:30:00Z'},
            'data': {
                'EUR': {'code': 'EUR', 'value': 0.85},
                'GBP': {'code': 'GBP', 'value': 0.73},
                ...
            }
        }
    
    Example:
        >>> rates = get_latest_rates('USD', ['EUR', 'GBP', 'JPY'])
        >>> eur_rate = rates['data']['EUR']['value']
    """
    params = {'base_currency': base.upper()}
    if currencies:
        params['currencies'] = ','.join([c.upper() for c in currencies])
    
    return _make_request('latest', params)


def get_historical_rates(date: str, base: str = 'USD', currencies: Optional[List[str]] = None) -> Dict:
    """
    Get historical exchange rates for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency code (default: USD)
        currencies: Optional list of target currencies
    
    Returns:
        dict: Same structure as get_latest_rates() but for historical date
    
    Example:
        >>> rates = get_historical_rates('2026-01-01', 'USD', ['EUR'])
        >>> eur_rate = rates['data']['EUR']['value']
    """
    params = {
        'date': date,
        'base_currency': base.upper()
    }
    if currencies:
        params['currencies'] = ','.join([c.upper() for c in currencies])
    
    return _make_request('historical', params)


def convert(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        dict: {
            'amount': 100,
            'from': 'USD',
            'to': 'EUR',
            'rate': 0.85,
            'converted': 85.0,
            'timestamp': '2026-03-06T05:30:00Z'
        }
    
    Example:
        >>> result = convert(100, 'USD', 'EUR')
        >>> print(f"100 USD = {result['converted']} EUR")
    """
    rates = get_latest_rates(from_currency, [to_currency])
    
    if 'error' in rates:
        return rates
    
    if 'data' not in rates or to_currency.upper() not in rates['data']:
        return {'error': f'Currency {to_currency} not found'}
    
    rate = rates['data'][to_currency.upper()]['value']
    converted = amount * rate
    
    return {
        'amount': amount,
        'from': from_currency.upper(),
        'to': to_currency.upper(),
        'rate': rate,
        'converted': round(converted, 2),
        'timestamp': rates['meta']['last_updated_at']
    }


def get_fluctuation(start_date: str, end_date: str, base: str = 'USD', currencies: Optional[List[str]] = None) -> Dict:
    """
    Calculate fluctuation/volatility between two dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base: Base currency code (default: USD)
        currencies: Optional list of target currencies
    
    Returns:
        dict: {
            'base': 'USD',
            'period': {'start': '2026-01-01', 'end': '2026-03-06'},
            'fluctuations': {
                'EUR': {
                    'start_rate': 0.85,
                    'end_rate': 0.87,
                    'change': 0.02,
                    'change_pct': 2.35,
                    'min_rate': 0.84,
                    'max_rate': 0.89
                },
                ...
            }
        }
    
    Example:
        >>> fluct = get_fluctuation('2026-01-01', '2026-03-06', 'USD', ['EUR'])
        >>> volatility = fluct['fluctuations']['EUR']['change_pct']
    """
    start_rates = get_historical_rates(start_date, base, currencies)
    end_rates = get_historical_rates(end_date, base, currencies)
    
    if 'error' in start_rates or 'error' in end_rates:
        return start_rates if 'error' in start_rates else end_rates
    
    fluctuations = {}
    
    for currency, end_data in end_rates.get('data', {}).items():
        if currency in start_rates.get('data', {}):
            start_rate = start_rates['data'][currency]['value']
            end_rate = end_data['value']
            change = end_rate - start_rate
            change_pct = (change / start_rate) * 100 if start_rate else 0
            
            fluctuations[currency] = {
                'start_rate': round(start_rate, 6),
                'end_rate': round(end_rate, 6),
                'change': round(change, 6),
                'change_pct': round(change_pct, 2)
            }
    
    return {
        'base': base.upper(),
        'period': {'start': start_date, 'end': end_date},
        'fluctuations': fluctuations
    }


def get_supported_currencies() -> Dict:
    """
    Get metadata for all supported currencies.
    
    Returns:
        dict: {
            'data': {
                'USD': {
                    'symbol': '$',
                    'name': 'US Dollar',
                    'symbol_native': '$',
                    'decimal_digits': 2,
                    'rounding': 0,
                    'code': 'USD',
                    'name_plural': 'US dollars'
                },
                ...
            }
        }
    
    Example:
        >>> currencies = get_supported_currencies()
        >>> usd_symbol = currencies['data']['USD']['symbol']
    """
    return _make_request('currencies', {})


if __name__ == "__main__":
    # Test import and basic functionality
    test_result = {
        'module': 'currencyapi',
        'status': 'ready',
        'source': 'https://currencyapi.com/',
        'api_key_set': bool(API_KEY),
        'functions': [
            'get_latest_rates',
            'get_historical_rates',
            'convert',
            'get_fluctuation',
            'get_supported_currencies'
        ]
    }
    
    if API_KEY:
        # Quick test with real data
        test_rates = get_latest_rates('USD', ['EUR', 'GBP'])
        if 'data' in test_rates:
            test_result['test'] = 'success'
            test_result['sample_rate'] = test_rates['data'].get('EUR', {})
        else:
            test_result['test'] = 'error'
            test_result['error'] = test_rates.get('error')
    else:
        test_result['test'] = 'skipped_no_key'
    
    print(json.dumps(test_result, indent=2))
