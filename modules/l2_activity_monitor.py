"""Layer 2 Activity Monitor — tracks L2 rollup metrics across Arbitrum, Optimism, Base, and more.

Monitors transaction counts, TVL, active addresses, gas costs, and bridge
activity on major Ethereum L2 networks using free public APIs and RPC endpoints.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# L2 network metadata
L2_NETWORKS = {
    "arbitrum": {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "explorer_api": "https://api.arbiscan.io/api",
        "l2beat_slug": "arbitrum",
        "token": "ARB",
        "type": "optimistic_rollup",
    },
    "optimism": {
        "name": "Optimism",
        "chain_id": 10,
        "explorer_api": "https://api-optimistic.etherscan.io/api",
        "l2beat_slug": "optimism",
        "token": "OP",
        "type": "optimistic_rollup",
    },
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "explorer_api": "https://api.basescan.org/api",
        "l2beat_slug": "base",
        "token": "ETH",
        "type": "optimistic_rollup",
    },
    "zksync": {
        "name": "zkSync Era",
        "chain_id": 324,
        "explorer_api": "https://block-explorer-api.mainnet.zksync.io/api",
        "l2beat_slug": "zksync-era",
        "token": "ZK",
        "type": "zk_rollup",
    },
    "polygon_zkevm": {
        "name": "Polygon zkEVM",
        "chain_id": 1101,
        "explorer_api": "https://api-zkevm.polygonscan.com/api",
        "l2beat_slug": "polygonzkevm",
        "token": "MATIC",
        "type": "zk_rollup",
    },
    "starknet": {
        "name": "StarkNet",
        "chain_id": -1,
        "l2beat_slug": "starknet",
        "token": "STRK",
        "type": "zk_rollup",
    },
    "linea": {
        "name": "Linea",
        "chain_id": 59144,
        "l2beat_slug": "linea",
        "token": "ETH",
        "type": "zk_rollup",
    },
    "scroll": {
        "name": "Scroll",
        "chain_id": 534352,
        "l2beat_slug": "scroll",
        "token": "ETH",
        "type": "zk_rollup",
    },
}


def get_l2_tvl_data() -> Dict[str, Any]:
    """Fetch TVL data for all L2 networks from L2Beat/DeFiLlama.
    
    Returns:
        Dictionary with TVL data per network and aggregate stats.
    """
    results = {}
    total_tvl = 0
    
    try:
        url = "https://l2beat.com/api/scaling/tvl"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, dict) and "data" in data:
                for project in data.get("data", []):
                    slug = project.get("slug", "")
                    for key, net in L2_NETWORKS.items():
                        if net["l2beat_slug"] == slug:
                            tvl = project.get("tvl", {}).get("breakdown", {})
                            total = sum(tvl.values()) if isinstance(tvl, dict) else project.get("tvl", 0)
                            results[key] = {
                                "name": net["name"],
                                "tvl_usd": total,
                                "type": net["type"],
                            }
                            total_tvl += total if isinstance(total, (int, float)) else 0
    except Exception as e:
        # Fallback: try DeFiLlama
        try:
            url = "https://api.llama.fi/v2/chains"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                chains = json.loads(resp.read().decode())
                chain_map = {
                    "Arbitrum": "arbitrum", "Optimism": "optimism", "Base": "base",
                    "zkSync Era": "zksync", "Polygon zkEVM": "polygon_zkevm",
                    "Starknet": "starknet", "Linea": "linea", "Scroll": "scroll",
                }
                for chain in chains:
                    name = chain.get("name", "")
                    if name in chain_map:
                        key = chain_map[name]
                        tvl = chain.get("tvl", 0)
                        results[key] = {
                            "name": name,
                            "tvl_usd": tvl,
                            "type": L2_NETWORKS[key]["type"],
                        }
                        total_tvl += tvl
        except Exception as e2:
            return {"error": f"Failed to fetch TVL: {e}, fallback: {e2}"}
    
    return {
        "networks": results,
        "total_l2_tvl": total_tvl,
        "network_count": len(results),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_network_activity(network: str = "arbitrum") -> Dict[str, Any]:
    """Get activity metrics for a specific L2 network.
    
    Args:
        network: Network key (arbitrum, optimism, base, zksync, etc.).
        
    Returns:
        Activity metrics including tx count estimates, gas savings.
    """
    if network not in L2_NETWORKS:
        return {"error": f"Unknown network: {network}", "available": list(L2_NETWORKS.keys())}
    
    net = L2_NETWORKS[network]
    result = {
        "network": net["name"],
        "chain_id": net["chain_id"],
        "type": net["type"],
        "native_token": net["token"],
    }
    
    # Try explorer API for basic stats
    if "explorer_api" in net:
        try:
            url = f"{net['explorer_api']}?module=proxy&action=eth_blockNumber"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get("result"):
                    block_num = int(data["result"], 16)
                    result["latest_block"] = block_num
        except Exception:
            pass
        
        try:
            url = f"{net['explorer_api']}?module=proxy&action=eth_gasPrice"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get("result"):
                    gas_wei = int(data["result"], 16)
                    result["gas_price_gwei"] = round(gas_wei / 1e9, 4)
        except Exception:
            pass
    
    result["timestamp"] = datetime.utcnow().isoformat()
    return result


def compare_l2_networks(metrics: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compare all L2 networks side by side.
    
    Args:
        metrics: Optional list of metrics to compare (default: all available).
        
    Returns:
        Comparison table with rankings.
    """
    tvl_data = get_l2_tvl_data()
    networks = tvl_data.get("networks", {})
    
    comparison = []
    for key, net_info in L2_NETWORKS.items():
        entry = {
            "network": net_info["name"],
            "key": key,
            "type": net_info["type"],
            "token": net_info["token"],
        }
        if key in networks:
            entry["tvl_usd"] = networks[key].get("tvl_usd", 0)
        else:
            entry["tvl_usd"] = 0
        comparison.append(entry)
    
    # Rank by TVL
    comparison.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
    for i, entry in enumerate(comparison):
        entry["tvl_rank"] = i + 1
    
    # Type breakdown
    or_count = sum(1 for c in comparison if c["type"] == "optimistic_rollup")
    zk_count = sum(1 for c in comparison if c["type"] == "zk_rollup")
    
    return {
        "networks": comparison,
        "total_l2_tvl": tvl_data.get("total_l2_tvl", 0),
        "optimistic_rollups": or_count,
        "zk_rollups": zk_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_l2_gas_savings() -> Dict[str, Any]:
    """Estimate gas cost savings across L2 networks vs Ethereum L1.
    
    Returns:
        Gas cost comparison showing L2 savings ratios.
    """
    # Typical L1 gas prices and L2 equivalents
    l1_typical_gwei = 30  # Typical L1 gas price
    l1_transfer_gas = 21000
    l1_swap_gas = 150000
    
    l2_estimates = {
        "arbitrum": {"transfer_gwei": 0.1, "multiplier": 0.01},
        "optimism": {"transfer_gwei": 0.05, "multiplier": 0.008},
        "base": {"transfer_gwei": 0.03, "multiplier": 0.005},
        "zksync": {"transfer_gwei": 0.25, "multiplier": 0.015},
        "polygon_zkevm": {"transfer_gwei": 0.1, "multiplier": 0.01},
        "starknet": {"transfer_gwei": 0.2, "multiplier": 0.012},
        "linea": {"transfer_gwei": 0.15, "multiplier": 0.01},
        "scroll": {"transfer_gwei": 0.2, "multiplier": 0.012},
    }
    
    eth_price = 3000  # Approximate
    l1_transfer_cost = l1_typical_gwei * l1_transfer_gas * 1e-9 * eth_price
    l1_swap_cost = l1_typical_gwei * l1_swap_gas * 1e-9 * eth_price
    
    savings = []
    for key, est in l2_estimates.items():
        l2_transfer = l1_transfer_cost * est["multiplier"]
        l2_swap = l1_swap_cost * est["multiplier"]
        savings.append({
            "network": L2_NETWORKS[key]["name"],
            "l2_transfer_cost_usd": round(l2_transfer, 4),
            "l2_swap_cost_usd": round(l2_swap, 4),
            "transfer_savings_pct": round((1 - est["multiplier"]) * 100, 1),
            "swap_savings_pct": round((1 - est["multiplier"]) * 100, 1),
        })
    
    savings.sort(key=lambda x: x["transfer_savings_pct"], reverse=True)
    
    return {
        "l1_reference": {
            "gas_price_gwei": l1_typical_gwei,
            "transfer_cost_usd": round(l1_transfer_cost, 2),
            "swap_cost_usd": round(l1_swap_cost, 2),
            "eth_price_usd": eth_price,
        },
        "l2_savings": savings,
        "cheapest_transfer": savings[0]["network"] if savings else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
