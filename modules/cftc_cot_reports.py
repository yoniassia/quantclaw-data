#!/usr/bin/env python3
"""
QuantClaw Data Module: cftc_cot_reports

PURPOSE: Fetches Commitment of Traders reports for futures and options market positions.

Data Source: https://www.cftc.gov/dea
Update Frequency: Weekly
Authentication: None required; public data available via free endpoints.

CATEGORY: derivatives
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/cftc_cot_reports')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a cached GET request.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching the response.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

    Returns:
        dict: The JSON response data.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.RequestException as e:
        return {'error': str(e)}

def fetch_latest_cot_report():
    """
    Fetches the latest Commitment of Traders report.

    Returns:
        dict: The report data as a dictionary, or an error dictionary.
    """
    try:
        url = 'https://www.cftc.gov/dea/futures/api/latest'  # Example endpoint; adjust based on actual API
        return _cached_get(url, 'latest_cot_report')
    except Exception as e:
        return {'error': str(e)}

def fetch_cot_report_by_date(report_date):
    """
    Fetches a COT report for a specific date.

    Args:
        report_date (str): The date in YYYY-MM-DD format.

    Returns:
        dict: The report data as a dictionary, or an error dictionary.
    """
    try:
        url = 'https://www.cftc.gov/dea/futures/api/bydate'
        params = {'date': report_date}
        return _cached_get(url, f'cot_report_{report_date}', params=params)
    except Exception as e:
        return {'error': str(e)}

def fetch_cot_reports_for_commodity(commodity_code):
    """
    Fetches COT reports for a specific commodity code.

    Args:
        commodity_code (str): The commodity code (e.g., 'CL' for Crude Oil).

    Returns:
        list: A list of report dictionaries for the commodity, or an error dictionary.
    """
    try:
        url = 'https://www.cftc.gov/dea/futures/api/bycommodity'
        params = {'code': commodity_code}
        return _cached_get(url, f'cot_reports_{commodity_code}', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_cot_report_summary(report_data):
    """
    Extracts a summary from a COT report dictionary.

    Args:
        report_data (dict): The full report data.

    Returns:
        dict: A summarized dictionary with key metrics, or an error dictionary.
    """
    try:
        if 'error' in report_data:
            return report_data  # Propagate error
        summary = {
            'as_of_date': report_data.get('asOfDate', 'N/A'),
            'open_interest': report_data.get('openInterest', {}),
            'noncommercial_positions': report_data.get('noncommercial', {})
        }
        return summary
    except Exception as e:
        return {'error': str(e)}

def list_available_cot_dates():
    """
    Fetches a list of available COT report dates.

    Returns:
        list: A list of available dates as strings, or an error dictionary.
    """
    try:
        url = 'https://www.cftc.gov/dea/futures/api/dates'  # Example endpoint; adjust based on actual API
        return _cached_get(url, 'available_cot_dates')
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates key functions in the module.
    """
    print("Demonstrating fetch_latest_cot_report:")
    latest_report = fetch_latest_cot_report()
    if 'error' not in latest_report:
        print("Latest report fetched successfully.")
        summary = get_cot_report_summary(latest_report)
        if 'error' not in summary:
            print(f"Summary: {summary}")
        else:
            print(f"Summary error: {summary}")
    else:
        print(f"Error: {latest_report}")

    print("\nDemonstrating fetch_cot_report_by_date for 2023-01-01:")
    report_by_date = fetch_cot_report_by_date('2023-01-01')
    if 'error' not in report_by_date:
        print("Report by date fetched successfully.")
    else:
        print(f"Error: {report_by_date}")

    print("\nDemonstrating list_available_cot_dates:")
    available_dates = list_available_cot_dates()
    if 'error' not in available_dates:
        print(f"Available dates: {available_dates[:5]}...")  # Show first 5 for brevity
    else:
        print(f"Error: {available_dates}")

if __name__ == '__main__':
    main()
