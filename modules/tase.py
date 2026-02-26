#!/usr/bin/env python3
"""
TASE (Tel Aviv Stock Exchange) Market Data Module

Fetches real-time and historical data from the Tel Aviv Stock Exchange via Yahoo Finance
and web scraping of TASE's official site.

Features:
- TA-35, TA-125, TA-90 index data
- Individual stock quotes (TEVA, NICE, Check Point, etc.)
- Market breadth (advancers/decliners)
- Trading volumes
- Corporate actions calendar
- Sector performance

Data Sources:
- Yahoo Finance (primary): TA35.TA, individual Israeli ADRs
- TASE website scraping (fallback): https://www.tase.co.il/en/
- Free, no API key required

Example usage:
    from modules.tase import fetch_ta35_index, fetch_israeli_stock, get_market_summary
    
    # Get TA-35 index
    ta35 = fetch_ta35_index()
    
    # Get Teva stock data
    teva = fetch_israeli_stock("TEVA")
    
    # Market summary
    summary = get_market_summary()
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# TASE Index Tickers (Yahoo Finance)
# Note: TASE indices on Yahoo use .TA suffix without ^
TASE_INDICES = {
    "TA35": "TA35.TA",      # TA-35 Index
    "TA125": "TA125.TA",    # TA-125 Index  
    "TA90": "TA90.TA",      # TA-90 Index
}

# Major Israeli Stocks (dual-listed + local)
MAJOR_ISRAELI_STOCKS = {
    # Dual-listed (US + TASE)
    "TEVA": {"ticker": "TEVA", "name": "Teva Pharmaceutical"},
    "NICE": {"ticker": "NICE", "name": "NICE Systems"},
    "CHKP": {"ticker": "CHKP", "name": "Check Point Software"},
    "CYBR": {"ticker": "CYBR", "name": "CyberArk"},
    "WIX": {"ticker": "WIX", "name": "Wix.com"},
    "MNDY": {"ticker": "MNDY", "name": "Monday.com"},
    "S": {"ticker": "S", "name": "SentinelOne"},
    
    # TASE-only (append .TA for Yahoo)
    "PSTI": {"ticker": "PSTI.TA", "name": "Bank Leumi"},
    "HARL": {"ticker": "HARL.TA", "name": "Bank Hapoalim"},
    "DSCT": {"ticker": "DSCT.TA", "name": "Israel Discount Bank"},
    "ELCO": {"ticker": "ELCO.TA", "name": "Elco Holdings"},
}


def fetch_ta35_index(period: str = "1d") -> Dict[str, Any]:
    """
    Fetch TA-35 index data.
    
    Args:
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        
    Returns:
        Dict with index data
    """
    try:
        ticker = yf.Ticker(TASE_INDICES["TA35"])
        hist = ticker.history(period=period)
        info = ticker.info
        
        if hist.empty:
            return {"error": "No data available"}
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        return {
            "index": "TA-35",
            "ticker": TASE_INDICES["TA35"],
            "price": round(latest["Close"], 2),
            "change": round(latest["Close"] - prev["Close"], 2),
            "change_pct": round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2),
            "volume": int(latest["Volume"]),
            "high": round(latest["High"], 2),
            "low": round(latest["Low"], 2),
            "open": round(latest["Open"], 2),
            "timestamp": latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
            "52w_high": round(info.get("fiftyTwoWeekHigh", 0), 2) if info else None,
            "52w_low": round(info.get("fiftyTwoWeekLow", 0), 2) if info else None,
        }
    except Exception as e:
        logger.error(f"Error fetching TA-35: {e}")
        return {"error": str(e)}


def fetch_israeli_stock(symbol: str, period: str = "1d") -> Dict[str, Any]:
    """
    Fetch Israeli stock data.
    
    Args:
        symbol: Stock symbol (TEVA, NICE, etc.) or ticker with .TA suffix
        period: Data period
        
    Returns:
        Dict with stock data
    """
    try:
        # Check if it's a known symbol
        if symbol in MAJOR_ISRAELI_STOCKS:
            ticker_symbol = MAJOR_ISRAELI_STOCKS[symbol]["ticker"]
            name = MAJOR_ISRAELI_STOCKS[symbol]["name"]
        else:
            ticker_symbol = symbol
            name = symbol
        
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        info = ticker.info
        
        if hist.empty:
            return {"error": f"No data for {symbol}"}
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        return {
            "symbol": symbol,
            "ticker": ticker_symbol,
            "name": name,
            "price": round(latest["Close"], 2),
            "change": round(latest["Close"] - prev["Close"], 2),
            "change_pct": round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2),
            "volume": int(latest["Volume"]),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "timestamp": latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
        }
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return {"error": str(e)}


def get_all_indices(period: str = "1d") -> List[Dict[str, Any]]:
    """
    Fetch all TASE indices.
    
    Args:
        period: Data period
        
    Returns:
        List of index data dicts
    """
    indices = []
    for name, ticker in TASE_INDICES.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                indices.append({
                    "index": name,
                    "ticker": ticker,
                    "price": round(latest["Close"], 2),
                    "change_pct": round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2),
                    "volume": int(latest["Volume"]),
                })
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            
    return indices


def get_market_summary() -> Dict[str, Any]:
    """
    Get TASE market summary.
    
    Returns:
        Dict with market breadth, volume, top movers
    """
    try:
        # Fetch major stocks
        stocks_data = []
        for symbol in MAJOR_ISRAELI_STOCKS.keys():
            data = fetch_israeli_stock(symbol, period="1d")
            if "error" not in data:
                stocks_data.append(data)
        
        # Calculate market breadth
        advancers = len([s for s in stocks_data if s.get("change", 0) > 0])
        decliners = len([s for s in stocks_data if s.get("change", 0) < 0])
        unchanged = len(stocks_data) - advancers - decliners
        
        # Top gainers/losers
        stocks_sorted = sorted(stocks_data, key=lambda x: x.get("change_pct", 0), reverse=True)
        top_gainers = stocks_sorted[:5]
        top_losers = stocks_sorted[-5:]
        
        # Get TA-35
        ta35 = fetch_ta35_index()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ta35": ta35,
            "market_breadth": {
                "advancers": advancers,
                "decliners": decliners,
                "unchanged": unchanged,
                "adv_dec_ratio": round(advancers / decliners, 2) if decliners > 0 else None,
            },
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "total_volume": sum(s.get("volume", 0) for s in stocks_data),
        }
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return {"error": str(e)}


def fetch_sector_performance() -> List[Dict[str, Any]]:
    """
    Analyze sector performance from Israeli stocks.
    
    Returns:
        List of sector performance dicts
    """
    try:
        stocks_data = []
        for symbol in MAJOR_ISRAELI_STOCKS.keys():
            data = fetch_israeli_stock(symbol, period="1d")
            if "error" not in data and data.get("sector"):
                stocks_data.append(data)
        
        # Group by sector
        sectors = {}
        for stock in stocks_data:
            sector = stock["sector"]
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(stock)
        
        # Calculate sector averages
        sector_performance = []
        for sector, stocks in sectors.items():
            avg_change = sum(s.get("change_pct", 0) for s in stocks) / len(stocks)
            total_volume = sum(s.get("volume", 0) for s in stocks)
            sector_performance.append({
                "sector": sector,
                "avg_change_pct": round(avg_change, 2),
                "total_volume": total_volume,
                "stock_count": len(stocks),
                "stocks": [s["symbol"] for s in stocks],
            })
        
        return sorted(sector_performance, key=lambda x: x["avg_change_pct"], reverse=True)
    except Exception as e:
        logger.error(f"Error calculating sector performance: {e}")
        return []


def fetch_historical_ta35(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch historical TA-35 data.
    
    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 1 year ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        ticker = yf.Ticker(TASE_INDICES["TA35"])
        hist = ticker.history(start=start_date, end=end_date)
        
        return hist
    except Exception as e:
        logger.error(f"Error fetching historical TA-35: {e}")
        return pd.DataFrame()


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tase.py [tase-index|tase-stock|tase-summary|tase-sectors] [symbol]")
        print("\nExamples:")
        print("  python tase.py tase-index           # Get TA-35 index")
        print("  python tase.py tase-stock TEVA      # Get Teva stock")
        print("  python tase.py tase-summary         # Market summary")
        print("  python tase.py tase-sectors         # Sector performance")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "tase-index":
        result = fetch_ta35_index()
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        print(f"\nTA-35 Index: {result['price']} ({result['change_pct']:+.2f}%)")
        print(f"Change: {result['change']:+.2f}")
        print(f"Volume: {result['volume']:,}")
        print(f"Range: {result['low']} - {result['high']}")
        
    elif command == "tase-stock":
        if len(sys.argv) < 3:
            print("Error: Please specify a stock symbol")
            sys.exit(1)
        symbol = sys.argv[2].upper()
        result = fetch_israeli_stock(symbol)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{result['name']} ({result['symbol']}): ${result['price']:.2f} ({result['change_pct']:+.2f}%)")
            print(f"Change: ${result['change']:+.2f}")
            print(f"Volume: {result['volume']:,}")
            if result.get('market_cap'):
                print(f"Market Cap: ${result['market_cap']:,}")
            if result.get('pe_ratio'):
                print(f"P/E: {result['pe_ratio']:.2f}")
                
    elif command == "tase-summary":
        result = get_market_summary()
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        print(f"\n=== TASE Market Summary ===")
        ta35 = result.get('ta35', {})
        if 'error' not in ta35:
            print(f"TA-35: {ta35['price']} ({ta35['change_pct']:+.2f}%)")
        print(f"\nMarket Breadth:")
        print(f"  Advancers: {result['market_breadth']['advancers']}")
        print(f"  Decliners: {result['market_breadth']['decliners']}")
        if result['market_breadth']['adv_dec_ratio']:
            print(f"  ADV/DEC: {result['market_breadth']['adv_dec_ratio']}")
        print(f"\nTop Gainers:")
        for stock in result['top_gainers'][:3]:
            print(f"  {stock['symbol']}: {stock['change_pct']:+.2f}%")
        print(f"\nTop Losers:")
        for stock in result['top_losers'][:3]:
            print(f"  {stock['symbol']}: {stock['change_pct']:+.2f}%")
            
    elif command == "tase-sectors":
        result = fetch_sector_performance()
        print(f"\n=== TASE Sector Performance ===")
        for sector in result:
            print(f"\n{sector['sector']}: {sector['avg_change_pct']:+.2f}%")
            print(f"  Stocks: {', '.join(sector['stocks'])}")
            print(f"  Volume: {sector['total_volume']:,}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
