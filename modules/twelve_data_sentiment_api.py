#!/usr/bin/env python3
"""
Twelve Data Sentiment API — Market Sentiment Analysis

Derives sentiment indicators from price action, volume, and volatility data.
Provides sentiment scores based on technical momentum, volume patterns, and
price behavior - fundamental components of quantitative sentiment analysis.

Source: https://api.twelvedata.com
Category: News & NLP (Technical Sentiment Proxies)
Free tier: True - 800 API calls/day, 8 calls/min with demo key
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Twelve Data API Configuration
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "demo")


def _calculate_sentiment_score(
    price_change_pct: float,
    volume_ratio: float,
    volatility: float
) -> Dict:
    """
    Calculate sentiment score from price, volume, and volatility metrics
    
    Args:
        price_change_pct: Percentage price change
        volume_ratio: Current volume vs average volume
        volatility: Price volatility measure
    
    Returns:
        Dict with sentiment score, label, and components
    """
    # Sentiment components (normalized to -100 to +100 scale)
    price_sentiment = max(-100, min(100, price_change_pct * 10))
    
    # Volume indicates conviction (high volume = stronger signal)
    volume_sentiment = max(-50, min(50, (volume_ratio - 1.0) * 50))
    
    # High volatility reduces confidence
    volatility_penalty = max(-30, min(0, -volatility * 3))
    
    # Weighted composite score
    raw_score = (
        price_sentiment * 0.5 +
        volume_sentiment * 0.3 +
        volatility_penalty * 0.2
    )
    
    # Normalize to -100 to +100
    sentiment_score = max(-100, min(100, raw_score))
    
    # Label sentiment
    if sentiment_score > 40:
        label = "Very Bullish"
    elif sentiment_score > 15:
        label = "Bullish"
    elif sentiment_score > -15:
        label = "Neutral"
    elif sentiment_score > -40:
        label = "Bearish"
    else:
        label = "Very Bearish"
    
    return {
        "sentiment_score": round(sentiment_score, 2),
        "sentiment_label": label,
        "components": {
            "price_sentiment": round(price_sentiment, 2),
            "volume_sentiment": round(volume_sentiment, 2),
            "volatility_penalty": round(volatility_penalty, 2)
        }
    }


def get_sentiment(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get sentiment score for a single stock
    
    Analyzes recent price action, volume patterns, and volatility to derive
    a quantitative sentiment indicator from -100 (very bearish) to +100 (very bullish).
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        api_key: Optional Twelve Data API key (defaults to env or 'demo')
    
    Returns:
        Dict with sentiment score, label, price data, and metadata
    """
    try:
        key = api_key or TWELVE_DATA_API_KEY
        
        # Get current quote
        quote_url = f"{TWELVE_DATA_BASE_URL}/quote"
        quote_params = {"symbol": symbol, "apikey": key}
        
        quote_response = requests.get(quote_url, params=quote_params, timeout=15)
        quote_response.raise_for_status()
        quote_data = quote_response.json()
        
        if quote_data.get("status") == "error":
            return {
                "success": False,
                "error": quote_data.get("message", "API error"),
                "symbol": symbol
            }
        
        # Get recent time series for volatility calculation
        ts_url = f"{TWELVE_DATA_BASE_URL}/time_series"
        ts_params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 20,
            "apikey": key
        }
        
        ts_response = requests.get(ts_url, params=ts_params, timeout=15)
        ts_response.raise_for_status()
        ts_data = ts_response.json()
        
        # Calculate metrics
        price_change_pct = float(quote_data.get("percent_change", 0))
        current_volume = float(quote_data.get("volume", 0))
        avg_volume = float(quote_data.get("average_volume", current_volume))
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Calculate volatility from recent closes
        volatility = 0.0
        if ts_data.get("status") == "ok" and "values" in ts_data:
            closes = [float(v["close"]) for v in ts_data["values"][:10]]
            if len(closes) > 1:
                returns = [(closes[i] - closes[i+1]) / closes[i+1] * 100 
                          for i in range(len(closes)-1)]
                volatility = sum(abs(r) for r in returns) / len(returns)
        
        # Calculate sentiment
        sentiment = _calculate_sentiment_score(price_change_pct, volume_ratio, volatility)
        
        return {
            "success": True,
            "symbol": symbol,
            "name": quote_data.get("name", symbol),
            "sentiment_score": sentiment["sentiment_score"],
            "sentiment_label": sentiment["sentiment_label"],
            "components": sentiment["components"],
            "price_data": {
                "close": float(quote_data.get("close", 0)),
                "change": float(quote_data.get("change", 0)),
                "percent_change": price_change_pct,
                "volume": current_volume,
                "avg_volume": avg_volume,
                "volume_ratio": round(volume_ratio, 2)
            },
            "volatility": round(volatility, 2),
            "date": quote_data.get("datetime", datetime.now().strftime("%Y-%m-%d")),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "symbol": symbol
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "symbol": symbol
        }


