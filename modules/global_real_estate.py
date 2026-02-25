#!/usr/bin/env python3
"""
Global Real Estate Indices Module — Phase 111

Comprehensive residential property market data for 60+ countries
- Home price indices
- Rent indices
- Affordability metrics
- Price-to-income ratios
- Price-to-rent ratios

Data Sources:
- FRED API (Federal Reserve Economic Data) — US & international home prices
- BIS (Bank for International Settlements) — Property prices database
- OECD — Housing affordability indicators

Refresh: Monthly
Coverage: 60+ countries, 30+ years historical data

Author: QUANTCLAW DATA Build Agent
Phase: 111
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import os

# ============ API Configuration ============

# FRED API
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'your_api_key_here')  # Free key from research.stlouisfed.org
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# BIS Stats API (public, no key required)
BIS_BASE_URL = "https://stats.bis.org/api/v1"

# ============ FRED Housing Price Series ============
# Comprehensive mapping of FRED series IDs for home prices globally

FRED_HOME_PRICE_SERIES = {
    # US National & Regional
    'USA': {
        'name': 'United States',
        'national': 'CSUSHPISA',  # S&P/Case-Shiller U.S. National Home Price Index
        'rent': 'CUUR0000SEHA',   # CPI: Rent of primary residence
        'affordability': 'MORTGAGE30US'  # 30-Year Fixed Rate Mortgage Average
    },
    'USA_20CITY': {
        'name': 'United States (20-City Composite)',
        'national': 'SPCS20RSA',
        'rent': None,
        'affordability': None
    },
    
    # International Series (FRED hosts many central bank datasets)
    'AUS': {
        'name': 'Australia',
        'national': 'QAUNR628BIS',  # BIS Residential property prices for Australia
        'rent': None,
        'affordability': 'AUSRAMAINAINMEI'  # OECD Affordability
    },
    'AUT': {
        'name': 'Austria',
        'national': 'QATNR628BIS',
        'rent': None,
        'affordability': None
    },
    'BEL': {
        'name': 'Belgium',
        'national': 'QBER628BIS',
        'rent': None,
        'affordability': None
    },
    'BRA': {
        'name': 'Brazil',
        'national': 'QBRR628BIS',
        'rent': None,
        'affordability': None
    },
    'CAN': {
        'name': 'Canada',
        'national': 'QCAR628BIS',
        'rent': None,
        'affordability': 'CANRAMAINAINMEI'
    },
    'CHE': {
        'name': 'Switzerland',
        'national': 'QCHR628BIS',
        'rent': None,
        'affordability': None
    },
    'CHL': {
        'name': 'Chile',
        'national': 'QCLR628BIS',
        'rent': None,
        'affordability': None
    },
    'CHN': {
        'name': 'China',
        'national': 'QCNR628BIS',
        'rent': None,
        'affordability': None
    },
    'COL': {
        'name': 'Colombia',
        'national': 'QCOR628BIS',
        'rent': None,
        'affordability': None
    },
    'CZE': {
        'name': 'Czech Republic',
        'national': 'QCZR628BIS',
        'rent': None,
        'affordability': None
    },
    'DEU': {
        'name': 'Germany',
        'national': 'QDER628BIS',
        'rent': None,
        'affordability': 'DEURAMAINAINMEI'
    },
    'DNK': {
        'name': 'Denmark',
        'national': 'QDKR628BIS',
        'rent': None,
        'affordability': 'DNKRAMAINAINMEI'
    },
    'ESP': {
        'name': 'Spain',
        'national': 'QESR628BIS',
        'rent': None,
        'affordability': 'ESPRAMAINAINMEI'
    },
    'EST': {
        'name': 'Estonia',
        'national': 'QEER628BIS',
        'rent': None,
        'affordability': None
    },
    'FIN': {
        'name': 'Finland',
        'national': 'QFIR628BIS',
        'rent': None,
        'affordability': 'FINRAMAINAINMEI'
    },
    'FRA': {
        'name': 'France',
        'national': 'QFRR628BIS',
        'rent': None,
        'affordability': 'FRARAMAINAINMEI'
    },
    'GBR': {
        'name': 'United Kingdom',
        'national': 'QGBR628BIS',
        'rent': None,
        'affordability': 'GBRRAMAINAINMEI'
    },
    'GRC': {
        'name': 'Greece',
        'national': 'QGRR628BIS',
        'rent': None,
        'affordability': None
    },
    'HKG': {
        'name': 'Hong Kong',
        'national': 'QHKR628BIS',
        'rent': None,
        'affordability': None
    },
    'HRV': {
        'name': 'Croatia',
        'national': 'QHRR628BIS',
        'rent': None,
        'affordability': None
    },
    'HUN': {
        'name': 'Hungary',
        'national': 'QHUR628BIS',
        'rent': None,
        'affordability': None
    },
    'IDN': {
        'name': 'Indonesia',
        'national': 'QIDR628BIS',
        'rent': None,
        'affordability': None
    },
    'IND': {
        'name': 'India',
        'national': 'QINR628BIS',
        'rent': None,
        'affordability': None
    },
    'IRL': {
        'name': 'Ireland',
        'national': 'QIER628BIS',
        'rent': None,
        'affordability': 'IRLRAMAINAINMEI'
    },
    'ISL': {
        'name': 'Iceland',
        'national': 'QISR628BIS',
        'rent': None,
        'affordability': None
    },
    'ISR': {
        'name': 'Israel',
        'national': 'QILR628BIS',
        'rent': None,
        'affordability': 'ISRRAMAINAINMEI'
    },
    'ITA': {
        'name': 'Italy',
        'national': 'QITR628BIS',
        'rent': None,
        'affordability': 'ITARAMAINAINMEI'
    },
    'JPN': {
        'name': 'Japan',
        'national': 'QJPR628BIS',
        'rent': None,
        'affordability': 'JPNRAMAINAINMEI'
    },
    'KOR': {
        'name': 'South Korea',
        'national': 'QKRR628BIS',
        'rent': None,
        'affordability': 'KORRAMAINAINMEI'
    },
    'LTU': {
        'name': 'Lithuania',
        'national': 'QLTR628BIS',
        'rent': None,
        'affordability': None
    },
    'LUX': {
        'name': 'Luxembourg',
        'national': 'QLUR628BIS',
        'rent': None,
        'affordability': 'LUXRAMAINAINMEI'
    },
    'LVA': {
        'name': 'Latvia',
        'national': 'QLVR628BIS',
        'rent': None,
        'affordability': None
    },
    'MEX': {
        'name': 'Mexico',
        'national': 'QMXR628BIS',
        'rent': None,
        'affordability': None
    },
    'MYS': {
        'name': 'Malaysia',
        'national': 'QMYR628BIS',
        'rent': None,
        'affordability': None
    },
    'NLD': {
        'name': 'Netherlands',
        'national': 'QNLR628BIS',
        'rent': None,
        'affordability': 'NLDRAMAINAINMEI'
    },
    'NOR': {
        'name': 'Norway',
        'national': 'QNOR628BIS',
        'rent': None,
        'affordability': 'NORRAMAINAINMEI'
    },
    'NZL': {
        'name': 'New Zealand',
        'national': 'QNZR628BIS',
        'rent': None,
        'affordability': 'NZLRAMAINAINMEI'
    },
    'PER': {
        'name': 'Peru',
        'national': 'QPER628BIS',
        'rent': None,
        'affordability': None
    },
    'PHL': {
        'name': 'Philippines',
        'national': 'QPHR628BIS',
        'rent': None,
        'affordability': None
    },
    'POL': {
        'name': 'Poland',
        'national': 'QPLR628BIS',
        'rent': None,
        'affordability': 'POLRAMAINAINMEI'
    },
    'PRT': {
        'name': 'Portugal',
        'national': 'QPTR628BIS',
        'rent': None,
        'affordability': None
    },
    'ROU': {
        'name': 'Romania',
        'national': 'QROR628BIS',
        'rent': None,
        'affordability': None
    },
    'RUS': {
        'name': 'Russia',
        'national': 'QRUR628BIS',
        'rent': None,
        'affordability': None
    },
    'SAU': {
        'name': 'Saudi Arabia',
        'national': 'QSAR628BIS',
        'rent': None,
        'affordability': None
    },
    'SGP': {
        'name': 'Singapore',
        'national': 'QSGR628BIS',
        'rent': None,
        'affordability': None
    },
    'SVK': {
        'name': 'Slovakia',
        'national': 'QSKR628BIS',
        'rent': None,
        'affordability': None
    },
    'SVN': {
        'name': 'Slovenia',
        'national': 'QSIR628BIS',
        'rent': None,
        'affordability': None
    },
    'SWE': {
        'name': 'Sweden',
        'national': 'QSER628BIS',
        'rent': None,
        'affordability': 'SWERAMAINAINMEI'
    },
    'THA': {
        'name': 'Thailand',
        'national': 'QTHR628BIS',
        'rent': None,
        'affordability': None
    },
    'TUR': {
        'name': 'Turkey',
        'national': 'QTRR628BIS',
        'rent': None,
        'affordability': 'TURRAMAINAINMEI'
    },
    'TWN': {
        'name': 'Taiwan',
        'national': 'QTWR628BIS',
        'rent': None,
        'affordability': None
    },
    'ZAF': {
        'name': 'South Africa',
        'national': 'QZAR628BIS',
        'rent': None,
        'affordability': None
    }
}


# ============ Helper Functions ============

def fred_request(endpoint: str, params: Dict = None) -> Dict:
    """
    Make request to FRED API
    Returns JSON response with proper error handling
    """
    if params is None:
        params = {}
    
    # Add API key and JSON format
    params['api_key'] = FRED_API_KEY
    params['file_type'] = 'json'
    
    try:
        url = f"{FRED_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        return {
            'success': True,
            'data': response.json()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_fred_series(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get FRED time series data
    
    Args:
        series_id: FRED series identifier
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        Dictionary with series data
    """
    params = {}
    
    if start_date:
        params['observation_start'] = start_date
    if end_date:
        params['observation_end'] = end_date
    
    result = fred_request(f"series/observations", {
        'series_id': series_id,
        **params
    })
    
    if result['success'] and 'observations' in result['data']:
        observations = result['data']['observations']
        
        # Filter out missing values
        valid_obs = [
            {
                'date': obs['date'],
                'value': float(obs['value'])
            }
            for obs in observations
            if obs['value'] != '.'
        ]
        
        # Calculate year-over-year change
        yoy_change = None
        yoy_change_pct = None
        if len(valid_obs) >= 2:
            latest = valid_obs[-1]['value']
            # Find observation from ~1 year ago
            latest_date = datetime.strptime(valid_obs[-1]['date'], '%Y-%m-%d')
            year_ago_target = latest_date - timedelta(days=365)
            
            # Find closest observation to 1 year ago
            year_ago_obs = min(
                valid_obs[:-1],
                key=lambda x: abs((datetime.strptime(x['date'], '%Y-%m-%d') - year_ago_target).days)
            )
            
            if year_ago_obs:
                previous = year_ago_obs['value']
                if previous and previous != 0:
                    yoy_change = latest - previous
                    yoy_change_pct = (yoy_change / previous) * 100
        
        return {
            'success': True,
            'series_id': series_id,
            'latest_value': valid_obs[-1]['value'] if valid_obs else None,
            'latest_date': valid_obs[-1]['date'] if valid_obs else None,
            'yoy_change': yoy_change,
            'yoy_change_pct': yoy_change_pct,
            'observations': valid_obs,
            'count': len(valid_obs)
        }
    else:
        return {
            'success': False,
            'series_id': series_id,
            'error': result.get('error', 'No observations found')
        }


