#!/usr/bin/env python3
"""
CFTC Commitments of Traders API — Weekly Market Positioning Data

Provides weekly reports on futures and options positions held by traders in commodity markets,
including disaggregated data for managed money, producers/merchants, and swap dealers.
Essential for analyzing market positioning and sentiment in commodities and financial futures.

Source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
Category: Government & Regulatory
Free tier: True
Update frequency: Weekly (Tuesday 3:30 PM ET)
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import requests
import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

# CFTC COT Report URLs
CFTC_URLS = {
    'futures_only': 'https://www.cftc.gov/dea/newcot/deafut.txt',
    'futures_options': 'https://www.cftc.gov/dea/newcot/deacmxsf.txt',
    'disaggregated': 'https://www.cftc.gov/dea/newcot/FinFutWk.txt',
    'traders_in_financial_futures': 'https://www.cftc.gov/dea/newcot/FinFutWk.txt',
    'historical_base': 'https://www.cftc.gov/files/dea/history/'
}

def get_current_cot_report(report_type: str = 'futures_only') -> Dict:
    """
    Fetch the latest Commitments of Traders report.
    
    Args:
        report_type: Type of report - 'futures_only', 'futures_options', or 'disaggregated'
        
    Returns:
        Dict with parsed report data including markets and positions
        
    Example:
        >>> report = get_current_cot_report('futures_only')
        >>> print(report['report_date'])
        >>> print(len(report['markets']))
    """
    try:
        url = CFTC_URLS.get(report_type, CFTC_URLS['futures_only'])
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse the fixed-width text format
        lines = response.text.strip().split('\n')
        
        if len(lines) < 3:
            return {
                'error': 'Invalid report format',
                'report_type': report_type,
                'status': 'failed'
            }
        
        # Extract report date from header (usually in first few lines)
        report_date = _extract_report_date(lines)
        
        # Parse data lines (skip headers)
        markets = []
        header_found = False
        
        for line in lines:
            # Skip empty lines and separators
            if not line.strip() or line.startswith('---') or line.startswith('==='):
                continue
                
            # Look for data lines (they contain market codes)
            if re.search(r'\d{6}', line):  # Market code pattern
                market_data = _parse_cot_line(line, report_type)
                if market_data:
                    markets.append(market_data)
        
        return {
            'report_date': report_date,
            'report_type': report_type,
            'markets_count': len(markets),
            'markets': markets,
            'status': 'success',
            'fetched_at': datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to fetch report: {str(e)}',
            'report_type': report_type,
            'status': 'failed'
        }
    except Exception as e:
        return {
            'error': f'Parse error: {str(e)}',
            'report_type': report_type,
            'status': 'failed'
        }

def get_disaggregated_report() -> Dict:
    """
    Fetch the disaggregated Commitments of Traders report.
    This report breaks down positions by trader category:
    - Producer/Merchant/Processor/User
    - Swap Dealers
    - Managed Money
    - Other Reportables
    
    Returns:
        Dict with disaggregated position data
    """
    return get_current_cot_report('disaggregated')

def search_by_market(market_name: str, report_data: Optional[Dict] = None) -> List[Dict]:
    """
    Search for a specific market in COT report data.
    
    Args:
        market_name: Market/commodity name to search (e.g., 'CRUDE OIL', 'S&P 500', 'GOLD')
        report_data: Optional pre-fetched report data. If None, fetches fresh data.
        
    Returns:
        List of matching market entries
        
    Example:
        >>> results = search_by_market('CRUDE OIL')
        >>> for r in results:
        ...     print(r['market_name'], r['open_interest'])
    """
    if report_data is None:
        report_data = get_current_cot_report('futures_only')
    
    if report_data.get('status') != 'success':
        return []
    
    market_name_upper = market_name.upper()
    matches = []
    
    for market in report_data.get('markets', []):
        if market_name_upper in market.get('market_name', '').upper():
            matches.append(market)
    
    return matches

def get_net_positions(market_name: str) -> Dict:
    """
    Calculate net long/short positions for commercials and non-commercials.
    
    Args:
        market_name: Market/commodity name (e.g., 'CRUDE OIL', 'GOLD')
        
    Returns:
        Dict with net positions:
        - commercial_net: Net position of commercial traders (long - short)
        - noncommercial_net: Net position of non-commercial traders (long - short)
        - market_name: Market identifier
        - open_interest: Total open interest
        - report_date: Report date
        
    Example:
        >>> positions = get_net_positions('CRUDE OIL')
        >>> print(f"Commercial net: {positions['commercial_net']:,}")
        >>> print(f"Non-commercial net: {positions['noncommercial_net']:,}")
    """
    report = get_current_cot_report('futures_only')
    
    if report.get('status') != 'success':
        return {
            'error': 'Failed to fetch report',
            'market_name': market_name
        }
    
    matches = search_by_market(market_name, report)
    
    if not matches:
        return {
            'error': 'Market not found',
            'market_name': market_name,
            'suggestion': 'Try broader search terms like CRUDE, GOLD, S&P'
        }
    
    # Use first match (or aggregate if multiple)
    market = matches[0]
    
    commercial_long = market.get('commercial_long', 0)
    commercial_short = market.get('commercial_short', 0)
    noncommercial_long = market.get('noncommercial_long', 0)
    noncommercial_short = market.get('noncommercial_short', 0)
    
    return {
        'market_name': market.get('market_name'),
        'market_code': market.get('market_code'),
        'report_date': report.get('report_date'),
        'open_interest': market.get('open_interest', 0),
        'commercial_net': commercial_long - commercial_short,
        'noncommercial_net': noncommercial_long - noncommercial_short,
        'commercial_long': commercial_long,
        'commercial_short': commercial_short,
        'noncommercial_long': noncommercial_long,
        'noncommercial_short': noncommercial_short,
        'status': 'success'
    }

def get_historical_cot(year: int = 2025) -> Dict:
    """
    Download historical Commitments of Traders data for a specific year.
    
    Args:
        year: Year to fetch (default: 2025)
        
    Returns:
        Dict with download info and file content preview
        
    Note:
        Historical files are large compressed CSV archives.
        File naming pattern: deacot{year}.zip
        
    Example:
        >>> hist = get_historical_cot(2024)
        >>> print(hist['file_url'])
        >>> print(hist['file_size_mb'])
    """
    try:
        # CFTC historical file naming convention
        filename = f'deacot{year}.zip'
        url = f"{CFTC_URLS['historical_base']}{filename}"
        
        # HEAD request to check file existence and size
        head_response = requests.head(url, timeout=10, allow_redirects=True)
        
        if head_response.status_code == 404:
            return {
                'error': f'Historical data for {year} not found',
                'year': year,
                'file_url': url,
                'status': 'not_found',
                'suggestion': 'Data typically available from 1986 to previous year'
            }
        
        head_response.raise_for_status()
        
        file_size = int(head_response.headers.get('Content-Length', 0))
        
        return {
            'year': year,
            'file_url': url,
            'file_name': filename,
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'status': 'available',
            'note': 'Use requests.get() to download the full ZIP archive',
            'fetched_at': datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to check historical data: {str(e)}',
            'year': year,
            'status': 'failed'
        }

def _extract_report_date(lines: List[str]) -> str:
    """Extract report date from header lines."""
    for line in lines[:10]:  # Check first 10 lines
        # Look for date patterns like "AS OF 03/04/2026" or "MARCH 4, 2026"
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', line)
        if date_match:
            month, day, year = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Alternative format: "MARCH 4, 2026"
        date_match = re.search(r'([A-Z]+)\s+(\d{1,2}),?\s+(\d{4})', line)
        if date_match:
            month_name, day, year = date_match.groups()
            try:
                month_num = datetime.strptime(month_name[:3], '%b').month
                return f"{year}-{str(month_num).zfill(2)}-{day.zfill(2)}"
            except:
                pass
    
    return datetime.utcnow().strftime('%Y-%m-%d')

def _parse_cot_line(line: str, report_type: str) -> Optional[Dict]:
    """
    Parse a single line from COT report.
    
    Note: CFTC reports use fixed-width format with varying column positions.
    This is a best-effort parser that extracts key fields.
    """
    try:
        # Split by multiple spaces (fixed-width separator)
        parts = re.split(r'\s{2,}', line.strip())
        
        if len(parts) < 5:
            return None
        
        # Extract market code (6-digit number)
        market_code_match = re.search(r'(\d{6})', line)
        market_code = market_code_match.group(1) if market_code_match else ''
        
        # Market name is usually the first text field
        market_name = parts[0] if parts else 'UNKNOWN'
        
        # Try to extract numeric fields (positions)
        # Format varies but usually: Market, Open Interest, NonComm Long, NonComm Short, Comm Long, Comm Short
        numbers = [int(re.sub(r'[^\d-]', '', p)) for p in parts if re.search(r'\d+', p)]
        
        result = {
            'market_code': market_code,
            'market_name': market_name,
            'open_interest': numbers[0] if len(numbers) > 0 else 0,
            'noncommercial_long': numbers[1] if len(numbers) > 1 else 0,
            'noncommercial_short': numbers[2] if len(numbers) > 2 else 0,
            'commercial_long': numbers[3] if len(numbers) > 3 else 0,
            'commercial_short': numbers[4] if len(numbers) > 4 else 0,
        }
        
        return result
        
    except Exception as e:
        return None

# ========== CLI Testing ==========

if __name__ == "__main__":
    import json
    
    print("=== CFTC Commitments of Traders API ===\n")
    
    # Test 1: Get current report
    print("1. Fetching current futures report...")
    report = get_current_cot_report('futures_only')
    print(f"Status: {report.get('status')}")
    print(f"Report Date: {report.get('report_date')}")
    print(f"Markets: {report.get('markets_count')}")
    
    if report.get('markets'):
        print(f"\nFirst market: {report['markets'][0].get('market_name')}")
    
    # Test 2: Search for specific market
    print("\n2. Searching for CRUDE OIL...")
    crude_results = search_by_market('CRUDE OIL')
    print(f"Found {len(crude_results)} matches")
    for r in crude_results[:2]:
        print(f"  - {r.get('market_name')}: OI={r.get('open_interest'):,}")
    
    # Test 3: Get net positions
    print("\n3. Getting net positions for CRUDE OIL...")
    positions = get_net_positions('CRUDE OIL')
    if positions.get('status') == 'success':
        print(f"Market: {positions['market_name']}")
        print(f"Commercial net: {positions['commercial_net']:,}")
        print(f"Non-commercial net: {positions['noncommercial_net']:,}")
    else:
        print(f"Error: {positions.get('error')}")
    
    # Test 4: Check historical data availability
    print("\n4. Checking historical data for 2024...")
    hist = get_historical_cot(2024)
    print(f"Status: {hist.get('status')}")
    if hist.get('file_url'):
        print(f"URL: {hist['file_url']}")
        print(f"Size: {hist.get('file_size_mb')} MB")
    
    print("\n=== Module ready ===")
