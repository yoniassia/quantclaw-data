"""
Bitcoin Miner Revenue Tracker — Monitor mining economics, hash rate, and profitability.

Tracks miner revenue (block rewards + fees), hash rate trends, difficulty adjustments,
hash price, and mining profitability metrics. Key signal for BTC market structure.

Data sources: Blockchain.com API, mempool.space API (all free, no key required).
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _fetch_text(url: str, timeout: int = 15) -> str:
    """Fetch plain text from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode().strip()


def get_mining_stats() -> Dict:
    """
    Get current Bitcoin mining statistics from blockchain.com.

    Returns hash_rate, difficulty, block_reward, estimated_btc_mined_per_day,
    and network stats.
    """
    stats_url = "https://api.blockchain.info/stats"
    stats = _fetch_json(stats_url)

    hash_rate_eh = stats.get("hash_rate", 0) / 1e9  # Convert to EH/s
    difficulty = stats.get("difficulty", 0)
    market_price = stats.get("market_price_usd", 0)
    n_blocks = stats.get("n_blocks_total", 0)
    minutes_between = stats.get("minutes_between_blocks", 0)

    # Current block reward (halving every 210,000 blocks)
    halvings = n_blocks // 210000
    block_reward = 50 / (2 ** halvings)

    # Blocks per day estimate
    blocks_per_day = 1440 / minutes_between if minutes_between > 0 else 144

    # Daily miner revenue estimate
    daily_btc = blocks_per_day * block_reward
    daily_revenue_usd = daily_btc * market_price

    # Fee revenue (from stats)
    total_fees_btc = stats.get("total_fees_btc", 0) / 1e8  # satoshis to BTC

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "hash_rate_eh_s": round(hash_rate_eh, 2),
        "difficulty": difficulty,
        "block_reward_btc": block_reward,
        "blocks_per_day": round(blocks_per_day, 1),
        "daily_btc_mined": round(daily_btc, 2),
        "daily_revenue_usd": round(daily_revenue_usd, 0),
        "btc_price_usd": market_price,
        "minutes_between_blocks": round(minutes_between, 2),
        "total_blocks": n_blocks,
        "halvings_occurred": halvings,
        "next_halving_block": (halvings + 1) * 210000,
        "blocks_until_halving": (halvings + 1) * 210000 - n_blocks,
        "summary": f"Hash rate: {hash_rate_eh:.1f} EH/s | Difficulty: {difficulty:.2e} | "
                   f"Daily revenue: ${daily_revenue_usd:,.0f} ({daily_btc:.1f} BTC) | "
                   f"Next halving in {(halvings + 1) * 210000 - n_blocks:,} blocks"
    }


def get_mempool_stats() -> Dict:
    """
    Get current mempool statistics from mempool.space.

    Returns mempool size, fee estimates, and transaction backlog info.
    """
    # Mempool stats
    mempool_url = "https://mempool.space/api/mempool"
    mempool = _fetch_json(mempool_url)

    # Fee estimates
    fees_url = "https://mempool.space/api/v1/fees/recommended"
    fees = _fetch_json(fees_url)

    # Difficulty adjustment
    diff_url = "https://mempool.space/api/v1/difficulty-adjustment"
    diff = _fetch_json(diff_url)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "mempool_count": mempool.get("count", 0),
        "mempool_size_mb": round(mempool.get("vsize", 0) / 1e6, 2),
        "total_fee_btc": round(mempool.get("total_fee", 0) / 1e8, 4),
        "fees_sat_vb": {
            "fastest": fees.get("fastestFee", 0),
            "half_hour": fees.get("halfHourFee", 0),
            "hour": fees.get("hourFee", 0),
            "economy": fees.get("economyFee", 0),
            "minimum": fees.get("minimumFee", 0)
        },
        "difficulty_adjustment": {
            "progress_pct": round(diff.get("progressPercent", 0), 2),
            "change_pct": round(diff.get("difficultyChange", 0), 2),
            "estimated_retarget": diff.get("estimatedRetargetDate"),
            "remaining_blocks": diff.get("remainingBlocks", 0)
        },
        "summary": f"Mempool: {mempool.get('count', 0):,} txs ({mempool.get('vsize', 0) / 1e6:.1f} MB) | "
                   f"Fastest fee: {fees.get('fastestFee', 0)} sat/vB | "
                   f"Next difficulty: {diff.get('difficultyChange', 0):+.2f}%"
    }


def get_hash_rate_history(timespan: str = "1year") -> List[Dict]:
    """
    Fetch historical hash rate data from blockchain.com.

    Args:
        timespan: Time period (e.g., '30days', '60days', '1year', '2years')

    Returns list of daily hash rate values.
    """
    url = f"https://api.blockchain.info/charts/hash-rate?timespan={timespan}&format=json"
    data = _fetch_json(url)

    results = []
    for point in data.get("values", []):
        results.append({
            "timestamp": datetime.utcfromtimestamp(point["x"]).isoformat(),
            "hash_rate_th_s": point["y"],
            "hash_rate_eh_s": round(point["y"] / 1e9, 2)
        })

    return results


def get_miner_revenue_history(timespan: str = "1year") -> List[Dict]:
    """
    Fetch historical daily miner revenue from blockchain.com.

    Args:
        timespan: Time period (e.g., '30days', '1year')

    Returns list of daily miner revenue in USD.
    """
    url = f"https://api.blockchain.info/charts/miners-revenue?timespan={timespan}&format=json"
    data = _fetch_json(url)

    results = []
    for point in data.get("values", []):
        results.append({
            "timestamp": datetime.utcfromtimestamp(point["x"]).isoformat(),
            "revenue_usd": point["y"]
        })

    return results


def get_mining_dashboard() -> Dict:
    """
    Comprehensive Bitcoin mining dashboard combining all metrics.

    Returns mining stats, mempool state, fee environment, and health indicators.
    """
    mining = get_mining_stats()
    mempool = get_mempool_stats()

    # Hash price: revenue per EH/s per day
    hash_price = (mining["daily_revenue_usd"] / mining["hash_rate_eh_s"]
                  if mining["hash_rate_eh_s"] > 0 else 0)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "mining": mining,
        "mempool": mempool,
        "hash_price_usd_per_eh": round(hash_price, 0),
        "health_indicators": {
            "blocks_on_schedule": mining["minutes_between_blocks"] < 11,
            "mempool_congested": mempool["mempool_count"] > 50000,
            "fees_elevated": mempool["fees_sat_vb"]["fastest"] > 50,
            "halving_proximity": mining["blocks_until_halving"] < 10000
        }
    }
