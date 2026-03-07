#!/usr/bin/env python3
"""
Finnhub Insider API — Insider Trading & Institutional Ownership Module

Real-time and historical insider trading data from SEC filings, including:
- Insider transactions (buys, sells, option exercises)
- Insider sentiment aggregates
- Institutional ownership breakdowns
- Mutual fund/ETF ownership
- Summary statistics for insider activity

Source: https://finnhub.io/docs/api/insider-transactions
Category: Insider & Institutional
Free tier: True (60 calls/minute, 500 calls/day)
Author: QuantClaw Data NightBuilder
Phase: Night Build 2026-03-07
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

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def _make_finnhub_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Helper function to make Finnhub API requests
    
    Args:
        endpoint: API endpoint (e.g., '/stock/insider-transactions')
        params: Query parameters (symbol, dates, etc.)
    
    Returns:
        Dict with response data or error information
    """
    try:
        if not FINNHUB_API_KEY:
            return {
                "success": False,
                "error": "FINNHUB_API_KEY not found in environment"
            }
        
        url = f"{FINNHUB_BASE_URL}{endpoint}"
        request_params = params.copy() if params else {}
        request_params["token"] = FINNHUB_API_KEY
        
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
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


def get_insider_transactions(
    symbol: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict:
    """
    Get insider transactions (buys, sells, option exercises) for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        from_date: Start date in YYYY-MM-DD format (default: 90 days ago)
        to_date: End date in YYYY-MM-DD format (default: today)
    
    Returns:
        Dict with insider transaction data including:
        - name: Insider name
        - share: Number of shares transacted
        - change: Net change in shares
        - filingDate: SEC filing date
        - transactionDate: Transaction date
        - transactionPrice: Price per share
        - transactionCode: Transaction type code
    """
    # Default to last 90 days if dates not provided
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    params = {
        "symbol": symbol.upper(),
        "from": from_date,
        "to": to_date
    }
    
    result = _make_finnhub_request("/stock/insider-transactions", params)
    
    if not result["success"]:
        return result
    
    transactions = result["data"].get("data", [])
    
    # Calculate summary stats
    total_buys = sum(1 for t in transactions if t.get("change", 0) > 0)
    total_sells = sum(1 for t in transactions if t.get("change", 0) < 0)
    total_value_bought = sum(
        abs(t.get("change", 0)) * t.get("transactionPrice", 0)
        for t in transactions if t.get("change", 0) > 0
    )
    total_value_sold = sum(
        abs(t.get("change", 0)) * t.get("transactionPrice", 0)
        for t in transactions if t.get("change", 0) < 0
    )
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "from_date": from_date,
        "to_date": to_date,
        "transactions": transactions,
        "count": len(transactions),
        "summary": {
            "total_buys": total_buys,
            "total_sells": total_sells,
            "total_value_bought": round(total_value_bought, 2),
            "total_value_sold": round(total_value_sold, 2),
            "net_value": round(total_value_bought - total_value_sold, 2)
        },
        "timestamp": datetime.now().isoformat()
    }


def get_insider_sentiment(symbol: str) -> Dict:
    """
    Get aggregate insider sentiment score for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        Dict with insider sentiment data including:
        - mspr: Monthly share purchase ratio
        - change: Net change in shares
        - Aggregated buy/sell statistics by month
    """
    params = {"symbol": symbol.upper()}
    
    result = _make_finnhub_request("/stock/insider-sentiment", params)
    
    if not result["success"]:
        return result
    
    sentiment_data = result["data"].get("data", [])
    
    if not sentiment_data:
        return {
            "success": True,
            "symbol": symbol.upper(),
            "sentiment": [],
            "analysis": "No insider sentiment data available",
            "timestamp": datetime.now().isoformat()
        }
    
    # Calculate overall sentiment trend
    recent_months = sentiment_data[-6:] if len(sentiment_data) >= 6 else sentiment_data
    avg_mspr = sum(m.get("mspr", 0) for m in recent_months) / len(recent_months) if recent_months else 0
    avg_change = sum(m.get("change", 0) for m in recent_months) / len(recent_months) if recent_months else 0
    
    # Interpret sentiment
    if avg_mspr > 0 and avg_change > 0:
        sentiment_signal = "Bullish (insiders buying)"
    elif avg_mspr < 0 and avg_change < 0:
        sentiment_signal = "Bearish (insiders selling)"
    else:
        sentiment_signal = "Neutral"
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "sentiment": sentiment_data,
        "recent_trend": {
            "avg_mspr": round(avg_mspr, 4),
            "avg_change": round(avg_change, 2),
            "signal": sentiment_signal,
            "months_analyzed": len(recent_months)
        },
        "timestamp": datetime.now().isoformat()
    }


