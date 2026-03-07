"""
Alpha Vantage FX — Foreign Exchange Rates & Technical Indicators

Provides intraday, daily, weekly, and monthly forex exchange rates for major
and emerging market currency pairs. Real-time exchange rates with bid/ask spreads.

Data source: Alpha Vantage FX API
API docs: https://www.alphavantage.co/documentation/#fx
Update frequency: Real-time for exchange rates, intraday/daily for time series
Coverage: 150+ currency pairs

Free tier: 5 calls/minute, 500 calls/day (requires API key)
Premium tier: Higher rate limits available

Common pairs: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, USD/CHF, NZD/USD
Emerging: USD/TRY, USD/ZAR, USD/BRL, USD/INR, USD/CNY, USD/RUB

API Key: Set ALPHA_VANTAGE_API_KEY env var or uses demo key (limited)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json
import os


class AlphaVantageFX:
    """Alpha Vantage Foreign Exchange data fetcher"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "alphavantagefx"
    CACHE_MINUTES = 5  # Rate limit: 5 calls/min
    
    # Valid intervals for intraday
    VALID_INTERVALS = ["1min", "5min", "15min", "30min", "60min"]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or parameter"""
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0 (AlphaVantageFX Module)'
        })
    
    def _build_url(self, params: Dict) -> str:
        """Build API URL with parameters"""
        params["apikey"] = self.api_key
        return self.BASE_URL
    
    def _get_cache_key(self, function: str, **kwargs) -> str:
        """Generate cache key from function and parameters"""
        parts = [function] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return "_".join(parts)
    
    def _fetch_data(self, params: Dict, cache_minutes: int = None) -> Dict:
        """Fetch data from API with caching"""
        if cache_minutes is None:
            cache_minutes = self.CACHE_MINUTES
        
        cache_key = self._get_cache_key(**params)
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        
        # Check cache (but skip if it contains error messages)
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(minutes=cache_minutes):
                with open(cache_file) as f:
                    cached = json.load(f)
                    # Don't return cached errors
                    if "Error Message" in cached or "Note" in cached or "Information" in cached:
                        pass  # Fetch fresh
                    else:
                        return cached
        
        # Fetch fresh data
        try:
            url = self._build_url(params)
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors (don't cache these)
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if "Note" in data:
                raise ValueError(f"API Rate Limit: {data['Note']}")
            if "Information" in data and "demo" in data["Information"].lower():
                raise ValueError(f"Demo API key limitation. Please set ALPHA_VANTAGE_API_KEY env var with a real API key from https://www.alphavantage.co/support/#api-key")
            
            # Cache successful result only
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return data
            
        except Exception as e:
            print(f"Error fetching AlphaVantage data: {e}")
            # Return cached data if available
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        """
        Get real-time exchange rate with bid/ask spread
        
        Args:
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'USD')
        
        Returns:
            Dict with exchange_rate, bid_price, ask_price, timestamp
        
        Example:
            >>> fx = AlphaVantageFX()
            >>> rate = fx.get_exchange_rate('EUR', 'USD')
            >>> print(f"EUR/USD: {rate['exchange_rate']}")
        """
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper()
        }
        
        data = self._fetch_data(params, cache_minutes=1)  # Real-time = 1min cache
        
        if "Realtime Currency Exchange Rate" not in data:
            raise ValueError(f"Invalid response for {from_currency}/{to_currency}")
        
        rate_data = data["Realtime Currency Exchange Rate"]
        
        return {
            "from_currency": rate_data["1. From_Currency Code"],
            "to_currency": rate_data["3. To_Currency Code"],
            "exchange_rate": float(rate_data["5. Exchange Rate"]),
            "bid_price": float(rate_data.get("8. Bid Price", rate_data["5. Exchange Rate"])),
            "ask_price": float(rate_data.get("9. Ask Price", rate_data["5. Exchange Rate"])),
            "timestamp": rate_data["6. Last Refreshed"],
            "timezone": rate_data.get("7. Time Zone", "UTC")
        }
    
    def get_fx_intraday(self, from_symbol: str, to_symbol: str, 
                        interval: str = "5min", outputsize: str = "compact") -> pd.DataFrame:
        """
        Get intraday FX time series
        
        Args:
            from_symbol: Source currency (e.g., 'EUR')
            to_symbol: Target currency (e.g., 'USD')
            interval: Time interval - 1min, 5min, 15min, 30min, 60min
            outputsize: 'compact' (last 100 points) or 'full' (all available)
        
        Returns:
            DataFrame with timestamp, open, high, low, close columns
        """
        if interval not in self.VALID_INTERVALS:
            raise ValueError(f"Invalid interval. Must be one of {self.VALID_INTERVALS}")
        
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "interval": interval,
            "outputsize": outputsize
        }
        
        data = self._fetch_data(params)
        
        # Parse time series data
        ts_key = f"Time Series FX ({interval})"
        if ts_key not in data:
            raise ValueError(f"No intraday data for {from_symbol}/{to_symbol}")
        
        records = []
        for timestamp, values in data[ts_key].items():
            records.append({
                "timestamp": pd.to_datetime(timestamp),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"])
            })
        
        df = pd.DataFrame(records)
        df.sort_values("timestamp", inplace=True)
        df.set_index("timestamp", inplace=True)
        
        return df
    
    def get_fx_daily(self, from_symbol: str, to_symbol: str, 
                     outputsize: str = "compact") -> pd.DataFrame:
        """
        Get daily FX time series
        
        Args:
            from_symbol: Source currency (e.g., 'EUR')
            to_symbol: Target currency (e.g., 'USD')
            outputsize: 'compact' (last 100 days) or 'full' (20+ years)
        
        Returns:
            DataFrame with date, open, high, low, close columns
        """
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "outputsize": outputsize
        }
        
        data = self._fetch_data(params, cache_minutes=60)  # Daily = 1hr cache
        
        ts_key = "Time Series FX (Daily)"
        if ts_key not in data:
            raise ValueError(f"No daily data for {from_symbol}/{to_symbol}")
        
        records = []
        for date, values in data[ts_key].items():
            records.append({
                "date": pd.to_datetime(date),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"])
            })
        
        df = pd.DataFrame(records)
        df.sort_values("date", inplace=True)
        df.set_index("date", inplace=True)
        
        return df
    
    def get_fx_weekly(self, from_symbol: str, to_symbol: str) -> pd.DataFrame:
        """
        Get weekly FX time series
        
        Args:
            from_symbol: Source currency (e.g., 'EUR')
            to_symbol: Target currency (e.g., 'USD')
        
        Returns:
            DataFrame with date, open, high, low, close columns
        """
        params = {
            "function": "FX_WEEKLY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper()
        }
        
        data = self._fetch_data(params, cache_minutes=1440)  # Weekly = 24hr cache
        
        ts_key = "Time Series FX (Weekly)"
        if ts_key not in data:
            raise ValueError(f"No weekly data for {from_symbol}/{to_symbol}")
        
        records = []
        for date, values in data[ts_key].items():
            records.append({
                "date": pd.to_datetime(date),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"])
            })
        
        df = pd.DataFrame(records)
        df.sort_values("date", inplace=True)
        df.set_index("date", inplace=True)
        
        return df
    
    def get_fx_monthly(self, from_symbol: str, to_symbol: str) -> pd.DataFrame:
        """
        Get monthly FX time series
        
        Args:
            from_symbol: Source currency (e.g., 'EUR')
            to_symbol: Target currency (e.g., 'USD')
        
        Returns:
            DataFrame with date, open, high, low, close columns
        """
        params = {
            "function": "FX_MONTHLY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper()
        }
        
        data = self._fetch_data(params, cache_minutes=1440)  # Monthly = 24hr cache
        
        ts_key = "Time Series FX (Monthly)"
        if ts_key not in data:
            raise ValueError(f"No monthly data for {from_symbol}/{to_symbol}")
        
        records = []
        for date, values in data[ts_key].items():
            records.append({
                "date": pd.to_datetime(date),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"])
            })
        
        df = pd.DataFrame(records)
        df.sort_values("date", inplace=True)
        df.set_index("date", inplace=True)
        
        return df


# Convenience functions for direct import
def get_exchange_rate(from_currency: str, to_currency: str, api_key: Optional[str] = None) -> Dict:
    """Get real-time exchange rate"""
    fx = AlphaVantageFX(api_key=api_key)
    return fx.get_exchange_rate(from_currency, to_currency)


def get_fx_intraday(from_symbol: str, to_symbol: str, interval: str = "5min", 
                    outputsize: str = "compact", api_key: Optional[str] = None) -> pd.DataFrame:
    """Get intraday FX time series"""
    fx = AlphaVantageFX(api_key=api_key)
    return fx.get_fx_intraday(from_symbol, to_symbol, interval, outputsize)


def get_fx_daily(from_symbol: str, to_symbol: str, outputsize: str = "compact", 
                 api_key: Optional[str] = None) -> pd.DataFrame:
    """Get daily FX time series"""
    fx = AlphaVantageFX(api_key=api_key)
    return fx.get_fx_daily(from_symbol, to_symbol, outputsize)


def get_fx_weekly(from_symbol: str, to_symbol: str, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get weekly FX time series"""
    fx = AlphaVantageFX(api_key=api_key)
    return fx.get_fx_weekly(from_symbol, to_symbol)


def get_fx_monthly(from_symbol: str, to_symbol: str, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get monthly FX time series"""
    fx = AlphaVantageFX(api_key=api_key)
    return fx.get_fx_monthly(from_symbol, to_symbol)


if __name__ == "__main__":
    # Quick test
    fx = AlphaVantageFX()
    try:
        rate = fx.get_exchange_rate("EUR", "USD")
        print(json.dumps(rate, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
