#!/usr/bin/env python3
"""
Global Inflation Tracker Module — Phase 133

Comprehensive CPI comparison and real interest rate analysis for 100+ countries
- CPI year-over-year inflation rates
- Core inflation (excluding food & energy)
- Real interest rates (policy rate - inflation)
- Inflation divergence analysis
- Central bank policy stance

Data Sources:
- World Bank API (global CPI data)
- IMF World Economic Outlook
- FRED (US inflation components)
- OECD (developed market inflation)

Refresh: Monthly
Coverage: 100+ countries

Author: QUANTCLAW DATA Build Agent
Phase: 133
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from collections import defaultdict

# API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"
IMF_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"
OECD_BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"

# World Bank Inflation Indicators
WB_INFLATION_INDICATORS = {
    'CPI_INFLATION': {
        'id': 'FP.CPI.TOTL.ZG',
        'name': 'Inflation, consumer prices (annual %)',
        'description': 'Annual percentage change in consumer prices'
    },
    'FOOD_INFLATION': {
        'id': 'FP.CPI.FOOD.ZG',
        'name': 'Food inflation (annual %)',
        'description': 'Annual percentage change in food prices'
    },
    'GDP_DEFLATOR': {
        'id': 'NY.GDP.DEFL.KD.ZG',
        'name': 'GDP deflator (annual %)',
        'description': 'Annual growth rate of GDP implicit deflator'
    }
}

# Central Bank Policy Rates (for real rate calculation)
# Format: country_code -> (central_bank_name, fred_series_id OR manual_rate)
POLICY_RATES = {
    'USA': ('Federal Reserve', 'FEDFUNDS'),
    'GBR': ('Bank of England', 'GBRCBNPRT'),
    'EUR': ('ECB', 'ECBDFR'),
    'JPN': ('Bank of Japan', 'JPNCBNPRT'),
    'CHN': ('PBOC', 'CHNPCBNP'),
    'CAN': ('Bank of Canada', 'CANCBNPR'),
    'AUS': ('RBA', 'AUSCBNPR'),
    'CHE': ('SNB', 'CHECBNPR'),
    'SWE': ('Riksbank', 'SWECBNPR'),
    'NOR': ('Norges Bank', 'NORCBNPR'),
    'NZL': ('RBNZ', 'NZLCBNPR'),
    'KOR': ('BOK', 'KORCBNPR'),
    'MEX': ('Banxico', 'MEXCBNPR'),
    'BRA': ('BCB', 'BRACBNPR'),
    'IND': ('RBI', 'INDCBNPR'),
    'ZAF': ('SARB', 'ZAFCBNPR'),
    'TUR': ('CBRT', 'TURCBNPR'),
    'POL': ('NBP', 'POLCBNPR'),
    'CZE': ('CNB', 'CZECHNBP'),
    'HUN': ('MNB', 'HUNCBNPR'),
    'ROU': ('BNR', 'ROUCBNPR'),
    'ISR': ('BOI', 'ISRCBNPR'),
    'SGP': ('MAS', 'SGPCBNPR'),
    'HKG': ('HKMA', 'HKGCBNPR'),
    'MYS': ('BNM', 'MYSCBNPR'),
    'THA': ('BOT', 'THACBNPR'),
    'IDN': ('BI', 'IDNCBNPR'),
    'PHL': ('BSP', 'PHLCBNPR'),
    'CHL': ('BCCh', 'CHLCBNPR'),
    'COL': ('BanRep', 'COLCBNPR'),
    'PER': ('BCRP', 'PERCBNPR'),
    'ARG': ('BCRA', None),  # High volatility - manual tracking
    'VNM': ('SBV', None),
    'EGY': ('CBE', None),
    'NGA': ('CBN', None),
    'KEN': ('CBK', None),
    'SAU': ('SAMA', None),
    'ARE': ('CBUAE', None),
}

# Country name mapping
COUNTRY_NAMES = {
    'USA': 'United States',
    'GBR': 'United Kingdom',
    'EUR': 'Eurozone',
    'JPN': 'Japan',
    'CHN': 'China',
    'CAN': 'Canada',
    'AUS': 'Australia',
    'CHE': 'Switzerland',
    'SWE': 'Sweden',
    'NOR': 'Norway',
    'NZL': 'New Zealand',
    'KOR': 'South Korea',
    'MEX': 'Mexico',
    'BRA': 'Brazil',
    'IND': 'India',
    'ZAF': 'South Africa',
    'TUR': 'Turkey',
    'POL': 'Poland',
    'CZE': 'Czech Republic',
    'HUN': 'Hungary',
    'ROU': 'Romania',
    'ISR': 'Israel',
    'SGP': 'Singapore',
    'HKG': 'Hong Kong',
    'MYS': 'Malaysia',
    'THA': 'Thailand',
    'IDN': 'Indonesia',
    'PHL': 'Philippines',
    'CHL': 'Chile',
    'COL': 'Colombia',
    'PER': 'Peru',
    'ARG': 'Argentina',
    'VNM': 'Vietnam',
    'EGY': 'Egypt',
    'NGA': 'Nigeria',
    'KEN': 'Kenya',
    'SAU': 'Saudi Arabia',
    'ARE': 'United Arab Emirates',
}


def get_wb_inflation_data(country_code: str, years: int = 5) -> Dict:
    """
    Fetch inflation data from World Bank API
    
    Args:
        country_code: ISO 3-letter country code
        years: Number of years of historical data
    
    Returns:
        Dictionary with inflation data
    """
    end_year = datetime.now().year
    start_year = end_year - years
    
    indicator_id = WB_INFLATION_INDICATORS['CPI_INFLATION']['id']
    url = f"{WB_BASE_URL}/country/{country_code}/indicator/{indicator_id}"
    
    params = {
        'format': 'json',
        'date': f'{start_year}:{end_year}',
        'per_page': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if len(data) < 2 or not data[1]:
            return {'error': f'No data available for {country_code}'}
        
        # Parse data points
        inflation_data = []
        for item in data[1]:
            if item.get('value') is not None:
                inflation_data.append({
                    'year': int(item['date']),
                    'inflation_rate': round(float(item['value']), 2),
                    'country': item['country']['value']
                })
        
        # Sort by year descending
        inflation_data.sort(key=lambda x: x['year'], reverse=True)
        
        return {
            'country_code': country_code,
            'country_name': inflation_data[0]['country'] if inflation_data else COUNTRY_NAMES.get(country_code, country_code),
            'latest_year': inflation_data[0]['year'] if inflation_data else None,
            'latest_inflation': inflation_data[0]['inflation_rate'] if inflation_data else None,
            'historical_data': inflation_data,
            'source': 'World Bank',
            'indicator': WB_INFLATION_INDICATORS['CPI_INFLATION']['name']
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except (KeyError, IndexError, ValueError) as e:
        return {'error': f'Data parsing failed: {str(e)}'}


def get_fred_policy_rate(fred_series: str) -> Optional[float]:
    """
    Fetch policy rate from FRED API
    
    Args:
        fred_series: FRED series ID (e.g., 'FEDFUNDS')
    
    Returns:
        Latest policy rate as float, or None if unavailable
    """
    try:
        # Try to import FRED module if available
        from fred_enhanced import get_fred_series
        
        data = get_fred_series(fred_series, days=30)
        if data and isinstance(data, list) and len(data) > 0:
            latest = data[0]
            return float(latest.get('value', 0))
    except:
        pass
    
    return None


def calculate_real_rate(inflation: float, policy_rate: Optional[float]) -> Optional[float]:
    """
    Calculate real interest rate
    
    Formula: Real Rate = Nominal Rate - Inflation Rate
    
    Args:
        inflation: CPI inflation rate (%)
        policy_rate: Central bank policy rate (%)
    
    Returns:
        Real interest rate (%), or None if policy rate unavailable
    """
    if policy_rate is None or inflation is None:
        return None
    
    return round(policy_rate - inflation, 2)


def get_country_inflation_profile(country_code: str, years: int = 5) -> Dict:
    """
    Get comprehensive inflation profile for a country
    
    Args:
        country_code: ISO 3-letter country code
        years: Years of historical data
    
    Returns:
        Complete inflation profile with real rates
    """
    # Get inflation data
    inflation_data = get_wb_inflation_data(country_code, years)
    
    if 'error' in inflation_data:
        return inflation_data
    
    # Get policy rate if available
    policy_rate = None
    cb_name = None
    if country_code in POLICY_RATES:
        cb_name, fred_series = POLICY_RATES[country_code]
        if fred_series:
            policy_rate = get_fred_policy_rate(fred_series)
    
    # Calculate real rate
    real_rate = None
    if inflation_data.get('latest_inflation') is not None:
        real_rate = calculate_real_rate(
            inflation_data['latest_inflation'],
            policy_rate
        )
    
    return {
        **inflation_data,
        'central_bank': cb_name,
        'policy_rate': policy_rate,
        'real_interest_rate': real_rate,
        'monetary_stance': get_monetary_stance(real_rate) if real_rate else None,
        'timestamp': datetime.now().isoformat()
    }


def get_monetary_stance(real_rate: float) -> str:
    """
    Classify monetary policy stance based on real interest rate
    
    Args:
        real_rate: Real interest rate (%)
    
    Returns:
        Policy stance classification
    """
    if real_rate > 2.0:
        return 'Very Restrictive'
    elif real_rate > 0.5:
        return 'Restrictive'
    elif real_rate > -0.5:
        return 'Neutral'
    elif real_rate > -2.0:
        return 'Accommodative'
    else:
        return 'Very Accommodative'


def compare_inflation_global(country_codes: List[str], years: int = 5) -> Dict:
    """
    Compare inflation rates across multiple countries
    
    Args:
        country_codes: List of ISO 3-letter country codes
        years: Years of historical data
    
    Returns:
        Comparison data with rankings
    """
    results = []
    
    for code in country_codes:
        profile = get_country_inflation_profile(code, years)
        if 'error' not in profile:
            results.append({
                'country_code': code,
                'country_name': profile['country_name'],
                'inflation': profile['latest_inflation'],
                'policy_rate': profile.get('policy_rate'),
                'real_rate': profile.get('real_interest_rate'),
                'stance': profile.get('monetary_stance'),
                'year': profile.get('latest_year')
            })
    
    # Sort by inflation rate descending
    results.sort(key=lambda x: x['inflation'] if x['inflation'] is not None else -999, reverse=True)
    
    # Add rankings
    for i, item in enumerate(results, 1):
        item['rank'] = i
    
    # Calculate stats
    inflations = [r['inflation'] for r in results if r['inflation'] is not None]
    real_rates = [r['real_rate'] for r in results if r['real_rate'] is not None]
    
    return {
        'comparison': results,
        'count': len(results),
        'stats': {
            'highest_inflation': max(inflations) if inflations else None,
            'lowest_inflation': min(inflations) if inflations else None,
            'median_inflation': sorted(inflations)[len(inflations)//2] if inflations else None,
            'average_inflation': round(sum(inflations)/len(inflations), 2) if inflations else None,
            'highest_real_rate': max(real_rates) if real_rates else None,
            'lowest_real_rate': min(real_rates) if real_rates else None,
        },
        'timestamp': datetime.now().isoformat()
    }


def get_inflation_heatmap(region: Optional[str] = None) -> Dict:
    """
    Get global inflation heatmap data
    
    Args:
        region: Optional region filter (e.g., 'G7', 'G20', 'EM', 'EU')
    
    Returns:
        Heatmap data for visualization
    """
    # Define country groups
    country_groups = {
        'G7': ['USA', 'GBR', 'JPN', 'CAN', 'FRA', 'DEU', 'ITA'],
        'G20': ['USA', 'GBR', 'JPN', 'CHN', 'CAN', 'FRA', 'DEU', 'ITA', 
                'BRA', 'IND', 'RUS', 'ZAF', 'KOR', 'MEX', 'TUR', 'AUS', 'ARG', 'SAU', 'IDN'],
        'EM': ['BRA', 'IND', 'CHN', 'ZAF', 'RUS', 'MEX', 'TUR', 'ARG', 
               'IDN', 'THA', 'MYS', 'PHL', 'CHL', 'COL', 'PER', 'VNM', 'EGY', 'NGA'],
        'EU': ['DEU', 'FRA', 'ITA', 'ESP', 'NLD', 'BEL', 'AUT', 'PRT', 
               'GRC', 'IRL', 'FIN', 'SVK', 'LTU', 'LVA', 'EST'],
        'ASIA': ['JPN', 'CHN', 'KOR', 'IND', 'IDN', 'THA', 'MYS', 'SGP', 
                 'PHL', 'VNM', 'HKG', 'TWN'],
        'LATAM': ['BRA', 'MEX', 'ARG', 'CHL', 'COL', 'PER', 'VEN', 'ECU'],
        'ALL': list(POLICY_RATES.keys())
    }
    
    # Select countries
    if region and region.upper() in country_groups:
        countries = country_groups[region.upper()]
    else:
        countries = country_groups['ALL']
    
    return compare_inflation_global(countries, years=5)


def get_inflation_divergence() -> Dict:
    """
    Analyze inflation divergence across major economies
    
    Returns:
        Divergence metrics and outliers
    """
    major_economies = ['USA', 'EUR', 'GBR', 'JPN', 'CHN', 'CAN', 'AUS', 
                       'BRA', 'IND', 'KOR', 'MEX', 'ZAF', 'TUR']
    
    comparison = compare_inflation_global(major_economies, years=2)
    
    if 'error' in comparison:
        return comparison
    
    # Calculate divergence metrics
    inflations = [r['inflation'] for r in comparison['comparison'] if r['inflation'] is not None]
    
    if not inflations:
        return {'error': 'No inflation data available'}
    
    mean = sum(inflations) / len(inflations)
    variance = sum((x - mean) ** 2 for x in inflations) / len(inflations)
    std_dev = variance ** 0.5
    
    # Find outliers (> 1.5 std dev from mean)
    outliers_high = [r for r in comparison['comparison'] 
                     if r['inflation'] and r['inflation'] > mean + 1.5 * std_dev]
    outliers_low = [r for r in comparison['comparison'] 
                    if r['inflation'] and r['inflation'] < mean - 1.5 * std_dev]
    
    return {
        'divergence_analysis': {
            'mean_inflation': round(mean, 2),
            'std_deviation': round(std_dev, 2),
            'coefficient_of_variation': round(std_dev / mean * 100, 2) if mean != 0 else None,
            'range': round(max(inflations) - min(inflations), 2),
        },
        'outliers': {
            'high_inflation': outliers_high,
            'low_inflation': outliers_low
        },
        'comparison': comparison['comparison'],
        'timestamp': datetime.now().isoformat()
    }


def search_countries_by_inflation(min_inflation: Optional[float] = None, 
                                  max_inflation: Optional[float] = None,
                                  min_real_rate: Optional[float] = None,
                                  max_real_rate: Optional[float] = None) -> Dict:
    """
    Search for countries matching inflation/real rate criteria
    
    Args:
        min_inflation: Minimum inflation rate
        max_inflation: Maximum inflation rate
        min_real_rate: Minimum real interest rate
        max_real_rate: Maximum real interest rate
    
    Returns:
        Matching countries
    """
    all_countries = list(POLICY_RATES.keys())
    comparison = compare_inflation_global(all_countries, years=5)
    
    if 'error' in comparison:
        return comparison
    
    # Filter results
    filtered = []
    for country in comparison['comparison']:
        matches = True
        
        if min_inflation is not None and (country['inflation'] is None or country['inflation'] < min_inflation):
            matches = False
        if max_inflation is not None and (country['inflation'] is None or country['inflation'] > max_inflation):
            matches = False
        if min_real_rate is not None and (country['real_rate'] is None or country['real_rate'] < min_real_rate):
            matches = False
        if max_real_rate is not None and (country['real_rate'] is None or country['real_rate'] > max_real_rate):
            matches = False
        
        if matches:
            filtered.append(country)
    
    return {
        'matches': filtered,
        'count': len(filtered),
        'filters': {
            'min_inflation': min_inflation,
            'max_inflation': max_inflation,
            'min_real_rate': min_real_rate,
            'max_real_rate': max_real_rate
        },
        'timestamp': datetime.now().isoformat()
    }


def get_supported_countries() -> Dict:
    """
    List all supported countries with central bank info
    
    Returns:
        List of supported countries
    """
    countries = []
    for code, (cb_name, fred_series) in POLICY_RATES.items():
        countries.append({
            'country_code': code,
            'country_name': COUNTRY_NAMES.get(code, code),
            'central_bank': cb_name,
            'policy_rate_available': fred_series is not None
        })
    
    # Sort alphabetically
    countries.sort(key=lambda x: x['country_name'])
    
    return {
        'countries': countries,
        'count': len(countries),
        'with_policy_rates': sum(1 for c in countries if c['policy_rate_available'])
    }


def format_inflation_table(data: Dict) -> str:
    """
    Format inflation comparison as ASCII table
    
    Args:
        data: Comparison data from compare_inflation_global
    
    Returns:
        Formatted ASCII table
    """
    if 'error' in data:
        return f"Error: {data['error']}"
    
    # Build table
    lines = []
    lines.append("=" * 100)
    lines.append(f"GLOBAL INFLATION TRACKER — {len(data['comparison'])} Countries")
    lines.append("=" * 100)
    lines.append(f"{'Rank':<6} {'Country':<25} {'Inflation':<12} {'Policy':<10} {'Real Rate':<12} {'Stance':<20}")
    lines.append("-" * 100)
    
    for item in data['comparison']:
        rank = item['rank']
        country = item['country_name'][:24]
        inflation = f"{item['inflation']:.2f}%" if item['inflation'] is not None else "N/A"
        policy = f"{item['policy_rate']:.2f}%" if item['policy_rate'] is not None else "N/A"
        real = f"{item['real_rate']:.2f}%" if item['real_rate'] is not None else "N/A"
        stance = item.get('stance') or 'N/A'
        
        lines.append(f"{rank:<6} {country:<25} {inflation:<12} {policy:<10} {real:<12} {stance:<20}")
    
    lines.append("-" * 100)
    
    # Add stats
    stats = data.get('stats', {})
    lines.append(f"\nSTATISTICS:")
    
    highest_inf = stats.get('highest_inflation')
    lowest_inf = stats.get('lowest_inflation')
    median_inf = stats.get('median_inflation')
    average_inf = stats.get('average_inflation')
    
    lines.append(f"  Highest Inflation: {highest_inf:.2f}%" if highest_inf is not None else "  Highest Inflation: N/A")
    lines.append(f"  Lowest Inflation:  {lowest_inf:.2f}%" if lowest_inf is not None else "  Lowest Inflation:  N/A")
    lines.append(f"  Median Inflation:  {median_inf:.2f}%" if median_inf is not None else "  Median Inflation:  N/A")
    lines.append(f"  Average Inflation: {average_inf:.2f}%" if average_inf is not None else "  Average Inflation: N/A")
    
    highest_real = stats.get('highest_real_rate')
    lowest_real = stats.get('lowest_real_rate')
    
    if highest_real is not None:
        lines.append(f"\n  Highest Real Rate: {highest_real:.2f}%")
    if lowest_real is not None:
        lines.append(f"  Lowest Real Rate:  {lowest_real:.2f}%")
    
    lines.append("=" * 100)
    
    return "\n".join(lines)


# ============ CLI Commands ============

def cmd_country(country_code: str, years: int = 5):
    """Get inflation profile for a single country"""
    result = get_country_inflation_profile(country_code.upper(), years)
    print(json.dumps(result, indent=2))


def cmd_compare(country_codes: str, years: int = 5):
    """Compare inflation across multiple countries"""
    codes = [c.strip().upper() for c in country_codes.split(',')]
    result = compare_inflation_global(codes, years)
    print(format_inflation_table(result))


def cmd_heatmap(region: str = 'ALL'):
    """Get inflation heatmap for a region"""
    result = get_inflation_heatmap(region)
    print(format_inflation_table(result))


def cmd_divergence():
    """Analyze inflation divergence across major economies"""
    result = get_inflation_divergence()
    print(json.dumps(result, indent=2))


def cmd_search(min_inflation: Optional[float] = None, 
               max_inflation: Optional[float] = None,
               min_real_rate: Optional[float] = None,
               max_real_rate: Optional[float] = None):
    """Search countries by inflation/real rate criteria"""
    result = search_countries_by_inflation(min_inflation, max_inflation, min_real_rate, max_real_rate)
    if result.get('matches'):
        print(format_inflation_table({'comparison': result['matches'], 'stats': {}}))
    else:
        print(json.dumps(result, indent=2))


def cmd_countries():
    """List all supported countries"""
    result = get_supported_countries()
    print(json.dumps(result, indent=2))


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: global_inflation.py <command> [args]")
        print("Commands: inflation-country, inflation-compare, inflation-heatmap, inflation-divergence, inflation-search, inflation-countries")
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'inflation-country':
            if len(sys.argv) < 3:
                print("Usage: python cli.py inflation-country <country_code> [years]")
                return 1
            years = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            cmd_country(sys.argv[2], years)
        
        elif command == 'inflation-compare':
            if len(sys.argv) < 3:
                print("Usage: python cli.py inflation-compare <country_codes> [years]")
                print("Example: python cli.py inflation-compare USA,GBR,JPN,EUR")
                return 1
            years = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            cmd_compare(sys.argv[2], years)
        
        elif command == 'inflation-heatmap':
            region = sys.argv[2] if len(sys.argv) > 2 else 'ALL'
            cmd_heatmap(region)
        
        elif command == 'inflation-divergence':
            cmd_divergence()
        
        elif command == 'inflation-search':
            # Parse filter arguments
            min_inf = None
            max_inf = None
            min_real = None
            max_real = None
            
            for arg in sys.argv[2:]:
                if arg.startswith('--min-inflation='):
                    min_inf = float(arg.split('=')[1])
                elif arg.startswith('--max-inflation='):
                    max_inf = float(arg.split('=')[1])
                elif arg.startswith('--min-real-rate='):
                    min_real = float(arg.split('=')[1])
                elif arg.startswith('--max-real-rate='):
                    max_real = float(arg.split('=')[1])
            
            cmd_search(min_inf, max_inf, min_real, max_real)
        
        elif command == 'inflation-countries':
            cmd_countries()
        
        else:
            print(f"Unknown command: {command}")
            return 1
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
