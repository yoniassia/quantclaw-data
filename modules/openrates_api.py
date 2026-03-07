#!/usr/bin/env python3
"""
OpenRates API — Foreign Exchange Rate Data Module

Provides free FX rate data for currency conversion and analysis.
Uses frankfurter.app (ECB rates) as primary source - no API key required.
Covers 30+ currencies with historical data back to 1999.

Source: https://api.frankfurter.app (European Central Bank data)
Category: FX & Rates
Free tier: True
Update frequency: Daily (ECB business days)
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union


# Frankfurter API Configuration
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"


def get_latest_rates(base: str = 'USD', symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get latest foreign exchange rates
    
    Args:
        base: Base currency (default 'USD')
        symbols: Target currency or list of currencies (None = all currencies)
    
    Returns:
        Dict with latest rates, date, and base currency
        
    Example:
        >>> get_latest_rates('USD', 'EUR')
        {'success': True, 'base': 'USD', 'date': '2026-03-07', 'rates': {'EUR': 0.92}}
        
        >>> get_latest_rates('USD', ['EUR', 'GBP', 'JPY'])
        {'success': True, 'base': 'USD', 'rates': {'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5}}
    """
    try:
        url = f"{FRANKFURTER_BASE_URL}/latest"
        params = {'from': base.upper()}
        
        # Handle symbols parameter
        if symbols:
            if isinstance(symbols, list):
                params['to'] = ','.join([s.upper() for s in symbols])
            else:
                params['to'] = symbols.upper()
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'base': data.get('base'),
            'date': data.get('date'),
            'rates': data.get('rates', {}),
            'count': len(data.get('rates', {})),
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'base': base
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'base': base
        }


def get_historical_rates(date: str, base: str = 'USD', symbols: Optional[Union[str, List[str]]] = None) -> Dict:
    """
    Get historical foreign exchange rates for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format
        base: Base currency (default 'USD')
        symbols: Target currency or list of currencies (None = all currencies)
    
    Returns:
        Dict with historical rates for the specified date
        
    Example:
        >>> get_historical_rates('2026-01-01', 'USD', 'EUR')
        {'success': True, 'base': 'USD', 'date': '2026-01-01', 'rates': {'EUR': 0.91}}
    """
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        
        url = f"{FRANKFURTER_BASE_URL}/{date}"
        params = {'from': base.upper()}
        
        # Handle symbols parameter
        if symbols:
            if isinstance(symbols, list):
                params['to'] = ','.join([s.upper() for s in symbols])
            else:
                params['to'] = symbols.upper()
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'base': data.get('base'),
            'date': data.get('date'),
            'rates': data.get('rates', {}),
            'count': len(data.get('rates', {})),
            'timestamp': datetime.now().isoformat()
        }
    
    except ValueError:
        return {
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'date': date
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'date': date
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'date': date
        }


