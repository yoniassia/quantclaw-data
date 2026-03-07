#!/usr/bin/env python3
"""
Trading Economics Commodity API — Commodity Prices & Forecasts

Real-time commodity prices including energy (oil, gas), metals (gold, silver, copper),
and agriculture (wheat, corn, soybeans). Free tier provides 100 calls/day.

Source: https://tradingeconomics.com/api
Category: Commodities & Energy
Free tier: True (100 calls/day)
Update frequency: Real-time quotes, daily updates
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Trading Economics API Configuration
TE_BASE_URL = "https://api.tradingeconomics.com"
TE_API_KEY = os.environ.get("TRADING_ECONOMICS_API_KEY", "")

# Commodity categories mapping
COMMODITY_CATEGORIES = {
    'energy': ['crude-oil', 'brent-crude-oil', 'natural-gas', 'heating-oil', 'gasoline', 'coal'],
    'metals': ['gold', 'silver', 'copper', 'platinum', 'palladium', 'aluminum', 'zinc', 'nickel'],
    'agriculture': ['wheat', 'corn', 'soybeans', 'rice', 'sugar', 'coffee', 'cocoa', 'cotton']
}

# Sample data for when API key is not available (represents realistic 2026 prices)
SAMPLE_COMMODITY_DATA = [
    # Energy
    {"Symbol": "CL1:COM", "Name": "Crude Oil WTI", "Last": 72.45, "DailyChange": 1.23, "PercentageChange": 1.73, "Unit": "USD/BBL", "Category": "Energy"},
    {"Symbol": "CO1:COM", "Name": "Brent Crude Oil", "Last": 76.82, "DailyChange": 0.98, "PercentageChange": 1.29, "Unit": "USD/BBL", "Category": "Energy"},
    {"Symbol": "NG1:COM", "Name": "Natural Gas", "Last": 3.42, "DailyChange": -0.08, "PercentageChange": -2.29, "Unit": "USD/MMBtu", "Category": "Energy"},
    {"Symbol": "HO1:COM", "Name": "Heating Oil", "Last": 2.18, "DailyChange": 0.03, "PercentageChange": 1.40, "Unit": "USD/GAL", "Category": "Energy"},
    
    # Precious Metals
    {"Symbol": "GC1:COM", "Name": "Gold", "Last": 2842.50, "DailyChange": 18.40, "PercentageChange": 0.65, "Unit": "USD/OZ", "Category": "Metal"},
    {"Symbol": "SI1:COM", "Name": "Silver", "Last": 32.18, "DailyChange": 0.42, "PercentageChange": 1.32, "Unit": "USD/OZ", "Category": "Metal"},
    {"Symbol": "PL1:COM", "Name": "Platinum", "Last": 978.20, "DailyChange": -5.30, "PercentageChange": -0.54, "Unit": "USD/OZ", "Category": "Metal"},
    {"Symbol": "PA1:COM", "Name": "Palladium", "Last": 956.40, "DailyChange": 12.10, "PercentageChange": 1.28, "Unit": "USD/OZ", "Category": "Metal"},
    
    # Industrial Metals
    {"Symbol": "HG1:COM", "Name": "Copper", "Last": 4.32, "DailyChange": 0.07, "PercentageChange": 1.65, "Unit": "USD/LB", "Category": "Metal"},
    {"Symbol": "ALI1:COM", "Name": "Aluminum", "Last": 2587.00, "DailyChange": 15.50, "PercentageChange": 0.60, "Unit": "USD/MT", "Category": "Metal"},
    
    # Agriculture - Grains
    {"Symbol": "W 1:COM", "Name": "Wheat", "Last": 562.25, "DailyChange": -8.50, "PercentageChange": -1.49, "Unit": "USd/BU", "Category": "Agriculture"},
    {"Symbol": "C 1:COM", "Name": "Corn", "Last": 458.00, "DailyChange": 3.25, "PercentageChange": 0.71, "Unit": "USd/BU", "Category": "Agriculture"},
    {"Symbol": "S 1:COM", "Name": "Soybeans", "Last": 1042.50, "DailyChange": 12.75, "PercentageChange": 1.24, "Unit": "USd/BU", "Category": "Agriculture"},
    
    # Agriculture - Softs
    {"Symbol": "SB1:COM", "Name": "Sugar", "Last": 18.42, "DailyChange": -0.18, "PercentageChange": -0.97, "Unit": "USd/LB", "Category": "Agriculture"},
    {"Symbol": "KC1:COM", "Name": "Coffee", "Last": 325.45, "DailyChange": 5.20, "PercentageChange": 1.62, "Unit": "USd/LB", "Category": "Agriculture"},
    {"Symbol": "CC1:COM", "Name": "Cocoa", "Last": 9842.00, "DailyChange": -142.00, "PercentageChange": -1.42, "Unit": "USD/MT", "Category": "Agriculture"},
    {"Symbol": "CT1:COM", "Name": "Cotton", "Last": 68.52, "DailyChange": 0.87, "PercentageChange": 1.29, "Unit": "USd/LB", "Category": "Agriculture"},
]


def _make_request(endpoint: str, params: Optional[Dict] = None, api_key: Optional[str] = None) -> Dict:
    """
    Internal helper to make API requests with error handling
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        api_key: Optional API key override
        
    Returns:
        Dict with success flag and data or error message
    """
    try:
        # Use provided key or env var
        key = api_key or TE_API_KEY
        
        if not key:
            # Return sample data if no API key
            return {
                "success": True,
                "data": SAMPLE_COMMODITY_DATA,
                "timestamp": datetime.now().isoformat(),
                "source": "sample_data",
                "note": "Using sample data - set TRADING_ECONOMICS_API_KEY for live data"
            }
        
        # Build URL
        url = f"{TE_BASE_URL}{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        
        params['c'] = key
        
        # Make request
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "live_api"
        }
    
    except requests.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg = "Authentication failed - check TRADING_ECONOMICS_API_KEY"
        elif e.response.status_code == 429:
            error_msg = "Rate limit exceeded (100 calls/day for free tier)"
        
        return {
            "success": False,
            "error": error_msg,
            "status_code": e.response.status_code
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_commodity_prices(api_key: Optional[str] = None) -> Dict:
    """
    Get latest prices for all commodities
    
    Args:
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with commodity prices, categories, and changes
        
    Example:
        >>> prices = get_commodity_prices()
        >>> if prices['success']:
        ...     for item in prices['commodities'][:3]:
        ...         print(f"{item['Name']}: ${item['Last']}")
    """
    result = _make_request("/commodities", api_key=api_key)
    
    if not result['success']:
        return result
    
    commodities = result['data']
    
    # Organize by category
    categorized = {
        'energy': [],
        'metals': [],
        'agriculture': [],
        'other': []
    }
    
    for commodity in commodities:
        # Check both Symbol and Name fields, plus Category if present
        symbol = commodity.get('Symbol', '').lower()
        name = commodity.get('Name', '').lower()
        cat = commodity.get('Category', '').lower()
        
        category_assigned = False
        
        # First try direct category match
        if cat in ['energy', 'metal', 'agriculture']:
            category_map = {'metal': 'metals', 'energy': 'energy', 'agriculture': 'agriculture'}
            categorized[category_map.get(cat, cat)].append(commodity)
            category_assigned = True
        else:
            # Try keyword matching
            for category, items in COMMODITY_CATEGORIES.items():
                if any(item in name or item in symbol for item in items):
                    categorized[category].append(commodity)
                    category_assigned = True
                    break
        
        if not category_assigned:
            categorized['other'].append(commodity)
    
    # Extract key metrics
    summary = {
        'total_commodities': len(commodities),
        'energy_count': len(categorized['energy']),
        'metals_count': len(categorized['metals']),
        'agriculture_count': len(categorized['agriculture'])
    }
    
    return {
        'success': True,
        'commodities': commodities,
        'categorized': categorized,
        'summary': summary,
        'timestamp': result['timestamp'],
        'source': result.get('source', 'unknown'),
        'note': result.get('note', '')
    }


def get_commodity_history(commodity: str, start_date: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
    """
    Get historical prices for a specific commodity
    
    Args:
        commodity: Commodity symbol (e.g., 'crude-oil', 'gold', 'wheat')
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with historical price data and statistics
        
    Example:
        >>> history = get_commodity_history('gold', '2025-01-01')
        >>> if history['success']:
        ...     print(f"Gold stats: {history['statistics']}")
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Check if we have API key
    key = api_key or TE_API_KEY
    
    if not key:
        # Generate sample historical data
        base_price = 2800 if 'gold' in commodity.lower() else 70
        days = 90
        history = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            # Add some randomness
            import random
            variation = random.uniform(-0.02, 0.02)
            price = base_price * (1 + variation)
            history.append({
                'Date': date,
                'Price': round(price, 2)
            })
        
        prices = [item['Price'] for item in history]
        statistics = {
            'high': max(prices),
            'low': min(prices),
            'average': sum(prices) / len(prices),
            'latest': prices[-1],
            'change': prices[-1] - prices[0],
            'change_pct': ((prices[-1] - prices[0]) / prices[0] * 100)
        }
        
        return {
            'success': True,
            'commodity': commodity,
            'history': history,
            'statistics': statistics,
            'data_points': len(history),
            'start_date': start_date,
            'timestamp': datetime.now().isoformat(),
            'source': 'sample_data',
            'note': 'Using sample data - set TRADING_ECONOMICS_API_KEY for live data'
        }
    
    # Use real API
    params = {'d1': start_date}
    result = _make_request(f"/commodity/{commodity}", params=params, api_key=api_key)
    
    if not result['success']:
        return result
    
    history = result['data']
    
    if not history:
        return {
            'success': False,
            'error': f'No historical data found for {commodity}'
        }
    
    # Calculate statistics
    prices = [float(item.get('Price', 0)) for item in history if item.get('Price')]
    
    statistics = {}
    if prices:
        statistics = {
            'high': max(prices),
            'low': min(prices),
            'average': sum(prices) / len(prices),
            'latest': prices[-1] if prices else None,
            'change': prices[-1] - prices[0] if len(prices) > 1 else 0,
            'change_pct': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0
        }
    
    return {
        'success': True,
        'commodity': commodity,
        'history': history,
        'statistics': statistics,
        'data_points': len(history),
        'start_date': start_date,
        'timestamp': result['timestamp']
    }


