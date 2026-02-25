"""
Walk-Forward Optimization Module
Out-of-sample strategy tuning with rolling windows to prevent overfitting.
Phase 37: Quantitative Analytics
"""

import yfinance as yf
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')


@dataclass
class OptimizationResult:
    """Results from a single optimization window"""
    params: Dict[str, float]
    in_sample_sharpe: float
    out_sample_sharpe: float
    in_sample_returns: float
    out_sample_returns: float
    degradation: float  # Sharpe ratio degradation (IS - OOS)
    overfitting_score: float  # 0-100, higher = more overfit


@dataclass
class WalkForwardResults:
    """Complete walk-forward analysis results"""
    windows: List[OptimizationResult]
    avg_is_sharpe: float
    avg_oos_sharpe: float
    avg_degradation: float
    overall_oos_sharpe: float
    param_stability: Dict[str, float]  # std dev of each param across windows
    overfitting_detected: bool
    combined_returns: pd.Series


class Strategy:
    """Base strategy class"""
    
    def __init__(self, **params):
        self.params = params
    
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Generate trading signals (-1, 0, 1)"""
        raise NotImplementedError


class SMAStrategy(Strategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        super().__init__(fast_period=fast_period, slow_period=slow_period)
        self.fast_period = int(fast_period)
        self.slow_period = int(slow_period)
    
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Generate signals: 1 (long), -1 (short), 0 (neutral)"""
        fast_ma = prices.rolling(window=self.fast_period).mean()
        slow_ma = prices.rolling(window=self.slow_period).mean()
        
        signals = pd.Series(0, index=prices.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma < slow_ma] = -1
        
        return signals


def fetch_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch price data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            raise ValueError(f"No data found for {symbol}")
        
        return df
    except Exception as e:
        raise Exception(f"Error fetching data for {symbol}: {str(e)}")


def calculate_returns(prices: pd.Series, signals: pd.Series) -> pd.Series:
    """Calculate strategy returns based on signals"""
    price_returns = prices.pct_change()
    strategy_returns = signals.shift(1) * price_returns
    return strategy_returns.fillna(0)


