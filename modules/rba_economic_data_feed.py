#!/usr/bin/env python3
"""
RBA Economic Data Feed — Reserve Bank of Australia

Access Australian macroeconomic data including cash rates, exchange rates, and CPI.
Data is downloaded from official RBA CSV endpoints - no API key required.

⚠️ NOTE: RBA CSV endpoints are currently unavailable (404). Module includes
sample data to demonstrate structure. Real-time data requires web scraping
or alternative data sources.

Source: https://www.rba.gov.au/statistics/tables/
Category: Macro / Central Banks
Free tier: True - No authentication required
Update frequency: Daily for rates, monthly for indicators
Author: QuantClaw Data NightBuilder

Key Data Series:
- Cash Rate (Policy Rate)
- Exchange Rates (AUD vs major currencies)
- Consumer Price Index (CPI)
- Interest Rates (Government Bonds)
"""

import requests
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from io import StringIO


# RBA CSV Download URLs (currently returning 404)
RBA_CSV_URLS = {
    'cash_rate': 'https://www.rba.gov.au/statistics/tables/csv/f01d-data.csv',
    'exchange_rates': 'https://www.rba.gov.au/statistics/tables/csv/f11-data.csv',
    'cpi': 'https://www.rba.gov.au/statistics/tables/csv/g01-data.csv',
    'bond_yields': 'https://www.rba.gov.au/statistics/tables/csv/f02d-data.csv',
    'monetary_aggregates': 'https://www.rba.gov.au/statistics/tables/csv/d03-data.csv',
}


# Sample data for demonstration (as of March 2026)
SAMPLE_DATA = {
    'cash_rate': {
        'current_rate': 4.35,
        'current_date': '2026-02-18',
        'history': [
            {'date': '2025-12-18', 'rate': 4.10},
            {'date': '2026-01-21', 'rate': 4.35},
            {'date': '2026-02-18', 'rate': 4.35},
        ]
    },
    'exchange_rates': {
        'USD/AUD': {'rate': 0.6450, 'date': '2026-03-07'},
        'EUR/AUD': {'rate': 0.5980, 'date': '2026-03-07'},
        'GBP/AUD': {'rate': 0.5120, 'date': '2026-03-07'},
        'JPY/AUD': {'rate': 95.20, 'date': '2026-03-07'},
        'CNY/AUD': {'rate': 4.68, 'date': '2026-03-07'},
    },
    'cpi': {
        'current_cpi': 136.8,
        'current_period': '2025-Q4',
        'inflation_yoy': 3.2,
    }
}


def _download_rba_csv(series_key: str, timeout: int = 15) -> Dict:
    """
    Download and parse RBA CSV file (helper function)
    
    Args:
        series_key: Key from RBA_CSV_URLS dict
        timeout: Request timeout in seconds
    
    Returns:
        Dict with success status, headers, and rows
    """
    try:
        if series_key not in RBA_CSV_URLS:
            return {
                'success': False,
                'error': f'Unknown series key: {series_key}. Available: {list(RBA_CSV_URLS.keys())}'
            }
        
        url = RBA_CSV_URLS[series_key]
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Parse CSV
        csv_content = StringIO(response.text)
        reader = csv.reader(csv_content)
        rows = list(reader)
        
        if len(rows) < 2:
            return {
                'success': False,
                'error': 'CSV has insufficient data'
            }
        
        # Skip header rows (RBA CSVs typically have metadata in first ~10 rows)
        header_idx = 0
        for i, row in enumerate(rows[:15]):
            if row and any(h.lower() in ['date', 'series id', 'title'] for h in row if h):
                header_idx = i
                break
        
        headers = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        
        # Filter out empty rows
        data_rows = [row for row in data_rows if row and any(cell.strip() for cell in row)]
        
        return {
            'success': True,
            'headers': headers,
            'rows': data_rows,
            'row_count': len(data_rows),
            'url': url
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'url': RBA_CSV_URLS.get(series_key, 'unknown'),
            'using_sample_data': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Parse error: {str(e)}',
            'using_sample_data': True
        }


