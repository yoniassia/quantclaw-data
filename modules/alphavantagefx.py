"""
Alpha Vantage FX — Forex market data from Alpha Vantage free tier.

Real-time and historical foreign exchange rate data for 150+ currency pairs.
Covers exchange rates, intraday/daily/weekly/monthly OHLC, and currency lists.

Source: https://www.alphavantage.co/documentation/#fx
Update frequency: Real-time (5 min delay on free tier)
Category: Quant Tools & ML
Free tier: 25 API calls/day (requires free API key)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://www.alphavantage.co/query"
# Demo key for testing - replace with real key for production
DEMO_KEY = "demo"


def _fetch(params: dict) -> dict:
    """Internal helper to fetch and parse Alpha Vantage API response."""
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as response:
        data = json.loads(response.read().decode())

    if "Error Message" in data:
        raise ValueError(data["Error Message"])

    if "Note" in data:
        raise ValueError(f"API rate limit exceeded: {data['Note']}")

    if "Information" in data:
        raise ValueError(f"API limit: {data['Information']}")

    return data


def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time exchange rate for a currency pair.

    Args:
        from_currency: Source currency code (e.g., 'EUR', 'GBP', 'BTC')
        to_currency: Target currency code (e.g., 'USD', 'JPY')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with exchange rate, bid/ask, and timestamp

    Example:
        >>> rate = get_exchange_rate('EUR', 'USD')
        >>> print(rate.get('rate'), rate.get('bid'), rate.get('ask'))
    """
    pair = f"{from_currency.upper()}/{to_currency.upper()}"
    try:
        data = _fetch({
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "apikey": apikey or DEMO_KEY
        })

        info = data.get("Realtime Currency Exchange Rate", {})
        if not info:
            return {"error": "No data returned", "pair": pair}

        return {
            "from_currency": info.get("1. From_Currency Code"),
            "from_name": info.get("2. From_Currency Name"),
            "to_currency": info.get("3. To_Currency Code"),
            "to_name": info.get("4. To_Currency Name"),
            "rate": float(info.get("5. Exchange Rate", 0)),
            "last_refreshed": info.get("6. Last Refreshed"),
            "timezone": info.get("7. Time Zone"),
            "bid": float(info.get("8. Bid Price", 0)),
            "ask": float(info.get("9. Ask Price", 0)),
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "pair": pair}


def _parse_fx_series(data: dict, ts_key: str, pair: str, date_field: str = "date") -> list:
    """Parse time series data into a sorted list of price dicts."""
    time_series = data.get(ts_key, {})
    if not time_series:
        return []

    prices = []
    for dt, values in time_series.items():
        prices.append({
            date_field: dt,
            "open": float(values.get("1. open", 0)),
            "high": float(values.get("2. high", 0)),
            "low": float(values.get("3. low", 0)),
            "close": float(values.get("4. close", 0))
        })

    prices.sort(key=lambda x: x[date_field], reverse=True)
    return prices


