#!/usr/bin/env python3
"""
Nasdaq Emerging Markets — QuantClaw Data Module

Access emerging market equity data via Nasdaq Data Link (formerly Quandl).
Covers India NSE/BSE, Hong Kong HKEX, and legacy WIKI datasets.
Provides historical OHLCV prices for quantitative backtesting.

Source: https://data.nasdaq.com/
Category: Emerging Markets
Free tier: True — 50 calls/day keyless; register free at data.nasdaq.com for more
Update frequency: Daily
Author: QuantClaw Data NightBuilder
Phase: NightBuilder v2

Setup:
    1. Register free at https://data.nasdaq.com/
    2. Set env var: export NASDAQ_DATA_LINK_API_KEY=your_key
    OR put NASDAQ_DATA_LINK_API_KEY=your_key in quantclaw-data/.env

Supported databases: NSE, BSE, HKEX, WIKI, SSE, SZSE
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Try to import the official library (optional)
_HAS_NDL_LIB = False
try:
    import nasdaqdatalink
    _HAS_NDL_LIB = True
except ImportError:
    pass

# ── Config ──────────────────────────────────────────────────────────────────

BASE_URL = "https://data.nasdaq.com/api/v3"
API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY", "")

CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "nasdaq_em"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 12

# ── Database Registry ───────────────────────────────────────────────────────

EM_DATABASES: Dict[str, str] = {
    "NSE":  "National Stock Exchange of India",
    "BSE":  "Bombay Stock Exchange (India)",
    "HKEX": "Hong Kong Stock Exchange",
    "SSE":  "Shanghai Stock Exchange",
    "SZSE": "Shenzhen Stock Exchange",
    "WIKI": "Wiki EOD Stock Prices (US, legacy free)",
}

EM_POPULAR_STOCKS: Dict[str, List[str]] = {
    "NSE":  ["TATAMOTORS", "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "WIPRO", "SBIN"],
    "BSE":  ["BOM500325", "BOM500112", "BOM500209"],
    "HKEX": ["00700", "09988", "00941", "01810"],
}

EM_INDICES: Dict[str, tuple] = {
    "india_nifty50":  ("NSE", "NIFTY_50"),
    "india_sensex":   ("BSE", "SENSEX"),
    "hong_kong_hsi":  ("HKEX", "HSI"),
}


# ── Internal Helpers ────────────────────────────────────────────────────────

def _cache_key(endpoint: str, params: dict) -> str:
    """Generate a filesystem-safe cache key."""
    slug = endpoint.replace("/", "_")
    param_str = "_".join(f"{k}{v}" for k, v in sorted(params.items()) if k != "api_key")
    return f"{slug}_{param_str}.json"


def _read_cache(key: str) -> Optional[dict]:
    """Read from disk cache if fresh enough."""
    path = CACHE_DIR / key
    if not path.exists():
        return None
    age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
    if age_hours > CACHE_TTL_HOURS:
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(key: str, data: dict) -> None:
    """Write data to disk cache."""
    try:
        (CACHE_DIR / key).write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _api_request(endpoint: str, params: Optional[Dict[str, Any]] = None,
                 use_cache: bool = True) -> Dict[str, Any]:
    """
    Make an API request to Nasdaq Data Link.
    Uses the nasdaqdatalink library if available, else falls back to requests.

    Args:
        endpoint: Path after /api/v3/ (e.g. 'datasets/NSE/TATAMOTORS.json')
        params: Query parameters
        use_cache: Whether to use disk cache

    Returns:
        Parsed JSON response dict, or dict with 'error' key on failure.
    """
    if params is None:
        params = {}

    # Check cache
    if use_cache:
        ck = _cache_key(endpoint, params)
        cached = _read_cache(ck)
        if cached:
            cached["_from_cache"] = True
            return cached

    # Add API key
    if API_KEY:
        params["api_key"] = API_KEY

    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "User-Agent": "QuantClaw-DataModule/2.0 (Python/requests)",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Cache successful responses
        if use_cache and "error" not in data:
            _write_cache(_cache_key(endpoint, params), data)
        return data
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else None
        if code == 403:
            return {
                "error": "Access denied (403). Likely blocked by WAF or missing API key.",
                "hint": "Register free at https://data.nasdaq.com/ and set NASDAQ_DATA_LINK_API_KEY env var.",
                "status_code": 403,
            }
        if code == 429:
            return {"error": "Rate limited (429). Free tier allows 50 calls/day.", "status_code": 429}
        return {"error": str(e), "status_code": code}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}


def _lib_request(database: str, dataset: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Try fetching via the nasdaqdatalink library (handles auth/retries better).
    Returns None if library not available or fails.
    """
    if not _HAS_NDL_LIB:
        return None
    if API_KEY:
        nasdaqdatalink.ApiConfig.api_key = API_KEY
    try:
        df = nasdaqdatalink.get(f"{database}/{dataset}", **kwargs)
        records = df.reset_index().to_dict(orient="records")
        # Convert timestamps
        for r in records:
            for k, v in r.items():
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        return {
            "dataset": {
                "database_code": database,
                "dataset_code": dataset,
                "column_names": list(df.columns),
                "data": records,
                "name": f"{database}/{dataset}",
                "_fetched_at": datetime.utcnow().isoformat(),
                "_source": "nasdaqdatalink_lib",
            }
        }
    except Exception:
        return None


