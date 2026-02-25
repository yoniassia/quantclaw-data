#!/usr/bin/env python3
"""
UN Comtrade Trade Flows Module — Phase 103

Bilateral trade flows and commodity-level import/export data for 200+ countries
- Bilateral trade matrices (country-to-country flows)
- Commodity-level trade (HS codes, SITC classification)
- Trade balances and dependencies
- Export/import concentration analysis

Data Source: comtradeapi.un.org
Refresh: Monthly
Coverage: 200+ countries, bilateral flows, 5,000+ commodity codes

Author: QUANTCLAW DATA Build Agent
Phase: 103
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from collections import defaultdict

# UN Comtrade API Configuration
COMTRADE_BASE_URL = "https://comtradeapi.un.org"
COMTRADE_DATA_URL = f"{COMTRADE_BASE_URL}/data/v1/get"
COMTRADE_REF_URL = f"{COMTRADE_BASE_URL}/files/v1/app/reference"

# Cache for reference data
_CACHE = {
    'reporters': None,
    'partners': None,
    'commodities': None,
    'flows': None,
    'timestamp': None
}

CACHE_TTL = 86400  # 24 hours

# Trade Flow Types
FLOW_CODES = {
    'M': 'Imports',
    'X': 'Exports',
    'RM': 'Re-Imports',
    'RX': 'Re-Exports'
}

# Major Commodity Categories (HS 2-digit)
MAJOR_COMMODITIES = {
    '01-05': 'Live Animals & Animal Products',
    '06-14': 'Vegetable Products',
    '15': 'Animal/Vegetable Fats & Oils',
    '16-24': 'Prepared Food, Beverages & Tobacco',
    '25-27': 'Mineral Products',
    '28-38': 'Chemicals & Allied Industries',
    '39-40': 'Plastics & Rubber',
    '41-43': 'Raw Hides, Skins & Leather',
    '44-46': 'Wood & Wood Products',
    '47-49': 'Pulp, Paper & Paperboard',
    '50-63': 'Textiles & Textile Articles',
    '64-67': 'Footwear, Headgear & Accessories',
    '68-70': 'Stone, Glass & Ceramics',
    '71': 'Precious Stones & Metals',
    '72-83': 'Base Metals & Articles',
    '84-85': 'Machinery & Electrical Equipment',
    '86-89': 'Transportation Equipment',
    '90-92': 'Precision Instruments & Optical',
    '93': 'Arms & Ammunition',
    '94-96': 'Miscellaneous Manufactured Articles',
    '97': 'Works of Art & Antiques'
}


def _get_cache_key(endpoint: str) -> str:
    """Generate cache key for endpoint"""
    return endpoint.split('/')[-1].replace('.json', '')


def _is_cache_valid() -> bool:
    """Check if cache is still valid"""
    if _CACHE['timestamp'] is None:
        return False
    return (datetime.now() - _CACHE['timestamp']).seconds < CACHE_TTL


def get_reporters(region: Optional[str] = None) -> List[Dict]:
    """
    Get list of reporting countries
    
    Args:
        region: Optional region filter (Africa, Americas, Asia, Europe, Oceania)
    
    Returns:
        List of reporter country dictionaries
    """
    cache_key = 'reporters'
    
    if not _is_cache_valid() or _CACHE[cache_key] is None:
        try:
            url = f"{COMTRADE_REF_URL}/Reporters.json"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            _CACHE[cache_key] = data.get('results', [])
            _CACHE['timestamp'] = datetime.now()
        except Exception as e:
            return {'error': f'Failed to fetch reporters: {str(e)}'}
    
    reporters = _CACHE[cache_key]
    
    # Filter by region if specified
    if region:
        # Note: Region filtering would require additional metadata
        # For now, return all reporters
        pass
    
    return reporters


def get_partners() -> List[Dict]:
    """
    Get list of partner countries (trade destinations/origins)
    
    Note: Partners are the same as reporters in UN Comtrade
    
    Returns:
        List of partner country dictionaries
    """
    # In UN Comtrade, partners are the same as reporters
    # Just return reporters list
    return get_reporters()


def get_commodities(level: Optional[int] = None) -> List[Dict]:
    """
    Get commodity classification codes (HS codes)
    
    Args:
        level: Optional aggregation level (2, 4, or 6-digit HS code)
    
    Returns:
        List of commodity dictionaries
    """
    cache_key = 'commodities'
    
    if not _is_cache_valid() or _CACHE[cache_key] is None:
        try:
            url = f"{COMTRADE_REF_URL}/HS.json"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            _CACHE[cache_key] = data.get('results', [])
            _CACHE['timestamp'] = datetime.now()
        except Exception as e:
            return {'error': f'Failed to fetch commodities: {str(e)}'}
    
    commodities = _CACHE[cache_key]
    
    # Filter by aggregation level if specified
    if level and isinstance(commodities, list):
        commodities = [c for c in commodities if c.get('aggrLevel') == level * 2]
    
    return commodities


def search_country(query: str) -> List[Dict]:
    """
    Search for countries by name or code
    
    Args:
        query: Search string (name or ISO code)
    
    Returns:
        List of matching countries
    """
    reporters = get_reporters()
    
    if isinstance(reporters, dict) and 'error' in reporters:
        return reporters
    
    query_lower = query.lower()
    matches = []
    
    for country in reporters:
        if (query_lower in country.get('text', '').lower() or
            query_lower in country.get('reporterCodeIsoAlpha2', '').lower() or
            query_lower in country.get('reporterCodeIsoAlpha3', '').lower() or
            str(country.get('reporterCode', '')) == query):
            matches.append(country)
    
    return matches


def search_commodity(query: str) -> List[Dict]:
    """
    Search for commodities by description or HS code
    
    Args:
        query: Search string (description or HS code)
    
    Returns:
        List of matching commodities
    """
    commodities = get_commodities()
    
    if isinstance(commodities, dict) and 'error' in commodities:
        return commodities
    
    query_lower = query.lower()
    matches = []
    
    for commodity in commodities:
        if (query_lower in commodity.get('text', '').lower() or
            query_lower in commodity.get('id', '').lower()):
            matches.append(commodity)
    
    return matches[:50]  # Limit to 50 results


def get_bilateral_trade(
    reporter: str,
    partner: str,
    year: Optional[int] = None,
    flow: str = 'M',
    commodity: str = 'TOTAL',
    api_key: Optional[str] = None
) -> Dict:
    """
    Get bilateral trade flows between two countries
    
    Args:
        reporter: Reporter country code (ISO3 or numeric)
        partner: Partner country code (ISO3 or numeric)
        year: Year (default: current year - 1)
        flow: Trade flow type (M=imports, X=exports)
        commodity: HS commodity code (default: TOTAL)
        api_key: UN Comtrade API subscription key
    
    Returns:
        Trade flow data dictionary
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key. Get one at: https://comtradeplus.un.org/',
            'note': 'Reference data (countries, commodities) is available without API key'
        }
    
    if year is None:
        year = datetime.now().year - 1
    
    try:
        # Convert country names/codes to numeric codes if needed
        reporter_code = _resolve_country_code(reporter)
        partner_code = _resolve_country_code(partner)
        
        if not reporter_code or not partner_code:
            return {'error': 'Invalid country code'}
        
        # Build API request
        url = f"{COMTRADE_DATA_URL}/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'partnerCode': partner_code,
            'period': year,
            'flowCode': flow,
            'cmdCode': commodity
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except Exception as e:
        return {'error': f'Failed to fetch trade data: {str(e)}'}


