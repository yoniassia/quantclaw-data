#!/usr/bin/env python3
"""
Deribit Crypto Options API — Specialized Options Data Module

Focused specifically on crypto options (BTC/ETH) with:
- Formatted option chains by expiration and strike
- Greeks analysis (Delta, Gamma, Vega, Theta, Rho)
- Historical and implied volatility metrics
- Option-specific order book summaries
- Volatility surface data

Complements deribit_crypto_derivatives.py with options-specialized views.

Free tier: Unlimited public API access (rate limit: 10 req/sec)
Source: https://docs.deribit.com/
Category: Options & Derivatives
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict

BASE_URL = "https://www.deribit.com/api/v2/public"

def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Helper function for API requests with error handling
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Dict with API response or error
    """
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            return {"success": True, "data": data["result"]}
        elif "error" in data:
            return {"success": False, "error": data["error"].get("message", "Unknown error")}
        else:
            return {"success": False, "error": "Unexpected response format"}
            
    except requests.RequestException as e:
        return {"success": False, "error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_options_instruments(currency: str = "BTC", expired: bool = False) -> Dict:
    """
    Get all option instruments for a currency with detailed metadata
    
    Args:
        currency: BTC or ETH (default: BTC)
        expired: Include expired options (default: False)
        
    Returns:
        Dict with options list, count, and expiration summary
    """
    result = _make_request("get_instruments", {
        "currency": currency.upper(),
        "kind": "option",
        "expired": str(expired).lower()
    })
    
    if not result["success"]:
        return result
    
    instruments = result["data"]
    
    # Organize by expiration and option type
    by_expiration = defaultdict(lambda: {"calls": [], "puts": []})
    strikes = set()
    
    for inst in instruments:
        exp_ts = inst.get("expiration_timestamp", 0)
        exp_date = datetime.fromtimestamp(exp_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if exp_ts else "Unknown"
        opt_type = inst.get("option_type", "").lower()
        strike = inst.get("strike", 0)
        
        strikes.add(strike)
        
        option_data = {
            "instrument_name": inst.get("instrument_name"),
            "strike": strike,
            "expiration_timestamp": exp_ts,
            "expiration_date": exp_date,
            "tick_size": inst.get("tick_size"),
            "min_trade_amount": inst.get("min_trade_amount"),
            "is_active": inst.get("is_active", False)
        }
        
        if opt_type == "call":
            by_expiration[exp_date]["calls"].append(option_data)
        elif opt_type == "put":
            by_expiration[exp_date]["puts"].append(option_data)
    
    # Sort strikes for each expiration
    for exp_date in by_expiration:
        by_expiration[exp_date]["calls"].sort(key=lambda x: x["strike"])
        by_expiration[exp_date]["puts"].sort(key=lambda x: x["strike"])
    
    return {
        "success": True,
        "currency": currency.upper(),
        "total_options": len(instruments),
        "active_options": sum(1 for i in instruments if i.get("is_active")),
        "expirations": sorted(by_expiration.keys()),
        "strike_range": {"min": min(strikes) if strikes else 0, "max": max(strikes) if strikes else 0},
        "options_by_expiration": dict(by_expiration),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_option_book_summary(currency: str = "BTC") -> Dict:
    """
    Get option book summaries with Greeks for all active options
    
    Args:
        currency: BTC or ETH (default: BTC)
        
    Returns:
        Dict with options data including prices, IV, and Greeks
    """
    result = _make_request("get_book_summary_by_currency", {
        "currency": currency.upper(),
        "kind": "option"
    })
    
    if not result["success"]:
        return result
    
    summaries = result["data"]
    
    # Extract key metrics
    options_data = []
    total_volume = 0
    total_open_interest = 0
    
    for summary in summaries:
        greeks = summary.get("greeks", {})
        
        option = {
            "instrument_name": summary.get("instrument_name"),
            "underlying_index": summary.get("underlying_index"),
            "last_price": summary.get("last"),
            "mark_price": summary.get("mark_price"),
            "bid": summary.get("bid_price"),
            "ask": summary.get("ask_price"),
            "mid_price": summary.get("mid_price"),
            "implied_volatility": summary.get("mark_iv"),
            "greeks": {
                "delta": greeks.get("delta"),
                "gamma": greeks.get("gamma"),
                "vega": greeks.get("vega"),
                "theta": greeks.get("theta"),
                "rho": greeks.get("rho")
            },
            "volume_24h": summary.get("volume_usd", 0),
            "open_interest": summary.get("open_interest", 0),
            "estimated_delivery_price": summary.get("estimated_delivery_price")
        }
        
        options_data.append(option)
        total_volume += summary.get("volume_usd", 0)
        total_open_interest += summary.get("open_interest", 0)
    
    # Calculate average IV (weighted by open interest)
    total_oi = sum(o["open_interest"] for o in options_data if o["open_interest"])
    avg_iv = 0
    if total_oi > 0:
        avg_iv = sum(
            (o.get("implied_volatility", 0) or 0) * o["open_interest"]
            for o in options_data if o["open_interest"]
        ) / total_oi
    
    return {
        "success": True,
        "currency": currency.upper(),
        "options_count": len(options_data),
        "total_volume_24h_usd": total_volume,
        "total_open_interest": total_open_interest,
        "average_implied_volatility": round(avg_iv, 2) if avg_iv else None,
        "options": options_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_option_chain(underlying: str = "BTC", expiration: Optional[str] = None) -> Dict:
    """
    Get formatted option chain with calls and puts side-by-side
    
    Args:
        underlying: BTC or ETH (default: BTC)
        expiration: Specific expiration date in DDMMMYY format (e.g., "28MAR26")
                   If None, returns nearest expiration
        
    Returns:
        Dict with formatted option chain showing calls/puts at each strike
    """
    # Get all options
    instruments_result = get_options_instruments(underlying, expired=False)
    
    if not instruments_result["success"]:
        return instruments_result
    
    options_by_exp = instruments_result["options_by_expiration"]
    
    # Select expiration
    if expiration:
        # Try to find matching expiration
        target_exp = None
        for exp_date in options_by_exp.keys():
            if expiration.upper() in exp_date.upper():
                target_exp = exp_date
                break
        if not target_exp:
            return {
                "success": False,
                "error": f"Expiration {expiration} not found. Available: {list(options_by_exp.keys())[:5]}"
            }
    else:
        # Get nearest expiration
        sorted_exps = sorted(options_by_exp.keys())
        target_exp = sorted_exps[0] if sorted_exps else None
    
    if not target_exp:
        return {"success": False, "error": "No active options found"}
    
    # Build option chain
    calls = options_by_exp[target_exp]["calls"]
    puts = options_by_exp[target_exp]["puts"]
    
    # Get all strikes
    all_strikes = sorted(set([c["strike"] for c in calls] + [p["strike"] for p in puts]))
    
    # Build side-by-side chain
    chain = []
    for strike in all_strikes:
        call_data = next((c for c in calls if c["strike"] == strike), None)
        put_data = next((p for p in puts if p["strike"] == strike), None)
        
        chain.append({
            "strike": strike,
            "call": {
                "instrument": call_data["instrument_name"] if call_data else None,
                "active": call_data["is_active"] if call_data else False
            },
            "put": {
                "instrument": put_data["instrument_name"] if put_data else None,
                "active": put_data["is_active"] if put_data else False
            }
        })
    
    return {
        "success": True,
        "underlying": underlying.upper(),
        "expiration": target_exp,
        "strikes_count": len(chain),
        "option_chain": chain,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_historical_volatility(currency: str = "BTC", days: int = 30) -> Dict:
    """
    Get historical volatility data using DVOL index
    
    Args:
        currency: BTC or ETH (default: BTC)
        days: Historical period (not directly used, returns current DVOL)
        
    Returns:
        Dict with volatility index data
    """
    # Deribit provides DVOL (Bitcoin Volatility Index) and ETHVOL
    index_name = f"{currency.lower()}_dvol" if currency.upper() == "BTC" else f"{currency.lower()}_vol"
    
    result = _make_request("get_index_price", {"index_name": index_name})
    
    if not result["success"]:
        # Try alternative endpoint - get volatility from ATM options
        return _estimate_volatility_from_options(currency)
    
    data = result["data"]
    
    return {
        "success": True,
        "currency": currency.upper(),
        "index": index_name,
        "volatility_index": data.get("index_price"),
        "edp": data.get("estimated_delivery_price"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "DVOL index represents 30-day implied volatility"
    }


def _estimate_volatility_from_options(currency: str) -> Dict:
    """
    Fallback method to estimate volatility from ATM options
    
    Args:
        currency: BTC or ETH
        
    Returns:
        Dict with estimated volatility
    """
    # Get book summary to access IVs
    book_summary = get_option_book_summary(currency)
    
    if not book_summary["success"] or not book_summary.get("options"):
        return {"success": False, "error": "Cannot estimate volatility - no option data"}
    
    avg_iv = book_summary.get("average_implied_volatility")
    
    return {
        "success": True,
        "currency": currency.upper(),
        "estimated_volatility": avg_iv,
        "method": "ATM_OPTIONS_IV_AVERAGE",
        "sample_size": book_summary["options_count"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_index_price(currency: str = "BTC") -> Dict:
    """
    Get current spot index price for BTC or ETH
    
    Args:
        currency: BTC or ETH (default: BTC)
        
    Returns:
        Dict with index price and timestamp
    """
    index_name = f"{currency.lower()}_usd"
    
    result = _make_request("get_index_price", {"index_name": index_name})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    return {
        "success": True,
        "currency": currency.upper(),
        "index": index_name,
        "price": data.get("index_price"),
        "estimated_delivery_price": data.get("estimated_delivery_price"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_volatility_surface(currency: str = "BTC", expirations: Optional[List[str]] = None) -> Dict:
    """
    Get implied volatility surface across strikes and expirations
    
    Args:
        currency: BTC or ETH (default: BTC)
        expirations: List of expiration dates to include (None = all active)
        
    Returns:
        Dict with IV surface data organized by expiration and strike
    """
    # Get all option book summaries
    book_summary = get_option_book_summary(currency)
    
    if not book_summary["success"]:
        return book_summary
    
    # Organize by expiration and strike
    vol_surface = defaultdict(lambda: defaultdict(dict))
    
    for option in book_summary["options"]:
        inst_name = option["instrument_name"]
        
        # Parse instrument name: BTC-28MAR26-50000-C
        parts = inst_name.split("-")
        if len(parts) != 4:
            continue
        
        exp = parts[1]
        strike = float(parts[2])
        opt_type = parts[3]
        
        # Filter by expiration if specified
        if expirations and exp not in expirations:
            continue
        
        iv = option.get("implied_volatility")
        if iv is not None:
            vol_surface[exp][strike][opt_type] = {
                "iv": iv,
                "delta": option["greeks"].get("delta"),
                "vega": option["greeks"].get("vega"),
                "volume": option.get("volume_24h", 0)
            }
    
    # Convert to regular dict for JSON serialization
    surface_data = {}
    for exp in sorted(vol_surface.keys()):
        surface_data[exp] = {}
        for strike in sorted(vol_surface[exp].keys()):
            surface_data[exp][strike] = dict(vol_surface[exp][strike])
    
    return {
        "success": True,
        "currency": currency.upper(),
        "expirations_count": len(surface_data),
        "volatility_surface": surface_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def list_all_functions() -> Dict:
    """
    List all available functions in this module
    
    Returns:
        Dict with function names and descriptions
    """
    functions = {
        "get_options_instruments": "List all option instruments with expiration summary",
        "get_option_book_summary": "Get option book summaries with Greeks",
        "get_option_chain": "Formatted option chain (calls/puts by strike)",
        "get_historical_volatility": "Historical/implied volatility metrics",
        "get_index_price": "Current spot index price",
        "get_volatility_surface": "IV surface across strikes and expirations",
        "list_all_functions": "This function - lists all available functions"
    }
    
    return {
        "success": True,
        "module": "deribit_crypto_options_api",
        "functions_count": len(functions),
        "functions": functions,
        "source": "https://docs.deribit.com/",
        "free_tier": True,
        "requires_auth": False
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Deribit Crypto Options API")
    print("=" * 60)
    
    # List functions
    funcs = list_all_functions()
    print(f"\n📋 Available Functions: {funcs['functions_count']}")
    for name, desc in funcs['functions'].items():
        print(f"  • {name}: {desc}")
    
    # Test with BTC
    print("\n\n🧪 Testing with BTC...\n")
    
    # 1. Index price
    print("1️⃣ BTC Index Price:")
    index = get_index_price("BTC")
    if index["success"]:
        print(f"   ${index['price']:,.2f}")
    else:
        print(f"   Error: {index.get('error')}")
    
    # 2. Historical volatility
    print("\n2️⃣ Historical Volatility:")
    vol = get_historical_volatility("BTC")
    if vol["success"]:
        vol_value = vol.get('volatility_index') or vol.get('estimated_volatility')
        print(f"   {vol_value:.2f}%" if vol_value else "   N/A")
    else:
        print(f"   Error: {vol.get('error')}")
    
    # 3. Options summary
    print("\n3️⃣ Options Summary:")
    summary = get_option_book_summary("BTC")
    if summary["success"]:
        print(f"   Total Options: {summary['options_count']}")
        print(f"   24h Volume: ${summary['total_volume_24h_usd']:,.0f}")
        print(f"   Open Interest: {summary['total_open_interest']:,.0f}")
        if summary['average_implied_volatility']:
            print(f"   Avg IV: {summary['average_implied_volatility']:.2f}%")
    else:
        print(f"   Error: {summary.get('error')}")
    
    print("\n✅ Module test complete")