def get_commodity_forecast(commodity: str, api_key: Optional[str] = None) -> Dict:
    """
    Get forecast data for a specific commodity
    
    Args:
        commodity: Commodity symbol (e.g., 'crude-oil', 'gold')
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with forecast data including quarterly predictions
        
    Example:
        >>> forecast = get_commodity_forecast('crude-oil')
        >>> if forecast['success']:
        ...     print(f"Mean forecast: ${forecast['forecast_summary']['mean_forecast']}")
    """
    key = api_key or TE_API_KEY
    
    if not key:
        # Generate sample forecast
        base_price = 2850 if 'gold' in commodity.lower() else 75
        forecasts = [
            {'Quarter': 'Q1 2026', 'Value': base_price * 1.01},
            {'Quarter': 'Q2 2026', 'Value': base_price * 1.02},
            {'Quarter': 'Q3 2026', 'Value': base_price * 1.03},
            {'Quarter': 'Q4 2026', 'Value': base_price * 1.04},
        ]
        
        forecast_values = [f['Value'] for f in forecasts]
        forecast_summary = {
            'mean_forecast': sum(forecast_values) / len(forecast_values),
            'min_forecast': min(forecast_values),
            'max_forecast': max(forecast_values),
            'forecast_range': max(forecast_values) - min(forecast_values)
        }
        
        return {
            'success': True,
            'commodity': commodity,
            'forecasts': forecasts,
            'forecast_summary': forecast_summary,
            'timestamp': datetime.now().isoformat(),
            'source': 'sample_data',
            'note': 'Using sample data - set TRADING_ECONOMICS_API_KEY for live data'
        }
    
    result = _make_request(f"/forecast/commodity/{commodity}", api_key=api_key)
    
    if not result['success']:
        return result
    
    forecasts = result['data']
    
    if not forecasts:
        return {
            'success': False,
            'error': f'No forecast data available for {commodity}'
        }
    
    # Extract forecast values
    forecast_values = []
    for item in forecasts:
        if 'Value' in item:
            forecast_values.append(float(item['Value']))
    
    forecast_summary = {}
    if forecast_values:
        forecast_summary = {
            'mean_forecast': sum(forecast_values) / len(forecast_values),
            'min_forecast': min(forecast_values),
            'max_forecast': max(forecast_values),
            'forecast_range': max(forecast_values) - min(forecast_values)
        }
    
    return {
        'success': True,
        'commodity': commodity,
        'forecasts': forecasts,
        'forecast_summary': forecast_summary,
        'timestamp': result['timestamp']
    }


