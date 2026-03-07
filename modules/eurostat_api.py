#!/usr/bin/env python3
"""
Eurostat API — European Union Statistics Module

Provides comprehensive European economic, demographic, and labor market data.
Focused on key indicators for financial and macroeconomic analysis:
- Employment rates and labor statistics
- GDP growth and national accounts
- Inflation (HICP) data
- Population demographics
- Trade balance and external trade

Source: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
Category: Labor & Demographics, Macroeconomics
Free tier: True (100 calls/hour, no registration required)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Eurostat API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
EUROSTAT_CATALOG_URL = "https://ec.europa.eu/eurostat/api/dissemination/catalogue/1.0/datasets"

# ========== DATASET REGISTRY ==========

EUROSTAT_DATASETS = {
    'EMPLOYMENT': {
        'lfsa_ergan': 'Employment rate by sex, age and NUTS 2 regions',
        'lfsa_ergaed': 'Employment rate by sex, age and educational attainment level',
        'lfsq_ergan': 'Employment rate - quarterly data',
    },
    'GDP': {
        'namq_10_gdp': 'GDP and main components - quarterly data',
        'nama_10_gdp': 'GDP and main components - annual data',
        'namq_10_pc': 'GDP per capita - quarterly data',
    },
    'INFLATION': {
        'prc_hicp_manr': 'HICP - monthly data (annual rate of change)',
        'prc_hicp_midx': 'HICP - monthly data (index)',
        'prc_hicp_aind': 'HICP - annual data (index)',
    },
    'POPULATION': {
        'demo_pjan': 'Population on 1st January by age and sex',
        'demo_gind': 'Population change - demographic balance and crude rates',
        'proj_19np': 'Population projections',
    },
    'TRADE': {
        'ext_lt_maineu': 'EU trade since 1999 by HS2-4-6 and CN8',
        'ext_lt_intratrd': 'EU trade since 1988 by SITC',
        'bop_its6_det': 'International trade in services - detailed data',
    },
}


def _fetch_eurostat_data(dataset_code: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Internal function to fetch data from Eurostat API.
    
    Args:
        dataset_code: Eurostat dataset code (e.g., 'lfsa_ergan')
        params: Optional URL parameters for filtering
        
    Returns:
        Dict containing API response data
        
    Raises:
        requests.RequestException: If API call fails
    """
    url = f"{EUROSTAT_BASE_URL}/{dataset_code}"
    
    # Default parameters
    default_params = {
        'format': 'JSON',
        'lang': 'EN'
    }
    
    if params:
        default_params.update(params)
    
    try:
        response = requests.get(url, params=default_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {
            'error': str(e),
            'dataset': dataset_code,
            'status': 'failed'
        }


def _parse_eurostat_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse Eurostat JSON-stat format into readable records.
    
    Args:
        data: Raw API response
        
    Returns:
        List of data records with time periods and values
    """
    if 'error' in data:
        return [data]
    
    try:
        # Extract dimensions and values
        dimension = data.get('dimension', {})
        value = data.get('value', {})
        
        # Get time dimension
        time_dimension = dimension.get('time', {}).get('category', {}).get('index', {})
        time_labels = dimension.get('time', {}).get('category', {}).get('label', {})
        
        # Get geo dimension
        geo_dimension = dimension.get('geo', {}).get('category', {}).get('index', {})
        
        # Parse values
        records = []
        for idx_str, val in value.items():
            idx = int(idx_str)
            
            # Find corresponding time period
            time_key = None
            for t_key, t_idx in time_dimension.items():
                if t_idx == idx % len(time_dimension):
                    time_key = t_key
                    break
            
            if time_key:
                records.append({
                    'period': time_key,
                    'value': val,
                    'label': time_labels.get(time_key, time_key)
                })
        
        # Sort by period descending (most recent first)
        records.sort(key=lambda x: x['period'], reverse=True)
        return records
        
    except (KeyError, ValueError) as e:
        return [{
            'error': f'Parse error: {str(e)}',
            'raw_data_keys': list(data.keys())
        }]


def get_employment_rate(country_code: str = 'EU27_2020', age_group: str = 'Y20-64') -> Dict[str, Any]:
    """
    Get employment rate from Eurostat lfsa_ergan dataset.
    
    Args:
        country_code: Geographic code (default: EU27_2020)
        age_group: Age group code (default: Y20-64 for 20-64 years)
        
    Returns:
        Dict with employment rate data including:
        - latest_value: Most recent employment rate
        - latest_period: Time period of latest data
        - historical: List of historical data points
        - metadata: Dataset information
        
    Example:
        >>> data = get_employment_rate('EU27_2020', 'Y20-64')
        >>> print(data['latest_value'])
    """
    params = {
        'sex': 'T',  # Total (both sexes)
        'age': age_group,
        'geo': country_code,
        'unit': 'PC'  # Percentage
    }
    
    data = _fetch_eurostat_data('lfsa_ergan', params)
    
    if 'error' in data:
        return data
    
    records = _parse_eurostat_response(data)
    
    return {
        'dataset': 'lfsa_ergan',
        'indicator': 'Employment Rate',
        'country': country_code,
        'age_group': age_group,
        'latest_value': records[0]['value'] if records else None,
        'latest_period': records[0]['period'] if records else None,
        'historical': records[:10],  # Last 10 data points
        'metadata': {
            'source': 'Eurostat',
            'unit': 'Percentage',
            'last_updated': datetime.now().isoformat()
        }
    }


def get_gdp_growth(country_code: str = 'EU27_2020', frequency: str = 'Q') -> Dict[str, Any]:
    """
    Get GDP growth from Eurostat namq_10_gdp dataset.
    
    Args:
        country_code: Geographic code (default: EU27_2020)
        frequency: Data frequency - 'Q' for quarterly, 'A' for annual
        
    Returns:
        Dict with GDP growth data including:
        - latest_value: Most recent GDP value
        - latest_period: Time period of latest data
        - growth_rate: Year-over-year growth rate (if available)
        - historical: List of historical data points
        - metadata: Dataset information
        
    Example:
        >>> data = get_gdp_growth('EU27_2020', 'Q')
        >>> print(f"GDP: {data['latest_value']}")
    """
    dataset = 'namq_10_gdp' if frequency == 'Q' else 'nama_10_gdp'
    
    # Add filters to avoid 413 error (dataset too large)
    params = {
        'na_item': 'B1GQ',  # Gross domestic product at market prices
        'unit': 'CLV10_MNAC',  # Chain linked volumes, million units of national currency
        'geo': country_code,
        's_adj': 'SCA'  # Seasonally and calendar adjusted
    }
    
    data = _fetch_eurostat_data(dataset, params)
    
    if 'error' in data:
        return data
    
    records = _parse_eurostat_response(data)
    
    # Calculate growth rate if we have enough data
    growth_rate = None
    if len(records) >= 2:
        try:
            current = float(records[0]['value'])
            previous = float(records[1]['value'])
            growth_rate = ((current - previous) / previous) * 100
        except (ValueError, TypeError):
            pass
    
    return {
        'dataset': dataset,
        'indicator': 'GDP and Main Components',
        'country': country_code,
        'frequency': 'Quarterly' if frequency == 'Q' else 'Annual',
        'latest_value': records[0]['value'] if records else None,
        'latest_period': records[0]['period'] if records else None,
        'growth_rate': round(growth_rate, 2) if growth_rate else None,
        'historical': records[:12],  # Last 12 data points
        'metadata': {
            'source': 'Eurostat',
            'unit': 'Chain linked volumes (2010), million EUR',
            'last_updated': datetime.now().isoformat()
        }
    }


def get_inflation_rate(country_code: str = 'EU27_2020') -> Dict[str, Any]:
    """
    Get HICP inflation rate from Eurostat prc_hicp_manr dataset.
    
    Args:
        country_code: Geographic code (default: EU27_2020)
        
    Returns:
        Dict with inflation data including:
        - latest_value: Most recent inflation rate (annual % change)
        - latest_period: Time period of latest data
        - historical: List of historical monthly inflation rates
        - metadata: Dataset information
        
    Example:
        >>> data = get_inflation_rate('EU27_2020')
        >>> print(f"Inflation: {data['latest_value']}%")
    """
    data = _fetch_eurostat_data('prc_hicp_manr')
    
    if 'error' in data:
        return data
    
    records = _parse_eurostat_response(data)
    
    return {
        'dataset': 'prc_hicp_manr',
        'indicator': 'HICP - Harmonized Index of Consumer Prices',
        'country': country_code,
        'latest_value': records[0]['value'] if records else None,
        'latest_period': records[0]['period'] if records else None,
        'historical': records[:24],  # Last 24 months
        'metadata': {
            'source': 'Eurostat',
            'unit': 'Annual rate of change (%)',
            'last_updated': datetime.now().isoformat()
        }
    }


def get_population(country_code: str = 'EU27_2020') -> Dict[str, Any]:
    """
    Get population data from Eurostat demo_pjan dataset.
    
    Args:
        country_code: Geographic code (default: EU27_2020)
        
    Returns:
        Dict with population data including:
        - latest_value: Most recent population count
        - latest_period: Year of latest data
        - historical: List of historical population figures
        - metadata: Dataset information
        
    Example:
        >>> data = get_population('EU27_2020')
        >>> print(f"Population: {data['latest_value']:,}")
    """
    params = {
        'sex': 'T',  # Total
        'age': 'TOTAL',  # All ages
        'geo': country_code
    }
    
    data = _fetch_eurostat_data('demo_pjan', params)
    
    if 'error' in data:
        return data
    
    records = _parse_eurostat_response(data)
    
    return {
        'dataset': 'demo_pjan',
        'indicator': 'Population on 1st January',
        'country': country_code,
        'latest_value': records[0]['value'] if records else None,
        'latest_period': records[0]['period'] if records else None,
        'historical': records[:10],  # Last 10 years
        'metadata': {
            'source': 'Eurostat',
            'unit': 'Number of persons',
            'last_updated': datetime.now().isoformat()
        }
    }


def get_trade_balance(country_code: str = 'EU27_2020', partner: str = 'WORLD') -> Dict[str, Any]:
    """
    Get trade balance data from Eurostat ext_lt_maineu dataset.
    
    Args:
        country_code: Geographic code (default: EU27_2020)
        partner: Trading partner code (default: WORLD for total trade)
        
    Returns:
        Dict with trade data including:
        - latest_value: Most recent trade value
        - latest_period: Time period of latest data
        - historical: List of historical trade data
        - metadata: Dataset information
        
    Example:
        >>> data = get_trade_balance('EU27_2020', 'WORLD')
        >>> print(f"Trade: {data['latest_value']}")
    """
    params = {
        'reporter': country_code,
        'partner': partner,
        'sitc06': 'TOTAL',  # All products
        'indic_et': 'BAL'  # Balance (exports - imports)
    }
    
    data = _fetch_eurostat_data('ext_lt_maineu', params)
    
    if 'error' in data:
        return data
    
    records = _parse_eurostat_response(data)
    
    return {
        'dataset': 'ext_lt_maineu',
        'indicator': 'EU Trade Balance',
        'country': country_code,
        'partner': partner,
        'latest_value': records[0]['value'] if records else None,
        'latest_period': records[0]['period'] if records else None,
        'historical': records[:12],  # Last 12 data points
        'metadata': {
            'source': 'Eurostat',
            'unit': 'Million EUR',
            'last_updated': datetime.now().isoformat()
        }
    }


def search_datasets(keyword: str) -> Dict[str, Any]:
    """
    Search Eurostat dataset catalog by keyword.
    
    Args:
        keyword: Search term to find relevant datasets
        
    Returns:
        Dict with search results including:
        - keyword: Search term used
        - matches: List of matching datasets from local registry
        - total_matches: Number of datasets found
        - categories: Categories containing matches
        
    Example:
        >>> results = search_datasets('employment')
        >>> for match in results['matches']:
        ...     print(f"{match['code']}: {match['description']}")
    """
    keyword_lower = keyword.lower()
    matches = []
    categories_found = set()
    
    # Search through local dataset registry
    for category, datasets in EUROSTAT_DATASETS.items():
        for code, description in datasets.items():
            if (keyword_lower in code.lower() or 
                keyword_lower in description.lower() or
                keyword_lower in category.lower()):
                matches.append({
                    'code': code,
                    'description': description,
                    'category': category,
                    'url': f"{EUROSTAT_BASE_URL}/{code}?format=JSON&lang=EN"
                })
                categories_found.add(category)
    
    return {
        'keyword': keyword,
        'matches': matches,
        'total_matches': len(matches),
        'categories': sorted(list(categories_found)),
        'metadata': {
            'source': 'Eurostat Dataset Registry',
            'search_date': datetime.now().isoformat()
        }
    }


# ========== MODULE INFO ==========

def get_module_info() -> Dict[str, Any]:
    """
    Get information about this module.
    
    Returns:
        Dict with module metadata
    """
    return {
        'module': 'eurostat_api',
        'description': 'Eurostat API integration for EU economic and demographic data',
        'version': '1.0.0',
        'author': 'QuantClaw Data NightBuilder',
        'functions': [
            'get_employment_rate',
            'get_gdp_growth',
            'get_inflation_rate',
            'get_population',
            'get_trade_balance',
            'search_datasets'
        ],
        'datasets_covered': len([d for cat in EUROSTAT_DATASETS.values() for d in cat]),
        'categories': list(EUROSTAT_DATASETS.keys()),
        'base_url': EUROSTAT_BASE_URL,
        'free_tier': True,
        'rate_limit': '100 calls/hour'
    }


if __name__ == "__main__":
    # Demo output
    info = get_module_info()
    print(json.dumps(info, indent=2))
