"""
DefiLlama API — DeFi Protocol TVL, Yields & Chain Stats

Data Source: DefiLlama (defillama.com)
Update: Real-time (5-minute refresh)
History: Multi-year TVL history for protocols and chains
Free: Yes (no API key required)

Provides:
- Total DeFi TVL across all chains
- Per-protocol TVL and metadata (7000+ protocols)
- Per-chain TVL breakdown (400+ chains)
- Historical TVL data (global + per-protocol + per-chain)
- Yield/APY data for DeFi pools (19000+ pools)
- Stablecoin market data
- DEX volume data

Usage:
    from modules.defillama_api import *
    protocols = get_protocols()
    tvl = get_global_tvl()
    yields = get_top_yields(min_tvl=1_000_000, limit=20)
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

BASE_URL = "https://api.llama.fi"
YIELDS_URL = "https://yields.llama.fi"
STABLECOINS_URL = "https://stablecoins.llama.fi"
COINS_URL = "https://coins.llama.fi"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "QuantClaw-Data/1.0",
    "Accept": "application/json",
})

DEFAULT_TIMEOUT = 15


def _get(url: str, params: Optional[Dict] = None, timeout: int = DEFAULT_TIMEOUT) -> Any:
    """Internal helper for GET requests with error handling."""
    try:
        resp = _SESSION.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "url": url}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}", "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "url": url}
    except ValueError:
        return {"error": "Invalid JSON response", "url": url}


# ── Global TVL ──────────────────────────────────────────────────────────────

def get_global_tvl() -> Dict:
    """
    Get current total DeFi TVL across all chains.

    Returns:
        dict with 'tvl' (float), 'formatted' (str), 'timestamp' (str)
    """
    data = _get(f"{BASE_URL}/v2/historicalChainTvl")
    if isinstance(data, dict) and "error" in data:
        return data
    if not data:
        return {"error": "No data returned"}
    latest = data[-1]
    tvl = latest.get("tvl", 0)
    return {
        "tvl": tvl,
        "formatted": f"${tvl / 1e9:.2f}B",
        "date": datetime.utcfromtimestamp(latest["date"]).strftime("%Y-%m-%d"),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_global_tvl_history(days: Optional[int] = None) -> List[Dict]:
    """
    Get historical total DeFi TVL.

    Args:
        days: Limit to last N days (None = all history)

    Returns:
        List of {'date': 'YYYY-MM-DD', 'tvl': float}
    """
    data = _get(f"{BASE_URL}/v2/historicalChainTvl")
    if isinstance(data, dict) and "error" in data:
        return [data]
    result = [
        {
            "date": datetime.utcfromtimestamp(d["date"]).strftime("%Y-%m-%d"),
            "tvl": d["tvl"],
        }
        for d in data
    ]
    if days:
        result = result[-days:]
    return result


# ── Protocols ───────────────────────────────────────────────────────────────

def get_protocols() -> List[Dict]:
    """
    Get all DeFi protocols with TVL, category, chains, and metadata.

    Returns:
        List of protocol dicts (7000+), sorted by TVL descending.
    """
    data = _get(f"{BASE_URL}/protocols", timeout=30)
    if isinstance(data, dict) and "error" in data:
        return [data]
    # Sort by TVL descending
    data.sort(key=lambda x: x.get("tvl") or 0, reverse=True)
    return data


def get_top_protocols(limit: int = 25, category: Optional[str] = None) -> List[Dict]:
    """
    Get top DeFi protocols by TVL with clean output.

    Args:
        limit: Number of protocols to return
        category: Filter by category (e.g. 'Liquid Staking', 'DEX', 'Lending', 'Bridge', 'CDP')

    Returns:
        List of dicts with name, tvl, category, chains, change_1d/7d/30d
    """
    protocols = get_protocols()
    if protocols and isinstance(protocols[0], dict) and "error" in protocols[0]:
        return protocols

    if category:
        protocols = [p for p in protocols if (p.get("category") or "").lower() == category.lower()]

    results = []
    for p in protocols[:limit]:
        tvl = p.get("tvl") or 0
        results.append({
            "name": p.get("name"),
            "symbol": p.get("symbol"),
            "tvl": tvl,
            "tvl_formatted": f"${tvl / 1e9:.2f}B" if tvl >= 1e9 else f"${tvl / 1e6:.1f}M",
            "category": p.get("category"),
            "chains": p.get("chains", []),
            "chain_count": len(p.get("chains", [])),
            "change_1d": p.get("change_1d"),
            "change_7d": p.get("change_7d"),
            "change_1m": p.get("change_1m"),
        })
    return results


def get_protocol(slug: str) -> Dict:
    """
    Get detailed data for a specific protocol.

    Args:
        slug: Protocol slug (e.g. 'aave', 'lido', 'uniswap')

    Returns:
        Dict with TVL history, chain breakdown, token info, etc.
    """
    return _get(f"{BASE_URL}/protocol/{slug}")


def search_protocols(query: str, limit: int = 10) -> List[Dict]:
    """
    Search protocols by name (case-insensitive).

    Args:
        query: Search term
        limit: Max results

    Returns:
        Matching protocols sorted by TVL
    """
    protocols = get_protocols()
    if protocols and isinstance(protocols[0], dict) and "error" in protocols[0]:
        return protocols
    q = query.lower()
    matches = [p for p in protocols if q in (p.get("name") or "").lower()]
    return [
        {
            "name": p.get("name"),
            "slug": p.get("slug"),
            "tvl": p.get("tvl"),
            "category": p.get("category"),
            "chains": p.get("chains", []),
        }
        for p in matches[:limit]
    ]


# ── Chains ──────────────────────────────────────────────────────────────────

def get_chains() -> List[Dict]:
    """
    Get all chains with their current TVL.

    Returns:
        List of chain dicts sorted by TVL descending.
    """
    data = _get(f"{BASE_URL}/v2/chains")
    if isinstance(data, dict) and "error" in data:
        return [data]
    data.sort(key=lambda x: x.get("tvl") or 0, reverse=True)
    return data


def get_top_chains(limit: int = 20) -> List[Dict]:
    """
    Get top blockchains by DeFi TVL.

    Args:
        limit: Number of chains to return

    Returns:
        List of dicts with name, tvl, tokenSymbol
    """
    chains = get_chains()
    if chains and isinstance(chains[0], dict) and "error" in chains[0]:
        return chains
    results = []
    for c in chains[:limit]:
        tvl = c.get("tvl") or 0
        results.append({
            "name": c.get("name"),
            "tvl": tvl,
            "tvl_formatted": f"${tvl / 1e9:.2f}B" if tvl >= 1e9 else f"${tvl / 1e6:.1f}M",
            "token": c.get("tokenSymbol"),
            "gecko_id": c.get("gecko_id"),
        })
    return results


def get_chain_tvl_history(chain: str) -> List[Dict]:
    """
    Get historical TVL for a specific chain.

    Args:
        chain: Chain name (e.g. 'Ethereum', 'Solana', 'BSC')

    Returns:
        List of {'date': str, 'tvl': float}
    """
    data = _get(f"{BASE_URL}/v2/historicalChainTvl/{chain}")
    if isinstance(data, dict) and "error" in data:
        return [data]
    return [
        {
            "date": datetime.utcfromtimestamp(d["date"]).strftime("%Y-%m-%d"),
            "tvl": d.get("tvl", 0),
        }
        for d in data
    ]


# ── Yields / Pools ─────────────────────────────────────────────────────────

def get_pools() -> List[Dict]:
    """
    Get all yield pools (19000+).

    Returns:
        List of pool dicts with APY, TVL, chain, project info.
    """
    data = _get(f"{YIELDS_URL}/pools", timeout=30)
    if isinstance(data, dict) and "error" in data:
        return [data]
    return data.get("data", [])


def get_top_yields(
    min_tvl: float = 1_000_000,
    chain: Optional[str] = None,
    stablecoin_only: bool = False,
    limit: int = 25,
) -> List[Dict]:
    """
    Get top DeFi yields filtered by criteria.

    Args:
        min_tvl: Minimum pool TVL in USD (default $1M)
        chain: Filter by chain (e.g. 'Ethereum', 'Solana')
        stablecoin_only: Only show stablecoin pools
        limit: Max results

    Returns:
        List of pools sorted by APY descending
    """
    pools = get_pools()
    if pools and isinstance(pools[0], dict) and "error" in pools[0]:
        return pools

    filtered = [p for p in pools if (p.get("tvlUsd") or 0) >= min_tvl]

    if chain:
        filtered = [p for p in filtered if (p.get("chain") or "").lower() == chain.lower()]

    if stablecoin_only:
        filtered = [p for p in filtered if p.get("stablecoin")]

    filtered.sort(key=lambda x: x.get("apy") or 0, reverse=True)

    results = []
    for p in filtered[:limit]:
        tvl = p.get("tvlUsd") or 0
        results.append({
            "pool": p.get("pool"),
            "project": p.get("project"),
            "symbol": p.get("symbol"),
            "chain": p.get("chain"),
            "apy": round(p.get("apy") or 0, 2),
            "apy_base": round(p.get("apyBase") or 0, 2),
            "apy_reward": round(p.get("apyReward") or 0, 2) if p.get("apyReward") else None,
            "tvl": tvl,
            "tvl_formatted": f"${tvl / 1e6:.1f}M" if tvl < 1e9 else f"${tvl / 1e9:.2f}B",
            "stablecoin": p.get("stablecoin"),
            "il_risk": p.get("ilRisk"),
            "prediction": p.get("predictions", {}).get("predictedClass") if p.get("predictions") else None,
        })
    return results


def get_pool_history(pool_id: str) -> List[Dict]:
    """
    Get historical APY/TVL for a specific pool.

    Args:
        pool_id: Pool UUID (from get_pools() or get_top_yields())

    Returns:
        List of historical data points
    """
    data = _get(f"{YIELDS_URL}/chart/{pool_id}")
    if isinstance(data, dict) and "error" in data:
        return [data]
    return data.get("data", [])


# ── Stablecoins ─────────────────────────────────────────────────────────────

def get_stablecoins() -> List[Dict]:
    """
    Get all stablecoins with market cap and chain distribution.

    Returns:
        List of stablecoin dicts sorted by market cap.
    """
    data = _get(f"{STABLECOINS_URL}/stablecoins?includePrices=true")
    if isinstance(data, dict) and "error" in data:
        return [data]
    coins = data.get("peggedAssets", [])
    coins.sort(key=lambda x: (x.get("circulating", {}).get("peggedUSD") or 0), reverse=True)
    return coins


def get_top_stablecoins(limit: int = 15) -> List[Dict]:
    """
    Get top stablecoins by circulating supply.

    Args:
        limit: Number to return

    Returns:
        List of dicts with name, symbol, circulating, peg type
    """
    coins = get_stablecoins()
    if coins and isinstance(coins[0], dict) and "error" in coins[0]:
        return coins
    results = []
    for c in coins[:limit]:
        circ = c.get("circulating", {}).get("peggedUSD") or 0
        results.append({
            "name": c.get("name"),
            "symbol": c.get("symbol"),
            "circulating": circ,
            "circulating_formatted": f"${circ / 1e9:.2f}B",
            "peg_type": c.get("pegType"),
            "peg_mechanism": c.get("pegMechanism"),
            "chains": c.get("chains", []),
            "price": c.get("price"),
        })
    return results


# ── DEX Volumes ─────────────────────────────────────────────────────────────

def get_dex_volumes() -> Dict:
    """
    Get DEX trading volumes (24h).

    Returns:
        Dict with total volume and per-protocol breakdown.
    """
    return _get(f"{BASE_URL}/../overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true",
                timeout=20)


def get_dex_volume_summary() -> Dict:
    """
    Get a clean summary of DEX volumes.

    Returns:
        Dict with total_24h, top protocols by volume.
    """
    # Use the correct DeFiLlama API endpoint for DEX overview
    data = _get("https://api.llama.fi/overview/dexs", timeout=20)
    if isinstance(data, dict) and "error" in data:
        return data
    total = data.get("totalDataChart", [])
    protocols = data.get("protocols", [])
    protocols.sort(key=lambda x: (x.get("total24h") or 0), reverse=True)
    top = []
    for p in protocols[:10]:
        vol = p.get("total24h") or 0
        top.append({
            "name": p.get("name"),
            "volume_24h": vol,
            "volume_formatted": f"${vol / 1e6:.1f}M" if vol < 1e9 else f"${vol / 1e9:.2f}B",
            "change_1d": p.get("change_1d"),
        })
    return {
        "total_24h": data.get("total24h"),
        "total_24h_formatted": f"${(data.get('total24h') or 0) / 1e9:.2f}B",
        "top_dexes": top,
    }


# ── Fees & Revenue ──────────────────────────────────────────────────────────

def get_fees_overview() -> Dict:
    """
    Get protocol fees and revenue overview (24h).

    Returns:
        Dict with total fees/revenue and per-protocol breakdown.
    """
    data = _get("https://api.llama.fi/overview/fees", timeout=20)
    if isinstance(data, dict) and "error" in data:
        return data
    protocols = data.get("protocols", [])
    protocols.sort(key=lambda x: (x.get("total24h") or 0), reverse=True)
    top = []
    for p in protocols[:10]:
        fees = p.get("total24h") or 0
        top.append({
            "name": p.get("name"),
            "fees_24h": fees,
            "fees_formatted": f"${fees / 1e6:.1f}M" if fees < 1e9 else f"${fees / 1e9:.2f}B",
            "revenue_24h": p.get("totalRevenue24h"),
        })
    return {
        "total_fees_24h": data.get("total24h"),
        "total_fees_formatted": f"${(data.get('total24h') or 0) / 1e6:.1f}M",
        "top_protocols": top,
    }


# ── Utility ─────────────────────────────────────────────────────────────────

def get_protocol_categories() -> List[str]:
    """
    Get all unique protocol categories.

    Returns:
        Sorted list of category strings.
    """
    protocols = get_protocols()
    if protocols and isinstance(protocols[0], dict) and "error" in protocols[0]:
        return []
    cats = set(p.get("category") for p in protocols if p.get("category"))
    return sorted(cats)


def defi_dashboard() -> Dict:
    """
    Quick DeFi market overview — TVL, top chains, top protocols, top yields.

    Returns:
        Dict with global_tvl, top_chains, top_protocols, top_yields
    """
    return {
        "global_tvl": get_global_tvl(),
        "top_chains": get_top_chains(limit=10),
        "top_protocols": get_top_protocols(limit=10),
        "top_yields": get_top_yields(min_tvl=10_000_000, limit=10),
    }
