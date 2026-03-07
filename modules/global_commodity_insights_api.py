#!/usr/bin/env python3
"""
Global Commodity Insights API — Free Commodity Price Data Module

Fetches commodity price data from World Bank Commodity Markets (Pink Sheet).
Covers oil, gas, metals, and agriculture with monthly price indices and historical data.

Data sources:
- World Bank Commodity Markets (Pink Sheet) - free, public, updated monthly

Source: https://www.worldbank.org/en/research/commodity-markets
Category: Commodities & Energy
Free tier: True (no API key required)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# World Bank Pink Sheet Excel URL
PINK_SHEET_URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"

# Commodity mapping (exact column names from Pink Sheet)
COMMODITY_MAP = {
    # Energy
    'crude_oil': 'Crude oil, Brent',
    'crude_oil_wti': 'Crude oil, WTI',
    'crude_oil_dubai': 'Crude oil, Dubai',
    'natural_gas_us': 'Natural gas, US',
    'natural_gas_europe': 'Natural gas, Europe',
    'coal_australia': 'Coal, Australia',
    
    # Metals
    'gold': 'Gold',
    'silver': 'Silver',
    'copper': 'Copper',
    'iron_ore': 'Iron ore, cfr spot',
    'aluminum': 'Aluminum',
    'nickel': 'Nickel',
    'zinc': 'Zinc',
    'lead': 'Lead',
    'tin': 'Tin',
    
    # Agriculture
    'wheat': 'Wheat, US HRW',
    'corn': 'Maize',
    'soybeans': 'Soybeans',
    'rice': 'Rice, Thailand 5%',
    'sugar': 'Sugar, world',
    'coffee': 'Coffee, Arabica',
    'cotton': 'Cotton, A Index',
    'palm_oil': 'Palm oil',
}

# Cache for Pink Sheet data (to avoid repeated downloads)
_PINK_SHEET_CACHE = None
_CACHE_TIMESTAMP = None


def _fetch_pink_sheet_data() -> Optional[pd.DataFrame]:
    """
    Fetch and parse World Bank Pink Sheet Excel data with caching.
    
    Returns:
        DataFrame with commodity prices (dates as index, commodities as columns) or None on error
    """
    global _PINK_SHEET_CACHE, _CACHE_TIMESTAMP
    
    # Return cached data if less than 1 hour old
    if _PINK_SHEET_CACHE is not None and _CACHE_TIMESTAMP is not None:
        if (datetime.now() - _CACHE_TIMESTAMP).seconds < 3600:
            return _PINK_SHEET_CACHE
    
    try:
        response = requests.get(PINK_SHEET_URL, timeout=30)
        response.raise_for_status()
        
        # Read Excel file from bytes (header row 4 has commodity names)
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name='Monthly Prices', header=4)
        
        # First column is dates, set as index
        df = df.rename(columns={df.columns[0]: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'], format='%YM%m', errors='coerce')
        df = df.set_index('Date')
        
        # Drop rows with invalid dates
        df = df[df.index.notna()]
        
        # Cache the data
        _PINK_SHEET_CACHE = df
        _CACHE_TIMESTAMP = datetime.now()
        
        return df
        
    except Exception as e:
        print(f"Warning: Could not fetch Pink Sheet data: {str(e)}")
        return None


def get_commodity_prices(commodity: str = 'crude_oil') -> Dict:
    """
    Get latest commodity price for a specific commodity.
    
    Args:
        commodity: Commodity identifier (default: 'crude_oil')
                  Options: crude_oil, crude_oil_wti, crude_oil_dubai, natural_gas_us, 
                          natural_gas_europe, coal_australia, gold, silver, copper, 
                          iron_ore, aluminum, nickel, zinc, lead, tin, wheat, corn, 
                          soybeans, rice, sugar, coffee, cotton, palm_oil
    
    Returns:
        Dict with keys: commodity, name, price, unit, date, source
    
    Example:
        >>> price = get_commodity_prices('crude_oil')
        >>> print(f"Brent Crude: ${price['price']:.2f}/bbl on {price['date']}")
    """
    try:
        commodity = commodity.lower()
        
        if commodity not in COMMODITY_MAP:
            return {
                'error': f'Unknown commodity: {commodity}',
                'available': list(COMMODITY_MAP.keys())
            }
        
        column_name = COMMODITY_MAP[commodity]
        
        # Fetch Pink Sheet data
        df = _fetch_pink_sheet_data()
        
        if df is None:
            return {
                'error': 'Could not fetch commodity data',
                'commodity': commodity
            }
        
        # Check if column exists
        if column_name not in df.columns:
            return {
                'error': f'Commodity "{column_name}" not found in data',
                'commodity': commodity,
                'available_columns': list(df.columns[:10])
            }
        
        # Get latest non-null price
        series = df[column_name].dropna()
        if series.empty:
            return {
                'error': 'No price data available',
                'commodity': commodity
            }
        
        latest_price = float(series.iloc[-1])
        latest_date = series.index[-1].strftime('%Y-%m')
        
        # Determine unit based on commodity
        if 'oil' in commodity or 'coal' in commodity.lower():
            unit = 'USD/bbl' if 'oil' in commodity else 'USD/mt'
        elif commodity in ['gold', 'silver']:
            unit = 'USD/toz'
        elif commodity in ['wheat', 'corn', 'soybeans', 'rice']:
            unit = 'USD/mt'
        elif commodity in ['coffee', 'sugar', 'cotton']:
            unit = 'USD/kg'
        else:
            unit = 'USD/mt'
        
        return {
            'commodity': commodity,
            'name': column_name,
            'price': latest_price,
            'unit': unit,
            'date': latest_date,
            'source': 'World Bank Pink Sheet',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e), 'commodity': commodity}


def get_commodity_history(commodity: str = 'crude_oil', months: int = 12) -> Dict:
    """
    Get historical commodity prices.
    
    Args:
        commodity: Commodity identifier (default: 'crude_oil')
        months: Number of months of history (default: 12)
    
    Returns:
        Dict with keys: commodity, name, prices (list), dates (list), unit, source
    
    Example:
        >>> history = get_commodity_history('gold', months=24)
        >>> print(f"Gold: {len(history['prices'])} months, latest ${history['prices'][-1]:.2f}")
    """
    try:
        commodity = commodity.lower()
        
        if commodity not in COMMODITY_MAP:
            return {
                'error': f'Unknown commodity: {commodity}',
                'available': list(COMMODITY_MAP.keys())
            }
        
        column_name = COMMODITY_MAP[commodity]
        
        # Fetch Pink Sheet data
        df = _fetch_pink_sheet_data()
        
        if df is None:
            return {
                'error': 'Could not fetch commodity data',
                'commodity': commodity
            }
        
        # Check if column exists
        if column_name not in df.columns:
            return {
                'error': f'Commodity "{column_name}" not found in data',
                'commodity': commodity
            }
        
        # Get last N months of data
        series = df[column_name].dropna().tail(months)
        
        if series.empty:
            return {
                'error': 'No historical data available',
                'commodity': commodity
            }
        
        prices = [float(p) for p in series.tolist()]
        dates = [d.strftime('%Y-%m') for d in series.index]
        
        # Determine unit
        if 'oil' in commodity or 'coal' in commodity:
            unit = 'USD/bbl' if 'oil' in commodity else 'USD/mt'
        elif commodity in ['gold', 'silver']:
            unit = 'USD/toz'
        elif commodity in ['wheat', 'corn', 'soybeans', 'rice']:
            unit = 'USD/mt'
        elif commodity in ['coffee', 'sugar', 'cotton']:
            unit = 'USD/kg'
        else:
            unit = 'USD/mt'
        
        return {
            'commodity': commodity,
            'name': column_name,
            'prices': prices,
            'dates': dates,
            'unit': unit,
            'count': len(prices),
            'source': 'World Bank Pink Sheet',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e), 'commodity': commodity}


def list_commodities() -> Dict:
    """
    Get list of available commodities with metadata.
    
    Returns:
        Dict with 'commodities' key containing list of dicts with:
        id, name, category
    
    Example:
        >>> commodities = list_commodities()
        >>> for c in commodities['commodities'][:5]:
        ...     print(f"{c['id']}: {c['name']} ({c['category']})")
    """
    try:
        commodities = []
        
        for key, name in COMMODITY_MAP.items():
            # Determine category
            if any(x in key for x in ['oil', 'gas', 'coal']):
                category = 'Energy'
            elif any(x in key for x in ['gold', 'silver', 'copper', 'iron', 'aluminum', 'nickel', 'zinc', 'lead', 'tin']):
                category = 'Metals'
            else:
                category = 'Agriculture'
            
            commodities.append({
                'id': key,
                'name': name,
                'category': category
            })
        
        return {
            'commodities': commodities,
            'count': len(commodities),
            'categories': ['Energy', 'Metals', 'Agriculture'],
            'source': 'World Bank Pink Sheet',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}


def get_energy_prices() -> Dict:
    """
    Get bundle of major energy commodity prices.
    
    Returns:
        Dict with energy commodities: crude_oil, natural_gas_us, coal_australia
    
    Example:
        >>> energy = get_energy_prices()
        >>> for key, data in energy['energy'].items():
        ...     print(f"{data['name']}: ${data['price']:.2f}")
    """
    try:
        energy_commodities = ['crude_oil', 'natural_gas_us', 'coal_australia']
        results = {}
        
        for commodity in energy_commodities:
            price_data = get_commodity_prices(commodity)
            if 'error' not in price_data:
                results[commodity] = {
                    'name': price_data['name'],
                    'price': price_data['price'],
                    'unit': price_data['unit'],
                    'date': price_data['date']
                }
        
        if not results:
            return {'error': 'No energy prices available'}
        
        return {
            'energy': results,
            'count': len(results),
            'source': 'World Bank Pink Sheet',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}


def get_metals_prices() -> Dict:
    """
    Get bundle of major metal commodity prices.
    
    Returns:
        Dict with metal commodities: gold, silver, copper, iron_ore
    
    Example:
        >>> metals = get_metals_prices()
        >>> for key, data in metals['metals'].items():
        ...     print(f"{data['name']}: ${data['price']:.2f}/{data['unit']}")
    """
    try:
        metal_commodities = ['gold', 'silver', 'copper', 'iron_ore']
        results = {}
        
        for commodity in metal_commodities:
            price_data = get_commodity_prices(commodity)
            if 'error' not in price_data:
                results[commodity] = {
                    'name': price_data['name'],
                    'price': price_data['price'],
                    'unit': price_data['unit'],
                    'date': price_data['date']
                }
        
        if not results:
            return {'error': 'No metal prices available'}
        
        return {
            'metals': results,
            'count': len(results),
            'source': 'World Bank Pink Sheet',
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "price" and len(sys.argv) > 2:
            result = get_commodity_prices(sys.argv[2])
        elif command == "history" and len(sys.argv) > 2:
            months = int(sys.argv[3]) if len(sys.argv) > 3 else 12
            result = get_commodity_history(sys.argv[2], months)
        elif command == "list":
            result = list_commodities()
        elif command == "energy":
            result = get_energy_prices()
        elif command == "metals":
            result = get_metals_prices()
        else:
            result = {
                "module": "global_commodity_insights_api",
                "version": "1.0",
                "usage": "python global_commodity_insights_api.py [price|history|list|energy|metals] <commodity>",
                "functions": [
                    "get_commodity_prices(commodity)",
                    "get_commodity_history(commodity, months)",
                    "list_commodities()",
                    "get_energy_prices()",
                    "get_metals_prices()"
                ]
            }
    else:
        result = {
            "module": "global_commodity_insights_api",
            "status": "ready",
            "source": "World Bank Pink Sheet",
            "functions": 5,
            "commodities": len(COMMODITY_MAP)
        }
    
    print(json.dumps(result, indent=2))
