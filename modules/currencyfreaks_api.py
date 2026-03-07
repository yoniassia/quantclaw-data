#!/usr/bin/env python3
"""
CurrencyFreaks API — Real-time and Historical FX Rates

CurrencyFreaks offers a free-tier API for real-time and historical forex rates covering 180+ currencies,
with additional support for cryptocurrency conversions. High-accuracy data from multiple sources for
quant analysis, including volatility indicators.

Source: https://currencyfreaks.com/
Category: FX & Rates
Free tier: 1000 requests per month, no credit card required; API key needed
Update frequency: real-time updates every 60 seconds
Author: QuantClaw Data NightBuilder
Phase: NightBuilder

Fallback: Uses exchangerate.host when no API key available
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# CurrencyFreaks API Configuration
CURRENCYFREAKS_BASE_URL = "https://api.currencyfreaks.com/v2.0"
CURRENCYFREAKS_API_KEY = os.environ.get("CURRENCYFREAKS_API_KEY", "")

# Primary Fallback API (free, no key required)
FALLBACK_BASE_URL = "https://api.frankfurter.app"

# Alternative fallback (now requires key, kept for reference)
EXCHANGERATE_BASE_URL = "https://api.exchangerate.host"


def _get_with_currencyfreaks(endpoint: str, params: Dict) -> Dict:
    """
    Fetch data from CurrencyFreaks API (requires API key)
    
    Args:
        endpoint: API endpoint (e.g., 'rates/latest')
        params: Query parameters
    
    Returns:
        Dict with API response or error
    """
    if not CURRENCYFREAKS_API_KEY:
        return {
            "success": False,
            "error": "CURRENCYFREAKS_API_KEY not set",
            "fallback_available": True
        }
    
    try:
        url = f"{CURRENCYFREAKS_BASE_URL}/{endpoint}"
        params["apikey"] = CURRENCYFREAKS_API_KEY
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "data": data,
            "source": "currencyfreaks"
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "fallback_available": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback_available": True
        }


def _get_with_fallback(endpoint_type: str, params: Dict) -> Dict:
    """
    Fetch data from fallback API (frankfurter.app - free, no key required)
    
    Args:
        endpoint_type: Type of request ('latest', 'historical', 'symbols', 'convert', 'timeseries')
        params: Query parameters
    
    Returns:
        Dict with API response or error
    """
    try:
        # Use Frankfurter API (free, open, no key required)
        if endpoint_type == 'latest':
            url = f"{FALLBACK_BASE_URL}/latest"
            params_fallback = {"from": params.get("base", "USD")}
            if "symbols" in params and params["symbols"]:
                params_fallback["to"] = params["symbols"]
        
        elif endpoint_type == 'historical':
            date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
            url = f"{FALLBACK_BASE_URL}/{date}"
            params_fallback = {"from": params.get("base", "USD")}
            if "symbols" in params and params["symbols"]:
                params_fallback["to"] = params["symbols"]
        
        elif endpoint_type == 'symbols':
            url = f"{FALLBACK_BASE_URL}/currencies"
            params_fallback = {}
        
        elif endpoint_type == 'convert':
            # Frankfurter doesn't have convert endpoint, use latest rates
            url = f"{FALLBACK_BASE_URL}/latest"
            params_fallback = {
                "from": params.get("from", "USD"),
                "to": params.get("to", "EUR")
            }
        
        elif endpoint_type == 'timeseries':
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            url = f"{FALLBACK_BASE_URL}/{start_date}..{end_date}"
            params_fallback = {"from": params.get("base", "USD")}
            if "symbols" in params and params["symbols"]:
                params_fallback["to"] = params["symbols"]
        
        else:
            return {
                "success": False,
                "error": f"Unknown endpoint type: {endpoint_type}"
            }
        
        response = requests.get(url, params=params_fallback, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Normalize response to match CurrencyFreaks format
        if endpoint_type in ['latest', 'historical']:
            normalized = {
                "date": data.get("date"),
                "base": data.get("base"),
                "rates": data.get("rates", {})
            }
        elif endpoint_type == 'symbols':
            # Frankfurter returns {code: name} dict directly
            normalized = {
                "symbols": data
            }
        elif endpoint_type == 'convert':
            # Calculate from latest rates
            normalized = {
                "result": data.get("rates", {}).get(params.get("to", "EUR"), 0) * params.get("amount", 1),
                "info": {
                    "rate": data.get("rates", {}).get(params.get("to", "EUR"), 0)
                }
            }
        elif endpoint_type == 'timeseries':
            normalized = {
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "base": data.get("base"),
                "rates": data.get("rates", {})
            }
        else:
            normalized = data
        
        return {
            "success": True,
            "data": normalized,
            "source": "frankfurter.app (fallback)"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Fallback API failed: {str(e)}"
        }


def get_latest_rates(base: str = 'USD', symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get latest FX rates
    
    Args:
        base: Base currency (default 'USD')
        symbols: Optional currency codes to filter (string or list)
    
    Returns:
        Dict with latest rates, date, and metadata
    
    Example:
        >>> result = get_latest_rates('USD', ['EUR', 'GBP', 'JPY'])
        >>> print(result['data']['rates']['EUR'])
    """
    params = {"base": base}
    
    if symbols:
        if isinstance(symbols, list):
            symbols = ",".join(symbols)
        params["symbols"] = symbols
    
    # Try CurrencyFreaks first
    result = _get_with_currencyfreaks("rates/latest", params)
    
    # Fall back if needed
    if not result["success"] and result.get("fallback_available"):
        result = _get_with_fallback("latest", params)
    
    if result["success"]:
        result["timestamp"] = datetime.now().isoformat()
    
    return result