def get_top_trade_partners(
    reporter: str,
    flow: str = 'M',
    year: Optional[int] = None,
    limit: int = 20,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get top trade partners for a country
    
    Args:
        reporter: Reporter country code
        flow: Trade flow type (M=imports, X=exports)
        year: Year (default: current year - 1)
        limit: Number of top partners to return
        api_key: UN Comtrade API subscription key
    
    Returns:
        Top trade partners data
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key'
        }
    
    if year is None:
        year = datetime.now().year - 1
    
    try:
        reporter_code = _resolve_country_code(reporter)
        
        url = f"{COMTRADE_DATA_URL}/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'partnerCode': 'all',
            'period': year,
            'flowCode': flow,
            'cmdCode': 'TOTAL'
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Sort by trade value and return top N
        if 'data' in data:
            sorted_data = sorted(
                data['data'],
                key=lambda x: x.get('primaryValue', 0),
                reverse=True
            )
            return {
                'reporter': reporter,
                'flow': FLOW_CODES.get(flow, flow),
                'year': year,
                'top_partners': sorted_data[:limit],
                'total_trade_value': sum(x.get('primaryValue', 0) for x in sorted_data)
            }
        
        return data
        
    except Exception as e:
        return {'error': f'Failed to fetch top partners: {str(e)}'}


