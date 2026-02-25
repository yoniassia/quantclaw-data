#!/usr/bin/env python3
"""
Poland GUS (Central Statistical Office) Module — Phase 132

Polish economic statistics via BDL (Bank Danych Lokalnych) API
- GDP (Gross Domestic Product)
- CPI (Consumer Price Index / Inflation)
- Employment & Unemployment
- Industrial Production
- Trade Balance
- Wages & Earnings

Data Source: https://bdl.stat.gov.pl/api/v1/
API Docs: https://api.stat.gov.pl/Home/BdlApi
Refresh: Monthly
Coverage: Poland national statistics + voivodeships (regions)

Author: QUANTCLAW DATA Build Agent
Phase: 132

NOTE: BDL API variable IDs may change as GUS updates their database structure.
To find current variable IDs:
1. Browse BDL database: https://bdl.stat.gov.pl/
2. Search for indicators (e.g., "PKB" for GDP, "CPI", "Bezrobocie" for unemployment)
3. Use API endpoint: https://bdl.stat.gov.pl/api/v1/variables?subject-id=<SUBJECT_ID>
4. Update POLAND_INDICATORS dictionary with correct variable_id values

Current variable IDs are placeholders and need verification against current GUS BDL database.
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# GUS BDL API Configuration
BDL_BASE_URL = "https://bdl.stat.gov.pl/api/v1"

# Core Polish Economic Indicators (BDL Variable IDs)
# Format: variable_id, name, description, frequency
POLAND_INDICATORS = {
    'GDP': {
        'variable_id': '917',  # GDP current prices (PLN millions)
        'name': 'GDP - Gross Domestic Product (PLN millions)',
        'description': 'Poland GDP at current prices, quarterly data',
        'frequency': 'quarterly',
        'unit': 'PLN millions'
    },
    'GDP_GROWTH': {
        'variable_id': '918',  # GDP real growth rate
        'name': 'GDP Real Growth Rate (%)',
        'description': 'Year-on-year GDP growth rate, constant prices',
        'frequency': 'quarterly',
        'unit': '%'
    },
    'CPI': {
        'variable_id': '270',  # CPI index (previous year = 100)
        'name': 'CPI - Consumer Price Index',
        'description': 'Consumer price index, year-on-year change',
        'frequency': 'monthly',
        'unit': 'index (prev year = 100)'
    },
    'INFLATION': {
        'variable_id': '299',  # Inflation rate
        'name': 'Inflation Rate (%)',
        'description': 'Year-on-year inflation rate based on CPI',
        'frequency': 'monthly',
        'unit': '%'
    },
    'EMPLOYMENT': {
        'variable_id': '421',  # Employment in enterprises
        'name': 'Employment (thousands)',
        'description': 'Employment in enterprises sector (entities employing >9 persons)',
        'frequency': 'monthly',
        'unit': 'thousands of persons'
    },
    'UNEMPLOYMENT_RATE': {
        'variable_id': '421',  # Registered unemployment rate
        'name': 'Unemployment Rate (%)',
        'description': 'Registered unemployment rate',
        'frequency': 'monthly',
        'unit': '%'
    },
    'INDUSTRIAL_PRODUCTION': {
        'variable_id': '1696',  # Sold production of industry
        'name': 'Industrial Production Index',
        'description': 'Industrial production sold, constant prices',
        'frequency': 'monthly',
        'unit': 'index (prev year = 100)'
    },
    'INDUSTRIAL_GROWTH': {
        'variable_id': '1697',  # Industrial production growth
        'name': 'Industrial Production Growth (%)',
        'description': 'Year-on-year growth of industrial production',
        'frequency': 'monthly',
        'unit': '%'
    },
    'AVERAGE_WAGE': {
        'variable_id': '1633',  # Average monthly gross wages
        'name': 'Average Monthly Gross Wage (PLN)',
        'description': 'Average monthly gross wages and salaries in enterprise sector',
        'frequency': 'monthly',
        'unit': 'PLN'
    },
    'RETAIL_SALES': {
        'variable_id': '1698',  # Retail sales
        'name': 'Retail Sales Growth (%)',
        'description': 'Year-on-year growth of retail sales, constant prices',
        'frequency': 'monthly',
        'unit': '%'
    },
    'EXPORTS': {
        'variable_id': '1389',  # Exports value
        'name': 'Exports (EUR millions)',
        'description': 'Total exports value',
        'frequency': 'monthly',
        'unit': 'EUR millions'
    },
    'IMPORTS': {
        'variable_id': '1390',  # Imports value
        'name': 'Imports (EUR millions)',
        'description': 'Total imports value',
        'frequency': 'monthly',
        'unit': 'EUR millions'
    },
}

# Polish Voivodeships (Regions)
VOIVODESHIPS = {
    '02': 'Dolnośląskie (Lower Silesia)',
    '04': 'Kujawsko-pomorskie (Kuyavia-Pomerania)',
    '06': 'Lubelskie (Lublin)',
    '08': 'Lubuskie (Lubusz)',
    '10': 'Łódzkie (Łódź)',
    '12': 'Małopolskie (Lesser Poland)',
    '14': 'Mazowieckie (Masovia)',
    '16': 'Opolskie (Opole)',
    '18': 'Podkarpackie (Subcarpathia)',
    '20': 'Podlaskie (Podlaskie)',
    '22': 'Pomorskie (Pomerania)',
    '24': 'Śląskie (Silesia)',
    '26': 'Świętokrzyskie (Świętokrzyskie)',
    '28': 'Warmińsko-mazurskie (Warmia-Masuria)',
    '30': 'Wielkopolskie (Greater Poland)',
    '32': 'Zachodniopomorskie (West Pomerania)',
    '00': 'POLSKA (Poland - National)',
}


def bdl_request(endpoint: str, params: Dict = None) -> Dict:
    """
    Make request to BDL API
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
    
    Returns:
        API response as dictionary
    """
    if params is None:
        params = {}
    
    # Set default format to JSON
    params['format'] = 'json'
    
    try:
        url = f"{BDL_BASE_URL}/{endpoint}"
        headers = {
            'User-Agent': 'QuantClaw-Data/1.0',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        return {
            'success': True,
            'data': response.json(),
            'status_code': response.status_code
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_indicator_data(indicator_key: str, year_range: int = 3, unit_level: str = '0') -> Dict:
    """
    Get indicator data from BDL API
    
    Args:
        indicator_key: Indicator key from POLAND_INDICATORS
        year_range: Number of years of historical data (default 3)
        unit_level: Territorial unit level (0 = national, TERYT code for voivodeships)
    
    Returns:
        Dictionary with indicator data
    """
    if indicator_key not in POLAND_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = POLAND_INDICATORS[indicator_key]
    variable_id = indicator_config['variable_id']
    
    # Request data from BDL API
    # Endpoint: /data/by-variable/{variable-id}
    # Note: BDL API returns all available years by default, we'll filter in Python
    params = {
        'unit-level': unit_level
    }
    
    result = bdl_request(f'data/by-variable/{variable_id}', params)
    
    if not result['success']:
        return result
    
    # Parse BDL response
    response_data = result['data']
    
    if 'results' not in response_data or not response_data['results']:
        return {
            'success': False,
            'error': 'No data found in BDL response',
            'indicator': indicator_key
        }
    
    # Extract time series data
    observations = []
    current_year = datetime.now().year
    min_year = current_year - year_range
    
    for result_item in response_data['results']:
        if 'values' in result_item:
            for value_entry in result_item['values']:
                year_str = value_entry.get('year')
                val = value_entry.get('val')
                
                if year_str and val is not None:
                    try:
                        year = int(year_str)
                        # Filter to requested year range
                        if year < min_year:
                            continue
                        
                        # BDL API doesn't provide period info in the values array
                        # For now, use just the year as the period
                        period_str = year_str
                        
                        observations.append({
                            'period': period_str,
                            'year': year,
                            'value': float(val)
                        })
                    except (ValueError, TypeError):
                        continue
    
    # Sort by period descending
    observations.sort(key=lambda x: x['year'], reverse=True)
    
    if not observations:
        return {
            'success': False,
            'error': 'No valid observations found',
            'indicator': indicator_key
        }
    
    # Calculate changes
    latest_value = observations[0]['value']
    
    # Period-over-period change (month/quarter)
    period_change = None
    period_change_pct = None
    if len(observations) >= 2:
        previous = observations[1]['value']
        if previous and previous != 0:
            period_change = latest_value - previous
            period_change_pct = (period_change / previous) * 100
    
    # Year-over-year change
    yoy_change = None
    yoy_change_pct = None
    periods_per_year = 12 if indicator_config['frequency'] == 'monthly' else 4
    if len(observations) > periods_per_year:
        year_ago = observations[periods_per_year]['value']
        if year_ago and year_ago != 0:
            yoy_change = latest_value - year_ago
            yoy_change_pct = (yoy_change / year_ago) * 100
    
    return {
        'success': True,
        'indicator': indicator_config['name'],
        'indicator_key': indicator_key,
        'description': indicator_config['description'],
        'frequency': indicator_config['frequency'],
        'unit': indicator_config['unit'],
        'latest_value': latest_value,
        'latest_period': observations[0]['period'],
        'period_change': period_change,
        'period_change_pct': period_change_pct,
        'yoy_change': yoy_change,
        'yoy_change_pct': yoy_change_pct,
        'data_points': observations[:24],  # Last 24 periods
        'count': len(observations),
        'timestamp': datetime.now().isoformat()
    }


def get_gdp_data() -> Dict:
    """
    Get Poland GDP data (current prices and real growth)
    
    Returns:
        Dictionary with GDP statistics
    """
    gdp = get_indicator_data('GDP', year_range=5)
    gdp_growth = get_indicator_data('GDP_GROWTH', year_range=5)
    
    result = {
        'success': True,
        'country': 'Poland',
        'timestamp': datetime.now().isoformat()
    }
    
    if gdp['success']:
        result['gdp'] = {
            'current_value_pln_millions': gdp['latest_value'],
            'period': gdp['latest_period'],
            'yoy_change_pct': gdp.get('yoy_change_pct'),
            'history': gdp['data_points'][:8]
        }
    
    if gdp_growth['success']:
        result['gdp_real_growth'] = {
            'current_rate_pct': gdp_growth['latest_value'],
            'period': gdp_growth['latest_period'],
            'history': gdp_growth['data_points'][:8]
        }
    
    return result


def get_inflation_data() -> Dict:
    """
    Get Poland inflation/CPI data
    
    Returns:
        Dictionary with inflation statistics
    """
    cpi = get_indicator_data('CPI', year_range=3)
    inflation = get_indicator_data('INFLATION', year_range=3)
    
    result = {
        'success': True,
        'country': 'Poland',
        'timestamp': datetime.now().isoformat()
    }
    
    if cpi['success']:
        result['cpi'] = {
            'current_index': cpi['latest_value'],
            'period': cpi['latest_period'],
            'mom_change_pct': cpi.get('period_change_pct'),
            'yoy_change_pct': cpi.get('yoy_change_pct'),
            'history': cpi['data_points'][:12]
        }
    
    if inflation['success']:
        result['inflation_rate'] = {
            'current_rate_pct': inflation['latest_value'],
            'period': inflation['latest_period'],
            'change_from_previous': inflation.get('period_change'),
            'history': inflation['data_points'][:12]
        }
    
    return result


def get_employment_data() -> Dict:
    """
    Get Poland employment and unemployment data
    
    Returns:
        Dictionary with employment statistics
    """
    employment = get_indicator_data('EMPLOYMENT', year_range=3)
    unemployment = get_indicator_data('UNEMPLOYMENT_RATE', year_range=3)
    wages = get_indicator_data('AVERAGE_WAGE', year_range=3)
    
    result = {
        'success': True,
        'country': 'Poland',
        'timestamp': datetime.now().isoformat()
    }
    
    if employment['success']:
        result['employment'] = {
            'current_level_thousands': employment['latest_value'],
            'period': employment['latest_period'],
            'yoy_change_pct': employment.get('yoy_change_pct'),
            'history': employment['data_points'][:12]
        }
    
    if unemployment['success']:
        result['unemployment_rate'] = {
            'current_rate_pct': unemployment['latest_value'],
            'period': unemployment['latest_period'],
            'change_from_previous': unemployment.get('period_change'),
            'history': unemployment['data_points'][:12]
        }
    
    if wages['success']:
        result['average_wage'] = {
            'current_wage_pln': wages['latest_value'],
            'period': wages['latest_period'],
            'yoy_change_pct': wages.get('yoy_change_pct'),
            'history': wages['data_points'][:12]
        }
    
    return result


def get_industrial_data() -> Dict:
    """
    Get Poland industrial production data
    
    Returns:
        Dictionary with industrial production statistics
    """
    production = get_indicator_data('INDUSTRIAL_PRODUCTION', year_range=3)
    growth = get_indicator_data('INDUSTRIAL_GROWTH', year_range=3)
    
    result = {
        'success': True,
        'country': 'Poland',
        'timestamp': datetime.now().isoformat()
    }
    
    if production['success']:
        result['industrial_production'] = {
            'current_index': production['latest_value'],
            'period': production['latest_period'],
            'mom_change_pct': production.get('period_change_pct'),
            'yoy_change_pct': production.get('yoy_change_pct'),
            'history': production['data_points'][:12]
        }
    
    if growth['success']:
        result['industrial_growth'] = {
            'current_rate_pct': growth['latest_value'],
            'period': growth['latest_period'],
            'change_from_previous': growth.get('period_change'),
            'history': growth['data_points'][:12]
        }
    
    return result


def get_trade_data() -> Dict:
    """
    Get Poland trade balance (exports/imports)
    
    Returns:
        Dictionary with trade statistics
    """
    exports = get_indicator_data('EXPORTS', year_range=3)
    imports = get_indicator_data('IMPORTS', year_range=3)
    
    result = {
        'success': True,
        'country': 'Poland',
        'timestamp': datetime.now().isoformat()
    }
    
    if exports['success']:
        result['exports'] = {
            'current_value_eur_millions': exports['latest_value'],
            'period': exports['latest_period'],
            'yoy_change_pct': exports.get('yoy_change_pct'),
            'history': exports['data_points'][:12]
        }
    
    if imports['success']:
        result['imports'] = {
            'current_value_eur_millions': imports['latest_value'],
            'period': imports['latest_period'],
            'yoy_change_pct': imports.get('yoy_change_pct'),
            'history': imports['data_points'][:12]
        }
    
    # Calculate trade balance
    if exports['success'] and imports['success']:
        trade_balance = exports['latest_value'] - imports['latest_value']
        result['trade_balance'] = {
            'current_value_eur_millions': trade_balance,
            'period': exports['latest_period']
        }
    
    return result


def get_economic_dashboard() -> Dict:
    """
    Get comprehensive Poland economic dashboard
    
    Returns:
        Dictionary with complete economic overview
    """
    dashboard = {
        'success': True,
        'country': 'Poland',
        'dashboard': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Get all key indicators
    print("Fetching GDP data...", file=sys.stderr)
    gdp = get_gdp_data()
    if gdp['success']:
        dashboard['dashboard']['gdp'] = gdp
    
    print("Fetching inflation data...", file=sys.stderr)
    inflation = get_inflation_data()
    if inflation['success']:
        dashboard['dashboard']['inflation'] = inflation
    
    print("Fetching employment data...", file=sys.stderr)
    employment = get_employment_data()
    if employment['success']:
        dashboard['dashboard']['employment'] = employment
    
    print("Fetching industrial production data...", file=sys.stderr)
    industrial = get_industrial_data()
    if industrial['success']:
        dashboard['dashboard']['industrial'] = industrial
    
    print("Fetching trade data...", file=sys.stderr)
    trade = get_trade_data()
    if trade['success']:
        dashboard['dashboard']['trade'] = trade
    
    return dashboard


def list_indicators() -> Dict:
    """
    List all available Poland GUS indicators
    
    Returns:
        Dictionary with indicator list
    """
    indicators = []
    for key, config in POLAND_INDICATORS.items():
        indicators.append({
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'frequency': config['frequency'],
            'unit': config['unit'],
            'variable_id': config['variable_id']
        })
    
    return {
        'success': True,
        'indicators': indicators,
        'count': len(indicators)
    }


def list_voivodeships() -> Dict:
    """
    List Polish voivodeships (regions)
    
    Returns:
        Dictionary with voivodeship list
    """
    voivodeships = [{'code': code, 'name': name} for code, name in VOIVODESHIPS.items()]
    
    return {
        'success': True,
        'voivodeships': voivodeships,
        'count': len(voivodeships)
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'poland-indicator':
            if len(sys.argv) < 3:
                print("Error: poland-indicator requires indicator key", file=sys.stderr)
                print("Usage: python3 poland_gus.py poland-indicator <INDICATOR_KEY>", file=sys.stderr)
                return 1
            
            indicator_key = sys.argv[2].upper()
            
            if indicator_key not in POLAND_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(POLAND_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            data = get_indicator_data(indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-gdp':
            data = get_gdp_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-inflation':
            data = get_inflation_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-employment':
            data = get_employment_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-industrial':
            data = get_industrial_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-trade':
            data = get_trade_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-dashboard':
            data = get_economic_dashboard()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-indicators':
            data = list_indicators()
            print(json.dumps(data, indent=2))
        
        elif command == 'poland-voivodeships':
            data = list_voivodeships()
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
Poland GUS (Central Statistical Office) Module (Phase 132)

Commands:
  python3 poland_gus.py poland-indicator <KEY>    # Get specific indicator
  python3 poland_gus.py poland-gdp                # Get GDP data
  python3 poland_gus.py poland-inflation          # Get CPI/inflation data
  python3 poland_gus.py poland-employment         # Get employment/unemployment/wages
  python3 poland_gus.py poland-industrial         # Get industrial production
  python3 poland_gus.py poland-trade              # Get trade balance (exports/imports)
  python3 poland_gus.py poland-dashboard          # Complete economic overview
  python3 poland_gus.py poland-indicators         # List all indicators
  python3 poland_gus.py poland-voivodeships       # List Polish regions

Examples:
  python3 poland_gus.py poland-indicator GDP
  python3 poland_gus.py poland-indicator INFLATION
  python3 poland_gus.py poland-gdp
  python3 poland_gus.py poland-inflation
  python3 poland_gus.py poland-employment
  python3 poland_gus.py poland-industrial
  python3 poland_gus.py poland-trade
  python3 poland_gus.py poland-dashboard

Available Indicators:
  Economic Output:
    GDP                     = Gross Domestic Product (PLN millions, quarterly)
    GDP_GROWTH              = Real GDP growth rate (%, quarterly)
  
  Prices:
    CPI                     = Consumer Price Index (monthly)
    INFLATION               = Year-on-year inflation rate (%, monthly)
  
  Labor Market:
    EMPLOYMENT              = Employment level (thousands, monthly)
    UNEMPLOYMENT_RATE       = Unemployment rate (%, monthly)
    AVERAGE_WAGE            = Average monthly gross wage (PLN, monthly)
  
  Production & Sales:
    INDUSTRIAL_PRODUCTION   = Industrial production index (monthly)
    INDUSTRIAL_GROWTH       = Industrial production growth (%, monthly)
    RETAIL_SALES            = Retail sales growth (%, monthly)
  
  External Trade:
    EXPORTS                 = Total exports (EUR millions, monthly)
    IMPORTS                 = Total imports (EUR millions, monthly)

Data Source: https://bdl.stat.gov.pl/api/v1/
Authority: GUS - Główny Urząd Statystyczny (Central Statistical Office of Poland)
Coverage: National data + 16 voivodeships (regions)
Refresh: Monthly (most indicators), Quarterly (GDP)

Note: This module uses the BDL (Bank Danych Lokalnych) public API.
Variable IDs may change - check https://bdl.stat.gov.pl for updates.
""")


if __name__ == "__main__":
    sys.exit(main())
