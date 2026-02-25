#!/usr/bin/env python3
"""
Turkish Statistical Institute Module — Phase 124

Comprehensive economic indicators for Turkey via TUIK (TÜİK) and CBRT (TCMB)
- CPI (Consumer Price Index - Inflation) 
- PPI (Producer Price Index)
- GDP (Gross Domestic Product)
- Trade balance, exports, imports
- Unemployment rate
- Industrial production
- FX reserves, interest rates

Data Sources:
- TUIK (TÜİK): https://data.tuik.gov.tr/
- CBRT (TCMB): https://evds2.tcmb.gov.tr/

API Protocol: REST JSON
Refresh: Monthly
Coverage: Turkey national data

Author: QUANTCLAW DATA Build Agent
Phase: 124
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# CBRT EVDS API Configuration
# Public data available without API key
CBRT_BASE_URL = "https://evds2.tcmb.gov.tr/service/evds"
CBRT_SERIES_URL = "https://evds2.tcmb.gov.tr/service/evds/series"

# Core Turkish Economic Indicators (CBRT EVDS Series)
# Format: series_code, name, description, unit
TURKISH_INDICATORS = {
    'CPI': {
        'series': 'TP.FG.J0',  # Consumer Price Index (2003=100)
        'name': 'Consumer Price Index',
        'description': 'Tüketici Fiyat Endeksi (TÜFE)',
        'unit': 'Index (2003=100)',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'CPI_ANNUAL': {
        'series': 'TP.FG.A01',  # Annual CPI Change
        'name': 'Annual CPI Change',
        'description': 'Annual inflation rate (year-over-year)',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'CPI_MONTHLY': {
        'series': 'TP.FG.A02',  # Monthly CPI Change
        'name': 'Monthly CPI Change',
        'description': 'Month-over-month inflation',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'PPI': {
        'series': 'TP.FG.PI01',  # Producer Price Index (Domestic)
        'name': 'Producer Price Index',
        'description': 'Üretici Fiyat Endeksi (ÜFE)',
        'unit': 'Index (2003=100)',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'PPI_ANNUAL': {
        'series': 'TP.FG.PI02',  # Annual PPI Change
        'name': 'Annual PPI Change',
        'description': 'Annual producer price inflation',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'UNEMPLOYMENT': {
        'series': 'TP.ISTG01.U1',  # Unemployment Rate
        'name': 'Unemployment Rate',
        'description': 'İşsizlik Oranı',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'INDUSTRIAL_PRODUCTION': {
        'series': 'TP.SANAYIURET.A01',  # Industrial Production Index
        'name': 'Industrial Production Index',
        'description': 'Sanayi Üretim Endeksi',
        'unit': 'Index (2015=100)',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'GDP_REAL': {
        'series': 'TP.GSYIH01',  # Real GDP (quarterly)
        'name': 'Real GDP',
        'description': 'Reel Gayri Safi Yurtiçi Hasıla',
        'unit': 'Millions of TRY (1998 prices)',
        'frequency': 'Quarterly',
        'source': 'TUIK'
    },
    'GDP_NOMINAL': {
        'series': 'TP.GSYIH02',  # Nominal GDP
        'name': 'Nominal GDP',
        'description': 'Nominal Gayri Safi Yurtiçi Hasıla',
        'unit': 'Millions of TRY',
        'frequency': 'Quarterly',
        'source': 'TUIK'
    },
    'EXPORTS': {
        'series': 'TP.DIS.TIC.AB01',  # Exports
        'name': 'Exports',
        'description': 'İhracat',
        'unit': 'Millions of USD',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'IMPORTS': {
        'series': 'TP.DIS.TIC.AB02',  # Imports
        'name': 'Imports',
        'description': 'İthalat',
        'unit': 'Millions of USD',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'TRADE_BALANCE': {
        'series': 'TP.DIS.TIC.AB03',  # Trade Balance
        'name': 'Trade Balance',
        'description': 'Dış Ticaret Dengesi',
        'unit': 'Millions of USD',
        'frequency': 'Monthly',
        'source': 'TUIK'
    },
    'POLICY_RATE': {
        'series': 'TP.MB.F01',  # CBRT Policy Rate (1 Week Repo)
        'name': 'Policy Rate (1 Week Repo)',
        'description': 'TCMB Politika Faizi (1 Hafta Repo)',
        'unit': 'Percent',
        'frequency': 'Daily',
        'source': 'CBRT'
    },
    'FX_RESERVES': {
        'series': 'TP.MB.R01',  # International Reserves
        'name': 'International Reserves',
        'description': 'Uluslararası Rezervler',
        'unit': 'Millions of USD',
        'frequency': 'Weekly',
        'source': 'CBRT'
    },
    'USD_TRY': {
        'series': 'TP.DK.USD.A.YTL',  # USD/TRY Exchange Rate
        'name': 'USD/TRY Exchange Rate',
        'description': 'Dolar/Türk Lirası Kuru',
        'unit': 'TRY per USD',
        'frequency': 'Daily',
        'source': 'CBRT'
    },
    'EUR_TRY': {
        'series': 'TP.DK.EUR.A.YTL',  # EUR/TRY Exchange Rate
        'name': 'EUR/TRY Exchange Rate',
        'description': 'Euro/Türk Lirası Kuru',
        'unit': 'TRY per EUR',
        'frequency': 'Daily',
        'source': 'CBRT'
    },
}

# Economic Sectors for Industrial Production breakdown
INDUSTRIAL_SECTORS = {
    'MANUFACTURING': 'Manufacturing',
    'MINING': 'Mining and Quarrying',
    'ELECTRICITY': 'Electricity, Gas, Steam',
}


def cbrt_request(series_code: str, start_date: str = None, end_date: str = None, 
                 frequency: int = 5) -> Dict:
    """
    Make request to CBRT EVDS API (no API key required for basic access)
    
    Args:
        series_code: CBRT series code (e.g., 'TP.FG.J0')
        start_date: Start date (DD-MM-YYYY)
        end_date: End date (DD-MM-YYYY)
        frequency: Data frequency (5=daily, 6=weekly, 7=monthly, 8=quarterly, 9=annual)
    
    Returns:
        Dictionary with response data
    """
    if end_date is None:
        end_date = datetime.now().strftime('%d-%m-%Y')
    
    if start_date is None:
        # Default to 2 years of data
        start_date = (datetime.now() - timedelta(days=730)).strftime('%d-%m-%Y')
    
    try:
        # CBRT EVDS API endpoint
        url = f"{CBRT_BASE_URL}/series={series_code}"
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'type': 'json',
            'frequency': frequency
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        # CBRT returns JSON but may wrap in different formats
        # Try to parse as JSON directly
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status_code
                }
            except json.JSONDecodeError:
                # If not JSON, return raw text
                return {
                    'success': True,
                    'raw_text': response.text,
                    'status_code': response.status_code
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'status_code': response.status_code
            }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def parse_cbrt_response(response_data: Dict) -> List[Dict]:
    """
    Parse CBRT API response into observations
    
    Returns:
        List of observation dictionaries with date and value
    """
    observations = []
    
    if not response_data.get('success'):
        return observations
    
    data = response_data.get('data', [])
    
    # CBRT may return data in different formats
    # Common format: list of dicts with 'Tarih' (date) and series code as value key
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Extract date
                date = item.get('Tarih') or item.get('TARIH') or item.get('date')
                
                # Extract value (may be under different keys)
                value = None
                for key, val in item.items():
                    if key not in ['Tarih', 'TARIH', 'date', 'UNIXTIME']:
                        try:
                            value = float(val) if val else None
                            break
                        except (ValueError, TypeError):
                            continue
                
                if date and value is not None:
                    observations.append({
                        'date': date,
                        'value': value
                    })
    
    return observations


def get_indicator_data(indicator_key: str, periods: int = 24) -> Dict:
    """
    Get Turkish indicator data
    
    Args:
        indicator_key: Indicator key from TURKISH_INDICATORS
        periods: Number of periods to fetch (default 24 months = 2 years)
    
    Returns:
        Dictionary with indicator data
    """
    if indicator_key not in TURKISH_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = TURKISH_INDICATORS[indicator_key]
    series_code = indicator_config['series']
    frequency_map = {
        'Daily': 5,
        'Weekly': 6,
        'Monthly': 7,
        'Quarterly': 8,
        'Annual': 9
    }
    frequency = frequency_map.get(indicator_config['frequency'], 7)
    
    # Calculate start date based on periods
    if frequency == 5:  # Daily
        days_back = periods
    elif frequency == 6:  # Weekly
        days_back = periods * 7
    elif frequency == 7:  # Monthly
        days_back = periods * 30
    elif frequency == 8:  # Quarterly
        days_back = periods * 90
    else:  # Annual
        days_back = periods * 365
    
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%m-%Y')
    
    result = cbrt_request(series_code, start_date=start_date, frequency=frequency)
    
    if not result['success']:
        return result
    
    observations = parse_cbrt_response(result)
    
    if not observations:
        return {
            'success': False,
            'error': 'No data found or parsing failed',
            'indicator': indicator_key,
            'series': series_code
        }
    
    # Sort by date descending
    observations.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate period-over-period change
    period_change = None
    period_change_pct = None
    if len(observations) >= 2:
        latest = observations[0]['value']
        previous = observations[1]['value']
        if previous and previous != 0:
            period_change = latest - previous
            period_change_pct = (period_change / previous) * 100
    
    # Calculate year-over-year change
    yoy_change = None
    yoy_change_pct = None
    lookback = 12 if frequency == 7 else (4 if frequency == 8 else 52)  # Monthly: 12, Quarterly: 4, Weekly: 52
    if len(observations) >= lookback + 1:
        latest = observations[0]['value']
        year_ago = observations[lookback]['value']
        if year_ago and year_ago != 0:
            yoy_change = latest - year_ago
            yoy_change_pct = (yoy_change / year_ago) * 100
    
    return {
        'success': True,
        'indicator': indicator_config['name'],
        'indicator_key': indicator_key,
        'description': indicator_config['description'],
        'latest_value': observations[0]['value'],
        'latest_date': observations[0]['date'],
        'period_change': period_change,
        'period_change_pct': period_change_pct,
        'yoy_change': yoy_change,
        'yoy_change_pct': yoy_change_pct,
        'unit': indicator_config['unit'],
        'frequency': indicator_config['frequency'],
        'source': indicator_config['source'],
        'data_points': observations[:min(len(observations), 24)],
        'count': len(observations),
        'timestamp': datetime.now().isoformat()
    }


def get_inflation_data() -> Dict:
    """
    Get comprehensive inflation data (CPI and PPI)
    
    Returns:
        Dictionary with inflation metrics
    """
    inflation = {
        'success': True,
        'inflation': {},
        'timestamp': datetime.now().isoformat()
    }
    
    inflation_keys = ['CPI', 'CPI_ANNUAL', 'CPI_MONTHLY', 'PPI', 'PPI_ANNUAL']
    
    for key in inflation_keys:
        data = get_indicator_data(key, periods=36)
        
        if data['success']:
            inflation['inflation'][key] = {
                'name': data['indicator'],
                'latest_value': data['latest_value'],
                'latest_date': data['latest_date'],
                'period_change_pct': data.get('period_change_pct'),
                'yoy_change_pct': data.get('yoy_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:12]
            }
        else:
            inflation['inflation'][key] = {
                'name': TURKISH_INDICATORS[key]['name'],
                'error': data.get('error', 'Data not available')
            }
        
        time.sleep(0.5)  # Rate limiting
    
    return inflation


def get_gdp_data() -> Dict:
    """
    Get GDP data (real and nominal)
    
    Returns:
        Dictionary with GDP metrics
    """
    gdp = {
        'success': True,
        'gdp': {},
        'timestamp': datetime.now().isoformat()
    }
    
    gdp_keys = ['GDP_REAL', 'GDP_NOMINAL']
    
    for key in gdp_keys:
        data = get_indicator_data(key, periods=20)  # 20 quarters = 5 years
        
        if data['success']:
            gdp['gdp'][key] = {
                'name': data['indicator'],
                'latest_value': data['latest_value'],
                'latest_date': data['latest_date'],
                'period_change_pct': data.get('period_change_pct'),
                'yoy_change_pct': data.get('yoy_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:8]  # 2 years of quarterly data
            }
        else:
            gdp['gdp'][key] = {
                'name': TURKISH_INDICATORS[key]['name'],
                'error': data.get('error', 'Data not available')
            }
        
        time.sleep(0.5)  # Rate limiting
    
    return gdp


def get_trade_data() -> Dict:
    """
    Get trade data (exports, imports, balance)
    
    Returns:
        Dictionary with trade metrics
    """
    trade = {
        'success': True,
        'trade': {},
        'timestamp': datetime.now().isoformat()
    }
    
    trade_keys = ['EXPORTS', 'IMPORTS', 'TRADE_BALANCE']
    
    for key in trade_keys:
        data = get_indicator_data(key, periods=24)
        
        if data['success']:
            trade['trade'][key] = {
                'name': data['indicator'],
                'latest_value': data['latest_value'],
                'latest_date': data['latest_date'],
                'period_change_pct': data.get('period_change_pct'),
                'yoy_change_pct': data.get('yoy_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:12]
            }
        else:
            trade['trade'][key] = {
                'name': TURKISH_INDICATORS[key]['name'],
                'error': data.get('error', 'Data not available')
            }
        
        time.sleep(0.5)  # Rate limiting
    
    return trade


def get_unemployment_data() -> Dict:
    """
    Get unemployment data
    
    Returns:
        Dictionary with unemployment metrics
    """
    data = get_indicator_data('UNEMPLOYMENT', periods=36)
    
    if data['success']:
        return {
            'success': True,
            'unemployment': {
                'rate': data['latest_value'],
                'latest_date': data['latest_date'],
                'period_change': data.get('period_change_pct'),
                'yoy_change': data.get('yoy_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:12]
            },
            'timestamp': datetime.now().isoformat()
        }
    else:
        return data


def get_monetary_policy() -> Dict:
    """
    Get monetary policy indicators (policy rate, FX reserves)
    
    Returns:
        Dictionary with monetary policy data
    """
    monetary = {
        'success': True,
        'monetary_policy': {},
        'timestamp': datetime.now().isoformat()
    }
    
    monetary_keys = ['POLICY_RATE', 'FX_RESERVES']
    
    for key in monetary_keys:
        periods = 90 if key == 'POLICY_RATE' else 52  # 90 days or 52 weeks
        data = get_indicator_data(key, periods=periods)
        
        if data['success']:
            monetary['monetary_policy'][key] = {
                'name': data['indicator'],
                'latest_value': data['latest_value'],
                'latest_date': data['latest_date'],
                'period_change': data.get('period_change'),
                'period_change_pct': data.get('period_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:20]
            }
        else:
            monetary['monetary_policy'][key] = {
                'name': TURKISH_INDICATORS[key]['name'],
                'error': data.get('error', 'Data not available')
            }
        
        time.sleep(0.5)  # Rate limiting
    
    return monetary


def get_exchange_rates() -> Dict:
    """
    Get exchange rates (USD/TRY, EUR/TRY)
    
    Returns:
        Dictionary with FX rates
    """
    fx = {
        'success': True,
        'exchange_rates': {},
        'timestamp': datetime.now().isoformat()
    }
    
    fx_keys = ['USD_TRY', 'EUR_TRY']
    
    for key in fx_keys:
        data = get_indicator_data(key, periods=90)  # 90 days
        
        if data['success']:
            fx['exchange_rates'][key] = {
                'pair': data['indicator'],
                'current_rate': data['latest_value'],
                'latest_date': data['latest_date'],
                'day_over_day_change_pct': data.get('period_change_pct'),
                'ytd_change_pct': data.get('yoy_change_pct'),
                'unit': data['unit'],
                'history': data['data_points'][:30]
            }
        else:
            fx['exchange_rates'][key] = {
                'pair': TURKISH_INDICATORS[key]['name'],
                'error': data.get('error', 'Data not available')
            }
        
        time.sleep(0.5)  # Rate limiting
    
    return fx


def get_economic_snapshot() -> Dict:
    """
    Get comprehensive Turkish economic snapshot
    
    Returns:
        Dictionary with complete economic overview
    """
    snapshot = {
        'success': True,
        'snapshot': {},
        'timestamp': datetime.now().isoformat()
    }
    
    print("Fetching inflation data...", file=sys.stderr)
    inflation = get_inflation_data()
    if inflation['success']:
        snapshot['snapshot']['inflation'] = inflation['inflation']
    
    print("Fetching GDP data...", file=sys.stderr)
    gdp = get_gdp_data()
    if gdp['success']:
        snapshot['snapshot']['gdp'] = gdp['gdp']
    
    print("Fetching trade data...", file=sys.stderr)
    trade = get_trade_data()
    if trade['success']:
        snapshot['snapshot']['trade'] = trade['trade']
    
    print("Fetching unemployment data...", file=sys.stderr)
    unemployment = get_unemployment_data()
    if unemployment['success']:
        snapshot['snapshot']['unemployment'] = unemployment['unemployment']
    
    print("Fetching monetary policy data...", file=sys.stderr)
    monetary = get_monetary_policy()
    if monetary['success']:
        snapshot['snapshot']['monetary_policy'] = monetary['monetary_policy']
    
    print("Fetching exchange rates...", file=sys.stderr)
    fx = get_exchange_rates()
    if fx['success']:
        snapshot['snapshot']['exchange_rates'] = fx['exchange_rates']
    
    return snapshot


def list_indicators() -> Dict:
    """
    List all Turkish economic indicators
    
    Returns:
        Dictionary with indicator list
    """
    indicators = []
    for key, config in TURKISH_INDICATORS.items():
        indicators.append({
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'unit': config['unit'],
            'frequency': config['frequency'],
            'source': config['source']
        })
    
    return {
        'success': True,
        'indicators': indicators,
        'count': len(indicators)
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'tuik-indicator':
            if len(sys.argv) < 3:
                print("Error: tuik-indicator requires indicator key", file=sys.stderr)
                print("Usage: python3 turkish_institute.py tuik-indicator <INDICATOR_KEY>", file=sys.stderr)
                return 1
            
            indicator_key = sys.argv[2].upper()
            
            if indicator_key not in TURKISH_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(TURKISH_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            data = get_indicator_data(indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-inflation':
            data = get_inflation_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-gdp':
            data = get_gdp_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-trade':
            data = get_trade_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-unemployment':
            data = get_unemployment_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-monetary':
            data = get_monetary_policy()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-fx':
            data = get_exchange_rates()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-snapshot':
            data = get_economic_snapshot()
            print(json.dumps(data, indent=2))
        
        elif command == 'tuik-indicators':
            data = list_indicators()
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
Turkish Statistical Institute Module (Phase 124)

Commands:
  python3 turkish_institute.py tuik-indicator <KEY>   # Get specific indicator
  python3 turkish_institute.py tuik-inflation         # Get CPI/PPI inflation data
  python3 turkish_institute.py tuik-gdp               # Get real & nominal GDP
  python3 turkish_institute.py tuik-trade             # Get exports/imports/balance
  python3 turkish_institute.py tuik-unemployment      # Get unemployment rate
  python3 turkish_institute.py tuik-monetary          # Get policy rate & FX reserves
  python3 turkish_institute.py tuik-fx                # Get USD/TRY, EUR/TRY rates
  python3 turkish_institute.py tuik-snapshot          # Complete economic snapshot
  python3 turkish_institute.py tuik-indicators        # List all indicators

Examples:
  python3 turkish_institute.py tuik-indicator CPI_ANNUAL
  python3 turkish_institute.py tuik-indicator USD_TRY
  python3 turkish_institute.py tuik-inflation
  python3 turkish_institute.py tuik-gdp
  python3 turkish_institute.py tuik-snapshot

Available Indicators:
  Inflation:
    CPI                = Consumer Price Index
    CPI_ANNUAL         = Annual CPI change (%)
    CPI_MONTHLY        = Monthly CPI change (%)
    PPI                = Producer Price Index
    PPI_ANNUAL         = Annual PPI change (%)
  
  Economic Activity:
    GDP_REAL           = Real GDP
    GDP_NOMINAL        = Nominal GDP
    UNEMPLOYMENT       = Unemployment rate (%)
    INDUSTRIAL_PRODUCTION = Industrial production index
  
  Trade:
    EXPORTS            = Exports (millions USD)
    IMPORTS            = Imports (millions USD)
    TRADE_BALANCE      = Trade balance (millions USD)
  
  Monetary & FX:
    POLICY_RATE        = CBRT policy rate (1-week repo %)
    FX_RESERVES        = International reserves (millions USD)
    USD_TRY            = USD/TRY exchange rate
    EUR_TRY            = EUR/TRY exchange rate

Data Sources:
  - TUIK (TÜİK): Turkish Statistical Institute
  - CBRT (TCMB): Central Bank of the Republic of Turkey

Refresh: Monthly (most indicators), Daily (FX rates, policy rate), Weekly (reserves)
Coverage: Turkey national data
""")


if __name__ == "__main__":
    sys.exit(main())
