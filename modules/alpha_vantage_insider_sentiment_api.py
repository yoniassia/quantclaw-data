#!/usr/bin/env python3
"""
Alpha Vantage Insider Sentiment API

Provides insider sentiment data based on SEC filings, including monthly aggregates 
of insider transactions. Helps gauge institutional confidence and insider activity.

Source: https://www.alphavantage.co/documentation/#insider-sentiment
Category: Insider & Institutional
Free tier: True (5 calls/min, 500 calls/day - requires ALPHA_VANTAGE_API_KEY)
Update frequency: Monthly aggregates with daily underlying updates
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


def get_insider_sentiment(symbol: str) -> Dict:
    """
    Get insider sentiment data for a specific stock symbol.
    
    Retrieves aggregated insider trading sentiment based on SEC filings,
    including monthly buy/sell ratios, transaction counts, and sentiment scores.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'IBM')
    
    Returns:
        Dict with keys: symbol, feed (list of monthly sentiment data)
        Each feed item contains: year, month, change, mspr_change, sentiment_score, etc.
    
    Example:
        >>> sentiment = get_insider_sentiment('AAPL')
        >>> if 'feed' in sentiment:
        ...     latest = sentiment['feed'][0]
        ...     print(f"Latest sentiment: {latest.get('sentiment_score')}")
    """
    try:
        params = {
            'function': 'INSIDER_SENTIMENT',
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
            return {'error': 'Rate limit exceeded', 'note': data['Note']}
        if 'Information' in data:
            return {'error': 'API limit reached', 'info': data['Information']}
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}', 'symbol': symbol}
    except json.JSONDecodeError as e:
        return {'error': f'JSON decode error: {str(e)}', 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_insider_transactions(symbol: str, limit: int = 10) -> List[Dict]:
    """
    Get recent insider transactions for a specific stock symbol.
    
    Extracts individual transaction records from the sentiment feed,
    providing details on insider buying/selling activity.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'IBM')
        limit: Maximum number of transactions to return (default: 10)
    
    Returns:
        List of Dict with transaction details (year, month, change, mspr_change, etc.)
    
    Example:
        >>> transactions = get_insider_transactions('MSFT', limit=5)
        >>> for txn in transactions[:3]:
        ...     print(f"{txn.get('year')}-{txn.get('month')}: {txn.get('change')} shares")
    """
    try:
        data = get_insider_sentiment(symbol)
        
        if 'error' in data:
            return [data]
        
        feed = data.get('feed', [])
        if not feed:
            return [{'error': 'No transaction data available', 'symbol': symbol}]
        
        # Return limited number of most recent transactions
        return feed[:limit]
        
    except Exception as e:
        return [{'error': f'Failed to get transactions: {str(e)}', 'symbol': symbol}]


def get_insider_summary(symbol: str) -> Dict:
    """
    Get summarized insider sentiment metrics for a stock.
    
    Calculates aggregate metrics including total change, average sentiment,
    recent activity trends, and buy/sell balance.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'IBM')
    
    Returns:
        Dict with keys: symbol, total_months, total_change, avg_mspr_change,
        recent_sentiment, buy_sell_ratio, latest_activity
    
    Example:
        >>> summary = get_insider_summary('AAPL')
        >>> print(f"Buy/Sell Ratio: {summary.get('buy_sell_ratio')}")
        >>> print(f"Recent Sentiment: {summary.get('recent_sentiment')}")
    """
    try:
        data = get_insider_sentiment(symbol)
        
        if 'error' in data:
            return data
        
        feed = data.get('feed', [])
        if not feed:
            return {'error': 'No data available for summary', 'symbol': symbol}
        
        # Calculate summary metrics
        total_change = sum(int(item.get('change', 0)) for item in feed)
        avg_mspr = sum(float(item.get('mspr_change', 0)) for item in feed if item.get('mspr_change')) / max(len(feed), 1)
        
        # Recent activity (last 3 months)
        recent_feed = feed[:3]
        recent_change = sum(int(item.get('change', 0)) for item in recent_feed)
        
        # Buy/sell ratio
        buys = sum(1 for item in feed if int(item.get('change', 0)) > 0)
        sells = sum(1 for item in feed if int(item.get('change', 0)) < 0)
        buy_sell_ratio = round(buys / max(sells, 1), 2) if sells > 0 else float('inf')
        
        # Latest activity
        latest = feed[0] if feed else {}
        
        summary = {
            'symbol': symbol,
            'total_months': len(feed),
            'total_change': total_change,
            'avg_mspr_change': round(avg_mspr, 4),
            'recent_change_3mo': recent_change,
            'buy_months': buys,
            'sell_months': sells,
            'buy_sell_ratio': buy_sell_ratio,
            'latest_activity': {
                'year': latest.get('year'),
                'month': latest.get('month'),
                'change': latest.get('change'),
                'mspr_change': latest.get('mspr_change')
            }
        }
        
        return summary
        
    except Exception as e:
        return {'error': f'Failed to generate summary: {str(e)}', 'symbol': symbol}


def analyze_insider_activity(symbol: str) -> Dict:
    """
    Analyze insider activity and provide actionable insights.
    
    Interprets insider sentiment data to determine if insiders are bullish,
    bearish, or neutral. Includes confidence scores and trend analysis.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'IBM')
    
    Returns:
        Dict with keys: symbol, sentiment (bullish/bearish/neutral), 
        confidence, trend, key_metrics, interpretation
    
    Example:
        >>> analysis = analyze_insider_activity('MSFT')
        >>> print(f"Sentiment: {analysis.get('sentiment')}")
        >>> print(f"Confidence: {analysis.get('confidence')}")
        >>> print(f"Interpretation: {analysis.get('interpretation')}")
    """
    try:
        summary = get_insider_summary(symbol)
        
        if 'error' in summary:
            return summary
        
        # Determine sentiment based on metrics
        buy_sell_ratio = summary.get('buy_sell_ratio', 1.0)
        recent_change = summary.get('recent_change_3mo', 0)
        total_change = summary.get('total_change', 0)
        
        # Sentiment classification
        if buy_sell_ratio > 1.5 and recent_change > 0:
            sentiment = 'bullish'
            confidence = 'high' if buy_sell_ratio > 2.0 else 'medium'
        elif buy_sell_ratio < 0.67 and recent_change < 0:
            sentiment = 'bearish'
            confidence = 'high' if buy_sell_ratio < 0.5 else 'medium'
        else:
            sentiment = 'neutral'
            confidence = 'low'
        
        # Trend analysis
        if recent_change > 0 and total_change > 0:
            trend = 'accumulating'
        elif recent_change < 0 and total_change < 0:
            trend = 'distributing'
        elif recent_change > 0 and total_change < 0:
            trend = 'reversing_positive'
        elif recent_change < 0 and total_change > 0:
            trend = 'reversing_negative'
        else:
            trend = 'stable'
        
        # Generate interpretation
        interpretations = {
            'bullish': f"Insiders are buying (buy/sell ratio: {buy_sell_ratio}). Positive signal for stock outlook.",
            'bearish': f"Insiders are selling (buy/sell ratio: {buy_sell_ratio}). Caution warranted.",
            'neutral': f"Insider activity is balanced (buy/sell ratio: {buy_sell_ratio}). No clear directional signal."
        }
        
        analysis = {
            'symbol': symbol,
            'sentiment': sentiment,
            'confidence': confidence,
            'trend': trend,
            'key_metrics': {
                'buy_sell_ratio': buy_sell_ratio,
                'recent_change_3mo': recent_change,
                'total_change': total_change,
                'total_months_analyzed': summary.get('total_months', 0)
            },
            'interpretation': interpretations.get(sentiment, 'Unable to determine sentiment'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        return {'error': f'Analysis failed: {str(e)}', 'symbol': symbol}


def demo():
    """
    Demonstrate all module functions with example stocks.
    
    Tests the module with AAPL and MSFT, showing output from each function.
    """
    print("=" * 80)
    print("Alpha Vantage Insider Sentiment API - Demo")
    print("=" * 80)
    
    test_symbols = ['AAPL', 'MSFT']
    
    for symbol in test_symbols:
        print(f"\n{'─' * 80}")
        print(f"Testing with {symbol}")
        print('─' * 80)
        
        # Test 1: Get insider sentiment
        print(f"\n1. get_insider_sentiment('{symbol}'):")
        sentiment = get_insider_sentiment(symbol)
        if 'error' in sentiment:
            print(f"   Error: {sentiment['error']}")
        else:
            feed_count = len(sentiment.get('feed', []))
            print(f"   ✓ Retrieved {feed_count} months of sentiment data")
            if feed_count > 0:
                latest = sentiment['feed'][0]
                print(f"   Latest: {latest.get('year')}-{latest.get('month')} | Change: {latest.get('change')} | MSPR: {latest.get('mspr_change')}")
        
        # Test 2: Get transactions
        print(f"\n2. get_insider_transactions('{symbol}', limit=5):")
        transactions = get_insider_transactions(symbol, limit=5)
        if transactions and 'error' in transactions[0]:
            print(f"   Error: {transactions[0]['error']}")
        else:
            print(f"   ✓ Retrieved {len(transactions)} recent transactions")
            for i, txn in enumerate(transactions[:3], 1):
                print(f"   {i}. {txn.get('year')}-{txn.get('month')}: {txn.get('change')} shares")
        
        # Test 3: Get summary
        print(f"\n3. get_insider_summary('{symbol}'):")
        summary = get_insider_summary(symbol)
        if 'error' in summary:
            print(f"   Error: {summary['error']}")
        else:
            print(f"   ✓ Summary generated:")
            print(f"   Total months: {summary.get('total_months')}")
            print(f"   Total change: {summary.get('total_change')}")
            print(f"   Buy/Sell ratio: {summary.get('buy_sell_ratio')}")
            print(f"   Recent 3mo change: {summary.get('recent_change_3mo')}")
        
        # Test 4: Analyze activity
        print(f"\n4. analyze_insider_activity('{symbol}'):")
        analysis = analyze_insider_activity(symbol)
        if 'error' in analysis:
            print(f"   Error: {analysis['error']}")
        else:
            print(f"   ✓ Analysis complete:")
            print(f"   Sentiment: {analysis.get('sentiment').upper()} ({analysis.get('confidence')} confidence)")
            print(f"   Trend: {analysis.get('trend')}")
            print(f"   {analysis.get('interpretation')}")
        
        print()
    
    print("=" * 80)
    print(f"Demo complete | API Key: {ALPHA_VANTAGE_API_KEY[:10]}..." if len(ALPHA_VANTAGE_API_KEY) > 10 else f"Demo complete | API Key: {ALPHA_VANTAGE_API_KEY}")
    print("=" * 80)


if __name__ == "__main__":
    demo()
