"""
Financial Modeling Prep Insider API — Insider trading data from SEC filings.

FMP offers API access to insider trading data pulled from SEC forms, including 
buys, sells, and ownership changes. Includes 13F institutional filings and hedge 
fund positions. Free tier: 250 requests/day with limited historical data access.

Source: https://financialmodelingprep.com/api/v4/insider-trading
Update frequency: Daily updates from SEC filings
Category: Insider & Institutional
Free tier: 250 calls/day
"""

import json
import os
import urllib.request
import urllib.parse
from typing import Any, Optional


API_BASE = "https://financialmodelingprep.com/api"
# API key from environment or None
DEFAULT_KEY = os.environ.get("FMP_API_KEY")


def get_insider_trades(
    symbol: str,
    limit: int = 100,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get recent insider trades for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        limit: Maximum number of trades to return (default 100)
        api_key: FMP API key (falls back to FMP_API_KEY env var)
        
    Returns:
        dict with insider trades data including transaction type, shares, price
        
    Example:
        >>> trades = get_insider_trades('AAPL', limit=10)
        >>> for trade in trades.get('data', []):
        ...     print(trade['filingDate'], trade['transactionType'], trade['securitiesTransacted'])
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {
            "error": "API key required. Set FMP_API_KEY env var or get free key at https://financialmodelingprep.com"
        }
    
    endpoint = f"{API_BASE}/v4/insider-trading"
    params = {
        "symbol": symbol.upper(),
        "limit": limit,
        "apikey": key
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            # FMP returns array directly
            if isinstance(data, list):
                return {
                    "symbol": symbol.upper(),
                    "count": len(data),
                    "data": data,
                    "source": "fmp_insider_api"
                }
            elif isinstance(data, dict) and "Error Message" in data:
                return {"error": data["Error Message"]}
            else:
                return {
                    "symbol": symbol.upper(),
                    "data": data if isinstance(data, list) else [data],
                    "source": "fmp_insider_api"
                }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def get_insider_roster(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get list of insiders (officers and directors) for a company.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        api_key: FMP API key (falls back to FMP_API_KEY env var)
        
    Returns:
        dict with list of company insiders and their positions
        
    Example:
        >>> roster = get_insider_roster('MSFT')
        >>> for insider in roster.get('data', []):
        ...     print(insider['name'], insider['position'])
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    # Note: API documentation shows /v3/insider-roaster (yes, with typo)
    endpoint = f"{API_BASE}/v3/insider-roaster"
    params = {
        "symbol": symbol.upper(),
        "apikey": key
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, list):
                return {
                    "symbol": symbol.upper(),
                    "count": len(data),
                    "data": data,
                    "source": "fmp_insider_api"
                }
            elif isinstance(data, dict) and "Error Message" in data:
                return {"error": data["Error Message"]}
            else:
                return {
                    "symbol": symbol.upper(),
                    "data": data if isinstance(data, list) else [data],
                    "source": "fmp_insider_api"
                }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def get_insider_statistics(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get insider trading statistics summary (buy/sell aggregates).
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        api_key: FMP API key (falls back to FMP_API_KEY env var)
        
    Returns:
        dict with insider buy/sell statistics and trends
        
    Example:
        >>> stats = get_insider_statistics('AAPL')
        >>> print(f"Total buys: {stats.get('total_buys', 0)}")
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    endpoint = f"{API_BASE}/v4/insider-trading-transaction-type"
    params = {
        "symbol": symbol.upper(),
        "apikey": key
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, list):
                # Aggregate statistics
                buys = sum(1 for item in data if item.get('acquistionOrDisposition') == 'A')
                sells = sum(1 for item in data if item.get('acquistionOrDisposition') == 'D')
                
                return {
                    "symbol": symbol.upper(),
                    "total_transactions": len(data),
                    "total_buys": buys,
                    "total_sells": sells,
                    "buy_sell_ratio": round(buys / sells, 2) if sells > 0 else float('inf'),
                    "data": data,
                    "source": "fmp_insider_api"
                }
            elif isinstance(data, dict) and "Error Message" in data:
                return {"error": data["Error Message"]}
            else:
                return {
                    "symbol": symbol.upper(),
                    "data": data,
                    "source": "fmp_insider_api"
                }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def get_cik_search(
    query: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for companies by name or CIK (Central Index Key).
    
    Args:
        query: Company name or CIK number
        api_key: FMP API key (falls back to FMP_API_KEY env var)
        
    Returns:
        dict with matching companies and their CIK numbers
        
    Example:
        >>> results = get_cik_search('Apple')
        >>> for company in results.get('data', []):
        ...     print(company['name'], company['cik'])
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    endpoint = f"{API_BASE}/v3/cik-search/{urllib.parse.quote(query)}"
    params = {
        "apikey": key
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if isinstance(data, list):
                return {
                    "query": query,
                    "count": len(data),
                    "data": data,
                    "source": "fmp_insider_api"
                }
            elif isinstance(data, dict) and "Error Message" in data:
                return {"error": data["Error Message"]}
            else:
                return {
                    "query": query,
                    "data": data if isinstance(data, list) else [data],
                    "source": "fmp_insider_api"
                }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


# Demo function for testing
def demo():
    """Demo with sample insider trading data (no API key required)."""
    return {
        "symbol": "AAPL",
        "count": 3,
        "data": [
            {
                "filingDate": "2024-12-15",
                "transactionDate": "2024-12-13",
                "reportingName": "COOK TIMOTHY D",
                "transactionType": "S-Sale",
                "securitiesTransacted": 223986,
                "price": 195.87,
                "securitiesOwned": 3280000,
                "typeOfOwner": "director"
            },
            {
                "filingDate": "2024-11-08",
                "transactionDate": "2024-11-05",
                "reportingName": "WILLIAMS JEFFREY E",
                "transactionType": "S-Sale",
                "securitiesTransacted": 82234,
                "price": 222.91,
                "securitiesOwned": 489560,
                "typeOfOwner": "officer"
            },
            {
                "filingDate": "2024-10-20",
                "transactionDate": "2024-10-18",
                "reportingName": "ADAMS KATHERINE L",
                "transactionType": "P-Purchase",
                "securitiesTransacted": 5000,
                "price": 228.45,
                "securitiesOwned": 125000,
                "typeOfOwner": "officer"
            }
        ],
        "source": "sample_data",
        "note": "This is sample data. Provide FMP_API_KEY env var for real insider trading data from SEC filings."
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
