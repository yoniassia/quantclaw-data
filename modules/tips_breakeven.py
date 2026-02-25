#!/usr/bin/env python3
"""
TIPS & Breakeven Inflation Module — Phase 159

Treasury Inflation-Protected Securities (TIPS) analysis and breakeven
inflation expectations from Federal Reserve Economic Data (FRED).

Tracks:
- TIPS real yields across maturities (5Y, 7Y, 10Y, 20Y, 30Y)
- Breakeven inflation rates (market-implied inflation expectations)
- Nominal Treasury yields vs TIPS real yields
- Inflation risk premium analysis
- Historical trends and projections

Data Sources:
- FRED API (Federal Reserve Economic Data)
- TIPS real yield series (DFII series)
- Breakeven inflation series (T*IE series)
- Nominal Treasury series (DGS series)

Refresh: Daily
Coverage: Current expectations + historical analysis back to 2003

Author: QUANTCLAW DATA Build Agent
Phase: 159
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""

# Load FRED API key from credentials
try:
    import os
    creds_path = os.path.expanduser('~/.openclaw/workspace/.credentials/fred-api.json')
    if os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            FRED_API_KEY = creds.get('fredApiKey', '')
except:
    pass

# ========== TIPS & BREAKEVEN INFLATION SERIES ==========

TIPS_SERIES = {
    # Real Yields (TIPS)
    'REAL_YIELDS': {
        'DFII5': '5-Year TIPS Constant Maturity Rate',
        'DFII7': '7-Year TIPS Constant Maturity Rate',
        'DFII10': '10-Year TIPS Constant Maturity Rate',
        'DFII20': '20-Year TIPS Constant Maturity Rate',
        'DFII30': '30-Year TIPS Constant Maturity Rate',
    },
    
    # Breakeven Inflation Rates (Nominal - TIPS)
    'BREAKEVEN': {
        'T5YIE': '5-Year Breakeven Inflation Rate',
        'T7YIE': '7-Year Breakeven Inflation Rate',
        'T10YIE': '10-Year Breakeven Inflation Rate',
        'T20YIE': '20-Year Breakeven Inflation Rate',
        'T30YIE': '30-Year Breakeven Inflation Rate',
    },
    
    # Nominal Treasury Yields (for comparison)
    'NOMINAL': {
        'DGS5': '5-Year Treasury Constant Maturity Rate',
        'DGS7': '7-Year Treasury Constant Maturity Rate',
        'DGS10': '10-Year Treasury Constant Maturity Rate',
        'DGS20': '20-Year Treasury Constant Maturity Rate',
        'DGS30': '30-Year Treasury Constant Maturity Rate',
    },
    
    # Forward Inflation Expectations
    'FORWARD_INFLATION': {
        'T5YIFR': '5-Year, 5-Year Forward Inflation Expectation Rate',
    },
    
    # Actual Inflation Measures (for comparison)
    'ACTUAL_INFLATION': {
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
        'CPILFESL': 'Core CPI (ex Food & Energy)',
        'PCEPI': 'Personal Consumption Expenditures Price Index',
        'PCEPILFE': 'Core PCE Price Index',
    }
}

# Maturity mapping
MATURITIES = ['5Y', '7Y', '10Y', '20Y', '30Y']

# ========== CORE FUNCTIONS ==========

def get_current_tips_data(include_inflation: bool = True) -> Dict:
    """
    Get current TIPS yields, breakeven rates, and nominal yields
    
    Args:
        include_inflation: Include actual inflation measures
        
    Returns:
        Dict with current TIPS market data
    """
    try:
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'real_yields': {},
            'breakeven_rates': {},
            'nominal_yields': {},
            'date': None
        }
        
        # Fetch real yields (TIPS)
        for series_id, description in TIPS_SERIES['REAL_YIELDS'].items():
            data = _fetch_latest_value(series_id)
            if data:
                maturity = series_id.replace('DFII', '') + 'Y'
                result['real_yields'][maturity] = {
                    'value': data['value'],
                    'date': data['date'],
                    'series': series_id,
                    'description': description
                }
                if not result['date'] or data['date'] > result['date']:
                    result['date'] = data['date']
        
        # Fetch breakeven inflation rates
        for series_id, description in TIPS_SERIES['BREAKEVEN'].items():
            data = _fetch_latest_value(series_id)
            if data:
                maturity = series_id.replace('T', '').replace('IE', '')
                result['breakeven_rates'][maturity] = {
                    'value': data['value'],
                    'date': data['date'],
                    'series': series_id,
                    'description': description
                }
        
        # Fetch nominal yields
        for series_id, description in TIPS_SERIES['NOMINAL'].items():
            data = _fetch_latest_value(series_id)
            if data:
                maturity = series_id.replace('DGS', '') + 'Y'
                result['nominal_yields'][maturity] = {
                    'value': data['value'],
                    'date': data['date'],
                    'series': series_id,
                    'description': description
                }
        
        # Fetch forward inflation expectations
        fwd_data = _fetch_latest_value('T5YIFR')
        if fwd_data:
            result['forward_5y5y'] = {
                'value': fwd_data['value'],
                'date': fwd_data['date'],
                'description': '5-Year, 5-Year Forward Inflation Expectation'
            }
        
        # Include actual inflation if requested
        if include_inflation:
            result['actual_inflation'] = {}
            for series_id, description in TIPS_SERIES['ACTUAL_INFLATION'].items():
                data = _fetch_latest_value(series_id)
                if data:
                    # For inflation indices, calculate YoY change
                    hist = _fetch_historical_data(series_id, days_back=365)
                    if hist and len(hist) > 250:
                        recent = hist[0]['value']
                        year_ago = hist[-1]['value']
                        yoy_pct = ((recent - year_ago) / year_ago) * 100
                        
                        result['actual_inflation'][series_id] = {
                            'current': recent,
                            'yoy_change_pct': round(yoy_pct, 2),
                            'date': data['date'],
                            'description': description
                        }
        
        # Calculate summary statistics
        result['summary'] = _calculate_tips_summary(result)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching TIPS data: {str(e)}'
        }


def analyze_breakeven_curve(format_table: bool = False) -> Dict:
    """
    Analyze the breakeven inflation curve shape and trends
    
    Args:
        format_table: Return formatted ASCII table
        
    Returns:
        Dict with breakeven curve analysis
    """
    try:
        data = get_current_tips_data(include_inflation=True)
        
        if not data.get('success'):
            return data
        
        breakevens = data['breakeven_rates']
        
        # Sort by maturity
        sorted_breakevens = {}
        for maturity in MATURITIES:
            if maturity in breakevens:
                sorted_breakevens[maturity] = breakevens[maturity]['value']
        
        # Analyze curve shape
        analysis = {
            'success': True,
            'date': data['date'],
            'breakevens': sorted_breakevens,
            'shape': 'unknown',
            'slope': 0,
            'signals': []
        }
        
        # Calculate slope (10Y - 5Y)
        if '10Y' in sorted_breakevens and '5Y' in sorted_breakevens:
            analysis['slope'] = round(sorted_breakevens['10Y'] - sorted_breakevens['5Y'], 2)
            
            if analysis['slope'] > 0.3:
                analysis['shape'] = 'Upward sloping (higher long-term inflation expected)'
            elif analysis['slope'] < -0.1:
                analysis['shape'] = 'Inverted (lower long-term inflation expected)'
                analysis['signals'].append('⚠️ Inverted breakeven curve - deflationary concerns')
            else:
                analysis['shape'] = 'Flat (stable inflation expectations)'
        
        # Check absolute levels
        if '10Y' in sorted_breakevens:
            be_10y = sorted_breakevens['10Y']
            
            if be_10y < 1.5:
                analysis['signals'].append('🔵 Low inflation expectations (< 1.5%)')
            elif be_10y > 3.0:
                analysis['signals'].append('🔴 High inflation expectations (> 3.0%)')
            elif be_10y >= 1.8 and be_10y <= 2.5:
                analysis['signals'].append('✅ Inflation expectations near Fed target (2%)')
        
        # Compare to actual inflation
        if 'actual_inflation' in data and 'CPIAUCSL' in data['actual_inflation']:
            actual_cpi = data['actual_inflation']['CPIAUCSL']['yoy_change_pct']
            if '10Y' in sorted_breakevens:
                diff = round(sorted_breakevens['10Y'] - actual_cpi, 2)
                analysis['actual_vs_expected'] = {
                    'expected_10y': sorted_breakevens['10Y'],
                    'actual_cpi': actual_cpi,
                    'difference': diff
                }
                
                if diff < -1.0:
                    analysis['signals'].append(f'📉 Inflation expectations below current CPI by {abs(diff):.1f}%')
                elif diff > 1.0:
                    analysis['signals'].append(f'📈 Inflation expectations above current CPI by {diff:.1f}%')
        
        if format_table:
            analysis['table'] = _format_breakeven_table(sorted_breakevens, analysis)
        
        return analysis
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error analyzing breakeven curve: {str(e)}'
        }


def get_real_yield_history(
    maturity: str = '10Y',
    days_back: int = 365
) -> Dict:
    """
    Get historical real yield (TIPS) data for a specific maturity
    
    Args:
        maturity: Maturity (5Y, 7Y, 10Y, 20Y, 30Y)
        days_back: Historical lookback period
        
    Returns:
        Dict with time series data
    """
    try:
        # Map maturity to FRED series
        series_map = {
            '5Y': 'DFII5',
            '7Y': 'DFII7',
            '10Y': 'DFII10',
            '20Y': 'DFII20',
            '30Y': 'DFII30',
        }
        
        if maturity not in series_map:
            return {'success': False, 'error': f'Invalid maturity: {maturity}'}
        
        series_id = series_map[maturity]
        
        # Fetch historical data
        history = _fetch_historical_data(series_id, days_back=days_back)
        
        if not history:
            return {'success': False, 'error': 'No historical data available'}
        
        # Calculate statistics
        values = [point['value'] for point in history]
        latest = values[0]
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        return {
            'success': True,
            'maturity': maturity,
            'series_id': series_id,
            'latest': latest,
            'average': round(avg, 2),
            'min': min_val,
            'max': max_val,
            'time_series': history,
            'count': len(history),
            'period_days': days_back
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching real yield history: {str(e)}'
        }


def compare_tips_vs_nominal(maturity: str = '10Y') -> Dict:
    """
    Compare TIPS (real) yields vs nominal Treasury yields
    Shows the implied inflation expectation (breakeven)
    
    Args:
        maturity: Maturity to compare (5Y, 7Y, 10Y, 20Y, 30Y)
        
    Returns:
        Dict with comparison analysis
    """
    try:
        data = get_current_tips_data(include_inflation=False)
        
        if not data.get('success'):
            return data
        
        if maturity not in data['real_yields'] or maturity not in data['nominal_yields']:
            return {'success': False, 'error': f'Data not available for {maturity}'}
        
        real = data['real_yields'][maturity]['value']
        nominal = data['nominal_yields'][maturity]['value']
        breakeven = data['breakeven_rates'].get(maturity, {}).get('value', nominal - real)
        
        result = {
            'success': True,
            'maturity': maturity,
            'date': data['date'],
            'nominal_yield': nominal,
            'real_yield': real,
            'breakeven_inflation': round(breakeven, 2),
            'analysis': []
        }
        
        # Fisher equation: nominal ≈ real + expected_inflation
        implied_breakeven = round(nominal - real, 2)
        result['implied_breakeven'] = implied_breakeven
        
        # Analysis
        if real < 0:
            result['analysis'].append(f'⚠️ Negative real yield ({real:.2f}%)')
        
        if breakeven < 1.5:
            result['analysis'].append('🔵 Low inflation expectations')
        elif breakeven > 3.0:
            result['analysis'].append('🔴 High inflation expectations')
        else:
            result['analysis'].append('✅ Moderate inflation expectations')
        
        # Real return context
        if real > 2.0:
            result['analysis'].append(f'💰 Attractive real return ({real:.2f}%)')
        elif real < 0.5:
            result['analysis'].append(f'📉 Low real return ({real:.2f}%)')
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error comparing TIPS vs nominal: {str(e)}'
        }


def get_inflation_expectations_summary() -> Dict:
    """
    Get comprehensive summary of market inflation expectations
    Includes breakeven rates, forward expectations, and actual inflation
    
    Returns:
        Dict with inflation expectations summary
    """
    try:
        data = get_current_tips_data(include_inflation=True)
        
        if not data.get('success'):
            return data
        
        summary = {
            'success': True,
            'date': data['date'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Short-term expectations (5Y)
        if '5Y' in data['breakeven_rates']:
            summary['short_term_5y'] = {
                'breakeven': data['breakeven_rates']['5Y']['value'],
                'timeframe': '5-Year'
            }
        
        # Medium-term expectations (10Y - most watched)
        if '10Y' in data['breakeven_rates']:
            summary['medium_term_10y'] = {
                'breakeven': data['breakeven_rates']['10Y']['value'],
                'timeframe': '10-Year'
            }
        
        # Long-term expectations (30Y)
        if '30Y' in data['breakeven_rates']:
            summary['long_term_30y'] = {
                'breakeven': data['breakeven_rates']['30Y']['value'],
                'timeframe': '30-Year'
            }
        
        # Forward expectations (what market expects 5-10 years out)
        if 'forward_5y5y' in data:
            summary['forward_5y5y'] = {
                'rate': data['forward_5y5y']['value'],
                'description': 'Expected inflation 5-10 years from now'
            }
        
        # Actual inflation
        if 'actual_inflation' in data:
            summary['actual_inflation'] = {}
            
            if 'CPIAUCSL' in data['actual_inflation']:
                summary['actual_inflation']['headline_cpi'] = data['actual_inflation']['CPIAUCSL']['yoy_change_pct']
            
            if 'CPILFESL' in data['actual_inflation']:
                summary['actual_inflation']['core_cpi'] = data['actual_inflation']['CPILFESL']['yoy_change_pct']
            
            if 'PCEPI' in data['actual_inflation']:
                summary['actual_inflation']['headline_pce'] = data['actual_inflation']['PCEPI']['yoy_change_pct']
            
            if 'PCEPILFE' in data['actual_inflation']:
                summary['actual_inflation']['core_pce'] = data['actual_inflation']['PCEPILFE']['yoy_change_pct']
        
        # Generate signals
        summary['signals'] = []
        
        if 'medium_term_10y' in summary:
            be_10y = summary['medium_term_10y']['breakeven']
            
            if be_10y < 1.5:
                summary['signals'].append('🔵 Market expects LOW inflation (< 1.5%)')
            elif be_10y > 3.0:
                summary['signals'].append('🔴 Market expects HIGH inflation (> 3.0%)')
            elif be_10y >= 1.8 and be_10y <= 2.5:
                summary['signals'].append('✅ Inflation expectations ANCHORED near Fed 2% target')
        
        # Compare forward to spot
        if 'forward_5y5y' in summary and 'medium_term_10y' in summary:
            fwd = summary['forward_5y5y']['rate']
            spot = summary['medium_term_10y']['breakeven']
            
            if fwd > spot + 0.3:
                summary['signals'].append('📈 Market expects inflation to RISE in outer years')
            elif fwd < spot - 0.3:
                summary['signals'].append('📉 Market expects inflation to FALL in outer years')
        
        return summary
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating inflation expectations summary: {str(e)}'
        }


def track_breakeven_changes(days_back: int = 30) -> Dict:
    """
    Track how breakeven inflation rates have changed over time
    
    Args:
        days_back: Period to analyze
        
    Returns:
        Dict with change analysis
    """
    try:
        result = {
            'success': True,
            'period_days': days_back,
            'changes': {}
        }
        
        # Fetch historical data for each breakeven series
        for maturity in MATURITIES:
            series_map = {
                '5Y': 'T5YIE',
                '7Y': 'T7YIE',
                '10Y': 'T10YIE',
                '20Y': 'T20YIE',
                '30Y': 'T30YIE',
            }
            
            if maturity not in series_map:
                continue
            
            series_id = series_map[maturity]
            history = _fetch_historical_data(series_id, days_back=days_back)
            
            if not history or len(history) < 2:
                continue
            
            current = history[0]['value']
            previous = history[-1]['value']
            change = round(current - previous, 2)
            change_bps = int(change * 100)
            
            result['changes'][maturity] = {
                'current': current,
                'previous': previous,
                'change': change,
                'change_bps': change_bps,
                'current_date': history[0]['date'],
                'previous_date': history[-1]['date']
            }
        
        # Summary
        if result['changes']:
            avg_change = sum(c['change'] for c in result['changes'].values()) / len(result['changes'])
            result['avg_change'] = round(avg_change, 2)
            result['avg_change_bps'] = int(avg_change * 100)
            
            if avg_change > 0.2:
                result['trend'] = 'Inflation expectations RISING'
            elif avg_change < -0.2:
                result['trend'] = 'Inflation expectations FALLING'
            else:
                result['trend'] = 'Inflation expectations STABLE'
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error tracking breakeven changes: {str(e)}'
        }


# ========== HELPER FUNCTIONS ==========

def _fetch_latest_value(series_id: str) -> Optional[Dict]:
    """Fetch the most recent value for a FRED series"""
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
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
                    return {
                        'value': float(obs['value']),
                        'date': obs['date']
                    }
        
        return None
        
    except Exception as e:
        return None


def _fetch_historical_data(
    series_id: str,
    days_back: int = 365
) -> Optional[List[Dict]]:
    """Fetch historical data for a FRED series"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'sort_order': 'desc'
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('observations'):
                return [
                    {'date': obs['date'], 'value': float(obs['value'])}
                    for obs in data['observations']
                    if obs['value'] != '.'
                ]
        
        return None
        
    except Exception as e:
        return None


