#!/usr/bin/env python3
"""
EIA Open Data API — Energy Market Data Module

The U.S. Energy Information Administration (EIA) provides comprehensive data on energy 
production, consumption, prices, and reserves for commodities like oil, natural gas, 
coal, and electricity. Includes historical and forecast data for energy market analysis.

Key data series:
- Crude oil spot prices (daily)
- Natural gas prices (monthly)
- Petroleum inventories (weekly)
- Electricity retail sales (monthly)
- Energy production and consumption

Source: https://www.eia.gov/opendata/
Category: Commodities & Energy
Free tier: True (requires EIA_API_KEY env var, unlimited access)
Update frequency: Real-time for some feeds, daily/weekly for prices, monthly for aggregates
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# EIA API Configuration
EIA_BASE_URL = "https://api.eia.gov/v2"
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")

# ========== EIA DATA SERIES REGISTRY ==========

EIA_SERIES = {
    # ===== PETROLEUM PRICES =====
    'PETROLEUM_PRICES': {
        'crude_oil_wti': 'petroleum/pri/spt',  # WTI Crude Oil Spot Price
        'crude_oil_brent': 'petroleum/pri/spt',  # Brent Crude Oil Spot Price
        'gasoline_regular': 'petroleum/pri/gnd',  # Regular Gasoline Retail Price
        'diesel': 'petroleum/pri/gnd',  # Diesel Retail Price
    },
    
    # ===== NATURAL GAS =====
    'NATURAL_GAS': {
        'henry_hub': 'natural-gas/pri/sum',  # Henry Hub Natural Gas Spot Price
        'citygate': 'natural-gas/pri/sum',  # Natural Gas Citygate Price
        'residential': 'natural-gas/pri/sum',  # Natural Gas Residential Price
        'commercial': 'natural-gas/pri/sum',  # Natural Gas Commercial Price
    },
    
    # ===== PETROLEUM INVENTORIES =====
    'PETROLEUM_STOCKS': {
        'crude_oil': 'petroleum/stoc/wstk',  # Crude Oil Stocks
        'gasoline': 'petroleum/stoc/wstk',  # Gasoline Stocks
        'distillate': 'petroleum/stoc/wstk',  # Distillate Fuel Oil Stocks
        'propane': 'petroleum/stoc/wstk',  # Propane/Propylene Stocks
    },
    
    # ===== ELECTRICITY =====
    'ELECTRICITY': {
        'retail_sales': 'electricity/retail-sales',  # Electricity Retail Sales
        'retail_price': 'electricity/retail-sales',  # Electricity Retail Price
        'generation': 'electricity/electric-power-operational-data',  # Electricity Generation
    },
}

# ========== HELPER FUNCTIONS ==========

def _make_eia_request(route: str, params: Dict[str, Any] = None) -> Dict:
    """
    Make an authenticated request to the EIA API.
    
    Args:
        route: API route (e.g., 'petroleum/pri/spt/data')
        params: Query parameters (frequency, data fields, filters, etc.)
    
    Returns:
        dict: Parsed JSON response
    
    Raises:
        Exception: If API key is missing or request fails
    """
    if not EIA_API_KEY:
        raise ValueError("EIA_API_KEY not found in environment variables. Get one at https://www.eia.gov/opendata/")
    
    # Build URL
    url = f"{EIA_BASE_URL}/{route}"
    
    # Prepare parameters
    request_params = params.copy() if params else {}
    request_params['api_key'] = EIA_API_KEY
    
    try:
        response = requests.get(url, params=request_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"EIA API request failed for {route}: {str(e)}")

def _parse_eia_data(response: Dict) -> List[Dict]:
    """
    Parse EIA API response and extract data records.
    
    Args:
        response: Raw API response dict
    
    Returns:
        list: Cleaned data records
    """
    if 'response' in response and 'data' in response['response']:
        return response['response']['data']
    elif 'data' in response:
        return response['data']
    else:
        return []

# ========== CRUDE OIL PRICES ==========

def get_crude_oil_prices(frequency: str = "daily", start_date: str = None, end_date: str = None, limit: int = 100) -> Dict:
    """
    Get crude oil spot prices (WTI and Brent).
    
    Args:
        frequency: Data frequency ('daily', 'weekly', 'monthly', 'annual')
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        limit: Maximum number of records to return
    
    Returns:
        dict: {
            'metadata': {...},
            'data': [{'period': '2024-01-01', 'value': 75.23, 'series': 'WTI', ...}, ...]
        }
    """
    params = {
        'frequency': frequency,
        'data[0]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit
    }
    
    if start_date:
        params['start'] = start_date
    if end_date:
        params['end'] = end_date
    
    try:
        response = _make_eia_request('petroleum/pri/spt/data', params)
        data = _parse_eia_data(response)
        
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Petroleum Prices',
                'frequency': frequency,
                'count': len(data),
                'fetched_at': datetime.utcnow().isoformat()
            },
            'data': data
        }
    except Exception as e:
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Petroleum Prices',
                'error': str(e)
            },
            'data': []
        }

# ========== NATURAL GAS PRICES ==========

def get_natural_gas_prices(frequency: str = "monthly", start_date: str = None, end_date: str = None, limit: int = 100) -> Dict:
    """
    Get natural gas prices (Henry Hub spot price).
    
    Args:
        frequency: Data frequency ('daily', 'weekly', 'monthly', 'annual')
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        limit: Maximum number of records to return
    
    Returns:
        dict: {
            'metadata': {...},
            'data': [{'period': '2024-01', 'value': 2.54, ...}, ...]
        }
    """
    params = {
        'frequency': frequency,
        'data[0]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit
    }
    
    if start_date:
        params['start'] = start_date
    if end_date:
        params['end'] = end_date
    
    try:
        response = _make_eia_request('natural-gas/pri/sum/data', params)
        data = _parse_eia_data(response)
        
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Natural Gas Prices',
                'frequency': frequency,
                'count': len(data),
                'fetched_at': datetime.utcnow().isoformat()
            },
            'data': data
        }
    except Exception as e:
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Natural Gas Prices',
                'error': str(e)
            },
            'data': []
        }

# ========== PETROLEUM INVENTORIES ==========

def get_petroleum_inventories(frequency: str = "weekly", start_date: str = None, end_date: str = None, limit: int = 100) -> Dict:
    """
    Get petroleum stocks/inventories (crude oil, gasoline, distillate).
    
    Args:
        frequency: Data frequency ('weekly', 'monthly', 'annual')
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        limit: Maximum number of records to return
    
    Returns:
        dict: {
            'metadata': {...},
            'data': [{'period': '2024-01-05', 'value': 425000, 'product': 'Crude Oil', ...}, ...]
        }
    """
    params = {
        'frequency': frequency,
        'data[0]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit
    }
    
    if start_date:
        params['start'] = start_date
    if end_date:
        params['end'] = end_date
    
    try:
        response = _make_eia_request('petroleum/stoc/wstk/data', params)
        data = _parse_eia_data(response)
        
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Petroleum Inventories',
                'frequency': frequency,
                'count': len(data),
                'fetched_at': datetime.utcnow().isoformat()
            },
            'data': data
        }
    except Exception as e:
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Petroleum Inventories',
                'error': str(e)
            },
            'data': []
        }

# ========== ELECTRICITY DATA ==========

def get_electricity_data(frequency: str = "monthly", start_date: str = None, end_date: str = None, limit: int = 100) -> Dict:
    """
    Get electricity retail sales and price data.
    
    Args:
        frequency: Data frequency ('monthly', 'quarterly', 'annual')
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        limit: Maximum number of records to return
    
    Returns:
        dict: {
            'metadata': {...},
            'data': [{'period': '2024-01', 'sales': 123456, 'price': 0.13, ...}, ...]
        }
    """
    params = {
        'frequency': frequency,
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': limit
    }
    
    if start_date:
        params['start'] = start_date
    if end_date:
        params['end'] = end_date
    
    try:
        response = _make_eia_request('electricity/retail-sales/data', params)
        data = _parse_eia_data(response)
        
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Electricity',
                'frequency': frequency,
                'count': len(data),
                'fetched_at': datetime.utcnow().isoformat()
            },
            'data': data
        }
    except Exception as e:
        return {
            'metadata': {
                'source': 'EIA',
                'category': 'Electricity',
                'error': str(e)
            },
            'data': []
        }

# ========== GENERIC SERIES FETCHER ==========

def get_eia_series(route: str, params: Dict[str, Any] = None) -> Dict:
    """
    Generic function to fetch any EIA data series.
    
    Args:
        route: API route (e.g., 'petroleum/pri/spt/data')
        params: Query parameters dict
    
    Returns:
        dict: {
            'metadata': {...},
            'data': [...]
        }
    
    Example:
        >>> get_eia_series('petroleum/pri/spt/data', {'frequency': 'daily', 'length': 10})
    """
    default_params = {
        'frequency': 'monthly',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': 100
    }
    
    if params:
        default_params.update(params)
    
    try:
        response = _make_eia_request(route, default_params)
        data = _parse_eia_data(response)
        
        return {
            'metadata': {
                'source': 'EIA',
                'route': route,
                'params': default_params,
                'count': len(data),
                'fetched_at': datetime.utcnow().isoformat()
            },
            'data': data
        }
    except Exception as e:
        return {
            'metadata': {
                'source': 'EIA',
                'route': route,
                'error': str(e)
            },
            'data': []
        }

# ========== COMMAND LINE INTERFACE ==========

if __name__ == "__main__":
    print(json.dumps({
        "module": "eia_open_data_api",
        "status": "active",
        "source": "https://www.eia.gov/opendata/",
        "api_key_configured": bool(EIA_API_KEY),
        "functions": [
            "get_crude_oil_prices",
            "get_natural_gas_prices",
            "get_petroleum_inventories",
            "get_electricity_data",
            "get_eia_series"
        ],
        "categories": list(EIA_SERIES.keys())
    }, indent=2))
