"""
Alpha Vantage Global Markets — International indices, forex, and cross-listed equities.

Access global market data including international stock exchanges, currency exchange
rates, forex pairs, and market status across worldwide exchanges. Covers emerging
markets (India, Brazil, China, Japan) and developed markets (US, UK, Germany).

Source: https://www.alphavantage.co/documentation/
Update frequency: Real-time (5 min delay on free tier)
Category: Quant Tools & ML
Free tier: 5 API calls/min, 500 calls/day (requires free API key)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://www.alphavantage.co/query"
# Demo key for testing - replace with real key for production
DEMO_KEY = "demo"

# Major global indices mapped to their Alpha Vantage symbols
GLOBAL_INDICES = {
    "SP500": {"symbol": "SPY", "name": "S&P 500 (ETF proxy)", "exchange": "NYSE", "country": "US"},
    "NASDAQ": {"symbol": "QQQ", "name": "NASDAQ 100 (ETF proxy)", "exchange": "NASDAQ", "country": "US"},
    "DOW": {"symbol": "DIA", "name": "Dow Jones (ETF proxy)", "exchange": "NYSE", "country": "US"},
    "FTSE100": {"symbol": "ISF.LON", "name": "FTSE 100 (ETF proxy)", "exchange": "LSE", "country": "UK"},
    "DAX": {"symbol": "DAX.DEX", "name": "DAX 40", "exchange": "XETRA", "country": "Germany"},
    "NIKKEI": {"symbol": "1321.TYO", "name": "Nikkei 225 (ETF proxy)", "exchange": "TSE", "country": "Japan"},
    "HANGSENG": {"symbol": "2800.HKG", "name": "Hang Seng (ETF proxy)", "exchange": "HKEX", "country": "Hong Kong"},
    "SENSEX": {"symbol": "SENSEX.BSE", "name": "BSE Sensex", "exchange": "BSE", "country": "India"},
    "NIFTY50": {"symbol": "NIFTY50.NS", "name": "Nifty 50", "exchange": "NSE", "country": "India"},
    "ASX200": {"symbol": "STW.AX", "name": "ASX 200 (ETF proxy)", "exchange": "ASX", "country": "Australia"},
    "CAC40": {"symbol": "CAC.PAR", "name": "CAC 40", "exchange": "Euronext Paris", "country": "France"},
    "IBOVESPA": {"symbol": "BOVA11.SAO", "name": "Ibovespa (ETF proxy)", "exchange": "B3", "country": "Brazil"},
    "TSX": {"symbol": "XIU.TRT", "name": "TSX 60 (ETF proxy)", "exchange": "TSX", "country": "Canada"},
    "KOSPI": {"symbol": "069500.KRX", "name": "KOSPI (ETF proxy)", "exchange": "KRX", "country": "South Korea"},
}


def _api_request(params: dict) -> dict[str, Any]:
    """
    Internal helper for Alpha Vantage API requests.

    Args:
        params: Query parameters dict (function, symbol, etc.)

    Returns:
        Parsed JSON response as dict
    """
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())

            if "Error Message" in data:
                return {"error": data["Error Message"]}

            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}

            if "Information" in data:
                return {"error": data["Information"]}

            return data
    except Exception as e:
        return {"error": str(e)}


def get_market_status(
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get current open/close status of major global stock exchanges.

    Args:
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with list of exchanges and their open/close status

    Example:
        >>> status = get_market_status()
        >>> for mkt in status.get('markets', []):
        ...     print(mkt['region'], mkt['market_type'], mkt['current_status'])
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "MARKET_STATUS",
        "apikey": key
    })

    if "error" in data:
        return data

    markets = data.get("markets", [])
    parsed = []
    for m in markets:
        parsed.append({
            "market_type": m.get("market_type"),
            "region": m.get("region"),
            "primary_exchanges": m.get("primary_exchanges"),
            "local_open": m.get("local_open"),
            "local_close": m.get("local_close"),
            "current_status": m.get("current_status"),
            "notes": m.get("notes"),
        })

    return {
        "count": len(parsed),
        "markets": parsed,
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_forex_rate(
    from_currency: str,
    to_currency: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g., 'USD', 'EUR', 'BTC')
        to_currency: Target currency code (e.g., 'JPY', 'GBP', 'INR')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with exchange rate, bid/ask prices

    Example:
        >>> rate = get_forex_rate('USD', 'JPY')
        >>> print(rate.get('exchange_rate'), rate.get('bid_price'))
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency,
        "to_currency": to_currency,
        "apikey": key
    })

    if "error" in data:
        return data

    rate_data = data.get("Realtime Currency Exchange Rate", {})
    if not rate_data:
        return {"error": "No data returned", "from": from_currency, "to": to_currency}

    return {
        "from_currency": rate_data.get("1. From_Currency Code"),
        "from_name": rate_data.get("2. From_Currency Name"),
        "to_currency": rate_data.get("3. To_Currency Code"),
        "to_name": rate_data.get("4. To_Currency Name"),
        "exchange_rate": float(rate_data.get("5. Exchange Rate", 0)),
        "last_refreshed": rate_data.get("6. Last Refreshed"),
        "timezone": rate_data.get("7. Time Zone"),
        "bid_price": float(rate_data.get("8. Bid Price", 0)),
        "ask_price": float(rate_data.get("9. Ask Price", 0)),
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_forex_daily(
    from_symbol: str,
    to_symbol: str,
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get daily historical forex data for a currency pair.

    Args:
        from_symbol: Source currency code (e.g., 'EUR')
        to_symbol: Target currency code (e.g., 'USD')
        outputsize: 'compact' (100 days) or 'full' (20+ years)
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with daily OHLC forex data

    Example:
        >>> data = get_forex_daily('EUR', 'USD')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "FX_DAILY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "outputsize": outputsize,
        "apikey": key
    })

    if "error" in data:
        return data

    time_series = data.get("Time Series FX (Daily)", {})
    if not time_series:
        return {"error": "No data returned", "pair": f"{from_symbol}/{to_symbol}"}

    prices = []
    for date_str, values in time_series.items():
        prices.append({
            "date": date_str,
            "open": float(values.get("1. open", 0)),
            "high": float(values.get("2. high", 0)),
            "low": float(values.get("3. low", 0)),
            "close": float(values.get("4. close", 0)),
        })

    prices.sort(key=lambda x: x["date"], reverse=True)

    meta = data.get("Meta Data", {})
    return {
        "from_symbol": meta.get("2. From Symbol"),
        "to_symbol": meta.get("3. To Symbol"),
        "last_refreshed": meta.get("5. Last Refreshed"),
        "count": len(prices),
        "prices": prices,
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_forex_intraday(
    from_symbol: str,
    to_symbol: str,
    interval: str = "5min",
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get intraday forex data at specified intervals.

    Args:
        from_symbol: Source currency code (e.g., 'EUR')
        to_symbol: Target currency code (e.g., 'USD')
        interval: '1min', '5min', '15min', '30min', '60min'
        outputsize: 'compact' (latest 100) or 'full' (trailing month)
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with intraday OHLC forex data

    Example:
        >>> data = get_forex_intraday('EUR', 'USD', interval='15min')
        >>> print(data.get('count'))
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "FX_INTRADAY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": key
    })

    if "error" in data:
        return data

    ts_key = f"Time Series FX (Intraday)"
    time_series = data.get(ts_key, {})
    if not time_series:
        return {"error": "No data returned", "pair": f"{from_symbol}/{to_symbol}"}

    prices = []
    for ts, values in time_series.items():
        prices.append({
            "timestamp": ts,
            "open": float(values.get("1. open", 0)),
            "high": float(values.get("2. high", 0)),
            "low": float(values.get("3. low", 0)),
            "close": float(values.get("4. close", 0)),
        })

    prices.sort(key=lambda x: x["timestamp"], reverse=True)

    meta = data.get("Meta Data", {})
    return {
        "from_symbol": meta.get("2. From Symbol"),
        "to_symbol": meta.get("3. To Symbol"),
        "interval": meta.get("4. Interval"),
        "last_refreshed": meta.get("5. Last Refreshed"),
        "count": len(prices),
        "prices": prices,
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_global_index_quote(
    index_key: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time quote for a major global index via ETF proxy.

    Args:
        index_key: Key from GLOBAL_INDICES (e.g., 'SP500', 'NIKKEI', 'DAX')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with index price data and metadata

    Example:
        >>> quote = get_global_index_quote('SP500')
        >>> print(quote.get('index_name'), quote.get('price'))
    """
    key = apikey or DEMO_KEY

    index_info = GLOBAL_INDICES.get(index_key.upper())
    if not index_info:
        return {
            "error": f"Unknown index key: {index_key}",
            "available_indices": list(GLOBAL_INDICES.keys())
        }

    data = _api_request({
        "function": "GLOBAL_QUOTE",
        "symbol": index_info["symbol"],
        "apikey": key
    })

    if "error" in data:
        return data

    quote = data.get("Global Quote", {})
    if not quote:
        return {"error": "No data returned", "index": index_key}

    return {
        "index_key": index_key,
        "index_name": index_info["name"],
        "exchange": index_info["exchange"],
        "country": index_info["country"],
        "symbol": quote.get("01. symbol"),
        "price": float(quote.get("05. price", 0)),
        "volume": int(quote.get("06. volume", 0)),
        "change": float(quote.get("09. change", 0)),
        "change_percent": quote.get("10. change percent", "0%").rstrip('%'),
        "open": float(quote.get("02. open", 0)),
        "high": float(quote.get("03. high", 0)),
        "low": float(quote.get("04. low", 0)),
        "previous_close": float(quote.get("08. previous close", 0)),
        "latest_trading_day": quote.get("07. latest trading day"),
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def list_global_indices() -> dict[str, Any]:
    """
    List all available global index keys and their metadata.

    Returns:
        dict with list of available indices

    Example:
        >>> indices = list_global_indices()
        >>> for idx in indices['indices']:
        ...     print(idx['key'], idx['name'], idx['country'])
    """
    indices = []
    for key, info in GLOBAL_INDICES.items():
        indices.append({
            "key": key,
            "symbol": info["symbol"],
            "name": info["name"],
            "exchange": info["exchange"],
            "country": info["country"]
        })

    return {
        "count": len(indices),
        "indices": indices,
        "timestamp": datetime.now().isoformat()
    }


def get_global_index_daily(
    index_key: str,
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get daily historical data for a global index via ETF proxy.

    Args:
        index_key: Key from GLOBAL_INDICES (e.g., 'NIKKEI', 'FTSE100')
        outputsize: 'compact' (100 days) or 'full' (20+ years)
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with daily OHLCV data for the index proxy

    Example:
        >>> data = get_global_index_daily('DAX')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    key = apikey or DEMO_KEY

    index_info = GLOBAL_INDICES.get(index_key.upper())
    if not index_info:
        return {
            "error": f"Unknown index key: {index_key}",
            "available_indices": list(GLOBAL_INDICES.keys())
        }

    data = _api_request({
        "function": "TIME_SERIES_DAILY",
        "symbol": index_info["symbol"],
        "outputsize": outputsize,
        "apikey": key
    })

    if "error" in data:
        return data

    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        return {"error": "No data returned", "index": index_key}

    prices = []
    for date_str, values in time_series.items():
        prices.append({
            "date": date_str,
            "open": float(values.get("1. open", 0)),
            "high": float(values.get("2. high", 0)),
            "low": float(values.get("3. low", 0)),
            "close": float(values.get("4. close", 0)),
            "volume": int(values.get("5. volume", 0))
        })

    prices.sort(key=lambda x: x["date"], reverse=True)

    meta = data.get("Meta Data", {})
    return {
        "index_key": index_key,
        "index_name": index_info["name"],
        "exchange": index_info["exchange"],
        "country": index_info["country"],
        "symbol": meta.get("2. Symbol"),
        "last_refreshed": meta.get("3. Last Refreshed"),
        "count": len(prices),
        "prices": prices,
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_listing_status(
    state: str = "active",
    exchange: Optional[str] = None,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get list of active or delisted stocks from US exchanges.

    Args:
        state: 'active' or 'delisted'
        exchange: Filter by exchange (e.g., 'NYSE', 'NASDAQ', 'AMEX') or None for all
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with list of listed/delisted securities

    Example:
        >>> listings = get_listing_status(state='active')
        >>> print(listings.get('count'))
    """
    key = apikey or DEMO_KEY

    params = {
        "function": "LISTING_STATUS",
        "state": state,
        "apikey": key
    }

    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode()

            # This endpoint returns CSV
            lines = content.strip().split('\n')
            if len(lines) < 2:
                return {"error": "No data returned", "state": state}

            headers = lines[0].split(',')
            listings = []
            for line in lines[1:]:
                values = line.split(',')
                if len(values) >= len(headers):
                    row = dict(zip(headers, values))
                    if exchange and row.get("exchange", "").upper() != exchange.upper():
                        continue
                    listings.append(row)

            return {
                "state": state,
                "exchange_filter": exchange,
                "count": len(listings),
                "listings": listings[:100],  # Cap at 100 for response size
                "total_available": len(listings),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {"error": str(e), "state": state}


def get_top_gainers_losers(
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get top gainers, losers, and most actively traded tickers (US market).

    Args:
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with top gainers, losers, and most active tickers

    Example:
        >>> movers = get_top_gainers_losers()
        >>> print(movers.get('top_gainers')[:3])
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "TOP_GAINERS_LOSERS",
        "apikey": key
    })

    if "error" in data:
        return data

    def _parse_movers(items: list) -> list:
        parsed = []
        for item in items:
            parsed.append({
                "ticker": item.get("ticker"),
                "price": item.get("price"),
                "change_amount": item.get("change_amount"),
                "change_percentage": item.get("change_percentage", "").rstrip('%'),
                "volume": item.get("volume"),
            })
        return parsed

    return {
        "metadata": data.get("metadata"),
        "last_updated": data.get("last_updated"),
        "top_gainers": _parse_movers(data.get("top_gainers", [])),
        "top_losers": _parse_movers(data.get("top_losers", [])),
        "most_actively_traded": _parse_movers(data.get("most_actively_traded", [])),
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


def get_crypto_exchange_rate(
    from_currency: str,
    to_currency: str = "USD",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time exchange rate for a cryptocurrency pair.

    Args:
        from_currency: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
        to_currency: Target currency (e.g., 'USD', 'EUR', 'JPY')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with real-time crypto exchange rate

    Example:
        >>> rate = get_crypto_exchange_rate('BTC', 'USD')
        >>> print(rate.get('exchange_rate'))
    """
    # Uses same endpoint as forex
    return get_forex_rate(from_currency, to_currency, apikey)


def get_crypto_daily(
    symbol: str,
    market: str = "USD",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get daily historical data for a cryptocurrency.

    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH')
        market: Exchange currency (e.g., 'USD', 'EUR')
        apikey: Alpha Vantage API key (uses demo if not provided)

    Returns:
        dict with daily OHLCV crypto data

    Example:
        >>> data = get_crypto_daily('BTC', 'USD')
        >>> print(data.get('count'), data.get('prices')[0])
    """
    key = apikey or DEMO_KEY

    data = _api_request({
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": symbol,
        "market": market,
        "apikey": key
    })

    if "error" in data:
        return data

    time_series = data.get("Time Series (Digital Currency Daily)", {})
    if not time_series:
        return {"error": "No data returned", "symbol": symbol}

    prices = []
    for date_str, values in time_series.items():
        prices.append({
            "date": date_str,
            "open": float(values.get(f"1a. open ({market})", 0)),
            "high": float(values.get(f"2a. high ({market})", 0)),
            "low": float(values.get(f"3a. low ({market})", 0)),
            "close": float(values.get(f"4a. close ({market})", 0)),
            "volume": float(values.get("5. volume", 0)),
            "market_cap": float(values.get("6. market cap (USD)", 0)),
        })

    prices.sort(key=lambda x: x["date"], reverse=True)

    meta = data.get("Meta Data", {})
    return {
        "symbol": meta.get("2. Digital Currency Code"),
        "name": meta.get("3. Digital Currency Name"),
        "market": meta.get("4. Market Code"),
        "last_refreshed": meta.get("6. Last Refreshed"),
        "count": len(prices),
        "prices": prices,
        "timestamp": datetime.now().isoformat(),
        "raw": data
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "alpha_vantage_global_markets_api",
        "status": "implemented",
        "source": "https://www.alphavantage.co/documentation/",
        "functions": [
            "get_market_status",
            "get_forex_rate",
            "get_forex_daily",
            "get_forex_intraday",
            "get_global_index_quote",
            "list_global_indices",
            "get_global_index_daily",
            "get_listing_status",
            "get_top_gainers_losers",
            "get_crypto_exchange_rate",
            "get_crypto_daily"
        ]
    }, indent=2))
