#!/usr/bin/env python3
"""
Treasury Yield Curve (Full) Module — Phase 154

Daily US Treasury yield curve from 1 Month to 30 Years
Real-time data from treasury.gov with historical analysis

Data Sources:
- Treasury.gov Daily Treasury Yield Curve Rates API
- Federal Reserve FRED API (backup/validation)

Maturities Covered:
- Short-term: 1M, 2M, 3M, 4M, 6M
- Bills: 1Y
- Notes: 2Y, 3Y, 5Y, 7Y, 10Y
- Bonds: 20Y, 30Y

Refresh: Daily (updated around 6pm ET)
Coverage: Current curve + historical analysis

Author: QUANTCLAW DATA Build Agent
Phase: 154
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from xml.etree import ElementTree as ET

# Treasury.gov API Configuration
TREASURY_CURVE_API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TREASURY_CURVE_ENDPOINT = f"{TREASURY_CURVE_API}/v2/accounting/od/avg_interest_rates"

# FRED API Configuration (primary source)
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Load FRED API key from credentials
FRED_API_KEY = ""
try:
    import os
    creds_path = os.path.expanduser('~/.openclaw/workspace/.credentials/fred-api.json')
    if os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            FRED_API_KEY = creds.get('fredApiKey', '')
except:
    pass

# Maturity mappings
MATURITIES = {
    '1_MONTH': {'label': '1M', 'days': 30, 'fred': 'DGS1MO'},
    '2_MONTH': {'label': '2M', 'days': 60, 'fred': 'DGS2MO'},
    '3_MONTH': {'label': '3M', 'days': 90, 'fred': 'DGS3MO'},
    '4_MONTH': {'label': '4M', 'days': 120, 'fred': None},
    '6_MONTH': {'label': '6M', 'days': 180, 'fred': 'DGS6MO'},
    '1_YEAR': {'label': '1Y', 'days': 365, 'fred': 'DGS1'},
    '2_YEAR': {'label': '2Y', 'days': 730, 'fred': 'DGS2'},
    '3_YEAR': {'label': '3Y', 'days': 1095, 'fred': 'DGS3'},
    '5_YEAR': {'label': '5Y', 'days': 1825, 'fred': 'DGS5'},
    '7_YEAR': {'label': '7Y', 'days': 2555, 'fred': 'DGS7'},
    '10_YEAR': {'label': '10Y', 'days': 3650, 'fred': 'DGS10'},
    '20_YEAR': {'label': '20Y', 'days': 7300, 'fred': 'DGS20'},
    '30_YEAR': {'label': '30Y', 'days': 10950, 'fred': 'DGS30'},
}

# Security types in Treasury API
SECURITY_TYPES = {
    'Treasury Bills': ['1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo', '1 Yr'],
    'Treasury Notes': ['2 Yr', '3 Yr', '5 Yr', '7 Yr', '10 Yr'],
    'Treasury Bonds': ['20 Yr', '30 Yr']
}


def get_current_curve(format_table: bool = False) -> Dict:
    """
    Get current Treasury yield curve (all maturities)
    Uses FRED API as primary source for reliability
    
    Args:
        format_table: If True, return ASCII table format
        
    Returns:
        Dict with current yield curve data
    """
    try:
        # Use FRED API directly (more reliable than Treasury.gov API)
        curve_data = {}
        latest_date = None
        
        for key, info in MATURITIES.items():
            fred_series = info.get('fred')
            if not fred_series:
                continue
            
            url = f"{FRED_BASE_URL}/series/observations"
            params = {
                'series_id': fred_series,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            
            if FRED_API_KEY:
                params['api_key'] = FRED_API_KEY
            
            try:
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations'):
                        obs = data['observations'][0]
                        if obs['value'] != '.':
                            curve_data[key] = {
                                'maturity': info['label'],
                                'days': info['days'],
                                'yield': float(obs['value']),
                                'date': obs['date']
                            }
                            if latest_date is None or obs['date'] > latest_date:
                                latest_date = obs['date']
            except:
                continue
        
        if not curve_data:
            return {'success': False, 'error': 'No data available from FRED'}
        
        # Sort by maturity
        sorted_curve = dict(sorted(
            curve_data.items(), 
            key=lambda x: MATURITIES[x[0]]['days']
        ))
        
        # Calculate curve metrics
        metrics = _calculate_curve_metrics(sorted_curve)
        
        result = {
            'success': True,
            'date': latest_date,
            'source': 'FRED',
            'curve': sorted_curve,
            'metrics': metrics,
            'count': len(sorted_curve)
        }
        
        if format_table:
            result['table'] = _format_curve_table(sorted_curve, metrics)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching yield curve: {str(e)}'
        }


def get_historical_curve(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days_back: int = 90
) -> Dict:
    """
    Get historical yield curve data
    Uses FRED API for historical time series
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        days_back: If dates not provided, days to look back
        
    Returns:
        Dict with historical curve data by date
    """
    try:
        # Set date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start = datetime.now() - timedelta(days=days_back)
            start_date = start.strftime('%Y-%m-%d')
        
        # Fetch data for each maturity from FRED
        all_series_data = {}
        
        for key, info in MATURITIES.items():
            fred_series = info.get('fred')
            if not fred_series:
                continue
            
            url = f"{FRED_BASE_URL}/series/observations"
            params = {
                'series_id': fred_series,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date
            }
            
            if FRED_API_KEY:
                params['api_key'] = FRED_API_KEY
            
            try:
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations'):
                        all_series_data[key] = {
                            obs['date']: float(obs['value']) 
                            for obs in data['observations'] 
                            if obs['value'] != '.'
                        }
            except:
                continue
        
        # Reorganize by date
        curves_by_date = {}
        all_dates = set()
        
        for key, date_values in all_series_data.items():
            all_dates.update(date_values.keys())
        
        for date in all_dates:
            curves_by_date[date] = {}
            for key, date_values in all_series_data.items():
                if date in date_values:
                    curves_by_date[date][key] = {
                        'maturity': MATURITIES[key]['label'],
                        'yield': date_values[date]
                    }
        
        # Sort dates
        sorted_dates = sorted(curves_by_date.keys(), reverse=True)
        
        return {
            'success': True,
            'source': 'FRED',
            'start_date': start_date,
            'end_date': end_date,
            'curves': curves_by_date,
            'dates': sorted_dates,
            'count': len(sorted_dates)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching historical data: {str(e)}'
        }


def analyze_curve_shape(curve_data: Optional[Dict] = None) -> Dict:
    """
    Analyze yield curve shape and slope
    Detect inversions, steepening, flattening
    
    Args:
        curve_data: Optional pre-fetched curve data
        
    Returns:
        Dict with shape analysis
    """
    try:
        if not curve_data:
            result = get_current_curve()
            if not result.get('success'):
                return result
            curve_data = result['curve']
        
        # Extract key yields
        yields_map = {k: v['yield'] for k, v in curve_data.items()}
        
        # Calculate key spreads
        spreads = {}
        
        # 10Y-2Y (classic recession indicator)
        if '10_YEAR' in yields_map and '2_YEAR' in yields_map:
            spreads['10y_2y'] = round(yields_map['10_YEAR'] - yields_map['2_YEAR'], 2)
        
        # 10Y-3M (another recession indicator)
        if '10_YEAR' in yields_map and '3_MONTH' in yields_map:
            spreads['10y_3m'] = round(yields_map['10_YEAR'] - yields_map['3_MONTH'], 2)
        
        # 30Y-5Y (long-term slope)
        if '30_YEAR' in yields_map and '5_YEAR' in yields_map:
            spreads['30y_5y'] = round(yields_map['30_YEAR'] - yields_map['5_YEAR'], 2)
        
        # 2Y-3M (front-end slope)
        if '2_YEAR' in yields_map and '3_MONTH' in yields_map:
            spreads['2y_3m'] = round(yields_map['2_YEAR'] - yields_map['3_MONTH'], 2)
        
        # Determine shape
        shape_analysis = {
            'shape': 'unknown',
            'inversions': [],
            'signals': []
        }
        
        # Check for inversions
        if spreads.get('10y_2y', 0) < 0:
            shape_analysis['inversions'].append('10Y-2Y inverted')
            shape_analysis['signals'].append('🚨 RECESSION SIGNAL: 10Y-2Y inversion')
        
        if spreads.get('10y_3m', 0) < 0:
            shape_analysis['inversions'].append('10Y-3M inverted')
            shape_analysis['signals'].append('🚨 RECESSION SIGNAL: 10Y-3M inversion')
        
        # Determine overall shape
        if len(shape_analysis['inversions']) > 0:
            shape_analysis['shape'] = 'Inverted'
        elif spreads.get('10y_2y', 0) < 0.15:
            shape_analysis['shape'] = 'Flat'
        elif spreads.get('10y_2y', 0) > 1.5:
            shape_analysis['shape'] = 'Steep'
        else:
            shape_analysis['shape'] = 'Normal'
        
        return {
            'success': True,
            'spreads': spreads,
            'analysis': shape_analysis
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error analyzing curve: {str(e)}'
        }


def compare_curves(
    date1: Optional[str] = None,
    date2: Optional[str] = None,
    days_back: int = 30
) -> Dict:
    """
    Compare yield curves between two dates
    Show how curve has shifted
    
    Args:
        date1: First date (default: today)
        date2: Second date (default: days_back ago)
        days_back: Days back for second date if not specified
        
    Returns:
        Dict with comparison analysis
    """
    try:
        if not date1:
            date1 = datetime.now().strftime('%Y-%m-%d')
        if not date2:
            d2 = datetime.now() - timedelta(days=days_back)
            date2 = d2.strftime('%Y-%m-%d')
        
        # Get historical data
        hist = get_historical_curve(start_date=date2, end_date=date1)
        
        if not hist.get('success'):
            return hist
        
        curves = hist['curves']
        
        # Find closest dates
        curve1_date = min(curves.keys(), key=lambda d: abs((datetime.strptime(d, '%Y-%m-%d') - datetime.strptime(date1, '%Y-%m-%d')).days))
        curve2_date = min(curves.keys(), key=lambda d: abs((datetime.strptime(d, '%Y-%m-%d') - datetime.strptime(date2, '%Y-%m-%d')).days))
        
        curve1 = curves[curve1_date]
        curve2 = curves[curve2_date]
        
        # Calculate changes
        changes = {}
        for maturity in MATURITIES.keys():
            if maturity in curve1 and maturity in curve2:
                y1 = curve1[maturity]['yield']
                y2 = curve2[maturity]['yield']
                change = round(y1 - y2, 2)
                changes[maturity] = {
                    'maturity': MATURITIES[maturity]['label'],
                    'current': y1,
                    'previous': y2,
                    'change_bps': int(change * 100),  # basis points
                    'change_pct': round((change / y2) * 100, 1) if y2 != 0 else 0
                }
        
        # Determine shift type
        avg_change = sum(c['change_bps'] for c in changes.values()) / len(changes) if changes else 0
        
        shift_type = 'unchanged'
        if avg_change > 10:
            shift_type = 'Bear steepening' if changes.get('30_YEAR', {}).get('change_bps', 0) > changes.get('2_YEAR', {}).get('change_bps', 0) else 'Parallel shift up'
        elif avg_change < -10:
            shift_type = 'Bull steepening' if changes.get('30_YEAR', {}).get('change_bps', 0) < changes.get('2_YEAR', {}).get('change_bps', 0) else 'Parallel shift down'
        
        return {
            'success': True,
            'date1': curve1_date,
            'date2': curve2_date,
            'changes': changes,
            'avg_change_bps': int(avg_change),
            'shift_type': shift_type
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error comparing curves: {str(e)}'
        }


def get_specific_maturity(maturity: str, days_back: int = 365) -> Dict:
    """
    Get historical data for a specific maturity
    
    Args:
        maturity: Maturity code (e.g., '10Y', '2Y', '3M')
        days_back: Historical lookback period
        
    Returns:
        Dict with time series for the maturity
    """
    try:
        # Find maturity key
        maturity_key = None
        for key, info in MATURITIES.items():
            if info['label'].upper() == maturity.upper():
                maturity_key = key
                break
        
        if not maturity_key:
            return {'success': False, 'error': f'Invalid maturity: {maturity}'}
        
        # Get historical curves
        hist = get_historical_curve(days_back=days_back)
        
        if not hist.get('success'):
            return hist
        
        # Extract time series for this maturity
        time_series = []
        for date in sorted(hist['dates']):
            curve = hist['curves'][date]
            if maturity_key in curve:
                time_series.append({
                    'date': date,
                    'yield': curve[maturity_key]['yield']
                })
        
        if not time_series:
            return {'success': False, 'error': f'No data for {maturity}'}
        
        # Calculate statistics
        yields = [point['yield'] for point in time_series]
        latest = yields[0] if time_series else 0
        avg = sum(yields) / len(yields) if yields else 0
        min_yield = min(yields) if yields else 0
        max_yield = max(yields) if yields else 0
        
        return {
            'success': True,
            'maturity': maturity.upper(),
            'latest': latest,
            'average': round(avg, 2),
            'min': min_yield,
            'max': max_yield,
            'time_series': time_series,
            'count': len(time_series)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching maturity data: {str(e)}'
        }


# ========== HELPER FUNCTIONS ==========

def _calculate_curve_metrics(curve_data: Dict) -> Dict:
    """Calculate summary metrics for yield curve"""
    if not curve_data:
        return {}
    
    yields = [v['yield'] for v in curve_data.values()]
    
    metrics = {
        'average_yield': round(sum(yields) / len(yields), 2),
        'min_yield': round(min(yields), 2),
        'max_yield': round(max(yields), 2),
        'range': round(max(yields) - min(yields), 2)
    }
    
    # Add specific benchmarks if available
    curve_dict = {v['maturity']: v['yield'] for v in curve_data.values()}
    
    if '3M' in curve_dict:
        metrics['short_rate'] = curve_dict['3M']
    if '10Y' in curve_dict:
        metrics['long_rate'] = curve_dict['10Y']
    if '3M' in curve_dict and '10Y' in curve_dict:
        metrics['10y_3m_spread'] = round(curve_dict['10Y'] - curve_dict['3M'], 2)
    
    return metrics


def _format_curve_table(curve_data: Dict, metrics: Dict) -> str:
    """Format yield curve as ASCII table"""
    lines = []
    lines.append("\n" + "="*60)
    lines.append("US TREASURY YIELD CURVE")
    lines.append("="*60)
    lines.append(f"{'Maturity':<12} {'Yield':<10} {'Days':<10}")
    lines.append("-"*60)
    
    for maturity_key, data in curve_data.items():
        maturity = data['maturity']
        yield_val = data['yield']
        days = data['days']
        lines.append(f"{maturity:<12} {yield_val:>6.2f}%    {days:<10}")
    
    lines.append("-"*60)
    lines.append(f"Average Yield: {metrics.get('average_yield', 0):.2f}%")
    lines.append(f"Range: {metrics.get('range', 0):.2f}%")
    
    if '10y_3m_spread' in metrics:
        spread = metrics['10y_3m_spread']
        status = "⚠️ INVERTED" if spread < 0 else "✓ Normal"
        lines.append(f"10Y-3M Spread: {spread:.2f}% {status}")
    
    lines.append("="*60 + "\n")
    
    return "\n".join(lines)


def _get_curve_from_fred() -> Dict:
    """Fallback: Get yield curve from FRED API"""
    try:
        curve_data = {}
        
        for key, info in MATURITIES.items():
            fred_series = info.get('fred')
            if not fred_series:
                continue
            
            url = f"{FRED_BASE_URL}/series/observations"
            params = {
                'series_id': fred_series,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            
            if FRED_API_KEY:
                params['api_key'] = FRED_API_KEY
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('observations'):
                    obs = data['observations'][0]
                    if obs['value'] != '.':
                        curve_data[key] = {
                            'maturity': info['label'],
                            'days': info['days'],
                            'yield': float(obs['value']),
                            'date': obs['date']
                        }
        
        if curve_data:
            metrics = _calculate_curve_metrics(curve_data)
            return {
                'success': True,
                'source': 'FRED',
                'curve': curve_data,
                'metrics': metrics,
                'count': len(curve_data)
            }
        
        return {'success': False, 'error': 'No data from FRED'}
        
    except Exception as e:
        return {'success': False, 'error': f'FRED fallback failed: {str(e)}'}


# ========== CLI INTERFACE ==========

def main():
    """CLI interface for treasury curve module"""
    if len(sys.argv) < 2:
        print("Usage: treasury_curve.py <command> [options]")
        print("\nCommands:")
        print("  yield-curve              Get current yield curve")
        print("  yield-history [days]     Get historical curves (default: 90 days)")
        print("  yield-analyze            Analyze curve shape and inversions")
        print("  yield-compare [days]     Compare curves (default: 30 days back)")
        print("  yield-maturity <code>    Get specific maturity (e.g., 10Y)")
        return
    
    command = sys.argv[1]
    
    if command == 'yield-curve':
        result = get_current_curve(format_table=True)
        if result.get('table'):
            print(result['table'])
        print(json.dumps(result, indent=2))
    
    elif command == 'yield-history':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        result = get_historical_curve(days_back=days)
        print(json.dumps(result, indent=2))
    
    elif command == 'yield-analyze':
        result = analyze_curve_shape()
        print(json.dumps(result, indent=2))
    
    elif command == 'yield-compare':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = compare_curves(days_back=days)
        print(json.dumps(result, indent=2))
    
    elif command == 'yield-maturity':
        if len(sys.argv) < 3:
            print("Error: Specify maturity (e.g., 10Y)")
            return
        maturity = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        result = get_specific_maturity(maturity, days_back=days)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
