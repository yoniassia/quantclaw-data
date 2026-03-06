#!/usr/bin/env python3
"""
Deribit Crypto Derivatives API

Provides real-time crypto options and futures data including:
- Options chains for BTC/ETH (strikes, expirations, premiums)
- Implied volatility and Greeks (delta, gamma, vega, theta)
- Order book depth and trade history
- Index prices for BTC/ETH

Free tier: Unlimited public data access (rate limit: 10 req/sec)
Source: https://docs.deribit.com/
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "https://www.deribit.com/api/v2/public"

def get_book_summary(currency: str = "BTC", kind: str = "option") -> Dict:
    """
    Get book summary for all instruments of a given currency and kind.
    
    Args:
        currency: BTC or ETH
        kind: option or future
        
    Returns:
        Dict containing summary data for all instruments
    """
    try:
        url = f"{BASE_URL}/get_book_summary_by_currency"
        params = {"currency": currency.upper(), "kind": kind}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result"):
            return {
                "currency": currency,
                "kind": kind,
                "count": len(data["result"]),
                "instruments": data["result"],
                "timestamp": datetime.utcnow().isoformat()
            }
        return {"error": "No data returned"}
    except Exception as e:
        return {"error": str(e)}


def get_instruments(currency: str = "BTC", kind: str = "option", expired: bool = False) -> List[Dict]:
    """
    Get all available instruments for a currency.
    
    Args:
        currency: BTC or ETH
        kind: option, future, or spot
        expired: Include expired instruments
        
    Returns:
        List of instrument details
    """
    try:
        url = f"{BASE_URL}/get_instruments"
        params = {
            "currency": currency.upper(),
            "kind": kind,
            "expired": str(expired).lower()
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result"):
            instruments = []
            for inst in data["result"]:
                instruments.append({
                    "instrument_name": inst.get("instrument_name"),
                    "strike": inst.get("strike"),
                    "expiration": inst.get("expiration_timestamp"),
                    "option_type": inst.get("option_type"),
                    "min_trade_amount": inst.get("min_trade_amount"),
                    "is_active": inst.get("is_active")
                })
            return instruments
        return []
    except Exception as e:
        print(f"Error fetching instruments: {e}")
        return []


def get_ticker(instrument_name: str) -> Dict:
    """
    Get current ticker data including Greeks for a specific instrument.
    
    Args:
        instrument_name: e.g., "BTC-29MAR24-50000-C"
        
    Returns:
        Dict with price, IV, Greeks, and volume
    """
    try:
        url = f"{BASE_URL}/ticker"
        params = {"instrument_name": instrument_name}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result"):
            r = data["result"]
            return {
                "instrument": instrument_name,
                "last_price": r.get("last_price"),
                "mark_price": r.get("mark_price"),
                "bid_price": r.get("best_bid_price"),
                "ask_price": r.get("best_ask_price"),
                "implied_volatility": r.get("mark_iv"),
                "greeks": {
                    "delta": r.get("greeks", {}).get("delta"),
                    "gamma": r.get("greeks", {}).get("gamma"),
                    "vega": r.get("greeks", {}).get("vega"),
                    "theta": r.get("greeks", {}).get("theta"),
                    "rho": r.get("greeks", {}).get("rho")
                },
                "volume_24h": r.get("stats", {}).get("volume"),
                "open_interest": r.get("open_interest"),
                "timestamp": r.get("timestamp")
            }
        return {"error": "No ticker data"}
    except Exception as e:
        return {"error": str(e)}


def get_index_price(index_name: str = "btc_usd") -> Dict:
    """
    Get current index price for BTC or ETH.
    
    Args:
        index_name: btc_usd or eth_usd
        
    Returns:
        Dict with index price and timestamp
    """
    try:
        url = f"{BASE_URL}/get_index_price"
        params = {"index_name": index_name}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result"):
            return {
                "index": index_name,
                "price": data["result"].get("index_price"),
                "timestamp": data["result"].get("estimated_delivery_price")
            }
        return {"error": "No index price"}
    except Exception as e:
        return {"error": str(e)}


def get_order_book(instrument_name: str, depth: int = 5) -> Dict:
    """
    Get order book for a specific instrument.
    
    Args:
        instrument_name: e.g., "BTC-PERPETUAL"
        depth: Number of levels to fetch
        
    Returns:
        Dict with bids and asks
    """
    try:
        url = f"{BASE_URL}/get_order_book"
        params = {"instrument_name": instrument_name, "depth": depth}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result"):
            r = data["result"]
            return {
                "instrument": instrument_name,
                "bids": r.get("bids", []),
                "asks": r.get("asks", []),
                "best_bid": r.get("best_bid_price"),
                "best_ask": r.get("best_ask_price"),
                "mark_price": r.get("mark_price"),
                "timestamp": r.get("timestamp")
            }
        return {"error": "No order book data"}
    except Exception as e:
        return {"error": str(e)}


def get_atm_options(currency: str = "BTC") -> List[Dict]:
    """
    Get near-the-money options for quick analysis.
    
    Args:
        currency: BTC or ETH
        
    Returns:
        List of ATM option tickers with Greeks
    """
    try:
        # Get current index price
        index = get_index_price(f"{currency.lower()}_usd")
        if "error" in index:
            return []
        
        current_price = index["price"]
        
        # Get all options
        instruments = get_instruments(currency, "option")
        
        # Filter for ATM options (within 10% of spot)
        atm_options = []
        for inst in instruments[:20]:  # Limit to first 20 for speed
            strike = inst.get("strike")
            if strike and abs(strike - current_price) / current_price < 0.10:
                ticker = get_ticker(inst["instrument_name"])
                if "error" not in ticker:
                    atm_options.append(ticker)
        
        return atm_options
    except Exception as e:
        print(f"Error fetching ATM options: {e}")
        return []


if __name__ == "__main__":
    # Test the module
    print("=== Deribit Crypto Derivatives Test ===\n")
    
    # Test 1: Get BTC index price
    print("1. BTC Index Price:")
    btc_price = get_index_price("btc_usd")
    print(json.dumps(btc_price, indent=2))
    
    # Test 2: Get book summary
    print("\n2. BTC Options Summary:")
    summary = get_book_summary("BTC", "option")
    print(f"Total BTC options: {summary.get('count', 0)}")
    
    # Test 3: Get first 3 instruments
    print("\n3. First 3 BTC Options:")
    instruments = get_instruments("BTC", "option")
    for inst in instruments[:3]:
        print(f"  - {inst['instrument_name']}: Strike ${inst['strike']}")
    
    print("\n✅ Module test complete")
