#!/usr/bin/env python3
"""
DeFi TVL & Yield Aggregator Module — Total Value Locked, Yield Farming Rates via DeFi Llama API

Data Sources:
- DeFi Llama TVL API: Protocol TVL, historical data, chain-level data (free)
- DeFi Llama Yields API: Yield farming rates, pool APY/APR, historical yields (free)

Features:
- Real-time protocol TVL across 200+ protocols
- Yield farming opportunities with APY comparison
- Historical TVL trends and analytics
- Chain-level TVL breakdowns
- Stablecoin pool yields
- Risk-adjusted yield metrics

Author: QUANTCLAW DATA Build Agent
Phase: 186
API Docs: https://defillama.com/docs/api
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from collections import defaultdict

# API Configuration
DEFILLAMA_BASE_URL = "https://api.llama.fi"
YIELDS_BASE_URL = "https://yields.llama.fi"

# Chain mappings
MAJOR_CHAINS = [
    "Ethereum", "BSC", "Polygon", "Avalanche", "Arbitrum", 
    "Optimism", "Fantom", "Solana", "Base", "Cronos"
]

# Protocol categories
PROTOCOL_CATEGORIES = [
    "Lending", "DEX", "Yield", "CDP", "Derivatives", 
    "Options", "Bridge", "Staking", "Insurance", "Synthetics"
]


def get_global_tvl() -> Dict[str, Any]:
    """
    Get current global DeFi TVL across all protocols and chains
    Returns total TVL in USD and historical data
    """
    try:
        # Get historical chart data
        url = f"{DEFILLAMA_BASE_URL}/charts"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Get latest TVL (last data point)
        if data and len(data) > 0:
            latest = data[-1]
            current_tvl = latest.get('totalLiquidityUSD', 0)
            
            # Calculate change over time
            if len(data) > 1:
                day_ago = data[-2] if len(data) > 1 else data[0]
                week_ago = data[-7] if len(data) > 7 else data[0]
                
                change_1d = ((current_tvl - day_ago.get('totalLiquidityUSD', 0)) / day_ago.get('totalLiquidityUSD', 1)) * 100 if day_ago.get('totalLiquidityUSD') else 0
                change_7d = ((current_tvl - week_ago.get('totalLiquidityUSD', 0)) / week_ago.get('totalLiquidityUSD', 1)) * 100 if week_ago.get('totalLiquidityUSD') else 0
            else:
                change_1d = 0
                change_7d = 0
            
            return {
                "current_tvl_usd": current_tvl,
                "change_1d_pct": round(change_1d, 2),
                "change_7d_pct": round(change_7d, 2),
                "timestamp": datetime.now().isoformat(),
                "data_source": "DeFi Llama",
                "note": "Global TVL across all DeFi protocols"
            }
        
        return {"error": "No data available"}
    
    except Exception as e:
        return {"error": str(e)}


def get_protocol_tvl(protocol: str) -> Dict[str, Any]:
    """
    Get TVL data for a specific protocol
    protocol: Protocol slug (e.g., 'aave', 'uniswap', 'compound')
    """
    try:
        url = f"{DEFILLAMA_BASE_URL}/protocol/{protocol}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract key metrics
        current_tvl = data.get('tvl', [])
        if current_tvl:
            latest_tvl = current_tvl[-1].get('totalLiquidityUSD', 0)
        else:
            latest_tvl = data.get('chainTvls', {}).get('Ethereum', 0)
        
        chains_tvl = data.get('chainTvls', {})
        
        # Calculate chain breakdown
        chain_breakdown = {}
        for chain, values in chains_tvl.items():
            if isinstance(values, dict):
                chain_tvl = values.get('tvl', [])
                if chain_tvl:
                    chain_breakdown[chain] = chain_tvl[-1].get('totalLiquidityUSD', 0)
            elif isinstance(values, (int, float)):
                chain_breakdown[chain] = values
        
        return {
            "protocol": data.get('name', protocol),
            "slug": data.get('slug', protocol),
            "tvl_usd": latest_tvl,
            "chain_breakdown": chain_breakdown,
            "category": data.get('category', 'Unknown'),
            "logo": data.get('logo'),
            "url": data.get('url'),
            "description": data.get('description'),
            "twitter": data.get('twitter'),
            "gecko_id": data.get('gecko_id'),
            "timestamp": datetime.now().isoformat(),
            "chains": list(chain_breakdown.keys()) if chain_breakdown else data.get('chains', [])
        }
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Protocol '{protocol}' not found. Try searching protocols first."}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_all_protocols() -> Dict[str, Any]:
    """
    Get list of all DeFi protocols with their current TVL
    Returns sorted list by TVL
    """
    try:
        url = f"{DEFILLAMA_BASE_URL}/protocols"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        protocols = response.json()
        
        # Sort by TVL
        sorted_protocols = sorted(
            protocols, 
            key=lambda x: x.get('tvl', 0), 
            reverse=True
        )
        
        # Format top 50 protocols
        top_protocols = []
        for p in sorted_protocols[:50]:
            top_protocols.append({
                "name": p.get('name'),
                "slug": p.get('slug'),
                "tvl_usd": p.get('tvl', 0),
                "change_1h": p.get('change_1h'),
                "change_1d": p.get('change_1d'),
                "change_7d": p.get('change_7d'),
                "category": p.get('category'),
                "chains": p.get('chains', []),
                "mcap": p.get('mcap')
            })
        
        return {
            "total_protocols": len(protocols),
            "top_50_protocols": top_protocols,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_chain_tvl(chain: str) -> Dict[str, Any]:
    """
    Get TVL for a specific blockchain
    chain: Chain name (e.g., 'Ethereum', 'BSC', 'Polygon')
    """
    try:
        url = f"{DEFILLAMA_BASE_URL}/v2/historicalChainTvl/{chain}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Get current TVL (last data point)
        if data:
            latest = data[-1]
            current_tvl = latest.get('tvl', 0)
            
            # Calculate change over time
            if len(data) > 1:
                day_ago = data[-2] if len(data) > 1 else data[0]
                week_ago = data[-7] if len(data) > 7 else data[0]
                
                change_1d = ((current_tvl - day_ago.get('tvl', 0)) / day_ago.get('tvl', 1)) * 100 if day_ago.get('tvl') else 0
                change_7d = ((current_tvl - week_ago.get('tvl', 0)) / week_ago.get('tvl', 1)) * 100 if week_ago.get('tvl') else 0
            else:
                change_1d = 0
                change_7d = 0
            
            return {
                "chain": chain,
                "tvl_usd": current_tvl,
                "change_1d_pct": round(change_1d, 2),
                "change_7d_pct": round(change_7d, 2),
                "timestamp": datetime.fromtimestamp(latest.get('date', 0)).isoformat(),
                "historical_data_points": len(data)
            }
        
        return {"error": f"No data found for chain '{chain}'"}
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Chain '{chain}' not found. Available chains: {', '.join(MAJOR_CHAINS)}"}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_chains_tvl() -> Dict[str, Any]:
    """
    Get TVL breakdown across all major chains
    """
    try:
        url = f"{DEFILLAMA_BASE_URL}/v2/chains"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        chains = response.json()
        
        # Sort by TVL
        sorted_chains = sorted(
            chains,
            key=lambda x: x.get('tvl', 0),
            reverse=True
        )
        
        chain_data = []
        for chain in sorted_chains[:20]:  # Top 20 chains
            chain_data.append({
                "name": chain.get('name'),
                "gecko_id": chain.get('gecko_id'),
                "tvl_usd": chain.get('tvl', 0),
                "token_symbol": chain.get('tokenSymbol'),
                "cmc_id": chain.get('cmcId')
            })
        
        total_tvl = sum(c.get('tvl', 0) for c in chains)
        
        return {
            "total_chains": len(chains),
            "total_tvl_usd": total_tvl,
            "top_20_chains": chain_data,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_yield_pools(chain: Optional[str] = None, min_tvl: float = 1000000) -> Dict[str, Any]:
    """
    Get yield farming opportunities across DeFi protocols
    chain: Optional chain filter (e.g., 'Ethereum', 'BSC')
    min_tvl: Minimum pool TVL in USD (default $1M)
    """
    try:
        url = f"{YIELDS_BASE_URL}/pools"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        pools = response.json().get('data', [])
        
        # Filter by chain and TVL
        filtered_pools = []
        for pool in pools:
            pool_tvl = pool.get('tvlUsd', 0)
            pool_chain = pool.get('chain', '')
            
            # Apply filters
            if pool_tvl < min_tvl:
                continue
            if chain and pool_chain.lower() != chain.lower():
                continue
            
            filtered_pools.append({
                "pool_id": pool.get('pool'),
                "chain": pool_chain,
                "project": pool.get('project'),
                "symbol": pool.get('symbol'),
                "tvl_usd": pool_tvl,
                "apy": pool.get('apy', 0),
                "apy_base": pool.get('apyBase', 0),
                "apy_reward": pool.get('apyReward', 0),
                "il_risk": pool.get('ilRisk', 'unknown'),
                "exposure": pool.get('exposure', 'single'),
                "stablecoin": pool.get('stablecoin', False),
                "url": pool.get('url')
            })
        
        # Sort by APY
        filtered_pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
        
        # Take top 50
        top_pools = filtered_pools[:50]
        
        return {
            "total_pools_found": len(filtered_pools),
            "top_50_pools": top_pools,
            "filters": {
                "chain": chain or "All",
                "min_tvl_usd": min_tvl
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_stablecoin_yields(min_apy: float = 0) -> Dict[str, Any]:
    """
    Get stablecoin yield opportunities (low risk)
    min_apy: Minimum APY threshold (default 0%)
    """
    try:
        url = f"{YIELDS_BASE_URL}/pools"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        pools = response.json().get('data', [])
        
        # Filter for stablecoins
        stablecoin_pools = []
        for pool in pools:
            if not pool.get('stablecoin', False):
                continue
            
            apy = pool.get('apy', 0)
            if apy < min_apy:
                continue
            
            stablecoin_pools.append({
                "pool_id": pool.get('pool'),
                "chain": pool.get('chain'),
                "project": pool.get('project'),
                "symbol": pool.get('symbol'),
                "tvl_usd": pool.get('tvlUsd', 0),
                "apy": apy,
                "apy_base": pool.get('apyBase', 0),
                "apy_reward": pool.get('apyReward', 0),
                "exposure": pool.get('exposure', 'single'),
                "url": pool.get('url')
            })
        
        # Sort by APY
        stablecoin_pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
        
        # Take top 30
        top_pools = stablecoin_pools[:30]
        
        return {
            "total_stablecoin_pools": len(stablecoin_pools),
            "top_30_pools": top_pools,
            "min_apy_filter": min_apy,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_protocol_yields(protocol: str) -> Dict[str, Any]:
    """
    Get all yield pools for a specific protocol
    protocol: Protocol name (e.g., 'aave', 'compound', 'curve')
    """
    try:
        url = f"{YIELDS_BASE_URL}/pools"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        pools = response.json().get('data', [])
        
        # Filter by protocol
        protocol_pools = []
        for pool in pools:
            if pool.get('project', '').lower() == protocol.lower():
                protocol_pools.append({
                    "pool_id": pool.get('pool'),
                    "chain": pool.get('chain'),
                    "symbol": pool.get('symbol'),
                    "tvl_usd": pool.get('tvlUsd', 0),
                    "apy": pool.get('apy', 0),
                    "apy_base": pool.get('apyBase', 0),
                    "apy_reward": pool.get('apyReward', 0),
                    "il_risk": pool.get('ilRisk', 'unknown'),
                    "stablecoin": pool.get('stablecoin', False),
                    "url": pool.get('url')
                })
        
        if not protocol_pools:
            return {"error": f"No pools found for protocol '{protocol}'"}
        
        # Sort by TVL
        protocol_pools.sort(key=lambda x: x.get('tvl_usd', 0), reverse=True)
        
        # Calculate aggregate stats
        total_tvl = sum(p.get('tvl_usd', 0) for p in protocol_pools)
        avg_apy = sum(p.get('apy', 0) for p in protocol_pools) / len(protocol_pools) if protocol_pools else 0
        
        return {
            "protocol": protocol,
            "total_pools": len(protocol_pools),
            "total_tvl_usd": total_tvl,
            "average_apy": round(avg_apy, 2),
            "pools": protocol_pools,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_tvl_rankings(category: Optional[str] = None, top_n: int = 25) -> Dict[str, Any]:
    """
    Get protocol TVL rankings
    category: Optional category filter (e.g., 'Lending', 'DEX')
    top_n: Number of top protocols to return (default 25)
    """
    try:
        url = f"{DEFILLAMA_BASE_URL}/protocols"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        protocols = response.json()
        
        # Filter by category if specified
        if category:
            protocols = [p for p in protocols if p.get('category', '').lower() == category.lower()]
        
        # Filter out protocols with None or 0 TVL
        protocols = [p for p in protocols if p.get('tvl') is not None and p.get('tvl', 0) > 0]
        
        # Sort by TVL
        protocols.sort(key=lambda x: x.get('tvl', 0), reverse=True)
        
        # Take top N
        top_protocols = []
        for i, p in enumerate(protocols[:top_n], 1):
            top_protocols.append({
                "rank": i,
                "name": p.get('name'),
                "slug": p.get('slug'),
                "category": p.get('category'),
                "tvl_usd": p.get('tvl', 0),
                "change_1d_pct": p.get('change_1d'),
                "change_7d_pct": p.get('change_7d'),
                "chains": p.get('chains', []),
                "mcap": p.get('mcap')
            })
        
        return {
            "category": category or "All Categories",
            "total_protocols": len(protocols),
            f"top_{top_n}_protocols": top_protocols,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_defi_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive DeFi dashboard with TVL and top yields
    Combines multiple data sources for overview
    """
    try:
        # Get global TVL
        global_tvl = get_global_tvl()
        
        # Get top protocols
        protocols_result = get_all_protocols()
        top_5_protocols = protocols_result.get('top_50_protocols', [])[:5] if 'error' not in protocols_result else []
        
        # Get top chains
        chains_result = get_chains_tvl()
        top_5_chains = chains_result.get('top_20_chains', [])[:5] if 'error' not in chains_result else []
        
        # Get top stablecoin yields
        stable_yields = get_stablecoin_yields(min_apy=1.0)
        top_5_stable = stable_yields.get('top_30_pools', [])[:5] if 'error' not in stable_yields else []
        
        # Get top overall yields
        all_yields = get_yield_pools(min_tvl=500000)
        top_5_yields = all_yields.get('top_50_pools', [])[:5] if 'error' not in all_yields else []
        
        return {
            "global_tvl_usd": global_tvl.get('current_tvl_usd', 0),
            "top_5_protocols": top_5_protocols,
            "top_5_chains": top_5_chains,
            "top_5_stablecoin_yields": top_5_stable,
            "top_5_all_yields": top_5_yields,
            "timestamp": datetime.now().isoformat(),
            "note": "Comprehensive DeFi overview - TVL and yield opportunities"
        }
    
    except Exception as e:
        return {"error": str(e)}


