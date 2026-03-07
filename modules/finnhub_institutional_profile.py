"""
Finnhub Institutional Profile — Institutional investor holdings and 13F filings.

Aggregates hedge fund and institutional investor position data for quantitative analysis.
Includes AUM, top holdings, portfolio concentration, filing history, and sector allocations.

Source: https://finnhub.io/docs/api/institutional-profile
Update frequency: Quarterly (13F filings)
Category: Insider & Institutional
Free tier: 60 requests/minute with free API key
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://finnhub.io/api/v1"
DEFAULT_KEY = os.environ.get("FINNHUB_API_KEY", "demo")


def get_institutional_holders(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get top institutional holders for a stock.
    
    Returns institutional ownership data including investor names, share counts,
    portfolio weight, and change from previous quarter.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var or 'demo')
        
    Returns:
        dict with institutional holder data
        
    Example:
        >>> holders = get_institutional_holders('AAPL')
        >>> for h in holders.get('data', []):
        ...     print(h['investor'], h['shares'], h['change'])
    """
    token = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol.upper(),
        "token": token
    }
    
    url = f"{API_BASE}/stock/institutional-ownership?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, dict) and data.get("error"):
                return {"error": data.get("error"), "symbol": symbol}
            
            # Finnhub returns {"data": [...], "symbol": "AAPL"}
            holders = data.get("data", [])
            
            return {
                "symbol": symbol.upper(),
                "total_holders": len(holders),
                "data": [
                    {
                        "investor": h.get("name"),
                        "cik": h.get("cik"),
                        "shares": h.get("share"),
                        "value": h.get("value"),
                        "change": h.get("change"),
                        "portfolio_percent": h.get("portfolioPercent"),
                        "filing_date": h.get("filingDate")
                    }
                    for h in holders
                ],
                "raw": data
            }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limit exceeded (60 req/min)", "symbol": symbol}
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_institutional_profile(
    cik: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get profile information for an institutional investor.
    
    Returns investor profile including name, CIK, portfolio summary, and recent activity.
    
    Args:
        cik: Central Index Key (CIK) of the institution
        api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var or 'demo')
        
    Returns:
        dict with institutional investor profile
        
    Example:
        >>> profile = get_institutional_profile('0001067983')  # Berkshire Hathaway
        >>> print(profile.get('name'), profile.get('total_value'))
    """
    token = api_key or DEFAULT_KEY
    
    params = {
        "cik": cik,
        "token": token
    }
    
    url = f"{API_BASE}/stock/institutional-profile?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, dict) and data.get("error"):
                return {"error": data.get("error"), "cik": cik}
            
            return {
                "cik": cik,
                "name": data.get("name"),
                "address": data.get("address"),
                "total_value": data.get("totalValue"),
                "filing_date": data.get("filingDate"),
                "positions_count": data.get("numberOfPositions"),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limit exceeded (60 req/min)", "cik": cik}
        return {"error": f"HTTP {e.code}: {e.reason}", "cik": cik}
    except Exception as e:
        return {"error": str(e), "cik": cik}


def get_fund_holdings(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get mutual fund and ETF holdings for a stock.
    
    Returns list of funds holding the stock with share counts and portfolio weights.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var or 'demo')
        
    Returns:
        dict with fund holdings data
        
    Example:
        >>> funds = get_fund_holdings('AAPL')
        >>> for f in funds.get('data', []):
        ...     print(f['fund_name'], f['shares'])
    """
    token = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol.upper(),
        "token": token
    }
    
    url = f"{API_BASE}/stock/fund-ownership?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, dict) and data.get("error"):
                return {"error": data.get("error"), "symbol": symbol}
            
            holdings = data.get("ownership", [])
            
            return {
                "symbol": symbol.upper(),
                "total_funds": len(holdings),
                "data": [
                    {
                        "fund_name": h.get("name"),
                        "cusip": h.get("cusip"),
                        "shares": h.get("share"),
                        "value": h.get("value"),
                        "change": h.get("change"),
                        "portfolio_percent": h.get("portfolioPercent"),
                        "filing_date": h.get("filingDate")
                    }
                    for h in holdings
                ],
                "raw": data
            }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limit exceeded (60 req/min)", "symbol": symbol}
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_ownership_summary(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get comprehensive ownership breakdown for a stock.
    
    Combines institutional and fund ownership data to provide complete picture
    of major stakeholders, concentration metrics, and recent changes.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var or 'demo')
        
    Returns:
        dict with aggregated ownership summary
        
    Example:
        >>> summary = get_ownership_summary('AAPL')
        >>> print(summary.get('total_institutional_holders'))
        >>> print(summary.get('concentration_top10'))
    """
    # Fetch both institutional and fund data
    inst_data = get_institutional_holders(symbol, api_key)
    fund_data = get_fund_holdings(symbol, api_key)
    
    # Calculate summary metrics
    summary = {
        "symbol": symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "total_institutional_holders": inst_data.get("total_holders", 0),
        "total_fund_holders": fund_data.get("total_funds", 0)
    }
    
    # Calculate concentration (top 10 holders)
    if "data" in inst_data and inst_data["data"]:
        top10_shares = sum(h.get("shares", 0) for h in inst_data["data"][:10])
        total_shares = sum(h.get("shares", 0) for h in inst_data["data"])
        
        summary["concentration_top10"] = (top10_shares / total_shares * 100) if total_shares > 0 else 0
        summary["largest_holder"] = inst_data["data"][0] if inst_data["data"] else None
    
    # Aggregate by sector if available
    summary["institutional_data"] = inst_data
    summary["fund_data"] = fund_data
    
    return summary


def get_insider_transactions(
    symbol: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get insider trading transactions for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var or 'demo')
        
    Returns:
        dict with insider transaction data
        
    Example:
        >>> transactions = get_insider_transactions('AAPL', '2024-01-01', '2024-12-31')
        >>> for txn in transactions.get('data', []):
        ...     print(txn['name'], txn['transaction_type'], txn['shares'])
    """
    token = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol.upper(),
        "token": token
    }
    
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    url = f"{API_BASE}/stock/insider-transactions?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, dict) and data.get("error"):
                return {"error": data.get("error"), "symbol": symbol}
            
            transactions = data.get("data", [])
            
            return {
                "symbol": symbol.upper(),
                "from_date": from_date,
                "to_date": to_date,
                "total_transactions": len(transactions),
                "data": [
                    {
                        "name": t.get("name"),
                        "shares": t.get("share"),
                        "change": t.get("change"),
                        "filing_date": t.get("filingDate"),
                        "transaction_date": t.get("transactionDate"),
                        "transaction_type": t.get("transactionCode"),
                        "transaction_price": t.get("transactionPrice")
                    }
                    for t in transactions
                ],
                "raw": data
            }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limit exceeded (60 req/min)", "symbol": symbol}
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def demo():
    """Demo with sample institutional data (no API key required)."""
    sample_data = {
        "symbol": "AAPL",
        "total_holders": 3,
        "data": [
            {
                "investor": "Vanguard Group Inc",
                "cik": "0000102909",
                "shares": 1285000000,
                "value": 234500000000,
                "change": 12500000,
                "portfolio_percent": 8.5,
                "filing_date": "2024-12-31"
            },
            {
                "investor": "BlackRock Inc",
                "cik": "0001364742",
                "shares": 1045000000,
                "value": 191000000000,
                "change": 8200000,
                "portfolio_percent": 7.2,
                "filing_date": "2024-12-31"
            },
            {
                "investor": "Berkshire Hathaway Inc",
                "cik": "0001067983",
                "shares": 915000000,
                "value": 167000000000,
                "change": -10000000,
                "portfolio_percent": 45.3,
                "filing_date": "2024-12-31"
            }
        ],
        "note": "This is sample data. Provide valid FINNHUB_API_KEY for real data."
    }
    return sample_data


if __name__ == "__main__":
    # Test with demo data
    print(json.dumps(demo(), indent=2))
