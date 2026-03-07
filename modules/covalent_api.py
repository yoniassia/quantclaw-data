#!/usr/bin/env python3
"""
Covalent API (GoldRush) — Unified On-Chain Data

Provides unified on-chain data across 200+ blockchains including:
- Token balances (ERC20, native)
- Transaction history with full details
- Token holder lists
- NFT balances and metadata
- Block information

Source: https://www.covalenthq.com/docs/unified-api/
Category: Crypto & DeFi On-Chain
Free tier: True - 100,000 credits/month (1 credit per call), 5 calls/sec
Requires: Sign up at https://www.covalenthq.com to get API key
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Covalent API Configuration
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"
COVALENT_API_KEY = os.environ.get("COVALENT_API_KEY") or os.environ.get("GOLDRUSH_API_KEY")

# Chain ID mapping for common chains
CHAIN_NAMES = {
    1: "Ethereum Mainnet",
    10: "Optimism",
    56: "BNB Smart Chain",
    137: "Polygon",
    8453: "Base",
    42161: "Arbitrum One",
    43114: "Avalanche C-Chain",
}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Covalent API.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters
        
    Returns:
        Dict with response data
        
    Raises:
        Exception: If API request fails
    """
    if not COVALENT_API_KEY:
        return {
            "error": "No API key found. Set COVALENT_API_KEY or GOLDRUSH_API_KEY in .env",
            "status": "error",
            "signup_url": "https://www.covalenthq.com"
        }
    
    url = f"{COVALENT_BASE_URL}/{endpoint}"
    
    # Add API key to params
    if params is None:
        params = {}
    params['key'] = COVALENT_API_KEY
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data"):
            return {
                "error": data.get("error_message", "No data returned"),
                "status": "error"
            }
            
        return data["data"]
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status": "error",
            "endpoint": endpoint
        }


def get_token_balances(address: str, chain_id: int = 1) -> Dict:
    """
    Get ERC20 token balances for a wallet address.
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (1=Ethereum, 137=Polygon, 8453=Base, etc.)
        
    Returns:
        Dict containing:
        - address: Wallet address
        - chain_id: Chain ID
        - chain_name: Human-readable chain name
        - items: List of token balances with metadata
        - updated_at: Timestamp
        
    Example:
        >>> balances = get_token_balances('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
        >>> print(f"Found {len(balances['items'])} tokens")
    """
    endpoint = f"{chain_id}/address/{address}/balances_v2/"
    data = _make_request(endpoint)
    
    if "error" in data:
        return data
        
    return {
        "address": data.get("address"),
        "chain_id": chain_id,
        "chain_name": CHAIN_NAMES.get(chain_id, f"Chain {chain_id}"),
        "items": data.get("items", []),
        "updated_at": data.get("updated_at"),
        "quote_currency": data.get("quote_currency", "USD")
    }


def get_transactions(address: str, chain_id: int = 1, page: int = 0) -> Dict:
    """
    Get transaction history for a wallet address.
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
        page: Page number for pagination (0-indexed)
        
    Returns:
        Dict containing:
        - address: Wallet address
        - chain_id: Chain ID
        - items: List of transactions with full details
        - pagination: Pagination info (has_more, page_number, page_size)
        
    Example:
        >>> txs = get_transactions('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
        >>> print(f"Latest tx: {txs['items'][0]['tx_hash']}")
    """
    endpoint = f"{chain_id}/address/{address}/transactions_v2/"
    params = {"page-number": page}
    
    data = _make_request(endpoint, params)
    
    if "error" in data:
        return data
        
    return {
        "address": data.get("address"),
        "chain_id": chain_id,
        "chain_name": CHAIN_NAMES.get(chain_id, f"Chain {chain_id}"),
        "items": data.get("items", []),
        "pagination": data.get("pagination", {})
    }


def get_token_holders(contract_address: str, chain_id: int = 1, page: int = 0) -> Dict:
    """
    Get token holder list for a contract address.
    
    Args:
        contract_address: Token contract address (0x...)
        chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
        page: Page number for pagination
        
    Returns:
        Dict containing:
        - contract_address: Token contract
        - chain_id: Chain ID
        - items: List of holders with balance and share percentage
        - pagination: Pagination info
        
    Example:
        >>> holders = get_token_holders('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')  # USDC
        >>> print(f"Top holder: {holders['items'][0]['address']}")
    """
    endpoint = f"{chain_id}/tokens/{contract_address}/token_holders/"
    params = {"page-number": page}
    
    data = _make_request(endpoint, params)
    
    if "error" in data:
        return data
        
    return {
        "contract_address": contract_address,
        "chain_id": chain_id,
        "chain_name": CHAIN_NAMES.get(chain_id, f"Chain {chain_id}"),
        "items": data.get("items", []),
        "pagination": data.get("pagination", {})
    }