# CLI Commands
def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python defi_tvl_yield.py <command> [args]")
        print("\nCommands:")
        print("  global-tvl              - Get global DeFi TVL")
        print("  protocol <slug>         - Get TVL for specific protocol")
        print("  all-protocols           - List all protocols with TVL")
        print("  chain <name>            - Get TVL for specific chain")
        print("  chains                  - Get all chains TVL")
        print("  yields [chain]          - Get top yield opportunities")
        print("  stable-yields           - Get stablecoin yields")
        print("  protocol-yields <name>  - Get yields for specific protocol")
        print("  rankings [category]     - Get TVL rankings")
        print("  dashboard               - Get comprehensive DeFi overview")
        return
    
    command = sys.argv[1]
    
    if command == "global-tvl":
        result = get_global_tvl()
    elif command == "protocol" and len(sys.argv) > 2:
        result = get_protocol_tvl(sys.argv[2])
    elif command == "all-protocols":
        result = get_all_protocols()
    elif command == "chain" and len(sys.argv) > 2:
        result = get_chain_tvl(sys.argv[2])
    elif command == "chains":
        result = get_chains_tvl()
    elif command == "yields":
        chain = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_yield_pools(chain=chain)
    elif command == "stable-yields":
        result = get_stablecoin_yields()
    elif command == "protocol-yields" and len(sys.argv) > 2:
        result = get_protocol_yields(sys.argv[2])
    elif command == "rankings":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_tvl_rankings(category=category)
    elif command == "dashboard":
        result = get_defi_dashboard()
    else:
        result = {"error": "Unknown command or missing arguments"}
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
