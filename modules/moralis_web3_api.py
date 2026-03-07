#!/usr/bin/env python3
"""
Moralis Web3 API — On-Chain Data for EVM Chains

Real-time blockchain data across EVM-compatible chains including:
- Token balances (ERC20, native)
- Transaction histories
- NFT ownership and metadata
- DeFi protocol positions
- Token prices and market data

Supports: Ethereum, BSC, Polygon, Avalanche, Fantom, Cronos, and more.

Source: https://docs.moralis.io/web3-data-api
Category: Crypto & DeFi On-Chain
Free tier: True (1,000,000 compute units/month, requires MORALIS_API_KEY)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-06
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

# Moralis API Configuration
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2"
MORALIS_API_KEY = os.environ.get("MORALIS_API_KEY", "")

# Chain mappings
SUPPORTED_CHAINS = {
    'eth': 'ethereum',
    'ethereum': 'ethereum',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'matic': 'polygon',
    'avalanche': 'avalanche',
    'avax': 'avalanche',
    'fantom': 'fantom',
    'ftm': 'fantom',
    'cronos': 'cronos',
    'arbitrum': 'arbitrum',
    'optimism': 'optimism',
    'base': 'base',
}


def _check_api_key() -> bool:
    """Check if MORALIS_API_KEY is set"""
    return bool(MORALIS_API_KEY)


def _get_headers() -> Dict[str, str]:
    """Get headers for Moralis API requests"""
    if not _check_api_key():
        raise ValueError(
            "MORALIS_API_KEY not found in environment variables. "
            "Get a free API key at https://moralis.io and set it with: "
            "export MORALIS_API_KEY='your_key_here'"
        )
    return {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }


def _normalize_chain(chain: str) -> str:
    """Normalize chain name to Moralis format"""
    normalized = SUPPORTED_CHAINS.get(chain.lower())
    if not normalized:
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(SUPPORTED_CHAINS.keys())}"
        )
    return normalized


def get_wallet_tokens(address: str, chain: str = 'eth') -> Dict:
    """
    Get ERC20 token balances for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain: Blockchain network (default: 'eth')
        
    Returns:
        Dictionary with token balances and metadata
        
    Example:
        >>> tokens = get_wallet_tokens("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        >>> print(f"Found {len(tokens['result'])} tokens")
    """
    if not _check_api_key():
        return {
            "error": "MORALIS_API_KEY not set",
            "message": "Get a free API key at https://moralis.io",
            "address": address,
            "chain": chain
        }
    
    try:
        chain_normalized = _normalize_chain(chain)
        url = f"{MORALIS_BASE_URL}/{address}/erc20"
        params = {"chain": chain_normalized}
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "address": address,
            "chain": chain_normalized,
            "token_count": len(data),
            "tokens": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "address": address,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_wallet_transactions(address: str, chain: str = 'eth', limit: int = 25) -> Dict:
    """
    Get recent transactions for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain: Blockchain network (default: 'eth')
        limit: Maximum number of transactions to return (default: 25)
        
    Returns:
        Dictionary with transaction history
        
    Example:
        >>> txs = get_wallet_transactions("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", limit=10)
        >>> print(f"Recent transactions: {len(txs['result'])}")
    """
    if not _check_api_key():
        return {
            "error": "MORALIS_API_KEY not set",
            "message": "Get a free API key at https://moralis.io",
            "address": address,
            "chain": chain
        }
    
    try:
        chain_normalized = _normalize_chain(chain)
        url = f"{MORALIS_BASE_URL}/{address}"
        params = {
            "chain": chain_normalized,
            "limit": limit
        }
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "address": address,
            "chain": chain_normalized,
            "transaction_count": len(data.get('result', [])),
            "transactions": data.get('result', []),
            "cursor": data.get('cursor'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "address": address,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_token_price(address: str, chain: str = 'eth') -> Dict:
    """
    Get current price for an ERC20 token
    
    Args:
        address: Token contract address (0x...)
        chain: Blockchain network (default: 'eth')
        
    Returns:
        Dictionary with token price and metadata
        
    Example:
        >>> price = get_token_price("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # WETH
        >>> print(f"Price: ${price['usdPrice']}")
    """
    if not _check_api_key():
        return {
            "error": "MORALIS_API_KEY not set",
            "message": "Get a free API key at https://moralis.io",
            "address": address,
            "chain": chain
        }
    
    try:
        chain_normalized = _normalize_chain(chain)
        url = f"{MORALIS_BASE_URL}/erc20/{address}/price"
        params = {"chain": chain_normalized}
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "token_address": address,
            "chain": chain_normalized,
            "usdPrice": data.get('usdPrice'),
            "nativePrice": data.get('nativePrice'),
            "exchangeAddress": data.get('exchangeAddress'),
            "exchangeName": data.get('exchangeName'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "address": address,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_nft_holdings(address: str, chain: str = 'eth') -> Dict:
    """
    Get NFT holdings for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain: Blockchain network (default: 'eth')
        
    Returns:
        Dictionary with NFT collection data
        
    Example:
        >>> nfts = get_nft_holdings("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        >>> print(f"NFT count: {nfts['nft_count']}")
    """
    if not _check_api_key():
        return {
            "error": "MORALIS_API_KEY not set",
            "message": "Get a free API key at https://moralis.io",
            "address": address,
            "chain": chain
        }
    
    try:
        chain_normalized = _normalize_chain(chain)
        url = f"{MORALIS_BASE_URL}/{address}/nft"
        params = {"chain": chain_normalized}
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "address": address,
            "chain": chain_normalized,
            "nft_count": len(data.get('result', [])),
            "nfts": data.get('result', []),
            "cursor": data.get('cursor'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "address": address,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_defi_positions(address: str, chain: str = 'eth') -> Dict:
    """
    Get DeFi protocol positions for a wallet address
    
    Args:
        address: Wallet address (0x...)
        chain: Blockchain network (default: 'eth')
        
    Returns:
        Dictionary with DeFi positions across protocols
        
    Example:
        >>> positions = get_defi_positions("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        >>> print(f"Active positions: {len(positions['positions'])}")
    """
    if not _check_api_key():
        return {
            "error": "MORALIS_API_KEY not set",
            "message": "Get a free API key at https://moralis.io",
            "address": address,
            "chain": chain
        }
    
    try:
        chain_normalized = _normalize_chain(chain)
        url = f"{MORALIS_BASE_URL}/wallets/{address}/defi/positions"
        params = {"chain": chain_normalized}
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "address": address,
            "chain": chain_normalized,
            "position_count": len(data.get('result', [])),
            "positions": data.get('result', []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "address": address,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # Test module
    print(json.dumps({
        "module": "moralis_web3_api",
        "status": "ready",
        "api_key_set": _check_api_key(),
        "supported_chains": list(set(SUPPORTED_CHAINS.values())),
        "functions": [
            "get_wallet_tokens",
            "get_wallet_transactions",
            "get_token_price",
            "get_nft_holdings",
            "get_defi_positions"
        ]
    }, indent=2))
