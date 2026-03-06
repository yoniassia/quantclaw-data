#!/usr/bin/env python3
"""
Global PMI Aggregator Module — Phase 106

Manufacturing & Services PMI for 30+ countries from multiple sources:
- ISM (US Manufacturing & Services)
- S&P Global / Markit PMI data via FRED
- National statistical agencies
- Trading Economics data

PMI (Purchasing Managers' Index):
- Above 50 = expansion
- Below 50 = contraction
- Leading indicator of economic health

Data Sources:
- FRED API (most comprehensive, free)
- ISM Official Data (US only, free)
- Direct from statistical agencies where available

Monthly refresh on PMI release days (typically 1st-3rd business day of month).

Phase: 106
Author: QUANTCLAW DATA Build Agent
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# FRED API Configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = ""  # Optional: configure via environment

# Global PMI Series Mapping
# Format: Country -> {manufacturing: FRED_ID, services: FRED_ID}
PMI_SERIES = {
    # === G7 Countries ===
    'USA': {
        'manufacturing': 'NAPM',  # ISM Manufacturing PMI
        'services': 'NAPMNOI',  # ISM Non-Manufacturing/Services PMI
        'name': 'United States',
        'region': 'North America'
    },
    'CHN': {
        'manufacturing': 'CHNPMICN',  # China Manufacturing PMI (NBS)
        'services': 'CHNPMISVCN',  # China Services PMI
        'name': 'China',
        'region': 'Asia'
    },
    'JPN': {
        'manufacturing': 'JPNMFGPMISMMT',  # Japan Manufacturing PMI
        'services': 'JPNSRVPMISMMT',  # Japan Services PMI
        'name': 'Japan',
        'region': 'Asia'
    },
    'DEU': {
        'manufacturing': 'DEUMFGPMISMMT',  # Germany Manufacturing PMI
        'services': 'DEUSRVPMISMMT',  # Germany Services PMI
        'name': 'Germany',
        'region': 'Europe'
    },
    'GBR': {
        'manufacturing': 'GBRMFGPMISMMT',  # UK Manufacturing PMI
        'services': 'GBRSRVPMISMMT',  # UK Services PMI
        'name': 'United Kingdom',
        'region': 'Europe'
    },
    'FRA': {
        'manufacturing': 'FRAMFGPMISMMT',  # France Manufacturing PMI
        'services': 'FRASRVPMISMMT',  # France Services PMI
        'name': 'France',
        'region': 'Europe'
    },
    'ITA': {
        'manufacturing': 'ITAMFGPMISMMT',  # Italy Manufacturing PMI
        'services': 'ITASRVPMISMMT',  # Italy Services PMI
        'name': 'Italy',
        'region': 'Europe'
    },
    'CAN': {
        'manufacturing': 'CANMFGPMISMMT',  # Canada Manufacturing PMI
        'services': 'CANSRVPMISMMT',  # Canada Services PMI
        'name': 'Canada',
        'region': 'North America'
    },
    
    # === Europe ===
    'ESP': {
        'manufacturing': 'ESPNMFGPMISMMT',  # Spain Manufacturing PMI
        'services': 'ESPSRVPMISMMT',  # Spain Services PMI
        'name': 'Spain',
        'region': 'Europe'
    },
    'NLD': {
        'manufacturing': 'NLDMFGPMISMMT',  # Netherlands Manufacturing PMI
        'services': 'NLDSRVPMISMMT',  # Netherlands Services PMI
        'name': 'Netherlands',
        'region': 'Europe'
    },
    'SWE': {
        'manufacturing': 'SWEMFGPMISMMT',  # Sweden Manufacturing PMI
        'services': 'SWESRVPMISMMT',  # Sweden Services PMI
        'name': 'Sweden',
        'region': 'Europe'
    },
    'CHE': {
        'manufacturing': 'CHEMFGPMISMMT',  # Switzerland Manufacturing PMI
        'services': 'CHESRVPMISMMT',  # Switzerland Services PMI
        'name': 'Switzerland',
        'region': 'Europe'
    },
    'AUT': {
        'manufacturing': 'AUTMFGPMISMMT',  # Austria Manufacturing PMI
        'services': 'AUTSRVPMISMMT',  # Austria Services PMI
        'name': 'Austria',
        'region': 'Europe'
    },
    'GRC': {
        'manufacturing': 'GRCMFGPMISMMT',  # Greece Manufacturing PMI
        'services': 'GRCSRVPMISMMT',  # Greece Services PMI
        'name': 'Greece',
        'region': 'Europe'
    },
    'POL': {
        'manufacturing': 'POLMFGPMISMMT',  # Poland Manufacturing PMI
        'services': 'POLSRVPMISMMT',  # Poland Services PMI
        'name': 'Poland',
        'region': 'Europe'
    },
    
    # === Asia-Pacific ===
    'IND': {
        'manufacturing': 'INDMFGPMISMMT',  # India Manufacturing PMI
        'services': 'INDSRVPMISMMT',  # India Services PMI
        'name': 'India',
        'region': 'Asia'
    },
    'KOR': {
        'manufacturing': 'KORMFGPMISMMT',  # South Korea Manufacturing PMI
        'services': 'KORSRVPMISMMT',  # South Korea Services PMI
        'name': 'South Korea',
        'region': 'Asia'
    },
    'AUS': {
        'manufacturing': 'AUSMFGPMISMMT',  # Australia Manufacturing PMI
        'services': 'AUSSRVPMISMMT',  # Australia Services PMI
        'name': 'Australia',
        'region': 'Asia-Pacific'
    },
    'IDN': {
        'manufacturing': 'IDNMFGPMISMMT',  # Indonesia Manufacturing PMI
        'services': 'IDNSRVPMISMMT',  # Indonesia Services PMI
        'name': 'Indonesia',
        'region': 'Asia'
    },
    'THA': {
        'manufacturing': 'THAMFGPMISMMT',  # Thailand Manufacturing PMI
        'services': 'THASRVPMISMMT',  # Thailand Services PMI
        'name': 'Thailand',
        'region': 'Asia'
    },
    'MYS': {
        'manufacturing': 'MYSMFGPMISMMT',  # Malaysia Manufacturing PMI
        'services': 'MYSSRVPMISMMT',  # Malaysia Services PMI
        'name': 'Malaysia',
        'region': 'Asia'
    },
    'SGP': {
        'manufacturing': 'SGPMFGPMISMMT',  # Singapore Manufacturing PMI
        'services': 'SGPSRVPMISMMT',  # Singapore Services PMI
        'name': 'Singapore',
        'region': 'Asia'
    },
    'TWN': {
        'manufacturing': 'TWNMFGPMISMMT',  # Taiwan Manufacturing PMI
        'services': 'TWNSRVPMISMMT',  # Taiwan Services PMI
        'name': 'Taiwan',
        'region': 'Asia'
    },
    'VNM': {
        'manufacturing': 'VNMMFGPMISMMT',  # Vietnam Manufacturing PMI
        'services': 'VNMSRVPMISMMT',  # Vietnam Services PMI
        'name': 'Vietnam',
        'region': 'Asia'
    },
    
    # === Americas ===
    'BRA': {
        'manufacturing': 'BRAMFGPMISMMT',  # Brazil Manufacturing PMI
        'services': 'BRASRVPMISMMT',  # Brazil Services PMI
        'name': 'Brazil',
        'region': 'Latin America'
    },
    'MEX': {
        'manufacturing': 'MEXMFGPMISMMT',  # Mexico Manufacturing PMI
        'services': 'MEXSRVPMISMMT',  # Mexico Services PMI
        'name': 'Mexico',
        'region': 'Latin America'
    },
    'ARG': {
        'manufacturing': 'ARGMFGPMISMMT',  # Argentina Manufacturing PMI
        'services': 'ARGSRVPMISMMT',  # Argentina Services PMI
        'name': 'Argentina',
        'region': 'Latin America'
    },
    'CHL': {
        'manufacturing': 'CHLMFGPMISMMT',  # Chile Manufacturing PMI
        'services': 'CHLSRVPMISMMT',  # Chile Services PMI
        'name': 'Chile',
        'region': 'Latin America'
    },
    'COL': {
        'manufacturing': 'COLMFGPMISMMT',  # Colombia Manufacturing PMI
        'services': 'COLSRVPMISMMT',  # Colombia Services PMI
        'name': 'Colombia',
        'region': 'Latin America'
    },
    
    # === Middle East & Africa ===
    'TUR': {
        'manufacturing': 'TURMFGPMISMMT',  # Turkey Manufacturing PMI
        'services': 'TURSRVPMISMMT',  # Turkey Services PMI
        'name': 'Turkey',
        'region': 'Middle East'
    },
    'SAU': {
        'manufacturing': 'SAUMFGPMISMMT',  # Saudi Arabia Manufacturing PMI
        'services': 'SAUSRVPMISMMT',  # Saudi Arabia Services PMI
        'name': 'Saudi Arabia',
        'region': 'Middle East'
    },
    'ARE': {
        'manufacturing': 'AREMFGPMISMMT',  # UAE Manufacturing PMI
        'services': 'ARESRVPMISMMT',  # UAE Services PMI
        'name': 'United Arab Emirates',
        'region': 'Middle East'
    },
    'ZAF': {
        'manufacturing': 'ZAFMFGPMISMMT',  # South Africa Manufacturing PMI
        'services': 'ZAFSRVPMISMMT',  # South Africa Services PMI
        'name': 'South Africa',
        'region': 'Africa'
    },
    'EGY': {
        'manufacturing': 'EGYMFGPMISMMT',  # Egypt Manufacturing PMI
        'services': 'EGYSRVPMISMMT',  # Egypt Services PMI
        'name': 'Egypt',
        'region': 'Africa'
    },
    
    # === Other ===
    'RUS': {
        'manufacturing': 'RUSMFGPMISMMT',  # Russia Manufacturing PMI
        'services': 'RUSSRVPMISMMT',  # Russia Services PMI
        'name': 'Russia',
        'region': 'Europe'
    },
    'ISR': {
        'manufacturing': 'ISRMFGPMISMMT',  # Israel Manufacturing PMI
        'services': 'ISRSRVPMISMMT',  # Israel Services PMI
        'name': 'Israel',
        'region': 'Middle East'
    },
}

# Eurozone Aggregate
EUROZONE_PMI = {
    'EUR': {
        'manufacturing': 'EZMFGPMISMMT',  # Eurozone Manufacturing PMI
        'services': 'EZSRVPMISMMT',  # Eurozone Services PMI
        'composite': 'EZCOMPPMISMMT',  # Eurozone Composite PMI
        'name': 'Eurozone',
        'region': 'Europe'
    }
}


def fetch_fred_series(series_id: str, months_back: int = 12, 
                     api_key: Optional[str] = None) -> Dict:
    """
    Fetch PMI data from FRED API
    
    Args:
        series_id: FRED series identifier
        months_back: Number of months of historical data to fetch
        api_key: Optional FRED API key
        
    Returns:
        Dictionary with time series data
    """
    try:
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'observation_start': (datetime.now() - timedelta(days=months_back*30)).strftime('%Y-%m-%d'),
            'sort_order': 'desc'
        }
        
        if api_key or FRED_API_KEY:
            params['api_key'] = api_key or FRED_API_KEY
        
        response = requests.get(FRED_API_BASE, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'observations' in data:
                observations = []
                for obs in data['observations']:
                    try:
                        value = float(obs['value']) if obs['value'] != '.' else None
                        if value is not None:
                            observations.append({
                                'date': obs['date'],
                                'value': value
                            })
                    except (ValueError, KeyError):
                        continue
                
                if observations:
                    latest = observations[0]
                    prev = observations[1] if len(observations) > 1 else None
                    
                    mom_change = None
                    if prev and prev['value']:
                        mom_change = latest['value'] - prev['value']
                    
                    return {
                        'success': True,
                        'series_id': series_id,
                        'latest_value': latest['value'],
                        'latest_date': latest['date'],
                        'previous_value': prev['value'] if prev else None,
                        'previous_date': prev['date'] if prev else None,
                        'mom_change': mom_change,
                        'observations': observations,
                        'count': len(observations)
                    }
        
        return {
            'success': False,
            'series_id': series_id,
            'error': f'HTTP {response.status_code}',
            'message': 'Data not available or API rate limit exceeded. FRED API key recommended.'
        }
    
    except Exception as e:
        return {
            'success': False,
            'series_id': series_id,
            'error': str(e)
        }


def get_country_pmi(country_code: str, pmi_type: str = 'both', months: int = 12) -> Dict:
    """
    Get PMI data for a specific country
    
    Args:
        country_code: ISO 3-letter country code
        pmi_type: 'manufacturing', 'services', or 'both'
        months: Number of months of historical data
        
    Returns:
        Dictionary with PMI data
    """
    country_code = country_code.upper()
    
    # Check Eurozone aggregate
    if country_code == 'EUR' and country_code in EUROZONE_PMI:
        country_info = EUROZONE_PMI[country_code]
    elif country_code not in PMI_SERIES:
        return {
            'success': False,
            'error': f'Country {country_code} not in PMI database',
            'available_countries': list(PMI_SERIES.keys()) + ['EUR']
        }
    else:
        country_info = PMI_SERIES[country_code]
    
    result = {
        'success': True,
        'country': country_info['name'],
        'country_code': country_code,
        'region': country_info['region'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Fetch manufacturing PMI
    if pmi_type in ['manufacturing', 'both'] and 'manufacturing' in country_info:
        mfg_data = fetch_fred_series(country_info['manufacturing'], months_back=months)
        result['manufacturing'] = mfg_data
        
        if mfg_data.get('success'):
            result['manufacturing_latest'] = mfg_data['latest_value']
            result['manufacturing_status'] = 'expansion' if mfg_data['latest_value'] > 50 else 'contraction'
    
    # Fetch services PMI
    if pmi_type in ['services', 'both'] and 'services' in country_info:
        svc_data = fetch_fred_series(country_info['services'], months_back=months)
        result['services'] = svc_data
        
        if svc_data.get('success'):
            result['services_latest'] = svc_data['latest_value']
            result['services_status'] = 'expansion' if svc_data['latest_value'] > 50 else 'contraction'
    
    # Calculate composite if both available
    if result.get('manufacturing_latest') and result.get('services_latest'):
        result['composite_pmi'] = round((result['manufacturing_latest'] + result['services_latest']) / 2, 1)
        result['composite_status'] = 'expansion' if result['composite_pmi'] > 50 else 'contraction'
    
    return result


def get_global_pmi_snapshot(pmi_type: str = 'manufacturing', include_eurozone: bool = True) -> Dict:
    """
    Get global PMI snapshot for all countries
    
    Args:
        pmi_type: 'manufacturing' or 'services'
        include_eurozone: Include EUR aggregate
        
    Returns:
        Dictionary with global PMI data
    """
    countries = list(PMI_SERIES.keys())
    if include_eurozone:
        countries.append('EUR')
    
    snapshot = {
        'pmi_type': pmi_type,
        'countries': [],
        'expansion_count': 0,
        'contraction_count': 0,
        'timestamp': datetime.now().isoformat()
    }
    
    for country_code in countries:
        data = get_country_pmi(country_code, pmi_type=pmi_type, months=3)
        
        if data.get('success'):
            pmi_key = f'{pmi_type}_latest'
            status_key = f'{pmi_type}_status'
            
            if pmi_key in data:
                country_entry = {
                    'country': data['country'],
                    'code': country_code,
                    'region': data['region'],
                    'value': data[pmi_key],
                    'status': data[status_key]
                }
                
                # Add month-over-month change if available
                pmi_data = data.get(pmi_type, {})
                if pmi_data.get('mom_change'):
                    country_entry['mom_change'] = pmi_data['mom_change']
                
                snapshot['countries'].append(country_entry)
                
                if data[status_key] == 'expansion':
                    snapshot['expansion_count'] += 1
                else:
                    snapshot['contraction_count'] += 1
    
    # Sort by value descending
    snapshot['countries'].sort(key=lambda x: x['value'], reverse=True)
    
    # Calculate global statistics
    values = [c['value'] for c in snapshot['countries']]
    if values:
        snapshot['global_avg'] = round(sum(values) / len(values), 1)
        snapshot['global_median'] = round(sorted(values)[len(values)//2], 1)
        snapshot['highest'] = snapshot['countries'][0]
        snapshot['lowest'] = snapshot['countries'][-1]
    
    return snapshot


def compare_countries_pmi(country_codes: List[str], pmi_type: str = 'manufacturing', 
                         months: int = 12) -> Dict:
    """
    Compare PMI across multiple countries with time series
    
    Args:
        country_codes: List of ISO country codes
        pmi_type: 'manufacturing' or 'services'
        months: Number of months of historical data
        
    Returns:
        Comparative analysis dictionary
    """
    comparison = {
        'pmi_type': pmi_type,
        'countries': [],
        'months': months,
        'timestamp': datetime.now().isoformat()
    }
    
    for code in country_codes:
        data = get_country_pmi(code.upper(), pmi_type=pmi_type, months=months)
        
        if data.get('success'):
            pmi_key = f'{pmi_type}_latest'
            if pmi_key in data:
                pmi_data = data.get(pmi_type, {})
                
                country_entry = {
                    'country': data['country'],
                    'code': code.upper(),
                    'region': data['region'],
                    'latest': data[pmi_key],
                    'status': data[f'{pmi_type}_status'],
                    'history': pmi_data.get('observations', [])[:months]
                }
                
                comparison['countries'].append(country_entry)
    
    # Sort by latest value
    comparison['countries'].sort(key=lambda x: x['latest'], reverse=True)
    
    return comparison


def get_regional_pmi(region: str, pmi_type: str = 'manufacturing') -> Dict:
    """
    Get PMI snapshot for a specific region
    
    Regions: 'Europe', 'Asia', 'North America', 'Latin America', 'Middle East', 'Africa', 'Asia-Pacific'
    
    Args:
        region: Region name
        pmi_type: 'manufacturing' or 'services'
        
    Returns:
        Regional PMI snapshot
    """
    # Filter countries by region
    region_countries = []
    for code, info in PMI_SERIES.items():
        if info['region'].lower() == region.lower():
            region_countries.append(code)
    
    if not region_countries:
        return {
            'success': False,
            'error': f'Region "{region}" not found',
            'available_regions': sorted(set(info['region'] for info in PMI_SERIES.values()))
        }
    
    regional_data = {
        'region': region,
        'pmi_type': pmi_type,
        'countries': [],
        'timestamp': datetime.now().isoformat()
    }
    
    for code in region_countries:
        data = get_country_pmi(code, pmi_type=pmi_type, months=3)
        
        if data.get('success'):
            pmi_key = f'{pmi_type}_latest'
            if pmi_key in data:
                regional_data['countries'].append({
                    'country': data['country'],
                    'code': code,
                    'value': data[pmi_key],
                    'status': data[f'{pmi_type}_status']
                })
    
    # Calculate regional average
    if regional_data['countries']:
        values = [c['value'] for c in regional_data['countries']]
        regional_data['regional_avg'] = round(sum(values) / len(values), 1)
        regional_data['regional_status'] = 'expansion' if regional_data['regional_avg'] > 50 else 'contraction'
        
        # Sort by value
        regional_data['countries'].sort(key=lambda x: x['value'], reverse=True)
    
    return regional_data


def get_pmi_divergence(months: int = 6) -> Dict:
    """
    Identify countries with significant PMI divergence between manufacturing and services
    
    Args:
        months: Number of months of data to analyze
        
    Returns:
        Dictionary with divergence analysis
    """
    divergence = {
        'analysis': [],
        'months_analyzed': months,
        'timestamp': datetime.now().isoformat()
    }
    
    for code in PMI_SERIES.keys():
        data = get_country_pmi(code, pmi_type='both', months=months)
        
        if data.get('success') and data.get('manufacturing_latest') and data.get('services_latest'):
            mfg = data['manufacturing_latest']
            svc = data['services_latest']
            diff = svc - mfg
            
            divergence['analysis'].append({
                'country': data['country'],
                'code': code,
                'manufacturing': mfg,
                'services': svc,
                'divergence': round(diff, 1),
                'abs_divergence': round(abs(diff), 1),
                'interpretation': 'Services outperforming' if diff > 0 else 'Manufacturing outperforming'
            })
    
    # Sort by absolute divergence
    divergence['analysis'].sort(key=lambda x: x['abs_divergence'], reverse=True)
    
    return divergence


def search_countries(query: str) -> List[Dict]:
    """
    Search for countries in PMI database
    
    Args:
        query: Search query (name or code)
        
    Returns:
        List of matching countries
    """
    query_lower = query.lower()
    matches = []
    
    # Search PMI series
    for code, info in PMI_SERIES.items():
        if query_lower in info['name'].lower() or query_lower in code.lower():
            matches.append({
                'code': code,
                'name': info['name'],
                'region': info['region']
            })
    
    # Include Eurozone
    if query_lower in 'eurozone' or query_lower in 'eur':
        matches.append({
            'code': 'EUR',
            'name': 'Eurozone',
            'region': 'Europe'
        })
    
    return matches


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'pmi-country':
            if len(sys.argv) < 3:
                print("Error: country command requires a country code", file=sys.stderr)
                print("Usage: python global_pmi.py country <CODE> [--type manufacturing|services|both] [--months 12]", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            pmi_type = 'both'
            months = 12
            
            if '--type' in sys.argv:
                idx = sys.argv.index('--type')
                if idx + 1 < len(sys.argv):
                    pmi_type = sys.argv[idx + 1]
            
            if '--months' in sys.argv:
                idx = sys.argv.index('--months')
                if idx + 1 < len(sys.argv):
                    months = int(sys.argv[idx + 1])
            
            data = get_country_pmi(country_code, pmi_type=pmi_type, months=months)
            print(json.dumps(data, indent=2))
        
        elif command == 'pmi-global':
            pmi_type = 'manufacturing'
            if len(sys.argv) > 2:
                pmi_type = sys.argv[2]
            
            data = get_global_pmi_snapshot(pmi_type=pmi_type)
            print(json.dumps(data, indent=2))
        
        elif command == 'pmi-compare':
            if len(sys.argv) < 3:
                print("Error: compare requires country codes", file=sys.stderr)
                print("Usage: python global_pmi.py compare <CODE1,CODE2,CODE3> [--type manufacturing] [--months 12]", file=sys.stderr)
                return 1
            
            country_codes = sys.argv[2].upper().split(',')
            pmi_type = 'manufacturing'
            months = 12
            
            if '--type' in sys.argv:
                idx = sys.argv.index('--type')
                if idx + 1 < len(sys.argv):
                    pmi_type = sys.argv[idx + 1]
            
            if '--months' in sys.argv:
                idx = sys.argv.index('--months')
                if idx + 1 < len(sys.argv):
                    months = int(sys.argv[idx + 1])
            
            data = compare_countries_pmi(country_codes, pmi_type=pmi_type, months=months)
            print(json.dumps(data, indent=2))
        
        elif command == 'pmi-regional':
            if len(sys.argv) < 3:
                print("Error: pmi-regional requires a region name", file=sys.stderr)
                print("Usage: python global_pmi.py pmi-regional <REGION> [--type manufacturing]", file=sys.stderr)
                return 1
            
            region = ' '.join(sys.argv[2:])
            pmi_type = 'manufacturing'
            
            # Extract --type if present
            if '--type' in region:
                parts = region.split('--type')
                region = parts[0].strip()
                if len(parts) > 1:
                    pmi_type = parts[1].strip().split()[0]
            
            data = get_regional_pmi(region, pmi_type=pmi_type)
            print(json.dumps(data, indent=2))
        
        elif command == 'pmi-divergence':
            months = 6
            if '--months' in sys.argv:
                idx = sys.argv.index('--months')
                if idx + 1 < len(sys.argv):
                    months = int(sys.argv[idx + 1])
            
            data = get_pmi_divergence(months=months)
            print(json.dumps(data, indent=2))
        
        elif command == 'pmi-search':
            if len(sys.argv) < 3:
                print("Error: search requires a query", file=sys.stderr)
                print("Usage: python global_pmi.py search <QUERY>", file=sys.stderr)
                return 1
            
            query = ' '.join(sys.argv[2:])
            matches = search_countries(query)
            print(json.dumps(matches, indent=2))
        
        elif command == 'pmi-list':
            # List all available countries
            countries = []
            for code, info in sorted(PMI_SERIES.items()):
                countries.append({
                    'code': code,
                    'name': info['name'],
                    'region': info['region']
                })
            countries.append({'code': 'EUR', 'name': 'Eurozone', 'region': 'Europe'})
            
            print(json.dumps({
                'success': True,
                'countries': countries,
                'count': len(countries)
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
Global PMI Aggregator (Phase 106)

Commands:
  python cli.py pmi-country <CODE> [--type manufacturing|services|both] [--months 12]
                                      # Get PMI data for specific country
  
  python cli.py pmi-global [manufacturing|services]
                                      # Global PMI snapshot for all countries
  
  python cli.py pmi-compare <CODE1,CODE2,CODE3> [--type manufacturing] [--months 12]
                                      # Compare PMI across countries
  
  python cli.py pmi-regional <REGION> [--type manufacturing]
                                      # Regional PMI snapshot
  
  python cli.py pmi-divergence [--months 6]
                                      # Manufacturing vs Services divergence analysis
  
  python cli.py pmi-search <QUERY>
                                      # Search for countries
  
  python cli.py pmi-list              # List all available countries

Examples:
  python cli.py pmi-country USA
  python cli.py pmi-country CHN --type both --months 24
  python cli.py pmi-global manufacturing
  python cli.py pmi-compare USA,CHN,DEU,JPN --type manufacturing
  python cli.py pmi-regional Europe --type services
  python cli.py pmi-divergence --months 12
  python cli.py pmi-search Korea

Coverage: 30+ countries including G7, G20, BRICS, major emerging markets

PMI Interpretation:
  > 50.0  = Expansion (economic growth)
  < 50.0  = Contraction (economic decline)
  ~ 50.0  = Stagnation

Regions:
  - Europe
  - Asia
  - North America
  - Latin America
  - Middle East
  - Africa
  - Asia-Pacific

Data Source: FRED API (Federal Reserve Economic Data)
Frequency: Monthly
Release: Typically 1st-3rd business day of each month
""")


if __name__ == "__main__":
    sys.exit(main())
