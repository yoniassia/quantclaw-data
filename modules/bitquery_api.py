"""
Bitquery API — GraphQL blockchain data for 40+ chains

Bitquery provides GraphQL-based access to on-chain data including DEX trades,
token transfers, smart contract events, and money flow analysis across Ethereum,
BSC, Polygon, and 40+ other blockchains.

Source: https://bitquery.io/docs
Endpoint: https://graphql.bitquery.io/
Free tier: 100 queries/day with API key
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache" / "bitquery"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://graphql.bitquery.io/"


def _get_api_key() -> Optional[str]:
    """Get Bitquery API key from environment."""
    return os.environ.get("BITQUERY_API_KEY")


def _execute_query(query: str, variables: Optional[Dict] = None, use_cache: bool = True, cache_hours: int = 24) -> Optional[Dict]:
    """Execute a GraphQL query against Bitquery API."""
    api_key = _get_api_key()
    
    # Generate cache key from query and variables
    cache_key = hash(query + str(variables))
    cache_path = CACHE_DIR / f"query_{abs(cache_key)}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Execute query
    headers = {
        "Content-Type": "application/json",
    }
    
    if api_key:
        headers["X-API-KEY"] = api_key
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
        
        # Handle auth errors gracefully
        if response.status_code == 401:
            return {
                "error": "Authentication required",
                "message": "Set BITQUERY_API_KEY environment variable",
                "status_code": 401
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Cache successful response
        if "data" in data and cache_path:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error executing Bitquery query: {e}")
        return {"error": str(e)}


def get_dex_trades(
    network: str = "ethereum",
    base_currency: str = "ETH",
    quote_currency: str = "USDT",
    limit: int = 100,
    since_date: Optional[str] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Get DEX trades for a token pair.
    
    Args:
        network: Blockchain network (ethereum, bsc, polygon, etc.)
        base_currency: Base currency symbol
        quote_currency: Quote currency symbol
        limit: Number of trades to fetch
        since_date: Start date (YYYY-MM-DD format)
        use_cache: Use cached data if available
        
    Returns:
        DataFrame with trade data
    """
    if not since_date:
        since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    query = """
    query ($network: EthereumNetwork!, $baseCurrency: String!, $quoteCurrency: String!, $since: ISO8601DateTime, $limit: Int!) {
      ethereum(network: $network) {
        dexTrades(
          baseCurrency: {is: $baseCurrency}
          quoteCurrency: {is: $quoteCurrency}
          date: {since: $since}
          options: {limit: $limit, desc: "block.timestamp.time"}
        ) {
          block {
            timestamp {
              time(format: "%Y-%m-%d %H:%M:%S")
            }
            height
          }
          transaction {
            hash
          }
          baseCurrency {
            symbol
            address
          }
          quoteCurrency {
            symbol
            address
          }
          baseAmount
          quoteAmount
          trades: count
          quotePrice
          exchange {
            fullName
          }
          smartContract {
            address {
              address
            }
          }
        }
      }
    }
    """
    
    variables = {
        "network": network,
        "baseCurrency": base_currency,
        "quoteCurrency": quote_currency,
        "since": since_date,
        "limit": limit
    }
    
    result = _execute_query(query, variables, use_cache=use_cache)
    
    if not result or "error" in result:
        return pd.DataFrame({"error": [result.get("error", "Unknown error")]})
    
    if "data" not in result or not result["data"].get("ethereum", {}).get("dexTrades"):
        return pd.DataFrame()
    
    trades = result["data"]["ethereum"]["dexTrades"]
    
    # Flatten nested structure
    records = []
    for trade in trades:
        records.append({
            "timestamp": trade["block"]["timestamp"]["time"],
            "block_height": trade["block"]["height"],
            "tx_hash": trade["transaction"]["hash"],
            "base_symbol": trade["baseCurrency"]["symbol"],
            "base_address": trade["baseCurrency"]["address"],
            "quote_symbol": trade["quoteCurrency"]["symbol"],
            "quote_address": trade["quoteCurrency"]["address"],
            "base_amount": float(trade["baseAmount"]),
            "quote_amount": float(trade["quoteAmount"]),
            "price": float(trade["quotePrice"]),
            "trade_count": trade["trades"],
            "exchange": trade["exchange"]["fullName"],
            "contract_address": trade["smartContract"]["address"]["address"]
        })
    
    return pd.DataFrame(records)


