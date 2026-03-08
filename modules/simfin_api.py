"""
SimFin API — Financial statements and company data.

Free access to historical financial statements (income, balance sheet, cash flow)
and company data for thousands of publicly traded companies worldwide.
Data sourced from official SEC/regulatory filings.

Source: https://simfin.com/data/api
Update frequency: Quarterly
Category: Earnings & Fundamentals
Free tier: True (requires free API key from simfin.com)
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://backend.simfin.com/api/v3"
DEFAULT_KEY = os.environ.get("SIMFIN_API_KEY", "")


def _request(endpoint: str, params: dict, apikey: Optional[str] = None) -> dict:
    """
    Internal helper to make SimFin API requests.

    Args:
        endpoint: API path after base URL
        params: Query parameters
        apikey: SimFin API key (uses env SIMFIN_API_KEY if not provided)

    Returns:
        Parsed JSON response as dict/list
    """
    key = apikey or DEFAULT_KEY
    if not key:
        return {"error": "No API key. Set SIMFIN_API_KEY env var or pass apikey parameter. Get free key at https://simfin.com"}

    headers = {
        "Authorization": f"api-key {key}",
        "Accept": "application/json",
    }

    url = f"{API_BASE}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            return data
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:500]
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


def get_income_statement(
    ticker: str,
    period: str = "quarterly",
    fyear: Optional[int] = None,
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get income statement data for a company.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        period: 'quarterly' or 'annual'
        fyear: Fiscal year (e.g., 2024). If None, returns latest available.
        apikey: SimFin API key

    Returns:
        dict with revenue, net income, EPS, and other income statement items

    Example:
        >>> stmt = get_income_statement('AAPL', period='quarterly')
        >>> print(stmt)
    """
    params = {"ticker": ticker, "period": period}
    if fyear:
        params["fyear"] = fyear
    result = _request("companies/statements", {**params, "statement": "pl"}, apikey)
    return _format_statement(result, ticker, "income")


def get_balance_sheet(
    ticker: str,
    period: str = "quarterly",
    fyear: Optional[int] = None,
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get balance sheet data for a company.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        period: 'quarterly' or 'annual'
        fyear: Fiscal year. If None, returns latest available.
        apikey: SimFin API key

    Returns:
        dict with assets, liabilities, equity, and other balance sheet items

    Example:
        >>> bs = get_balance_sheet('TSLA', period='annual', fyear=2024)
        >>> print(bs)
    """
    params = {"ticker": ticker, "period": period}
    if fyear:
        params["fyear"] = fyear
    result = _request("companies/statements", {**params, "statement": "bs"}, apikey)
    return _format_statement(result, ticker, "balance_sheet")


def get_cash_flow(
    ticker: str,
    period: str = "quarterly",
    fyear: Optional[int] = None,
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get cash flow statement data for a company.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOG')
        period: 'quarterly' or 'annual'
        fyear: Fiscal year. If None, returns latest available.
        apikey: SimFin API key

    Returns:
        dict with operating, investing, financing cash flows

    Example:
        >>> cf = get_cash_flow('AAPL', period='annual')
        >>> print(cf)
    """
    params = {"ticker": ticker, "period": period}
    if fyear:
        params["fyear"] = fyear
    result = _request("companies/statements", {**params, "statement": "cf"}, apikey)
    return _format_statement(result, ticker, "cash_flow")


def get_company_info(
    ticker: str,
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get general company information.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        apikey: SimFin API key

    Returns:
        dict with company name, industry, sector, market cap, etc.

    Example:
        >>> info = get_company_info('AAPL')
        >>> print(info.get('name'), info.get('sector'))
    """
    result = _request("companies/general", {"ticker": ticker}, apikey)
    if isinstance(result, dict) and "error" in result:
        return result
    return {
        "ticker": ticker,
        "data": result,
        "timestamp": datetime.now().isoformat(),
        "source": "simfin",
    }


def get_share_prices(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get historical share price data.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        start: Start date 'YYYY-MM-DD' (optional)
        end: End date 'YYYY-MM-DD' (optional)
        apikey: SimFin API key

    Returns:
        dict with daily OHLCV price data

    Example:
        >>> prices = get_share_prices('TSLA', start='2024-01-01', end='2024-12-31')
    """
    params = {"ticker": ticker}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    result = _request("companies/prices", params, apikey)
    if isinstance(result, dict) and "error" in result:
        return result
    return {
        "ticker": ticker,
        "data": result,
        "timestamp": datetime.now().isoformat(),
        "source": "simfin",
    }


def list_companies(
    market: str = "us",
    apikey: Optional[str] = None,
) -> dict[str, Any]:
    """
    List all available companies in SimFin database.

    Args:
        market: Market code (e.g., 'us', 'de', 'cn')
        apikey: SimFin API key

    Returns:
        dict with list of companies (ticker, name, simfin_id)

    Example:
        >>> companies = list_companies('us')
        >>> print(len(companies.get('data', [])))
    """
    result = _request("companies/list", {"market": market}, apikey)
    if isinstance(result, dict) and "error" in result:
        return result
    return {
        "market": market,
        "data": result,
        "count": len(result) if isinstance(result, list) else None,
        "timestamp": datetime.now().isoformat(),
        "source": "simfin",
    }


def _format_statement(result: Any, ticker: str, statement_type: str) -> dict[str, Any]:
    """Format raw API response into clean statement dict."""
    if isinstance(result, dict) and "error" in result:
        return result

    # SimFin v3 returns list of statement objects or columnar data
    if isinstance(result, list) and len(result) > 0:
        return {
            "ticker": ticker,
            "statement": statement_type,
            "periods": len(result),
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "source": "simfin",
        }
    elif isinstance(result, dict):
        return {
            "ticker": ticker,
            "statement": statement_type,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "source": "simfin",
        }
    else:
        return {
            "ticker": ticker,
            "statement": statement_type,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "source": "simfin",
            "note": "Unexpected response format",
        }


# Convenience aliases
fetch_data = get_income_statement
get_latest = get_income_statement


if __name__ == "__main__":
    print(json.dumps({
        "module": "simfin_api",
        "status": "ready",
        "source": "https://simfin.com/data/api",
        "functions": [
            "get_income_statement", "get_balance_sheet", "get_cash_flow",
            "get_company_info", "get_share_prices", "list_companies",
        ],
    }, indent=2))
