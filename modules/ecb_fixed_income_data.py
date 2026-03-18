#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_fixed_income_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

"""
ECB Fixed Income Data Module

PURPOSE: Accesses Eurozone interest rates, bond yields, and monetary policy indicators

Data Source URL: https://sdw-wsrest.ecb.europa.eu/

Update Frequency: Data is updated daily by the ECB.

Auth Info: No authentication required for public endpoints.
"""

def get_main_refinancing_rate():
    """Fetches the Main Refinancing Operations rate from the ECB API.

    Returns:
        dict: The JSON response containing the rate data, or an error dictionary if the request fails.
    """
    url = "https://sdw-wsrest.ecb.europa.eu/service/data/ERT/MNA/"
    cache_key = "main_refinancing_rate"
    try:
        data = _cached_get(url, cache_key)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_deposit_facility_rate():
    """Fetches the Deposit Facility rate from the ECB API.

    Returns:
        dict: The JSON response containing the rate data, or an error dictionary if the request fails.
    """
    url = "https://sdw-wsrest.ecb.europa.eu/service/data/ERT/DFR/"
    cache_key = "deposit_facility_rate"
    try:
        data = _cached_get(url, cache_key)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_marginal_lending_facility_rate():
    """Fetches the Marginal Lending Facility rate from the ECB API.

    Returns:
        dict: The JSON response containing the rate data, or an error dictionary if the request fails.
    """
    url = "https://sdw-wsrest.ecb.europa.eu/service/data/ERT/MLFR/"
    cache_key = "marginal_lending_facility_rate"
    try:
        data = _cached_get(url, cache_key)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_10_year_bond_yield():
    """Fetches the 10-year government bond yield for the Eurozone from the ECB API.

    Returns:
        dict: The JSON response containing the yield data, or an error dictionary if the request fails.
    """
    url = "https://sdw-wsrest.ecb.europa.eu/service/data/IRST/M.NA.A2XX.WT00/"
    cache_key = "10_year_bond_yield"
    try:
        data = _cached_get(url, cache_key)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_eonia_rate():
    """Fetches the EONIA (Euro Overnight Index Average) rate from the ECB API.

    Returns:
        dict: The JSON response containing the rate data, or an error dictionary if the request fails.
    """
    url = "https://sdw-wsrest.ecb.europa.eu/service/data/ERT/EONIA/"
    cache_key = "eonia_rate"
    try:
        data = _cached_get(url, cache_key)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    """Demonstrates key functions from the module."""
    # Demo get_main_refinancing_rate
    mro_rate = get_main_refinancing_rate()
    if "error" in mro_rate:
        print("Error fetching Main Refinancing Rate:", mro_rate["error"])
    else:
        print("Main Refinancing Rate data:", mro_rate)  # In practice, process the dict further
    
    # Demo get_10_year_bond_yield
    bond_yield = get_10_year_bond_yield()
    if "error" in bond_yield:
        print("Error fetching 10-Year Bond Yield:", bond_yield["error"])
    else:
        print("10-Year Bond Yield data:", bond_yield)  # In practice, process the dict further
    
    # Demo get_eonia_rate
    eonia_rate = get_eonia_rate()
    if "error" in eonia_rate:
        print("Error fetching EONIA Rate:", eonia_rate["error"])
    else:
        print("EONIA Rate data:", eonia_rate)  # In practice, process the dict further

if __name__ == "__main__":
    main()
