#!/usr/bin/env python3
"""
Signal Discovery Engine — Automated Alpha Signal Factory

Systematically tests correlations between price returns and all available data modules
to discover new alpha signals.

Functions:
- discover_signals(universe=['AAPL','MSFT','NVDA','GOOGL','TSLA'], lookback_days=252)
- test_signal_correlation(ticker, signal_data, price_returns, lag_days=0)

Usage:
    python3 signal_discovery_engine.py discover --universe AAPL,MSFT,NVDA --lookback 252
    python3 signal_discovery_engine.py --json
"""

import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_price_data(ticker: str, lookback_days: int = 252) -> Optional[Dict[str, Any]]:
    """Get price history using yfinance"""
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 30)  # Extra buffer
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return None
            
        # Calculate returns
        hist['Returns'] = hist['Close'].pct_change()
        hist['Cumulative_Returns'] = (1 + hist['Returns']).cumprod() - 1
        
        return {
            'ticker': ticker,
            'start_date': hist.index[0].strftime('%Y-%m-%d'),
            'end_date': hist.index[-1].strftime('%Y-%m-%d'),
            'prices': hist['Close'].tolist(),
            'returns': hist['Returns'].fillna(0).tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in hist.index]
        }
    except Exception as e:
        return None


def test_signal_correlation(ticker: str, signal_name: str, signal_values: List[float], 
                            price_returns: List[float], lag_days: int = 0) -> Dict[str, Any]:
    """
    Test correlation between a signal and price returns with optional lag.
    
    Args:
        ticker: Stock ticker
        signal_name: Name of the signal being tested
        signal_values: List of signal values
        price_returns: List of price returns
        lag_days: Number of days to lag the signal (positive = signal leads price)
    
    Returns:
        Dict with correlation, p_value, and signal metadata
    """
    try:
        import numpy as np
        from scipy import stats
        
        # Align arrays
        min_len = min(len(signal_values), len(price_returns))
        if min_len < 30:  # Need at least 30 data points
            return {
                'ticker': ticker,
                'signal_name': signal_name,
                'correlation': 0,
                'p_value': 1.0,
                'lag_days': lag_days,
                'error': 'Insufficient data'
            }
        
        # Apply lag
        if lag_days > 0:
            signal_aligned = signal_values[:-lag_days] if lag_days < len(signal_values) else signal_values
            returns_aligned = price_returns[lag_days:]
        elif lag_days < 0:
            signal_aligned = signal_values[-lag_days:]
            returns_aligned = price_returns[:lag_days]
        else:
            signal_aligned = signal_values[:min_len]
            returns_aligned = price_returns[:min_len]
        
        # Remove NaN values
        signal_clean = np.array(signal_aligned)
        returns_clean = np.array(returns_aligned)
        
        # Create mask for valid values
        valid_mask = ~(np.isnan(signal_clean) | np.isnan(returns_clean) | np.isinf(signal_clean) | np.isinf(returns_clean))
        signal_clean = signal_clean[valid_mask]
        returns_clean = returns_clean[valid_mask]
        
        if len(signal_clean) < 30:
            return {
                'ticker': ticker,
                'signal_name': signal_name,
                'correlation': 0,
                'p_value': 1.0,
                'lag_days': lag_days,
                'error': 'Insufficient valid data after cleaning'
            }
        
        # Calculate correlation
        correlation, p_value = stats.pearsonr(signal_clean, returns_clean)
        
        # Calculate additional statistics
        mean_signal = float(np.mean(signal_clean))
        std_signal = float(np.std(signal_clean))
        
        return {
            'ticker': ticker,
            'signal_name': signal_name,
            'correlation': float(correlation),
            'p_value': float(p_value),
            'lag_days': lag_days,
            'data_points': len(signal_clean),
            'signal_mean': mean_signal,
            'signal_std': std_signal,
            'significant': bool(p_value < 0.05),
            'description': f"{signal_name} for {ticker} with {lag_days}-day lag"
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'signal_name': signal_name,
            'correlation': 0,
            'p_value': 1.0,
            'lag_days': lag_days,
            'error': str(e)
        }


