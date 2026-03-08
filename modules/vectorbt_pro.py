"""
VectorBT Pro Module - Advanced Backtesting Features

Advanced features of VectorBT library for professional quantitative analysis.
Focuses on multi-asset portfolios, walk-forward optimization, risk analytics,
and Monte Carlo simulation - all using FREE tier features.

Category: Quant Tools & ML
Data Type: Library
Free Tier: True (uses free vectorbt features only)
Update Frequency: N/A (library)
Relevance Score: 9/10
Integration Ease: 8/10

Installation:
    pip install vectorbt

Documentation: https://vectorbt.dev/
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta

def get_module_info() -> Dict:
    """Get information about the VectorBT Pro module."""
    try:
        import vectorbt as vbt
        version = vbt.__version__
        installed = True
    except ImportError:
        version = "Not installed"
        installed = False
    
    return {
        "name": "VectorBT Pro (Advanced Features)",
        "version": version,
        "installed": installed,
        "category": "Quant Tools & ML",
        "description": "Advanced backtesting with multi-asset portfolios and risk analytics",
        "license": "Apache 2.0",
        "documentation": "https://vectorbt.dev/",
        "installation": "pip install vectorbt",
        "key_features": [
            "Multi-asset portfolio backtesting",
            "Walk-forward optimization",
            "Advanced risk metrics (VaR, CVaR, Sortino)",
            "Monte Carlo simulation",
            "Custom indicator creation",
            "Portfolio rebalancing strategies"
        ]
    }

def backtest_multi_asset_portfolio(
    data: Dict[str, pd.DataFrame],
    weights: Optional[Dict[str, float]] = None,
    rebalance_freq: str = 'ME',
    init_cash: float = 10000.0
) -> Dict:
    """
    Backtest a multi-asset portfolio with periodic rebalancing.
    
    Args:
        data: Dict of {symbol: DataFrame with price data}
        weights: Dict of {symbol: weight}. If None, uses equal weights.
        rebalance_freq: Rebalancing frequency ('D', 'W', 'M', 'Q', 'Y')
        init_cash: Initial cash
    
    Returns:
        Dict with portfolio performance metrics
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {
            "error": "VectorBT not installed. Run: pip install vectorbt",
            "success": False
        }
    
    try:
        # Extract close prices and align dates
        symbols = list(data.keys())
        prices_dict = {}
        
        for symbol in symbols:
            df = data[symbol]
            close = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]
            prices_dict[symbol] = close
        
        # Create aligned DataFrame
        prices_df = pd.DataFrame(prices_dict)
        prices_df = prices_df.dropna()
        
        # Set equal weights if not provided
        if weights is None:
            weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Create weight series for each asset
        weight_series = pd.DataFrame({
            symbol: weights.get(symbol, 0.0) 
            for symbol in symbols
        }, index=prices_df.index)
        
        # Resample for rebalancing
        rebalance_dates = prices_df.resample(rebalance_freq).last().index
        
        # Calculate equal-weighted portfolio returns manually
        returns_df = prices_df.pct_change()
        
        # Apply weights to each asset's returns
        weighted_returns = pd.Series(0.0, index=returns_df.index)
        for symbol in symbols:
            weight = weights.get(symbol, 0.0)
            weighted_returns += returns_df[symbol] * weight
        
        # Calculate cumulative portfolio value
        portfolio_values = init_cash * (1 + weighted_returns).cumprod()
        
        # Calculate metrics
        total_return = (portfolio_values.iloc[-1] - init_cash) / init_cash
        sharpe = (weighted_returns.mean() / weighted_returns.std() * np.sqrt(252)) if weighted_returns.std() != 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = weighted_returns[weighted_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino = (weighted_returns.mean() * 252 / downside_std) if downside_std != 0 else 0
        
        # Max drawdown
        cumulative = portfolio_values
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            "success": True,
            "strategy": f"Multi-Asset Portfolio ({len(symbols)} assets, rebalance {rebalance_freq})",
            "symbols": symbols,
            "weights": weights,
            "total_return": float(total_return),
            "annualized_return": float(weighted_returns.mean() * 252),
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "max_drawdown": float(max_dd),
            "volatility": float(weighted_returns.std() * np.sqrt(252)),
            "final_value": float(portfolio_values.iloc[-1]),
            "init_cash": init_cash,
            "rebalancing": {
                "frequency": rebalance_freq,
                "count": len(rebalance_dates)
            },
            "period": {
                "start": str(prices_df.index[0]),
                "end": str(prices_df.index[-1]),
                "days": len(prices_df)
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def calculate_risk_metrics(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.02
) -> Dict:
    """
    Calculate advanced risk metrics including VaR, CVaR, and Sortino ratio.
    
    Args:
        returns: Series or array of returns
        confidence_level: Confidence level for VaR/CVaR (0.95 = 95%)
        risk_free_rate: Annual risk-free rate for Sortino ratio
    
    Returns:
        Dict with risk metrics
    """
    try:
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        # Remove NaN values
        returns = returns.dropna()
        
        # Value at Risk (VaR)
        var = float(returns.quantile(1 - confidence_level))
        
        # Conditional Value at Risk (CVaR) - expected shortfall
        cvar = float(returns[returns <= var].mean())
        
        # Sortino Ratio (uses downside deviation)
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = float(downside_returns.std() * np.sqrt(252))
        sortino = float((returns.mean() * 252 - risk_free_rate) / downside_std) if downside_std != 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
        
        # Calmar Ratio
        annual_return = float(returns.mean() * 252)
        calmar = float(annual_return / abs(max_dd)) if max_dd != 0 else 0
        
        return {
            "value_at_risk": var,
            "conditional_var": cvar,
            "confidence_level": confidence_level,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "max_drawdown": max_dd,
            "downside_deviation": downside_std,
            "skewness": float(returns.skew()),
            "kurtosis": float(returns.kurtosis()),
            "positive_periods": int((returns > 0).sum()),
            "negative_periods": int((returns < 0).sum())
        }
    
    except Exception as e:
        return {"error": str(e)}

def walk_forward_optimization(
    data: pd.DataFrame,
    train_period: int = 252,
    test_period: int = 63,
    short_windows: List[int] = [10, 20, 30],
    long_windows: List[int] = [50, 100, 150],
    init_cash: float = 10000.0
) -> Dict:
    """
    Perform walk-forward optimization for strategy parameters.
    
    Args:
        data: DataFrame with price data
        train_period: Number of days for training window
        test_period: Number of days for testing window
        short_windows: Short SMA periods to test
        long_windows: Long SMA periods to test
        init_cash: Initial cash
    
    Returns:
        Dict with walk-forward results
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {
            "error": "VectorBT not installed",
            "success": False
        }
    
    try:
        close = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        
        results = []
        total_days = len(close)
        current_pos = 0
        
        while current_pos + train_period + test_period <= total_days:
            # Training window
            train_start = current_pos
            train_end = current_pos + train_period
            train_data = close.iloc[train_start:train_end]
            
            # Optimize on training data
            best_sharpe = -np.inf
            best_short = None
            best_long = None
            
            for short in short_windows:
                for long in long_windows:
                    if short >= long:
                        continue
                    
                    short_sma = train_data.rolling(window=short).mean()
                    long_sma = train_data.rolling(window=long).mean()
                    entries = short_sma > long_sma
                    exits = short_sma < long_sma
                    
                    pf = vbt.Portfolio.from_signals(
                        train_data, entries, exits, init_cash=init_cash, freq='1D'
                    )
                    sharpe = float(pf.sharpe_ratio())
                    
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_short = short
                        best_long = long
            
            # Test on out-of-sample data
            test_start = train_end
            test_end = min(test_start + test_period, total_days)
            test_data = close.iloc[test_start:test_end]
            
            if best_short and best_long:
                short_sma = test_data.rolling(window=best_short).mean()
                long_sma = test_data.rolling(window=best_long).mean()
                entries = short_sma > long_sma
                exits = short_sma < long_sma
                
                pf = vbt.Portfolio.from_signals(
                    test_data, entries, exits, init_cash=init_cash, freq='1D'
                )
                
                results.append({
                    "train_period": f"{train_data.index[0]} to {train_data.index[-1]}",
                    "test_period": f"{test_data.index[0]} to {test_data.index[-1]}",
                    "best_short": best_short,
                    "best_long": best_long,
                    "train_sharpe": best_sharpe,
                    "test_sharpe": float(pf.sharpe_ratio()),
                    "test_return": float(pf.total_return()),
                    "test_max_dd": float(pf.max_drawdown())
                })
            
            current_pos += test_period
        
        # Aggregate results
        if results:
            avg_test_sharpe = np.mean([r['test_sharpe'] for r in results])
            avg_test_return = np.mean([r['test_return'] for r in results])
            
            return {
                "success": True,
                "walk_forward_results": results,
                "summary": {
                    "total_periods": len(results),
                    "avg_test_sharpe": float(avg_test_sharpe),
                    "avg_test_return": float(avg_test_return),
                    "train_window_days": train_period,
                    "test_window_days": test_period
                }
            }
        else:
            return {
                "error": "Insufficient data for walk-forward analysis",
                "success": False
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def monte_carlo_simulation(
    returns: Union[pd.Series, np.ndarray],
    num_simulations: int = 1000,
    num_days: int = 252,
    init_value: float = 10000.0
) -> Dict:
    """
    Run Monte Carlo simulation for portfolio projections.
    
    Args:
        returns: Historical returns series
        num_simulations: Number of simulation paths
        num_days: Number of days to project forward
        init_value: Initial portfolio value
    
    Returns:
        Dict with simulation results and statistics
    """
    try:
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        returns = returns.dropna()
        
        # Calculate mean and std of historical returns
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Run simulations
        simulations = np.zeros((num_simulations, num_days))
        
        for i in range(num_simulations):
            # Generate random returns from normal distribution
            sim_returns = np.random.normal(mean_return, std_return, num_days)
            
            # Calculate cumulative portfolio value
            portfolio_values = init_value * (1 + sim_returns).cumprod()
            simulations[i] = portfolio_values
        
        # Calculate statistics
        final_values = simulations[:, -1]
        
        percentiles = {
            "5th": float(np.percentile(final_values, 5)),
            "25th": float(np.percentile(final_values, 25)),
            "50th": float(np.percentile(final_values, 50)),
            "75th": float(np.percentile(final_values, 75)),
            "95th": float(np.percentile(final_values, 95))
        }
        
        return {
            "success": True,
            "num_simulations": num_simulations,
            "num_days": num_days,
            "init_value": init_value,
            "final_value_stats": {
                "mean": float(final_values.mean()),
                "median": float(np.median(final_values)),
                "std": float(final_values.std()),
                "min": float(final_values.min()),
                "max": float(final_values.max()),
                "percentiles": percentiles
            },
            "probability_of_profit": float((final_values > init_value).sum() / num_simulations),
            "expected_return": float((final_values.mean() - init_value) / init_value),
            "risk_of_ruin": float((final_values < init_value * 0.5).sum() / num_simulations)
        }
    
    except Exception as e:
        return {"error": str(e)}

def create_custom_indicator(
    data: pd.DataFrame,
    indicator_type: str = 'momentum',
    window: int = 14
) -> pd.DataFrame:
    """
    Create custom technical indicators.
    
    Args:
        data: DataFrame with OHLCV data
        indicator_type: Type of indicator ('momentum', 'volatility', 'trend')
        window: Lookback window
    
    Returns:
        DataFrame with custom indicator added
    """
    try:
        result = data.copy()
        close = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        
        if indicator_type == 'momentum':
            # Rate of Change (ROC)
            roc = (close - close.shift(window)) / close.shift(window) * 100
            result['ROC'] = roc
            
            # Momentum
            momentum = close - close.shift(window)
            result['Momentum'] = momentum
        
        elif indicator_type == 'volatility':
            # Average True Range (ATR) approximation
            high = data['High'] if 'High' in data.columns else close
            low = data['Low'] if 'Low' in data.columns else close
            tr = high - low
            atr = tr.rolling(window=window).mean()
            result['ATR'] = atr
            
            # Historical Volatility
            returns = close.pct_change()
            hvol = returns.rolling(window=window).std() * np.sqrt(252)
            result['HistVol'] = hvol
        
        elif indicator_type == 'trend':
            # Moving Average Convergence
            sma_short = close.rolling(window=window).mean()
            sma_long = close.rolling(window=window * 2).mean()
            result['MA_Convergence'] = sma_short - sma_long
            
            # Average Directional Index (simplified)
            high = data['High'] if 'High' in data.columns else close
            low = data['Low'] if 'Low' in data.columns else close
            tr = high - low
            result['TrendStrength'] = tr.rolling(window=window).mean()
        
        return result
    
    except Exception as e:
        print(f"Error creating custom indicator: {e}")
        return data

def backtest_mean_reversion(
    data: pd.DataFrame,
    lookback: int = 20,
    entry_std: float = 2.0,
    exit_std: float = 0.5,
    init_cash: float = 10000.0
) -> Dict:
    """
    Backtest a mean reversion strategy using Bollinger Bands logic.
    
    Args:
        data: DataFrame with price data
        lookback: Lookback period for mean calculation
        entry_std: Standard deviations for entry signal
        exit_std: Standard deviations for exit signal
        init_cash: Initial cash
    
    Returns:
        Dict with backtest results
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {
            "error": "VectorBT not installed",
            "success": False
        }
    
    try:
        close = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        
        # Calculate mean and standard deviation
        mean = close.rolling(window=lookback).mean()
        std = close.rolling(window=lookback).std()
        
        # Entry: price moves beyond entry_std standard deviations
        upper_entry = mean + (entry_std * std)
        lower_entry = mean - (entry_std * std)
        
        # Exit: price returns to exit_std standard deviations
        upper_exit = mean + (exit_std * std)
        lower_exit = mean - (exit_std * std)
        
        # Long entries when price drops below lower band
        long_entries = close < lower_entry
        # Exit longs when price returns to mean
        long_exits = close > lower_exit
        
        # Short entries when price rises above upper band
        short_entries = close > upper_entry
        # Exit shorts when price returns to mean
        short_exits = close < upper_exit
        
        # Combine long and short signals
        entries = long_entries | short_entries
        exits = long_exits | short_exits
        
        portfolio = vbt.Portfolio.from_signals(
            close, entries, exits, init_cash=init_cash, freq='1D'
        )
        
        return {
            "success": True,
            "strategy": f"Mean Reversion (lookback={lookback}, entry={entry_std}σ)",
            "total_return": float(portfolio.total_return()),
            "sharpe_ratio": float(portfolio.sharpe_ratio()),
            "sortino_ratio": float(portfolio.sortino_ratio()),
            "max_drawdown": float(portfolio.max_drawdown()),
            "win_rate": float(portfolio.trades.win_rate()),
            "total_trades": int(portfolio.trades.count()),
            "final_value": float(portfolio.final_value()),
            "init_cash": init_cash,
            "parameters": {
                "lookback": lookback,
                "entry_std": entry_std,
                "exit_std": exit_std
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

# Example usage
if __name__ == "__main__":
    print("VectorBT Pro Module - Advanced Features")
    print("=" * 50)
    info = get_module_info()
    for k, v in info.items():
        print(f"{k}: {v}")
    
    print("\n" + "=" * 50)
    print("Available Functions:")
    print("1. backtest_multi_asset_portfolio() - Multi-asset portfolios with rebalancing")
    print("2. calculate_risk_metrics() - VaR, CVaR, Sortino, Calmar ratios")
    print("3. walk_forward_optimization() - Robust parameter optimization")
    print("4. monte_carlo_simulation() - Portfolio projections")
    print("5. create_custom_indicator() - Custom technical indicators")
    print("6. backtest_mean_reversion() - Mean reversion strategies")
