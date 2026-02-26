"""
DeFi Yield Optimizer — Compare yields across DeFi protocols.

Aggregates yield data from major DeFi protocols (Aave, Compound, MakerDAO,
Lido, Curve, Convex) via DeFi Llama Yields API. Ranks by risk-adjusted
returns, identifies best opportunities per asset class.

Roadmap item #303.
"""

import json
import urllib.request
from typing import Dict, List, Optional


def get_top_yields(
    chain: Optional[str] = None,
    stablecoin_only: bool = False,
    min_tvl: float = 1_000_000,
    limit: int = 25,
) -> List[Dict]:
    """
    Fetch top DeFi yields across all protocols via DeFi Llama.

    Args:
        chain: Filter by chain (ethereum, polygon, arbitrum, base, etc.) or None for all
        stablecoin_only: Only show stablecoin pools
        min_tvl: Minimum TVL in USD to filter noise
        limit: Max results

    Returns:
        List of yield opportunities sorted by APY
    """
    url = "https://yields.llama.fi/pools"
    results = []

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        for pool in data.get("data", []):
            tvl = pool.get("tvlUsd", 0) or 0
            if tvl < min_tvl:
                continue
            if chain and pool.get("chain", "").lower() != chain.lower():
                continue
            if stablecoin_only and not pool.get("stablecoin", False):
                continue

            apy = pool.get("apy", 0) or 0
            if apy <= 0 or apy > 1000:  # filter unrealistic yields
                continue

            results.append({
                "protocol": pool.get("project", ""),
                "chain": pool.get("chain", ""),
                "symbol": pool.get("symbol", ""),
                "pool_id": pool.get("pool", ""),
                "apy_total": round(apy, 2),
                "apy_base": round(pool.get("apyBase", 0) or 0, 2),
                "apy_reward": round(pool.get("apyReward", 0) or 0, 2),
                "tvl_usd": round(tvl, 0),
                "stablecoin": pool.get("stablecoin", False),
                "il_risk": pool.get("ilRisk", "unknown"),
                "exposure": pool.get("exposure", "single"),
                "apy_mean_30d": round(pool.get("apyMean30d", 0) or 0, 2),
            })

        results.sort(key=lambda x: x["apy_total"], reverse=True)
        return results[:limit]
    except Exception as e:
        return [{"error": str(e)}]


def compare_protocol_yields(
    asset: str = "USDC",
    chains: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Compare yields for a specific asset across protocols.

    Args:
        asset: Token symbol to compare (USDC, ETH, WBTC, etc.)
        chains: Filter by chains or None for all

    Returns:
        List of protocol yields for the asset, sorted by APY
    """
    url = "https://yields.llama.fi/pools"
    results = []
    asset_upper = asset.upper()

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        for pool in data.get("data", []):
            symbol = pool.get("symbol", "").upper()
            if asset_upper not in symbol:
                continue
            if chains and pool.get("chain", "").lower() not in [c.lower() for c in chains]:
                continue
            tvl = pool.get("tvlUsd", 0) or 0
            if tvl < 100_000:
                continue

            results.append({
                "protocol": pool.get("project", ""),
                "chain": pool.get("chain", ""),
                "symbol": symbol,
                "apy_total": round(pool.get("apy", 0) or 0, 2),
                "apy_base": round(pool.get("apyBase", 0) or 0, 2),
                "tvl_usd": round(tvl, 0),
                "pool_type": pool.get("exposure", "single"),
            })

        results.sort(key=lambda x: x["apy_total"], reverse=True)
    except Exception as e:
        results.append({"error": str(e)})

    return results


def yield_risk_score(apy: float, tvl: float, is_stablecoin: bool, apy_30d_mean: float) -> Dict:
    """
    Calculate a risk-adjusted yield score.

    Args:
        apy: Current APY percentage
        tvl: Total value locked in USD
        is_stablecoin: Whether pool is stablecoin-only
        apy_30d_mean: 30-day mean APY for stability check

    Returns:
        Risk assessment with score, category, and flags
    """
    score = 50.0  # base score

    # TVL factor (higher TVL = lower risk)
    if tvl > 100_000_000:
        score += 20
    elif tvl > 10_000_000:
        score += 10
    elif tvl < 1_000_000:
        score -= 15

    # Stablecoin bonus
    if is_stablecoin:
        score += 10

    # Yield sustainability (compare current vs 30d mean)
    if apy_30d_mean > 0:
        volatility_ratio = abs(apy - apy_30d_mean) / apy_30d_mean
        if volatility_ratio > 0.5:
            score -= 15  # highly volatile yield
        elif volatility_ratio < 0.1:
            score += 10  # stable yield

    # Unrealistic yield penalty
    if apy > 100:
        score -= 20
    if apy > 500:
        score -= 30

    score = max(0, min(100, score))

    flags = []
    if apy > 100:
        flags.append("HIGH_YIELD_WARNING")
    if tvl < 1_000_000:
        flags.append("LOW_TVL")
    if apy_30d_mean > 0 and apy > apy_30d_mean * 2:
        flags.append("YIELD_SPIKE")

    category = "HIGH_RISK" if score < 30 else "MODERATE" if score < 60 else "LOW_RISK"

    return {
        "risk_score": round(score, 1),
        "category": category,
        "flags": flags,
        "yield_sustainability": "stable" if apy_30d_mean > 0 and abs(apy - apy_30d_mean) / apy_30d_mean < 0.2 else "volatile",
    }