def get_trade_balance(
    reporter: str,
    partner: Optional[str] = None,
    year: Optional[int] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate trade balance (exports - imports) for a country
    
    Args:
        reporter: Reporter country code
        partner: Optional partner code (default: all partners)
        year: Year (default: current year - 1)
        api_key: UN Comtrade API subscription key
    
    Returns:
        Trade balance data
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key'
        }
    
    partner_code = _resolve_country_code(partner) if partner else 'all'
    
    # Get imports and exports
    imports = get_bilateral_trade(reporter, partner_code, year, 'M', 'TOTAL', api_key)
    exports = get_bilateral_trade(reporter, partner_code, year, 'X', 'TOTAL', api_key)
    
    if 'error' in imports or 'error' in exports:
        return {'error': 'Failed to calculate trade balance'}
    
    import_value = sum(x.get('primaryValue', 0) for x in imports.get('data', []))
    export_value = sum(x.get('primaryValue', 0) for x in exports.get('data', []))
    
    return {
        'reporter': reporter,
        'partner': partner if partner else 'All partners',
        'year': year or datetime.now().year - 1,
        'imports': import_value,
        'exports': export_value,
        'trade_balance': export_value - import_value,
        'trade_volume': import_value + export_value
    }


def get_commodity_trade(
    reporter: str,
    commodity: str,
    year: Optional[int] = None,
    flow: str = 'M',
    api_key: Optional[str] = None
) -> Dict:
    """
    Get trade data for a specific commodity
    
    Args:
        reporter: Reporter country code
        commodity: HS commodity code (e.g., '84' for machinery)
        year: Year (default: current year - 1)
        flow: Trade flow type (M=imports, X=exports)
        api_key: UN Comtrade API subscription key
    
    Returns:
        Commodity trade data
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key'
        }
    
    return get_bilateral_trade(
        reporter=reporter,
        partner='all',
        year=year,
        flow=flow,
        commodity=commodity,
        api_key=api_key
    )


def analyze_trade_concentration(
    reporter: str,
    year: Optional[int] = None,
    flow: str = 'X',
    api_key: Optional[str] = None
) -> Dict:
    """
    Analyze trade concentration (Herfindahl-Hirschman Index)
    
    Args:
        reporter: Reporter country code
        year: Year (default: current year - 1)
        flow: Trade flow type (M=imports, X=exports)
        api_key: UN Comtrade API subscription key
    
    Returns:
        Concentration analysis with HHI score
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key'
        }
    
    top_partners = get_top_trade_partners(reporter, flow, year, limit=50, api_key=api_key)
    
    if 'error' in top_partners:
        return top_partners
    
    partners = top_partners.get('top_partners', [])
    total_value = top_partners.get('total_trade_value', 0)
    
    if total_value == 0:
        return {'error': 'No trade data available'}
    
    # Calculate HHI (sum of squared market shares)
    hhi = 0
    shares = []
    
    for partner in partners:
        value = partner.get('primaryValue', 0)
        share = (value / total_value) * 100
        hhi += (share ** 2)
        shares.append({
            'partner': partner.get('partnerDesc', 'Unknown'),
            'value': value,
            'share': share
        })
    
    # HHI interpretation
    if hhi < 1000:
        concentration = 'Low concentration (diversified)'
    elif hhi < 1800:
        concentration = 'Moderate concentration'
    else:
        concentration = 'High concentration (risky)'
    
    return {
        'reporter': reporter,
        'year': year or datetime.now().year - 1,
        'flow': FLOW_CODES.get(flow, flow),
        'hhi': round(hhi, 2),
        'concentration_level': concentration,
        'top_partners': shares[:10],
        'top_3_share': sum(s['share'] for s in shares[:3])
    }


def _resolve_country_code(country: str) -> Optional[str]:
    """
    Resolve country name or ISO code to numeric code
    
    Args:
        country: Country name, ISO2, ISO3, or numeric code
    
    Returns:
        Numeric country code or None
    """
    if country.isdigit():
        return country
    
    # Search in reporters cache
    reporters = get_reporters()
    
    if isinstance(reporters, dict) and 'error' in reporters:
        return None
    
    country_upper = country.upper()
    
    for reporter in reporters:
        if (reporter.get('reporterCodeIsoAlpha2', '').upper() == country_upper or
            reporter.get('reporterCodeIsoAlpha3', '').upper() == country_upper or
            reporter.get('text', '').upper() == country.upper()):
            return str(reporter.get('reporterCode'))
    
    return None


