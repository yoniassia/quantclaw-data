#!/usr/bin/env python3
"""
Regime Correlation — Cross-Asset Regime Detector

Tracks rolling correlations between major assets to detect market regime changes.
Identifies: risk-on, risk-off, transition, and decorrelation regimes.

Functions:
- detect_regime(lookback=60) → current market regime
- get_correlation_matrix(tickers, period='6mo') → NxN correlation matrix

Usage:
    python3 regime_correlation.py detect --lookback 60
    python3 regime_correlation.py matrix --tickers SPY,TLT,GLD
    python3 regime_correlation.py --json
"""

import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# Major asset tickers for regime detection
MAJOR_ASSETS = {
    'SPY': 'US Equities',
    'TLT': 'US Bonds (20Y)',
    'GLD': 'Gold',
    'BTC-USD': 'Bitcoin',
    'DX-Y.NYB': 'US Dollar Index',
    'USO': 'Oil'
}


def get_asset_data(tickers: List[str], period: str = '6mo') -> Optional[Dict[str, Any]]:
    """Fetch historical data for multiple assets"""
    try:
        import yfinance as yf
        import pandas as pd
        
        data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    data[ticker] = hist['Close']
            except:
                continue
        
        if not data:
            return None
        
        # Create DataFrame with all assets
        df = pd.DataFrame(data)
        df = df.dropna()
        
        return {
            'data': df,
            'start_date': df.index[0].strftime('%Y-%m-%d'),
            'end_date': df.index[-1].strftime('%Y-%m-%d'),
            'tickers': list(df.columns)
        }
    except Exception as e:
        return None


