"""
Nasdaq Data Link Fixed Income — US Treasury yields, TIPS, and credit data.

Provides free access to US Treasury yield curves, real yields (TIPS), bill rates,
and key spread calculations for quantitative fixed income analysis.

Source: https://data.nasdaq.com/databases/FIC
Update frequency: Daily
Category: Fixed Income & Credit
Free tier: Works without API key for USTREASURY datasets; 50 anonymous calls/day
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


API_BASE = "https://data.nasdaq.com/api/v3/datasets"


def get_treasury_yields(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get US Treasury yield curve data across all maturities.
    
    Includes yields for 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y maturities.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        api_key: Optional Nasdaq Data Link API key for higher limits
        
    Returns:
        dict with yield curve data, columns, and metadata
        
    Example:
        >>> yields = get_treasury_yields()
        >>> latest = yields.get('data', [[]])[0]
        >>> print(f"10Y yield: {latest[10]}%")
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    if api_key:
        params["api_key"] = api_key
    
    url = f"{API_BASE}/USTREASURY/YIELD.json?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            result = json.loads(response.read().decode())
            dataset = result.get("dataset", {})
            
            return {
                "data": dataset.get("data", []),
                "columns": dataset.get("column_names", []),
                "start_date": start_date,
                "end_date": end_date,
                "frequency": dataset.get("frequency"),
                "last_updated": dataset.get("newest_available_date"),
                "source": "US Treasury",
                "raw": dataset
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_real_yields(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get Treasury Inflation-Protected Securities (TIPS) real yields.
    
    TIPS yields adjusted for inflation expectations across multiple maturities.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        api_key: Optional Nasdaq Data Link API key
        
    Returns:
        dict with TIPS real yield data
        
    Example:
        >>> tips = get_real_yields()
        >>> print(tips.get('data', [[]])[0])
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    if api_key:
        params["api_key"] = api_key
    
    url = f"{API_BASE}/USTREASURY/REALYIELD.json?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            result = json.loads(response.read().decode())
            dataset = result.get("dataset", {})
            
            return {
                "data": dataset.get("data", []),
                "columns": dataset.get("column_names", []),
                "start_date": start_date,
                "end_date": end_date,
                "frequency": dataset.get("frequency"),
                "last_updated": dataset.get("newest_available_date"),
                "source": "US Treasury TIPS",
                "raw": dataset
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_bill_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get US Treasury bill rates for short-term maturities.
    
    Includes 4-week, 8-week, 13-week, 26-week, and 52-week T-bill rates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        api_key: Optional Nasdaq Data Link API key
        
    Returns:
        dict with T-bill rates data
        
    Example:
        >>> bills = get_bill_rates()
        >>> print(f"Latest rates: {bills.get('data', [[]])[0]}")
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    if api_key:
        params["api_key"] = api_key
    
    url = f"{API_BASE}/USTREASURY/BILLRATES.json?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            result = json.loads(response.read().decode())
            dataset = result.get("dataset", {})
            
            return {
                "data": dataset.get("data", []),
                "columns": dataset.get("column_names", []),
                "start_date": start_date,
                "end_date": end_date,
                "frequency": dataset.get("frequency"),
                "last_updated": dataset.get("newest_available_date"),
                "source": "US Treasury Bills",
                "raw": dataset
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_yield_curve_snapshot(api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Get the latest US Treasury yield curve snapshot across all maturities.
    
    Returns the most recent yield for each maturity from 1 month to 30 years.
    
    Args:
        api_key: Optional Nasdaq Data Link API key
        
    Returns:
        dict with latest yield curve snapshot
        
    Example:
        >>> curve = get_yield_curve_snapshot()
        >>> yields = curve.get('yields', {})
        >>> print(f"2Y: {yields.get('2Y')}%, 10Y: {yields.get('10Y')}%")
    """
    params = {"rows": 1}
    
    if api_key:
        params["api_key"] = api_key
    
    url = f"{API_BASE}/USTREASURY/YIELD.json?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            result = json.loads(response.read().decode())
            dataset = result.get("dataset", {})
            data = dataset.get("data", [])
            columns = dataset.get("column_names", [])
            
            if not data or not columns:
                return {"error": "No data available"}
            
            latest = data[0]
            date = latest[0]
            
            # Map columns to yields (skip date column)
            yields = {}
            maturity_map = {
                1: "1M", 2: "3M", 3: "6M", 4: "1Y", 5: "2Y",
                6: "3Y", 7: "5Y", 8: "7Y", 9: "10Y", 10: "20Y", 11: "30Y"
            }
            
            for i in range(1, len(latest)):
                if i in maturity_map and latest[i] is not None:
                    yields[maturity_map[i]] = latest[i]
            
            return {
                "date": date,
                "yields": yields,
                "columns": columns,
                "last_updated": dataset.get("newest_available_date"),
                "source": "US Treasury"
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_spread(
    maturity_long: str = "10Y",
    maturity_short: str = "2Y",
    days: int = 30,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Calculate yield spread between two maturities (e.g., 10Y-2Y).
    
    Common spreads: 10Y-2Y (recession indicator), 10Y-3M, 30Y-5Y
    
    Args:
        maturity_long: Longer maturity (10Y, 30Y, etc.)
        maturity_short: Shorter maturity (2Y, 3M, etc.)
        days: Number of days of historical data (default: 30)
        api_key: Optional Nasdaq Data Link API key
        
    Returns:
        dict with spread calculations over time
        
    Example:
        >>> spread = get_spread('10Y', '2Y')
        >>> latest = spread.get('spreads', [[]])[0]
        >>> print(f"10Y-2Y spread: {latest[1]:.2f} bps")
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    yields_data = get_treasury_yields(start_date, end_date, api_key)
    
    if "error" in yields_data:
        return yields_data
    
    columns = yields_data.get("columns", [])
    data = yields_data.get("data", [])
    
    # Map maturity strings to column indices
    maturity_map = {
        "1M": 1, "3M": 2, "6M": 3, "1Y": 4, "2Y": 5,
        "3Y": 6, "5Y": 7, "7Y": 8, "10Y": 9, "20Y": 10, "30Y": 11
    }
    
    if maturity_long not in maturity_map or maturity_short not in maturity_map:
        return {
            "error": f"Invalid maturity. Use: {', '.join(maturity_map.keys())}",
            "available": list(maturity_map.keys())
        }
    
    idx_long = maturity_map[maturity_long]
    idx_short = maturity_map[maturity_short]
    
    spreads = []
    for row in data:
        if len(row) > max(idx_long, idx_short):
            date = row[0]
            long_yield = row[idx_long]
            short_yield = row[idx_short]
            
            if long_yield is not None and short_yield is not None:
                spread_bps = (long_yield - short_yield) * 100  # Convert to basis points
                spreads.append([date, spread_bps, long_yield, short_yield])
    
    latest_spread = spreads[0][1] if spreads else None
    
    return {
        "spread": f"{maturity_long}-{maturity_short}",
        "latest_bps": latest_spread,
        "spreads": spreads,
        "columns": ["Date", "Spread (bps)", f"{maturity_long} Yield", f"{maturity_short} Yield"],
        "inverted": latest_spread < 0 if latest_spread is not None else None,
        "start_date": start_date,
        "end_date": end_date
    }


def demo():
    """Demo function showing latest yield curve snapshot."""
    curve = get_yield_curve_snapshot()
    
    if "error" in curve:
        return {
            "module": "nasdaq_data_link_fixed_income",
            "status": "demo",
            "note": "Demo mode - API not accessible",
            "sample_functions": [
                "get_treasury_yields()",
                "get_real_yields()",
                "get_bill_rates()",
                "get_yield_curve_snapshot()",
                "get_spread('10Y', '2Y')"
            ]
        }
    
    return {
        "module": "nasdaq_data_link_fixed_income",
        "latest_curve": curve,
        "note": "Real data from Nasdaq Data Link (formerly Quandl)"
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
