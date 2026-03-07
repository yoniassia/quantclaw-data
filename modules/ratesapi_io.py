#!/usr/bin/env python3
"""
RatesAPI (Frankfurter) — FX & Rates Data Module

Foreign exchange rates data integration for:
- Real-time spot FX rates
- Historical FX rates
- Rate time series data
- Currency conversion utilities

Source: https://api.frankfurter.app/ (ECB data)
Category: FX & Rates
Free tier: True (no API key required)
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

# FX Rates API Configuration
# Using Frankfurter (reliable ECB data source, no key required)
RATES_BASE_URL = "https://api.frankfurter.app"


def get_latest_rates(base: str = 'USD', symbols: Optional[str] = None) -> Dict:
    """
    Get latest foreign exchange rates.
    
    Args:
        base: Base currency code (default: 'USD')
        symbols: Comma-separated currency symbols (e.g., 'EUR,GBP')
                If None, returns all available currencies
    
    Returns:
        Dict with keys: amount, base, date, rates (dict of currency: rate)
    
    Example:
        >>> rates = get_latest_rates('USD', 'EUR,GBP')
        >>> print(f"EUR: {rates['rates']['EUR']}, GBP: {rates['rates']['GBP']}")
    """
    try:
        url = f"{RATES_BASE_URL}/latest"
        params = {'from': base}
        if symbols:
            params['to'] = symbols
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}


def get_historical_rates(date: str, base: str = 'USD', symbols: Optional[str] = None) -> Dict:
    """
    Get foreign exchange rates for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency code (default: 'USD')
        symbols: Comma-separated currency symbols (e.g., 'EUR,GBP')
                If None, returns all available currencies
    
    Returns:
        Dict with keys: amount, base, date, rates (dict of currency: rate)
    
    Example:
        >>> rates = get_historical_rates('2026-03-01', 'USD', 'EUR,GBP')
        >>> print(f"On {rates['date']}: EUR {rates['rates']['EUR']}")
    """
    try:
        url = f"{RATES_BASE_URL}/{date}"
        params = {'from': base}
        if symbols:
            params['to'] = symbols
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}


def get_rate_timeseries(start_date: str, end_date: str, base: str = 'USD', symbols: Optional[str] = None) -> Dict:
    """
    Get foreign exchange rate time series over a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base: Base currency code (default: 'USD')
        symbols: Comma-separated currency symbols (e.g., 'EUR,GBP')
                If None, returns all available currencies
    
    Returns:
        Dict with keys: amount, base, start_date, end_date, 
                       rates (dict of date: {currency: rate})
    
    Example:
        >>> series = get_rate_timeseries('2026-03-01', '2026-03-05', 'USD', 'EUR')
        >>> for date, rates in series['rates'].items():
        ...     print(f"{date}: EUR {rates['EUR']}")
    """
    try:
        url = f"{RATES_BASE_URL}/{start_date}..{end_date}"
        params = {'from': base}
        if symbols:
            params['to'] = symbols
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert amount from one currency to another using latest rates.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
    
    Returns:
        Dict with keys: amount, from, to, rate, converted_amount, date
    
    Example:
        >>> result = convert_currency(100, 'USD', 'EUR')
        >>> print(f"${result['amount']} USD = €{result['converted_amount']} EUR")
        >>> print(f"Rate: {result['rate']} on {result['date']}")
    """
    try:
        url = f"{RATES_BASE_URL}/latest"
        params = {
            'amount': amount,
            'from': from_currency,
            'to': to_currency
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Calculate converted amount and rate
        converted = data['rates'].get(to_currency, 0)
        rate = converted / amount if amount > 0 else 0
        
        return {
            'amount': amount,
            'from': from_currency,
            'to': to_currency,
            'rate': rate,
            'converted_amount': converted,
            'date': data['date']
        }
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    # Quick test
    print("Testing RatesAPI module...")
    
    print("\n1. Latest rates (USD -> EUR,GBP):")
    latest = get_latest_rates('USD', 'EUR,GBP')
    print(json.dumps(latest, indent=2))
    
    print("\n2. Historical rates (2026-03-01):")
    historical = get_historical_rates('2026-03-01', 'USD', 'EUR,GBP')
    print(json.dumps(historical, indent=2))
    
    print("\n3. Currency conversion (100 USD -> EUR):")
    conversion = convert_currency(100, 'USD', 'EUR')
    print(json.dumps(conversion, indent=2))
