#!/usr/bin/env python3

"""
Module for accessing ECB Euro Foreign Exchange Reference Rates.

Data Source: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
Update Frequency: Daily
Authentication: None (public endpoint)
"""

import requests
import os
import json
import time
from pathlib import Path
import xml.etree.ElementTree as ET

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_fx_rates')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Fetch data from URL and cache it with a TTL.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Key for the cache file.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

    Returns:
        str: The raw response text if successful, or a dict with 'error' key if failed.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())  # Returns the cached XML string
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.text  # Get XML as string
        cache_file.write_text(json.dumps(data, indent=2))  # Cache the XML string
        return data
    except requests.RequestException as e:
        return {'error': str(e)}

def fetch_raw_data():
    """
    Fetch the raw XML data from the ECB endpoint.

    Returns:
        str: The XML string if successful, or a dict with 'error' key if failed.
    """
    url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
    return _cached_get(url, 'latest')

def parse_rates(xml_string):
    """
    Parse the XML string into a dictionary of rates.

    Args:
        xml_string (str): The raw XML string.

    Returns:
        dict: A dictionary with 'date' and 'rates' keys, or a dict with 'error' key if parsing fails.
    """
    try:
        root = ET.fromstring(xml_string)
        date_cube = root.find('.//{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube[@time]')
        if date_cube is not None:
            date = date_cube.attrib['time']
            currency_cubes = date_cube.findall('{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube')
            rates = {cube.attrib['currency']: float(cube.attrib['rate']) for cube in currency_cubes if 'currency' in cube.attrib}
            return {'date': date, 'rates': rates}
        return {'error': 'No data found in XML'}
    except ET.ParseError as e:
        return {'error': str(e)}

def get_latest_rates():
    """
    Get the latest exchange rates.

    Returns:
        dict: A dictionary with 'date' and 'rates' keys if successful, or a dict with 'error' key if failed.
    """
    data = fetch_raw_data()
    if isinstance(data, dict) and 'error' in data:
        return data  # Propagate error
    return parse_rates(data)

def get_rate(currency):
    """
    Get the exchange rate for a specific currency from the latest rates.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        float: The exchange rate if successful, or a dict with 'error' key if failed.
    """
    rates_data = get_latest_rates()
    if isinstance(rates_data, dict) and 'error' in rates_data:
        return rates_data  # Propagate error
    elif 'rates' in rates_data:
        return rates_data['rates'].get(currency.upper(), {'error': f'Currency {currency} not found'})
    return {'error': 'No rates data available'}

def get_available_currencies():
    """
    Get a list of available currencies from the latest rates.

    Returns:
        list: A list of currency codes if successful, or a dict with 'error' key if failed.
    """
    rates_data = get_latest_rates()
    if isinstance(rates_data, dict) and 'error' in rates_data:
        return rates_data  # Propagate error
    elif 'rates' in rates_data:
        return list(rates_data['rates'].keys())
    return {'error': 'No rates data available'}

def main():
    """
    Demonstrate key functions of the module.
    """
    latest_rates = get_latest_rates()
    if 'error' in latest_rates:
        print(f"Error fetching latest rates: {latest_rates['error']}")
    else:
        print(f"Latest rates as of {latest_rates['date']}: {latest_rates['rates']}")
    
    usd_rate = get_rate('USD')
    if 'error' in usd_rate:
        print(f"Error getting USD rate: {usd_rate['error']}")
    else:
        print(f"USD exchange rate: {usd_rate}")
    
    currencies = get_available_currencies()
    if 'error' in currencies:
        print(f"Error getting currencies: {currencies['error']}")
    else:
        print(f"Available currencies: {currencies}")

if __name__ == '__main__':
    main()
