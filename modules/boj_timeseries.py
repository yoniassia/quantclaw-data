#!/usr/bin/env python3
"""
Bank of Japan Time-Series Data Module

Comprehensive access to BOJ statistical data via the official API:
- Interest rates (policy rates, deposit/loan rates)
- Financial markets (call rates, FX rates, effective exchange rates)
- Money supply (monetary base, money stock M2/M3)
- TANKAN survey (business conditions, capacity, employment)
- Prices (CGPI, SPPI)
- Balance of payments
- Flow of funds
- BOJ balance sheet

Data Source: BOJ Time-Series Data Search API
Base URL: https://www.stat-search.boj.or.jp/api/v1
Auth: None required (public API)
Rate Limit: ~200 requests/day recommended
Coverage: Daily/Weekly/Monthly/Quarterly depending on series

Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# BOJ API Configuration
BOJ_BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"
BOJ_HEADERS = {"Accept-Encoding": "gzip"}
REQUEST_TIMEOUT = 30

# Database registry with descriptions
BOJ_DATABASES = {
    'IR01': 'Basic Discount/Loan Rates',
    'IR02': 'Avg Interest Rates by Deposit Type',
    'IR03': 'Avg Interest Rates on Time Deposits',
    'IR04': 'Avg Contract Interest Rates on Loans',
    'FM01': 'Uncollateralized Overnight Call Rate',
    'FM02': 'Short-term Money Market Rates',
    'FM03': 'Euro-Yen TIBOR',
    'FM04': 'Yields on Government Bonds',
    'FM05': 'Interest Rate Swaps',
    'FM06': 'Stock Prices',
    'FM07': 'Interest Rates on CDs',
    'FM08': 'Foreign Exchange Rates',
    'FM09': 'Effective Exchange Rate',
    'MD01': 'Monetary Base',
    'MD02': 'Money Stock',
    'MD03': 'Deposits by Depositor',
    'MD10': 'Deposits',
    'MD11': 'Deposits Vault Cash Loans',
    'MD13': 'Principal Figures Financial Institutions',
    'MD14': 'Outstanding Domestic Deposits',
    'BS01': 'BOJ Balance Sheet',
    'BS02': 'Financial Institutions Balance Sheets',
    'FF':   'Flow of Funds',
    'CO':   'TANKAN',
    'PR01': 'Corporate Goods Price Index (CGPI)',
    'PR02': 'Services Producer Price Index (SPPI)',
    'BP01': 'Balance of Payments',
    'BIS':  'BIS Banking Statistics',
    'PF01': 'Public Finance (Central Govt)',
    'PF02': 'Public Finance (Local Govt)',
    'PS01': 'Payment and Settlement (BOJ)',
    'PS02': 'Payment and Settlement (Clearing)',
    'OB01': 'Other BOJ Statistics 1',
    'OB02': 'Other BOJ Statistics 2',
    'OT':   'Others',
}

# Well-known series codes for quick access
KNOWN_SERIES = {
    # Call rates (FM01)
    'overnight_call_rate': {'db': 'FM01', 'code': 'STRDCLUCON', 'freq': 'D',
        'name': 'Uncollateralized Overnight Call Rate (Average)'},
    'overnight_call_high': {'db': 'FM01', 'code': 'STRDCLUCONH', 'freq': 'D',
        'name': 'Uncollateralized Overnight Call Rate (High)'},
    'overnight_call_low': {'db': 'FM01', 'code': 'STRDCLUCONL', 'freq': 'D',
        'name': 'Uncollateralized Overnight Call Rate (Low)'},
    # Basic loan rate (IR01)
    'basic_loan_rate': {'db': 'IR01', 'code': 'MADR1Z@D', 'freq': 'D',
        'name': 'Basic Loan Rate'},
    # TANKAN business conditions (CO)
    'tankan_large_mfg': {'db': 'CO', 'code': 'TK99F1000601GCQ01000', 'freq': 'Q',
        'name': 'TANKAN DI Large Manufacturing (Actual)'},
    'tankan_large_mfg_forecast': {'db': 'CO', 'code': 'TK99F2000601GCQ01000', 'freq': 'Q',
        'name': 'TANKAN DI Large Manufacturing (Forecast)'},
}

# Frequency labels
FREQUENCY_MAP = {
    'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Q': 'Quarterly',
    'CY': 'Calendar Year', 'FY': 'Fiscal Year',
    'CH': 'Calendar Half-Year', 'FH': 'Fiscal Half-Year',
}


def _boj_request(endpoint: str, params: Dict) -> Dict:
    """
    Internal: Make request to BOJ API.
    Returns parsed JSON or error dict.
    """
    url = f"{BOJ_BASE_URL}/{endpoint}"
    # Always request English JSON
    params.setdefault('format', 'json')
    params.setdefault('lang', 'en')

    try:
        resp = requests.get(url, params=params, headers=BOJ_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if data.get('STATUS') != 200:
            return {
                'error': True,
                'status': data.get('STATUS'),
                'message': data.get('MESSAGE', 'Unknown BOJ API error'),
                'message_id': data.get('MESSAGEID'),
            }
        return data

    except requests.exceptions.Timeout:
        return {'error': True, 'message': 'BOJ API request timed out'}
    except requests.exceptions.ConnectionError:
        return {'error': True, 'message': 'BOJ API connection failed'}
    except requests.exceptions.RequestException as e:
        return {'error': True, 'message': f'BOJ API request failed: {str(e)}'}
    except (json.JSONDecodeError, ValueError) as e:
        return {'error': True, 'message': f'BOJ API returned invalid JSON: {str(e)}'}


def _parse_resultset(data: Dict) -> List[Dict]:
    """
    Parse BOJ API RESULTSET into clean list of series dicts.
    """
    results = []
    for series in data.get('RESULTSET', []):
        values_block = series.get('VALUES', {})
        dates = values_block.get('SURVEY_DATES', [])
        vals = values_block.get('VALUES', [])

        observations = []
        for d, v in zip(dates, vals):
            observations.append({'date': d, 'value': v})

        results.append({
            'series_code': series.get('SERIES_CODE', ''),
            'name': series.get('NAME_OF_TIME_SERIES', ''),
            'unit': series.get('UNIT', ''),
            'frequency': series.get('FREQUENCY', ''),
            'category': series.get('CATEGORY', ''),
            'last_update': series.get('LAST_UPDATE'),
            'observations': observations,
        })
    return results


def _format_date_param(year: int, month: int = None, frequency: str = 'M') -> str:
    """Format date parameter based on frequency."""
    freq = frequency.upper()
    if freq in ('CY', 'FY'):
        return str(year)
    elif freq in ('CH', 'FH'):
        half = '01' if (month or 1) <= 6 else '02'
        return f"{year}{half}"
    elif freq == 'Q':
        q = ((month or 1) - 1) // 3 + 1
        return f"{year}{q:02d}"
    else:  # M, W, D
        return f"{year}{(month or 1):02d}"


def get_series_by_code(db: str, codes: Union[str, List[str]],
                       start_date: str = None, end_date: str = None) -> Dict:
    """
    Fetch time-series data by series code(s).

    Args:
        db: Database name (e.g. 'FM01', 'CO', 'IR01')
        codes: Series code or list of codes (same frequency required)
        start_date: Start date string (format depends on frequency, e.g. '202501')
        end_date: End date string

    Returns:
        Dict with 'series' list and metadata, or error dict
    """
    if isinstance(codes, list):
        code_str = ','.join(codes)
    else:
        code_str = codes

    params = {'db': db, 'code': code_str}
    if start_date:
        params['startDate'] = start_date
    if end_date:
        params['endDate'] = end_date

    data = _boj_request('getDataCode', params)
    if data.get('error'):
        return data

    return {
        'source': 'BOJ',
        'database': db,
        'database_name': BOJ_DATABASES.get(db.upper(), db),
        'series': _parse_resultset(data),
        'next_position': data.get('NEXTPOSITION'),
        'timestamp': datetime.utcnow().isoformat(),
    }


def get_series_by_layer(db: str, layer: str, frequency: str,
                        start_date: str = None, end_date: str = None) -> Dict:
    """
    Fetch time-series data by layer (hierarchical navigation).

    Args:
        db: Database name
        layer: Layer info (comma-separated, e.g. '1,1,1' or '*')
        frequency: 'D','W','M','Q','CY','FY','CH','FH'
        start_date: Start date string
        end_date: End date string

    Returns:
        Dict with 'series' list and metadata, or error dict
    """
    params = {'db': db, 'layer': layer, 'frequency': frequency}
    if start_date:
        params['startDate'] = start_date
    if end_date:
        params['endDate'] = end_date

    data = _boj_request('getDataLayer', params)
    if data.get('error'):
        return data

    return {
        'source': 'BOJ',
        'database': db,
        'database_name': BOJ_DATABASES.get(db.upper(), db),
        'frequency': FREQUENCY_MAP.get(frequency.upper(), frequency),
        'series': _parse_resultset(data),
        'next_position': data.get('NEXTPOSITION'),
        'timestamp': datetime.utcnow().isoformat(),
    }


def get_metadata(db: str) -> Dict:
    """
    Get metadata for all series in a database (codes, names, attributes).

    Args:
        db: Database name (e.g. 'FM08', 'CO')

    Returns:
        Dict with series metadata list, or error dict
    """
    data = _boj_request('getMetadata', {'db': db})
    if data.get('error'):
        return data

    series_list = []
    for s in data.get('RESULTSET', []):
        series_list.append({
            'series_code': s.get('SERIES_CODE', ''),
            'name': s.get('NAME_OF_TIME_SERIES', ''),
            'unit': s.get('UNIT', ''),
            'frequency': s.get('FREQUENCY', ''),
            'category': s.get('CATEGORY', ''),
            'last_update': s.get('LAST_UPDATE'),
        })

    return {
        'source': 'BOJ',
        'database': db,
        'database_name': BOJ_DATABASES.get(db.upper(), db),
        'series_count': len(series_list),
        'series': series_list,
        'timestamp': datetime.utcnow().isoformat(),
    }


def get_overnight_call_rate(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get uncollateralized overnight call rate (BOJ policy rate proxy).

    Args:
        start_date: Start date (YYYYMM format, e.g. '202501')
        end_date: End date (YYYYMM format)

    Returns:
        Dict with rate data (average, high, low)
    """
    codes = ['STRDCLUCON', 'STRDCLUCONH', 'STRDCLUCONL']
    return get_series_by_code('FM01', codes, start_date=start_date, end_date=end_date)


