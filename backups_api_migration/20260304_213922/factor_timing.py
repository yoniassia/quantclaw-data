#!/usr/bin/env python3
"""
FACTOR TIMING MODEL - Phase 73
Regime detection for when factors work, adaptive factor rotation
Uses: Ken French Data Library, FRED (macro indicators), Yahoo Finance
"""

import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from fredapi import Fred
except ImportError as e:
    print(f"Error: Missing required package: {e}", file=sys.stderr)
    print("Install with: pip install yfinance pandas numpy fredapi pandas_datareader", file=sys.stderr)
    sys.exit(1)


# Factor ETF proxies
FACTOR_ETFS = {
    'value': 'VTV',      # Vanguard Value ETF
    'momentum': 'MTUM',  # iShares MSCI USA Momentum Factor ETF
    'quality': 'QUAL',   # iShares MSCI USA Quality Factor ETF
    'size': 'VB',        # Vanguard Small-Cap ETF
    'low_vol': 'USMV',   # iShares MSCI USA Min Vol Factor ETF
    'market': 'SPY'      # S&P 500 as benchmark
}

# FRED API key (using demo key, users should replace with their own)
FRED_API_KEY = "demo"  # Replace with real key from https://fred.stlouisfed.org/docs/api/api_key.html

# Economic indicators for regime detection
MACRO_INDICATORS = {
    'unemployment': 'UNRATE',           # Unemployment rate
    'inflation': 'CPIAUCSL',            # CPI
    'gdp_growth': 'GDP',                # GDP
    'yield_curve': ['DGS10', 'DGS2'],  # 10Y - 2Y Treasury spread
    'vix': '^VIX',                      # Market volatility (Yahoo)
    'credit_spread': 'BAA10Y'           # BBB-Treasury spread
}


