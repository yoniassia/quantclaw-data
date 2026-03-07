#!/usr/bin/env python3
"""
World Bank Commodity Price Data API Module

Global commodity price indices and data from the World Bank's Commodity Markets.
Provides monthly Pink Sheet data on energy, metals, and agriculture prices.

Data sources:
- World Bank API v2: https://api.worldbank.org/v2/
- Commodity Markets (Pink Sheet): Energy, metals, agriculture prices
- Historical data back to 1960 for many commodities

Source: https://www.worldbank.org/en/research/commodity-markets
Category: Commodities & Energy
Free tier: True (No API key required)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# World Bank API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"
DEFAULT_TIMEOUT = 30

# ========== COMMODITY INDICATOR REGISTRY ==========

# World Bank Commodity Price Indicators (World Bank Commodity Markets data)
COMMODITY_INDICATORS = {
    # ===== ENERGY =====
    'ENERGY': {
        'crude_oil': 'CRUDE_WTI',  # Crude oil, WTI spot price
        'crude_oil_brent': 'CRUDE_BRENT',  # Crude oil, Brent
        'crude_oil_dubai': 'CRUDE_DUBAI',  # Crude oil, Dubai
        'natural_gas': 'NATURAL_GAS_US',  # Natural gas, US
        'natural_gas_eu': 'NATURAL_GAS_EUR',  # Natural gas, Europe
        'coal_aus': 'COAL_AUSTRALIAN',  # Coal, Australian
        'coal_sa': 'COAL_STHAFR',  # Coal, South African
    },
    
    # ===== METALS & MINERALS =====
    'METALS': {
        'aluminum': 'ALUMINUM',
        'copper': 'COPPER',
        'iron_ore': 'IRONORE',
        'lead': 'LEAD',
        'nickel': 'NICKEL',
        'tin': 'TIN',
        'zinc': 'ZINC',
        'gold': 'GOLD',
        'silver': 'SILVER',
        'platinum': 'PLATINUM',
    },
    
    # ===== AGRICULTURE =====
    'AGRICULTURE': {
        'wheat': 'WHEAT_US_HRW',  # Wheat, US HRW
        'wheat_srw': 'WHEAT_US_SRW',  # Wheat, US SRW
        'maize': 'MAIZE',  # Maize (corn)
        'rice': 'RICE_05',  # Rice, Thailand 5%
        'barley': 'BARLEY',
        'sorghum': 'SORGHUM',
        'soybeans': 'SOYBEAN',
        'soybean_oil': 'SOYBEAN_OIL',
        'soybean_meal': 'SOYBEAN_MEAL',
        'palm_oil': 'PALM_OIL',
        'sugar': 'SUGAR_WLD',  # Sugar, world
        'coffee_arabica': 'COFFEE_ARAB',
        'coffee_robusta': 'COFFEE_ROBU',
        'cocoa': 'COCOA',
        'tea': 'TEA_COLOMBO',
        'cotton': 'COTTON_A_INDEX',
        'rubber': 'RUBBER_RSS3',
        'tobacco': 'TOBACCO',
        'beef': 'BEEF',
        'chicken': 'CHICKEN',
        'banana': 'BANANA_EU',
        'orange': 'ORANGE',
    },
    
    # ===== FERTILIZERS =====
    'FERTILIZERS': {
        'dap': 'DAP',  # Diammonium phosphate
        'phosphate_rock': 'PHOSROCK',
        'potassium_chloride': 'POTASSIUM_CHLORIDE',
        'tsp': 'TSP',  # Triple superphosphate
        'urea': 'UREA',
    },
}

# Flatten for easy lookup
ALL_COMMODITIES = {}
for category, items in COMMODITY_INDICATORS.items():
    ALL_COMMODITIES.update(items)


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to World Bank API with error handling.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        Exception on API errors
    """
    url = f"{WB_BASE_URL}/{endpoint}"
    default_params = {'format': 'json', 'per_page': 1000}
    
    if params:
        default_params.update(params)
    
    try:
        response = requests.get(url, params=default_params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # World Bank API returns [metadata, data] array
        if isinstance(data, list) and len(data) >= 2:
            return {'metadata': data[0], 'data': data[1]}
        
        return {'data': data}
        
    except requests.exceptions.Timeout:
        raise Exception(f"Request timeout after {DEFAULT_TIMEOUT}s: {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"World Bank API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {str(e)}")


def list_commodities() -> Dict[str, List[str]]:
    """
    List all available commodities grouped by category.
    
    Returns:
        Dict with categories as keys and commodity lists as values
        
    Example:
        {
            'ENERGY': ['crude_oil', 'natural_gas', 'coal_aus', ...],
            'METALS': ['aluminum', 'copper', 'gold', ...],
            'AGRICULTURE': ['wheat', 'maize', 'rice', ...]
        }
    """
    result = {}
    for category, commodities in COMMODITY_INDICATORS.items():
        result[category] = list(commodities.keys())
    
    return result


def get_commodity_prices(commodity: str = 'crude_oil') -> Dict:
    """
    Get latest price for a specific commodity.
    
    Args:
        commodity: Commodity identifier (e.g., 'crude_oil', 'gold', 'wheat')
        
    Returns:
        Dict with latest price data
        
    Example:
        {
            'commodity': 'crude_oil',
            'indicator': 'CRUDE_WTI',
            'value': 75.50,
            'date': '2026-02',
            'unit': 'USD per barrel'
        }
    """
    if commodity not in ALL_COMMODITIES:
        available = ', '.join(list(ALL_COMMODITIES.keys())[:10])
        raise ValueError(f"Unknown commodity: {commodity}. Try: {available}...")
    
    indicator = ALL_COMMODITIES[commodity]
    
    # World Bank uses MRV (Most Recent Value) for latest data
    endpoint = f"country/all/indicator/{indicator}"
    params = {'date': 'MRV:1'}  # Most recent value
    
    try:
        response = _make_request(endpoint, params)
        data_points = response.get('data', [])
        
        if not data_points:
            return {
                'commodity': commodity,
                'indicator': indicator,
                'value': None,
                'date': None,
                'error': 'No data available'
            }
        
        latest = data_points[0]
        return {
            'commodity': commodity,
            'indicator': indicator,
            'value': latest.get('value'),
            'date': latest.get('date'),
            'country': latest.get('country', {}).get('value'),
            'unit': latest.get('unit', 'Index or USD'),
            'indicator_name': latest.get('indicator', {}).get('value')
        }
        
    except Exception as e:
        return {
            'commodity': commodity,
            'indicator': indicator,
            'error': str(e)
        }


def get_commodity_price_history(commodity: str = 'crude_oil', start_year: int = 2020) -> List[Dict]:
    """
    Get historical price data for a commodity.
    
    Args:
        commodity: Commodity identifier
        start_year: Starting year for historical data (default: 2020)
        
    Returns:
        List of dicts with historical prices
        
    Example:
        [
            {'date': '2026-02', 'value': 75.50},
            {'date': '2026-01', 'value': 74.20},
            ...
        ]
    """
    if commodity not in ALL_COMMODITIES:
        raise ValueError(f"Unknown commodity: {commodity}")
    
    indicator = ALL_COMMODITIES[commodity]
    current_year = datetime.now().year
    
    endpoint = f"country/all/indicator/{indicator}"
    params = {'date': f"{start_year}:{current_year}"}
    
    try:
        response = _make_request(endpoint, params)
        data_points = response.get('data', [])
        
        if not data_points:
            return []
        
        # Sort by date descending
        history = []
        for point in data_points:
            if point.get('value') is not None:
                history.append({
                    'date': point.get('date'),
                    'value': point.get('value'),
                    'country': point.get('country', {}).get('value')
                })
        
        return sorted(history, key=lambda x: x['date'], reverse=True)
        
    except Exception as e:
        return [{'error': str(e)}]


def get_energy_prices() -> Dict[str, Dict]:
    """
    Get latest prices for all energy commodities.
    
    Returns:
        Dict with energy commodity prices
        
    Example:
        {
            'crude_oil': {'value': 75.50, 'date': '2026-02'},
            'natural_gas': {'value': 3.20, 'date': '2026-02'},
            ...
        }
    """
    energy_commodities = COMMODITY_INDICATORS['ENERGY']
    results = {}
    
    for commodity_name in energy_commodities.keys():
        price_data = get_commodity_prices(commodity_name)
        results[commodity_name] = {
            'value': price_data.get('value'),
            'date': price_data.get('date'),
            'unit': price_data.get('unit'),
            'indicator': price_data.get('indicator')
        }
    
    return results


def get_metals_prices() -> Dict[str, Dict]:
    """
    Get latest prices for all metals and minerals.
    
    Returns:
        Dict with metals prices
        
    Example:
        {
            'gold': {'value': 2050.00, 'date': '2026-02'},
            'copper': {'value': 4.15, 'date': '2026-02'},
            ...
        }
    """
    metals = COMMODITY_INDICATORS['METALS']
    results = {}
    
    for commodity_name in metals.keys():
        price_data = get_commodity_prices(commodity_name)
        results[commodity_name] = {
            'value': price_data.get('value'),
            'date': price_data.get('date'),
            'unit': price_data.get('unit'),
            'indicator': price_data.get('indicator')
        }
    
    return results


def get_agriculture_prices() -> Dict[str, Dict]:
    """
    Get latest prices for agricultural commodities.
    
    Returns:
        Dict with agriculture prices
        
    Example:
        {
            'wheat': {'value': 215.50, 'date': '2026-02'},
            'maize': {'value': 198.75, 'date': '2026-02'},
            ...
        }
    """
    agriculture = COMMODITY_INDICATORS['AGRICULTURE']
    results = {}
    
    for commodity_name in agriculture.keys():
        price_data = get_commodity_prices(commodity_name)
        results[commodity_name] = {
            'value': price_data.get('value'),
            'date': price_data.get('date'),
            'unit': price_data.get('unit'),
            'indicator': price_data.get('indicator')
        }
    
    return results


def get_pink_sheet_data(frequency: str = 'monthly') -> Dict:
    """
    Get World Bank Pink Sheet commodity market data summary.
    
    Note: The Pink Sheet is published as an Excel file. This function provides
    metadata and access info. For full Pink Sheet data, download from:
    https://www.worldbank.org/en/research/commodity-markets
    
    Args:
        frequency: Data frequency ('monthly', 'quarterly', 'annual')
        
    Returns:
        Dict with Pink Sheet information and sample commodity data
    """
    if frequency not in ['monthly', 'quarterly', 'annual']:
        frequency = 'monthly'
    
    # Get sample data from key commodity indices
    sample_commodities = ['crude_oil', 'gold', 'wheat', 'natural_gas', 'copper']
    sample_data = {}
    
    for commodity in sample_commodities:
        try:
            price_data = get_commodity_prices(commodity)
            sample_data[commodity] = price_data
        except Exception:
            continue
    
    return {
        'pink_sheet_info': {
            'description': 'World Bank Commodity Markets (Pink Sheet)',
            'frequency': frequency,
            'url': 'https://www.worldbank.org/en/research/commodity-markets',
            'excel_download': 'https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMOHistoricalDataMonthly.xlsx',
            'note': 'Full Pink Sheet data available via Excel download. API provides individual commodity indicators.'
        },
        'sample_data': sample_data,
        'timestamp': datetime.now().isoformat(),
        'available_categories': list(COMMODITY_INDICATORS.keys())
    }


if __name__ == "__main__":
    # Quick test
    print(json.dumps({
        "module": "world_bank_commodity_price_data_api",
        "status": "active",
        "commodities_count": len(ALL_COMMODITIES),
        "categories": list(COMMODITY_INDICATORS.keys()),
        "source": "https://www.worldbank.org/en/research/commodity-markets"
    }, indent=2))