def get_historical_rates(date: str, base: str = 'USD', symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get historical FX rates for specific date
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency (default 'USD')
        symbols: Optional currency codes to filter (string or list)
    
    Returns:
        Dict with historical rates for specified date
    
    Example:
        >>> result = get_historical_rates('2024-01-15', 'USD', ['EUR', 'GBP'])
        >>> print(result['data']['rates'])
    """
    params = {
        "date": date,
        "base": base
    }
    
    if symbols:
        if isinstance(symbols, list):
            symbols = ",".join(symbols)
        params["symbols"] = symbols
    
    # Try CurrencyFreaks first
    result = _get_with_currencyfreaks("rates/historical", params)
    
    # Fall back if needed
    if not result["success"] and result.get("fallback_available"):
        result = _get_with_fallback("historical", params)
    
    if result["success"]:
        result["timestamp"] = datetime.now().isoformat()
    
    return result


def get_supported_currencies() -> Dict:
    """
    Get list of all supported currencies
    
    Returns:
        Dict with currency codes and names
    
    Example:
        >>> result = get_supported_currencies()
        >>> print(len(result['data']['symbols']))
    """
    # Try CurrencyFreaks first
    result = _get_with_currencyfreaks("supported-currencies", {})
    
    # Fall back if needed
    if not result["success"] and result.get("fallback_available"):
        result = _get_with_fallback("symbols", {})
    
    if result["success"]:
        result["timestamp"] = datetime.now().isoformat()
    
    return result


def convert(amount: float, from_currency: str, to_currency: str, date: Optional[str] = None) -> Dict:
    """
    Convert amount from one currency to another
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        date: Optional date for historical conversion (YYYY-MM-DD)
    
    Returns:
        Dict with converted amount and rate
    
    Example:
        >>> result = convert(100, 'USD', 'EUR')
        >>> print(f"100 USD = {result['converted_amount']:.2f} EUR")
    """
    try:
        # Get rates for the conversion
        if date:
            rates_result = get_historical_rates(date, from_currency, to_currency)
        else:
            rates_result = get_latest_rates(from_currency, to_currency)
        
        if not rates_result["success"]:
            return rates_result
        
        rates = rates_result["data"].get("rates", {})
        
        if to_currency not in rates:
            return {
                "success": False,
                "error": f"Currency {to_currency} not found in rates"
            }
        
        rate = rates[to_currency]
        converted_amount = amount * rate
        
        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "converted_amount": converted_amount,
            "date": rates_result["data"].get("date"),
            "source": rates_result.get("source"),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Conversion error: {str(e)}"
        }


def get_rate_timeseries(
    from_currency: str,
    to_currency: str,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get rate history/timeseries between two currencies
    
    Args:
        from_currency: Base currency code
        to_currency: Target currency code
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with daily rates for the period
    
    Example:
        >>> result = get_rate_timeseries('USD', 'EUR', '2024-01-01', '2024-01-31')
        >>> for date, rate in result['data']['rates'].items():
        ...     print(f"{date}: {rate}")
    """
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "base": from_currency,
        "symbols": to_currency
    }
    
    # Try fallback (CurrencyFreaks doesn't have timeseries endpoint in free tier)
    result = _get_with_fallback("timeseries", params)
    
    if result["success"]:
        # Calculate statistics
        rates_data = result["data"].get("rates", {})
        if rates_data:
            values = []
            for date_key, rate_dict in rates_data.items():
                if to_currency in rate_dict:
                    values.append(rate_dict[to_currency])
            
            if values:
                result["statistics"] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values)
                }
        
        result["timestamp"] = datetime.now().isoformat()
    
    return result


