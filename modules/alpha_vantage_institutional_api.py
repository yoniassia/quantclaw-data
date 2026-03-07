#!/usr/bin/env python3
"""
Alpha Vantage Institutional API — Institutional & Insider Ownership Module

Access to institutional ownership data (13F filings), insider transactions,
mutual fund/ETF holdings, and ownership concentration metrics for U.S. equities.

Key features:
- Top institutional holders for any U.S. stock
- Quarterly institutional ownership history (13F data)
- Mutual fund and ETF holdings breakdown
- Recent insider buy/sell transactions

Source: https://www.alphavantage.co/documentation/#institutional-ownership
Category: Insider & Institutional
Free tier: 5 calls/min, 500 calls/day (requires free API key)
Update frequency: Daily (13F filings are quarterly)
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
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# Rate limit info for reference
RATE_LIMIT = {
    "calls_per_minute": 5,
    "calls_per_day": 500,
    "tier": "free"
}


def _make_av_request(function: str, symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Internal helper to make Alpha Vantage API requests
    
    Args:
        function: Alpha Vantage API function name
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        api_key: Optional API key override
    
    Returns:
        Dict with parsed JSON response or error info
    """
    try:
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "apikey": api_key or AV_API_KEY
        }
        
        response = requests.get(AV_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if "Error Message" in data:
            return {
                "success": False,
                "error": data["Error Message"],
                "symbol": symbol
            }
        
        if "Note" in data:
            return {
                "success": False,
                "error": "Rate limit exceeded - " + data["Note"],
                "symbol": symbol,
                "rate_limit": RATE_LIMIT
            }
        
        if "Information" in data:
            return {
                "success": False,
                "error": data["Information"],
                "symbol": symbol
            }
        
        return {
            "success": True,
            "data": data,
            "symbol": symbol
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "symbol": symbol
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON decode error: {str(e)}",
            "symbol": symbol
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


def get_institutional_holders(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get top institutional holders for a stock (13F filings)
    
    Shows which hedge funds, mutual funds, and institutions own the most shares.
    Data comes from quarterly 13F filings required for institutions managing >$100M.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'MSFT', 'IBM')
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with:
        - top_holders: List of institutional holders with shares, value, % ownership
        - total_institutional_shares: Total shares held by institutions
        - institutional_ownership_pct: % of float owned by institutions
        - last_updated: Most recent 13F filing date
    
    Example:
        >>> data = get_institutional_holders('AAPL')
        >>> print(data['top_holders'][0]['holder'])
        'Vanguard Group Inc'
    """
    result = _make_av_request("INSTITUTIONAL_OWNERSHIP", symbol, api_key)
    
    if not result["success"]:
        return result
    
    raw_data = result["data"]
    
    # Parse institutional holders
    holders = []
    total_shares = 0
    
    # Alpha Vantage returns data in different formats - handle both
    if "data" in raw_data:
        holdings_data = raw_data["data"]
    elif "holdings" in raw_data:
        holdings_data = raw_data["holdings"]
    else:
        # Fallback - look for any list-like structure
        holdings_data = [v for v in raw_data.values() if isinstance(v, list)]
        holdings_data = holdings_data[0] if holdings_data else []
    
    for holder in holdings_data[:20]:  # Top 20 holders
        try:
            shares = int(holder.get("shares", 0))
            value = float(holder.get("value", 0))
            
            holders.append({
                "holder": holder.get("holder", holder.get("name", "Unknown")),
                "shares": shares,
                "value_usd": value,
                "ownership_pct": float(holder.get("ownership_percent", 0)),
                "filing_date": holder.get("date", holder.get("filing_date", ""))
            })
            
            total_shares += shares
        except (ValueError, TypeError):
            continue
    
    # Calculate summary metrics
    summary = raw_data.get("summary", {})
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "top_holders": holders,
        "total_institutional_shares": total_shares,
        "institutional_ownership_pct": summary.get("institutional_ownership_pct", 0),
        "last_updated": summary.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
        "holder_count": len(holders),
        "timestamp": datetime.now().isoformat()
    }


def get_institutional_ownership_history(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get quarterly institutional ownership changes over time
    
    Tracks how institutional ownership has changed quarter-by-quarter.
    Useful for identifying accumulation/distribution trends by smart money.
    
    Args:
        symbol: Stock ticker
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with:
        - quarterly_data: List of quarters with ownership %, shares, changes
        - trend: 'accumulating', 'distributing', or 'stable'
        - recent_change_pct: Change in ownership over last quarter
    
    Example:
        >>> data = get_institutional_ownership_history('MSFT')
        >>> print(data['trend'])
        'accumulating'
    """
    result = _make_av_request("INSTITUTIONAL_OWNERSHIP_HISTORY", symbol, api_key)
    
    if not result["success"]:
        # If specific history endpoint doesn't exist, derive from main endpoint
        base_result = get_institutional_holders(symbol, api_key)
        if base_result["success"]:
            return {
                "success": True,
                "symbol": symbol.upper(),
                "quarterly_data": [{
                    "quarter": base_result["last_updated"],
                    "ownership_pct": base_result["institutional_ownership_pct"],
                    "total_shares": base_result["total_institutional_shares"]
                }],
                "trend": "insufficient_data",
                "recent_change_pct": 0,
                "note": "Full historical data requires premium API access",
                "timestamp": datetime.now().isoformat()
            }
        return result
    
    raw_data = result["data"]
    
    # Parse quarterly history
    quarterly = []
    history_data = raw_data.get("history", raw_data.get("data", []))
    
    for quarter in history_data:
        quarterly.append({
            "quarter": quarter.get("quarter", quarter.get("date", "")),
            "ownership_pct": float(quarter.get("ownership_percent", 0)),
            "total_shares": int(quarter.get("shares", 0)),
            "holder_count": int(quarter.get("holders", 0)),
            "change_pct": float(quarter.get("change_percent", 0))
        })
    
    # Determine trend
    trend = "stable"
    recent_change = 0
    
    if len(quarterly) >= 2:
        recent_change = quarterly[0]["ownership_pct"] - quarterly[1]["ownership_pct"]
        
        if recent_change > 2:
            trend = "accumulating"
        elif recent_change < -2:
            trend = "distributing"
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "quarterly_data": quarterly,
        "trend": trend,
        "recent_change_pct": recent_change,
        "quarters_available": len(quarterly),
        "timestamp": datetime.now().isoformat()
    }


def get_fund_holdings(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get mutual fund and ETF holdings of a stock
    
    Shows which mutual funds and ETFs hold the stock and what % of their portfolio
    it represents. Useful for understanding fund exposure and potential flows.
    
    Args:
        symbol: Stock ticker
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with:
        - fund_holdings: List of funds holding the stock
        - total_funds: Number of funds holding
        - largest_positions: Funds where this stock is a top holding
    
    Example:
        >>> data = get_fund_holdings('TSLA')
        >>> print(f"{data['total_funds']} funds hold TSLA")
    """
    result = _make_av_request("MUTUAL_FUND_HOLDINGS", symbol, api_key)
    
    if not result["success"]:
        return result
    
    raw_data = result["data"]
    
    # Parse fund holdings
    funds = []
    holdings_data = raw_data.get("holdings", raw_data.get("data", []))
    
    for fund in holdings_data:
        try:
            portfolio_weight = float(fund.get("portfolio_percent", 0))
            
            funds.append({
                "fund_name": fund.get("fund", fund.get("name", "Unknown")),
                "fund_ticker": fund.get("ticker", ""),
                "shares": int(fund.get("shares", 0)),
                "market_value_usd": float(fund.get("value", 0)),
                "portfolio_weight_pct": portfolio_weight,
                "change_shares": int(fund.get("change", 0)),
                "report_date": fund.get("date", "")
            })
        except (ValueError, TypeError):
            continue
    
    # Find largest positions (funds where this stock is >2% of portfolio)
    largest_positions = [f for f in funds if f["portfolio_weight_pct"] > 2.0]
    largest_positions.sort(key=lambda x: x["portfolio_weight_pct"], reverse=True)
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "fund_holdings": funds[:30],  # Top 30 funds
        "total_funds": len(funds),
        "largest_positions": largest_positions[:10],
        "total_fund_shares": sum(f["shares"] for f in funds),
        "timestamp": datetime.now().isoformat()
    }


def get_insider_transactions(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get recent insider buy/sell transactions
    
    Tracks purchases and sales by company executives, directors, and 10% owners.
    Insider buying can signal confidence; selling may indicate concerns (or just diversification).
    
    Args:
        symbol: Stock ticker
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with:
        - transactions: List of recent insider trades
        - buy_sell_ratio: Ratio of buying to selling activity
        - net_insider_shares: Net change in insider shares (buys - sells)
        - signal: 'bullish', 'bearish', or 'neutral'
    
    Example:
        >>> data = get_insider_transactions('NVDA')
        >>> print(data['signal'])
        'bullish'
    """
    result = _make_av_request("INSIDER_TRANSACTIONS", symbol, api_key)
    
    if not result["success"]:
        return result
    
    raw_data = result["data"]
    
    # Parse insider transactions
    transactions = []
    trades_data = raw_data.get("transactions", raw_data.get("data", []))
    
    total_buys = 0
    total_sells = 0
    buy_shares = 0
    sell_shares = 0
    
    for trade in trades_data:
        try:
            transaction_type = trade.get("transaction_type", trade.get("type", "")).upper()
            shares = int(trade.get("shares", 0))
            
            is_buy = "BUY" in transaction_type or "PURCHASE" in transaction_type
            
            transactions.append({
                "insider_name": trade.get("insider", trade.get("name", "Unknown")),
                "position": trade.get("position", trade.get("title", "")),
                "transaction_type": transaction_type,
                "shares": shares,
                "price_per_share": float(trade.get("price", 0)),
                "total_value_usd": float(trade.get("value", 0)),
                "transaction_date": trade.get("date", ""),
                "filing_date": trade.get("filing_date", "")
            })
            
            if is_buy:
                total_buys += 1
                buy_shares += shares
            else:
                total_sells += 1
                sell_shares += shares
                
        except (ValueError, TypeError):
            continue
    
    # Calculate buy/sell metrics
    buy_sell_ratio = total_buys / total_sells if total_sells > 0 else float('inf')
    net_shares = buy_shares - sell_shares
    
    # Determine signal
    signal = "neutral"
    if buy_sell_ratio > 2 and net_shares > 0:
        signal = "bullish"
    elif buy_sell_ratio < 0.5 and net_shares < 0:
        signal = "bearish"
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "transactions": transactions[:30],  # Most recent 30
        "total_transactions": len(transactions),
        "buy_transactions": total_buys,
        "sell_transactions": total_sells,
        "buy_sell_ratio": round(buy_sell_ratio, 2),
        "net_insider_shares": net_shares,
        "signal": signal,
        "timestamp": datetime.now().isoformat()
    }


def get_ownership_summary(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive ownership summary combining institutional and insider data
    
    Consolidated view of who owns the stock and recent ownership trends.
    
    Args:
        symbol: Stock ticker
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with institutional holders, fund holdings, insider activity
    """
    summary = {
        "success": True,
        "symbol": symbol.upper(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Get all ownership data
    institutional = get_institutional_holders(symbol, api_key)
    insider = get_insider_transactions(symbol, api_key)
    
    if institutional["success"]:
        summary["institutional"] = {
            "ownership_pct": institutional.get("institutional_ownership_pct", 0),
            "top_holder": institutional["top_holders"][0]["holder"] if institutional["top_holders"] else None,
            "holder_count": institutional["holder_count"]
        }
    
    if insider["success"]:
        summary["insider"] = {
            "signal": insider["signal"],
            "buy_sell_ratio": insider["buy_sell_ratio"],
            "net_shares": insider["net_insider_shares"],
            "recent_transactions": insider["total_transactions"]
        }
    
    return summary


if __name__ == "__main__":
    # CLI demonstration
    import sys
    
    test_symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    print("=" * 70)
    print(f"Alpha Vantage Institutional API - {test_symbol}")
    print("=" * 70)
    
    print(f"\n1. Institutional Holders for {test_symbol}:")
    holders = get_institutional_holders(test_symbol)
    print(json.dumps(holders, indent=2))
    
    print(f"\n2. Insider Transactions for {test_symbol}:")
    insider = get_insider_transactions(test_symbol)
    print(json.dumps(insider, indent=2))
    
    print(f"\n3. Ownership Summary for {test_symbol}:")
    summary = get_ownership_summary(test_symbol)
    print(json.dumps(summary, indent=2))
