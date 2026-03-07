#!/usr/bin/env python3
"""
China A-Shares Open Data Feed Module
====================================

Comprehensive A-shares market data covering major indices, top stocks, and sector breakdowns.

Data Sources:
- Yahoo Finance: SSE Composite (000001.SS), CSI 300 (000300.SS), SZSE Component (399001.SZ)
- Major A-share stocks via Yahoo Finance tickers
- Free, no API key required

Focus Areas:
- A-shares index data (SSE Composite, CSI 300)
- Top stocks by market cap
- Sector breakdowns
- Market statistics

Category: Emerging Markets
Relevance: 8/10

Author: NightBuilder / QuantClaw
Generated: 2026-03-07
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class ChinaASharesFeed:
    """China A-Shares market data aggregator."""
    
    # Major A-shares indices
    INDICES = {
        "sse_composite": "000001.SS",   # Shanghai Stock Exchange Composite
        "csi_300": "000300.SS",          # CSI 300 (top 300 A-shares)
        "szse_component": "399001.SZ",   # Shenzhen Stock Exchange Component
        "chinext": "399006.SZ",          # ChiNext Growth Enterprise
    }
    
    # Top A-share stocks by market cap (representative sample)
    TOP_STOCKS = {
        "Kweichow Moutai": "600519.SS",      # Liquor giant
        "CATL": "300750.SZ",                  # Battery/EV
        "BYD": "002594.SZ",                   # EV manufacturer
        "China Merchants Bank": "600036.SS",  # Banking
        "Ping An Insurance": "601318.SS",     # Insurance
        "Industrial Bank": "601166.SS",       # Banking
        "Wuliangye": "000858.SZ",            # Liquor
        "LONGi Green Energy": "601012.SS",    # Solar
        "Contemporary Amperex": "300750.SZ",  # Batteries
        "Midea Group": "000333.SZ",          # Appliances
    }
    
    def get_index_data(
        self,
        index: str = "sse_composite",
        period: str = "1mo"
    ) -> Dict:
        """
        Get A-shares index historical data.
        
        Args:
            index: Index name (sse_composite, csi_300, szse_component, chinext)
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            
        Returns:
            Dict with OHLCV data and statistics
        """
        if index not in self.INDICES:
            return {
                "error": f"Unknown index: {index}",
                "available": list(self.INDICES.keys())
            }
        
        ticker_symbol = self.INDICES[index]
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {
                    "error": "No data available",
                    "symbol": ticker_symbol,
                    "index": index
                }
            
            # Calculate statistics
            returns = hist['Close'].pct_change().dropna()
            latest = hist.iloc[-1]
            first = hist.iloc[0]
            
            result = {
                "index": index,
                "symbol": ticker_symbol,
                "period": period,
                "latest": {
                    "date": latest.name.strftime('%Y-%m-%d'),
                    "close": round(float(latest['Close']), 2),
                    "open": round(float(latest['Open']), 2),
                    "high": round(float(latest['High']), 2),
                    "low": round(float(latest['Low']), 2),
                    "volume": int(latest['Volume']),
                },
                "period_stats": {
                    "start_date": first.name.strftime('%Y-%m-%d'),
                    "end_date": latest.name.strftime('%Y-%m-%d'),
                    "start_price": round(float(first['Close']), 2),
                    "end_price": round(float(latest['Close']), 2),
                    "return_pct": round((latest['Close'] / first['Close'] - 1) * 100, 2),
                    "high": round(float(hist['High'].max()), 2),
                    "low": round(float(hist['Low'].min()), 2),
                    "avg_volume": int(hist['Volume'].mean()),
                    "volatility_pct": round(float(returns.std() * 100), 2),
                },
                "data_points": len(hist)
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to fetch data: {str(e)}",
                "symbol": ticker_symbol,
                "index": index
            }
    
    def get_market_summary(self) -> Dict:
        """
        Get summary of all major A-shares indices.
        
        Returns:
            Dict with current quotes for all indices
        """
        summary = {}
        
        for index_name, ticker_symbol in self.INDICES.items():
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    summary[index_name] = {
                        "symbol": ticker_symbol,
                        "price": round(float(latest['Close']), 2),
                        "change": round(float(latest['Close'] - prev['Close']), 2),
                        "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                        "volume": int(latest['Volume']),
                        "date": latest.name.strftime('%Y-%m-%d')
                    }
            except Exception as e:
                summary[index_name] = {"error": str(e)}
        
        return summary
    
    def get_top_stocks(self, count: int = 10) -> List[Dict]:
        """
        Get current data for top A-share stocks by market cap.
        
        Args:
            count: Number of stocks to return
            
        Returns:
            List of dicts with stock data
        """
        results = []
        stock_items = list(self.TOP_STOCKS.items())[:count]
        
        for name, ticker_symbol in stock_items:
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    results.append({
                        "name": name,
                        "symbol": ticker_symbol,
                        "price": round(float(latest['Close']), 2),
                        "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                        "volume": int(latest['Volume']),
                        "date": latest.name.strftime('%Y-%m-%d')
                    })
            except Exception as e:
                results.append({
                    "name": name,
                    "symbol": ticker_symbol,
                    "error": str(e)
                })
        
        return results
    
    def get_sector_breakdown(self) -> Dict:
        """
        Get sector breakdown of A-shares market (representative sample).
        
        Returns:
            Dict with sector performance
        """
        sectors = {
            "Financial": ["600036.SS", "601318.SS", "601166.SS"],  # Banks, Insurance
            "Consumer": ["600519.SS", "000858.SZ", "000333.SZ"],   # Liquor, Appliances
            "Technology": ["300750.SZ", "002594.SZ"],              # Batteries, EV
            "Energy": ["601012.SS"],                               # Solar
        }
        
        sector_data = {}
        
        for sector_name, tickers in sectors.items():
            sector_returns = []
            
            for ticker_symbol in tickers:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty and len(hist) > 1:
                        latest = hist.iloc[-1]
                        prev = hist.iloc[-2]
                        change_pct = (latest['Close'] - prev['Close']) / prev['Close'] * 100
                        sector_returns.append(float(change_pct))
                except:
                    continue
            
            if sector_returns:
                sector_data[sector_name] = {
                    "avg_change_pct": round(sum(sector_returns) / len(sector_returns), 2),
                    "stocks_count": len(tickers),
                    "data_points": len(sector_returns)
                }
        
        return sector_data
    
    def compare_indices(self, period: str = "1mo") -> Dict:
        """
        Compare performance across all major A-shares indices.
        
        Args:
            period: Comparison period
            
        Returns:
            Dict with comparative metrics
        """
        comparison = {}
        
        for index_name, ticker_symbol in self.INDICES.items():
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    returns = hist['Close'].pct_change().dropna()
                    total_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                    
                    comparison[index_name] = {
                        "symbol": ticker_symbol,
                        "return_pct": round(float(total_return), 2),
                        "volatility_pct": round(float(returns.std() * 100), 2),
                        "current_price": round(float(hist['Close'].iloc[-1]), 2),
                        "data_points": len(hist)
                    }
            except Exception as e:
                comparison[index_name] = {"error": str(e)}
        
        return {
            "period": period,
            "comparison_date": datetime.now().strftime('%Y-%m-%d'),
            "indices": comparison
        }


# Convenience functions for quick access

def get_sse_composite(period: str = "1mo") -> Dict:
    """Get SSE Composite Index data."""
    feed = ChinaASharesFeed()
    return feed.get_index_data("sse_composite", period)


def get_csi_300(period: str = "1mo") -> Dict:
    """Get CSI 300 Index data."""
    feed = ChinaASharesFeed()
    return feed.get_index_data("csi_300", period)


def get_market_summary() -> Dict:
    """Get summary of all major A-shares indices."""
    feed = ChinaASharesFeed()
    return feed.get_market_summary()


def get_top_a_shares(count: int = 10) -> List[Dict]:
    """Get top A-share stocks by market cap."""
    feed = ChinaASharesFeed()
    return feed.get_top_stocks(count)


def get_sectors() -> Dict:
    """Get sector breakdown of A-shares market."""
    feed = ChinaASharesFeed()
    return feed.get_sector_breakdown()


def compare_all_indices(period: str = "1mo") -> Dict:
    """Compare all A-shares indices."""
    feed = ChinaASharesFeed()
    return feed.compare_indices(period)


def cli():
    """CLI interface for China A-Shares module."""
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "module": "china_a_shares_open_data_feed",
            "usage": "python -m modules.china_a_shares_open_data_feed <command>",
            "commands": {
                "summary": "Market summary of all indices",
                "sse": "SSE Composite Index data",
                "csi300": "CSI 300 Index data",
                "top": "Top A-share stocks",
                "sectors": "Sector breakdown",
                "compare": "Compare all indices"
            }
        }, indent=2))
        return
    
    command = sys.argv[1].lower()
    
    if command == "summary":
        result = get_market_summary()
    elif command == "sse":
        period = sys.argv[2] if len(sys.argv) > 2 else "1mo"
        result = get_sse_composite(period)
    elif command == "csi300":
        period = sys.argv[2] if len(sys.argv) > 2 else "1mo"
        result = get_csi_300(period)
    elif command == "top":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = get_top_a_shares(count)
    elif command == "sectors":
        result = get_sectors()
    elif command == "compare":
        period = sys.argv[2] if len(sys.argv) > 2 else "1mo"
        result = compare_all_indices(period)
    else:
        result = {
            "error": f"Unknown command: {command}",
            "valid_commands": ["summary", "sse", "csi300", "top", "sectors", "compare"]
        }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