def _calculate_tips_summary(data: Dict) -> Dict:
    """Calculate summary statistics from TIPS data"""
    summary = {}
    
    # Average real yield
    if data.get('real_yields'):
        real_yields = [v['value'] for v in data['real_yields'].values()]
        summary['avg_real_yield'] = round(sum(real_yields) / len(real_yields), 2)
    
    # Average breakeven
    if data.get('breakeven_rates'):
        breakevens = [v['value'] for v in data['breakeven_rates'].values()]
        summary['avg_breakeven'] = round(sum(breakevens) / len(breakevens), 2)
    
    # Curve slope (10Y - 5Y breakeven)
    if '10Y' in data.get('breakeven_rates', {}) and '5Y' in data.get('breakeven_rates', {}):
        slope = data['breakeven_rates']['10Y']['value'] - data['breakeven_rates']['5Y']['value']
        summary['breakeven_slope_10y_5y'] = round(slope, 2)
    
    return summary


def _format_breakeven_table(breakevens: Dict, analysis: Dict) -> str:
    """Format breakeven inflation curve as ASCII table"""
    lines = []
    lines.append("\n" + "="*70)
    lines.append("BREAKEVEN INFLATION CURVE")
    lines.append("="*70)
    lines.append(f"Date: {analysis.get('date', 'N/A')}")
    lines.append(f"Shape: {analysis.get('shape', 'Unknown')}")
    lines.append(f"Slope (10Y-5Y): {analysis.get('slope', 0):.2f}%")
    lines.append("-"*70)
    lines.append(f"{'Maturity':<12} {'Breakeven Rate':<20}")
    lines.append("-"*70)
    
    for maturity in MATURITIES:
        if maturity in breakevens:
            lines.append(f"{maturity:<12} {breakevens[maturity]:>6.2f}%")
    
    lines.append("-"*70)
    
    if analysis.get('signals'):
        lines.append("\nSignals:")
        for signal in analysis['signals']:
            lines.append(f"  {signal}")
    
    if 'actual_vs_expected' in analysis:
        lines.append("\nActual vs Expected:")
        ave = analysis['actual_vs_expected']
        lines.append(f"  Expected (10Y): {ave['expected_10y']:.2f}%")
        lines.append(f"  Actual CPI: {ave['actual_cpi']:.2f}%")
        lines.append(f"  Difference: {ave['difference']:.2f}%")
    
    lines.append("="*70 + "\n")
    
    return "\n".join(lines)


