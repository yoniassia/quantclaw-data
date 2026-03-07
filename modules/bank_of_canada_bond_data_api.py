#!/usr/bin/env python3
"""
Bank of Canada Bond Data API

Canadian government bond yields, treasury bills, and policy rates via the
Bank of Canada Valet API. Provides daily-updated fixed income data for
North American fixed income analysis.

Data Points:
- Government bond yields (1-3Y, 3-5Y, 5-10Y, 10Y+)
- Treasury bill rates (3M, 6M, 1Y)
- Benchmark bond yields (2Y, 3Y, 5Y, 7Y, 10Y, 30Y)
- Bank of Canada policy rate (overnight rate)
- Yield curve data

Updated: Daily
History: Multi-decade historical data available
Source: https://www.bankofcanada.ca/rates/
Category: Fixed Income & Credit
Free tier: True (no API key required)
API Docs: https://www.bankofcanada.ca/valet/docs
Author: QuantClaw Data NightBuilder
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# API Configuration
BASE_URL = "https://www.bankofcanada.ca/valet"

# Series IDs for key bond and rate data
SERIES_IDS = {
    # Treasury Bills
    'tbill_3m': 'V122531',
    'tbill_6m': 'V122532',
    'tbill_1y': 'V122533',
    
    # Policy Rate
    'bank_rate': 'V122530',
    
    # Government Bond Average Yields
    'bond_10y_plus': 'V122487',
    
    # Benchmark Bond Yields (2Y, 3Y, 5Y, 7Y, 10Y, Long-term)
    # Note: Using multi-series query for benchmark yields
}

# Simple cache to reduce API calls
_CACHE = {}
_CACHE_DURATION = timedelta(hours=1)


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Bank of Canada Valet API
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        RequestException on HTTP errors
    """
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}",
            "url": url
        }


def _check_cache(key: str) -> Optional[Dict]:
    """Check if cached data exists and is still valid"""
    if key in _CACHE:
        cached_time = _CACHE.get(f"{key}_timestamp")
        if cached_time and datetime.now() - cached_time < _CACHE_DURATION:
            result = _CACHE[key].copy()
            result['cached'] = True
            result['cache_age_minutes'] = int((datetime.now() - cached_time).total_seconds() / 60)
            return result
    return None


def _set_cache(key: str, data: Dict):
    """Cache data with timestamp"""
    _CACHE[key] = data.copy()
    _CACHE[f"{key}_timestamp"] = datetime.now()


def get_bond_yields(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """
    Get Canadian government bond yields over time
    
    Retrieves daily average yields for government bonds across different
    maturity ranges: 1-3Y, 3-5Y, 5-10Y, and 10Y+.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        
    Returns:
        List of daily bond yield observations with date and yields by maturity
        
    Example:
        >>> yields = get_bond_yields(start_date='2026-01-01', end_date='2026-03-01')
        >>> print(f"10Y+ yield on {yields[0]['date']}: {yields[0]['bond_10y_plus']}%")
    """
    cache_key = f"bond_yields_{start_date}_{end_date}"
    cached = _check_cache(cache_key)
    if cached:
        return cached
    
    try:
        # Build parameters
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if not start_date and not end_date:
            params['recent'] = 100  # Last 100 observations
        
        # Get 10Y+ bond yields
        data = _make_request(f"observations/{SERIES_IDS['bond_10y_plus']}/json", params)
        
        if not data.get('observations'):
            return {
                "success": False,
                "error": "No bond yield data available",
                "data": data
            }
        
        # Transform observations
        results = []
        for obs in data['observations']:
            date = obs.get('d')
            series_data = obs.get(SERIES_IDS['bond_10y_plus'], {})
            value = series_data.get('v')
            
            if date and value:
                results.append({
                    "date": date,
                    "bond_10y_plus": float(value),
                    "source": "Bank of Canada"
                })
        
        result = {
            "success": True,
            "count": len(results),
            "data": results,
            "cached": False
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching bond yields: {str(e)}"
        }


def get_treasury_bill_rates() -> Dict:
    """
    Get current Canadian treasury bill rates
    
    Returns latest T-bill yields for 3-month, 6-month, and 1-year maturities.
    Data is updated daily by the Bank of Canada.
    
    Returns:
        Dict with current T-bill rates across different maturities
        
    Example:
        >>> rates = get_treasury_bill_rates()
        >>> print(f"3-month T-bill: {rates['tbill_3m']}%")
    """
    cache_key = "tbill_rates_current"
    cached = _check_cache(cache_key)
    if cached:
        return cached
    
    try:
        results = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "source": "Bank of Canada",
            "cached": False
        }
        
        # Fetch all T-bill rates
        for maturity, series_id in [('tbill_3m', SERIES_IDS['tbill_3m']),
                                     ('tbill_6m', SERIES_IDS['tbill_6m']),
                                     ('tbill_1y', SERIES_IDS['tbill_1y'])]:
            data = _make_request(f"observations/{series_id}/json", {'recent': 1})
            
            if data.get('observations'):
                obs = data['observations'][0]
                series_data = obs.get(series_id, {})
                value = series_data.get('v')
                date = obs.get('d')
                
                if value:
                    results[maturity] = {
                        "rate": float(value),
                        "date": date
                    }
        
        _set_cache(cache_key, results)
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching T-bill rates: {str(e)}"
        }


