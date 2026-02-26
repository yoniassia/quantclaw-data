"""Bitcoin Miner Revenue Tracker — Monitor mining economics and miner health.

Tracks hashrate, difficulty, miner revenue, hash price, and miner capitulation
signals using free public blockchain data.

Data sources: Blockchain.info API (free), mempool.space API (free).
Roadmap item #316.
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any


def get_mining_stats() -> dict[str, Any]:
    """Fetch current Bitcoin mining statistics.

    Returns:
        Dict with hashrate, difficulty, block_reward, fees, and estimated miner revenue.
    """
    stats = {}
    endpoints = {
        "hashrate": "https://blockchain.info/q/hashrate",
        "difficulty": "https://blockchain.info/q/getdifficulty",
        "block_count": "https://blockchain.info/q/getblockcount",
        "total_btc": "https://blockchain.info/q/totalbc",
    }
    for key, url in endpoints.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                val = resp.read().decode().strip()
            stats[key] = float(val)
        except Exception:
            stats[key] = None

    # Get BTC price for USD revenue calc
    try:
        url = "https://blockchain.info/ticker"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ticker = json.loads(resp.read())
        stats["btc_price_usd"] = ticker.get("USD", {}).get("last", 0)
    except Exception:
        stats["btc_price_usd"] = None

    # Block subsidy (halving schedule)
    if stats.get("block_count"):
        halvings = int(stats["block_count"]) // 210000
        stats["block_subsidy_btc"] = 50 / (2 ** halvings)
    else:
        stats["block_subsidy_btc"] = 3.125  # Post-2024 halving default

    # Hash price estimate (USD per TH/s per day)
    if stats.get("hashrate") and stats.get("btc_price_usd") and stats.get("block_subsidy_btc"):
        daily_blocks = 144
        daily_btc = daily_blocks * stats["block_subsidy_btc"]
        daily_revenue_usd = daily_btc * stats["btc_price_usd"]
        hashrate_th = stats["hashrate"] / 1e6  # Convert GH/s to TH/s... blockchain.info returns GH/s
        if hashrate_th > 0:
            stats["hash_price_usd_per_th"] = round(daily_revenue_usd / hashrate_th, 6)

    stats["timestamp"] = datetime.now(timezone.utc).isoformat()
    return stats


def get_mempool_stats() -> dict[str, Any]:
    """Fetch Bitcoin mempool statistics for fee revenue estimation.

    Returns:
        Dict with mempool size, fee estimates, and transaction count.
    """
    try:
        url = "https://mempool.space/api/mempool"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return {
            "tx_count": data.get("count", 0),
            "vsize_bytes": data.get("vsize", 0),
            "total_fee_btc": round(data.get("total_fee", 0) / 1e8, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def miner_health_assessment() -> dict[str, Any]:
    """Assess overall Bitcoin miner health and capitulation risk.

    Combines hashrate trends, hash price, and difficulty to gauge miner stress.
    """
    stats = get_mining_stats()
    mempool = get_mempool_stats()

    assessment = {
        "mining_stats": stats,
        "mempool": mempool,
    }

    hash_price = stats.get("hash_price_usd_per_th")
    if hash_price is not None:
        # Rough thresholds for miner profitability
        if hash_price < 0.04:
            assessment["miner_stress"] = "critical"
            assessment["signal"] = "capitulation_risk"
        elif hash_price < 0.06:
            assessment["miner_stress"] = "elevated"
            assessment["signal"] = "marginal_miners_squeezed"
        elif hash_price < 0.10:
            assessment["miner_stress"] = "moderate"
            assessment["signal"] = "healthy"
        else:
            assessment["miner_stress"] = "low"
            assessment["signal"] = "highly_profitable"

    assessment["timestamp"] = datetime.now(timezone.utc).isoformat()
    return assessment
