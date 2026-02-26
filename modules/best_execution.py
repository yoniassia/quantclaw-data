"""Best Execution Analyzer — VWAP/TWAP/POV benchmark comparison.

Evaluates trade execution quality by comparing realized prices against
VWAP, TWAP, and POV (Percentage of Volume) benchmarks. Uses free
Yahoo Finance data to compute intraday benchmarks.

Roadmap #245: Best Execution Analyzer (VWAP/TWAP/POV comparison)
"""

import datetime
import math
import random
from typing import Any


def compute_vwap(prices: list[float], volumes: list[float]) -> float:
    """Compute Volume-Weighted Average Price from price/volume bars.

    Args:
        prices: List of bar prices (e.g., typical price = (H+L+C)/3).
        volumes: List of corresponding volumes.

    Returns:
        VWAP value, or 0.0 if no volume.
    """
    if not prices or not volumes or len(prices) != len(volumes):
        return 0.0
    total_pv = sum(p * v for p, v in zip(prices, volumes))
    total_v = sum(volumes)
    return total_pv / total_v if total_v > 0 else 0.0


def compute_twap(prices: list[float]) -> float:
    """Compute Time-Weighted Average Price (simple average over time bars).

    Args:
        prices: List of bar prices over the execution window.

    Returns:
        TWAP value.
    """
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


def compute_pov_benchmark(
    prices: list[float], volumes: list[float], participation_rate: float = 0.10
) -> dict[str, Any]:
    """Compute POV (Percentage of Volume) benchmark.

    Simulates executing a fixed participation rate per bar and computes
    the resulting average fill price.

    Args:
        prices: List of bar prices.
        volumes: List of bar volumes.
        participation_rate: Target participation rate (0-1).

    Returns:
        Dict with pov_avg_price, total_shares_filled, participation_rate.
    """
    if not prices or not volumes:
        return {"pov_avg_price": 0.0, "total_shares_filled": 0, "participation_rate": participation_rate}

    total_cost = 0.0
    total_shares = 0.0
    for p, v in zip(prices, volumes):
        shares = v * participation_rate
        total_cost += shares * p
        total_shares += shares

    avg_price = total_cost / total_shares if total_shares > 0 else 0.0
    return {
        "pov_avg_price": round(avg_price, 4),
        "total_shares_filled": round(total_shares),
        "participation_rate": participation_rate,
    }


def analyze_execution(
    exec_price: float,
    exec_shares: int,
    side: str,
    prices: list[float],
    volumes: list[float],
    participation_rate: float = 0.10,
) -> dict[str, Any]:
    """Full execution quality analysis against VWAP/TWAP/POV benchmarks.

    Args:
        exec_price: Realized average execution price.
        exec_shares: Total shares executed.
        side: 'buy' or 'sell'.
        prices: Intraday bar prices for benchmark window.
        volumes: Intraday bar volumes for benchmark window.
        participation_rate: POV target rate.

    Returns:
        Dict with benchmarks, slippage in bps, and quality grade.
    """
    vwap = compute_vwap(prices, volumes)
    twap = compute_twap(prices)
    pov = compute_pov_benchmark(prices, volumes, participation_rate)

    sign = 1 if side.lower() == "buy" else -1

    def slippage_bps(benchmark: float) -> float:
        if benchmark == 0:
            return 0.0
        return sign * (exec_price - benchmark) / benchmark * 10000

    vwap_slip = slippage_bps(vwap)
    twap_slip = slippage_bps(twap)
    pov_slip = slippage_bps(pov["pov_avg_price"])

    avg_slip = (vwap_slip + twap_slip + pov_slip) / 3

    if avg_slip < 2:
        grade = "Excellent"
    elif avg_slip < 5:
        grade = "Good"
    elif avg_slip < 15:
        grade = "Acceptable"
    else:
        grade = "Poor"

    return {
        "exec_price": exec_price,
        "exec_shares": exec_shares,
        "side": side,
        "vwap": round(vwap, 4),
        "twap": round(twap, 4),
        "pov_avg_price": pov["pov_avg_price"],
        "vwap_slippage_bps": round(vwap_slip, 2),
        "twap_slippage_bps": round(twap_slip, 2),
        "pov_slippage_bps": round(pov_slip, 2),
        "avg_slippage_bps": round(avg_slip, 2),
        "grade": grade,
    }


def generate_sample_analysis(ticker: str = "AAPL") -> dict[str, Any]:
    """Generate a sample execution analysis with synthetic intraday data.

    Args:
        ticker: Stock ticker for labeling.

    Returns:
        Sample analysis result.
    """
    base = 150.0 + random.random() * 50
    n_bars = 78  # 5-min bars in trading day
    prices = [base + random.gauss(0, 0.5) for _ in range(n_bars)]
    volumes = [random.randint(5000, 50000) for _ in range(n_bars)]
    exec_price = base + random.gauss(0, 0.3)

    result = analyze_execution(exec_price, 10000, "buy", prices, volumes)
    result["ticker"] = ticker
    result["date"] = datetime.date.today().isoformat()
    return result
