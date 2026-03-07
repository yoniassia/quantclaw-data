#!/usr/bin/env python3
"""
UN Comtrade Transport Mode API — International Trade Data Module

UN Comtrade API delivers international trade data segmented by transport modes 
(air, sea, land, rail, etc.), including shipping volumes and values for commodities. 
This module aids in quantifying global trade flows and infrastructure impacts on markets.

NOTE: As of 2025, UN Comtrade has migrated to comtradeplus.un.org and requires API key.
Free tier available at: https://comtradeplus.un.org/

Functions:
- get_trade_by_transport: Get trade data filtered by transport mode
- get_trade_summary: Get total trade summary for a reporter
- get_commodity_flows: Get commodity-specific trade flows
- get_transport_mode_breakdown: Get breakdown by all transport modes
- get_top_partners: Get top trading partners by value

Source: https://comtradeplus.un.org/
Category: Infrastructure & Transport
Free tier: True (requires registration for API key)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# UN Comtrade API Configuration
COMTRADE_BASE_URL = "https://comtradeapi.un.org/data/v1"
COMTRADE_REF_URL = "https://comtradeapi.un.org/files/v1/app/reference"
COMTRADE_API_KEY = os.environ.get("COMTRADE_API_KEY", "")

# Country code mapping (ISO3 to numeric)
COUNTRY_CODES = {
    'USA': 842,
    'CHN': 156,
    'JPN': 392,
    'DEU': 276,
    'GBR': 826,
    'FRA': 250,
    'IND': 356,
    'BRA': 76
}

# Transport mode codes mapping
TRANSPORT_MODES = {
    'sea': 1,
    'air': 2,
    'land': 3,
    'rail': 4,
    'mail': 5,
    'pipeline': 6,
    'inland_waterway': 7,
    'other': 8,
    'unknown': 9
}


def _get_country_code(iso3: str) -> int:
    """Convert ISO3 country code to numeric code."""
    return COUNTRY_CODES.get(iso3.upper(), 0)


def _check_api_key() -> Optional[str]:
    """Check if API key is configured."""
    if not COMTRADE_API_KEY:
        return "COMTRADE_API_KEY not set. Register at https://comtradeplus.un.org/ and add to .env"
    return None


def get_trade_by_transport(
    reporter: str = 'USA', 
    partner: str = 'CHN', 
    year: int = 2023, 
    mode: str = 'sea'
) -> Dict:
    """
    Get bilateral trade data filtered by transport mode.
    
    Args:
        reporter: Reporting country code (ISO3) (default: 'USA')
        partner: Partner country code (ISO3) (default: 'CHN')
        year: Year for trade data (default: 2023)
        mode: Transport mode - 'sea', 'air', 'land', 'rail', etc. (default: 'sea')
    
    Returns:
        Dict with trade values, counts, and metadata
    
    Example:
        >>> trade = get_trade_by_transport('USA', 'CHN', 2023, 'sea')
        >>> print(f"Sea trade value: ${trade.get('total_value', 0):,.0f}")
    """
    try:
        # Check API key
        error_msg = _check_api_key()
        if error_msg:
            return _create_mock_trade_data(reporter, partner, year, mode, error_msg)
        
        reporter_code = _get_country_code(reporter)
        partner_code = _get_country_code(partner)
        mode_code = TRANSPORT_MODES.get(mode.lower(), 1)
        
        if reporter_code == 0 or partner_code == 0:
            return _create_mock_trade_data(reporter, partner, year, mode, 
                                          "Country code not found in mapping")
        
        # API endpoint structure: /data/v1/get/{typeCode}/{freqCode}/{clCode}
        url = f"{COMTRADE_BASE_URL}/get/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'partnerCode': partner_code,
            'period': year,
            'motCode': mode_code,  # Mode of transport
            'flowCode': 'M,X'  # Import and Export
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': COMTRADE_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        
        # Calculate aggregates
        total_value = sum(float(r.get('primaryValue', 0)) for r in records)
        total_quantity = sum(float(r.get('netWgt', 0)) for r in records)
        
        result = {
            'reporter': reporter.upper(),
            'partner': partner.upper(),
            'year': year,
            'transport_mode': mode,
            'mode_code': mode_code,
            'total_value': total_value,
            'total_quantity_kg': total_quantity,
            'record_count': len(records),
            'records': records[:10],  # Sample of first 10
            'timestamp': datetime.now().isoformat(),
            'source': 'UN Comtrade'
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return _create_mock_trade_data(reporter, partner, year, mode, str(e))
    except Exception as e:
        return _create_mock_trade_data(reporter, partner, year, mode, 
                                       f'Unexpected error: {str(e)}')


def get_trade_summary(reporter: str = 'USA', year: int = 2023) -> Dict:
    """
    Get total trade summary for a reporting country.
    
    Args:
        reporter: Reporting country code (ISO3) (default: 'USA')
        year: Year for trade data (default: 2023)
    
    Returns:
        Dict with total imports, exports, balance, and top commodities
    
    Example:
        >>> summary = get_trade_summary('USA', 2023)
        >>> print(f"Trade balance: ${summary.get('trade_balance', 0):,.0f}")
    """
    try:
        error_msg = _check_api_key()
        if error_msg:
            return _create_mock_summary(reporter, year, error_msg)
        
        reporter_code = _get_country_code(reporter)
        if reporter_code == 0:
            return _create_mock_summary(reporter, year, "Country code not found")
        
        url = f"{COMTRADE_BASE_URL}/get/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'period': year,
            'flowCode': 'M,X'
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': COMTRADE_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        
        # Separate imports and exports
        imports = [r for r in records if r.get('flowCode') == 'M']
        exports = [r for r in records if r.get('flowCode') == 'X']
        
        total_imports = sum(float(r.get('primaryValue', 0)) for r in imports)
        total_exports = sum(float(r.get('primaryValue', 0)) for r in exports)
        
        result = {
            'reporter': reporter.upper(),
            'year': year,
            'total_imports': total_imports,
            'total_exports': total_exports,
            'trade_balance': total_exports - total_imports,
            'import_count': len(imports),
            'export_count': len(exports),
            'total_records': len(records),
            'timestamp': datetime.now().isoformat(),
            'source': 'UN Comtrade'
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return _create_mock_summary(reporter, year, str(e))
    except Exception as e:
        return _create_mock_summary(reporter, year, f'Unexpected error: {str(e)}')


def get_commodity_flows(
    commodity_code: str = 'TOTAL', 
    reporter: str = 'USA',
    year: int = 2023
) -> List[Dict]:
    """
    Get commodity-specific trade flows for a reporter.
    
    Args:
        commodity_code: HS commodity code (default: 'TOTAL')
        reporter: Reporting country code (ISO3) (default: 'USA')
        year: Year for trade data (default: 2023)
    
    Returns:
        List of trade flow dictionaries with partner, value, quantity
    
    Example:
        >>> flows = get_commodity_flows('TOTAL', 'USA', 2023)
        >>> print(f"Found {len(flows)} trade flows")
    """
    try:
        error_msg = _check_api_key()
        if error_msg:
            return [_create_mock_flow(reporter, year, error_msg)]
        
        reporter_code = _get_country_code(reporter)
        if reporter_code == 0:
            return [_create_mock_flow(reporter, year, "Country code not found")]
        
        url = f"{COMTRADE_BASE_URL}/get/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'period': year,
            'cmdCode': commodity_code
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': COMTRADE_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        
        # Transform to simplified flow records
        flows = []
        for r in records:
            flows.append({
                'partner': r.get('partnerDesc', 'Unknown'),
                'partner_code': r.get('partnerCode', ''),
                'flow': 'Import' if r.get('flowCode') == 'M' else 'Export',
                'value': float(r.get('primaryValue', 0)),
                'quantity_kg': float(r.get('netWgt', 0)),
                'commodity': r.get('cmdDesc', commodity_code),
                'year': year
            })
        
        return flows if flows else [_create_mock_flow(reporter, year, "No data")]
        
    except requests.exceptions.RequestException as e:
        return [_create_mock_flow(reporter, year, str(e))]
    except Exception as e:
        return [_create_mock_flow(reporter, year, f'Unexpected error: {str(e)}')]


def get_transport_mode_breakdown(
    reporter: str = 'USA', 
    year: int = 2023
) -> Dict:
    """
    Get trade breakdown by all transport modes (air/sea/land).
    
    Args:
        reporter: Reporting country code (ISO3) (default: 'USA')
        year: Year for trade data (default: 2023)
    
    Returns:
        Dict with breakdown by mode and total values
    
    Example:
        >>> breakdown = get_transport_mode_breakdown('USA', 2023)
        >>> print(f"Sea trade: ${breakdown['modes'].get('sea', {}).get('value', 0):,.0f}")
    """
    try:
        error_msg = _check_api_key()
        if error_msg:
            return _create_mock_breakdown(reporter, year, error_msg)
        
        reporter_code = _get_country_code(reporter)
        if reporter_code == 0:
            return _create_mock_breakdown(reporter, year, "Country code not found")
        
        url = f"{COMTRADE_BASE_URL}/get/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'period': year
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': COMTRADE_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        
        # Group by transport mode
        mode_totals = {}
        for r in records:
            mode_code = r.get('motCode', 9)
            value = float(r.get('primaryValue', 0))
            
            if mode_code not in mode_totals:
                mode_totals[mode_code] = 0
            mode_totals[mode_code] += value
        
        total_value = sum(mode_totals.values())
        
        # Map codes to names
        mode_names = {v: k for k, v in TRANSPORT_MODES.items()}
        modes_result = {}
        for code, value in mode_totals.items():
            mode_name = mode_names.get(code, 'unknown')
            modes_result[mode_name] = {
                'value': value,
                'share': value / total_value if total_value > 0 else 0
            }
        
        result = {
            'reporter': reporter.upper(),
            'year': year,
            'total_value': total_value,
            'modes': modes_result,
            'record_count': len(records),
            'timestamp': datetime.now().isoformat(),
            'source': 'UN Comtrade'
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return _create_mock_breakdown(reporter, year, str(e))
    except Exception as e:
        return _create_mock_breakdown(reporter, year, f'Unexpected error: {str(e)}')


def get_top_partners(
    reporter: str = 'USA', 
    year: int = 2023, 
    limit: int = 10
) -> List[Dict]:
    """
    Get top trading partners by total trade value.
    
    Args:
        reporter: Reporting country code (ISO3) (default: 'USA')
        year: Year for trade data (default: 2023)
        limit: Number of top partners to return (default: 10)
    
    Returns:
        List of dicts with partner country, trade value, imports, exports
    
    Example:
        >>> partners = get_top_partners('USA', 2023, 5)
        >>> for p in partners[:3]:
        ...     print(f"{p['partner']}: ${p['total_value']:,.0f}")
    """
    try:
        error_msg = _check_api_key()
        if error_msg:
            return _create_mock_partners(reporter, year, limit, error_msg)
        
        reporter_code = _get_country_code(reporter)
        if reporter_code == 0:
            return _create_mock_partners(reporter, year, limit, "Country code not found")
        
        url = f"{COMTRADE_BASE_URL}/get/C/A/HS"
        params = {
            'reporterCode': reporter_code,
            'period': year
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': COMTRADE_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        
        # Group by partner
        partner_stats = {}
        for r in records:
            partner = r.get('partnerDesc', 'Unknown')
            partner_code = r.get('partnerCode', '')
            value = float(r.get('primaryValue', 0))
            flow = r.get('flowCode', '')
            
            if partner not in partner_stats:
                partner_stats[partner] = {
                    'partner': partner,
                    'partner_code': partner_code,
                    'imports': 0,
                    'exports': 0,
                    'total_value': 0
                }
            
            if flow == 'M':  # Import
                partner_stats[partner]['imports'] += value
            elif flow == 'X':  # Export
                partner_stats[partner]['exports'] += value
            
            partner_stats[partner]['total_value'] += value
        
        # Sort by total value and take top N
        sorted_partners = sorted(
            partner_stats.values(), 
            key=lambda x: x['total_value'], 
            reverse=True
        )
        
        top_partners = sorted_partners[:limit]
        
        # Add rankings
        for idx, p in enumerate(top_partners, 1):
            p['rank'] = idx
            p['year'] = year
        
        return top_partners if top_partners else _create_mock_partners(reporter, year, limit, "No data")
        
    except requests.exceptions.RequestException as e:
        return _create_mock_partners(reporter, year, limit, str(e))
    except Exception as e:
        return _create_mock_partners(reporter, year, limit, f'Unexpected error: {str(e)}')


# Mock data generators for when API is unavailable
def _create_mock_trade_data(reporter: str, partner: str, year: int, mode: str, error: str) -> Dict:
    """Create mock trade data when API is unavailable."""
    return {
        'reporter': reporter.upper(),
        'partner': partner.upper(),
        'year': year,
        'transport_mode': mode,
        'mode_code': TRANSPORT_MODES.get(mode.lower(), 1),
        'total_value': 50000000000.0,  # $50B mock
        'total_quantity_kg': 10000000000.0,  # 10M tons mock
        'record_count': 150,
        'records': [],
        'timestamp': datetime.now().isoformat(),
        'source': 'UN Comtrade (mock)',
        'note': f'Mock data - API unavailable: {error}'
    }


def _create_mock_summary(reporter: str, year: int, error: str) -> Dict:
    """Create mock summary when API is unavailable."""
    return {
        'reporter': reporter.upper(),
        'year': year,
        'total_imports': 2500000000000.0,  # $2.5T mock
        'total_exports': 1800000000000.0,  # $1.8T mock
        'trade_balance': -700000000000.0,
        'import_count': 5000,
        'export_count': 4500,
        'total_records': 9500,
        'timestamp': datetime.now().isoformat(),
        'source': 'UN Comtrade (mock)',
        'note': f'Mock data - API unavailable: {error}'
    }


def _create_mock_flow(reporter: str, year: int, error: str) -> Dict:
    """Create mock flow when API is unavailable."""
    return {
        'partner': 'Mock Partner',
        'partner_code': '999',
        'flow': 'Import',
        'value': 100000000.0,
        'quantity_kg': 50000000.0,
        'commodity': 'TOTAL',
        'year': year,
        'note': f'Mock data - API unavailable: {error}'
    }


def _create_mock_breakdown(reporter: str, year: int, error: str) -> Dict:
    """Create mock breakdown when API is unavailable."""
    return {
        'reporter': reporter.upper(),
        'year': year,
        'total_value': 4300000000000.0,  # $4.3T mock
        'modes': {
            'sea': {'value': 2795000000000.0, 'share': 0.65},
            'air': {'value': 860000000000.0, 'share': 0.20},
            'land': {'value': 645000000000.0, 'share': 0.15}
        },
        'record_count': 9500,
        'timestamp': datetime.now().isoformat(),
        'source': 'UN Comtrade (mock)',
        'note': f'Mock data - API unavailable: {error}'
    }


def _create_mock_partners(reporter: str, year: int, limit: int, error: str) -> List[Dict]:
    """Create mock partners when API is unavailable."""
    mock_partners = [
        {'partner': 'China', 'partner_code': '156', 'imports': 450000000000.0, 'exports': 120000000000.0},
        {'partner': 'Canada', 'partner_code': '124', 'imports': 280000000000.0, 'exports': 250000000000.0},
        {'partner': 'Mexico', 'partner_code': '484', 'imports': 350000000000.0, 'exports': 240000000000.0},
        {'partner': 'Japan', 'partner_code': '392', 'imports': 130000000000.0, 'exports': 70000000000.0},
        {'partner': 'Germany', 'partner_code': '276', 'imports': 120000000000.0, 'exports': 60000000000.0}
    ]
    
    result = []
    for idx, p in enumerate(mock_partners[:limit], 1):
        result.append({
            'rank': idx,
            'partner': p['partner'],
            'partner_code': p['partner_code'],
            'imports': p['imports'],
            'exports': p['exports'],
            'total_value': p['imports'] + p['exports'],
            'year': year,
            'note': f'Mock data - API unavailable: {error}'
        })
    
    return result


if __name__ == "__main__":
    # Test the module
    print(json.dumps({
        "module": "un_comtrade_transport_mode_api",
        "status": "active",
        "functions": [
            "get_trade_by_transport",
            "get_trade_summary",
            "get_commodity_flows",
            "get_transport_mode_breakdown",
            "get_top_partners"
        ],
        "source": "https://comtradeplus.un.org/",
        "note": "Requires COMTRADE_API_KEY in .env - Register at comtradeplus.un.org",
        "author": "QuantClaw Data NightBuilder"
    }, indent=2))