# ── Public API ──────────────────────────────────────────────────────────────

def get_dataset(database: str, dataset: str, start_date: Optional[str] = None,
                end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch a dataset from Nasdaq Data Link.

    Args:
        database: Database code ('NSE', 'BSE', 'HKEX', 'WIKI', etc.)
        dataset: Dataset/symbol code (e.g. 'TATAMOTORS', 'AAPL')
        start_date: Start date YYYY-MM-DD (optional)
        end_date: End date YYYY-MM-DD (optional)
        limit: Max rows (default 100)

    Returns:
        Dict with 'dataset' key containing metadata + data rows,
        or 'error' key on failure.

    Example:
        >>> data = get_dataset('NSE', 'TATAMOTORS', limit=5)
    """
    # Try library first
    lib_kwargs = {"rows": limit}
    if start_date:
        lib_kwargs["start_date"] = start_date
    if end_date:
        lib_kwargs["end_date"] = end_date
    lib_result = _lib_request(database, dataset, **lib_kwargs)
    if lib_result and "dataset" in lib_result:
        return lib_result

    # Fallback to REST
    params: Dict[str, Any] = {"limit": limit}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    result = _api_request(f"datasets/{database}/{dataset}.json", params)
    if "dataset" in result:
        result["dataset"]["_fetched_at"] = datetime.utcnow().isoformat()
    return result


def get_nse_stock(symbol: str, start_date: Optional[str] = None,
                  end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch Indian NSE stock data.

    Args:
        symbol: NSE symbol (e.g. 'TATAMOTORS', 'RELIANCE', 'INFY')
        start_date: YYYY-MM-DD (optional)
        end_date: YYYY-MM-DD (optional)
        limit: Max rows

    Returns:
        Dict with OHLCV data or error.
    """
    return get_dataset("NSE", symbol.upper(), start_date, end_date, limit)


def get_bse_stock(symbol: str, start_date: Optional[str] = None,
                  end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch Indian BSE stock data.

    Args:
        symbol: BSE symbol (e.g. 'BOM500325')
        start_date: YYYY-MM-DD (optional)
        end_date: YYYY-MM-DD (optional)
        limit: Max rows
    """
    return get_dataset("BSE", symbol.upper(), start_date, end_date, limit)


def get_hkex_stock(symbol: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch Hong Kong HKEX stock data.

    Args:
        symbol: HKEX code (e.g. '00700' for Tencent)
        start_date: YYYY-MM-DD (optional)
        end_date: YYYY-MM-DD (optional)
        limit: Max rows
    """
    return get_dataset("HKEX", symbol, start_date, end_date, limit)


def search_datasets(query: str, per_page: int = 10, page: int = 1) -> Dict[str, Any]:
    """
    Search Nasdaq Data Link for datasets matching a query.

    Args:
        query: Search string (e.g. 'india stock', 'emerging market')
        per_page: Results per page (max 100)
        page: Page number

    Returns:
        Dict with 'datasets' list or 'error'.

    Example:
        >>> results = search_datasets('india nse', per_page=5)
    """
    params = {"query": query, "per_page": min(per_page, 100), "page": page}
    result = _api_request("datasets.json", params)
    result["_query"] = query
    return result


def get_emerging_market_index(market: str, start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               limit: int = 100) -> Dict[str, Any]:
    """
    Fetch a major emerging market index.

    Args:
        market: One of 'india_nifty50', 'india_sensex', 'hong_kong_hsi'
        start_date: YYYY-MM-DD (optional)
        end_date: YYYY-MM-DD (optional)
        limit: Max rows

    Returns:
        Dict with index data or error. Use list_indices() for valid markets.
    """
    key = market.lower()
    if key not in EM_INDICES:
        return {
            "error": f"Unknown index '{market}'",
            "valid_indices": list(EM_INDICES.keys()),
        }
    db, ds = EM_INDICES[key]
    return get_dataset(db, ds, start_date, end_date, limit)


def get_dataset_metadata(database: str, dataset: str) -> Dict[str, Any]:
    """
    Fetch metadata only (no data rows) for a dataset.

    Args:
        database: Database code
        dataset: Dataset code

    Returns:
        Dict with metadata (description, columns, frequency, etc.)
    """
    return _api_request(f"datasets/{database}/{dataset}/metadata.json")


def get_latest_price(database: str, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent data row for a symbol as a column→value dict.

    Args:
        database: Database code ('NSE', 'BSE', etc.)
        symbol: Stock symbol

    Returns:
        Dict mapping column names to values, or None on failure.

    Example:
        >>> p = get_latest_price('NSE', 'TATAMOTORS')
        >>> if p: print(p.get('Close'))
    """
    result = get_dataset(database, symbol, limit=1)
    if "error" in result or "dataset" not in result:
        return None
    ds = result["dataset"]
    # Handle both library (list-of-dicts) and REST (list-of-lists) formats
    data = ds.get("data")
    if not data:
        return None
    row = data[0]
    if isinstance(row, dict):
        row["_symbol"] = symbol
        row["_database"] = database
        return row
    columns = ds.get("column_names", [])
    mapped = dict(zip(columns, row))
    mapped["_symbol"] = symbol
    mapped["_database"] = database
    return mapped


def list_databases() -> Dict[str, str]:
    """Return supported emerging-market database codes and descriptions."""
    return EM_DATABASES.copy()


def list_indices() -> Dict[str, tuple]:
    """Return supported index identifiers and their (database, dataset) codes."""
    return EM_INDICES.copy()


def list_popular_stocks(database: str = "NSE") -> List[str]:
    """
    Return popular stock symbols for a given database.

    Args:
        database: Database code (default 'NSE')

    Returns:
        List of symbol strings.
    """
    return EM_POPULAR_STOCKS.get(database.upper(), [])


def get_module_info() -> Dict[str, Any]:
    """Return module metadata."""
    return {
        "module": "nasdaq_emerging_markets",
        "version": "2.0.0",
        "source": "https://data.nasdaq.com/",
        "category": "Emerging Markets",
        "free_tier": True,
        "api_key_required": False,
        "api_key_configured": bool(API_KEY),
        "ndl_library_available": _HAS_NDL_LIB,
        "cache_dir": str(CACHE_DIR),
        "databases": list(EM_DATABASES.keys()),
        "indices": list(EM_INDICES.keys()),
        "functions": [
            "get_dataset", "get_nse_stock", "get_bse_stock", "get_hkex_stock",
            "search_datasets", "get_emerging_market_index", "get_dataset_metadata",
            "get_latest_price", "list_databases", "list_indices",
            "list_popular_stocks", "get_module_info",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
