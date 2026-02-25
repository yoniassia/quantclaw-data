#!/usr/bin/env python3
"""
Corporate Bond Spreads Module — Phase 156

Comprehensive corporate bond spread tracking for Investment Grade (IG) 
and High Yield (HY) bonds using ICE BofA indices from FRED.

Tracks:
- IG/HY option-adjusted spreads (OAS)
- Sector-specific spreads (energy, financials, tech, utilities, etc.)
- Maturity-based spreads (1-3Y, 3-5Y, 5-7Y, 7-10Y, 10-15Y, 15Y+)
- Rating-specific spreads (AAA, AA, A, BBB, BB, B, CCC and below)
- Spread comparisons and trend analysis

Data Source: FRED API (ICE BofA Bond Indices)
Refresh: Daily
Coverage: US Corporate bonds by rating, sector, and maturity

Author: QUANTCLAW DATA Build Agent
Phase: 156
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# ========== ICE BOFA CORPORATE BOND SPREAD SERIES ==========

CORPORATE_BOND_SERIES = {
    # ===== INVESTMENT GRADE (IG) =====
    'IG_OVERALL': {
        'BAMLC0A0CM': 'ICE BofA US Corporate Master - OAS',
        'BAMLC0A0CMEY': 'ICE BofA US Corporate Master - Effective Yield',
        'BAMLC0A1CAAAEY': 'ICE BofA AAA US Corporate - Effective Yield',
        'BAMLC0A2CAAEY': 'ICE BofA AA US Corporate - Effective Yield',
        'BAMLC0A3CAEY': 'ICE BofA A US Corporate - Effective Yield',
        'BAMLC0A4CBBBEY': 'ICE BofA BBB US Corporate - Effective Yield',
    },
    
    'IG_OAS_BY_RATING': {
        'BAMLC0A1CAAAOAS': 'ICE BofA AAA US Corporate - OAS',
        'BAMLC0A2CAAOAS': 'ICE BofA AA US Corporate - OAS',
        'BAMLC0A3CAOAS': 'ICE BofA A US Corporate - OAS',
        'BAMLC0A4CBBBOAS': 'ICE BofA BBB US Corporate - OAS',
    },
    
    'IG_OAS_BY_MATURITY': {
        'BAMLC1A0C13YEY': 'ICE BofA 1-3 Year US Corporate - Effective Yield',
        'BAMLC2A0C35YEY': 'ICE BofA 3-5 Year US Corporate - Effective Yield',
        'BAMLC3A0C57YEY': 'ICE BofA 5-7 Year US Corporate - Effective Yield',
        'BAMLC4A0C710YEY': 'ICE BofA 7-10 Year US Corporate - Effective Yield',
        'BAMLC7A0C1015YEY': 'ICE BofA 10-15 Year US Corporate - Effective Yield',
        'BAMLC8A0C15PYEY': 'ICE BofA 15+ Year US Corporate - Effective Yield',
    },
    
    # ===== HIGH YIELD (HY) =====
    'HY_OVERALL': {
        'BAMLH0A0HYM2': 'ICE BofA US High Yield Master II - OAS',
        'BAMLH0A0HYM2EY': 'ICE BofA US High Yield Master II - Effective Yield',
        'BAMLH0A1HYBB': 'ICE BofA BB US High Yield - OAS',
        'BAMLH0A2HYB': 'ICE BofA B US High Yield - OAS',
        'BAMLH0A3HYC': 'ICE BofA CCC and Below US High Yield - OAS',
    },
    
    'HY_BY_RATING': {
        'BAMLH0A1HYBBEY': 'ICE BofA BB US High Yield - Effective Yield',
        'BAMLH0A2HYBEY': 'ICE BofA B US High Yield - Effective Yield',
        'BAMLH0A3HYCEY': 'ICE BofA CCC and Below US High Yield - Effective Yield',
    },
    
    # ===== SECTOR SPREADS =====
    'SECTORS': {
        'BAMLCC0A0CMTRIV': 'ICE BofA Corporate Master Total Return Index',
        'BAMLC0A1CAAA': 'ICE BofA AAA US Corporate Index',
        'BAMLC0A2CAA': 'ICE BofA AA US Corporate Index',
        'BAMLC0A3CA': 'ICE BofA A US Corporate Index',
        'BAMLC0A4CBBB': 'ICE BofA BBB US Corporate Index',
    },
    
    # ===== SPREAD DIFFERENTIALS =====
    'SPREADS': {
        'BAMLC0A0CM': 'US Corporate OAS (All IG)',
        'BAMLH0A0HYM2': 'US High Yield OAS (All HY)',
        'BAMLC0A4CBBBOAS': 'BBB Corporate OAS',
        'BAMLC0A3CAOAS': 'A Corporate OAS',
        'BAMLC0A2CAAOAS': 'AA Corporate OAS',
        'BAMLC0A1CAAAOAS': 'AAA Corporate OAS',
    },
    
    # ===== TREASURY COMPARISON =====
    'TREASURIES': {
        'DGS2': '2-Year Treasury Constant Maturity Rate',
        'DGS5': '5-Year Treasury Constant Maturity Rate',
        'DGS10': '10-Year Treasury Constant Maturity Rate',
        'DGS30': '30-Year Treasury Constant Maturity Rate',
    },
}

# Sector mapping for common industry classifications
SECTOR_MAPPINGS = {
    'financials': ['BAMLC0A2CAA', 'BAMLC0A3CA'],
    'industrials': ['BAMLC0A0CM'],
    'utilities': ['BAMLC0A4CBBB'],
    'energy': ['BAMLH0A0HYM2'],
    'technology': ['BAMLC0A3CA'],
}


# ========== CORE FUNCTIONS ==========

def fetch_fred_series(
    series_id: str,
    days_back: int = 365,
    api_key: str = FRED_API_KEY
) -> Dict:
    """
    Fetch time series data from FRED API
    
    Args:
        series_id: FRED series identifier
        days_back: Number of days of historical data
        api_key: FRED API key (optional for public access)
        
    Returns:
        Dict with time series data
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build request URL
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
            'file_type': 'json',
            'sort_order': 'desc'
        }
        
        if api_key:
            params['api_key'] = api_key
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = []
        
        for obs in data.get('observations', []):
            if obs.get('value') != '.':
                observations.append({
                    'date': obs['date'],
                    'value': float(obs['value']),
                    'series_id': series_id
                })
        
        return {
            'success': True,
            'series_id': series_id,
            'data': observations,
            'count': len(observations),
            'latest_value': observations[0]['value'] if observations else None,
            'latest_date': observations[0]['date'] if observations else None,
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'FRED API request failed: {str(e)}',
            'series_id': series_id,
            'data': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing FRED data: {str(e)}',
            'series_id': series_id,
            'data': []
        }


