#!/usr/bin/env python3
"""
Stocktwits Sentiment API — Social Trading Sentiment Module

Social sentiment data from trader discussions on StockTwits. Provides:
- Bullish/bearish sentiment indicators
- Trending symbols and watchlists
- Message streams by symbol
- Retail sentiment aggregation for quant trading

Source: https://api.stocktwits.com/developers/docs
Category: News & NLP
Free tier: True (100 calls/hour, no auth required for basic streams)
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

# API Configuration
STOCKTWITS_BASE_URL = "https://api.stocktwits.com/api/2"
DEFAULT_TIMEOUT = 10  # seconds
USER_AGENT = "QuantClaw-Data/1.0"

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Internal function to make API requests with error handling.
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        
    Returns:
        Dict with response data or error information
    """
    url = f"{STOCKTWITS_BASE_URL}/{endpoint}"
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "status": "timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "error"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "status": "parse_error"}

def get_symbol_sentiment(symbol: str) -> Dict:
    """
    Get sentiment analysis for a specific stock symbol.
    
    Fetches recent messages and calculates bullish/bearish sentiment ratios
    from the StockTwits community for the given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        
    Returns:
        Dict containing:
            - symbol: The ticker symbol
            - total_messages: Number of messages analyzed
            - bullish: Count of bullish messages
            - bearish: Count of bearish messages
            - neutral: Count of neutral messages
            - sentiment_ratio: Bullish/(Bullish+Bearish) ratio
            - messages: List of recent messages with sentiment
            - timestamp: ISO timestamp of analysis
            - error: Error message if request failed
            
    Example:
        >>> sentiment = get_symbol_sentiment("AAPL")
        >>> print(f"Bullish: {sentiment['bullish']}, Bearish: {sentiment['bearish']}")
    """
    symbol = symbol.upper().strip()
    endpoint = f"streams/symbol/{symbol}.json"
    
    data = _make_request(endpoint)
    
    if "error" in data:
        return {
            "symbol": symbol,
            "error": data["error"],
            "status": data.get("status", "error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Parse sentiment from messages
    messages = data.get("messages", [])
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    
    processed_messages = []
    
    for msg in messages:
        entities = msg.get("entities", {})
        sentiment_data = entities.get("sentiment")
        
        sentiment = None
        if sentiment_data:
            sentiment = sentiment_data.get("basic")
            
        if sentiment == "Bullish":
            bullish_count += 1
        elif sentiment == "Bearish":
            bearish_count += 1
        else:
            neutral_count += 1
            
        processed_messages.append({
            "id": msg.get("id"),
            "body": msg.get("body", "")[:200],  # Truncate long messages
            "created_at": msg.get("created_at"),
            "sentiment": sentiment,
            "user": msg.get("user", {}).get("username"),
            "likes": msg.get("likes", {}).get("total", 0)
        })
    
    total = bullish_count + bearish_count
    sentiment_ratio = bullish_count / total if total > 0 else 0.5
    
    return {
        "symbol": symbol,
        "total_messages": len(messages),
        "bullish": bullish_count,
        "bearish": bearish_count,
        "neutral": neutral_count,
        "sentiment_ratio": round(sentiment_ratio, 3),
        "messages": processed_messages,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

def get_trending_symbols() -> Dict:
    """
    Get currently trending stock symbols on StockTwits.
    
    Returns the most talked-about symbols with message counts and sentiment.
    
    Returns:
        Dict containing:
            - symbols: List of trending symbols with metadata
            - count: Number of trending symbols
            - timestamp: ISO timestamp
            - error: Error message if request failed
            
    Example:
        >>> trending = get_trending_symbols()
        >>> for symbol in trending['symbols'][:5]:
        ...     print(f"{symbol['symbol']}: {symbol['watchlist_count']} watchers")
    """
    endpoint = "trending/symbols.json"
    
    data = _make_request(endpoint)
    
    if "error" in data:
        return {
            "error": data["error"],
            "status": data.get("status", "error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    symbols = data.get("symbols", [])
    
    processed_symbols = []
    for sym in symbols:
        processed_symbols.append({
            "symbol": sym.get("symbol"),
            "title": sym.get("title"),
            "watchlist_count": sym.get("watchlist_count", 0),
            "exchange": sym.get("exchange"),
            "is_trending": sym.get("is_trending", False)
        })
    
    return {
        "symbols": processed_symbols,
        "count": len(processed_symbols),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

def get_symbol_messages(symbol: str, limit: int = 30) -> Dict:
    """
    Get recent messages for a specific symbol.
    
    Fetches the message stream for a symbol with detailed message content,
    user info, and engagement metrics.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        limit: Maximum number of messages to return (default: 30, API max: 30)
        
    Returns:
        Dict containing:
            - symbol: The ticker symbol
            - messages: List of message objects with full details
            - count: Number of messages returned
            - timestamp: ISO timestamp
            - error: Error message if request failed
            
    Example:
        >>> messages = get_symbol_messages("TSLA", limit=10)
        >>> for msg in messages['messages']:
        ...     print(f"{msg['user']}: {msg['body'][:50]}...")
    """
    symbol = symbol.upper().strip()
    limit = min(max(1, limit), 30)  # API limit is 30
    
    endpoint = f"streams/symbol/{symbol}.json"
    params = {"limit": limit}
    
    data = _make_request(endpoint, params)
    
    if "error" in data:
        return {
            "symbol": symbol,
            "error": data["error"],
            "status": data.get("status", "error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    messages = data.get("messages", [])
    
    processed_messages = []
    for msg in messages:
        entities = msg.get("entities", {})
        sentiment_data = entities.get("sentiment")
        
        processed_messages.append({
            "id": msg.get("id"),
            "body": msg.get("body"),
            "created_at": msg.get("created_at"),
            "sentiment": sentiment_data.get("basic") if sentiment_data else None,
            "user": msg.get("user", {}).get("username"),
            "user_followers": msg.get("user", {}).get("followers", 0),
            "likes": msg.get("likes", {}).get("total", 0),
            "source": msg.get("source", {}).get("title"),
            "symbols": [s.get("symbol") for s in entities.get("chart", {}).get("symbols", [])]
        })
    
    return {
        "symbol": symbol,
        "messages": processed_messages,
        "count": len(processed_messages),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

def get_trending_stream() -> Dict:
    """
    Get the global trending message stream.
    
    Returns recent messages from the trending stream across all symbols.
    
    Returns:
        Dict containing trending messages with sentiment and engagement data
    """
    endpoint = "streams/trending.json"
    
    data = _make_request(endpoint)
    
    if "error" in data:
        return {
            "error": data["error"],
            "status": data.get("status", "error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    messages = data.get("messages", [])
    
    processed_messages = []
    for msg in messages:
        entities = msg.get("entities", {})
        sentiment_data = entities.get("sentiment")
        symbols = entities.get("chart", {}).get("symbols", [])
        
        processed_messages.append({
            "id": msg.get("id"),
            "body": msg.get("body", "")[:300],
            "created_at": msg.get("created_at"),
            "sentiment": sentiment_data.get("basic") if sentiment_data else None,
            "user": msg.get("user", {}).get("username"),
            "likes": msg.get("likes", {}).get("total", 0),
            "symbols": [s.get("symbol") for s in symbols]
        })
    
    return {
        "messages": processed_messages,
        "count": len(processed_messages),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

# CLI / Testing Interface
if __name__ == "__main__":
    print(json.dumps({
        "module": "stocktwits_sentiment_api",
        "status": "active",
        "functions": [
            "get_symbol_sentiment(symbol)",
            "get_trending_symbols()",
            "get_symbol_messages(symbol, limit=30)",
            "get_trending_stream()"
        ],
        "source": "https://api.stocktwits.com/developers/docs",
        "free_tier": True,
        "rate_limit": "100 calls/hour"
    }, indent=2))
