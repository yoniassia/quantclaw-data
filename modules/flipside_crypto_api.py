#!/usr/bin/env python3
"""
Flipside Crypto API — On-Chain Analytics via SQL

Flipside provides on-chain analytics via SQL queries for blockchains like Ethereum, 
Solana, and Near, focusing on DeFi metrics, token transfers, DEX trades, and wallet behaviors.
Free tier: 50 queries per hour.

Source: https://docs.flipsidecrypto.xyz/flipside-api
Category: Crypto & DeFi On-Chain
Free tier: True - 50 queries/hour
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Flipside API Configuration  
FLIPSIDE_BASE_URL = "https://api.flipsidecrypto.com"
FLIPSIDE_API_KEY = os.environ.get("FLIPSIDE_API_KEY", "")

# Query result polling config
MAX_POLL_ATTEMPTS = 30
POLL_INTERVAL_SECONDS = 2


def run_query(sql: str, api_key: Optional[str] = None, timeout: int = 60) -> Dict:
    """
    Execute SQL query against Flipside API
    
    Args:
        sql: SQL query string (use Flipside schema - ethereum.core, solana.core, etc)
        api_key: Optional Flipside API key (uses FLIPSIDE_API_KEY env var if not provided)
        timeout: Maximum seconds to wait for query completion (default 60)
    
    Returns:
        Dict with query results or error information
    """
    try:
        key = api_key or FLIPSIDE_API_KEY
        
        # Create query
        headers = {
            "Content-Type": "application/json",
            "x-api-key": key
        } if key else {"Content-Type": "application/json"}
        
        create_url = f"{FLIPSIDE_BASE_URL}/queries"
        payload = {
            "sql": sql,
            "ttlMinutes": 5
        }
        
        response = requests.post(create_url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        query_data = response.json()
        query_id = query_data.get("token") or query_data.get("query_id")
        
        if not query_id:
            return {
                "success": False,
                "error": "No query ID returned from API",
                "response": query_data
            }
        
        # Poll for results
        result_url = f"{FLIPSIDE_BASE_URL}/queries/{query_id}"
        start_time = time.time()
        attempts = 0
        
        while attempts < MAX_POLL_ATTEMPTS and (time.time() - start_time) < timeout:
            time.sleep(POLL_INTERVAL_SECONDS)
            attempts += 1
            
            result_response = requests.get(result_url, headers=headers, timeout=15)
            result_response.raise_for_status()
            
            result_data = result_response.json()
            status = result_data.get("status", "").lower()
            
            if status == "finished" or status == "success":
                results = result_data.get("results", [])
                return {
                    "success": True,
                    "query_id": query_id,
                    "rows": len(results),
                    "data": results,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
            elif status == "error" or status == "failed":
                return {
                    "success": False,
                    "error": result_data.get("error", "Query failed"),
                    "query_id": query_id
                }
        
        return {
            "success": False,
            "error": f"Query timeout after {timeout}s",
            "query_id": query_id,
            "attempts": attempts
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_eth_transactions(address: str, limit: int = 100, api_key: Optional[str] = None) -> Dict:
    """
    Get recent Ethereum transactions for a wallet address
    
    Args:
        address: Ethereum wallet address (0x...)
        limit: Maximum number of transactions to return (default 100)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with transaction history and summary stats
    """
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        from_address,
        to_address,
        eth_value,
        gas_price,
        gas_used,
        tx_fee
    FROM ethereum.core.fact_transactions
    WHERE from_address = LOWER('{address}') OR to_address = LOWER('{address}')
    ORDER BY block_timestamp DESC
    LIMIT {limit}
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        transactions = result.get("data", [])
        
        # Calculate summary stats
        total_eth_sent = sum(float(tx.get("eth_value", 0)) for tx in transactions if tx.get("from_address", "").lower() == address.lower())
        total_eth_received = sum(float(tx.get("eth_value", 0)) for tx in transactions if tx.get("to_address", "").lower() == address.lower())
        total_fees = sum(float(tx.get("tx_fee", 0)) for tx in transactions)
        
        result["summary"] = {
            "total_transactions": len(transactions),
            "total_eth_sent": round(total_eth_sent, 4),
            "total_eth_received": round(total_eth_received, 4),
            "net_eth_flow": round(total_eth_received - total_eth_sent, 4),
            "total_gas_fees": round(total_fees, 6)
        }
    
    return result


def get_defi_tvl(protocol: str = "uniswap", api_key: Optional[str] = None) -> Dict:
    """
    Get DeFi protocol Total Value Locked (TVL) metrics
    
    Args:
        protocol: DeFi protocol name (uniswap, aave, compound, curve, etc)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with TVL data and historical trends
    """
    sql = f"""
    SELECT 
        date_trunc('day', block_timestamp) as date,
        SUM(amount_usd) as tvl_usd,
        COUNT(DISTINCT user_address) as unique_users
    FROM ethereum.core.ez_dex_swaps
    WHERE platform = '{protocol.lower()}'
    AND block_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 30
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        data = result.get("data", [])
        if data:
            latest = data[0]
            result["latest_tvl"] = {
                "protocol": protocol,
                "tvl_usd": latest.get("tvl_usd"),
                "unique_users": latest.get("unique_users"),
                "date": latest.get("date")
            }
    
    return result


