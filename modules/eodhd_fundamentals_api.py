"""
EODHD Fundamentals API — Company Fundamentals & Financial Data

Data Source: EODHD Financial APIs
Update: Daily
Coverage: Global stocks (US + International)
Free Tier: Yes (demo token works for AAPL.US, 100 req/day with API key)

Provides:
- Company fundamentals (EPS, P/E, revenue, market cap)
- Quarterly earnings history
- Balance sheet data
- Income statement data
- Financial ratios (profitability, leverage, efficiency)

API: https://eodhd.com/financial-apis
Free tier: 100 requests/day, 5 years historical data
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

# API Configuration
BASE_URL = "https://eodhd.com/api/fundamentals"
API_KEY = os.environ.get("EODHD_API_KEY", "demo")

def _make_request(ticker: str) -> Optional[Dict]:
    """
    Make request to EODHD API for fundamentals data.
    
    Args:
        ticker: Stock ticker with exchange (e.g., "AAPL.US")
    
    Returns:
        JSON response as dict or None on error
    """
    url = f"{BASE_URL}/{ticker}"
    params = {
        "api_token": API_KEY,
        "fmt": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {ticker}: {e}")
        return None

def get_fundamentals(ticker: str = "AAPL.US") -> Dict:
    """
    Get company fundamentals overview.
    
    Returns key metrics: EPS, P/E ratio, revenue, market cap, etc.
    
    Args:
        ticker: Stock ticker with exchange (default: "AAPL.US")
    
    Returns:
        Dict with fundamental metrics
    """
    data = _make_request(ticker)
    if not data:
        return {"error": "Failed to fetch fundamentals", "ticker": ticker}
    
    highlights = data.get("Highlights", {})
    general = data.get("General", {})
    
    return {
        "ticker": ticker,
        "company_name": general.get("Name"),
        "sector": general.get("Sector"),
        "industry": general.get("Industry"),
        "market_cap": highlights.get("MarketCapitalization"),
        "eps": highlights.get("EarningsShare"),
        "pe_ratio": highlights.get("PERatio"),
        "dividend_yield": highlights.get("DividendYield"),
        "book_value": highlights.get("BookValue"),
        "profit_margin": highlights.get("ProfitMargin"),
        "updated": highlights.get("UpdatedAt"),
        "timestamp": datetime.now().isoformat()
    }

def get_earnings(ticker: str = "AAPL.US") -> Dict:
    """
    Get quarterly earnings history.
    
    Returns historical earnings data with EPS, revenue, surprises.
    
    Args:
        ticker: Stock ticker with exchange (default: "AAPL.US")
    
    Returns:
        Dict with earnings history by quarter
    """
    data = _make_request(ticker)
    if not data:
        return {"error": "Failed to fetch earnings", "ticker": ticker}
    
    earnings = data.get("Earnings", {})
    history = earnings.get("History", {})
    
    # Convert history dict to list of quarters
    quarterly_data = []
    for date, metrics in history.items():
        quarterly_data.append({
            "date": date,
            "eps_actual": metrics.get("epsActual"),
            "eps_estimate": metrics.get("epsEstimate"),
            "revenue_actual": metrics.get("revenueActual"),
            "revenue_estimate": metrics.get("revenueEstimate"),
            "eps_difference": metrics.get("epsDifference"),
            "surprise_percent": metrics.get("surprisePercent")
        })
    
    # Sort by date descending
    quarterly_data.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "ticker": ticker,
        "trend": earnings.get("Trend"),
        "annual": earnings.get("Annual"),
        "quarterly": quarterly_data[:8],  # Last 8 quarters
        "count": len(quarterly_data),
        "timestamp": datetime.now().isoformat()
    }

def get_balance_sheet(ticker: str = "AAPL.US") -> Dict:
    """
    Get balance sheet data.
    
    Returns assets, liabilities, equity breakdown.
    
    Args:
        ticker: Stock ticker with exchange (default: "AAPL.US")
    
    Returns:
        Dict with balance sheet metrics
    """
    data = _make_request(ticker)
    if not data:
        return {"error": "Failed to fetch balance sheet", "ticker": ticker}
    
    financials = data.get("Financials", {})
    balance_sheet = financials.get("Balance_Sheet", {})
    
    # Get most recent quarter/year
    if not balance_sheet or not isinstance(balance_sheet, dict):
        return {"error": "No balance sheet data available", "ticker": ticker}
    
    latest_date = max(balance_sheet.keys()) if balance_sheet else None
    latest = balance_sheet.get(latest_date, {}) if latest_date else {}
    
    return {
        "ticker": ticker,
        "date": latest_date,
        "total_assets": latest.get("totalAssets"),
        "total_liabilities": latest.get("totalLiab"),
        "total_equity": latest.get("totalStockholderEquity"),
        "current_assets": latest.get("totalCurrentAssets"),
        "current_liabilities": latest.get("totalCurrentLiabilities"),
        "long_term_debt": latest.get("longTermDebt"),
        "cash": latest.get("cash"),
        "inventory": latest.get("inventory"),
        "timestamp": datetime.now().isoformat()
    }

def get_income_statement(ticker: str = "AAPL.US") -> Dict:
    """
    Get income statement data.
    
    Returns revenue, expenses, net income breakdown.
    
    Args:
        ticker: Stock ticker with exchange (default: "AAPL.US")
    
    Returns:
        Dict with income statement metrics
    """
    data = _make_request(ticker)
    if not data:
        return {"error": "Failed to fetch income statement", "ticker": ticker}
    
    financials = data.get("Financials", {})
    income_statement = financials.get("Income_Statement", {})
    
    # Get most recent period
    if not income_statement or not isinstance(income_statement, dict):
        return {"error": "No income statement data available", "ticker": ticker}
    
    latest_date = max(income_statement.keys()) if income_statement else None
    latest = income_statement.get(latest_date, {}) if latest_date else {}
    
    return {
        "ticker": ticker,
        "date": latest_date,
        "total_revenue": latest.get("totalRevenue"),
        "gross_profit": latest.get("grossProfit"),
        "operating_income": latest.get("operatingIncome"),
        "net_income": latest.get("netIncome"),
        "ebitda": latest.get("ebitda"),
        "cost_of_revenue": latest.get("costOfRevenue"),
        "research_development": latest.get("researchDevelopment"),
        "operating_expenses": latest.get("operatingExpense"),
        "timestamp": datetime.now().isoformat()
    }

def get_financial_ratios(ticker: str = "AAPL.US") -> Dict:
    """
    Get financial ratios and metrics.
    
    Returns profitability, leverage, efficiency ratios.
    
    Args:
        ticker: Stock ticker with exchange (default: "AAPL.US")
    
    Returns:
        Dict with financial ratios
    """
    data = _make_request(ticker)
    if not data:
        return {"error": "Failed to fetch financial ratios", "ticker": ticker}
    
    valuation = data.get("Valuation", {})
    technicals = data.get("Technicals", {})
    highlights = data.get("Highlights", {})
    
    return {
        "ticker": ticker,
        # Valuation ratios
        "trailing_pe": valuation.get("TrailingPE"),
        "forward_pe": valuation.get("ForwardPE"),
        "price_to_sales": valuation.get("PriceSalesTTM"),
        "price_to_book": valuation.get("PriceBookMRQ"),
        "enterprise_value": valuation.get("EnterpriseValue"),
        "ev_to_revenue": valuation.get("EnterpriseValueRevenue"),
        "ev_to_ebitda": valuation.get("EnterpriseValueEbitda"),
        # Profitability
        "profit_margin": highlights.get("ProfitMargin"),
        "operating_margin": highlights.get("OperatingMarginTTM"),
        "return_on_assets": highlights.get("ReturnOnAssetsTTM"),
        "return_on_equity": highlights.get("ReturnOnEquityTTM"),
        # Technical
        "beta": technicals.get("Beta"),
        "52week_high": technicals.get("52WeekHigh"),
        "52week_low": technicals.get("52WeekLow"),
        "50day_ma": technicals.get("50DayMA"),
        "200day_ma": technicals.get("200DayMA"),
        "timestamp": datetime.now().isoformat()
    }

def get_latest() -> Dict:
    """
    Get summary demonstrating module capabilities.
    
    Returns overview with all data types for AAPL.US (demo ticker).
    
    Returns:
        Dict with sample of all available data types
    """
    ticker = "AAPL.US"
    
    return {
        "module": "eodhd_fundamentals_api",
        "status": "active",
        "api_key_set": API_KEY != "demo",
        "sample_ticker": ticker,
        "capabilities": {
            "fundamentals": "Company overview with key metrics",
            "earnings": "Quarterly earnings history with surprises",
            "balance_sheet": "Assets, liabilities, equity breakdown",
            "income_statement": "Revenue, expenses, net income",
            "financial_ratios": "Valuation, profitability, efficiency ratios"
        },
        "sample_data": {
            "fundamentals": get_fundamentals(ticker),
            "latest_earnings": get_earnings(ticker).get("quarterly", [{}])[0] if get_earnings(ticker).get("quarterly") else {},
            "ratios_summary": {
                "pe_ratio": get_financial_ratios(ticker).get("trailing_pe"),
                "profit_margin": get_financial_ratios(ticker).get("profit_margin"),
                "beta": get_financial_ratios(ticker).get("beta")
            }
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Quick test
    result = get_latest()
    print(json.dumps(result, indent=2))
