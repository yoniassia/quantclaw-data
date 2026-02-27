#!/usr/bin/env python3
"""
ASX (Australian Securities Exchange) Market Data Module
Free data sources: ASX website, Yahoo Finance, investing.com
"""
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

# Simple in-memory cache
_cache = {}
_cache_ttl = {}

def cache_result(hours=1):
    """Simple cache decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            now = datetime.now()
            if key in _cache and key in _cache_ttl:
                if now < _cache_ttl[key]:
                    return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_ttl[key] = now + timedelta(hours=hours)
            return result
        return wrapper
    return decorator

BASE_URL = "https://www.asx.com.au"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

class ASXClient:
    """Client for ASX Exchange data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    @cache_result(hours=24)
    def get_asx200_composition(self) -> List[Dict]:
        """
        Get ASX 200 index composition
        Uses Yahoo Finance for index constituents
        """
        try:
            # ASX 200 ticker on Yahoo Finance
            ticker = "^AXJO"
            index = yf.Ticker(ticker)
            
            # Get historical data to confirm index exists
            hist = index.history(period="5d")
            
            if hist.empty:
                return []
            
            # For actual constituents, we'll use a static list of top holdings
            # (ASX doesn't provide free API for full constituent list)
            top_holdings = [
                {"ticker": "BHP.AX", "name": "BHP Group", "sector": "Materials"},
                {"ticker": "CBA.AX", "name": "Commonwealth Bank", "sector": "Financials"},
                {"ticker": "CSL.AX", "name": "CSL Limited", "sector": "Healthcare"},
                {"ticker": "NAB.AX", "name": "National Australia Bank", "sector": "Financials"},
                {"ticker": "WBC.AX", "name": "Westpac Banking", "sector": "Financials"},
                {"ticker": "ANZ.AX", "name": "ANZ Banking Group", "sector": "Financials"},
                {"ticker": "WES.AX", "name": "Wesfarmers", "sector": "Consumer Staples"},
                {"ticker": "MQG.AX", "name": "Macquarie Group", "sector": "Financials"},
                {"ticker": "WDS.AX", "name": "Woodside Energy", "sector": "Energy"},
                {"ticker": "GMG.AX", "name": "Goodman Group", "sector": "Real Estate"},
                {"ticker": "RIO.AX", "name": "Rio Tinto", "sector": "Materials"},
                {"ticker": "WOW.AX", "name": "Woolworths Group", "sector": "Consumer Staples"},
                {"ticker": "FMG.AX", "name": "Fortescue Metals", "sector": "Materials"},
                {"ticker": "TLS.AX", "name": "Telstra Corporation", "sector": "Communication"},
                {"ticker": "TCL.AX", "name": "Transurban Group", "sector": "Industrials"},
            ]
            
            # Enrich with live prices
            result = []
            for holding in top_holdings:
                try:
                    stock = yf.Ticker(holding["ticker"])
                    info = stock.info
                    hist = stock.history(period="1d")
                    
                    if not hist.empty:
                        result.append({
                            "ticker": holding["ticker"],
                            "name": holding["name"],
                            "sector": holding["sector"],
                            "price": round(hist['Close'].iloc[-1], 2),
                            "market_cap": info.get("marketCap", 0),
                            "volume": int(hist['Volume'].iloc[-1]) if not hist.empty else 0
                        })
                except Exception as e:
                    result.append(holding)
                    
            return result
            
        except Exception as e:
            print(f"ASX 200 composition error: {e}")
            return []
    
    @cache_result(hours=1)
    def get_market_summary(self) -> Dict:
        """
        Get ASX market summary (index level, volume, etc.)
        """
        try:
            # ASX 200 (All Ordinaries would be ^AORD)
            ticker = "^AXJO"
            index = yf.Ticker(ticker)
            hist = index.history(period="5d")
            
            if hist.empty:
                return {}
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            return {
                "index": "ASX 200",
                "ticker": ticker,
                "level": round(latest['Close'], 2),
                "change": round(latest['Close'] - prev['Close'], 2),
                "change_pct": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                "volume": int(latest['Volume']),
                "high": round(latest['High'], 2),
                "low": round(latest['Low'], 2),
                "open": round(latest['Open'], 2),
                "timestamp": latest.name.isoformat()
            }
            
        except Exception as e:
            print(f"Market summary error: {e}")
            return {}
    
    @cache_result(hours=6)
    def get_stock_info(self, ticker: str) -> Dict:
        """
        Get detailed stock information for an ASX ticker
        Ticker format: ABC.AX (must include .AX suffix)
        """
        try:
            if not ticker.endswith(".AX"):
                ticker = f"{ticker}.AX"
            
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")
            
            if hist.empty:
                return {"error": f"No data for {ticker}"}
            
            latest = hist.iloc[-1]
            
            return {
                "ticker": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "price": round(latest['Close'], 2),
                "change": round(latest['Close'] - hist['Close'].iloc[-2], 2),
                "change_pct": round(((latest['Close'] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100, 2),
                "volume": int(latest['Volume']),
                "avg_volume": int(hist['Volume'].mean()),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "52w_high": round(hist['High'].max(), 2),
                "52w_low": round(hist['Low'].min(), 2),
                "currency": "AUD"
            }
            
        except Exception as e:
            print(f"Stock info error for {ticker}: {e}")
            return {"error": str(e)}
    
    @cache_result(hours=24)
    def get_corporate_actions(self, ticker: str, days_back: int = 90) -> List[Dict]:
        """
        Get corporate actions (dividends, splits, etc.)
        """
        try:
            if not ticker.endswith(".AX"):
                ticker = f"{ticker}.AX"
            
            stock = yf.Ticker(ticker)
            
            # Dividends
            dividends = stock.dividends
            splits = stock.splits
            
            actions = []
            
            # Process dividends
            if not dividends.empty:
                cutoff = datetime.now() - timedelta(days=days_back)
                recent_divs = dividends[dividends.index >= cutoff]
                
                for date, amount in recent_divs.items():
                    actions.append({
                        "type": "dividend",
                        "date": date.strftime("%Y-%m-%d"),
                        "amount": round(amount, 2),
                        "currency": "AUD"
                    })
            
            # Process splits
            if not splits.empty:
                cutoff = datetime.now() - timedelta(days=days_back)
                recent_splits = splits[splits.index >= cutoff]
                
                for date, ratio in recent_splits.items():
                    actions.append({
                        "type": "split",
                        "date": date.strftime("%Y-%m-%d"),
                        "ratio": f"{ratio}:1"
                    })
            
            return sorted(actions, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            print(f"Corporate actions error for {ticker}: {e}")
            return []
    
    @cache_result(hours=1)
    def get_sector_performance(self) -> List[Dict]:
        """
        Get sector performance across ASX
        Uses S&P/ASX sector indices
        """
        sectors = {
            "XEJ.AX": "Energy",
            "XMJ.AX": "Materials",
            "XNJ.AX": "Industrials",
            "XDJ.AX": "Consumer Discretionary",
            "XSJ.AX": "Consumer Staples",
            "XHJ.AX": "Healthcare",
            "XFJ.AX": "Financials",
            "XIJ.AX": "Information Technology",
            "XTJ.AX": "Communication Services",
            "XUJ.AX": "Utilities",
            "XPJ.AX": "Real Estate"
        }
        
        results = []
        for ticker, name in sectors.items():
            try:
                sector = yf.Ticker(ticker)
                hist = sector.history(period="5d")
                
                if not hist.empty and len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    
                    results.append({
                        "sector": name,
                        "ticker": ticker,
                        "level": round(latest['Close'], 2),
                        "change": round(latest['Close'] - prev['Close'], 2),
                        "change_pct": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2)
                    })
            except Exception as e:
                pass
        
        return sorted(results, key=lambda x: x['change_pct'], reverse=True)
    
    @cache_result(hours=1)
    def get_market_depth(self, ticker: str) -> Dict:
        """
        Get market depth (bid/ask spread, volume)
        Limited data from Yahoo Finance quote
        """
        try:
            if not ticker.endswith(".AX"):
                ticker = f"{ticker}.AX"
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "ticker": ticker,
                "bid": info.get("bid", 0),
                "ask": info.get("ask", 0),
                "spread": round(info.get("ask", 0) - info.get("bid", 0), 2),
                "spread_pct": round(((info.get("ask", 0) - info.get("bid", 0)) / info.get("bid", 1)) * 100, 2) if info.get("bid", 0) > 0 else 0,
                "bid_size": info.get("bidSize", 0),
                "ask_size": info.get("askSize", 0)
            }
            
        except Exception as e:
            print(f"Market depth error for {ticker}: {e}")
            return {}
    
    @cache_result(hours=24)
    def get_asx_ipos(self, days_back: int = 180) -> List[Dict]:
        """
        Get recent ASX IPOs
        This is a placeholder - would need web scraping of ASX announcements
        """
        # In production, would scrape https://www.asx.com.au/markets/trade-our-cash-market/ipos-and-placements
        return [
            {
                "company": "Check ASX website for current IPOs",
                "ticker": "N/A",
                "list_date": "N/A",
                "offer_price": 0,
                "note": "IPO data requires web scraping or paid API"
            }
        ]
    
    @cache_result(hours=1)
    def get_stock_history(self, ticker: str, period: str = "1mo") -> Dict:
        """
        Get historical price data for ASX stock
        """
        try:
            if not ticker.endswith(".AX"):
                ticker = f"{ticker}.AX"
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return {"error": f"No data for {ticker}"}
            
            # Calculate basic statistics
            returns = hist['Close'].pct_change().dropna()
            
            return {
                "ticker": ticker,
                "period": period,
                "data_points": len(hist),
                "start_date": hist.index[0].strftime("%Y-%m-%d"),
                "end_date": hist.index[-1].strftime("%Y-%m-%d"),
                "start_price": round(hist['Close'].iloc[0], 2),
                "end_price": round(hist['Close'].iloc[-1], 2),
                "total_return_pct": round(((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100, 2),
                "avg_volume": int(hist['Volume'].mean()),
                "volatility_pct": round(returns.std() * (252 ** 0.5) * 100, 2),  # Annualized
                "max_drawdown_pct": round((hist['Close'] / hist['Close'].cummax() - 1).min() * 100, 2),
                "high": round(hist['High'].max(), 2),
                "low": round(hist['Low'].min(), 2)
            }
            
        except Exception as e:
            print(f"Stock history error for {ticker}: {e}")
            return {"error": str(e)}
    
    @cache_result(hours=6)
    def compare_stocks(self, tickers: List[str], period: str = "3mo") -> List[Dict]:
        """
        Compare multiple ASX stocks side by side
        """
        results = []
        for ticker in tickers:
            if not ticker.endswith(".AX"):
                ticker = f"{ticker}.AX"
            
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                info = stock.info
                
                if not hist.empty:
                    returns = hist['Close'].pct_change().dropna()
                    
                    results.append({
                        "ticker": ticker,
                        "name": info.get("longName", ticker),
                        "sector": info.get("sector", "Unknown"),
                        "price": round(hist['Close'].iloc[-1], 2),
                        "return_pct": round(((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100, 2),
                        "volatility_pct": round(returns.std() * (252 ** 0.5) * 100, 2),
                        "market_cap": info.get("marketCap", 0),
                        "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
                        "dividend_yield": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else 0
                    })
            except Exception as e:
                pass
        
        return sorted(results, key=lambda x: x['return_pct'], reverse=True)
    
    @cache_result(hours=1)
    def get_market_movers(self, direction: str = "gainers", limit: int = 10) -> List[Dict]:
        """
        Get top gainers or losers on ASX
        Uses a subset of ASX 200 stocks for performance
        """
        holdings = self.get_asx200_composition()
        
        if direction == "losers":
            sorted_holdings = sorted(holdings, key=lambda x: x.get('change_pct', 0) if 'change_pct' in x else 0)
        else:
            sorted_holdings = sorted(holdings, key=lambda x: x.get('change_pct', 0) if 'change_pct' in x else 0, reverse=True)
        
        # Calculate change_pct for holdings that don't have it
        for holding in sorted_holdings[:limit]:
            if 'change_pct' not in holding:
                try:
                    stock = yf.Ticker(holding['ticker'])
                    hist = stock.history(period="5d")
                    if len(hist) >= 2:
                        latest = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        holding['change_pct'] = round(((latest - prev) / prev) * 100, 2)
                        holding['price'] = round(latest, 2)
                except:
                    holding['change_pct'] = 0
        
        return sorted_holdings[:limit]
    
    @cache_result(hours=1)
    def get_index_comparison(self) -> Dict:
        """
        Compare major ASX indices (ASX 200, All Ords, Small Caps)
        """
        indices = {
            "ASX 200": "^AXJO",
            "All Ordinaries": "^AORD",
            "Small Caps": "^AXSO"
        }
        
        results = {}
        for name, ticker in indices.items():
            try:
                index = yf.Ticker(ticker)
                hist = index.history(period="5d")
                
                if not hist.empty and len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    
                    results[name] = {
                        "ticker": ticker,
                        "level": round(latest['Close'], 2),
                        "change": round(latest['Close'] - prev['Close'], 2),
                        "change_pct": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                        "volume": int(latest['Volume'])
                    }
            except:
                pass
        
        return results


def asx_index_summary() -> Dict:
    """CLI: Get ASX market summary"""
    client = ASXClient()
    return client.get_market_summary()

def asx_top_holdings(limit: int = 15) -> List[Dict]:
    """CLI: Get ASX 200 top holdings"""
    client = ASXClient()
    holdings = client.get_asx200_composition()
    return holdings[:limit]

def asx_stock_quote(ticker: str) -> Dict:
    """CLI: Get stock quote for ASX ticker"""
    client = ASXClient()
    return client.get_stock_info(ticker)

def asx_corporate_actions(ticker: str, days: int = 90) -> List[Dict]:
    """CLI: Get corporate actions for stock"""
    client = ASXClient()
    return client.get_corporate_actions(ticker, days)

def asx_sectors() -> List[Dict]:
    """CLI: Get sector performance"""
    client = ASXClient()
    return client.get_sector_performance()

def asx_depth(ticker: str) -> Dict:
    """CLI: Get market depth for ticker"""
    client = ASXClient()
    return client.get_market_depth(ticker)

def asx_history(ticker: str, period: str = "1mo") -> Dict:
    """CLI: Get historical data for ticker"""
    client = ASXClient()
    return client.get_stock_history(ticker, period)

def asx_compare(tickers: List[str], period: str = "3mo") -> List[Dict]:
    """CLI: Compare multiple stocks"""
    client = ASXClient()
    return client.compare_stocks(tickers, period)

def asx_movers(direction: str = "gainers", limit: int = 10) -> List[Dict]:
    """CLI: Get top gainers or losers"""
    client = ASXClient()
    return client.get_market_movers(direction, limit)

def asx_indices() -> Dict:
    """CLI: Compare major ASX indices"""
    client = ASXClient()
    return client.get_index_comparison()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python asx.py <command> [args]")
        print("Commands:")
        print("  asx-summary                    - Market summary")
        print("  asx-holdings [limit]           - Top ASX 200 holdings")
        print("  asx-quote <ticker>             - Stock quote")
        print("  asx-actions <ticker> [days]    - Corporate actions")
        print("  asx-sectors                    - Sector performance")
        print("  asx-depth <ticker>             - Market depth")
        print("  asx-history <ticker> [period]  - Historical data")
        print("  asx-compare <ticker1,ticker2>  - Compare stocks")
        print("  asx-movers [gainers|losers]    - Top movers")
        print("  asx-indices                    - Compare indices")
        sys.exit(1)
    
    command = sys.argv[1]
    client = ASXClient()
    
    if command == "asx-summary":
        result = client.get_market_summary()
    elif command == "asx-holdings":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        result = client.get_asx200_composition()[:limit]
    elif command == "asx-quote":
        if len(sys.argv) < 3:
            print("Error: ticker required")
            sys.exit(1)
        result = client.get_stock_info(sys.argv[2])
    elif command == "asx-actions":
        if len(sys.argv) < 3:
            print("Error: ticker required")
            sys.exit(1)
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
        result = client.get_corporate_actions(sys.argv[2], days)
    elif command == "asx-sectors":
        result = client.get_sector_performance()
    elif command == "asx-depth":
        if len(sys.argv) < 3:
            print("Error: ticker required")
            sys.exit(1)
        result = client.get_market_depth(sys.argv[2])
    elif command == "asx-history":
        if len(sys.argv) < 3:
            print("Error: ticker required")
            sys.exit(1)
        period = sys.argv[3] if len(sys.argv) > 3 else "1mo"
        result = client.get_stock_history(sys.argv[2], period)
    elif command == "asx-compare":
        if len(sys.argv) < 3:
            print("Error: tickers required (comma-separated)")
            sys.exit(1)
        tickers = [t.strip() for t in sys.argv[2].split(',')]
        result = client.compare_stocks(tickers)
    elif command == "asx-movers":
        direction = sys.argv[2] if len(sys.argv) > 2 else "gainers"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = client.get_market_movers(direction, limit)
    elif command == "asx-indices":
        result = client.get_index_comparison()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))
