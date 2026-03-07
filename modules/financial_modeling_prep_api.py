#!/usr/bin/env python3
"""
Financial Modeling Prep API — Company Fundamentals & Earnings Module

Comprehensive company financial data including earnings calendars, income statements,
balance sheets, cash flow statements, financial ratios, DCF valuations, and real-time quotes.
Supports US and international stocks with quarterly and annual reporting periods.

Source: https://site.financialmodelingprep.com/developer/docs/
Category: Earnings & Fundamentals
Free tier: True (250 calls/day with "demo" key, unlimited with FMP_API_KEY)
Author: QuantClaw Data NightBuilder
Phase: 106
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

# FMP API Configuration
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
FMP_API_KEY = os.environ.get("FMP_API_KEY", "demo")

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to FMP API with error handling.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters (apikey auto-added)
        
    Returns:
        Dict with parsed JSON response or error structure
    """
    if params is None:
        params = {}
    
    params['apikey'] = FMP_API_KEY
    url = f"{FMP_BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # FMP returns error as dict with "Error Message" key
        if isinstance(data, dict) and "Error Message" in data:
            return {"error": data["Error Message"], "success": False}
        
        return {"data": data, "success": True}
        
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "success": False}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "success": False}


def get_earnings_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
    """
    Get upcoming earnings announcements for all companies.
    
    Args:
        from_date: Start date in YYYY-MM-DD format (default: today)
        to_date: End date in YYYY-MM-DD format (default: 3 months ahead)
        
    Returns:
        Dict with list of earnings events including ticker, date, EPS estimates
        
    Example:
        >>> get_earnings_calendar("2026-03-01", "2026-03-31")
        {'data': [{'symbol': 'AAPL', 'date': '2026-03-15', 'eps': 1.52, ...}], 'success': True}
    """
    if from_date is None:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if to_date is None:
        to_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    params = {"from": from_date, "to": to_date}
    return _make_request("/earning_calendar", params)


def get_income_statement(ticker: str = "AAPL", period: str = "annual", limit: int = 5) -> Dict:
    """
    Get company income statements (P&L) for specified period.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter" 
        limit: Number of periods to return (default: 5)
        
    Returns:
        Dict with list of income statements including revenue, expenses, net income
        
    Example:
        >>> get_income_statement("AAPL", "annual", 3)
        {'data': [{'date': '2025-09-30', 'revenue': 383285000000, ...}], 'success': True}
    """
    params = {"period": period, "limit": limit}
    return _make_request(f"/income-statement/{ticker}", params)


def get_balance_sheet(ticker: str = "AAPL", period: str = "annual", limit: int = 5) -> Dict:
    """
    Get company balance sheet statements for specified period.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        limit: Number of periods to return (default: 5)
        
    Returns:
        Dict with list of balance sheets including assets, liabilities, equity
        
    Example:
        >>> get_balance_sheet("MSFT", "quarter", 4)
        {'data': [{'date': '2025-12-31', 'totalAssets': 512345000000, ...}], 'success': True}
    """
    params = {"period": period, "limit": limit}
    return _make_request(f"/balance-sheet-statement/{ticker}", params)


def get_cash_flow(ticker: str = "AAPL", period: str = "annual", limit: int = 5) -> Dict:
    """
    Get company cash flow statements for specified period.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        limit: Number of periods to return (default: 5)
        
    Returns:
        Dict with list of cash flow statements including operating, investing, financing flows
        
    Example:
        >>> get_cash_flow("GOOGL", "annual", 3)
        {'data': [{'date': '2025-12-31', 'operatingCashFlow': 87234000000, ...}], 'success': True}
    """
    params = {"period": period, "limit": limit}
    return _make_request(f"/cash-flow-statement/{ticker}", params)


def get_financial_ratios(ticker: str = "AAPL", period: str = "annual", limit: int = 5) -> Dict:
    """
    Get key financial ratios for company analysis.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        limit: Number of periods to return (default: 5)
        
    Returns:
        Dict with list of financial ratios including P/E, ROE, debt ratios, margins
        
    Example:
        >>> get_financial_ratios("TSLA", "annual", 3)
        {'data': [{'date': '2025-12-31', 'peRatio': 45.2, 'roe': 0.18, ...}], 'success': True}
    """
    params = {"period": period, "limit": limit}
    return _make_request(f"/ratios/{ticker}", params)


def get_dcf_value(ticker: str = "AAPL") -> Dict:
    """
    Get discounted cash flow (DCF) fair value estimate for a stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with DCF valuation including intrinsic value, current price, over/undervalued %
        
    Example:
        >>> get_dcf_value("AAPL")
        {'data': [{'symbol': 'AAPL', 'dcf': 185.23, 'stock_price': 172.45, ...}], 'success': True}
    """
    return _make_request(f"/discounted-cash-flow/{ticker}")


def get_stock_quote(ticker: str = "AAPL") -> Dict:
    """
    Get real-time stock quote with price, volume, and daily change.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with current quote including price, volume, day high/low, market cap
        
    Example:
        >>> get_stock_quote("AAPL")
        {'data': [{'symbol': 'AAPL', 'price': 172.45, 'change': 2.35, ...}], 'success': True}
    """
    return _make_request(f"/quote/{ticker}")


def get_earnings_surprises(ticker: str = "AAPL") -> Dict:
    """
    Get historical earnings surprises (actual vs expected EPS).
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with list of earnings surprises including actual, estimated EPS, surprise %
        
    Example:
        >>> get_earnings_surprises("NVDA")
        {'data': [{'date': '2025-11-20', 'actual': 0.68, 'estimated': 0.62, ...}], 'success': True}
    """
    return _make_request(f"/earnings-surprises/{ticker}")


def search_company(query: str = "apple") -> Dict:
    """
    Search for companies by name or ticker symbol.
    
    Args:
        query: Company name or ticker to search
        
    Returns:
        Dict with list of matching companies including symbol, name, exchange
        
    Example:
        >>> search_company("microsoft")
        {'data': [{'symbol': 'MSFT', 'name': 'Microsoft Corporation', ...}], 'success': True}
    """
    params = {"query": query, "limit": 10}
    return _make_request("/search", params)


# ========== MODULE METADATA ==========

MODULE_INFO = {
    "name": "financial_modeling_prep_api",
    "functions": [
        "get_earnings_calendar",
        "get_income_statement", 
        "get_balance_sheet",
        "get_cash_flow",
        "get_financial_ratios",
        "get_dcf_value",
        "get_stock_quote",
        "get_earnings_surprises",
        "search_company"
    ],
    "api_key_required": False,  # Works with "demo" key
    "free_tier": "250 calls/day",
    "source": "https://site.financialmodelingprep.com/developer/docs/"
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
