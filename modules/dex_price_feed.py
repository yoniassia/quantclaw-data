"""
DEX Aggregator Price Feed — Multi-DEX token price aggregation.

Fetches real-time token prices from decentralized exchanges (Uniswap, SushiSwap,
Curve, Balancer) via free public APIs (DeFi Llama, CoinGecko).
Compares prices across venues to identify arbitrage opportunities.

Roadmap item #302.
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple


def get_dex_token_prices(token_addresses: List[str], chain: str = "ethereum") -> Dict[str, Dict]:
    """
    Fetch token prices across multiple DEXs via DeFi Llama.

    Args:
        token_addresses: List of token contract addresses
        chain: Blockchain network (ethereum, polygon, arbitrum, base, optimism)

    Returns:
        Dict mapping address to price data with confidence and sources
    """
    results = {}
    coins = ",".join(f"{chain}:{addr}" for addr in token_addresses)
    url = f"https://coins.llama.fi/prices/current/{coins}?searchWidth=4h"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        for key, info in data.get("coins", {}).items():
            addr = key.split(":")[1] if ":" in key else key
            results[addr] = {
                "price_usd": info.get("price", 0),
                "symbol": info.get("symbol", "UNKNOWN"),
                "timestamp": info.get("timestamp", 0),
                "confidence": info.get("confidence", 0),
                "decimals": info.get("decimals", 18),
            }
    except Exception as e:
        results["error"] = str(e)

    return results


def find_dex_arbitrage(token_id: str = "ethereum", threshold_pct: float = 0.5) -> List[Dict]:
    """
    Find price discrepancies across DEXs for arbitrage opportunities.

    Uses CoinGecko tickers to compare prices across decentralized exchanges.

    Args:
        token_id: CoinGecko token ID
        threshold_pct: Minimum price difference percentage to flag

    Returns:
        List of arbitrage opportunities with buy/sell venues and spread
    """
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/tickers?include_exchange_logo=false"
    opportunities = []

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        dex_tickers = [
            t for t in data.get("tickers", [])
            if t.get("market", {}).get("identifier", "") in (
                "uniswap_v3", "uniswap_v2", "sushiswap", "curve",
                "balancer_v2", "pancakeswap_new", "trader_joe"
            )
        ]

        if len(dex_tickers) < 2:
            return opportunities

        for i, buy in enumerate(dex_tickers):
            for sell in dex_tickers[i + 1:]:
                buy_price = buy.get("converted_last", {}).get("usd", 0)
                sell_price = sell.get("converted_last", {}).get("usd", 0)
                if buy_price <= 0 or sell_price <= 0:
                    continue

                spread_pct = abs(sell_price - buy_price) / min(buy_price, sell_price) * 100
                if spread_pct >= threshold_pct:
                    low, high = (buy, sell) if buy_price < sell_price else (sell, buy)
                    opportunities.append({
                        "token": token_id,
                        "buy_venue": low["market"]["name"],
                        "buy_price": low["converted_last"]["usd"],
                        "sell_venue": high["market"]["name"],
                        "sell_price": high["converted_last"]["usd"],
                        "spread_pct": round(spread_pct, 3),
                        "pair": f"{buy.get('base', '')}/{buy.get('target', '')}",
                    })

        opportunities.sort(key=lambda x: x["spread_pct"], reverse=True)
    except Exception as e:
        opportunities.append({"error": str(e)})

    return opportunities


def get_pool_liquidity(protocol: str = "uniswap", chain: str = "ethereum", limit: int = 20) -> List[Dict]:
    """
    Get top liquidity pools for a DEX protocol via DeFi Llama.

    Args:
        protocol: DEX protocol name
        chain: Blockchain network
        limit: Max pools to return

    Returns:
        List of pools with TVL, APY, and token composition
    """
    url = "https://yields.llama.fi/pools"
    pools = []

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        for pool in data.get("data", []):
            if (pool.get("project", "").lower() == protocol.lower() and
                    pool.get("chain", "").lower() == chain.lower()):
                pools.append({
                    "pool_id": pool.get("pool", ""),
                    "symbol": pool.get("symbol", ""),
                    "tvl_usd": pool.get("tvlUsd", 0),
                    "apy_base": pool.get("apyBase", 0),
                    "apy_reward": pool.get("apyReward", 0),
                    "apy_total": pool.get("apy", 0),
                    "volume_1d_usd": pool.get("volumeUsd1d", 0),
                    "volume_7d_usd": pool.get("volumeUsd7d", 0),
                    "il_risk": pool.get("ilRisk", "unknown"),
                })
                if len(pools) >= limit:
                    break

        pools.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
    except Exception as e:
        pools.append({"error": str(e)})

    return pools
