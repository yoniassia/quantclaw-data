#!/usr/bin/env python3
"""Alchemy API — Blockchain infrastructure for on-chain data.

Alchemy provides high-performance access to Ethereum and Layer 2 blockchain data.
Supports transaction details, block information, token balances, and DeFi contract states.

Data source: Alchemy API (https://docs.alchemy.com/)
Free tier: 300M compute units/month
Update frequency: real-time
"""

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional


_BASE_URL = "https://eth-mainnet.g.alchemy.com/v2/"
_DEMO_KEY = "demo"  # Alchemy provides demo key for testing
_TIMEOUT = 15


def _get_api_key() -> str:
    """Get Alchemy API key from environment or use demo key."""
    return os.environ.get("ALCHEMY_API_KEY", _DEMO_KEY)


def _make_request(method: str, params: list) -> dict[str, Any]:
    """Make JSON-RPC request to Alchemy API.
    
    Args:
        method: Ethereum JSON-RPC method name
        params: List of parameters for the method
        
    Returns:
        Response data dict
        
    Raises:
        Exception if request fails or returns error
    """
    api_key = _get_api_key()
    url = f"{_BASE_URL}{api_key}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "QuantClaw/1.0"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)
        
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            result = json.loads(resp.read())
            
        if "error" in result:
            error_msg = result["error"].get("message", "Unknown error")
            return {"error": f"Alchemy API error: {error_msg}"}
            
        return result.get("result", {})
        
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP error {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"URL error: {str(e.reason)}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_block_number() -> int | dict[str, str]:
    """Get the latest block number on Ethereum mainnet.
    
    Returns:
        Latest block number as integer, or error dict
    """
    result = _make_request("eth_blockNumber", [])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    try:
        return int(result, 16)  # Convert hex to int
    except (ValueError, TypeError) as e:
        return {"error": f"Failed to parse block number: {str(e)}"}


def get_block(block_number: str | int = "latest") -> dict[str, Any]:
    """Get detailed information about a specific block.
    
    Args:
        block_number: Block number (int), hex string, or "latest"
        
    Returns:
        Dict with block details including transactions, gas used, timestamp
    """
    # Convert block_number to proper format
    if isinstance(block_number, int):
        block_param = hex(block_number)
    elif block_number == "latest":
        block_param = "latest"
    else:
        block_param = block_number
        
    result = _make_request("eth_getBlockByNumber", [block_param, False])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    if not result:
        return {"error": "Block not found"}
        
    # Parse and format the response
    try:
        block_data = {
            "number": int(result.get("number", "0x0"), 16),
            "hash": result.get("hash"),
            "parent_hash": result.get("parentHash"),
            "timestamp": int(result.get("timestamp", "0x0"), 16),
            "timestamp_iso": datetime.fromtimestamp(
                int(result.get("timestamp", "0x0"), 16), 
                tz=timezone.utc
            ).isoformat(),
            "transactions_count": len(result.get("transactions", [])),
            "gas_used": int(result.get("gasUsed", "0x0"), 16),
            "gas_limit": int(result.get("gasLimit", "0x0"), 16),
            "base_fee_per_gas": int(result.get("baseFeePerGas", "0x0"), 16) if result.get("baseFeePerGas") else None,
            "miner": result.get("miner"),
            "difficulty": int(result.get("difficulty", "0x0"), 16),
            "size": int(result.get("size", "0x0"), 16),
        }
        return block_data
    except (ValueError, TypeError, KeyError) as e:
        return {"error": f"Failed to parse block data: {str(e)}"}


def get_gas_price() -> dict[str, Any]:
    """Get current gas price on Ethereum mainnet.
    
    Returns:
        Dict with gas price in Wei and Gwei
    """
    result = _make_request("eth_gasPrice", [])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    try:
        gas_wei = int(result, 16)
        gas_gwei = gas_wei / 1e9
        
        return {
            "gas_price_wei": gas_wei,
            "gas_price_gwei": round(gas_gwei, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except (ValueError, TypeError) as e:
        return {"error": f"Failed to parse gas price: {str(e)}"}


def get_eth_balance(address: str) -> dict[str, Any]:
    """Get ETH balance for a specific address.
    
    Args:
        address: Ethereum address (0x...)
        
    Returns:
        Dict with balance in Wei and ETH
    """
    if not address or not address.startswith("0x"):
        return {"error": "Invalid Ethereum address format"}
        
    result = _make_request("eth_getBalance", [address, "latest"])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    try:
        balance_wei = int(result, 16)
        balance_eth = balance_wei / 1e18
        
        return {
            "address": address,
            "balance_wei": balance_wei,
            "balance_eth": round(balance_eth, 6),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except (ValueError, TypeError) as e:
        return {"error": f"Failed to parse balance: {str(e)}"}


def get_token_balances(address: str) -> list[dict[str, Any]] | dict[str, str]:
    """Get ERC-20 token balances for a specific address.
    
    Args:
        address: Ethereum address (0x...)
        
    Returns:
        List of token balance dicts, or error dict
    """
    if not address or not address.startswith("0x"):
        return {"error": "Invalid Ethereum address format"}
        
    # Use Alchemy's alchemy_getTokenBalances method
    result = _make_request("alchemy_getTokenBalances", [address, "erc20"])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    try:
        token_balances = result.get("tokenBalances", [])
        
        balances = []
        for token in token_balances:
            contract_address = token.get("contractAddress")
            token_balance_hex = token.get("tokenBalance")
            
            # Skip tokens with zero balance or error
            if not token_balance_hex or token_balance_hex == "0x":
                continue
                
            try:
                balance_raw = int(token_balance_hex, 16)
                if balance_raw > 0:
                    balances.append({
                        "contract_address": contract_address,
                        "balance_raw": balance_raw,
                        "balance_hex": token_balance_hex,
                    })
            except (ValueError, TypeError):
                continue
                
        return balances
        
    except (KeyError, TypeError) as e:
        return {"error": f"Failed to parse token balances: {str(e)}"}


def get_transaction(tx_hash: str) -> dict[str, Any]:
    """Get detailed information about a specific transaction.
    
    Args:
        tx_hash: Transaction hash (0x...)
        
    Returns:
        Dict with transaction details
    """
    if not tx_hash or not tx_hash.startswith("0x"):
        return {"error": "Invalid transaction hash format"}
        
    result = _make_request("eth_getTransactionByHash", [tx_hash])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    if not result:
        return {"error": "Transaction not found"}
        
    try:
        tx_data = {
            "hash": result.get("hash"),
            "from": result.get("from"),
            "to": result.get("to"),
            "value_wei": int(result.get("value", "0x0"), 16),
            "value_eth": int(result.get("value", "0x0"), 16) / 1e18,
            "gas": int(result.get("gas", "0x0"), 16),
            "gas_price": int(result.get("gasPrice", "0x0"), 16),
            "gas_price_gwei": int(result.get("gasPrice", "0x0"), 16) / 1e9,
            "nonce": int(result.get("nonce", "0x0"), 16),
            "block_number": int(result.get("blockNumber", "0x0"), 16) if result.get("blockNumber") else None,
            "block_hash": result.get("blockHash"),
            "transaction_index": int(result.get("transactionIndex", "0x0"), 16) if result.get("transactionIndex") else None,
            "input": result.get("input"),
        }
        return tx_data
    except (ValueError, TypeError, KeyError) as e:
        return {"error": f"Failed to parse transaction data: {str(e)}"}


def get_transaction_receipt(tx_hash: str) -> dict[str, Any]:
    """Get transaction receipt (includes status, logs, gas used).
    
    Args:
        tx_hash: Transaction hash (0x...)
        
    Returns:
        Dict with transaction receipt details
    """
    if not tx_hash or not tx_hash.startswith("0x"):
        return {"error": "Invalid transaction hash format"}
        
    result = _make_request("eth_getTransactionReceipt", [tx_hash])
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    if not result:
        return {"error": "Transaction receipt not found"}
        
    try:
        status = result.get("status")
        receipt_data = {
            "transaction_hash": result.get("transactionHash"),
            "status": int(status, 16) if status else None,
            "status_text": "success" if status == "0x1" else "failed" if status == "0x0" else "pending",
            "block_number": int(result.get("blockNumber", "0x0"), 16),
            "gas_used": int(result.get("gasUsed", "0x0"), 16),
            "cumulative_gas_used": int(result.get("cumulativeGasUsed", "0x0"), 16),
            "logs_count": len(result.get("logs", [])),
            "from": result.get("from"),
            "to": result.get("to"),
            "contract_address": result.get("contractAddress"),
        }
        return receipt_data
    except (ValueError, TypeError, KeyError) as e:
        return {"error": f"Failed to parse receipt data: {str(e)}"}


if __name__ == "__main__":
    print(json.dumps({
        "module": "alchemy_api",
        "status": "active",
        "functions": [
            "get_block_number",
            "get_block",
            "get_gas_price",
            "get_eth_balance",
            "get_token_balances",
            "get_transaction",
            "get_transaction_receipt"
        ],
        "source": "https://docs.alchemy.com/",
        "free_tier": "300M compute units/month"
    }, indent=2))