def get_sentiment_bulk(symbols: List[str], api_key: Optional[str] = None) -> Dict:
    """
    Get sentiment scores for multiple stocks
    
    Args:
        symbols: List of stock ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])
        api_key: Optional Twelve Data API key (defaults to env or 'demo')
    
    Returns:
        Dict with sentiment data for all symbols, sorted by sentiment score
    """
    results = []
    errors = []
    
    for symbol in symbols:
        sentiment_data = get_sentiment(symbol, api_key)
        
        if sentiment_data["success"]:
            results.append({
                "symbol": sentiment_data["symbol"],
                "name": sentiment_data["name"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "sentiment_label": sentiment_data["sentiment_label"],
                "percent_change": sentiment_data["price_data"]["percent_change"],
                "volume_ratio": sentiment_data["price_data"]["volume_ratio"]
            })
        else:
            errors.append({
                "symbol": symbol,
                "error": sentiment_data["error"]
            })
    
    # Sort by sentiment score (most bullish first)
    results.sort(key=lambda x: x["sentiment_score"], reverse=True)
    
    # Calculate aggregate sentiment
    if results:
        avg_sentiment = sum(r["sentiment_score"] for r in results) / len(results)
        bullish_count = sum(1 for r in results if r["sentiment_score"] > 15)
        bearish_count = sum(1 for r in results if r["sentiment_score"] < -15)
    else:
        avg_sentiment = 0
        bullish_count = 0
        bearish_count = 0
    
    return {
        "success": True,
        "count": len(results),
        "symbols": results,
        "aggregate": {
            "average_sentiment": round(avg_sentiment, 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": len(results) - bullish_count - bearish_count
        },
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat()
    }


def get_sentiment_history(symbol: str, days: int = 30, api_key: Optional[str] = None) -> Dict:
    """
    Get historical sentiment trend for a stock
    
    Calculates daily sentiment scores over the specified period using price
    momentum and volume patterns.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        days: Number of days of history (default 30, max ~250 for free tier)
        api_key: Optional Twelve Data API key (defaults to env or 'demo')
    
    Returns:
        Dict with historical sentiment scores and trend analysis
    """
    try:
        key = api_key or TWELVE_DATA_API_KEY
        
        # Get time series data
        ts_url = f"{TWELVE_DATA_BASE_URL}/time_series"
        ts_params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": min(days + 20, 250),  # Extra for calculations
            "apikey": key
        }
        
        ts_response = requests.get(ts_url, params=ts_params, timeout=15)
        ts_response.raise_for_status()
        ts_data = ts_response.json()
        
        if ts_data.get("status") == "error":
            return {
                "success": False,
                "error": ts_data.get("message", "API error"),
                "symbol": symbol
            }
        
        if "values" not in ts_data or len(ts_data["values"]) < 2:
            return {
                "success": False,
                "error": "Insufficient data",
                "symbol": symbol
            }
        
        values = ts_data["values"]
        history = []
        
        # Calculate sentiment for each day
        for i in range(min(days, len(values) - 1)):
            current = values[i]
            previous = values[i + 1]
            
            current_close = float(current["close"])
            prev_close = float(previous["close"])
            current_volume = float(current["volume"])
            
            # Calculate daily change
            price_change_pct = ((current_close - prev_close) / prev_close) * 100
            
            # Calculate average volume (from available data)
            avg_volume = sum(float(v["volume"]) for v in values[i:i+10]) / min(10, len(values) - i)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Calculate local volatility
            closes = [float(v["close"]) for v in values[i:i+5]]
            volatility = 0.0
            if len(closes) > 1:
                returns = [(closes[j] - closes[j+1]) / closes[j+1] * 100 
                          for j in range(len(closes)-1)]
                volatility = sum(abs(r) for r in returns) / len(returns)
            
            sentiment = _calculate_sentiment_score(price_change_pct, volume_ratio, volatility)
            
            history.append({
                "date": current["datetime"],
                "sentiment_score": sentiment["sentiment_score"],
                "sentiment_label": sentiment["sentiment_label"],
                "close": current_close,
                "volume": current_volume,
                "percent_change": round(price_change_pct, 2)
            })
        
        # Trend analysis
        recent_sentiment = [h["sentiment_score"] for h in history[:7]]  # Last week
        older_sentiment = [h["sentiment_score"] for h in history[7:14]] if len(history) > 14 else recent_sentiment
        
        recent_avg = sum(recent_sentiment) / len(recent_sentiment) if recent_sentiment else 0
        older_avg = sum(older_sentiment) / len(older_sentiment) if older_sentiment else recent_avg
        
        trend = "improving" if recent_avg > older_avg + 5 else \
                "declining" if recent_avg < older_avg - 5 else "stable"
        
        return {
            "success": True,
            "symbol": symbol,
            "days": len(history),
            "history": history,
            "trend_analysis": {
                "current_sentiment": history[0]["sentiment_score"] if history else 0,
                "week_avg_sentiment": round(recent_avg, 2),
                "prev_week_avg_sentiment": round(older_avg, 2),
                "trend": trend,
                "max_sentiment": max(h["sentiment_score"] for h in history) if history else 0,
                "min_sentiment": min(h["sentiment_score"] for h in history) if history else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "symbol": symbol
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "symbol": symbol
        }


def get_trending_sentiment(limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get stocks with most significant sentiment shifts
    
    Analyzes a predefined watchlist of popular stocks to identify those with
    the strongest bullish or bearish sentiment based on recent price action.
    
    Args:
        limit: Maximum number of trending stocks to return (default 10)
        api_key: Optional Twelve Data API key (defaults to env or 'demo')
    
    Returns:
        Dict with top bullish and bearish stocks by sentiment
    """
    # Predefined watchlist of liquid stocks
    watchlist = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM",
        "V", "MA", "DIS", "NFLX", "INTC", "AMD", "CRM", "ORCL",
        "BAC", "WMT", "PG", "KO"
    ]
    
    # Get sentiment for all symbols
    bulk_data = get_sentiment_bulk(watchlist[:20], api_key)  # Limit to avoid rate limits
    
    if not bulk_data["success"] or not bulk_data["symbols"]:
        return {
            "success": False,
            "error": "Unable to fetch sentiment data",
            "timestamp": datetime.now().isoformat()
        }
    
    symbols = bulk_data["symbols"]
    
    # Top bullish (highest sentiment scores)
    most_bullish = sorted(symbols, key=lambda x: x["sentiment_score"], reverse=True)[:limit]
    
    # Top bearish (lowest sentiment scores)
    most_bearish = sorted(symbols, key=lambda x: x["sentiment_score"])[:limit]
    
    # Biggest movers (highest absolute sentiment)
    biggest_movers = sorted(symbols, key=lambda x: abs(x["sentiment_score"]), reverse=True)[:limit]
    
    return {
        "success": True,
        "most_bullish": most_bullish,
        "most_bearish": most_bearish,
        "biggest_movers": biggest_movers,
        "market_breadth": {
            "total_analyzed": len(symbols),
            "bullish_count": bulk_data["aggregate"]["bullish_count"],
            "bearish_count": bulk_data["aggregate"]["bearish_count"],
            "neutral_count": bulk_data["aggregate"]["neutral_count"],
            "average_sentiment": bulk_data["aggregate"]["average_sentiment"]
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Twelve Data Sentiment Analysis Module")
    print("=" * 60)
    
    # Test single sentiment
    print("\n1. Testing get_sentiment(AAPL):")
    aapl_sentiment = get_sentiment("AAPL")
    print(json.dumps(aapl_sentiment, indent=2))
    
    # Test bulk sentiment
    print("\n2. Testing get_sentiment_bulk([AAPL, MSFT, GOOGL]):")
    bulk_sentiment = get_sentiment_bulk(["AAPL", "MSFT", "GOOGL"])
    print(json.dumps(bulk_sentiment, indent=2))
    
    # Test trending
    print("\n3. Testing get_trending_sentiment():")
    trending = get_trending_sentiment(limit=5)
    print(json.dumps(trending, indent=2))
