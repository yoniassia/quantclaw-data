#!/usr/bin/env python3
"""
World Bank Open Data Module — Phase 94

Comprehensive economic indicators for 217 countries via World Bank API
- GDP (current USD)
- GNI (Gross National Income)
- Inflation (CPI)
- FDI (Foreign Direct Investment)
- Poverty headcount ratio

Data Source: api.worldbank.org/v2
Refresh: Weekly
Coverage: 217 countries, 60+ years of historical data

Author: QUANTCLAW DATA Build Agent
Phase: 94
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# World Bank API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"

# Core Economic Indicators
WB_INDICATORS = {
    'GDP': {
        'id': 'NY.GDP.MKTP.CD',
        'name': 'GDP (current US$)',
        'description': 'Gross domestic product at market prices'
    },
    'GDP_GROWTH': {
        'id': 'NY.GDP.MKTP.KD.ZG',
        'name': 'GDP growth (annual %)',
        'description': 'Annual percentage growth rate of GDP'
    },
    'GNI': {
        'id': 'NY.GNP.MKTP.CD',
        'name': 'GNI (current US$)',
        'description': 'Gross national income'
    },
    'GNI_PER_CAPITA': {
        'id': 'NY.GNP.PCAP.CD',
        'name': 'GNI per capita (current US$)',
        'description': 'Gross national income divided by midyear population'
    },
    'INFLATION': {
        'id': 'FP.CPI.TOTL.ZG',
        'name': 'Inflation, consumer prices (annual %)',
        'description': 'Annual change in consumer price index'
    },
    'FDI': {
        'id': 'BX.KLT.DINV.WD.GD.ZS',
        'name': 'Foreign direct investment, net inflows (% of GDP)',
        'description': 'Net inflows of investment to acquire management interest'
    },
    'FDI_NET_INFLOWS': {
        'id': 'BX.KLT.DINV.CD.WD',
        'name': 'Foreign direct investment, net inflows (BoP, current US$)',
        'description': 'Net FDI inflows in current dollars'
    },
    'POVERTY': {
        'id': 'SI.POV.DDAY',
        'name': 'Poverty headcount ratio at $2.15 a day (2017 PPP) (% of population)',
        'description': 'Percentage of population living on less than $2.15 per day'
    },
    'UNEMPLOYMENT': {
        'id': 'SL.UEM.TOTL.ZS',
        'name': 'Unemployment, total (% of total labor force)',
        'description': 'Share of labor force that is without work'
    },
    'TRADE': {
        'id': 'NE.TRD.GNFS.ZS',
        'name': 'Trade (% of GDP)',
        'description': 'Sum of exports and imports as % of GDP'
    },
    'DEBT': {
        'id': 'GC.DOD.TOTL.GD.ZS',
        'name': 'Central government debt, total (% of GDP)',
        'description': 'Gross debt of central government as % of GDP'
    },
    'POPULATION': {
        'id': 'SP.POP.TOTL',
        'name': 'Population, total',
        'description': 'Total population based on de facto definition'
    },
}


def wb_request(endpoint: str, params: Dict = None, per_page: int = 500) -> Dict:
    """
    Make request to World Bank API
    Returns JSON response with proper error handling and pagination
    """
    if params is None:
        params = {}
    
    # Set default format to JSON
    params['format'] = 'json'
    params['per_page'] = per_page
    
    try:
        url = f"{WB_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # World Bank API returns [metadata, data] array
        if isinstance(data, list) and len(data) >= 2:
            metadata = data[0]
            results = data[1]
            
            return {
                'success': True,
                'metadata': metadata,
                'data': results,
                'total': metadata.get('total', 0),
                'page': metadata.get('page', 1),
                'pages': metadata.get('pages', 1)
            }
        else:
            return {
                'success': False,
                'error': 'Unexpected API response format',
                'raw': data
            }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_countries(region: Optional[str] = None) -> Dict:
    """
    Get list of all countries from World Bank
    
    Args:
        region: Optional region code (e.g., 'EAS', 'ECS', 'LCN', 'NAC', 'SAS', 'SSA')
    
    Returns:
        Dictionary with country data
    """
    params = {}
    if region:
        endpoint = f"region/{region}/country"
    else:
        endpoint = "country"
    
    params['per_page'] = 500
    
    result = wb_request(endpoint, params)
    
    if result['success']:
        countries = []
        for country in result['data']:
            # Filter out aggregates (regions, income groups)
            if country.get('capitalCity'):  # Real countries have capitals
                countries.append({
                    'id': country['id'],
                    'iso2Code': country['iso2Code'],
                    'name': country['name'],
                    'region': country['region']['value'] if country.get('region') else 'Unknown',
                    'income_level': country['incomeLevel']['value'] if country.get('incomeLevel') else 'Unknown',
                    'capital': country.get('capitalCity', ''),
                    'longitude': country.get('longitude', ''),
                    'latitude': country.get('latitude', '')
                })
        
        return {
            'success': True,
            'countries': countries,
            'count': len(countries)
        }
    else:
        return result


def get_indicator_data(country_code: str, indicator_id: str, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict:
    """
    Get indicator data for a specific country
    
    Args:
        country_code: ISO 3-letter country code (e.g., 'USA', 'CHN', 'GBR')
        indicator_id: World Bank indicator ID (e.g., 'NY.GDP.MKTP.CD')
        start_year: Optional start year (defaults to 10 years ago)
        end_year: Optional end year (defaults to current year)
    
    Returns:
        Dictionary with indicator data
    """
    if start_year is None:
        start_year = datetime.now().year - 10
    if end_year is None:
        end_year = datetime.now().year
    
    endpoint = f"country/{country_code}/indicator/{indicator_id}"
    params = {
        'date': f"{start_year}:{end_year}",
    }
    
    result = wb_request(endpoint, params)
    
    if result['success']:
        # Parse and structure the data
        data_points = []
        for item in result['data']:
            if item['value'] is not None:
                data_points.append({
                    'year': int(item['date']),
                    'value': item['value'],
                    'country': item['country']['value'],
                    'country_code': item['countryiso3code']
                })
        
        # Sort by year descending
        data_points.sort(key=lambda x: x['year'], reverse=True)
        
        # Calculate year-over-year change for latest value
        yoy_change = None
        yoy_change_pct = None
        if len(data_points) >= 2:
            latest = data_points[0]['value']
            previous = data_points[1]['value']
            if previous and previous != 0:
                yoy_change = latest - previous
                yoy_change_pct = (yoy_change / previous) * 100
        
        return {
            'success': True,
            'country': data_points[0]['country'] if data_points else country_code,
            'country_code': country_code,
            'indicator': indicator_id,
            'latest_value': data_points[0]['value'] if data_points else None,
            'latest_year': data_points[0]['year'] if data_points else None,
            'yoy_change': yoy_change,
            'yoy_change_pct': yoy_change_pct,
            'data_points': data_points,
            'count': len(data_points)
        }
    else:
        return result


def get_country_profile(country_code: str, indicators: Optional[List[str]] = None, years: int = 10) -> Dict:
    """
    Get comprehensive economic profile for a country
    
    Args:
        country_code: ISO 3-letter country code
        indicators: List of indicator keys from WB_INDICATORS (defaults to core set)
        years: Number of historical years to fetch (default 10)
    
    Returns:
        Dictionary with complete country economic profile
    """
    if indicators is None:
        # Core indicators set
        indicators = ['GDP', 'GDP_GROWTH', 'GNI_PER_CAPITA', 'INFLATION', 'FDI', 'UNEMPLOYMENT', 'POPULATION']
    
    # Get country metadata
    country_info_result = wb_request(f"country/{country_code}")
    
    if not country_info_result['success'] or not country_info_result['data']:
        return {
            'success': False,
            'error': f'Country {country_code} not found'
        }
    
    country_info = country_info_result['data'][0]
    
    # Fetch all indicators
    profile = {
        'success': True,
        'country': country_info['name'],
        'country_code': country_code,
        'iso2_code': country_info['iso2Code'],
        'region': country_info['region']['value'] if country_info.get('region') else 'Unknown',
        'income_level': country_info['incomeLevel']['value'] if country_info.get('incomeLevel') else 'Unknown',
        'capital': country_info.get('capitalCity', ''),
        'coordinates': {
            'longitude': country_info.get('longitude', ''),
            'latitude': country_info.get('latitude', '')
        },
        'indicators': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Fetch each indicator
    for indicator_key in indicators:
        if indicator_key not in WB_INDICATORS:
            continue
        
        indicator_config = WB_INDICATORS[indicator_key]
        indicator_data = get_indicator_data(country_code, indicator_config['id'], 
                                           start_year=datetime.now().year - years)
        
        if indicator_data['success'] and indicator_data['latest_value'] is not None:
            profile['indicators'][indicator_key] = {
                'name': indicator_config['name'],
                'latest_value': indicator_data['latest_value'],
                'latest_year': indicator_data['latest_year'],
                'yoy_change': indicator_data['yoy_change'],
                'yoy_change_pct': indicator_data['yoy_change_pct'],
                'history': indicator_data['data_points'][:5]  # Last 5 years
            }
        else:
            profile['indicators'][indicator_key] = {
                'name': indicator_config['name'],
                'latest_value': None,
                'note': 'Data not available'
            }
        
        # Rate limiting - be nice to World Bank API
        time.sleep(0.1)
    
    return profile


def compare_countries(country_codes: List[str], indicator_key: str = 'GDP', year: Optional[int] = None) -> Dict:
    """
    Compare indicator across multiple countries
    
    Args:
        country_codes: List of ISO 3-letter country codes
        indicator_key: Indicator key from WB_INDICATORS
        year: Specific year to compare (defaults to latest available)
    
    Returns:
        Dictionary with comparison data
    """
    if indicator_key not in WB_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = WB_INDICATORS[indicator_key]
    
    comparison = {
        'success': True,
        'indicator': indicator_config['name'],
        'indicator_id': indicator_config['id'],
        'comparison_year': year or 'latest',
        'countries': []
    }
    
    for country_code in country_codes:
        indicator_data = get_indicator_data(country_code, indicator_config['id'], 
                                           start_year=datetime.now().year - 10)
        
        if indicator_data['success'] and indicator_data['data_points']:
            # If specific year requested, find it
            if year:
                data_point = next((d for d in indicator_data['data_points'] if d['year'] == year), None)
            else:
                data_point = indicator_data['data_points'][0]  # Latest
            
            if data_point:
                comparison['countries'].append({
                    'country': indicator_data['country'],
                    'country_code': country_code,
                    'value': data_point['value'],
                    'year': data_point['year']
                })
        
        time.sleep(0.1)  # Rate limiting
    
    # Sort by value descending
    comparison['countries'].sort(key=lambda x: x['value'] if x['value'] else 0, reverse=True)
    
    return comparison


def search_countries(query: str) -> Dict:
    """
    Search for countries by name
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with matching countries
    """
    all_countries = get_countries()
    
    if not all_countries['success']:
        return all_countries
    
    query_lower = query.lower()
    matches = [
        country for country in all_countries['countries']
        if query_lower in country['name'].lower() or query_lower in country['id'].lower()
    ]
    
    return {
        'success': True,
        'query': query,
        'matches': matches,
        'count': len(matches)
    }


def get_regional_aggregate(region_code: str, indicator_key: str = 'GDP') -> Dict:
    """
    Get aggregated indicator data for a region
    
    World Bank regions:
    - EAS: East Asia & Pacific
    - ECS: Europe & Central Asia
    - LCN: Latin America & Caribbean
    - MEA: Middle East & North Africa
    - NAC: North America
    - SAS: South Asia
    - SSA: Sub-Saharan Africa
    
    Args:
        region_code: World Bank region code
        indicator_key: Indicator key from WB_INDICATORS
    
    Returns:
        Dictionary with regional aggregate data
    """
    if indicator_key not in WB_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = WB_INDICATORS[indicator_key]
    
    # World Bank provides regional aggregates with special codes
    region_mapping = {
        'EAS': 'EAS',  # East Asia & Pacific
        'ECS': 'ECS',  # Europe & Central Asia
        'LCN': 'LCN',  # Latin America & Caribbean
        'MEA': 'MEA',  # Middle East & North Africa
        'NAC': 'NAC',  # North America
        'SAS': 'SAS',  # South Asia
        'SSA': 'SSF',  # Sub-Saharan Africa
    }
    
    wb_region_code = region_mapping.get(region_code, region_code)
    
    return get_indicator_data(wb_region_code, indicator_config['id'], 
                            start_year=datetime.now().year - 10)


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'country-profile':
            if len(sys.argv) < 3:
                print("Error: country-profile requires a country code", file=sys.stderr)
                print("Usage: python cli.py country-profile <COUNTRY_CODE> [--indicators GDP,INFLATION]", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            
            # Parse optional indicators
            indicators = None
            if '--indicators' in sys.argv:
                idx = sys.argv.index('--indicators')
                if idx + 1 < len(sys.argv):
                    indicators = sys.argv[idx + 1].split(',')
            
            data = get_country_profile(country_code, indicators=indicators)
            print(json.dumps(data, indent=2))
        
        elif command == 'countries':
            region = None
            if '--region' in sys.argv:
                idx = sys.argv.index('--region')
                if idx + 1 < len(sys.argv):
                    region = sys.argv[idx + 1]
            
            data = get_countries(region=region)
            print(json.dumps(data, indent=2))
        
        elif command == 'indicator':
            if len(sys.argv) < 4:
                print("Error: indicator requires country code and indicator key", file=sys.stderr)
                print("Usage: python cli.py indicator <COUNTRY_CODE> <INDICATOR_KEY>", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            indicator_key = sys.argv[3].upper()
            
            if indicator_key not in WB_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(WB_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            indicator_config = WB_INDICATORS[indicator_key]
            data = get_indicator_data(country_code, indicator_config['id'])
            print(json.dumps(data, indent=2))
        
        elif command == 'compare':
            if len(sys.argv) < 3:
                print("Error: compare requires country codes", file=sys.stderr)
                print("Usage: python cli.py compare <CODES> [--indicator GDP]", file=sys.stderr)
                return 1
            
            country_codes = sys.argv[2].upper().split(',')
            
            indicator_key = 'GDP'
            if '--indicator' in sys.argv:
                idx = sys.argv.index('--indicator')
                if idx + 1 < len(sys.argv):
                    indicator_key = sys.argv[idx + 1].upper()
            
            data = compare_countries(country_codes, indicator_key=indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'search':
            if len(sys.argv) < 3:
                print("Error: search requires a query", file=sys.stderr)
                print("Usage: python cli.py search <QUERY>", file=sys.stderr)
                return 1
            
            query = ' '.join(sys.argv[2:])
            data = search_countries(query)
            print(json.dumps(data, indent=2))
        
        elif command == 'regional':
            if len(sys.argv) < 3:
                print("Error: regional requires a region code", file=sys.stderr)
                print("Usage: python cli.py regional <REGION_CODE> [--indicator GDP]", file=sys.stderr)
                return 1
            
            region_code = sys.argv[2].upper()
            
            indicator_key = 'GDP'
            if '--indicator' in sys.argv:
                idx = sys.argv.index('--indicator')
                if idx + 1 < len(sys.argv):
                    indicator_key = sys.argv[idx + 1].upper()
            
            data = get_regional_aggregate(region_code, indicator_key=indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'indicators':
            # List all available indicators
            indicators_list = []
            for key, config in WB_INDICATORS.items():
                indicators_list.append({
                    'key': key,
                    'id': config['id'],
                    'name': config['name'],
                    'description': config['description']
                })
            
            print(json.dumps({
                'success': True,
                'indicators': indicators_list,
                'count': len(indicators_list)
            }, indent=2))
        
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
World Bank Open Data Module (Phase 94)

Commands:
  python cli.py country-profile <CODE> [--indicators GDP,INFLATION]
                                      # Comprehensive country economic profile
  
  python cli.py countries [--region EAS]
                                      # List all countries (optional: filter by region)
  
  python cli.py indicator <CODE> <INDICATOR>
                                      # Get specific indicator for a country
  
  python cli.py compare <CODE1,CODE2,CODE3> [--indicator GDP]
                                      # Compare countries on specific indicator
  
  python cli.py search <QUERY>       # Search for countries by name
  
  python cli.py regional <REGION> [--indicator GDP]
                                      # Regional aggregate data
  
  python cli.py indicators            # List all available indicators

Examples:
  python cli.py country-profile USA
  python cli.py country-profile CHN --indicators GDP,INFLATION,FDI
  python cli.py countries --region EAS
  python cli.py indicator USA GDP
  python cli.py indicator CHN INFLATION
  python cli.py compare USA,CHN,JPN,DEU,GBR --indicator GDP
  python cli.py search "United"
  python cli.py regional EAS --indicator GDP_GROWTH
  python cli.py indicators

Country Codes: 3-letter ISO codes (USA, CHN, GBR, DEU, JPN, etc.)

Regions:
  EAS  = East Asia & Pacific
  ECS  = Europe & Central Asia
  LCN  = Latin America & Caribbean
  MEA  = Middle East & North Africa
  NAC  = North America
  SAS  = South Asia
  SSA  = Sub-Saharan Africa

Indicators:
  GDP              = GDP (current US$)
  GDP_GROWTH       = GDP growth (annual %)
  GNI              = GNI (current US$)
  GNI_PER_CAPITA   = GNI per capita
  INFLATION        = Consumer price inflation (annual %)
  FDI              = Foreign direct investment (% of GDP)
  FDI_NET_INFLOWS  = FDI net inflows (current US$)
  POVERTY          = Poverty headcount ratio at $2.15/day
  UNEMPLOYMENT     = Unemployment rate
  TRADE            = Trade (% of GDP)
  DEBT             = Government debt (% of GDP)
  POPULATION       = Total population

Data Source: api.worldbank.org/v2
Coverage: 217 countries, 60+ years historical data
Refresh: Weekly
""")


if __name__ == "__main__":
    sys.exit(main())
