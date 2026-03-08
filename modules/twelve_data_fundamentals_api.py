#!/usr/bin/env python3
"""
Twelve Data Fundamentals API — Company Profiles, Financial Statements & Earnings

Core Twelve Data integration for fundamental data including:
- Company profiles (overview, sector, industry, employees)
- Income statements (annual/quarterly)
- Balance sheets (annual/quarterly)
- Cash flow statements (annual/quarterly)
- Earnings data and estimates
- Key statistics and financial ratios
- Dividends

Source: https://twelvedata.com/docs#fundamentals
Category: Earnings & Fundamentals
Free tier: True (requires TWELVE_DATA_API_KEY env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Twelve Data API Configuration
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")


def _request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Internal helper for Twelve Data API requests.

    Args:
        endpoint: API endpoint path (e.g. '/profile')
        params: Query parameters (apikey added automatically)

    Returns:
        Parsed JSON response as dict/list
    """
    if params is None:
        params = {}
    params['apikey'] = TWELVE_DATA_API_KEY
    url = f"{TWELVE_DATA_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        # Twelve Data returns {"code": 400, "message": "..."} on errors
        if isinstance(data, dict) and data.get('code') and data['code'] != 200:
            return {'error': data.get('message', 'Unknown API error'), 'code': data.get('code')}
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except json.JSONDecodeError as e:
        return {'error': f'JSON decode error: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_profile(symbol: str = 'AAPL', exchange: str = '', country: str = '') -> Dict:
    """
    Get company profile including sector, industry, CEO, employees, description.

    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        exchange: Exchange name filter (optional)
        country: Country filter (optional)

    Returns:
        Dict with name, exchange, sector, industry, employees, CEO, description, etc.

    Example:
        >>> profile = get_profile('AAPL')
        >>> print(f"{profile.get('name')} — {profile.get('sector')}")
    """
    params = {'symbol': symbol.upper()}
    if exchange:
        params['exchange'] = exchange
    if country:
        params['country'] = country
    data = _request('/profile', params)
    if isinstance(data, dict) and 'error' not in data:
        data['_symbol'] = symbol.upper()
        data['_fetched_at'] = datetime.now().isoformat()
    return data


def get_income_statement(symbol: str = 'AAPL', period: str = 'annual',
                         start_date: str = '', end_date: str = '') -> Dict:
    """
    Get income statement data (revenue, net income, EPS, etc.).

    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarterly' (default: 'annual')
        start_date: Start date filter YYYY-MM-DD (optional)
        end_date: End date filter YYYY-MM-DD (optional)

    Returns:
        Dict with 'income_statement' list of period records

    Example:
        >>> inc = get_income_statement('MSFT', period='quarterly')
        >>> print(inc.get('income_statement', [{}])[0].get('revenue'))
    """
    params = {'symbol': symbol.upper(), 'period': period}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return _request('/income_statement', params)


def get_balance_sheet(symbol: str = 'AAPL', period: str = 'annual',
                      start_date: str = '', end_date: str = '') -> Dict:
    """
    Get balance sheet data (total assets, liabilities, equity, cash, debt).

    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarterly' (default: 'annual')
        start_date: Start date filter YYYY-MM-DD (optional)
        end_date: End date filter YYYY-MM-DD (optional)

    Returns:
        Dict with 'balance_sheet' list of period records

    Example:
        >>> bs = get_balance_sheet('AAPL')
        >>> print(bs.get('balance_sheet', [{}])[0].get('total_assets'))
    """
    params = {'symbol': symbol.upper(), 'period': period}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return _request('/balance_sheet', params)


def get_cash_flow(symbol: str = 'AAPL', period: str = 'annual',
                  start_date: str = '', end_date: str = '') -> Dict:
    """
    Get cash flow statement data (operating, investing, financing cash flows).

    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarterly' (default: 'annual')
        start_date: Start date filter YYYY-MM-DD (optional)
        end_date: End date filter YYYY-MM-DD (optional)

    Returns:
        Dict with 'cash_flow' list of period records

    Example:
        >>> cf = get_cash_flow('AAPL')
        >>> print(cf.get('cash_flow', [{}])[0].get('free_cash_flow'))
    """
    params = {'symbol': symbol.upper(), 'period': period}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return _request('/cash_flow', params)


def get_earnings(symbol: str = 'AAPL', period: str = 'quarterly',
                 start_date: str = '', end_date: str = '') -> Dict:
    """
    Get historical earnings data (EPS actual vs estimated, surprise %).

    Args:
        symbol: Stock ticker symbol
        period: 'quarterly' or 'annual' (default: 'quarterly')
        start_date: Start date filter YYYY-MM-DD (optional)
        end_date: End date filter YYYY-MM-DD (optional)

    Returns:
        Dict with 'earnings' list of earnings records

    Example:
        >>> earn = get_earnings('AAPL')
        >>> latest = earn.get('earnings', [{}])[0]
        >>> print(f"EPS: {latest.get('eps_actual')} vs est {latest.get('eps_estimate')}")
    """
    params = {'symbol': symbol.upper(), 'period': period}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return _request('/earnings', params)


def get_earnings_calendar(dp: int = 7) -> Dict:
    """
    Get upcoming earnings calendar for the next N days.

    Args:
        dp: Number of days to look ahead (default: 7)

    Returns:
        Dict with 'earnings' list of upcoming earnings events

    Example:
        >>> cal = get_earnings_calendar(dp=14)
        >>> for e in cal.get('earnings', {}).get('data', [])[:5]:
        ...     print(f"{e.get('symbol')} reports {e.get('date')}")
    """
    params = {'dp': dp}
    return _request('/earnings_calendar', params)


def get_statistics(symbol: str = 'AAPL') -> Dict:
    """
    Get key statistics: market cap, P/E, EPS, beta, 52-week range, etc.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with statistics categories (valuations, financials, stock_price_summary)

    Example:
        >>> stats = get_statistics('AAPL')
        >>> val = stats.get('statistics', {}).get('valuations', {})
        >>> print(f"P/E: {val.get('trailing_pe')}")
    """
    params = {'symbol': symbol.upper()}
    return _request('/statistics', params)


def get_dividends(symbol: str = 'AAPL', start_date: str = '', end_date: str = '') -> Dict:
    """
    Get dividend history for a symbol.

    Args:
        symbol: Stock ticker symbol
        start_date: Start date filter YYYY-MM-DD (optional)
        end_date: End date filter YYYY-MM-DD (optional)

    Returns:
        Dict with 'dividends' list of dividend records (amount, date, etc.)

    Example:
        >>> divs = get_dividends('MSFT')
        >>> for d in divs.get('dividends', [])[:3]:
        ...     print(f"{d.get('payment_date')}: ${d.get('amount')}")
    """
    params = {'symbol': symbol.upper()}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    return _request('/dividends', params)


def get_key_executives(symbol: str = 'AAPL') -> Dict:
    """
    Get key executives / insiders for a company.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with 'key_executives' list of executive records

    Example:
        >>> execs = get_key_executives('AAPL')
        >>> for e in execs.get('key_executives', [])[:3]:
        ...     print(f"{e.get('name')} — {e.get('title')}")
    """
    params = {'symbol': symbol.upper()}
    return _request('/key_executives', params)


def get_institutional_holders(symbol: str = 'AAPL') -> Dict:
    """
    Get institutional holders for a symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with 'institutional_holders' list of holder records

    Example:
        >>> holders = get_institutional_holders('AAPL')
        >>> for h in holders.get('institutional_holders', [])[:3]:
        ...     print(f"{h.get('entity_name')}: {h.get('shares')}")
    """
    params = {'symbol': symbol.upper()}
    return _request('/institutional_holders', params)


def get_fund_holders(symbol: str = 'AAPL') -> Dict:
    """
    Get mutual fund holders for a symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with 'fund_holders' list of fund records

    Example:
        >>> funds = get_fund_holders('MSFT')
        >>> for f in funds.get('fund_holders', [])[:3]:
        ...     print(f"{f.get('entity_name')}: {f.get('shares')}")
    """
    params = {'symbol': symbol.upper()}
    return _request('/fund_holders', params)


def fetch_data(symbol: str = 'AAPL') -> Dict:
    """
    Fetch comprehensive fundamentals bundle for a symbol.
    Combines profile, statistics, and latest earnings in one call.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with 'profile', 'statistics', 'earnings' keys

    Example:
        >>> data = fetch_data('AAPL')
        >>> print(data['profile'].get('name'), data['statistics'].get('statistics', {}).get('valuations', {}).get('market_capitalization'))
    """
    return {
        'symbol': symbol.upper(),
        'profile': get_profile(symbol),
        'statistics': get_statistics(symbol),
        'earnings': get_earnings(symbol),
        '_fetched_at': datetime.now().isoformat()
    }


def get_latest(symbol: str = 'AAPL') -> Dict:
    """
    Get latest fundamental snapshot (profile + key stats).
    Alias for fetch_data.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with fundamental data bundle
    """
    return fetch_data(symbol)


if __name__ == "__main__":
    print(json.dumps({
        "module": "twelve_data_fundamentals_api",
        "status": "active",
        "source": "https://twelvedata.com/docs#fundamentals",
        "functions": [
            "get_profile", "get_income_statement", "get_balance_sheet",
            "get_cash_flow", "get_earnings", "get_earnings_calendar",
            "get_statistics", "get_dividends", "get_key_executives",
            "get_institutional_holders", "get_fund_holders",
            "fetch_data", "get_latest"
        ]
    }, indent=2))