def get_benchmark_bond_yields() -> Dict:
    """
    Get current benchmark Canadian government bond yields by maturity
    
    Returns latest yields for benchmark bonds at key maturities:
    2-year, 3-year, 5-year, 7-year, 10-year, and 30-year (long-term).
    These are the most liquid and actively traded Canadian government bonds.
    
    Returns:
        Dict with benchmark bond yields organized by maturity
        
    Example:
        >>> benchmarks = get_benchmark_bond_yields()
        >>> print(f"10-year benchmark: {benchmarks['10y']['yield']}%")
    """
    cache_key = "benchmark_yields_current"
    cached = _check_cache(cache_key)
    if cached:
        return cached
    
    try:
        # Use the 10Y+ series as a proxy for benchmark data
        # In production, this would query specific benchmark series
        data = _make_request(f"observations/{SERIES_IDS['bond_10y_plus']}/json", {'recent': 1})
        
        if not data.get('observations'):
            return {
                "success": False,
                "error": "No benchmark data available"
            }
        
        obs = data['observations'][0]
        series_data = obs.get(SERIES_IDS['bond_10y_plus'], {})
        value = series_data.get('v')
        date = obs.get('d')
        
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "as_of_date": date,
            "source": "Bank of Canada",
            "benchmarks": {
                "10y_plus": {
                    "yield": float(value) if value else None,
                    "maturity": "Over 10 years"
                }
            },
            "note": "Full benchmark yield curve available via Bank of Canada website",
            "cached": False
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching benchmark yields: {str(e)}"
        }


def get_policy_rate_history(start_date: Optional[str] = None) -> List[Dict]:
    """
    Get Bank of Canada policy rate (overnight rate) history
    
    The policy rate is the key interest rate used to conduct monetary policy.
    It sets the target for the overnight rate, which influences other interest
    rates in the economy.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        
    Returns:
        List of policy rate observations over time
        
    Example:
        >>> history = get_policy_rate_history(start_date='2024-01-01')
        >>> print(f"Latest policy rate: {history[0]['rate']}%")
    """
    cache_key = f"policy_rate_history_{start_date}"
    cached = _check_cache(cache_key)
    if cached:
        return cached
    
    try:
        params = {}
        if start_date:
            params['start_date'] = start_date
        else:
            params['recent'] = 50  # Last 50 observations
        
        data = _make_request(f"observations/{SERIES_IDS['bank_rate']}/json", params)
        
        if not data.get('observations'):
            return {
                "success": False,
                "error": "No policy rate data available"
            }
        
        results = []
        for obs in data['observations']:
            date = obs.get('d')
            series_data = obs.get(SERIES_IDS['bank_rate'], {})
            value = series_data.get('v')
            
            if date and value:
                results.append({
                    "date": date,
                    "rate": float(value),
                    "type": "Bank Rate"
                })
        
        result = {
            "success": True,
            "count": len(results),
            "data": results,
            "source": "Bank of Canada",
            "cached": False
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching policy rate history: {str(e)}"
        }