def get_energy_prices(api_key: Optional[str] = None) -> Dict:
    """
    Get current prices for energy commodities (oil, gas, coal, etc.)
    
    Args:
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with energy commodity prices and market indicators
        
    Example:
        >>> energy = get_energy_prices()
        >>> if energy['success']:
        ...     print(f"WTI Crude: ${energy['key_indicators']['wti_crude_oil']['price']}")
    """
    result = get_commodity_prices(api_key=api_key)
    
    if not result['success']:
        return result
    
    energy_commodities = result['categorized']['energy']
    
    # Extract key energy indicators
    indicators = {}
    for commodity in energy_commodities:
        symbol = commodity.get('Symbol', '').lower()
        name = commodity.get('Name', '').lower()
        
        if 'wti' in name or ('crude' in name and 'brent' not in name):
            indicators['wti_crude_oil'] = {
                'price': commodity.get('Last', 0),
                'change': commodity.get('DailyChange', 0),
                'change_pct': commodity.get('PercentageChange', 0)
            }
        elif 'brent' in name:
            indicators['brent_crude_oil'] = {
                'price': commodity.get('Last', 0),
                'change': commodity.get('DailyChange', 0),
                'change_pct': commodity.get('PercentageChange', 0)
            }
        elif 'natural' in name and 'gas' in name:
            indicators['natural_gas'] = {
                'price': commodity.get('Last', 0),
                'change': commodity.get('DailyChange', 0),
                'change_pct': commodity.get('PercentageChange', 0)
            }
    
    return {
        'success': True,
        'energy_commodities': energy_commodities,
        'key_indicators': indicators,
        'count': len(energy_commodities),
        'timestamp': result['timestamp'],
        'source': result.get('source', 'unknown')
    }


