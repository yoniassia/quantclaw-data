#!/usr/bin/env python3
"""
Alpha Vantage Forex — Real-time and Historical Currency Exchange Rates

Provides comprehensive forex data for major currency pairs:
- Real-time exchange rates
- Intraday rates (1min, 5min, 15min, 30min, 60min)
- Daily, weekly, and monthly historical OHLC data
- Support for 150+ physical and digital currencies

Data Source: Alpha Vantage API
Update frequency: Real-time (rate limited to 5 API calls/min on free tier)
Free tier: Yes (demo key available, or set ALPHA_VANTAGE_API_KEY env var)
Category: FX & Rates

Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# Alpha Vantage Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# API Function Names
FUNCTIONS = {
    'exchange_rate': 'CURRENCY_EXCHANGE_RATE',
    'intraday': 'FX_INTRADAY',
    'daily': 'FX_DAILY',
    'weekly': 'FX_WEEKLY',
    'monthly': 'FX_MONTHLY'
}

# Valid intervals for intraday data
VALID_INTERVALS = ['1min', '5min', '15min', '30min', '60min']


def _make_request(params: Dict) -> Dict:
    """
    Internal helper to make requests to Alpha Vantage API.
    
    Args:
        params: Query parameters for the API request
        
    Returns:
        Dict containing API response or error information
    """
    params['apikey'] = API_KEY
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return {
                'error': True,
                'message': data['Error Message'],
                'source': 'Alpha Vantage API'
            }
        
        if 'Note' in data:
            # Rate limit message
            return {
                'error': True,
                'message': 'API rate limit reached. Free tier: 5 calls/min, 500 calls/day',
                'note': data['Note'],
                'source': 'Alpha Vantage API'
            }
        
        if 'Information' in data:
            # Demo key limitation or other info message
            return {
                'error': True,
                'message': 'API key limitation',
                'info': data['Information'],
                'suggestion': 'Set ALPHA_VANTAGE_API_KEY environment variable with your free API key',
                'source': 'Alpha Vantage API'
            }
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            'error': True,
            'message': f"Request failed: {str(e)}",
            'url': ALPHA_VANTAGE_BASE_URL
        }
    except json.JSONDecodeError as e:
        return {
            'error': True,
            'message': f"Invalid JSON response: {str(e)}"
        }


def get_exchange_rate(from_currency: str, to_currency: str) -> Dict:
    """
    Get real-time exchange rate between two currencies.
    
    Args:
        from_currency: The currency to convert from (e.g., 'USD', 'EUR', 'BTC')
        to_currency: The currency to convert to (e.g., 'JPY', 'GBP', 'ETH')
        
    Returns:
        Dict containing:
            - from_currency: Source currency code
            - to_currency: Target currency code
            - exchange_rate: Current exchange rate
            - last_refreshed: Timestamp of last update
            - timezone: Timezone of the timestamp
            - bid_price: Bid price
            - ask_price: Ask price
            
    Example:
        >>> rate = get_exchange_rate('USD', 'EUR')
        >>> print(f"1 USD = {rate['exchange_rate']} EUR")
    """
    params = {
        'function': FUNCTIONS['exchange_rate'],
        'from_currency': from_currency.upper(),
        'to_currency': to_currency.upper()
    }
    
    result = _make_request(params)
    
    if 'error' in result:
        return result
    
    # Parse real-time exchange rate data
    if 'Realtime Currency Exchange Rate' in result:
        data = result['Realtime Currency Exchange Rate']
        
        return {
            'from_currency': data.get('1. From_Currency Code', from_currency),
            'from_currency_name': data.get('2. From_Currency Name', ''),
            'to_currency': data.get('3. To_Currency Code', to_currency),
            'to_currency_name': data.get('4. To_Currency Name', ''),
            'exchange_rate': float(data.get('5. Exchange Rate', 0)),
            'last_refreshed': data.get('6. Last Refreshed', ''),
            'timezone': data.get('7. Time Zone', 'UTC'),
            'bid_price': float(data.get('8. Bid Price', 0)),
            'ask_price': float(data.get('9. Ask Price', 0)),
            'source': 'Alpha Vantage',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return {
        'error': True,
        'message': 'Unexpected API response format',
        'raw_response': result
    }


def get_intraday_rates(from_currency: str, to_currency: str, 
                       interval: str = '5min', outputsize: str = 'compact') -> Dict:
    """
    Get intraday time series (OHLC) for currency pair.
    
    Args:
        from_currency: The currency to convert from (e.g., 'EUR', 'GBP')
        to_currency: The currency to convert to (e.g., 'USD', 'JPY')
        interval: Time interval between data points. 
                 Valid: '1min', '5min', '15min', '30min', '60min'
                 Default: '5min'
        outputsize: 'compact' (latest 100 data points) or 'full' (up to 30 days)
                   Default: 'compact'
        
    Returns:
        Dict containing:
            - metadata: Information about the time series
            - time_series: List of OHLC data points
            
    Example:
        >>> rates = get_intraday_rates('EUR', 'USD', interval='5min')
        >>> latest = rates['time_series'][0]
        >>> print(f"Latest EUR/USD: {latest['close']}")
    """
    if interval not in VALID_INTERVALS:
        return {
            'error': True,
            'message': f"Invalid interval '{interval}'. Valid: {VALID_INTERVALS}"
        }
    
    params = {
        'function': FUNCTIONS['intraday'],
        'from_symbol': from_currency.upper(),
        'to_symbol': to_currency.upper(),
        'interval': interval,
        'outputsize': outputsize
    }
    
    result = _make_request(params)
    
    if 'error' in result:
        return result
    
    # Parse intraday time series
    metadata_key = 'Meta Data'
    timeseries_key = f'Time Series FX ({interval})'
    
    if metadata_key in result and timeseries_key in result:
        metadata = result[metadata_key]
        timeseries = result[timeseries_key]
        
        # Convert to list of dicts
        data_points = []
        for timestamp, values in timeseries.items():
            data_points.append({
                'timestamp': timestamp,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0))
            })
        
        # Sort by timestamp (most recent first)
        data_points.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'metadata': {
                'from_currency': metadata.get('2. From Symbol', from_currency),
                'to_currency': metadata.get('3. To Symbol', to_currency),
                'last_refreshed': metadata.get('4. Last Refreshed', ''),
                'interval': metadata.get('5. Interval', interval),
                'outputsize': metadata.get('6. Output Size', outputsize),
                'timezone': metadata.get('7. Time Zone', 'UTC')
            },
            'time_series': data_points,
            'count': len(data_points),
            'source': 'Alpha Vantage'
        }
    
    return {
        'error': True,
        'message': 'Unexpected API response format',
        'raw_response': result
    }


def get_daily_rates(from_currency: str, to_currency: str, 
                    outputsize: str = 'compact') -> Dict:
    """
    Get daily time series (OHLC) for currency pair.
    
    Args:
        from_currency: The currency to convert from (e.g., 'USD', 'EUR')
        to_currency: The currency to convert to (e.g., 'JPY', 'GBP')
        outputsize: 'compact' (latest 100 data points) or 'full' (20+ years)
                   Default: 'compact'
        
    Returns:
        Dict containing:
            - metadata: Information about the time series
            - time_series: List of daily OHLC data points
            
    Example:
        >>> rates = get_daily_rates('USD', 'JPY')
        >>> print(f"Latest close: {rates['time_series'][0]['close']}")
    """
    params = {
        'function': FUNCTIONS['daily'],
        'from_symbol': from_currency.upper(),
        'to_symbol': to_currency.upper(),
        'outputsize': outputsize
    }
    
    result = _make_request(params)
    
    if 'error' in result:
        return result
    
    # Parse daily time series
    metadata_key = 'Meta Data'
    timeseries_key = 'Time Series FX (Daily)'
    
    if metadata_key in result and timeseries_key in result:
        metadata = result[metadata_key]
        timeseries = result[timeseries_key]
        
        # Convert to list of dicts
        data_points = []
        for date, values in timeseries.items():
            data_points.append({
                'date': date,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0))
            })
        
        # Sort by date (most recent first)
        data_points.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'metadata': {
                'from_currency': metadata.get('2. From Symbol', from_currency),
                'to_currency': metadata.get('3. To Symbol', to_currency),
                'last_refreshed': metadata.get('4. Last Refreshed', ''),
                'outputsize': metadata.get('5. Output Size', outputsize),
                'timezone': metadata.get('6. Time Zone', 'UTC')
            },
            'time_series': data_points,
            'count': len(data_points),
            'source': 'Alpha Vantage'
        }
    
    return {
        'error': True,
        'message': 'Unexpected API response format',
        'raw_response': result
    }


def get_weekly_rates(from_currency: str, to_currency: str) -> Dict:
    """
    Get weekly time series (OHLC) for currency pair.
    
    Args:
        from_currency: The currency to convert from (e.g., 'EUR', 'GBP')
        to_currency: The currency to convert to (e.g., 'USD', 'JPY')
        
    Returns:
        Dict containing:
            - metadata: Information about the time series
            - time_series: List of weekly OHLC data points (20+ years of data)
            
    Example:
        >>> rates = get_weekly_rates('EUR', 'USD')
        >>> print(f"Data points: {rates['count']}")
    """
    params = {
        'function': FUNCTIONS['weekly'],
        'from_symbol': from_currency.upper(),
        'to_symbol': to_currency.upper()
    }
    
    result = _make_request(params)
    
    if 'error' in result:
        return result
    
    # Parse weekly time series
    metadata_key = 'Meta Data'
    timeseries_key = 'Time Series FX (Weekly)'
    
    if metadata_key in result and timeseries_key in result:
        metadata = result[metadata_key]
        timeseries = result[timeseries_key]
        
        # Convert to list of dicts
        data_points = []
        for date, values in timeseries.items():
            data_points.append({
                'date': date,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0))
            })
        
        # Sort by date (most recent first)
        data_points.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'metadata': {
                'from_currency': metadata.get('2. From Symbol', from_currency),
                'to_currency': metadata.get('3. To Symbol', to_currency),
                'last_refreshed': metadata.get('4. Last Refreshed', ''),
                'timezone': metadata.get('5. Time Zone', 'UTC')
            },
            'time_series': data_points,
            'count': len(data_points),
            'source': 'Alpha Vantage'
        }
    
    return {
        'error': True,
        'message': 'Unexpected API response format',
        'raw_response': result
    }


def get_monthly_rates(from_currency: str, to_currency: str) -> Dict:
    """
    Get monthly time series (OHLC) for currency pair.
    
    Args:
        from_currency: The currency to convert from (e.g., 'USD', 'EUR')
        to_currency: The currency to convert to (e.g., 'JPY', 'GBP')
        
    Returns:
        Dict containing:
            - metadata: Information about the time series
            - time_series: List of monthly OHLC data points (20+ years of data)
            
    Example:
        >>> rates = get_monthly_rates('USD', 'EUR')
        >>> trend = [r['close'] for r in rates['time_series'][:12]]  # Last year
    """
    params = {
        'function': FUNCTIONS['monthly'],
        'from_symbol': from_currency.upper(),
        'to_symbol': to_currency.upper()
    }
    
    result = _make_request(params)
    
    if 'error' in result:
        return result
    
    # Parse monthly time series
    metadata_key = 'Meta Data'
    timeseries_key = 'Time Series FX (Monthly)'
    
    if metadata_key in result and timeseries_key in result:
        metadata = result[metadata_key]
        timeseries = result[timeseries_key]
        
        # Convert to list of dicts
        data_points = []
        for date, values in timeseries.items():
            data_points.append({
                'date': date,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0))
            })
        
        # Sort by date (most recent first)
        data_points.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'metadata': {
                'from_currency': metadata.get('2. From Symbol', from_currency),
                'to_currency': metadata.get('3. To Symbol', to_currency),
                'last_refreshed': metadata.get('4. Last Refreshed', ''),
                'timezone': metadata.get('5. Time Zone', 'UTC')
            },
            'time_series': data_points,
            'count': len(data_points),
            'source': 'Alpha Vantage'
        }
    
    return {
        'error': True,
        'message': 'Unexpected API response format',
        'raw_response': result
    }


# === CLI Commands ===

def cli_rate(from_curr: str, to_curr: str):
    """CLI: Get real-time exchange rate"""
    data = get_exchange_rate(from_curr, to_curr)
    print(json.dumps(data, indent=2))


def cli_intraday(from_curr: str, to_curr: str, interval: str = '5min'):
    """CLI: Get intraday rates"""
    data = get_intraday_rates(from_curr, to_curr, interval=interval)
    print(json.dumps(data, indent=2))


def cli_daily(from_curr: str, to_curr: str):
    """CLI: Get daily rates"""
    data = get_daily_rates(from_curr, to_curr)
    print(json.dumps(data, indent=2))


def cli_weekly(from_curr: str, to_curr: str):
    """CLI: Get weekly rates"""
    data = get_weekly_rates(from_curr, to_curr)
    print(json.dumps(data, indent=2))


def cli_monthly(from_curr: str, to_curr: str):
    """CLI: Get monthly rates"""
    data = get_monthly_rates(from_curr, to_curr)
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: alpha_vantage_forex.py <command> <args>")
        print("Commands:")
        print("  rate <FROM> <TO>           - Real-time exchange rate")
        print("  intraday <FROM> <TO> [INT] - Intraday rates (interval: 1min/5min/15min/30min/60min)")
        print("  daily <FROM> <TO>          - Daily rates")
        print("  weekly <FROM> <TO>         - Weekly rates")
        print("  monthly <FROM> <TO>        - Monthly rates")
        print("\nExample: alpha_vantage_forex.py rate USD EUR")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        'rate': cli_rate,
        'intraday': cli_intraday,
        'daily': cli_daily,
        'weekly': cli_weekly,
        'monthly': cli_monthly
    }
    
    if command in commands:
        try:
            commands[command](*sys.argv[2:])
        except TypeError as e:
            print(f"Error: {e}")
            print("Check command arguments")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
