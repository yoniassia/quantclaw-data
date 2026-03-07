#!/usr/bin/env python3
"""
Alpha Vantage Fundamentals API — Company Financials Module

Fetch company fundamentals including income statements, balance sheets, 
cash flows, earnings, and company overviews for global equities.

Source: https://www.alphavantage.co/documentation/
Category: Earnings & Fundamentals
Free tier: True (500 calls/day, 5 calls/min with free API key)
Update frequency: Daily for updates, quarterly for earnings releases
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# Rate limiting: 5 calls per minute, 500 per day on free tier
RATE_LIMIT_MSG = "Alpha Vantage rate limit: 5 calls/min, 500 calls/day on free tier"


def _make_request(function: str, symbol: str, **kwargs) -> Dict:
    """
    Internal helper to make Alpha Vantage API requests.
    
    Args:
        function: Alpha Vantage API function name
        symbol: Stock ticker symbol
        **kwargs: Additional query parameters
        
    Returns:
        Dict: Parsed JSON response
        
    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On API errors or invalid responses
    """
    params = {
        "function": function,
        "symbol": symbol.upper(),
        "apikey": ALPHA_VANTAGE_API_KEY,
        **kwargs
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        
        if "Note" in data:
            raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
            
        if "Information" in data:
            raise ValueError(f"Alpha Vantage info: {data['Information']}")
        
        return data
        
    except requests.exceptions.Timeout:
        raise ValueError(f"Request timeout for {symbol}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed for {symbol}: {str(e)}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON response for {symbol}")


def get_company_overview(symbol: str) -> Dict:
    """
    Get company fundamentals snapshot including sector, market cap, PE ratio,
    dividend yield, profit margin, and key financial metrics.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        
    Returns:
        Dict: Company overview with fundamental metrics
        
    Example:
        >>> overview = get_company_overview('AAPL')
        >>> print(overview['MarketCapitalization'])
        >>> print(overview['PERatio'])
    """
    data = _make_request("OVERVIEW", symbol)
    
    # Return empty dict if no data
    if not data or "Symbol" not in data:
        return {"error": f"No overview data found for {symbol}"}
    
    return data


def get_income_statement(symbol: str, annual: bool = True) -> Union[Dict, List[Dict]]:
    """
    Get income statement data (revenue, expenses, net income, EPS).
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        annual: If True, return annual reports; if False, return quarterly reports
        
    Returns:
        List[Dict]: List of income statement reports, most recent first
        
    Example:
        >>> annual_income = get_income_statement('AAPL', annual=True)
        >>> quarterly_income = get_income_statement('AAPL', annual=False)
        >>> latest = annual_income[0]
        >>> print(latest['totalRevenue'])
    """
    data = _make_request("INCOME_STATEMENT", symbol)
    
    if not data:
        return {"error": f"No income statement data found for {symbol}"}
    
    # Return appropriate period
    if annual:
        return data.get("annualReports", [])
    else:
        return data.get("quarterlyReports", [])


def get_balance_sheet(symbol: str, annual: bool = True) -> Union[Dict, List[Dict]]:
    """
    Get balance sheet data (assets, liabilities, equity, debt).
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        annual: If True, return annual reports; if False, return quarterly reports
        
    Returns:
        List[Dict]: List of balance sheet reports, most recent first
        
    Example:
        >>> annual_balance = get_balance_sheet('AAPL', annual=True)
        >>> latest = annual_balance[0]
        >>> print(latest['totalAssets'])
        >>> print(latest['totalLiabilities'])
    """
    data = _make_request("BALANCE_SHEET", symbol)
    
    if not data:
        return {"error": f"No balance sheet data found for {symbol}"}
    
    # Return appropriate period
    if annual:
        return data.get("annualReports", [])
    else:
        return data.get("quarterlyReports", [])


def get_cash_flow(symbol: str, annual: bool = True) -> Union[Dict, List[Dict]]:
    """
    Get cash flow statement (operating, investing, financing cash flows).
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        annual: If True, return annual reports; if False, return quarterly reports
        
    Returns:
        List[Dict]: List of cash flow reports, most recent first
        
    Example:
        >>> annual_cashflow = get_cash_flow('AAPL', annual=True)
        >>> latest = annual_cashflow[0]
        >>> print(latest['operatingCashflow'])
        >>> print(latest['capitalExpenditures'])
    """
    data = _make_request("CASH_FLOW", symbol)
    
    if not data:
        return {"error": f"No cash flow data found for {symbol}"}
    
    # Return appropriate period
    if annual:
        return data.get("annualReports", [])
    else:
        return data.get("quarterlyReports", [])


def get_earnings(symbol: str) -> Dict:
    """
    Get quarterly and annual earnings data including EPS.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        
    Returns:
        Dict: Earnings data with 'quarterlyEarnings' and 'annualEarnings' keys
        
    Example:
        >>> earnings = get_earnings('AAPL')
        >>> quarterly = earnings.get('quarterlyEarnings', [])
        >>> annual = earnings.get('annualEarnings', [])
        >>> print(quarterly[0]['reportedEPS'])
    """
    data = _make_request("EARNINGS", symbol)
    
    if not data:
        return {"error": f"No earnings data found for {symbol}"}
    
    return {
        "symbol": data.get("symbol", symbol),
        "quarterlyEarnings": data.get("quarterlyEarnings", []),
        "annualEarnings": data.get("annualEarnings", [])
    }


# Module metadata
MODULE_INFO = {
    "module": "alpha_vantage_fundamentals_api",
    "version": "1.0.0",
    "source": "https://www.alphavantage.co/documentation/",
    "category": "Earnings & Fundamentals",
    "free_tier": True,
    "rate_limit": "5 calls/min, 500 calls/day",
    "functions": [
        "get_company_overview",
        "get_income_statement",
        "get_balance_sheet",
        "get_cash_flow",
        "get_earnings"
    ]
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
    print(f"\nAPI Key configured: {'Yes' if ALPHA_VANTAGE_API_KEY != 'demo' else 'No (using demo)'}")
    print(f"Rate limit: {RATE_LIMIT_MSG}")
