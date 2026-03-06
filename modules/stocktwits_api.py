"""
StockTwits API — Real-time social sentiment from financial community.

User-generated messages, sentiment classifications (bullish/bearish), and watchlist data 
from StockTwits financial social network. Tracks retail trader sentiment in real-time.

Source: https://api.stocktwits.com/developers/docs
Update frequency: Real-time
Category: Alternative Data — Social & Sentiment
Free tier: 200 calls/hour (unlimited for basic streams)
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, UTC
from typing import Any, Optional


STOCKTWITS_BASE = "https://api.stocktwits.com/api/2"


def get_symbol_stream(symbol: str, max_results: int = 30) -> dict[str, Any]:
    """
    Get message stream for a specific stock symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        max_results: Max messages to return (default 30, max 30)
    
    Returns:
        Dictionary with messages, sentiment, and metadata
        
    Example:
        data = get_symbol_stream('AAPL')
        for msg in data['messages']:
            print(f"{msg['user']['username']}: {msg['body'][:100]}")
            sentiment = msg.get('entities', {}).get('sentiment')
            if sentiment:
                print(f"Sentiment: {sentiment.get('basic')}")
    """
    url = f"{STOCKTWITS_BASE}/streams/symbol/{symbol.upper()}.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw-Data/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            if not data:
                return {'symbol': symbol.upper(), 'error': 'Empty response', 'messages': []}
            
            # Extract sentiment counts
            messages = data.get('messages', [])
            bullish_count = 0
            bearish_count = 0
            
            for m in messages:
                entities = m.get('entities', {})
                if entities:
                    sentiment = entities.get('sentiment')
                    if sentiment and isinstance(sentiment, dict):
                        basic = sentiment.get('basic')
                        if basic == 'Bullish':
                            bullish_count += 1
                        elif basic == 'Bearish':
                            bearish_count += 1
            
            return {
                'symbol': symbol.upper(),
                'messages': messages[:max_results],
                'total_messages': len(messages),
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'bullish_pct': round(100 * bullish_count / len(messages), 1) if messages else 0,
                'watchlist_count': data.get('symbol', {}).get('watchlist_count', 0),
                'timestamp': datetime.now(UTC).isoformat()
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'symbol': symbol.upper(), 'error': 'Symbol not found', 'messages': []}
        raise
    except Exception as e:
        return {'symbol': symbol.upper(), 'error': str(e), 'messages': []}


def get_trending_symbols(limit: int = 30) -> dict[str, Any]:
    """
    Get trending stock symbols on StockTwits.
    
    Args:
        limit: Number of trending symbols to return (default 30, max 30)
    
    Returns:
        Dictionary with trending symbols and metadata
        
    Example:
        trending = get_trending_symbols()
        for s in trending['symbols']:
            print(f"{s['symbol']}: {s['title']} (Watchlist: {s['watchlist_count']})")
    """
    url = f"{STOCKTWITS_BASE}/trending/symbols.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw-Data/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            symbols = data.get('symbols', [])[:limit]
            
            return {
                'symbols': symbols,
                'count': len(symbols),
                'timestamp': datetime.now(UTC).isoformat()
            }
    except Exception as e:
        return {'error': str(e), 'symbols': []}


def get_user_stream(username: str, max_results: int = 30) -> dict[str, Any]:
    """
    Get message stream for a specific user.
    
    Args:
        username: StockTwits username
        max_results: Max messages to return (default 30, max 30)
    
    Returns:
        Dictionary with user messages and metadata
        
    Example:
        data = get_user_stream('jimcramer')
        print(f"Messages: {data['total_messages']}")
    """
    url = f"{STOCKTWITS_BASE}/streams/user/{username}.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw-Data/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            messages = data.get('messages', [])[:max_results]
            
            return {
                'username': username,
                'messages': messages,
                'total_messages': len(messages),
                'timestamp': datetime.now(UTC).isoformat()
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'username': username, 'error': 'User not found', 'messages': []}
        raise
    except Exception as e:
        return {'username': username, 'error': str(e), 'messages': []}


def analyze_symbol_sentiment(symbol: str, window: int = 100) -> dict[str, Any]:
    """
    Analyze overall sentiment for a symbol over recent messages.
    
    Args:
        symbol: Stock ticker
        window: Number of recent messages to analyze (max 30 per call)
    
    Returns:
        Sentiment analysis summary
        
    Example:
        analysis = analyze_symbol_sentiment('NVDA')
        print(f"Bullish: {analysis['bullish_pct']}%")
        print(f"Signal: {analysis['signal']}")
    """
    data = get_symbol_stream(symbol, max_results=30)
    
    if 'error' in data:
        return data
    
    bullish = data['bullish_count']
    bearish = data['bearish_count']
    total = bullish + bearish
    
    if total == 0:
        signal = 'NEUTRAL'
    elif bullish / total > 0.7:
        signal = 'STRONG_BULLISH'
    elif bullish / total > 0.55:
        signal = 'BULLISH'
    elif bearish / total > 0.7:
        signal = 'STRONG_BEARISH'
    elif bearish / total > 0.55:
        signal = 'BEARISH'
    else:
        signal = 'NEUTRAL'
    
    return {
        'symbol': symbol.upper(),
        'bullish_count': bullish,
        'bearish_count': bearish,
        'neutral_count': data['total_messages'] - total,
        'bullish_pct': data['bullish_pct'],
        'signal': signal,
        'sample_size': data['total_messages'],
        'watchlist_count': data.get('watchlist_count', 0),
        'timestamp': data['timestamp']
    }


if __name__ == "__main__":
    # Test with AAPL
    print("=== StockTwits Sentiment for AAPL ===")
    sentiment = analyze_symbol_sentiment('AAPL')
    print(json.dumps(sentiment, indent=2))
    
    print("\n=== Trending Symbols ===")
    trending = get_trending_symbols(limit=10)
    for s in trending.get('symbols', [])[:5]:
        print(f"{s['symbol']}: {s.get('title', 'N/A')} (Watchlist: {s.get('watchlist_count', 0)})")