def get_fx_intraday(
    from_symbol: str,
    to_symbol: str,
    interval: str = "5min",
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get intraday forex OHLC data at specified intervals.

    Args:
        from_symbol: Source currency code (e.g., 'EUR')
        to_symbol: Target currency code (e.g., 'USD')
        interval: '1min', '5min', '15min', '30min', '60min'
        outputsize: 'compact' (latest 100) or 'full' (trailing 30 days)
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with intraday OHLC price data

    Example:
        >>> data = get_fx_intraday('EUR', 'USD', interval='15min')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    pair = f"{from_symbol.upper()}/{to_symbol.upper()}"
    key = apikey or DEMO_KEY

    params = {
        "function": "FX_INTRADAY",
        "from_symbol": from_symbol.upper(),
        "to_symbol": to_symbol.upper(),
        "interval": interval,
        "apikey": key
    }
    if key != DEMO_KEY:
        params["outputsize"] = outputsize

    try:
        data = _fetch(params)

        ts_key = f"Time Series FX ({interval})"
        prices = _parse_fx_series(data, ts_key, pair, date_field="timestamp")
        if not prices:
            return {"error": "No data returned", "pair": pair}

        meta = data.get("Meta Data", {})
        return {
            "pair": pair,
            "interval": meta.get("5. Interval", interval),
            "last_refreshed": meta.get("4. Last Refreshed"),
            "timezone": meta.get("7. Time Zone"),
            "count": len(prices),
            "prices": prices,
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "pair": pair}


def get_fx_daily(
    from_symbol: str,
    to_symbol: str,
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get daily forex OHLC data.

    Args:
        from_symbol: Source currency code (e.g., 'EUR')
        to_symbol: Target currency code (e.g., 'USD')
        outputsize: 'compact' (100 days) or 'full' (20+ years)
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with daily OHLC price data

    Example:
        >>> data = get_fx_daily('GBP', 'USD')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    pair = f"{from_symbol.upper()}/{to_symbol.upper()}"
    key = apikey or DEMO_KEY

    params = {
        "function": "FX_DAILY",
        "from_symbol": from_symbol.upper(),
        "to_symbol": to_symbol.upper(),
        "apikey": key
    }
    if key != DEMO_KEY:
        params["outputsize"] = outputsize

    try:
        data = _fetch(params)

        prices = _parse_fx_series(data, "Time Series FX (Daily)", pair)
        if not prices:
            return {"error": "No data returned", "pair": pair}

        meta = data.get("Meta Data", {})
        return {
            "pair": pair,
            "last_refreshed": meta.get("5. Last Refreshed"),
            "timezone": meta.get("6. Time Zone"),
            "count": len(prices),
            "prices": prices,
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "pair": pair}


def get_fx_weekly(
    from_symbol: str,
    to_symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get weekly forex OHLC data (full history).

    Args:
        from_symbol: Source currency code (e.g., 'EUR')
        to_symbol: Target currency code (e.g., 'USD')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with weekly OHLC price data

    Example:
        >>> data = get_fx_weekly('EUR', 'JPY')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    pair = f"{from_symbol.upper()}/{to_symbol.upper()}"
    try:
        data = _fetch({
            "function": "FX_WEEKLY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "apikey": apikey or DEMO_KEY
        })

        prices = _parse_fx_series(data, "Time Series FX (Weekly)", pair)
        if not prices:
            return {"error": "No data returned", "pair": pair}

        meta = data.get("Meta Data", {})
        return {
            "pair": pair,
            "last_refreshed": meta.get("4. Last Refreshed"),
            "timezone": meta.get("5. Time Zone"),
            "count": len(prices),
            "prices": prices,
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "pair": pair}


def get_fx_monthly(
    from_symbol: str,
    to_symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get monthly forex OHLC data (full history).

    Args:
        from_symbol: Source currency code (e.g., 'GBP')
        to_symbol: Target currency code (e.g., 'JPY')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with monthly OHLC price data

    Example:
        >>> data = get_fx_monthly('GBP', 'JPY')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    pair = f"{from_symbol.upper()}/{to_symbol.upper()}"
    try:
        data = _fetch({
            "function": "FX_MONTHLY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "apikey": apikey or DEMO_KEY
        })

        prices = _parse_fx_series(data, "Time Series FX (Monthly)", pair)
        if not prices:
            return {"error": "No data returned", "pair": pair}

        meta = data.get("Meta Data", {})
        return {
            "pair": pair,
            "last_refreshed": meta.get("4. Last Refreshed"),
            "timezone": meta.get("5. Time Zone"),
            "count": len(prices),
            "prices": prices,
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "pair": pair}


if __name__ == "__main__":
    print(json.dumps({
        "module": "alphavantagefx",
        "status": "implemented",
        "source": "https://www.alphavantage.co/documentation/#fx",
        "functions": [
            "get_exchange_rate",
            "get_fx_intraday",
            "get_fx_daily",
            "get_fx_weekly",
            "get_fx_monthly"
        ]
    }, indent=2))
