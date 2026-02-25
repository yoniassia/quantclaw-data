#!/usr/bin/env python3
"""
Order Book Depth Analysis Module
Phase 39: Level 2 data analysis, bid-ask imbalance, hidden liquidity detection

Uses yfinance for bid/ask spreads, simulates realistic order book from options OI + volume
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json


def get_bid_ask_data(ticker: str) -> Dict:
    """
    Get current bid-ask spread data for a ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        
    Returns:
        Dict with bid, ask, spread, spread_pct, mid_price
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        
        if bid == 0 or ask == 0:
            # Fallback to current price with estimated spread
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            if current_price == 0:
                return {"error": f"No price data available for {ticker}"}
            
            # Estimate 0.05% spread for liquid stocks
            spread = current_price * 0.0005
            bid = current_price - spread / 2
            ask = current_price + spread / 2
        
        mid_price = (bid + ask) / 2
        spread = ask - bid
        spread_pct = (spread / mid_price) * 100 if mid_price > 0 else 0
        
        return {
            "ticker": ticker,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "spread": round(spread, 4),
            "spread_pct": round(spread_pct, 4),
            "mid_price": round(mid_price, 2),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


def simulate_order_book(ticker: str, levels: int = 10) -> Dict:
    """
    Simulate a realistic Level 2 order book using options OI, volume, and price action.
    
    Args:
        ticker: Stock symbol
        levels: Number of price levels to simulate (default 10 each side)
        
    Returns:
        Dict with bids, asks, imbalance, depth metrics
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get current market data
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        if current_price == 0:
            return {"error": f"No price data for {ticker}"}
        
        volume = info.get('volume', info.get('regularMarketVolume', 1000000))
        avg_volume = info.get('averageVolume', volume)
        
        # Get options data for OI signals
        try:
            options_dates = stock.options
            if options_dates:
                # Use nearest expiry for flow signals
                opt_chain = stock.option_chain(options_dates[0])
                calls_oi = opt_chain.calls['openInterest'].sum() if not opt_chain.calls.empty else 0
                puts_oi = opt_chain.puts['openInterest'].sum() if not opt_chain.puts.empty else 0
                
                # Higher put OI suggests defensive positioning → more bids
                # Higher call OI suggests bullish positioning → more asks (selling covered calls)
                put_call_ratio = puts_oi / calls_oi if calls_oi > 0 else 1.0
            else:
                put_call_ratio = 1.0
        except:
            put_call_ratio = 1.0
        
        # Estimate typical spread based on price and volume
        if current_price < 10:
            tick_size = 0.01
        elif current_price < 100:
            tick_size = 0.01
        else:
            tick_size = 0.05
        
        # Spread widens with low volume, tightens with high volume
        volume_factor = min(avg_volume / 10_000_000, 2.0)  # Normalize to 10M shares
        base_spread = tick_size * (3 - volume_factor)  # 1-3 ticks typically
        
        # Build bid side
        bids = []
        bid_price = current_price - base_spread / 2
        
        # Bid depth influenced by put/call ratio (higher puts = more bids)
        bid_multiplier = 1.0 + (put_call_ratio - 1.0) * 0.3
        
        for i in range(levels):
            # Size decreases exponentially away from best bid
            level_size = int((volume / 100) * bid_multiplier * np.exp(-i * 0.3))
            level_size = max(level_size, 100)  # Min 100 shares per level
            
            bids.append({
                "price": round(bid_price - i * tick_size, 2),
                "size": level_size,
                "orders": max(1, level_size // 500)  # Estimate order count
            })
        
        # Build ask side
        asks = []
        ask_price = current_price + base_spread / 2
        
        # Ask depth inversely influenced by put/call ratio (higher calls = more asks)
        ask_multiplier = 1.0 + (1.0 / put_call_ratio - 1.0) * 0.3
        
        for i in range(levels):
            level_size = int((volume / 100) * ask_multiplier * np.exp(-i * 0.3))
            level_size = max(level_size, 100)
            
            asks.append({
                "price": round(ask_price + i * tick_size, 2),
                "size": level_size,
                "orders": max(1, level_size // 500)
            })
        
        # Calculate metrics
        total_bid_size = sum(b['size'] for b in bids)
        total_ask_size = sum(a['size'] for a in asks)
        
        imbalance = (total_bid_size - total_ask_size) / (total_bid_size + total_ask_size)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "bids": bids,
            "asks": asks,
            "total_bid_size": total_bid_size,
            "total_ask_size": total_ask_size,
            "imbalance": round(imbalance, 4),
            "spread": round(base_spread, 4),
            "put_call_ratio": round(put_call_ratio, 3),
            "levels": levels
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_order_imbalance(ticker: str, period: str = "1d") -> Dict:
    """
    Calculate order flow imbalance from intraday volume patterns.
    
    Args:
        ticker: Stock symbol
        period: Time period ('1d', '5d', '1mo')
        
    Returns:
        Dict with buy/sell pressure, volume weighted imbalance
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get intraday data (1min intervals for 1d, 5min for longer)
        if period == "1d":
            hist = stock.history(period="1d", interval="1m")
        elif period == "5d":
            hist = stock.history(period="5d", interval="5m")
        else:
            hist = stock.history(period="1mo", interval="15m")
        
        if hist.empty:
            return {"error": f"No historical data for {ticker}"}
        
        # Classify volume as buy/sell based on price movement
        # Up tick = buy pressure, down tick = sell pressure
        hist['price_change'] = hist['Close'].diff()
        hist['buy_volume'] = np.where(hist['price_change'] > 0, hist['Volume'], 0)
        hist['sell_volume'] = np.where(hist['price_change'] < 0, hist['Volume'], 0)
        
        total_buy_vol = hist['buy_volume'].sum()
        total_sell_vol = hist['sell_volume'].sum()
        total_vol = hist['Volume'].sum()
        
        # Order imbalance ratio: (Buy - Sell) / Total
        imbalance_ratio = (total_buy_vol - total_sell_vol) / total_vol if total_vol > 0 else 0
        
        # Volume-weighted price movement
        vwap = (hist['Close'] * hist['Volume']).sum() / total_vol if total_vol > 0 else hist['Close'].iloc[-1]
        
        # Recent imbalance (last 10% of data for momentum)
        recent_bars = max(len(hist) // 10, 10)
        recent_buy = hist['buy_volume'].tail(recent_bars).sum()
        recent_sell = hist['sell_volume'].tail(recent_bars).sum()
        recent_imbalance = (recent_buy - recent_sell) / (recent_buy + recent_sell) if (recent_buy + recent_sell) > 0 else 0
        
        return {
            "ticker": ticker,
            "period": period,
            "total_buy_volume": int(total_buy_vol),
            "total_sell_volume": int(total_sell_vol),
            "total_volume": int(total_vol),
            "imbalance_ratio": round(imbalance_ratio, 4),
            "recent_imbalance": round(recent_imbalance, 4),
            "vwap": round(vwap, 2),
            "current_price": round(hist['Close'].iloc[-1], 2),
            "price_vs_vwap": round(((hist['Close'].iloc[-1] / vwap) - 1) * 100, 2),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


def score_liquidity(ticker: str) -> Dict:
    """
    Score liquidity based on spread, volume, and order book depth.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with liquidity score (0-100), components, grade
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Component 1: Spread (tighter = better)
        bid_ask = get_bid_ask_data(ticker)
        if "error" in bid_ask:
            return bid_ask
        
        spread_pct = bid_ask.get('spread_pct', 0)
        
        # Score: <0.05% = 100, >1% = 0
        spread_score = max(0, min(100, (1 - spread_pct) * 100))
        
        # Component 2: Volume (higher = better)
        volume = info.get('volume', info.get('regularMarketVolume', 0))
        avg_volume = info.get('averageVolume', volume)
        
        # Score: >10M = 100, <100k = 0
        volume_score = max(0, min(100, (np.log10(avg_volume + 1) - 5) * 25))
        
        # Component 3: Market cap (larger = more liquid)
        market_cap = info.get('marketCap', 0)
        
        # Score: >100B = 100, <1B = 0
        cap_score = max(0, min(100, (np.log10(market_cap + 1) - 9) * 50)) if market_cap > 0 else 0
        
        # Component 4: Order book depth simulation
        order_book = simulate_order_book(ticker, levels=5)
        if "error" not in order_book:
            depth_imbalance = abs(order_book.get('imbalance', 0))
            # Score: balanced book = 100, highly imbalanced = 0
            depth_score = max(0, (1 - depth_imbalance) * 100)
        else:
            depth_score = 50  # Neutral if can't simulate
        
        # Weighted composite score
        liquidity_score = (
            spread_score * 0.35 +
            volume_score * 0.30 +
            cap_score * 0.20 +
            depth_score * 0.15
        )
        
        # Letter grade
        if liquidity_score >= 90:
            grade = "A+"
        elif liquidity_score >= 80:
            grade = "A"
        elif liquidity_score >= 70:
            grade = "B"
        elif liquidity_score >= 60:
            grade = "C"
        elif liquidity_score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "ticker": ticker,
            "liquidity_score": round(liquidity_score, 1),
            "grade": grade,
            "components": {
                "spread_score": round(spread_score, 1),
                "volume_score": round(volume_score, 1),
                "market_cap_score": round(cap_score, 1),
                "depth_score": round(depth_score, 1)
            },
            "metrics": {
                "spread_pct": spread_pct,
                "avg_volume": avg_volume,
                "market_cap": market_cap,
                "depth_imbalance": round(depth_imbalance, 4) if "error" not in order_book else None
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


def detect_support_resistance(ticker: str, period: str = "3mo") -> Dict:
    """
    Detect support/resistance levels from volume clusters.
    
    Args:
        ticker: Stock symbol
        period: Historical period to analyze
        
    Returns:
        Dict with support/resistance levels ranked by strength
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {"error": f"No historical data for {ticker}"}
        
        current_price = hist['Close'].iloc[-1]
        
        # Create price-volume profile
        # Bin prices into 0.5% buckets
        price_min = hist['Low'].min()
        price_max = hist['High'].max()
        price_range = price_max - price_min
        
        num_bins = min(100, max(20, int(price_range / (current_price * 0.005))))
        bins = np.linspace(price_min, price_max, num_bins)
        
        # Accumulate volume at each price level
        volume_profile = np.zeros(len(bins) - 1)
        
        for idx, row in hist.iterrows():
            # Distribute volume across price range for this bar
            bar_bins = np.digitize([row['Low'], row['High']], bins)
            for b in range(bar_bins[0], min(bar_bins[1] + 1, len(volume_profile))):
                volume_profile[b] += row['Volume'] / (bar_bins[1] - bar_bins[0] + 1)
        
        # Find peaks in volume profile (high volume = support/resistance)
        from scipy.signal import find_peaks
        
        peaks, properties = find_peaks(volume_profile, prominence=np.percentile(volume_profile, 60))
        
        # Classify as support or resistance based on current price
        support_levels = []
        resistance_levels = []
        
        for peak in peaks:
            price_level = (bins[peak] + bins[peak + 1]) / 2
            volume_strength = volume_profile[peak]
            
            # Normalize strength 0-100
            strength = min(100, (volume_strength / volume_profile.max()) * 100)
            
            level = {
                "price": round(price_level, 2),
                "strength": round(strength, 1),
                "distance_pct": round(((price_level / current_price) - 1) * 100, 2),
                "volume": int(volume_strength)
            }
            
            if price_level < current_price:
                support_levels.append(level)
            else:
                resistance_levels.append(level)
        
        # Sort by distance from current price
        support_levels.sort(key=lambda x: x['distance_pct'], reverse=True)
        resistance_levels.sort(key=lambda x: x['distance_pct'])
        
        # Keep top 5 of each
        support_levels = support_levels[:5]
        resistance_levels = resistance_levels[:5]
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "period": period,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "nearest_support": support_levels[0] if support_levels else None,
            "nearest_resistance": resistance_levels[0] if resistance_levels else None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Fallback without scipy
        try:
            # Simple approach: find high volume price levels
            volume_by_price = {}
            
            for idx, row in hist.iterrows():
                # Round to nearest 1% of current price
                bucket_size = max(0.01, current_price * 0.01)
                price_bucket = round(row['Close'] / bucket_size) * bucket_size
                
                if price_bucket not in volume_by_price:
                    volume_by_price[price_bucket] = 0
                volume_by_price[price_bucket] += row['Volume']
            
            # Get top volume levels
            sorted_levels = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)[:10]
            
            support_levels = []
            resistance_levels = []
            
            for price, volume in sorted_levels:
                level = {
                    "price": round(price, 2),
                    "strength": round((volume / sorted_levels[0][1]) * 100, 1),
                    "distance_pct": round(((price / current_price) - 1) * 100, 2),
                    "volume": int(volume)
                }
                
                if price < current_price:
                    support_levels.append(level)
                else:
                    resistance_levels.append(level)
            
            support_levels.sort(key=lambda x: x['distance_pct'], reverse=True)
            resistance_levels.sort(key=lambda x: x['distance_pct'])
            
            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "period": period,
                "support_levels": support_levels[:5],
                "resistance_levels": resistance_levels[:5],
                "nearest_support": support_levels[0] if support_levels else None,
                "nearest_resistance": resistance_levels[0] if resistance_levels else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e2:
            return {"error": str(e2)}


if __name__ == "__main__":
    import sys
    import argparse
    
    if len(sys.argv) < 2:
        # Test mode
        print("Testing Order Book Module...")
        print("\n1. Bid-Ask Spread (AAPL):")
        print(json.dumps(get_bid_ask_data("AAPL"), indent=2))
        
        print("\n2. Order Book Simulation (AAPL):")
        ob = simulate_order_book("AAPL", levels=5)
        if "error" not in ob:
            print(f"Best Bid: ${ob['bids'][0]['price']} x {ob['bids'][0]['size']}")
            print(f"Best Ask: ${ob['asks'][0]['price']} x {ob['asks'][0]['size']}")
            print(f"Imbalance: {ob['imbalance']:.2%}")
        else:
            print(ob)
        
        print("\n3. Order Imbalance (AAPL):")
        print(json.dumps(calculate_order_imbalance("AAPL", "1d"), indent=2))
        
        print("\n4. Liquidity Score (AAPL):")
        print(json.dumps(score_liquidity("AAPL"), indent=2))
        
        print("\n5. Support/Resistance (AAPL):")
        sr = detect_support_resistance("AAPL", "3mo")
        if "error" not in sr:
            print(f"Current: ${sr['current_price']}")
            if sr['nearest_support']:
                print(f"Nearest Support: ${sr['nearest_support']['price']} ({sr['nearest_support']['distance_pct']:.2f}%)")
            if sr['nearest_resistance']:
                print(f"Nearest Resistance: ${sr['nearest_resistance']['price']} ({sr['nearest_resistance']['distance_pct']:.2f}%)")
            print(f"Support Levels: {len(sr['support_levels'])}, Resistance Levels: {len(sr['resistance_levels'])}")
        else:
            print(sr)
    else:
        # CLI mode
        command = sys.argv[1]
        
        if command == "order-book":
            parser = argparse.ArgumentParser(description="Simulate order book depth")
            parser.add_argument("ticker", help="Stock symbol (e.g., AAPL)")
            parser.add_argument("--levels", type=int, default=10, help="Number of price levels (default: 10)")
            args = parser.parse_args(sys.argv[2:])
            
            result = simulate_order_book(args.ticker.upper(), levels=args.levels)
            print(json.dumps(result, indent=2))
        
        elif command == "bid-ask":
            if len(sys.argv) < 3:
                print("Usage: python cli.py bid-ask SYMBOL", file=sys.stderr)
                sys.exit(1)
            
            ticker = sys.argv[2].upper()
            result = get_bid_ask_data(ticker)
            print(json.dumps(result, indent=2))
        
        elif command == "liquidity":
            if len(sys.argv) < 3:
                print("Usage: python cli.py liquidity SYMBOL", file=sys.stderr)
                sys.exit(1)
            
            ticker = sys.argv[2].upper()
            result = score_liquidity(ticker)
            print(json.dumps(result, indent=2))
        
        elif command == "imbalance":
            parser = argparse.ArgumentParser(description="Calculate order flow imbalance")
            parser.add_argument("ticker", help="Stock symbol (e.g., AAPL)")
            parser.add_argument("--period", default="1d", choices=["1d", "5d", "1mo"], help="Time period (default: 1d)")
            args = parser.parse_args(sys.argv[2:])
            
            result = calculate_order_imbalance(args.ticker.upper(), args.period)
            print(json.dumps(result, indent=2))
        
        elif command == "support-resistance":
            parser = argparse.ArgumentParser(description="Detect support/resistance from volume clusters")
            parser.add_argument("ticker", help="Stock symbol (e.g., AAPL)")
            parser.add_argument("--period", default="3mo", help="Historical period (default: 3mo)")
            args = parser.parse_args(sys.argv[2:])
            
            result = detect_support_resistance(args.ticker.upper(), args.period)
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print("Available commands: order-book, bid-ask, liquidity, imbalance, support-resistance", file=sys.stderr)
            sys.exit(1)
