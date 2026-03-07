#!/usr/bin/env python3
"""
Finnhub Institutional API — Institutional Ownership & Insider Trading Data

Provides access to:
- 13F institutional ownership filings (quarterly)
- Institutional portfolio holdings by CIK
- Insider transactions (real-time from SEC Form 4)
- Insider sentiment analysis
- Fund ownership data

Source: https://finnhub.io/docs/api/institutional-ownership
Category: Insider & Institutional
Free tier: 60 calls/minute, 500,000 calls/month
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

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def _make_finnhub_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Helper function to make Finnhub API requests with error handling
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/institutional-ownership')
        params: Optional query parameters
    
    Returns:
        Dict with success flag and data or error message
    """
    try:
        if not FINNHUB_API_KEY:
            return {
                "success": False,
                "error": "FINNHUB_API_KEY not found in environment"
            }
        
        url = f"{FINNHUB_BASE_URL}{endpoint}"
        request_params = params or {}
        request_params["token"] = FINNHUB_API_KEY
        
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"error": "..."} on API errors
        if isinstance(data, dict) and "error" in data:
            return {
                "success": False,
                "error": data["error"]
            }
        
        return {
            "success": True,
            "data": data
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


def get_institutional_ownership(symbol: str, limit: int = 50) -> Dict:
    """
    Get institutional ownership data from 13F filings
    
    Shows which hedge funds, mutual funds, and institutions own shares
    Updated quarterly based on SEC 13F filing deadlines
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        limit: Number of results to return (default 50)
    
    Returns:
        Dict with institutional holders, shares owned, value, and changes
    
    Example:
        >>> data = get_institutional_ownership('AAPL')
        >>> print(f"Top holder: {data['ownership'][0]['name']}")
    """
    result = _make_finnhub_request(
        '/stock/institutional-ownership',
        {'symbol': symbol.upper(), 'limit': limit}
    )
    
    if not result['success']:
        return result
    
    ownership_data = result['data']
    
    # Parse and enrich the data
    if isinstance(ownership_data, dict) and 'data' in ownership_data:
        holdings = ownership_data['data']
        
        # Calculate summary stats
        total_shares = sum(h.get('share', 0) for h in holdings)
        total_value = sum(h.get('value', 0) for h in holdings)
        
        # Sort by value
        holdings_sorted = sorted(
            holdings,
            key=lambda x: x.get('value', 0),
            reverse=True
        )
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "ownership": holdings_sorted[:limit],
            "summary": {
                "total_institutions": len(holdings),
                "total_shares": total_shares,
                "total_value_usd": total_value,
                "filing_date": ownership_data.get('filingDate', 'N/A')
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": False,
        "error": "Unexpected data format",
        "raw_data": ownership_data
    }


def get_institutional_portfolio(cik: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
    """
    Get institutional portfolio holdings by CIK (Central Index Key)
    
    Shows all positions held by a specific institution
    Useful for tracking smart money and following institutional investors
    
    Args:
        cik: SEC Central Index Key (e.g., '0001067983' for Berkshire Hathaway)
        from_date: Start date YYYY-MM-DD (optional)
        to_date: End date YYYY-MM-DD (optional)
    
    Returns:
        Dict with portfolio holdings, positions, and values
    
    Example:
        >>> portfolio = get_institutional_portfolio('0001067983')  # Berkshire
        >>> print(f"Holdings: {len(portfolio['holdings'])}")
    """
    params = {'cik': cik}
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date
    
    result = _make_finnhub_request('/institutional/portfolio', params)
    
    if not result['success']:
        return result
    
    portfolio_data = result['data']
    
    # Parse and analyze portfolio
    if isinstance(portfolio_data, dict) and 'data' in portfolio_data:
        holdings = portfolio_data['data']
        
        # Calculate portfolio metrics
        total_value = sum(h.get('value', 0) for h in holdings)
        
        # Top positions
        top_holdings = sorted(
            holdings,
            key=lambda x: x.get('value', 0),
            reverse=True
        )[:20]
        
        return {
            "success": True,
            "cik": cik,
            "holdings": top_holdings,
            "summary": {
                "total_positions": len(holdings),
                "total_value_usd": total_value,
                "filing_date": portfolio_data.get('filingDate', 'N/A'),
                "investor_name": portfolio_data.get('investorName', 'N/A')
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": False,
        "error": "Unexpected data format",
        "raw_data": portfolio_data
    }


def get_insider_transactions(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
    """
    Get insider transactions from SEC Form 4 filings
    
    Real-time feed of insider buying/selling by executives, directors, and large shareholders
    Critical signal for detecting insider knowledge and confidence
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        from_date: Start date YYYY-MM-DD (optional, defaults to last 12 months)
        to_date: End date YYYY-MM-DD (optional, defaults to today)
    
    Returns:
        Dict with insider transactions, names, positions, shares traded
    
    Example:
        >>> trades = get_insider_transactions('TSLA')
        >>> buys = [t for t in trades['transactions'] if t['transactionType'] == 'P']
        >>> print(f"Insider buys: {len(buys)}")
    """
    params = {'symbol': symbol.upper()}
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date
    
    result = _make_finnhub_request('/stock/insider-transactions', params)
    
    if not result['success']:
        return result
    
    transaction_data = result['data']
    
    # Parse and categorize transactions
    if isinstance(transaction_data, dict) and 'data' in transaction_data:
        transactions = transaction_data['data']
        
        # Categorize buys vs sells
        buys = [t for t in transactions if t.get('transactionCode') == 'P']
        sells = [t for t in transactions if t.get('transactionCode') == 'S']
        
        # Calculate net insider activity
        total_buy_shares = sum(t.get('share', 0) for t in buys)
        total_sell_shares = sum(t.get('share', 0) for t in sells)
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "transactions": transactions,
            "summary": {
                "total_transactions": len(transactions),
                "buy_transactions": len(buys),
                "sell_transactions": len(sells),
                "net_shares": total_buy_shares - total_sell_shares,
                "sentiment": "bullish" if total_buy_shares > total_sell_shares else "bearish" if total_sell_shares > total_buy_shares else "neutral"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": False,
        "error": "No transaction data found",
        "raw_data": transaction_data
    }


def get_insider_sentiment(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
    """
    Get aggregated insider sentiment metrics
    
    Provides sentiment scores based on insider trading patterns
    Combines transaction data with statistical analysis
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        from_date: Start date YYYY-MM-DD (optional)
        to_date: End date YYYY-MM-DD (optional)
    
    Returns:
        Dict with sentiment scores, MSPR (Monthly Share Purchase Ratio), and signals
    
    Example:
        >>> sentiment = get_insider_sentiment('AAPL')
        >>> print(f"MSPR: {sentiment['data'][0]['mspr']}")
    """
    params = {'symbol': symbol.upper()}
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date
    
    result = _make_finnhub_request('/stock/insider-sentiment', params)
    
    if not result['success']:
        return result
    
    sentiment_data = result['data']
    
    # Analyze sentiment trends
    if isinstance(sentiment_data, dict) and 'data' in sentiment_data:
        data_points = sentiment_data['data']
        
        if data_points:
            # Get latest sentiment
            latest = data_points[0]
            
            # Calculate average MSPR (Monthly Share Purchase Ratio)
            avg_mspr = sum(d.get('mspr', 0) for d in data_points) / len(data_points)
            
            # MSPR interpretation:
            # > 0: More buying than selling
            # < 0: More selling than buying
            # Magnitude matters: >0.5 or <-0.5 is significant
            
            sentiment_signal = "neutral"
            if avg_mspr > 0.5:
                sentiment_signal = "strong bullish"
            elif avg_mspr > 0:
                sentiment_signal = "bullish"
            elif avg_mspr < -0.5:
                sentiment_signal = "strong bearish"
            elif avg_mspr < 0:
                sentiment_signal = "bearish"
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "latest_sentiment": latest,
                "historical_data": data_points,
                "analysis": {
                    "average_mspr": round(avg_mspr, 4),
                    "sentiment_signal": sentiment_signal,
                    "data_points": len(data_points)
                },
                "timestamp": datetime.now().isoformat()
            }
    
    return {
        "success": False,
        "error": "No sentiment data available",
        "raw_data": sentiment_data
    }


def get_fund_ownership(symbol: str, limit: int = 50) -> Dict:
    """
    Get mutual fund ownership data
    
    Shows which mutual funds hold positions in the stock
    Complements institutional ownership with retail-focused funds
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        limit: Number of results to return (default 50)
    
    Returns:
        Dict with fund holders, shares, portfolio weights
    
    Example:
        >>> funds = get_fund_ownership('AAPL')
        >>> print(f"Top fund: {funds['ownership'][0]['name']}")
    """
    result = _make_finnhub_request(
        '/stock/fund-ownership',
        {'symbol': symbol.upper(), 'limit': limit}
    )
    
    if not result['success']:
        return result
    
    fund_data = result['data']
    
    # Parse fund ownership
    if isinstance(fund_data, dict) and 'ownership' in fund_data:
        ownership = fund_data['ownership']
        
        # Calculate metrics
        total_shares = sum(f.get('share', 0) for f in ownership)
        
        # Sort by share count
        ownership_sorted = sorted(
            ownership,
            key=lambda x: x.get('share', 0),
            reverse=True
        )
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "ownership": ownership_sorted[:limit],
            "summary": {
                "total_funds": len(ownership),
                "total_shares": total_shares,
                "report_date": fund_data.get('reportDate', 'N/A')
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": False,
        "error": "Unexpected data format",
        "raw_data": fund_data
    }


def get_ownership_summary(symbol: str) -> Dict:
    """
    Get comprehensive ownership summary combining institutional and fund data
    
    Provides a complete picture of who owns the stock
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict with combined institutional, fund, and insider data
    """
    institutional = get_institutional_ownership(symbol, limit=10)
    funds = get_fund_ownership(symbol, limit=10)
    insider_trans = get_insider_transactions(symbol)
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "institutional_ownership": institutional.get('summary', {}),
        "fund_ownership": funds.get('summary', {}),
        "insider_activity": insider_trans.get('summary', {}),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Finnhub Institutional & Insider Trading API")
    print("=" * 60)
    
    # Test with AAPL
    symbol = "AAPL"
    print(f"\nTesting with {symbol}...")
    
    # Institutional ownership
    print("\n1. Institutional Ownership:")
    inst_own = get_institutional_ownership(symbol, limit=5)
    if inst_own['success']:
        print(json.dumps(inst_own['summary'], indent=2))
        print(f"Top 3 holders:")
        for i, holder in enumerate(inst_own['ownership'][:3], 1):
            print(f"  {i}. {holder.get('name', 'N/A')}: {holder.get('share', 0):,} shares")
    else:
        print(f"Error: {inst_own['error']}")
    
    # Insider transactions
    print("\n2. Insider Transactions:")
    insider = get_insider_transactions(symbol)
    if insider['success']:
        print(json.dumps(insider['summary'], indent=2))
    else:
        print(f"Error: {insider['error']}")
    
    # Insider sentiment
    print("\n3. Insider Sentiment:")
    sentiment = get_insider_sentiment(symbol)
    if sentiment['success']:
        print(json.dumps(sentiment.get('analysis', {}), indent=2))
    else:
        print(f"Error: {sentiment['error']}")
    
    print("\n" + "=" * 60)
