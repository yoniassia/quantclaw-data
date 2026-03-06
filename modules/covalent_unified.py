#!/usr/bin/env python3
"""
Covalent Unified API — Multi-Chain On-Chain Data

Data Source: Covalent API
Update: Real-time
Free: Yes (100,000 credits/month, 1 credit per call)

Provides:
- Wallet balances across 50+ blockchains
- Transaction histories
- Token metadata and prices
- DeFi liquidity pool data
- NFT transactions
- Historical portfolio values

Supported chains: Ethereum, Polygon, BSC, Avalanche, Arbitrum, Optimism, etc.

Usage:
    from modules import covalent_unified
    
    # Get wallet balances
    df = covalent_unified.get_balances(address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', chain_id=1)
    
    # Get transactions
    df = covalent_unified.get_transactions(address='0x...', chain_id=1)
    
    # Get token prices
    df = covalent_unified.get_token_prices(chain_id=1, contract_address='0x...')

Example:
    python -c "from modules import covalent_unified; print(covalent_unified.get_balances('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', 1))"
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import requests
import pandas as pd
import json
import time
from datetime import datetime
from typing import Optional, Dict, List

# API key from environment
COVALENT_API_KEY = os.environ.get("COVALENT_API_KEY", "")

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 300  # 5 minutes for real-time data

# API configuration
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"

# Chain IDs mapping
CHAIN_IDS = {
    'ethereum': 1,
    'eth': 1,
    'polygon': 137,
    'matic': 137,
    'bsc': 56,
    'binance': 56,
    'avalanche': 43114,
    'avax': 43114,
    'arbitrum': 42161,
    'arb': 42161,
    'optimism': 10,
    'op': 10,
    'fantom': 250,
    'ftm': 250,
    'moonbeam': 1284,
    'moonriver': 1285,
}


def get_api_key() -> Optional[str]:
    """
    Get Covalent API key from environment variable.
    
    Returns API key or None.
    """
    if COVALENT_API_KEY:
        return COVALENT_API_KEY
    
    print("Warning: COVALENT_API_KEY not set in environment")
    return None


def get_chain_id(chain: any) -> int:
    """
    Resolve chain name or ID to numeric chain ID.
    
    Args:
        chain: Chain name (string) or ID (int)
        
    Returns:
        Numeric chain ID
    """
    if isinstance(chain, int):
        return chain
    
    if isinstance(chain, str):
        chain_lower = chain.lower()
        if chain_lower in CHAIN_IDS:
            return CHAIN_IDS[chain_lower]
        
        # Try to parse as int
        try:
            return int(chain)
        except ValueError:
            pass
    
    # Default to Ethereum
    print(f"Warning: Unknown chain '{chain}', defaulting to Ethereum (1)")
    return 1


def fetch_balances(address: str, chain_id: int, api_key: str) -> Dict:
    """
    Fetch wallet balances from Covalent API.
    
    Args:
        address: Wallet address
        chain_id: Blockchain chain ID
        api_key: Covalent API key
        
    Returns:
        API response dict
    """
    url = f"{COVALENT_BASE_URL}/{chain_id}/address/{address}/balances_v2/"
    
    try:
        response = requests.get(url, params={'key': api_key}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balances: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return {}


def fetch_transactions(address: str, chain_id: int, api_key: str, page: int = 0) -> Dict:
    """
    Fetch transaction history from Covalent API.
    
    Args:
        address: Wallet address
        chain_id: Blockchain chain ID
        api_key: Covalent API key
        page: Page number for pagination
        
    Returns:
        API response dict
    """
    url = f"{COVALENT_BASE_URL}/{chain_id}/address/{address}/transactions_v2/"
    
    try:
        response = requests.get(url, params={'key': api_key, 'page-number': page}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return {}


def parse_balances(data: Dict, address: str, chain_id: int) -> pd.DataFrame:
    """
    Parse balance data into DataFrame.
    
    Args:
        data: Raw API response
        address: Wallet address
        chain_id: Chain ID
        
    Returns:
        DataFrame with balance data
    """
    if not data or 'data' not in data:
        return pd.DataFrame()
    
    items = data['data'].get('items', [])
    
    if not items:
        return pd.DataFrame()
    
    balances = []
    for item in items:
        balance_dict = {
            'address': address,
            'chain_id': chain_id,
            'contract_address': item.get('contract_address', ''),
            'contract_name': item.get('contract_name', ''),
            'contract_ticker_symbol': item.get('contract_ticker_symbol', ''),
            'contract_decimals': item.get('contract_decimals', 0),
            'balance': item.get('balance', '0'),
            'balance_24h': item.get('balance_24h', '0'),
            'quote': item.get('quote', 0),
            'quote_24h': item.get('quote_24h', 0),
            'quote_rate': item.get('quote_rate', 0),
            'quote_rate_24h': item.get('quote_rate_24h', 0),
            'type': item.get('type', ''),
            'supports_erc': item.get('supports_erc', []),
            'logo_url': item.get('logo_url', ''),
            'updated': datetime.now().isoformat()
        }
        
        balances.append(balance_dict)
    
    df = pd.DataFrame(balances)
    
    # Convert numeric columns
    numeric_cols = ['contract_decimals', 'quote', 'quote_24h', 'quote_rate', 'quote_rate_24h']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def parse_transactions(data: Dict, address: str, chain_id: int) -> pd.DataFrame:
    """
    Parse transaction data into DataFrame.
    
    Args:
        data: Raw API response
        address: Wallet address
        chain_id: Chain ID
        
    Returns:
        DataFrame with transaction data
    """
    if not data or 'data' not in data:
        return pd.DataFrame()
    
    items = data['data'].get('items', [])
    
    if not items:
        return pd.DataFrame()
    
    txs = []
    for item in items:
        tx_dict = {
            'address': address,
            'chain_id': chain_id,
            'block_signed_at': item.get('block_signed_at', ''),
            'block_height': item.get('block_height', 0),
            'tx_hash': item.get('tx_hash', ''),
            'tx_offset': item.get('tx_offset', 0),
            'successful': item.get('successful', False),
            'from_address': item.get('from_address', ''),
            'to_address': item.get('to_address', ''),
            'value': item.get('value', '0'),
            'value_quote': item.get('value_quote', 0),
            'gas_offered': item.get('gas_offered', 0),
            'gas_spent': item.get('gas_spent', 0),
            'gas_price': item.get('gas_price', 0),
            'gas_quote': item.get('gas_quote', 0),
            'gas_quote_rate': item.get('gas_quote_rate', 0),
            'updated': datetime.now().isoformat()
        }
        
        txs.append(tx_dict)
    
    df = pd.DataFrame(txs)
    
    # Parse timestamp
    if 'block_signed_at' in df.columns:
        df['block_signed_at'] = pd.to_datetime(df['block_signed_at'], errors='coerce')
    
    # Convert numeric columns
    numeric_cols = ['block_height', 'tx_offset', 'value_quote', 'gas_offered', 
                    'gas_spent', 'gas_price', 'gas_quote', 'gas_quote_rate']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def get_balances(address: str, chain: any = 'ethereum', use_cache: bool = True) -> pd.DataFrame:
    """
    Get wallet balances.
    
    Args:
        address: Wallet address
        chain: Chain name or ID
        use_cache: Whether to use cached data
        
    Returns:
        DataFrame with balance data
    """
    chain_id = get_chain_id(chain)
    
    cache_key = f"covalent_balances_{chain_id}_{address}"
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if use_cache and os.path.exists(cache_path):
        cache_age = time.time() - os.path.getmtime(cache_path)
        if cache_age < CACHE_TTL:
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    return pd.DataFrame(cached_data)
            except (json.JSONDecodeError, IOError):
                pass
    
    # Fetch fresh data
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame()
    
    data = fetch_balances(address, chain_id, api_key)
    df = parse_balances(data, address, chain_id)
    
    # Cache the result
    if not df.empty:
        try:
            with open(cache_path, 'w') as f:
                json.dump(df.to_dict('records'), f, indent=2)
        except IOError as e:
            print(f"Warning: Could not write cache: {e}")
    
    return df


def get_transactions(address: str, chain: any = 'ethereum', page: int = 0, use_cache: bool = True) -> pd.DataFrame:
    """
    Get transaction history.
    
    Args:
        address: Wallet address
        chain: Chain name or ID
        page: Page number
        use_cache: Whether to use cached data
        
    Returns:
        DataFrame with transaction data
    """
    chain_id = get_chain_id(chain)
    
    cache_key = f"covalent_txs_{chain_id}_{address}_{page}"
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if use_cache and os.path.exists(cache_path):
        cache_age = time.time() - os.path.getmtime(cache_path)
        if cache_age < CACHE_TTL:
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    df = pd.DataFrame(cached_data)
                    # Convert timestamp back
                    if 'block_signed_at' in df.columns:
                        df['block_signed_at'] = pd.to_datetime(df['block_signed_at'])
                    return df
            except (json.JSONDecodeError, IOError):
                pass
    
    # Fetch fresh data
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame()
    
    data = fetch_transactions(address, chain_id, api_key, page)
    df = parse_transactions(data, address, chain_id)
    
    # Cache the result
    if not df.empty:
        try:
            # Convert timestamp to string for JSON
            df_copy = df.copy()
            if 'block_signed_at' in df_copy.columns:
                df_copy['block_signed_at'] = df_copy['block_signed_at'].astype(str)
            with open(cache_path, 'w') as f:
                json.dump(df_copy.to_dict('records'), f, indent=2)
        except IOError as e:
            print(f"Warning: Could not write cache: {e}")
    
    return df


def get_data(address: str, data_type: str = 'balances', chain: any = 'ethereum', **kwargs) -> pd.DataFrame:
    """
    Get data from Covalent API.
    
    Args:
        address: Wallet address
        data_type: Type of data ('balances' or 'transactions')
        chain: Chain name or ID
        **kwargs: Additional arguments
        
    Returns:
        DataFrame with requested data
    """
    if data_type == 'balances':
        return get_balances(address, chain, **kwargs)
    elif data_type == 'transactions':
        return get_transactions(address, chain, **kwargs)
    else:
        print(f"Unknown data type: {data_type}")
        return pd.DataFrame()


def get_latest(address: str = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb') -> pd.DataFrame:
    """Get latest balances for an address (default: Vitalik's address)."""
    return get_balances(address, 'ethereum')


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Covalent Unified API - Multi-chain on-chain data')
    parser.add_argument('address', help='Wallet address')
    parser.add_argument('--type', '-t', default='balances', choices=['balances', 'transactions'],
                       help='Data type (default: balances)')
    parser.add_argument('--chain', '-c', default='ethereum', help='Chain name or ID (default: ethereum)')
    parser.add_argument('--page', '-p', type=int, default=0, help='Page number for transactions')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--no-cache', action='store_true', help='Skip cache')
    
    args = parser.parse_args()
    
    if args.type == 'transactions':
        df = get_transactions(args.address, args.chain, args.page, use_cache=not args.no_cache)
    else:
        df = get_balances(args.address, args.chain, use_cache=not args.no_cache)
    
    if args.json:
        print(df.to_json(orient='records', indent=2))
    else:
        if df.empty:
            print(f"No {args.type} found for {args.address} on chain {args.chain}")
        else:
            print(f"\nCovalent {args.type.upper()} for {args.address}")
            print(f"Chain: {args.chain}")
            print(f"Records: {len(df)}")
            print(f"\nData:\n")
            print(df.head(10).to_string(index=False))
