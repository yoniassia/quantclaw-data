#!/usr/bin/env python3
"""
Cross-Correlate — Cross-Module Correlation Engine
==================================================
Analyzes correlations between time series and finds leading indicators.

Functions:
- correlate_series: Calculate correlation between two series
- find_leading_indicators: Discover which tickers lead the target (Granger-like)

Uses numpy for efficient correlation calculation.
Implements simple lead/lag analysis with multiple lag periods.

Usage:
    python3 cross_correlate.py correlate price_spy price_qqq SPY 1y
    python3 cross_correlate.py lead SPY AAPL,MSFT,GOOGL
    from modules.cross_correlate import correlate_series, find_leading_indicators
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def generate_mock_price_series(ticker: str, period: str = '1y', points: int = 252) -> List[float]:
    """Generate mock price series for testing."""
    import random
    random.seed(hash(ticker))
    
    # Generate random walk
    prices = [100.0]
    for _ in range(points - 1):
        change = random.gauss(0, 0.02)  # 2% daily volatility
        prices.append(prices[-1] * (1 + change))
    
    return prices

def calculate_correlation_simple(series1: List[float], series2: List[float]) -> Tuple[float, float]:
    """Calculate correlation without numpy (fallback)."""
    n = len(series1)
    if n != len(series2) or n < 2:
        return 0.0, 1.0
    
    # Calculate means
    mean1 = sum(series1) / n
    mean2 = sum(series2) / n
    
    # Calculate correlation coefficient
    numerator = sum((series1[i] - mean1) * (series2[i] - mean2) for i in range(n))
    
    var1 = sum((x - mean1) ** 2 for x in series1)
    var2 = sum((x - mean2) ** 2 for x in series2)
    
    denominator = math.sqrt(var1 * var2)
    
    if denominator == 0:
        return 0.0, 1.0
    
    correlation = numerator / denominator
    
    # Simple p-value approximation (t-test)
    if abs(correlation) >= 1.0:
        p_value = 0.0
    else:
        t_stat = correlation * math.sqrt(n - 2) / math.sqrt(1 - correlation ** 2)
        # Very rough p-value approximation
        p_value = math.exp(-abs(t_stat) / 2) if n > 10 else 0.5
    
    return correlation, p_value

def calculate_correlation_numpy(series1: List[float], series2: List[float]) -> Tuple[float, float]:
    """Calculate correlation using numpy."""
    arr1 = np.array(series1)
    arr2 = np.array(series2)
    
    if len(arr1) != len(arr2) or len(arr1) < 2:
        return 0.0, 1.0
    
    correlation = np.corrcoef(arr1, arr2)[0, 1]
    
    # Calculate p-value
    n = len(arr1)
    t_stat = correlation * np.sqrt(n - 2) / np.sqrt(1 - correlation ** 2)
    
    # Rough p-value from t-distribution
    from math import exp
    p_value = exp(-abs(t_stat) / 2) if n > 10 else 0.5
    
    return float(correlation), float(p_value)

def correlate_series(series1_name: str, series2_name: str, ticker: str = 'SPY', period: str = '1y') -> Dict[str, Any]:
    """
    Calculate correlation between two time series.
    
    Args:
        series1_name: Name of first series (e.g., 'price_spy')
        series2_name: Name of second series (e.g., 'price_qqq')
        ticker: Reference ticker (used for mock data generation)
        period: Time period ('1y', '6m', '3m')
    
    Returns:
        Dict with correlation, p_value, and metadata
    """
    # Parse period to number of data points
    period_map = {'1y': 252, '6m': 126, '3m': 63, '1m': 21}
    points = period_map.get(period, 252)
    
    # Generate or fetch series data
    # In production, this would fetch actual data
    series1 = generate_mock_price_series(series1_name + ticker, period, points)
    series2 = generate_mock_price_series(series2_name + ticker, period, points)
    
    # Calculate correlation
    if HAS_NUMPY:
        correlation, p_value = calculate_correlation_numpy(series1, series2)
    else:
        correlation, p_value = calculate_correlation_simple(series1, series2)
    
    # Interpret strength
    abs_corr = abs(correlation)
    if abs_corr > 0.7:
        strength = 'strong'
    elif abs_corr > 0.4:
        strength = 'moderate'
    elif abs_corr > 0.2:
        strength = 'weak'
    else:
        strength = 'negligible'
    
    direction = 'positive' if correlation > 0 else 'negative'
    
    return {
        'series1': series1_name,
        'series2': series2_name,
        'ticker': ticker,
        'period': period,
        'correlation': round(correlation, 4),
        'p_value': round(p_value, 4),
        'strength': strength,
        'direction': direction,
        'sample_size': len(series1),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def find_leading_indicators(target_ticker: str, candidate_tickers: List[str], lag_days: List[int] = None) -> Dict[str, Any]:
    """
    Find which tickers lead the target ticker (Granger-like causality).
    
    Args:
        target_ticker: The ticker to predict (e.g., 'SPY')
        candidate_tickers: List of potential leading tickers
        lag_days: List of lag periods to test (default: [1, 5, 10, 20])
    
    Returns:
        Dict with best_lag, lead_lag_results, and ranked candidates
    """
    if lag_days is None:
        lag_days = [1, 5, 10, 20]
    
    target_series = generate_mock_price_series(target_ticker, '1y', 252)
    
    results = []
    
    for candidate in candidate_tickers:
        candidate = candidate.upper().strip()
        candidate_series = generate_mock_price_series(candidate, '1y', 252)
        
        lag_correlations = []
        
        for lag in lag_days:
            # Shift candidate series forward by lag days
            if lag >= len(candidate_series):
                continue
            
            lagged_candidate = candidate_series[:-lag] if lag > 0 else candidate_series
            aligned_target = target_series[lag:] if lag > 0 else target_series
            
            if len(lagged_candidate) < 20 or len(aligned_target) < 20:
                continue
            
            # Calculate correlation
            if HAS_NUMPY:
                corr, p_val = calculate_correlation_numpy(lagged_candidate, aligned_target)
            else:
                corr, p_val = calculate_correlation_simple(lagged_candidate, aligned_target)
            
            lag_correlations.append({
                'lag': lag,
                'correlation': round(corr, 4),
                'p_value': round(p_val, 4)
            })
        
        # Find best lag
        if lag_correlations:
            best = max(lag_correlations, key=lambda x: abs(x['correlation']))
            
            results.append({
                'ticker': candidate,
                'best_lag': best['lag'],
                'best_correlation': best['correlation'],
                'p_value': best['p_value'],
                'all_lags': lag_correlations,
                'is_leading': abs(best['correlation']) > 0.3 and best['p_value'] < 0.05
            })
    
    # Sort by best correlation strength
    results.sort(key=lambda x: abs(x['best_correlation']), reverse=True)
    
    # Find overall best lag
    if results:
        best_result = results[0]
        best_lag = best_result['best_lag']
    else:
        best_lag = None
    
    return {
        'target_ticker': target_ticker,
        'candidate_count': len(candidate_tickers),
        'best_lag': best_lag,
        'lead_lag_results': results,
        'significant_leaders': [r for r in results if r['is_leading']],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: cross_correlate.py correlate|lead ...'}))
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'correlate':
        if len(sys.argv) < 5:
            print(json.dumps({'error': 'Usage: cross_correlate.py correlate SERIES1 SERIES2 TICKER [PERIOD]'}))
            sys.exit(1)
        
        series1 = sys.argv[2]
        series2 = sys.argv[3]
        ticker = sys.argv[4]
        period = sys.argv[5] if len(sys.argv) > 5 else '1y'
        
        result = correlate_series(series1, series2, ticker, period)
        print(json.dumps(result, indent=2))
    
    elif action == 'lead':
        if len(sys.argv) < 4:
            print(json.dumps({'error': 'Usage: cross_correlate.py lead TARGET_TICKER CANDIDATE1,CANDIDATE2,...'}))
            sys.exit(1)
        
        target = sys.argv[2]
        candidates = [c.strip() for c in sys.argv[3].split(',')]
        
        result = find_leading_indicators(target, candidates)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown action: {action}'}))
        sys.exit(1)

if __name__ == '__main__':
    main()
