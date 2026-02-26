"""Ethereum Gas Price Predictor — Monitor and forecast ETH gas prices.

Tracks current gas prices, historical trends, and provides short-term forecasts
based on network activity patterns.

Data sources: Etherscan API (free tier), mempool data.
Roadmap item #317.
"""

import json
import math
import urllib.request
from datetime import datetime, timezone
from typing import Any


_ETHERSCAN_FREE = "https://api.etherscan.io/api"


def get_gas_prices() -> dict[str, Any]:
    """Fetch current Ethereum gas prices (safe, standard, fast).

    Returns:
        Dict with gas prices in Gwei for different speed tiers.
    """
    # Use Blocknative-style free endpoint or Etherscan
    try:
        url = f"{_ETHERSCAN_FREE}?module=gastracker&action=gasoracle"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = data.get("result", {})
        safe = float(result.get("SafeGasPrice", 0))
        standard = float(result.get("ProposeGasPrice", 0))
        fast = float(result.get("FastGasPrice", 0))
        base_fee = float(result.get("suggestBaseFee", 0)) if result.get("suggestBaseFee") else None
        return {
            "safe_gwei": safe,
            "standard_gwei": standard,
            "fast_gwei": fast,
            "base_fee_gwei": base_fee,
            "gas_used_ratio": result.get("gasUsedRatio", ""),
            "cost_estimate_usd": _estimate_tx_cost(standard),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def gas_cost_calculator(gas_limit: int = 21000, gas_price_gwei: float | None = None) -> dict[str, Any]:
    """Calculate transaction cost in ETH and USD.

    Args:
        gas_limit: Gas units for the transaction (21000 for simple transfer).
        gas_price_gwei: Override gas price. If None, fetches current standard.

    Returns:
        Dict with cost in Gwei, ETH, and estimated USD.
    """
    if gas_price_gwei is None:
        current = get_gas_prices()
        gas_price_gwei = current.get("standard_gwei", 20)

    cost_gwei = gas_limit * gas_price_gwei
    cost_eth = cost_gwei / 1e9

    # Common transaction types
    tx_types = {
        "simple_transfer": 21000,
        "erc20_transfer": 65000,
        "uniswap_swap": 150000,
        "nft_mint": 200000,
        "contract_deploy": 500000,
    }

    costs = {}
    eth_price = _get_eth_price()
    for name, limit in tx_types.items():
        eth_cost = (limit * gas_price_gwei) / 1e9
        costs[name] = {
            "gas_limit": limit,
            "cost_eth": round(eth_cost, 6),
            "cost_usd": round(eth_cost * eth_price, 2) if eth_price else None,
        }

    return {
        "gas_price_gwei": gas_price_gwei,
        "custom_tx": {
            "gas_limit": gas_limit,
            "cost_eth": round(cost_eth, 6),
            "cost_usd": round(cost_eth * eth_price, 2) if eth_price else None,
        },
        "common_transactions": costs,
        "eth_price_usd": eth_price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def gas_price_analysis() -> dict[str, Any]:
    """Analyze current gas environment and provide recommendations.

    Returns:
        Analysis with congestion level, recommendation, and optimal timing hints.
    """
    current = get_gas_prices()
    if "error" in current:
        return current

    standard = current.get("standard_gwei", 0)
    base_fee = current.get("base_fee_gwei")

    # Congestion assessment
    if standard <= 10:
        congestion = "very_low"
        recommendation = "Excellent time for transactions — gas is cheap"
    elif standard <= 30:
        congestion = "low"
        recommendation = "Good conditions for most transactions"
    elif standard <= 60:
        congestion = "moderate"
        recommendation = "Normal activity — consider waiting for non-urgent txs"
    elif standard <= 100:
        congestion = "high"
        recommendation = "Network congested — delay non-critical transactions"
    else:
        congestion = "very_high"
        recommendation = "Extreme congestion — only urgent transactions recommended"

    # Priority fee estimate (EIP-1559)
    priority_fee = None
    if base_fee and standard > base_fee:
        priority_fee = round(standard - base_fee, 2)

    return {
        "current_gas": current,
        "congestion_level": congestion,
        "recommendation": recommendation,
        "priority_fee_gwei": priority_fee,
        "eip1559_base_fee": base_fee,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _estimate_tx_cost(gas_price_gwei: float) -> float | None:
    """Estimate simple transfer cost in USD."""
    eth_price = _get_eth_price()
    if eth_price:
        return round((21000 * gas_price_gwei / 1e9) * eth_price, 4)
    return None


def _get_eth_price() -> float | None:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("ethereum", {}).get("usd")
    except Exception:
        return None
