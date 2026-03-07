#!/usr/bin/env python3
"""
Alpha Vantage Commodities API — Real-time & Historical Commodity Prices

Provides access to real-time and historical data for physical commodities including:
- Energy: WTI crude oil, Brent crude oil, natural gas
- Metals: Copper, aluminum
- Agriculture: Wheat, corn, cotton, sugar, coffee

Source: https://www.alphavantage.co/documentation/#commodities
Category: Commodities & Energy
Free tier: True (500 calls/day, 5 calls/min - requires ALPHA_VANTAGE_API_KEY)
Update frequency: Real-time/intraday for prices, daily for historical
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Literal
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

# ========== COMMODITY SYMBOLS REGISTRY ==========

COMMODITY_SYMBOLS = {
    # Energy
    'WTI': {'function': 'WTI', 'name': 'WTI Crude Oil', 'unit': 'USD per barrel'},
    'BRENT': {'function': 'BRENT', 'name': 'Brent Crude Oil', 'unit': 'USD per barrel'},
    'NATURAL_GAS': {'function': 'NATURAL_GAS', 'name': 'Henry Hub Natural Gas', 'unit': 'USD per MMBtu'},
    
    # Metals
    'COPPER': {'function': 'COPPER', 'name': 'Global Copper', 'unit': 'USD per pound'},
    'ALUMINUM': {'function': 'ALUMINUM', 'name': 'Global Aluminum', 'unit': 'USD per pound'},
    
    # Agriculture
    'WHEAT': {'function': 'WHEAT', 'name': 'Global Wheat', 'unit': 'USD per bushel'},
    'CORN': {'function': 'CORN', 'name': 'Global Corn', 'unit': 'USD per bushel'},
    'COTTON': {'function': 'COTTON', 'name': 'Global Cotton', 'unit': 'USD per pound'},
    'SUGAR': {'function': 'SUGAR', 'name': 'Global Sugar', 'unit': 'USD per pound'},
    'COFFEE': {'function': 'COFFEE', 'name': 'Global Coffee', 'unit': 'USD per pound'}
}

IntervalType = Literal["daily", "weekly", "monthly"]


# ========== CORE API FUNCTIONS ==========

def get_commodity_price(
    commodity: str,
    interval: IntervalType = "monthly"
) -> Dict:
    """
    Fetch price data for a specific commodity.
    
    Args:
        commodity: Commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER')
        interval: Data interval - 'daily', 'weekly', or 'monthly' (default: 'monthly')
    
    Returns:
        dict: {
            'commodity': str,
            'name': str,
            'unit': str,
            'interval': str,
            'data': [{'date': str, 'value': float}, ...],
            'latest_price': float,
            'latest_date': str
        }
    
    Raises:
        ValueError: If commodity symbol is invalid
        requests.RequestException: If API call fails
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment")
    
    commodity = commodity.upper()
    if commodity not in COMMODITY_SYMBOLS:
        raise ValueError(f"Invalid commodity symbol: {commodity}. Use list_commodities() to see available options.")
    
    commodity_info = COMMODITY_SYMBOLS[commodity]
    
    try:
        params = {
            'function': commodity_info['function'],
            'interval': interval,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            raise ValueError(f"API Error: {data['Error Message']}")
        if 'Note' in data:
            raise ValueError(f"API Rate Limit: {data['Note']}")
        
        # Parse the response - Alpha Vantage returns data with 'data' key
        if 'data' not in data:
            raise ValueError(f"Unexpected API response format: {list(data.keys())}")
        
        raw_data = data['data']
        parsed_data = []
        
        for item in raw_data:
            parsed_data.append({
                'date': item.get('date'),
                'value': float(item.get('value', 0))
            })
        
        # Sort by date descending (newest first)
        parsed_data.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'commodity': commodity,
            'name': commodity_info['name'],
            'unit': commodity_info['unit'],
            'interval': interval,
            'data': parsed_data,
            'latest_price': parsed_data[0]['value'] if parsed_data else None,
            'latest_date': parsed_data[0]['date'] if parsed_data else None,
            'retrieved_at': datetime.utcnow().isoformat()
        }
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch {commodity} data: {str(e)}")


def get_wti_crude(interval: IntervalType = "monthly") -> Dict:
    """
    Fetch WTI (West Texas Intermediate) crude oil prices.
    
    Args:
        interval: Data interval - 'daily', 'weekly', or 'monthly' (default: 'monthly')
    
    Returns:
        dict: WTI crude oil price data with historical series
    """
    return get_commodity_price('WTI', interval=interval)


