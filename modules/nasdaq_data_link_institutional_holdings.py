"""
Nasdaq Data Link Institutional Holdings — 13F institutional ownership data.

Nasdaq Data Link (formerly Quandl) provides datasets on institutional holdings 
from 13F filings, including Zacks Institutional Holdings data. Covers hedge fund 
and institutional positions with historical depth.

Source: https://data.nasdaq.com/api/v3/datatables/
Update frequency: Quarterly
Category: Insider & Institutional
Free tier: Limited queries with API key (get at https://data.nasdaq.com/)
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://data.nasdaq.com/api/v3/datatables"
# API key from environment
DEFAULT_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY")


def get_institutional_holders(
    ticker: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get top institutional holders for a stock from 13F filings.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        api_key: Nasdaq Data Link API key (or set NASDAQ_DATA_LINK_API_KEY env var)
        
    Returns:
        dict with list of institutional holders and their positions
        
    Example:
        >>> holders = get_institutional_holders('AAPL')
        >>> for holder in holders.get('holders', []):
        ...     print(holder['institution'], holder['shares'])
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {
            "error": "API key required. Set NASDAQ_DATA_LINK_API_KEY env var or get free key at https://data.nasdaq.com/"
        }
    
    # Use ZACKS/IH table for institutional holdings
    endpoint = f"{API_BASE}/ZACKS/IH.json"
    
    params = {
        "ticker": ticker.upper(),
        "api_key": key,
        "qopts.per_page": 100
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            # Extract datatable data
            datatable = data.get("datatable", {})
            columns = datatable.get("columns", [])
            rows = datatable.get("data", [])
            
            if not rows:
                return {
                    "ticker": ticker.upper(),
                    "holders": [],
                    "total": 0,
                    "note": "No institutional holdings data found"
                }
            
            # Map column names to indices
            col_map = {col["name"]: i for i, col in enumerate(columns)}
            
            # Parse holders
            holders = []
            for row in rows:
                holder = {}
                if "m_ticker" in col_map:
                    holder["ticker"] = row[col_map["m_ticker"]]
                if "inst_name" in col_map:
                    holder["institution"] = row[col_map["inst_name"]]
                if "shares_held" in col_map:
                    holder["shares"] = row[col_map["shares_held"]]
                if "pct_shares_out" in col_map:
                    holder["percent_outstanding"] = row[col_map["pct_shares_out"]]
                if "per_end_date" in col_map:
                    holder["period_end"] = row[col_map["per_end_date"]]
                if "filing_date" in col_map:
                    holder["filing_date"] = row[col_map["filing_date"]]
                
                holders.append(holder)
            
            return {
                "ticker": ticker.upper(),
                "holders": holders,
                "total": len(holders),
                "as_of": datetime.now().isoformat(),
                "raw": data
            }
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode() if e.fp else str(e)
        return {"error": f"HTTP {e.code}: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def get_13f_filings(
    cik: Optional[str] = None,
    ticker: Optional[str] = None,
    date: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get 13F filing data filtered by CIK, ticker, or date.
    
    Args:
        cik: Central Index Key (institution identifier)
        ticker: Stock ticker to filter by
        date: Filing date (YYYY-MM-DD format)
        api_key: Nasdaq Data Link API key
        
    Returns:
        dict with 13F filing records
        
    Example:
        >>> filings = get_13f_filings(ticker='AAPL')
        >>> print(filings.get('total'), 'filings found')
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    if not cik and not ticker and not date:
        return {"error": "Must provide at least one filter: cik, ticker, or date"}
    
    endpoint = f"{API_BASE}/ZACKS/IH.json"
    
    params = {"api_key": key, "qopts.per_page": 200}
    
    if ticker:
        params["ticker"] = ticker.upper()
    if cik:
        params["cik"] = cik
    if date:
        params["per_end_date"] = date
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            datatable = data.get("datatable", {})
            columns = datatable.get("columns", [])
            rows = datatable.get("data", [])
            
            col_map = {col["name"]: i for i, col in enumerate(columns)}
            
            filings = []
            for row in rows:
                filing = {}
                for col_name, idx in col_map.items():
                    if idx < len(row):
                        filing[col_name] = row[idx]
                filings.append(filing)
            
            return {
                "filings": filings,
                "total": len(filings),
                "filters": {
                    "cik": cik,
                    "ticker": ticker,
                    "date": date
                },
                "raw": data
            }
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode() if e.fp else str(e)
        return {"error": f"HTTP {e.code}: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def get_ownership_changes(
    ticker: str,
    periods: int = 4,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get quarterly ownership changes for institutional holders.
    
    Args:
        ticker: Stock ticker symbol
        periods: Number of quarters to analyze (default 4)
        api_key: Nasdaq Data Link API key
        
    Returns:
        dict with ownership trends and changes over time
        
    Example:
        >>> changes = get_ownership_changes('AAPL', periods=4)
        >>> print(changes.get('summary'))
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    # Get institutional holdings data
    holdings_data = get_institutional_holders(ticker, api_key=key)
    
    if "error" in holdings_data:
        return holdings_data
    
    holders = holdings_data.get("holders", [])
    
    if not holders:
        return {
            "ticker": ticker.upper(),
            "periods": periods,
            "changes": [],
            "note": "No data available to calculate changes"
        }
    
    # Group by period and institution
    period_data = {}
    for holder in holders:
        period = holder.get("period_end")
        inst = holder.get("institution")
        shares = holder.get("shares", 0)
        
        if period and inst:
            if period not in period_data:
                period_data[period] = {}
            period_data[period][inst] = shares
    
    # Sort periods
    sorted_periods = sorted(period_data.keys(), reverse=True)[:periods]
    
    # Calculate changes
    changes = []
    if len(sorted_periods) >= 2:
        for i in range(len(sorted_periods) - 1):
            current_period = sorted_periods[i]
            prev_period = sorted_periods[i + 1]
            
            current = period_data[current_period]
            previous = period_data[prev_period]
            
            for inst in current:
                if inst in previous:
                    delta = current[inst] - previous[inst]
                    pct_change = (delta / previous[inst] * 100) if previous[inst] else 0
                    
                    changes.append({
                        "institution": inst,
                        "from_period": prev_period,
                        "to_period": current_period,
                        "shares_change": delta,
                        "percent_change": round(pct_change, 2)
                    })
    
    # Summary stats
    total_increases = sum(1 for c in changes if c["shares_change"] > 0)
    total_decreases = sum(1 for c in changes if c["shares_change"] < 0)
    
    return {
        "ticker": ticker.upper(),
        "periods_analyzed": len(sorted_periods),
        "periods": sorted_periods,
        "changes": changes,
        "summary": {
            "total_institutions_tracked": len(changes),
            "increased_positions": total_increases,
            "decreased_positions": total_decreases
        },
        "raw_holdings": holdings_data
    }


def search_institutions(
    query: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for institutions by name in 13F filings.
    
    Args:
        query: Institution name or partial name to search
        api_key: Nasdaq Data Link API key
        
    Returns:
        dict with matching institutions and their recent holdings
        
    Example:
        >>> results = search_institutions('Vanguard')
        >>> for inst in results.get('institutions', []):
        ...     print(inst['name'], inst['holdings_count'])
    """
    key = api_key or DEFAULT_KEY
    if not key:
        return {"error": "API key required"}
    
    endpoint = f"{API_BASE}/ZACKS/IH.json"
    
    # Note: Nasdaq Data Link doesn't support text search in API params,
    # so we fetch a larger dataset and filter locally
    params = {
        "api_key": key,
        "qopts.per_page": 1000
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            datatable = data.get("datatable", {})
            columns = datatable.get("columns", [])
            rows = datatable.get("data", [])
            
            col_map = {col["name"]: i for i, col in enumerate(columns)}
            
            # Find institution name column
            inst_col_idx = col_map.get("inst_name")
            if inst_col_idx is None:
                return {"error": "Institution name column not found in API response"}
            
            # Filter rows by query
            query_lower = query.lower()
            matching_rows = [
                row for row in rows 
                if inst_col_idx < len(row) and query_lower in str(row[inst_col_idx]).lower()
            ]
            
            # Group by institution
            institutions = {}
            for row in matching_rows:
                inst_name = row[inst_col_idx] if inst_col_idx < len(row) else "Unknown"
                
                if inst_name not in institutions:
                    institutions[inst_name] = {
                        "name": inst_name,
                        "holdings": [],
                        "holdings_count": 0
                    }
                
                holding = {}
                for col_name, idx in col_map.items():
                    if idx < len(row):
                        holding[col_name] = row[idx]
                
                institutions[inst_name]["holdings"].append(holding)
                institutions[inst_name]["holdings_count"] += 1
            
            return {
                "query": query,
                "institutions": list(institutions.values()),
                "total": len(institutions),
                "raw": data
            }
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode() if e.fp else str(e)
        return {"error": f"HTTP {e.code}: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def demo():
    """Demo with sample institutional holdings data (no API key required)."""
    sample_data = {
        "ticker": "AAPL",
        "holders": [
            {
                "institution": "Vanguard Group Inc",
                "shares": 1234567890,
                "percent_outstanding": 7.85,
                "period_end": "2024-12-31"
            },
            {
                "institution": "BlackRock Inc",
                "shares": 1098765432,
                "percent_outstanding": 6.98,
                "period_end": "2024-12-31"
            },
            {
                "institution": "State Street Corp",
                "shares": 876543210,
                "percent_outstanding": 5.57,
                "period_end": "2024-12-31"
            }
        ],
        "total": 3,
        "note": "This is sample data. Provide API key for real 13F filing data from Nasdaq Data Link."
    }
    return sample_data


if __name__ == "__main__":
    # Test with demo data
    print(json.dumps(demo(), indent=2))
