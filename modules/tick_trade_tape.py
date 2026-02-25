"""
Tick-by-Tick Trade Tape — Time & Sales data aggregator.
Roadmap #204: Records individual trades, computes VWAP, detects block trades,
and provides trade flow analysis using free data sources.
"""

import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import deque


class TradeTape:
    """Rolling window trade tape for a single instrument."""

    def __init__(self, max_ticks: int = 10000):
        self.ticks: deque = deque(maxlen=max_ticks)

    def add_tick(self, price: float, size: int, side: str = "unknown", timestamp: Optional[str] = None):
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self.ticks.append({
            "price": price,
            "size": size,
            "side": side,
            "timestamp": ts,
            "notional": round(price * size, 2),
        })

    def get_vwap(self) -> float:
        """Compute Volume-Weighted Average Price over all ticks in tape."""
        if not self.ticks:
            return 0.0
        total_notional = sum(t["notional"] for t in self.ticks)
        total_volume = sum(t["size"] for t in self.ticks)
        return round(total_notional / total_volume, 4) if total_volume else 0.0

    def get_block_trades(self, threshold_size: int = 10000) -> List[Dict]:
        """Find block trades exceeding the size threshold."""
        return [t for t in self.ticks if t["size"] >= threshold_size]

    def get_trade_flow_summary(self) -> Dict:
        """Summarize buy vs sell flow."""
        buys = [t for t in self.ticks if t["side"] == "buy"]
        sells = [t for t in self.ticks if t["side"] == "sell"]
        unknown = [t for t in self.ticks if t["side"] == "unknown"]

        buy_vol = sum(t["size"] for t in buys)
        sell_vol = sum(t["size"] for t in sells)
        total_vol = buy_vol + sell_vol + sum(t["size"] for t in unknown)

        return {
            "total_ticks": len(self.ticks),
            "total_volume": total_vol,
            "buy_volume": buy_vol,
            "sell_volume": sell_vol,
            "buy_pct": round(buy_vol / total_vol * 100, 2) if total_vol else 0,
            "sell_pct": round(sell_vol / total_vol * 100, 2) if total_vol else 0,
            "net_flow": buy_vol - sell_vol,
            "vwap": self.get_vwap(),
        }

    def get_recent(self, n: int = 50) -> List[Dict]:
        """Get the N most recent ticks."""
        return list(self.ticks)[-n:]


def classify_trade_side(price: float, bid: float, ask: float) -> str:
    """Classify trade as buy/sell using Lee-Ready tick rule."""
    mid = (bid + ask) / 2
    if price > mid:
        return "buy"
    elif price < mid:
        return "sell"
    return "unknown"


def compute_trade_intensity(ticks: List[Dict], window_seconds: int = 60) -> List[Dict]:
    """
    Compute trade intensity (trades per second) over rolling windows.
    Returns list of {window_start, trades_count, volume, avg_size}.
    """
    if not ticks:
        return []

    results = []
    # Group by window
    from datetime import datetime as dt
    sorted_ticks = sorted(ticks, key=lambda t: t["timestamp"])

    window_start_idx = 0
    for i, tick in enumerate(sorted_ticks):
        try:
            t_current = dt.fromisoformat(tick["timestamp"].replace("Z", "+00:00"))
            t_start = dt.fromisoformat(sorted_ticks[window_start_idx]["timestamp"].replace("Z", "+00:00"))
            while (t_current - t_start).total_seconds() > window_seconds:
                window_start_idx += 1
                t_start = dt.fromisoformat(sorted_ticks[window_start_idx]["timestamp"].replace("Z", "+00:00"))
        except (ValueError, IndexError):
            continue

        window_ticks = sorted_ticks[window_start_idx:i + 1]
        vol = sum(t["size"] for t in window_ticks)
        count = len(window_ticks)
        results.append({
            "as_of": tick["timestamp"],
            "trades_in_window": count,
            "volume_in_window": vol,
            "avg_size": round(vol / count, 2) if count else 0,
            "intensity_per_sec": round(count / window_seconds, 4),
        })

    return results


def detect_sweeps(ticks: List[Dict], min_trades: int = 5, max_seconds: int = 3) -> List[Dict]:
    """
    Detect potential sweep orders — rapid same-direction trades in short window.
    """
    if len(ticks) < min_trades:
        return []

    sweeps = []
    from datetime import datetime as dt

    for i in range(len(ticks) - min_trades + 1):
        window = ticks[i:i + min_trades]
        sides = [t["side"] for t in window if t["side"] != "unknown"]
        if len(sides) < min_trades:
            continue
        if len(set(sides)) != 1:
            continue

        try:
            t0 = dt.fromisoformat(window[0]["timestamp"].replace("Z", "+00:00"))
            t1 = dt.fromisoformat(window[-1]["timestamp"].replace("Z", "+00:00"))
            elapsed = (t1 - t0).total_seconds()
        except (ValueError, KeyError):
            continue

        if elapsed <= max_seconds:
            total_size = sum(t["size"] for t in window)
            sweeps.append({
                "direction": sides[0],
                "trades": min_trades,
                "total_size": total_size,
                "elapsed_seconds": round(elapsed, 2),
                "start_time": window[0]["timestamp"],
                "end_time": window[-1]["timestamp"],
            })

    return sweeps
