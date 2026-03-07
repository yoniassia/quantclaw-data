"""
Twelve Data Options Chain — Options & Derivatives Data

Comprehensive options chain data for global equities via Twelve Data API.
Real-time pricing, Greeks, unusual activity, and expiration data.

Source: https://twelvedata.com/docs#options
Category: Options & Derivatives

Use cases:
- Options chain analysis for trading strategies
- Put/call ratio monitoring
- Unusual options activity detection
- Max pain calculation
- Greeks analysis for risk management

Free tier: 800 API calls/day, 8 calls/min (no credit card required)
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache" / "twelve_data_options"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.twelvedata.com"


def _get_api_key() -> Optional[str]:
    """Get Twelve Data API key from environment."""
    return os.environ.get("TWELVE_DATA_API_KEY")


def _check_api_key() -> Dict[str, str]:
    """Check if API key is configured, return error dict if not."""
    if not _get_api_key():
        return {
            "error": "TWELVE_DATA_API_KEY not found in environment",
            "message": "Set environment variable TWELVE_DATA_API_KEY to use Twelve Data API",
            "help": "Get free API key at https://twelvedata.com/pricing"
        }
    return {}


def get_options_expirations(symbol: str = "AAPL", use_cache: bool = True) -> Dict[str, Any]:
    """
    Get available options expiration dates for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: AAPL)
        use_cache: Use cached data if available and < 24h old
        
    Returns:
        Dict with expiration dates list or error message
    """
    # Check API key
    error = _check_api_key()
    if error:
        return error
    
    # Check cache
    cache_path = CACHE_DIR / f"{symbol}_expirations.json"
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/options/expiration"
    params = {
        "symbol": symbol,
        "apikey": _get_api_key()
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "symbol": symbol}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}", "symbol": symbol}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_options_chain(symbol: str = "AAPL", expiration_date: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
    """
    Get full options chain (calls + puts) for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: AAPL)
        expiration_date: Expiration date in YYYY-MM-DD format (default: nearest expiration)
        use_cache: Use cached data if available and < 1h old
        
    Returns:
        Dict with options chain data including calls and puts, or error message
    """
    # Check API key
    error = _check_api_key()
    if error:
        return error
    
    # Build cache key
    cache_key = f"{symbol}_{expiration_date or 'nearest'}_chain.json"
    cache_path = CACHE_DIR / cache_key
    
    # Check cache (shorter TTL for chain data - 1 hour)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/options/chain"
    params = {
        "symbol": symbol,
        "apikey": _get_api_key()
    }
    
    if expiration_date:
        params["expiration_date"] = expiration_date
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "symbol": symbol}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}", "symbol": symbol}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_options_quote(symbol: str = "AAPL", option_type: str = "call", strike: Optional[float] = None, expiration: Optional[str] = None) -> Dict[str, Any]:
    """
    Get quote for a specific option contract.
    
    Args:
        symbol: Stock ticker symbol (default: AAPL)
        option_type: "call" or "put"
        strike: Strike price (default: ATM)
        expiration: Expiration date in YYYY-MM-DD format (default: nearest)
        
    Returns:
        Dict with option quote data or error message
    """
    # Check API key
    error = _check_api_key()
    if error:
        return error
    
    # Validate option_type
    if option_type.lower() not in ["call", "put"]:
        return {"error": f"Invalid option_type: {option_type}. Must be 'call' or 'put'"}
    
    # Get full chain and filter
    chain_data = get_options_chain(symbol, expiration)
    
    if "error" in chain_data:
        return chain_data
    
    # Extract the requested option type
    option_key = f"{option_type.lower()}s"
    if option_key not in chain_data:
        return {"error": f"No {option_type}s found in chain", "symbol": symbol}
    
    options = chain_data[option_key]
    
    # If strike specified, filter to that strike
    if strike is not None:
        matching = [opt for opt in options if opt.get("strike") == strike]
        if matching:
            return matching[0]
        else:
            return {"error": f"No {option_type} found at strike {strike}", "symbol": symbol}
    
    # Return first option (typically ATM or closest)
    if options:
        return options[0]
    
    return {"error": f"No {option_type} options available", "symbol": symbol}


def get_options_summary(symbol: str = "AAPL") -> Dict[str, Any]:
    """
    Get options summary statistics including volume, put/call ratio, max pain.
    
    Args:
        symbol: Stock ticker symbol (default: AAPL)
        
    Returns:
        Dict with summary statistics or error message
    """
    # Get full chain
    chain_data = get_options_chain(symbol)
    
    if "error" in chain_data:
        return chain_data
    
    # Calculate summary stats
    summary = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "expiration_date": chain_data.get("expiration_date", "N/A")
    }
    
    # Extract calls and puts
    calls = chain_data.get("calls", [])
    puts = chain_data.get("puts", [])
    
    # Total volume
    call_volume = sum(opt.get("volume", 0) or 0 for opt in calls)
    put_volume = sum(opt.get("volume", 0) or 0 for opt in puts)
    
    summary["call_volume"] = call_volume
    summary["put_volume"] = put_volume
    summary["total_volume"] = call_volume + put_volume
    
    # Put/Call ratio
    if call_volume > 0:
        summary["put_call_ratio"] = round(put_volume / call_volume, 3)
    else:
        summary["put_call_ratio"] = None
    
    # Open interest
    call_oi = sum(opt.get("open_interest", 0) or 0 for opt in calls)
    put_oi = sum(opt.get("open_interest", 0) or 0 for opt in puts)
    
    summary["call_open_interest"] = call_oi
    summary["put_open_interest"] = put_oi
    summary["total_open_interest"] = call_oi + put_oi
    
    # Max pain calculation (strike with max combined call + put open interest)
    all_options = calls + puts
    strike_oi = {}
    
    for opt in all_options:
        strike = opt.get("strike")
        oi = opt.get("open_interest", 0) or 0
        if strike is not None:
            strike_oi[strike] = strike_oi.get(strike, 0) + oi
    
    if strike_oi:
        max_pain_strike = max(strike_oi.items(), key=lambda x: x[1])
        summary["max_pain_strike"] = max_pain_strike[0]
        summary["max_pain_oi"] = max_pain_strike[1]
    else:
        summary["max_pain_strike"] = None
        summary["max_pain_oi"] = None
    
    return summary


# CLI helpers for testing
def cli_options_expirations(symbol: str = "AAPL"):
    """CLI: Display available expiration dates."""
    data = get_options_expirations(symbol)
    print(json.dumps(data, indent=2))


def cli_options_chain(symbol: str = "AAPL", expiration: Optional[str] = None):
    """CLI: Display full options chain."""
    data = get_options_chain(symbol, expiration)
    print(json.dumps(data, indent=2))


def cli_options_summary(symbol: str = "AAPL"):
    """CLI: Display options summary statistics."""
    data = get_options_summary(symbol)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python twelve_data_options_chain.py [summary|expirations|chain] [SYMBOL]")
        cli_options_summary()
        sys.exit(0)
    
    command = args[0]
    symbol = args[1] if len(args) > 1 else "AAPL"
    
    if command == "summary":
        cli_options_summary(symbol)
    elif command == "expirations":
        cli_options_expirations(symbol)
    elif command == "chain":
        expiration = args[2] if len(args) > 2 else None
        cli_options_chain(symbol, expiration)
    else:
        print(f"Unknown command: {command}")
        print("Available: summary, expirations, chain")
        sys.exit(1)
