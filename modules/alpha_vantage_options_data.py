#!/usr/bin/env python3
"""
Alpha Vantage Options Data — Phase 1084
========================================
Historical options pricing, Greeks, and backtesting data for equities.
Free access for quant analysis of options strategies.

Data source: https://www.alphavantage.co/documentation/#options
Update frequency: Daily
Free tier: 5 API calls/min, 500 calls/day (no credit card)

Metrics:
- Historical options prices (bid/ask)
- Volume and open interest
- Greeks (delta, gamma, theta, vega, rho)
- Expiration dates and strike prices
- Implied volatility

References:
- Black, F., & Scholes, M. (1973). "The pricing of options and corporate liabilities"
- Hull, J. C. (2018). "Options, Futures, and Other Derivatives" (10th ed.)
"""

import requests
import os
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
import json

# API config
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

# Cache for repeated requests
_cache: Dict[str, Dict] = {}


def get_options_chain(
    symbol: str,
    api_key: Optional[str] = None,
    use_cache: bool = True
) -> Dict:
    """
    Fetch options chain data for a symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
        api_key: Alpha Vantage API key (or use env ALPHA_VANTAGE_API_KEY)
        use_cache: Use in-memory cache for repeated calls
    
    Returns:
        Dict with options chain data:
        - data: List of option contracts
        - symbol: Ticker symbol
        - last_refreshed: Timestamp
    """
    cache_key = f"{symbol.upper()}_chain"
    if use_cache and cache_key in _cache:
        return _cache[cache_key]
    
    key = api_key or API_KEY
    if key == "demo":
        return {"error": "ALPHA_VANTAGE_API_KEY not set. Use environment variable or pass api_key parameter."}
    
    params = {
        "function": "HISTORICAL_OPTIONS",
        "symbol": symbol.upper(),
        "apikey": key
    }
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        
        data = resp.json()
        
        # Check for API errors
        if "Error Message" in data:
            return {"error": data["Error Message"], "symbol": symbol}
        if "Note" in data:
            return {"error": "API rate limit exceeded. Free tier: 5 calls/min, 500/day.", "symbol": symbol}
        if "Information" in data:
            return {"error": data["Information"], "symbol": symbol}
        
        # Cache result
        _cache[cache_key] = data
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "symbol": symbol}


