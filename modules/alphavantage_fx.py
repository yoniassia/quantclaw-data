"""
AlphaVantage FX — Foreign Exchange Rates & Technical Indicators

Data Source: Alpha Vantage API
Update: Real-time / Intraday / Daily / Weekly
Free Tier: 500 API calls/day, 5 calls/minute (requires free API key)
Coverage: 160+ currency pairs, major and emerging markets

Provides:
- Real-time FX quotes
- Intraday rates (1min, 5min, 15min, 30min, 60min)
- Daily/weekly/monthly historical rates
- Technical indicators (SMA, EMA, RSI) for currency pairs
- Currency exchange conversions

API Key: Get free key at https://www.alphavantage.co/support/#api-key
"""

import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/alphavantage_fx")
os.makedirs(CACHE_DIR, exist_ok=True)

# Try to get API key from environment or config
API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

def get_fx_rate(from_currency: str = "EUR", to_currency: str = "USD") -> Dict:
    """
    Get real-time exchange rate for a currency pair.
    
    Args:
        from_currency: Base currency code (e.g., 'EUR', 'GBP')
        to_currency: Quote currency code (e.g., 'USD', 'JPY')
    
    Returns:
        Dict with exchange rate and metadata
    """
    cache_key = f"{from_currency}_{to_currency}_realtime"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # Cache for 5 minutes (real-time data)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(minutes=5):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "Realtime Currency Exchange Rate" in data:
            rate_data = data["Realtime Currency Exchange Rate"]
            result = {
                "from_currency": rate_data.get("1. From_Currency Code"),
                "to_currency": rate_data.get("3. To_Currency Code"),
                "exchange_rate": float(rate_data.get("5. Exchange Rate", 0)),
                "last_refreshed": rate_data.get("6. Last Refreshed"),
                "time_zone": rate_data.get("7. Time Zone"),
                "bid_price": float(rate_data.get("8. Bid Price", 0)),
                "ask_price": float(rate_data.get("9. Ask Price", 0))
            }
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        else:
            return {"error": "No data returned", "raw": data}
    
    except Exception as e:
        return {"error": str(e)}


def get_fx_intraday(from_currency: str = "EUR", to_currency: str = "USD", 
                    interval: str = "5min", outputsize: str = "compact") -> List[Dict]:
    """
    Get intraday FX time series.
    
    Args:
        from_currency: Base currency
        to_currency: Quote currency
        interval: Time interval ('1min', '5min', '15min', '30min', '60min')
        outputsize: 'compact' (last 100 points) or 'full' (full history)
    
    Returns:
        List of dicts with timestamp and OHLC data
    """
    cache_key = f"{from_currency}_{to_currency}_intraday_{interval}_{outputsize}"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # Cache intraday for 15 minutes
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(minutes=15):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        time_series_key = f"Time Series FX ({interval})"
        
        if time_series_key in data:
            time_series = data[time_series_key]
            result = []
            
            for timestamp, values in time_series.items():
                result.append({
                    "timestamp": timestamp,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0))
                })
            
            # Sort by timestamp descending
            result.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        else:
            return [{"error": "No time series data", "raw": data}]
    
    except Exception as e:
        return [{"error": str(e)}]


def get_fx_daily(from_currency: str = "EUR", to_currency: str = "USD",
                 outputsize: str = "compact") -> List[Dict]:
    """
    Get daily FX time series.
    
    Args:
        from_currency: Base currency
        to_currency: Quote currency
        outputsize: 'compact' (last 100 days) or 'full' (20+ years)
    
    Returns:
        List of dicts with date and OHLC data
    """
    cache_key = f"{from_currency}_{to_currency}_daily_{outputsize}"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # Cache daily data for 1 day
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize,
            "apikey": API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "Time Series FX (Daily)" in data:
            time_series = data["Time Series FX (Daily)"]
            result = []
            
            for date, values in time_series.items():
                result.append({
                    "date": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0))
                })
            
            # Sort by date descending
            result.sort(key=lambda x: x["date"], reverse=True)
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        else:
            return [{"error": "No time series data", "raw": data}]
    
    except Exception as e:
        return [{"error": str(e)}]


def get_fx_weekly(from_currency: str = "EUR", to_currency: str = "USD") -> List[Dict]:
    """
    Get weekly FX time series.
    
    Args:
        from_currency: Base currency
        to_currency: Quote currency
    
    Returns:
        List of dicts with week end date and OHLC data
    """
    cache_key = f"{from_currency}_{to_currency}_weekly"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # Cache weekly data for 7 days
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            "function": "FX_WEEKLY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "Time Series FX (Weekly)" in data:
            time_series = data["Time Series FX (Weekly)"]
            result = []
            
            for date, values in time_series.items():
                result.append({
                    "week_end": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0))
                })
            
            # Sort by date descending
            result.sort(key=lambda x: x["week_end"], reverse=True)
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        else:
            return [{"error": "No time series data", "raw": data}]
    
    except Exception as e:
        return [{"error": str(e)}]


def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        Dict with converted amount and exchange rate
    """
    rate_data = get_fx_rate(from_currency, to_currency)
    
    if "error" not in rate_data and "exchange_rate" in rate_data:
        exchange_rate = rate_data["exchange_rate"]
        converted = amount * exchange_rate
        
        return {
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": round(converted, 2),
            "to_currency": to_currency,
            "exchange_rate": exchange_rate,
            "timestamp": rate_data.get("last_refreshed")
        }
    else:
        return {"error": "Could not fetch exchange rate", "details": rate_data}


# Example usage and testing
if __name__ == "__main__":
    # Test real-time rate
    print("=== EUR/USD Real-Time ===")
    rate = get_fx_rate("EUR", "USD")
    print(json.dumps(rate, indent=2))
    
    # Test conversion
    print("\n=== Convert 1000 EUR to USD ===")
    conversion = convert_currency(1000, "EUR", "USD")
    print(json.dumps(conversion, indent=2))
    
    # Test intraday
    print("\n=== EUR/USD Intraday (last 5 data points) ===")
    intraday = get_fx_intraday("EUR", "USD", interval="5min", outputsize="compact")
    for point in intraday[:5]:
        print(point)
    
    # Test daily
    print("\n=== EUR/USD Daily (last 5 days) ===")
    daily = get_fx_daily("EUR", "USD", outputsize="compact")
    for day in daily[:5]:
        print(day)
