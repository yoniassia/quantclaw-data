#!/usr/bin/env python3
"""
Crypto Derivatives Module — Perpetual Funding Rates, Futures Basis, Open Interest

Data Sources:
- CoinGlass API: Funding rates, open interest, liquidations (free tier)
- Binance API: Futures funding rates, basis, open interest (free)
- Coingecko API: Spot prices for basis calculation (free tier)
- Bybit API: Funding rates for perpetuals (free)

Features:
- Track perpetual funding rates across major exchanges
- Calculate futures basis (futures price - spot price)
- Monitor open interest changes as market sentiment indicator
- Detect funding rate arbitrage opportunities
- Liquidation cascades and risk monitoring

Author: QUANTCLAW DATA Build Agent
Phase: 188
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import sys
from collections import defaultdict
import statistics

# API Configuration
COINGLASS_BASE_URL = "https://open-api.coinglass.com/public/v2"
BINANCE_BASE_URL = "https://fapi.binance.com/fapi/v1"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
BYBIT_BASE_URL = "https://api.bybit.com/v5"

# Popular perpetual contracts
POPULAR_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "MATIC", "DOT", "DOGE"]

# Exchange mapping for CoinGlass
EXCHANGES = ["Binance", "OKX", "Bybit", "Bitget", "Gate", "dYdX"]


def get_funding_rates(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Fetch current funding rates across multiple exchanges
    Returns funding rates as annualized percentages
    """
    try:
        # Try CoinGlass first (aggregated data)
        # Note: CoinGlass free tier may be limited, fallback to individual exchanges
        
        # Method 1: Binance (most reliable free API)
        binance_funding = _get_binance_funding_rate(symbol)
        
        # Method 2: Bybit
        bybit_funding = _get_bybit_funding_rate(symbol)
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "exchanges": {},
            "average_funding_rate": None,
            "max_funding_rate": None,
            "min_funding_rate": None,
            "spread": None,  # Max - Min (arbitrage opportunity)
        }
        
        # Collect rates
        rates = []
        
        if binance_funding and "rate" in binance_funding:
            result["exchanges"]["Binance"] = binance_funding
            rates.append(binance_funding["rate"])
        
        if bybit_funding and "rate" in bybit_funding:
            result["exchanges"]["Bybit"] = bybit_funding
            rates.append(bybit_funding["rate"])
        
        # Calculate statistics
        if rates:
            result["average_funding_rate"] = statistics.mean(rates)
            result["max_funding_rate"] = max(rates)
            result["min_funding_rate"] = min(rates)
            result["spread"] = max(rates) - min(rates)
        
        return result
    
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _get_binance_funding_rate(symbol: str) -> Dict[str, Any]:
    """Fetch funding rate from Binance"""
    try:
        # Get current funding rate
        url = f"{BINANCE_BASE_URL}/premiumIndex"
        params = {"symbol": f"{symbol}USDT"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Funding rate is 8-hour rate, annualize it
        funding_rate_8h = float(data.get("lastFundingRate", 0))
        funding_rate_annual = funding_rate_8h * 3 * 365 * 100  # Convert to annual %
        
        return {
            "rate": funding_rate_annual,
            "rate_8h": funding_rate_8h * 100,  # 8-hour rate as %
            "next_funding_time": datetime.fromtimestamp(int(data.get("nextFundingTime", 0)) / 1000).isoformat(),
            "mark_price": float(data.get("markPrice", 0)),
            "index_price": float(data.get("indexPrice", 0)),
        }
    
    except Exception as e:
        return {"error": str(e)}


def _get_bybit_funding_rate(symbol: str) -> Dict[str, Any]:
    """Fetch funding rate from Bybit"""
    try:
        url = f"{BYBIT_BASE_URL}/market/tickers"
        params = {
            "category": "linear",
            "symbol": f"{symbol}USDT",
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("retCode") == 0 and data.get("result", {}).get("list"):
            ticker = data["result"]["list"][0]
            funding_rate_8h = float(ticker.get("fundingRate", 0))
            funding_rate_annual = funding_rate_8h * 3 * 365 * 100
            
            return {
                "rate": funding_rate_annual,
                "rate_8h": funding_rate_8h * 100,
                "mark_price": float(ticker.get("markPrice", 0)),
                "index_price": float(ticker.get("indexPrice", 0)),
            }
        
        return {"error": "No data available"}
    
    except Exception as e:
        return {"error": str(e)}


def get_futures_basis(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Calculate futures basis = (Futures Price - Spot Price) / Spot Price
    Positive basis = contango (bullish), negative = backwardation (bearish)
    """
    try:
        # Get spot price from CoinGecko
        spot_price = _get_spot_price(symbol)
        
        # Get futures price from Binance
        futures_price = _get_futures_price(symbol)
        
        if not spot_price or not futures_price:
            return {"error": "Failed to fetch prices"}
        
        # Calculate basis
        basis_absolute = futures_price - spot_price
        basis_percent = (basis_absolute / spot_price) * 100
        
        # Annualize basis (assuming quarterly futures)
        # For perpetuals, we use mark price vs index price
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "spot_price": spot_price,
            "futures_price": futures_price,
            "basis_absolute": basis_absolute,
            "basis_percent": basis_percent,
            "market_structure": "contango" if basis_percent > 0 else "backwardation",
            "interpretation": _interpret_basis(basis_percent),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _get_spot_price(symbol: str) -> Optional[float]:
    """Fetch spot price from Binance spot market (more reliable than CoinGecko)"""
    try:
        # Use Binance spot price instead of CoinGecko
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": f"{symbol}USDT"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return float(data.get("price", 0))
    
    except Exception:
        # Fallback to CoinGecko if Binance fails
        try:
            coin_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "BNB": "binancecoin",
                "XRP": "ripple",
                "ADA": "cardano",
                "AVAX": "avalanche-2",
                "MATIC": "matic-network",
                "DOT": "polkadot",
                "DOGE": "dogecoin",
            }
            
            coin_id = coin_map.get(symbol, symbol.lower())
            
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get(coin_id, {}).get("usd")
        
        except Exception:
            return None


def _get_futures_price(symbol: str) -> Optional[float]:
    """Fetch futures mark price from Binance"""
    try:
        url = f"{BINANCE_BASE_URL}/premiumIndex"
        params = {"symbol": f"{symbol}USDT"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return float(data.get("markPrice", 0))
    
    except Exception:
        return None


def _interpret_basis(basis_percent: float) -> str:
    """Interpret what the basis means for market sentiment"""
    if basis_percent > 5:
        return "Strong contango - Very bullish sentiment, high carry cost"
    elif basis_percent > 1:
        return "Moderate contango - Bullish sentiment"
    elif basis_percent > -1:
        return "Flat - Neutral market"
    elif basis_percent > -5:
        return "Moderate backwardation - Bearish sentiment"
    else:
        return "Strong backwardation - Very bearish, potential delivery squeeze"


def get_open_interest(symbol: str = "BTC", exchanges: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch open interest data across exchanges
    Rising OI + rising price = bullish, Rising OI + falling price = bearish
    """
    try:
        if not exchanges:
            exchanges = ["Binance"]
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "exchanges": {},
            "total_oi_usd": 0,
        }
        
        # Binance open interest
        binance_oi = _get_binance_open_interest(symbol)
        if binance_oi:
            result["exchanges"]["Binance"] = binance_oi
            result["total_oi_usd"] += binance_oi.get("open_interest_usd", 0)
        
        return result
    
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _get_binance_open_interest(symbol: str) -> Dict[str, Any]:
    """Fetch open interest from Binance"""
    try:
        url = f"{BINANCE_BASE_URL}/openInterest"
        params = {"symbol": f"{symbol}USDT"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get mark price for USD value
        mark_price = _get_futures_price(symbol) or 0
        
        oi_contracts = float(data.get("openInterest", 0))
        oi_usd = oi_contracts * mark_price
        
        return {
            "open_interest_contracts": oi_contracts,
            "open_interest_usd": oi_usd,
            "timestamp": datetime.fromtimestamp(int(data.get("time", 0)) / 1000).isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def scan_funding_arbitrage(min_spread: float = 0.5) -> List[Dict[str, Any]]:
    """
    Scan for funding rate arbitrage opportunities
    min_spread: minimum annual % spread to flag (default 0.5%)
    """
    opportunities = []
    
    for symbol in POPULAR_SYMBOLS:
        try:
            funding_data = get_funding_rates(symbol)
            
            if "spread" in funding_data and funding_data["spread"]:
                if funding_data["spread"] >= min_spread:
                    opportunities.append({
                        "symbol": symbol,
                        "spread": funding_data["spread"],
                        "max_rate": funding_data["max_funding_rate"],
                        "min_rate": funding_data["min_funding_rate"],
                        "average_rate": funding_data["average_funding_rate"],
                        "potential_annual_return": funding_data["spread"],
                    })
        
        except Exception as e:
            continue
    
    # Sort by spread descending
    opportunities.sort(key=lambda x: x["spread"], reverse=True)
    
    return opportunities


def get_market_snapshot(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get comprehensive derivatives market snapshot
    Includes funding rates, basis, open interest for multiple symbols
    """
    if not symbols:
        symbols = ["BTC", "ETH", "SOL"]
    
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "markets": {},
        "summary": {
            "average_funding_rate": None,
            "total_oi_usd": 0,
            "contango_count": 0,
            "backwardation_count": 0,
        }
    }
    
    funding_rates = []
    
    for symbol in symbols:
        try:
            market_data = {
                "funding": get_funding_rates(symbol),
                "basis": get_futures_basis(symbol),
                "open_interest": get_open_interest(symbol),
            }
            
            snapshot["markets"][symbol] = market_data
            
            # Collect for summary
            if "average_funding_rate" in market_data["funding"]:
                funding_rates.append(market_data["funding"]["average_funding_rate"])
            
            if "total_oi_usd" in market_data["open_interest"]:
                snapshot["summary"]["total_oi_usd"] += market_data["open_interest"]["total_oi_usd"]
            
            if "market_structure" in market_data["basis"]:
                if market_data["basis"]["market_structure"] == "contango":
                    snapshot["summary"]["contango_count"] += 1
                else:
                    snapshot["summary"]["backwardation_count"] += 1
        
        except Exception as e:
            snapshot["markets"][symbol] = {"error": str(e)}
    
    # Calculate summary stats
    if funding_rates:
        snapshot["summary"]["average_funding_rate"] = statistics.mean(funding_rates)
    
    return snapshot


def format_funding_rates(data: Dict[str, Any]) -> str:
    """Format funding rates for CLI output"""
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    output = [f"\n{'='*60}"]
    output.append(f"💰 FUNDING RATES: {data['symbol']}")
    output.append(f"{'='*60}")
    output.append(f"Timestamp: {data['timestamp']}")
    output.append("")
    
    if data.get("exchanges"):
        output.append("📊 Exchange Rates:")
        for exchange, rate_data in data["exchanges"].items():
            if "error" not in rate_data:
                output.append(f"  {exchange}:")
                output.append(f"    Annual Rate: {rate_data['rate']:.2f}%")
                output.append(f"    8-Hour Rate: {rate_data['rate_8h']:.4f}%")
                if "next_funding_time" in rate_data:
                    output.append(f"    Next Funding: {rate_data['next_funding_time']}")
        output.append("")
    
    if data.get("average_funding_rate") is not None:
        output.append(f"📈 Average Rate: {data['average_funding_rate']:.2f}% annual")
        output.append(f"📊 Spread: {data.get('spread', 0):.2f}% (arb opportunity)")
        
        # Interpretation
        avg_rate = data['average_funding_rate']
        if avg_rate > 20:
            interp = "🔥 VERY BULLISH - High funding, longs paying shorts"
        elif avg_rate > 10:
            interp = "📈 Bullish - Positive funding"
        elif avg_rate > -10:
            interp = "⚖️ Neutral - Balanced market"
        elif avg_rate > -20:
            interp = "📉 Bearish - Negative funding"
        else:
            interp = "🧊 VERY BEARISH - Shorts paying longs"
        
        output.append(f"\n{interp}")
    
    return "\n".join(output)


def format_futures_basis(data: Dict[str, Any]) -> str:
    """Format futures basis for CLI output"""
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    output = [f"\n{'='*60}"]
    output.append(f"📊 FUTURES BASIS: {data['symbol']}")
    output.append(f"{'='*60}")
    output.append(f"Timestamp: {data['timestamp']}")
    output.append("")
    output.append(f"Spot Price:    ${data['spot_price']:,.2f}")
    output.append(f"Futures Price: ${data['futures_price']:,.2f}")
    output.append("")
    output.append(f"Basis (Absolute): ${data['basis_absolute']:,.2f}")
    output.append(f"Basis (Percent):  {data['basis_percent']:.2f}%")
    output.append("")
    output.append(f"Market Structure: {data['market_structure'].upper()}")
    output.append(f"Interpretation:   {data['interpretation']}")
    
    return "\n".join(output)


def format_open_interest(data: Dict[str, Any]) -> str:
    """Format open interest for CLI output"""
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    output = [f"\n{'='*60}"]
    output.append(f"🎯 OPEN INTEREST: {data['symbol']}")
    output.append(f"{'='*60}")
    output.append(f"Timestamp: {data['timestamp']}")
    output.append("")
    
    if data.get("exchanges"):
        for exchange, oi_data in data["exchanges"].items():
            if "error" not in oi_data:
                output.append(f"{exchange}:")
                output.append(f"  Contracts: {oi_data['open_interest_contracts']:,.2f}")
                output.append(f"  USD Value: ${oi_data['open_interest_usd']:,.0f}")
                output.append("")
    
    output.append(f"Total OI: ${data['total_oi_usd']:,.0f}")
    
    return "\n".join(output)


def format_market_snapshot(data: Dict[str, Any]) -> str:
    """Format market snapshot for CLI output"""
    output = [f"\n{'='*70}"]
    output.append("🌐 CRYPTO DERIVATIVES MARKET SNAPSHOT")
    output.append(f"{'='*70}")
    output.append(f"Timestamp: {data['timestamp']}")
    output.append("")
    
    # Summary
    summary = data["summary"]
    output.append("📊 MARKET SUMMARY:")
    if summary.get("average_funding_rate") is not None:
        output.append(f"  Average Funding Rate: {summary['average_funding_rate']:.2f}% annual")
    output.append(f"  Total Open Interest:  ${summary['total_oi_usd']:,.0f}")
    output.append(f"  Contango Markets:     {summary['contango_count']}")
    output.append(f"  Backwardation Markets: {summary['backwardation_count']}")
    output.append("")
    
    # Individual markets
    for symbol, market_data in data["markets"].items():
        if "error" in market_data:
            output.append(f"{symbol}: ❌ {market_data['error']}")
            continue
        
        output.append(f"{'─'*70}")
        output.append(f"💎 {symbol}")
        output.append(f"{'─'*70}")
        
        # Funding
        if "funding" in market_data and "average_funding_rate" in market_data["funding"]:
            output.append(f"  Funding Rate: {market_data['funding']['average_funding_rate']:.2f}% annual")
        
        # Basis
        if "basis" in market_data and "basis_percent" in market_data["basis"]:
            basis = market_data["basis"]
            output.append(f"  Basis: {basis['basis_percent']:.2f}% ({basis['market_structure']})")
        
        # OI
        if "open_interest" in market_data and "total_oi_usd" in market_data["open_interest"]:
            output.append(f"  Open Interest: ${market_data['open_interest']['total_oi_usd']:,.0f}")
        
        output.append("")
    
    return "\n".join(output)


# CLI Entry Points
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crypto_derivatives.py <command> [args]")
        print("Commands: funding, basis, oi, arb-scan, snapshot")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "funding":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTC"
        result = get_funding_rates(symbol)
        print(format_funding_rates(result))
    
    elif command == "basis":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTC"
        result = get_futures_basis(symbol)
        print(format_futures_basis(result))
    
    elif command == "oi":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTC"
        result = get_open_interest(symbol)
        print(format_open_interest(result))
    
    elif command == "arb-scan":
        min_spread = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
        opportunities = scan_funding_arbitrage(min_spread)
        print(f"\n🎯 FUNDING RATE ARBITRAGE OPPORTUNITIES (min spread: {min_spread}%)")
        print("="*70)
        if opportunities:
            for opp in opportunities:
                print(f"{opp['symbol']:6s} | Spread: {opp['spread']:6.2f}% | Avg: {opp['average_rate']:7.2f}%")
        else:
            print("No opportunities found above threshold.")
    
    elif command == "snapshot":
        symbols = sys.argv[2:] if len(sys.argv) > 2 else ["BTC", "ETH", "SOL"]
        result = get_market_snapshot(symbols)
        print(format_market_snapshot(result))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
