#!/usr/bin/env python3

"""
QuantClaw Data: ecb_foreign_exchange_rates

Provides daily euro foreign exchange reference rates against global currencies.

Data Source: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
Update Frequency: Daily
Authentication: None required; public endpoint.
"""

import requests
import os
import json
import time
from pathlib import Path
import xml.etree.ElementTree as ET

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_foreign_exchange_rates')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def parse_xml(xml_content):
    """
    Parse the ECB XML response into a dictionary.

    Returns:
        dict: {'date': str, 'rates': dict of currency: rate} or {'error': str}
    """
    try:
        root = ET.fromstring(xml_content)
        namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01', 'ecb': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        cube_date = root.find('.//ecb:Cube[@time]', namespaces)
        if cube_date is not None:
            date = cube_date.get('time')
            rates = {}
            for currency_cube in cube_date.findall('ecb:Cube', namespaces):
                currency = currency_cube.get('currency')
                rate = float(currency_cube.get('rate'))  # Convert to float for ease of use
                rates[currency] = rate
            return {'date': date, 'rates': rates}
        return {'error': 'No data found in XML'}
    except ET.ParseError as e:
        return {'error': str(e)}

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Fetch data from URL with caching.

    Returns:
        dict: The parsed data or an error dictionary.
    """
    try:
        cache_file = CACHE_DIR / f'{cache_key}.json'
        if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
            return json.loads(cache_file.read_text())
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = parse_xml(resp.text)
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.RequestException as e:
        return {'error': f'HTTP request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_latest_data():
    """
    Fetch the latest ECB foreign exchange data.

    Returns:
        dict: {'date': str, 'rates': dict} or error dictionary.
    """
    return _cached_get('https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml', 'latest')

def get_rates():
    """
    Get the latest exchange rates.

    Returns:
        dict: Dictionary of currency codes to rates or error dictionary.
    """
    data = get_latest_data()
    if 'error' in data:
        return data
    return data.get('rates', {'error': 'Rates not found in data'})

def get_rate(currency):
    """
    Get the exchange rate for a specific currency.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        dict: {'currency': float} or error dictionary.
    """
    rates = get_rates()
    if 'error' in rates:
        return rates
    if currency in rates:
        return {currency: rates[currency]}
    return {'error': f'Currency {currency} not found'}

def list_currencies():
    """
    List all available currencies from the latest rates.

    Returns:
        list: List of currency codes or error dictionary.
    """
    rates = get_rates()
    if 'error' in rates:
        return rates
    return list(rates.keys())

def get_date():
    """
    Get the date of the latest data.

    Returns:
        str: The date string or error dictionary.
    """
    data = get_latest_data()
    if 'error' in data:
        return data
    return data.get('date', {'error': 'Date not found in data'})

def main():
    """
    Demonstrate key functions.
    """
    latest_data = get_latest_data()
    print("Latest data:", latest_data)  # For demo, print the result

    rates = get_rates()
    print("Latest rates:", rates)

    usd_rate = get_rate('USD')
    print("USD rate:", usd_rate)

if __name__ == '__main__':
    main()
