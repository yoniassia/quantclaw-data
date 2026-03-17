#!/usr/bin/env python3

"""
QuantClaw Data: 'exchangeratesapi_fx_rates'

Purpose: Offers current and historical foreign exchange rates based on ECB data for major currency pairs.

Data Source URL: https://api.exchangeratesapi.io/v1/

Update frequency: Daily (based on ECB data updates)

Auth info: Requires a free API access key from exchangeratesapi.io; use the free tier only.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/exchangeratesapi_fx_rates')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
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
        return {'error': str(e)}

def get_latest_rates(base='EUR', api_key='YOUR_FREE_API_KEY'):
    """
    Retrieve the latest foreign exchange rates for a given base currency.

    Args:
        base (str): The base currency (e.g., 'EUR').
        api_key (str): The free API access key.

    Returns:
        dict: A dictionary containing the rates or an error message.
    """
    url = f"https://api.exchangeratesapi.io/v1/latest?access_key={api_key}&base={base}"
    cache_key = f"latest_{base}"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': str(e)}

def get_historical_rates(date, base='EUR', api_key='YOUR_FREE_API_KEY'):
    """
    Retrieve historical foreign exchange rates for a specific date and base currency.

    Args:
        date (str): The date in YYYY-MM-DD format (e.g., '2023-01-01').
        base (str): The base currency (e.g., 'EUR').
        api_key (str): The free API access key.

    Returns:
        dict: A dictionary containing the rates or an error message.
    """
    url = f"https://api.exchangeratesapi.io/v1/{date}?access_key={api_key}&base={base}"
    cache_key = f"historical_{date}_{base}"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': str(e)}

def get_available_currencies(api_key='YOUR_FREE_API_KEY'):
    """
    Retrieve a list of available currencies based on the latest rates.

    Args:
        api_key (str): The free API access key.

    Returns:
        list: A list of currency codes or an error dictionary.
    """
    try:
        latest_data = get_latest_rates(api_key=api_key)
        if 'error' in latest_data:
            return latest_data  # Return error dict
        rates = latest_data.get('rates', {})
        currencies = list(rates.keys())  # Currencies from rates
        return currencies  # Returns a list
    except Exception as e:
        return {'error': str(e)}

def convert_amount(amount, from_currency, to_currency, date=None, api_key='YOUR_FREE_API_KEY'):
    """
    Convert an amount from one currency to another using the latest or historical rates.

    Args:
        amount (float): The amount to convert.
        from_currency (str): The source currency (e.g., 'EUR').
        to_currency (str): The target currency (e.g., 'USD').
        date (str, optional): The date for historical rates (e.g., '2023-01-01').
        api_key (str): The free API access key.

    Returns:
        dict: A dictionary with the converted amount or an error message.
    """
    try:
        if date:
            rates_data = get_historical_rates(date, from_currency, api_key)
        else:
            rates_data = get_latest_rates(from_currency, api_key)
        
        if 'error' in rates_data:
            return rates_data  # Return error dict
        
        rates = rates_data.get('rates', {})
        if to_currency in rates:
            converted = amount * rates[to_currency]
            return {'converted_amount': converted, 'from_currency': from_currency, 'to_currency': to_currency, 'date': date or 'latest'}
        else:
            return {'error': f"Rate for {to_currency} not found"}
    except Exception as e:
        return {'error': str(e)}

def get_specific_rate(base, symbols, date=None, api_key='YOUR_FREE_API_KEY'):
    """
    Retrieve the rate for specific currency symbols from a base currency.

    Args:
        base (str): The base currency (e.g., 'EUR').
        symbols (str): Comma-separated symbols (e.g., 'USD,GBP').
        date (str, optional): The date for historical rates (e.g., '2023-01-01').
        api_key (str): The free API access key.

    Returns:
        dict: A dictionary containing the specific rates or an error message.
    """
    try:
        if date:
            rates_data = get_historical_rates(date, base, api_key)
        else:
            rates_data = get_latest_rates(base, api_key)
        
        if 'error' in rates_data:
            return rates_data  # Return error dict
        
        rates = rates_data.get('rates', {})
        specific_rates = {symbol: rates.get(symbol) for symbol in symbols.split(',')}
        return specific_rates  # Returns a dict of specific rates
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrate key functions of the module.
    """
    # Demo 1: Get latest rates
    latest_rates = get_latest_rates(base='EUR')
    print(latest_rates)  # Output: dict of rates or error
    
    # Demo 2: Get historical rates
    historical_rates = get_historical_rates('2023-01-01', base='EUR')
    print(historical_rates)  # Output: dict of rates or error
    
    # Demo 3: Convert amount
    conversion_result = convert_amount(100, 'EUR', 'USD')
    print(conversion_result)  # Output: dict with converted amount or error

if __name__ == '__main__':
    main()
