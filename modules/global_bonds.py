#!/usr/bin/env python3
"""
Global Government Bond Yields Module — Phase 107

10-year government bond yields for 40+ countries
Real yields, breakeven inflation rates, yield curves
Data Source: FRED (Federal Reserve Economic Data)
Update Frequency: Daily

Covers major economies:
- G7 (US, Germany, Japan, UK, France, Italy, Canada)
- BRICS+ (China, India, Brazil, Russia, South Africa)
- Asia-Pacific (Australia, New Zealand, Singapore, South Korea, Taiwan, Hong Kong)
- Europe (Spain, Portugal, Greece, Netherlands, Belgium, Austria, Switzerland, Norway, Sweden, Denmark, Poland)
- Latin America (Mexico, Chile, Colombia, Argentina)
- Middle East (Israel, Turkey, Saudi Arabia)

Author: QUANTCLAW DATA Build Agent
Phase: 107
"""

import requests
import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# FRED API Configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')  # Get from environment. Register at https://fred.stlouisfed.org/

# Global 10Y Bond Yield Series IDs (FRED)
BOND_YIELDS_10Y = {
    # G7
    'US': {'id': 'DGS10', 'name': 'United States 10Y Treasury'},
    'DE': {'id': 'IRLTLT01DEM156N', 'name': 'Germany 10Y Bund'},
    'JP': {'id': 'IRLTLT01JPM156N', 'name': 'Japan 10Y JGB'},
    'GB': {'id': 'IRLTLT01GBM156N', 'name': 'United Kingdom 10Y Gilt'},
    'FR': {'id': 'IRLTLT01FRM156N', 'name': 'France 10Y OAT'},
    'IT': {'id': 'IRLTLT01ITM156N', 'name': 'Italy 10Y BTP'},
    'CA': {'id': 'IRLTLT01CAM156N', 'name': 'Canada 10Y Bond'},
    
    # Europe
    'ES': {'id': 'IRLTLT01ESM156N', 'name': 'Spain 10Y Bond'},
    'PT': {'id': 'IRLTLT01PTM156N', 'name': 'Portugal 10Y Bond'},
    'GR': {'id': 'IRLTLT01GRM156N', 'name': 'Greece 10Y Bond'},
    'NL': {'id': 'IRLTLT01NLM156N', 'name': 'Netherlands 10Y Bond'},
    'BE': {'id': 'IRLTLT01BEM156N', 'name': 'Belgium 10Y Bond'},
    'AT': {'id': 'IRLTLT01ATM156N', 'name': 'Austria 10Y Bond'},
    'CH': {'id': 'IRLTLT01CHM156N', 'name': 'Switzerland 10Y Bond'},
    'NO': {'id': 'IRLTLT01NOM156N', 'name': 'Norway 10Y Bond'},
    'SE': {'id': 'IRLTLT01SEM156N', 'name': 'Sweden 10Y Bond'},
    'DK': {'id': 'IRLTLT01DKM156N', 'name': 'Denmark 10Y Bond'},
    'PL': {'id': 'IRLTLT01PLM156N', 'name': 'Poland 10Y Bond'},
    
    # Asia-Pacific
    'AU': {'id': 'IRLTLT01AUM156N', 'name': 'Australia 10Y Bond'},
    'NZ': {'id': 'IRLTLT01NZM156N', 'name': 'New Zealand 10Y Bond'},
    'KR': {'id': 'IRLTLT01KRM156N', 'name': 'South Korea 10Y Bond'},
    'SG': {'id': 'IRLTLT01SGM156N', 'name': 'Singapore 10Y Bond'},
    'HK': {'id': 'IRLTLT01HKM156N', 'name': 'Hong Kong 10Y Bond'},
    'CN': {'id': 'IRLTLT01CNM156N', 'name': 'China 10Y Bond'},
    'IN': {'id': 'IRLTLT01INM156N', 'name': 'India 10Y Bond'},
    
    # Latin America
    'MX': {'id': 'IRLTLT01MXM156N', 'name': 'Mexico 10Y Bond'},
    'BR': {'id': 'IRLTLT01BRM156N', 'name': 'Brazil 10Y Bond'},
    'CL': {'id': 'IRLTLT01CLM156N', 'name': 'Chile 10Y Bond'},
    'CO': {'id': 'IRLTLT01COM156N', 'name': 'Colombia 10Y Bond'},
    
    # Middle East / Other
    'IL': {'id': 'IRLTLT01ILM156N', 'name': 'Israel 10Y Bond'},
    'TR': {'id': 'IRLTLT01TRM156N', 'name': 'Turkey 10Y Bond'},
    'ZA': {'id': 'IRLTLT01ZAM156N', 'name': 'South Africa 10Y Bond'},
    'RU': {'id': 'IRLTLT01RUM156N', 'name': 'Russia 10Y Bond'},
}

