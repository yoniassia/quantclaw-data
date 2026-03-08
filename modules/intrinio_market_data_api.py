"""
Intrinio Market Data API — Stock Prices, Company Data & Market Microstructure

Data Source: Intrinio API v2
API Docs: https://docs.intrinio.com/documentation/api_v2
Category: Exchanges & Market Microstructure
Free tier: Yes (sign up at https://intrinio.com/signup for free API key)
Update frequency: Real-time (EOD on free tier)
Auth: Requires INTRINIO_API_KEY env var (free tier key from intrinio.com/signup)

Provides:
- Historical & real-time stock prices (OHLCV + adjusted)
- Security search and lookup
- Company fundamentals (overview, filings)
- Stock exchanges listing
- 52-week highs/lows, split/dividend history
- Bulk security screening

Usage:
    export INTRINIO_API_KEY="your_free_key_here"
    from modules.intrinio_market_data_api import *
    prices = get_stock_prices("AAPL", start_date="2025-01-01")
    security = get_security_details("AAPL")
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://api-v2.intrinio.com"
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/intrinio")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "QuantClaw-Data/1.0"
}

CACHE_TTL_HOURS = 1  # cache freshness for non-historical data


def _get_api_key() -> str:
    """Get Intrinio API key from environment."""
    key = os.environ.get("INTRINIO_API_KEY", "")
    if not key:
        raise ValueError(
            "INTRINIO_API_KEY not set. "
            "Sign up for a free key at https://intrinio.com/signup "
            "then: export INTRINIO_API_KEY='your_key'"
        )
    return key


def _cache_path(name: str) -> str:
    """Build cache file path."""
    safe = name.replace("/", "_").replace("?", "_").replace("&", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _read_cache(name: str, ttl_hours: float = CACHE_TTL_HOURS) -> Optional[Any]:
    """Read from cache if fresh enough."""
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=ttl_hours):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _write_cache(name: str, data: Any) -> None:
    """Write data to cache."""
    try:
        with open(_cache_path(name), "w") as f:
            json.dump(data, f, default=str)
    except IOError:
        pass


def _request(endpoint: str, params: Optional[Dict] = None,
             cache_key: Optional[str] = None,
             cache_ttl: float = CACHE_TTL_HOURS) -> Dict:
    """
    Make authenticated GET request to Intrinio API v2.

    Args:
        endpoint: API path (e.g. '/securities/AAPL/prices')
        params: Additional query parameters
        cache_key: Optional cache identifier
        cache_ttl: Cache TTL in hours

    Returns:
        JSON response as dict
    """
    if cache_key:
        cached = _read_cache(cache_key, cache_ttl)
        if cached is not None:
            cached["_cached"] = True
            return cached

    api_key = _get_api_key()
    url = f"{BASE_URL}{endpoint}"
    req_params = {"api_key": api_key}
    if params:
        req_params.update(params)

    try:
        resp = requests.get(url, params=req_params, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if cache_key:
            _write_cache(cache_key, data)

        return data

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        body = ""
        try:
            body = e.response.json() if e.response is not None else {}
        except Exception:
            body = e.response.text if e.response is not None else str(e)
        return {
            "error": True,
            "status_code": status,
            "message": str(body),
            "endpoint": endpoint
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": str(e),
            "endpoint": endpoint
        }


# ---------------------------------------------------------------------------
# Security / Stock Data
# ---------------------------------------------------------------------------

def get_stock_prices(ticker: str,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     frequency: str = "daily",
                     page_size: int = 100) -> Dict:
    """
    Get historical stock prices for a security.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
        start_date: Start date 'YYYY-MM-DD' (default: 30 days ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        frequency: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
        page_size: Number of results per page (max 10000)

    Returns:
        Dict with 'stock_prices' list containing OHLCV + adjusted prices,
        52-week high/low, split ratios, dividends.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "frequency": frequency,
        "page_size": min(page_size, 10000)
    }
    cache_key = f"prices_{ticker}_{start_date}_{end_date}_{frequency}"
    return _request(f"/securities/{ticker}/prices", params, cache_key, cache_ttl=0.5)


def get_realtime_price(ticker: str) -> Dict:
    """
    Get real-time (or 15-min delayed on free tier) stock price.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with last_price, last_time, open, high, low, volume, etc.
    """
    cache_key = f"realtime_{ticker}"
    return _request(f"/securities/{ticker}/prices/realtime", cache_key=cache_key, cache_ttl=0.05)


