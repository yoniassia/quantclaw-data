#!/usr/bin/env python3
"""
Alpha Vantage Emerging Markets API — Emerging Markets Stock & FX Data

Comprehensive emerging markets integration for Alpha Vantage including:
- Real-time quotes for BSE, NSE, and other EM exchanges
- Daily and intraday OHLCV data
- Emerging markets forex rates
- Market overviews and indices
- Symbol search across emerging markets

Source: https://www.alphavantage.co/documentation/
Category: Emerging Markets
Free tier: True (5 calls/min, 500 calls/day - requires ALPHA_VANTAGE_API_KEY)
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

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")


def get_em_stock_quote(symbol: str = 'RELIANCE.BSE') -> Dict:
    """
    Get real-time quote for an emerging market stock.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'RELIANCE.BSE', 'TCS.BSE')
    
    Returns:
        Dict with keys: symbol, price, volume, timestamp, change, change_percent
    
    Example:
        >>> quote = get_em_stock_quote('RELIANCE.BSE')
        >>> print(f"Price: {quote.get('price')}")
    """
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'symbol': symbol}
        if 'Note' in data:
            return {'error': 'Rate limit exceeded', 'note': data['Note'], 'symbol': symbol}
        
        # Parse global quote
        quote_data = data.get('Global Quote', {})
        if not quote_data:
            return {'error': 'No data returned', 'symbol': symbol}
        
        result = {
            'symbol': quote_data.get('01. symbol', symbol),
            'price': float(quote_data.get('05. price', 0)),
            'volume': int(quote_data.get('06. volume', 0)),
            'latest_trading_day': quote_data.get('07. latest trading day'),
            'previous_close': float(quote_data.get('08. previous close', 0)),
            'change': float(quote_data.get('09. change', 0)),
            'change_percent': quote_data.get('10. change percent', '0%'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}', 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_em_daily(symbol: str = 'RELIANCE.BSE', outputsize: str = 'compact') -> List[Dict]:
    """
    Get daily OHLCV data for an emerging market stock.
    
    Args:
        symbol: Stock ticker with exchange suffix
        outputsize: 'compact' (100 days) or 'full' (20+ years)
    
    Returns:
        List of Dict with keys: date, open, high, low, close, volume
    
    Example:
        >>> daily_data = get_em_daily('TCS.BSE', 'compact')
        >>> print(f"Latest close: {daily_data[0]['close']}")
    """
    try:
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'symbol': symbol}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note'], 'symbol': symbol}]
        
        # Parse time series
        time_series = data.get('Time Series (Daily)', {})
        if not time_series:
            return [{'error': 'No data returned', 'symbol': symbol}]
        
        result = []
        for date_str, values in sorted(time_series.items(), reverse=True):
            result.append({
                'date': date_str,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'volume': int(values.get('5. volume', 0)),
                'symbol': symbol
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'symbol': symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'symbol': symbol}]


def get_em_intraday(symbol: str = 'RELIANCE.BSE', interval: str = '5min') -> List[Dict]:
    """
    Get intraday OHLCV data for an emerging market stock.
    
    Args:
        symbol: Stock ticker with exchange suffix
        interval: Time interval ('1min', '5min', '15min', '30min', '60min')
    
    Returns:
        List of Dict with keys: datetime, open, high, low, close, volume
    
    Example:
        >>> intraday = get_em_intraday('RELIANCE.BSE', '5min')
        >>> print(f"Latest: {intraday[0]['datetime']} @ {intraday[0]['close']}")
    """
    try:
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'symbol': symbol}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note'], 'symbol': symbol}]
        
        # Parse time series
        time_series_key = f'Time Series ({interval})'
        time_series = data.get(time_series_key, {})
        if not time_series:
            return [{'error': 'No data returned', 'symbol': symbol}]
        
        result = []
        for datetime_str, values in sorted(time_series.items(), reverse=True):
            result.append({
                'datetime': datetime_str,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'volume': int(values.get('5. volume', 0)),
                'symbol': symbol
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'symbol': symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'symbol': symbol}]


def get_em_forex(from_currency: str = 'INR', to_currency: str = 'USD') -> Dict:
    """
    Get emerging markets forex exchange rates.
    
    Args:
        from_currency: Source currency code (e.g., 'INR', 'BRL', 'ZAR')
        to_currency: Target currency code (e.g., 'USD', 'EUR')
    
    Returns:
        Dict with keys: from_currency, to_currency, exchange_rate, last_refreshed, bid, ask
    
    Example:
        >>> fx = get_em_forex('INR', 'USD')
        >>> print(f"1 INR = {fx['exchange_rate']} USD")
    """
    try:
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'from_currency': from_currency, 'to_currency': to_currency}
        if 'Note' in data:
            return {'error': 'Rate limit exceeded', 'note': data['Note']}
        
        # Parse exchange rate data
        rate_data = data.get('Realtime Currency Exchange Rate', {})
        if not rate_data:
            return {'error': 'No data returned', 'from_currency': from_currency, 'to_currency': to_currency}
        
        result = {
            'from_currency': rate_data.get('1. From_Currency Code', from_currency),
            'from_currency_name': rate_data.get('2. From_Currency Name', ''),
            'to_currency': rate_data.get('3. To_Currency Code', to_currency),
            'to_currency_name': rate_data.get('4. To_Currency Name', ''),
            'exchange_rate': float(rate_data.get('5. Exchange Rate', 0)),
            'last_refreshed': rate_data.get('6. Last Refreshed', ''),
            'bid': float(rate_data.get('8. Bid Price', 0)),
            'ask': float(rate_data.get('9. Ask Price', 0)),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}', 'from_currency': from_currency, 'to_currency': to_currency}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'from_currency': from_currency, 'to_currency': to_currency}


def get_em_market_overview(market: str = 'india') -> Dict:
    """
    Get overview of major emerging market indices.
    
    Note: Alpha Vantage doesn't have a dedicated market overview endpoint.
    This function fetches major indices for the specified market using symbol search.
    
    Args:
        market: Market name ('india', 'brazil', 'china', 'south_africa')
    
    Returns:
        Dict with market info and major indices
    
    Example:
        >>> overview = get_em_market_overview('india')
        >>> print(overview.get('market'))
    """
    # Map market to major index symbols
    market_indices = {
        'india': ['SENSEX.BSE', 'NIFTY.NSE'],
        'brazil': ['IBOV.SAO'],
        'china': ['000001.SHZ'],  # Shanghai Composite
        'south_africa': ['JSE.JNB']
    }
    
    indices = market_indices.get(market.lower(), [])
    if not indices:
        return {'error': f'Unknown market: {market}', 'supported_markets': list(market_indices.keys())}
    
    result = {
        'market': market,
        'indices': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Fetch quotes for each major index
    for index_symbol in indices:
        quote = get_em_stock_quote(index_symbol)
        if 'error' not in quote:
            result['indices'].append(quote)
    
    return result


def search_em_symbols(keywords: str = 'Tata', market: str = 'india') -> List[Dict]:
    """
    Search for stock symbols in emerging markets.
    
    Args:
        keywords: Search keywords (company name or ticker)
        market: Market region filter (currently informational only)
    
    Returns:
        List of Dict with keys: symbol, name, type, region, currency
    
    Example:
        >>> results = search_em_symbols('Tata', 'india')
        >>> for stock in results[:3]:
        >>>     print(f"{stock['symbol']}: {stock['name']}")
    """
    try:
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'keywords': keywords}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note'], 'keywords': keywords}]
        
        # Parse best matches
        matches = data.get('bestMatches', [])
        if not matches:
            return [{'error': 'No matches found', 'keywords': keywords, 'market': market}]
        
        result = []
        for match in matches:
            result.append({
                'symbol': match.get('1. symbol', ''),
                'name': match.get('2. name', ''),
                'type': match.get('3. type', ''),
                'region': match.get('4. region', ''),
                'market_open': match.get('5. marketOpen', ''),
                'market_close': match.get('6. marketClose', ''),
                'timezone': match.get('7. timezone', ''),
                'currency': match.get('8. currency', ''),
                'match_score': float(match.get('9. matchScore', 0))
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'keywords': keywords}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'keywords': keywords}]


if __name__ == "__main__":
    # Module test
    print(json.dumps({
        "module": "alpha_vantage_emerging_markets_api",
        "status": "active",
        "functions": [
            "get_em_stock_quote",
            "get_em_daily",
            "get_em_intraday",
            "get_em_forex",
            "get_em_market_overview",
            "search_em_symbols"
        ],
        "source": "https://www.alphavantage.co/documentation/",
        "free_tier": "5 calls/min, 500 calls/day"
    }, indent=2))
