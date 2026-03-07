#!/usr/bin/env python3
"""
DefiLlama API — DeFi TVL, yields, chains, stablecoins
DefiLlama aggregates on-chain DeFi data across protocols and chains — TVL, yields, volumes.

Source: https://defillama.com/docs/api
Category: Crypto & DeFi On-Chain
Free tier: true - No API key required.
"""

import requests
from typing import Dict, List, Any
import json
from datetime import datetime

BASE_URL = "https://api.llama.fi"
YIELDS_URL = "https://yields.llama.fi"

def get_protocols(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch list of DeFi protocols sorted by TVL.
    
    Args:
        limit: Number of protocols to return (default 100)
    
    Returns:
        List of protocol dicts with 'name', 'tvl', 'change_1d', 'chains', etc.
    """
    try:
        params = {'limit': limit}
        resp = requests.get(f"{BASE_URL}/protocols", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching protocols: {e}")
        return []

def get_protocol_tvl(protocol: str, include_history: bool = False) -> Dict[str, Any]:
    """
    Fetch TVL and metrics for a specific protocol.
    
    Args:
        protocol: Protocol slug (e.g., 'aave', 'uniswap')
        include_history: If True, includes TVL history (larger response)
    
    Returns:
        Dict with 'tvl', 'change_1d', 'chains', etc.
    """
    try:
        url = f"{BASE_URL}/protocol/{protocol}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "protocol": protocol,
            "tvl": data.get("tvl", 0),
            "change_1d": data.get("change_1d", 0),
            "change_7d": data.get("change_7d", 0),
            "chains": data.get("chains", []),
            "full_data": data
        }
    except requests.RequestException as e:
        print(f"Error fetching protocol {protocol}: {e}")
        return {}

def get_chains() -> List[Dict[str, Any]]:
    """Fetch list of chains with TVL rankings."""
    try:
        resp = requests.get(f"{BASE_URL}/chains", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching chains: {e}")
        return []

def get_yields(pool_limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch top yield-bearing pools.
    
    Args:
        pool_limit: Limit number of pools (default 100)
    
    Returns:
        List of pool dicts with 'apy', 'tvl', 'pool', etc.
    """
    try:
        params = {'poolLimit': pool_limit}
        resp = requests.get(f"{YIELDS_URL}/pools", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching yields: {e}")
        return []

def get_stablecoin_stats(chain: str = None) -> Dict[str, Any]:
    """
    Fetch stablecoin issuance, market cap, transfers.
    
    Args:
        chain: Filter by chain slug (e.g., 'Ethereum'); None for all
    
    Returns:
        Dict with pegged USD TVL, market cap deviation, 24h transfers, etc.
    """
    try:
        url = f"{BASE_URL}/stablecoins"
        if chain:
            url += f"/{chain}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching stablecoins: {e}")
        return {}

if __name__ == "__main__":
    print(json.dumps({
        "module": "defillama_api",
        "status": "ready",
        "source": "https://defillama.com/docs/api",
        "functions": ["get_protocols", "get_protocol_tvl", "get_chains", "get_yields", "get_stablecoin_stats"]
    }, indent=2))
