#!/usr/bin/env python3
"""
CNN Fear & Greed Index Module

Real-time market sentiment indicator from CNN Business combining 7 market metrics.
The index ranges from 0 (Extreme Fear) to 100 (Extreme Greed) and is based on:
- Market Momentum (SP500 vs 125-day MA)
- Stock Price Strength (52-week highs/lows)
- Stock Price Breadth (advancing vs declining volume)
- Put/Call Options (sentiment indicator)
- Market Volatility (VIX)
- Safe Haven Demand (stocks vs bonds)
- Junk Bond Demand (credit risk appetite)

Source: https://production.dataviz.cnn.io/index/fearandgreed/graphdata
Category: Market Sentiment
Free tier: True (no API key required)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# CNN Fear & Greed API Configuration
CNN_BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# Browser-like headers to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.cnn.com/",
}

# Rating thresholds
RATING_MAP = {
    "extreme fear": (0, 25),
    "fear": (25, 45),
    "neutral": (45, 55),
    "greed": (55, 75),
    "extreme greed": (75, 100),
}


def _fetch_fear_greed_data() -> Dict:
    """
    Internal helper to fetch raw data from CNN endpoint
    
    Returns:
        Dict with raw JSON response from CNN API
    """
    try:
        response = requests.get(CNN_BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _rating_from_score(score: float) -> str:
    """
    Convert numeric score to rating label
    
    Args:
        score: Fear & Greed score (0-100)
    
    Returns:
        Rating string (extreme fear, fear, neutral, greed, extreme greed)
    """
    for rating, (low, high) in RATING_MAP.items():
        if low <= score < high:
            return rating
    return "extreme greed"  # >= 75


def get_fear_greed_index() -> Dict:
    """
    Get current Fear & Greed Index with overall score and rating
    
    Returns:
        Dict with current score, rating, timestamp, and historical comparisons
    """
    result = _fetch_fear_greed_data()
    
    if not result["success"]:
        return result
    
    data = result["data"]
    fg = data.get("fear_and_greed", {})
    
    score = fg.get("score", 0)
    rating = fg.get("rating", "unknown")
    
    return {
        "success": True,
        "current_score": round(score, 2),
        "rating": rating,
        "timestamp": fg.get("timestamp"),
        "previous_close": round(fg.get("previous_close", 0), 2),
        "previous_1_week": round(fg.get("previous_1_week", 0), 2),
        "previous_1_month": round(fg.get("previous_1_month", 0), 2),
        "previous_1_year": round(fg.get("previous_1_year", 0), 2),
        "change_from_yesterday": round(score - fg.get("previous_close", score), 2),
        "change_from_week": round(score - fg.get("previous_1_week", score), 2),
        "change_from_month": round(score - fg.get("previous_1_month", score), 2),
        "interpretation": _interpret_score(score),
        "source": "CNN Fear & Greed Index"
    }


def get_fear_greed_components() -> Dict:
    """
    Get all 7 component scores that make up the Fear & Greed Index
    
    Components:
    - Market Momentum (SP500 vs 125-day MA)
    - Stock Price Strength (52-week highs/lows)
    - Stock Price Breadth (advancing vs declining volume)
    - Put/Call Options
    - Market Volatility (VIX)
    - Safe Haven Demand (stocks vs bonds)
    - Junk Bond Demand (high yield credit spreads)
    
    Returns:
        Dict with all component scores, ratings, and latest values
    """
    result = _fetch_fear_greed_data()
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    components = {
        "market_momentum_sp500": {
            "name": "Market Momentum (SP500 vs 125-day MA)",
            "data": data.get("market_momentum_sp500", {}),
        },
        "market_momentum_sp125": {
            "name": "Market Momentum (SP125 vs 125-day MA)",
            "data": data.get("market_momentum_sp125", {}),
        },
        "stock_price_strength": {
            "name": "Stock Price Strength (52-week highs/lows)",
            "data": data.get("stock_price_strength", {}),
        },
        "stock_price_breadth": {
            "name": "Stock Price Breadth (advancing vs declining volume)",
            "data": data.get("stock_price_breadth", {}),
        },
        "put_call_options": {
            "name": "Put/Call Options Ratio",
            "data": data.get("put_call_options", {}),
        },
        "market_volatility_vix": {
            "name": "Market Volatility (VIX)",
            "data": data.get("market_volatility_vix", {}),
        },
        "junk_bond_demand": {
            "name": "Junk Bond Demand (high yield spreads)",
            "data": data.get("junk_bond_demand", {}),
        },
        "safe_haven_demand": {
            "name": "Safe Haven Demand (stocks vs bonds)",
            "data": data.get("safe_haven_demand", {}),
        },
    }
    
    # Extract key metrics from each component
    component_summary = {}
    for key, info in components.items():
        comp_data = info["data"]
        if comp_data:
            component_summary[key] = {
                "name": info["name"],
                "score": round(comp_data.get("score", 0), 2),
                "rating": comp_data.get("rating", "unknown"),
                "timestamp": comp_data.get("timestamp"),
            }
    
    return {
        "success": True,
        "components": component_summary,
        "component_count": len(component_summary),
        "timestamp": datetime.now().isoformat(),
        "source": "CNN Fear & Greed Index"
    }


def get_fear_greed_history(days: int = 30) -> Dict:
    """
    Get historical Fear & Greed Index scores
    
    Args:
        days: Number of days of history to return (default 30, max ~250)
    
    Returns:
        Dict with historical scores, dates, and ratings
    """
    result = _fetch_fear_greed_data()
    
    if not result["success"]:
        return result
    
    data = result["data"]
    historical = data.get("fear_and_greed_historical", {})
    
    hist_data = historical.get("data", [])
    
    # Filter to requested number of days
    if days < len(hist_data):
        hist_data = hist_data[-days:]
    
    # Format historical data
    formatted_history = []
    for point in hist_data:
        formatted_history.append({
            "date": datetime.fromtimestamp(point["x"] / 1000).strftime("%Y-%m-%d"),
            "score": round(point["y"], 2),
            "rating": point.get("rating", _rating_from_score(point["y"]))
        })
    
    # Calculate statistics
    scores = [p["y"] for p in hist_data]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "success": True,
        "history": formatted_history,
        "days_requested": days,
        "days_returned": len(formatted_history),
        "average_score": round(avg_score, 2),
        "min_score": round(min(scores), 2) if scores else 0,
        "max_score": round(max(scores), 2) if scores else 0,
        "current_score": round(hist_data[-1]["y"], 2) if hist_data else 0,
        "source": "CNN Fear & Greed Index"
    }


def get_fear_greed_signal() -> Dict:
    """
    Generate trading signal based on contrarian logic
    
    Contrarian Strategy:
    - Extreme Fear (0-25) → BUY signal (market oversold)
    - Fear (25-45) → ACCUMULATE signal
    - Neutral (45-55) → HOLD signal
    - Greed (55-75) → REDUCE signal
    - Extreme Greed (75-100) → SELL signal (market overbought)
    
    Returns:
        Dict with signal, score, rating, and reasoning
    """
    index_result = get_fear_greed_index()
    
    if not index_result["success"]:
        return index_result
    
    score = index_result["current_score"]
    rating = index_result["rating"]
    
    # Contrarian signal mapping
    if score < 25:
        signal = "BUY"
        reasoning = "Extreme fear indicates market oversold. Contrarian opportunity."
        strength = "STRONG"
    elif score < 45:
        signal = "ACCUMULATE"
        reasoning = "Fear sentiment suggests potential buying opportunity."
        strength = "MODERATE"
    elif score < 55:
        signal = "HOLD"
        reasoning = "Neutral sentiment. No clear directional bias."
        strength = "NEUTRAL"
    elif score < 75:
        signal = "REDUCE"
        reasoning = "Greed building. Consider taking some profits."
        strength = "MODERATE"
    else:
        signal = "SELL"
        reasoning = "Extreme greed indicates market overbought. Risk of correction."
        strength = "STRONG"
    
    # Add historical context
    components = get_fear_greed_components()
    
    return {
        "success": True,
        "signal": signal,
        "strength": strength,
        "current_score": score,
        "rating": rating,
        "reasoning": reasoning,
        "contrarian_logic": "Buy fear, sell greed",
        "timestamp": index_result["timestamp"],
        "historical_context": {
            "change_from_yesterday": index_result["change_from_yesterday"],
            "change_from_week": index_result["change_from_week"],
            "change_from_month": index_result["change_from_month"],
        },
        "component_count": components.get("component_count", 0),
        "source": "CNN Fear & Greed Index"
    }


def _interpret_score(score: float) -> str:
    """
    Provide human-readable interpretation of score
    
    Args:
        score: Fear & Greed score (0-100)
    
    Returns:
        Interpretation string
    """
    if score < 25:
        return "Markets are in extreme fear. Investors are very worried."
    elif score < 45:
        return "Markets showing fear. Investors are concerned about risk."
    elif score < 55:
        return "Markets are neutral. No strong directional sentiment."
    elif score < 75:
        return "Markets showing greed. Investors are taking on more risk."
    else:
        return "Markets are in extreme greed. Investors are very bullish."


if __name__ == "__main__":
    # CLI demonstration
    import json
    
    print("=" * 60)
    print("CNN Fear & Greed Index")
    print("=" * 60)
    
    # Current index
    print("\n1. Current Fear & Greed Index:")
    index = get_fear_greed_index()
    print(json.dumps(index, indent=2))
    
    # Components
    print("\n2. Component Breakdown:")
    components = get_fear_greed_components()
    if components["success"]:
        for comp_key, comp_data in components["components"].items():
            print(f"  {comp_data['name']}: {comp_data['score']} ({comp_data['rating']})")
    
    # Trading signal
    print("\n3. Trading Signal (Contrarian):")
    signal = get_fear_greed_signal()
    if signal["success"]:
        print(f"  Signal: {signal['signal']} ({signal['strength']})")
        print(f"  Score: {signal['current_score']} ({signal['rating']})")
        print(f"  Reasoning: {signal['reasoning']}")
    
    # Recent history
    print("\n4. Last 7 Days:")
    history = get_fear_greed_history(days=7)
    if history["success"]:
        for day in history["history"]:
            print(f"  {day['date']}: {day['score']} ({day['rating']})")
