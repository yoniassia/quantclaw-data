#!/usr/bin/env python3

"""
QuantClaw Data: ecb_exchange_rates

Fetches daily reference exchange rates for the euro against global currencies.

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

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_exchange_rates')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def get_full_data():
    """Fetches and parses the full exchange rates data from the ECB.

    Returns:
        dict: A dictionary containing 'date' (str) and 'rates' (dict of currency: rate).
              If an error occurs, returns {'error': str}.
    """
    cache_key = 'eurofxref-daily'
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    
    try:
        resp = requests.get('https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml', timeout=15)
        resp.raise_for_status()
        NS = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01', 'eurofxref': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        root = ET.fromstring(resp.content)
        date_cube = root.find('.//eurofxref:Cube[@time]', namespaces=NS)
        if date_cube is not None:
            data = {'date': date_cube.get('time'), 'rates': {}}
            for currency_cube in date_cube.findall('eurofxref:Cube', namespaces=NS):
                currency = currency_cube.get('currency')
                rate = currency_cube.get('rate')
                if currency and rate:
                    data['rates'][currency] = float(rate)
            cache_file.write_text(json.dumps(data, indent=2))
            return data
        else:
            return {'error': 'No data found in XML'}
    except requests.RequestException as e:
        return {'error': str(e)}
    except ET.ParseError as e:
        return {'error': 'XML parsing error: ' + str(e)}

def get_rate(currency):
    """Get the exchange rate for a specific currency.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        float or None: The exchange rate if available, None if not found or error.
    """
    data = get_full_data()
    if 'error' in data:
        return None
    return data.get('rates', {}).get(currency.upper(), None)

def get_date():
    """Get the date of the latest exchange rates.

    Returns:
        str or None: The date string if available, None if error.
    """
    data = get_full_data()
    if 'error' in data:
        return None
    return data.get('date')

def list_currencies():
    """List all currencies in the exchange rates.

    Returns:
        list: A list of currency codes (str), or an empty list if error.
    """
    data = get_full_data()
    if 'error' in data:
        return []
    return list(data.get('rates', {}).keys())

def is_data_fresh():
    """Check if the cached data is fresh.

    Returns:
        bool: True if the cache exists and is within TTL, False otherwise.
    """
    cache_key = 'eurofxref-daily'
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return True
    return False

def main():
    """Demonstrate key functions."""
    full_data = get_full_data()
    rate_usd = get_rate('USD')
    latest_date = get_date()
    currencies_list = list_currencies()
    
    return {
        'full_data': full_data,
        'rate_for_USD': rate_usd,
        'latest_date': latest_date,
        'currencies_list': currencies_list
    }

if __name__ == '__main__':
    result = main()
    # For demonstration, we return a dict; in practice, you might print it
    print(result)  # This is for demo purposes in main()
