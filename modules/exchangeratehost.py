"""
Exchangerate.host — Free Foreign Exchange Rates API

Data Source: https://frankfurter.app/ (ECB-based, truly free alternative)
Update: Daily rates from European Central Bank
Free: Yes (unlimited requests, no API key required)
History: Historical data available from 1999+

Provides:
- Live exchange rates for 30+ major currencies
- Historical rates by date
- Currency conversion
- Time-series data
- Supported currencies list

Base currency options: EUR (default), USD, GBP, JPY, CHF, etc.
Note: Uses Frankfurter API (open-source, ECB data, no rate limits)
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union


BASE_URL = "https://api.frankfurter.app"


def _fetch_json(url: str) -> Dict:
    """
    Internal helper to fetch JSON from exchangerate.host API.
    
    Args:
        url: Full API endpoint URL
        
    Returns:
        Parsed JSON response as dict
        
    Raises:
        Exception with error details if request fails
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "QuantClaw/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check for API error in response
            if not data.get("success", True):
                error_msg = data.get("error", {}).get("info", "Unknown API error")
                return {"error": error_msg, "success": False}
                
            return data
            
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "success": False}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "success": False}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}", "success": False}


def get_latest_rates(base: str = "USD", symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get current exchange rates for a base currency.
    
    Args:
        base: Base currency code (default: USD)
        symbols: Optional list of currency codes to limit results (e.g., ["EUR", "GBP"])
                or comma-separated string "EUR,GBP"
                
    Returns:
        Dict with rates, timestamp, and base currency:
        {
            "success": True,
            "base": "USD",
            "date": "2026-03-06",
            "rates": {
                "EUR": 0.92,
                "GBP": 0.79,
                ...
            }
        }
    """
    url = f"{BASE_URL}/latest?from={base.upper()}"
    
    # Handle symbols parameter (Frankfurter uses 'to' instead of 'symbols')
    if symbols:
        if isinstance(symbols, list):
            symbols_str = ",".join([s.upper() for s in symbols])
        else:
            symbols_str = symbols.upper()
        url += f"&to={symbols_str}"
    
    result = _fetch_json(url)
    
    # Normalize response to match expected format
    if "rates" in result:
        result["success"] = True
    
    return result


def convert_currency(from_curr: str, to_curr: str, amount: float = 1.0, 
                     date: Optional[str] = None) -> Dict:
    """
    Convert amount from one currency to another.
    
    Args:
        from_curr: Source currency code (e.g., "USD")
        to_curr: Target currency code (e.g., "EUR")
        amount: Amount to convert (default: 1.0)
        date: Optional date for historical conversion (YYYY-MM-DD)
        
    Returns:
        Dict with conversion result:
        {
            "success": True,
            "query": {
                "from": "USD",
                "to": "EUR",
                "amount": 100
            },
            "info": {
                "rate": 0.92
            },
            "result": 92.0,
            "date": "2026-03-06"
        }
    """
    # Frankfurter uses: /latest?from=USD&to=EUR&amount=100
    # Or for historical: /2025-01-01?from=USD&to=EUR&amount=100
    
    if date:
        url = f"{BASE_URL}/{date}?from={from_curr.upper()}&to={to_curr.upper()}&amount={amount}"
    else:
        url = f"{BASE_URL}/latest?from={from_curr.upper()}&to={to_curr.upper()}&amount={amount}"
    
    result = _fetch_json(url)
    
    # Normalize response to match expected format
    if "rates" in result and to_curr.upper() in result["rates"]:
        rate = result["rates"][to_curr.upper()] / amount  # Calculate per-unit rate
        converted_amount = result["rates"][to_curr.upper()]
        
        result["success"] = True
        result["query"] = {
            "from": from_curr.upper(),
            "to": to_curr.upper(),
            "amount": amount
        }
        result["info"] = {
            "rate": rate
        }
        result["result"] = converted_amount
    
    return result


def get_historical_rates(date: str, base: str = "USD", 
                         symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get exchange rates for a specific historical date.
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency code (default: USD)
        symbols: Optional list of currency codes to limit results
        
    Returns:
        Dict with historical rates:
        {
            "success": True,
            "historical": True,
            "base": "USD",
            "date": "2025-01-15",
            "rates": {
                "EUR": 0.93,
                "GBP": 0.81,
                ...
            }
        }
    """
    url = f"{BASE_URL}/{date}?from={base.upper()}"
    
    # Handle symbols parameter (Frankfurter uses 'to')
    if symbols:
        if isinstance(symbols, list):
            symbols_str = ",".join([s.upper() for s in symbols])
        else:
            symbols_str = symbols.upper()
        url += f"&to={symbols_str}"
    
    result = _fetch_json(url)
    
    # Normalize response
    if "rates" in result:
        result["success"] = True
        result["historical"] = True
        result["base"] = base.upper()
    
    return result


def get_time_series(start_date: str, end_date: str, base: str = "USD",
                    symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get exchange rate time series between two dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base: Base currency code (default: USD)
        symbols: Optional list of currency codes to limit results
        
    Returns:
        Dict with time series data:
        {
            "success": True,
            "timeseries": True,
            "base": "USD",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "rates": {
                "2025-01-01": {"EUR": 0.93, "GBP": 0.81},
                "2025-01-02": {"EUR": 0.94, "GBP": 0.82},
                ...
            }
        }
    """
    # Frankfurter uses: /start_date..end_date?from=USD&to=EUR,GBP
    url = f"{BASE_URL}/{start_date}..{end_date}?from={base.upper()}"
    
    # Handle symbols parameter
    if symbols:
        if isinstance(symbols, list):
            symbols_str = ",".join([s.upper() for s in symbols])
        else:
            symbols_str = symbols.upper()
        url += f"&to={symbols_str}"
    
    result = _fetch_json(url)
    
    # Normalize response
    if "rates" in result:
        result["success"] = True
        result["timeseries"] = True
        result["base"] = base.upper()
    
    return result


def get_fluctuation(start_date: str, end_date: str, base: str = "USD",
                    symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get currency fluctuation data between two dates.
    Shows change and percentage change for each currency.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base: Base currency code (default: USD)
        symbols: Optional list of currency codes to limit results
        
    Returns:
        Dict with fluctuation data:
        {
            "success": True,
            "fluctuation": True,
            "base": "USD",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "rates": {
                "EUR": {
                    "start_rate": 0.93,
                    "end_rate": 0.92,
                    "change": -0.01,
                    "change_pct": -1.08
                },
                ...
            }
        }
    """
    # Get time series and calculate fluctuation
    ts_result = get_time_series(start_date, end_date, base, symbols)
    
    if not ts_result.get("success") or "rates" not in ts_result:
        return ts_result
    
    rates_by_date = ts_result["rates"]
    
    # Get first and last dates with data
    sorted_dates = sorted(rates_by_date.keys())
    if len(sorted_dates) < 2:
        return {
            "success": False,
            "error": "Insufficient data for fluctuation calculation"
        }
    
    first_date = sorted_dates[0]
    last_date = sorted_dates[-1]
    
    start_rates = rates_by_date[first_date]
    end_rates = rates_by_date[last_date]
    
    # Calculate fluctuation for each currency
    fluctuation_data = {}
    for currency in start_rates.keys():
        if currency in end_rates:
            start_rate = start_rates[currency]
            end_rate = end_rates[currency]
            change = end_rate - start_rate
            change_pct = (change / start_rate * 100) if start_rate != 0 else 0
            
            fluctuation_data[currency] = {
                "start_rate": round(start_rate, 6),
                "end_rate": round(end_rate, 6),
                "change": round(change, 6),
                "change_pct": round(change_pct, 2)
            }
    
    return {
        "success": True,
        "fluctuation": True,
        "base": base.upper(),
        "start_date": first_date,
        "end_date": last_date,
        "rates": fluctuation_data
    }


def get_supported_currencies() -> Dict:
    """
    Get list of all supported currency codes and names.
    
    Returns:
        Dict with all supported currencies:
        {
            "success": True,
            "symbols": {
                "USD": "United States Dollar",
                "EUR": "Euro",
                "GBP": "British Pound Sterling",
                ...
            }
        }
    """
    url = f"{BASE_URL}/currencies"
    result = _fetch_json(url)
    
    # Normalize response - Frankfurter returns currencies directly
    if isinstance(result, dict) and "error" not in result:
        return {
            "success": True,
            "symbols": result
        }
    
    return result


# Convenience aliases
latest_rates = get_latest_rates
historical_rates = get_historical_rates
time_series = get_time_series
fluctuation = get_fluctuation
supported_currencies = get_supported_currencies


if __name__ == "__main__":
    # Self-test
    print("Testing exchangeratehost module...\n")
    
    # Test 1: Latest rates
    print("1. Latest USD rates (EUR, GBP, JPY):")
    latest = get_latest_rates("USD", ["EUR", "GBP", "JPY"])
    if latest.get("success"):
        print(f"   Date: {latest.get('date')}")
        print(f"   Rates: {latest.get('rates')}")
    else:
        print(f"   Error: {latest.get('error')}")
    
    print("\n2. Convert 100 USD to EUR:")
    conversion = convert_currency("USD", "EUR", 100)
    if conversion.get("success"):
        rate = conversion.get("info", {}).get("rate", 0)
        result = conversion.get("result", 0)
        print(f"   Rate: {rate}")
        print(f"   Result: {result} EUR")
    else:
        print(f"   Error: {conversion.get('error')}")
    
    print("\n3. Get supported currencies (first 5):")
    symbols = get_supported_currencies()
    if symbols.get("success"):
        items = list(symbols.get("symbols", {}).items())[:5]
        for code, name in items:
            print(f"   {code}: {name}")
    else:
        print(f"   Error: {symbols.get('error')}")
    
    print("\nModule test complete!")