def get_metals_prices(api_key: Optional[str] = None) -> Dict:
    """
    Get current prices for precious and industrial metals
    
    Args:
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with metals prices, precious metals spotlight, and industrial metals
        
    Example:
        >>> metals = get_metals_prices()
        >>> if metals['success']:
        ...     gold = metals['precious_metals'].get('gold', {})
        ...     print(f"Gold: ${gold.get('price', 'N/A')}")
    """
    result = get_commodity_prices(api_key=api_key)
    
    if not result['success']:
        return result
    
    metals_commodities = result['categorized']['metals']
    
    # Separate precious vs industrial
    precious_metals = {}
    industrial_metals = {}
    
    precious = ['gold', 'silver', 'platinum', 'palladium']
    
    for commodity in metals_commodities:
        symbol = commodity.get('Symbol', '').lower()
        name = commodity.get('Name', '').lower()
        
        metal_data = {
            'price': commodity.get('Last', 0),
            'change': commodity.get('DailyChange', 0),
            'change_pct': commodity.get('PercentageChange', 0),
            'unit': commodity.get('Unit', 'USD')
        }
        
        found = False
        for precious_metal in precious:
            if precious_metal in name:
                precious_metals[precious_metal] = metal_data
                found = True
                break
        
        if not found:
            # It's industrial
            metal_name = name.split()[-1] if ' ' in name else name
            industrial_metals[metal_name] = metal_data
    
    return {
        'success': True,
        'all_metals': metals_commodities,
        'precious_metals': precious_metals,
        'industrial_metals': industrial_metals,
        'count': len(metals_commodities),
        'timestamp': result['timestamp'],
        'source': result.get('source', 'unknown')
    }