# US Treasury Yield Curve
US_TREASURY_CURVE = {
    '1M': 'DGS1MO',
    '3M': 'DGS3MO',
    '6M': 'DGS6MO',
    '1Y': 'DGS1',
    '2Y': 'DGS2',
    '3Y': 'DGS3',
    '5Y': 'DGS5',
    '7Y': 'DGS7',
    '10Y': 'DGS10',
    '20Y': 'DGS20',
    '30Y': 'DGS30'
}

# US Real Yields (TIPS)
US_REAL_YIELDS = {
    '5Y': 'DFII5',
    '7Y': 'DFII7',
    '10Y': 'DFII10',
    '20Y': 'DFII20',
    '30Y': 'DFII30'
}

# Breakeven Inflation Rates
US_BREAKEVEN_INFLATION = {
    '5Y': 'T5YIE',
    '10Y': 'T10YIE',
    '30Y': 'T30YIE'
}


def _call_fred_api(endpoint: str, params: Dict) -> Optional[Dict]:
    """
    Call FRED API with error handling
    
    Args:
        endpoint: API endpoint (e.g., 'series/observations')
        params: Query parameters
        
    Returns:
        API response as dict, or None on error
    """
    if not FRED_API_KEY:
        print("Error: FRED_API_KEY not set. Register at https://fred.stlouisfed.org/ and set FRED_API_KEY environment variable.", file=sys.stderr)
        return None
    
    url = f"{FRED_API_BASE}/{endpoint}"
    params['api_key'] = FRED_API_KEY
    params['file_type'] = 'json'
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling FRED API: {e}", file=sys.stderr)
        return None


