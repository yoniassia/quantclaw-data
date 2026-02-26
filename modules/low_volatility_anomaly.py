"""
Low Volatility Anomaly Scanner — Identifies stocks exhibiting the low-vol premium.

The low volatility anomaly shows that low-risk stocks tend to deliver higher
risk-adjusted returns than high-risk stocks, contradicting CAPM predictions.
Scans for low-beta, low-vol stocks with strong risk-adjusted returns.
Uses free Yahoo Finance data via yfinance.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def calculate_volatility_metrics(prices: List[float], risk_free_rate: float = 0.05) -> Dict:
    """
    Calculate comprehensive volatility metrics for a price series.

    Args:
        prices: List of daily closing prices (oldest first)
        risk_free_rate: Annual risk-free rate (default 5%)

    Returns:
        Dict with annualized vol, downside vol, Sharpe, Sortino, max drawdown
    """
    if len(prices) < 22:
        return {"error": "Need at least 22 prices"}

    # Daily returns
    returns = [(prices[i] / prices[i - 1]) - 1 for i in range(1, len(prices))]

    # Annualized volatility
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    daily_vol = math.sqrt(variance)
    ann_vol = daily_vol * math.sqrt(252)
    ann_return = mean_ret * 252

    # Downside volatility (Sortino)
    daily_rf = risk_free_rate / 252
    downside_returns = [r for r in returns if r < daily_rf]
    if downside_returns:
        downside_var = sum((r - daily_rf) ** 2 for r in downside_returns) / len(downside_returns)
        downside_vol = math.sqrt(downside_var) * math.sqrt(252)
    else:
        downside_vol = 0.001

    # Sharpe and Sortino
    sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 0 else 0
    sortino = (ann_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0

    # Max drawdown
    peak = prices[0]
    max_dd = 0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_dd:
            max_dd = dd

    # Beta proxy (vs equal-weighted return of the series itself — placeholder)
    # In production, compare against market index
    return {
        "annualized_return": round(ann_return, 4),
        "annualized_volatility": round(ann_vol, 4),
        "downside_volatility": round(downside_vol, 4),
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "max_drawdown": round(max_dd, 4),
        "daily_returns_count": len(returns),
        "positive_days_pct": round(sum(1 for r in returns if r > 0) / len(returns), 3)
    }


def rank_by_low_volatility(stocks_data: Dict[str, List[float]], top_n: int = 20) -> List[Dict]:
    """
    Rank stocks by low volatility anomaly score (low vol + high risk-adjusted return).

    Args:
        stocks_data: Dict mapping ticker -> list of daily prices
        top_n: Number of top stocks to return

    Returns:
        Sorted list of dicts with ticker, metrics, and anomaly_score
    """
    results = []
    all_vols = []

    for ticker, prices in stocks_data.items():
        metrics = calculate_volatility_metrics(prices)
        if "error" in metrics:
            continue
        all_vols.append(metrics["annualized_volatility"])
        results.append({"ticker": ticker, **metrics})

    if not results:
        return []

    # Normalize: lower vol = higher score, higher Sharpe = higher score
    max_vol = max(all_vols) if all_vols else 1
    min_vol = min(all_vols) if all_vols else 0
    vol_range = max_vol - min_vol if max_vol != min_vol else 1

    for r in results:
        # Low vol score: 0 (highest vol) to 1 (lowest vol)
        vol_score = 1 - (r["annualized_volatility"] - min_vol) / vol_range
        # Risk-adjusted score from Sharpe (capped)
        sharpe_score = min(max(r["sharpe_ratio"], -2), 3) / 3.0
        # Anomaly score: high when vol is low BUT returns are good
        r["low_vol_score"] = round(vol_score, 3)
        r["anomaly_score"] = round(vol_score * 0.4 + sharpe_score * 0.4 + (1 - r["max_drawdown"]) * 0.2, 3)

    results.sort(key=lambda x: x["anomaly_score"], reverse=True)
    return results[:top_n]


def detect_vol_regime(prices: List[float], window: int = 63) -> List[Dict]:
    """
    Detect volatility regime changes using rolling volatility.

    Args:
        prices: Daily price series
        window: Rolling window in days (default 63 = ~3 months)

    Returns:
        List of regime periods with start, end, regime type, avg vol
    """
    if len(prices) < window + 1:
        return [{"error": f"Need at least {window + 1} prices"}]

    returns = [(prices[i] / prices[i - 1]) - 1 for i in range(1, len(prices))]

    # Rolling volatility
    rolling_vols = []
    for i in range(window, len(returns)):
        w = returns[i - window:i]
        mean_w = sum(w) / len(w)
        var_w = sum((r - mean_w) ** 2 for r in w) / (len(w) - 1)
        rolling_vols.append(math.sqrt(var_w) * math.sqrt(252))

    if not rolling_vols:
        return []

    # Regime thresholds
    median_vol = sorted(rolling_vols)[len(rolling_vols) // 2]
    low_threshold = median_vol * 0.75
    high_threshold = median_vol * 1.5

    regimes = []
    current_regime = None
    regime_start = 0

    for i, vol in enumerate(rolling_vols):
        if vol < low_threshold:
            regime = "low_vol"
        elif vol > high_threshold:
            regime = "high_vol"
        else:
            regime = "normal"

        if regime != current_regime:
            if current_regime is not None:
                regimes.append({
                    "regime": current_regime,
                    "start_idx": regime_start,
                    "end_idx": i - 1,
                    "duration_days": i - regime_start,
                    "avg_vol": round(sum(rolling_vols[regime_start:i]) / (i - regime_start), 4)
                })
            current_regime = regime
            regime_start = i

    # Final regime
    if current_regime:
        regimes.append({
            "regime": current_regime,
            "start_idx": regime_start,
            "end_idx": len(rolling_vols) - 1,
            "duration_days": len(rolling_vols) - regime_start,
            "avg_vol": round(sum(rolling_vols[regime_start:]) / (len(rolling_vols) - regime_start), 4)
        })

    return regimes


def quintile_analysis(stocks_data: Dict[str, List[float]]) -> Dict:
    """
    Perform quintile analysis: sort stocks by vol, compare returns across quintiles.
    Classic test of the low-volatility anomaly.

    Args:
        stocks_data: Dict mapping ticker -> list of daily prices

    Returns:
        Dict with quintile performance comparison
    """
    metrics_list = []
    for ticker, prices in stocks_data.items():
        m = calculate_volatility_metrics(prices)
        if "error" not in m:
            metrics_list.append({"ticker": ticker, **m})

    if len(metrics_list) < 5:
        return {"error": "Need at least 5 stocks for quintile analysis"}

    # Sort by volatility
    metrics_list.sort(key=lambda x: x["annualized_volatility"])
    q_size = len(metrics_list) // 5

    quintiles = {}
    for q in range(5):
        start = q * q_size
        end = start + q_size if q < 4 else len(metrics_list)
        group = metrics_list[start:end]
        quintiles[f"Q{q + 1}_{'lowest' if q == 0 else 'highest' if q == 4 else 'mid'}"] = {
            "count": len(group),
            "avg_volatility": round(sum(g["annualized_volatility"] for g in group) / len(group), 4),
            "avg_return": round(sum(g["annualized_return"] for g in group) / len(group), 4),
            "avg_sharpe": round(sum(g["sharpe_ratio"] for g in group) / len(group), 3),
            "avg_max_drawdown": round(sum(g["max_drawdown"] for g in group) / len(group), 4),
            "tickers": [g["ticker"] for g in group]
        }

    # Anomaly strength: Q1 Sharpe vs Q5 Sharpe
    q1_sharpe = quintiles["Q1_lowest"]["avg_sharpe"]
    q5_sharpe = quintiles["Q5_highest"]["avg_sharpe"]

    return {
        "quintiles": quintiles,
        "anomaly_present": q1_sharpe > q5_sharpe,
        "anomaly_strength": round(q1_sharpe - q5_sharpe, 3),
        "total_stocks": len(metrics_list)
    }