def get_security_details(ticker: str) -> Dict:
    """
    Get detailed security information.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with company_id, name, exchange, currency, FIGI,
        sector, industry, and more.
    """
    cache_key = f"security_{ticker}"
    return _request(f"/securities/{ticker}", cache_key=cache_key, cache_ttl=24)


def search_securities(query: str, page_size: int = 20) -> Dict:
    """
    Search for securities by name or ticker.

    Args:
        query: Search term (ticker or company name)
        page_size: Number of results

    Returns:
        Dict with 'securities' list of matching results.
    """
    params = {"query": query, "page_size": page_size}
    return _request("/securities/search", params)


def get_security_screen(market_cap_gt: Optional[float] = None,
                        market_cap_lt: Optional[float] = None,
                        exchange_mic: str = "USCOMP",
                        active: bool = True,
                        page_size: int = 100) -> Dict:
    """
    Screen securities by criteria.

    Args:
        market_cap_gt: Minimum market cap filter
        market_cap_lt: Maximum market cap filter
        exchange_mic: Exchange MIC code (default: USCOMP for all US)
        active: Only active securities
        page_size: Results per page

    Returns:
        Dict with 'securities' list of matching securities.
    """
    params = {
        "active": str(active).lower(),
        "composite_mic": exchange_mic,
        "page_size": page_size
    }
    if market_cap_gt:
        params["market_cap_greater_than"] = market_cap_gt
    if market_cap_lt:
        params["market_cap_less_than"] = market_cap_lt

    return _request("/securities", params)


# ---------------------------------------------------------------------------
# Company Data
# ---------------------------------------------------------------------------

def get_company(ticker: str) -> Dict:
    """
    Get company profile and fundamentals.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with company name, CIK, LEI, SIC code, sector, industry,
        business description, CEO, employees, etc.
    """
    cache_key = f"company_{ticker}"
    return _request(f"/companies/{ticker}", cache_key=cache_key, cache_ttl=24)


def search_companies(query: str, page_size: int = 20) -> Dict:
    """
    Search companies by name or ticker.

    Args:
        query: Search term
        page_size: Number of results

    Returns:
        Dict with 'companies' list.
    """
    params = {"query": query, "page_size": page_size}
    return _request("/companies/search", params)


def get_company_filings(ticker: str,
                        report_type: Optional[str] = None,
                        start_date: Optional[str] = None,
                        page_size: int = 20) -> Dict:
    """
    Get SEC filings for a company.

    Args:
        ticker: Stock ticker symbol
        report_type: Filter by type (e.g. '10-K', '10-Q', '8-K')
        start_date: Filter filings after this date
        page_size: Number of results

    Returns:
        Dict with 'filings' list containing filing date, type, URL.
    """
    params = {"page_size": page_size}
    if report_type:
        params["report_type"] = report_type
    if start_date:
        params["start_date"] = start_date

    cache_key = f"filings_{ticker}_{report_type}_{start_date}"
    return _request(f"/companies/{ticker}/filings", params, cache_key, cache_ttl=6)


def get_company_fundamentals(ticker: str,
                             statement_code: str = "income_statement",
                             fiscal_year: Optional[int] = None,
                             fiscal_period: str = "FY",
                             page_size: int = 10) -> Dict:
    """
    Get company financial fundamentals.

    Args:
        ticker: Stock ticker
        statement_code: 'income_statement', 'balance_sheet_statement',
                        'cash_flow_statement', 'calculations'
        fiscal_year: Filter by year
        fiscal_period: 'FY', 'Q1', 'Q2', 'Q3', 'Q4', 'TTM'
        page_size: Number of results

    Returns:
        Dict with 'fundamentals' list.
    """
    params = {
        "statement_code": statement_code,
        "type": "reported",
        "fiscal_period": fiscal_period,
        "page_size": page_size
    }
    if fiscal_year:
        params["fiscal_year"] = fiscal_year

    cache_key = f"fundamentals_{ticker}_{statement_code}_{fiscal_period}_{fiscal_year}"
    return _request(f"/companies/{ticker}/fundamentals", params, cache_key, cache_ttl=6)


# ---------------------------------------------------------------------------
# Exchanges
# ---------------------------------------------------------------------------

def get_stock_exchanges() -> Dict:
    """
    List all available stock exchanges.

    Returns:
        Dict with 'stock_exchanges' list containing name, MIC,
        country, city, and more.
    """
    cache_key = "exchanges_all"
    return _request("/stock_exchanges", cache_key=cache_key, cache_ttl=168)