def get_trade_dependencies(
    reporter: str,
    threshold: float = 10.0,
    year: Optional[int] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Identify critical trade dependencies (partners > threshold% of total trade)
    
    Args:
        reporter: Reporter country code
        threshold: Minimum share percentage to flag as dependency (default: 10%)
        year: Year (default: current year - 1)
        api_key: UN Comtrade API subscription key
    
    Returns:
        Critical trade dependencies
    """
    if not api_key:
        return {
            'error': 'API key required',
            'message': 'UN Comtrade data endpoint requires a subscription key'
        }
    
    # Get both imports and exports
    import_partners = get_top_trade_partners(reporter, 'M', year, limit=50, api_key=api_key)
    export_partners = get_top_trade_partners(reporter, 'X', year, limit=50, api_key=api_key)
    
    if 'error' in import_partners or 'error' in export_partners:
        return {'error': 'Failed to fetch trade data'}
    
    import_total = import_partners.get('total_trade_value', 0)
    export_total = export_partners.get('total_trade_value', 0)
    
    dependencies = {
        'import_dependencies': [],
        'export_dependencies': [],
        'critical_partners': set()
    }
    
    # Analyze imports
    for partner in import_partners.get('top_partners', []):
        value = partner.get('primaryValue', 0)
        share = (value / import_total * 100) if import_total > 0 else 0
        
        if share >= threshold:
            dep = {
                'partner': partner.get('partnerDesc', 'Unknown'),
                'value': value,
                'share': round(share, 2)
            }
            dependencies['import_dependencies'].append(dep)
            dependencies['critical_partners'].add(partner.get('partnerDesc', 'Unknown'))
    
    # Analyze exports
    for partner in export_partners.get('top_partners', []):
        value = partner.get('primaryValue', 0)
        share = (value / export_total * 100) if export_total > 0 else 0
        
        if share >= threshold:
            dep = {
                'partner': partner.get('partnerDesc', 'Unknown'),
                'value': value,
                'share': round(share, 2)
            }
            dependencies['export_dependencies'].append(dep)
            dependencies['critical_partners'].add(partner.get('partnerDesc', 'Unknown'))
    
    dependencies['critical_partners'] = list(dependencies['critical_partners'])
    
    return {
        'reporter': reporter,
        'year': year or datetime.now().year - 1,
        'threshold': threshold,
        'dependencies': dependencies,
        'total_critical_partners': len(dependencies['critical_partners'])
    }


def cli_main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("""UN Comtrade Trade Flows

Commands:
  reporters [region]              List reporting countries
  partners                        List partner countries
  commodities [level]             List commodity codes (level: 2, 4, or 6)
  search-country <query>          Search for country by name or code
  search-commodity <query>        Search for commodity by description or HS code
  bilateral <reporter> <partner> [year] [flow]  Get bilateral trade flows
  top-partners <reporter> [flow] [year] [limit]  Get top trade partners
  trade-balance <reporter> [partner] [year]      Calculate trade balance
  commodity-trade <reporter> <commodity> [year] [flow]  Get commodity trade
  concentration <reporter> [year] [flow]         Analyze trade concentration (HHI)
  dependencies <reporter> [threshold] [year]     Identify critical dependencies

Flow types: M (imports), X (exports), RM (re-imports), RX (re-exports)

Examples:
  cli.py comtrade reporters
  cli.py comtrade search-country china
  cli.py comtrade search-commodity machinery
  cli.py comtrade bilateral USA CHN 2023 M
  cli.py comtrade top-partners USA X 2023 10
  cli.py comtrade concentration CHN 2023 X
  cli.py comtrade dependencies USA 10 2023

Note: Data endpoints require UN Comtrade API key (set COMTRADE_API_KEY env var)
      Reference data (countries, commodities) works without API key
""")
        sys.exit(0)
    
    import os
    api_key = os.getenv('COMTRADE_API_KEY')
    
    command = sys.argv[1]
    
    if command == 'reporters':
        region = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_reporters(region)
        
        if isinstance(result, list):
            print(f"\n📊 Reporting Countries ({len(result)} total)")
            print("=" * 80)
            for country in result[:50]:  # Show first 50
                code = country.get('reporterCodeIsoAlpha3', 'N/A')
                name = country.get('text', 'Unknown')
                print(f"  {code:5s} {name}")
            if len(result) > 50:
                print(f"\n... and {len(result) - 50} more")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == 'partners':
        result = get_partners()
        
        if isinstance(result, list):
            print(f"\n📊 Partner Countries ({len(result)} total)")
            print("=" * 80)
            for country in result[:50]:
                code = country.get('partnerCodeIsoAlpha3', country.get('reporterCodeIsoAlpha3', 'N/A'))
                name = country.get('text', 'Unknown')
                print(f"  {code:5s} {name}")
            if len(result) > 50:
                print(f"\n... and {len(result) - 50} more")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == 'commodities':
        level = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = get_commodities(level)
        
        if isinstance(result, list):
            print(f"\n📦 Commodity Codes")
            if level:
                print(f"Level: {level}-digit HS codes")
            print("=" * 80)
            for commodity in result[:50]:
                code = commodity.get('id', 'N/A')
                name = commodity.get('text', 'Unknown')
                print(f"  {code:10s} {name}")
            if len(result) > 50:
                print(f"\n... and {len(result) - 50} more")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == 'search-country':
        if len(sys.argv) < 3:
            print("Error: Missing search query")
            sys.exit(1)
        
        query = sys.argv[2]
        result = search_country(query)
        
        if isinstance(result, list):
            print(f"\n🔍 Search Results for '{query}' ({len(result)} matches)")
            print("=" * 80)
            for country in result:
                code = country.get('reporterCodeIsoAlpha3', 'N/A')
                name = country.get('text', 'Unknown')
                numeric = country.get('reporterCode', 'N/A')
                print(f"  {code} ({numeric:3}) - {name}")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == 'search-commodity':
        if len(sys.argv) < 3:
            print("Error: Missing search query")
            sys.exit(1)
        
        query = sys.argv[2]
        result = search_commodity(query)
        
        if isinstance(result, list):
            print(f"\n🔍 Commodity Search Results for '{query}' ({len(result)} matches)")
            print("=" * 80)
            for commodity in result:
                code = commodity.get('id', 'N/A')
                name = commodity.get('text', 'Unknown')
                level = commodity.get('aggrLevel', 'N/A')
                print(f"  {code:10s} (L{level}) {name}")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == 'bilateral':
        if len(sys.argv) < 4:
            print("Error: Missing reporter and/or partner")
            sys.exit(1)
        
        reporter = sys.argv[2]
        partner = sys.argv[3]
        year = int(sys.argv[4]) if len(sys.argv) > 4 else None
        flow = sys.argv[5] if len(sys.argv) > 5 else 'M'
        
        result = get_bilateral_trade(reporter, partner, year, flow, 'TOTAL', api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'top-partners':
        if len(sys.argv) < 3:
            print("Error: Missing reporter")
            sys.exit(1)
        
        reporter = sys.argv[2]
        flow = sys.argv[3] if len(sys.argv) > 3 else 'M'
        year = int(sys.argv[4]) if len(sys.argv) > 4 else None
        limit = int(sys.argv[5]) if len(sys.argv) > 5 else 20
        
        result = get_top_trade_partners(reporter, flow, year, limit, api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'trade-balance':
        if len(sys.argv) < 3:
            print("Error: Missing reporter")
            sys.exit(1)
        
        reporter = sys.argv[2]
        partner = sys.argv[3] if len(sys.argv) > 3 else None
        year = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        result = get_trade_balance(reporter, partner, year, api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'commodity-trade':
        if len(sys.argv) < 4:
            print("Error: Missing reporter and/or commodity")
            sys.exit(1)
        
        reporter = sys.argv[2]
        commodity = sys.argv[3]
        year = int(sys.argv[4]) if len(sys.argv) > 4 else None
        flow = sys.argv[5] if len(sys.argv) > 5 else 'M'
        
        result = get_commodity_trade(reporter, commodity, year, flow, api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'concentration':
        if len(sys.argv) < 3:
            print("Error: Missing reporter")
            sys.exit(1)
        
        reporter = sys.argv[2]
        year = int(sys.argv[3]) if len(sys.argv) > 3 else None
        flow = sys.argv[4] if len(sys.argv) > 4 else 'X'
        
        result = analyze_trade_concentration(reporter, year, flow, api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'dependencies':
        if len(sys.argv) < 3:
            print("Error: Missing reporter")
            sys.exit(1)
        
        reporter = sys.argv[2]
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
        year = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        result = get_trade_dependencies(reporter, threshold, year, api_key)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    cli_main()
