#!/usr/bin/env python3
"""
MicroTick Dataset — Tick-Level European Exchange Data

Free historical tick-level data for European exchanges (quarterly CSV downloads).
Implements framework for download/parse/analyze order flow, spreads, volatility even if source offline.

Key functions:
- download_dataset(): Download or generate sample CSV
- parse_tick_data(): Load to structured pd.DataFrame
- get_order_imbalance(ticks): Rolling order flow imbalance
- get_effective_spread(ticks): Trade effective spreads
- get_realized_volatility(ticks, interval): Realized vol
- get_vwap(ticks): Volume-weighted average price
- generate_sample_ticks(): Synthetic data generator

Source: https://microtick.org/datasets (unavailable Mar 2026, using synthetic)
Category: Exchanges & Market Microstructure
Free tier: true
Author: QuantClaw Data NightBuilder
Phase: 1
"""

import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
from pathlib import Path

def generate_sample_ticks(n_ticks: int = 50000, symbol: str = "SAMPLE_EURONEXT") -> pd.DataFrame:
    """Generate realistic synthetic tick data for testing. Columns: timestamp, bid_price, ask_price, trade_price, trade_volume, trade_side, mid_price"""
    np.random.seed(42)
    timestamps = pd.date_range(start="2026-01-01 09:30:00", periods=n_ticks, freq="100ms")
    price = 100.0
    bids, asks, mids, trade_prices, trade_vols, sides = [], [], [], [], [], []
    for _ in range(n_ticks):
        mid = price + np.random.normal(0, 0.001)
        spread = np.random.uniform(0.0005, 0.002) * mid
        bid = mid - spread / 2
        ask = mid + spread / 2
        bids.append(bid)
        asks.append(ask)
        mids.append(mid)
        if np.random.random() < 0.15:  # ~15% trades
            trade_price = ask if np.random.random() < 0.52 else bid  # slight buy bias
            trade_vol = np.random.poisson(100)
            side = "B" if trade_price >= mid else "S"
            trade_prices.append(trade_price)
            trade_vols.append(trade_vol)
            sides.append(side)
            price = (price * 0.9 + trade_price * 0.1)  # slow update
        else:
            trade_prices.append(np.nan)
            trade_vols.append(0)
            sides.append("")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "bid_price": bids,
        "ask_price": asks,
        "trade_price": trade_prices,
        "trade_volume": trade_vols,
        "trade_side": sides,
        "mid_price": mids,
    })
    return df

def download_dataset(exchange: str = "EURONEXT", quarter: str = "2026Q1",
                     data_dir: str = "data/microtick",
                     base_url: str = "https://microtick.org/data/tick") -> str:
    """Download quarterly tick CSV or generate sample if source unavailable."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    filename = f"{quarter}_{exchange.upper()}.csv"
    filepath = data_path / filename
    url = f"{base_url}/{quarter}/{exchange.upper()}.csv"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        print(f"Downloaded: {filepath}")
    except Exception as e:
        print(f"Source unavailable ({e}), generating sample: {filepath}")
        ticks = generate_sample_ticks(50000, f"{exchange}_{quarter}")
        ticks.to_csv(filepath, index=False)
    return str(filepath)

def parse_tick_data(filepath: str) -> pd.DataFrame:
    """Parse tick CSV to DataFrame with computed fields."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Tick data not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df["trade_side_num"] = df["trade_side"].map({"B": 1, "S": -1}).fillna(0)
    if "mid_price" not in df.columns:
        df["mid_price"] = (df["bid_price"] + df["ask_price"]) / 2
    return df.sort_values("timestamp")

def get_order_imbalance(ticks: pd.DataFrame, window: int = 100) -> pd.Series:
    """Rolling order flow imbalance: (buy_vol - sell_vol) / total_vol over window ticks."""
    trades = ticks[ticks["trade_volume"] > 0].copy()
    trades["buy_vol"] = trades["trade_volume"] * (trades["trade_side_num"] > 0)
    trades["sell_vol"] = trades["trade_volume"] * (trades["trade_side_num"] < 0)
    imb_num = trades["buy_vol"].rolling(window, min_periods=10).sum() - trades["sell_vol"].rolling(window, min_periods=10).sum()
    imb_den = trades["buy_vol"].rolling(window, min_periods=10).sum() + trades["sell_vol"].rolling(window, min_periods=10).sum()
    return imb_num / imb_den

def get_effective_spread(ticks: pd.DataFrame) -> pd.Series:
    """Effective spread: 2 * direction * |trade_price - mid| / mid for trades."""
    trades = ticks[ticks["trade_volume"] > 0].copy()
    trades["eff_spread"] = 2 * trades["trade_side_num"] * np.abs(trades["trade_price"] - trades["mid_price"]) / trades["mid_price"]
    return trades["eff_spread"]

def get_realized_volatility(ticks: pd.DataFrame, interval: str = "1min") -> pd.Series:
    """Realized volatility per interval using last trade price."""
    trades = ticks[ticks["trade_volume"] > 0][["timestamp", "trade_price"]].set_index("timestamp")
    bar_prices = trades.resample(interval).last().dropna()
    log_rets = np.log(bar_prices / bar_prices.shift(1)).dropna()
    rv = np.sqrt((log_rets ** 2).rolling(5, min_periods=2).sum()) * 100  # % vol
    return rv

def get_vwap(ticks: pd.DataFrame) -> float:
    """Overall VWAP for period."""
    trades = ticks[ticks["trade_volume"] > 0]
    if len(trades) == 0:
        return np.nan
    return np.average(trades["trade_price"], weights=trades["trade_volume"])

# Legacy compatibility
def fetch_data():
    return download_dataset()

def get_latest():
    return "2026Q1 (synthetic)"

if __name__ == "__main__":
    fp = download_dataset()
    df = parse_tick_data(fp)
    print(json.dumps({
        "module": "microtick_dataset",
        "status": "ready",
        "rows": len(df),
        "trades": len(df[df["trade_volume"] > 0]),
        "vwap": float(get_vwap(df)),
        "mean_spread_bp": float(get_effective_spread(df).mean() * 10000) if len(df) > 0 else 0
    }, indent=2))
