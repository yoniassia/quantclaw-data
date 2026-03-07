"""
B3 Brazil Market Data API — Brazilian Stock Exchange Data

Provides access to Brazilian market data from B3 (Brasil Bolsa Balcão):
- IBOVESPA index (^BVSP) - Brazil's main stock index
- Individual Brazilian stocks (e.g., PETR4, VALE3, ITUB4)
- Top gainers and losers
- Sector performance
- Stock search functionality

Data source: Yahoo Finance (B3 official API not publicly available)
Ticker format: Add .SA suffix for B3-listed stocks (e.g., PETR4.SA, VALE3.SA)
Update frequency: 15-minute delayed quotes
Coverage: All B3-listed securities

Major Brazilian stocks:
- PETR4.SA (Petrobras) - Oil & Gas
- VALE3.SA (Vale) - Mining
- ITUB4.SA (Itaú Unibanco) - Banking
- BBDC4.SA (Bradesco) - Banking
- ABEV3.SA (Ambev) - Beverages
- B3SA3.SA (B3) - Exchange
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import json


class B3MarketData:
    """B3 Brazil Market Data fetcher via Yahoo Finance"""
    
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "b3_brazil_market_data"
    CACHE_HOURS = 1  # Refresh every hour
    
    # Major B3 stocks by sector
    MAJOR_STOCKS = {
        "oil_gas": ["PETR3.SA", "PETR4.SA", "PRIO3.SA"],
        "mining": ["VALE3.SA", "CSNA3.SA"],
        "banking": ["ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA"],
        "retail": ["MGLU3.SA", "LREN3.SA", "ARZZ3.SA"],
        "utilities": ["ELET3.SA", "ELET6.SA", "CMIG4.SA"],
        "beverages": ["ABEV3.SA"],
        "technology": ["B3SA3.SA", "TOTS3.SA"],
        "telecom": ["VIVT3.SA", "TIMS3.SA"],
    }
    
    # IBOVESPA index ticker
    IBOVESPA_TICKER = "^BVSP"
    
    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _normalize_ticker(self, ticker: str) -> str:
        """Normalize ticker to Yahoo Finance format (add .SA if needed)"""
        ticker = ticker.upper().strip()
        if ticker == "IBOVESPA" or ticker == "BVSP":
            return self.IBOVESPA_TICKER
        if not ticker.endswith(".SA") and not ticker.startswith("^"):
            ticker = f"{ticker}.SA"
        return ticker
    
    def _fetch_quote(self, ticker: str) -> Dict:
        """Fetch quote data from Yahoo Finance"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "interval": "1d",
            "range": "5d"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"]:
                raise ValueError(f"Invalid response for {ticker}")
            
            result = data["chart"]["result"][0]
            meta = result.get("meta", {})
            quote = result.get("indicators", {}).get("quote", [{}])[0]
            timestamps = result.get("timestamp", [])
            
            # Get latest values
            latest_idx = -1
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")
            
            # Calculate change
            change = current_price - prev_close if current_price and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            return {
                "ticker": ticker,
                "name": meta.get("longName") or meta.get("shortName") or ticker,
                "price": current_price,
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "previous_close": prev_close,
                "open": quote.get("open", [None])[latest_idx],
                "high": meta.get("regularMarketDayHigh"),
                "low": meta.get("regularMarketDayLow"),
                "volume": meta.get("regularMarketVolume"),
                "currency": meta.get("currency", "BRL"),
                "market_state": meta.get("marketState"),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            raise Exception(f"Error fetching {ticker}: {e}")
    
    def get_ibovespa(self) -> Dict:
        """Get IBOVESPA index current value and recent history"""
        cache_file = self.CACHE_DIR / "ibovespa.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        try:
            # Fetch IBOVESPA data
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.IBOVESPA_TICKER}"
            params = {
                "interval": "1d",
                "range": "1mo"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = data["chart"]["result"][0]
            meta = result["meta"]
            quote = result["indicators"]["quote"][0]
            timestamps = result["timestamp"]
            
            # Build historical data
            history = []
            closes = quote.get("close", [])
            for i, ts in enumerate(timestamps):
                if i < len(closes) and closes[i] is not None:
                    history.append({
                        "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                        "close": round(closes[i], 2)
                    })
            
            # Current data
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")
            change = current_price - prev_close if current_price and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            result_data = {
                "index": "IBOVESPA",
                "ticker": self.IBOVESPA_TICKER,
                "price": current_price,
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "previous_close": prev_close,
                "open": meta.get("regularMarketDayHigh"),
                "high": meta.get("regularMarketDayHigh"),
                "low": meta.get("regularMarketDayLow"),
                "volume": meta.get("regularMarketVolume"),
                "market_state": meta.get("marketState"),
                "history": history[-30:],  # Last 30 days
                "timestamp": datetime.now().isoformat(),
            }
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            return result_data
            
        except Exception as e:
            print(f"Error fetching IBOVESPA: {e}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_stock_quote(self, ticker: str) -> Dict:
        """Get quote for a Brazilian stock (e.g., PETR4, VALE3)"""
        ticker = self._normalize_ticker(ticker)
        cache_file = self.CACHE_DIR / f"quote_{ticker.replace('.', '_')}.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        try:
            quote = self._fetch_quote(ticker)
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(quote, f, indent=2)
            
            return quote
            
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Get top gaining stocks on B3"""
        cache_file = self.CACHE_DIR / "top_gainers.json"
        
        # Check cache (15 min for movers)
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(minutes=15):
                with open(cache_file) as f:
                    return json.load(f)
        
        try:
            # Fetch quotes for major stocks
            all_tickers = []
            for sector_tickers in self.MAJOR_STOCKS.values():
                all_tickers.extend(sector_tickers)
            
            quotes = []
            for ticker in all_tickers:
                try:
                    quote = self._fetch_quote(ticker)
                    quotes.append(quote)
                except:
                    continue
            
            # Sort by change percentage (descending)
            gainers = sorted(quotes, key=lambda x: x.get("change_percent", 0), reverse=True)[:limit]
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(gainers, f, indent=2)
            
            return gainers
            
        except Exception as e:
            print(f"Error fetching top gainers: {e}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """Get top losing stocks on B3"""
        cache_file = self.CACHE_DIR / "top_losers.json"
        
        # Check cache (15 min for movers)
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(minutes=15):
                with open(cache_file) as f:
                    return json.load(f)
        
        try:
            # Fetch quotes for major stocks
            all_tickers = []
            for sector_tickers in self.MAJOR_STOCKS.values():
                all_tickers.extend(sector_tickers)
            
            quotes = []
            for ticker in all_tickers:
                try:
                    quote = self._fetch_quote(ticker)
                    quotes.append(quote)
                except:
                    continue
            
            # Sort by change percentage (ascending)
            losers = sorted(quotes, key=lambda x: x.get("change_percent", 0))[:limit]
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(losers, f, indent=2)
            
            return losers
            
        except Exception as e:
            print(f"Error fetching top losers: {e}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_sector_performance(self) -> Dict[str, Dict]:
        """Get B3 sector performance breakdown"""
        cache_file = self.CACHE_DIR / "sector_performance.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=1):
                with open(cache_file) as f:
                    return json.load(f)
        
        try:
            sector_data = {}
            
            for sector, tickers in self.MAJOR_STOCKS.items():
                quotes = []
                for ticker in tickers:
                    try:
                        quote = self._fetch_quote(ticker)
                        quotes.append(quote)
                    except:
                        continue
                
                if quotes:
                    # Calculate sector average
                    avg_change = sum(q.get("change_percent", 0) for q in quotes) / len(quotes)
                    total_volume = sum(q.get("volume", 0) or 0 for q in quotes)
                    
                    sector_data[sector] = {
                        "name": sector.replace("_", " ").title(),
                        "avg_change_percent": round(avg_change, 2),
                        "total_volume": total_volume,
                        "stocks_count": len(quotes),
                        "stocks": [q["ticker"] for q in quotes]
                    }
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "sectors": sector_data
            }
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            print(f"Error fetching sector performance: {e}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search B3 listed stocks by name or ticker"""
        query = query.upper().strip()
        
        # Build searchable list from major stocks
        all_stocks = []
        for sector, tickers in self.MAJOR_STOCKS.items():
            for ticker in tickers:
                # Extract base ticker (remove .SA)
                base_ticker = ticker.replace(".SA", "")
                all_stocks.append({
                    "ticker": ticker,
                    "base_ticker": base_ticker,
                    "sector": sector.replace("_", " ").title()
                })
        
        # Search by ticker
        results = []
        for stock in all_stocks:
            if query in stock["base_ticker"] or query in stock["ticker"]:
                try:
                    quote = self._fetch_quote(stock["ticker"])
                    quote["sector"] = stock["sector"]
                    results.append(quote)
                except:
                    continue
        
        return results


# Convenience functions for direct imports
def get_ibovespa() -> Dict:
    """Get IBOVESPA index current value and recent history"""
    client = B3MarketData()
    return client.get_ibovespa()


def get_stock_quote(ticker: str) -> Dict:
    """Get quote for Brazilian stock (e.g., PETR4, VALE3)"""
    client = B3MarketData()
    return client.get_stock_quote(ticker)


def get_top_gainers(limit: int = 10) -> List[Dict]:
    """Get top gaining stocks on B3"""
    client = B3MarketData()
    return client.get_top_gainers(limit)


def get_top_losers(limit: int = 10) -> List[Dict]:
    """Get top losing stocks on B3"""
    client = B3MarketData()
    return client.get_top_losers(limit)


def get_sector_performance() -> Dict[str, Dict]:
    """Get B3 sector performance breakdown"""
    client = B3MarketData()
    return client.get_sector_performance()


def search_stocks(query: str) -> List[Dict]:
    """Search B3 listed stocks"""
    client = B3MarketData()
    return client.search_stocks(query)


if __name__ == "__main__":
    # Test module
    print("Testing B3 Brazil Market Data API module...")
    print("\n1. IBOVESPA Index:")
    ibov = get_ibovespa()
    print(f"   {ibov['index']}: {ibov['price']:,.2f} ({ibov['change_percent']:+.2f}%)")
    
    print("\n2. Stock Quote (PETR4):")
    petr4 = get_stock_quote("PETR4")
    print(f"   {petr4['name']}: R$ {petr4['price']:.2f} ({petr4['change_percent']:+.2f}%)")
    
    print("\n3. Top 3 Gainers:")
    gainers = get_top_gainers(3)
    for g in gainers:
        print(f"   {g['ticker']}: {g['change_percent']:+.2f}%")
    
    print("\nModule test complete!")