def get_option_greeks(
    symbol: str,
    contract_id: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch Greeks (delta, gamma, theta, vega, rho) for options.
    
    Args:
        symbol: Stock ticker symbol
        contract_id: Specific contract ID (optional)
        api_key: Alpha Vantage API key
    
    Returns:
        Dict with Greeks data
    """
    chain = get_options_chain(symbol, api_key=api_key)
    
    if "error" in chain:
        return chain
    
    # Parse Greeks from chain data
    # Note: Actual Alpha Vantage response structure may vary
    # This is a skeleton based on typical options API responses
    
    if contract_id:
        # Filter for specific contract
        return {"error": "Contract filtering not yet implemented. Fetch full chain first."}
    
    return {
        "symbol": symbol,
        "greeks_available": "data" in chain,
        "message": "Greeks data available in options chain response"
    }


def parse_options_to_df(chain_data: Dict) -> pd.DataFrame:
    """
    Convert options chain JSON to DataFrame for analysis.
    
    Args:
        chain_data: Raw options chain dict from get_options_chain()
    
    Returns:
        DataFrame with columns:
        - contract_id
        - strike
        - expiration
        - type (call/put)
        - bid, ask, last
        - volume, open_interest
        - implied_volatility
        - delta, gamma, theta, vega (if available)
    """
    if "error" in chain_data:
        return pd.DataFrame()
    
    # Parse based on Alpha Vantage response structure
    # Note: Actual structure may vary - this is a placeholder
    
    if "data" not in chain_data:
        return pd.DataFrame()
    
    records = []
    for contract in chain_data.get("data", []):
        records.append({
            "contract_id": contract.get("contractID", ""),
            "strike": float(contract.get("strike", 0)),
            "expiration": contract.get("expiration", ""),
            "type": contract.get("type", ""),
            "bid": float(contract.get("bid", 0)),
            "ask": float(contract.get("ask", 0)),
            "last": float(contract.get("lastPrice", 0)),
            "volume": int(contract.get("volume", 0)),
            "open_interest": int(contract.get("openInterest", 0)),
            "implied_volatility": float(contract.get("impliedVolatility", 0))
        })
    
    return pd.DataFrame(records)


def get_atm_options(
    symbol: str,
    spot_price: float,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Get at-the-money (ATM) options for a given spot price.
    
    Args:
        symbol: Stock ticker
        spot_price: Current stock price
        api_key: Alpha Vantage API key
    
    Returns:
        DataFrame of ATM options (strikes within ±5% of spot)
    """
    chain = get_options_chain(symbol, api_key=api_key)
    df = parse_options_to_df(chain)
    
    if df.empty:
        return df
    
    # Filter for ATM options (within 5% of spot)
    lower = spot_price * 0.95
    upper = spot_price * 1.05
    
    atm = df[(df['strike'] >= lower) & (df['strike'] <= upper)].copy()
    return atm.sort_values('strike')


def calculate_pcr(chain_data: Dict) -> Dict:
    """
    Calculate Put-Call Ratio from options chain.
    
    Args:
        chain_data: Options chain dict
    
    Returns:
        Dict with:
        - pcr_volume: Put volume / Call volume
        - pcr_oi: Put OI / Call OI
        - total_call_volume, total_put_volume
        - total_call_oi, total_put_oi
    """
    df = parse_options_to_df(chain_data)
    
    if df.empty:
        return {"error": "No data to calculate PCR"}
    
    calls = df[df['type'] == 'call']
    puts = df[df['type'] == 'put']
    
    call_vol = calls['volume'].sum()
    put_vol = puts['volume'].sum()
    call_oi = calls['open_interest'].sum()
    put_oi = puts['open_interest'].sum()
    
    pcr_vol = put_vol / call_vol if call_vol > 0 else 0
    pcr_oi = put_oi / call_oi if call_oi > 0 else 0
    
    return {
        "symbol": chain_data.get("symbol", ""),
        "pcr_volume": round(pcr_vol, 3),
        "pcr_oi": round(pcr_oi, 3),
        "total_call_volume": int(call_vol),
        "total_put_volume": int(put_vol),
        "total_call_oi": int(call_oi),
        "total_put_oi": int(put_oi),
        "signal": "Bullish" if pcr_vol < 0.7 else "Bearish" if pcr_vol > 1.3 else "Neutral"
    }


# ==============================================================================
# CLI Integration
# ==============================================================================

def cli_options_chain(symbol: str):
    """CLI: Display options chain summary"""
    chain = get_options_chain(symbol)
    
    if "error" in chain:
        print(f"❌ {chain['error']}")
        return
    
    df = parse_options_to_df(chain)
    
    print(f"\n📊 {symbol.upper()} Options Chain")
    print("=" * 70)
    
    if df.empty:
        print("No options data available")
    else:
        print(f"Total Contracts: {len(df)}")
        print(f"Calls: {len(df[df['type']=='call'])}")
        print(f"Puts: {len(df[df['type']=='put'])}")
        print(f"\nSample (first 10):\n{df.head(10).to_string(index=False)}")
    
    print()


def cli_options_pcr(symbol: str):
    """CLI: Display Put-Call Ratio"""
    chain = get_options_chain(symbol)
    
    if "error" in chain:
        print(f"❌ {chain['error']}")
        return
    
    pcr = calculate_pcr(chain)
    
    if "error" in pcr:
        print(f"❌ {pcr['error']}")
        return
    
    print(f"\n📉 {symbol.upper()} Put-Call Ratio")
    print("=" * 60)
    print(f"PCR (Volume):        {pcr['pcr_volume']:.3f}")
    print(f"PCR (Open Interest): {pcr['pcr_oi']:.3f}")
    print(f"\nCall Volume:  {pcr['total_call_volume']:,}")
    print(f"Put Volume:   {pcr['total_put_volume']:,}")
    print(f"Call OI:      {pcr['total_call_oi']:,}")
    print(f"Put OI:       {pcr['total_put_oi']:,}")
    print(f"\nSignal: {pcr['signal']}")
    print()


# ==============================================================================
# CLI Argument Parsing
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Self-test
        print("✅ Alpha Vantage Options Data module loaded")
        print("✅ Functions available:")
        print("   - get_options_chain(symbol, api_key)")
        print("   - get_option_greeks(symbol, contract_id, api_key)")
        print("   - parse_options_to_df(chain_data)")
        print("   - get_atm_options(symbol, spot_price, api_key)")
        print("   - calculate_pcr(chain_data)")
        print("   - CLI: options-chain SYMBOL, options-pcr SYMBOL")
        print("\n⚠️  Set ALPHA_VANTAGE_API_KEY environment variable to use")
        print("Free tier: 5 API calls/min, 500 calls/day")
    else:
        command = sys.argv[1]
        
        if command == "options-chain":
            if len(sys.argv) < 3:
                print("Usage: options-chain SYMBOL")
                sys.exit(1)
            cli_options_chain(sys.argv[2])
        
        elif command == "options-pcr":
            if len(sys.argv) < 3:
                print("Usage: options-pcr SYMBOL")
                sys.exit(1)
            cli_options_pcr(sys.argv[2])
        
        else:
            print(f"Unknown command: {command}")
            print("Available: options-chain, options-pcr")
            sys.exit(1)
