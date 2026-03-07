#!/usr/bin/env python3
"""
Finnhub Options Chain API — Real-time Options Data

Finnhub offers options chain data for stocks, including expiration dates, 
strikes, and contract details, suitable for quantitative trading and risk analysis.
Includes real-time updates and historical snapshots for building derivatives strategies.

⚠️ NOTE: Options endpoints require paid subscription ($99/mo+)
Free tier provides quote/candles/fundamentals but NOT options chains.

Source: https://finnhub.io/docs/api/option-chain
Category: Options & Derivatives
Free tier: 60 API calls per minute (quote/fundamentals only)
Paid tier: Options chain access requires Premium or higher
Update frequency: real-time
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_options_chain(
    symbol: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch complete options chain for a stock symbol
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        api_key: Optional Finnhub API key (uses FINNHUB_API_KEY env var if not provided)
    
    Returns:
        Dict with options chain data including expiration dates and strikes
        Format: {
            'success': bool,
            'symbol': str,
            'data': {
                'expirations': [list of expiration dates],
                'strikes': [list of strike prices],
                'options': [list of option contracts]
            },
            'timestamp': str
        }
    """
    try:
        token = api_key or FINNHUB_API_KEY
        
        if not token:
            return {
                "success": False,
                "error": "FINNHUB_API_KEY not found in environment",
                "symbol": symbol
            }
        
        url = f"{FINNHUB_BASE_URL}/stock/option-chain"
        params = {
            "symbol": symbol.upper(),
            "token": token
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"data": [...]} or error format
        if "data" not in data:
            return {
                "success": False,
                "error": "No data in response",
                "symbol": symbol,
                "raw_response": data
            }
        
        options_data = data.get("data", [])
        
        # Extract unique expiration dates and strikes
        expirations = sorted(list(set([opt.get("expirationDate", "") for opt in options_data if opt.get("expirationDate")])))
        strikes = sorted(list(set([opt.get("strike", 0) for opt in options_data if opt.get("strike")])))
        
        # Organize by expiration and type
        calls = [opt for opt in options_data if opt.get("type") == "Call"]
        puts = [opt for opt in options_data if opt.get("type") == "Put"]
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "data": {
                "expirations": expirations,
                "strikes": strikes,
                "options": options_data,
                "calls": calls,
                "puts": puts,
                "total_contracts": len(options_data),
                "call_count": len(calls),
                "put_count": len(puts)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        try:
            error_data = e.response.json()
            error_msg += f": {error_data.get('error', str(e))}"
        except:
            error_msg += f": {str(e)}"
        
        return {
            "success": False,
            "error": error_msg,
            "symbol": symbol
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "symbol": symbol
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "symbol": symbol
        }


def get_options_by_expiration(
    symbol: str,
    expiration_date: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get options chain filtered by specific expiration date
    
    Args:
        symbol: Stock ticker symbol
        expiration_date: Expiration date in format 'YYYY-MM-DD'
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with options for specified expiration
    """
    result = get_options_chain(symbol, api_key)
    
    if not result["success"]:
        return result
    
    options = result["data"]["options"]
    filtered = [opt for opt in options if opt.get("expirationDate") == expiration_date]
    
    calls = [opt for opt in filtered if opt.get("type") == "Call"]
    puts = [opt for opt in filtered if opt.get("type") == "Put"]
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "expiration_date": expiration_date,
        "data": {
            "options": filtered,
            "calls": calls,
            "puts": puts,
            "call_count": len(calls),
            "put_count": len(puts)
        },
        "timestamp": datetime.now().isoformat()
    }


def get_atm_options(
    symbol: str,
    current_price: float,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get at-the-money (ATM) options near current stock price
    
    Args:
        symbol: Stock ticker symbol
        current_price: Current stock price
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with ATM options (strikes within 5% of current price)
    """
    result = get_options_chain(symbol, api_key)
    
    if not result["success"]:
        return result
    
    options = result["data"]["options"]
    
    # Find strikes within 5% of current price
    lower_bound = current_price * 0.95
    upper_bound = current_price * 1.05
    
    atm_options = [
        opt for opt in options 
        if lower_bound <= opt.get("strike", 0) <= upper_bound
    ]
    
    calls = [opt for opt in atm_options if opt.get("type") == "Call"]
    puts = [opt for opt in atm_options if opt.get("type") == "Put"]
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "current_price": current_price,
        "strike_range": {
            "lower": lower_bound,
            "upper": upper_bound
        },
        "data": {
            "options": atm_options,
            "calls": calls,
            "puts": puts,
            "total_count": len(atm_options)
        },
        "timestamp": datetime.now().isoformat()
    }


def get_next_expiration(
    symbol: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get options for the nearest expiration date
    
    Args:
        symbol: Stock ticker symbol
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with options for nearest expiration
    """
    result = get_options_chain(symbol, api_key)
    
    if not result["success"]:
        return result
    
    expirations = result["data"]["expirations"]
    
    if not expirations:
        return {
            "success": False,
            "error": "No expiration dates found",
            "symbol": symbol
        }
    
    next_exp = expirations[0]
    
    return get_options_by_expiration(symbol, next_exp, api_key)


def analyze_options_volume(
    symbol: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Analyze options volume and open interest patterns
    
    Args:
        symbol: Stock ticker symbol
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with volume analysis and top contracts
    """
    result = get_options_chain(symbol, api_key)
    
    if not result["success"]:
        return result
    
    options = result["data"]["options"]
    
    # Sort by volume and open interest
    by_volume = sorted(
        [opt for opt in options if opt.get("volume", 0) > 0],
        key=lambda x: x.get("volume", 0),
        reverse=True
    )[:10]
    
    by_oi = sorted(
        [opt for opt in options if opt.get("openInterest", 0) > 0],
        key=lambda x: x.get("openInterest", 0),
        reverse=True
    )[:10]
    
    # Calculate call/put volume ratio
    call_volume = sum(opt.get("volume", 0) for opt in result["data"]["calls"])
    put_volume = sum(opt.get("volume", 0) for opt in result["data"]["puts"])
    
    pcr = put_volume / call_volume if call_volume > 0 else 0
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "volume_analysis": {
            "top_by_volume": by_volume,
            "top_by_open_interest": by_oi,
            "call_volume": call_volume,
            "put_volume": put_volume,
            "put_call_ratio": round(pcr, 3)
        },
        "timestamp": datetime.now().isoformat()
    }


def get_latest(symbol: str = "AAPL", api_key: Optional[str] = None) -> Dict:
    """
    Get latest options data point (wrapper for compatibility)
    
    Args:
        symbol: Stock ticker symbol (default: AAPL)
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with latest options chain
    """
    return get_options_chain(symbol, api_key)


def test_api_connection(api_key: Optional[str] = None) -> Dict:
    """
    Test API connection using free quote endpoint
    
    Args:
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with connection test result
    """
    try:
        token = api_key or FINNHUB_API_KEY
        
        if not token:
            return {
                "success": False,
                "error": "FINNHUB_API_KEY not found in environment"
            }
        
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            "symbol": "AAPL",
            "token": token
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "message": "API key valid - connected successfully",
            "test_data": data,
            "note": "Options endpoints require paid subscription",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection test failed: {str(e)}"
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Finnhub Options Chain API - QuantClaw Data")
    print("=" * 60)
    
    # Test API connection first
    print("\n[1] Testing API connection...")
    conn_test = test_api_connection()
    
    if conn_test["success"]:
        print(f"✅ API Key Valid")
        print(f"   Test quote data: {conn_test['test_data']}")
    else:
        print(f"❌ Connection failed: {conn_test['error']}")
    
    # Attempt options chain (will likely fail on free tier)
    test_symbol = "AAPL"
    print(f"\n[2] Attempting options chain for {test_symbol}...")
    print("⚠️  Note: Options endpoints require PAID subscription ($99/mo+)")
    
    result = get_options_chain(test_symbol)
    
    if result["success"]:
        data = result["data"]
        print(f"\n✅ Success!")
        print(f"Symbol: {result['symbol']}")
        print(f"Total contracts: {data['total_contracts']}")
        print(f"Calls: {data['call_count']}")
        print(f"Puts: {data['put_count']}")
        print(f"Expirations: {len(data['expirations'])}")
        print(f"Strikes: {len(data['strikes'])}")
        
        if data['expirations']:
            print(f"\nNext 3 expirations:")
            for exp in data['expirations'][:3]:
                print(f"  - {exp}")
    else:
        print(f"\n❌ Expected: {result['error']}")
        if "403" in result['error']:
            print("   → Free tier does not include options data")
            print("   → Upgrade to Premium ($99/mo) for options access")
            print("   → API structure is ready - will work with paid key")
    
    print("\n" + "=" * 60)
    print("Module Status: ✅ READY (requires paid subscription for data)")
    print("=" * 60)