def get_token_transfers(
    network: str = "ethereum",
    currency: str = "USDT",
    limit: int = 100,
    since_date: Optional[str] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Get token transfers for a specific token.
    
    Args:
        network: Blockchain network
        currency: Token symbol
        limit: Number of transfers to fetch
        since_date: Start date (YYYY-MM-DD format)
        use_cache: Use cached data if available
        
    Returns:
        DataFrame with transfer data
    """
    if not since_date:
        since_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    query = """
    query ($network: EthereumNetwork!, $currency: String!, $since: ISO8601DateTime, $limit: Int!) {
      ethereum(network: $network) {
        transfers(
          currency: {is: $currency}
          date: {since: $since}
          options: {limit: $limit, desc: "block.timestamp.time"}
        ) {
          block {
            timestamp {
              time(format: "%Y-%m-%d %H:%M:%S")
            }
            height
          }
          transaction {
            hash
          }
          sender {
            address
          }
          receiver {
            address
          }
          amount
          currency {
            symbol
            address
            decimals
          }
        }
      }
    }
    """
    
    variables = {
        "network": network,
        "currency": currency,
        "since": since_date,
        "limit": limit
    }
    
    result = _execute_query(query, variables, use_cache=use_cache)
    
    if not result or "error" in result:
        return pd.DataFrame({"error": [result.get("error", "Unknown error")]})
    
    if "data" not in result or not result["data"].get("ethereum", {}).get("transfers"):
        return pd.DataFrame()
    
    transfers = result["data"]["ethereum"]["transfers"]
    
    records = []
    for transfer in transfers:
        records.append({
            "timestamp": transfer["block"]["timestamp"]["time"],
            "block_height": transfer["block"]["height"],
            "tx_hash": transfer["transaction"]["hash"],
            "from": transfer["sender"]["address"],
            "to": transfer["receiver"]["address"],
            "amount": float(transfer["amount"]),
            "symbol": transfer["currency"]["symbol"],
            "token_address": transfer["currency"]["address"],
            "decimals": transfer["currency"]["decimals"]
        })
    
    return pd.DataFrame(records)


def get_smart_contract_events(
    contract_address: str,
    network: str = "ethereum",
    limit: int = 100,
    since_date: Optional[str] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Get smart contract events for a specific contract.
    
    Args:
        network: Blockchain network
        contract_address: Contract address to monitor
        limit: Number of events to fetch
        since_date: Start date (YYYY-MM-DD format)
        use_cache: Use cached data if available
        
    Returns:
        DataFrame with event data
    """
    if not since_date:
        since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    query = """
    query ($network: EthereumNetwork!, $address: String!, $since: ISO8601DateTime, $limit: Int!) {
      ethereum(network: $network) {
        smartContractEvents(
          smartContractAddress: {is: $address}
          date: {since: $since}
          options: {limit: $limit, desc: "block.timestamp.time"}
        ) {
          block {
            timestamp {
              time(format: "%Y-%m-%d %H:%M:%S")
            }
            height
          }
          transaction {
            hash
          }
          smartContract {
            address {
              address
            }
            contractType
          }
          smartContractEvent {
            name
            signature
          }
          arguments {
            argument
            value
          }
        }
      }
    }
    """
    
    variables = {
        "network": network,
        "address": contract_address,
        "since": since_date,
        "limit": limit
    }
    
    result = _execute_query(query, variables, use_cache=use_cache)
    
    if not result or "error" in result:
        return pd.DataFrame({"error": [result.get("error", "Unknown error")]})
    
    if "data" not in result or not result["data"].get("ethereum", {}).get("smartContractEvents"):
        return pd.DataFrame()
    
    events = result["data"]["ethereum"]["smartContractEvents"]
    
    records = []
    for event in events:
        # Parse arguments
        args = {arg["argument"]: arg["value"] for arg in event["arguments"]}
        
        records.append({
            "timestamp": event["block"]["timestamp"]["time"],
            "block_height": event["block"]["height"],
            "tx_hash": event["transaction"]["hash"],
            "contract_address": event["smartContract"]["address"]["address"],
            "contract_type": event["smartContract"]["contractType"],
            "event_name": event["smartContractEvent"]["name"],
            "event_signature": event["smartContractEvent"]["signature"],
            "arguments": json.dumps(args)
        })
    
    return pd.DataFrame(records)


def get_address_balance(
    address: str,
    network: str = "ethereum",
    currencies: Optional[List[str]] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Get token balances for an address.
    
    Args:
        network: Blockchain network
        address: Wallet address
        currencies: List of token symbols (None for all)
        use_cache: Use cached data if available
        
    Returns:
        DataFrame with balance data
    """
    currency_filter = ""
    if currencies:
        currency_filter = f'currency: {{in: {json.dumps(currencies)}}}'
    
    query = f"""
    query {{
      ethereum(network: {network}) {{
        address(address: {{is: "{address}"}}) {{
          balances({currency_filter}) {{
            currency {{
              symbol
              address
              decimals
              tokenType
            }}
            value
          }}
        }}
      }}
    }}
    """
    
    result = _execute_query(query, use_cache=use_cache, cache_hours=1)
    
    if not result or "error" in result:
        return pd.DataFrame({"error": [result.get("error", "Unknown error")]})
    
    if "data" not in result or not result["data"].get("ethereum", {}).get("address"):
        return pd.DataFrame()
    
    balances = result["data"]["ethereum"]["address"][0]["balances"]
    
    records = []
    for balance in balances:
        records.append({
            "address": address,
            "symbol": balance["currency"]["symbol"],
            "token_address": balance["currency"]["address"],
            "decimals": balance["currency"]["decimals"],
            "token_type": balance["currency"]["tokenType"],
            "balance": float(balance["value"])
        })
    
    return pd.DataFrame(records)


def get_latest_blocks(
    network: str = "ethereum",
    limit: int = 10,
    use_cache: bool = False
) -> pd.DataFrame:
    """
    Get latest blocks from a blockchain.
    
    Args:
        network: Blockchain network
        limit: Number of blocks to fetch
        use_cache: Use cached data if available
        
    Returns:
        DataFrame with block data
    """
    query = """
    query ($network: EthereumNetwork!, $limit: Int!) {
      ethereum(network: $network) {
        blocks(options: {limit: $limit, desc: "height"}) {
          timestamp {
            time(format: "%Y-%m-%d %H:%M:%S")
          }
          height
          blockHash
          transactionCount
          difficulty
          gasUsed
          gasLimit
          miner {
            address
          }
        }
      }
    }
    """
    
    variables = {
        "network": network,
        "limit": limit
    }
    
    result = _execute_query(query, variables, use_cache=use_cache)
    
    if not result or "error" in result:
        return pd.DataFrame({"error": [result.get("error", "Unknown error")]})
    
    if "data" not in result or not result["data"].get("ethereum", {}).get("blocks"):
        return pd.DataFrame()
    
    blocks = result["data"]["ethereum"]["blocks"]
    
    records = []
    for block in blocks:
        records.append({
            "timestamp": block["timestamp"]["time"],
            "height": block["height"],
            "hash": block["blockHash"],
            "tx_count": block["transactionCount"],
            "difficulty": block.get("difficulty", 0),
            "gas_used": block["gasUsed"],
            "gas_limit": block["gasLimit"],
            "miner": block["miner"]["address"]
        })
    
    return pd.DataFrame(records)


if __name__ == "__main__":
    # Test module
    print("Bitquery API Module - Test")
    print("=" * 50)
    
    api_key = _get_api_key()
    if api_key:
        print(f"✓ API key found: {api_key[:8]}...")
    else:
        print("⚠ No API key (set BITQUERY_API_KEY)")
    
    print("\n1. Testing DEX trades...")
    df = get_dex_trades(limit=5)
    if not df.empty:
        print(f"   Retrieved {len(df)} trades")
        if "error" not in df.columns:
            print(f"   Latest price: {df.iloc[0]['price']:.4f}")
    else:
        print("   No data or error")
    
    print("\n2. Testing token transfers...")
    df = get_token_transfers(limit=5)
    if not df.empty:
        print(f"   Retrieved {len(df)} transfers")
    else:
        print("   No data or error")
    
    print("\n3. Testing latest blocks...")
    df = get_latest_blocks(limit=5)
    if not df.empty:
        print(f"   Retrieved {len(df)} blocks")
        if "error" not in df.columns:
            print(f"   Latest block: {df.iloc[0]['height']}")
    else:
        print("   No data or error")
    
    print("\n✓ Module test complete")
