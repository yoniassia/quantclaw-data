#!/usr/bin/env python3
"""
EIA Open Data API v2 — U.S. Energy Information Administration

Comprehensive energy data including:
- Crude oil prices (WTI, Brent spot prices)
- Natural gas storage and prices
- Electricity generation by source
- Renewable energy production
- Coal, petroleum, and natural gas imports/exports

Source: https://www.eia.gov/opendata/
Category: Commodities & Energy
Free tier: True (5,000 calls/day with free API key)
Update frequency: Real-time for prices, daily/weekly for reports
Author: QuantClaw Data NightBuilder
Phase: NightBuilder-105
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

# EIA API Configuration
EIA_BASE_URL = "https://api.eia.gov/v2"
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")

# ========== EIA V2 ROUTE REGISTRY ==========
# Based on https://www.eia.gov/opendata/browser/

EIA_ROUTES = {
    # Petroleum routes
    'PETROLEUM_SPOT_PRICES': 'petroleum/pri/spt',
    'PETROLEUM_FUTURES': 'petroleum/pri/fut',
    'PETROLEUM_IMPORTS': 'petroleum/move/imp',
    'PETROLEUM_EXPORTS': 'petroleum/move/exp',
    'PETROLEUM_STOCKS': 'petroleum/stoc/wstk',
    'PETROLEUM_PRODUCTION': 'petroleum/sum/sndw',
    
    # Natural gas routes
    'NATURAL_GAS_STORAGE': 'natural-gas/stor/wkly',
    'NATURAL_GAS_PRICES': 'natural-gas/pri/sum',
    'NATURAL_GAS_PRODUCTION': 'natural-gas/prod/sum',
    'NATURAL_GAS_CONSUMPTION': 'natural-gas/cons/sum',
    
    # Electricity routes
    'ELECTRICITY_GENERATION': 'electricity/electric-power-operational-data',
    'ELECTRICITY_RETAIL_SALES': 'electricity/retail-sales',
    'ELECTRICITY_PRICES': 'electricity/retail-sales',
    
    # Coal routes
    'COAL_PRODUCTION': 'coal/production',
    'COAL_CONSUMPTION': 'coal/consumption-and-quality',
    
    # Total energy routes
    'TOTAL_ENERGY': 'total-energy/data',
    
    # International routes
    'INTERNATIONAL_ENERGY': 'international/data',
}

# Product facet codes for petroleum spot prices
PETROLEUM_PRODUCTS = {
    'EPCWTI': 'WTI Crude Oil ($/barrel)',
    'EPCBRENT': 'UK Brent Crude Oil ($/barrel)',
    'EPD2F': 'No 2 Fuel Oil / Heating Oil ($/gallon)',
    'EPD2DXL0': 'No 2 Diesel Low Sulfur (0-15 ppm) ($/gallon)',
    'EPLLPA': 'Propane ($/gallon)',
    'EPJK': 'Kerosene-Type Jet Fuel ($/gallon)',
    'EPMRR': 'Reformulated Regular Gasoline ($/gallon)',
    'EPMRU': 'Conventional Regular Gasoline ($/gallon)',
}


def _make_eia_request(
    route: str,
    params: Optional[Dict] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Internal helper to make EIA API v2 requests
    
    Args:
        route: API route (e.g., 'petroleum/pri/spt')
        params: Query parameters dict
        api_key: Optional API key override
    
    Returns:
        Dict with API response or error
    """
    try:
        url = f"{EIA_BASE_URL}/{route}/data/"
        
        request_params = params.copy() if params else {}
        
        # Add API key if available
        key = api_key or EIA_API_KEY
        if key:
            request_params['api_key'] = key
        
        response = requests.get(url, params=request_params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'response' not in data:
            return {
                "success": False,
                "error": "Invalid API response format",
                "raw": data
            }
        
        response_data = data['response']
        
        return {
            "success": True,
            "data": response_data.get('data', []),
            "total": response_data.get('total', 0),
            "route": route,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "route": route
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "route": route
        }


def get_crude_oil_prices(
    products: Optional[List[str]] = None,
    frequency: str = "daily",
    limit: int = 30,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get crude oil spot prices (WTI, Brent, and refined products)
    
    Args:
        products: List of product codes (default: ['EPC0', 'EPCBRENT'] for WTI/Brent)
        frequency: Data frequency ('daily', 'weekly', 'monthly', 'annual')
        limit: Number of data points to return (default 30)
        api_key: Optional EIA API key
    
    Returns:
        Dict with crude oil prices, latest values, and changes
    """
    if products is None:
        products = ['EPCWTI', 'EPCBRENT']  # WTI and Brent
    
    params = {
        'frequency': frequency,
        'data[0]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit * len(products),  # Get enough for all products
    }
    
    # Add product facets - EIA v2 API needs multiple values for same key
    # We'll filter after fetching since multi-value params are tricky
    
    result = _make_eia_request(EIA_ROUTES['PETROLEUM_SPOT_PRICES'], params, api_key)
    
    if not result['success']:
        return result
    
    # Parse and structure the data
    # Filter for requested products
    all_data = result['data']
    filtered_data = [d for d in all_data if d.get('product') in products]
    
    prices = {}
    for product_code in products:
        product_data = [d for d in filtered_data if d.get('product') == product_code]
        
        if product_data:
            latest = product_data[0]
            prices[product_code] = {
                'name': PETROLEUM_PRODUCTS.get(product_code, product_code),
                'latest_value': latest.get('value'),
                'latest_date': latest.get('period'),
                'unit': latest.get('units', '$/barrel'),
                'series': product_data[:10]  # Last 10 data points
            }
            
            # Calculate changes
            if len(product_data) >= 2:
                prev_val = product_data[1].get('value')
                latest_val = latest.get('value')
                if prev_val and latest_val:
                    prices[product_code]['change'] = latest_val - prev_val
                    prices[product_code]['change_pct'] = ((latest_val - prev_val) / prev_val * 100)
    
    return {
        'success': True,
        'crude_oil_prices': prices,
        'frequency': frequency,
        'count': len(result['data']),
        'timestamp': datetime.now().isoformat()
    }


def get_natural_gas_storage(
    frequency: str = "weekly",
    limit: int = 52,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get U.S. natural gas underground storage data
    
    Args:
        frequency: Data frequency (default 'weekly')
        limit: Number of weeks to return (default 52 for 1 year)
        api_key: Optional EIA API key
    
    Returns:
        Dict with natural gas storage levels and changes
    """
    params = {
        'frequency': frequency,
        'data[]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit,
    }
    
    result = _make_eia_request(EIA_ROUTES['NATURAL_GAS_STORAGE'], params, api_key)
    
    if not result['success']:
        return result
    
    data_points = result['data']
    
    if not data_points:
        return {
            'success': False,
            'error': 'No storage data available',
            'route': EIA_ROUTES['NATURAL_GAS_STORAGE']
        }
    
    # Get latest storage level
    latest = data_points[0]
    
    storage_info = {
        'latest_value': latest.get('value'),
        'latest_date': latest.get('period'),
        'unit': latest.get('units', 'Bcf'),
        'process': latest.get('process', 'Total'),
        'area': latest.get('area-name', 'U.S. Lower 48')
    }
    
    # Calculate week-over-week and year-over-year changes
    if len(data_points) >= 2:
        week_ago = data_points[1].get('value')
        if week_ago:
            storage_info['week_change'] = latest.get('value') - week_ago
            storage_info['week_change_pct'] = ((latest.get('value') - week_ago) / week_ago * 100)
    
    if len(data_points) >= 52:
        year_ago = data_points[51].get('value')
        if year_ago:
            storage_info['yoy_change'] = latest.get('value') - year_ago
            storage_info['yoy_change_pct'] = ((latest.get('value') - year_ago) / year_ago * 100)
    
    return {
        'success': True,
        'natural_gas_storage': storage_info,
        'historical_data': data_points[:12],  # Last 3 months
        'frequency': frequency,
        'timestamp': datetime.now().isoformat()
    }


def get_electricity_generation(
    frequency: str = "monthly",
    limit: int = 12,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get U.S. electricity net generation by energy source
    
    Args:
        frequency: Data frequency (default 'monthly')
        limit: Number of periods to return
        api_key: Optional EIA API key
    
    Returns:
        Dict with electricity generation by source (coal, natural gas, nuclear, renewables)
    """
    params = {
        'frequency': frequency,
        'data[]': 'generation',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit * 10,  # Get more to cover multiple sources
    }
    
    result = _make_eia_request(EIA_ROUTES['ELECTRICITY_GENERATION'], params, api_key)
    
    if not result['success']:
        return result
    
    # Group by energy source
    by_source = {}
    for record in result['data']:
        source = record.get('fuelTypeDescription') or record.get('fueltypeid', 'Unknown')
        period = record.get('period')
        value = record.get('generation')
        
        if source not in by_source:
            by_source[source] = []
        
        by_source[source].append({
            'period': period,
            'value': value,
            'unit': 'thousand megawatthours'
        })
    
    # Get latest for each source
    latest_by_source = {}
    for source, data_list in by_source.items():
        if data_list:
            latest_by_source[source] = {
                'latest_value': data_list[0]['value'],
                'latest_period': data_list[0]['period'],
                'unit': data_list[0]['unit'],
                'data_points': len(data_list)
            }
    
    return {
        'success': True,
        'electricity_generation': latest_by_source,
        'frequency': frequency,
        'count': len(result['data']),
        'timestamp': datetime.now().isoformat()
    }


def get_petroleum_stocks(
    frequency: str = "weekly",
    limit: int = 52,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get U.S. petroleum stocks (crude oil, gasoline, distillates)
    
    Args:
        frequency: Data frequency (default 'weekly')
        limit: Number of periods to return
        api_key: Optional EIA API key
    
    Returns:
        Dict with petroleum inventory levels
    """
    params = {
        'frequency': frequency,
        'data[]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit * 5,  # Multiple products
    }
    
    result = _make_eia_request(EIA_ROUTES['PETROLEUM_STOCKS'], params, api_key)
    
    if not result['success']:
        return result
    
    # Group by product
    by_product = {}
    for record in result['data']:
        product = record.get('product-name', 'Unknown')
        
        if product not in by_product:
            by_product[product] = {
                'latest_value': record.get('value'),
                'latest_period': record.get('period'),
                'unit': record.get('units', 'Thousand Barrels'),
                'area': record.get('area-name', 'U.S.')
            }
    
    return {
        'success': True,
        'petroleum_stocks': by_product,
        'frequency': frequency,
        'count': len(by_product),
        'timestamp': datetime.now().isoformat()
    }


def get_natural_gas_prices(
    frequency: str = "monthly",
    limit: int = 12,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get natural gas prices by sector and location
    
    Args:
        frequency: Data frequency (default 'monthly')
        limit: Number of periods to return
        api_key: Optional EIA API key
    
    Returns:
        Dict with natural gas prices
    """
    params = {
        'frequency': frequency,
        'data[]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit * 10,
    }
    
    result = _make_eia_request(EIA_ROUTES['NATURAL_GAS_PRICES'], params, api_key)
    
    if not result['success']:
        return result
    
    # Group by process (sector)
    by_sector = {}
    for record in result['data']:
        process = record.get('process-name', 'Unknown')
        
        if process not in by_sector:
            by_sector[process] = {
                'latest_value': record.get('value'),
                'latest_period': record.get('period'),
                'unit': record.get('units', '$/MCF')
            }
    
    return {
        'success': True,
        'natural_gas_prices': by_sector,
        'frequency': frequency,
        'timestamp': datetime.now().isoformat()
    }


def get_coal_production(
    frequency: str = "quarterly",
    limit: int = 8,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get U.S. coal production data
    
    Args:
        frequency: Data frequency (default 'quarterly')
        limit: Number of periods to return
        api_key: Optional EIA API key
    
    Returns:
        Dict with coal production levels
    """
    params = {
        'frequency': frequency,
        'data[]': 'production',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit,
    }
    
    result = _make_eia_request(EIA_ROUTES['COAL_PRODUCTION'], params, api_key)
    
    if not result['success']:
        return result
    
    if result['data']:
        latest = result['data'][0]
        
        production_info = {
            'latest_value': latest.get('production'),
            'latest_period': latest.get('period'),
            'unit': latest.get('units', 'thousand short tons'),
            'historical_data': result['data'][:4]
        }
        
        return {
            'success': True,
            'coal_production': production_info,
            'frequency': frequency,
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': False,
        'error': 'No coal production data available'
    }


def get_energy_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive energy markets snapshot
    Key metrics across oil, gas, electricity, and renewables
    
    Returns:
        Dict with latest values from all major energy categories
    """
    snapshot = {}
    
    # Get WTI and Brent crude prices
    crude = get_crude_oil_prices(products=['EPCWTI', 'EPCBRENT'], limit=5, api_key=api_key)
    if crude['success']:
        snapshot['crude_oil'] = crude['crude_oil_prices']
    
    # Get natural gas storage
    ng_storage = get_natural_gas_storage(limit=5, api_key=api_key)
    if ng_storage['success']:
        snapshot['natural_gas_storage'] = ng_storage['natural_gas_storage']
    
    # Get petroleum stocks
    stocks = get_petroleum_stocks(limit=10, api_key=api_key)
    if stocks['success']:
        snapshot['petroleum_stocks'] = stocks['petroleum_stocks']
    
    return {
        'success': True,
        'energy_snapshot': snapshot,
        'timestamp': datetime.now().isoformat(),
        'source': 'EIA Open Data API v2'
    }


def list_all_routes() -> Dict:
    """
    List all available EIA v2 API routes in this module
    
    Returns:
        Dict with route names and paths
    """
    routes = []
    for name, path in EIA_ROUTES.items():
        routes.append({
            'name': name,
            'path': path,
            'url': f"{EIA_BASE_URL}/{path}/data/"
        })
    
    return {
        'success': True,
        'total_routes': len(routes),
        'routes': routes,
        'module': 'eia_open_data_api_v2'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("EIA Open Data API v2 - U.S. Energy Information Administration")
    print("=" * 60)
    
    # Show available routes
    routes_list = list_all_routes()
    print(f"\nTotal Routes: {routes_list['total_routes']}\n")
    
    # Get energy snapshot
    print("Fetching energy markets snapshot...\n")
    snapshot = get_energy_snapshot()
    print(json.dumps(snapshot, indent=2))