def get_token_transfers(token: str = "USDC", limit: int = 100, api_key: Optional[str] = None) -> Dict:
    """
    Get recent token transfer activity
    
    Args:
        token: Token symbol (USDC, USDT, WETH, etc)
        limit: Maximum number of transfers to return (default 100)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with token transfer data and volume metrics
    """
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        from_address,
        to_address,
        amount,
        amount_usd,
        contract_address
    FROM ethereum.core.ez_token_transfers
    WHERE symbol = '{token.upper()}'
    ORDER BY block_timestamp DESC
    LIMIT {limit}
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        transfers = result.get("data", [])
        
        # Calculate volume metrics
        total_volume_usd = sum(float(tx.get("amount_usd", 0)) for tx in transfers if tx.get("amount_usd"))
        unique_addresses = set()
        for tx in transfers:
            unique_addresses.add(tx.get("from_address"))
            unique_addresses.add(tx.get("to_address"))
        
        result["volume_metrics"] = {
            "token": token,
            "total_transfers": len(transfers),
            "total_volume_usd": round(total_volume_usd, 2),
            "unique_addresses": len(unique_addresses)
        }
    
    return result


def get_dex_trades(pair: str = "WETH/USDC", limit: int = 100, api_key: Optional[str] = None) -> Dict:
    """
    Get recent DEX trading activity for a token pair
    
    Args:
        pair: Trading pair (WETH/USDC, UNI/WETH, etc)
        limit: Maximum number of trades to return (default 100)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with DEX trade data and trading metrics
    """
    tokens = pair.upper().split("/")
    if len(tokens) != 2:
        return {
            "success": False,
            "error": "Invalid pair format. Use TOKEN1/TOKEN2 (e.g., WETH/USDC)"
        }
    
    token0, token1 = tokens
    
    sql = f"""
    SELECT 
        block_timestamp,
        tx_hash,
        platform,
        token_in,
        token_out,
        amount_in,
        amount_out,
        amount_in_usd,
        amount_out_usd,
        trader
    FROM ethereum.core.ez_dex_swaps
    WHERE (symbol_in = '{token0}' AND symbol_out = '{token1}')
       OR (symbol_in = '{token1}' AND symbol_out = '{token0}')
    ORDER BY block_timestamp DESC
    LIMIT {limit}
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        trades = result.get("data", [])
        
        # Calculate trading metrics
        total_volume_usd = sum(float(tx.get("amount_in_usd", 0)) for tx in trades if tx.get("amount_in_usd"))
        platforms = {}
        for trade in trades:
            platform = trade.get("platform", "unknown")
            platforms[platform] = platforms.get(platform, 0) + 1
        
        result["trading_metrics"] = {
            "pair": pair,
            "total_trades": len(trades),
            "total_volume_usd": round(total_volume_usd, 2),
            "unique_traders": len(set(tx.get("trader") for tx in trades if tx.get("trader"))),
            "platforms": platforms
        }
    
    return result


def get_wallet_balance(address: str, chain: str = "ethereum", api_key: Optional[str] = None) -> Dict:
    """
    Get current token balances for a wallet address
    
    Args:
        address: Wallet address (0x... for Ethereum)
        chain: Blockchain (ethereum, solana, near)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with current token holdings and USD value
    """
    if chain.lower() == "ethereum":
        sql = f"""
        SELECT 
            contract_address,
            symbol,
            balance,
            balance_usd,
            last_updated
        FROM ethereum.core.ez_current_balances
        WHERE user_address = LOWER('{address}')
        AND balance > 0
        ORDER BY balance_usd DESC
        LIMIT 50
        """
    elif chain.lower() == "solana":
        sql = f"""
        SELECT 
            mint,
            symbol,
            balance,
            balance_usd
        FROM solana.core.ez_current_balances
        WHERE address = '{address}'
        AND balance > 0
        ORDER BY balance_usd DESC
        LIMIT 50
        """
    else:
        return {
            "success": False,
            "error": f"Unsupported chain: {chain}. Use ethereum or solana."
        }
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        balances = result.get("data", [])
        
        # Calculate portfolio metrics
        total_usd = sum(float(bal.get("balance_usd", 0)) for bal in balances if bal.get("balance_usd"))
        
        result["portfolio"] = {
            "address": address,
            "chain": chain,
            "total_tokens": len(balances),
            "total_value_usd": round(total_usd, 2),
            "top_holdings": balances[:10] if len(balances) > 10 else balances
        }
    
    return result


def get_latest(api_key: Optional[str] = None) -> Dict:
    """
    Get summary of latest on-chain metrics across Ethereum
    
    Args:
        api_key: Optional Flipside API key
    
    Returns:
        Dict with latest blockchain activity snapshot
    """
    sql = """
    SELECT 
        COUNT(DISTINCT tx_hash) as total_transactions,
        COUNT(DISTINCT from_address) as active_addresses,
        SUM(eth_value) as total_eth_transferred,
        SUM(tx_fee) as total_gas_fees,
        AVG(gas_price) as avg_gas_price
    FROM ethereum.core.fact_transactions
    WHERE block_timestamp >= CURRENT_DATE - INTERVAL '1 hour'
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success") and result.get("data"):
        metrics = result["data"][0]
        result["latest_metrics"] = {
            "timeframe": "last 1 hour",
            "total_transactions": metrics.get("total_transactions"),
            "active_addresses": metrics.get("active_addresses"),
            "total_eth_transferred": round(float(metrics.get("total_eth_transferred", 0)), 4),
            "total_gas_fees": round(float(metrics.get("total_gas_fees", 0)), 6),
            "avg_gas_price_gwei": round(float(metrics.get("avg_gas_price", 0)) / 1e9, 2) if metrics.get("avg_gas_price") else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_gas_trends(days: int = 7, api_key: Optional[str] = None) -> Dict:
    """
    Get Ethereum gas price trends over time
    
    Args:
        days: Number of days of history (default 7)
        api_key: Optional Flipside API key
    
    Returns:
        Dict with gas price statistics and trends
    """
    sql = f"""
    SELECT 
        date_trunc('hour', block_timestamp) as hour,
        AVG(gas_price) as avg_gas_price,
        MIN(gas_price) as min_gas_price,
        MAX(gas_price) as max_gas_price,
        COUNT(*) as tx_count
    FROM ethereum.core.fact_transactions
    WHERE block_timestamp >= CURRENT_DATE - INTERVAL '{days} days'
    GROUP BY hour
    ORDER BY hour DESC
    LIMIT 168
    """
    
    result = run_query(sql, api_key)
    
    if result.get("success"):
        data = result.get("data", [])
        if data:
            # Convert to Gwei and calculate stats
            current_avg = float(data[0].get("avg_gas_price", 0)) / 1e9
            all_avgs = [float(h.get("avg_gas_price", 0)) / 1e9 for h in data]
            
            result["gas_stats"] = {
                "current_avg_gwei": round(current_avg, 2),
                "period_avg_gwei": round(sum(all_avgs) / len(all_avgs), 2),
                "period_min_gwei": round(min(all_avgs), 2),
                "period_max_gwei": round(max(all_avgs), 2),
                "days": days
            }
    
    return result


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Flipside Crypto API - On-Chain Analytics")
    print("=" * 60)
    
    # Test get_latest
    print("\nFetching latest Ethereum metrics...")
    latest = get_latest()
    print(json.dumps(latest, indent=2))
