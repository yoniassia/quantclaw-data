#!/usr/bin/env python3

"""
QuantClaw Data Module: exchangeratesapi_fx

Purpose: Offers current and historical foreign exchange rates for forex market monitoring.

Data Source: https://api.exchangeratesapi.io/

Update Frequency: Real-time via API, but responses are cached for 1 hour in this module.

Auth Info: No authentication required for the free tier; uses public endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/exchangeratesapi_fx')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to get data with caching."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        raise  # Let the caller handle it

def get_latest_rates(base='EUR'):
    """Fetch the latest foreign exchange rates for the given base currency.

    Args:
        base (str): The base currency (e.g., 'USD'). Default: 'EUR'

    Returns:
        dict: The API response containing rates, or an error dictionary.
    """
    url = 'https://api.exchangeratesapi.io/latest'
    cache_key = f'latest_{base}'
    try:
        data = _cached_get(url, cache_key, params={'base': base})
        return data
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_historical_rates(date, base='EUR'):
    """Fetch historical foreign exchange rates for the specified date and base currency.

    Args:
        date (str): The date in YYYY-MM-DD format.
        base (str): The base currency. Default: 'EUR'

    Returns:
        dict: The API response containing rates, or an error dictionary.
    """
    url = f'https://api.exchangeratesapi.io/{date}'
    cache_key = f'historical_{date}_{base}'
    try:
        data = _cached_get(url, cache_key, params={'base': base})
        return data
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_specific_rates(base='EUR', symbols=None):
    """Fetch the latest rates for specific symbols.

    Args:
        base (str): The base currency. Default: 'EUR'
        symbols (str or list): Comma-separated string or list of symbols (e.g., 'USD,GBP').

    Returns:
        dict: The API response with specified symbols, or an error dictionary.
    """
    url = 'https://api.exchangeratesapi.io/latest'
    params = {'base': base}
    if symbols:
        if isinstance(symbols, list):
            symbols = ','.join(symbols)
        params['symbols'] = symbols
    cache_key = f'latest_{base}_{symbols}' if symbols else f'latest_{base}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_exchange_rate(base, target):
    """Get the current exchange rate from base to target currency.

    Args:
        base (str): The base currency.
        target (str): The target currency.

    Returns:
        float: The exchange rate, or an error dictionary.
    """
    rates_data = get_latest_rates(base)
    if 'error' in rates_data:
        return rates_data
    if 'rates' in rates_data and target in rates_data['rates']:
        return rates_data['rates'][target]
    return {'error': f'Rate for {target} not found'}

def convert_currency(amount, from_currency, to_currency):
    """Convert an amount from one currency to another using latest rates.

    Args:
        amount (float): The amount to convert.
        from_currency (str): The source currency.
        to_currency (str): The target currency.

    Returns:
        float: The converted amount, or an error dictionary.
    """
    if from_currency == to_currency:
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    if isinstance(rate, float):
        return amount * rate
    return rate  # This will be the error dictionary

def main():
    """Demonstrate key functions of the module."""
    latest_rates = get_latest_rates(base='USD')
    print("Latest rates for USD base:", latest_rates)

    historical_rates = get_historical_rates('2023-01-01', base='EUR')
    print("Historical rates for 2023-01-01 with EUR base:", historical_rates)

    conversion_result = convert_currency(100, 'USD', 'EUR')
    print("Conversion of 100 USD to EUR:", conversion_result)

if __name__ == '__main__':
    main()