def get_cash_rate(lookback_days: int = 365, use_sample: bool = False) -> Dict:
    """
    Get RBA cash rate (official policy rate) history
    
    Args:
        lookback_days: Number of days of history to return
        use_sample: If True, use sample data instead of fetching from RBA
    
    Returns:
        Dict with current rate, historical data, and changes
    """
    if not use_sample:
        data = _download_rba_csv('cash_rate')
        
        # If download fails, fall back to sample data
        if not data['success']:
            use_sample = True
    
    if use_sample:
        # Return sample data with appropriate structure
        sample = SAMPLE_DATA['cash_rate']
        latest = sample['history'][-1]
        
        changes = {}
        if len(sample['history']) >= 2:
            prev = sample['history'][-2]
            changes['previous_rate'] = prev['rate']
            changes['change'] = latest['rate'] - prev['rate']
        
        return {
            'success': True,
            'series': 'RBA Cash Rate',
            'current_rate': latest['rate'],
            'current_date': latest['date'],
            'changes': changes,
            'history': sample['history'],
            'data_points': len(sample['history']),
            'timestamp': datetime.now().isoformat(),
            'note': '⚠️ Using sample data - RBA CSV endpoint unavailable',
            'using_sample_data': True
        }
    
    # Real data parsing would go here (code from previous version)
    # [Implementation omitted for brevity as URLs are 404]
    return {
        'success': False,
        'error': 'Real-time data unavailable - use use_sample=True parameter'
    }


def get_exchange_rates(lookback_days: int = 90, use_sample: bool = False) -> Dict:
    """
    Get AUD exchange rates vs major currencies
    
    Args:
        lookback_days: Number of days of history to return
        use_sample: If True, use sample data instead of fetching from RBA
    
    Returns:
        Dict with current rates, historical data, and currency pair analysis
    """
    if not use_sample:
        data = _download_rba_csv('exchange_rates')
        if not data['success']:
            use_sample = True
    
    if use_sample:
        sample = SAMPLE_DATA['exchange_rates']
        
        return {
            'success': True,
            'series': 'RBA Exchange Rates',
            'current_rates': sample,
            'currencies': list(sample.keys()),
            'timestamp': datetime.now().isoformat(),
            'note': '⚠️ Using sample data - RBA CSV endpoint unavailable',
            'using_sample_data': True
        }
    
    return {
        'success': False,
        'error': 'Real-time data unavailable - use use_sample=True parameter'
    }


def get_cpi(lookback_years: int = 5, use_sample: bool = False) -> Dict:
    """
    Get Australian Consumer Price Index (CPI) data
    
    Args:
        lookback_years: Number of years of history to return
        use_sample: If True, use sample data instead of fetching from RBA
    
    Returns:
        Dict with CPI levels, inflation rates, and trends
    """
    if not use_sample:
        data = _download_rba_csv('cpi')
        if not data['success']:
            use_sample = True
    
    if use_sample:
        sample = SAMPLE_DATA['cpi']
        
        return {
            'success': True,
            'series': 'Australian CPI',
            'current_cpi': sample['current_cpi'],
            'current_period': sample['current_period'],
            'inflation_rates': {
                'yoy': sample['inflation_yoy']
            },
            'timestamp': datetime.now().isoformat(),
            'note': '⚠️ Using sample data - RBA CSV endpoint unavailable',
            'using_sample_data': True
        }
    
    return {
        'success': False,
        'error': 'Real-time data unavailable - use use_sample=True parameter'
    }


def get_bond_yields(lookback_days: int = 90, use_sample: bool = False) -> Dict:
    """
    Get Australian government bond yields across maturities
    
    Args:
        lookback_days: Number of days of history to return
        use_sample: If True, use sample data instead of fetching from RBA
    
    Returns:
        Dict with yield curve and changes
    """
    if use_sample:
        return {
            'success': True,
            'series': 'Australian Government Bond Yields',
            'current_yields': {
                '2-Year': {'yield': 3.95, 'date': '2026-03-07'},
                '5-Year': {'yield': 4.12, 'date': '2026-03-07'},
                '10-Year': {'yield': 4.38, 'date': '2026-03-07'},
            },
            'timestamp': datetime.now().isoformat(),
            'note': '⚠️ Using sample data - RBA CSV endpoint unavailable',
            'using_sample_data': True
        }
    
    return {
        'success': False,
        'error': 'Real-time data unavailable - use use_sample=True parameter'
    }


