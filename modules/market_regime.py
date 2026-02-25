#!/usr/bin/env python3
"""
Market Regime Detection Module
Detects volatility clustering, correlation breakdowns, risk-on vs risk-off
Uses VIX, cross-asset correlations, credit spreads, and HMM/rule-based detection
"""

import sys
import argparse
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try importing FRED for financial conditions data
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("Warning: fredapi not installed. Run: pip install fredapi", file=sys.stderr)

# Try importing HMM
try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False


class MarketRegimeDetector:
    """Detect market regimes using multi-asset analysis"""
    
    def __init__(self, lookback_days=252):
        self.lookback_days = lookback_days
        self.fred = None
        if FRED_AVAILABLE:
            try:
                # Try to initialize FRED (may need API key)
                self.fred = Fred()
            except:
                pass
    
    def fetch_market_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch key market indicators"""
        tickers = {
            'VIX': '^VIX',      # Volatility
            'SPY': 'SPY',       # Equities
            'TLT': 'TLT',       # Treasuries
            'GLD': 'GLD',       # Gold
            'HYG': 'HYG',       # High Yield Credit
            'DXY': 'DX-Y.NYB',  # Dollar Index
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days + 30)
        
        data = {}
        for name, ticker in tickers.items():
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not df.empty:
                    # Ensure we get a Series
                    if 'Close' in df.columns:
                        data[name] = df['Close'].squeeze()
                    else:
                        # Multi-index columns case
                        close_data = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df['Close']
                        data[name] = close_data.squeeze() if hasattr(close_data, 'squeeze') else close_data
                else:
                    print(f"Warning: No data for {name} ({ticker})", file=sys.stderr)
            except Exception as e:
                print(f"Error fetching {name}: {e}", file=sys.stderr)
        
        return data
    
    def calculate_correlations(self, data: Dict[str, pd.DataFrame], window=20) -> pd.DataFrame:
        """Calculate rolling correlations between asset classes"""
        # Convert dict of Series to DataFrame
        df_dict = {}
        for name, series in data.items():
            if isinstance(series, pd.Series):
                df_dict[name] = series
        
        if not df_dict:
            return pd.DataFrame()
        
        df = pd.DataFrame(df_dict)
        
        # Calculate returns
        returns = df.pct_change().dropna()
        
        # Rolling correlations
        correlations = {}
        pairs = [
            ('SPY', 'TLT', 'Stocks-Bonds'),
            ('SPY', 'GLD', 'Stocks-Gold'),
            ('SPY', 'HYG', 'Stocks-Credit'),
            ('VIX', 'SPY', 'VIX-Stocks'),
        ]
        
        for asset1, asset2, label in pairs:
            if asset1 in returns.columns and asset2 in returns.columns:
                corr = returns[asset1].rolling(window).corr(returns[asset2])
                correlations[label] = corr
        
        return pd.DataFrame(correlations)
    
    def calculate_vix_regime(self, vix_data: pd.Series) -> Tuple[str, float]:
        """Classify regime based on VIX levels"""
        current_vix = vix_data.iloc[-1]
        
        if current_vix < 15:
            regime = "Low Volatility (Complacency)"
            score = 0.2
        elif current_vix < 20:
            regime = "Normal Volatility"
            score = 0.4
        elif current_vix < 30:
            regime = "Elevated Volatility (Caution)"
            score = 0.6
        elif current_vix < 40:
            regime = "High Volatility (Fear)"
            score = 0.8
        else:
            regime = "Crisis Volatility (Panic)"
            score = 1.0
        
        return regime, score
    
    def calculate_credit_spread(self, hyg_data: pd.Series, tlt_data: pd.Series) -> float:
        """Estimate credit spread widening"""
        # HYG yield vs TLT yield proxy
        hyg_returns = hyg_data.pct_change(20).iloc[-1]
        tlt_returns = tlt_data.pct_change(20).iloc[-1]
        
        # Widening spread = HYG underperforming TLT
        spread_signal = tlt_returns - hyg_returns
        return spread_signal
    
    def detect_regime_hmm(self, data: Dict[str, pd.DataFrame], n_states=4) -> pd.DataFrame:
        """Use Hidden Markov Model for regime detection"""
        if not HMM_AVAILABLE:
            return None
        
        df = pd.DataFrame(data)
        returns = df.pct_change().dropna()
        
        # Use VIX and SPY returns as features
        features = returns[['VIX', 'SPY']].dropna()
        
        if len(features) < 50:
            return None
        
        try:
            # Fit HMM
            model = hmm.GaussianHMM(n_components=n_states, covariance_type="full", 
                                    n_iter=1000, random_state=42)
            model.fit(features.values)
            
            # Predict states
            states = model.predict(features.values)
            
            # Map states to regimes based on mean volatility
            state_means = []
            for state in range(n_states):
                state_mask = states == state
                mean_vix = features[state_mask]['VIX'].mean()
                state_means.append((state, mean_vix))
            
            # Sort by VIX level
            state_means.sort(key=lambda x: x[1])
            regime_map = {
                state_means[0][0]: "Risk-On",
                state_means[1][0]: "Normal",
                state_means[2][0]: "Risk-Off",
                state_means[3][0]: "Crisis"
            }
            
            regime_labels = [regime_map[s] for s in states]
            
            result = pd.DataFrame({
                'Date': features.index,
                'State': states,
                'Regime': regime_labels
            })
            result.set_index('Date', inplace=True)
            
            return result
        except Exception as e:
            print(f"HMM detection failed: {e}", file=sys.stderr)
            return None
    
    def detect_regime_rules(self, data: Dict[str, pd.DataFrame]) -> Tuple[str, Dict]:
        """Rule-based regime classification"""
        vix = data.get('VIX')
        spy = data.get('SPY')
        tlt = data.get('TLT')
        hyg = data.get('HYG')
        gld = data.get('GLD')
        
        if vix is None or spy is None:
            return "Unknown", {}
        
        # Calculate metrics (handle both Series and DataFrame)
        def get_scalar(val):
            if isinstance(val, (pd.Series, pd.DataFrame)):
                return float(val.iloc[-1] if isinstance(val, pd.Series) else val.values.flatten()[-1])
            return float(val)
        
        current_vix = get_scalar(vix.iloc[-1])
        vix_20d_avg = get_scalar(vix.tail(20).mean())
        spy_ret_20d = get_scalar(spy.pct_change(20).iloc[-1])
        
        # Correlation breakdown detection
        correlations = self.calculate_correlations(data, window=20)
        
        signals = {
            'vix_level': current_vix,
            'vix_vs_avg': current_vix / vix_20d_avg if vix_20d_avg > 0 else 1.0,
            'spy_return_20d': spy_ret_20d,
        }
        
        # Add correlation signals
        if 'Stocks-Bonds' in correlations.columns and len(correlations) > 0:
            corr_val = correlations['Stocks-Bonds'].iloc[-1]
            if not pd.isna(corr_val):
                signals['stocks_bonds_corr'] = float(corr_val)
        if 'VIX-Stocks' in correlations.columns and len(correlations) > 0:
            corr_val = correlations['VIX-Stocks'].iloc[-1]
            if not pd.isna(corr_val):
                signals['vix_stocks_corr'] = float(corr_val)
        
        # Credit spread signal
        if hyg is not None and tlt is not None:
            signals['credit_spread_signal'] = self.calculate_credit_spread(hyg, tlt)
        
        # Regime classification logic
        score = 0
        
        # VIX signals
        if current_vix > 40:
            score += 3  # Crisis
        elif current_vix > 30:
            score += 2  # High stress
        elif current_vix > 20:
            score += 1  # Moderate stress
        
        # Market return
        if spy_ret_20d < -0.10:
            score += 2
        elif spy_ret_20d < -0.05:
            score += 1
        elif spy_ret_20d > 0.05:
            score -= 1
        
        # Correlation breakdown
        if 'stocks_bonds_corr' in signals:
            if signals['stocks_bonds_corr'] > 0.3:  # Both falling (crisis)
                score += 1
        
        # Classify regime
        if score >= 4:
            regime = "Crisis"
        elif score >= 2:
            regime = "Risk-Off"
        elif score >= 1:
            regime = "Transition"
        else:
            regime = "Risk-On"
        
        return regime, signals
    
    def get_regime_timeline(self, data: Dict[str, pd.DataFrame], window=20) -> pd.DataFrame:
        """Generate regime timeline"""
        vix = data.get('VIX')
        spy = data.get('SPY')
        
        if vix is None or spy is None:
            return pd.DataFrame()
        
        df = pd.DataFrame({'VIX': vix, 'SPY': spy})
        df['SPY_ret_20d'] = df['SPY'].pct_change(20)
        df['VIX_20d_avg'] = df['VIX'].rolling(20).mean()
        
        regimes = []
        for idx in range(len(df)):
            if idx < 20:
                regimes.append("Insufficient Data")
                continue
            
            vix_val = df['VIX'].iloc[idx]
            spy_ret = df['SPY_ret_20d'].iloc[idx]
            
            score = 0
            if vix_val > 40:
                score += 3
            elif vix_val > 30:
                score += 2
            elif vix_val > 20:
                score += 1
            
            if spy_ret < -0.10:
                score += 2
            elif spy_ret < -0.05:
                score += 1
            elif spy_ret > 0.05:
                score -= 1
            
            if score >= 4:
                regime = "Crisis"
            elif score >= 2:
                regime = "Risk-Off"
            elif score >= 1:
                regime = "Transition"
            else:
                regime = "Risk-On"
            
            regimes.append(regime)
        
        df['Regime'] = regimes
        return df[['VIX', 'SPY', 'SPY_ret_20d', 'Regime']].tail(60)
    
    def print_current_regime(self):
        """Print current market regime classification"""
        print("=" * 60)
        print("MARKET REGIME DETECTION")
        print("=" * 60)
        
        data = self.fetch_market_data()
        
        if not data:
            print("Error: Unable to fetch market data")
            return
        
        regime, signals = self.detect_regime_rules(data)
        
        print(f"\n🎯 Current Regime: {regime}")
        print(f"\nKey Signals:")
        print(f"  VIX Level: {signals.get('vix_level', 'N/A'):.2f}")
        print(f"  VIX vs 20D Avg: {signals.get('vix_vs_avg', 'N/A'):.2f}x")
        print(f"  SPY 20D Return: {signals.get('spy_return_20d', 0) * 100:.2f}%")
        
        if 'stocks_bonds_corr' in signals:
            print(f"  Stocks-Bonds Correlation: {signals['stocks_bonds_corr']:.2f}")
        if 'vix_stocks_corr' in signals:
            print(f"  VIX-Stocks Correlation: {signals['vix_stocks_corr']:.2f}")
        if 'credit_spread_signal' in signals:
            spread_val = signals['credit_spread_signal']
            print(f"  Credit Spread Signal: {spread_val:.4f} {'(Widening)' if spread_val > 0 else '(Tightening)'}")
        
        # Regime interpretation
        print(f"\n📊 Interpretation:")
        if regime == "Crisis":
            print("  ⚠️  Crisis mode: High volatility, significant drawdowns, flight to quality")
        elif regime == "Risk-Off":
            print("  ⚠️  Risk-off: Elevated volatility, defensive positioning recommended")
        elif regime == "Transition":
            print("  ⚠️  Transitioning: Mixed signals, uncertainty elevated")
        else:
            print("  ✅ Risk-on: Low volatility, bullish sentiment, risk appetite strong")
        
        print("\n" + "=" * 60)
    
    def print_regime_history(self):
        """Print regime timeline"""
        print("=" * 60)
        print("MARKET REGIME HISTORY (Last 60 Days)")
        print("=" * 60)
        
        data = self.fetch_market_data()
        timeline = self.get_regime_timeline(data)
        
        if timeline.empty:
            print("Error: Unable to generate timeline")
            return
        
        print(f"\n{'Date':<12} {'VIX':<8} {'SPY':<10} {'20D Ret':<10} {'Regime':<15}")
        print("-" * 60)
        
        for idx, row in timeline.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            vix = row['VIX']
            spy = row['SPY']
            ret = row['SPY_ret_20d'] * 100
            regime = row['Regime']
            
            print(f"{date_str:<12} {vix:<8.2f} {spy:<10.2f} {ret:<10.2f}% {regime:<15}")
        
        # Summary statistics
        regime_counts = timeline['Regime'].value_counts()
        print("\n" + "=" * 60)
        print("REGIME DISTRIBUTION (Last 60 Days):")
        for regime, count in regime_counts.items():
            pct = count / len(timeline) * 100
            print(f"  {regime}: {count} days ({pct:.1f}%)")
        
        print("=" * 60)
    
    def print_risk_dashboard(self):
        """Print comprehensive risk dashboard"""
        print("=" * 70)
        print("RISK-ON / RISK-OFF DASHBOARD")
        print("=" * 70)
        
        data = self.fetch_market_data()
        regime, signals = self.detect_regime_rules(data)
        correlations = self.calculate_correlations(data, window=20)
        
        # VIX analysis
        vix = data.get('VIX')
        if vix is not None:
            vix_regime, vix_score = self.calculate_vix_regime(vix)
            print(f"\n📊 VOLATILITY ASSESSMENT:")
            print(f"  Current VIX: {vix.iloc[-1]:.2f}")
            print(f"  VIX Regime: {vix_regime}")
            print(f"  Risk Score: {vix_score * 100:.0f}/100")
            print(f"  30D High: {vix.tail(30).max():.2f}")
            print(f"  30D Low: {vix.tail(30).min():.2f}")
        
        # Cross-asset performance
        print(f"\n📈 ASSET CLASS PERFORMANCE (20D):")
        for name, prices in data.items():
            if len(prices) > 20:
                ret = prices.pct_change(20).iloc[-1] * 100
                indicator = "🟢" if ret > 0 else "🔴"
                print(f"  {indicator} {name:<6}: {ret:>6.2f}%")
        
        # Correlation analysis
        print(f"\n🔗 CROSS-ASSET CORRELATIONS (20D Rolling):")
        if not correlations.empty:
            latest_corr = correlations.iloc[-1]
            for pair, corr in latest_corr.items():
                if not pd.isna(corr):
                    print(f"  {pair:<20}: {corr:>6.2f}")
        
        # Overall regime
        print(f"\n🎯 OVERALL MARKET REGIME: {regime}")
        
        if regime == "Risk-On":
            print("\n✅ RISK-ON INDICATORS:")
            print("  • Low volatility environment")
            print("  • Positive equity momentum")
            print("  • Credit spreads tight")
            print("  • Normal correlations")
        elif regime == "Risk-Off":
            print("\n⚠️  RISK-OFF INDICATORS:")
            print("  • Elevated volatility")
            print("  • Equity weakness")
            print("  • Credit spread widening")
            print("  • Flight to quality")
        elif regime == "Transition":
            print("\n⚠️  TRANSITIONING:")
            print("  • Mixed signals")
            print("  • Correlation breakdown possible")
            print("  • Increased uncertainty")
        else:  # Crisis
            print("\n🚨 CRISIS MODE:")
            print("  • Extreme volatility")
            print("  • Severe drawdowns")
            print("  • Correlations → 1")
            print("  • Liquidity concerns")
        
        print("\n" + "=" * 70)
    
    def print_correlation_regime(self):
        """Print correlation regime analysis"""
        print("=" * 70)
        print("CORRELATION REGIME ANALYSIS")
        print("=" * 70)
        
        data = self.fetch_market_data()
        
        # Calculate correlations at different windows
        windows = [5, 20, 60]
        
        for window in windows:
            correlations = self.calculate_correlations(data, window=window)
            
            print(f"\n📊 {window}-Day Rolling Correlations:")
            if not correlations.empty and len(correlations) > 0:
                latest = correlations.iloc[-1]
                
                for pair, corr in latest.items():
                    if not pd.isna(corr):
                        # Correlation breakdown detection
                        if abs(corr) < 0.2:
                            status = "✅ Normal (Low)"
                        elif abs(corr) > 0.7:
                            status = "⚠️  High (Breakdown?)"
                        else:
                            status = "➖ Moderate"
                        
                        print(f"  {pair:<20}: {corr:>6.2f}  {status}")
        
        # Detect correlation regime shifts
        print(f"\n🔍 CORRELATION REGIME SHIFTS:")
        correlations_20d = self.calculate_correlations(data, window=20)
        
        if 'Stocks-Bonds' in correlations_20d.columns:
            recent_corr = correlations_20d['Stocks-Bonds'].tail(20)
            if recent_corr.std() > 0.3:
                print("  ⚠️  Stocks-Bonds correlation UNSTABLE (high variance)")
            else:
                print("  ✅ Stocks-Bonds correlation STABLE")
        
        if 'VIX-Stocks' in correlations_20d.columns:
            vix_stock_corr = correlations_20d['VIX-Stocks'].iloc[-1]
            if vix_stock_corr > -0.5:
                print("  ⚠️  VIX-Stocks correlation BREAKDOWN (should be negative)")
            else:
                print("  ✅ VIX-Stocks correlation NORMAL (negative)")
        
        # Crisis signal
        print(f"\n🚨 CRISIS CORRELATION SIGNALS:")
        crisis_signals = []
        
        if 'Stocks-Bonds' in correlations_20d.columns:
            sb_corr = correlations_20d['Stocks-Bonds'].iloc[-1]
            if sb_corr > 0.5:
                crisis_signals.append("Stocks-Bonds positive correlation (both falling)")
        
        if 'Stocks-Gold' in correlations_20d.columns:
            sg_corr = correlations_20d['Stocks-Gold'].iloc[-1]
            if sg_corr < -0.6:
                crisis_signals.append("Strong negative Stocks-Gold correlation (flight to safety)")
        
        if crisis_signals:
            for signal in crisis_signals:
                print(f"  ⚠️  {signal}")
        else:
            print("  ✅ No crisis correlation patterns detected")
        
        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Market Regime Detection')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('--lookback', type=int, default=252, help='Lookback period in days')
    
    args = parser.parse_args()
    
    detector = MarketRegimeDetector(lookback_days=args.lookback)
    
    if args.command == 'market-regime':
        detector.print_current_regime()
    elif args.command == 'regime-history':
        detector.print_regime_history()
    elif args.command == 'risk-dashboard':
        detector.print_risk_dashboard()
    elif args.command == 'correlation-regime':
        detector.print_correlation_regime()
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        print("Available commands: market-regime, regime-history, risk-dashboard, correlation-regime")
        sys.exit(1)


if __name__ == '__main__':
    main()
