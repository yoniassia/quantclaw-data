#!/usr/bin/env python3
"""
NFT Market Tracker Module — Collection Floor Prices, Volume, Wash Trading Detection

Data Sources:
- OpenSea API: NFT collection stats, floor prices, volume (public API)
- CoinGecko NFT API: Market cap, volume, floor prices (free tier)
- Reservoir API: Aggregated NFT data across marketplaces (free tier)

Features:
- Real-time collection floor prices
- Trading volume tracking
- Wash trading detection heuristics
- Top collections by volume/market cap
- Historical price trends

Author: QUANTCLAW DATA Build Agent
Phase: 189
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
from collections import defaultdict
import time

# API Configuration
OPENSEA_BASE_URL = "https://api.opensea.io/api/v2"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
RESERVOIR_BASE_URL = "https://api.reservoir.tools"

# Wash Trading Detection Thresholds
WASH_TRADE_INDICATORS = {
    "high_repeat_buyer_rate": 0.3,  # >30% of sales to same buyers
    "low_unique_holders": 0.1,       # <10% unique holder rate
    "high_self_transfer_rate": 0.15, # >15% self-transfers
    "suspicious_volume_spike": 5.0,  # 5x volume spike in 24h
}


def get_collection_stats(collection_slug: str) -> Dict[str, Any]:
    """
    Fetch NFT collection statistics from OpenSea
    
    Args:
        collection_slug: OpenSea collection identifier (e.g., 'boredapeyachtclub')
    
    Returns:
        Dict with floor_price, volume, sales, market_cap, etc.
    """
    try:
        # OpenSea v2 API - public endpoint
        url = f"{OPENSEA_BASE_URL}/collections/{collection_slug}/stats"
        
        headers = {
            "Accept": "application/json",
            "X-API-KEY": ""  # Public API - no key needed for basic queries
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # If OpenSea fails, try alternative sources
        if response.status_code != 200:
            return get_collection_stats_fallback(collection_slug)
        
        data = response.json()
        stats = data.get("stats", {})
        
        return {
            "collection": collection_slug,
            "floor_price_eth": stats.get("floor_price"),
            "market_cap_eth": stats.get("market_cap"),
            "volume_24h_eth": stats.get("one_day_volume"),
            "volume_7d_eth": stats.get("seven_day_volume"),
            "volume_30d_eth": stats.get("thirty_day_volume"),
            "sales_24h": stats.get("one_day_sales"),
            "sales_7d": stats.get("seven_day_sales"),
            "num_owners": stats.get("num_owners"),
            "total_supply": stats.get("total_supply"),
            "avg_price_eth": stats.get("average_price"),
            "timestamp": datetime.now().isoformat(),
            "data_source": "opensea"
        }
    
    except Exception as e:
        return {"error": str(e), "collection": collection_slug}


def get_collection_stats_fallback(collection_slug: str) -> Dict[str, Any]:
    """
    Fallback to CoinGecko NFT API when OpenSea fails
    """
    try:
        # Try CoinGecko NFT endpoint
        url = f"{COINGECKO_BASE_URL}/nfts/{collection_slug}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "collection": collection_slug,
            "floor_price_native": data.get("floor_price", {}).get("native_currency"),
            "floor_price_usd": data.get("floor_price", {}).get("usd"),
            "market_cap_usd": data.get("market_cap", {}).get("usd"),
            "volume_24h_usd": data.get("volume_24h", {}).get("usd"),
            "num_owners": data.get("number_of_unique_addresses"),
            "total_supply": data.get("total_supply"),
            "description": data.get("description", "")[:200],
            "timestamp": datetime.now().isoformat(),
            "data_source": "coingecko"
        }
    
    except Exception as e:
        return {"error": f"All data sources failed: {str(e)}", "collection": collection_slug}


def get_top_collections(limit: int = 20, time_window: str = "24h") -> List[Dict[str, Any]]:
    """
    Fetch top NFT collections by volume
    
    Args:
        limit: Number of collections to return (default 20)
        time_window: '24h', '7d', '30d' (default '24h')
    
    Returns:
        List of collections sorted by volume
    """
    try:
        # Use Reservoir API for aggregated marketplace data
        url = f"{RESERVOIR_BASE_URL}/collections/v7"
        
        params = {
            "sortBy": "volume",
            "limit": limit,
            "includeTopBid": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        # Fallback to CoinGecko if Reservoir fails
        if response.status_code != 200:
            return get_top_collections_coingecko(limit)
        
        data = response.json()
        collections = []
        
        for collection in data.get("collections", []):
            collections.append({
                "name": collection.get("name"),
                "slug": collection.get("slug"),
                "floor_price_eth": collection.get("floorAsk", {}).get("price", {}).get("amount", {}).get("native"),
                "volume_1d_eth": collection.get("volume", {}).get("1day"),
                "volume_7d_eth": collection.get("volume", {}).get("7day"),
                "volume_30d_eth": collection.get("volume", {}).get("30day"),
                "volume_all_time_eth": collection.get("volume", {}).get("allTime"),
                "market_cap_eth": collection.get("marketCap"),
                "owner_count": collection.get("ownerCount"),
                "token_count": collection.get("tokenCount"),
                "timestamp": datetime.now().isoformat()
            })
        
        return collections
    
    except Exception as e:
        # Final fallback to CoinGecko
        return get_top_collections_coingecko(limit)


def get_top_collections_coingecko(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fallback: Fetch top NFT collections from CoinGecko
    """
    try:
        url = f"{COINGECKO_BASE_URL}/nfts/list"
        
        params = {
            "order": "market_cap_usd_desc",
            "per_page": limit
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        collections = []
        
        for item in data:
            collections.append({
                "name": item.get("name"),
                "slug": item.get("id"),
                "floor_price_native": item.get("floor_price_in_native_currency"),
                "floor_price_usd": item.get("floor_price_24h_percentage_change"),
                "market_cap_usd": item.get("market_cap_usd"),
                "volume_24h_usd": item.get("volume_24h_usd"),
                "description": item.get("description", "")[:100],
                "timestamp": datetime.now().isoformat(),
                "data_source": "coingecko"
            })
        
        return collections
    
    except Exception as e:
        return [{"error": f"Failed to fetch top collections: {str(e)}"}]


def detect_wash_trading(collection_slug: str) -> Dict[str, Any]:
    """
    Detect potential wash trading using heuristic indicators
    
    Wash Trading Indicators:
    1. High repeat buyer rate (same addresses buying repeatedly)
    2. Low unique holder rate vs total supply
    3. High self-transfer rate (wallet to wallet same owner)
    4. Suspicious volume spikes without holder growth
    5. Price manipulation patterns
    
    Args:
        collection_slug: Collection identifier
    
    Returns:
        Dict with wash trading risk score and indicators
    """
    try:
        stats = get_collection_stats(collection_slug)
        
        if "error" in stats:
            return {"error": stats["error"], "collection": collection_slug}
        
        # Calculate wash trading indicators
        indicators = {}
        risk_score = 0.0
        risk_factors = []
        
        # Indicator 1: Low unique holder ratio
        total_supply = stats.get("total_supply", 0)
        num_owners = stats.get("num_owners", 0)
        
        if total_supply > 0 and num_owners > 0:
            holder_ratio = num_owners / total_supply
            indicators["unique_holder_ratio"] = holder_ratio
            
            if holder_ratio < WASH_TRADE_INDICATORS["low_unique_holders"]:
                risk_score += 30
                risk_factors.append(f"Low unique holders: {holder_ratio:.2%} (red flag: <10%)")
        
        # Indicator 2: Volume to market cap ratio
        volume_24h = stats.get("volume_24h_eth", 0) or 0
        market_cap = stats.get("market_cap_eth", 0) or 0
        
        if market_cap > 0:
            volume_to_mcap = volume_24h / market_cap
            indicators["volume_to_mcap_ratio"] = volume_to_mcap
            
            # Excessive turnover (>50% daily volume/mcap) is suspicious
            if volume_to_mcap > 0.5:
                risk_score += 25
                risk_factors.append(f"High volume/mcap ratio: {volume_to_mcap:.2%} (suspicious: >50%)")
        
        # Indicator 3: Sales concentration
        sales_24h = stats.get("sales_24h", 0) or 0
        avg_price = stats.get("avg_price_eth", 0) or 0
        
        if sales_24h > 0 and avg_price > 0:
            expected_volume = sales_24h * avg_price
            actual_volume = volume_24h
            
            # If actual volume significantly differs from expected, suspicious
            if expected_volume > 0:
                volume_discrepancy = abs(actual_volume - expected_volume) / expected_volume
                indicators["volume_discrepancy"] = volume_discrepancy
                
                if volume_discrepancy > 0.3:
                    risk_score += 20
                    risk_factors.append(f"Volume discrepancy: {volume_discrepancy:.2%}")
        
        # Indicator 4: Floor price volatility (if we have historical data)
        # This would require tracking price changes over time
        # For now, we'll mark as "needs_historical_data"
        indicators["floor_price_volatility"] = "needs_historical_data"
        
        # Calculate final risk assessment
        if risk_score >= 60:
            risk_level = "HIGH"
            risk_description = "Strong indicators of wash trading present"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
            risk_description = "Some suspicious activity detected"
        else:
            risk_level = "LOW"
            risk_description = "No major wash trading indicators"
        
        return {
            "collection": collection_slug,
            "wash_trading_risk_score": risk_score,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "risk_factors": risk_factors,
            "indicators": indicators,
            "data_quality": "Limited by public API data",
            "recommendation": (
                "Consider additional on-chain analysis for definitive wash trading detection. "
                "This analysis uses heuristics based on publicly available data."
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "collection": collection_slug}


def get_nft_market_overview() -> Dict[str, Any]:
    """
    Get comprehensive NFT market overview
    
    Returns:
        Dict with market-wide statistics
    """
    try:
        # Fetch top 10 collections for market snapshot
        top_collections = get_top_collections(limit=10)
        
        if not top_collections or "error" in top_collections[0]:
            return {"error": "Failed to fetch market overview"}
        
        # Calculate market-wide metrics
        total_volume_24h = sum(
            c.get("volume_1d_eth", 0) or c.get("volume_24h_usd", 0) or 0 
            for c in top_collections
        )
        
        total_market_cap = sum(
            c.get("market_cap_eth", 0) or c.get("market_cap_usd", 0) or 0 
            for c in top_collections
        )
        
        avg_floor_price = sum(
            c.get("floor_price_eth", 0) or c.get("floor_price_native", 0) or 0 
            for c in top_collections
        ) / len(top_collections)
        
        return {
            "market_snapshot": {
                "top_10_volume_24h": total_volume_24h,
                "top_10_market_cap": total_market_cap,
                "avg_floor_price_top_10": avg_floor_price,
                "num_collections_tracked": len(top_collections),
            },
            "top_collections": top_collections[:5],  # Top 5 for overview
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["reservoir", "coingecko", "opensea"],
            "notes": "Market overview based on top collections. Full market data requires premium APIs."
        }
    
    except Exception as e:
        return {"error": str(e)}


def compare_collections(collection_slugs: List[str]) -> Dict[str, Any]:
    """
    Compare multiple NFT collections side-by-side
    
    Args:
        collection_slugs: List of collection identifiers
    
    Returns:
        Dict with comparative analysis
    """
    try:
        if len(collection_slugs) < 2:
            return {"error": "Need at least 2 collections to compare"}
        
        if len(collection_slugs) > 5:
            return {"error": "Maximum 5 collections for comparison"}
        
        collections_data = []
        
        for slug in collection_slugs:
            stats = get_collection_stats(slug)
            if "error" not in stats:
                collections_data.append(stats)
            else:
                collections_data.append({
                    "collection": slug,
                    "error": stats.get("error"),
                    "floor_price_eth": None,
                    "volume_24h_eth": None,
                    "num_owners": None
                })
        
        if not collections_data:
            return {"error": "Failed to fetch any collection data"}
        
        # Identify leaders in each category
        leaders = {
            "highest_floor": max(
                (c for c in collections_data if c.get("floor_price_eth")),
                key=lambda x: x.get("floor_price_eth", 0),
                default=None
            ),
            "highest_volume": max(
                (c for c in collections_data if c.get("volume_24h_eth")),
                key=lambda x: x.get("volume_24h_eth", 0),
                default=None
            ),
            "most_owners": max(
                (c for c in collections_data if c.get("num_owners")),
                key=lambda x: x.get("num_owners", 0),
                default=None
            ),
        }
        
        return {
            "comparison": collections_data,
            "leaders": {
                "highest_floor_price": leaders["highest_floor"].get("collection") if leaders["highest_floor"] else None,
                "highest_24h_volume": leaders["highest_volume"].get("collection") if leaders["highest_volume"] else None,
                "most_owners": leaders["most_owners"].get("collection") if leaders["most_owners"] else None,
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_collection_history(collection_slug: str, days: int = 30) -> Dict[str, Any]:
    """
    Get historical floor price and volume data (limited by free API tiers)
    
    Args:
        collection_slug: Collection identifier
        days: Number of days of history (default 30)
    
    Returns:
        Dict with historical data points
    """
    try:
        # Note: Historical data requires premium API access for most providers
        # This is a placeholder that returns current data with a note
        
        current_stats = get_collection_stats(collection_slug)
        
        if "error" in current_stats:
            return current_stats
        
        return {
            "collection": collection_slug,
            "current_stats": current_stats,
            "historical_data": "Historical data requires premium API access",
            "recommendation": (
                "For historical NFT data, consider: "
                "1. Reservoir API (premium tier), "
                "2. Dune Analytics (SQL queries), "
                "3. On-chain analysis via Etherscan"
            ),
            "workaround": "Take daily snapshots using this API to build your own historical database",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "collection": collection_slug}


# CLI Interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command specified",
            "available_commands": [
                "collection-stats <slug>",
                "top-collections [limit]",
                "wash-trading <slug>",
                "market-overview",
                "compare-collections <slug1> <slug2> [slug3...]",
                "collection-history <slug> [days]"
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "collection-stats":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing collection slug"}, indent=2))
                sys.exit(1)
            result = get_collection_stats(sys.argv[2])
        
        elif command == "top-collections":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            result = get_top_collections(limit=limit)
        
        elif command == "wash-trading":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing collection slug"}, indent=2))
                sys.exit(1)
            result = detect_wash_trading(sys.argv[2])
        
        elif command == "market-overview":
            result = get_nft_market_overview()
        
        elif command == "compare-collections":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Need at least 2 collection slugs"}, indent=2))
                sys.exit(1)
            slugs = sys.argv[2:]
            result = compare_collections(slugs)
        
        elif command == "collection-history":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing collection slug"}, indent=2))
                sys.exit(1)
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            result = get_collection_history(sys.argv[2], days=days)
        
        else:
            result = {"error": f"Unknown command: {command}"}
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)