def get_volatility(from_currency: str, to_currency: str, days: int = 30) -> Dict:
    """
    Calculate volatility for currency pair over period
    
    Args:
        from_currency: Base currency code
        to_currency: Target currency code
        days: Number of days for volatility calculation (default 30)
    
    Returns:
        Dict with volatility metrics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        result = get_rate_timeseries(
            from_currency,
            to_currency,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if not result["success"]:
            return result
        
        # Extract rates
        rates_data = result["data"].get("rates", {})
        rates = []
        dates = []
        
        for date_key in sorted(rates_data.keys()):
            rate_dict = rates_data[date_key]
            if to_currency in rate_dict:
                rates.append(rate_dict[to_currency])
                dates.append(date_key)
        
        if len(rates) < 2:
            return {
                "success": False,
                "error": "Insufficient data for volatility calculation"
            }
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(rates)):
            daily_return = (rates[i] - rates[i-1]) / rates[i-1]
            returns.append(daily_return)
        
        # Calculate volatility (standard deviation of returns)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        # Annualized volatility (assuming 252 trading days)
        annualized_volatility = volatility * (252 ** 0.5)
        
        return {
            "success": True,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "period_days": len(rates),
            "daily_volatility": volatility,
            "annualized_volatility": annualized_volatility,
            "mean_daily_return": mean_return,
            "latest_rate": rates[-1],
            "period_return": (rates[-1] - rates[0]) / rates[0],
            "source": result.get("source"),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Volatility calculation error: {str(e)}"
        }


def get_cross_rate(from_currency: str, to_currency: str, via_currency: str = 'USD') -> Dict:
    """
    Calculate cross rate via intermediate currency (useful when direct pair not available)
    
    Args:
        from_currency: Source currency
        to_currency: Target currency
        via_currency: Intermediate currency (default USD)
    
    Returns:
        Dict with cross rate calculation
    """
    try:
        # Get both legs
        leg1 = get_latest_rates(via_currency, from_currency)
        leg2 = get_latest_rates(via_currency, to_currency)
        
        if not leg1["success"] or not leg2["success"]:
            return {
                "success": False,
                "error": "Failed to fetch rates for cross calculation"
            }
        
        rate1 = leg1["data"]["rates"].get(from_currency)
        rate2 = leg2["data"]["rates"].get(to_currency)
        
        if not rate1 or not rate2:
            return {
                "success": False,
                "error": "Currency not found in rates"
            }
        
        # Calculate cross rate
        cross_rate = rate2 / rate1
        
        return {
            "success": True,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "via_currency": via_currency,
            "cross_rate": cross_rate,
            "leg1_rate": rate1,
            "leg2_rate": rate2,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Cross rate calculation error: {str(e)}"
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("CurrencyFreaks API - FX Rates Module")
    print("=" * 60)
    
    # Check API key status
    if CURRENCYFREAKS_API_KEY:
        print(f"\n✓ API Key configured (using CurrencyFreaks)")
    else:
        print(f"\n⚠ No API Key - using free fallback (exchangerate.host)")
    
    # Test latest rates
    print("\n--- Latest Rates (USD base) ---")
    latest = get_latest_rates('USD', ['EUR', 'GBP', 'JPY'])
    if latest["success"]:
        print(f"Source: {latest.get('source')}")
        print(f"Date: {latest['data'].get('date')}")
        for currency, rate in latest["data"]["rates"].items():
            print(f"  {currency}: {rate}")
    else:
        print(f"Error: {latest.get('error')}")
    
    # Test conversion
    print("\n--- Convert 100 USD to EUR ---")
    conv = convert(100, 'USD', 'EUR')
    if conv["success"]:
        print(f"100 USD = {conv['converted_amount']:.2f} EUR")
        print(f"Rate: {conv['rate']}")
        print(f"Source: {conv.get('source')}")
    else:
        print(f"Error: {conv.get('error')}")
    
    # Test volatility
    print("\n--- EUR/USD 30-day Volatility ---")
    vol = get_volatility('USD', 'EUR', days=30)
    if vol["success"]:
        print(f"Daily Volatility: {vol['daily_volatility']*100:.4f}%")
        print(f"Annualized Volatility: {vol['annualized_volatility']*100:.2f}%")
        print(f"Period Return: {vol['period_return']*100:.2f}%")
    else:
        print(f"Error: {vol.get('error')}")
    
    print("\n" + "=" * 60)