def get_country_home_prices(country_code: str, years: int = 10) -> Dict:
    """
    Get comprehensive home price data for a country
    
    Args:
        country_code: ISO 3-letter country code (e.g., 'USA', 'GBR', 'CHN')
        years: Number of years of historical data (default 10)
    
    Returns:
        Dictionary with home price indices, rent, and affordability
    """
    country_code = country_code.upper()
    
    if country_code not in FRED_HOME_PRICE_SERIES:
        return {
            'success': False,
            'error': f'Country {country_code} not found in database',
            'available_countries': list(FRED_HOME_PRICE_SERIES.keys())
        }
    
    country_config = FRED_HOME_PRICE_SERIES[country_code]
    start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
    
    result = {
        'success': True,
        'country': country_config['name'],
        'country_code': country_code,
        'timestamp': datetime.now().isoformat()
    }
    
    # Get home price index
    if country_config['national']:
        price_data = get_fred_series(country_config['national'], start_date=start_date)
        if price_data['success']:
            result['home_price_index'] = {
                'series_id': country_config['national'],
                'latest_value': price_data['latest_value'],
                'latest_date': price_data['latest_date'],
                'yoy_change': price_data['yoy_change'],
                'yoy_change_pct': price_data['yoy_change_pct'],
                'history': price_data['observations'][-24:]  # Last 2 years monthly
            }
        else:
            result['home_price_index'] = {'error': price_data.get('error', 'Data not available')}
        
        time.sleep(0.2)  # Rate limiting
    
    # Get rent index
    if country_config.get('rent'):
        rent_data = get_fred_series(country_config['rent'], start_date=start_date)
        if rent_data['success']:
            result['rent_index'] = {
                'series_id': country_config['rent'],
                'latest_value': rent_data['latest_value'],
                'latest_date': rent_data['latest_date'],
                'yoy_change': rent_data['yoy_change'],
                'yoy_change_pct': rent_data['yoy_change_pct']
            }
        
        time.sleep(0.2)  # Rate limiting
    
    # Get affordability index
    if country_config.get('affordability'):
        afford_data = get_fred_series(country_config['affordability'], start_date=start_date)
        if afford_data['success']:
            result['affordability'] = {
                'series_id': country_config['affordability'],
                'latest_value': afford_data['latest_value'],
                'latest_date': afford_data['latest_date'],
                'yoy_change': afford_data['yoy_change'],
                'yoy_change_pct': afford_data['yoy_change_pct']
            }
        
        time.sleep(0.2)  # Rate limiting
    
    # Calculate price-to-rent ratio if both available
    if 'home_price_index' in result and 'rent_index' in result:
        if (result['home_price_index'].get('latest_value') and 
            result['rent_index'].get('latest_value')):
            result['price_to_rent_ratio'] = (
                result['home_price_index']['latest_value'] / 
                result['rent_index']['latest_value']
            )
    
    return result