def get_correlation_matrix(tickers: List[str] = None, period: str = '6mo') -> Dict[str, Any]:
    """
    Calculate correlation matrix for given tickers.
    
    Args:
        tickers: List of ticker symbols (default: major assets)
        period: Time period (e.g., '6mo', '1y', '2y')
    
    Returns:
        Dict with correlation matrix and metadata
    """
    if tickers is None:
        tickers = list(MAJOR_ASSETS.keys())
    
    try:
        import pandas as pd
        import numpy as np
        
        asset_data = get_asset_data(tickers, period)
        if not asset_data:
            return {
                'error': 'Failed to fetch asset data',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        df = asset_data['data']
        
        # Calculate returns
        returns = df.pct_change().dropna()
        
        # Calculate correlation matrix
        corr_matrix = returns.corr()
        
        # Convert to dict format
        matrix_dict = {}
        for ticker1 in corr_matrix.index:
            matrix_dict[ticker1] = {}
            for ticker2 in corr_matrix.columns:
                matrix_dict[ticker1][ticker2] = float(corr_matrix.loc[ticker1, ticker2])
        
        # Find strongest correlations (excluding diagonal)
        strong_correlations = []
        for i, ticker1 in enumerate(corr_matrix.index):
            for j, ticker2 in enumerate(corr_matrix.columns):
                if i < j:  # Upper triangle only
                    corr = corr_matrix.loc[ticker1, ticker2]
                    strong_correlations.append({
                        'pair': f"{ticker1}-{ticker2}",
                        'correlation': float(corr),
                        'asset1': ticker1,
                        'asset2': ticker2
                    })
        
        strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period': period,
            'start_date': asset_data['start_date'],
            'end_date': asset_data['end_date'],
            'tickers': tickers,
            'matrix': matrix_dict,
            'top_correlations': strong_correlations[:10],
            'data_points': len(returns)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def detect_regime(lookback: int = 60) -> Dict[str, Any]:
    """
    Detect current market regime based on cross-asset correlations.
    
    Regime types:
    - risk-on: Stocks up, bonds down, high stock-bond negative correlation
    - risk-off: Stocks down, bonds up, flight to safety
    - transition: Mixed signals, correlations breaking down
    - decorrelation: Low correlations across assets
    
    Args:
        lookback: Number of days to analyze
    
    Returns:
        Dict with regime classification and supporting signals
    """
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        from scipy import stats
        
        # Get data for major assets
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback + 30)
        
        tickers = list(MAJOR_ASSETS.keys())
        asset_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                if not hist.empty:
                    asset_data[ticker] = hist['Close']
            except:
                continue
        
        if len(asset_data) < 3:
            return {
                'error': 'Insufficient asset data',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Create DataFrame
        df = pd.DataFrame(asset_data)
        df = df.dropna()
        
        # Calculate returns
        returns = df.pct_change().dropna()
        
        # Recent performance (last lookback days)
        recent_returns = returns.tail(lookback)
        
        # Calculate rolling correlations
        spy_tlt_corr = recent_returns[['SPY', 'TLT']].corr().iloc[0, 1] if 'SPY' in recent_returns.columns and 'TLT' in recent_returns.columns else 0
        spy_gld_corr = recent_returns[['SPY', 'GLD']].corr().iloc[0, 1] if 'SPY' in recent_returns.columns and 'GLD' in recent_returns.columns else 0
        
        # Calculate cumulative returns for recent period
        cumulative_returns = {}
        for ticker in recent_returns.columns:
            cumulative_returns[ticker] = float((1 + recent_returns[ticker]).prod() - 1)
        
        # Calculate average absolute correlation (measure of market integration)
        corr_matrix = recent_returns.corr()
        avg_abs_corr = np.mean(np.abs(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]))
        
        # Regime detection logic
        signals = []
        regime = 'unknown'
        
        # Get SPY and TLT returns if available
        spy_return = cumulative_returns.get('SPY', 0)
        tlt_return = cumulative_returns.get('TLT', 0)
        
        # Risk-on: Stocks up, bonds down, negative SPY-TLT correlation
        if spy_return > 0.02 and tlt_return < -0.01 and spy_tlt_corr < -0.3:
            regime = 'risk-on'
            signals.append('Stocks outperforming bonds')
            signals.append('Negative stock-bond correlation')
        
        # Risk-off: Stocks down, bonds up, flight to safety
        elif spy_return < -0.02 and tlt_return > 0.01 and spy_tlt_corr < -0.2:
            regime = 'risk-off'
            signals.append('Flight to safety: bonds outperforming')
            signals.append('Stocks under pressure')
        
        # Decorrelation: Low average correlation
        elif avg_abs_corr < 0.3:
            regime = 'decorrelation'
            signals.append('Assets moving independently')
            signals.append('Low market integration')
        
        # Transition: Everything else
        else:
            regime = 'transition'
            signals.append('Mixed signals across assets')
            signals.append('Regime not clearly defined')
        
        # Calculate z-scores for correlation breaks
        # Historical correlation vs recent
        historical_corr = returns.corr()
        correlation_breaks = []
        
        for i, ticker1 in enumerate(corr_matrix.index):
            for j, ticker2 in enumerate(corr_matrix.columns):
                if i < j:
                    recent_corr = corr_matrix.loc[ticker1, ticker2]
                    hist_corr = historical_corr.loc[ticker1, ticker2]
                    
                    # Calculate z-score (simplified)
                    z_score = abs(recent_corr - hist_corr) * 10  # Scaled for visibility
                    
                    if z_score > 2:
                        correlation_breaks.append({
                            'pair': f"{ticker1}-{ticker2}",
                            'recent_corr': float(recent_corr),
                            'historical_corr': float(hist_corr),
                            'z_score': float(z_score),
                            'breaking': True
                        })
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'regime': regime,
            'confidence': 'high' if len(signals) >= 2 else 'medium',
            'lookback_days': lookback,
            'signals': signals,
            'key_correlations': {
                'SPY_TLT': float(spy_tlt_corr),
                'SPY_GLD': float(spy_gld_corr),
                'avg_abs_correlation': float(avg_abs_corr)
            },
            'cumulative_returns': cumulative_returns,
            'correlation_breaks': correlation_breaks,
            'assets_analyzed': list(asset_data.keys()),
            'data_points': len(recent_returns)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'detect':
            lookback = 60
            for i, arg in enumerate(sys.argv):
                if arg == '--lookback' and i + 1 < len(sys.argv):
                    lookback = int(sys.argv[i + 1])
            
            result = detect_regime(lookback)
            print(json.dumps(result, indent=2))
        
        elif sys.argv[1] == 'matrix':
            tickers = None
            period = '6mo'
            
            for i, arg in enumerate(sys.argv):
                if arg == '--tickers' and i + 1 < len(sys.argv):
                    tickers = sys.argv[i + 1].split(',')
                elif arg == '--period' and i + 1 < len(sys.argv):
                    period = sys.argv[i + 1]
            
            result = get_correlation_matrix(tickers, period)
            print(json.dumps(result, indent=2))
        
        elif sys.argv[1] == '--json':
            result = detect_regime()
            print(json.dumps(result))
        
        else:
            print("Unknown command. Use: detect [--lookback 60] or matrix [--tickers SPY,TLT]")
            sys.exit(1)
    else:
        # Default: detect regime
        result = detect_regime()
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
