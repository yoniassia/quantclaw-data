"""
MEV Detection Engine — Detect Maximal Extractable Value activity on-chain.

Monitors for sandwich attacks, front-running, back-running, and arbitrage
on Ethereum and L2s. Uses public mempool data and block analysis via
free APIs (Flashbots, Etherscan, block explorers).

Roadmap item #305.
"""

import json
import urllib.request
from typing import Dict, List, Optional
from datetime import datetime


KNOWN_MEV_BOTS = [
    "0x98C3d3183C4b8A650614ad179A1a98be0a8d6B8E",  # jaredfromsubway.eth
    "0x6b75d8AF000000e20B7a7DDf000Ba900b4009A80",  # Flashbots builder
    "0xDAFEA492D9c6733ae3d56b7Ed1ADB60692c98Bc5",  # Flashbots coinbase
]


def get_flashbots_blocks(limit: int = 10) -> List[Dict]:
    """
    Fetch recent Flashbots bundle data to identify MEV extraction.

    Args:
        limit: Number of recent blocks to analyze

    Returns:
        List of blocks with MEV bundle information
    """
    url = "https://blocks.flashbots.net/v1/blocks?limit=" + str(min(limit, 100))
    results = []

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        for block in data.get("blocks", [])[:limit]:
            total_mev = sum(
                float(b.get("coinbase_transfer", 0)) / 1e18
                for b in block.get("transactions", [])
            )
            results.append({
                "block_number": block.get("block_number"),
                "miner_reward_eth": round(float(block.get("miner_reward", 0)) / 1e18, 6),
                "total_mev_eth": round(total_mev, 6),
                "bundle_count": len(block.get("transactions", [])),
                "gas_used": block.get("gas_used", 0),
                "gas_price_gwei": round(float(block.get("gas_price", 0)) / 1e9, 2),
                "timestamp": block.get("timestamp", ""),
            })
    except Exception as e:
        results.append({"error": str(e)})

    return results


def detect_sandwich_pattern(transactions: List[Dict]) -> List[Dict]:
    """
    Analyze a list of transactions for sandwich attack patterns.

    A sandwich attack: Bot front-runs a victim swap (buy), victim executes
    at worse price, bot back-runs (sell) for profit.

    Args:
        transactions: List of tx dicts with 'from', 'to', 'value', 'input', 'index'

    Returns:
        List of detected sandwich patterns with attacker, victim, profit estimate
    """
    sandwiches = []
    swap_sigs = ["0x38ed1739", "0x8803dbee", "0x7ff36ab5", "0x18cbafe5", "0x5c11d795"]

    swap_txs = []
    for tx in transactions:
        input_data = tx.get("input", "")[:10]
        if input_data in swap_sigs:
            swap_txs.append(tx)

    for i in range(len(swap_txs) - 2):
        tx_a = swap_txs[i]
        tx_b = swap_txs[i + 1]
        tx_c = swap_txs[i + 2]

        # Pattern: same sender for A and C, different sender for B
        if (tx_a.get("from", "").lower() == tx_c.get("from", "").lower() and
                tx_a.get("from", "").lower() != tx_b.get("from", "").lower() and
                tx_a.get("to", "").lower() == tx_c.get("to", "").lower()):
            sandwiches.append({
                "type": "SANDWICH",
                "attacker": tx_a["from"],
                "victim": tx_b["from"],
                "frontrun_tx": tx_a.get("hash", ""),
                "victim_tx": tx_b.get("hash", ""),
                "backrun_tx": tx_c.get("hash", ""),
                "router": tx_a.get("to", ""),
                "confidence": "HIGH",
                "detected_at": datetime.utcnow().isoformat(),
            })

    return sandwiches


def classify_mev_type(tx: Dict) -> Dict:
    """
    Classify a transaction's MEV type based on its characteristics.

    Args:
        tx: Transaction dict with from, to, value, gas_price, input

    Returns:
        Classification with MEV type, confidence, and explanation
    """
    from_addr = tx.get("from", "").lower()
    to_addr = tx.get("to", "").lower()
    gas_price = tx.get("gas_price", 0)
    value = tx.get("value", 0)
    input_data = tx.get("input", "")

    is_known_bot = any(bot.lower() == from_addr for bot in KNOWN_MEV_BOTS)

    # Flashbots bundle (0 gas price or coinbase transfer)
    if gas_price == 0 and input_data and len(input_data) > 10:
        return {
            "mev_type": "FLASHBOTS_BUNDLE",
            "confidence": "HIGH" if is_known_bot else "MEDIUM",
            "is_known_bot": is_known_bot,
            "explanation": "Zero gas price transaction likely submitted via Flashbots",
        }

    # Arbitrage pattern (complex input, no ETH value, known router)
    arb_routers = ["0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45"]  # Uniswap Universal
    if to_addr in [r.lower() for r in arb_routers] and value == 0 and len(input_data) > 200:
        return {
            "mev_type": "ARBITRAGE",
            "confidence": "MEDIUM",
            "is_known_bot": is_known_bot,
            "explanation": "Complex router call with no ETH value suggests arbitrage",
        }

    # Liquidation
    liquidation_sigs = ["0x00f714ce", "0x96b64a8c", "0xe8eda9df"]
    if input_data[:10] in liquidation_sigs:
        return {
            "mev_type": "LIQUIDATION",
            "confidence": "HIGH",
            "is_known_bot": is_known_bot,
            "explanation": "Transaction calls a known liquidation function",
        }

    return {
        "mev_type": "UNKNOWN",
        "confidence": "LOW",
        "is_known_bot": is_known_bot,
        "explanation": "Could not classify MEV type from available data",
    }


def get_mev_stats_summary() -> Dict:
    """
    Get a summary of recent MEV activity from Flashbots.

    Returns:
        Summary with total MEV extracted, avg per block, top strategies
    """
    blocks = get_flashbots_blocks(limit=50)
    valid = [b for b in blocks if "error" not in b]

    if not valid:
        return {"error": "No block data available"}

    total_mev = sum(b.get("total_mev_eth", 0) for b in valid)
    total_bundles = sum(b.get("bundle_count", 0) for b in valid)

    return {
        "blocks_analyzed": len(valid),
        "total_mev_eth": round(total_mev, 4),
        "avg_mev_per_block_eth": round(total_mev / len(valid), 6) if valid else 0,
        "total_bundles": total_bundles,
        "avg_bundles_per_block": round(total_bundles / len(valid), 1) if valid else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
