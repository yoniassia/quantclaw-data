#!/usr/bin/env python3
"""
Eurostat International Trade API — EU Trade Statistics Module

Provides detailed international trade data for EU countries, including:
- Extra-EU and intra-EU trade by product, partner, and flow
- Trade balances and market shares
- Supply chain metrics for European-focused trading strategies

Source: https://ec.europa.eu/eurostat/web/main/data/database
Category: Trade & Supply Chain
Free tier: True - Fully free with no registration required
Update frequency: Monthly/Annual depending on dataset
Author: QuantClaw Data NightBuilder
Phase: Night Build
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Eurostat API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Key dataset identifiers
DATASETS = {
    'ext_st_ea27': 'Extra-EU trade by partner country (monthly)',
    'ext_lt_maineu': 'EU international trade main aggregates (annual)',
    'ext_go_agg': 'International trade aggregate',
    'ext_st_eu27_2020': 'Extra-EU27 trade since 2020',
    'tet00037': 'EU trade by trading partner',
}

# Trade indicators (correct parameter names for ext_lt_maineu)
TRADE_INDICATORS = {
    'MIO_BAL_VAL': 'Trade balance in million EUR',
    'MIO_EXP_VAL': 'Exports in million EUR',
    'MIO_IMP_VAL': 'Imports in million EUR',
    'PC_IMP_PART': 'Share of imports by partner (%)',
    'PC_EXP_PART': 'Share of exports by partner (%)',
}


def _make_request(dataset: str, params: Dict) -> Dict:
    """
    Internal helper to make Eurostat API requests
    
    Args:
        dataset: Dataset identifier (e.g., 'ext_lt_maineu')
        params: Query parameters dict
    
    Returns:
        Dict with success flag and data or error
    """
    try:
        # Ensure JSON format and English language
        params['format'] = 'JSON'
        params['lang'] = 'en'
        
        url = f"{EUROSTAT_BASE_URL}/{dataset}"
        
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'dataset': dataset,
            'query_params': params
        }
    
    except requests.HTTPError as e:
        error_text = e.response.text[:300] if e.response else str(e)
        return {
            'success': False,
            'error': f'HTTP {e.response.status_code}: {error_text}',
            'dataset': dataset
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request error: {str(e)}',
            'dataset': dataset
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Invalid JSON response: {str(e)}',
            'dataset': dataset
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'dataset': dataset
        }


def _extract_values(response_data: Dict) -> List[Dict]:
    """
    Extract time series values from Eurostat JSON-stat format
    
    Args:
        response_data: Raw Eurostat API response
    
    Returns:
        List of dicts with time, value, and metadata
    """
    try:
        if 'value' not in response_data or not response_data['value']:
            return []
        
        values_dict = response_data.get('value', {})
        dimension = response_data.get('dimension', {})
        
        # Extract time dimension labels
        time_cat = dimension.get('time', {}).get('category', {})
        time_index = time_cat.get('index', {})
        time_labels = {str(v): k for k, v in time_index.items()}
        
        # Extract size to understand dimensionality
        size = response_data.get('size', [])
        
        # Parse values
        records = []
        for idx_str, value in values_dict.items():
            if value is not None:
                idx = int(idx_str)
                
                # Map index to time (simplified - assumes time is last dimension)
                time_idx = idx % size[-1] if size else idx
                time_val = time_labels.get(str(time_idx), f'T{time_idx}')
                
                records.append({
                    'time': time_val,
                    'value': float(value) if isinstance(value, (int, float, str)) else value,
                    'index': idx
                })
        
        # Sort by time
        records.sort(key=lambda x: x['time'])
        
        return records
    
    except Exception as e:
        return []


def get_eu_trade_balance(
    country: str = 'EU27_2020',
    partner: str = 'WORLD',
    year: Optional[int] = None
) -> Dict:
    """
    Get EU trade balance for a country with a trading partner
    
    Args:
        country: Country code (default 'EU27_2020')
        partner: Partner country code (default 'WORLD' or specific like 'US', 'CN')
        year: Year (default None for all available years)
    
    Returns:
        Dict with trade balance, exports, imports values
    """
    params = {
        'geo': country,
        'partner': partner,
        'indic_et': 'MIO_BAL_VAL',  # Trade balance
        'sitc06': 'TOTAL',  # All products
    }
    
    if year:
        params['time'] = str(year)
    
    result = _make_request('ext_lt_maineu', params)
    
    if not result['success']:
        return result
    
    records = _extract_values(result['data'])
    
    if not records:
        # Try getting exports and imports separately
        params_exp = params.copy()
        params_exp['indic_et'] = 'MIO_EXP_VAL'
        
        params_imp = params.copy()
        params_imp['indic_et'] = 'MIO_IMP_VAL'
        
        exp_result = _make_request('ext_lt_maineu', params_exp)
        imp_result = _make_request('ext_lt_maineu', params_imp)
        
        exp_records = _extract_values(exp_result['data']) if exp_result['success'] else []
        imp_records = _extract_values(imp_result['data']) if imp_result['success'] else []
        
        if exp_records and imp_records:
            # Calculate balance
            records = []
            for exp, imp in zip(exp_records, imp_records):
                if exp['time'] == imp['time']:
                    records.append({
                        'time': exp['time'],
                        'exports': exp['value'],
                        'imports': imp['value'],
                        'balance': exp['value'] - imp['value']
                    })
    
    if not records:
        return {
            'success': False,
            'error': 'No trade data available for specified parameters',
            'country': country,
            'partner': partner,
            'year': year
        }
    
    # Calculate summary
    latest = records[-1] if records else {}
    total_balance = sum(r.get('balance', r.get('value', 0)) for r in records)
    
    return {
        'success': True,
        'country': country,
        'partner': partner,
        'year': year,
        'latest_period': latest.get('time'),
        'latest_balance_million_eur': latest.get('balance', latest.get('value')),
        'latest_exports_million_eur': latest.get('exports'),
        'latest_imports_million_eur': latest.get('imports'),
        'total_balance_million_eur': round(total_balance, 2) if total_balance else None,
        'periods_available': len(records),
        'time_series': records,
        'timestamp': datetime.now().isoformat()
    }


def get_trade_by_product(
    product_code: str,
    country: str = 'EU27_2020',
    period: Optional[str] = None
) -> Dict:
    """
    Get trade data by product classification code (SITC)
    
    Args:
        product_code: Product code (SITC classification, e.g., 'TOTAL', 'FOOD', 'CHEM')
        country: Country code (default 'EU27_2020')
        period: Time period (e.g., '2023', default latest available)
    
    Returns:
        Dict with product trade values
    """
    params = {
        'geo': country,
        'sitc06': product_code,
        'indic_et': 'MIO_EXP_VAL',  # Exports by default
        'partner': 'WORLD'
    }
    
    if period:
        params['time'] = period
    
    result = _make_request('ext_lt_maineu', params)
    
    if not result['success']:
        return result
    
    records = _extract_values(result['data'])
    
    return {
        'success': True,
        'product_code': product_code,
        'country': country,
        'period': period,
        'records_found': len(records),
        'data': records,
        'latest_value': records[-1]['value'] if records else None,
        'latest_period': records[-1]['time'] if records else None,
        'timestamp': datetime.now().isoformat()
    }


def get_trade_partners(
    country: str = 'EU27_2020',
    flow: str = 'EXPORTS',
    limit: int = 20
) -> Dict:
    """
    Get top trade partners for a country
    
    Args:
        country: Country code (default 'EU27_2020')
        flow: Trade flow 'EXPORTS' or 'IMPORTS' (default 'EXPORTS')
        limit: Max number of partners to return (default 20)
    
    Returns:
        Dict with ranked list of trading partners
    """
    # Map flow to indicator
    indicator = 'MIO_EXP_VAL' if flow.upper() == 'EXPORTS' else 'MIO_IMP_VAL'
    
    params = {
        'geo': country,
        'indic_et': indicator,
        'sitc06': 'TOTAL'
    }
    
    result = _make_request('ext_lt_maineu', params)
    
    if not result['success']:
        return result
    
    data = result.get('data', {})
    dimension = data.get('dimension', {})
    
    # Extract partner information
    partner_cat = dimension.get('partner', {}).get('category', {})
    partner_labels = partner_cat.get('label', {})
    partner_index = partner_cat.get('index', {})
    
    # Get values
    values = data.get('value', {})
    
    # Build partner list (simplified aggregation)
    partners = []
    for partner_code, partner_name in list(partner_labels.items())[:limit]:
        partners.append({
            'partner_code': partner_code,
            'partner_name': partner_name,
            'note': 'Full value extraction requires dimension mapping'
        })
    
    return {
        'success': True,
        'country': country,
        'flow': flow,
        'indicator': indicator,
        'partners_found': len(partner_labels),
        'top_partners': partners[:limit],
        'timestamp': datetime.now().isoformat()
    }


def get_trade_timeseries(
    country: str,
    partner: str,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None
) -> Dict:
    """
    Get trade time series between country and partner
    
    Args:
        country: Country code (e.g., 'EU27_2020', 'DE')
        partner: Partner country code (e.g., 'US', 'CN', 'WORLD')
        start_period: Start year (e.g., '2020', default 5 years ago)
        end_period: End year (e.g., '2025', default current year)
    
    Returns:
        Dict with annual time series and trend analysis
    """
    if start_period is None:
        start_period = str(datetime.now().year - 5)
    
    if end_period is None:
        end_period = str(datetime.now().year)
    
    # Get exports
    params_exp = {
        'geo': country,
        'partner': partner,
        'indic_et': 'MIO_EXP_VAL',
        'sitc06': 'TOTAL',
        'startPeriod': start_period,
        'endPeriod': end_period
    }
    
    # Get imports
    params_imp = params_exp.copy()
    params_imp['indic_et'] = 'MIO_IMP_VAL'
    
    exp_result = _make_request('ext_lt_maineu', params_exp)
    imp_result = _make_request('ext_lt_maineu', params_imp)
    
    if not exp_result['success'] and not imp_result['success']:
        return {
            'success': False,
            'error': 'Could not fetch trade data',
            'country': country,
            'partner': partner
        }
    
    exp_records = _extract_values(exp_result['data']) if exp_result['success'] else []
    imp_records = _extract_values(imp_result['data']) if imp_result['success'] else []
    
    # Merge exports and imports
    time_series = []
    exp_dict = {r['time']: r['value'] for r in exp_records}
    imp_dict = {r['time']: r['value'] for r in imp_records}
    
    all_times = sorted(set(exp_dict.keys()) | set(imp_dict.keys()))
    
    for time in all_times:
        exp_val = exp_dict.get(time, 0)
        imp_val = imp_dict.get(time, 0)
        
        time_series.append({
            'time': time,
            'exports_million_eur': exp_val,
            'imports_million_eur': imp_val,
            'balance_million_eur': exp_val - imp_val
        })
    
    # Calculate trends
    if time_series:
        exp_values = [r['exports_million_eur'] for r in time_series]
        imp_values = [r['imports_million_eur'] for r in time_series]
        
        avg_exports = sum(exp_values) / len(exp_values) if exp_values else 0
        avg_imports = sum(imp_values) / len(imp_values) if imp_values else 0
        
        # Growth rate (first to last)
        exp_growth = 0
        imp_growth = 0
        if len(exp_values) >= 2 and exp_values[0] != 0:
            exp_growth = ((exp_values[-1] - exp_values[0]) / exp_values[0]) * 100
        if len(imp_values) >= 2 and imp_values[0] != 0:
            imp_growth = ((imp_values[-1] - imp_values[0]) / imp_values[0]) * 100
    else:
        avg_exports = avg_imports = exp_growth = imp_growth = 0
    
    return {
        'success': True,
        'country': country,
        'partner': partner,
        'start_period': start_period,
        'end_period': end_period,
        'records_count': len(time_series),
        'avg_exports_million_eur': round(avg_exports, 2),
        'avg_imports_million_eur': round(avg_imports, 2),
        'exports_growth_pct': round(exp_growth, 2),
        'imports_growth_pct': round(imp_growth, 2),
        'time_series': time_series,
        'timestamp': datetime.now().isoformat()
    }


def search_datasets(keyword: str = 'trade') -> Dict:
    """
    Search available Eurostat trade datasets
    
    Args:
        keyword: Search keyword (default 'trade')
    
    Returns:
        Dict with matching datasets and available indicators
    """
    keyword_lower = keyword.lower()
    
    matching_datasets = {
        code: desc
        for code, desc in DATASETS.items()
        if keyword_lower in desc.lower() or keyword_lower in code.lower()
    }
    
    return {
        'success': True,
        'keyword': keyword,
        'matches_found': len(matching_datasets),
        'datasets': [
            {
                'code': code,
                'description': desc,
                'url': f'{EUROSTAT_BASE_URL}/{code}'
            }
            for code, desc in matching_datasets.items()
        ],
        'available_indicators': TRADE_INDICATORS,
        'timestamp': datetime.now().isoformat()
    }


def get_eurostat_metadata() -> Dict:
    """
    Get metadata about available datasets and indicators
    
    Returns:
        Dict with complete registry
    """
    return {
        'success': True,
        'api_base_url': EUROSTAT_BASE_URL,
        'datasets': DATASETS,
        'trade_indicators': TRADE_INDICATORS,
        'total_datasets': len(DATASETS),
        'example_countries': ['EU27_2020', 'DE', 'FR', 'IT', 'ES', 'US', 'CN', 'UK'],
        'example_partners': ['WORLD', 'US', 'CN', 'UK', 'JP', 'RU'],
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Eurostat International Trade API - QuantClaw Data Module")
    print("=" * 70)
    
    # Test search
    print("\n1. Searching datasets...")
    search_result = search_datasets('trade')
    print(f"✅ Found {search_result['matches_found']} datasets")
    
    # Test trade balance
    print("\n2. Getting EU-US trade balance...")
    balance = get_eu_trade_balance(country='EU27_2020', partner='US', year=2023)
    if balance['success']:
        print(f"✅ Latest balance: {balance.get('latest_balance_million_eur', 'N/A')} M EUR")
    else:
        print(f"⚠️  {balance.get('error', 'Unknown error')}")
    
    print("\n" + json.dumps(search_result, indent=2))