class FactorRegimeDetector:
    """Detect market regimes and optimal factor exposures"""
    
    def __init__(self):
        self.fred = None
        try:
            self.fred = Fred(api_key=FRED_API_KEY)
        except:
            pass  # Will use fallback data if FRED unavailable
    
    def get_factor_returns(self, period: str = '1y') -> pd.DataFrame:
        """Fetch factor ETF returns"""
        end_date = datetime.now()
        
        # Parse period
        if period.endswith('y'):
            days = int(period[:-1]) * 365
        elif period.endswith('m'):
            days = int(period[:-1]) * 30
        elif period.endswith('d'):
            days = int(period[:-1])
        else:
            days = 365  # Default 1 year
        
        start_date = end_date - timedelta(days=days)
        
        factor_data = {}
        for factor_name, ticker in FACTOR_ETFS.items():
            try:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not data.empty:
                    returns = data['Adj Close'].pct_change()
                    factor_data[factor_name] = {
                        'ticker': ticker,
                        'total_return': ((1 + returns).prod() - 1) * 100,
                        'annualized_return': (((1 + returns.mean()) ** 252) - 1) * 100,
                        'volatility': returns.std() * np.sqrt(252) * 100,
                        'sharpe': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0,
                        'current_price': data['Adj Close'].iloc[-1],
                        'max_drawdown': self._calculate_max_drawdown(data['Adj Close'])
                    }
            except Exception as e:
                print(f"Warning: Could not fetch {ticker}: {e}", file=sys.stderr)
        
        return pd.DataFrame(factor_data).T
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown percentage"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min() * 100
    
    def get_macro_regime(self) -> Dict:
        """Detect current macroeconomic regime"""
        regime = {
            'timestamp': datetime.now().isoformat(),
            'regime': 'Unknown',
            'confidence': 0.0,
            'indicators': {},
            'signals': []
        }
        
        # Fetch VIX for volatility regime
        try:
            vix_data = yf.download('^VIX', period='5d', progress=False)
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                regime['indicators']['vix'] = float(current_vix)
                
                if current_vix > 30:
                    regime['signals'].append('HIGH_VOLATILITY')
                elif current_vix < 15:
                    regime['signals'].append('LOW_VOLATILITY')
        except:
            pass
        
        # Fetch yield curve data
        if self.fred:
            try:
                ten_year = self.fred.get_series('DGS10', observation_start=datetime.now() - timedelta(days=7))
                two_year = self.fred.get_series('DGS2', observation_start=datetime.now() - timedelta(days=7))
                
                if not ten_year.empty and not two_year.empty:
                    spread = ten_year.iloc[-1] - two_year.iloc[-1]
                    regime['indicators']['yield_curve_spread'] = float(spread)
                    
                    if spread < 0:
                        regime['signals'].append('INVERTED_YIELD_CURVE')
                    elif spread > 2:
                        regime['signals'].append('STEEP_YIELD_CURVE')
                
                # Unemployment rate
                unemployment = self.fred.get_series('UNRATE', observation_start=datetime.now() - timedelta(days=60))
                if not unemployment.empty:
                    current_unemployment = unemployment.iloc[-1]
                    regime['indicators']['unemployment'] = float(current_unemployment)
                    
                    if len(unemployment) > 1:
                        change = current_unemployment - unemployment.iloc[-2]
                        if change > 0.3:
                            regime['signals'].append('RISING_UNEMPLOYMENT')
            except:
                pass
        
        # Classify regime
        regime['regime'] = self._classify_regime(regime['signals'], regime['indicators'])
        regime['confidence'] = self._calculate_confidence(regime['signals'])
        
        return regime
    
    def _classify_regime(self, signals: List[str], indicators: Dict) -> str:
        """Classify market regime based on signals"""
        if 'HIGH_VOLATILITY' in signals or 'INVERTED_YIELD_CURVE' in signals:
            return 'RISK_OFF'
        elif 'LOW_VOLATILITY' in signals and 'STEEP_YIELD_CURVE' in signals:
            return 'RISK_ON'
        elif 'HIGH_VOLATILITY' in signals and 'RISING_UNEMPLOYMENT' in signals:
            return 'RECESSION'
        elif indicators.get('vix', 20) < 20:
            return 'RISK_ON'
        else:
            return 'NEUTRAL'
    
    def _calculate_confidence(self, signals: List[str]) -> float:
        """Calculate confidence in regime classification"""
        if len(signals) == 0:
            return 0.3
        elif len(signals) >= 3:
            return 0.9
        elif len(signals) == 2:
            return 0.7
        else:
            return 0.5
    
    def get_optimal_factors(self, regime: str) -> List[Dict]:
        """Recommend factors based on regime"""
        recommendations = {
            'RISK_ON': [
                {'factor': 'momentum', 'weight': 0.35, 'reason': 'Momentum performs well in risk-on markets'},
                {'factor': 'quality', 'weight': 0.30, 'reason': 'Quality provides stability with upside'},
                {'factor': 'size', 'weight': 0.20, 'reason': 'Small caps outperform in expansions'},
                {'factor': 'value', 'weight': 0.15, 'reason': 'Modest value exposure'}
            ],
            'RISK_OFF': [
                {'factor': 'quality', 'weight': 0.40, 'reason': 'Quality defensiveness in downturns'},
                {'factor': 'low_vol', 'weight': 0.35, 'reason': 'Low volatility protection'},
                {'factor': 'value', 'weight': 0.15, 'reason': 'Value holds up in defensive rotation'},
                {'factor': 'momentum', 'weight': 0.10, 'reason': 'Reduced momentum exposure'}
            ],
            'RECESSION': [
                {'factor': 'low_vol', 'weight': 0.45, 'reason': 'Maximum defensive positioning'},
                {'factor': 'quality', 'weight': 0.40, 'reason': 'High-quality balance sheets'},
                {'factor': 'value', 'weight': 0.10, 'reason': 'Minimal value exposure'},
                {'factor': 'momentum', 'weight': 0.05, 'reason': 'Minimal momentum exposure'}
            ],
            'NEUTRAL': [
                {'factor': 'quality', 'weight': 0.30, 'reason': 'Balanced core position'},
                {'factor': 'value', 'weight': 0.25, 'reason': 'Balanced value exposure'},
                {'factor': 'momentum', 'weight': 0.25, 'reason': 'Balanced momentum exposure'},
                {'factor': 'low_vol', 'weight': 0.20, 'reason': 'Defensive buffer'}
            ]
        }
        
        return recommendations.get(regime, recommendations['NEUTRAL'])
    
    def generate_rotation_signals(self) -> Dict:
        """Generate adaptive factor rotation signals"""
        # Get current regime
        regime_info = self.get_macro_regime()
        regime = regime_info['regime']
        
        # Get factor performance
        factor_returns = self.get_factor_returns(period='3m')
        
        # Get optimal allocation
        optimal_factors = self.get_optimal_factors(regime)
        
        # Generate rotation signals
        signals = []
        for rec in optimal_factors:
            factor = rec['factor']
            if factor in factor_returns.index:
                current_performance = factor_returns.loc[factor, 'total_return']
                sharpe = factor_returns.loc[factor, 'sharpe']
                
                signal = {
                    'factor': factor,
                    'ticker': FACTOR_ETFS[factor],
                    'action': 'OVERWEIGHT' if rec['weight'] > 0.25 else 'NEUTRAL',
                    'target_weight': rec['weight'],
                    'reason': rec['reason'],
                    'recent_return_3m': round(current_performance, 2),
                    'sharpe_ratio': round(sharpe, 2)
                }
                
                # Determine if we should rotate
                if rec['weight'] > 0.30 and sharpe > 1.0:
                    signal['action'] = 'STRONG_BUY'
                elif rec['weight'] < 0.15:
                    signal['action'] = 'UNDERWEIGHT'
                
                signals.append(signal)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'regime': regime,
            'confidence': regime_info['confidence'],
            'signals': signals,
            'macro_indicators': regime_info['indicators']
        }
    
    def get_regime_history(self, days: int = 60) -> List[Dict]:
        """Calculate historical regime timeline"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Sample regime at weekly intervals
        timeline = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simplified historical regime detection using VIX
            try:
                vix_data = yf.download('^VIX', start=current_date - timedelta(days=7), 
                                       end=current_date, progress=False)
                if not vix_data.empty:
                    avg_vix = vix_data['Close'].mean()
                    
                    if avg_vix > 30:
                        regime = 'RISK_OFF'
                    elif avg_vix < 15:
                        regime = 'RISK_ON'
                    else:
                        regime = 'NEUTRAL'
                    
                    timeline.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'regime': regime,
                        'vix': round(float(avg_vix), 2)
                    })
            except:
                pass
            
            current_date += timedelta(days=7)
        
        return timeline


def cmd_factor_timing(args):
    """Display current factor regime"""
    detector = FactorRegimeDetector()
    
    print("=" * 80)
    print("FACTOR TIMING MODEL - CURRENT REGIME")
    print("=" * 80)
    
    regime_info = detector.get_macro_regime()
    
    print(f"\n📊 CURRENT REGIME: {regime_info['regime']}")
    print(f"Confidence: {regime_info['confidence']:.0%}")
    print(f"Timestamp: {regime_info['timestamp']}")
    
    if regime_info['indicators']:
        print("\n📈 Macro Indicators:")
        for key, value in regime_info['indicators'].items():
            print(f"  • {key.replace('_', ' ').title()}: {value:.2f}")
    
    if regime_info['signals']:
        print("\n🚨 Active Signals:")
        for signal in regime_info['signals']:
            print(f"  • {signal.replace('_', ' ').title()}")
    
    # Show optimal factors for this regime
    optimal = detector.get_optimal_factors(regime_info['regime'])
    print(f"\n✅ RECOMMENDED FACTOR ALLOCATION ({regime_info['regime']}):")
    print(f"{'Factor':<12} {'Weight':<10} {'Reason'}")
    print("-" * 70)
    
    for rec in optimal:
        factor = rec['factor'].replace('_', ' ').title()
        weight = f"{rec['weight']:.0%}"
        reason = rec['reason']
        print(f"{factor:<12} {weight:<10} {reason}")
    
    print("\n" + "=" * 80)


def cmd_factor_rotation(args):
    """Display rotation signals"""
    detector = FactorRegimeDetector()
    
    print("=" * 80)
    print("ADAPTIVE FACTOR ROTATION SIGNALS")
    print("=" * 80)
    
    rotation = detector.generate_rotation_signals()
    
    print(f"\n📊 Current Regime: {rotation['regime']} (Confidence: {rotation['confidence']:.0%})")
    print(f"Timestamp: {rotation['timestamp']}")
    
    if rotation['macro_indicators']:
        print("\n📈 Macro Context:")
        for key, value in rotation['macro_indicators'].items():
            print(f"  • {key.replace('_', ' ').title()}: {value:.2f}")
    
    print("\n🔄 ROTATION SIGNALS:")
    print(f"{'Factor':<12} {'Ticker':<8} {'Action':<15} {'Target %':<10} {'3M Ret%':<10} {'Sharpe':<8} {'Reason'}")
    print("-" * 110)
    
    for signal in rotation['signals']:
        factor = signal['factor'].replace('_', ' ').title()
        ticker = signal['ticker']
        action = signal['action']
        target = f"{signal['target_weight']:.0%}"
        ret_3m = f"{signal['recent_return_3m']:.1f}%"
        sharpe = f"{signal['sharpe_ratio']:.2f}"
        reason = signal['reason'][:40]
        
        # Color code actions
        action_display = action
        if action == 'STRONG_BUY':
            action_display = f"🟢 {action}"
        elif action == 'OVERWEIGHT':
            action_display = f"🔵 {action}"
        elif action == 'UNDERWEIGHT':
            action_display = f"🟡 {action}"
        
        print(f"{factor:<12} {ticker:<8} {action_display:<15} {target:<10} {ret_3m:<10} {sharpe:<8} {reason}")
    
    print("\n" + "=" * 80)


def cmd_factor_performance(args):
    """Display factor performance over period"""
    detector = FactorRegimeDetector()
    
    period = args.period if hasattr(args, 'period') and args.period else '1y'
    
    print("=" * 80)
    print(f"FACTOR PERFORMANCE - {period.upper()}")
    print("=" * 80)
    
    factor_returns = detector.get_factor_returns(period=period)
    
    if factor_returns.empty:
        print("No factor data available")
        return
    
    # Sort by total return
    factor_returns = factor_returns.sort_values('total_return', ascending=False)
    
    print(f"\n{'Factor':<12} {'Ticker':<8} {'Total Ret%':<12} {'Ann. Ret%':<12} {'Vol%':<10} {'Sharpe':<10} {'Max DD%'}")
    print("-" * 90)
    
    for factor in factor_returns.index:
        data = factor_returns.loc[factor]
        factor_name = factor.replace('_', ' ').title()
        ticker = data['ticker']
        total_ret = f"{data['total_return']:.2f}%"
        ann_ret = f"{data['annualized_return']:.2f}%"
        vol = f"{data['volatility']:.2f}%"
        sharpe = f"{data['sharpe']:.2f}"
        max_dd = f"{data['max_drawdown']:.2f}%"
        
        print(f"{factor_name:<12} {ticker:<8} {total_ret:<12} {ann_ret:<12} {vol:<10} {sharpe:<10} {max_dd}")
    
    print("\n📊 Best Factor: " + factor_returns.index[0].replace('_', ' ').title())
    print(f"   Return: {factor_returns.iloc[0]['total_return']:.2f}% | Sharpe: {factor_returns.iloc[0]['sharpe']:.2f}")
    
    print("\n" + "=" * 80)


def cmd_factor_regime_history(args):
    """Display regime timeline"""
    detector = FactorRegimeDetector()
    
    days = args.days if hasattr(args, 'days') and args.days else 60
    
    print("=" * 80)
    print(f"REGIME HISTORY - LAST {days} DAYS")
    print("=" * 80)
    
    timeline = detector.get_regime_history(days=days)
    
    if not timeline:
        print("No historical regime data available")
        return
    
    print(f"\n{'Date':<12} {'Regime':<15} {'VIX':<8}")
    print("-" * 40)
    
    regime_counts = {'RISK_ON': 0, 'RISK_OFF': 0, 'NEUTRAL': 0}
    
    for entry in timeline:
        date = entry['date']
        regime = entry['regime']
        vix = f"{entry['vix']:.1f}"
        
        regime_counts[regime] += 1
        
        # Visual indicator
        if regime == 'RISK_ON':
            regime_display = "🟢 RISK_ON"
        elif regime == 'RISK_OFF':
            regime_display = "🔴 RISK_OFF"
        else:
            regime_display = "🟡 NEUTRAL"
        
        print(f"{date:<12} {regime_display:<15} {vix:<8}")
    
    total = sum(regime_counts.values())
    if total > 0:
        print("\n📊 REGIME DISTRIBUTION:")
        for regime, count in regime_counts.items():
            pct = (count / total) * 100
            print(f"   {regime}: {pct:.1f}% ({count} weeks)")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Factor Timing Model')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('period', nargs='?', default='1y', help='Time period (e.g., 1y, 6m, 3m)')
    parser.add_argument('--days', type=int, default=60, help='Number of days for regime history')
    
    args = parser.parse_args()
    
    if not args.command:
        print("Usage: python factor_timing.py <command>", file=sys.stderr)
        print("Commands: factor-timing, factor-rotation, factor-performance, factor-regime-history", file=sys.stderr)
        return 1
    
    commands = {
        'factor-timing': cmd_factor_timing,
        'factor-rotation': cmd_factor_rotation,
        'factor-performance': cmd_factor_performance,
        'factor-regime-history': cmd_factor_regime_history
    }
    
    if args.command in commands:
        try:
            commands[args.command](args)
            return 0
        except Exception as e:
            print(f"Error executing {args.command}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
