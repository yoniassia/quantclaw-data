#!/usr/bin/env python3
"""
Covalent Unified API (GoldRush) — Blockchain Data Module

Unified blockchain data API for 50+ chains including Ethereum, Polygon, BSC, Arbitrum, Optimism, Base, and more.
Provides ERC-20 token balances, transaction histories, NFT holdings, token holder analytics, block data, and contract events.

Source: https://www.covalenthq.com/docs/unified-api/
Category: Crypto & DeFi On-Chain
Free tier: True (100,000 credits/month, 1 credit per API call)
API key required: Get free key at https://goldrush.dev
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Covalent API Configuration
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"
COVALENT_API_KEY = os.environ.get("COVALENT_API_KEY", "")

# Chain ID mapping for common networks
CHAIN_IDS = {
    "ethereum": 1,
    "polygon": 137,
    "bsc": 56,
    "arbitrum": 42161,
    "optimism": 10,
    "base": 8453,
    "avalanche": 43114,
    "fantom": 250,
    "gnosis": 100,
    "moonbeam": 1284,
}


def _make_request(endpoint: str, params: Optional[Dict] = None, api_key: Optional[str] = None) -> Dict:
    """
    Internal helper to make Covalent API requests
    
    Args:
        endpoint: API endpoint path (e.g., '/1/address/{address}/balances_v2/')
        params: Optional query parameters
        api_key: Optional API key override
    
    Returns:
        Dict with response data or error information
    """
    try:
        key = api_key or COVALENT_API_KEY
        
        if not key:
            return {
                "success": False,
                "error": "COVALENT_API_KEY not found in environment. Get free key at https://goldrush.dev"
            }
        
        url = f"{COVALENT_BASE_URL}{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params["key"] = key
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Covalent wraps responses in "data" field
        if "data" in data:
            return {
                "success": True,
                "data": data["data"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Unexpected response format",
                "raw_response": data
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "endpoint": endpoint
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "endpoint": endpoint
        }


def get_token_balances(address: str, chain_id: int = 1, api_key: Optional[str] = None) -> Dict:
    """
    Get ERC-20 token balances for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (default: 1 = Ethereum)
        api_key: Optional API key override
    
    Returns:
        Dict with token balances, USD values, and metadata
    
    Example:
        >>> balances = get_token_balances("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", chain_id=1)
        >>> print(balances['data']['items'][0]['contract_name'])
    """
    endpoint = f"/{chain_id}/address/{address}/balances_v2/"
    result = _make_request(endpoint, api_key=api_key)
    
    if result["success"]:
        # Add summary stats
        items = result["data"].get("items", [])
        total_usd = sum(float(item.get("quote", 0) or 0) for item in items)
        
        result["summary"] = {
            "total_tokens": len(items),
            "total_value_usd": round(total_usd, 2),
            "chain_id": chain_id,
            "address": address
        }
    
    return result


def get_transactions(address: str, chain_id: int = 1, page_size: int = 100, api_key: Optional[str] = None) -> Dict:
    """
    Get transaction history for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (default: 1 = Ethereum)
        page_size: Number of transactions to return (max 1000)
        api_key: Optional API key override
    
    Returns:
        Dict with transaction history including gas fees, values, and decoded logs
    
    Example:
        >>> txs = get_transactions("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", chain_id=1)
        >>> print(f"Found {len(txs['data']['items'])} transactions")
    """
    endpoint = f"/{chain_id}/address/{address}/transactions_v3/"
    params = {"page-size": min(page_size, 1000)}
    
    result = _make_request(endpoint, params=params, api_key=api_key)
    
    if result["success"]:
        items = result["data"].get("items", [])
        
        # Calculate summary stats
        total_gas = sum(int(tx.get("gas_spent", 0) or 0) for tx in items)
        total_gas_usd = sum(float(tx.get("gas_quote", 0) or 0) for tx in items)
        
        result["summary"] = {
            "total_transactions": len(items),
            "total_gas_spent": total_gas,
            "total_gas_usd": round(total_gas_usd, 2),
            "chain_id": chain_id,
            "address": address
        }
    
    return result


def get_token_holders(contract_address: str, chain_id: int = 1, page_size: int = 100, api_key: Optional[str] = None) -> Dict:
    """
    Get top token holders for a contract address
    
    Args:
        contract_address: Token contract address (0x...)
        chain_id: Chain ID (default: 1 = Ethereum)
        page_size: Number of holders to return (max 1000)
        api_key: Optional API key override
    
    Returns:
        Dict with holder addresses, balances, and ownership percentages
    
    Example:
        >>> holders = get_token_holders("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", chain_id=1)  # UNI token
        >>> print(f"Top holder owns {holders['data']['items'][0]['balance']} tokens")
    """
    endpoint = f"/{chain_id}/tokens/{contract_address}/token_holders_v2/"
    params = {"page-size": min(page_size, 1000)}
    
    result = _make_request(endpoint, params=params, api_key=api_key)
    
    if result["success"]:
        items = result["data"].get("items", [])
        
        # Calculate concentration metrics
        if items and len(items) > 0:
            total_supply = sum(int(holder.get("balance", 0) or 0) for holder in items)
            top_10_pct = 0
            if len(items) >= 10:
                top_10_balance = sum(int(items[i].get("balance", 0) or 0) for i in range(min(10, len(items))))
                top_10_pct = (top_10_balance / total_supply * 100) if total_supply > 0 else 0
            
            result["summary"] = {
                "total_holders_shown": len(items),
                "top_10_concentration_pct": round(top_10_pct, 2),
                "chain_id": chain_id,
                "contract_address": contract_address
            }
    
    return result


def get_nft_balances(address: str, chain_id: int = 1, api_key: Optional[str] = None) -> Dict:
    """
    Get NFT holdings for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (default: 1 = Ethereum)
        api_key: Optional API key override
    
    Returns:
        Dict with NFT collections, token IDs, metadata, and floor prices
    
    Example:
        >>> nfts = get_nft_balances("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", chain_id=1)
        >>> print(f"Owns {nfts['summary']['total_nfts']} NFTs across {nfts['summary']['total_collections']} collections")
    """
    endpoint = f"/{chain_id}/address/{address}/balances_nft/"
    result = _make_request(endpoint, api_key=api_key)
    
    if result["success"]:
        items = result["data"].get("items", [])
        
        # Count total NFTs and collections
        total_nfts = 0
        collections = set()
        
        for item in items:
            nft_data = item.get("nft_data", [])
            total_nfts += len(nft_data)
            collections.add(item.get("contract_address", ""))
        
        result["summary"] = {
            "total_nfts": total_nfts,
            "total_collections": len(collections),
            "chain_id": chain_id,
            "address": address
        }
    
    return result


def get_block(block_height: int, chain_id: int = 1, api_key: Optional[str] = None) -> Dict:
    """
    Get block details by block number
    
    Args:
        block_height: Block number
        chain_id: Chain ID (default: 1 = Ethereum)
        api_key: Optional API key override
    
    Returns:
        Dict with block data including transactions, gas used, miner, and timestamps
    
    Example:
        >>> block = get_block(17000000, chain_id=1)
        >>> print(f"Block mined at {block['data']['signed_at']}")
    """
    endpoint = f"/{chain_id}/block_v2/{block_height}/"
    result = _make_request(endpoint, api_key=api_key)
    
    if result["success"]:
        block_data = result["data"]
        
        result["summary"] = {
            "block_height": block_height,
            "chain_id": chain_id,
            "signed_at": block_data.get("signed_at", ""),
            "gas_used": block_data.get("gas_used", 0),
            "gas_limit": block_data.get("gas_limit", 0),
            "miner_address": block_data.get("miner_address", "")
        }
    
    return result


def get_log_events(
    contract_address: str,
    chain_id: int = 1,
    start_block: Optional[int] = None,
    end_block: Optional[int] = None,
    page_size: int = 100,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get contract log events (emitted events from smart contract)
    
    Args:
        contract_address: Contract address (0x...)
        chain_id: Chain ID (default: 1 = Ethereum)
        start_block: Optional starting block number
        end_block: Optional ending block number
        page_size: Number of events to return (max 1000)
        api_key: Optional API key override
    
    Returns:
        Dict with decoded log events, topics, and event signatures
    
    Example:
        >>> events = get_log_events("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", chain_id=1)
        >>> print(f"Found {len(events['data']['items'])} events")
    """
    endpoint = f"/{chain_id}/events/address/{contract_address}/"
    
    params = {"page-size": min(page_size, 1000)}
    if start_block is not None:
        params["starting-block"] = start_block
    if end_block is not None:
        params["ending-block"] = end_block
    
    result = _make_request(endpoint, params=params, api_key=api_key)
    
    if result["success"]:
        items = result["data"].get("items", [])
        
        # Count unique event types
        event_types = set()
        for item in items:
            decoded = item.get("decoded", {})
            if decoded:
                event_types.add(decoded.get("name", "unknown"))
        
        result["summary"] = {
            "total_events": len(items),
            "unique_event_types": len(event_types),
            "event_types": list(event_types),
            "chain_id": chain_id,
            "contract_address": contract_address
        }
    
    return result