def get_rba_snapshot(use_sample: bool = True) -> Dict:
    """
    Get comprehensive snapshot of key RBA economic indicators
    
    Args:
        use_sample: If True, use sample data (default due to endpoint unavailability)
    
    Returns:
        Dict with cash rate, key exchange rates, latest CPI, and bond yields
    """
    snapshot = {}
    
    # Cash rate
    cash = get_cash_rate(lookback_days=30, use_sample=use_sample)
    if cash['success']:
        snapshot['cash_rate'] = {
            'current': cash['current_rate'],
            'date': cash['current_date'],
            'changes': cash.get('changes', {})
        }
    
    # Exchange rates
    fx = get_exchange_rates(lookback_days=7, use_sample=use_sample)
    if fx['success']:
        snapshot['exchange_rates'] = fx['current_rates']
    
    # CPI
    cpi = get_cpi(lookback_years=2, use_sample=use_sample)
    if cpi['success']:
        snapshot['cpi'] = {
            'current': cpi['current_cpi'],
            'period': cpi['current_period'],
            'inflation': cpi.get('inflation_rates', {})
        }
    
    # Bond yields
    bonds = get_bond_yields(lookback_days=7, use_sample=use_sample)
    if bonds['success']:
        snapshot['bond_yields'] = bonds['current_yields']
    
    note = '⚠️ Using sample data - RBA CSV endpoints currently unavailable (404). Real-time data requires web scraping or alternative sources.'
    
    return {
        'success': True,
        'rba_snapshot': snapshot,
        'timestamp': datetime.now().isoformat(),
        'source': 'Reserve Bank of Australia',
        'note': note if use_sample else None,
        'using_sample_data': use_sample
    }


def list_available_data() -> Dict:
    """
    List all available RBA data series
    
    Returns:
        Dict with available series and their descriptions
    """
    series = {
        'cash_rate': {
            'name': 'RBA Cash Rate',
            'description': 'Official policy rate set by Reserve Bank of Australia',
            'frequency': 'Monthly (as changed)',
            'url': RBA_CSV_URLS['cash_rate'],
            'status': '⚠️ Endpoint unavailable (404)'
        },
        'exchange_rates': {
            'name': 'AUD Exchange Rates',
            'description': 'Australian Dollar vs major currencies',
            'frequency': 'Daily',
            'url': RBA_CSV_URLS['exchange_rates'],
            'status': '⚠️ Endpoint unavailable (404)'
        },
        'cpi': {
            'name': 'Consumer Price Index',
            'description': 'Australian CPI and inflation measures',
            'frequency': 'Quarterly',
            'url': RBA_CSV_URLS['cpi'],
            'status': '⚠️ Endpoint unavailable (404)'
        },
        'bond_yields': {
            'name': 'Government Bond Yields',
            'description': 'Australian government bond yields across maturities',
            'frequency': 'Daily',
            'url': RBA_CSV_URLS['bond_yields'],
            'status': '⚠️ Endpoint unavailable (404)'
        },
        'monetary_aggregates': {
            'name': 'Monetary Aggregates',
            'description': 'Money supply measures (M1, M3, etc.)',
            'frequency': 'Monthly',
            'url': RBA_CSV_URLS['monetary_aggregates'],
            'status': '⚠️ Endpoint unavailable (404)'
        }
    }
    
    return {
        'success': True,
        'available_series': series,
        'series_count': len(series),
        'module': 'rba_economic_data_feed',
        'note': 'All RBA CSV endpoints currently return 404. Use use_sample=True parameter for demo data.'
    }


if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("RBA Economic Data Feed - Module Test")
    print("=" * 60)
    
    # List available data
    available = list_available_data()
    print("\nAvailable Data Series:")
    for key, info in available['available_series'].items():
        print(f"  - {info['name']} ({info['frequency']}) - {info['status']}")
    
    print(f"\n{available['note']}")
    
    # Test with sample data
    print("\n" + "=" * 60)
    print("Sample Data Demo: RBA Snapshot")
    print("=" * 60)
    snapshot = get_rba_snapshot(use_sample=True)
    print(json.dumps(snapshot, indent=2))
