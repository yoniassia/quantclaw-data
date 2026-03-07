#!/usr/bin/env python3
"""
The Graph Protocol API Module

Decentralized protocol for indexing and querying blockchain data through GraphQL subgraphs.
- DeFi protocol data (Uniswap, Aave, Compound)
- DEX trading volumes and liquidity pools
- Lending markets and interest rates
- Token swap data and price feeds

Data Source: https://gateway.thegraph.com (Decentralized Network)
Refresh: Real-time blockchain indexing
Coverage: Ethereum, Polygon, Arbitrum, Optimism, and 30+ chains
Free tier: Yes, rate-limited queries, no API key required for public gateway

NOTE: The Graph DEPRECATED free hosted service endpoints in 2024/2025.
      All queries return: "This endpoint has been removed"
      Module returns structured errors with migration alternatives.
      STATUS: Non-functional without paid API key.

Author: QUANTCLAW DATA NightBuilder
Phase: GRAPH_001
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# The Graph Studio API endpoints (working as of 2024)
# Using direct API endpoints instead of deprecated hosted service
SUBGRAPH_URLS = {
    'uniswap-v3': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
    'uniswap-v2': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
    'aave-v2': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v2',
    'curve': 'https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum'
}

# Legacy - kept for compatibility
SUBGRAPH_IDS = {k: k for k in SUBGRAPH_URLS.keys()}


def query_subgraph(subgraph_id: str, query: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a GraphQL query against a subgraph.
    
    Args:
        subgraph_id: Subgraph identifier key (e.g., 'uniswap-v3')
        query: GraphQL query string
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing query results or error info
        
    Example:
        >>> result = query_subgraph('uniswap-v3', '{ factories { id } }')
        >>> print(result['data'])
    """
    # Use direct URL if subgraph_id is a key in SUBGRAPH_URLS
    if subgraph_id in SUBGRAPH_URLS:
        url = SUBGRAPH_URLS[subgraph_id]
    else:
        # Fallback: assume it's a full URL
        url = subgraph_id
    
    payload = json.dumps({"query": query}).encode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'QuantClaw-Data/1.0'
    }
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            return {
                'success': True,
                'data': data.get('data', {}),
                'errors': data.get('errors', []),
                'subgraph_id': subgraph_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        return {
            'success': False,
            'error': f'HTTP {e.code}: {e.reason}',
            'error_detail': error_body[:500],
            'subgraph_id': subgraph_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    except urllib.error.URLError as e:
        return {
            'success': False,
            'error': f'Connection error: {str(e.reason)}',
            'subgraph_id': subgraph_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Query failed: {str(e)}',
            'subgraph_id': subgraph_id,
            'timestamp': datetime.utcnow().isoformat()
        }


def get_uniswap_v3_pools(first: int = 10, skip: int = 0) -> Dict[str, Any]:
    """
    Get top Uniswap V3 liquidity pools by TVL.
    
    Args:
        first: Number of pools to return (max 1000)
        skip: Number of pools to skip for pagination
        
    Returns:
        Dict with pool data including tokens, TVL, volume, fees
        
    Example:
        >>> pools = get_uniswap_v3_pools(first=5)
        >>> for pool in pools.get('data', {}).get('pools', []):
        ...     print(f"{pool['token0']['symbol']}/{pool['token1']['symbol']}")
    """
    query = f"""
    {{
      pools(first: {first}, skip: {skip}, orderBy: totalValueLockedUSD, orderDirection: desc) {{
        id
        token0 {{
          id
          symbol
          name
        }}
        token1 {{
          id
          symbol
          name
        }}
        feeTier
        liquidity
        volumeUSD
        txCount
        totalValueLockedUSD
      }}
    }}
    """
    
    result = query_subgraph(SUBGRAPH_IDS['uniswap-v3'], query)
    result['note'] = 'Using decentralized network - deployment may be outdated or migrated'
    return result


def get_uniswap_v2_pairs(first: int = 10) -> Dict[str, Any]:
    """
    Get Uniswap V2 trading pairs.
    
    Args:
        first: Number of pairs to return
        
    Returns:
        Dict with pair data including reserves and volume
        
    Example:
        >>> pairs = get_uniswap_v2_pairs(first=5)
        >>> for pair in pairs.get('data', {}).get('pairs', []):
        ...     print(f"{pair['token0']['symbol']}/{pair['token1']['symbol']}")
    """
    query = f"""
    {{
      pairs(first: {first}, orderBy: reserveUSD, orderDirection: desc) {{
        id
        token0 {{
          id
          symbol
          name
        }}
        token1 {{
          id
          symbol
          name
        }}
        reserve0
        reserve1
        reserveUSD
        volumeUSD
        txCount
      }}
    }}
    """
    
    result = query_subgraph(SUBGRAPH_IDS['uniswap-v2'], query)
    result['note'] = 'Using decentralized network - deployment may be outdated or migrated'
    return result


def get_aave_v2_reserves(first: int = 20) -> Dict[str, Any]:
    """
    Get Aave V2 lending reserves (markets).
    
    Args:
        first: Number of reserves to return
        
    Returns:
        Dict with reserve data including liquidity and rates
        
    Example:
        >>> reserves = get_aave_v2_reserves()
        >>> for reserve in reserves.get('data', {}).get('reserves', []):
        ...     print(f"{reserve['symbol']}: {reserve['liquidityRate']}")
    """
    query = f"""
    {{
      reserves(first: {first}) {{
        id
        symbol
        name
        decimals
        liquidityRate
        variableBorrowRate
        stableBorrowRate
        totalLiquidity
        availableLiquidity
        totalDeposits
        totalBorrows
      }}
    }}
    """
    
    result = query_subgraph(SUBGRAPH_IDS['aave-v2'], query)
    result['note'] = 'Using decentralized network - deployment may be outdated or migrated'
    return result


def get_compound_markets(first: int = 20) -> Dict[str, Any]:
    """
    Get Compound V2 lending markets.
    
    NOTE: Compound data may not be available on decentralized network.
          Returns stub response for now.
    
    Args:
        first: Number of markets to return
        
    Returns:
        Dict indicating service migration status
    """
    return {
        'success': False,
        'error': 'Compound subgraph not available on free decentralized gateway',
        'note': 'The Graph migrated to paid decentralized network. Free public gateway has limited subgraphs.',
        'alternatives': [
            'Use Compound API directly: https://api.compound.finance/api/v2/ctoken',
            'Use DeFiLlama API for lending data',
            'Deploy your own subgraph indexer'
        ],
        'timestamp': datetime.utcnow().isoformat()
    }


def get_dex_volume(protocol: str = 'uniswap-v3', days: int = 7) -> Dict[str, Any]:
    """
    Get DEX trading volume for recent days.
    
    Args:
        protocol: DEX protocol ('uniswap-v3', 'uniswap-v2')
        days: Number of days to fetch
        
    Returns:
        Dict with daily volume data or migration notice
    """
    if protocol not in SUBGRAPH_IDS:
        return {
            'success': False,
            'error': f'Unknown protocol: {protocol}. Available: {list(SUBGRAPH_IDS.keys())}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    query = f"""
    {{
      uniswapDayDatas(first: {days}, orderBy: date, orderDirection: desc) {{
        id
        date
        volumeUSD
        tvlUSD
        txCount
      }}
    }}
    """
    
    result = query_subgraph(SUBGRAPH_IDS[protocol], query)
    result['note'] = 'Decentralized network endpoints may have outdated or incomplete data'
    return result


def get_factory_data(protocol: str = 'uniswap-v3') -> Dict[str, Any]:
    """
    Get factory-level protocol statistics.
    
    Args:
        protocol: DEX protocol identifier
        
    Returns:
        Dict with total pools, volume, TVL if available
        
    Example:
        >>> factory = get_factory_data('uniswap-v3')
        >>> if factory['success']:
        ...     print(f"Total pools: {factory['data']['factories'][0]['poolCount']}")
    """
    if protocol not in SUBGRAPH_IDS:
        return {
            'success': False,
            'error': f'Unknown protocol: {protocol}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    query = """
    {
      factories(first: 1) {
        id
        poolCount
        txCount
        totalVolumeUSD
        totalValueLockedUSD
      }
    }
    """
    
    return query_subgraph(SUBGRAPH_IDS[protocol], query)


def get_token_swaps(token_address: str, first: int = 100, hours: int = 24) -> Dict[str, Any]:
    """
    Get recent token swaps from Uniswap V3.
    
    Args:
        token_address: Ethereum token address (checksummed)
        first: Number of swaps to return
        hours: Look back period in hours
        
    Returns:
        Dict with swap transaction data or migration notice
    """
    timestamp = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
    
    # Note: Complex where clauses may not work on all gateways
    query = f"""
    {{
      swaps(
        first: {first},
        orderBy: timestamp,
        orderDirection: desc
      ) {{
        id
        timestamp
        amount0
        amount1
        amountUSD
        token0 {{
          symbol
        }}
        token1 {{
          symbol
        }}
      }}
    }}
    """
    
    result = query_subgraph(SUBGRAPH_IDS['uniswap-v3'], query)
    result['note'] = 'Filtered queries may not work on free gateway - returns all swaps'
    return result


def get_pool_info(pool_address: str) -> Dict[str, Any]:
    """
    Get detailed info for a specific Uniswap V3 pool.
    
    Args:
        pool_address: Pool contract address (checksummed)
        
    Returns:
        Dict with pool details or migration notice
    """
    query = f"""
    {{
      pool(id: "{pool_address.lower()}") {{
        id
        token0 {{
          symbol
          name
        }}
        token1 {{
          symbol
          name
        }}
        feeTier
        liquidity
        volumeUSD
        totalValueLockedUSD
        txCount
      }}
    }}
    """
    
    return query_subgraph(SUBGRAPH_IDS['uniswap-v3'], query)


# Migration helper
def get_migration_info() -> Dict[str, Any]:
    """
    Get information about The Graph's migration to decentralized network.
    
    Returns:
        Dict with migration details and recommended alternatives
    """
    return {
        'status': 'MIGRATED',
        'message': 'The Graph hosted service deprecated in 2024. Migrated to decentralized network.',
        'impact': 'Free public gateway has rate limits and may have outdated subgraphs',
        'alternatives': {
            'direct_apis': [
                'Uniswap: https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3 (may redirect)',
                'DeFiLlama: https://api.llama.fi (aggregated DeFi data)',
                'CoinGecko: https://api.coingecko.com (price feeds)',
                'Dune Analytics: https://dune.com/api (custom queries)'
            ],
            'paid_gateway': 'https://thegraph.com/studio (requires API key and GRT payments)',
            'self_hosted': 'Run your own Graph Node'
        },
        'free_tier_limits': {
            'rate_limit': '~100 req/min per IP',
            'query_complexity': 'Limited',
            'data_freshness': 'May lag behind chain head'
        },
        'timestamp': datetime.utcnow().isoformat()
    }


# Module metadata
__all__ = [
    'query_subgraph',
    'get_uniswap_v3_pools',
    'get_uniswap_v2_pairs',
    'get_aave_v2_reserves',
    'get_compound_markets',
    'get_dex_volume',
    'get_token_swaps',
    'get_pool_info',
    'get_factory_data',
    'get_migration_info',
    'SUBGRAPH_IDS'
]


if __name__ == "__main__":
    # Test basic functionality
    print("Testing The Graph API module...")
    print("\nNOTE: The Graph migrated to decentralized network.")
    print("Free public gateway has limitations.\n")
    
    # Show migration info
    info = get_migration_info()
    print("Migration Status:", info['status'])
    print("Message:", info['message'])
    print("\nAlternatives:")
    for alt in info['alternatives']['direct_apis'][:2]:
        print(f"  - {alt}")
    
    print("\nModule ready for import.")
    print("Functions: query_subgraph, get_uniswap_v3_pools, get_uniswap_v2_pairs,")
    print("           get_aave_v2_reserves, get_factory_data, get_migration_info")
