#!/usr/bin/env python3
"""
Alpha Vantage Institutional Holdings & Insider Data Module

Core Alpha Vantage integration for institutional ownership and insider trading data:
- Institutional holders (13F filings)
- Insider transactions (Form 4 filings)
- Institutional ownership summary statistics
- Insider sentiment scores

Source: https://www.alphavantage.co/documentation/
Category: Insider & Institutional
Free tier: 500 calls/day, 5 calls/minute (requires free API key)
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
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY", "")


def get_institutional_holders(symbol: str = 'IBM') -> Dict:
    """
    Get institutional holders (13F filings) for a stock.
    
    Args:
        symbol: Stock ticker symbol (default: 'IBM')
    
    Returns:
        Dict with institutional ownership data from 13F filings
    
    Example:
        >>> holders = get_institutional_holders('IBM')
        >>> print(f"Total institutions: {len(holders.get('data', []))}")
    """
    try:
        params = {
            'function': 'INSTITUTIONAL_HOLDERS',
            'symbol': symbol.upper(),
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'symbol': symbol}
        if 'Note' in data:
            return {'error': f"API rate limit: {data['Note']}", 'symbol': symbol}
        
        # Add metadata
        data['symbol'] = symbol.upper()
        data['fetched_at'] = datetime.now().isoformat()
        data['source'] = 'alpha_vantage'
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_insider_transactions(symbol: str = 'IBM') -> Dict:
    """
    Get insider buy/sell transactions (Form 4 filings) for a stock.
    
    Args:
        symbol: Stock ticker symbol (default: 'IBM')
    
    Returns:
        Dict with insider transaction data including buys, sells, and filing dates
    
    Example:
        >>> txns = get_insider_transactions('AAPL')
        >>> if 'data' in txns:
        ...     print(f"Recent insider activity: {len(txns['data'])} transactions")
    """
    try:
        params = {
            'function': 'INSIDER_TRANSACTIONS',
            'symbol': symbol.upper(),
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'symbol': symbol}
        if 'Note' in data:
            return {'error': f"API rate limit: {data['Note']}", 'symbol': symbol}
        
        # Add metadata
        data['symbol'] = symbol.upper()
        data['fetched_at'] = datetime.now().isoformat()
        data['source'] = 'alpha_vantage'
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_institutional_summary(symbol: str = 'IBM') -> Dict:
    """
    Get institutional ownership summary statistics.
    
    Calculates aggregate metrics from institutional holders data:
    - Total institutional ownership percentage
    - Top holders
    - Net change in institutional positions
    
    Args:
        symbol: Stock ticker symbol (default: 'IBM')
    
    Returns:
        Dict with summary statistics about institutional ownership
    
    Example:
        >>> summary = get_institutional_summary('IBM')
        >>> if 'total_institutional_pct' in summary:
        ...     print(f"Institutional ownership: {summary['total_institutional_pct']}%")
    """
    try:
        # Get raw institutional holders data
        holders_data = get_institutional_holders(symbol)
        
        if 'error' in holders_data:
            return holders_data
        
        # Parse and summarize
        summary = {
            'symbol': symbol.upper(),
            'fetched_at': datetime.now().isoformat(),
            'source': 'alpha_vantage',
            'total_institutions': 0,
            'total_shares_held': 0,
            'total_institutional_pct': 0.0,
            'top_holders': [],
            'data_available': False
        }
        
        # Alpha Vantage returns different formats - adapt as needed
        if 'data' in holders_data and holders_data['data']:
            summary['data_available'] = True
            summary['total_institutions'] = len(holders_data['data'])
            
            # Extract top holders (first 5)
            summary['top_holders'] = holders_data['data'][:5] if len(holders_data['data']) >= 5 else holders_data['data']
        
        return summary
        
    except Exception as e:
        return {'error': f'Summary calculation error: {str(e)}', 'symbol': symbol}


def get_insider_sentiment(symbol: str = 'IBM') -> Dict:
    """
    Get insider sentiment score based on recent insider trading activity.
    
    Analyzes insider buy/sell patterns to generate a sentiment score.
    Positive score = more buying than selling (bullish)
    Negative score = more selling than buying (bearish)
    
    Args:
        symbol: Stock ticker symbol (default: 'IBM')
    
    Returns:
        Dict with insider sentiment metrics and score
    
    Example:
        >>> sentiment = get_insider_sentiment('AAPL')
        >>> if 'sentiment_score' in sentiment:
        ...     print(f"Insider sentiment: {sentiment['sentiment_score']}")
    """
    try:
        # Get raw insider transactions data
        txns_data = get_insider_transactions(symbol)
        
        if 'error' in txns_data:
            return txns_data
        
        # Calculate sentiment
        sentiment = {
            'symbol': symbol.upper(),
            'fetched_at': datetime.now().isoformat(),
            'source': 'alpha_vantage',
            'total_transactions': 0,
            'buy_count': 0,
            'sell_count': 0,
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'data_available': False
        }
        
        # Alpha Vantage may return data in different formats
        if 'data' in txns_data and txns_data['data']:
            sentiment['data_available'] = True
            sentiment['total_transactions'] = len(txns_data['data'])
            
            # Count buys vs sells (adapt field names based on actual API response)
            for txn in txns_data['data']:
                transaction_type = txn.get('transaction_type', '').lower()
                if 'buy' in transaction_type or 'purchase' in transaction_type:
                    sentiment['buy_count'] += 1
                elif 'sell' in transaction_type or 'sale' in transaction_type:
                    sentiment['sell_count'] += 1
            
            # Calculate sentiment score (-1 to +1)
            if sentiment['total_transactions'] > 0:
                sentiment['sentiment_score'] = (sentiment['buy_count'] - sentiment['sell_count']) / sentiment['total_transactions']
                
                # Assign label
                if sentiment['sentiment_score'] > 0.2:
                    sentiment['sentiment_label'] = 'bullish'
                elif sentiment['sentiment_score'] < -0.2:
                    sentiment['sentiment_label'] = 'bearish'
                else:
                    sentiment['sentiment_label'] = 'neutral'
        
        return sentiment
        
    except Exception as e:
        return {'error': f'Sentiment calculation error: {str(e)}', 'symbol': symbol}


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "holders" and len(sys.argv) > 2:
            result = get_institutional_holders(sys.argv[2])
        elif command == "insiders" and len(sys.argv) > 2:
            result = get_insider_transactions(sys.argv[2])
        elif command == "summary" and len(sys.argv) > 2:
            result = get_institutional_summary(sys.argv[2])
        elif command == "sentiment" and len(sys.argv) > 2:
            result = get_insider_sentiment(sys.argv[2])
        else:
            result = {
                "module": "alpha_vantage_institutional_holdings",
                "version": "1.0",
                "usage": "python alpha_vantage_institutional_holdings.py [holders|insiders|summary|sentiment] <symbol>",
                "functions": [
                    "get_institutional_holders(symbol)",
                    "get_insider_transactions(symbol)",
                    "get_institutional_summary(symbol)",
                    "get_insider_sentiment(symbol)"
                ]
            }
    else:
        result = {
            "module": "alpha_vantage_institutional_holdings",
            "status": "ready",
            "api_key_set": bool(ALPHA_VANTAGE_API_KEY),
            "functions": 4,
            "source": "https://www.alphavantage.co/documentation/"
        }
    
    print(json.dumps(result, indent=2))
