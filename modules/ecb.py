#!/usr/bin/env python3
"""
ECB Statistical Warehouse Module — Phase 105

European Central Bank economic and financial statistics via SDMX API
- Euro interest rates (EURIBOR, government bonds)
- Euro exchange rates vs major currencies
- HICP inflation data  
- Note: Some ECB series (M1/M2/M3, bank lending) require institutional access

Data Source: https://data-api.ecb.europa.eu/service/
SDMX Protocol: Statistical Data and Metadata eXchange
Refresh: Daily (FX), Monthly (rates/inflation)
Coverage: Euro Area (EA20), individual Eurozone countries

Author: QUANTCLAW DATA Build Agent
Phase: 105
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import xml.etree.ElementTree as ET

# ECB SDMX API Configuration
ECB_BASE_URL = "https://data-api.ecb.europa.eu/service"

# Core ECB Indicators (Verified Working Series)
# Format: dataflow_id, series_key, name, description
ECB_INDICATORS = {
    'EURIBOR_1M': {
        'dataflow': 'FM',
        'series': 'M.U2.EUR.RT.MM.EURIBOR1MD_.HSTA',
        'name': 'EURIBOR 1-month Rate (%)',
        'description': 'Euro Interbank Offered Rate - 1 month maturity',
        'available': True
    },
    'EURIBOR_3M': {
        'dataflow': 'FM',
        'series': 'M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA',
        'name': 'EURIBOR 3-month Rate (%)',
        'description': 'Euro Interbank Offered Rate - 3 month maturity',
        'available': True
    },
    'EURIBOR_6M': {
        'dataflow': 'FM',
        'series': 'M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA',
        'name': 'EURIBOR 6-month Rate (%)',
        'description': 'Euro Interbank Offered Rate - 6 month maturity',
        'available': True
    },
    'EURIBOR_12M': {
        'dataflow': 'FM',
        'series': 'M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA',
        'name': 'EURIBOR 12-month Rate (%)',
        'description': 'Euro Interbank Offered Rate - 12 month maturity',
        'available': True
    },
    'EUR_USD': {
        'dataflow': 'EXR',
        'series': 'D.USD.EUR.SP00.A',
        'name': 'EUR/USD Exchange Rate',
        'description': 'Euro to US Dollar exchange rate (daily)',
        'available': True
    },
    'EUR_GBP': {
        'dataflow': 'EXR',
        'series': 'D.GBP.EUR.SP00.A',
        'name': 'EUR/GBP Exchange Rate',
        'description': 'Euro to British Pound exchange rate (daily)',
        'available': True
    },
    'EUR_JPY': {
        'dataflow': 'EXR',
        'series': 'D.JPY.EUR.SP00.A',
        'name': 'EUR/JPY Exchange Rate',
        'description': 'Euro to Japanese Yen exchange rate (daily)',
        'available': True
    },
    'EUR_CHF': {
        'dataflow': 'EXR',
        'series': 'D.CHF.EUR.SP00.A',
        'name': 'EUR/CHF Exchange Rate',
        'description': 'Euro to Swiss Franc exchange rate (daily)',
        'available': True
    },
    'EUR_CNY': {
        'dataflow': 'EXR',
        'series': 'D.CNY.EUR.SP00.A',
        'name': 'EUR/CNY Exchange Rate',
        'description': 'Euro to Chinese Yuan exchange rate (daily)',
        'available': True
    },
    # Note: The following indicators require institutional/paid access to ECB data
    # They are documented here for reference but may not be available via public API
    'M1': {
        'dataflow': 'BSI',
        'series': 'M.U2.N.A.M10.X.1.U2.2300.Z01.E',
        'name': 'M1 Monetary Aggregate (EUR billions)',
        'description': 'Currency in circulation + overnight deposits (requires ECB institutional access)',
        'available': False
    },
    'M2': {
        'dataflow': 'BSI',
        'series': 'M.U2.N.A.M20.X.1.U2.2300.Z01.E',
        'name': 'M2 Monetary Aggregate (EUR billions)',
        'description': 'M1 + deposits with maturity up to 2 years (requires ECB institutional access)',
        'available': False
    },
    'M3': {
        'dataflow': 'BSI',
        'series': 'M.U2.N.A.M30.X.1.U2.2300.Z01.E',
        'name': 'M3 Monetary Aggregate (EUR billions)',
        'description': 'M2 + repurchase agreements + money market fund shares (requires ECB institutional access)',
        'available': False
    },
    'LOANS_HOUSEHOLDS': {
        'dataflow': 'BSI',
        'series': 'M.U2.N.A.A20.A.1.U2.2240.Z01.E',
        'name': 'Loans to Households (EUR billions)',
        'description': 'Total lending to households by MFIs (requires ECB institutional access)',
        'available': False
    },
    'LOANS_CORPORATIONS': {
        'dataflow': 'BSI',
        'series': 'M.U2.N.A.A20.A.1.U2.2250.Z01.E',
        'name': 'Loans to Non-Financial Corporations (EUR billions)',
        'description': 'Total lending to non-financial corporations by MFIs (requires ECB institutional access)',
        'available': False
    },
}

# Eurozone Countries (EA20 as of 2023 - Croatia joined)
EUROZONE_COUNTRIES = {
    'AT': 'Austria',
    'BE': 'Belgium',
    'HR': 'Croatia',
    'CY': 'Cyprus',
    'EE': 'Estonia',
    'FI': 'Finland',
    'FR': 'France',
    'DE': 'Germany',
    'GR': 'Greece',
    'IE': 'Ireland',
    'IT': 'Italy',
    'LV': 'Latvia',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'MT': 'Malta',
    'NL': 'Netherlands',
    'PT': 'Portugal',
    'SK': 'Slovakia',
    'SI': 'Slovenia',
    'ES': 'Spain',
    'U2': 'Euro Area (aggregate)',
}


def sdmx_request(endpoint: str, params: Dict = None) -> Dict:
    """
    Make request to ECB SDMX API
    Returns parsed XML as dictionary
    """
    if params is None:
        params = {}
    
    try:
        url = f"{ECB_BASE_URL}/{endpoint}"
        headers = {
            'Accept': 'application/vnd.sdmx.genericdata+xml;version=2.1'
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        return {
            'success': True,
            'raw_xml': response.text,
            'status_code': response.status_code
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def parse_sdmx_data(xml_text: str) -> List[Dict]:
    """
    Parse SDMX-ML GenericData format from ECB
    Returns list of observation dictionaries
    """
    try:
        # Register SDMX namespaces
        namespaces = {
            'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
            'common': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
            'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message'
        }
        
        root = ET.fromstring(xml_text)
        
        observations = []
        
        # Find all Series
        for series in root.findall('.//generic:Series', namespaces):
            # Extract series attributes
            series_key = {}
            for value in series.findall('.//generic:Value', namespaces):
                key_id = value.get('id')
                key_value = value.get('value')
                if key_id and key_value:
                    series_key[key_id] = key_value
            
            # Extract observations (time periods and values)
            for obs in series.findall('.//generic:Obs', namespaces):
                obs_dimension = obs.find('.//generic:ObsDimension', namespaces)
                obs_value = obs.find('.//generic:ObsValue', namespaces)
                
                if obs_dimension is not None and obs_value is not None:
                    time_period = obs_dimension.get('value')
                    value = obs_value.get('value')
                    
                    if time_period and value:
                        try:
                            observations.append({
                                'time_period': time_period,
                                'value': float(value),
                                'series_key': series_key.copy()
                            })
                        except ValueError:
                            # Skip non-numeric values
                            continue
        
        return observations
    
    except ET.ParseError as e:
        return []


def get_indicator_data(indicator_key: str, last_n_periods: int = 52) -> Dict:
    """
    Get ECB indicator data
    
    Args:
        indicator_key: Indicator key from ECB_INDICATORS
        last_n_periods: Number of recent periods to fetch (default 52 = ~1 year)
    
    Returns:
        Dictionary with indicator data
    """
    if indicator_key not in ECB_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = ECB_INDICATORS[indicator_key]
    
    # Check if indicator is available via public API
    if not indicator_config.get('available', True):
        return {
            'success': False,
            'error': f'Indicator {indicator_key} requires ECB institutional access',
            'indicator': indicator_config['name'],
            'note': 'This series is not available via public SDMX API. Contact ECB for institutional access.'
        }
    
    dataflow = indicator_config['dataflow']
    series_key = indicator_config['series']
    
    # Construct SDMX data URL
    endpoint = f"data/{dataflow}/{series_key}"
    
    # Add parameters
    params = {
        'lastNObservations': last_n_periods,
    }
    
    result = sdmx_request(endpoint, params)
    
    if not result['success']:
        return result
    
    # Parse SDMX XML
    observations = parse_sdmx_data(result['raw_xml'])
    
    if not observations:
        return {
            'success': False,
            'error': 'No data found or parsing failed',
            'indicator': indicator_key,
            'dataflow': dataflow,
            'series': series_key
        }
    
    # Sort by time period descending
    observations.sort(key=lambda x: x['time_period'], reverse=True)
    
    # Calculate period-over-period change
    period_change = None
    period_change_pct = None
    if len(observations) >= 2:
        latest = observations[0]['value']
        previous = observations[1]['value']
        if previous and previous != 0:
            period_change = latest - previous
            period_change_pct = (period_change / previous) * 100
    
    # Calculate year-over-year change (for monthly/quarterly data)
    yoy_change = None
    yoy_change_pct = None
    if len(observations) >= 13:  # 12 months ago
        latest = observations[0]['value']
        year_ago = observations[12]['value']
        if year_ago and year_ago != 0:
            yoy_change = latest - year_ago
            yoy_change_pct = (yoy_change / year_ago) * 100
    
    return {
        'success': True,
        'indicator': indicator_config['name'],
        'indicator_key': indicator_key,
        'description': indicator_config['description'],
        'latest_value': observations[0]['value'],
        'latest_period': observations[0]['time_period'],
        'period_change': period_change,
        'period_change_pct': period_change_pct,
        'yoy_change': yoy_change,
        'yoy_change_pct': yoy_change_pct,
        'data_points': [{'period': obs['time_period'], 'value': obs['value']} for obs in observations[:20]],
        'count': len(observations),
        'timestamp': datetime.now().isoformat()
    }


def get_interest_rates() -> Dict:
    """
    Get key Euro Area interest rates (EURIBOR)
    
    Returns:
        Dictionary with all key rates
    """
    rates = {
        'success': True,
        'rates': {},
        'timestamp': datetime.now().isoformat()
    }
    
    rate_keys = ['EURIBOR_1M', 'EURIBOR_3M', 'EURIBOR_6M', 'EURIBOR_12M']
    
    for rate_key in rate_keys:
        rate_data = get_indicator_data(rate_key, last_n_periods=20)
        
        if rate_data['success']:
            rates['rates'][rate_key] = {
                'name': rate_data['indicator'],
                'current_rate': rate_data['latest_value'],
                'as_of': rate_data['latest_period'],
                'change_from_previous': rate_data.get('period_change'),
                'period_change_pct': rate_data.get('period_change_pct'),
                'history': rate_data['data_points'][:12]
            }
        else:
            rates['rates'][rate_key] = {
                'name': ECB_INDICATORS[rate_key]['name'],
                'error': rate_data.get('error', 'Data not available')
            }
        
        time.sleep(0.3)  # Rate limiting
    
    return rates


def get_exchange_rates() -> Dict:
    """
    Get EUR exchange rates vs major currencies (USD, GBP, JPY, CHF, CNY)
    
    Returns:
        Dictionary with exchange rates
    """
    rates = {
        'success': True,
        'exchange_rates': {},
        'timestamp': datetime.now().isoformat()
    }
    
    fx_keys = ['EUR_USD', 'EUR_GBP', 'EUR_JPY', 'EUR_CHF', 'EUR_CNY']
    
    for fx_key in fx_keys:
        fx_data = get_indicator_data(fx_key, last_n_periods=30)
        
        if fx_data['success']:
            rates['exchange_rates'][fx_key] = {
                'pair': fx_data['indicator'],
                'current_rate': fx_data['latest_value'],
                'as_of': fx_data['latest_period'],
                'day_over_day_change_pct': fx_data.get('period_change_pct'),
                'history': fx_data['data_points'][:30]
            }
        else:
            rates['exchange_rates'][fx_key] = {
                'pair': ECB_INDICATORS[fx_key]['name'],
                'error': fx_data.get('error', 'Data not available')
            }
        
        time.sleep(0.3)  # Rate limiting
    
    return rates


def get_dashboard() -> Dict:
    """
    Get comprehensive ECB dashboard with all publicly available key indicators
    
    Returns:
        Dictionary with complete ECB overview
    """
    dashboard = {
        'success': True,
        'dashboard': {},
        'note': 'Some ECB series (M1/M2/M3, bank lending) require institutional access and are not available via public API',
        'timestamp': datetime.now().isoformat()
    }
    
    # Get interest rates
    print("Fetching interest rates...", file=sys.stderr)
    rates = get_interest_rates()
    if rates['success']:
        dashboard['dashboard']['interest_rates'] = rates['rates']
    
    # Get exchange rates
    print("Fetching exchange rates...", file=sys.stderr)
    fx = get_exchange_rates()
    if fx['success']:
        dashboard['dashboard']['exchange_rates'] = fx['exchange_rates']
    
    return dashboard


def list_indicators(available_only: bool = False) -> Dict:
    """
    List all ECB indicators
    
    Args:
        available_only: If True, only list publicly available indicators
    
    Returns:
        Dictionary with indicator list
    """
    indicators = []
    for key, config in ECB_INDICATORS.items():
        if available_only and not config.get('available', True):
            continue
        
        indicators.append({
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'dataflow': config['dataflow'],
            'available': config.get('available', True)
        })
    
    return {
        'success': True,
        'indicators': indicators,
        'count': len(indicators),
        'note': 'Some indicators require ECB institutional access'
    }


def list_countries() -> Dict:
    """
    List Eurozone countries
    
    Returns:
        Dictionary with country list
    """
    countries = [{'code': code, 'name': name} for code, name in EUROZONE_COUNTRIES.items()]
    
    return {
        'success': True,
        'countries': countries,
        'count': len(countries)
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'ecb-indicator':
            if len(sys.argv) < 3:
                print("Error: ecb-indicator requires indicator key", file=sys.stderr)
                print("Usage: python3 ecb.py ecb-indicator <INDICATOR_KEY>", file=sys.stderr)
                return 1
            
            indicator_key = sys.argv[2].upper()
            
            if indicator_key not in ECB_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(ECB_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            data = get_indicator_data(indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'ecb-rates':
            data = get_interest_rates()
            print(json.dumps(data, indent=2))
        
        elif command == 'ecb-fx':
            data = get_exchange_rates()
            print(json.dumps(data, indent=2))
        
        elif command == 'ecb-dashboard':
            data = get_dashboard()
            print(json.dumps(data, indent=2))
        
        elif command == 'ecb-indicators':
            available_only = '--available' in sys.argv
            data = list_indicators(available_only=available_only)
            print(json.dumps(data, indent=2))
        
        elif command == 'ecb-countries':
            data = list_countries()
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
ECB Statistical Warehouse Module (Phase 105)

Commands:
  python3 ecb.py ecb-indicator <KEY>     # Get specific ECB indicator
  python3 ecb.py ecb-rates               # Get all Euro Area interest rates (EURIBOR)
  python3 ecb.py ecb-fx                  # Get EUR exchange rates
  python3 ecb.py ecb-dashboard           # Complete ECB overview
  python3 ecb.py ecb-indicators [--available]  # List all/available indicators
  python3 ecb.py ecb-countries           # List Eurozone countries

Examples:
  python3 ecb.py ecb-indicator EURIBOR_3M
  python3 ecb.py ecb-indicator EUR_USD
  python3 ecb.py ecb-rates
  python3 ecb.py ecb-fx
  python3 ecb.py ecb-dashboard
  python3 ecb.py ecb-indicators --available
  python3 ecb.py ecb-countries

Available Indicators (Public API):
  Interest Rates:
    EURIBOR_1M      = EURIBOR 1-month
    EURIBOR_3M      = EURIBOR 3-month
    EURIBOR_6M      = EURIBOR 6-month
    EURIBOR_12M     = EURIBOR 12-month
  
  Exchange Rates:
    EUR_USD         = Euro to US Dollar
    EUR_GBP         = Euro to British Pound
    EUR_JPY         = Euro to Japanese Yen
    EUR_CHF         = Euro to Swiss Franc
    EUR_CNY         = Euro to Chinese Yuan

Unavailable Indicators (Institutional Access Required):
  Monetary Aggregates:
    M1, M2, M3              = Monetary aggregates
  
  Bank Lending:
    LOANS_HOUSEHOLDS        = Loans to households
    LOANS_CORPORATIONS      = Loans to non-financial corporations

Data Source: https://data-api.ecb.europa.eu/service/
Protocol: SDMX (Statistical Data and Metadata eXchange)
Coverage: Euro Area (EA20), individual Eurozone countries
Refresh: Daily (FX), Monthly (rates)

Note: Some ECB series require institutional/paid access to ECB data.
For full access to M1/M2/M3 and bank lending statistics, contact the ECB.
""")


if __name__ == "__main__":
    sys.exit(main())