def get_exchange_securities(mic: str = "XNAS", page_size: int = 100) -> Dict:
    """
    List securities traded on a specific exchange.

    Args:
        mic: Market Identification Code (e.g. 'XNAS', 'XNYS')
        page_size: Number of results

    Returns:
        Dict with 'securities' list.
    """
    params = {"page_size": page_size}
    return _request(f"/stock_exchanges/{mic}/securities", params)


# ---------------------------------------------------------------------------
# Market-wide / Bulk
# ---------------------------------------------------------------------------

def get_security_latest_prices(ticker: str) -> Dict:
    """
    Get the latest available price snapshot for a security.
    Useful for quick dashboard/portfolio checks.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with latest OHLCV data point.
    """
    params = {"page_size": 1}
    cache_key = f"latest_price_{ticker}"
    return _request(f"/securities/{ticker}/prices", params, cache_key, cache_ttl=0.25)


def get_security_sma(ticker: str, period: int = 50,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     page_size: int = 50) -> Dict:
    """
    Get Simple Moving Average technical indicator.

    Args:
        ticker: Stock ticker
        period: SMA period (e.g. 20, 50, 200)
        start_date: Start date
        end_date: End date
        page_size: Number of data points

    Returns:
        Dict with 'technicals' list of SMA values.
    """
    params = {"period": period, "page_size": page_size}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    cache_key = f"sma_{ticker}_{period}_{start_date}_{end_date}"
    return _request(f"/securities/{ticker}/prices/technicals/sma", params, cache_key, cache_ttl=1)


def get_security_rsi(ticker: str, period: int = 14,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     page_size: int = 50) -> Dict:
    """
    Get Relative Strength Index technical indicator.

    Args:
        ticker: Stock ticker
        period: RSI period (default 14)
        start_date: Start date
        end_date: End date
        page_size: Number of data points

    Returns:
        Dict with 'technicals' list of RSI values.
    """
    params = {"period": period, "page_size": page_size}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    cache_key = f"rsi_{ticker}_{period}_{start_date}_{end_date}"
    return _request(f"/securities/{ticker}/prices/technicals/rsi", params, cache_key, cache_ttl=1)


def get_security_macd(ticker: str,
                      fast_period: int = 12,
                      slow_period: int = 26,
                      signal_period: int = 9,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      page_size: int = 50) -> Dict:
    """
    Get MACD (Moving Average Convergence Divergence) technical indicator.

    Args:
        ticker: Stock ticker
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)
        start_date: Start date
        end_date: End date
        page_size: Number of data points

    Returns:
        Dict with 'technicals' list of MACD, signal, histogram values.
    """
    params = {
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "page_size": page_size
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    cache_key = f"macd_{ticker}_{fast_period}_{slow_period}_{signal_period}"
    return _request(f"/securities/{ticker}/prices/technicals/macd", params, cache_key, cache_ttl=1)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def check_api_status() -> Dict:
    """
    Check if the Intrinio API is accessible and key is valid.

    Returns:
        Dict with 'ok' bool and diagnostic info.
    """
    try:
        api_key = _get_api_key()
        resp = requests.get(
            f"{BASE_URL}/securities/AAPL",
            params={"api_key": api_key},
            headers=DEFAULT_HEADERS,
            timeout=10
        )
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "api_key_set": True,
            "base_url": BASE_URL
        }
    except ValueError as e:
        return {"ok": False, "api_key_set": False, "message": str(e)}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "api_key_set": True, "message": str(e)}


def list_functions() -> List[str]:
    """List all public functions in this module."""
    return [
        "get_stock_prices",
        "get_realtime_price",
        "get_security_details",
        "search_securities",
        "get_security_screen",
        "get_company",
        "search_companies",
        "get_company_filings",
        "get_company_fundamentals",
        "get_stock_exchanges",
        "get_exchange_securities",
        "get_security_latest_prices",
        "get_security_sma",
        "get_security_rsi",
        "get_security_macd",
        "check_api_status",
        "list_functions",
    ]


if __name__ == "__main__":
    print(json.dumps({
        "module": "intrinio_market_data_api",
        "status": "active",
        "source": "https://docs.intrinio.com/documentation/api_v2",
        "functions": list_functions(),
        "requires": "INTRINIO_API_KEY env var (free at https://intrinio.com/signup)",
        "category": "Exchanges & Market Microstructure"
    }, indent=2))
