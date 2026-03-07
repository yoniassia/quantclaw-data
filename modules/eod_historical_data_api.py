#!/usr/bin/env python3
"""
EOD Historical Data API Module

Fetches fundamentals, earnings, dividends, historical prices, and bulk fundamentals from EODHD API.
Uses 'demo' token by default (limited to 20 calls/day, few symbols like AAPL.US).

Source: https://eodhd.com/financial-apis/
Free tier: 20 calls/day with demo token.

Style: Clean functions returning dict/list, requests-based, error handling, docstrings.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration
BASE_URL = "https://eodhistoricaldata.com/api"
API_TOKEN = os.environ.get("EODHD_API_TOKEN", "demo")


def _api_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Internal API request helper with error handling.
    """
    url = f"{BASE_URL}/{endpoint}"
    default_params = {
        "api_token": API_TOKEN,
        "fmt": "json"
    }
    if params:
        default_params.update(params)

    try:
        response = requests.get(url, params=default_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "message" in data and "api_token" in data.get("message", ""):
            raise ValueError(f"API error (demo limit?): {data['message']}")
        return data
    except requests.exceptions.RequestException as e:
        raise ValueError(f"EODHD API request failed for {endpoint}: {str(e)}")
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Failed to parse JSON response for {endpoint}: {str(e)}")


def get_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch company fundamentals (P/E, EPS, market cap, financials, etc.).

    Args:
        ticker: Symbol like 'AAPL.US'

    Returns:
        Dict with General, Financials, Valuation, etc.

    Example:
        >>> get_fundamentals("AAPL.US")
        {"General": {...}, "Financials": {...}}
    """
    return _api_request(f"fundamentals/{ticker}")


def get_earnings(ticker: str) -> List[Dict[str, Any]]:
    """
    Fetch earnings history from fundamentals Financials (quarterly/annual).

    Args:
        ticker: Symbol like 'AAPL.US'

    Returns:
        List of earnings reports [{"date": "YYYY-MM-DD", "netIncome": "...", "eps": "...", ...}]
    """
    fundamentals = get_fundamentals(ticker)
    financials = fundamentals.get("Financials", {})
    earnings: List[Dict[str, Any]] = []

    symbol_fin = financials.get(ticker)
    if not symbol_fin:
        return []

    for period_type in ["quarterly", "annual"]:
        if period_type in symbol_fin:
            for date_str, report in symbol_fin[period_type].items():
                earnings.append({
                    "period": period_type,
                    "date": date_str,
                    "currency": report.get("currency_symbol", "USD"),
                    "netIncome": report.get("netIncome"),
                    "eps": report.get("eps"),
                    "revenue": report.get("totalRevenue"),
                    "grossProfit": report.get("grossProfit"),
                    "ebitda": report.get("ebitda"),
                })
    return earnings


def get_dividends(ticker: str) -> List[Dict[str, float]]:
    """
    Fetch dividend history.

    Args:
        ticker: Symbol like 'AAPL.US'

    Returns:
        List of [{"date": "YYYY-MM-DD", "dividend": float}, ...]

    Example:
        >>> get_dividends("AAPL.US")[-3:]
        [{"date": "2024-11-08", "dividend": 0.25}, ...]
    """
    data = _api_request(f"div/{ticker}")
    dividends = []
    for row in data:
        if len(row) >= 2:
            dividends.append({
                "date": row[0],
                "dividend": float(row[1])
            })
    return dividends


def get_historical_prices(ticker: str, period: str = "d", from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch historical EOD prices.

    Args:
        ticker: Symbol like 'AAPL.US'
        period: 'd' (daily), 'w' (weekly), 'm' (monthly)
        from_date: YYYY-MM-DD
        to_date: YYYY-MM-DD

    Returns:
        List of {"Date": "...", "Open": float, "High": ..., "Low": ..., "Close": ..., "Adjusted_close": ..., "Volume": int}
    """
    params = {"period": period}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    return _api_request(f"eod/{ticker}", params)


def get_bulk_fundamentals(exchange: str = "US") -> List[Dict[str, Any]]:
    """
    Fetch bulk fundamentals list for exchange (demo may be limited).

    Args:
        exchange: e.g. 'US', 'LSE'

    Returns:
        List of fundamentals dicts
    """
    return _api_request(f"fundamentals-list/{exchange}")


if __name__ == "__main__":
    import json
    print(json.dumps({
        "module": "eod_historical_data_api",
        "functions": ["get_fundamentals", "get_earnings", "get_dividends", "get_historical_prices", "get_bulk_fundamentals"],
        "status": "ready",
        "demo_ticker": "AAPL.US"
    }, indent=2))
