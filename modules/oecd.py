#!/usr/bin/env python3
"""
OECD Leading Indicators Module — Phase 102

Composite economic indicators for 38 OECD countries via OECD.Stat API
- Composite Leading Indicators (CLI)
- Housing Price Index (Real & Nominal)
- Labour Productivity (per hour worked)
- Monthly/Quarterly frequency

Data Source: stats.oecd.org/sdmx-json
Refresh: Monthly
Coverage: 38 OECD countries + major non-members

Author: QUANTCLAW DATA Build Agent
Phase: 102
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# OECD.Stat API Configuration
OECD_BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"

# Dataset identifiers
DATASETS = {
    'CLI': {
        'id': 'MEI_CLI',
        'name': 'Composite Leading Indicators',
        'description': 'CLI designed to provide early signals of turning points in economic activity',
        'frequency': 'monthly',
        'measures': {
            'AMPLITUDE': 'Amplitude adjusted (CLI)',
            'AMPLNORM': 'Normalised (CLI)',
            'TREND': 'Trend restored (CLI)'
        }
    },
    'HOUSING': {
        'id': 'HOUSE_PRICES',
        'name': 'Housing Prices',
        'description': 'Real and nominal residential property prices',
        'frequency': 'quarterly',
        'measures': {
            'REAL': 'Real house price index',
            'NOMINAL': 'Nominal house price index'
        }
    },
    'PRODUCTIVITY': {
        'id': 'PDB_LV',
        'name': 'Labour Productivity',
        'description': 'GDP per hour worked',
        'frequency': 'annual',
        'measures': {
            'T_GDPHRS': 'GDP per hour worked'
        }
    }
}

# OECD Country Codes (38 members + key non-members)
OECD_COUNTRIES = {
    'AUS': 'Australia',
    'AUT': 'Austria',
    'BEL': 'Belgium',
    'CAN': 'Canada',
    'CHL': 'Chile',
    'COL': 'Colombia',
    'CRI': 'Costa Rica',
    'CZE': 'Czech Republic',
    'DNK': 'Denmark',
    'EST': 'Estonia',
    'FIN': 'Finland',
    'FRA': 'France',
    'DEU': 'Germany',
    'GRC': 'Greece',
    'HUN': 'Hungary',
    'ISL': 'Iceland',
    'IRL': 'Ireland',
    'ISR': 'Israel',
    'ITA': 'Italy',
    'JPN': 'Japan',
    'KOR': 'South Korea',
    'LVA': 'Latvia',
    'LTU': 'Lithuania',
    'LUX': 'Luxembourg',
    'MEX': 'Mexico',
    'NLD': 'Netherlands',
    'NZL': 'New Zealand',
    'NOR': 'Norway',
    'POL': 'Poland',
    'PRT': 'Portugal',
    'SVK': 'Slovakia',
    'SVN': 'Slovenia',
    'ESP': 'Spain',
    'SWE': 'Sweden',
    'CHE': 'Switzerland',
    'TUR': 'Turkey',
    'GBR': 'United Kingdom',
    'USA': 'United States',
    # Key non-members
    'CHN': 'China',
    'IND': 'India',
    'BRA': 'Brazil',
    'RUS': 'Russia',
    'ZAF': 'South Africa',
    'IDN': 'Indonesia',
    'ARG': 'Argentina'
}


def oecd_request(dataset: str, filters: str = "", params: Dict = None) -> Dict:
    """
    Make request to OECD.Stat SDMX-JSON API
    
    Args:
        dataset: Dataset identifier (e.g., 'MEI_CLI')
        filters: SDMX filter string (e.g., 'USA.AMPLNORM.M')
        params: Additional query parameters
    
    Returns:
        Parsed JSON response with proper error handling
    """
    if params is None:
        params = {}
    
    try:
        # Build URL: /dataset/filters?params
        url = f"{OECD_BASE_URL}/{dataset}/{filters}"
        
        # Add standard params
        params.setdefault('dimensionAtObservation', 'AllDimensions')
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'url': response.url
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'url': url if 'url' in locals() else None
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Invalid JSON response: {str(e)}'
        }


def parse_sdmx_observations(sdmx_data: Dict) -> List[Dict]:
    """
    Parse OECD SDMX-JSON format into flat observation list
    
    SDMX-JSON structure:
    - dataSets[0].observations: {index_key: [value, status]}
    - structure.dimensions.observation: dimension definitions with positions
    
    Returns:
        List of {date, value, country, measure, ...} dicts
    """
    try:
        structure = sdmx_data.get('structure', {})
        datasets = sdmx_data.get('dataSets', [])
        
        if not datasets:
            return []
        
        observations = datasets[0].get('observations', {})
        
        # Get dimension definitions
        dimensions = structure.get('dimensions', {}).get('observation', [])
        dim_map = {dim['id']: dim for dim in dimensions}
        
        # Parse each observation
        results = []
        for obs_key, obs_values in observations.items():
            # obs_key is like "0:0:0:0" mapping to dimension value positions
            indices = obs_key.split(':')
            
            # Map indices to dimension values
            obs_data = {}
            for i, dim in enumerate(dimensions):
                if i < len(indices):
                    pos = int(indices[i])
                    dim_id = dim['id']
                    dim_values = dim.get('values', [])
                    
                    if pos < len(dim_values):
                        obs_data[dim_id] = dim_values[pos].get('id', '')
                        obs_data[f"{dim_id}_name"] = dim_values[pos].get('name', '')
            
            # Add observation value
            if isinstance(obs_values, list) and len(obs_values) > 0:
                obs_data['value'] = obs_values[0]
                obs_data['status'] = obs_values[1] if len(obs_values) > 1 else None
            
            results.append(obs_data)
        
        return results
    
    except Exception as e:
        print(f"Error parsing SDMX: {str(e)}", file=sys.stderr)
        return []


def get_cli(country: str = 'USA', measure: str = 'AMPLITUDE', months: int = 24) -> Dict:
    """
    Get Composite Leading Indicator for a country
    
    Args:
        country: ISO 3-letter country code (default USA)
        measure: AMPLITUDE, AMPLNORM, or TREND
        months: Number of months to fetch (default 24)
    
    Returns:
        Dict with CLI data and metadata
    """
    if country not in OECD_COUNTRIES:
        return {
            'success': False,
            'error': f'Invalid country code. Must be one of {list(OECD_COUNTRIES.keys())}'
        }
    
    # Build filter: LOCATION.MEASURE.FREQUENCY
    filters = f"{country}.{measure}.M"  # M = Monthly
    
    params = {
        'startTime': (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m'),
        'endTime': datetime.now().strftime('%Y-%m')
    }
    
    response = oecd_request('MEI_CLI', filters, params)
    
    if not response['success']:
        return response
    
    # Parse SDMX observations
    observations = parse_sdmx_observations(response['data'])
    
    # Sort by time period
    observations.sort(key=lambda x: x.get('TIME_PERIOD', ''), reverse=True)
    
    # Calculate trend
    values = [float(obs['value']) for obs in observations if 'value' in obs]
    latest_value = values[0] if values else None
    previous_value = values[1] if len(values) > 1 else None
    
    change = None
    if latest_value and previous_value:
        change = latest_value - previous_value
        pct_change = (change / previous_value) * 100
    else:
        pct_change = None
    
    return {
        'success': True,
        'country': OECD_COUNTRIES[country],
        'country_code': country,
        'measure': measure,
        'latest_value': latest_value,
        'previous_value': previous_value,
        'month_change': change,
        'month_change_pct': pct_change,
        'observations': observations[:months],
        'data_points': len(observations),
        'source': 'OECD.Stat MEI_CLI',
        'url': response['url']
    }


def get_housing_prices(country: str = 'USA', measure: str = 'REAL', quarters: int = 20) -> Dict:
    """
    Get Housing Price Index for a country
    
    Args:
        country: ISO 3-letter country code (default USA)
        measure: REAL or NOMINAL
        quarters: Number of quarters to fetch (default 20 = 5 years)
    
    Returns:
        Dict with housing price data and trends
    """
    if country not in OECD_COUNTRIES:
        return {
            'success': False,
            'error': f'Invalid country code. Must be one of {list(OECD_COUNTRIES.keys())}'
        }
    
    # Build filter: LOCATION.MEASURE.FREQUENCY
    filters = f"{country}+OECD.{measure}.Q"  # Q = Quarterly
    
    params = {
        'startTime': (datetime.now() - timedelta(days=quarters*90)).strftime('%Y-Q1'),
        'endTime': datetime.now().strftime('%Y-Q4')
    }
    
    response = oecd_request('HOUSE_PRICES', filters, params)
    
    if not response['success']:
        return response
    
    # Parse SDMX observations
    observations = parse_sdmx_observations(response['data'])
    
    # Filter by country (in case OECD aggregate is included)
    observations = [obs for obs in observations if obs.get('LOCATION') == country]
    
    # Sort by time period
    observations.sort(key=lambda x: x.get('TIME_PERIOD', ''), reverse=True)
    
    # Calculate trends
    values = [float(obs['value']) for obs in observations if 'value' in obs]
    
    if len(values) >= 2:
        latest = values[0]
        previous_quarter = values[1]
        yoy = values[4] if len(values) > 4 else None
        
        qoq_change = ((latest - previous_quarter) / previous_quarter) * 100
        yoy_change = ((latest - yoy) / yoy) * 100 if yoy else None
    else:
        latest = values[0] if values else None
        qoq_change = None
        yoy_change = None
    
    return {
        'success': True,
        'country': OECD_COUNTRIES[country],
        'country_code': country,
        'measure': f"{measure.title()} House Price Index",
        'latest_value': latest,
        'quarter_over_quarter_pct': qoq_change,
        'year_over_year_pct': yoy_change,
        'observations': observations[:quarters],
        'data_points': len(observations),
        'source': 'OECD.Stat HOUSE_PRICES',
        'url': response['url']
    }


def get_productivity(country: str = 'USA', years: int = 10) -> Dict:
    """
    Get Labour Productivity (GDP per hour worked) for a country
    
    Args:
        country: ISO 3-letter country code (default USA)
        years: Number of years to fetch (default 10)
    
    Returns:
        Dict with productivity data and growth rates
    """
    if country not in OECD_COUNTRIES:
        return {
            'success': False,
            'error': f'Invalid country code. Must be one of {list(OECD_COUNTRIES.keys())}'
        }
    
    # Build filter: LOCATION.SUBJECT.MEASURE
    # T_GDPHRS = GDP per hour worked
    filters = f"{country}.T_GDPHRS.IXOB"  # IXOB = Index
    
    params = {
        'startTime': str(datetime.now().year - years),
        'endTime': str(datetime.now().year)
    }
    
    response = oecd_request('PDB_LV', filters, params)
    
    if not response['success']:
        return response
    
    # Parse SDMX observations
    observations = parse_sdmx_observations(response['data'])
    
    # Sort by year
    observations.sort(key=lambda x: x.get('TIME_PERIOD', ''), reverse=True)
    
    # Calculate growth rates
    values = [float(obs['value']) for obs in observations if 'value' in obs]
    
    if len(values) >= 2:
        latest = values[0]
        previous_year = values[1]
        
        annual_growth = ((latest - previous_year) / previous_year) * 100
        
        # Calculate CAGR over full period
        oldest = values[-1]
        n_years = len(values) - 1
        cagr = (((latest / oldest) ** (1 / n_years)) - 1) * 100 if n_years > 0 else None
    else:
        latest = values[0] if values else None
        annual_growth = None
        cagr = None
    
    return {
        'success': True,
        'country': OECD_COUNTRIES[country],
        'country_code': country,
        'measure': 'GDP per hour worked (Index)',
        'latest_value': latest,
        'annual_growth_pct': annual_growth,
        'cagr_pct': cagr,
        'observations': observations[:years],
        'data_points': len(observations),
        'source': 'OECD.Stat PDB_LV',
        'url': response['url']
    }


def compare_countries(indicator: str = 'CLI', countries: List[str] = None, measure: str = None) -> Dict:
    """
    Compare an indicator across multiple countries
    
    Args:
        indicator: CLI, HOUSING, or PRODUCTIVITY
        countries: List of country codes (default: G7)
        measure: Optional specific measure (depends on indicator)
    
    Returns:
        Dict with comparative analysis
    """
    if countries is None:
        # Default to G7
        countries = ['USA', 'CAN', 'GBR', 'DEU', 'FRA', 'ITA', 'JPN']
    
    # Validate countries
    invalid = [c for c in countries if c not in OECD_COUNTRIES]
    if invalid:
        return {
            'success': False,
            'error': f'Invalid country codes: {invalid}'
        }
    
    # Fetch data for each country
    results = []
    errors = []
    
    for country in countries:
        try:
            if indicator == 'CLI':
                measure = measure or 'AMPLITUDE'
                data = get_cli(country, measure, months=12)
            elif indicator == 'HOUSING':
                measure = measure or 'REAL'
                data = get_housing_prices(country, measure, quarters=8)
            elif indicator == 'PRODUCTIVITY':
                data = get_productivity(country, years=5)
            else:
                return {
                    'success': False,
                    'error': f'Invalid indicator: {indicator}. Must be CLI, HOUSING, or PRODUCTIVITY'
                }
            
            if data['success']:
                results.append({
                    'country': data['country'],
                    'country_code': data['country_code'],
                    'latest_value': data['latest_value'],
                    'change_pct': data.get('month_change_pct') or data.get('quarter_over_quarter_pct') or data.get('annual_growth_pct')
                })
            else:
                errors.append(f"{country}: {data.get('error', 'Unknown error')}")
        
        except Exception as e:
            errors.append(f"{country}: {str(e)}")
    
    # Sort by latest value
    results.sort(key=lambda x: x['latest_value'] or 0, reverse=True)
    
    return {
        'success': True,
        'indicator': indicator,
        'measure': measure,
        'countries_compared': len(results),
        'rankings': results,
        'errors': errors if errors else None,
        'timestamp': datetime.now().isoformat()
    }


def get_oecd_snapshot(country: str = 'USA') -> Dict:
    """
    Get comprehensive economic snapshot for a country (all indicators)
    
    Args:
        country: ISO 3-letter country code
    
    Returns:
        Dict with CLI, housing, and productivity data
    """
    if country not in OECD_COUNTRIES:
        return {
            'success': False,
            'error': f'Invalid country code. Must be one of {list(OECD_COUNTRIES.keys())}'
        }
    
    # Fetch all indicators
    cli = get_cli(country, 'AMPLITUDE', months=12)
    housing = get_housing_prices(country, 'REAL', quarters=8)
    productivity = get_productivity(country, years=5)
    
    return {
        'success': True,
        'country': OECD_COUNTRIES[country],
        'country_code': country,
        'timestamp': datetime.now().isoformat(),
        'indicators': {
            'composite_leading_indicator': {
                'value': cli.get('latest_value'),
                'change_pct': cli.get('month_change_pct'),
                'trend': 'expanding' if (cli.get('month_change_pct') or 0) > 0 else 'contracting',
                'success': cli['success'],
                'error': cli.get('error')
            },
            'housing_prices': {
                'value': housing.get('latest_value'),
                'qoq_pct': housing.get('quarter_over_quarter_pct'),
                'yoy_pct': housing.get('year_over_year_pct'),
                'success': housing['success'],
                'error': housing.get('error')
            },
            'productivity': {
                'value': productivity.get('latest_value'),
                'growth_pct': productivity.get('annual_growth_pct'),
                'cagr_pct': productivity.get('cagr_pct'),
                'success': productivity['success'],
                'error': productivity.get('error')
            }
        }
    }


def cli_main():
    """CLI interface for OECD module"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OECD Leading Indicators')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # oecd cli
    cli_parser = subparsers.add_parser('cli', help='Get Composite Leading Indicator')
    cli_parser.add_argument('country', nargs='?', default='USA', help='Country code (default: USA)')
    cli_parser.add_argument('--measure', default='AMPLITUDE', choices=['AMPLITUDE', 'AMPLNORM', 'TREND'])
    cli_parser.add_argument('--months', type=int, default=24, help='Number of months (default: 24)')
    
    # oecd housing
    housing_parser = subparsers.add_parser('housing', help='Get Housing Price Index')
    housing_parser.add_argument('country', nargs='?', default='USA', help='Country code (default: USA)')
    housing_parser.add_argument('--measure', default='REAL', choices=['REAL', 'NOMINAL'])
    housing_parser.add_argument('--quarters', type=int, default=20, help='Number of quarters (default: 20)')
    
    # oecd productivity
    prod_parser = subparsers.add_parser('productivity', help='Get Labour Productivity')
    prod_parser.add_argument('country', nargs='?', default='USA', help='Country code (default: USA)')
    prod_parser.add_argument('--years', type=int, default=10, help='Number of years (default: 10)')
    
    # oecd compare
    compare_parser = subparsers.add_parser('compare', help='Compare countries')
    compare_parser.add_argument('indicator', choices=['CLI', 'HOUSING', 'PRODUCTIVITY'])
    compare_parser.add_argument('--countries', nargs='+', help='Country codes (default: G7)')
    compare_parser.add_argument('--measure', help='Specific measure to compare')
    
    # oecd snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='Get comprehensive snapshot')
    snapshot_parser.add_argument('country', nargs='?', default='USA', help='Country code (default: USA)')
    
    # oecd countries
    subparsers.add_parser('countries', help='List all OECD countries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'cli':
        result = get_cli(args.country.upper(), args.measure, args.months)
    elif args.command == 'housing':
        result = get_housing_prices(args.country.upper(), args.measure, args.quarters)
    elif args.command == 'productivity':
        result = get_productivity(args.country.upper(), args.years)
    elif args.command == 'compare':
        countries = [c.upper() for c in args.countries] if args.countries else None
        result = compare_countries(args.indicator, countries, args.measure)
    elif args.command == 'snapshot':
        result = get_oecd_snapshot(args.country.upper())
    elif args.command == 'countries':
        print("\nOECD Countries (38 members + key non-members):\n")
        for code, name in sorted(OECD_COUNTRIES.items()):
            print(f"  {code:3s} - {name}")
        return
    
    # Print result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    cli_main()
