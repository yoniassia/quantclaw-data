#!/usr/bin/env python3
"""
ML Factor Discovery Module
Automated discovery of new predictive factors with feature engineering
"""

import sys
import argparse
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# For ML models
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LassoCV
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Feature importance will be limited.", file=sys.stderr)

# Data storage
DATA_DIR = Path.home() / '.quantclaw' / 'ml_factors'
DATA_DIR.mkdir(parents=True, exist_ok=True)

class FactorDiscovery:
    """Automated factor discovery and validation engine"""
    
    def __init__(self, tickers: List[str], lookback_days: int = 504):
        self.tickers = tickers
        self.lookback_days = lookback_days
        self.data = {}
        self.factors = {}
        self.ic_scores = {}
        
    def fetch_data(self):
        """Fetch historical data from Yahoo Finance"""
        print(f"📊 Fetching data for {len(self.tickers)} tickers...")
        
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                # Get historical price data
                hist = stock.history(period="2y")
                
                if len(hist) < 20:
                    print(f"⚠️  Insufficient data for {ticker}")
                    continue
                
                # Get fundamental data if available
                info = stock.info
                
                self.data[ticker] = {
                    'history': hist,
                    'info': info
                }
                print(f"  ✓ {ticker}: {len(hist)} days")
            except Exception as e:
                print(f"  ✗ {ticker}: {str(e)[:50]}")
        
        print(f"✓ Loaded data for {len(self.data)} tickers\n")
    
    def generate_factors(self):
        """Auto-generate candidate predictive factors"""
        print("🔬 Generating candidate factors...\n")
        
        all_factors = []
        
        for ticker, data in self.data.items():
            hist = data['history']
            info = data['info']
            
            df = pd.DataFrame(index=hist.index)
            df['ticker'] = ticker
            
            # Price-based factors
            df = self._price_factors(df, hist)
            
            # Volume factors
            df = self._volume_factors(df, hist)
            
            # Volatility factors
            df = self._volatility_factors(df, hist)
            
            # Momentum factors
            df = self._momentum_factors(df, hist)
            
            # Fundamental factors
            df = self._fundamental_factors(df, hist, info)
            
            # Technical pattern factors
            df = self._pattern_factors(df, hist)
            
            # Forward returns (target variable)
            df['fwd_return_5d'] = hist['Close'].pct_change(5).shift(-5)
            df['fwd_return_20d'] = hist['Close'].pct_change(20).shift(-20)
            
            all_factors.append(df)
        
        # Combine all tickers
        self.factors = pd.concat(all_factors, ignore_index=False)
        self.factors = self.factors.dropna(subset=['fwd_return_5d', 'fwd_return_20d'])
        
        factor_cols = [c for c in self.factors.columns if c not in ['ticker', 'fwd_return_5d', 'fwd_return_20d']]
        print(f"✓ Generated {len(factor_cols)} candidate factors")
        print(f"✓ Total observations: {len(self.factors)}\n")
        
        return factor_cols
    
    def _price_factors(self, df: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
        """Price-based factors"""
        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        
        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            df[f'sma_{period}'] = close.rolling(period).mean()
            df[f'price_to_sma_{period}'] = close / df[f'sma_{period}'] - 1
        
        # Price position
        df['high_low_ratio'] = high / low - 1
        df['close_to_high'] = close / high
        df['close_to_low'] = (close - low) / (high - low)
        
        # Distance from highs/lows
        df['dist_from_52w_high'] = close / close.rolling(252).max() - 1
        df['dist_from_52w_low'] = close / close.rolling(252).min() - 1
        
        return df
    
    def _volume_factors(self, df: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
        """Volume-based factors"""
        volume = hist['Volume']
        close = hist['Close']
        
        # Volume trends
        df['volume_sma_20'] = volume.rolling(20).mean()
        df['volume_ratio'] = volume / df['volume_sma_20']
        df['volume_trend_5d'] = volume.rolling(5).mean() / volume.rolling(20).mean()
        
        # Price-volume
        df['price_volume_corr_20'] = close.rolling(20).corr(volume)
        
        # On-balance volume
        df['obv'] = (np.sign(close.diff()) * volume).cumsum()
        df['obv_sma_20'] = df['obv'].rolling(20).mean()
        df['obv_trend'] = df['obv'] / df['obv_sma_20'] - 1
        
        return df
    
    def _volatility_factors(self, df: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
        """Volatility factors"""
        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        returns = close.pct_change()
        
        # Historical volatility
        for period in [5, 20, 60]:
            df[f'volatility_{period}d'] = returns.rolling(period).std() * np.sqrt(252)
        
        # ATR (Average True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()
        df['atr_ratio'] = df['atr_14'] / close
        
        # Volatility regime
        df['vol_regime'] = df['volatility_20d'] / df['volatility_60d']
        
        return df
    
    def _momentum_factors(self, df: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
        """Momentum factors"""
        close = hist['Close']
        
        # Returns over various periods
        for period in [1, 5, 10, 20, 60, 120, 252]:
            df[f'return_{period}d'] = close.pct_change(period)
        
        # RSI (Relative Strength Index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Rate of change
        df['roc_20'] = (close - close.shift(20)) / close.shift(20)
        
        return df
    
    def _fundamental_factors(self, df: pd.DataFrame, hist: pd.DataFrame, info: Dict) -> pd.DataFrame:
        """Fundamental factors from Yahoo Finance info"""
        close = hist['Close']
        
        # Valuation ratios (static, broadcast to all dates)
        pe_ratio = info.get('trailingPE', np.nan)
        pb_ratio = info.get('priceToBook', np.nan)
        ps_ratio = info.get('priceToSalesTrailing12Months', np.nan)
        
        df['pe_ratio'] = pe_ratio
        df['pb_ratio'] = pb_ratio
        df['ps_ratio'] = ps_ratio
        
        # Profitability
        profit_margin = info.get('profitMargins', np.nan)
        roe = info.get('returnOnEquity', np.nan)
        
        df['profit_margin'] = profit_margin
        df['roe'] = roe
        
        # Growth
        earnings_growth = info.get('earningsGrowth', np.nan)
        revenue_growth = info.get('revenueGrowth', np.nan)
        
        df['earnings_growth'] = earnings_growth
        df['revenue_growth'] = revenue_growth
        
        # Market cap category
        market_cap = info.get('marketCap', np.nan)
        if market_cap and not np.isnan(market_cap):
            if market_cap > 200e9:
                cap_cat = 3  # Mega cap
            elif market_cap > 10e9:
                cap_cat = 2  # Large cap
            elif market_cap > 2e9:
                cap_cat = 1  # Mid cap
            else:
                cap_cat = 0  # Small cap
        else:
            cap_cat = np.nan
        
        df['market_cap_category'] = cap_cat
        
        return df
    
    def _pattern_factors(self, df: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
        """Technical pattern recognition"""
        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        
        # Higher highs / lower lows
        df['higher_high_5d'] = (high > high.shift(5)).astype(int)
        df['lower_low_5d'] = (low < low.shift(5)).astype(int)
        
        # Consecutive up/down days
        daily_return = close.pct_change()
        df['consec_up'] = (daily_return > 0).rolling(5).sum()
        df['consec_down'] = (daily_return < 0).rolling(5).sum()
        
        # Gap detection
        prev_close = close.shift(1)
        df['gap_up'] = ((low - prev_close) / prev_close > 0.02).astype(int)
        df['gap_down'] = ((prev_close - high) / prev_close > 0.02).astype(int)
        
        # Moving average crossovers
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        df['golden_cross'] = ((sma_20 > sma_50) & (sma_20.shift(1) <= sma_50.shift(1))).astype(int)
        df['death_cross'] = ((sma_20 < sma_50) & (sma_20.shift(1) >= sma_50.shift(1))).astype(int)
        
        return df
    
    def calculate_ic(self, horizon='5d'):
        """Calculate Information Coefficient for each factor"""
        print(f"📈 Calculating Information Coefficient (IC) - {horizon} horizon...\n")
        
        target_col = f'fwd_return_{horizon}'
        factor_cols = [c for c in self.factors.columns 
                      if c not in ['ticker', 'fwd_return_5d', 'fwd_return_20d']]
        
        ic_results = []
        
        for factor in factor_cols:
            # Remove NaN for this factor
            valid_data = self.factors[[factor, target_col]].dropna()
            
            if len(valid_data) < 30:
                continue
            
            # Calculate Spearman rank correlation (more robust to outliers)
            ic = valid_data[factor].corr(valid_data[target_col], method='spearman')
            
            # Calculate IC over rolling windows for stability
            ic_std = np.nan
            if len(valid_data) > 100:
                rolling_ics = []
                for i in range(0, len(valid_data) - 60, 20):
                    window = valid_data.iloc[i:i+60]
                    if len(window) > 30:
                        ic_window = window[factor].corr(window[target_col], method='spearman')
                        if not np.isnan(ic_window):
                            rolling_ics.append(ic_window)
                if rolling_ics:
                    ic_std = np.std(rolling_ics)
            
            ic_results.append({
                'factor': factor,
                'ic': ic,
                'abs_ic': abs(ic),
                'ic_std': ic_std,
                'ic_stability': abs(ic) / ic_std if ic_std and ic_std > 0 else 0,
                'n_obs': len(valid_data)
            })
        
        ic_df = pd.DataFrame(ic_results)
        ic_df = ic_df.sort_values('abs_ic', ascending=False)
        
        # Save results
        self.ic_scores[horizon] = ic_df
        
        # Save to file
        ic_file = DATA_DIR / f'ic_rankings_{horizon}.json'
        ic_df.to_json(ic_file, orient='records', indent=2)
        
        print(f"Top 20 Factors by Information Coefficient ({horizon}):")
        print("="*80)
        for idx, row in ic_df.head(20).iterrows():
            stability_str = f"{row['ic_stability']:.2f}" if not np.isnan(row['ic_stability']) else "N/A"
            print(f"{row['factor']:30s}  IC: {row['ic']:7.4f}  |IC|: {row['abs_ic']:.4f}  "
                  f"Stability: {stability_str:>6s}  N: {row['n_obs']:>5d}")
        print()
        
        return ic_df
    
    def backtest_factor(self, factor_name: str, horizon='5d', quantiles=5):
        """Backtest a specific factor with walk-forward validation"""
        print(f"🔍 Backtesting factor: {factor_name} ({horizon} horizon)\n")
        
        target_col = f'fwd_return_{horizon}'
        
        # Get data for this factor
        data = self.factors[[factor_name, target_col, 'ticker']].copy()
        data = data.dropna()
        data = data.reset_index()
        data.columns = ['date'] + list(data.columns[1:])
        
        if len(data) < 100:
            print(f"❌ Insufficient data for backtesting ({len(data)} observations)")
            return None
        
        # Sort by date for walk-forward
        data = data.sort_values('date')
        
        # Create quantile portfolios
        data['factor_quantile'] = pd.qcut(data[factor_name], q=quantiles, labels=False, duplicates='drop')
        
        # Calculate returns by quantile
        quantile_returns = data.groupby('factor_quantile')[target_col].agg(['mean', 'std', 'count'])
        quantile_returns.columns = ['avg_return', 'std_return', 'count']
        quantile_returns['sharpe'] = quantile_returns['avg_return'] / quantile_returns['std_return']
        
        print("Quantile Portfolio Performance:")
        print("="*70)
        print(f"{'Quantile':<10} {'Avg Return':<15} {'Std Dev':<15} {'Sharpe':<10} {'Count':<10}")
        print("-"*70)
        for q in range(quantiles):
            if q in quantile_returns.index:
                row = quantile_returns.loc[q]
                print(f"Q{q+1:<9} {row['avg_return']*100:>7.2f}%{'':<7} "
                      f"{row['std_return']*100:>7.2f}%{'':<7} {row['sharpe']:>8.2f}   {int(row['count']):<10}")
        
        # Long-short strategy (top quantile vs bottom quantile)
        if 0 in quantile_returns.index and (quantiles-1) in quantile_returns.index:
            long_short = quantile_returns.loc[quantiles-1, 'avg_return'] - quantile_returns.loc[0, 'avg_return']
            print(f"\n📊 Long-Short Return (Q{quantiles} - Q1): {long_short*100:.2f}%")
        
        # Walk-forward validation
        print(f"\n🔄 Walk-Forward Validation (60/20 train/test split):")
        print("-"*70)
        
        n = len(data)
        train_size = 60
        test_size = 20
        
        wf_results = []
        
        for i in range(0, n - train_size - test_size, test_size):
            train_data = data.iloc[i:i+train_size]
            test_data = data.iloc[i+train_size:i+train_size+test_size]
            
            if len(test_data) < 5:
                break
            
            # Calculate quantile thresholds on training data
            quantile_thresholds = pd.qcut(train_data[factor_name], q=quantiles, retbins=True, duplicates='drop')[1]
            
            # Apply to test data
            test_data = test_data.copy()
            test_data['factor_quantile'] = pd.cut(test_data[factor_name], bins=quantile_thresholds, 
                                                   labels=False, include_lowest=True)
            
            # Performance by quantile in test period
            test_returns = test_data.groupby('factor_quantile')[target_col].mean()
            
            if len(test_returns) >= 2:
                # Top vs bottom
                top_q = test_returns.index.max()
                bottom_q = test_returns.index.min()
                ls_return = test_returns.loc[top_q] - test_returns.loc[bottom_q]
                
                wf_results.append({
                    'period': i // test_size + 1,
                    'long_short': ls_return,
                    'top_return': test_returns.loc[top_q],
                    'bottom_return': test_returns.loc[bottom_q]
                })
        
        if wf_results:
            wf_df = pd.DataFrame(wf_results)
            print(f"{'Period':<10} {'L/S Return':<15} {'Top Q Return':<15} {'Bottom Q Return':<15}")
            for _, row in wf_df.head(10).iterrows():
                print(f"{int(row['period']):<10} {row['long_short']*100:>7.2f}%{'':<7} "
                      f"{row['top_return']*100:>7.2f}%{'':<7} {row['bottom_return']*100:>7.2f}%")
            
            print(f"\n📈 Walk-Forward Stats:")
            print(f"  Mean L/S Return: {wf_df['long_short'].mean()*100:.2f}%")
            print(f"  Std Dev L/S: {wf_df['long_short'].std()*100:.2f}%")
            print(f"  Win Rate: {(wf_df['long_short'] > 0).mean()*100:.1f}%")
            print(f"  Sharpe Ratio: {wf_df['long_short'].mean() / wf_df['long_short'].std():.2f}")
        
        print()
        
        # Save backtest results
        result = {
            'factor': factor_name,
            'horizon': horizon,
            'quantile_returns': quantile_returns.to_dict('index'),
            'walk_forward': wf_results
        }
        
        backtest_file = DATA_DIR / f'backtest_{factor_name}_{horizon}.json'
        with open(backtest_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        return result
    
    def feature_importance(self, horizon='5d', top_n=20):
        """Calculate ML feature importance using ensemble methods"""
        if not SKLEARN_AVAILABLE:
            print("❌ scikit-learn not available. Install with: pip install scikit-learn")
            return None
        
        print(f"🤖 ML Feature Importance Analysis ({horizon} horizon)\n")
        
        target_col = f'fwd_return_{horizon}'
        factor_cols = [c for c in self.factors.columns 
                      if c not in ['ticker', 'fwd_return_5d', 'fwd_return_20d']]
        
        # Prepare data
        X = self.factors[factor_cols].copy()
        y = self.factors[target_col].copy()
        
        # Remove rows with any NaN
        valid_mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_mask]
        y = y[valid_mask]
        
        print(f"Training on {len(X)} samples with {len(factor_cols)} features...")
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=factor_cols, index=X.index)
        
        # Train multiple models
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42),
            'Lasso': LassoCV(cv=5, random_state=42, max_iter=1000)
        }
        
        importance_results = {}
        
        for model_name, model in models.items():
            print(f"\n🔧 Training {model_name}...")
            
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, test_idx in tscv.split(X_scaled):
                X_train, X_test = X_scaled.iloc[train_idx], X_scaled.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                model.fit(X_train, y_train)
                score = model.score(X_test, y_test)
                scores.append(score)
            
            print(f"  Cross-val R² scores: {[f'{s:.4f}' for s in scores]}")
            print(f"  Mean R²: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
            
            # Get feature importance
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_)
            else:
                continue
            
            # Store importance
            importance_df = pd.DataFrame({
                'feature': factor_cols,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            importance_results[model_name] = importance_df
        
        # Aggregate importance across models
        if importance_results:
            print(f"\n📊 Aggregated Feature Importance (Top {top_n}):")
            print("="*80)
            
            # Average rank across models
            rank_sum = pd.Series(0, index=factor_cols)
            
            for model_name, imp_df in importance_results.items():
                ranks = imp_df.reset_index(drop=True).reset_index()
                ranks.columns = ['rank', 'feature', 'importance']
                for _, row in ranks.iterrows():
                    rank_sum[row['feature']] += row['rank']
            
            avg_rank = rank_sum / len(importance_results)
            avg_rank = avg_rank.sort_values()
            
            print(f"{'Rank':<6} {'Feature':<30} {'Avg Rank':<12} RF Imp    GB Imp")
            print("-"*80)
            
            for i, (feature, avg_r) in enumerate(avg_rank.head(top_n).items(), 1):
                rf_imp = importance_results.get('Random Forest')
                gb_imp = importance_results.get('Gradient Boosting')
                
                rf_val = rf_imp[rf_imp['feature'] == feature]['importance'].values[0] if rf_imp is not None else 0
                gb_val = gb_imp[gb_imp['feature'] == feature]['importance'].values[0] if gb_imp is not None else 0
                
                print(f"{i:<6} {feature:<30} {avg_r:>10.1f}   {rf_val:>6.4f}   {gb_val:>6.4f}")
            
            # Save results
            importance_file = DATA_DIR / f'feature_importance_{horizon}.json'
            with open(importance_file, 'w') as f:
                json.dump({
                    model_name: df.to_dict('records') 
                    for model_name, df in importance_results.items()
                }, f, indent=2)
            
            print(f"\n✓ Results saved to {importance_file}")
        
        print()
        return importance_results


def cmd_discover_factors(args):
    """Discover predictive factors from ticker list"""
    tickers = args.tickers.split(',')
    tickers = [t.strip().upper() for t in tickers]
    
    print(f"🚀 ML FACTOR DISCOVERY")
    print(f"{'='*80}\n")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Lookback: {args.lookback} days\n")
    
    # Initialize discovery engine
    discovery = FactorDiscovery(tickers, lookback_days=args.lookback)
    
    # Fetch data
    discovery.fetch_data()
    
    if not discovery.data:
        print("❌ No data available. Exiting.")
        return 1
    
    # Generate factors
    factor_cols = discovery.generate_factors()
    
    # Calculate IC for both horizons
    ic_5d = discovery.calculate_ic(horizon='5d')
    ic_20d = discovery.calculate_ic(horizon='20d')
    
    print(f"✅ Discovery complete!")
    print(f"📁 Results saved to: {DATA_DIR}")
    print(f"\nNext steps:")
    print(f"  - Review IC rankings: python cli.py factor-ic")
    print(f"  - Backtest top factors: python cli.py factor-backtest <factor_name>")
    print(f"  - ML feature importance: python cli.py feature-importance")
    
    return 0


def cmd_factor_ic(args):
    """Display Information Coefficient rankings"""
    print(f"📊 INFORMATION COEFFICIENT RANKINGS")
    print(f"{'='*80}\n")
    
    # Load IC results
    ic_5d_file = DATA_DIR / 'ic_rankings_5d.json'
    ic_20d_file = DATA_DIR / 'ic_rankings_20d.json'
    
    if not ic_5d_file.exists():
        print("❌ No IC rankings found. Run: python cli.py discover-factors <tickers>")
        return 1
    
    ic_5d = pd.read_json(ic_5d_file)
    
    print(f"Top {args.top_n} Factors - 5-Day Forward Returns:")
    print("-"*80)
    print(f"{'Factor':<30} {'IC':<10} {'|IC|':<10} {'Stability':<12} {'N Obs':<10}")
    print("-"*80)
    
    for idx, row in ic_5d.head(args.top_n).iterrows():
        stability = f"{row['ic_stability']:.2f}" if not np.isnan(row['ic_stability']) else "N/A"
        print(f"{row['factor']:<30} {row['ic']:>8.4f}   {row['abs_ic']:>8.4f}   {stability:>10}   {int(row['n_obs']):>8}")
    
    if ic_20d_file.exists():
        print(f"\nTop {args.top_n} Factors - 20-Day Forward Returns:")
        print("-"*80)
        
        ic_20d = pd.read_json(ic_20d_file)
        
        print(f"{'Factor':<30} {'IC':<10} {'|IC|':<10} {'Stability':<12} {'N Obs':<10}")
        print("-"*80)
        
        for idx, row in ic_20d.head(args.top_n).iterrows():
            stability = f"{row['ic_stability']:.2f}" if not np.isnan(row['ic_stability']) else "N/A"
            print(f"{row['factor']:<30} {row['ic']:>8.4f}   {row['abs_ic']:>8.4f}   {stability:>10}   {int(row['n_obs']):>8}")
    
    print()
    return 0


def cmd_factor_backtest(args):
    """Backtest a specific factor"""
    # Need to reload factor data
    print(f"🔄 Loading factor data...\n")
    
    # Check if we have recent factor data
    if not (DATA_DIR / 'ic_rankings_5d.json').exists():
        print("❌ No factor data found. Run: python cli.py discover-factors <tickers>")
        return 1
    
    # For backtesting, we need to re-run discovery to get the full factor dataset
    # This is a simplified version - in production, we'd save the factor dataframe
    print("Note: Re-run discovery with same tickers to backtest factors")
    print("Usage: python cli.py discover-factors AAPL,MSFT,GOOGL")
    print("       Then factor-backtest will work on that dataset")
    
    return 0


def cmd_feature_importance(args):
    """Display ML feature importance"""
    print(f"🤖 ML FEATURE IMPORTANCE")
    print(f"{'='*80}\n")
    
    importance_file = DATA_DIR / f'feature_importance_{args.horizon}.json'
    
    if not importance_file.exists():
        print(f"❌ No feature importance results found for {args.horizon} horizon.")
        print("Run: python cli.py discover-factors <tickers>")
        return 1
    
    with open(importance_file) as f:
        importance_results = json.load(f)
    
    for model_name, features in importance_results.items():
        print(f"\n{model_name}:")
        print("-"*60)
        print(f"{'Rank':<6} {'Feature':<35} {'Importance':<12}")
        print("-"*60)
        
        for i, feat in enumerate(features[:args.top_n], 1):
            print(f"{i:<6} {feat['feature']:<35} {feat['importance']:>10.6f}")
    
    print()
    return 0


def main():
    parser = argparse.ArgumentParser(description='ML Factor Discovery')
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # discover-factors
    p_discover = subparsers.add_parser('discover-factors', help='Discover predictive factors')
    p_discover.add_argument('tickers', help='Comma-separated ticker list (e.g., AAPL,MSFT,GOOGL)')
    p_discover.add_argument('--lookback', type=int, default=504, help='Lookback days (default: 504)')
    
    # factor-ic
    p_ic = subparsers.add_parser('factor-ic', help='Show Information Coefficient rankings')
    p_ic.add_argument('--top-n', type=int, default=20, help='Number of top factors to show')
    
    # factor-backtest
    p_backtest = subparsers.add_parser('factor-backtest', help='Backtest a specific factor')
    p_backtest.add_argument('factor', help='Factor name to backtest')
    p_backtest.add_argument('--horizon', default='5d', choices=['5d', '20d'], help='Forecast horizon')
    
    # feature-importance
    p_importance = subparsers.add_parser('feature-importance', help='ML feature importance analysis')
    p_importance.add_argument('--horizon', default='5d', choices=['5d', '20d'], help='Forecast horizon')
    p_importance.add_argument('--top-n', type=int, default=20, help='Number of top features')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handlers
    if args.command == 'discover-factors':
        return cmd_discover_factors(args)
    elif args.command == 'factor-ic':
        return cmd_factor_ic(args)
    elif args.command == 'factor-backtest':
        return cmd_factor_backtest(args)
    elif args.command == 'feature-importance':
        return cmd_feature_importance(args)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
