"""
Twelve Data Sentiment API — News and social media sentiment for stocks.

Aggregates sentiment from news and social media sources, providing scores and trends 
for quantitative trading. Includes historical data for backtesting momentum/event strategies.

Source: https://twelvedata.com/docs#sentiment
Update frequency: Daily
Category: News & NLP
Free tier: 800 API calls/day, 8 calls/min (API key required)
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, UTC
from typing import Any, Optional


TD_BASE = "https://api.twelvedata.com"
TD_API_KEY = None  # Set via environment or parameter


def get_sentiment(symbol: str, api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Get sentiment analysis for a stock symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        api_key: Twelve Data API key (required for production use)
    
    Returns:
        Dictionary with sentiment score, label, volume, timestamp, source count
        
    Example:
        data = get_sentiment('AAPL', api_key='YOUR_KEY')
        print(f"Sentiment: {data['sentiment_label']} ({data['sentiment_score']}/10)")
        print(f"Based on {data['source_count']} sources")
    """
    key = api_key or TD_API_KEY
    if not key:
        return {
            'symbol': symbol.upper(),
            'error': 'API key required',
            'sentiment_score': None,
            'timestamp': datetime.now(UTC).isoformat()
        }
    
    url = f"{TD_BASE}/sentiment?symbol={symbol.upper()}&apikey={key}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw-Data/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            if 'status' in data and data['status'] == 'error':
                return {
                    'symbol': symbol.upper(),
                    'error': data.get('message', 'API error'),
                    'sentiment_score': None,
                    'timestamp': datetime.now(UTC).isoformat()
                }
            
            # Extract sentiment metrics
            sentiment_score = data.get('sentiment_score')
            sentiment_label = data.get('sentiment_label', 'neutral')
            
            return {
                'symbol': symbol.upper(),
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label.lower(),
                'volume': data.get('volume', 0),
                'source_count': data.get('source_count', 0),
                'timestamp': data.get('timestamp') or datetime.now(UTC).isoformat(),
                'raw': data
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'symbol': symbol.upper(), 'error': 'Symbol not found', 'sentiment_score': None, 'timestamp': datetime.now(UTC).isoformat()}
        elif e.code == 429:
            return {'symbol': symbol.upper(), 'error': 'Rate limit exceeded', 'sentiment_score': None, 'timestamp': datetime.now(UTC).isoformat()}
        else:
            return {'symbol': symbol.upper(), 'error': f'HTTP {e.code}', 'sentiment_score': None, 'timestamp': datetime.now(UTC).isoformat()}
    except Exception as e:
        return {'symbol': symbol.upper(), 'error': str(e), 'sentiment_score': None, 'timestamp': datetime.now(UTC).isoformat()}


def get_multi_sentiment(symbols: list[str], api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Get sentiment for multiple symbols (batch query).
    
    Args:
        symbols: List of stock tickers
        api_key: Twelve Data API key
    
    Returns:
        Dictionary mapping symbols to sentiment data
    """
    results = {}
    for symbol in symbols:
        results[symbol.upper()] = get_sentiment(symbol, api_key)
    return results


def get_latest(symbol: str = 'SPY', api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Alias for get_sentiment (for DataScout module pattern).
    """
    return get_sentiment(symbol, api_key)


if __name__ == "__main__":
    # Demo output (requires API key for real data)
    demo_result = {
        "module": "twelve_data_sentiment",
        "status": "operational",
        "source": "https://twelvedata.com/docs#sentiment",
        "demo": get_sentiment('AAPL')
    }
    print(json.dumps(demo_result, indent=2))