def get_ig_spreads(days_back: int = 365) -> Dict:
    """
    Get Investment Grade corporate bond spreads by rating
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with IG spreads by rating class
    """
    try:
        spreads = {}
        
        for series_id, name in CORPORATE_BOND_SERIES['IG_OAS_BY_RATING'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                spreads[series_id] = {
                    'name': name,
                    'current_oas_bps': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:90]  # Last 90 days
                }
        
        return {
            'success': True,
            'category': 'Investment Grade',
            'data': spreads,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_hy_spreads(days_back: int = 365) -> Dict:
    """
    Get High Yield corporate bond spreads by rating
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with HY spreads by rating class
    """
    try:
        spreads = {}
        
        # Get overall HY OAS
        for series_id in ['BAMLH0A0HYM2', 'BAMLH0A1HYBB', 'BAMLH0A2HYB', 'BAMLH0A3HYC']:
            name = CORPORATE_BOND_SERIES['HY_OVERALL'].get(series_id, series_id)
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                spreads[series_id] = {
                    'name': name,
                    'current_oas_bps': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:90]
                }
        
        return {
            'success': True,
            'category': 'High Yield',
            'data': spreads,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_sector_spreads(sector: Optional[str] = None, days_back: int = 365) -> Dict:
    """
    Get sector-specific corporate bond spreads
    
    Args:
        sector: Specific sector (financials, energy, utilities, etc.)
        days_back: Number of days of historical data
        
    Returns:
        Dict with sector spread analysis
    """
    try:
        if sector and sector.lower() in SECTOR_MAPPINGS:
            series_list = SECTOR_MAPPINGS[sector.lower()]
        else:
            # Return all major sector proxies
            series_list = list(CORPORATE_BOND_SERIES['SECTORS'].keys())[:5]
        
        sector_data = {}
        for series_id in series_list:
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                sector_data[series_id] = {
                    'series_id': series_id,
                    'latest_value': result['latest_value'],
                    'latest_date': result['latest_date'],
                    'data': result['data'][:30]
                }
        
        return {
            'success': True,
            'sector': sector or 'All',
            'data': sector_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def compare_ig_vs_hy(days_back: int = 365) -> Dict:
    """
    Compare Investment Grade vs High Yield spreads
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with IG/HY spread comparison
    """
    try:
        # Fetch IG Master OAS
        ig_result = fetch_fred_series('BAMLC0A0CM', days_back)
        
        # Fetch HY Master OAS
        hy_result = fetch_fred_series('BAMLH0A0HYM2', days_back)
        
        if not (ig_result['success'] and hy_result['success']):
            return {
                'success': False,
                'error': 'Failed to fetch IG or HY data',
                'data': {}
            }
        
        # Calculate spread differential
        ig_latest = ig_result['latest_value']
        hy_latest = hy_result['latest_value']
        spread_diff = hy_latest - ig_latest
        
        # Calculate percentiles
        ig_values = [obs['value'] for obs in ig_result['data']]
        hy_values = [obs['value'] for obs in hy_result['data']]
        
        ig_values_sorted = sorted(ig_values)
        hy_values_sorted = sorted(hy_values)
        
        ig_percentile = (ig_values_sorted.index(ig_latest) / len(ig_values_sorted)) * 100 if ig_latest in ig_values_sorted else 50
        hy_percentile = (hy_values_sorted.index(hy_latest) / len(hy_values_sorted)) * 100 if hy_latest in hy_values_sorted else 50
        
        return {
            'success': True,
            'data': {
                'investment_grade': {
                    'current_oas_bps': ig_latest,
                    'date': ig_result['latest_date'],
                    'percentile_rank': round(ig_percentile, 1),
                    'avg_1y': round(sum(ig_values) / len(ig_values), 2),
                    'min_1y': min(ig_values),
                    'max_1y': max(ig_values),
                },
                'high_yield': {
                    'current_oas_bps': hy_latest,
                    'date': hy_result['latest_date'],
                    'percentile_rank': round(hy_percentile, 1),
                    'avg_1y': round(sum(hy_values) / len(hy_values), 2),
                    'min_1y': min(hy_values),
                    'max_1y': max(hy_values),
                },
                'spread_differential': {
                    'hy_minus_ig_bps': round(spread_diff, 2),
                    'hy_ig_ratio': round(hy_latest / ig_latest, 2) if ig_latest > 0 else 0,
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_spreads_by_maturity(days_back: int = 365) -> Dict:
    """
    Get corporate bond spreads segmented by maturity buckets
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with spreads by maturity
    """
    try:
        maturity_spreads = {}
        
        for series_id, name in CORPORATE_BOND_SERIES['IG_OAS_BY_MATURITY'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                maturity_spreads[series_id] = {
                    'name': name,
                    'current_yield_pct': result['latest_value'],
                    'date': result['latest_date'],
                    'historical': result['data'][:60]
                }
        
        return {
            'success': True,
            'data': maturity_spreads,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_credit_risk_dashboard(days_back: int = 365) -> Dict:
    """
    Comprehensive credit risk dashboard combining all spread metrics
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with comprehensive credit dashboard
    """
    try:
        # Fetch all key metrics
        ig_spreads = get_ig_spreads(days_back)
        hy_spreads = get_hy_spreads(days_back)
        ig_hy_comparison = compare_ig_vs_hy(days_back)
        maturity_spreads = get_spreads_by_maturity(days_back)
        
        # Get Treasury yields for context
        treasury_10y = fetch_fred_series('DGS10', 90)
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'treasury_context': {
                '10y_yield': treasury_10y['latest_value'] if treasury_10y['success'] else None,
                'date': treasury_10y['latest_date'] if treasury_10y['success'] else None,
            },
            'investment_grade': ig_spreads.get('data', {}),
            'high_yield': hy_spreads.get('data', {}),
            'ig_vs_hy': ig_hy_comparison.get('data', {}),
            'maturity_buckets': maturity_spreads.get('data', {}),
            'data_sources': [
                'FRED API (Federal Reserve Bank of St. Louis)',
                'ICE BofA Bond Indices'
            ]
        }
        
        return {
            'success': True,
            'data': dashboard
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def analyze_spread_trends(days_back: int = 90) -> Dict:
    """
    Analyze recent spread trends and identify anomalies
    
    Args:
        days_back: Number of days to analyze
        
    Returns:
        Dict with trend analysis
    """
    try:
        # Fetch key spread series
        ig_data = fetch_fred_series('BAMLC0A0CM', days_back)
        hy_data = fetch_fred_series('BAMLH0A0HYM2', days_back)
        
        if not (ig_data['success'] and hy_data['success']):
            return {
                'success': False,
                'error': 'Failed to fetch spread data',
                'data': {}
            }
        
        # Calculate trends
        ig_values = [obs['value'] for obs in ig_data['data'][:30]]
        hy_values = [obs['value'] for obs in hy_data['data'][:30]]
        
        ig_30d_change = ig_values[0] - ig_values[-1] if len(ig_values) >= 30 else 0
        hy_30d_change = hy_values[0] - hy_values[-1] if len(hy_values) >= 30 else 0
        
        ig_trend = 'widening' if ig_30d_change > 5 else 'tightening' if ig_30d_change < -5 else 'stable'
        hy_trend = 'widening' if hy_30d_change > 10 else 'tightening' if hy_30d_change < -10 else 'stable'
        
        return {
            'success': True,
            'data': {
                'investment_grade': {
                    'current_oas': ig_values[0],
                    '30d_change_bps': round(ig_30d_change, 2),
                    'trend': ig_trend,
                },
                'high_yield': {
                    'current_oas': hy_values[0],
                    '30d_change_bps': round(hy_30d_change, 2),
                    'trend': hy_trend,
                },
                'market_signal': {
                    'credit_conditions': 'tightening' if (ig_trend == 'tightening' and hy_trend == 'tightening') else 'widening' if (ig_trend == 'widening' and hy_trend == 'widening') else 'mixed',
                    'risk_appetite': 'increasing' if hy_30d_change < -10 else 'decreasing' if hy_30d_change > 10 else 'neutral'
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


# ========== CLI INTERFACE ==========

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python corporate_bond_spreads.py <command> [options]")
        print("\nCommands:")
        print("  ig-spreads [days]                - Investment Grade spreads by rating")
        print("  hy-spreads [days]                - High Yield spreads by rating")
        print("  sector-spreads [sector] [days]   - Sector-specific spreads")
        print("  ig-vs-hy [days]                  - Compare IG vs HY spreads")
        print("  spreads-by-maturity [days]       - Spreads by maturity bucket")
        print("  credit-dashboard [days]          - Comprehensive credit risk dashboard")
        print("  spread-trends [days]             - Analyze recent spread trends")
        print("\nExamples:")
        print("  python corporate_bond_spreads.py ig-spreads 365")
        print("  python corporate_bond_spreads.py hy-spreads 180")
        print("  python corporate_bond_spreads.py ig-vs-hy 730")
        print("  python corporate_bond_spreads.py credit-dashboard")
        return
    
    command = sys.argv[1]
    
    if command == 'ig-spreads':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_ig_spreads(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'hy-spreads':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_hy_spreads(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'sector-spreads':
        sector = sys.argv[2] if len(sys.argv) > 2 else None
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        result = get_sector_spreads(sector=sector, days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'ig-vs-hy':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = compare_ig_vs_hy(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'spreads-by-maturity':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_spreads_by_maturity(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'credit-dashboard':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_credit_risk_dashboard(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'spread-trends':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        result = analyze_spread_trends(days_back=days)
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == '__main__':
    main()