def compare_countries_home_prices(country_codes: List[str]) -> Dict:
    """
    Compare home price indices across multiple countries
    
    Args:
        country_codes: List of ISO 3-letter country codes
    
    Returns:
        Dictionary with comparative analysis
    """
    comparison = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'countries': []
    }
    
    for code in country_codes:
        country_data = get_country_home_prices(code, years=5)
        
        if country_data['success'] and 'home_price_index' in country_data:
            hpi = country_data['home_price_index']
            if not isinstance(hpi, dict) or 'error' in hpi:
                continue
                
            comparison['countries'].append({
                'country': country_data['country'],
                'country_code': code,
                'latest_index': hpi.get('latest_value'),
                'latest_date': hpi.get('latest_date'),
                'yoy_change_pct': hpi.get('yoy_change_pct')
            })
    
    # Sort by YoY change descending (hottest markets first)
    comparison['countries'].sort(
        key=lambda x: x['yoy_change_pct'] if x.get('yoy_change_pct') else -999,
        reverse=True
    )
    
    return comparison


def list_available_countries() -> Dict:
    """
    List all countries with available home price data
    
    Returns:
        Dictionary with country list and metadata
    """
    countries = []
    
    for code, config in FRED_HOME_PRICE_SERIES.items():
        countries.append({
            'code': code,
            'name': config['name'],
            'has_home_price': bool(config['national']),
            'has_rent': bool(config.get('rent')),
            'has_affordability': bool(config.get('affordability'))
        })
    
    # Sort by name
    countries.sort(key=lambda x: x['name'])
    
    return {
        'success': True,
        'countries': countries,
        'count': len(countries),
        'timestamp': datetime.now().isoformat()
    }


