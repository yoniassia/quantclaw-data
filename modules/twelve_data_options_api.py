"""
Twelve Data Options API — Options chain and derivatives data.

Real-time and historical options data including chains, expirations, and quotes
for global markets. Supports quantitative finance applications like backtesting
and options pricing models.

Source: https://api.twelvedata.com
Update frequency: Real-time
Category: Options & Derivatives
Free tier: 800 calls/day, 8 calls/minute
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://api.twelvedata.com"
DEFAULT_KEY = os.environ.get("TWELVE_DATA_API_KEY")


def get_options_chain(
    symbol: str,
    expiration_date: Optional[str] = None,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get full options chain for a symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        expiration_date: Optional expiration date in YYYY-MM-DD format
        apikey: Twelve Data API key (uses TWELVE_DATA_API_KEY env if not provided)
        
    Returns:
        dict with options chain data including calls and puts
        
    Example:
        >>> chain = get_options_chain('AAPL')
        >>> print(chain.get('symbol'), len(chain.get('calls', [])))
        >>> chain_exp = get_options_chain('AAPL', expiration_date='2026-03-20')
    """
    key = apikey or DEFAULT_KEY
    if not key:
        return {
            "error": "API key required. Set TWELVE_DATA_API_KEY env or pass apikey parameter",
            "docs": "https://twelvedata.com/pricing"
        }
    
    endpoint = f"{API_BASE}/options/chain"
    params = {
        "symbol": symbol.upper(),
        "apikey": key
    }
    
    if expiration_date:
        params["expiration_date"] = expiration_date
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "status" in data and data["status"] == "error":
                return {"error": data.get("message", "API error"), "raw": data}
            
            # Extract and structure the response
            result = {
                "symbol": data.get("symbol", symbol),
                "expiration_date": data.get("expiration_date"),
                "calls": data.get("calls", []),
                "puts": data.get("puts", []),
                "total_calls": len(data.get("calls", [])),
                "total_puts": len(data.get("puts", [])),
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
            
            return result
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        try:
            error_data = json.loads(error_body)
            return {"error": error_data.get("message", str(e)), "status_code": e.code}
        except:
            return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": str(e)}


def get_options_expirations(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get available expiration dates for options on a symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        apikey: Twelve Data API key (uses TWELVE_DATA_API_KEY env if not provided)
        
    Returns:
        dict with list of available expiration dates
        
    Example:
        >>> expirations = get_options_expirations('AAPL')
        >>> print(expirations.get('dates', [])[:5])  # First 5 dates
    """
    key = apikey or DEFAULT_KEY
    if not key:
        return {
            "error": "API key required. Set TWELVE_DATA_API_KEY env or pass apikey parameter",
            "docs": "https://twelvedata.com/pricing"
        }
    
    endpoint = f"{API_BASE}/options/expiration"
    params = {
        "symbol": symbol.upper(),
        "apikey": key
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "status" in data and data["status"] == "error":
                return {"error": data.get("message", "API error"), "raw": data}
            
            # Structure the response
            result = {
                "symbol": data.get("symbol", symbol),
                "dates": data.get("dates", []),
                "total": len(data.get("dates", [])),
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
            
            return result
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        try:
            error_data = json.loads(error_body)
            return {"error": error_data.get("message", str(e)), "status_code": e.code}
        except:
            return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": str(e)}


def get_options_quotes(
    symbol: str,
    option_type: str = "call",
    strike: Optional[float] = None,
    expiration_date: Optional[str] = None,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get filtered options quotes by type and strike.
    
    This is a convenience wrapper around get_options_chain that filters
    the results by option type (call/put) and optionally by strike price.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        option_type: 'call' or 'put' (default: 'call')
        strike: Optional strike price to filter by
        expiration_date: Optional expiration date in YYYY-MM-DD format
        apikey: Twelve Data API key (uses TWELVE_DATA_API_KEY env if not provided)
        
    Returns:
        dict with filtered options quotes
        
    Example:
        >>> calls = get_options_quotes('AAPL', option_type='call')
        >>> print(len(calls.get('options', [])))
        >>> atm_puts = get_options_quotes('AAPL', option_type='put', strike=150.0)
    """
    # Get the full chain
    chain = get_options_chain(symbol, expiration_date=expiration_date, apikey=apikey)
    
    if "error" in chain:
        return chain
    
    # Filter by option type
    option_type = option_type.lower()
    if option_type not in ["call", "put"]:
        return {"error": f"Invalid option_type: {option_type}. Use 'call' or 'put'"}
    
    options_key = "calls" if option_type == "call" else "puts"
    options = chain.get(options_key, [])
    
    # Filter by strike if provided
    if strike is not None:
        options = [opt for opt in options if opt.get("strike") == strike]
    
    result = {
        "symbol": chain.get("symbol"),
        "option_type": option_type,
        "expiration_date": chain.get("expiration_date"),
        "strike_filter": strike,
        "options": options,
        "total": len(options),
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def demo():
    """Demo with sample options data (no API key required)."""
    sample_data = {
        "symbol": "AAPL",
        "expiration_date": "2026-03-20",
        "calls": [
            {
                "strike": 150.0,
                "bid": 5.20,
                "ask": 5.30,
                "last": 5.25,
                "volume": 1250,
                "open_interest": 5432
            }
        ],
        "puts": [
            {
                "strike": 150.0,
                "bid": 2.10,
                "ask": 2.15,
                "last": 2.12,
                "volume": 980,
                "open_interest": 3210
            }
        ],
        "note": "This is sample data. Provide API key for real data."
    }
    return sample_data


if __name__ == "__main__":
    # Test with demo data
    print(json.dumps(demo(), indent=2))