def get_ownership(symbol: str) -> Dict:
    """
    Get institutional ownership breakdown for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        Dict with institutional ownership data including:
        - Investor names
        - Share counts
        - Portfolio percentages
        - Report dates
    """
    params = {"symbol": symbol.upper()}
    
    result = _make_finnhub_request("/stock/ownership", params)
    
    if not result["success"]:
        return result
    
    ownership_data = result["data"].get("ownership", [])
    
    if not ownership_data:
        return {
            "success": True,
            "symbol": symbol.upper(),
            "ownership": [],
            "analysis": "No institutional ownership data available",
            "timestamp": datetime.now().isoformat()
        }
    
    # Calculate total institutional shares
    total_shares = sum(owner.get("share", 0) for owner in ownership_data)
    
    # Get top 10 holders
    sorted_owners = sorted(ownership_data, key=lambda x: x.get("share", 0), reverse=True)
    top_10 = sorted_owners[:10]
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "ownership": ownership_data,
        "count": len(ownership_data),
        "total_institutional_shares": total_shares,
        "top_10_holders": top_10,
        "timestamp": datetime.now().isoformat()
    }


def get_fund_ownership(symbol: str) -> Dict:
    """
    Get mutual fund and ETF ownership for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        Dict with fund ownership data including:
        - Fund names
        - Share counts
        - Portfolio weights
        - Report dates
    """
    params = {"symbol": symbol.upper()}
    
    result = _make_finnhub_request("/stock/fund-ownership", params)
    
    if not result["success"]:
        return result
    
    fund_data = result["data"].get("ownership", [])
    
    if not fund_data:
        return {
            "success": True,
            "symbol": symbol.upper(),
            "fund_ownership": [],
            "analysis": "No mutual fund/ETF ownership data available",
            "timestamp": datetime.now().isoformat()
        }
    
    # Calculate total fund shares
    total_fund_shares = sum(fund.get("share", 0) for fund in fund_data)
    
    # Get top funds by holdings
    sorted_funds = sorted(fund_data, key=lambda x: x.get("share", 0), reverse=True)
    top_funds = sorted_funds[:10]
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "fund_ownership": fund_data,
        "count": len(fund_data),
        "total_fund_shares": total_fund_shares,
        "top_10_funds": top_funds,
        "timestamp": datetime.now().isoformat()
    }


def get_insider_summary(symbol: str, lookback_days: int = 90) -> Dict:
    """
    Get comprehensive insider activity summary for a symbol
    Combines transactions, sentiment, and ownership data
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        lookback_days: Number of days to analyze (default: 90)
    
    Returns:
        Dict with comprehensive insider summary including:
        - Transaction statistics (total buys vs sells, net value)
        - Sentiment trend
        - Key institutional holders
        - Overall insider signal
    """
    from_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    
    # Gather all insider data
    transactions = get_insider_transactions(symbol, from_date, to_date)
    sentiment = get_insider_sentiment(symbol)
    ownership = get_ownership(symbol)
    
    # Compile summary
    summary = {
        "success": True,
        "symbol": symbol.upper(),
        "period": f"{from_date} to {to_date}",
        "lookback_days": lookback_days
    }
    
    # Transaction summary
    if transactions.get("success"):
        summary["transactions"] = transactions.get("summary", {})
        summary["transaction_count"] = transactions.get("count", 0)
    
    # Sentiment summary
    if sentiment.get("success"):
        summary["sentiment"] = sentiment.get("recent_trend", {})
    
    # Ownership summary
    if ownership.get("success"):
        summary["institutional_holders"] = ownership.get("count", 0)
        summary["total_institutional_shares"] = ownership.get("total_institutional_shares", 0)
        
        top_holders = ownership.get("top_10_holders", [])
        if top_holders:
            summary["top_3_holders"] = [
                {
                    "name": h.get("name", "Unknown"),
                    "shares": h.get("share", 0)
                }
                for h in top_holders[:3]
            ]
    
    # Generate overall signal
    signals = []
    
    if transactions.get("success"):
        net_value = transactions.get("summary", {}).get("net_value", 0)
        if net_value > 0:
            signals.append("Positive net insider buying")
        elif net_value < 0:
            signals.append("Net insider selling")
    
    if sentiment.get("success"):
        sentiment_signal = sentiment.get("recent_trend", {}).get("signal", "")
        if sentiment_signal:
            signals.append(sentiment_signal)
    
    summary["overall_signal"] = " | ".join(signals) if signals else "Insufficient data"
    summary["timestamp"] = datetime.now().isoformat()
    
    return summary


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Finnhub Insider API Module")
    print("=" * 60)
    
    test_symbol = "AAPL"
    
    print(f"\nTesting with {test_symbol}...")
    
    # Test insider summary (combines all data)
    summary = get_insider_summary(test_symbol)
    print("\n" + json.dumps(summary, indent=2))
