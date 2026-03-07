#!/usr/bin/env python3
"""
CFTC Commitments of Traders (COT) Data Module

Provides weekly futures positioning data by trader type from the CFTC.
Shows commercial hedgers, non-commercial speculators, and reportable positions
across commodity, financial, and index futures markets.

Data Sources:
- CFTC Legacy Reports: https://www.cftc.gov/dea/newcot/deacom.txt
- CFTC Socrata API: https://publicreporting.cftc.gov/resource/jun7-fc8e.json

Update: Weekly (Tuesday after market close, published Friday 3:30 PM ET)
Free: Yes (no API key required)
Coverage: 1986-present for legacy reports

Author: QUANTCLAW DATA NightBuilder
Generated: 2026-03-07
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import io

# Cache directory
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/cftc")
os.makedirs(CACHE_DIR, exist_ok=True)

# CFTC Data Endpoints
CFTC_LEGACY_URL = "https://www.cftc.gov/dea/newcot/deacom.txt"
CFTC_SOCRATA_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"

# Common commodity name mappings
COMMODITY_MAPPINGS = {
    'GOLD': ['GOLD'],
    'SILVER': ['SILVER'],
    'CRUDE OIL': ['CRUDE OIL'],
    'NATURAL GAS': ['NATURAL GAS'],
    'CORN': ['CORN'],
    'SOYBEANS': ['SOYBEANS', 'SOYBEAN'],
    'WHEAT': ['WHEAT'],
    'COPPER': ['COPPER'],
    'COTTON': ['COTTON'],
    'COFFEE': ['COFFEE'],
    'SUGAR': ['SUGAR'],
    'COCOA': ['COCOA'],
    'EURO': ['EURO'],
    'YEN': ['YEN', 'JAPANESE YEN'],
    'SP500': ['S&P 500', 'S&P500'],
    'NASDAQ': ['NASDAQ'],
    'BITCOIN': ['BITCOIN'],
}


def fetch_cot_legacy() -> pd.DataFrame:
    """
    Fetch latest COT data from CFTC legacy format (deacom.txt).
    Returns pandas DataFrame with parsed COT positions.
    
    Note: CFTC legacy format has NO header row, market name in first column.
    """
    cache_file = os.path.join(CACHE_DIR, "cot_legacy.csv")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            return pd.read_csv(cache_file)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (QuantClaw Data Module)'
        }
        response = requests.get(CFTC_LEGACY_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse CSV - NO header row, just data
        df = pd.read_csv(io.StringIO(response.text), header=None, low_memory=False)
        
        # Assign column names based on CFTC legacy format
        # Column indices from CFTC documentation
        column_names = ['market_name', 'cftc_contract_code', 'report_date', 'cftc_market_code', 
                       'exchange', 'future_only_flag', 'cftc_commodity_code', 'open_interest']
        
        # Add more columns (positions start at col 8)
        column_names += ['noncommercial_long', 'noncommercial_short']  # cols 8,9
        column_names += [f'col_{i}' for i in range(10, 20)]  # intermediate cols
        column_names += ['commercial_long', 'commercial_short']  # cols ~15-16 area
        
        # Fill remaining columns generically
        while len(column_names) < len(df.columns):
            column_names.append(f'col_{len(column_names)}')
        
        df.columns = column_names[:len(df.columns)]
        
        # Cache result
        df.to_csv(cache_file, index=False)
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching CFTC legacy data: {e}")
        # Return cached data if available
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file)
        return pd.DataFrame()


def fetch_cot_socrata(limit: int = 1000, offset: int = 0) -> List[Dict]:
    """
    Fetch COT data from CFTC Socrata API (JSON format).
    Returns list of records.
    """
    cache_file = os.path.join(CACHE_DIR, f"cot_socrata_{limit}_{offset}.json")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            '$limit': limit,
            '$offset': offset,
            '$order': 'report_date_as_yyyy_mm_dd DESC'
        }
        
        response = requests.get(CFTC_SOCRATA_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
        
    except Exception as e:
        print(f"⚠️  CFTC Socrata API error: {e}")
        # Return cached data if available
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                return json.load(f)
        return []


def get_cot_report(market: str = 'all', report_type: str = 'legacy') -> Dict:
    """
    Get latest COT report data.
    
    Args:
        market: 'all', 'commodity', 'financial', or 'index' (default: 'all')
        report_type: 'legacy' or 'disaggregated' (default: 'legacy')
    
    Returns:
        Dict with latest COT positioning data
    """
    df = fetch_cot_legacy()
    
    if df.empty:
        return {
            'error': 'Failed to fetch COT data',
            'market': market,
            'report_type': report_type
        }
    
    # Get latest report date
    latest_date = df['report_date'].iloc[0] if 'report_date' in df.columns else None
    
    result = {
        'report_type': report_type,
        'market': market,
        'report_date': latest_date,
        'total_contracts': len(df),
        'data': []
    }
    
    # Filter by market type if specified
    if market != 'all' and 'market_name' in df.columns:
        market_filter = {
            'commodity': ['GOLD', 'SILVER', 'COPPER', 'CRUDE', 'NATURAL GAS', 'CORN', 'WHEAT', 'SOYBEANS', 'COTTON', 'COFFEE', 'SUGAR', 'COCOA'],
            'financial': ['EURO', 'YEN', 'POUND', 'TREASURY', 'EURODOLLAR'],
            'index': ['S&P', 'NASDAQ', 'DOW', 'RUSSELL']
        }
        if market in market_filter:
            mask = df['market_name'].str.contains('|'.join(market_filter[market]), case=False, na=False)
            df = df[mask]
    
    # Convert to dict records (limit to top 50 by open interest)
    if 'open_interest' in df.columns:
        df['open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
        df_sorted = df.sort_values('open_interest', ascending=False).head(50)
    else:
        df_sorted = df.head(50)
    
    result['data'] = df_sorted.to_dict('records')
    result['count'] = len(result['data'])
    
    return result


def get_cot_by_commodity(commodity_name: str) -> Dict:
    """
    Get COT data for a specific commodity.
    
    Args:
        commodity_name: Commodity name (e.g., 'GOLD', 'CRUDE OIL', 'CORN')
    
    Returns:
        Dict with COT positioning for the specified commodity
    """
    commodity_name = commodity_name.upper()
    
    df = fetch_cot_legacy()
    
    if df.empty:
        return {
            'error': 'Failed to fetch COT data',
            'commodity': commodity_name
        }
    
    # Find matching commodity using mappings
    search_terms = COMMODITY_MAPPINGS.get(commodity_name, [commodity_name])
    
    mask = pd.Series([False] * len(df))
    if 'market_name' in df.columns:
        for term in search_terms:
            mask |= df['market_name'].str.contains(term, case=False, na=False)
    
    commodity_df = df[mask]
    
    if commodity_df.empty:
        return {
            'error': f'Commodity not found: {commodity_name}',
            'commodity': commodity_name,
            'available_commodities': list(COMMODITY_MAPPINGS.keys()),
            'sample_markets': df['market_name'].head(20).tolist() if 'market_name' in df.columns else []
        }
    
    # Get latest record
    latest = commodity_df.iloc[0].to_dict()
    
    # Convert numeric strings to numbers
    try:
        result = {
            'commodity': commodity_name,
            'report_date': latest.get('report_date'),
            'market_name': latest.get('market_name'),
            'exchange': latest.get('exchange'),
            'open_interest': int(pd.to_numeric(latest.get('open_interest', 0), errors='coerce') or 0),
            'positions': {
                'commercial_long': int(pd.to_numeric(latest.get('commercial_long', 0), errors='coerce') or 0),
                'commercial_short': int(pd.to_numeric(latest.get('commercial_short', 0), errors='coerce') or 0),
                'noncommercial_long': int(pd.to_numeric(latest.get('noncommercial_long', 0), errors='coerce') or 0),
                'noncommercial_short': int(pd.to_numeric(latest.get('noncommercial_short', 0), errors='coerce') or 0),
            },
            'total_records': len(commodity_df)
        }
    except (ValueError, TypeError) as e:
        result = {
            'commodity': commodity_name,
            'report_date': latest.get('report_date'),
            'market_name': latest.get('market_name'),
            'raw_data': latest,
            'parse_error': str(e)
        }
    
    return result


def get_historical_cot(commodity_name: str, weeks: int = 52) -> Dict:
    """
    Get historical COT data for a specific commodity.
    
    Args:
        commodity_name: Commodity name (e.g., 'GOLD', 'CRUDE OIL')
        weeks: Number of weeks of history (default: 52 = 1 year)
    
    Returns:
        Dict with historical COT positioning
    """
    commodity_name = commodity_name.upper()
    
    # Try Socrata API for historical data
    records = fetch_cot_socrata(limit=weeks * 2)  # Fetch more to filter
    
    if not records:
        return {
            'error': 'Failed to fetch historical COT data (Socrata API unavailable)',
            'commodity': commodity_name,
            'weeks': weeks,
            'note': 'Try using get_cot_by_commodity() for current week snapshot'
        }
    
    # Filter for specific commodity
    search_terms = COMMODITY_MAPPINGS.get(commodity_name, [commodity_name])
    
    commodity_records = []
    for record in records:
        market_name = record.get('market_and_exchange_names', '').upper()
        if any(term.upper() in market_name for term in search_terms):
            commodity_records.append(record)
    
    # Limit to requested weeks
    commodity_records = commodity_records[:weeks]
    
    if not commodity_records:
        return {
            'error': f'No historical data found for: {commodity_name}',
            'commodity': commodity_name,
            'available_commodities': list(COMMODITY_MAPPINGS.keys())
        }
    
    result = {
        'commodity': commodity_name,
        'weeks': len(commodity_records),
        'date_range': {
            'start': commodity_records[-1].get('report_date_as_yyyy_mm_dd'),
            'end': commodity_records[0].get('report_date_as_yyyy_mm_dd')
        },
        'data': commodity_records
    }
    
    return result


def get_net_positions(commodity_name: str) -> Dict:
    """
    Get net long/short positions by trader type.
    
    Args:
        commodity_name: Commodity name (e.g., 'GOLD', 'CRUDE OIL')
    
    Returns:
        Dict with net positions (long - short) for each trader category
    """
    cot_data = get_cot_by_commodity(commodity_name)
    
    if 'error' in cot_data:
        return cot_data
    
    positions = cot_data.get('positions', {})
    
    # Calculate net positions
    try:
        commercial_net = (
            int(positions.get('commercial_long', 0)) - 
            int(positions.get('commercial_short', 0))
        )
        
        noncommercial_net = (
            int(positions.get('noncommercial_long', 0)) - 
            int(positions.get('noncommercial_short', 0))
        )
        
        result = {
            'commodity': commodity_name,
            'report_date': cot_data.get('report_date'),
            'net_positions': {
                'commercial': {
                    'net': commercial_net,
                    'direction': 'LONG' if commercial_net > 0 else 'SHORT',
                    'magnitude': abs(commercial_net)
                },
                'noncommercial': {
                    'net': noncommercial_net,
                    'direction': 'LONG' if noncommercial_net > 0 else 'SHORT',
                    'magnitude': abs(noncommercial_net)
                }
            },
            'interpretation': {
                'commercial_hedgers': 'Typically contrarian - hedge production/consumption',
                'noncommercial_speculators': 'Large speculators - momentum traders',
                'signal': 'BULLISH' if noncommercial_net > 0 else 'BEARISH'
            }
        }
        
        return result
        
    except (ValueError, TypeError) as e:
        return {
            'error': f'Failed to calculate net positions: {e}',
            'commodity': commodity_name
        }


def get_extreme_positions(threshold: float = 2.0) -> Dict:
    """
    Find commodities at extreme positioning levels (z-score).
    
    Args:
        threshold: Z-score threshold for extreme (default: 2.0 = 2 std devs)
    
    Returns:
        Dict with commodities at extreme long/short positioning
    """
    df = fetch_cot_legacy()
    
    if df.empty:
        return {
            'error': 'Failed to fetch COT data',
            'threshold': threshold
        }
    
    extremes = {
        'threshold': threshold,
        'report_date': df['report_date'].iloc[0] if 'report_date' in df.columns else None,
        'extreme_long': [],
        'extreme_short': []
    }
    
    # Calculate net noncommercial positions and z-scores
    if all(col in df.columns for col in ['noncommercial_long', 'noncommercial_short', 'market_name']):
        df['noncommercial_long'] = pd.to_numeric(df['noncommercial_long'], errors='coerce')
        df['noncommercial_short'] = pd.to_numeric(df['noncommercial_short'], errors='coerce')
        
        df['noncommercial_net'] = df['noncommercial_long'] - df['noncommercial_short']
        
        # Calculate z-scores
        mean = df['noncommercial_net'].mean()
        std = df['noncommercial_net'].std()
        
        if std > 0:
            df['z_score'] = (df['noncommercial_net'] - mean) / std
            
            # Find extremes
            extreme_long_df = df[df['z_score'] > threshold].nlargest(10, 'z_score')
            extreme_short_df = df[df['z_score'] < -threshold].nsmallest(10, 'z_score')
            
            for _, row in extreme_long_df.iterrows():
                extremes['extreme_long'].append({
                    'commodity': row['market_name'],
                    'z_score': round(float(row['z_score']), 2),
                    'net_position': int(row['noncommercial_net']),
                    'signal': 'OVERBOUGHT'
                })
            
            for _, row in extreme_short_df.iterrows():
                extremes['extreme_short'].append({
                    'commodity': row['market_name'],
                    'z_score': round(float(row['z_score']), 2),
                    'net_position': int(row['noncommercial_net']),
                    'signal': 'OVERSOLD'
                })
    
    extremes['count_long'] = len(extremes['extreme_long'])
    extremes['count_short'] = len(extremes['extreme_short'])
    
    return extremes


# === CLI Commands ===

def cli_report(args):
    """CLI: Get COT report"""
    market = args[0] if args else 'all'
    data = get_cot_report(market=market)
    print(json.dumps(data, indent=2))


def cli_commodity(args):
    """CLI: Get COT for specific commodity"""
    if not args:
        print("Usage: cftc_commitments_of_traders_data.py commodity <COMMODITY_NAME>")
        print(f"Available: {', '.join(COMMODITY_MAPPINGS.keys())}")
        return
    
    commodity = ' '.join(args)
    data = get_cot_by_commodity(commodity)
    print(json.dumps(data, indent=2))


def cli_historical(args):
    """CLI: Get historical COT"""
    if not args:
        print("Usage: cftc_commitments_of_traders_data.py historical <COMMODITY_NAME> [weeks]")
        return
    
    commodity = args[0]
    weeks = int(args[1]) if len(args) > 1 else 52
    data = get_historical_cot(commodity, weeks)
    print(json.dumps(data, indent=2))


def cli_net_positions(args):
    """CLI: Get net positions"""
    if not args:
        print("Usage: cftc_commitments_of_traders_data.py net <COMMODITY_NAME>")
        return
    
    commodity = ' '.join(args)
    data = get_net_positions(commodity)
    print(json.dumps(data, indent=2))


def cli_extremes(args):
    """CLI: Get extreme positions"""
    threshold = float(args[0]) if args else 2.0
    data = get_extreme_positions(threshold)
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("CFTC Commitments of Traders Data Module")
        print("Usage: cftc_commitments_of_traders_data.py <command> [args]")
        print("\nCommands:")
        print("  report [market]          - Get latest COT report (market: all/commodity/financial/index)")
        print("  commodity <name>         - Get COT for specific commodity")
        print("  historical <name> [weeks]- Get historical COT data")
        print("  net <name>               - Get net positions by trader type")
        print("  extremes [threshold]     - Find commodities at extreme positioning")
        print(f"\nAvailable commodities: {', '.join(list(COMMODITY_MAPPINGS.keys())[:10])}...")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        'report': cli_report,
        'commodity': cli_commodity,
        'historical': cli_historical,
        'net': cli_net_positions,
        'extremes': cli_extremes
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
