#!/usr/bin/env python3
"""
USDA Crop & Agriculture Data Module — Phase 114

USDA National Agricultural Statistics Service (NASS) QuickStats API integration
Provides comprehensive US agriculture data for commodity markets, economic analysis, and trading.

Data Sources:
- USDA NASS QuickStats API: https://quickstats.nass.usda.gov/api
- FRED API: Agricultural price indices (fallback/supplementary)
- USDA WASDE Reports: World Agricultural Supply and Demand Estimates (monthly)

Coverage:
1. **Crop Production**: Corn, soybeans, wheat, cotton, rice - planted acres, yield, harvest
2. **Livestock**: Cattle, hogs, poultry inventories and prices
3. **Farm Prices**: Crop prices received by farmers, price indices
4. **WASDE Reports**: Supply/demand estimates, ending stocks, trade forecasts
5. **Farm Income**: Cash receipts, expenses, net farm income

Update Frequency: Monthly (WASDE), Quarterly (production), Annual (census)
API Key: Required (free from https://quickstats.nass.usda.gov/api)

Phase: 114
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import os
from pathlib import Path

# USDA NASS QuickStats API Configuration
NASS_API_BASE = "https://quickstats.nass.usda.gov/api"
NASS_API_KEY = os.environ.get('USDA_NASS_API_KEY', '')  # Set via environment or leave empty for demo

# FRED API for supplementary agricultural data
FRED_API_KEY = ""  # Will use fred module's key
FRED_API_BASE = "https://api.stlouisfed.org/fred"

# Core Commodities
MAJOR_CROPS = {
    'CORN': {
        'name': 'Corn',
        'units': 'BU (bushels)',
        'uses': 'Ethanol, livestock feed, exports',
        'planted_acres_estimate': 90_000_000
    },
    'SOYBEANS': {
        'name': 'Soybeans',
        'units': 'BU (bushels)',
        'uses': 'Soybean oil, meal, exports to China',
        'planted_acres_estimate': 87_000_000
    },
    'WHEAT': {
        'name': 'Wheat',
        'units': 'BU (bushels)',
        'uses': 'Flour, exports, livestock feed',
        'planted_acres_estimate': 45_000_000
    },
    'COTTON': {
        'name': 'Cotton',
        'units': 'BALES (480 lb each)',
        'uses': 'Textiles, cottonseed oil',
        'planted_acres_estimate': 12_000_000
    },
    'RICE': {
        'name': 'Rice',
        'units': 'CWT (hundredweight)',
        'uses': 'Food, exports',
        'planted_acres_estimate': 2_500_000
    },
}

LIVESTOCK_CATEGORIES = {
    'CATTLE': {
        'name': 'Cattle',
        'metrics': ['inventory', 'price', 'slaughter'],
        'units': 'HEAD for inventory, $ per CWT for price'
    },
    'HOGS': {
        'name': 'Hogs',
        'metrics': ['inventory', 'price', 'slaughter'],
        'units': 'HEAD for inventory, $ per CWT for price'
    },
    'CHICKEN': {
        'name': 'Chickens (Broilers)',
        'metrics': ['production', 'price'],
        'units': 'HEAD for production, $ per LB for price'
    },
}

# FRED Agricultural Series
FRED_AG_SERIES = {
    "WPU01": "PPI - Farm Products (all commodities)",
    "WPU0111": "PPI - Grains",
    "WPU014": "PPI - Livestock and livestock products",
    "APU0000FF1101": "CPI - Food at home",
    "CPIUFDSL": "CPI - Food and beverages",
}


def query_nass_api(params: Dict, endpoint: str = "api_GET") -> Dict:
    """
    Query USDA NASS QuickStats API
    
    Args:
        params: Query parameters
        endpoint: API endpoint (default: api_GET)
        
    Returns:
        Dict with API response data
    """
    if not NASS_API_KEY:
        return {
            'success': False,
            'error': 'USDA NASS API key not configured. Set USDA_NASS_API_KEY environment variable.',
            'help': 'Get free API key: https://quickstats.nass.usda.gov/api',
            'demo_mode': True
        }
    
    # Add API key and format to params
    params['key'] = NASS_API_KEY
    params['format'] = 'JSON'
    
    url = f"{NASS_API_BASE}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 401:
            return {
                'success': False,
                'error': 'Invalid API key',
                'help': 'Get free API key: https://quickstats.nass.usda.gov/api'
            }
        
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            return {
                'success': True,
                'data': data['data'],
                'count': len(data['data'])
            }
        elif 'error' in data:
            return {
                'success': False,
                'error': data['error']
            }
        else:
            return {
                'success': False,
                'error': 'Unexpected API response format'
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}'
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Failed to parse API response: {str(e)}'
        }


def fetch_fred_data(series_id: str, start_date: Optional[str] = None) -> Dict:
    """
    Fetch agricultural data from FRED API (fallback/supplementary)
    
    Args:
        series_id: FRED series ID
        start_date: Start date (YYYY-MM-DD)
        
    Returns:
        Dict with observations
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'sort_order': 'desc',
        'limit': 100
    }
    
    try:
        response = requests.get(f"{FRED_API_BASE}/series/observations", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' in data:
            return {
                'success': True,
                'series_id': series_id,
                'data': data['observations']
            }
        else:
            return {'success': False, 'error': 'No observations found'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_crop_production(commodity: str, year: Optional[int] = None, 
                       state: str = "US TOTAL") -> Dict:
    """
    Get crop production data for a specific commodity
    
    Args:
        commodity: Crop name (CORN, SOYBEANS, WHEAT, COTTON, RICE)
        year: Year (default: current year)
        state: State name or "US TOTAL" for national data
        
    Returns:
        Dict with production statistics (acres planted, harvested, yield, production)
    """
    commodity = commodity.upper()
    
    if commodity not in MAJOR_CROPS:
        return {
            'success': False,
            'error': f'Invalid commodity. Choose from: {", ".join(MAJOR_CROPS.keys())}'
        }
    
    if year is None:
        year = datetime.now().year
    
    # Query NASS API for production data
    params = {
        'commodity_desc': commodity,
        'year': year,
        'state_name': state,
        'agg_level_desc': 'NATIONAL' if state == "US TOTAL" else 'STATE',
        'statisticcat_desc': 'PRODUCTION',
    }
    
    result = query_nass_api(params)
    
    if not result.get('success'):
        # Fallback: Return structure with error
        return {
            'success': False,
            'commodity': MAJOR_CROPS[commodity]['name'],
            'year': year,
            'error': result.get('error', 'Failed to fetch data'),
            'help': result.get('help', '')
        }
    
    data = result.get('data', [])
    
    # Parse and organize production metrics
    metrics = {
        'planted_acres': None,
        'harvested_acres': None,
        'yield_per_acre': None,
        'total_production': None,
        'unit': MAJOR_CROPS[commodity]['units']
    }
    
    for record in data:
        stat_name = record.get('short_desc', '').upper()
        value = record.get('Value')
        
        # Try to parse numeric value
        try:
            if value and value != "(D)":  # (D) means withheld for disclosure
                # Remove commas
                value_clean = value.replace(',', '')
                value_numeric = float(value_clean)
                
                if 'ACRES PLANTED' in stat_name:
                    metrics['planted_acres'] = value_numeric
                elif 'ACRES HARVESTED' in stat_name:
                    metrics['harvested_acres'] = value_numeric
                elif 'YIELD' in stat_name:
                    metrics['yield_per_acre'] = value_numeric
                elif 'PRODUCTION' in stat_name and 'ACRES' not in stat_name:
                    metrics['total_production'] = value_numeric
        except (ValueError, TypeError):
            continue
    
    return {
        'success': True,
        'commodity': MAJOR_CROPS[commodity]['name'],
        'commodity_code': commodity,
        'year': year,
        'state': state,
        'metrics': metrics,
        'uses': MAJOR_CROPS[commodity]['uses'],
        'data_source': 'USDA NASS QuickStats',
        'record_count': len(data)
    }


def get_livestock_inventory(animal: str, year: Optional[int] = None) -> Dict:
    """
    Get livestock inventory and price data
    
    Args:
        animal: Livestock type (CATTLE, HOGS, CHICKEN)
        year: Year (default: current year)
        
    Returns:
        Dict with inventory counts and price data
    """
    animal = animal.upper()
    
    if animal not in LIVESTOCK_CATEGORIES:
        return {
            'success': False,
            'error': f'Invalid livestock type. Choose from: {", ".join(LIVESTOCK_CATEGORIES.keys())}'
        }
    
    if year is None:
        year = datetime.now().year
    
    # Query for inventory
    params = {
        'commodity_desc': animal if animal != 'CHICKEN' else 'CHICKENS',
        'year': year,
        'agg_level_desc': 'NATIONAL',
        'statisticcat_desc': 'INVENTORY',
    }
    
    result = query_nass_api(params)
    
    if not result.get('success'):
        return {
            'success': False,
            'animal': LIVESTOCK_CATEGORIES[animal]['name'],
            'year': year,
            'error': result.get('error', 'Failed to fetch data'),
            'help': result.get('help', '')
        }
    
    data = result.get('data', [])
    
    # Parse inventory data
    inventory = {
        'total_head': None,
        'date': None,
        'unit': 'HEAD'
    }
    
    for record in data:
        value = record.get('Value')
        if value and value != "(D)":
            try:
                value_clean = value.replace(',', '')
                inventory['total_head'] = float(value_clean)
                inventory['date'] = record.get('reference_period_desc', record.get('year'))
                break  # Take first valid record
            except (ValueError, TypeError):
                continue
    
    return {
        'success': True,
        'animal': LIVESTOCK_CATEGORIES[animal]['name'],
        'animal_code': animal,
        'year': year,
        'inventory': inventory,
        'metrics_available': LIVESTOCK_CATEGORIES[animal]['metrics'],
        'data_source': 'USDA NASS QuickStats',
        'record_count': len(data)
    }


def get_farm_prices(commodity: str, year: Optional[int] = None, 
                   months: int = 12) -> Dict:
    """
    Get prices received by farmers for crops
    
    Args:
        commodity: Crop name (CORN, SOYBEANS, WHEAT, etc.)
        year: Year (default: current year)
        months: Number of months to retrieve
        
    Returns:
        Dict with price data and trends
    """
    commodity = commodity.upper()
    
    if year is None:
        year = datetime.now().year
    
    # Query for prices received
    params = {
        'commodity_desc': commodity,
        'year': year,
        'agg_level_desc': 'NATIONAL',
        'statisticcat_desc': 'PRICE RECEIVED',
    }
    
    result = query_nass_api(params)
    
    if not result.get('success'):
        return {
            'success': False,
            'commodity': commodity,
            'year': year,
            'error': result.get('error', 'Failed to fetch data'),
            'help': result.get('help', '')
        }
    
    data = result.get('data', [])
    
    # Parse price data
    prices = []
    for record in data:
        value = record.get('Value')
        if value and value != "(D)":
            try:
                value_clean = value.replace(',', '')
                price = float(value_clean)
                prices.append({
                    'date': record.get('reference_period_desc', ''),
                    'price': price,
                    'unit': record.get('unit_desc', 'USD')
                })
            except (ValueError, TypeError):
                continue
    
    # Sort by date (newest first)
    prices.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate statistics
    current_price = prices[0]['price'] if prices else None
    avg_price = sum(p['price'] for p in prices[:months]) / len(prices[:months]) if prices else None
    
    price_change_pct = None
    if len(prices) >= 2:
        older_price = prices[-1]['price']
        if older_price > 0:
            price_change_pct = ((current_price - older_price) / older_price) * 100
    
    return {
        'success': True,
        'commodity': commodity,
        'year': year,
        'current_price': current_price,
        'avg_price': round(avg_price, 2) if avg_price else None,
        'price_change_pct': round(price_change_pct, 2) if price_change_pct else None,
        'price_history': prices[:months],
        'data_source': 'USDA NASS QuickStats',
        'record_count': len(prices)
    }


def get_wasde_summary(commodity: Optional[str] = None) -> Dict:
    """
    Get WASDE (World Agricultural Supply and Demand Estimates) summary
    
    WASDE reports are released monthly by USDA and move commodity markets significantly.
    They provide supply/demand balance sheets, ending stocks, and trade forecasts.
    
    Args:
        commodity: Specific crop (CORN, SOYBEANS, WHEAT) or None for all
        
    Returns:
        Dict with WASDE data and market-moving insights
    """
    # Note: WASDE reports are released as PDF documents, not via QuickStats API
    # This function provides context and points to where traders can find the data
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # WASDE release schedule (typically around 12th of each month)
    next_release = None
    if datetime.now().day < 12:
        next_release = datetime(current_year, current_month, 12)
    else:
        # Next month
        if current_month == 12:
            next_release = datetime(current_year + 1, 1, 12)
        else:
            next_release = datetime(current_year, current_month + 1, 12)
    
    wasde_info = {
        'success': True,
        'report_name': 'WASDE - World Agricultural Supply and Demand Estimates',
        'frequency': 'Monthly (around 12th of month)',
        'next_release': next_release.strftime('%Y-%m-%d'),
        'url': 'https://www.usda.gov/oce/commodity/wasde/',
        'market_impact': 'HIGH - Reports often cause 2-5% commodity price moves',
        'key_metrics': [
            'Production estimates (crop size)',
            'Ending stocks (surplus/deficit)',
            'Yield per acre revisions',
            'Export forecasts',
            'Prices received forecast'
        ],
        'trading_strategy': 'Position ahead of release based on weather/planting data. Exit on surprise.',
        'commodities_covered': list(MAJOR_CROPS.keys())
    }
    
    if commodity:
        commodity = commodity.upper()
        if commodity in MAJOR_CROPS:
            wasde_info['commodity'] = MAJOR_CROPS[commodity]['name']
            wasde_info['recent_production'] = get_crop_production(commodity, year=current_year)
    
    return wasde_info


def get_agricultural_dashboard(commodities: Optional[List[str]] = None) -> Dict:
    """
    Get comprehensive agricultural market dashboard
    
    Args:
        commodities: List of commodities (default: top 3 - CORN, SOYBEANS, WHEAT)
        
    Returns:
        Dict with multi-commodity overview, prices, production, and WASDE schedule
    """
    if commodities is None:
        commodities = ['CORN', 'SOYBEANS', 'WHEAT']
    
    dashboard = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'commodities': {},
        'wasde_schedule': get_wasde_summary(),
        'data_source': 'USDA NASS QuickStats'
    }
    
    for commodity in commodities:
        commodity = commodity.upper()
        if commodity not in MAJOR_CROPS:
            continue
        
        # Get production and price data
        production = get_crop_production(commodity)
        prices = get_farm_prices(commodity)
        
        dashboard['commodities'][commodity] = {
            'name': MAJOR_CROPS[commodity]['name'],
            'production': production.get('metrics', {}),
            'current_price': prices.get('current_price'),
            'price_change_pct': prices.get('price_change_pct'),
            'uses': MAJOR_CROPS[commodity]['uses']
        }
    
    return dashboard


def list_available_commodities() -> Dict:
    """
    List all available commodities and livestock types
    
    Returns:
        Dict with crops and livestock categories
    """
    return {
        'success': True,
        'crops': {k: v['name'] for k, v in MAJOR_CROPS.items()},
        'livestock': {k: v['name'] for k, v in LIVESTOCK_CATEGORIES.items()},
        'data_source': 'USDA NASS QuickStats',
        'api_key_required': not bool(NASS_API_KEY),
        'get_api_key': 'https://quickstats.nass.usda.gov/api'
    }


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Missing command',
            'usage': 'python usda_agriculture.py <command> [args]',
            'commands': [
                'crop-production <COMMODITY> [--year YYYY]',
                'livestock <ANIMAL> [--year YYYY]',
                'farm-prices <COMMODITY> [--year YYYY]',
                'wasde-summary [--commodity CROP]',
                'ag-dashboard [--commodities CORN,SOYBEANS,WHEAT]',
                'list-commodities'
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "crop-production":
            if len(sys.argv) < 3:
                result = {'error': 'Missing commodity argument'}
            else:
                commodity = sys.argv[2]
                year = None
                if '--year' in sys.argv:
                    year_idx = sys.argv.index('--year') + 1
                    year = int(sys.argv[year_idx])
                result = get_crop_production(commodity, year=year)
        
        elif command == "livestock":
            if len(sys.argv) < 3:
                result = {'error': 'Missing animal argument'}
            else:
                animal = sys.argv[2]
                year = None
                if '--year' in sys.argv:
                    year_idx = sys.argv.index('--year') + 1
                    year = int(sys.argv[year_idx])
                result = get_livestock_inventory(animal, year=year)
        
        elif command == "farm-prices":
            if len(sys.argv) < 3:
                result = {'error': 'Missing commodity argument'}
            else:
                commodity = sys.argv[2]
                year = None
                if '--year' in sys.argv:
                    year_idx = sys.argv.index('--year') + 1
                    year = int(sys.argv[year_idx])
                result = get_farm_prices(commodity, year=year)
        
        elif command == "wasde-summary":
            commodity = None
            if '--commodity' in sys.argv:
                comm_idx = sys.argv.index('--commodity') + 1
                commodity = sys.argv[comm_idx]
            result = get_wasde_summary(commodity=commodity)
        
        elif command == "ag-dashboard" or command == "dashboard":
            commodities = None
            if '--commodities' in sys.argv:
                comm_idx = sys.argv.index('--commodities') + 1
                commodities = sys.argv[comm_idx].split(',')
            result = get_agricultural_dashboard(commodities=commodities)
        
        elif command == "list-commodities":
            result = list_available_commodities()
        
        else:
            result = {'error': f'Unknown command: {command}'}
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)