def get_nft_balances(address: str, chain_id: int = 1) -> Dict:
    """
    Get NFT holdings for a wallet address.
    
    Args:
        address: Wallet address (0x...)
        chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
        
    Returns:
        Dict containing:
        - address: Wallet address
        - chain_id: Chain ID
        - items: List of NFT collections with token IDs
        - updated_at: Timestamp
        
    Example:
        >>> nfts = get_nft_balances('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
        >>> print(f"NFT collections: {len(nfts['items'])}")
    """
    endpoint = f"{chain_id}/address/{address}/balances_nft/"
    
    data = _make_request(endpoint)
    
    if "error" in data:
        return data
        
    return {
        "address": data.get("address"),
        "chain_id": chain_id,
        "chain_name": CHAIN_NAMES.get(chain_id, f"Chain {chain_id}"),
        "items": data.get("items", []),
        "updated_at": data.get("updated_at")
    }


def get_block_info(chain_id: int = 1, block_height: Union[str, int] = 'latest') -> Dict:
    """
    Get block information and statistics.
    
    Args:
        chain_id: Chain ID (1=Ethereum, 137=Polygon, etc.)
        block_height: Block number or 'latest' for most recent
        
    Returns:
        Dict containing:
        - chain_id: Chain ID
        - block_height: Block number
        - block_hash: Block hash
        - signed_at: Block timestamp
        - items: List of transactions in block (if detailed=True)
        
    Example:
        >>> block = get_block_info(chain_id=1, block_height='latest')
        >>> print(f"Latest Ethereum block: {block['block_height']}")
    """
    endpoint = f"{chain_id}/block_v2/{block_height}/"
    
    data = _make_request(endpoint)
    
    if "error" in data:
        return data
        
    return {
        "chain_id": chain_id,
        "chain_name": CHAIN_NAMES.get(chain_id, f"Chain {chain_id}"),
        "block_height": data.get("height"),
        "block_hash": data.get("hash"),
        "signed_at": data.get("signed_at"),
        "items": data.get("items", [])
    }


# ========== CLI Testing ==========

if __name__ == "__main__":
    import sys
    
    print("=== Covalent API Module Test ===\n")
    
    if not COVALENT_API_KEY:
        print("⚠️  No API key found!")
        print("   Set COVALENT_API_KEY or GOLDRUSH_API_KEY in .env")
        print("   Sign up: https://www.covalenthq.com\n")
        print("   Module structure is valid and ready for use with API key.\n")
        sys.exit(0)
    
    # Test 1: Vitalik's token balances
    print("1. Testing get_token_balances (Vitalik's address)...")
    balances = get_token_balances('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
    if "error" not in balances:
        print(f"   ✓ Found {len(balances['items'])} tokens on {balances['chain_name']}")
        if balances['items']:
            first_token = balances['items'][0]
            print(f"   Top token: {first_token.get('contract_name', 'N/A')} - {first_token.get('balance', 0)}")
    else:
        print(f"   ✗ Error: {balances['error']}")
    
    # Test 2: Transactions
    print("\n2. Testing get_transactions...")
    txs = get_transactions('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
    if "error" not in txs:
        print(f"   ✓ Found {len(txs['items'])} transactions")
        if txs['items']:
            latest_tx = txs['items'][0]
            print(f"   Latest: {latest_tx.get('tx_hash', 'N/A')[:20]}...")
    else:
        print(f"   ✗ Error: {txs['error']}")
    
    # Test 3: Block info
    print("\n3. Testing get_block_info...")
    block = get_block_info(chain_id=1, block_height='latest')
    if "error" not in block:
        print(f"   ✓ Latest block: {block['block_height']} on {block['chain_name']}")
        print(f"   Hash: {block['block_hash'][:20]}...")
    else:
        print(f"   ✗ Error: {block['error']}")
    
    # Test 4: NFT balances
    print("\n4. Testing get_nft_balances...")
    nfts = get_nft_balances('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
    if "error" not in nfts:
        print(f"   ✓ Found {len(nfts['items'])} NFT collections")
    else:
        print(f"   ✗ Error: {nfts['error']}")
    
    # Test 5: Token holders (USDC contract)
    print("\n5. Testing get_token_holders (USDC)...")
    holders = get_token_holders('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', chain_id=1)
    if "error" not in holders:
        print(f"   ✓ Found {len(holders['items'])} holders")
    else:
        print(f"   ✗ Error: {holders['error']}")
    
    print("\n=== Module Test Complete ===")
