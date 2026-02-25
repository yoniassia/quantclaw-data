#!/usr/bin/env python3
"""
Pairs Trading Signals Module
Phase 32: Cointegration detection, mean reversion opportunities, spread monitoring

Uses:
- yfinance for price data
- statsmodels for Engle-Granger and Johansen cointegration tests
- numpy/scipy for z-score calculations and half-life estimation
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.regression.linear_model import OLS
from scipy import stats
import sys


class PairsTradingAnalyzer:
    """Pairs trading analysis with cointegration detection and spread monitoring"""
    
    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        
    def fetch_price_data(self, symbols: List[str], period: str = "1y") -> Dict[str, pd.Series]:
        """Fetch historical price data for multiple symbols"""
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty:
                    data[symbol] = hist['Close']
            except Exception as e:
                print(f"Warning: Could not fetch {symbol}: {e}", file=sys.stderr)
        return data
    
    def engle_granger_test(self, y: pd.Series, x: pd.Series) -> Dict:
        """
        Engle-Granger two-step cointegration test
        Returns: test statistic, p-value, hedge ratio, half-life
        """
        # Align series
        df = pd.DataFrame({'y': y, 'x': x}).dropna()
        
        if len(df) < 30:
            return {
                'cointegrated': False,
                'error': 'Insufficient data points'
            }
        
        # Step 1: Run cointegration test
        score, pvalue, _ = coint(df['y'], df['x'])
        
        # Step 2: Estimate hedge ratio via OLS
        from statsmodels.tools import add_constant
        X = add_constant(df['x'])
        model = OLS(df['y'], X).fit()
        hedge_ratio = model.params.iloc[1]  # Coefficient on x, not intercept
        
        # Calculate spread
        spread = df['y'] - hedge_ratio * df['x']
        
        # Calculate half-life of mean reversion
        spread_lag = spread.shift(1).dropna()
        spread_ret = spread.diff().dropna()
        df_half_life = pd.DataFrame({'spread_lag': spread_lag, 'spread_ret': spread_ret}).dropna()
        
        if len(df_half_life) > 1:
            from statsmodels.tools import add_constant
            X_lag = add_constant(df_half_life['spread_lag'])
            half_life_model = OLS(df_half_life['spread_ret'], X_lag).fit()
            lambda_val = half_life_model.params.iloc[1]  # Coefficient on lagged spread
            half_life = -np.log(2) / lambda_val if lambda_val < 0 else np.inf
        else:
            half_life = np.inf
        
        # Calculate current z-score
        z_score = (spread.iloc[-1] - spread.mean()) / spread.std()
        
        return {
            'cointegrated': bool(pvalue < 0.05),
            'test_statistic': float(score),
            'p_value': float(pvalue),
            'hedge_ratio': float(hedge_ratio),
            'half_life_days': float(half_life) if half_life != np.inf else None,
            'current_z_score': float(z_score),
            'spread_mean': float(spread.mean()),
            'spread_std': float(spread.std()),
            'confidence': 'high' if pvalue < 0.01 else 'moderate' if pvalue < 0.05 else 'low'
        }
    
    def analyze_pair(self, symbol1: str, symbol2: str) -> Dict:
        """Comprehensive pair analysis"""
        # Fetch data
        data = self.fetch_price_data([symbol1, symbol2], period=f"{self.lookback_days}d")
        
        if symbol1 not in data or symbol2 not in data:
            return {
                'error': f'Could not fetch data for {symbol1} and/or {symbol2}'
            }
        
        # Run Engle-Granger test
        result = self.engle_granger_test(data[symbol1], data[symbol2])
        
        if 'error' in result:
            return result
        
        result['symbol1'] = symbol1
        result['symbol2'] = symbol2
        result['lookback_days'] = self.lookback_days
        result['analysis_date'] = datetime.now().isoformat()
        
        # Add trading signal
        z = result['current_z_score']
        if result['cointegrated']:
            if z > 2:
                result['signal'] = 'SHORT_SPREAD'
                result['signal_description'] = f'Short {symbol1}, Long {symbol2}'
            elif z < -2:
                result['signal'] = 'LONG_SPREAD'
                result['signal_description'] = f'Long {symbol1}, Short {symbol2}'
            elif abs(z) < 0.5:
                result['signal'] = 'CLOSE'
                result['signal_description'] = 'Close positions (mean reversion)'
            else:
                result['signal'] = 'HOLD'
                result['signal_description'] = 'Hold current positions'
        else:
            result['signal'] = 'NO_TRADE'
            result['signal_description'] = 'Pair not cointegrated'
        
        return result
    
    def scan_sector_pairs(self, sector: str, max_pairs: int = 10) -> List[Dict]:
        """
        Scan for cointegrated pairs within a sector
        Note: Using predefined sector tickers for common sectors
        """
        # Sector ticker mapping (simplified)
        sector_tickers = {
            'tech': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO'],
            'finance': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO'],
            'healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'LLY'],
            'consumer': ['AMZN', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW'],
            'beverage': ['KO', 'PEP', 'MNST', 'TAP', 'SAM', 'STZ', 'BUD'],
            'retail': ['WMT', 'TGT', 'COST', 'HD', 'LOW', 'TJX', 'DG', 'ROST']
        }
        
        tickers = sector_tickers.get(sector.lower())
        if not tickers:
            return [{'error': f'Unknown sector: {sector}. Available: {list(sector_tickers.keys())}'}]
        
        # Fetch all data once
        data = self.fetch_price_data(tickers)
        
        if len(data) < 2:
            return [{'error': 'Insufficient valid tickers for pair analysis'}]
        
        # Test all pairs
        pairs = []
        symbols = list(data.keys())
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                result = self.engle_granger_test(data[symbols[i]], data[symbols[j]])
                if result.get('cointegrated'):
                    result['symbol1'] = symbols[i]
                    result['symbol2'] = symbols[j]
                    result['sector'] = sector
                    pairs.append(result)
        
        # Sort by p-value (most significant first)
        pairs.sort(key=lambda x: x.get('p_value', 1.0))
        
        return pairs[:max_pairs]
    
    def monitor_spread(self, symbol1: str, symbol2: str, period: str = "30d") -> Dict:
        """
        Monitor spread dynamics over recent period
        Returns z-score history, mean reversion events, current position
        """
        data = self.fetch_price_data([symbol1, symbol2], period=period)
        
        if symbol1 not in data or symbol2 not in data:
            return {'error': f'Could not fetch data for {symbol1} and/or {symbol2}'}
        
        # Align data
        df = pd.DataFrame({'s1': data[symbol1], 's2': data[symbol2]}).dropna()
        
        # Calculate hedge ratio from full history
        from statsmodels.tools import add_constant
        full_data = self.fetch_price_data([symbol1, symbol2], period="1y")
        full_df = pd.DataFrame({'s1': full_data[symbol1], 's2': full_data[symbol2]}).dropna()
        X_full = add_constant(full_df['s2'])
        hedge_ratio = OLS(full_df['s1'], X_full).fit().params.iloc[1]
        
        # Calculate spread
        spread = df['s1'] - hedge_ratio * df['s2']
        
        # Calculate rolling z-score
        z_scores = (spread - spread.mean()) / spread.std()
        
        # Identify crossings
        crossings = []
        for i in range(1, len(z_scores)):
            prev_z = z_scores.iloc[i-1]
            curr_z = z_scores.iloc[i]
            
            # Upper threshold crossing
            if prev_z <= 2 and curr_z > 2:
                crossings.append({
                    'date': z_scores.index[i].strftime('%Y-%m-%d'),
                    'type': 'OVERBOUGHT',
                    'z_score': float(curr_z)
                })
            # Lower threshold crossing
            elif prev_z >= -2 and curr_z < -2:
                crossings.append({
                    'date': z_scores.index[i].strftime('%Y-%m-%d'),
                    'type': 'OVERSOLD',
                    'z_score': float(curr_z)
                })
            # Mean reversion
            elif abs(prev_z) > 0.5 and abs(curr_z) < 0.5:
                crossings.append({
                    'date': z_scores.index[i].strftime('%Y-%m-%d'),
                    'type': 'MEAN_REVERSION',
                    'z_score': float(curr_z)
                })
        
        return {
            'symbol1': symbol1,
            'symbol2': symbol2,
            'hedge_ratio': float(hedge_ratio),
            'current_z_score': float(z_scores.iloc[-1]),
            'mean_z_score': 0.0,
            'std_z_score': 1.0,
            'max_z_score': float(z_scores.max()),
            'min_z_score': float(z_scores.min()),
            'crossings': crossings,
            'z_score_history': [
                {
                    'date': idx.strftime('%Y-%m-%d'),
                    'z_score': float(val)
                }
                for idx, val in z_scores.tail(30).items()
            ]
        }


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pairs Trading Signals - Phase 32')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # pairs-scan command
    scan_parser = subparsers.add_parser('pairs-scan', help='Scan sector for cointegrated pairs')
    scan_parser.add_argument('sector', help='Sector to scan (tech, finance, energy, healthcare, consumer, beverage, retail)')
    scan_parser.add_argument('--limit', type=int, default=10, help='Max pairs to return')
    
    # cointegration command
    coint_parser = subparsers.add_parser('cointegration', help='Test cointegration between two symbols')
    coint_parser.add_argument('symbol1', help='First symbol')
    coint_parser.add_argument('symbol2', help='Second symbol')
    coint_parser.add_argument('--lookback', type=int, default=252, help='Lookback days')
    
    # spread-monitor command
    spread_parser = subparsers.add_parser('spread-monitor', help='Monitor spread dynamics')
    spread_parser.add_argument('symbol1', help='First symbol')
    spread_parser.add_argument('symbol2', help='Second symbol')
    spread_parser.add_argument('--period', default='30d', help='Monitoring period')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    analyzer = PairsTradingAnalyzer()
    
    if args.command == 'pairs-scan':
        results = analyzer.scan_sector_pairs(args.sector, max_pairs=args.limit)
        print(json.dumps(results, indent=2))
    
    elif args.command == 'cointegration':
        result = analyzer.analyze_pair(args.symbol1, args.symbol2)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'spread-monitor':
        result = analyzer.monitor_spread(args.symbol1, args.symbol2, period=args.period)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
