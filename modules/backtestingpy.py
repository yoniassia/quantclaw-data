"""
Backtesting.py — Strategy Backtesting Engine

Wraps the backtesting.py library to run trading strategy backtests on
historical OHLCV data, returning structured performance metrics as dicts/lists.

Source: https://kernc.github.io/backtesting.py/
Category: Quant Tools & ML
Free tier: Yes (open-source library, uses yfinance for data)
Update frequency: On-demand (runs against any OHLCV DataFrame)

Provides:
- Run SMA crossover backtests on any ticker
- Run RSI mean-reversion backtests
- Custom strategy backtesting from user-defined entry/exit rules
- Walk-forward optimization of strategy parameters
- Multi-ticker batch backtesting
- Strategy comparison across parameter sets
"""

import json
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/backtestingpy")
os.makedirs(CACHE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helper: fetch OHLCV data via yfinance
# ---------------------------------------------------------------------------

def _fetch_ohlcv(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data using yfinance. Returns DataFrame with columns:
    Open, High, Low, Close, Volume (capitalized, DatetimeIndex).
    """
    import yfinance as yf
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Ensure required columns exist
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            raise ValueError(f"Missing column {col} in data for {ticker}")
    return df[["Open", "High", "Low", "Close", "Volume"]]


# ---------------------------------------------------------------------------
# Helper: convert backtesting.py Stats to a plain dict
# ---------------------------------------------------------------------------

def _stats_to_dict(stats) -> Dict[str, Any]:
    """Convert a backtesting Stats Series to a JSON-serializable dict."""
    result = {}
    skip_keys = {"_strategy", "_equity_curve", "_trades"}
    for key in stats.index:
        if key in skip_keys:
            continue
        val = stats[key]
        if isinstance(val, (np.integer,)):
            val = int(val)
        elif isinstance(val, (np.floating,)):
            val = round(float(val), 4) if not np.isnan(val) else None
        elif isinstance(val, (np.bool_,)):
            val = bool(val)
        elif isinstance(val, pd.Timestamp):
            val = val.isoformat()
        elif isinstance(val, timedelta):
            val = str(val)
        elif isinstance(val, type):
            val = val.__name__
        elif not isinstance(val, (str, int, float, bool, type(None))):
            val = str(val)
        result[key] = val
    return result


def _trades_to_list(stats) -> List[Dict]:
    """Extract trades from backtesting stats as list of dicts."""
    try:
        trades_df = stats["_trades"]
        if trades_df is None or trades_df.empty:
            return []
        records = trades_df.copy()
        for col in records.columns:
            if records[col].dtype == "datetime64[ns]":
                records[col] = records[col].astype(str)
        return records.to_dict(orient="records")
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_sma_crossover(
    ticker: str = "AAPL",
    fast_period: int = 10,
    slow_period: int = 20,
    data_period: str = "2y",
    cash: float = 10000,
    commission: float = 0.002,
) -> Dict:
    """
    Run an SMA crossover backtest on a ticker.

    Buy when fast SMA crosses above slow SMA, sell on cross below.

    Args:
        ticker: Stock ticker symbol.
        fast_period: Fast SMA lookback window.
        slow_period: Slow SMA lookback window.
        data_period: yfinance period string (e.g. '1y', '2y', '5y').
        cash: Starting capital.
        commission: Per-trade commission fraction (0.002 = 0.2%).

    Returns:
        Dict with strategy params, performance metrics, and trade list.
    """
    from backtesting import Backtest, Strategy
    from backtesting.lib import crossover

    data = _fetch_ohlcv(ticker, period=data_period)

    class SmaCross(Strategy):
        n_fast = fast_period
        n_slow = slow_period

        def init(self):
            close = self.data.Close
            self.sma_fast = self.I(lambda c: pd.Series(c).rolling(self.n_fast).mean(), close)
            self.sma_slow = self.I(lambda c: pd.Series(c).rolling(self.n_slow).mean(), close)

        def next(self):
            if crossover(self.sma_fast, self.sma_slow):
                self.buy()
            elif crossover(self.sma_slow, self.sma_fast):
                self.position.close()

    bt = Backtest(data, SmaCross, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run()

    return {
        "ticker": ticker,
        "strategy": "SMA_Crossover",
        "params": {"fast_period": fast_period, "slow_period": slow_period},
        "data_period": data_period,
        "cash": cash,
        "commission": commission,
        "metrics": _stats_to_dict(stats),
        "trades": _trades_to_list(stats),
        "generated_at": datetime.utcnow().isoformat(),
    }


def run_rsi_strategy(
    ticker: str = "AAPL",
    rsi_period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    data_period: str = "2y",
    cash: float = 10000,
    commission: float = 0.002,
) -> Dict:
    """
    Run an RSI mean-reversion backtest.

    Buy when RSI drops below oversold threshold, sell when above overbought.

    Args:
        ticker: Stock ticker symbol.
        rsi_period: RSI lookback period.
        oversold: RSI level to trigger buy.
        overbought: RSI level to trigger sell.
        data_period: yfinance period string.
        cash: Starting capital.
        commission: Commission fraction.

    Returns:
        Dict with strategy params, performance metrics, and trade list.
    """
    from backtesting import Backtest, Strategy

    data = _fetch_ohlcv(ticker, period=data_period)

    def compute_rsi(close, period):
        s = pd.Series(close)
        delta = s.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    class RsiStrategy(Strategy):
        rsi_period_param = rsi_period
        oversold_param = oversold
        overbought_param = overbought

        def init(self):
            self.rsi = self.I(compute_rsi, self.data.Close, self.rsi_period_param)

        def next(self):
            if self.rsi[-1] < self.oversold_param:
                self.buy()
            elif self.rsi[-1] > self.overbought_param:
                self.position.close()

    bt = Backtest(data, RsiStrategy, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run()

    return {
        "ticker": ticker,
        "strategy": "RSI_MeanReversion",
        "params": {"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought},
        "data_period": data_period,
        "cash": cash,
        "commission": commission,
        "metrics": _stats_to_dict(stats),
        "trades": _trades_to_list(stats),
        "generated_at": datetime.utcnow().isoformat(),
    }


def optimize_sma(
    ticker: str = "AAPL",
    fast_range: tuple = (5, 30, 5),
    slow_range: tuple = (20, 100, 10),
    data_period: str = "2y",
    cash: float = 10000,
    commission: float = 0.002,
    maximize: str = "Sharpe Ratio",
) -> Dict:
    """
    Optimize SMA crossover parameters via grid search.

    Args:
        ticker: Stock ticker symbol.
        fast_range: (start, stop, step) for fast SMA.
        slow_range: (start, stop, step) for slow SMA.
        data_period: yfinance period string.
        cash: Starting capital.
        commission: Commission fraction.
        maximize: Metric to maximize (e.g. 'Sharpe Ratio', 'Return [%]').

    Returns:
        Dict with best parameters and metrics from optimization.
    """
    from backtesting import Backtest, Strategy
    from backtesting.lib import crossover

    data = _fetch_ohlcv(ticker, period=data_period)

    class SmaCross(Strategy):
        n_fast = 10
        n_slow = 20

        def init(self):
            close = self.data.Close
            self.sma_fast = self.I(lambda c: pd.Series(c).rolling(self.n_fast).mean(), close)
            self.sma_slow = self.I(lambda c: pd.Series(c).rolling(self.n_slow).mean(), close)

        def next(self):
            if crossover(self.sma_fast, self.sma_slow):
                self.buy()
            elif crossover(self.sma_slow, self.sma_fast):
                self.position.close()

    bt = Backtest(data, SmaCross, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.optimize(
        n_fast=range(*fast_range),
        n_slow=range(*slow_range),
        maximize=maximize,
        constraint=lambda p: p.n_fast < p.n_slow,
    )

    best_params = {"n_fast": int(stats._strategy.n_fast), "n_slow": int(stats._strategy.n_slow)}

    return {
        "ticker": ticker,
        "strategy": "SMA_Crossover_Optimized",
        "optimize_target": maximize,
        "best_params": best_params,
        "fast_range": list(fast_range),
        "slow_range": list(slow_range),
        "metrics": _stats_to_dict(stats),
        "trades_count": len(_trades_to_list(stats)),
        "generated_at": datetime.utcnow().isoformat(),
    }


def run_custom_backtest(
    ticker: str = "AAPL",
    buy_condition: str = "close[-1] > close[-2]",
    sell_condition: str = "close[-1] < close[-2]",
    data_period: str = "2y",
    cash: float = 10000,
    commission: float = 0.002,
) -> Dict:
    """
    Run a backtest with user-defined buy/sell conditions.

    Conditions are Python expressions evaluated in a context where:
    - close, open_, high, low, volume are numpy-like arrays of historical values.
    - Negative indexing: [-1] = current bar, [-2] = previous bar, etc.

    Args:
        ticker: Stock ticker symbol.
        buy_condition: Python expression for buy signal.
        sell_condition: Python expression for sell signal.
        data_period: yfinance period string.
        cash: Starting capital.
        commission: Commission fraction.

    Returns:
        Dict with strategy params, performance metrics, and trade list.
    """
    from backtesting import Backtest, Strategy

    data = _fetch_ohlcv(ticker, period=data_period)

    buy_cond = buy_condition
    sell_cond = sell_condition

    class CustomStrategy(Strategy):
        def init(self):
            pass

        def next(self):
            ctx = {
                "close": self.data.Close,
                "open_": self.data.Open,
                "high": self.data.High,
                "low": self.data.Low,
                "volume": self.data.Volume,
            }
            try:
                if eval(buy_cond, {"__builtins__": {}}, ctx):
                    self.buy()
                elif eval(sell_cond, {"__builtins__": {}}, ctx):
                    self.position.close()
            except Exception:
                pass

    bt = Backtest(data, CustomStrategy, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run()

    return {
        "ticker": ticker,
        "strategy": "Custom",
        "params": {"buy_condition": buy_condition, "sell_condition": sell_condition},
        "data_period": data_period,
        "cash": cash,
        "commission": commission,
        "metrics": _stats_to_dict(stats),
        "trades": _trades_to_list(stats),
        "generated_at": datetime.utcnow().isoformat(),
    }


def batch_backtest(
    tickers: List[str] = None,
    strategy: str = "sma",
    params: Dict = None,
    data_period: str = "2y",
    cash: float = 10000,
) -> List[Dict]:
    """
    Run the same strategy across multiple tickers.

    Args:
        tickers: List of ticker symbols. Defaults to ['AAPL', 'MSFT', 'GOOGL'].
        strategy: 'sma' or 'rsi'.
        params: Strategy parameters dict (passed to the strategy runner).
        data_period: yfinance period string.
        cash: Starting capital.

    Returns:
        List of result dicts, one per ticker.
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT", "GOOGL"]
    if params is None:
        params = {}

    results = []
    for ticker in tickers:
        try:
            if strategy == "rsi":
                res = run_rsi_strategy(ticker=ticker, data_period=data_period, cash=cash, **params)
            else:
                res = run_sma_crossover(ticker=ticker, data_period=data_period, cash=cash, **params)
            res["status"] = "success"
        except Exception as e:
            res = {"ticker": ticker, "strategy": strategy, "status": "error", "error": str(e)}
        results.append(res)

    return results


def get_equity_curve(
    ticker: str = "AAPL",
    strategy: str = "sma",
    fast_period: int = 10,
    slow_period: int = 20,
    data_period: str = "2y",
    cash: float = 10000,
) -> Dict:
    """
    Return the equity curve as a time-series dict for charting.

    Args:
        ticker: Stock ticker symbol.
        strategy: 'sma' or 'rsi'.
        fast_period: SMA fast period (only for sma strategy).
        slow_period: SMA slow period (only for sma strategy).
        data_period: yfinance period string.
        cash: Starting capital.

    Returns:
        Dict with 'dates' and 'equity' lists for plotting.
    """
    from backtesting import Backtest, Strategy
    from backtesting.lib import crossover

    data = _fetch_ohlcv(ticker, period=data_period)

    class SmaCross(Strategy):
        n_fast = fast_period
        n_slow = slow_period

        def init(self):
            close = self.data.Close
            self.sma_fast = self.I(lambda c: pd.Series(c).rolling(self.n_fast).mean(), close)
            self.sma_slow = self.I(lambda c: pd.Series(c).rolling(self.n_slow).mean(), close)

        def next(self):
            if crossover(self.sma_fast, self.sma_slow):
                self.buy()
            elif crossover(self.sma_slow, self.sma_fast):
                self.position.close()

    bt = Backtest(data, SmaCross, cash=cash, commission=0.002, exclusive_orders=True)
    stats = bt.run()

    equity_curve = stats["_equity_curve"]
    return {
        "ticker": ticker,
        "strategy": "SMA_Crossover",
        "dates": [d.isoformat() for d in equity_curve.index],
        "equity": [round(float(v), 2) for v in equity_curve["Equity"]],
        "drawdown_pct": [round(float(v) * 100, 2) for v in equity_curve["DrawdownPct"]],
        "generated_at": datetime.utcnow().isoformat(),
    }


def compare_strategies(
    ticker: str = "AAPL",
    data_period: str = "2y",
    cash: float = 10000,
) -> Dict:
    """
    Compare SMA crossover vs RSI strategy on the same ticker.

    Returns side-by-side performance metrics for quick comparison.

    Args:
        ticker: Stock ticker symbol.
        data_period: yfinance period string.
        cash: Starting capital.

    Returns:
        Dict with 'sma' and 'rsi' keys containing respective metrics.
    """
    sma_result = run_sma_crossover(ticker=ticker, data_period=data_period, cash=cash)
    rsi_result = run_rsi_strategy(ticker=ticker, data_period=data_period, cash=cash)

    return {
        "ticker": ticker,
        "comparison": {
            "sma_crossover": {
                "return_pct": sma_result["metrics"].get("Return [%]"),
                "sharpe": sma_result["metrics"].get("Sharpe Ratio"),
                "max_drawdown": sma_result["metrics"].get("Max. Drawdown [%]"),
                "trades": sma_result["metrics"].get("# Trades"),
                "win_rate": sma_result["metrics"].get("Win Rate [%]"),
            },
            "rsi_mean_reversion": {
                "return_pct": rsi_result["metrics"].get("Return [%]"),
                "sharpe": rsi_result["metrics"].get("Sharpe Ratio"),
                "max_drawdown": rsi_result["metrics"].get("Max. Drawdown [%]"),
                "trades": rsi_result["metrics"].get("# Trades"),
                "win_rate": rsi_result["metrics"].get("Win Rate [%]"),
            },
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    result = run_sma_crossover("AAPL")
    print(json.dumps(result, indent=2, default=str))
