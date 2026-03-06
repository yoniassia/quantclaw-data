#!/usr/bin/env python3
"""the_graph — The Graph blockchain indexer. Requires API key (free 100k queries/month)."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# The Graph Gateway requires API key - get one at https://thegraph.com/studio/apikeys/
# Format: https://gateway.thegraph.com/api/{api-key}/subgraphs/id/{subgraph-id}

# Public fallback: use specific protocol subgraphs that might still work
FALLBACK_ENDPOINTS = {
    'uniswap-v3-info': 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-subgraph',
    'sushiswap': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange',
}

def query_subgraph(endpoint_url, query, variables=None):
    """Execute GraphQL query."""
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        resp = requests.post(endpoint_url, json=payload, timeout=30, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def get_data(ticker="fallback", limit=100, **kwargs):
    """
    Fetch DeFi protocol data from The Graph.
    ticker: 'fallback' uses free endpoints (limited), or provide custom URL.
    limit: max rows.
    
    NOTE: The Graph moved to decentralized network. Most hosted service endpoints
    are deprecated. For production use, get a free API key at thegraph.com/studio.
    This module uses fallback endpoints that may become unavailable.
    """
    module_name = __name__.split('.')[-1]
    cache_key = ticker.lower().replace('/', '_').replace(':', '_')[:50]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 3600:  # 1h cache
            with open(cache_file, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                df['fetch_time'] = datetime.now().isoformat()
                return df.head(limit)
    
    # Use fallback Sushiswap endpoint (more stable)
    if ticker == "fallback" or ticker == "sushiswap":
        endpoint = FALLBACK_ENDPOINTS['sushiswap']
        query = """
        {
          pairs(first: 100, orderBy: reserveUSD, orderDirection: desc) {
            id
            token0 { symbol name }
            token1 { symbol name }
            reserveUSD
            volumeUSD
            txCount
          }
        }
        """
    else:
        # Custom endpoint provided
        if not ticker.startswith('http'):
            return pd.DataFrame({"error": ["Provide full subgraph URL or use 'fallback' for public endpoint"]})
        endpoint = ticker
        # Generic query
        query = """
        {
          pairs(first: 100, orderBy: reserveUSD, orderDirection: desc) {
            id
            reserveUSD
            volumeUSD
          }
        }
        """
    
    result = query_subgraph(endpoint, query)
    
    if 'error' in result:
        return pd.DataFrame({"error": [result['error']]})
    if 'errors' in result:
        err_list = result.get('errors', [])
        err_msg = err_list[0].get('message', 'GraphQL error') if err_list else 'Unknown'
        return pd.DataFrame({"error": [err_msg]})
    
    data = result.get('data', {})
    pairs = data.get('pairs', [])
    
    if not pairs:
        return pd.DataFrame({"error": ["No data returned from subgraph"]})
    
    df = pd.DataFrame(pairs)
    
    # Clean nested tokens
    if 'token0' in df.columns:
        df['token0_symbol'] = df['token0'].apply(lambda x: x.get('symbol', '') if isinstance(x, dict) else '')
        df['token1_symbol'] = df['token1'].apply(lambda x: x.get('symbol', '') if isinstance(x, dict) else '')
        df['pair'] = df['token0_symbol'] + '/' + df['token1_symbol']
        df = df.drop(['token0', 'token1'], axis=1, errors='ignore')
    
    # Convert numerics
    for col in ['reserveUSD', 'volumeUSD', 'txCount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['fetch_time'] = datetime.now().isoformat()
    
    # Cache
    cache_data = df.to_dict('records')
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, default=str)
    
    return df.head(limit)

def get_sushiswap_pairs(limit=50):
    """Get top Sushiswap trading pairs by TVL (fallback endpoint)."""
    return get_data(ticker='fallback', limit=limit)

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "fallback"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
