"""
Alpha Vantage International Stocks — Emerging Markets & Global Equities

Tracks international stock prices including India NSE (.NS), Brazil (.SA), 
China A-shares with intraday and daily data.

Data: https://www.alphavantage.co/query
Free tier: 5 calls/min, 500/day

Use cases:
- Emerging market stock prices
- International intraday data
- Global quote lookup
- FX rates for emerging currencies
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json
import time

CACHE_DIR = Path(__file__).parent.parent / "cache" / "av_intl_stocks"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")


def _make_request(params: Dict, cache_key: str, cache_ttl_hours: int = 1) -> Optional[Dict]:
    """Make API request with caching."""
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_ttl_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Add API key to params
    params['apikey'] = API_KEY
    
    # Fetch from API
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return None
        
        if "Note" in data:
            print(f"API Note (rate limit?): {data['Note']}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching Alpha Vantage data: {e}")
        return None


def get_quote(symbol: str) -> Optional[Dict]:
    """
    Get current price quote for international stock.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS, PETR4.SA, 000001.SZ)
        
    Returns:
        Dict with quote data: price, change, volume, etc.
    """
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol
    }
    
    cache_key = f"quote_{symbol.replace('.', '_')}"
    data = _make_request(params, cache_key, cache_ttl_hours=1)
    
    if not data or "Global Quote" not in data:
        return None
    
    quote = data["Global Quote"]
    if not quote:
        return None
    
    # Clean up the keys (remove numeric prefixes)
    clean_quote = {
        "symbol": quote.get("01. symbol", ""),
        "price": float(quote.get("05. price", 0)),
        "open": float(quote.get("02. open", 0)),
        "high": float(quote.get("03. high", 0)),
        "low": float(quote.get("04. low", 0)),
        "volume": int(quote.get("06. volume", 0)),
        "latest_trading_day": quote.get("07. latest trading day", ""),
        "previous_close": float(quote.get("08. previous close", 0)),
        "change": float(quote.get("09. change", 0)),
        "change_percent": quote.get("10. change percent", "").rstrip('%')
    }
    
    return clean_quote


def get_daily_prices(symbol: str, outputsize: str = "compact") -> pd.DataFrame:
    """
    Get daily OHLCV data for international stock.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS)
        outputsize: "compact" (100 days) or "full" (20+ years)
        
    Returns:
        DataFrame with date, open, high, low, close, volume
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": outputsize
    }
    
    cache_key = f"daily_{symbol.replace('.', '_')}_{outputsize}"
    cache_ttl = 24 if outputsize == "full" else 6
    
    data = _make_request(params, cache_key, cache_ttl_hours=cache_ttl)
    
    if not data or "Time Series (Daily)" not in data:
        return pd.DataFrame()
    
    timeseries = data["Time Series (Daily)"]
    
    # Convert to DataFrame
    records = []
    for date_str, values in timeseries.items():
        records.append({
            "date": date_str,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"])
        })
    
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    
    return df


def get_intraday(symbol: str, interval: str = "5min") -> pd.DataFrame:
    """
    Get intraday prices for international stock.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS)
        interval: "1min", "5min", "15min", "30min", "60min"
        
    Returns:
        DataFrame with timestamp, open, high, low, close, volume
    """
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "outputsize": "compact"
    }
    
    cache_key = f"intraday_{symbol.replace('.', '_')}_{interval}"
    
    data = _make_request(params, cache_key, cache_ttl_hours=1)
    
    if not data:
        return pd.DataFrame()
    
    # Find the time series key
    ts_key = f"Time Series ({interval})"
    if ts_key not in data:
        return pd.DataFrame()
    
    timeseries = data[ts_key]
    
    # Convert to DataFrame
    records = []
    for timestamp, values in timeseries.items():
        records.append({
            "timestamp": timestamp,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"])
        })
    
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    
    return df


