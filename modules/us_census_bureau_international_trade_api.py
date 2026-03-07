#!/usr/bin/env python3
"""
U.S. Census Bureau International Trade API

Monthly international trade data for the U.S., including exports, imports, 
and trade balances by country and commodity. Supports analysis of U.S.-centric 
supply chains and trade disruptions.

Source: https://www.census.gov/data/developers/data-sets/international-trade.html
Category: Trade & Supply Chain
Free tier: True (no API key required for basic access)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# Census Bureau API Configuration
CENSUS_TIMESERIES_BASE = "https://api.census.gov/data/timeseries/intltrade"
CENSUS_ANNUAL_BASE = "https://api.census.gov/data"

# Country code mappings (Census Bureau uses numeric codes)
MAJOR_TRADING_PARTNERS = {
    '5700': 'China',
    '2010': 'Mexico',
    '1220': 'Canada',
    '5880': 'Japan',
    '4280': 'Germany',
    '5800': 'South Korea',
    '4120': 'United Kingdom',
    '5330': 'India',
    '4279': 'France',
    '4759': 'Italy',
    '5830': 'Taiwan',
    '5520': 'Vietnam',
    '5330': 'Ireland',
    '4039': 'Switzerland',
    '3510': 'Brazil'
}


def _make_request(url: str, params: Dict) -> Dict:
    """
    Helper function to make API requests with error handling
    
    Args:
        url: Full API URL
        params: Query parameters
    
    Returns:
        Dict with response data or error
    """
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Census API returns data as array of arrays where first row is headers
        if not data or len(data) < 2:
            return {
                'success': False,
                'error': 'No data returned from API'
            }
        
        # Convert to list of dicts
        headers = data[0]
        rows = []
        for row in data[1:]:
            rows.append(dict(zip(headers, row)))
        
        return {
            'success': True,
            'data': rows,
            'count': len(rows)
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout - Census API slow to respond'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}'
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Invalid JSON response from API'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def get_us_trade_balance(country: str, year: int) -> Dict:
    """
    Get U.S. trade balance with a specific country for a given year
    
    Args:
        country: Country name or numeric code (e.g., '5700' for China, or 'China')
        year: Year (e.g., 2024, 2023)
    
    Returns:
        Dict with exports, imports, and trade balance
    """
    try:
        # Convert country name to code if needed
        cty_code = country
        if not country.isdigit():
            # Search for country in mappings
            country_upper = country.upper()
            for code, name in MAJOR_TRADING_PARTNERS.items():
                if name.upper() == country_upper:
                    cty_code = code
                    break
        
        # Fetch all months for the year and filter
        total_exports = 0
        total_imports = 0
        country_name = country
        months_found = 0
        
        for month in range(1, 13):
            time_param = f"{year}-{month:02d}"
            
            # Get exports
            exports_url = f"{CENSUS_TIMESERIES_BASE}/exports/hs"
            exports_result = _make_request(
                exports_url,
                {
                    'get': 'CTY_CODE,CTY_NAME,ALL_VAL_MO',
                    'time': time_param
                }
            )
            
            # Get imports
            imports_url = f"{CENSUS_TIMESERIES_BASE}/imports/enduse"
            imports_result = _make_request(
                imports_url,
                {
                    'get': 'CTY_CODE,CTY_NAME,GEN_VAL_MO',
                    'time': time_param
                }
            )
            
            if exports_result['success'] and imports_result['success']:
                # Filter for specific country
                for row in exports_result['data']:
                    if row.get('CTY_CODE') == cty_code:
                        total_exports += float(row.get('ALL_VAL_MO', 0) or 0)
                        country_name = row.get('CTY_NAME', country)
                        months_found += 1
                        break
                
                for row in imports_result['data']:
                    if row.get('CTY_CODE') == cty_code:
                        total_imports += float(row.get('GEN_VAL_MO', 0) or 0)
                        break
        
        if months_found == 0:
            return {
                'success': False,
                'error': f'No data found for country code {cty_code} in year {year}'
            }
        
        trade_balance = total_exports - total_imports
        
        return {
            'success': True,
            'country': country_name,
            'country_code': cty_code,
            'year': year,
            'exports_usd': total_exports,
            'imports_usd': total_imports,
            'trade_balance_usd': trade_balance,
            'surplus': trade_balance > 0,
            'monthly_data_points': months_found,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Error calculating trade balance: {str(e)}'
        }


def get_top_trading_partners(year: int, flow: str = 'exports', limit: int = 10) -> Dict:
    """
    Get top U.S. trading partners by exports or imports
    
    Args:
        year: Year (e.g., 2023)
        flow: 'exports' or 'imports'
        limit: Number of top partners to return (default 10)
    
    Returns:
        Dict with ranked list of top trading partners
    """
    try:
        if flow not in ['exports', 'imports']:
            return {
                'success': False,
                'error': "flow must be 'exports' or 'imports'"
            }
        
        # Fetch data for all countries across all months
        if flow == 'exports':
            url = f"{CENSUS_TIMESERIES_BASE}/exports/hs"
            value_field = 'ALL_VAL_MO'
        else:
            url = f"{CENSUS_TIMESERIES_BASE}/imports/enduse"
            value_field = 'GEN_VAL_MO'
        
        # Aggregate by country across all months
        country_totals = defaultdict(lambda: {'country_code': '', 'country_name': '', 'total_value': 0})
        
        for month in range(1, 13):
            time_param = f"{year}-{month:02d}"
            
            result = _make_request(
                url,
                {
                    'get': f'CTY_CODE,CTY_NAME,{value_field}',
                    'time': time_param
                }
            )
            
            if result['success']:
                for row in result['data']:
                    cty_code = row.get('CTY_CODE')
                    cty_name = row.get('CTY_NAME')
                    value = float(row.get(value_field, 0) or 0)
                    
                    if cty_code and cty_code != '-':  # Skip totals
                        country_totals[cty_code]['country_code'] = cty_code
                        country_totals[cty_code]['country_name'] = cty_name
                        country_totals[cty_code]['total_value'] += value
        
        if not country_totals:
            return {
                'success': False,
                'error': f'No data found for year {year}'
            }
        
        # Sort by total value descending
        sorted_partners = sorted(
            country_totals.values(),
            key=lambda x: x['total_value'],
            reverse=True
        )[:limit]
        
        # Add rankings and format values
        for idx, partner in enumerate(sorted_partners, 1):
            partner['rank'] = idx
            partner['value_usd'] = partner.pop('total_value')
        
        return {
            'success': True,
            'year': year,
            'flow': flow,
            'top_partners': sorted_partners,
            'count': len(sorted_partners),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching top trading partners: {str(e)}'
        }


def get_commodity_trade(hs_code: str, year: int, flow: str = 'exports') -> Dict:
    """
    Get trade data for a specific commodity by HS code
    
    Args:
        hs_code: Harmonized System code (e.g., '01' for animals, '8703' for cars)
        year: Year (e.g., 2023)
        flow: 'exports' or 'imports'
    
    Returns:
        Dict with commodity trade value and details
    """
    try:
        if flow not in ['exports', 'imports']:
            return {
                'success': False,
                'error': "flow must be 'exports' or 'imports'"
            }
        
        # Both exports and imports use HS codes
        if flow == 'exports':
            url = f"{CENSUS_TIMESERIES_BASE}/exports/hs"
            value_field = 'ALL_VAL_MO'
            comm_field = 'E_COMMODITY'
            desc_field = 'E_COMMODITY_LDESC'
        else:
            url = f"{CENSUS_TIMESERIES_BASE}/imports/hs"
            value_field = 'GEN_VAL_MO'
            comm_field = 'I_COMMODITY'
            desc_field = 'I_COMMODITY_LDESC'
        
        total_value = 0
        commodity_desc = 'Unknown'
        months_found = 0
        
        # Fetch all months and filter for HS code
        for month in range(1, 13):
            time_param = f"{year}-{month:02d}"
            
            result = _make_request(
                url,
                {
                    'get': f'{comm_field},{desc_field},{value_field}',
                    'time': time_param
                }
            )
            
            if result['success']:
                for row in result['data']:
                    if row.get(comm_field) == hs_code:
                        total_value += float(row.get(value_field, 0) or 0)
                        if commodity_desc == 'Unknown':
                            commodity_desc = row.get(desc_field, 'Unknown')
                        months_found += 1
                        break
        
        if months_found == 0:
            return {
                'success': False,
                'error': f'No data found for HS code {hs_code} in year {year}'
            }
        
        return {
            'success': True,
            'hs_code': hs_code,
            'commodity_description': commodity_desc,
            'year': year,
            'flow': flow,
            'total_value_usd': total_value,
            'monthly_data_points': months_found,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching commodity trade: {str(e)}'
        }


def get_trade_summary(year: int, month: Optional[int] = None) -> Dict:
    """
    Get U.S. trade summary for a specific period
    
    Args:
        year: Year (e.g., 2023)
        month: Optional month (1-12). If None, returns annual summary
    
    Returns:
        Dict with total exports, imports, and trade balance
    """
    try:
        if month is not None and not 1 <= month <= 12:
            return {
                'success': False,
                'error': 'Month must be between 1 and 12'
            }
        
        total_exports = 0
        total_imports = 0
        
        # Determine which months to fetch
        months_to_fetch = [month] if month else range(1, 13)
        
        for m in months_to_fetch:
            time_param = f"{year}-{m:02d}"
            
            # Get total exports
            exports_url = f"{CENSUS_TIMESERIES_BASE}/exports/hs"
            exports_result = _make_request(exports_url, {'get': 'ALL_VAL_MO', 'time': time_param})
            
            # Get total imports  
            imports_url = f"{CENSUS_TIMESERIES_BASE}/imports/enduse"
            imports_result = _make_request(imports_url, {'get': 'GEN_VAL_MO', 'time': time_param})
            
            if exports_result['success'] and imports_result['success']:
                # Sum across all rows (all countries)
                total_exports += sum(float(row.get('ALL_VAL_MO', 0) or 0) for row in exports_result['data'])
                total_imports += sum(float(row.get('GEN_VAL_MO', 0) or 0) for row in imports_result['data'])
        
        if total_exports == 0 and total_imports == 0:
            return {
                'success': False,
                'error': f'No data found for period {year}-{month:02d if month else "all"}'
            }
        
        trade_balance = total_exports - total_imports
        period = f'{year}-{month:02d}' if month else str(year)
        
        return {
            'success': True,
            'period': period,
            'year': year,
            'month': month,
            'total_exports_usd': total_exports,
            'total_imports_usd': total_imports,
            'trade_balance_usd': trade_balance,
            'trade_deficit': trade_balance < 0,
            'deficit_pct_of_imports': abs(trade_balance / total_imports * 100) if total_imports > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching trade summary: {str(e)}'
        }


def list_major_trading_partners() -> List[Dict]:
    """
    List major U.S. trading partners with country codes
    
    Returns:
        List of dicts with country codes and names
    """
    return [
        {'code': code, 'name': name}
        for code, name in MAJOR_TRADING_PARTNERS.items()
    ]


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("U.S. Census Bureau International Trade API")
    print("=" * 60)
    
    # Example: Get trade summary for 2023
    print("\n1. Trade Summary (2023):")
    summary = get_trade_summary(2023)
    print(json.dumps(summary, indent=2))
    
    # Example: Get top trading partners
    print("\n2. Top 5 Export Partners (2023):")
    top_exports = get_top_trading_partners(2023, flow='exports', limit=5)
    print(json.dumps(top_exports, indent=2))
    
    # Example: Get trade balance with China
    print("\n3. Trade Balance with China (2023):")
    china_balance = get_us_trade_balance('5700', 2023)
    print(json.dumps(china_balance, indent=2))
