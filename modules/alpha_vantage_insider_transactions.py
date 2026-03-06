#!/usr/bin/env python3
"""
Alpha Vantage Insider Transactions
Tracks insider buys, sells, and ownership changes from SEC filings.
Free tier: 5 API calls/min, 500/day

API Docs: https://www.alphavantage.co/documentation/#insider-transactions
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime

ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_api_key() -> str:
    """Get Alpha Vantage API key from environment or use demo key"""
    return os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

def get_insider_transactions(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get insider transaction data for a symbol from Alpha Vantage.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'IBM')
        api_key: Alpha Vantage API key (defaults to env var or 'demo')
    
    Returns:
        dict with 'transactions' list and 'metadata'
    """
    if api_key is None:
        api_key = get_api_key()
    
    try:
        params = {
            "function": "INSIDER_TRANSACTIONS",
            "symbol": symbol.upper(),
            "apikey": api_key
        }
        
        response = requests.get(ALPHAVANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error messages
        if "Error Message" in data:
            return {
                "symbol": symbol,
                "transactions": [],
                "error": data["Error Message"]
            }
        
        if "Note" in data:
            return {
                "symbol": symbol,
                "transactions": [],
                "error": "Rate limit exceeded - Alpha Vantage allows 5 calls/min, 500/day on free tier"
            }
        
        # Parse insider transaction data
        transactions = []
        if "data" in data:
            for tx in data["data"]:
                transactions.append({
                    "date": tx.get("transactionDate", ""),
                    "insider": tx.get("reportingName", ""),
                    "title": tx.get("reportingTitle", ""),
                    "transaction_type": tx.get("transactionType", ""),
                    "shares": int(tx.get("sharesTraded", 0)) if tx.get("sharesTraded") else 0,
                    "price": float(tx.get("transactionPrice", 0)) if tx.get("transactionPrice") else 0,
                    "value": float(tx.get("transactionValue", 0)) if tx.get("transactionValue") else 0,
                    "shares_owned_after": int(tx.get("sharesOwnedFollowing", 0)) if tx.get("sharesOwnedFollowing") else 0
                })
        
        return {
            "symbol": symbol,
            "transactions": transactions,
            "count": len(transactions),
            "retrieved": datetime.now().isoformat()
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "symbol": symbol,
            "transactions": [],
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "transactions": [],
            "error": f"Unexpected error: {str(e)}"
        }

def get_recent_buys(symbol: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
    """
    Get recent insider buys for a symbol.
    
    Args:
        symbol: Stock ticker
        limit: Max transactions to return
        api_key: Alpha Vantage API key
    
    Returns:
        List of insider buy transactions
    """
    data = get_insider_transactions(symbol, api_key)
    
    if "error" in data:
        return []
    
    buys = [
        tx for tx in data.get("transactions", [])
        if "buy" in tx.get("transaction_type", "").lower() or
           "purchase" in tx.get("transaction_type", "").lower()
    ]
    
    # Sort by date descending
    buys.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return buys[:limit]

def get_recent_sells(symbol: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
    """
    Get recent insider sells for a symbol.
    
    Args:
        symbol: Stock ticker
        limit: Max transactions to return
        api_key: Alpha Vantage API key
    
    Returns:
        List of insider sell transactions
    """
    data = get_insider_transactions(symbol, api_key)
    
    if "error" in data:
        return []
    
    sells = [
        tx for tx in data.get("transactions", [])
        if "sale" in tx.get("transaction_type", "").lower() or
           "sell" in tx.get("transaction_type", "").lower()
    ]
    
    # Sort by date descending
    sells.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return sells[:limit]

def get_insider_summary(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get summary statistics of insider trading activity.
    
    Args:
        symbol: Stock ticker
        api_key: Alpha Vantage API key
    
    Returns:
        Summary dict with buy/sell counts and values
    """
    data = get_insider_transactions(symbol, api_key)
    
    if "error" in data:
        return {
            "symbol": symbol,
            "total_transactions": 0,
            "buys": 0,
            "sells": 0,
            "total_buy_value": 0,
            "total_sell_value": 0,
            "error": data["error"]
        }
    
    transactions = data.get("transactions", [])
    
    buys = [tx for tx in transactions if "buy" in tx.get("transaction_type", "").lower() or
            "purchase" in tx.get("transaction_type", "").lower()]
    sells = [tx for tx in transactions if "sale" in tx.get("transaction_type", "").lower() or
             "sell" in tx.get("transaction_type", "").lower()]
    
    total_buy_value = sum(tx.get("value", 0) for tx in buys)
    total_sell_value = sum(tx.get("value", 0) for tx in sells)
    
    return {
        "symbol": symbol,
        "total_transactions": len(transactions),
        "buys": len(buys),
        "sells": len(sells),
        "total_buy_value": total_buy_value,
        "total_sell_value": total_sell_value,
        "net_value": total_buy_value - total_sell_value,
        "buy_sell_ratio": len(buys) / len(sells) if sells else float('inf') if buys else 0
    }

def get_data(symbol: str = "IBM") -> Dict:
    """
    Main entry point - get insider transaction data.
    
    Args:
        symbol: Stock ticker (default: IBM)
    
    Returns:
        Insider transaction data dict
    """
    return get_insider_transactions(symbol)

if __name__ == "__main__":
    # Test with IBM
    import json
    result = get_data("IBM")
    print(json.dumps(result, indent=2))