def get_agriculture_prices(api_key: Optional[str] = None) -> Dict:
    """
    Get current prices for agricultural commodities (grains, softs)
    
    Args:
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with agriculture commodity prices organized by type
        
    Example:
        >>> ag = get_agriculture_prices()
        >>> if ag['success']:
        ...     print(f"Grains count: {len(ag['grains'])}")
    """
    result = get_commodity_prices(api_key=api_key)
    
    if not result['success']:
        return result
    
    ag_commodities = result['categorized']['agriculture']
    
    # Categorize into grains, softs, livestock
    grains = []
    softs = []
    livestock = []
    other_ag = []
    
    grain_keywords = ['wheat', 'corn', 'soybeans', 'soybean', 'rice', 'oats']
    soft_keywords = ['sugar', 'coffee', 'cocoa', 'cotton', 'orange']
    livestock_keywords = ['cattle', 'hogs', 'pork', 'beef']
    
    for commodity in ag_commodities:
        name = commodity.get('Name', '').lower()
        
        if any(kw in name for kw in grain_keywords):
            grains.append(commodity)
        elif any(kw in name for kw in soft_keywords):
            softs.append(commodity)
        elif any(kw in name for kw in livestock_keywords):
            livestock.append(commodity)
        else:
            other_ag.append(commodity)
    
    return {
        'success': True,
        'all_agriculture': ag_commodities,
        'grains': grains,
        'softs': softs,
        'livestock': livestock,
        'other': other_ag,
        'count': len(ag_commodities),
        'timestamp': result['timestamp'],
        'source': result.get('source', 'unknown')
    }


def list_all_commodities(api_key: Optional[str] = None) -> Dict:
    """
    List all available commodities with their symbols
    
    Args:
        api_key: Optional Trading Economics API key
        
    Returns:
        Dict with commodity list organized by category
    """
    result = get_commodity_prices(api_key=api_key)
    
    if not result['success']:
        return result
    
    commodity_list = []
    for commodity in result['commodities']:
        commodity_list.append({
            'symbol': commodity.get('Symbol'),
            'name': commodity.get('Name', commodity.get('Symbol')),
            'last_price': commodity.get('Last'),
            'unit': commodity.get('Unit', 'USD'),
            'category': commodity.get('Category', 'Unknown')
        })
    
    return {
        'success': True,
        'commodities': commodity_list,
        'total_count': len(commodity_list),
        'by_category': result['summary'],
        'timestamp': result['timestamp'],
        'source': result.get('source', 'unknown')
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Trading Economics Commodity API - QuantClaw Data")
    print("=" * 70)
    
    # Check if API key is configured
    if TE_API_KEY:
        print(f"\n✓ API Key configured (starts with: {TE_API_KEY[:8]}...)")
    else:
        print("\n⚠ No API key found. Using sample data for testing.")
        print("  To get live data:")
        print("  1. Set TRADING_ECONOMICS_API_KEY in .env")
        print("  2. Free tier: 100 calls/day")
        print("  3. Register at: https://tradingeconomics.com/api")
    
    # Test basic functionality
    print("\n" + "-" * 70)
    print("Testing: get_commodity_prices()")
    print("-" * 70)
    
    prices = get_commodity_prices()
    if prices['success']:
        print(f"✓ Success! Found {prices['summary']['total_commodities']} commodities")
        print(f"  Energy: {prices['summary']['energy_count']}")
        print(f"  Metals: {prices['summary']['metals_count']}")
        print(f"  Agriculture: {prices['summary']['agriculture_count']}")
        print(f"  Source: {prices.get('source', 'unknown')}")
        
        # Show sample commodities
        print("\nSample prices:")
        for commodity in prices['commodities'][:5]:
            print(f"  {commodity['Name']}: ${commodity['Last']} {commodity.get('Unit', '')}")
    else:
        print(f"✗ Error: {prices.get('error')}")
    
    print("\n" + "-" * 70)
    print("Testing: get_energy_prices()")
    print("-" * 70)
    
    energy = get_energy_prices()
    if energy['success']:
        print(f"✓ Success! Found {energy['count']} energy commodities")
        print("\nKey indicators:")
        for name, data in energy['key_indicators'].items():
            print(f"  {name}: ${data['price']:.2f} ({data['change_pct']:+.2f}%)")
    else:
        print(f"✗ Error: {energy.get('error')}")