def get_rate_timeseries(
    base: str = 'USD',
    target: str = 'EUR',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """
    Get time series of exchange rates between two currencies
    
    Args:
        base: Base currency (default 'USD')
        target: Target currency (default 'EUR')
        start_date: Start date YYYY-MM-DD (default: 90 days ago)
        end_date: End date YYYY-MM-DD (default: today)
    
    Returns:
        Dict with time series data, statistics, and trend analysis
        
    Example:
        >>> get_rate_timeseries('USD', 'EUR', '2026-01-01', '2026-03-01')
        {'success': True, 'base': 'USD', 'target': 'EUR', 'rates': [...], 'stats': {...}}
    """
    try:
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Validate dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt >= end_dt:
            return {
                'success': False,
                'error': 'start_date must be before end_date'
            }
        
        url = f"{FRANKFURTER_BASE_URL}/{start_date}..{end_date}"
        params = {
            'from': base.upper(),
            'to': target.upper()
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        rates_dict = data.get('rates', {})
        
        # Convert to time series format
        timeseries = []
        values = []
        for date, rate_data in sorted(rates_dict.items()):
            rate = rate_data.get(target.upper(), 0)
            timeseries.append({
                'date': date,
                'rate': rate
            })
            values.append(rate)
        
        # Calculate statistics
        stats = {}
        if values:
            stats = {
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'latest': values[-1] if values else 0,
                'first': values[0] if values else 0,
                'change': values[-1] - values[0] if len(values) > 1 else 0,
                'change_pct': ((values[-1] - values[0]) / values[0] * 100) if len(values) > 1 and values[0] != 0 else 0,
                'volatility': max(values) - min(values) if values else 0
            }
        
        return {
            'success': True,
            'base': base.upper(),
            'target': target.upper(),
            'start_date': start_date,
            'end_date': end_date,
            'rates': timeseries,
            'count': len(timeseries),
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
    
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid date format: {str(e)}'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def convert(amount: float, from_currency: str, to_currency: str) -> Dict:
    """
    Convert amount from one currency to another using latest rates
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
    
    Returns:
        Dict with converted amount, rate, and calculation details
        
    Example:
        >>> convert(100, 'USD', 'EUR')
        {'success': True, 'from': 'USD', 'to': 'EUR', 'amount': 100, 'converted': 92.0, 'rate': 0.92}
    """
    try:
        if amount <= 0:
            return {
                'success': False,
                'error': 'Amount must be positive'
            }
        
        # Get latest rate
        rate_data = get_latest_rates(from_currency.upper(), to_currency.upper())
        
        if not rate_data['success']:
            return {
                'success': False,
                'error': f"Could not fetch rate: {rate_data.get('error', 'Unknown error')}"
            }
        
        rates = rate_data.get('rates', {})
        to_currency_upper = to_currency.upper()
        
        if to_currency_upper not in rates:
            return {
                'success': False,
                'error': f'Currency {to_currency_upper} not found in rates'
            }
        
        rate = rates[to_currency_upper]
        converted_amount = amount * rate
        
        return {
            'success': True,
            'from': from_currency.upper(),
            'to': to_currency_upper,
            'amount': amount,
            'converted': round(converted_amount, 2),
            'rate': rate,
            'date': rate_data.get('date'),
            'calculation': f'{amount} {from_currency.upper()} × {rate} = {converted_amount:.2f} {to_currency_upper}',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_available_currencies() -> Dict:
    """
    Get list of all supported currencies
    
    Returns:
        Dict with list of currency codes and count
        
    Example:
        >>> get_available_currencies()
        {'success': True, 'currencies': ['EUR', 'USD', 'JPY', ...], 'count': 32}
    """
    try:
        url = f"{FRANKFURTER_BASE_URL}/currencies"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract currency codes and names
        currencies = []
        currency_details = []
        
        for code, name in data.items():
            currencies.append(code)
            currency_details.append({
                'code': code,
                'name': name
            })
        
        return {
            'success': True,
            'currencies': sorted(currencies),
            'currency_details': sorted(currency_details, key=lambda x: x['code']),
            'count': len(currencies),
            'source': 'European Central Bank via Frankfurter API',
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("OpenRates API - Foreign Exchange Rate Data")
    print("=" * 60)
    
    # Show available currencies
    currencies = get_available_currencies()
    if currencies['success']:
        print(f"\n✓ Available Currencies: {currencies['count']}")
        print(f"  {', '.join(currencies['currencies'][:10])}...")
    
    # Get latest USD rates
    print("\n" + "=" * 60)
    print("Latest USD Exchange Rates")
    print("=" * 60)
    latest = get_latest_rates('USD', ['EUR', 'GBP', 'JPY', 'CNY'])
    print(json.dumps(latest, indent=2))
    
    # Currency conversion example
    print("\n" + "=" * 60)
    print("Currency Conversion Example")
    print("=" * 60)
    conversion = convert(100, 'USD', 'EUR')
    print(json.dumps(conversion, indent=2))
    
    # Time series example
    print("\n" + "=" * 60)
    print("USD/EUR Time Series (Last 30 days)")
    print("=" * 60)
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end = datetime.now().strftime('%Y-%m-%d')
    timeseries = get_rate_timeseries('USD', 'EUR', start, end)
    
    if timeseries['success']:
        print(f"Period: {timeseries['start_date']} to {timeseries['end_date']}")
        print(f"Data points: {timeseries['count']}")
        print(f"\nStatistics:")
        for key, value in timeseries['stats'].items():
            print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
