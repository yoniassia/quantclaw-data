#!/usr/bin/env python3
"""
Bank of Canada Rates API — Valet Web Services

The Bank of Canada Valet API provides free access to:
- Foreign exchange rates (daily updates)
- Policy interest rates
- Bond yields and money market rates
- Economic and financial indicators

Source: https://www.bankofcanada.ca/valet/
Category: Macro / Central Banks
Free tier: True (no API key required, rate limit ~1000 requests/month)
Update frequency: Daily for FX rates, as published for other series
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Bank of Canada Valet API Configuration
VALET_BASE_URL = "https://www.bankofcanada.ca/valet"

# ========== SERIES REGISTRY ==========

# Key FX rate series
FX_SERIES = {
    'FXUSDCAD': 'US Dollar to Canadian Dollar',
    'FXEURCAD': 'Euro to Canadian Dollar',
    'FXGBPCAD': 'UK Pound to Canadian Dollar',
    'FXJPYCAD': 'Japanese Yen to Canadian Dollar',
    'FXCHFCAD': 'Swiss Franc to Canadian Dollar',
    'FXAUDCAD': 'Australian Dollar to Canadian Dollar',
    'FXMXNCAD': 'Mexican Peso to Canadian Dollar',
    'FXCNYCAD': 'Chinese Yuan to Canadian Dollar',
    'FXINRCAD': 'Indian Rupee to Canadian Dollar',
}

# Policy and interest rate series
RATE_SERIES = {
    'POLICY_RATE': 'V39079',  # Bank of Canada policy rate
    'OVERNIGHT_RATE': 'V39062',  # Overnight money market financing rate
    'PRIME_RATE': 'V122530',  # Prime business rate
    '3M_TBILL': 'V122531',  # 3-month Treasury bill
    '1Y_TBILL': 'V122532',  # 1-year Treasury bill  
    '2Y_BOND': 'V122533',  # 2-year Government of Canada bond yield
    '5Y_BOND': 'V122534',  # 5-year Government of Canada bond yield
    '10Y_BOND': 'V122535',  # 10-year Government of Canada bond yield
    '30Y_BOND': 'V122536',  # 30-year Government of Canada bond yield
}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Helper function to make requests to Bank of Canada Valet API
    
    Args:
        endpoint: API endpoint path (e.g., 'observations/FXUSDCAD/json')
        params: Optional query parameters
    
    Returns:
        Dict with parsed JSON response or error
    """
    try:
        url = f"{VALET_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {
            'success': True,
            'data': data
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f"HTTP error: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f"JSON decode error: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_fx_rates(base: str = 'USD', start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get foreign exchange rates for specified base currency against CAD
    
    Args:
        base: Base currency code (default 'USD'). Options: USD, EUR, GBP, JPY, CHF, AUD, MXN, CNY, INR
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Dict with FX rate data, latest value, and historical observations
    """
    # Map base currency to series name
    series_map = {
        'USD': 'FXUSDCAD',
        'EUR': 'FXEURCAD',
        'GBP': 'FXGBPCAD',
        'JPY': 'FXJPYCAD',
        'CHF': 'FXCHFCAD',
        'AUD': 'FXAUDCAD',
        'MXN': 'FXMXNCAD',
        'CNY': 'FXCNYCAD',
        'INR': 'FXINRCAD',
    }
    
    base_upper = base.upper()
    if base_upper not in series_map:
        return {
            'success': False,
            'error': f"Unsupported base currency: {base}. Options: {', '.join(series_map.keys())}"
        }
    
    series_name = series_map[base_upper]
    
    # Build endpoint with date filters
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    endpoint = f"observations/{series_name}/json"
    result = _make_request(endpoint, params)
    
    if not result['success']:
        return result
    
    data = result['data']
    
    if 'observations' not in data:
        return {
            'success': False,
            'error': 'No observations in response'
        }
    
    observations = data['observations']
    
    if not observations:
        return {
            'success': False,
            'error': 'No data points found for specified range'
        }
    
    # Get latest value and calculate changes
    latest = observations[-1]
    latest_rate = float(latest[series_name]['v']) if latest[series_name]['v'] else None
    
    changes = {}
    if len(observations) >= 2 and latest_rate:
        prev = observations[-2]
        prev_rate = float(prev[series_name]['v']) if prev[series_name]['v'] else None
        if prev_rate:
            changes['day_change'] = latest_rate - prev_rate
            changes['day_change_pct'] = ((latest_rate - prev_rate) / prev_rate * 100)
    
    return {
        'success': True,
        'base_currency': base_upper,
        'quote_currency': 'CAD',
        'series_name': series_name,
        'latest_rate': latest_rate,
        'latest_date': latest['d'],
        'changes': changes,
        'observations': [
            {
                'date': obs['d'], 
                'rate': float(obs[series_name]['v']) if obs[series_name]['v'] else None
            } 
            for obs in observations[-30:]  # Last 30 observations
        ],
        'count': len(observations),
        'timestamp': datetime.now().isoformat()
    }


def get_policy_rate() -> Dict:
    """
    Get current Bank of Canada policy interest rate
    
    Returns:
        Dict with policy rate, latest date, and recent changes
    """
    series_name = RATE_SERIES['POLICY_RATE']
    
    # Get last 90 days of data
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    endpoint = f"observations/{series_name}/json"
    
    result = _make_request(endpoint, {'start_date': start_date})
    
    if not result['success']:
        return result
    
    data = result['data']
    
    if 'observations' not in data:
        return {
            'success': False,
            'error': 'No observations in response'
        }
    
    observations = data['observations']
    
    if not observations:
        return {
            'success': False,
            'error': 'No policy rate data found'
        }
    
    latest = observations[-1]
    latest_rate = float(latest[series_name]['v']) if latest[series_name]['v'] else None
    
    # Calculate changes if we have enough data
    changes = {}
    if len(observations) >= 2 and latest_rate:
        prev = observations[-2]
        prev_rate = float(prev[series_name]['v']) if prev[series_name]['v'] else None
        if prev_rate:
            changes['last_change'] = latest_rate - prev_rate
            changes['last_change_bps'] = (latest_rate - prev_rate) * 100
    
    return {
        'success': True,
        'policy_rate': latest_rate,
        'latest_date': latest['d'],
        'series_name': series_name,
        'changes': changes,
        'recent_observations': [
            {
                'date': obs['d'],
                'rate': float(obs[series_name]['v']) if obs[series_name]['v'] else None
            }
            for obs in observations[-10:]  # Last 10 observations
        ],
        'timestamp': datetime.now().isoformat()
    }


def get_interest_rates() -> Dict:
    """
    Get key Canadian interest rates across the yield curve
    Includes policy rate, overnight rate, T-bills, and government bond yields
    
    Returns:
        Dict with rates across maturities and yield curve shape
    """
    rates = {}
    
    # Fetch all key rate series
    for rate_name, series_id in RATE_SERIES.items():
        endpoint = f"observations/{series_id}/json"
        # Get recent data only for performance
        params = {'recent': '1'}
        
        result = _make_request(endpoint, params)
        
        if result['success'] and 'observations' in result['data']:
            observations = result['data']['observations']
            if observations:
                latest = observations[-1]
                rate_value = float(latest[series_id]['v']) if latest[series_id]['v'] else None
                
                rates[rate_name] = {
                    'value': rate_value,
                    'date': latest['d'],
                    'series_id': series_id
                }
    
    # Build yield curve if we have bond data
    yield_curve = []
    bond_series = ['2Y_BOND', '5Y_BOND', '10Y_BOND', '30Y_BOND']
    for maturity in bond_series:
        if maturity in rates and rates[maturity]['value']:
            yield_curve.append({
                'maturity': maturity.replace('_BOND', ''),
                'yield': rates[maturity]['value']
            })
    
    # Calculate spreads
    spreads = {}
    if '10Y_BOND' in rates and '2Y_BOND' in rates:
        if rates['10Y_BOND']['value'] and rates['2Y_BOND']['value']:
            spreads['10Y_2Y'] = rates['10Y_BOND']['value'] - rates['2Y_BOND']['value']
    
    if '10Y_BOND' in rates and 'POLICY_RATE' in rates:
        if rates['10Y_BOND']['value'] and rates['POLICY_RATE']['value']:
            spreads['10Y_POLICY'] = rates['10Y_BOND']['value'] - rates['POLICY_RATE']['value']
    
    return {
        'success': True,
        'interest_rates': rates,
        'yield_curve': yield_curve,
        'spreads': spreads,
        'timestamp': datetime.now().isoformat()
    }


def get_series_list(group: Optional[str] = None) -> Dict:
    """
    List available data series, optionally filtered by group
    
    Args:
        group: Optional group name to filter series (e.g., 'FX_RATES_DAILY')
    
    Returns:
        Dict with available series and groups
    """
    if group:
        # Get specific group
        endpoint = f"lists/groups/{group}/json"
    else:
        # Get all groups
        endpoint = "lists/groups/json"
    
    result = _make_request(endpoint)
    
    if not result['success']:
        return result
    
    data = result['data']
    
    # Parse response based on structure
    available_series = {}
    
    if 'groups' in data:
        # Multiple groups returned
        for grp in data['groups']:
            group_name = grp.get('name', 'Unknown')
            available_series[group_name] = {
                'label': grp.get('label', ''),
                'description': grp.get('description', ''),
                'link': grp.get('link', '')
            }
    elif 'series' in data:
        # Single group with series details
        series_list = []
        for series in data['series']:
            series_list.append({
                'name': series.get('name', ''),
                'label': series.get('label', ''),
                'description': series.get('description', '')
            })
        available_series[group or 'default'] = series_list
    
    return {
        'success': True,
        'series': available_series,
        'group_filter': group,
        'timestamp': datetime.now().isoformat()
    }


def get_observations(series_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get observations for any Bank of Canada series by name
    Generic fetcher for custom series queries
    
    Args:
        series_name: Series identifier (e.g., 'FXUSDCAD', 'V39079')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Dict with time series observations and metadata
    """
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    endpoint = f"observations/{series_name}/json"
    result = _make_request(endpoint, params)
    
    if not result['success']:
        return result
    
    data = result['data']
    
    if 'observations' not in data:
        return {
            'success': False,
            'error': 'No observations in response'
        }
    
    observations = data['observations']
    
    if not observations:
        return {
            'success': False,
            'error': 'No data points found'
        }
    
    # Parse observations
    parsed_obs = []
    for obs in observations:
        if series_name in obs:
            value = obs[series_name].get('v')
            parsed_obs.append({
                'date': obs['d'],
                'value': float(value) if value else None
            })
    
    # Get latest value
    latest = None
    if parsed_obs:
        latest = parsed_obs[-1]['value']
    
    # Get series metadata if available
    series_info = {}
    if 'seriesDetail' in data:
        detail = data['seriesDetail']
        if series_name in detail:
            series_info = {
                'label': detail[series_name].get('label', ''),
                'description': detail[series_name].get('description', ''),
                'dimension': detail[series_name].get('dimension', {})
            }
    
    return {
        'success': True,
        'series_name': series_name,
        'latest_value': latest,
        'latest_date': parsed_obs[-1]['date'] if parsed_obs else None,
        'series_info': series_info,
        'observations': parsed_obs,
        'count': len(parsed_obs),
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Bank of Canada Valet API - QuantClaw Data Module")
    print("=" * 60)
    
    # Test FX rates
    print("\n1. USD/CAD Exchange Rate:")
    fx = get_fx_rates('USD')
    if fx['success']:
        print(f"   Latest: {fx['latest_rate']:.4f} CAD ({fx['latest_date']})")
        if 'day_change_pct' in fx['changes']:
            print(f"   Change: {fx['changes']['day_change_pct']:+.2f}%")
    
    # Test policy rate
    print("\n2. Bank of Canada Policy Rate:")
    policy = get_policy_rate()
    if policy['success']:
        print(f"   Current: {policy['policy_rate']:.2f}% ({policy['latest_date']})")
    
    # Test interest rates
    print("\n3. Interest Rates Summary:")
    rates = get_interest_rates()
    if rates['success'] and rates['yield_curve']:
        print("   Yield Curve:")
        for point in rates['yield_curve']:
            print(f"     {point['maturity']}: {point['yield']:.2f}%")
    
    print("\n" + "=" * 60)