def search_international(keywords: str) -> List[Dict]:
    """
    Search for international stock symbols.
    
    Args:
        keywords: Search term (e.g., "Reliance", "Petrobras")
        
    Returns:
        List of matching symbols with metadata
    """
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keywords
    }
    
    cache_key = f"search_{keywords.replace(' ', '_').lower()}"
    
    data = _make_request(params, cache_key, cache_ttl_hours=168)  # 1 week cache
    
    if not data or "bestMatches" not in data:
        return []
    
    matches = data["bestMatches"]
    
    # Clean up results
    results = []
    for match in matches:
        results.append({
            "symbol": match.get("1. symbol", ""),
            "name": match.get("2. name", ""),
            "type": match.get("3. type", ""),
            "region": match.get("4. region", ""),
            "market_open": match.get("5. marketOpen", ""),
            "market_close": match.get("6. marketClose", ""),
            "timezone": match.get("7. timezone", ""),
            "currency": match.get("8. currency", ""),
            "match_score": float(match.get("9. matchScore", 0))
        })
    
    return results


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[Dict]:
    """
    Get FX exchange rate for emerging market currencies.
    
    Args:
        from_currency: From currency code (e.g., INR, BRL, CNY)
        to_currency: To currency code (e.g., USD, EUR)
        
    Returns:
        Dict with exchange rate data
    """
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency,
        "to_currency": to_currency
    }
    
    cache_key = f"fx_{from_currency}_{to_currency}"
    
    data = _make_request(params, cache_key, cache_ttl_hours=1)
    
    if not data or "Realtime Currency Exchange Rate" not in data:
        return None
    
    rate_data = data["Realtime Currency Exchange Rate"]
    
    result = {
        "from_currency": rate_data.get("1. From_Currency Code", ""),
        "from_name": rate_data.get("2. From_Currency Name", ""),
        "to_currency": rate_data.get("3. To_Currency Code", ""),
        "to_name": rate_data.get("4. To_Currency Name", ""),
        "rate": float(rate_data.get("5. Exchange Rate", 0)),
        "last_refreshed": rate_data.get("6. Last Refreshed", ""),
        "timezone": rate_data.get("7. Time Zone", ""),
        "bid": float(rate_data.get("8. Bid Price", 0)),
        "ask": float(rate_data.get("9. Ask Price", 0))
    }
    
    return result


# CLI functions
def cli_quote(symbol: str):
    """CLI: Display current quote."""
    quote = get_quote(symbol)
    if not quote:
        print(f"No data for {symbol}")
        return
    
    print(f"\n=== {quote['symbol']} Quote ===")
    print(f"Price: {quote['price']:.2f}")
    print(f"Change: {quote['change']:+.2f} ({quote['change_percent']}%)")
    print(f"Open: {quote['open']:.2f} | High: {quote['high']:.2f} | Low: {quote['low']:.2f}")
    print(f"Volume: {quote['volume']:,}")
    print(f"Previous Close: {quote['previous_close']:.2f}")
    print(f"Latest: {quote['latest_trading_day']}")


def cli_daily(symbol: str, days: int = 10):
    """CLI: Display daily prices."""
    df = get_daily_prices(symbol)
    if df.empty:
        print(f"No data for {symbol}")
        return
    
    print(f"\n=== {symbol} Daily Prices (last {days} days) ===")
    display_df = df.head(days)[["date", "close", "volume"]]
    print(display_df.to_string(index=False))


def cli_search(keywords: str):
    """CLI: Search for symbols."""
    results = search_international(keywords)
    if not results:
        print(f"No matches for '{keywords}'")
        return
    
    print(f"\n=== Search: {keywords} ===")
    for i, match in enumerate(results[:10], 1):
        print(f"{i}. {match['symbol']:12s} {match['name'][:40]:40s} | {match['region']:15s} | {match['currency']}")


def cli_fx(from_curr: str, to_curr: str = "USD"):
    """CLI: Display exchange rate."""
    rate = get_exchange_rate(from_curr, to_curr)
    if not rate:
        print(f"No rate for {from_curr}/{to_curr}")
        return
    
    print(f"\n=== FX Rate ===")
    print(f"{rate['from_currency']} → {rate['to_currency']}: {rate['rate']:.6f}")
    print(f"Bid: {rate['bid']:.6f} | Ask: {rate['ask']:.6f}")
    print(f"Updated: {rate['last_refreshed']} {rate['timezone']}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Alpha Vantage International Stocks Module")
        print("Commands: quote, daily, search, fx")
        sys.exit(0)
    
    command = args[0]
    
    if command == "quote" and len(args) > 1:
        cli_quote(args[1])
    elif command == "daily" and len(args) > 1:
        days = int(args[2]) if len(args) > 2 else 10
        cli_daily(args[1], days)
    elif command == "search" and len(args) > 1:
        cli_search(args[1])
    elif command == "fx" and len(args) > 1:
        to_curr = args[2] if len(args) > 2 else "USD"
        cli_fx(args[1], to_curr)
    else:
        print(f"Unknown command or missing args: {' '.join(args)}")
        print("Usage:")
        print("  quote <SYMBOL>")
        print("  daily <SYMBOL> [days]")
        print("  search <KEYWORDS>")
        print("  fx <FROM_CURRENCY> [TO_CURRENCY]")
        sys.exit(1)
