#!/usr/bin/env python3
"""
Dune Analytics API — On-Chain Blockchain Data Queries

Provides SQL-based querying of blockchain data across Ethereum, Polygon, and other chains.
Supports DeFi protocol analytics, transaction analysis, and smart contract events.

Source: https://dune.com/docs/api/
Category: Crypto & DeFi On-Chain
Free tier: 1,000 query credits/month, 10 queries/minute
Update frequency: real-time
"""

import os
import requests
import time
from typing import Optional, Dict, List, Any

DUNE_API_KEY = os.getenv("DUNE_API_KEY", "")
BASE_URL = "https://api.dune.com/api/v1"

def execute_query(query_id: int, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Execute a Dune query by ID.
    
    Args:
        query_id: Dune query ID (from dashboard URL)
        params: Optional query parameters dict
    
    Returns:
        dict with execution_id and state
    """
    if not DUNE_API_KEY:
        return {"error": "DUNE_API_KEY environment variable not set"}
    
    url = f"{BASE_URL}/query/{query_id}/execute"
    headers = {"X-Dune-API-Key": DUNE_API_KEY}
    payload = {"parameters": params or {}}
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    Check execution status.
    
    Args:
        execution_id: Execution ID from execute_query
    
    Returns:
        dict with state (PENDING/EXECUTING/COMPLETED/FAILED)
    """
    if not DUNE_API_KEY:
        return {"error": "DUNE_API_KEY not set"}
    
    url = f"{BASE_URL}/execution/{execution_id}/status"
    headers = {"X-Dune-API-Key": DUNE_API_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_execution_results(execution_id: str) -> Dict[str, Any]:
    """
    Retrieve execution results.
    
    Args:
        execution_id: Execution ID from execute_query
    
    Returns:
        dict with rows, metadata, state
    """
    if not DUNE_API_KEY:
        return {"error": "DUNE_API_KEY not set"}
    
    url = f"{BASE_URL}/execution/{execution_id}/results"
    headers = {"X-Dune-API-Key": DUNE_API_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract rows from nested result structure
        if "result" in data and "rows" in data["result"]:
            return {
                "rows": data["result"]["rows"],
                "metadata": data["result"].get("metadata", {}),
                "state": data.get("state", "UNKNOWN")
            }
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def run_query_sync(query_id: int, params: Optional[Dict] = None, max_wait: int = 120) -> Dict[str, Any]:
    """
    Execute query and wait for results (blocking).
    
    Args:
        query_id: Dune query ID
        params: Optional query parameters
        max_wait: Max seconds to wait for completion
    
    Returns:
        dict with rows and metadata
    """
    # Start execution
    exec_resp = execute_query(query_id, params)
    if "error" in exec_resp:
        return exec_resp
    
    execution_id = exec_resp.get("execution_id")
    if not execution_id:
        return {"error": "No execution_id returned"}
    
    # Poll for completion
    start = time.time()
    while time.time() - start < max_wait:
        status = get_execution_status(execution_id)
        state = status.get("state", "UNKNOWN")
        
        if state == "QUERY_STATE_COMPLETED":
            return get_execution_results(execution_id)
        elif state == "QUERY_STATE_FAILED":
            return {"error": "Query execution failed", "status": status}
        
        time.sleep(2)  # Respect rate limits
    
    return {"error": "Query timeout", "execution_id": execution_id}


def get_latest_blocks(chain: str = "ethereum", limit: int = 10) -> List[Dict]:
    """
    Example: Get latest blocks for a chain.
    Uses a public Dune query (customize query_id for your use case).
    
    Args:
        chain: Blockchain name (ethereum, polygon, etc)
        limit: Number of blocks to fetch
    
    Returns:
        List of block dicts
    """
    # NOTE: Replace with actual public query ID or your own
    # This is a placeholder - real query IDs come from dune.com/queries
    query_id = 1  # PLACEHOLDER
    params = {"chain": chain, "limit": limit}
    
    result = run_query_sync(query_id, params)
    return result.get("rows", [])


def get_dex_volume(protocol: str = "uniswap", days: int = 7) -> Dict[str, Any]:
    """
    Example: Get DEX trading volume.
    
    Args:
        protocol: DEX protocol name
        days: Days of history
    
    Returns:
        dict with volume metrics
    """
    # NOTE: Use actual Dune query ID for DEX volume
    query_id = 2  # PLACEHOLDER
    params = {"protocol": protocol, "days": days}
    
    result = run_query_sync(query_id, params)
    if "error" in result:
        return result
    
    rows = result.get("rows", [])
    if rows:
        return {
            "protocol": protocol,
            "total_volume": sum(r.get("volume", 0) for r in rows),
            "rows": rows
        }
    return {"error": "No data returned"}


if __name__ == "__main__":
    import json
    
    # Test: query execution status check
    if DUNE_API_KEY:
        print("Dune Analytics API module loaded")
        print(f"API Key configured: {DUNE_API_KEY[:8]}...")
    else:
        print(json.dumps({
            "module": "dune_analytics_api",
            "status": "ready",
            "error": "Set DUNE_API_KEY environment variable",
            "docs": "https://dune.com/docs/api/"
        }, indent=2))