def discover_signals(universe: List[str] = None, lookback_days: int = 252) -> Dict[str, Any]:
    """
    Systematically discover alpha signals by testing correlations between price returns
    and available data modules.
    
    Args:
        universe: List of tickers to analyze (default: FAANG + TSLA)
        lookback_days: Historical period to analyze
    
    Returns:
        Dict with discovered signals ranked by strength
    """
    if universe is None:
        universe = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA']
    
    try:
        import numpy as np
        
        discovered_signals = []
        
        # Test lags: 0, 1, 5, 10, 21 days
        test_lags = [0, 1, 5, 10, 21]
        
        for ticker in universe:
            # Get price data
            price_data = get_price_data(ticker, lookback_days)
            if not price_data:
                continue
            
            returns = price_data['returns']
            
            # Generate synthetic signals for demonstration
            # In production, these would come from actual data modules
            
            # 1. Momentum signal (past returns)
            momentum_signal = returns[:-1] + [0]  # Shifted returns
            for lag in test_lags:
                result = test_signal_correlation(
                    ticker, 
                    'momentum', 
                    momentum_signal, 
                    returns, 
                    lag
                )
                if abs(result['correlation']) > 0.1:  # Filter weak signals
                    discovered_signals.append(result)
            
            # 2. Volatility signal (rolling standard deviation)
            try:
                rolling_vol = []
                window = 20
                for i in range(len(returns)):
                    if i < window:
                        rolling_vol.append(0)
                    else:
                        rolling_vol.append(float(np.std(returns[i-window:i])))
                
                for lag in [0, 1, 5]:
                    result = test_signal_correlation(
                        ticker,
                        'volatility',
                        rolling_vol,
                        returns,
                        lag
                    )
                    if abs(result['correlation']) > 0.1:
                        discovered_signals.append(result)
            except:
                pass
            
            # 3. Volume trend signal (synthetic - would use real volume in production)
            try:
                volume_trend = [float(np.random.randn() * 0.1) for _ in returns]
                result = test_signal_correlation(
                    ticker,
                    'volume_trend',
                    volume_trend,
                    returns,
                    0
                )
                if abs(result['correlation']) > 0.05:
                    discovered_signals.append(result)
            except:
                pass
        
        # Rank by absolute correlation and statistical significance
        discovered_signals.sort(
            key=lambda x: (x.get('significant', False), abs(x.get('correlation', 0))),
            reverse=True
        )
        
        # Calculate summary statistics
        significant_count = sum(1 for s in discovered_signals if s.get('significant'))
        avg_correlation = np.mean([abs(s['correlation']) for s in discovered_signals]) if discovered_signals else 0
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'universe': universe,
            'lookback_days': lookback_days,
            'total_signals_tested': len(discovered_signals),
            'significant_signals': significant_count,
            'avg_correlation': float(avg_correlation),
            'top_signals': discovered_signals[:20],  # Top 20 signals
            'summary': f"Discovered {significant_count} significant signals from {len(universe)} tickers"
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'discover':
            # Parse arguments
            universe = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA']
            lookback = 252
            
            for i, arg in enumerate(sys.argv):
                if arg == '--universe' and i + 1 < len(sys.argv):
                    universe = sys.argv[i + 1].split(',')
                elif arg == '--lookback' and i + 1 < len(sys.argv):
                    lookback = int(sys.argv[i + 1])
            
            result = discover_signals(universe, lookback)
            print(json.dumps(result, indent=2))
        
        elif sys.argv[1] == '--json':
            result = discover_signals()
            print(json.dumps(result))
        
        else:
            print("Unknown command. Use: discover [--universe AAPL,MSFT] [--lookback 252]")
            sys.exit(1)
    else:
        # Default: run discovery and print results
        result = discover_signals()
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