# ========== CLI INTERFACE ==========

def main():
    """CLI interface for TIPS & Breakeven Inflation module"""
    if len(sys.argv) < 2:
        print("Usage: tips_breakeven.py <command> [options]")
        print("\nCommands:")
        print("  tips-current             Get current TIPS yields and breakeven rates")
        print("  breakeven-curve          Analyze breakeven inflation curve")
        print("  real-yield-history <maturity> [days]  Historical real yields (e.g., 10Y)")
        print("  tips-vs-nominal <maturity>  Compare TIPS vs nominal yields")
        print("  inflation-expectations   Summary of market inflation expectations")
        print("  breakeven-changes [days] Track breakeven rate changes (default: 30)")
        return
    
    command = sys.argv[1]
    
    if command == 'tips-current':
        result = get_current_tips_data(include_inflation=True)
        print(json.dumps(result, indent=2))
    
    elif command == 'breakeven-curve':
        result = analyze_breakeven_curve(format_table=True)
        if result.get('table'):
            print(result['table'])
        print(json.dumps(result, indent=2))
    
    elif command == 'real-yield-history':
        if len(sys.argv) < 3:
            print("Error: Specify maturity (e.g., 10Y)")
            return
        maturity = sys.argv[2].upper()
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        result = get_real_yield_history(maturity, days_back=days)
        print(json.dumps(result, indent=2))
    
    elif command == 'tips-vs-nominal':
        maturity = sys.argv[2].upper() if len(sys.argv) > 2 else '10Y'
        result = compare_tips_vs_nominal(maturity)
        print(json.dumps(result, indent=2))
    
    elif command == 'inflation-expectations':
        result = get_inflation_expectations_summary()
        print(json.dumps(result, indent=2))
    
    elif command == 'breakeven-changes':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = track_breakeven_changes(days_back=days)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