def list_supported_chains() -> Dict:
    """
    List commonly supported blockchain networks
    
    Returns:
        Dict with chain IDs and names
    
    Example:
        >>> chains = list_supported_chains()
        >>> print(chains['chains'])
    """
    return {
        "success": True,
        "chains": CHAIN_IDS,
        "total_chains": len(CHAIN_IDS),
        "note": "Covalent supports 50+ chains. This is a subset of popular networks."
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Covalent Unified API (GoldRush) - Blockchain Data Module")
    print("=" * 70)
    
    # Show supported chains
    chains = list_supported_chains()
    print(f"\nSupported Chains ({chains['total_chains']}):")
    for name, chain_id in CHAIN_IDS.items():
        print(f"  {name.capitalize()}: {chain_id}")
    
    print("\n" + "=" * 70)
    print("Available Functions:")
    print("=" * 70)
    functions = [
        "get_token_balances(address, chain_id=1)",
        "get_transactions(address, chain_id=1)",
        "get_token_holders(contract_address, chain_id=1)",
        "get_nft_balances(address, chain_id=1)",
        "get_block(block_height, chain_id=1)",
        "get_log_events(contract_address, chain_id=1, start_block, end_block)",
        "list_supported_chains()"
    ]
    
    for i, func in enumerate(functions, 1):
        print(f"  {i}. {func}")
    
    # Test API key presence
    if not COVALENT_API_KEY:
        print("\n" + "⚠" * 35)
        print("WARNING: COVALENT_API_KEY not found in environment")
        print("Get free API key at: https://goldrush.dev")
        print("Add to .env file: COVALENT_API_KEY=your_key_here")
        print("⚠" * 35)
    else:
        print("\n✓ API key loaded from environment")
    
    print("\n" + "=" * 70)
    print(json.dumps({
        "module": "covalent_unified_api",
        "status": "ready",
        "functions": len(functions),
        "source": "https://www.covalenthq.com/docs/unified-api/"
    }, indent=2))
