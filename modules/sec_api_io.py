"""
SEC-API.io Module

Provides programmatic access to SEC filings including:
- Form 4 insider trading data
- 13F institutional holdings
- Real-time and historical filing data from EDGAR

API: https://sec-api.io/
Free tier: 100 requests per day, no credit card required
"""

import requests
import os
from datetime import datetime, timedelta

# Get API key from environment or use demo key
SEC_API_KEY = os.getenv("SEC_API_IO_KEY", "demo")
BASE_URL = "https://api.sec-api.io"


def get_insider_trades(ticker=None, cik=None, limit=10):
    """
    Get recent Form 4 insider trading filings.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        cik: Company CIK number
        limit: Number of results to return
    
    Returns:
        List of insider trading transactions with details
    """
    try:
        query = {"formType": "4"}
        if ticker:
            query["ticker"] = ticker.upper()
        if cik:
            query["cik"] = cik
        
        params = {
            "token": SEC_API_KEY,
            "query": str(query).replace("'", '"'),
            "from": 0,
            "size": limit,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or "filings" not in data:
            return []
        
        trades = []
        for filing in data.get("filings", []):
            trades.append({
                "ticker": filing.get("ticker", ""),
                "cik": filing.get("cik", ""),
                "company_name": filing.get("companyName", ""),
                "insider_name": filing.get("reportingOwnerName", ""),
                "insider_title": filing.get("reportingOwnerTitle", ""),
                "filing_date": filing.get("filedAt", ""),
                "transaction_date": filing.get("transactionDate", ""),
                "shares": filing.get("sharesTraded", 0),
                "price": filing.get("pricePerShare", 0),
                "transaction_type": filing.get("transactionCode", ""),
                "is_director": filing.get("isDirector", False),
                "is_officer": filing.get("isOfficer", False),
                "accession_number": filing.get("accessionNo", ""),
                "filing_url": filing.get("linkToFilingDetails", "")
            })
        
        return trades
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching insider trades: {e}")
        return []
    except Exception as e:
        print(f"Error processing insider data: {e}")
        return []


def get_13f_holdings(cik=None, limit=10):
    """
    Get recent 13F institutional holdings filings.
    
    Args:
        cik: Institution CIK number
        limit: Number of results to return
    
    Returns:
        List of 13F filings with holdings data
    """
    try:
        query = {"formType": "13F-HR"}
        if cik:
            query["cik"] = cik
        
        params = {
            "token": SEC_API_KEY,
            "query": str(query).replace("'", '"'),
            "from": 0,
            "size": limit,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or "filings" not in data:
            return []
        
        holdings = []
        for filing in data.get("filings", []):
            holdings.append({
                "cik": filing.get("cik", ""),
                "institution_name": filing.get("companyName", ""),
                "filing_date": filing.get("filedAt", ""),
                "report_date": filing.get("periodOfReport", ""),
                "total_value": filing.get("totalValue", 0),
                "entry_count": filing.get("entryCount", 0),
                "accession_number": filing.get("accessionNo", ""),
                "filing_url": filing.get("linkToFilingDetails", "")
            })
        
        return holdings
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching 13F holdings: {e}")
        return []
    except Exception as e:
        print(f"Error processing 13F data: {e}")
        return []


def search_filings(form_type="4", ticker=None, date_from=None, date_to=None, limit=20):
    """
    Search SEC filings with flexible filtering.
    
    Args:
        form_type: Filing form type (4, 13F-HR, 10-K, etc.)
        ticker: Stock ticker symbol
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        limit: Number of results
    
    Returns:
        List of matching SEC filings
    """
    try:
        query = {"formType": form_type}
        
        if ticker:
            query["ticker"] = ticker.upper()
        
        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from
            if date_to:
                date_range["lte"] = date_to
            query["filedAt"] = date_range
        
        params = {
            "token": SEC_API_KEY,
            "query": str(query).replace("'", '"'),
            "from": 0,
            "size": limit
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("filings", [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching filings: {e}")
        return []
    except Exception as e:
        print(f"Error processing search: {e}")
        return []


def get_insider_summary(ticker):
    """
    Get summary of recent insider trading activity for a ticker.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dict with aggregated insider trading metrics
    """
    try:
        trades = get_insider_trades(ticker=ticker, limit=50)
        
        if not trades:
            return {
                "ticker": ticker,
                "total_trades": 0,
                "buys": 0,
                "sells": 0,
                "net_shares": 0,
                "total_value": 0
            }
        
        buys = [t for t in trades if t.get("transaction_type") in ["P", "M"]]
        sells = [t for t in trades if t.get("transaction_type") in ["S"]]
        
        buy_shares = sum(t.get("shares", 0) for t in buys)
        sell_shares = sum(t.get("shares", 0) for t in sells)
        
        buy_value = sum(t.get("shares", 0) * t.get("price", 0) for t in buys)
        sell_value = sum(t.get("shares", 0) * t.get("price", 0) for t in sells)
        
        return {
            "ticker": ticker,
            "total_trades": len(trades),
            "buys": len(buys),
            "sells": len(sells),
            "buy_shares": buy_shares,
            "sell_shares": sell_shares,
            "net_shares": buy_shares - sell_shares,
            "buy_value": buy_value,
            "sell_value": sell_value,
            "net_value": buy_value - sell_value,
            "latest_trades": trades[:5]
        }
        
    except Exception as e:
        print(f"Error creating insider summary: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the module
    print("Testing SEC-API.io module...")
    
    # Test 1: Get insider trades for AAPL
    print("\n1. Recent AAPL insider trades:")
    trades = get_insider_trades(ticker="AAPL", limit=3)
    for trade in trades[:3]:
        print(f"  {trade.get('insider_name')} - {trade.get('transaction_type')} "
              f"{trade.get('shares')} shares @ ${trade.get('price')}")
    
    # Test 2: Get insider summary
    print("\n2. AAPL insider summary:")
    summary = get_insider_summary("AAPL")
    print(f"  Total trades: {summary.get('total_trades')}")
    print(f"  Buys: {summary.get('buys')}, Sells: {summary.get('sells')}")
    print(f"  Net shares: {summary.get('net_shares'):,}")
    
    # Test 3: Get 13F holdings
    print("\n3. Recent 13F filings:")
    holdings = get_13f_holdings(limit=3)
    for h in holdings[:3]:
        print(f"  {h.get('institution_name')} - ${h.get('total_value'):,}")
