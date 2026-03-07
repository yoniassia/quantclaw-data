"""
Financial Modeling Prep (FMP) Income Statement API

Income statement and financial fundamentals from FMP. Free tier provides 250 calls/day
for income statements, financial ratios, key metrics, and growth analysis.

Source: https://financialmodelingprep.com/api/v3/
Update frequency: Quarterly (with filings), daily updates for estimates
Category: Earnings & Fundamentals
Free tier: 250 calls/day
"""

import json
import os
import requests
from datetime import datetime
from typing import Any, Optional, List


API_BASE = "https://financialmodelingprep.com/api/v3"


def _get_api_key() -> Optional[str]:
    """Get FMP API key from environment."""
    return os.environ.get("FMP_API_KEY")


def _make_request(endpoint: str, params: dict = None) -> dict[str, Any]:
    """
    Make authenticated request to FMP API.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters
        
    Returns:
        dict with API response or error
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "FMP_API_KEY not set. Get free key at https://site.financialmodelingprep.com/developer/docs",
            "free_tier": "250 calls/day"
        }
    
    params = params or {}
    params["apikey"] = api_key
    
    url = f"{API_BASE}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # FMP returns error messages as dict with "Error Message" key
        if isinstance(data, dict) and "Error Message" in data:
            return {"error": data["Error Message"]}
            
        return data if data else {"error": "No data returned"}
        
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}


def get_income_statement(
    symbol: str,
    period: str = "annual",
    limit: int = 10
) -> dict[str, Any]:
    """
    Get income statements for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        period: 'annual' or 'quarter'
        limit: Number of periods to return (max 120)
        
    Returns:
        dict with income statement data including revenue, expenses, net income
        
    Example:
        >>> stmt = get_income_statement('AAPL', period='annual', limit=5)
        >>> if 'error' not in stmt:
        ...     for item in stmt.get('data', []):
        ...         print(f"{item['date']}: Revenue ${item['revenue']:,}")
    """
    if period not in ["annual", "quarter"]:
        return {"error": "period must be 'annual' or 'quarter'"}
    
    limit = min(max(1, limit), 120)
    endpoint = f"income-statement/{symbol.upper()}"
    params = {"period": period, "limit": limit}
    
    result = _make_request(endpoint, params)
    
    if isinstance(result, dict) and "error" in result:
        return result
    
    # Structure the response
    return {
        "symbol": symbol.upper(),
        "period": period,
        "count": len(result) if isinstance(result, list) else 0,
        "data": result,
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_income_growth(
    symbol: str,
    period: str = "annual",
    limit: int = 10
) -> dict[str, Any]:
    """
    Get income statement growth rates (YoY or QoQ).
    
    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarter'
        limit: Number of periods to return
        
    Returns:
        dict with growth rates for revenue, gross profit, operating income, etc.
        
    Example:
        >>> growth = get_income_growth('AAPL', period='annual', limit=5)
        >>> if 'error' not in growth:
        ...     for item in growth.get('data', []):
        ...         print(f"{item['date']}: Revenue growth {item.get('revenueGrowth', 0):.2%}")
    """
    if period not in ["annual", "quarter"]:
        return {"error": "period must be 'annual' or 'quarter'"}
    
    limit = min(max(1, limit), 120)
    endpoint = f"income-statement-growth/{symbol.upper()}"
    params = {"period": period, "limit": limit}
    
    result = _make_request(endpoint, params)
    
    if isinstance(result, dict) and "error" in result:
        return result
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "count": len(result) if isinstance(result, list) else 0,
        "data": result,
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_financial_ratios(
    symbol: str,
    period: str = "annual",
    limit: int = 10
) -> dict[str, Any]:
    """
    Get financial ratios including liquidity, profitability, and leverage ratios.
    
    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarter'
        limit: Number of periods to return
        
    Returns:
        dict with financial ratios (current ratio, ROE, debt-to-equity, etc.)
        
    Example:
        >>> ratios = get_financial_ratios('AAPL', limit=3)
        >>> if 'error' not in ratios:
        ...     for item in ratios.get('data', []):
        ...         print(f"{item['date']}: ROE {item.get('returnOnEquity', 0):.2%}")
    """
    if period not in ["annual", "quarter"]:
        return {"error": "period must be 'annual' or 'quarter'"}
    
    limit = min(max(1, limit), 120)
    endpoint = f"ratios/{symbol.upper()}"
    params = {"period": period, "limit": limit}
    
    result = _make_request(endpoint, params)
    
    if isinstance(result, dict) and "error" in result:
        return result
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "count": len(result) if isinstance(result, list) else 0,
        "data": result,
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_key_metrics(
    symbol: str,
    period: str = "annual",
    limit: int = 10
) -> dict[str, Any]:
    """
    Get key valuation metrics (PE, EV/EBITDA, market cap, etc.).
    
    Args:
        symbol: Stock ticker symbol
        period: 'annual' or 'quarter'
        limit: Number of periods to return
        
    Returns:
        dict with valuation metrics
        
    Example:
        >>> metrics = get_key_metrics('TSLA', limit=5)
        >>> if 'error' not in metrics:
        ...     for item in metrics.get('data', []):
        ...         pe = item.get('peRatio', 0)
        ...         print(f"{item['date']}: P/E {pe:.2f}")
    """
    if period not in ["annual", "quarter"]:
        return {"error": "period must be 'annual' or 'quarter'"}
    
    limit = min(max(1, limit), 120)
    endpoint = f"key-metrics/{symbol.upper()}"
    params = {"period": period, "limit": limit}
    
    result = _make_request(endpoint, params)
    
    if isinstance(result, dict) and "error" in result:
        return result
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "count": len(result) if isinstance(result, list) else 0,
        "data": result,
        "fetched_at": datetime.utcnow().isoformat()
    }


def compare_income(
    symbols_list: List[str],
    period: str = "annual",
    limit: int = 1
) -> dict[str, Any]:
    """
    Compare income statements across multiple tickers.
    
    Args:
        symbols_list: List of stock ticker symbols
        period: 'annual' or 'quarter'
        limit: Number of periods per symbol (typically 1 for comparison)
        
    Returns:
        dict with comparative income data for all symbols
        
    Example:
        >>> comp = compare_income(['AAPL', 'MSFT', 'GOOGL'], limit=1)
        >>> if 'error' not in comp:
        ...     for sym, data in comp.get('comparison', {}).items():
        ...         latest = data.get('data', [{}])[0]
        ...         print(f"{sym}: ${latest.get('revenue', 0):,}")
    """
    if not symbols_list or len(symbols_list) == 0:
        return {"error": "symbols_list cannot be empty"}
    
    if period not in ["annual", "quarter"]:
        return {"error": "period must be 'annual' or 'quarter'"}
    
    comparison = {}
    errors = {}
    
    for symbol in symbols_list:
        result = get_income_statement(symbol, period=period, limit=limit)
        
        if "error" in result:
            errors[symbol.upper()] = result["error"]
        else:
            comparison[symbol.upper()] = result
    
    response = {
        "symbols": [s.upper() for s in symbols_list],
        "period": period,
        "comparison": comparison,
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    if errors:
        response["errors"] = errors
    
    return response


# Demo function for testing without API key
def demo():
    """Demo with sample data structure (no API key required)."""
    return {
        "module": "financial_modeling_prep_fmp_income_statement_api",
        "functions": [
            "get_income_statement",
            "get_income_growth",
            "get_financial_ratios",
            "get_key_metrics",
            "compare_income"
        ],
        "sample_usage": {
            "income_statement": "get_income_statement('AAPL', period='annual', limit=5)",
            "growth": "get_income_growth('AAPL', period='annual', limit=5)",
            "ratios": "get_financial_ratios('AAPL', limit=3)",
            "metrics": "get_key_metrics('TSLA', limit=5)",
            "compare": "compare_income(['AAPL', 'MSFT', 'GOOGL'])"
        },
        "note": "Set FMP_API_KEY environment variable for real data. Free tier: 250 calls/day"
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
