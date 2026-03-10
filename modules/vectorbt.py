"""
VectorBT — Vectorized backtesting and portfolio analytics.

High-performance backtesting library using vectorized operations via NumPy/Pandas.
Supports signal-based strategies, portfolio simulation, performance metrics,
and parameter optimization. Uses Yahoo Finance for data (no API key needed).

Source: https://vectorbt.dev/
Update frequency: Static (library-based, user-driven)
Category: Quant Tools & ML
Free tier: True (open-source library)
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Optional, Union


def _ensure_vbt():
    """Lazy import vectorbt."""
    try:
        import vectorbt as vbt
        return vbt
    except ImportError:
        return None


def download_price_data(
    symbols: Union[str, list[str]],
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365,
    interval: str = "1d"
) -> dict[str, Any]:
    """
    Download OHLCV price data via VectorBT's Yahoo Finance wrapper.

    Args:
        symbols: Ticker or list of tickers (e.g., 'AAPL' or ['AAPL','MSFT'])
        start: Start date 'YYYY-MM-DD' (default: period_days ago)
        end: End date 'YYYY-MM-DD' (default: today)
        period_days: Lookback days if start not given
        interval: Bar interval ('1d','1h','1wk')

    Returns:
        dict with 'symbols', 'rows', 'columns', 'date_range', 'close_last'

    Example:
        >>> data = download_price_data('AAPL', period_days=90)
        >>> print(data['rows'], data['close_last'])
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed. pip install vectorbt"}

    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbols, start=start, end=end, interval=interval)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No data returned", "symbols": symbols}

        close_last = {}
        if isinstance(close, pd.Series):
            close_last[symbols[0]] = round(float(close.iloc[-1]), 4)
        else:
            for col in close.columns:
                close_last[col] = round(float(close[col].iloc[-1]), 4)

        return {
            "symbols": symbols,
            "rows": len(close),
            "columns": list(close.columns) if isinstance(close, pd.DataFrame) else symbols,
            "date_range": [str(close.index[0].date()), str(close.index[-1].date())],
            "close_last": close_last,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbols": symbols}


def run_sma_crossover(
    symbol: str = "AAPL",
    fast_window: int = 10,
    slow_window: int = 50,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365,
    init_cash: float = 10000.0,
    fees: float = 0.001
) -> dict[str, Any]:
    """
    Run a simple SMA crossover backtest.

    Buys when fast SMA crosses above slow SMA, sells on cross below.

    Args:
        symbol: Ticker symbol
        fast_window: Fast moving average period
        slow_window: Slow moving average period
        start: Start date 'YYYY-MM-DD'
        end: End date 'YYYY-MM-DD'
        period_days: Lookback if start not given
        init_cash: Starting capital
        fees: Trading fee fraction (0.001 = 0.1%)

    Returns:
        dict with strategy performance metrics

    Example:
        >>> result = run_sma_crossover('AAPL', fast_window=10, slow_window=30)
        >>> print(result['total_return_pct'], result['sharpe_ratio'])
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed"}

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbol, start=start, end=end)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No price data", "symbol": symbol}

        fast_ma = vbt.MA.run(close, window=fast_window)
        slow_ma = vbt.MA.run(close, window=slow_window)

        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)

        pf = vbt.Portfolio.from_signals(
            close, entries, exits,
            init_cash=init_cash, fees=fees, freq="1D"
        )

        stats = pf.stats()
        stats_dict = stats.to_dict() if hasattr(stats, "to_dict") else {}

        total_return = float(pf.total_return()) * 100
        trades = pf.trades.records_readable if hasattr(pf.trades, "records_readable") else None
        n_trades = int(pf.trades.count()) if hasattr(pf.trades, "count") else 0

        try:
            sharpe = float(pf.sharpe_ratio())
        except Exception:
            sharpe = None
        try:
            max_dd = float(pf.max_drawdown()) * 100
        except Exception:
            max_dd = None
        try:
            win_rate = float(pf.trades.win_rate()) * 100 if n_trades > 0 else None
        except Exception:
            win_rate = None

        return {
            "symbol": symbol,
            "strategy": f"SMA({fast_window}/{slow_window})",
            "period": [start, end],
            "bars": len(close),
            "init_cash": init_cash,
            "final_value": round(float(pf.final_value()), 2),
            "total_return_pct": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
            "max_drawdown_pct": round(max_dd, 2) if max_dd is not None else None,
            "total_trades": n_trades,
            "win_rate_pct": round(win_rate, 2) if win_rate is not None else None,
            "fees": fees,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def run_rsi_strategy(
    symbol: str = "AAPL",
    rsi_window: int = 14,
    entry_threshold: float = 30.0,
    exit_threshold: float = 70.0,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365,
    init_cash: float = 10000.0,
    fees: float = 0.001
) -> dict[str, Any]:
    """
    Run an RSI mean-reversion backtest.

    Buys when RSI drops below entry_threshold, sells above exit_threshold.

    Args:
        symbol: Ticker symbol
        rsi_window: RSI calculation period
        entry_threshold: Buy when RSI below this (default 30)
        exit_threshold: Sell when RSI above this (default 70)
        start: Start date
        end: End date
        period_days: Lookback if start not given
        init_cash: Starting capital
        fees: Trading fee fraction

    Returns:
        dict with strategy performance metrics

    Example:
        >>> result = run_rsi_strategy('MSFT', rsi_window=14)
        >>> print(result['total_return_pct'])
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed"}

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbol, start=start, end=end)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No price data", "symbol": symbol}

        rsi = vbt.RSI.run(close, window=rsi_window)

        entries = rsi.rsi_crossed_below(entry_threshold)
        exits = rsi.rsi_crossed_above(exit_threshold)

        pf = vbt.Portfolio.from_signals(
            close, entries, exits,
            init_cash=init_cash, fees=fees, freq="1D"
        )

        total_return = float(pf.total_return()) * 100
        n_trades = int(pf.trades.count()) if hasattr(pf.trades, "count") else 0

        try:
            sharpe = float(pf.sharpe_ratio())
        except Exception:
            sharpe = None
        try:
            max_dd = float(pf.max_drawdown()) * 100
        except Exception:
            max_dd = None
        try:
            win_rate = float(pf.trades.win_rate()) * 100 if n_trades > 0 else None
        except Exception:
            win_rate = None

        return {
            "symbol": symbol,
            "strategy": f"RSI({rsi_window}, {entry_threshold}/{exit_threshold})",
            "period": [start, end],
            "bars": len(close),
            "init_cash": init_cash,
            "final_value": round(float(pf.final_value()), 2),
            "total_return_pct": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
            "max_drawdown_pct": round(max_dd, 2) if max_dd is not None else None,
            "total_trades": n_trades,
            "win_rate_pct": round(win_rate, 2) if win_rate is not None else None,
            "fees": fees,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def optimize_sma_windows(
    symbol: str = "AAPL",
    fast_range: tuple = (5, 30, 5),
    slow_range: tuple = (20, 100, 10),
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365,
    init_cash: float = 10000.0,
    fees: float = 0.001,
    top_n: int = 5
) -> dict[str, Any]:
    """
    Optimize SMA crossover parameters over a grid of fast/slow windows.

    Args:
        symbol: Ticker symbol
        fast_range: (start, stop, step) for fast window
        slow_range: (start, stop, step) for slow window
        start: Start date
        end: End date
        period_days: Lookback if start not given
        init_cash: Starting capital
        fees: Trading fee fraction
        top_n: Number of top combinations to return

    Returns:
        dict with top_n best parameter combos ranked by total return

    Example:
        >>> result = optimize_sma_windows('AAPL', fast_range=(5,25,5), slow_range=(20,60,10))
        >>> for combo in result['top_combos']: print(combo)
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed"}

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbol, start=start, end=end)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No price data", "symbol": symbol}

        fast_windows = np.arange(*fast_range)
        slow_windows = np.arange(*slow_range)

        # Filter: fast must be < slow
        results = []
        for fw in fast_windows:
            for sw in slow_windows:
                if fw >= sw:
                    continue
                fast_ma = vbt.MA.run(close, window=int(fw))
                slow_ma = vbt.MA.run(close, window=int(sw))
                entries = fast_ma.ma_crossed_above(slow_ma)
                exits = fast_ma.ma_crossed_below(slow_ma)
                pf = vbt.Portfolio.from_signals(
                    close, entries, exits,
                    init_cash=init_cash, fees=fees, freq="1D"
                )
                ret = float(pf.total_return()) * 100
                try:
                    sharpe = float(pf.sharpe_ratio())
                except Exception:
                    sharpe = 0.0
                n_trades = int(pf.trades.count()) if hasattr(pf.trades, "count") else 0
                results.append({
                    "fast": int(fw),
                    "slow": int(sw),
                    "return_pct": round(ret, 2),
                    "sharpe": round(sharpe, 4),
                    "trades": n_trades
                })

        results.sort(key=lambda x: x["return_pct"], reverse=True)

        return {
            "symbol": symbol,
            "period": [start, end],
            "bars": len(close),
            "combos_tested": len(results),
            "top_combos": results[:top_n],
            "worst_combo": results[-1] if results else None,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_portfolio_stats(
    symbols: Union[str, list[str]],
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365
) -> dict[str, Any]:
    """
    Get portfolio-level statistics for a basket of assets (equal-weight buy & hold).

    Args:
        symbols: Ticker or list of tickers
        start: Start date
        end: End date
        period_days: Lookback if start not given

    Returns:
        dict with per-asset and portfolio-level metrics

    Example:
        >>> stats = get_portfolio_stats(['AAPL','MSFT','GOOGL'], period_days=180)
        >>> print(stats['portfolio_return_pct'])
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed"}

    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbols, start=start, end=end)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No price data", "symbols": symbols}

        if isinstance(close, pd.Series):
            close = close.to_frame(name=symbols[0])

        # Equal weight buy & hold
        pf = vbt.Portfolio.from_holding(close, init_cash=10000.0, freq="1D")

        asset_stats = {}
        for col in close.columns:
            col_close = close[col].dropna()
            if len(col_close) < 2:
                continue
            ret = (col_close.iloc[-1] / col_close.iloc[0] - 1) * 100
            vol = float(col_close.pct_change().std() * np.sqrt(252)) * 100
            asset_stats[col] = {
                "return_pct": round(float(ret), 2),
                "annualized_vol_pct": round(vol, 2),
                "last_price": round(float(col_close.iloc[-1]), 4)
            }

        total_return = float(pf.total_return())
        if hasattr(total_return, "__iter__"):
            total_return = float(np.mean(list(total_return)))
        total_return *= 100

        return {
            "symbols": symbols,
            "period": [start, end],
            "bars": len(close),
            "portfolio_return_pct": round(total_return, 2),
            "asset_stats": asset_stats,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbols": symbols}


def run_custom_signals(
    symbol: str = "AAPL",
    entry_dates: Optional[list[str]] = None,
    exit_dates: Optional[list[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period_days: int = 365,
    init_cash: float = 10000.0,
    fees: float = 0.001
) -> dict[str, Any]:
    """
    Backtest custom entry/exit date signals.

    Args:
        symbol: Ticker symbol
        entry_dates: List of entry dates ['2024-01-15', '2024-03-01']
        exit_dates: List of exit dates ['2024-02-01', '2024-04-01']
        start: Start date
        end: End date
        period_days: Lookback if start not given
        init_cash: Starting capital
        fees: Fee fraction

    Returns:
        dict with backtest results

    Example:
        >>> r = run_custom_signals('AAPL', ['2024-01-15'], ['2024-02-15'])
        >>> print(r['total_return_pct'])
    """
    vbt = _ensure_vbt()
    if vbt is None:
        return {"error": "vectorbt not installed"}

    if not entry_dates or not exit_dates:
        return {"error": "Must provide entry_dates and exit_dates lists"}

    if not start:
        start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        yf_data = vbt.YFData.download(symbol, start=start, end=end)
        close = yf_data.get("Close")
        if close is None or close.empty:
            return {"error": "No price data", "symbol": symbol}

        entries = pd.Series(False, index=close.index)
        exits = pd.Series(False, index=close.index)

        for d in entry_dates:
            dt = pd.Timestamp(d, tz=close.index.tz)
            idx = close.index.get_indexer([dt], method="nearest")
            if idx[0] >= 0:
                entries.iloc[idx[0]] = True

        for d in exit_dates:
            dt = pd.Timestamp(d, tz=close.index.tz)
            idx = close.index.get_indexer([dt], method="nearest")
            if idx[0] >= 0:
                exits.iloc[idx[0]] = True

        pf = vbt.Portfolio.from_signals(
            close, entries, exits,
            init_cash=init_cash, fees=fees, freq="1D"
        )

        total_return = float(pf.total_return()) * 100
        n_trades = int(pf.trades.count()) if hasattr(pf.trades, "count") else 0

        return {
            "symbol": symbol,
            "strategy": "custom_signals",
            "entry_dates": entry_dates,
            "exit_dates": exit_dates,
            "total_return_pct": round(total_return, 2),
            "final_value": round(float(pf.final_value()), 2),
            "total_trades": n_trades,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


if __name__ == "__main__":
    print(json.dumps({"module": "vectorbt", "status": "ready", "source": "https://vectorbt.dev/"}, indent=2))
