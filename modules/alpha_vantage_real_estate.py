"""
Alpha Vantage Real Estate — REIT Data & Analytics

Provides real-time and historical data for Real Estate Investment Trusts (REITs):
- Current quotes (price, volume, change)
- Daily time series (compact/full)
- Company overview & fundamentals
- Sector performance comparison
- Top REITs tracking

Data source: Alpha Vantage API
API key: ALPHA_VANTAGE_API_KEY env var (defaults to demo key)
Rate limits: 5 calls/min, 500 calls/day (free tier)
Coverage: Major REIT tickers (VNQ, IYR, SCHH, O, SPG, AMT, etc.)

Alpha Vantage endpoints used:
- GLOBAL_QUOTE: Real-time quote
- TIME_SERIES_DAILY: Historical daily prices
- OVERVIEW: Company fundamentals
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json


class AlphaVantageRealEstate:
    """Alpha Vantage REIT data fetcher"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "alpha_vantage_real_estate"
    CACHE_HOURS = 4  # Refresh every 4 hours for quotes
    CACHE_DAYS_DAILY = 1  # Daily data cached for 1 day
    
    # Major REIT tickers by subsector
    TOP_REITS = {
        "diversified": ["VNQ", "IYR", "SCHH", "XLRE"],  # ETFs
        "retail": ["SPG", "O", "REG", "KIM"],
        "residential": ["EQR", "AVB", "ESS", "MAA"],
        "office": ["BXP", "VNO", "SLG"],
        "industrial": ["PLD", "DRE", "REXR"],
        "healthcare": ["WELL", "VTR", "PEAK"],
        "data_center": ["DLR", "EQIX", "COR"],
        "telecom": ["AMT", "CCI", "SBAC"],
        "storage": ["PSA", "EXR", "CUBE"],
        "hotel": ["HST", "RHP", "PEB"],
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _make_request(self, params: Dict) -> Dict:
        """Make API request with error handling"""
        params["apikey"] = self.api_key
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if "Note" in data:
                raise ValueError(f"API Rate Limit: {data['Note']}")
            if "Information" in data and "demo" in data["Information"].lower():
                raise ValueError("Demo API key - requires real key from ALPHA_VANTAGE_API_KEY env var")
            
            return data
            
        except Exception as e:
            print(f"Error fetching from Alpha Vantage: {e}")
            raise
    
    def get_reit_quote(self, symbol: str) -> Dict:
        """Get current quote for a REIT ticker
        
        Args:
            symbol: REIT ticker (e.g., 'VNQ', 'SPG', 'O')
        
        Returns:
            Dict with price, volume, change, timestamp
        """
        cache_file = self.CACHE_DIR / f"quote_{symbol.upper()}.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch fresh data
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper()
        }
        
        data = self._make_request(params)
        
        if "Global Quote" not in data:
            raise ValueError(f"No quote data for {symbol}")
        
        quote = data["Global Quote"]
        
        result = {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "latest_trading_day": quote.get("07. latest trading day"),
            "previous_close": float(quote.get("08. previous close", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%").rstrip("%"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def get_reit_daily(self, symbol: str, outputsize: str = 'compact') -> pd.DataFrame:
        """Get daily price history for a REIT
        
        Args:
            symbol: REIT ticker
            outputsize: 'compact' (100 days) or 'full' (20+ years)
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_file = self.CACHE_DIR / f"daily_{symbol.upper()}_{outputsize}.parquet"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(days=self.CACHE_DAYS_DAILY):
                return pd.read_parquet(cache_file)
        
        # Fetch fresh data
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "outputsize": outputsize
        }
        
        data = self._make_request(params)
        
        if "Time Series (Daily)" not in data:
            raise ValueError(f"No daily data for {symbol}")
        
        # Convert to DataFrame
        ts_data = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts_data, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Clean column names and convert types
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df = df.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': int
        })
        
        df['symbol'] = symbol.upper()
        
        # Cache result
        df.to_parquet(cache_file)
        
        return df
    
    def get_reit_overview(self, symbol: str) -> Dict:
        """Get company overview/fundamentals for a REIT
        
        Args:
            symbol: REIT ticker
        
        Returns:
            Dict with company info, market cap, dividend yield, P/FFO, etc.
        """
        cache_file = self.CACHE_DIR / f"overview_{symbol.upper()}.json"
        
        # Check cache (weekly refresh for fundamentals)
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(days=7):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch fresh data
        params = {
            "function": "OVERVIEW",
            "symbol": symbol.upper()
        }
        
        data = self._make_request(params)
        
        if not data or "Symbol" not in data:
            raise ValueError(f"No overview data for {symbol}")
        
        result = {
            "symbol": data.get("Symbol"),
            "name": data.get("Name"),
            "description": data.get("Description"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "dividend_yield": data.get("DividendYield"),
            "dividend_per_share": data.get("DividendPerShare"),
            "ex_dividend_date": data.get("ExDividendDate"),
            "beta": data.get("Beta"),
            "52_week_high": data.get("52WeekHigh"),
            "52_week_low": data.get("52WeekLow"),
            "50_day_ma": data.get("50DayMovingAverage"),
            "200_day_ma": data.get("200DayMovingAverage"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def get_top_reits(self, subsector: Optional[str] = None) -> pd.DataFrame:
        """Get current data for top REITs
        
        Args:
            subsector: Optional filter ('retail', 'residential', 'office', etc.)
                      If None, returns all major REITs
        
        Returns:
            DataFrame with current quotes for selected REITs
        """
        if subsector and subsector not in self.TOP_REITS:
            raise ValueError(f"Invalid subsector. Choose from: {list(self.TOP_REITS.keys())}")
        
        # Get ticker list
        if subsector:
            tickers = self.TOP_REITS[subsector]
        else:
            # Flatten all tickers
            tickers = [t for sublist in self.TOP_REITS.values() for t in sublist]
        
        # Fetch quotes
        results = []
        for ticker in tickers:
            try:
                quote = self.get_reit_quote(ticker)
                results.append(quote)
            except Exception as e:
                print(f"Warning: Could not fetch {ticker}: {e}")
                continue
        
        if not results:
            raise ValueError("No data retrieved for any REIT")
        
        df = pd.DataFrame(results)
        df['change_percent'] = df['change_percent'].astype(float)
        df = df.sort_values('market_cap' if 'market_cap' in df.columns else 'volume', ascending=False)
        
        return df
    
    def get_reit_sector_performance(self) -> Dict[str, Dict]:
        """Get performance comparison across REIT subsectors
        
        Returns:
            Dict mapping subsector -> aggregated performance metrics
        """
        results = {}
        
        for subsector, tickers in self.TOP_REITS.items():
            sector_data = []
            
            for ticker in tickers:
                try:
                    quote = self.get_reit_quote(ticker)
                    sector_data.append({
                        'symbol': quote['symbol'],
                        'change_percent': float(quote['change_percent'])
                    })
                except Exception as e:
                    print(f"Warning: Could not fetch {ticker}: {e}")
                    continue
            
            if sector_data:
                # Calculate sector averages
                changes = [d['change_percent'] for d in sector_data]
                results[subsector] = {
                    'avg_change_percent': sum(changes) / len(changes),
                    'count': len(sector_data),
                    'tickers': [d['symbol'] for d in sector_data]
                }
        
        return results


# Convenience functions for direct access
def get_reit_quote(symbol: str, api_key: Optional[str] = None) -> Dict:
    """Get current quote for a REIT ticker"""
    client = AlphaVantageRealEstate(api_key=api_key)
    return client.get_reit_quote(symbol)


def get_reit_daily(symbol: str, outputsize: str = 'compact', api_key: Optional[str] = None) -> pd.DataFrame:
    """Get daily price history for a REIT"""
    client = AlphaVantageRealEstate(api_key=api_key)
    return client.get_reit_daily(symbol, outputsize)


def get_reit_overview(symbol: str, api_key: Optional[str] = None) -> Dict:
    """Get company overview/fundamentals for a REIT"""
    client = AlphaVantageRealEstate(api_key=api_key)
    return client.get_reit_overview(symbol)


def get_top_reits(subsector: Optional[str] = None, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get current data for top REITs"""
    client = AlphaVantageRealEstate(api_key=api_key)
    return client.get_top_reits(subsector)


def get_reit_sector_performance(api_key: Optional[str] = None) -> Dict[str, Dict]:
    """Get performance comparison across REIT subsectors"""
    client = AlphaVantageRealEstate(api_key=api_key)
    return client.get_reit_sector_performance()


if __name__ == "__main__":
    # Test module
    print(json.dumps({
        "module": "alpha_vantage_real_estate",
        "status": "ready",
        "functions": [
            "get_reit_quote",
            "get_reit_daily",
            "get_reit_overview",
            "get_top_reits",
            "get_reit_sector_performance"
        ]
    }, indent=2))