def get_fx_rates(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get Tokyo Market Interbank FX Rates (USD/JPY, EUR/JPY, etc.).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with FX rate series
    """
    return get_series_by_layer('FM08', '*', 'D', start_date=start_date, end_date=end_date)


def get_effective_exchange_rates(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get real and nominal effective exchange rates of the yen.

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with effective exchange rate series
    """
    return get_series_by_layer('FM09', '*', 'M', start_date=start_date, end_date=end_date)


def get_monetary_base(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get monetary base data (monthly averages outstanding).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with monetary base series
    """
    return get_series_by_layer('MD01', '*', 'M', start_date=start_date, end_date=end_date)


def get_money_stock(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get money stock data (M1, M2, M3, broadly-defined liquidity).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with money stock series
    """
    return get_series_by_layer('MD02', '*', 'M', start_date=start_date, end_date=end_date)


def get_tankan(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get TANKAN survey results (Business Conditions DI, all categories).

    Args:
        start_date: Start date (YYYYQQ format, e.g. '202401' for Q1 2024)
        end_date: End date (YYYYQQ format)

    Returns:
        Dict with TANKAN series
    """
    return get_series_by_layer('CO', '*', 'Q', start_date=start_date, end_date=end_date)


def get_tankan_headline(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get headline TANKAN DI for Large Manufacturing (actual + forecast).

    Args:
        start_date: Start date (YYYYQQ)
        end_date: End date (YYYYQQ)

    Returns:
        Dict with headline TANKAN numbers
    """
    codes = ['TK99F1000601GCQ01000', 'TK99F2000601GCQ01000']
    return get_series_by_code('CO', codes, start_date=start_date, end_date=end_date)


def get_cgpi(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get Corporate Goods Price Index (CGPI / producer prices).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with CGPI series
    """
    return get_series_by_layer('PR01', '*', 'M', start_date=start_date, end_date=end_date)


def get_govt_bond_yields(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get Japanese Government Bond (JGB) yields.

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with JGB yield series
    """
    return get_series_by_layer('FM04', '*', 'D', start_date=start_date, end_date=end_date)


def get_boj_balance_sheet(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get Bank of Japan balance sheet data.

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with BOJ balance sheet series
    """
    return get_series_by_layer('BS01', '*', 'M', start_date=start_date, end_date=end_date)


def get_balance_of_payments(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get Japan Balance of Payments data (monthly).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with BOP series
    """
    return get_series_by_layer('BP01', '*', 'M', start_date=start_date, end_date=end_date)


def get_basic_loan_rate(start_date: str = None, end_date: str = None) -> Dict:
    """
    Get BOJ basic discount/loan rate (daily).

    Args:
        start_date: Start date (YYYYMM)
        end_date: End date (YYYYMM)

    Returns:
        Dict with basic loan rate series
    """
    return get_series_by_code('IR01', 'MADR1Z@D', start_date=start_date, end_date=end_date)


def get_known_series(key: str, start_date: str = None, end_date: str = None) -> Dict:
    """
    Fetch a well-known series by friendly key name.

    Args:
        key: One of: overnight_call_rate, overnight_call_high, overnight_call_low,
             basic_loan_rate, tankan_large_mfg, tankan_large_mfg_forecast
        start_date: Start date string
        end_date: End date string

    Returns:
        Dict with series data, or error if key not found
    """
    if key not in KNOWN_SERIES:
        return {
            'error': True,
            'message': f'Unknown series key: {key}. Available: {list(KNOWN_SERIES.keys())}',
        }
    info = KNOWN_SERIES[key]
    return get_series_by_code(info['db'], info['code'],
                              start_date=start_date, end_date=end_date)


def list_databases() -> Dict:
    """
    List all available BOJ databases with descriptions.

    Returns:
        Dict with database list
    """
    return {
        'source': 'BOJ',
        'databases': [{'id': k, 'name': v} for k, v in BOJ_DATABASES.items()],
        'count': len(BOJ_DATABASES),
        'timestamp': datetime.utcnow().isoformat(),
    }


def list_known_series() -> Dict:
    """
    List pre-configured well-known series for quick access.

    Returns:
        Dict with known series list
    """
    return {
        'source': 'BOJ',
        'known_series': {k: {'name': v['name'], 'db': v['db'], 'frequency': v['freq']}
                         for k, v in KNOWN_SERIES.items()},
        'count': len(KNOWN_SERIES),
    }


def get_all_paginated(db: str, layer: str, frequency: str,
                      start_date: str = None, end_date: str = None,
                      max_pages: int = 10, delay: float = 2.0) -> Dict:
    """
    Fetch all data with automatic pagination.

    Args:
        db: Database name
        layer: Layer info
        frequency: Frequency code
        start_date: Start date
        end_date: End date
        max_pages: Max pagination requests (safety limit)
        delay: Seconds between requests (respect rate limits)

    Returns:
        Dict with all series combined
    """
    all_series = []
    start_pos = None

    for page in range(max_pages):
        params = {'db': db, 'layer': layer, 'frequency': frequency}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        if start_pos:
            params['startPosition'] = start_pos

        data = _boj_request('getDataLayer', params)
        if data.get('error'):
            if all_series:
                # Return partial results
                break
            return data

        all_series.extend(_parse_resultset(data))
        next_pos = data.get('NEXTPOSITION')

        if next_pos is None:
            break

        start_pos = next_pos
        if page < max_pages - 1:
            time.sleep(delay)

    return {
        'source': 'BOJ',
        'database': db,
        'database_name': BOJ_DATABASES.get(db.upper(), db),
        'frequency': FREQUENCY_MAP.get(frequency.upper(), frequency),
        'series': all_series,
        'total_series': len(all_series),
        'pages_fetched': page + 1,
        'timestamp': datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "boj_timeseries",
        "status": "active",
        "source": "https://www.stat-search.boj.or.jp/api/v1",
        "databases": len(BOJ_DATABASES),
        "known_series": len(KNOWN_SERIES),
        "functions": [
            "get_series_by_code", "get_series_by_layer", "get_metadata",
            "get_overnight_call_rate", "get_fx_rates", "get_effective_exchange_rates",
            "get_monetary_base", "get_money_stock", "get_tankan", "get_tankan_headline",
            "get_cgpi", "get_govt_bond_yields", "get_boj_balance_sheet",
            "get_balance_of_payments", "get_basic_loan_rate", "get_known_series",
            "list_databases", "list_known_series", "get_all_paginated",
        ]
    }, indent=2))
