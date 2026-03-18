#!/usr/bin/env python3

"""
QuantClaw Data Module: fixer_fx_rates

Purpose: Offers current and historical foreign exchange rates based on EUR.

Data Source: https://data.fixer.io/api
Update Frequency: Real-time via API, with responses cached for 1 hour.
Auth Info: Requires a free API key from Fixer.io. Set the API_KEY variable with your free access key.

"""

import requests
import os
import json
import time
from pathlib import Path

# Constants
API_KEY = 'your_free_api_key_here'  # Replace with your actual free API key from Fixer.io
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fixer_fx_rates')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Key for the cache file.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

    Returns:
        dict: The JSON response data.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

def get_latest_rates():
    """
    Retrieve the latest foreign exchange rates based on EUR.

    Returns:
        dict: The API response containing rates, or an error dictionary.
    """
    url = 'https://data.fixer.io/api/latest'
    params = {'access_key': API_KEY}
    try:
        data = _cached_get(url, 'latest', params=params)
        return data
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch latest rates: {str(e)}'}

def get_historical_rates(date):
    """
    Retrieve historical foreign exchange rates for a specific date based on EUR.

    Args:
        date (str): The date in YYYY-MM-DD format.

    Returns:
        dict: The API response containing rates for the date, or an error dictionary.
    """
    url = f'https://data.fixer.io/api/{date}'
    params = {'access_key': API_KEY}
    try:
        data = _cached_get(url, f'historical_{date}', params=params)
        return data
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch historical rates for {date}: {str(e)}'}

def convert_eur_to_currency(amount, currency, date=None):
    """
    Convert an amount from EUR to another currency using the latest or historical rates.

    Args:
        amount (float): The amount in EUR to convert.
        currency (str): The target currency code (e.g., 'USD').
        date (str, optional): The date in YYYY-MM-DD format for historical rates.

    Returns:
        dict: A dictionary with the converted amount, or an error dictionary.
    """
    if date:
        rates_data = get_historical_rates(date)
    else:
        rates_data = get_latest_rates()
    
    if 'error' in rates_data:
        return rates_data  # Propagate error
    if 'rates' in rates_data and currency in rates_data['rates']:
        rate = rates_data['rates'][currency]
        converted_amount = amount * rate
        return {'from': 'EUR', 'to': currency, 'amount': amount, 'converted_amount': converted_amount, 'rate': rate, 'date': rates_data.get('date', 'latest')}
    return {'error': f'Currency {currency} not found in rates'}

def convert_currency_to_eur(amount, currency, date=None):
    """
    Convert an amount from another currency to EUR using the latest or historical rates.

    Args:
        amount (float): The amount in the source currency to convert.
        currency (str): The source currency code (e.g., 'USD').
        date (str, optional): The date in YYYY-MM-DD format for historical rates.

    Returns:
        dict: A dictionary with the converted amount, or an error dictionary.
    """
    if date:
        rates_data = get_historical_rates(date)
    else:
        rates_data = get_latest_rates()
    
    if 'error' in rates_data:
        return rates_data  # Propagate error
    if 'rates' in rates_data and currency in rates_data['rates']:
        rate = rates_data['rates'][currency]
        converted_amount = amount / rate  # Invert the rate
        return {'from': currency, 'to': 'EUR', 'amount': amount, 'converted_amount': converted_amount, 'rate': rate, 'date': rates_data.get('date', 'latest')}
    return {'error': f'Currency {currency} not found in rates'}

def get_available_currencies():
    """
    Retrieve a list of available currencies from the latest rates.

    Returns:
        list: A list of currency codes, or an error dictionary.
    """
    rates_data = get_latest_rates()
    if 'error' in rates_data:
        return rates_data  # Propagate error
    if 'rates' in rates_data:
        currencies = list(rates_data['rates'].keys())  # Includes base EUR
        return currencies
    return {'error': 'Rates not available in response'}

def main():
    """
    Demonstrate key functions.
    """
    print("Demo of get_latest_rates:")
    latest_rates = get_latest_rates()
    if 'error' in latest_rates:
        print(latest_rates['error'])
    else:
        print(f"Latest USD rate: {latest_rates.get('rates', {}).get('USD', 'N/A')}")
    
    print("\nDemo of get_historical_rates for 2023-01-01:")
    historical_rates = get_historical_rates('2023-01-01')
    if 'error' in historical_rates:
        print(historical_rates['error'])
    else:
        print(f"Historical USD rate on 2023-01-01: {historical_rates.get('rates', {}).get('USD', 'N/A')}")
    
    print("\nDemo of convert_eur_to_currency: 100 EUR to USD")
    conversion_result = convert_eur_to_currency(100, 'USD')
    if 'error' in conversion_result:
        print(conversion_result['error'])
    else:
        print(f"Converted amount: {conversion_result['converted_amount']}")

if __name__ == '__main__':
    main()
