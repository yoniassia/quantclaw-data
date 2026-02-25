#!/usr/bin/env python3
"""
Eurostat EU Statistics Module — Phase 99

Comprehensive economic indicators for EU-27 via Eurostat SDMX API
- GDP (Gross Domestic Product)
- HICP (Harmonized Index of Consumer Prices - Inflation)
- Unemployment rate
- Industrial production
- Trade balance
- Government debt

Data Source: https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1
SDMX Protocol: Statistical Data and Metadata eXchange
Refresh: Weekly
Coverage: EU-27 countries + UK, Norway, Switzerland, etc.

Author: QUANTCLAW DATA Build Agent
Phase: 99
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import xml.etree.ElementTree as ET

# Eurostat SDMX API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"

# Core Economic Indicators
# Format: dataflow_id, series_key
EUROSTAT_INDICATORS = {
    'GDP': {
        'dataflow': 'namq_10_gdp',
        'series': 'Q.CP_MEUR.NSA.B1GQ',
        'name': 'GDP (current prices, million EUR)',
        'description': 'Gross domestic product at market prices'
    },
    'GDP_GROWTH': {
        'dataflow': 'namq_10_gdp',
        'series': 'Q.CLV_PCH_PRE.NSA.B1GQ',
        'name': 'GDP growth rate (%, previous period)',
        'description': 'Quarterly GDP growth rate'
    },
    'HICP': {
        'dataflow': 'prc_hicp_midx',
        'series': 'M.CP-HI00.I15',
        'name': 'HICP - Harmonized Index of Consumer Prices',
        'description': 'Inflation index (2015=100)'
    },
    'INFLATION': {
        'dataflow': 'prc_hicp_manr',
        'series': 'M.CP-HI00.RCH_A',
        'name': 'HICP Inflation Rate (% year-on-year)',
        'description': 'Annual inflation rate'
    },
    'UNEMPLOYMENT': {
        'dataflow': 'une_rt_m',
        'series': 'M.SA.TOTAL.PC_ACT',
        'name': 'Unemployment rate (%, seasonally adjusted)',
        'description': 'Unemployment as % of active population'
    },
    'INDUSTRIAL_PRODUCTION': {
        'dataflow': 'sts_inpr_m',
        'series': 'M.PROD.B-D.CA.I21',
        'name': 'Industrial production index (2021=100)',
        'description': 'Manufacturing production volume index'
    },
    'TRADE_BALANCE': {
        'dataflow': 'ext_lt_intratrd',
        'series': 'M.BALANCE.MIO_EUR.4000',
        'name': 'Trade balance (million EUR)',
        'description': 'Extra-EU trade balance'
    },
    'GOVERNMENT_DEBT': {
        'dataflow': 'gov_10q_ggdebt',
        'series': 'Q.PC_GDP.S13.GD',
        'name': 'Government debt (% of GDP)',
        'description': 'General government gross debt'
    },
}

# EU-27 Country Codes
EU27_COUNTRIES = {
    'AT': 'Austria',
    'BE': 'Belgium',
    'BG': 'Bulgaria',
    'HR': 'Croatia',
    'CY': 'Cyprus',
    'CZ': 'Czech Republic',
    'DK': 'Denmark',
    'EE': 'Estonia',
    'FI': 'Finland',
    'FR': 'France',
    'DE': 'Germany',
    'EL': 'Greece',
    'HU': 'Hungary',
    'IE': 'Ireland',
    'IT': 'Italy',
    'LV': 'Latvia',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'MT': 'Malta',
    'NL': 'Netherlands',
    'PL': 'Poland',
    'PT': 'Portugal',
    'RO': 'Romania',
    'SK': 'Slovakia',
    'SI': 'Slovenia',
    'ES': 'Spain',
    'SE': 'Sweden',
}

# Additional European countries available in Eurostat
OTHER_COUNTRIES = {
    'UK': 'United Kingdom',
    'NO': 'Norway',
    'CH': 'Switzerland',
    'IS': 'Iceland',
    'LI': 'Liechtenstein',
    'TR': 'Turkey',
    'MK': 'North Macedonia',
    'RS': 'Serbia',
    'AL': 'Albania',
    'ME': 'Montenegro',
    'BA': 'Bosnia and Herzegovina',
}

ALL_COUNTRIES = {**EU27_COUNTRIES, **OTHER_COUNTRIES}


def sdmx_request(endpoint: str, params: Dict = None) -> Dict:
    """
    Make request to Eurostat SDMX API
    Returns parsed XML as dictionary
    """
    if params is None:
        params = {}
    
    try:
        url = f"{EUROSTAT_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=30)
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
    Parse SDMX-ML GenericData format
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
            # Extract series attributes (country, indicator, etc.)
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


def get_indicator_data(country_code: str, indicator_key: str, last_n_periods: int = 20) -> Dict:
    """
    Get indicator data for a specific country
    
    Args:
        country_code: EU country code (e.g., 'DE', 'FR', 'IT', 'EU27_2020' for EU aggregate)
        indicator_key: Indicator key from EUROSTAT_INDICATORS
        last_n_periods: Number of recent periods to fetch (default 20)
    
    Returns:
        Dictionary with indicator data
    """
    if indicator_key not in EUROSTAT_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = EUROSTAT_INDICATORS[indicator_key]
    dataflow = indicator_config['dataflow']
    
    # Construct SDMX data URL
    # Eurostat dimension order: FREQ.UNIT.S_ADJ.NA_ITEM.GEO
    # Our series format in config: FREQ.UNIT.S_ADJ.NA_ITEM (without GEO)
    series_parts = indicator_config['series'].split('.')
    freq = series_parts[0]  # M (monthly) or Q (quarterly)
    rest_of_series = '.'.join(series_parts[1:])
    
    # Build series key with country at the end (GEO dimension)
    series_key = f"{freq}.{rest_of_series}.{country_code}"
    endpoint = f"data/{dataflow}/{series_key}"
    
    # Add lastNObservations parameter
    params = {'lastNObservations': last_n_periods}
    
    result = sdmx_request(endpoint, params)
    
    if not result['success']:
        return result
    
    # Parse SDMX XML
    observations = parse_sdmx_data(result['raw_xml'])
    
    if not observations:
        return {
            'success': False,
            'error': 'No data found or parsing failed',
            'country_code': country_code,
            'indicator': indicator_key
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
    
    # Get country name
    country_name = ALL_COUNTRIES.get(country_code, 'EU27' if 'EU27' in country_code else country_code)
    
    return {
        'success': True,
        'country': country_name,
        'country_code': country_code,
        'indicator': indicator_config['name'],
        'indicator_key': indicator_key,
        'latest_value': observations[0]['value'],
        'latest_period': observations[0]['time_period'],
        'period_change': period_change,
        'period_change_pct': period_change_pct,
        'data_points': [{'period': obs['time_period'], 'value': obs['value']} for obs in observations],
        'count': len(observations),
        'timestamp': datetime.now().isoformat()
    }


def get_country_profile(country_code: str, indicators: Optional[List[str]] = None, periods: int = 20) -> Dict:
    """
    Get comprehensive economic profile for an EU country
    
    Args:
        country_code: EU country code (2-letter ISO)
        indicators: List of indicator keys (defaults to core set)
        periods: Number of historical periods to fetch
    
    Returns:
        Dictionary with complete country economic profile
    """
    if indicators is None:
        # Core indicators set
        indicators = ['GDP', 'GDP_GROWTH', 'HICP', 'INFLATION', 'UNEMPLOYMENT', 'INDUSTRIAL_PRODUCTION']
    
    # Validate country code
    if country_code not in ALL_COUNTRIES and 'EU27' not in country_code:
        return {
            'success': False,
            'error': f'Unknown country code: {country_code}'
        }
    
    country_name = ALL_COUNTRIES.get(country_code, 'EU27 Aggregate')
    
    profile = {
        'success': True,
        'country': country_name,
        'country_code': country_code,
        'is_eu27': country_code in EU27_COUNTRIES or 'EU27' in country_code,
        'indicators': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Fetch each indicator
    for indicator_key in indicators:
        if indicator_key not in EUROSTAT_INDICATORS:
            continue
        
        indicator_data = get_indicator_data(country_code, indicator_key, last_n_periods=periods)
        
        if indicator_data['success']:
            profile['indicators'][indicator_key] = {
                'name': indicator_data['indicator'],
                'latest_value': indicator_data['latest_value'],
                'latest_period': indicator_data['latest_period'],
                'period_change': indicator_data['period_change'],
                'period_change_pct': indicator_data['period_change_pct'],
                'history': indicator_data['data_points'][:10]  # Last 10 periods
            }
        else:
            profile['indicators'][indicator_key] = {
                'name': EUROSTAT_INDICATORS[indicator_key]['name'],
                'latest_value': None,
                'note': 'Data not available'
            }
        
        # Rate limiting - be nice to Eurostat API
        time.sleep(0.2)
    
    return profile


def compare_countries(country_codes: List[str], indicator_key: str = 'GDP') -> Dict:
    """
    Compare indicator across multiple EU countries
    
    Args:
        country_codes: List of EU country codes
        indicator_key: Indicator key from EUROSTAT_INDICATORS
    
    Returns:
        Dictionary with comparison data
    """
    if indicator_key not in EUROSTAT_INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator_key}'
        }
    
    indicator_config = EUROSTAT_INDICATORS[indicator_key]
    
    comparison = {
        'success': True,
        'indicator': indicator_config['name'],
        'indicator_key': indicator_key,
        'countries': []
    }
    
    for country_code in country_codes:
        indicator_data = get_indicator_data(country_code, indicator_key, last_n_periods=5)
        
        if indicator_data['success']:
            comparison['countries'].append({
                'country': indicator_data['country'],
                'country_code': country_code,
                'value': indicator_data['latest_value'],
                'period': indicator_data['latest_period'],
                'period_change_pct': indicator_data['period_change_pct']
            })
        
        time.sleep(0.2)  # Rate limiting
    
    # Sort by value descending
    comparison['countries'].sort(key=lambda x: x['value'] if x['value'] else 0, reverse=True)
    
    return comparison


def get_eu27_aggregate(indicator_key: str = 'GDP', periods: int = 20) -> Dict:
    """
    Get EU-27 aggregate data for an indicator
    
    Args:
        indicator_key: Indicator key from EUROSTAT_INDICATORS
        periods: Number of historical periods
    
    Returns:
        Dictionary with EU-27 aggregate data
    """
    # Eurostat uses 'EU27_2020' for EU-27 aggregate (post-Brexit)
    return get_indicator_data('EU27_2020', indicator_key, last_n_periods=periods)


def search_countries(query: str) -> Dict:
    """
    Search for countries by name
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with matching countries
    """
    query_lower = query.lower()
    matches = []
    
    for code, name in ALL_COUNTRIES.items():
        if query_lower in name.lower() or query_lower in code.lower():
            matches.append({
                'code': code,
                'name': name,
                'is_eu27': code in EU27_COUNTRIES
            })
    
    return {
        'success': True,
        'query': query,
        'matches': matches,
        'count': len(matches)
    }


def list_countries(eu27_only: bool = False) -> Dict:
    """
    List all available countries
    
    Args:
        eu27_only: If True, only return EU-27 countries
    
    Returns:
        Dictionary with country list
    """
    if eu27_only:
        countries = [{'code': code, 'name': name, 'is_eu27': True} 
                    for code, name in EU27_COUNTRIES.items()]
    else:
        countries = [{'code': code, 'name': name, 'is_eu27': code in EU27_COUNTRIES} 
                    for code, name in ALL_COUNTRIES.items()]
    
    return {
        'success': True,
        'countries': countries,
        'count': len(countries)
    }


def list_indicators() -> Dict:
    """
    List all available indicators
    
    Returns:
        Dictionary with indicator list
    """
    indicators = []
    for key, config in EUROSTAT_INDICATORS.items():
        indicators.append({
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'dataflow': config['dataflow']
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
        if command == 'eu-country-profile':
            if len(sys.argv) < 3:
                print("Error: eu-country-profile requires a country code", file=sys.stderr)
                print("Usage: python eurostat.py eu-country-profile <COUNTRY_CODE> [--indicators GDP,INFLATION]", file=sys.stderr)
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
        
        elif command == 'eu-countries':
            eu27_only = '--eu27' in sys.argv
            data = list_countries(eu27_only=eu27_only)
            print(json.dumps(data, indent=2))
        
        elif command == 'eu-indicator':
            if len(sys.argv) < 4:
                print("Error: eu-indicator requires country code and indicator key", file=sys.stderr)
                print("Usage: python eurostat.py eu-indicator <COUNTRY_CODE> <INDICATOR_KEY>", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            indicator_key = sys.argv[3].upper()
            
            if indicator_key not in EUROSTAT_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(EUROSTAT_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            data = get_indicator_data(country_code, indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'eu-compare':
            if len(sys.argv) < 3:
                print("Error: eu-compare requires country codes", file=sys.stderr)
                print("Usage: python eurostat.py eu-compare <CODE1,CODE2,CODE3> [--indicator GDP]", file=sys.stderr)
                return 1
            
            country_codes = sys.argv[2].upper().split(',')
            
            indicator_key = 'GDP'
            if '--indicator' in sys.argv:
                idx = sys.argv.index('--indicator')
                if idx + 1 < len(sys.argv):
                    indicator_key = sys.argv[idx + 1].upper()
            
            data = compare_countries(country_codes, indicator_key=indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'eu27-aggregate':
            indicator_key = 'GDP'
            if len(sys.argv) >= 3:
                indicator_key = sys.argv[2].upper()
            
            if indicator_key not in EUROSTAT_INDICATORS:
                print(f"Error: Unknown indicator '{indicator_key}'", file=sys.stderr)
                print(f"Available indicators: {', '.join(EUROSTAT_INDICATORS.keys())}", file=sys.stderr)
                return 1
            
            data = get_eu27_aggregate(indicator_key=indicator_key)
            print(json.dumps(data, indent=2))
        
        elif command == 'eu-search':
            if len(sys.argv) < 3:
                print("Error: eu-search requires a query", file=sys.stderr)
                print("Usage: python eurostat.py eu-search <QUERY>", file=sys.stderr)
                return 1
            
            query = ' '.join(sys.argv[2:])
            data = search_countries(query)
            print(json.dumps(data, indent=2))
        
        elif command == 'eu-indicators':
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
Eurostat EU Statistics Module (Phase 99)

Commands:
  python eurostat.py eu-country-profile <CODE> [--indicators GDP,INFLATION]
                                      # Comprehensive country economic profile
  
  python eurostat.py eu-countries [--eu27]
                                      # List all countries (--eu27 for EU-27 only)
  
  python eurostat.py eu-indicator <CODE> <INDICATOR>
                                      # Get specific indicator for a country
  
  python eurostat.py eu-compare <CODE1,CODE2,CODE3> [--indicator GDP]
                                      # Compare countries on specific indicator
  
  python eurostat.py eu27-aggregate [INDICATOR]  # EU-27 aggregate data
  
  python eurostat.py eu-search <QUERY>   # Search for countries by name
  
  python eurostat.py eu-indicators       # List all available indicators

Examples:
  python eurostat.py eu-country-profile DE
  python eurostat.py eu-country-profile FR --indicators GDP,INFLATION,UNEMPLOYMENT
  python eurostat.py eu-countries --eu27
  python eurostat.py eu-indicator DE GDP
  python eurostat.py eu-indicator IT UNEMPLOYMENT
  python eurostat.py eu-compare DE,FR,IT,ES,NL --indicator INFLATION
  python eurostat.py eu27-aggregate GDP_GROWTH
  python eurostat.py eu-search "Germany"
  python eurostat.py eu-indicators

Country Codes (EU-27):
  AT=Austria, BE=Belgium, BG=Bulgaria, HR=Croatia, CY=Cyprus, CZ=Czech Republic,
  DK=Denmark, EE=Estonia, FI=Finland, FR=France, DE=Germany, EL=Greece,
  HU=Hungary, IE=Ireland, IT=Italy, LV=Latvia, LT=Lithuania, LU=Luxembourg,
  MT=Malta, NL=Netherlands, PL=Poland, PT=Portugal, RO=Romania, SK=Slovakia,
  SI=Slovenia, ES=Spain, SE=Sweden

Additional Countries:
  UK=United Kingdom, NO=Norway, CH=Switzerland, IS=Iceland, TR=Turkey, etc.

Indicators:
  GDP                     = GDP (current prices, million EUR)
  GDP_GROWTH              = GDP growth rate (%, previous period)
  HICP                    = Harmonized Index of Consumer Prices
  INFLATION               = HICP Inflation Rate (% year-on-year)
  UNEMPLOYMENT            = Unemployment rate (%, seasonally adjusted)
  INDUSTRIAL_PRODUCTION   = Industrial production index
  TRADE_BALANCE           = Trade balance (million EUR)
  GOVERNMENT_DEBT         = Government debt (% of GDP)

Data Source: https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1
Protocol: SDMX (Statistical Data and Metadata eXchange)
Coverage: EU-27 + European countries
Refresh: Weekly
""")


if __name__ == "__main__":
    sys.exit(main())
