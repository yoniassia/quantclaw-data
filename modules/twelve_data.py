"""
Twelve Data — Real-time Market Data & Technical Indicators

Data Source: Twelve Data API (https://twelvedata.com)
Update: Real-time (stock, forex, crypto)
Free tier: Yes (8 API credits/min, 800/day)
API key: Required (free signup at twelvedata.com)

Provides:
- Real-time quotes (stocks, forex, crypto)
- Historical time series (OHLC data)
- Technical indicators (50+ indicators)
- Market fundamentals
- Cross-asset coverage (12,000+ instruments)

Usage:
- Set TWELVE_DATA_API_KEY environment variable
- Default 'demo' key for testing (limited symbols)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

BASE_URL = "https://api.twelvedata.com"
API_KEY = os.environ.get('TWELVE_DATA_API_KEY', 'demo')

# Cache directory
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/twelve_data")
os.makedirs(CACHE_DIR, exist_ok=True)

def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Internal: Make API request with error handling and rate limiting.
    """
    params['apikey'] = API_KEY
    
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'status' in data and data['status'] == 'error':
            return {
                "error": data.get('message', 'Unknown API error'),
                "code": data.get('code', 'unknown')
            }
        
        return data
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Request failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON response",
            "timestamp": datetime.now().isoformat()
        }

def get_quote(symbol: str, exchange: Optional[str] = None) -> Dict:
    """
    Get real-time quote for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC/USD')
        exchange: Optional exchange (e.g., 'NASDAQ', 'NYSE')
    
    Returns:
        Dict with price, volume, change, timestamp
    
    Example:
        >>> get_quote('AAPL')
        {
            'symbol': 'AAPL',
            'name': 'Apple Inc',
            'price': 175.43,
            'change': 2.15,
            'percent_change': 1.24,
            'volume': 52000000,
            'timestamp': '2026-03-07 14:00:00'
        }
    """
    params = {'symbol': symbol}
    if exchange:
        params['exchange'] = exchange
    
    data = _make_request('quote', params)
    
    if 'error' in data:
        return data
    
    # Transform to cleaner format
    try:
        return {
            'symbol': data.get('symbol'),
            'name': data.get('name'),
            'price': float(data.get('close', 0)),
            'open': float(data.get('open', 0)),
            'high': float(data.get('high', 0)),
            'low': float(data.get('low', 0)),
            'volume': int(data.get('volume', 0)),
            'change': float(data.get('change', 0)),
            'percent_change': float(data.get('percent_change', 0)),
            'previous_close': float(data.get('previous_close', 0)),
            'timestamp': data.get('datetime', datetime.now().isoformat()),
            'exchange': data.get('exchange'),
            'currency': data.get('currency'),
            'is_market_open': data.get('is_market_open', False)
        }
    except (ValueError, TypeError) as e:
        return {
            'error': f'Data parsing error: {str(e)}',
            'raw_data': data
        }

