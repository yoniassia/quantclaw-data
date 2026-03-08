"""
Backtrader Framework — Backtesting & Strategy Analysis Toolkit

Source: backtrader (open-source, pip install backtrader)
Category: Quant Tools & ML
Free: Yes (fully open source, no API key)
Update frequency: User-defined (typically daily)

Provides:
- Run backtests on any OHLCV data (pandas DataFrame or Yahoo feed)
- Built-in strategy templates (SMA crossover, RSI mean-reversion, etc.)
- Performance metrics: Sharpe, CAGR, max drawdown, win rate
- Trade log extraction
- Multi-strategy comparison
- Walk-forward / parameter sweep utilities

Usage:
    from modules.backtrader_framework import *
    result = run_sma_crossover_backtest("AAPL", period_fast=10, period_slow=30)
    metrics = get_strategy_metrics(result)
"""

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.analyzers as btanalyzers
import pandas as pd
import json
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/backtrader")
os.makedirs(CACHE_DIR, exist_ok=True)


# ──────────────────────────── Strategy Templates ────────────────────────────

class SMACrossover(bt.Strategy):
    """Simple Moving Average crossover strategy."""
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        elif self.crossover < 0:
            self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


class RSIMeanReversion(bt.Strategy):
    """RSI-based mean reversion: buy oversold, sell overbought."""
    params = (
        ("rsi_period", 14),
        ("oversold", 30),
        ("overbought", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsi < self.p.oversold:
                self.order = self.buy()
        elif self.rsi > self.p.overbought:
            self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


class BollingerBandStrategy(bt.Strategy):
    """Bollinger Band mean-reversion strategy."""
    params = (
        ("bb_period", 20),
        ("devfactor", 2.0),
    )

    def __init__(self):
        self.bband = bt.indicators.BollingerBands(
            self.data.close, period=self.p.bb_period, devfactor=self.p.devfactor
        )
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.data.close[0] < self.bband.lines.bot[0]:
                self.order = self.buy()
        elif self.data.close[0] > self.bband.lines.top[0]:
            self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


class MACDStrategy(bt.Strategy):
    """MACD crossover strategy."""
    params = (
        ("fast_ema", 12),
        ("slow_ema", 26),
        ("signal_period", 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_ema,
            period_me2=self.p.slow_ema,
            period_signal=self.p.signal_period,
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        elif self.crossover < 0:
            self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


STRATEGY_REGISTRY = {
    "sma_crossover": SMACrossover,
    "rsi_mean_reversion": RSIMeanReversion,
    "bollinger_band": BollingerBandStrategy,
    "macd": MACDStrategy,
}


# ──────────────────────────── Core Engine ────────────────────────────

def _build_cerebro(
    strategy_cls: type,
    data_feed: bt.feeds.DataBase,
    cash: float = 100000.0,
    commission: float = 0.001,
    strategy_params: Optional[Dict] = None,
) -> bt.Cerebro:
    """
    Internal helper: wire up a Cerebro engine with analyzers.
    """
    cerebro = bt.Cerebro()
    params = strategy_params or {}
    cerebro.addstrategy(strategy_cls, **params)
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)

    # Standard analyzers
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="sharpe", riskfreerate=0.04)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
    cerebro.addanalyzer(btanalyzers.SQN, _name="sqn")

    return cerebro


def _extract_metrics(strategy) -> Dict:
    """
    Pull analyzer results into a clean dict.
    """
    metrics = {}

    # Sharpe
    try:
        sharpe = strategy.analyzers.sharpe.get_analysis()
        metrics["sharpe_ratio"] = round(sharpe.get("sharperatio", 0) or 0, 4)
    except Exception:
        metrics["sharpe_ratio"] = None

    # Drawdown
    try:
        dd = strategy.analyzers.drawdown.get_analysis()
        metrics["max_drawdown_pct"] = round(dd.max.drawdown, 2)
        metrics["max_drawdown_len"] = dd.max.len
    except Exception:
        metrics["max_drawdown_pct"] = None
        metrics["max_drawdown_len"] = None

    # Returns
    try:
        ret = strategy.analyzers.returns.get_analysis()
        metrics["total_return_pct"] = round(ret.get("rtot", 0) * 100, 4)
    except Exception:
        metrics["total_return_pct"] = None

    # SQN
    try:
        sqn = strategy.analyzers.sqn.get_analysis()
        metrics["sqn"] = round(sqn.get("sqn", 0) or 0, 4)
    except Exception:
        metrics["sqn"] = None

    # Trade stats
    try:
        ta = strategy.analyzers.trades.get_analysis()
        total = ta.get("total", {}).get("total", 0)
        won = ta.get("won", {}).get("total", 0)
        lost = ta.get("lost", {}).get("total", 0)
        metrics["total_trades"] = total
        metrics["won"] = won
        metrics["lost"] = lost
        metrics["win_rate"] = round(won / total * 100, 2) if total > 0 else 0
        # PnL
        metrics["avg_win"] = round(ta.get("won", {}).get("pnl", {}).get("average", 0) or 0, 2)
        metrics["avg_loss"] = round(ta.get("lost", {}).get("pnl", {}).get("average", 0) or 0, 2)
        metrics["total_pnl"] = round(
            (ta.get("won", {}).get("pnl", {}).get("total", 0) or 0)
            + (ta.get("lost", {}).get("pnl", {}).get("total", 0) or 0), 2
        )
    except Exception:
        metrics["total_trades"] = 0
        metrics["win_rate"] = 0

    return metrics


def _df_to_feed(df: pd.DataFrame, name: str = "data") -> bt.feeds.PandasData:
    """
    Convert a pandas DataFrame (with Date/Open/High/Low/Close/Volume columns)
    into a backtrader PandasData feed.
    """
    df = df.copy()
    # Normalize column names
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("date", "datetime", "timestamp"):
            col_map[c] = "Date"
        elif cl == "open":
            col_map[c] = "Open"
        elif cl == "high":
            col_map[c] = "High"
        elif cl == "low":
            col_map[c] = "Low"
        elif cl in ("close", "adj close"):
            col_map[c] = "Close"
        elif cl == "volume":
            col_map[c] = "Volume"
    df.rename(columns=col_map, inplace=True)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)

    return bt.feeds.PandasData(dataname=df, name=name)


# ──────────────────────────── Public API ────────────────────────────

def list_strategies() -> List[Dict]:
    """
    List all available built-in strategy templates.

    Returns:
        List of dicts with strategy name, description, and default params.
    """
    result = []
    for name, cls in STRATEGY_REGISTRY.items():
        params = {p: getattr(cls.params, p) for p in cls.params._getkeys()}
        result.append({
            "name": name,
            "class": cls.__name__,
            "description": cls.__doc__.strip() if cls.__doc__ else "",
            "default_params": params,
        })
    return result


def run_backtest_from_df(
    df: pd.DataFrame,
    strategy: str = "sma_crossover",
    cash: float = 100000.0,
    commission: float = 0.001,
    strategy_params: Optional[Dict] = None,
) -> Dict:
    """
    Run a backtest on a pandas DataFrame of OHLCV data.

    Args:
        df: DataFrame with Date, Open, High, Low, Close, Volume columns.
        strategy: Strategy name from registry (sma_crossover, rsi_mean_reversion, etc.)
        cash: Starting cash.
        commission: Per-trade commission rate.
        strategy_params: Override default strategy parameters.

    Returns:
        Dict with starting_cash, ending_cash, return_pct, and detailed metrics.
    """
    if strategy not in STRATEGY_REGISTRY:
        return {"error": f"Unknown strategy '{strategy}'. Available: {list(STRATEGY_REGISTRY.keys())}"}

    try:
        feed = _df_to_feed(df)
        cerebro = _build_cerebro(
            STRATEGY_REGISTRY[strategy], feed, cash, commission, strategy_params
        )
        results = cerebro.run()
        strat = results[0]

        ending = cerebro.broker.getvalue()
        metrics = _extract_metrics(strat)
        metrics.update({
            "strategy": strategy,
            "starting_cash": cash,
            "ending_value": round(ending, 2),
            "return_pct": round((ending - cash) / cash * 100, 4),
            "commission": commission,
        })
        return metrics
    except Exception as e:
        return {"error": str(e), "strategy": strategy}


def run_yahoo_backtest(
    ticker: str,
    strategy: str = "sma_crossover",
    start: Optional[str] = None,
    end: Optional[str] = None,
    cash: float = 100000.0,
    commission: float = 0.001,
    strategy_params: Optional[Dict] = None,
) -> Dict:
    """
    Run a backtest using Yahoo Finance data (via yfinance).

    Args:
        ticker: Stock ticker (e.g. 'AAPL', 'SPY').
        strategy: Strategy name from registry.
        start: Start date 'YYYY-MM-DD' (default: 2 years ago).
        end: End date 'YYYY-MM-DD' (default: today).
        cash: Starting cash.
        commission: Per-trade commission rate.
        strategy_params: Override default strategy parameters.

    Returns:
        Dict with backtest metrics.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed. Run: pip install yfinance"}

    if not start:
        start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")

    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return {"error": f"No data for ticker '{ticker}'"}
        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        result = run_backtest_from_df(df, strategy, cash, commission, strategy_params)
        result["ticker"] = ticker
        result["period"] = f"{start} to {end}"
        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def run_sma_crossover_backtest(
    ticker: str,
    period_fast: int = 10,
    period_slow: int = 30,
    cash: float = 100000.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict:
    """
    Convenience: run SMA crossover backtest on a Yahoo ticker.

    Args:
        ticker: Stock ticker.
        period_fast: Fast SMA period.
        period_slow: Slow SMA period.
        cash: Starting cash.

    Returns:
        Dict with backtest results.
    """
    return run_yahoo_backtest(
        ticker, "sma_crossover", start, end, cash,
        strategy_params={"fast_period": period_fast, "slow_period": period_slow},
    )


def compare_strategies(
    ticker: str,
    strategies: Optional[List[str]] = None,
    cash: float = 100000.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Dict]:
    """
    Compare multiple strategies on the same ticker.

    Args:
        ticker: Stock ticker.
        strategies: List of strategy names. Default: all registered.
        cash: Starting cash.

    Returns:
        List of dicts sorted by return_pct descending.
    """
    if strategies is None:
        strategies = list(STRATEGY_REGISTRY.keys())

    results = []
    for strat_name in strategies:
        res = run_yahoo_backtest(ticker, strat_name, start, end, cash)
        results.append(res)

    # Sort by return
    results.sort(key=lambda x: x.get("return_pct", -9999), reverse=True)
    return results


def parameter_sweep(
    ticker: str,
    strategy: str = "sma_crossover",
    param_grid: Optional[Dict[str, List]] = None,
    cash: float = 100000.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Dict]:
    """
    Sweep strategy parameters and rank by return.

    Args:
        ticker: Stock ticker.
        strategy: Strategy name.
        param_grid: Dict of param_name -> list of values.
            e.g. {"fast_period": [5, 10, 15], "slow_period": [20, 30, 50]}
        cash: Starting cash.

    Returns:
        List of results sorted by return_pct descending.
    """
    if param_grid is None:
        if strategy == "sma_crossover":
            param_grid = {"fast_period": [5, 10, 20], "slow_period": [20, 40, 60]}
        elif strategy == "rsi_mean_reversion":
            param_grid = {"rsi_period": [7, 14, 21], "oversold": [25, 30], "overbought": [70, 75]}
        else:
            return [{"error": "Provide param_grid for this strategy"}]

    # Build all combos
    import itertools
    keys = list(param_grid.keys())
    combos = list(itertools.product(*[param_grid[k] for k in keys]))

    results = []
    for combo in combos:
        params = dict(zip(keys, combo))
        res = run_yahoo_backtest(ticker, strategy, start, end, cash, strategy_params=params)
        res["params"] = params
        results.append(res)

    results.sort(key=lambda x: x.get("return_pct", -9999), reverse=True)
    return results


def generate_sample_data(
    ticker: str = "SAMPLE",
    days: int = 500,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0003,
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing without external dependencies.

    Args:
        ticker: Ticker label.
        days: Number of trading days.
        start_price: Starting price.
        volatility: Daily return std deviation.
        trend: Daily drift (positive = uptrend).

    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume.
    """
    import random
    random.seed(42)
    rows = []
    price = start_price
    base_date = datetime(2023, 1, 3)

    for i in range(days):
        ret = random.gauss(trend, volatility)
        o = price
        c = price * (1 + ret)
        h = max(o, c) * (1 + abs(random.gauss(0, volatility * 0.5)))
        l = min(o, c) * (1 - abs(random.gauss(0, volatility * 0.5)))
        v = int(random.gauss(1_000_000, 300_000))
        rows.append({
            "Date": base_date + timedelta(days=i),
            "Open": round(o, 2),
            "High": round(h, 2),
            "Low": round(l, 2),
            "Close": round(c, 2),
            "Volume": max(v, 100_000),
        })
        price = c

    return pd.DataFrame(rows)


def get_available_indicators() -> List[Dict]:
    """
    List commonly available backtrader indicators.

    Returns:
        List of dicts with indicator name and category.
    """
    indicators = [
        {"name": "SMA", "full": "Simple Moving Average", "category": "trend"},
        {"name": "EMA", "full": "Exponential Moving Average", "category": "trend"},
        {"name": "WMA", "full": "Weighted Moving Average", "category": "trend"},
        {"name": "DEMA", "full": "Double Exponential Moving Average", "category": "trend"},
        {"name": "RSI", "full": "Relative Strength Index", "category": "momentum"},
        {"name": "MACD", "full": "Moving Average Convergence Divergence", "category": "momentum"},
        {"name": "Stochastic", "full": "Stochastic Oscillator", "category": "momentum"},
        {"name": "CCI", "full": "Commodity Channel Index", "category": "momentum"},
        {"name": "Williams %R", "full": "Williams Percent Range", "category": "momentum"},
        {"name": "BollingerBands", "full": "Bollinger Bands", "category": "volatility"},
        {"name": "ATR", "full": "Average True Range", "category": "volatility"},
        {"name": "ADX", "full": "Average Directional Index", "category": "trend_strength"},
        {"name": "OBV", "full": "On Balance Volume", "category": "volume"},
        {"name": "VWAP", "full": "Volume Weighted Average Price", "category": "volume"},
        {"name": "ParabolicSAR", "full": "Parabolic Stop and Reverse", "category": "trend"},
        {"name": "Ichimoku", "full": "Ichimoku Kinko Hyo", "category": "trend"},
        {"name": "CrossOver", "full": "Crossover Signal", "category": "signal"},
        {"name": "CrossDown", "full": "Cross Down Signal", "category": "signal"},
        {"name": "CrossUp", "full": "Cross Up Signal", "category": "signal"},
    ]
    return indicators


def get_backtrader_info() -> Dict:
    """
    Return backtrader version and module metadata.
    """
    return {
        "module": "backtrader_framework",
        "backtrader_version": bt.__version__,
        "strategies_available": list(STRATEGY_REGISTRY.keys()),
        "strategy_count": len(STRATEGY_REGISTRY),
        "source": "https://www.backtrader.com/docu/",
        "category": "Quant Tools & ML",
        "free_tier": True,
        "status": "active",
    }


if __name__ == "__main__":
    print(json.dumps(get_backtrader_info(), indent=2))
