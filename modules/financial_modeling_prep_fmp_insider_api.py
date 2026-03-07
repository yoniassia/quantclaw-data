#!/usr/bin/env python3
"""
Financial Modeling Prep (FMP) Insider API — Market Insider Trading Data Module

Core FMP integration for insider trading data including:
- Recent insider trades by ticker symbol
- Insider trades search by executive name
- Buy/sell ratio summaries for tickers
- CIK-based insider trade lookups
- Latest insider purchases across all markets

Source: https://site.financialmodelingprep.com/developer/docs/
Category: Insider & Institutional
Free tier: True (250 requests/day - requires FMP_API_KEY env var)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
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

# FMP API Configuration
FMP_BASE_URL = "https://financialmodelingprep.com/api"
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")


def get_insider_trades(symbol: str = 'AAPL', limit: int = 50) -> List[Dict]:
    """
    Get recent insider trades for a ticker symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        limit: Maximum number of trades to return (default: 50)
    
    Returns:
        List of dicts with keys: symbol, filingDate, transactionDate, 
                                reportingName, typeOfOwner, transactionType,
                                securitiesOwned, securitiesTransacted, price, link
    
    Example:
        >>> trades = get_insider_trades('AAPL', limit=10)
        >>> for trade in trades[:3]:
        ...     print(f"{trade['reportingName']}: {trade['transactionType']} {trade['securitiesTransacted']} shares")
    """
    try:
        url = f"{FMP_BASE_URL}/v4/insider-trading"
        params = {
            'symbol': symbol.upper(),
            'limit': limit,
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata to each trade
        if isinstance(data, list):
            for trade in data:
                trade['fetched_at'] = datetime.now().isoformat()
                trade['query_symbol'] = symbol.upper()
        
        return data if isinstance(data, list) else []
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e), 'symbol': symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'symbol': symbol}]


def get_insider_trades_by_name(name: str, limit: int = 20) -> List[Dict]:
    """
    Search insider trades by person/executive name.
    
    Args:
        name: Name of the insider/executive to search for
        limit: Maximum number of trades to return (default: 20)
    
    Returns:
        List of dicts with insider trade details matching the name
    
    Example:
        >>> trades = get_insider_trades_by_name('Tim Cook', limit=10)
        >>> for trade in trades:
        ...     print(f"{trade['symbol']}: {trade['transactionType']} on {trade['transactionDate']}")
    """
    try:
        url = f"{FMP_BASE_URL}/v4/insider-trading"
        params = {
            'name': name,
            'limit': limit,
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        if isinstance(data, list):
            for trade in data:
                trade['fetched_at'] = datetime.now().isoformat()
                trade['query_name'] = name
        
        return data if isinstance(data, list) else []
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e), 'name': name}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'name': name}]


def get_insider_summary(symbol: str = 'AAPL') -> Dict:
    """
    Summarize buy/sell ratio for a ticker's insider activity.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with summary statistics: total_trades, buys, sells, buy_sell_ratio,
                                     total_shares_bought, total_shares_sold, avg_price
    
    Example:
        >>> summary = get_insider_summary('AAPL')
        >>> print(f"Buy/Sell Ratio: {summary['buy_sell_ratio']:.2f}")
        >>> print(f"Total Buys: {summary['buys']}, Total Sells: {summary['sells']}")
    """
    try:
        # Fetch recent trades (larger sample for better summary)
        trades = get_insider_trades(symbol, limit=100)
        
        if not trades or 'error' in trades[0]:
            return {
                'error': 'Failed to fetch trades',
                'symbol': symbol.upper(),
                'fetched_at': datetime.now().isoformat()
            }
        
        # Calculate summary statistics
        buys = 0
        sells = 0
        total_shares_bought = 0
        total_shares_sold = 0
        buy_prices = []
        sell_prices = []
        
        for trade in trades:
            transaction_type = trade.get('transactionType', '').upper()
            shares = abs(float(trade.get('securitiesTransacted', 0) or 0))
            price = float(trade.get('price', 0) or 0)
            
            if 'P-Purchase' in transaction_type or 'BUY' in transaction_type:
                buys += 1
                total_shares_bought += shares
                if price > 0:
                    buy_prices.append(price)
            elif 'S-Sale' in transaction_type or 'SELL' in transaction_type:
                sells += 1
                total_shares_sold += shares
                if price > 0:
                    sell_prices.append(price)
        
        # Calculate ratios and averages
        buy_sell_ratio = buys / sells if sells > 0 else float('inf') if buys > 0 else 0
        avg_buy_price = sum(buy_prices) / len(buy_prices) if buy_prices else 0
        avg_sell_price = sum(sell_prices) / len(sell_prices) if sell_prices else 0
        
        return {
            'symbol': symbol.upper(),
            'total_trades': len(trades),
            'buys': buys,
            'sells': sells,
            'buy_sell_ratio': round(buy_sell_ratio, 2) if buy_sell_ratio != float('inf') else 'inf',
            'total_shares_bought': int(total_shares_bought),
            'total_shares_sold': int(total_shares_sold),
            'avg_buy_price': round(avg_buy_price, 2),
            'avg_sell_price': round(avg_sell_price, 2),
            'sentiment': 'bullish' if buy_sell_ratio > 1.5 else 'bearish' if buy_sell_ratio < 0.67 else 'neutral',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Summary calculation error: {str(e)}', 'symbol': symbol}


def get_cik_insider(cik: str) -> List[Dict]:
    """
    Get insider trades by CIK number (Central Index Key).
    
    Args:
        cik: CIK number (e.g., '0000320193' for Apple)
    
    Returns:
        List of dicts with insider trade details for the CIK
    
    Example:
        >>> trades = get_cik_insider('0000320193')  # Apple's CIK
        >>> print(f"Found {len(trades)} trades for CIK")
    """
    try:
        url = f"{FMP_BASE_URL}/v4/insider-trading"
        params = {
            'companyCik': cik,
            'limit': 100,
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        if isinstance(data, list):
            for trade in data:
                trade['fetched_at'] = datetime.now().isoformat()
                trade['query_cik'] = cik
        
        return data if isinstance(data, list) else []
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e), 'cik': cik}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'cik': cik}]


def get_latest_insider_buys(limit: int = 20) -> List[Dict]:
    """
    Get most recent insider purchases across all tickers.
    
    Args:
        limit: Maximum number of purchases to return (default: 20)
    
    Returns:
        List of dicts with recent insider purchase transactions
    
    Example:
        >>> buys = get_latest_insider_buys(limit=10)
        >>> for buy in buys[:5]:
        ...     print(f"{buy['symbol']}: {buy['reportingName']} bought {buy['securitiesTransacted']} shares")
    """
    try:
        url = f"{FMP_BASE_URL}/v4/insider-trading"
        params = {
            'transactionType': 'P-Purchase',
            'limit': limit,
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Filter for purchases and add metadata
        if isinstance(data, list):
            purchases = []
            for trade in data:
                transaction_type = trade.get('transactionType', '').upper()
                if 'P-PURCHASE' in transaction_type or 'BUY' in transaction_type:
                    trade['fetched_at'] = datetime.now().isoformat()
                    purchases.append(trade)
            return purchases[:limit]
        
        return []
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e)}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "trades" and len(sys.argv) > 2:
            result = get_insider_trades(sys.argv[2], limit=int(sys.argv[3]) if len(sys.argv) > 3 else 50)
        elif command == "name" and len(sys.argv) > 2:
            result = get_insider_trades_by_name(sys.argv[2], limit=int(sys.argv[3]) if len(sys.argv) > 3 else 20)
        elif command == "summary" and len(sys.argv) > 2:
            result = get_insider_summary(sys.argv[2])
        elif command == "cik" and len(sys.argv) > 2:
            result = get_cik_insider(sys.argv[2])
        elif command == "buys":
            result = get_latest_insider_buys(limit=int(sys.argv[2]) if len(sys.argv) > 2 else 20)
        else:
            result = {
                "module": "financial_modeling_prep_fmp_insider_api",
                "version": "1.0",
                "usage": "python financial_modeling_prep_fmp_insider_api.py [trades|name|summary|cik|buys] <symbol|name|cik>",
                "functions": [
                    "get_insider_trades(symbol, limit)",
                    "get_insider_trades_by_name(name, limit)",
                    "get_insider_summary(symbol)",
                    "get_cik_insider(cik)",
                    "get_latest_insider_buys(limit)"
                ]
            }
    else:
        result = {
            "module": "financial_modeling_prep_fmp_insider_api",
            "status": "ready",
            "api_key_set": bool(FMP_API_KEY),
            "functions": 5,
            "generated": "2026-03-07"
        }
    
    print(json.dumps(result, indent=2))
