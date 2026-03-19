#!/usr/bin/env python3

"""
Module for CFTC Commitments of Traders data.

Data Source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
Update Frequency: Weekly
Auth Info: Public access; no authentication required.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/cftc_commitments_of_traders')
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

def get_latest_report():
    """
    Fetches the latest Commitments of Traders report.

    Returns:
    dict: The report data as a dictionary, or an error dictionary if failed.
    """
    try:
        return _cached_get('https://www.cftc.gov/api/latest_report.json', 'latest_report')
    except Exception as e:
        return {'error': f'Failed to fetch latest report: {str(e)}'}

def get_report_by_date(date_str):
    """
    Fetches the COT report for a specific date.

    Args:
    date_str (str): Date in YYYY-MM-DD format.

    Returns:
    dict: The report data for the specified date, or an error dictionary.
    """
    try:
        url = f'https://www.cftc.gov/api/report/{date_str}.json'
        return _cached_get(url, f'report_{date_str}')
    except Exception as e:
        return {'error': f'Failed to fetch report for {date_str}: {str(e)}'}

def get_positions_for_contract(contract_code):
    """
    Fetches trader positions for a specific futures contract.

    Args:
    contract_code (str): The contract code (e.g., 'CL' for Crude Oil).

    Returns:
    dict: Positions data as a dictionary, or an error dictionary.
    """
    try:
        url = f'https://www.cftc.gov/api/positions/{contract_code}.json'
        return _cached_get(url, f'positions_{contract_code}')
    except Exception as e:
        return {'error': f'Failed to fetch positions for {contract_code}: {str(e)}'}

def get_trader_categories():
    """
    Fetches available trader categories from COT reports.

    Returns:
    list: A list of trader categories, or an error dictionary.
    """
    try:
        data = _cached_get('https://www.cftc.gov/api/categories.json', 'trader_categories')
        if 'error' in data:
            return data  # Propagate error
        return data.get('categories', [])  # Assuming the response has a 'categories' key
    except Exception as e:
        return {'error': f'Failed to fetch trader categories: {str(e)}'}

def summarize_report(report_data):
    """
    Summarizes key metrics from a COT report.

    Args:
    report_data (dict): The report data dictionary.

    Returns:
    dict: A summarized dictionary of key metrics, or an error dictionary.
    """
    try:
        if 'error' in report_data:
            return report_data  # Propagate error
        summary = {
            'total_open_interest': report_data.get('open_interest', 0),
            'net_positions': report_data.get('net_positions', {}),
            'top_contract': report_data.get('top_contract', 'N/A')
        }
        return summary
    except Exception as e:
        return {'error': f'Failed to summarize report: {str(e)}'}

def main():
    """
    Demonstrates key functions from the module.
    """
    import sys

    print("Demonstrating get_latest_report:")
    latest_report = get_latest_report()
    if 'error' in latest_report:
        print(f"Error: {latest_report['error']}")
    else:
        print(f"Latest report summary: {summarize_report(latest_report)}")

    print("\nDemonstrating get_report_by_date:")
    sample_date = '2023-01-01'  # Example date; adjust as needed
    report_by_date = get_report_by_date(sample_date)
    if 'error' in report_by_date:
        print(f"Error: {report_by_date['error']}")
    else:
        print(f"Report for {sample_date} summary: {summarize_report(report_by_date)}")

    print("\nDemonstrating get_positions_for_contract:")
    sample_contract = 'CL'  # Example for Crude Oil
    positions = get_positions_for_contract(sample_contract)
    if 'error' in positions:
        print(f"Error: {positions['error']}")
    else:
        print(f"Positions for {sample_contract}: {positions}")

if __name__ == '__main__':
    main()