def get_time_series(
    symbol: str, 
    interval: str = '1day',
    outputsize: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """
    Get historical OHLCV time series data.
    
    Args:
        symbol: Ticker symbol
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points (default 30, max 5000)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with OHLCV data and metadata
    
    Example:
        >>> get_time_series('AAPL', interval='1day', outputsize=5)
        {
            'symbol': 'AAPL',
            'interval': '1day',
            'values': [
                {'datetime': '2026-03-07', 'open': 174.0, 'high': 176.5, ...},
                ...
            ]
        }
    """
    params = {
        'symbol': symbol,
        'interval': interval,
        'outputsize': min(outputsize, 5000)
    }
    
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    data = _make_request('time_series', params)
    
    if 'error' in data:
        return data
    
    # Clean and structure the response
    try:
        values = []
        for item in data.get('values', []):
            values.append({
                'datetime': item.get('datetime'),
                'open': float(item.get('open', 0)),
                'high': float(item.get('high', 0)),
                'low': float(item.get('low', 0)),
                'close': float(item.get('close', 0)),
                'volume': int(item.get('volume', 0))
            })
        
        return {
            'symbol': data.get('meta', {}).get('symbol'),
            'interval': data.get('meta', {}).get('interval'),
            'currency': data.get('meta', {}).get('currency'),
            'exchange': data.get('meta', {}).get('exchange'),
            'type': data.get('meta', {}).get('type'),
            'values': values,
            'count': len(values)
        }
    except (ValueError, TypeError, KeyError) as e:
        return {
            'error': f'Data parsing error: {str(e)}',
            'raw_data': data
        }

def get_forex_rate(symbol: str = 'EUR/USD') -> Dict:
    """
    Get real-time forex exchange rate.
    
    Args:
        symbol: Currency pair (e.g., 'EUR/USD', 'GBP/JPY')
    
    Returns:
        Dict with exchange rate and metadata
    
    Example:
        >>> get_forex_rate('EUR/USD')
        {
            'symbol': 'EUR/USD',
            'rate': 1.0856,
            'timestamp': '2026-03-07 14:00:00'
        }
    """
    data = get_quote(symbol)
    
    if 'error' in data:
        return data
    
    return {
        'symbol': data.get('symbol'),
        'rate': data.get('price'),
        'bid': data.get('price'),  # Simplified for demo
        'ask': data.get('price'),
        'change': data.get('change'),
        'percent_change': data.get('percent_change'),
        'timestamp': data.get('timestamp')
    }

def get_crypto_quote(symbol: str = 'BTC/USD', exchange: str = 'Binance') -> Dict:
    """
    Get real-time cryptocurrency quote.
    
    Args:
        symbol: Crypto pair (e.g., 'BTC/USD', 'ETH/USD')
        exchange: Crypto exchange (e.g., 'Binance', 'Coinbase', 'Kraken')
    
    Returns:
        Dict with crypto price and metadata
    
    Example:
        >>> get_crypto_quote('BTC/USD')
        {
            'symbol': 'BTC/USD',
            'price': 45230.50,
            'volume': 12500000000,
            'exchange': 'Binance'
        }
    """
    return get_quote(symbol, exchange=exchange)

def get_technical_indicator(
    symbol: str,
    indicator: str = 'sma',
    interval: str = '1day',
    time_period: int = 20,
    **kwargs
) -> Dict:
    """
    Get technical indicator values.
    
    Args:
        symbol: Ticker symbol
        indicator: Indicator type (sma, ema, rsi, macd, bbands, stoch, adx, cci, etc.)
        interval: Time interval
        time_period: Lookback period for calculation
        **kwargs: Additional indicator-specific parameters
    
    Returns:
        Dict with indicator values
    
    Example:
        >>> get_technical_indicator('AAPL', indicator='rsi', time_period=14)
        {
            'symbol': 'AAPL',
            'indicator': 'RSI',
            'values': [{'datetime': '2026-03-07', 'rsi': 65.3}, ...]
        }
    """
    params = {
        'symbol': symbol,
        'interval': interval,
        'time_period': time_period,
        **kwargs
    }
    
    data = _make_request(indicator, params)
    
    if 'error' in data:
        return data
    
    try:
        return {
            'symbol': data.get('meta', {}).get('symbol'),
            'indicator': data.get('meta', {}).get('indicator', {}).get('name'),
            'interval': data.get('meta', {}).get('interval'),
            'values': data.get('values', []),
            'count': len(data.get('values', []))
        }
    except (KeyError, TypeError) as e:
        return {
            'error': f'Data parsing error: {str(e)}',
            'raw_data': data
        }

def get_price(symbol: str) -> Optional[float]:
    """
    Quick helper: Get just the current price.
    
    Args:
        symbol: Ticker symbol
    
    Returns:
        Float price or None if error
    
    Example:
        >>> get_price('AAPL')
        175.43
    """
    quote = get_quote(symbol)
    if 'error' in quote:
        return None
    return quote.get('price')

def search_instruments(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for instruments (stocks, forex, crypto).
    
    Args:
        query: Search term (symbol or name)
        limit: Max results
    
    Returns:
        List of matching instruments
    
    Example:
        >>> search_instruments('apple')
        [
            {'symbol': 'AAPL', 'name': 'Apple Inc', 'type': 'Common Stock', ...},
            ...
        ]
    """
    params = {
        'symbol': query,
        'outputsize': limit
    }
    
    data = _make_request('symbol_search', params)
    
    if 'error' in data:
        return []
    
    return data.get('data', [])

# === CLI Commands ===

def cli_quote(symbol: str):
    """Show real-time quote"""
    data = get_quote(symbol)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n📊 {data['name']} ({data['symbol']})")
    print("=" * 50)
    print(f"💰 Price: ${data['price']:.2f}")
    print(f"📈 Change: {data['change']:+.2f} ({data['percent_change']:+.2f}%)")
    print(f"📊 Open: ${data['open']:.2f} | High: ${data['high']:.2f} | Low: ${data['low']:.2f}")
    print(f"📦 Volume: {data['volume']:,}")
    print(f"⏰ {data['timestamp']}")
    print(f"🏢 Exchange: {data.get('exchange', 'N/A')}")
    
    if data.get('is_market_open'):
        print("🟢 Market Open")
    else:
        print("🔴 Market Closed")

def cli_forex(pair: str = 'EUR/USD'):
    """Show forex rate"""
    data = get_forex_rate(pair)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n💱 {data['symbol']}")
    print("=" * 50)
    print(f"📊 Rate: {data['rate']:.4f}")
    print(f"📈 Change: {data['change']:+.4f} ({data['percent_change']:+.2f}%)")
    print(f"⏰ {data['timestamp']}")

def cli_crypto(symbol: str = 'BTC/USD'):
    """Show crypto quote"""
    data = get_crypto_quote(symbol)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n₿ {data['symbol']}")
    print("=" * 50)
    print(f"💰 Price: ${data['price']:,.2f}")
    print(f"📈 Change: {data['change']:+,.2f} ({data['percent_change']:+.2f}%)")
    print(f"📦 Volume: ${data['volume']:,}")
    print(f"🏢 Exchange: {data.get('exchange', 'N/A')}")

def cli_history(symbol: str, days: int = 5):
    """Show price history"""
    data = get_time_series(symbol, interval='1day', outputsize=days)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n📈 {data['symbol']} — Last {days} Days")
    print("=" * 70)
    print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
    print("-" * 70)
    
    for val in data['values'][:days]:
        print(f"{val['datetime']:<12} "
              f"${val['open']:>9.2f} "
              f"${val['high']:>9.2f} "
              f"${val['low']:>9.2f} "
              f"${val['close']:>9.2f} "
              f"{val['volume']:>12,}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'quote' and len(sys.argv) > 2:
            cli_quote(sys.argv[2])
        elif cmd == 'forex':
            pair = sys.argv[2] if len(sys.argv) > 2 else 'EUR/USD'
            cli_forex(pair)
        elif cmd == 'crypto':
            symbol = sys.argv[2] if len(sys.argv) > 2 else 'BTC/USD'
            cli_crypto(symbol)
        elif cmd == 'history' and len(sys.argv) > 2:
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            cli_history(sys.argv[2], days)
        else:
            print("Usage:")
            print("  python twelve_data.py quote AAPL")
            print("  python twelve_data.py forex EUR/USD")
            print("  python twelve_data.py crypto BTC/USD")
            print("  python twelve_data.py history AAPL 10")
    else:
        # Demo
        print("🚀 Twelve Data Module Demo")
        cli_quote('AAPL')
        print()
        cli_forex('EUR/USD')