def get_brent_crude(interval: IntervalType = "monthly") -> Dict:
    """
    Fetch Brent crude oil prices.
    
    Args:
        interval: Data interval - 'daily', 'weekly', or 'monthly' (default: 'monthly')
    
    Returns:
        dict: Brent crude oil price data with historical series
    """
    return get_commodity_price('BRENT', interval=interval)


def get_natural_gas(interval: IntervalType = "monthly") -> Dict:
    """
    Fetch Henry Hub natural gas prices.
    
    Args:
        interval: Data interval - 'daily', 'weekly', or 'monthly' (default: 'monthly')
    
    Returns:
        dict: Natural gas price data with historical series
    """
    return get_commodity_price('NATURAL_GAS', interval=interval)


def get_commodity_summary() -> Dict:
    """
    Get latest prices for all available commodities.
    
    Returns:
        dict: {
            'timestamp': str,
            'commodities': {
                'WTI': {'name': str, 'price': float, 'unit': str, 'date': str},
                'BRENT': {...},
                ...
            },
            'count': int
        }
    
    Note: Makes multiple API calls - be mindful of rate limits (5 calls/min)
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment")
    
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'commodities': {},
        'count': 0,
        'errors': []
    }
    
    for symbol in COMMODITY_SYMBOLS.keys():
        try:
            data = get_commodity_price(symbol, interval='monthly')
            summary['commodities'][symbol] = {
                'name': data['name'],
                'price': data['latest_price'],
                'unit': data['unit'],
                'date': data['latest_date']
            }
            summary['count'] += 1
        except Exception as e:
            summary['errors'].append({
                'symbol': symbol,
                'error': str(e)
            })
    
    return summary


def list_commodities() -> List[Dict[str, str]]:
    """
    List all available commodity symbols with metadata.
    
    Returns:
        list: [
            {
                'symbol': 'WTI',
                'name': 'WTI Crude Oil',
                'unit': 'USD per barrel',
                'category': 'Energy'
            },
            ...
        ]
    """
    commodities = []
    
    # Define categories
    categories = {
        'WTI': 'Energy',
        'BRENT': 'Energy',
        'NATURAL_GAS': 'Energy',
        'COPPER': 'Metals',
        'ALUMINUM': 'Metals',
        'WHEAT': 'Agriculture',
        'CORN': 'Agriculture',
        'COTTON': 'Agriculture',
        'SUGAR': 'Agriculture',
        'COFFEE': 'Agriculture'
    }
    
    for symbol, info in COMMODITY_SYMBOLS.items():
        commodities.append({
            'symbol': symbol,
            'name': info['name'],
            'unit': info['unit'],
            'category': categories.get(symbol, 'Unknown')
        })
    
    return commodities


# ========== UTILITY FUNCTIONS ==========

def check_api_key() -> bool:
    """
    Check if Alpha Vantage API key is configured.
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    return bool(ALPHA_VANTAGE_API_KEY)


def get_api_info() -> Dict:
    """
    Get information about the API configuration and limits.
    
    Returns:
        dict: API configuration details
    """
    return {
        'api_name': 'Alpha Vantage Commodities API',
        'base_url': ALPHA_VANTAGE_BASE_URL,
        'api_key_configured': check_api_key(),
        'rate_limits': {
            'calls_per_day': 500,
            'calls_per_minute': 5
        },
        'available_commodities': len(COMMODITY_SYMBOLS),
        'documentation': 'https://www.alphavantage.co/documentation/#commodities'
    }


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    # Show module info
    if len(sys.argv) == 1 or sys.argv[1] == '--info':
        print(json.dumps(get_api_info(), indent=2))
        sys.exit(0)
    
    # List commodities
    if sys.argv[1] == '--list':
        print(json.dumps(list_commodities(), indent=2))
        sys.exit(0)
    
    # Get commodity price
    if sys.argv[1] == '--get' and len(sys.argv) >= 3:
        commodity = sys.argv[2]
        interval = sys.argv[3] if len(sys.argv) > 3 else 'monthly'
        try:
            data = get_commodity_price(commodity, interval)
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # Get summary
    if sys.argv[1] == '--summary':
        try:
            summary = get_commodity_summary()
            print(json.dumps(summary, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # Show usage
    print("Usage:")
    print("  python alpha_vantage_commodities_api.py --info           # Show API info")
    print("  python alpha_vantage_commodities_api.py --list           # List commodities")
    print("  python alpha_vantage_commodities_api.py --get WTI monthly # Get commodity price")
    print("  python alpha_vantage_commodities_api.py --summary        # Get all latest prices")
