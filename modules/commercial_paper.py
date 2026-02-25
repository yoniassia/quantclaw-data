#!/usr/bin/env python3
"""
Commercial Paper Rates Module — Phase 162

AA-rated commercial paper rates for both financial and nonfinancial companies
Daily monitoring of short-term corporate borrowing costs

Data Sources:
- FRED API: Commercial paper rates for various maturities
  - AA Financial Commercial Paper (DCPF1M, DCPF3M)
  - AA Nonfinancial Commercial Paper (DCPN1M, DCPN3M, DCPN2M)
  
Refresh: Daily
Coverage: US commercial paper market

Author: QUANTCLAW DATA Build Agent
Phase: 162
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# ========== FRED API CONFIGURATION ==========

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Load FRED API key
def load_fred_api_key() -> Optional[str]:
    """Load FRED API key from credentials file"""
    try:
        creds_path = Path.home() / ".openclaw" / "workspace" / ".credentials" / "fred-api.json"
        if creds_path.exists():
            with open(creds_path) as f:
                data = json.load(f)
                return data.get("fredApiKey")
    except Exception:
        pass
    return None

FRED_API_KEY = load_fred_api_key()

# FRED Series IDs for Commercial Paper Rates
CP_SERIES = {
    # Financial Commercial Paper (AA-rated)
    "AA_FIN_1M": {
        "series_id": "DCPF1M",
        "name": "AA Financial Commercial Paper 1-Month",
        "category": "Financial",
        "maturity": "1-Month"
    },
    "AA_FIN_3M": {
        "series_id": "DCPF3M",
        "name": "AA Financial Commercial Paper 3-Month",
        "category": "Financial",
        "maturity": "3-Month"
    },
    
    # Nonfinancial Commercial Paper (AA-rated)
    "AA_NONFIN_1M": {
        "series_id": "DCPN1M",
        "name": "AA Nonfinancial Commercial Paper 1-Month",
        "category": "Nonfinancial",
        "maturity": "1-Month"
    },
    "AA_NONFIN_2M": {
        "series_id": "DCPN2M",
        "name": "AA Nonfinancial Commercial Paper 2-Month",
        "category": "Nonfinancial",
        "maturity": "2-Month"
    },
    "AA_NONFIN_3M": {
        "series_id": "DCPN3M",
        "name": "AA Nonfinancial Commercial Paper 3-Month",
        "category": "Nonfinancial",
        "maturity": "3-Month"
    }
}


# ========== CORE FUNCTIONS ==========

def get_fred_series(series_id: str, lookback_days: int = 365) -> Dict:
    """
    Fetch FRED time series data
    
    Args:
        series_id: FRED series identifier
        lookback_days: Number of days of historical data
    
    Returns:
        Dictionary with series data
    """
    try:
        if not FRED_API_KEY:
            return {
                'success': False,
                'error': 'FRED API key not found',
                'data': []
            }
        
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'observation_start': start_date,
            'sort_order': 'desc',
            'limit': 1000
        }
        
        response = requests.get(FRED_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        observations = data.get('observations', [])
        
        if not observations:
            return {
                'success': False,
                'error': 'No data available',
                'data': []
            }
        
        # Parse observations
        parsed_obs = []
        for obs in observations:
            if obs.get('value') != '.':
                try:
                    parsed_obs.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
                except (ValueError, KeyError):
                    continue
        
        return {
            'success': True,
            'series_id': series_id,
            'data': parsed_obs
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}',
            'data': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching data: {str(e)}',
            'data': []
        }


def get_current_rates() -> Dict:
    """
    Get current commercial paper rates for all maturities
    
    Returns:
        Dict with latest rates for financial and nonfinancial CP
    """
    try:
        results = {
            'timestamp': datetime.now().isoformat(),
            'financial': {},
            'nonfinancial': {},
            'spread': {}
        }
        
        # Fetch all series
        for key, info in CP_SERIES.items():
            data = get_fred_series(info['series_id'], lookback_days=30)
            
            if data['success'] and data['data']:
                latest = data['data'][0]
                rate_info = {
                    'rate': latest['value'],
                    'date': latest['date'],
                    'maturity': info['maturity']
                }
                
                if info['category'] == 'Financial':
                    results['financial'][info['maturity']] = rate_info
                else:
                    results['nonfinancial'][info['maturity']] = rate_info
        
        # Calculate spreads (Nonfinancial - Financial)
        for maturity in ['1-Month', '3-Month']:
            if (maturity in results['financial'] and 
                maturity in results['nonfinancial']):
                fin_rate = results['financial'][maturity]['rate']
                nonfin_rate = results['nonfinancial'][maturity]['rate']
                results['spread'][maturity] = round(nonfin_rate - fin_rate, 2)
        
        return {
            'success': True,
            'data': results
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_rate_history(days: int = 90, category: Optional[str] = None) -> Dict:
    """
    Get historical commercial paper rates
    
    Args:
        days: Number of days of history
        category: Filter by 'Financial' or 'Nonfinancial'
    
    Returns:
        Dict with historical rate data
    """
    try:
        results = {}
        
        for key, info in CP_SERIES.items():
            # Apply category filter
            if category and info['category'] != category:
                continue
            
            data = get_fred_series(info['series_id'], lookback_days=days)
            
            if data['success']:
                results[key] = {
                    'name': info['name'],
                    'category': info['category'],
                    'maturity': info['maturity'],
                    'data': data['data']
                }
        
        return {
            'success': True,
            'data': results,
            'period_days': days
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def analyze_spreads(days: int = 90) -> Dict:
    """
    Analyze spreads between financial and nonfinancial commercial paper
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Dict with spread analysis
    """
    try:
        # Fetch data for both categories
        fin_1m = get_fred_series('DCPF1M', lookback_days=days)
        nonfin_1m = get_fred_series('DCPN1M', lookback_days=days)
        fin_3m = get_fred_series('DCPF3M', lookback_days=days)
        nonfin_3m = get_fred_series('DCPN3M', lookback_days=days)
        
        results = {
            '1-Month': _calculate_spread_stats(fin_1m, nonfin_1m),
            '3-Month': _calculate_spread_stats(fin_3m, nonfin_3m)
        }
        
        return {
            'success': True,
            'data': results,
            'period_days': days,
            'note': 'Spread = Nonfinancial rate - Financial rate. Positive spread indicates higher credit risk premium for nonfinancial issuers.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def _calculate_spread_stats(fin_data: Dict, nonfin_data: Dict) -> Dict:
    """Calculate spread statistics between two series"""
    try:
        if not (fin_data['success'] and nonfin_data['success']):
            return {'error': 'Data unavailable'}
        
        # Create date-aligned spreads
        fin_dict = {d['date']: d['value'] for d in fin_data['data']}
        nonfin_dict = {d['date']: d['value'] for d in nonfin_data['data']}
        
        spreads = []
        for date in fin_dict:
            if date in nonfin_dict:
                spread = nonfin_dict[date] - fin_dict[date]
                spreads.append({
                    'date': date,
                    'spread': round(spread, 2),
                    'financial_rate': fin_dict[date],
                    'nonfinancial_rate': nonfin_dict[date]
                })
        
        if not spreads:
            return {'error': 'No overlapping data'}
        
        spread_values = [s['spread'] for s in spreads]
        
        return {
            'current_spread': spreads[0]['spread'] if spreads else None,
            'avg_spread': round(sum(spread_values) / len(spread_values), 2),
            'min_spread': round(min(spread_values), 2),
            'max_spread': round(max(spread_values), 2),
            'latest_financial_rate': spreads[0]['financial_rate'] if spreads else None,
            'latest_nonfinancial_rate': spreads[0]['nonfinancial_rate'] if spreads else None,
            'observations': len(spreads),
            'history': spreads[:10]  # Last 10 observations
        }
        
    except Exception as e:
        return {'error': str(e)}


def get_rate_comparison() -> Dict:
    """
    Compare financial vs nonfinancial CP rates across all maturities
    
    Returns:
        Dict with side-by-side comparison
    """
    try:
        current = get_current_rates()
        
        if not current['success']:
            return current
        
        data = current['data']
        
        comparison = []
        for maturity in ['1-Month', '2-Month', '3-Month']:
            row = {
                'maturity': maturity,
                'financial_rate': data['financial'].get(maturity, {}).get('rate'),
                'nonfinancial_rate': data['nonfinancial'].get(maturity, {}).get('rate'),
                'spread': data['spread'].get(maturity),
                'date': data['financial'].get(maturity, {}).get('date')
            }
            comparison.append(row)
        
        return {
            'success': True,
            'data': comparison,
            'timestamp': data['timestamp']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


def get_cp_dashboard() -> Dict:
    """
    Get comprehensive commercial paper dashboard
    
    Returns:
        Dict with dashboard data
    """
    try:
        current = get_current_rates()
        spreads = analyze_spreads(days=90)
        comparison = get_rate_comparison()
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'current_rates': current.get('data', {}),
            'spread_analysis': spreads.get('data', {}),
            'rate_comparison': comparison.get('data', []),
            'sources': ['FRED - Federal Reserve Economic Data'],
            'series_tracked': list(CP_SERIES.keys())
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


# ========== CLI INTERFACE ==========

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python commercial_paper.py <command> [options]")
        print("\nCommands:")
        print("  cp-current                    - Current CP rates (all maturities)")
        print("  cp-history [days] [category]  - Historical rates (default: 90 days)")
        print("  cp-spreads [days]             - Spread analysis (default: 90 days)")
        print("  cp-compare                    - Side-by-side rate comparison")
        print("  cp-dashboard                  - Comprehensive dashboard")
        print("\nCategory options: Financial, Nonfinancial")
        print("\nExamples:")
        print("  python commercial_paper.py cp-current")
        print("  python commercial_paper.py cp-history 180 Financial")
        print("  python commercial_paper.py cp-spreads 365")
        print("  python commercial_paper.py cp-compare")
        return
    
    command = sys.argv[1]
    
    if command == 'cp-current':
        result = get_current_rates()
        print(json.dumps(result, indent=2))
        
    elif command == 'cp-history':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        category = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_rate_history(days=days, category=category)
        print(json.dumps(result, indent=2))
        
    elif command == 'cp-spreads':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        result = analyze_spreads(days=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'cp-compare':
        result = get_rate_comparison()
        print(json.dumps(result, indent=2))
        
    elif command == 'cp-dashboard':
        result = get_cp_dashboard()
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == '__main__':
    main()
