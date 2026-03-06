"""
VectorBT Backtesting Module

VectorBT is an open-source Python library for backtesting and analyzing trading strategies
at scale using vectorized operations. It enables rapid prototyping of quantitative models
with factor analysis and ML integrations for alpha generation.

Category: Quant Tools & ML
Data Type: Library
Free Tier: True (fully open source)
Update Frequency: N/A (library)
Relevance Score: 9/10
Integration Ease: 8/10

Installation:
    pip install vectorbt

Documentation: https://vectorbt.dev/
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

def get_library_info() -> Dict:
    """Get information about the VectorBT library."""
    try:
        import vectorbt as vbt
        version = vbt.__version__
    except ImportError:
        version = "Not installed"
    
    return {
        "name": "VectorBT",
        "version": version,
        "category": "Quant Tools & ML",
        "description": "Open-source backtesting library with vectorized operations",
        "license": "Apache 2.0",
        "documentation": "https://vectorbt.dev/",
        "github": "https://github.com/polakowo/vectorbt",
        "installation": "pip install vectorbt",
        "key_features": [
            "Vectorized backtesting",
            "Portfolio optimization",
            "Technical indicators",
            "Performance metrics",
            "Machine learning integration",
            "Custom strategy creation"
        ]
    }

def run_simple_sma_backtest(
    data: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 50,
    init_cash: float = 10000.0
) -> Dict:
    """
    Run a simple SMA crossover backtest.
    
    Args:
        data: DataFrame with OHLCV price data (must have 'Close' column)
        short_window: Short SMA period
        long_window: Long SMA period
        init_cash: Initial cash for the portfolio
    
    Returns:
        Dict with backtest results including returns, sharpe, drawdown
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {
            "error": "VectorBT not installed. Run: pip install vectorbt",
            "success": False
        }
    
    try:
        # Calculate SMAs
        close_prices = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        short_sma = close_prices.rolling(window=short_window).mean()
        long_sma = close_prices.rolling(window=long_window).mean()
        
        # Generate signals
        entries = short_sma > long_sma
        exits = short_sma < long_sma
        
        # Run backtest
        portfolio = vbt.Portfolio.from_signals(
            close_prices,
            entries,
            exits,
            init_cash=init_cash,
            freq='1D'
        )
        
        # Extract key metrics
        return {
            "success": True,
            "strategy": f"SMA Crossover ({short_window}/{long_window})",
            "total_return": float(portfolio.total_return()),
            "sharpe_ratio": float(portfolio.sharpe_ratio()),
            "max_drawdown": float(portfolio.max_drawdown()),
            "win_rate": float(portfolio.trades.win_rate()),
            "total_trades": int(portfolio.trades.count()),
            "final_value": float(portfolio.final_value()),
            "init_cash": init_cash,
            "period": {
                "start": str(close_prices.index[0]),
                "end": str(close_prices.index[-1]),
                "days": len(close_prices)
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def calculate_technical_indicators(
    data: pd.DataFrame,
    indicators: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate technical indicators using VectorBT.
    
    Args:
        data: DataFrame with OHLCV data
        indicators: List of indicators to calculate. Defaults to ['RSI', 'MACD', 'BB']
    
    Returns:
        DataFrame with original data and calculated indicators
    """
    try:
        import vectorbt as vbt
    except ImportError:
        print("VectorBT not installed. Run: pip install vectorbt")
        return data
    
    if indicators is None:
        indicators = ['RSI', 'MACD', 'BB']
    
    result = data.copy()
    close = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
    
    try:
        if 'RSI' in indicators:
            rsi = vbt.RSI.run(close, window=14)
            result['RSI'] = rsi.rsi
        
        if 'MACD' in indicators:
            macd = vbt.MACD.run(close, fast_window=12, slow_window=26, signal_window=9)
            result['MACD'] = macd.macd
            result['MACD_signal'] = macd.signal
            result['MACD_hist'] = macd.hist
        
        if 'BB' in indicators:
            bb = vbt.BBANDS.run(close, window=20, alpha=2)
            result['BB_upper'] = bb.upper
            result['BB_middle'] = bb.middle
            result['BB_lower'] = bb.lower
        
        return result
    
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return data

def optimize_strategy_parameters(
    data: pd.DataFrame,
    short_windows: List[int] = [10, 20, 30],
    long_windows: List[int] = [50, 100, 150],
    init_cash: float = 10000.0
) -> Dict:
    """
    Optimize SMA crossover parameters using grid search.
    
    Args:
        data: DataFrame with price data
        short_windows: List of short SMA periods to test
        long_windows: List of long SMA periods to test
        init_cash: Initial cash
    
    Returns:
        Dict with best parameters and performance metrics
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
        best_sharpe = -np.inf
        best_params = {}
        results = []
        
        for short in short_windows:
            for long in long_windows:
                if short >= long:
                    continue
                
                short_sma = close.rolling(window=short).mean()
                long_sma = close.rolling(window=long).mean()
                entries = short_sma > long_sma
                exits = short_sma < long_sma
                
                pf = vbt.Portfolio.from_signals(
                    close, entries, exits, init_cash=init_cash, freq='1D'
                )
                
                sharpe = float(pf.sharpe_ratio())
                total_return = float(pf.total_return())
                
                result = {
                    "short_window": short,
                    "long_window": long,
                    "sharpe_ratio": sharpe,
                    "total_return": total_return,
                    "max_drawdown": float(pf.max_drawdown())
                }
                results.append(result)
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = result
        
        return {
            "success": True,
            "best_parameters": best_params,
            "all_results": sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10],
            "search_space": {
                "short_windows": short_windows,
                "long_windows": long_windows,
                "combinations_tested": len(results)
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def get_portfolio_metrics(
    returns: Union[pd.Series, np.ndarray],
    freq: str = '1D'
) -> Dict:
    """
    Calculate comprehensive portfolio metrics.
    
    Args:
        returns: Series or array of portfolio returns
        freq: Frequency of returns ('1D' for daily, '1H' for hourly, etc.)
    
    Returns:
        Dict with performance metrics
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {"error": "VectorBT not installed"}
    
    try:
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        # Create a portfolio object from returns
        portfolio = vbt.Portfolio.from_orders(
            close=returns.cumsum() + 100,  # Simple price series from returns
            size=0,  # No orders, just metrics
            freq=freq
        )
        
        return {
            "total_return": float(returns.sum()),
            "annualized_return": float(returns.mean() * 252),  # Assuming daily
            "volatility": float(returns.std() * np.sqrt(252)),
            "sharpe_ratio": float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0,
            "max_drawdown": float((returns.cumsum() - returns.cumsum().cummax()).min()),
            "win_rate": float((returns > 0).sum() / len(returns)),
            "positive_periods": int((returns > 0).sum()),
            "negative_periods": int((returns < 0).sum()),
            "total_periods": len(returns)
        }
    
    except Exception as e:
        return {"error": str(e)}

def backtest_buy_and_hold(
    data: pd.DataFrame,
    init_cash: float = 10000.0
) -> Dict:
    """
    Run a simple buy-and-hold benchmark backtest.
    
    Args:
        data: DataFrame with price data
        init_cash: Initial cash
    
    Returns:
        Dict with benchmark performance
    """
    try:
        import vectorbt as vbt
    except ImportError:
        return {"error": "VectorBT not installed"}
    
    try:
        close = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        
        # Buy at start, hold till end
        entries = pd.Series(False, index=close.index)
        entries.iloc[0] = True
        exits = pd.Series(False, index=close.index)
        
        portfolio = vbt.Portfolio.from_signals(
            close, entries, exits, init_cash=init_cash, freq='1D'
        )
        
        return {
            "success": True,
            "strategy": "Buy and Hold",
            "total_return": float(portfolio.total_return()),
            "sharpe_ratio": float(portfolio.sharpe_ratio()),
            "max_drawdown": float(portfolio.max_drawdown()),
            "final_value": float(portfolio.final_value()),
            "init_cash": init_cash
        }
    
    except Exception as e:
        return {"error": str(e)}

# Example usage and tests
if __name__ == "__main__":
    print("VectorBT Module - Library Info:")
    print("=" * 50)
    info = get_library_info()
    for k, v in info.items():
        print(f"{k}: {v}")
    
    print("\n" + "=" * 50)
    print("To use VectorBT in your strategies:")
    print("1. pip install vectorbt")
    print("2. Import the module and run backtests")
    print("3. See functions: run_simple_sma_backtest(), optimize_strategy_parameters()")
    print("\nExample:")
    print("  result = run_simple_sma_backtest(price_data, short_window=20, long_window=50)")
    print("  print(result)")
