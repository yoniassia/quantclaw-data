#!/usr/bin/env python3
"""
OpenExchangeRates API — Foreign Exchange & Currency Data Module

Core OpenExchangeRates integration for currency exchange data including:
- Real-time exchange rates for 200+ currencies
- Historical exchange rates with date-specific queries
- Currency metadata and supported currency list
- API usage statistics
- Currency conversion utilities

Source: https://openexchangerates.org/api/
Category: FX & Rates
Free tier: True - 1,000 requests per month, base=USD only (requires OPENEXCHANGERATES_APP_ID env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# OpenExchangeRates API Configuration
BASE_URL = "https://openexchangerates.org/api"
APP_ID = os.environ.get("OPENEXCHANGERATES_APP_ID", "")


def get_latest_rates(base: str = 'USD', symbols: Optional[str] = None) -> Dict:
    """
    Get the latest exchange rates.
    
    Args:
        base: Base currency code (default: 'USD', free tier supports USD only)
        symbols: Comma-separated currency codes to limit results (optional)
    
    Returns:
        Dict with keys: disclaimer, license, timestamp, base, rates (dict of currency:rate)
    
    Example:
        >>> rates = get_latest_rates()
        >>> print(f"EUR rate: {rates['rates']['EUR']}")
        >>> rates_limited = get_latest_rates(symbols='EUR,GBP,JPY')
    """
    try:
        url = f"{BASE_URL}/latest.json"
        params = {
            'app_id': APP_ID,
            'base': base.upper()
        }
        
        if symbols:
            params['symbols'] = symbols.upper()
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['timestamp_dt'] = datetime.fromtimestamp(data.get('timestamp', 0)).isoformat() if data.get('timestamp') else None
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'base': base}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'base': base}


def get_historical_rates(date_str: str, base: str = 'USD', symbols: Optional[str] = None) -> Dict:
    """
    Get historical exchange rates for a specific date.
    
    Args:
        date_str: Date in YYYY-MM-DD format (e.g., '2026-03-01')
        base: Base currency code (default: 'USD', free tier supports USD only)
        symbols: Comma-separated currency codes to limit results (optional)
    
    Returns:
        Dict with keys: disclaimer, license, timestamp, historical (bool), base, rates
    
    Example:
        >>> rates = get_historical_rates('2026-02-01')
        >>> print(f"EUR on Feb 1: {rates['rates']['EUR']}")
        >>> rates_limited = get_historical_rates('2026-02-01', symbols='EUR,GBP')
    """
    try:
        url = f"{BASE_URL}/historical/{date_str}.json"
        params = {
            'app_id': APP_ID,
            'base': base.upper()
        }
        
        if symbols:
            params['symbols'] = symbols.upper()
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['timestamp_dt'] = datetime.fromtimestamp(data.get('timestamp', 0)).isoformat() if data.get('timestamp') else None
        data['date_requested'] = date_str
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'date': date_str, 'base': base}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'date': date_str, 'base': base}


def get_currencies() -> Dict:
    """
    Get list of all available currency codes and names.
    
    No authentication required for this endpoint.
    
    Returns:
        Dict mapping currency codes to full currency names
    
    Example:
        >>> currencies = get_currencies()
        >>> print(f"USD: {currencies['USD']}")
        >>> print(f"Total currencies: {len(currencies)}")
    """
    try:
        url = f"{BASE_URL}/currencies.json"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_usage() -> Dict:
    """
    Get API usage statistics for the current month.
    
    Returns:
        Dict with keys: status, data (usage info including requests_made, requests_quota, etc.)
    
    Example:
        >>> usage = get_usage()
        >>> print(f"Used: {usage['data']['usage']['requests']} of {usage['data']['plan']['quota']}")
    """
    try:
        url = f"{BASE_URL}/usage.json"
        params = {
            'app_id': APP_ID
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def convert(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert an amount from one currency to another using latest rates.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
    
    Returns:
        Dict with keys: amount, from, to, rate, result, timestamp
    
    Example:
        >>> result = convert(100, 'USD', 'EUR')
        >>> print(f"100 USD = {result['result']} EUR")
        >>> print(f"Rate: {result['rate']}")
    """
    try:
        # Get latest rates with USD as base
        rates_data = get_latest_rates(base='USD')
        
        if 'error' in rates_data:
            return rates_data
        
        rates = rates_data.get('rates', {})
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Handle USD as base
        if from_currency == 'USD':
            if to_currency not in rates:
                return {'error': f'Currency {to_currency} not found'}
            rate = rates[to_currency]
            result = amount * rate
        elif to_currency == 'USD':
            if from_currency not in rates:
                return {'error': f'Currency {from_currency} not found'}
            rate = 1 / rates[from_currency]
            result = amount * rate
        else:
            # Convert via USD: from -> USD -> to
            if from_currency not in rates or to_currency not in rates:
                return {'error': f'One or both currencies not found'}
            # Convert to USD first, then to target
            usd_amount = amount / rates[from_currency]
            result = usd_amount * rates[to_currency]
            rate = rates[to_currency] / rates[from_currency]
        
        return {
            'amount': amount,
            'from': from_currency,
            'to': to_currency,
            'rate': rate,
            'result': result,
            'timestamp': rates_data.get('timestamp'),
            'timestamp_dt': rates_data.get('timestamp_dt')
        }
        
    except Exception as e:
        return {'error': f'Conversion error: {str(e)}', 'amount': amount, 'from': from_currency, 'to': to_currency}


if __name__ == "__main__":
    # Test basic functionality
    print("OpenExchangeRates Module Test")
    print("=" * 50)
    
    # Test 1: Get currencies (no key needed)
    print("\n1. Testing get_currencies()...")
    currencies = get_currencies()
    if 'error' not in currencies:
        print(f"✓ Found {len(currencies)} currencies")
        print(f"  Sample: USD = {currencies.get('USD', 'N/A')}")
        print(f"  Sample: EUR = {currencies.get('EUR', 'N/A')}")
    else:
        print(f"✗ Error: {currencies['error']}")
    
    # Test 2: Get latest rates (requires key)
    if APP_ID:
        print("\n2. Testing get_latest_rates()...")
        rates = get_latest_rates()
        if 'error' not in rates:
            print(f"✓ Latest rates retrieved")
            print(f"  Base: {rates.get('base', 'N/A')}")
            print(f"  Timestamp: {rates.get('timestamp_dt', 'N/A')}")
            print(f"  EUR: {rates.get('rates', {}).get('EUR', 'N/A')}")
            print(f"  GBP: {rates.get('rates', {}).get('GBP', 'N/A')}")
        else:
            print(f"✗ Error: {rates['error']}")
        
        # Test 3: Convert
        print("\n3. Testing convert()...")
        result = convert(100, 'USD', 'EUR')
        if 'error' not in result:
            print(f"✓ 100 USD = {result['result']:.2f} EUR")
            print(f"  Rate: {result['rate']:.4f}")
        else:
            print(f"✗ Error: {result['error']}")
    else:
        print("\n⚠ OPENEXCHANGERATES_APP_ID not set - skipping authenticated tests")
    
    print("\n" + "=" * 50)
