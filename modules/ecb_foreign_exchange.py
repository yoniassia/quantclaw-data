#!/usr/bin/env python3

"""
QuantClaw Data: ecb_foreign_exchange

Fetches daily euro foreign exchange reference rates against global currencies for forex analysis.

Data Source: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
Update Frequency: Daily
Authentication: None required; public endpoint.
"""

import requests
import json
import time
from pathlib import Path
import xml.etree.ElementTree as ET

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_foreign_exchange')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def parse_ecb_xml(tree):
    """
    Parses the ECB XML response into a dictionary.

    Args:
        tree (xml.etree.ElementTree.Element): The root element of the parsed XML.

    Returns:
        dict: A dictionary containing 'date' and 'rates' keys, or {'error': 'message'} on failure.
    """
    try:
        namespace = {'eurofxref': 'http://www.ecb.int/vocabulary/stats/eurofxref/1.0'}
        for cube in tree.findall('.//eurofxref:Cube[@time]', namespaces=namespace):
            date = cube.get('time')
            rates = {}
            for subcube in cube.findall('eurofxref:Cube', namespaces=namespace):
                currency = subcube.get('currency')
                rate = subcube.get('rate')
                if currency and rate:
                    rates[currency] = rate
            return {'date': date, 'rates': rates}
        return {'error': 'No data found in XML'}
    except Exception as e:
        return {'error': str(e)}

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Fetches data from the URL, caches it, and returns the parsed data.

    Args:
        url (str): The URL to fetch.
        cache_key (str): The key for caching.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

    Returns:
        dict: The parsed data or an error dictionary.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        tree = ET.fromstring(resp.content)
        data = parse_ecb_xml(tree)
        if 'error' in data:
            return data  # Propagate parsing error
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.RequestException as e:
        return {'error': str(e)}

def get_latest_rates():
    """
    Fetches the latest euro foreign exchange reference rates.

    Returns:
        dict: A dictionary with 'date' and 'rates' keys, or an error dictionary.
    """
    url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
    return _cached_get(url, 'latest')

def get_rate_for_currency(currency):
    """
    Gets the exchange rate for a specific currency from the latest rates.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        dict: A dictionary with 'currency', 'rate', and 'date', or an error dictionary.
    """
    rates_data = get_latest_rates()
    if 'error' in rates_data:
        return rates_data
    if currency in rates_data.get('rates', {}):
        return {
            'currency': currency,
            'rate': rates_data['rates'][currency],
            'date': rates_data['date']
        }
    return {'error': f'Currency {currency} not found'}

def get_available_currencies():
    """
    Gets a list of available currencies from the latest rates.

    Returns:
        list: A list of currency codes, or an error dictionary.
    """
    rates_data = get_latest_rates()
    if 'error' in rates_data:
        return rates_data
    return list(rates_data.get('rates', {}).keys())

def get_last_update_date():
    """
    Gets the date of the latest rates.

    Returns:
        str: The date string, or an error dictionary.
    """
    rates_data = get_latest_rates()
    if 'error' in rates_data:
        return rates_data
    return rates_data['date']

def main():
    """
    Demonstrates key functions of the module.
    """
    latest_rates = get_latest_rates()
    print(latest_rates)  # Output: dict with rates or error

    usd_rate = get_rate_for_currency('USD')
    print(usd_rate)  # Output: dict with USD rate or error

    currencies = get_available_currencies()
    print(currencies)  # Output: list of currencies or error

if __name__ == '__main__':
    main()