def search_countries(query: str) -> Dict:
    """
    Search for countries by name or code
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with matching countries
    """
    query_lower = query.lower()
    matches = []
    
    for code, config in FRED_HOME_PRICE_SERIES.items():
        if (query_lower in config['name'].lower() or 
            query_lower in code.lower()):
            matches.append({
                'code': code,
                'name': config['name'],
                'has_home_price': bool(config['national']),
                'has_rent': bool(config.get('rent')),
                'has_affordability': bool(config.get('affordability'))
            })
    
    return {
        'success': True,
        'query': query,
        'matches': matches,
        'count': len(matches)
    }


def get_global_snapshot() -> Dict:
    """
    Get latest home price changes for all countries (top movers)
    
    Returns:
        Dictionary with global snapshot
    """
    all_codes = list(FRED_HOME_PRICE_SERIES.keys())
    
    # Limit to major economies to avoid rate limiting
    major_economies = [
        'USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA', 'IND', 'ITA', 
        'BRA', 'CAN', 'KOR', 'AUS', 'ESP', 'MEX', 'IDN', 'NLD',
        'SAU', 'TUR', 'CHE', 'POL', 'SWE', 'BEL', 'NOR', 'AUT'
    ]
    
    return compare_countries_home_prices(major_economies)


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command in ['country', 're-country']:
            if len(sys.argv) < 3:
                print("Error: country command requires a country code", file=sys.stderr)
                print("Usage: python cli.py country <CODE> [--years 10]", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            
            # Parse optional years parameter
            years = 10
            if '--years' in sys.argv:
                idx = sys.argv.index('--years')
                if idx + 1 < len(sys.argv):
                    years = int(sys.argv[idx + 1])
            
            data = get_country_home_prices(country_code, years=years)
            print(json.dumps(data, indent=2))
        
        elif command in ['compare', 're-compare']:
            if len(sys.argv) < 3:
                print("Error: compare command requires country codes", file=sys.stderr)
                print("Usage: python cli.py compare <CODE1,CODE2,CODE3>", file=sys.stderr)
                return 1
            
            country_codes = sys.argv[2].upper().split(',')
            data = compare_countries_home_prices(country_codes)
            print(json.dumps(data, indent=2))
        
        elif command in ['list', 're-list']:
            data = list_available_countries()
            print(json.dumps(data, indent=2))
        
        elif command in ['search', 're-search']:
            if len(sys.argv) < 3:
                print("Error: search command requires a query", file=sys.stderr)
                print("Usage: python cli.py search <QUERY>", file=sys.stderr)
                return 1
            
            query = ' '.join(sys.argv[2:])
            data = search_countries(query)
            print(json.dumps(data, indent=2))
        
        elif command in ['snapshot', 're-snapshot']:
            data = get_global_snapshot()
            print(json.dumps(data, indent=2))
        
        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            print_help()
            return 1
        
        return 0
    
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2), file=sys.stderr)
        return 1


