#!/usr/bin/env python3
"""
FX Volatility Surface Module
Phase 183: Implied vol for major pairs, risk reversals, butterfly spreads

Data Sources:
- Yahoo Finance: FX spot prices for historical volatility calculation
- Synthetic IV estimation: Implied volatility estimated from historical vol with term structure
- Risk Reversals: 25-delta put/call vol spread estimation
- Butterflies: Volatility smile/skew indicators

Daily updates. No API key required.

Major FX Pairs:
- EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD
- EUR/GBP, EUR/JPY, GBP/JPY

Methodology:
Since free real-time FX options data is unavailable, we estimate implied volatility using:
1. Historical realized volatility (HV) from spot prices
2. Term structure adjustment: longer tenors = higher vol (convexity)
3. Smile/skew estimation: OTM puts trade richer (risk premium)
4. Risk Reversal = 25-delta Call IV - 25-delta Put IV
5. Butterfly = (25-delta Call IV + 25-delta Put IV) / 2 - ATM IV

Phase: 183
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import statistics


# Major FX pairs (Yahoo Finance format: XXX=X)
FX_PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X", 
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X"
}

# Standard option tenors (days to expiry)
TENORS = {
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365
}

# Delta points for risk reversal and butterfly
DELTA_POINTS = [10, 25]  # 10-delta and 25-delta


def get_fx_spot(pair: str) -> Dict:
    """
    Fetch current FX spot rate from Yahoo Finance
    
    Args:
        pair: FX pair name (e.g., 'EURUSD')
        
    Returns:
        Dict with spot rate and metadata
    """
    ticker = FX_PAIRS.get(pair.upper())
    if not ticker:
        return {"error": f"Unknown FX pair: {pair}"}
    
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {"interval": "1d", "range": "1d"}
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data["chart"]["result"][0]
        meta = result["meta"]
        
        current_price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose")
        
        change = current_price - prev_close if (current_price and prev_close) else 0
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return {
            "pair": pair.upper(),
            "ticker": ticker,
            "spot": current_price,
            "change": change,
            "change_pct": change_pct,
            "bid": current_price * 0.99995,  # Approximation
            "ask": current_price * 1.00005,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch {pair}: {str(e)}"}


def get_fx_history(pair: str, days: int = 90) -> List[Dict]:
    """
    Fetch historical FX prices
    
    Args:
        pair: FX pair name
        days: Number of days of history
        
    Returns:
        List of daily price records
    """
    ticker = FX_PAIRS.get(pair.upper())
    if not ticker:
        return []
    
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "interval": "1d",
            "range": f"{days}d"
        }
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quotes = result["indicators"]["quote"][0]
        
        history = []
        for i, ts in enumerate(timestamps):
            if quotes["close"][i] is not None:
                history.append({
                    "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    "open": quotes["open"][i],
                    "high": quotes["high"][i],
                    "low": quotes["low"][i],
                    "close": quotes["close"][i]
                })
        
        return history
        
    except Exception as e:
        print(f"Error fetching history for {pair}: {e}", file=sys.stderr)
        return []


def calculate_realized_volatility(prices: List[float], window: int = 30) -> float:
    """
    Calculate realized historical volatility (annualized)
    
    Args:
        prices: List of historical prices
        window: Rolling window for volatility calculation
        
    Returns:
        Annualized volatility as percentage
    """
    if len(prices) < window + 1:
        return 0.0
    
    # Calculate log returns
    returns = []
    for i in range(1, len(prices)):
        if prices[i] > 0 and prices[i-1] > 0:
            log_return = math.log(prices[i] / prices[i-1])
            returns.append(log_return)
    
    if len(returns) < window:
        return 0.0
    
    # Use last 'window' returns
    recent_returns = returns[-window:]
    
    # Standard deviation of returns
    std_dev = statistics.stdev(recent_returns)
    
    # Annualize (252 trading days)
    annualized_vol = std_dev * math.sqrt(252) * 100
    
    return annualized_vol


def estimate_implied_volatility(pair: str, tenor_days: int, hv_30d: float) -> Dict:
    """
    Estimate implied volatility from historical volatility with term structure adjustment
    
    Args:
        pair: FX pair name
        tenor_days: Days to expiry
        hv_30d: 30-day historical volatility
        
    Returns:
        Dict with ATM IV and smile parameters
    """
    # Base IV starts from historical vol
    base_iv = hv_30d
    
    # Term structure adjustment: longer tenors have higher vol (convexity)
    # Rule: add 0.5% per month beyond 1M
    months = tenor_days / 30
    term_adjustment = (months - 1) * 0.5 if months > 1 else 0
    
    # ATM IV
    atm_iv = base_iv + term_adjustment
    
    # Smile/skew parameters (OTM puts typically trade richer in FX)
    # Risk premium increases for longer tenors
    risk_premium = 0.5 + (months - 1) * 0.2
    
    # 25-delta put IV (OTM put, protective)
    put_25d_iv = atm_iv + risk_premium
    
    # 25-delta call IV (OTM call)
    call_25d_iv = atm_iv + (risk_premium * 0.6)
    
    # 10-delta (further OTM)
    put_10d_iv = atm_iv + risk_premium * 1.8
    call_10d_iv = atm_iv + risk_premium * 1.2
    
    # Risk Reversal (25-delta): Call IV - Put IV
    # Negative RR = puts trade richer (typical in FX)
    rr_25d = call_25d_iv - put_25d_iv
    
    # Butterfly (25-delta): Average wing IV - ATM IV
    # Measures smile convexity
    bf_25d = ((call_25d_iv + put_25d_iv) / 2) - atm_iv
    
    return {
        "pair": pair,
        "tenor_days": tenor_days,
        "atm_iv": round(atm_iv, 2),
        "call_25d_iv": round(call_25d_iv, 2),
        "put_25d_iv": round(put_25d_iv, 2),
        "call_10d_iv": round(call_10d_iv, 2),
        "put_10d_iv": round(put_10d_iv, 2),
        "risk_reversal_25d": round(rr_25d, 2),
        "butterfly_25d": round(bf_25d, 2),
        "methodology": "synthetic_estimation"
    }


def get_volatility_surface(pair: str) -> Dict:
    """
    Generate full volatility surface for an FX pair
    
    Args:
        pair: FX pair name (e.g., 'EURUSD')
        
    Returns:
        Dict with spot rate, realized vol, and IV surface across tenors
    """
    # Get current spot
    spot_data = get_fx_spot(pair)
    if "error" in spot_data:
        return spot_data
    
    # Get historical prices for realized vol calculation
    history = get_fx_history(pair, days=90)
    if not history:
        return {"error": f"No historical data for {pair}"}
    
    # Calculate realized volatilities
    prices = [h["close"] for h in history if h["close"]]
    hv_30d = calculate_realized_volatility(prices, window=30)
    hv_60d = calculate_realized_volatility(prices, window=60)
    hv_90d = calculate_realized_volatility(prices, window=90) if len(prices) >= 91 else hv_60d
    
    # Generate IV surface for all tenors
    surface = []
    for tenor_name, tenor_days in TENORS.items():
        iv_data = estimate_implied_volatility(pair, tenor_days, hv_30d)
        iv_data["tenor"] = tenor_name
        surface.append(iv_data)
    
    return {
        "pair": pair.upper(),
        "spot": spot_data["spot"],
        "change_pct": spot_data["change_pct"],
        "realized_volatility": {
            "hv_30d": round(hv_30d, 2),
            "hv_60d": round(hv_60d, 2),
            "hv_90d": round(hv_90d, 2)
        },
        "implied_volatility_surface": surface,
        "timestamp": datetime.now().isoformat(),
        "note": "IV estimates are synthetic, derived from historical volatility with term structure and smile adjustments"
    }


def get_risk_reversals(pair: str) -> Dict:
    """
    Get risk reversal indicators across tenors
    
    Args:
        pair: FX pair name
        
    Returns:
        Dict with RR values showing put/call skew
    """
    surface = get_volatility_surface(pair)
    if "error" in surface:
        return surface
    
    risk_reversals = []
    for tenor_data in surface["implied_volatility_surface"]:
        risk_reversals.append({
            "tenor": tenor_data["tenor"],
            "tenor_days": tenor_data["tenor_days"],
            "rr_25d": tenor_data["risk_reversal_25d"],
            "interpretation": "negative = puts trade richer (risk premium), positive = calls trade richer"
        })
    
    return {
        "pair": pair.upper(),
        "spot": surface["spot"],
        "risk_reversals": risk_reversals,
        "timestamp": surface["timestamp"]
    }


def get_butterflies(pair: str) -> Dict:
    """
    Get butterfly spreads showing volatility smile convexity
    
    Args:
        pair: FX pair name
        
    Returns:
        Dict with butterfly values across tenors
    """
    surface = get_volatility_surface(pair)
    if "error" in surface:
        return surface
    
    butterflies = []
    for tenor_data in surface["implied_volatility_surface"]:
        butterflies.append({
            "tenor": tenor_data["tenor"],
            "tenor_days": tenor_data["tenor_days"],
            "bf_25d": tenor_data["butterfly_25d"],
            "interpretation": "positive = wings trade richer than ATM (smile convexity)"
        })
    
    return {
        "pair": pair.upper(),
        "spot": surface["spot"],
        "butterflies": butterflies,
        "timestamp": surface["timestamp"]
    }


def get_all_pairs_summary() -> Dict:
    """
    Get volatility summary for all major FX pairs
    
    Returns:
        Dict with ATM IV and RR for all pairs
    """
    summary = []
    
    for pair in FX_PAIRS.keys():
        try:
            surface = get_volatility_surface(pair)
            if "error" not in surface:
                # Get 1M (30-day) tenor data
                tenor_1m = next((t for t in surface["implied_volatility_surface"] if t["tenor"] == "1M"), None)
                
                if tenor_1m:
                    summary.append({
                        "pair": pair,
                        "spot": surface["spot"],
                        "change_pct": surface["change_pct"],
                        "hv_30d": surface["realized_volatility"]["hv_30d"],
                        "atm_iv_1m": tenor_1m["atm_iv"],
                        "rr_25d_1m": tenor_1m["risk_reversal_25d"],
                        "bf_25d_1m": tenor_1m["butterfly_25d"]
                    })
        except Exception as e:
            print(f"Error processing {pair}: {e}", file=sys.stderr)
            continue
    
    return {
        "fx_volatility_summary": summary,
        "timestamp": datetime.now().isoformat(),
        "count": len(summary)
    }


def main():
    """CLI interface for FX volatility surface module"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FX Volatility Surface Analysis")
    parser.add_argument("command", choices=[
        "fx-vol-surface", "fx-risk-reversal", "fx-butterfly", "fx-vol-summary"
    ], help="Command to execute")
    parser.add_argument("--pair", "-p", help="FX pair (e.g., EURUSD)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    result = None
    
    if args.command == "fx-vol-surface":
        if not args.pair:
            print("Error: --pair required for fx-vol-surface command", file=sys.stderr)
            sys.exit(1)
        result = get_volatility_surface(args.pair)
    
    elif args.command == "fx-risk-reversal":
        if not args.pair:
            print("Error: --pair required for fx-risk-reversal command", file=sys.stderr)
            sys.exit(1)
        result = get_risk_reversals(args.pair)
    
    elif args.command == "fx-butterfly":
        if not args.pair:
            print("Error: --pair required for fx-butterfly command", file=sys.stderr)
            sys.exit(1)
        result = get_butterflies(args.pair)
    
    elif args.command == "fx-vol-summary":
        result = get_all_pairs_summary()
    
    if result:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            if args.command == "surface" and "implied_volatility_surface" in result:
                print(f"\n{'='*60}")
                print(f"FX VOLATILITY SURFACE: {result['pair']}")
                print(f"{'='*60}")
                print(f"Spot Rate: {result['spot']:.5f} ({result['change_pct']:+.2f}%)")
                print(f"\nRealized Volatility:")
                print(f"  30-day: {result['realized_volatility']['hv_30d']:.2f}%")
                print(f"  60-day: {result['realized_volatility']['hv_60d']:.2f}%")
                print(f"  90-day: {result['realized_volatility']['hv_90d']:.2f}%")
                print(f"\nImplied Volatility Surface:")
                print(f"{'Tenor':<10} {'ATM IV':<10} {'25d RR':<10} {'25d BF':<10}")
                print(f"{'-'*40}")
                for tenor in result['implied_volatility_surface']:
                    print(f"{tenor['tenor']:<10} {tenor['atm_iv']:<10.2f} {tenor['risk_reversal_25d']:<10.2f} {tenor['butterfly_25d']:<10.2f}")
            
            elif args.command == "summary" and "fx_volatility_summary" in result:
                print(f"\n{'='*80}")
                print(f"FX VOLATILITY SUMMARY - All Major Pairs (1M Tenor)")
                print(f"{'='*80}")
                print(f"{'Pair':<10} {'Spot':<12} {'Chg%':<8} {'HV30d':<8} {'ATM IV':<8} {'RR25d':<8} {'BF25d':<8}")
                print(f"{'-'*80}")
                for item in result['fx_volatility_summary']:
                    print(f"{item['pair']:<10} {item['spot']:<12.5f} {item['change_pct']:>7.2f} {item['hv_30d']:>7.2f} {item['atm_iv_1m']:>7.2f} {item['rr_25d_1m']:>7.2f} {item['bf_25d_1m']:>7.2f}")
            
            else:
                print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