def calculate_sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized Sharpe ratio"""
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    
    mean_return = returns.mean() * periods_per_year
    std_return = returns.std() * np.sqrt(periods_per_year)
    
    return mean_return / std_return if std_return > 0 else 0.0


def optimize_strategy(prices: pd.Series, strategy_class: type, 
                     param_bounds: Dict[str, Tuple[float, float]]) -> Tuple[Dict, float]:
    """Optimize strategy parameters on in-sample data"""
    
    def objective(params_array):
        # Convert array to dict
        params = {name: val for name, val in zip(param_bounds.keys(), params_array)}
        
        # Create strategy and generate signals
        strategy = strategy_class(**params)
        signals = strategy.generate_signals(prices)
        
        # Calculate returns and Sharpe
        returns = calculate_returns(prices, signals)
        sharpe = calculate_sharpe_ratio(returns)
        
        # Minimize negative Sharpe (maximize Sharpe)
        return -sharpe
    
    # Initial guess (midpoint of bounds)
    x0 = [np.mean(bounds) for bounds in param_bounds.values()]
    
    # Bounds for scipy
    bounds = list(param_bounds.values())
    
    # Optimize
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    # Extract best parameters
    best_params = {name: val for name, val in zip(param_bounds.keys(), result.x)}
    best_sharpe = -result.fun
    
    return best_params, best_sharpe


def walk_forward_optimize(symbol: str, 
                         strategy_class: type = SMAStrategy,
                         param_bounds: Dict[str, Tuple[float, float]] = None,
                         start_date: str = None,
                         end_date: str = None,
                         in_sample_days: int = 252,
                         out_sample_days: int = 63,
                         step_days: int = 63) -> WalkForwardResults:
    """
    Perform walk-forward optimization
    
    Args:
        symbol: Stock ticker
        strategy_class: Strategy class to optimize
        param_bounds: Parameter bounds for optimization
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        in_sample_days: Training window size
        out_sample_days: Testing window size
        step_days: Window step size (overlap if < out_sample_days)
    
    Returns:
        WalkForwardResults with all analysis
    """
    
    # Default parameter bounds for SMA strategy
    if param_bounds is None:
        param_bounds = {
            'fast_period': (5, 50),
            'slow_period': (20, 200)
        }
    
    # Default date range (3 years)
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
    
    # Fetch data
    df = fetch_data(symbol, start_date, end_date)
    prices = df['Close']
    
    # Walk-forward windows
    windows: List[OptimizationResult] = []
    all_oos_returns = []
    param_history = {key: [] for key in param_bounds.keys()}
    
    start_idx = 0
    while start_idx + in_sample_days + out_sample_days <= len(prices):
        # Define windows
        is_start = start_idx
        is_end = start_idx + in_sample_days
        oos_start = is_end
        oos_end = min(oos_start + out_sample_days, len(prices))
        
        # In-sample optimization
        is_prices = prices.iloc[is_start:is_end]
        best_params, is_sharpe = optimize_strategy(is_prices, strategy_class, param_bounds)
        
        # Out-of-sample testing
        oos_prices = prices.iloc[oos_start:oos_end]
        strategy = strategy_class(**best_params)
        oos_signals = strategy.generate_signals(oos_prices)
        oos_returns = calculate_returns(oos_prices, oos_signals)
        oos_sharpe = calculate_sharpe_ratio(oos_returns)
        
        # Calculate metrics
        is_returns_total = ((1 + calculate_returns(is_prices, 
                            strategy_class(**best_params).generate_signals(is_prices))).prod() - 1) * 100
        oos_returns_total = ((1 + oos_returns).prod() - 1) * 100
        
        degradation = is_sharpe - oos_sharpe
        
        # Overfitting score (0-100, higher = worse)
        # Based on Sharpe degradation and returns divergence
        sharpe_penalty = max(0, degradation) * 20  # Each point of degradation = 20 points
        returns_divergence = abs(is_returns_total - oos_returns_total) / max(abs(is_returns_total), 0.1)
        overfit_score = min(100, sharpe_penalty + returns_divergence * 30)
        
        window_result = OptimizationResult(
            params=best_params,
            in_sample_sharpe=is_sharpe,
            out_sample_sharpe=oos_sharpe,
            in_sample_returns=is_returns_total,
            out_sample_returns=oos_returns_total,
            degradation=degradation,
            overfitting_score=overfit_score
        )
        
        windows.append(window_result)
        all_oos_returns.append(oos_returns)
        
        # Track parameter history
        for key, val in best_params.items():
            param_history[key].append(val)
        
        # Step forward
        start_idx += step_days
    
    # Calculate aggregate metrics
    avg_is_sharpe = np.mean([w.in_sample_sharpe for w in windows])
    avg_oos_sharpe = np.mean([w.out_sample_sharpe for w in windows])
    avg_degradation = np.mean([w.degradation for w in windows])
    
    # Combine all OOS returns for overall Sharpe
    combined_returns = pd.concat(all_oos_returns)
    overall_oos_sharpe = calculate_sharpe_ratio(combined_returns)
    
    # Parameter stability (lower std = more stable)
    param_stability = {key: np.std(vals) for key, vals in param_history.items()}
    
    # Overfitting detection
    # Criteria: avg degradation > 1.0 OR avg overfit score > 50 OR OOS Sharpe < 0
    overfitting_detected = (avg_degradation > 1.0 or 
                           np.mean([w.overfitting_score for w in windows]) > 50 or
                           overall_oos_sharpe < 0)
    
    return WalkForwardResults(
        windows=windows,
        avg_is_sharpe=avg_is_sharpe,
        avg_oos_sharpe=avg_oos_sharpe,
        avg_degradation=avg_degradation,
        overall_oos_sharpe=overall_oos_sharpe,
        param_stability=param_stability,
        overfitting_detected=overfitting_detected,
        combined_returns=combined_returns
    )


def format_results(results: WalkForwardResults, symbol: str) -> str:
    """Format walk-forward results for display"""
    
    output = []
    output.append(f"{'='*60}")
    output.append(f"WALK-FORWARD OPTIMIZATION RESULTS: {symbol}")
    output.append(f"{'='*60}\n")
    
    output.append(f"📊 OVERALL METRICS")
    output.append(f"  Number of Windows: {len(results.windows)}")
    output.append(f"  Avg In-Sample Sharpe: {results.avg_is_sharpe:.3f}")
    output.append(f"  Avg Out-Sample Sharpe: {results.avg_oos_sharpe:.3f}")
    output.append(f"  Overall OOS Sharpe: {results.overall_oos_sharpe:.3f}")
    output.append(f"  Avg Degradation: {results.avg_degradation:.3f}")
    output.append(f"  Overfitting Detected: {'⚠️  YES' if results.overfitting_detected else '✅ NO'}\n")
    
    output.append(f"🔧 PARAMETER STABILITY (Std Dev)")
    for param, std in results.param_stability.items():
        output.append(f"  {param}: {std:.2f}")
    output.append("")
    
    output.append(f"📈 WINDOW-BY-WINDOW RESULTS")
    output.append(f"{'Window':<8} {'IS Sharpe':<12} {'OOS Sharpe':<12} {'Degradation':<14} {'Overfit':<10} {'Params'}")
    output.append(f"{'-'*90}")
    
    for i, window in enumerate(results.windows, 1):
        params_str = ", ".join([f"{k}={v:.1f}" for k, v in window.params.items()])
        output.append(f"{i:<8} {window.in_sample_sharpe:<12.3f} {window.out_sample_sharpe:<12.3f} "
                     f"{window.degradation:<14.3f} {window.overfitting_score:<10.1f} {params_str}")
    
    return "\n".join(output)


def check_overfitting(symbol: str, **kwargs) -> Dict:
    """
    Quick overfitting check
    
    Returns JSON with overfitting metrics
    """
    results = walk_forward_optimize(symbol, **kwargs)
    
    return {
        "symbol": symbol,
        "overfitting_detected": results.overfitting_detected,
        "avg_degradation": round(results.avg_degradation, 3),
        "avg_is_sharpe": round(results.avg_is_sharpe, 3),
        "avg_oos_sharpe": round(results.avg_oos_sharpe, 3),
        "overall_oos_sharpe": round(results.overall_oos_sharpe, 3),
        "windows_analyzed": len(results.windows),
        "recommendation": "REJECT - Likely overfit" if results.overfitting_detected else "ACCEPT - Robust strategy"
    }


def analyze_param_stability(symbol: str, **kwargs) -> Dict:
    """
    Analyze parameter stability across windows
    
    Returns JSON with stability metrics
    """
    results = walk_forward_optimize(symbol, **kwargs)
    
    # Calculate coefficient of variation (CV = std/mean) for each param
    param_cv = {}
    for param, std in results.param_stability.items():
        mean_val = np.mean([w.params[param] for w in results.windows])
        param_cv[param] = (std / mean_val) if mean_val > 0 else 0
    
    # Stability assessment
    max_cv = max(param_cv.values())
    if max_cv < 0.2:
        stability = "EXCELLENT"
    elif max_cv < 0.5:
        stability = "GOOD"
    elif max_cv < 1.0:
        stability = "MODERATE"
    else:
        stability = "POOR"
    
    return {
        "symbol": symbol,
        "param_stability_std": {k: round(v, 2) for k, v in results.param_stability.items()},
        "param_coefficient_variation": {k: round(v, 3) for k, v in param_cv.items()},
        "stability_rating": stability,
        "windows_analyzed": len(results.windows),
        "recommendation": "Parameters are stable across time" if stability in ["EXCELLENT", "GOOD"] 
                         else "Parameters vary significantly - possible regime changes or overfitting"
    }


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Walk-Forward Optimization')
    parser.add_argument('command', choices=['walk-forward', 'overfit-check', 'param-stability'],
                       help='Command to execute')
    parser.add_argument('symbol', help='Stock ticker symbol')
    parser.add_argument('--strategy', default='sma-crossover', 
                       choices=['sma-crossover'],
                       help='Strategy to optimize')
    parser.add_argument('--in-sample', type=int, default=252,
                       help='In-sample window size in days')
    parser.add_argument('--out-sample', type=int, default=63,
                       help='Out-of-sample window size in days')
    parser.add_argument('--step', type=int, default=63,
                       help='Window step size in days')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'walk-forward':
            print(f"Running walk-forward optimization for {args.symbol}...")
            results = walk_forward_optimize(
                args.symbol,
                strategy_class=SMAStrategy,
                in_sample_days=args.in_sample,
                out_sample_days=args.out_sample,
                step_days=args.step
            )
            print(format_results(results, args.symbol))
        
        elif args.command == 'overfit-check':
            print(f"Checking overfitting for {args.symbol}...")
            result = check_overfitting(
                args.symbol,
                strategy_class=SMAStrategy,
                in_sample_days=args.in_sample,
                out_sample_days=args.out_sample,
                step_days=args.step
            )
            print(json.dumps(result, indent=2))
        
        elif args.command == 'param-stability':
            print(f"Analyzing parameter stability for {args.symbol}...")
            result = analyze_param_stability(
                args.symbol,
                strategy_class=SMAStrategy,
                in_sample_days=args.in_sample,
                out_sample_days=args.out_sample,
                step_days=args.step
            )
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
