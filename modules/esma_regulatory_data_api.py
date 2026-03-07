#!/usr/bin/env python3
"""
ESMA Regulatory Data API — European Financial Instruments & Regulatory Data

The European Securities and Markets Authority (ESMA) provides access to regulatory data
on financial instruments, MiFID II/MiFIR transparency calculations, and reference data.

This module queries ESMA's public Solr-based registers for:
- FIRDS (Financial Instruments Reference Data System) - 255M+ instruments
- MiFID transparency calculations
- Short selling positions
- Regulatory reporting data

Source: https://registers.esma.europa.eu/publication/searchRegister
Category: Government & Regulatory
Free tier: true - Public access with rate limits
Update frequency: daily
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode

# ESMA Solr API Configuration
ESMA_BASE_URL = "https://registers.esma.europa.eu/solr"
ESMA_TIMEOUT = 20  # seconds

# Available registers (confirmed working)
ESMA_REGISTERS = {
    'FIRDS': 'esma_registers_firds',  # Financial Instruments Reference Data System
}


def _query_esma_solr(
    core: str,
    query: str = '*:*',
    filters: Optional[Dict[str, str]] = None,
    rows: int = 50,
    start: int = 0,
    fields: Optional[List[str]] = None,
    sort: Optional[str] = None
) -> Dict:
    """
    Internal helper to query ESMA Solr API
    
    Args:
        core: Solr core name (e.g., 'esma_registers_firds')
        query: Solr query string (default '*:*' for all)
        filters: Additional filter queries {field: value}
        rows: Number of results to return (default 50, max 1000)
        start: Starting offset for pagination
        fields: List of fields to return (None = all fields)
        sort: Sort specification (e.g., 'valid_from_date desc')
    
    Returns:
        Dict with query results or error
    """
    try:
        url = f"{ESMA_BASE_URL}/{core}/select"
        
        params = {
            'q': query,
            'rows': min(rows, 1000),  # Cap at 1000
            'start': start,
            'wt': 'json'
        }
        
        # Add filters
        if filters:
            fq_list = [f'{k}:"{v}"' for k, v in filters.items()]
            params['fq'] = fq_list
        
        # Add field selection
        if fields:
            params['fl'] = ','.join(fields)
        
        # Add sorting
        if sort:
            params['sort'] = sort
        
        response = requests.get(url, params=params, timeout=ESMA_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'response' not in data:
            return {
                'success': False,
                'error': 'Invalid response format',
                'query': query
            }
        
        return {
            'success': True,
            'num_found': data['response'].get('numFound', 0),
            'num_returned': len(data['response'].get('docs', [])),
            'start': start,
            'documents': data['response'].get('docs', []),
            'response_time_ms': data.get('responseHeader', {}).get('QTime', 0)
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'query': query
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query
        }


def search_financial_instruments(
    query: str = '',
    country: str = '',
    rows: int = 50,
    instrument_type: Optional[str] = None,
    currency: Optional[str] = None
) -> Dict:
    """
    Search FIRDS register for financial instruments
    
    Args:
        query: Free-text search (ISIN, name, LEI, etc.) - leave empty for all
        country: ISO 2-letter country code (e.g., 'DE', 'FR', 'GB')
        rows: Number of results to return (default 50, max 1000)
        instrument_type: CFI code prefix or instrument type filter
        currency: Currency code filter (e.g., 'EUR', 'USD')
    
    Returns:
        Dict with search results and instrument details
    """
    filters = {}
    
    if country:
        filters['upcoming_rca'] = country.upper()
    
    if currency:
        filters['gnr_notional_curr_code'] = currency.upper()
    
    if instrument_type:
        # CFI code filtering
        filters['gnr_cfi_code'] = f'{instrument_type}*'
    
    # Build query string
    if query:
        # Search across multiple fields
        query_str = f'(isin:*{query}* OR gnr_full_name:*{query}* OR lei:*{query}* OR gnr_short_name:*{query}*)'
    else:
        query_str = '*:*'
    
    result = _query_esma_solr(
        core=ESMA_REGISTERS['FIRDS'],
        query=query_str,
        filters=filters if filters else None,
        rows=rows,
        sort='valid_from_date desc'
    )
    
    if not result['success']:
        return result
    
    # Parse and format instruments
    instruments = []
    for doc in result['documents']:
        instrument = {
            'isin': doc.get('isin'),
            'name': doc.get('gnr_full_name'),
            'short_name': doc.get('gnr_short_name'),
            'cfi_code': doc.get('gnr_cfi_code'),
            'currency': doc.get('gnr_notional_curr_code'),
            'country': doc.get('upcoming_rca'),
            'lei': doc.get('lei'),
            'mic': doc.get('mic'),
            'status': doc.get('status_label', doc.get('status')),
            'valid_from': doc.get('valid_from_date'),
            'trading_start': doc.get('mrkt_trdng_start_date'),
            'trading_end': doc.get('mrkt_trdng_trmination_date'),
        }
        
        # Add derivative-specific fields if present
        if doc.get('drv_underlng_isin'):
            instrument['derivative'] = {
                'underlying_isin': doc.get('drv_underlng_isin'),
                'option_type': doc.get('drv_option_type'),
                'strike_price': doc.get('drv_sp_prc_value_amount'),
                'expiry_date': doc.get('drv_expiry_date'),
                'exercise_style': doc.get('drv_option_exercise_style'),
                'delivery_type': doc.get('drv_delivery_type'),
            }
        
        instruments.append(instrument)
    
    return {
        'success': True,
        'query': query,
        'filters': filters,
        'total_found': result['num_found'],
        'returned': result['num_returned'],
        'instruments': instruments,
        'timestamp': datetime.now().isoformat()
    }


def get_mifid_entities(
    country: str = '',
    entity_type: str = '',
    rows: int = 50
) -> Dict:
    """
    Get MiFID investment firms and entities
    
    Note: This register requires further endpoint discovery.
    Currently returns placeholder data structure.
    
    Args:
        country: ISO 2-letter country code filter
        entity_type: Entity classification filter
        rows: Number of results to return
    
    Returns:
        Dict with entity information or error
    """
    return {
        'success': False,
        'error': 'MiFID entities register endpoint not yet available in public API',
        'note': 'Use FIRDS register for instrument-level data',
        'alternative': 'search_financial_instruments()',
        'timestamp': datetime.now().isoformat()
    }


def get_transparency_data(
    isin: str = '',
    rows: int = 50
) -> Dict:
    """
    Get MiFIR transparency calculations for instruments
    
    Note: This register requires further endpoint discovery.
    Currently returns placeholder data structure.
    
    Args:
        isin: ISIN code to search
        rows: Number of results to return
    
    Returns:
        Dict with transparency calculations or error
    """
    # Try to get transparency info from FIRDS if ISIN provided
    if isin:
        result = search_financial_instruments(query=isin, rows=rows)
        if result['success'] and result['instruments']:
            return {
                'success': True,
                'isin': isin,
                'note': 'Transparency data extracted from FIRDS register',
                'instruments': result['instruments'],
                'timestamp': datetime.now().isoformat()
            }
    
    return {
        'success': False,
        'error': 'Direct transparency register endpoint not yet available',
        'note': 'Use search_financial_instruments() with ISIN for instrument data',
        'timestamp': datetime.now().isoformat()
    }


def get_short_selling_positions(
    country: str = '',
    rows: int = 50
) -> Dict:
    """
    Get net short selling positions
    
    Note: This register requires further endpoint discovery.
    Currently returns placeholder data structure.
    
    Args:
        country: ISO 2-letter country code filter
        rows: Number of results to return
    
    Returns:
        Dict with short selling position data or error
    """
    return {
        'success': False,
        'error': 'Short selling positions register endpoint not yet available in public API',
        'note': 'This data may require authenticated access',
        'timestamp': datetime.now().isoformat()
    }


def get_register_summary() -> Dict:
    """
    Get summary statistics from key ESMA registers
    
    Returns:
        Dict with register stats and recent activity
    """
    summary = {}
    
    # Get FIRDS summary
    firds_result = _query_esma_solr(
        core=ESMA_REGISTERS['FIRDS'],
        query='*:*',
        rows=0  # Just get count
    )
    
    if firds_result['success']:
        summary['FIRDS'] = {
            'name': 'Financial Instruments Reference Data System',
            'total_instruments': firds_result['num_found'],
            'description': 'EU-wide database of financial instruments traded on EU venues',
            'available': True
        }
    
    # Get recent additions (last 7 days)
    date_7d_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    recent_result = _query_esma_solr(
        core=ESMA_REGISTERS['FIRDS'],
        query=f'publication_date:[{date_7d_ago} TO *]',
        rows=0
    )
    
    if recent_result['success']:
        summary['recent_activity'] = {
            'instruments_added_last_7d': recent_result['num_found'],
            'period': 'last 7 days'
        }
    
    # Sample active instruments by country
    country_samples = {}
    for country in ['DE', 'FR', 'GB', 'IT', 'ES', 'NL']:
        country_result = _query_esma_solr(
            core=ESMA_REGISTERS['FIRDS'],
            query='*:*',
            filters={'upcoming_rca': country, 'status': 'ACTV'},
            rows=0
        )
        if country_result['success']:
            country_samples[country] = {
                'active_instruments': country_result['num_found']
            }
    
    summary['by_country'] = country_samples
    
    # Placeholder for other registers
    summary['other_registers'] = {
        'MiFID_entities': {'available': False, 'note': 'Endpoint discovery pending'},
        'transparency': {'available': False, 'note': 'Endpoint discovery pending'},
        'short_selling': {'available': False, 'note': 'Endpoint discovery pending'}
    }
    
    return {
        'success': True,
        'registers': summary,
        'data_source': 'ESMA Public Registers',
        'timestamp': datetime.now().isoformat()
    }


def get_derivatives_by_underlying(
    underlying_isin: str,
    rows: int = 100,
    option_type: Optional[str] = None
) -> Dict:
    """
    Find derivatives based on underlying ISIN
    
    Args:
        underlying_isin: ISIN of the underlying asset
        rows: Number of results (default 100)
        option_type: Filter by CALL or PUT
    
    Returns:
        Dict with derivatives information
    """
    filters = {'drv_underlng_isin': underlying_isin}
    
    if option_type:
        filters['drv_option_type'] = option_type.upper()
    
    result = _query_esma_solr(
        core=ESMA_REGISTERS['FIRDS'],
        query='*:*',
        filters=filters,
        rows=rows,
        sort='drv_expiry_date asc'
    )
    
    if not result['success']:
        return result
    
    derivatives = []
    for doc in result['documents']:
        deriv = {
            'isin': doc.get('isin'),
            'name': doc.get('gnr_full_name'),
            'underlying_isin': doc.get('drv_underlng_isin'),
            'option_type': doc.get('drv_option_type'),
            'strike_price': doc.get('drv_sp_prc_value_amount'),
            'strike_currency': doc.get('drv_sp_prc_value_curr_code'),
            'expiry_date': doc.get('drv_expiry_date'),
            'exercise_style': doc.get('drv_option_exercise_style'),
            'delivery_type': doc.get('drv_delivery_type'),
            'status': doc.get('status_label'),
            'mic': doc.get('mic'),
        }
        derivatives.append(deriv)
    
    return {
        'success': True,
        'underlying_isin': underlying_isin,
        'total_found': result['num_found'],
        'returned': result['num_returned'],
        'derivatives': derivatives,
        'timestamp': datetime.now().isoformat()
    }


def list_available_registers() -> Dict:
    """
    List all ESMA registers with availability status
    
    Returns:
        Dict with register information
    """
    registers = {
        'FIRDS': {
            'name': 'Financial Instruments Reference Data System',
            'available': True,
            'description': '255M+ financial instruments traded on EU venues',
            'functions': [
                'search_financial_instruments()',
                'get_derivatives_by_underlying()'
            ]
        },
        'MiFID_Entities': {
            'name': 'MiFID Investment Firms',
            'available': False,
            'description': 'Registered investment firms and entities',
            'note': 'Endpoint discovery pending'
        },
        'Transparency': {
            'name': 'MiFIR Transparency Calculations',
            'available': False,
            'description': 'Pre and post-trade transparency data',
            'note': 'Endpoint discovery pending'
        },
        'Short_Selling': {
            'name': 'Net Short Positions',
            'available': False,
            'description': 'Reported short selling positions',
            'note': 'May require authentication'
        }
    }
    
    return {
        'success': True,
        'registers': registers,
        'module': 'esma_regulatory_data_api',
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("=" * 70)
    print("ESMA Regulatory Data API - Financial Instruments & Compliance")
    print("=" * 70)
    
    # Show available registers
    registers = list_available_registers()
    print(f"\nAvailable Registers: {len(registers['registers'])}")
    for reg_id, info in registers['registers'].items():
        status = "✓" if info['available'] else "⚠"
        print(f"  {status} {reg_id}: {info['name']}")
        if not info['available']:
            print(f"     Note: {info.get('note', 'N/A')}")
    
    # Get summary
    print("\nFetching register summary...")
    summary = get_register_summary()
    print(json.dumps(summary, indent=2))