def get_bond_yield(country_code: str, days: int = 30) -> Optional[Dict]:
    """
    Get 10-year government bond yield for a country
    
    Args:
        country_code: 2-letter country code (e.g., 'US', 'DE', 'JP')
        days: Number of days of historical data (default 30)
        
    Returns:
        Dict with yield data and metadata
    """
    if country_code.upper() not in BOND_YIELDS_10Y:
        print(f"Error: Country code '{country_code}' not found", file=sys.stderr)
        print(f"Available countries: {', '.join(sorted(BOND_YIELDS_10Y.keys()))}", file=sys.stderr)
        return None
    
    country = BOND_YIELDS_10Y[country_code.upper()]
    series_id = country['id']
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        'series_id': series_id,
        'observation_start': start_date.strftime('%Y-%m-%d'),
        'observation_end': end_date.strftime('%Y-%m-%d'),
        'sort_order': 'desc'
    }
    
    data = _call_fred_api('series/observations', params)
    if not data or 'observations' not in data:
        return None
    
    observations = data['observations']
    if not observations:
        return None
    
    # Get latest non-null value
    latest = None
    for obs in observations:
        if obs['value'] != '.':
            latest = {
                'date': obs['date'],
                'yield': float(obs['value'])
            }
            break
    
    if not latest:
        return None
    
    # Calculate change
    change_1d = None
    change_1w = None
    change_1m = None
    
    if len(observations) > 1:
        for obs in observations[1:]:
            if obs['value'] != '.':
                prev_value = float(obs['value'])
                change_1d = latest['yield'] - prev_value
                break
    
    week_ago = (datetime.strptime(latest['date'], '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago = (datetime.strptime(latest['date'], '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for obs in observations:
        if obs['value'] != '.' and obs['date'] <= week_ago and change_1w is None:
            change_1w = latest['yield'] - float(obs['value'])
        if obs['value'] != '.' and obs['date'] <= month_ago and change_1m is None:
            change_1m = latest['yield'] - float(obs['value'])
    
    return {
        'country': country_code.upper(),
        'country_name': country['name'],
        'series_id': series_id,
        'latest_date': latest['date'],
        'yield': latest['yield'],
        'change_1d': change_1d,
        'change_1w': change_1w,
        'change_1m': change_1m,
        'historical': [
            {'date': obs['date'], 'yield': float(obs['value'])}
            for obs in reversed(observations)
            if obs['value'] != '.'
        ]
    }


def compare_yields(country_codes: List[str]) -> Optional[List[Dict]]:
    """
    Compare 10Y bond yields across multiple countries
    
    Args:
        country_codes: List of 2-letter country codes
        
    Returns:
        List of yield data for each country
    """
    results = []
    for code in country_codes:
        data = get_bond_yield(code, days=30)
        if data:
            results.append(data)
    
    if not results:
        return None
    
    # Sort by yield descending
    results.sort(key=lambda x: x['yield'], reverse=True)
    return results


def get_yield_spreads(base_country: str = 'US') -> Optional[List[Dict]]:
    """
    Calculate yield spreads relative to a base country (default US)
    
    Args:
        base_country: Base country code for spread calculation
        
    Returns:
        List of countries with spreads vs base
    """
    base_data = get_bond_yield(base_country, days=30)
    if not base_data:
        return None
    
    base_yield = base_data['yield']
    spreads = []
    
    for code in BOND_YIELDS_10Y.keys():
        if code == base_country.upper():
            continue
        
        data = get_bond_yield(code, days=30)
        if data:
            spread = data['yield'] - base_yield
            spreads.append({
                'country': code,
                'country_name': data['country_name'],
                'yield': data['yield'],
                'spread_vs_base': spread,
                'spread_bps': int(spread * 100),
                'base_country': base_country.upper(),
                'base_yield': base_yield
            })
    
    # Sort by spread descending
    spreads.sort(key=lambda x: x['spread_vs_base'], reverse=True)
    return spreads


def get_us_yield_curve() -> Optional[Dict]:
    """
    Get full US Treasury yield curve (1M to 30Y)
    
    Returns:
        Dict with curve data
    """
    curve = {}
    latest_date = None
    
    for tenor, series_id in US_TREASURY_CURVE.items():
        params = {
            'series_id': series_id,
            'sort_order': 'desc',
            'limit': 1
        }
        
        data = _call_fred_api('series/observations', params)
        if data and 'observations' in data:
            obs = data['observations']
            if obs and obs[0]['value'] != '.':
                curve[tenor] = float(obs[0]['value'])
                if latest_date is None:
                    latest_date = obs[0]['date']
    
    if not curve:
        return None
    
    # Calculate curve slopes
    slope_2s10s = curve.get('10Y', 0) - curve.get('2Y', 0)
    slope_3m10y = curve.get('10Y', 0) - curve.get('3M', 0)
    
    return {
        'date': latest_date,
        'curve': curve,
        'slope_2s10s': slope_2s10s,
        'slope_3m10y': slope_3m10y,
        'inverted_2s10s': slope_2s10s < 0,
        'inverted_3m10y': slope_3m10y < 0
    }


def get_us_real_yields() -> Optional[Dict]:
    """
    Get US TIPS real yields
    
    Returns:
        Dict with real yield data
    """
    real_yields = {}
    latest_date = None
    
    for tenor, series_id in US_REAL_YIELDS.items():
        params = {
            'series_id': series_id,
            'sort_order': 'desc',
            'limit': 1
        }
        
        data = _call_fred_api('series/observations', params)
        if data and 'observations' in data:
            obs = data['observations']
            if obs and obs[0]['value'] != '.':
                real_yields[tenor] = float(obs[0]['value'])
                if latest_date is None:
                    latest_date = obs[0]['date']
    
    if not real_yields:
        return None
    
    return {
        'date': latest_date,
        'real_yields': real_yields
    }


def get_breakeven_inflation() -> Optional[Dict]:
    """
    Get US breakeven inflation rates (market-implied inflation expectations)
    
    Returns:
        Dict with breakeven inflation data
    """
    breakevens = {}
    latest_date = None
    
    for tenor, series_id in US_BREAKEVEN_INFLATION.items():
        params = {
            'series_id': series_id,
            'sort_order': 'desc',
            'limit': 1
        }
        
        data = _call_fred_api('series/observations', params)
        if data and 'observations' in data:
            obs = data['observations']
            if obs and obs[0]['value'] != '.':
                breakevens[tenor] = float(obs[0]['value'])
                if latest_date is None:
                    latest_date = obs[0]['date']
    
    if not breakevens:
        return None
    
    return {
        'date': latest_date,
        'breakeven_inflation': breakevens
    }


def get_comprehensive_bond_data(country_code: str = 'US') -> Optional[Dict]:
    """
    Get comprehensive bond data including yields, real yields, and breakeven inflation
    
    Args:
        country_code: Country code (default 'US', extended data only for US)
        
    Returns:
        Dict with comprehensive bond data
    """
    # Get 10Y yield
    yield_data = get_bond_yield(country_code, days=365)
    if not yield_data:
        return None
    
    result = {
        'country': country_code.upper(),
        'yield_10y': yield_data,
        'timestamp': datetime.now().isoformat()
    }
    
    # For US, add extended data
    if country_code.upper() == 'US':
        curve = get_us_yield_curve()
        real_yields = get_us_real_yields()
        breakevens = get_breakeven_inflation()
        
        if curve:
            result['yield_curve'] = curve
        if real_yields:
            result['real_yields'] = real_yields
        if breakevens:
            result['breakeven_inflation'] = breakevens
    
    return result


def list_countries() -> List[Dict]:
    """
    List all available countries with bond yield data
    
    Returns:
        List of country info dicts
    """
    countries = []
    for code, info in sorted(BOND_YIELDS_10Y.items()):
        countries.append({
            'code': code,
            'name': info['name'],
            'series_id': info['id']
        })
    return countries


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python global_bonds.py <command> [args]")
        print("\nCommands:")
        print("  list-countries              - List all available countries")
        print("  yield <COUNTRY>            - Get 10Y yield for country (e.g., US, DE, JP)")
        print("  compare <C1> <C2> ...      - Compare yields across countries")
        print("  spreads [BASE]             - Calculate spreads vs base country (default US)")
        print("  us-curve                   - Get full US Treasury yield curve")
        print("  us-real                    - Get US TIPS real yields")
        print("  us-breakeven               - Get US breakeven inflation rates")
        print("  comprehensive [COUNTRY]    - Get all data for country (default US)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list-countries':
        countries = list_countries()
        print(json.dumps(countries, indent=2))
    
    elif command == 'yield':
        if len(sys.argv) < 3:
            print("Error: Country code required", file=sys.stderr)
            sys.exit(1)
        data = get_bond_yield(sys.argv[2])
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'compare':
        if len(sys.argv) < 3:
            print("Error: At least one country code required", file=sys.stderr)
            sys.exit(1)
        codes = sys.argv[2:]
        data = compare_yields(codes)
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'spreads':
        base = sys.argv[2] if len(sys.argv) > 2 else 'US'
        data = get_yield_spreads(base)
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'us-curve':
        data = get_us_yield_curve()
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'us-real':
        data = get_us_real_yields()
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'us-breakeven':
        data = get_breakeven_inflation()
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    elif command == 'comprehensive':
        country = sys.argv[2] if len(sys.argv) > 2 else 'US'
        data = get_comprehensive_bond_data(country)
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