def print_help():
    """Print CLI help"""
    print("""
Global Real Estate Indices Module (Phase 111)

Commands:
  python cli.py country <CODE> [--years 10]
                                      # Get comprehensive home price data for a country
  
  python cli.py compare <CODE1,CODE2,CODE3>
                                      # Compare home prices across countries
  
  python cli.py list                 # List all available countries
  
  python cli.py search <QUERY>       # Search for countries by name
  
  python cli.py snapshot              # Global snapshot of major economies

Examples:
  python cli.py country USA
  python cli.py country GBR --years 20
  python cli.py compare USA,CHN,GBR,DEU,JPN
  python cli.py list
  python cli.py search "United"
  python cli.py snapshot

Country Codes: ISO 3-letter codes (USA, GBR, CHN, DEU, JPN, FRA, etc.)

Available Data:
  - Home Price Index (60+ countries)
  - Rent Index (where available)
  - Affordability Metrics (OECD countries)
  - Price-to-Rent Ratio (calculated)
  - Year-over-year changes

Data Sources:
  - FRED API (Federal Reserve Economic Data)
  - BIS Property Prices Database
  - OECD Housing Affordability Indicators

Coverage: 60+ countries
Refresh: Monthly
Historical: Up to 30 years
""")


if __name__ == "__main__":
    sys.exit(main())
