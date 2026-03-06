#!/usr/bin/env python3
"""
ExchangeRate-API (exchangerate.host alternative) — Free FX Rates Module

Provides real-time and historical foreign exchange rates for 160+ currencies
using the free ExchangeRate-API service (open.er-api.com).

Source: https://www.exchangerate-api.com/docs/free
Category: FX & Rates
Free tier: Completely free, no API key needed, 1500 requests/month
Update frequency: Daily (24-hour cache)
Built by: NightBuilder
Date: 2026-03-05

Functions:
- get_latest_rates(base='USD') -> dict: Latest FX rates
- convert(amount, from_currency, to_currency) -> dict: Currency conversion
- get_supported_currencies() -> list: All supported currency codes
- get_pair_rate(base, target) -> dict: Single currency pair rate
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Union

BASE_URL = "https://open.er-api.com/v6"

def get_latest_rates(base: str = 'USD') -> Dict:
    """
    Get latest exchange rates for all currencies against a base currency.
    
    Args:
        base: Base currency code (default: USD)
    
    Returns:
        dict: {
            'base': 'USD',
            'date': '2026-03-05',
            'rates': {'EUR': 0.85, 'GBP': 0.73, ...},
            'timestamp': 1772668951
        }
    
    Example:
        >>> rates = get_latest_rates('USD')
        >>> eur_rate = rates['rates']['EUR']
    """
    try:
        url = f"{BASE_URL}/latest/{base.upper()}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('result') != 'success':
            raise ValueError(f"API error: {data}")
        
        return {
            'base': data['base_code'],
            'date': datetime.utcfromtimestamp(data['time_last_update_unix']).strftime('%Y-%m-%d'),
            'rates': data['rates'],
            'timestamp': data['time_last_update_unix'],
            'provider': 'exchangerate-api.com'
        }
        
    except Exception as e:
        return {'error': str(e), 'base': base, 'rates': {}}


def convert(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        dict: {
            'from': 'USD',
            'to': 'EUR',
            'amount': 100,
            'result': 85.23,
            'rate': 0.8523,
            'date': '2026-03-05'
        }
    
    Example:
        >>> result = convert(100, 'USD', 'EUR')
        >>> print(f"100 USD = {result['result']:.2f} EUR")
    """
    try:
        rates_data = get_latest_rates(from_currency)
        
        if 'error' in rates_data:
            return {'error': rates_data['error']}
        
        rate = rates_data['rates'].get(to_currency.upper())
        
        if not rate:
            return {'error': f'Currency {to_currency} not found'}
        
        result = amount * rate
        
        return {
            'from': from_currency.upper(),
            'to': to_currency.upper(),
            'amount': amount,
            'result': round(result, 4),
            'rate': rate,
            'date': rates_data['date'],
            'provider': 'exchangerate-api.com'
        }
        
    except Exception as e:
        return {'error': str(e)}


def get_pair_rate(base: str, target: str) -> Dict:
    """
    Get exchange rate for a specific currency pair.
    
    Args:
        base: Base currency code
        target: Target currency code
    
    Returns:
        dict: {
            'pair': 'USD/EUR',
            'rate': 0.8523,
            'inverse_rate': 1.1732,
            'date': '2026-03-05'
        }
    
    Example:
        >>> rate = get_pair_rate('USD', 'EUR')
        >>> print(f"1 USD = {rate['rate']} EUR")
    """
    try:
        rates_data = get_latest_rates(base)
        
        if 'error' in rates_data:
            return {'error': rates_data['error']}
        
        rate = rates_data['rates'].get(target.upper())
        
        if not rate:
            return {'error': f'Currency {target} not found'}
        
        return {
            'pair': f"{base.upper()}/{target.upper()}",
            'rate': rate,
            'inverse_rate': round(1 / rate, 6),
            'date': rates_data['date'],
            'timestamp': rates_data['timestamp'],
            'provider': 'exchangerate-api.com'
        }
        
    except Exception as e:
        return {'error': str(e)}


def get_supported_currencies() -> List[str]:
    """
    Get list of all supported currency codes.
    
    Returns:
        list: ['USD', 'EUR', 'GBP', 'JPY', ...]
    
    Example:
        >>> currencies = get_supported_currencies()
        >>> print(f"Supports {len(currencies)} currencies")
    """
    try:
        rates_data = get_latest_rates('USD')
        
        if 'error' in rates_data:
            return []
        
        return sorted(rates_data['rates'].keys())
        
    except Exception as e:
        return []


def get_major_pairs() -> Dict:
    """
    Get current rates for major currency pairs vs USD.
    
    Returns:
        dict: {
            'USD/EUR': 0.8523,
            'USD/GBP': 0.7301,
            'USD/JPY': 110.52,
            'USD/CHF': 0.9234,
            'USD/CAD': 1.2567,
            'USD/AUD': 1.3421,
            'USD/NZD': 1.4123
        }
    """
    major_currencies = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
    
    try:
        rates_data = get_latest_rates('USD')
        
        if 'error' in rates_data:
            return {'error': rates_data['error']}
        
        major_rates = {}
        for currency in major_currencies:
            rate = rates_data['rates'].get(currency)
            if rate:
                major_rates[f'USD/{currency}'] = rate
        
        major_rates['date'] = rates_data['date']
        major_rates['provider'] = 'exchangerate-api.com'
        
        return major_rates
        
    except Exception as e:
        return {'error': str(e)}


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default: show major pairs
        print(json.dumps(get_major_pairs(), indent=2))
    elif sys.argv[1] == 'convert' and len(sys.argv) == 5:
        # Usage: python exchangerate_host.py convert 100 USD EUR
        amount = float(sys.argv[2])
        from_curr = sys.argv[3]
        to_curr = sys.argv[4]
        print(json.dumps(convert(amount, from_curr, to_curr), indent=2))
    elif sys.argv[1] == 'rate' and len(sys.argv) == 4:
        # Usage: python exchangerate_host.py rate USD EUR
        base = sys.argv[2]
        target = sys.argv[3]
        print(json.dumps(get_pair_rate(base, target), indent=2))
    elif sys.argv[1] == 'latest':
        # Usage: python exchangerate_host.py latest [BASE]
        base = sys.argv[2] if len(sys.argv) > 2 else 'USD'
        print(json.dumps(get_latest_rates(base), indent=2))
    elif sys.argv[1] == 'currencies':
        currencies = get_supported_currencies()
        print(json.dumps({'currencies': currencies, 'count': len(currencies)}, indent=2))
    else:
        print(json.dumps({
            'module': 'exchangerate_host',
            'usage': {
                'latest': 'python exchangerate_host.py latest [BASE]',
                'convert': 'python exchangerate_host.py convert AMOUNT FROM TO',
                'rate': 'python exchangerate_host.py rate BASE TARGET',
                'currencies': 'python exchangerate_host.py currencies',
                'major': 'python exchangerate_host.py (default)'
            },
            'source': 'https://www.exchangerate-api.com/docs/free'
        }, indent=2))
