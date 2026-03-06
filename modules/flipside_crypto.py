#!/usr/bin/env python3
"""
Flipside Crypto API module for QuantClaw Data
SQL-based on-chain analytics for Ethereum, Solana, and other blockchains.

Source: https://docs.flipsidecrypto.com/flipside-api
Category: Crypto & DeFi On-Chain
Free tier: 500 query runs per month, rate limit of 5 per minute
Update frequency: real-time
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any

BASE_URL = "https://api.flipsidecrypto.com/api/v2"

def create_query(sql: str, api_key: str) -> Dict[str, Any]:
    """
    Create and execute a SQL query against Flipside's database.
    
    Args:
        sql: SQL query string
        api_key: Flipside API key
        
    Returns:
        Dictionary with query result data
    """
    try:
        url = f"{BASE_URL}/queries"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "sql": sql,
            "ttlMinutes": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        query_id = data.get("token")
        
        # Poll for results
        return get_query_results(query_id, api_key)
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Query creation failed: {str(e)}"}


def get_query_results(query_id: str, api_key: str, max_wait: int = 60) -> Dict[str, Any]:
    """
    Poll for query results.
    
    Args:
        query_id: Query token from create_query
        api_key: Flipside API key
        max_wait: Maximum seconds to wait
        
    Returns:
        Query results as dictionary
    """
    try:
        url = f"{BASE_URL}/queries/{query_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            if status == "finished":
                return {
                    "success": True,
                    "query_id": query_id,
                    "rows": data.get("results", []),
                    "columns": data.get("columnLabels", []),
                    "row_count": len(data.get("results", []))
                }
            elif status == "error":
                return {"error": f"Query failed: {data.get('error')}"}
            
            time.sleep(2)
        
        return {"error": "Query timeout"}
        
    except Exception as e:
        return {"error": f"Failed to get results: {str(e)}"}


def get_ethereum_transactions(address: str, api_key: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get recent Ethereum transactions for an address.
    
    Args:
        address: Ethereum address
        api_key: Flipside API key
        limit: Max results
        
    Returns:
        Transaction data
    """
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        from_address,
        to_address,
        eth_value,
        gas_used,
        gas_price
    FROM ethereum.core.fact_transactions
    WHERE from_address = LOWER('{address}')
       OR to_address = LOWER('{address}')
    ORDER BY block_timestamp DESC
    LIMIT {limit}
    """
    
    return create_query(sql, api_key)


def get_dex_trades(token_address: str, api_key: str, days: int = 7, limit: int = 1000) -> Dict[str, Any]:
    """
    Get DEX trades for a token.
    
    Args:
        token_address: Token contract address
        api_key: Flipside API key
        days: Days to look back
        limit: Max results
        
    Returns:
        DEX trade data
    """
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        token_in,
        token_out,
        amount_in_usd,
        amount_out_usd,
        platform
    FROM ethereum.defi.ez_dex_swaps
    WHERE (token_in = LOWER('{token_address}') 
       OR token_out = LOWER('{token_address}'))
      AND block_timestamp >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY block_timestamp DESC
    LIMIT {limit}
    """
    
    return create_query(sql, api_key)


def get_wallet_balance(address: str, api_key: str) -> Dict[str, Any]:
    """
    Get current token balances for a wallet.
    
    Args:
        address: Ethereum address
        api_key: Flipside API key
        
    Returns:
        Wallet balance data
    """
    sql = f"""
    SELECT 
        token_address,
        symbol,
        balance,
        balance_usd
    FROM ethereum.core.ez_current_balances
    WHERE user_address = LOWER('{address}')
      AND balance > 0
    ORDER BY balance_usd DESC
    """
    
    return create_query(sql, api_key)


def get_defi_liquidations(protocol: str, api_key: str, days: int = 7) -> Dict[str, Any]:
    """
    Get DeFi liquidation events.
    
    Args:
        protocol: Protocol name (e.g., 'aave', 'compound')
        api_key: Flipside API key
        days: Days to look back
        
    Returns:
        Liquidation event data
    """
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        protocol,
        collateral_token,
        debt_token,
        liquidated_amount_usd,
        liquidator
    FROM ethereum.defi.ez_liquidations
    WHERE LOWER(protocol) = LOWER('{protocol}')
      AND block_timestamp >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY block_timestamp DESC
    """
    
    return create_query(sql, api_key)


def get_token_velocity(token_address: str, api_key: str, days: int = 30) -> Dict[str, Any]:
    """
    Calculate token velocity metrics.
    
    Args:
        token_address: Token contract address
        api_key: Flipside API key
        days: Days for calculation
        
    Returns:
        Velocity metrics
    """
    sql = f"""
    SELECT 
        DATE_TRUNC('day', block_timestamp) as date,
        COUNT(DISTINCT tx_hash) as tx_count,
        COUNT(DISTINCT from_address) as unique_senders,
        COUNT(DISTINCT to_address) as unique_receivers,
        SUM(amount_usd) as volume_usd
    FROM ethereum.core.ez_token_transfers
    WHERE contract_address = LOWER('{token_address}')
      AND block_timestamp >= CURRENT_DATE - INTERVAL '{days} days'
    GROUP BY date
    ORDER BY date DESC
    """
    
    return create_query(sql, api_key)


def test_module():
    """Test the module with example queries (requires API key)"""
    import os
    
    api_key = os.environ.get("FLIPSIDE_API_KEY")
    if not api_key:
        return {
            "status": "needs_api_key",
            "message": "Set FLIPSIDE_API_KEY environment variable to test"
        }
    
    # Simple test query
    sql = "SELECT COUNT(*) as tx_count FROM ethereum.core.fact_transactions WHERE block_timestamp >= CURRENT_DATE - 1 LIMIT 1"
    result = create_query(sql, api_key)
    
    return {
        "status": "tested",
        "functions": [
            "create_query",
            "get_query_results",
            "get_ethereum_transactions",
            "get_dex_trades",
            "get_wallet_balance",
            "get_defi_liquidations",
            "get_token_velocity"
        ],
        "test_result": result
    }


if __name__ == "__main__":
    result = test_module()
    print(json.dumps(result, indent=2))
