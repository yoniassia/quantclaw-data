#!/usr/bin/env python3
"""
Correlation Anomaly Detector — Phase 87
Identify unusual correlation breakdowns, detect regime shifts, flag arbitrage opportunities
"""

import sys
import argparse
import json
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from scipy.stats import zscore

warnings.filterwarnings('ignore')


class CorrelationAnomalyDetector:
    """Detect correlation anomalies and regime shifts across asset classes"""
    
    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        self.short_window = 20  # 1 month
        self.long_window = 60   # 3 months
        
    def fetch_prices(self, tickers: List[str]) -> pd.DataFrame:
        """Fetch historical prices for multiple tickers"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days + 100)
        
        data = {}
        for ticker in tickers:
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not df.empty and 'Close' in df.columns:
                    close_series = df['Close']
                    if isinstance(close_series, pd.DataFrame):
                        close_series = close_series.iloc[:, 0]
                    data[ticker] = close_series
                else:
                    print(f"Warning: No data for {ticker}", file=sys.stderr)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}", file=sys.stderr)
        
        if not data:
            raise ValueError("No price data available")
        
        df = pd.DataFrame(data)
        return df.dropna()
    
    def calculate_rolling_correlation(self, returns: pd.DataFrame, window: int = 60) -> pd.DataFrame:
        """Calculate rolling correlation matrix"""
        correlations = {}
        
        for col1 in returns.columns:
            for col2 in returns.columns:
                if col1 < col2:  # Avoid duplicates
                    rolling_corr = returns[col1].rolling(window).corr(returns[col2])
                    correlations[f"{col1}-{col2}"] = rolling_corr
        
        return pd.DataFrame(correlations)
    
    def detect_correlation_breakdown(self, ticker1: str, ticker2: str) -> Dict:
        """Detect correlation breakdown between two assets"""
        prices = self.fetch_prices([ticker1, ticker2])
        returns = prices.pct_change().dropna()
        
        # Calculate rolling correlation
        rolling_corr = returns[ticker1].rolling(self.long_window).corr(returns[ticker2])
        
        # Current correlation
        current_corr = rolling_corr.iloc[-self.short_window:].mean()
        
        # Historical mean and std
        hist_mean = rolling_corr.iloc[:-self.short_window].mean()
        hist_std = rolling_corr.iloc[:-self.short_window].std()
        
        # Z-score of current correlation
        z_score = (current_corr - hist_mean) / (hist_std + 1e-8)
        
        # Breakdown detected if |z-score| > 2
        breakdown = abs(z_score) > 2.0
        
        # Directional breakdown
        if breakdown:
            if z_score < -2.0:
                direction = "NEGATIVE_BREAKDOWN"  # Correlation weakening
            else:
                direction = "POSITIVE_SURGE"       # Correlation strengthening
        else:
            direction = "NORMAL"
        
        # Calculate correlation change velocity
        corr_change = current_corr - rolling_corr.iloc[-self.short_window*2:-self.short_window].mean()
        
        return {
            "pair": f"{ticker1}-{ticker2}",
            "current_correlation": round(float(current_corr), 4),
            "historical_mean": round(float(hist_mean), 4),
            "historical_std": round(float(hist_std), 4),
            "z_score": round(float(z_score), 3),
            "breakdown_detected": bool(breakdown),
            "direction": direction,
            "correlation_change": round(float(corr_change), 4),
            "signal": "ARBITRAGE_OPPORTUNITY" if breakdown else "NORMAL",
            "data_points": len(rolling_corr),
            "timestamp": datetime.now().isoformat()
        }
    
    def scan_correlation_matrix(self, tickers: List[str]) -> Dict:
        """Scan correlation matrix for anomalies"""
        prices = self.fetch_prices(tickers)
        returns = prices.pct_change().dropna()
        
        # Current correlation matrix (short-term)
        recent_returns = returns.iloc[-self.short_window:]
        current_corr_matrix = recent_returns.corr()
        
        # Historical correlation matrix (long-term)
        hist_returns = returns.iloc[:-self.short_window]
        hist_corr_matrix = hist_returns.corr()
        
        # Calculate correlation changes
        corr_changes = current_corr_matrix - hist_corr_matrix
        
        # Identify significant changes
        anomalies = []
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:  # Upper triangle only
                    change = corr_changes.loc[ticker1, ticker2]
                    current = current_corr_matrix.loc[ticker1, ticker2]
                    historical = hist_corr_matrix.loc[ticker1, ticker2]
                    
                    # Calculate z-score across all pairwise changes
                    std = hist_returns[ticker1].rolling(self.long_window).corr(hist_returns[ticker2]).std()
                    z_score = change / (std + 1e-8)
                    
                    if abs(change) > 0.3:  # Significant change threshold
                        anomalies.append({
                            "pair": f"{ticker1}-{ticker2}",
                            "current_corr": round(float(current), 4),
                            "historical_corr": round(float(historical), 4),
                            "change": round(float(change), 4),
                            "z_score": round(float(z_score), 3),
                            "severity": "HIGH" if abs(change) > 0.5 else "MEDIUM"
                        })
        
        # Sort by absolute change
        anomalies.sort(key=lambda x: abs(x["change"]), reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "universe": tickers,
            "window_short": self.short_window,
            "window_long": self.long_window,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[:10],  # Top 10
            "current_correlation_matrix": current_corr_matrix.round(3).to_dict(),
            "historical_correlation_matrix": hist_corr_matrix.round(3).to_dict()
        }
    
    def detect_regime_shift(self, tickers: List[str]) -> Dict:
        """Detect market regime shifts using correlation structure changes"""
        prices = self.fetch_prices(tickers)
        returns = prices.pct_change().dropna()
        
        # Calculate rolling correlation mean (average pairwise correlation)
        rolling_corrs = []
        window = self.long_window
        
        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]
            corr_matrix = window_returns.corr()
            # Average correlation (excluding diagonal)
            mask = np.ones(corr_matrix.shape, dtype=bool)
            np.fill_diagonal(mask, False)
            avg_corr = corr_matrix.values[mask].mean()
            rolling_corrs.append(avg_corr)
        
        rolling_corrs = pd.Series(rolling_corrs, index=returns.index[window:])
        
        # Current regime (last 20 days)
        current_avg_corr = rolling_corrs.iloc[-self.short_window:].mean()
        
        # Historical average
        hist_avg_corr = rolling_corrs.iloc[:-self.short_window].mean()
        hist_std = rolling_corrs.iloc[:-self.short_window].std()
        
        # Z-score
        z_score = (current_avg_corr - hist_avg_corr) / (hist_std + 1e-8)
        
        # Regime classification
        if current_avg_corr > 0.7:
            regime = "HIGH_CORRELATION"  # Crisis mode
            description = "High correlation regime (crisis/panic selling)"
        elif current_avg_corr > 0.4:
            regime = "NORMAL_CORRELATION"
            description = "Normal correlation regime"
        elif current_avg_corr > 0.1:
            regime = "LOW_CORRELATION"
            description = "Low correlation regime (market diversification)"
        else:
            regime = "DECORRELATED"  # Rare
            description = "Decorrelated regime (rare, check data quality)"
        
        # Detect shift
        regime_shift = abs(z_score) > 2.0
        
        # Correlation volatility (instability indicator)
        corr_volatility = rolling_corrs.iloc[-self.long_window:].std()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current_regime": regime,
            "description": description,
            "current_avg_correlation": round(float(current_avg_corr), 4),
            "historical_avg_correlation": round(float(hist_avg_corr), 4),
            "z_score": round(float(z_score), 3),
            "regime_shift_detected": bool(regime_shift),
            "correlation_volatility": round(float(corr_volatility), 4),
            "stability": "UNSTABLE" if corr_volatility > 0.15 else "STABLE",
            "universe": tickers,
            "data_points": len(rolling_corrs)
        }
    
    def find_arbitrage_opportunities(self, tickers: List[str]) -> Dict:
        """Identify pairs with correlation breakdown for statistical arbitrage"""
        prices = self.fetch_prices(tickers)
        returns = prices.pct_change().dropna()
        
        # Calculate cointegration and correlation for all pairs
        opportunities = []
        
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:
                    # Rolling correlation
                    rolling_corr = returns[ticker1].rolling(self.long_window).corr(returns[ticker2])
                    
                    # Current vs historical
                    current_corr = rolling_corr.iloc[-self.short_window:].mean()
                    hist_corr = rolling_corr.iloc[:-self.short_window].mean()
                    hist_std = rolling_corr.iloc[:-self.short_window].std()
                    
                    corr_change = current_corr - hist_corr
                    z_score = corr_change / (hist_std + 1e-8)
                    
                    # Calculate spread (normalized price ratio)
                    price_ratio = prices[ticker1] / prices[ticker2]
                    ratio_mean = price_ratio.iloc[:-self.short_window].mean()
                    ratio_std = price_ratio.iloc[:-self.short_window].std()
                    current_ratio = price_ratio.iloc[-1]
                    ratio_z = (current_ratio - ratio_mean) / (ratio_std + 1e-8)
                    
                    # Arbitrage signal: correlation breakdown + mean reversion opportunity
                    if abs(z_score) > 2.0 and hist_corr > 0.6:  # High historical correlation
                        signal_strength = abs(z_score) + abs(ratio_z)
                        
                        # Trade direction
                        if ratio_z > 2.0:
                            trade = f"SHORT {ticker1}, LONG {ticker2}"
                        elif ratio_z < -2.0:
                            trade = f"LONG {ticker1}, SHORT {ticker2}"
                        else:
                            trade = "WAIT (no clear spread)"
                        
                        opportunities.append({
                            "pair": f"{ticker1}-{ticker2}",
                            "historical_correlation": round(float(hist_corr), 4),
                            "current_correlation": round(float(current_corr), 4),
                            "correlation_z_score": round(float(z_score), 3),
                            "price_ratio_z_score": round(float(ratio_z), 3),
                            "signal_strength": round(float(signal_strength), 3),
                            "trade_recommendation": trade,
                            "confidence": "HIGH" if signal_strength > 4.0 else "MEDIUM"
                        })
        
        # Sort by signal strength
        opportunities.sort(key=lambda x: x["signal_strength"], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "universe": tickers,
            "opportunities_found": len(opportunities),
            "top_opportunities": opportunities[:5],  # Top 5
            "all_opportunities": opportunities
        }


def main():
    parser = argparse.ArgumentParser(description="Correlation Anomaly Detector")
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('--ticker1', help='First ticker (for corr-breakdown)')
    parser.add_argument('--ticker2', help='Second ticker (for corr-breakdown)')
    parser.add_argument('--tickers', help='Comma-separated list of tickers (for corr-scan/corr-regime/corr-arbitrage)')
    parser.add_argument('--lookback', type=int, default=252, help='Lookback period in days')
    
    args = parser.parse_args()
    
    detector = CorrelationAnomalyDetector(lookback_days=args.lookback)
    
    try:
        if args.command == 'corr-breakdown':
            if not args.ticker1 or not args.ticker2:
                print(json.dumps({"error": "Both --ticker1 and --ticker2 required for breakdown"}), 
                      file=sys.stderr)
                sys.exit(1)
            
            result = detector.detect_correlation_breakdown(args.ticker1, args.ticker2)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'corr-scan':
            if not args.tickers:
                # Default universe: major indices and sectors
                tickers = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'USO', 'UUP']
            else:
                tickers = args.tickers.split(',')
            
            result = detector.scan_correlation_matrix(tickers)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'corr-regime':
            if not args.tickers:
                # Default multi-asset universe
                tickers = ['SPY', 'TLT', 'GLD', 'DBC', 'UUP', 'EEM', 'HYG', 'LQD']
            else:
                tickers = args.tickers.split(',')
            
            result = detector.detect_regime_shift(tickers)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'corr-arbitrage':
            if not args.tickers:
                # Default sector ETF universe for pairs trading
                tickers = ['XLF', 'XLK', 'XLE', 'XLV', 'XLY', 'XLP', 'XLI', 'XLU', 'XLB']
            else:
                tickers = args.tickers.split(',')
            
            result = detector.find_arbitrage_opportunities(tickers)
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"error": f"Unknown command: {args.command}"}), file=sys.stderr)
            print("Available commands: corr-breakdown, corr-scan, corr-regime, corr-arbitrage", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        error_result = {
            "error": str(e),
            "command": args.command,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