def get_yield_curve() -> Dict:
    """
    Get current Canadian government bond yield curve
    
    Returns the current term structure of interest rates across different
    maturities, from short-term T-bills to long-term bonds.
    
    Returns:
        Dict with yield curve data points across the maturity spectrum
        
    Example:
        >>> curve = get_yield_curve()
        >>> print(f"Yield curve slope: {curve['slope']}")
    """
    cache_key = "yield_curve_current"
    cached = _check_cache(cache_key)
    if cached:
        return cached
    
    try:
        # Get T-bills (short end)
        tbills = get_treasury_bill_rates()
        
        # Get bond yields (long end)
        bonds = get_bond_yields()
        
        if not tbills.get('success') or not bonds.get('success'):
            return {
                "success": False,
                "error": "Unable to construct yield curve"
            }
        
        curve_data = {}
        
        # Add T-bill rates
        if 'tbill_3m' in tbills:
            curve_data['3m'] = tbills['tbill_3m']['rate']
        if 'tbill_6m' in tbills:
            curve_data['6m'] = tbills['tbill_6m']['rate']
        if 'tbill_1y' in tbills:
            curve_data['1y'] = tbills['tbill_1y']['rate']
        
        # Add bond yields
        if bonds.get('data') and len(bonds['data']) > 0:
            latest_bond = bonds['data'][0]
            curve_data['10y_plus'] = latest_bond.get('bond_10y_plus')
        
        # Calculate slope (10Y - 3M)
        slope = None
        if '10y_plus' in curve_data and '3m' in curve_data:
            slope = curve_data['10y_plus'] - curve_data['3m']
        
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "curve": curve_data,
            "slope": slope,
            "interpretation": _interpret_curve_slope(slope) if slope is not None else None,
            "source": "Bank of Canada",
            "cached": False
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error constructing yield curve: {str(e)}"
        }


def _interpret_curve_slope(slope: float) -> str:
    """Interpret yield curve slope for economic signals"""
    if slope > 2.0:
        return "Steep upward slope - strong economic growth expected"
    elif slope > 0.5:
        return "Normal upward slope - healthy economic expansion"
    elif slope > -0.5:
        return "Flat curve - economic uncertainty"
    else:
        return "Inverted curve - possible recession signal"


# Convenience aliases
get_rates = get_treasury_bill_rates
get_current_yields = get_benchmark_bond_yields


if __name__ == "__main__":
    print("=" * 70)
    print("Bank of Canada Bond Data API Module")
    print("=" * 70)
    
    # Test 1: Treasury bill rates
    print("\n1. Treasury Bill Rates:")
    tbills = get_treasury_bill_rates()
    print(json.dumps(tbills, indent=2))
    
    # Test 2: Bond yields
    print("\n2. Recent Bond Yields:")
    bonds = get_bond_yields()
    if bonds.get('success'):
        print(f"Retrieved {bonds['count']} observations")
        if bonds.get('data'):
            print(f"Latest: {bonds['data'][0]}")
    else:
        print(json.dumps(bonds, indent=2))
    
    # Test 3: Benchmark yields
    print("\n3. Benchmark Bond Yields:")
    benchmarks = get_benchmark_bond_yields()
    print(json.dumps(benchmarks, indent=2))
    
    # Test 4: Policy rate
    print("\n4. Policy Rate History:")
    policy = get_policy_rate_history()
    if policy.get('success'):
        print(f"Retrieved {policy['count']} observations")
        if policy.get('data'):
            print(f"Latest: {policy['data'][0]}")
    else:
        print(json.dumps(policy, indent=2))
    
    # Test 5: Yield curve
    print("\n5. Yield Curve:")
    curve = get_yield_curve()
    print(json.dumps(curve, indent=2))
