"""Meta-Learning Strategy Selector — dynamically select the best trading strategy for current regime.

Maintains a library of strategy archetypes (momentum, mean-reversion, carry, etc.)
and uses recent market conditions to predict which strategy will perform best.
Implements a bandit-style meta-learner with regime conditioning.
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


# Strategy archetypes and their preferred regimes
STRATEGY_ARCHETYPES = {
    "momentum": {
        "description": "Trend-following across timeframes",
        "preferred_regimes": ["trending_up", "trending_down"],
        "anti_regimes": ["mean_reverting", "choppy"],
    },
    "mean_reversion": {
        "description": "Fade extremes, bet on normalization",
        "preferred_regimes": ["mean_reverting", "range_bound"],
        "anti_regimes": ["trending_up", "trending_down", "crisis"],
    },
    "carry": {
        "description": "Harvest yield differentials",
        "preferred_regimes": ["low_vol", "range_bound"],
        "anti_regimes": ["crisis", "high_vol"],
    },
    "volatility_selling": {
        "description": "Sell premium, collect theta",
        "preferred_regimes": ["low_vol", "range_bound"],
        "anti_regimes": ["crisis", "high_vol"],
    },
    "breakout": {
        "description": "Trade range expansions",
        "preferred_regimes": ["compressed", "pre_trend"],
        "anti_regimes": ["mean_reverting"],
    },
    "risk_parity": {
        "description": "Equal risk contribution allocation",
        "preferred_regimes": ["diversified", "normal"],
        "anti_regimes": ["crisis_correlated"],
    },
    "defensive": {
        "description": "Capital preservation, tail hedging",
        "preferred_regimes": ["crisis", "high_vol", "uncertainty"],
        "anti_regimes": ["trending_up", "low_vol"],
    },
}


def classify_regime(
    returns: List[float],
    volatility: float,
    trend_strength: float,
    correlation_level: float,
) -> str:
    """Classify the current market regime from features.

    Args:
        returns: Recent returns (e.g., last 20 days).
        volatility: Annualized volatility estimate.
        trend_strength: Absolute value of trend (0-1).
        correlation_level: Average cross-asset correlation (0-1).

    Returns:
        Regime string.
    """
    avg_ret = sum(returns) / len(returns) if returns else 0

    if correlation_level > 0.7 and volatility > 0.25:
        return "crisis"
    if volatility > 0.30:
        return "high_vol"
    if volatility < 0.10:
        return "low_vol"
    if trend_strength > 0.6 and avg_ret > 0:
        return "trending_up"
    if trend_strength > 0.6 and avg_ret < 0:
        return "trending_down"
    if trend_strength < 0.2:
        return "mean_reverting"
    if volatility < 0.15 and trend_strength < 0.3:
        return "range_bound"
    return "normal"


def compute_strategy_scores(
    regime: str,
    performance_history: Optional[Dict[str, List[float]]] = None,
    exploration_rate: float = 0.1,
) -> Dict[str, Dict]:
    """Score each strategy archetype for the current regime.

    Args:
        regime: Current market regime.
        performance_history: {strategy_name: [recent sharpe ratios]}.
        exploration_rate: Epsilon for exploration (0-1).

    Returns:
        {strategy: {score, regime_fit, historical_perf, recommended}}.
    """
    results = {}

    for name, archetype in STRATEGY_ARCHETYPES.items():
        # Regime fit score
        if regime in archetype["preferred_regimes"]:
            regime_fit = 1.0
        elif regime in archetype["anti_regimes"]:
            regime_fit = -0.5
        else:
            regime_fit = 0.2

        # Historical performance component
        hist_perf = 0.0
        if performance_history and name in performance_history:
            recent = performance_history[name][-10:]
            if recent:
                hist_perf = sum(recent) / len(recent)

        # Combined score
        score = 0.6 * regime_fit + 0.4 * min(max(hist_perf, -1), 1)

        results[name] = {
            "score": round(score, 4),
            "regime_fit": regime_fit,
            "historical_perf": round(hist_perf, 4),
            "description": archetype["description"],
        }

    # Mark top recommendations
    sorted_strats = sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)
    for i, (name, data) in enumerate(sorted_strats):
        data["rank"] = i + 1
        data["recommended"] = i < 2  # Top 2

    return results


def select_strategy(
    regime: str,
    performance_history: Optional[Dict[str, List[float]]] = None,
    exploration_rate: float = 0.1,
) -> Dict:
    """Select the best strategy using epsilon-greedy meta-learning.

    Args:
        regime: Current market regime.
        performance_history: {strategy: [recent performances]}.
        exploration_rate: Probability of random exploration.

    Returns:
        Dict with selected_strategy, reason, confidence, all_scores.
    """
    scores = compute_strategy_scores(regime, performance_history, exploration_rate)

    # Epsilon-greedy selection
    if random.random() < exploration_rate:
        selected = random.choice(list(scores.keys()))
        reason = "exploration"
    else:
        selected = max(scores, key=lambda k: scores[k]["score"])
        reason = "exploitation"

    best_score = scores[selected]["score"]
    confidence = round(max(0, min(1, (best_score + 0.5) / 1.5)), 3)

    return {
        "selected_strategy": selected,
        "reason": reason,
        "regime": regime,
        "confidence": confidence,
        "strategy_score": scores[selected]["score"],
        "all_scores": scores,
    }


def backtest_meta_learner(
    regime_sequence: List[str],
    strategy_returns: Dict[str, List[float]],
    lookback: int = 10,
) -> Dict:
    """Backtest the meta-learner over a sequence of regimes.

    Args:
        regime_sequence: List of regime labels per period.
        strategy_returns: {strategy: [return per period]}.
        lookback: Periods to use for performance history.

    Returns:
        Dict with total_return, sharpe_proxy, strategy_switches, period_results.
    """
    n_periods = len(regime_sequence)
    cumulative = 0.0
    returns_list: List[float] = []
    switches = 0
    last_strategy = None
    period_results = []

    for t in range(n_periods):
        regime = regime_sequence[t]

        # Build performance history from past
        perf_hist = {}
        for s_name, s_rets in strategy_returns.items():
            start = max(0, t - lookback)
            perf_hist[s_name] = s_rets[start:t] if t > 0 else []

        result = select_strategy(regime, perf_hist, exploration_rate=0.05)
        chosen = result["selected_strategy"]

        if chosen != last_strategy:
            switches += 1
            last_strategy = chosen

        period_ret = strategy_returns.get(chosen, [0.0] * n_periods)[t] if t < len(strategy_returns.get(chosen, [])) else 0.0
        cumulative += period_ret
        returns_list.append(period_ret)

        period_results.append({
            "period": t,
            "regime": regime,
            "strategy": chosen,
            "return": round(period_ret, 4),
        })

    avg_ret = sum(returns_list) / len(returns_list) if returns_list else 0
    std_ret = math.sqrt(sum((r - avg_ret) ** 2 for r in returns_list) / max(len(returns_list) - 1, 1)) if len(returns_list) > 1 else 1
    sharpe = round(avg_ret / std_ret * math.sqrt(252), 3) if std_ret > 0 else 0

    return {
        "total_return": round(cumulative, 4),
        "sharpe_proxy": sharpe,
        "strategy_switches": switches,
        "periods": n_periods,
        "avg_return": round(avg_ret, 6),
    }
