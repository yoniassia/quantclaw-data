#!/usr/bin/env python3
"""
Stablecoin Supply Monitor — USDT/USDC/DAI supply, mint/burn events via DeFi Llama

Data Sources:
- DeFi Llama Stablecoins API: Total supply, circulating amounts, mint/burn events (free)
- Tracks USDT, USDC, DAI, and other major stablecoins across multiple chains

Endpoints:
- https://stablecoins.llama.fi/stablecoins — All stablecoins metadata
- https://stablecoins.llama.fi/stablecoin/{id} — Individual stablecoin data with history
- https://stablecoins.llama.fi/stablecoincharts/all — Historical supply data
- https://stablecoins.llama.fi/stablecoincharts/{chain} — Chain-specific data

Author: QUANTCLAW DATA Build Agent
Phase: 187
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys

# API Configuration
DEFILLAMA_STABLECOINS_BASE = "https://stablecoins.llama.fi"

# Major stablecoins to track
MAJOR_STABLECOINS = {
    "1": {"name": "USDT", "symbol": "USDT", "gecko_id": "tether"},
    "2": {"name": "USDC", "symbol": "USDC", "gecko_id": "usd-coin"},
    "3": {"name": "DAI", "symbol": "DAI", "gecko_id": "dai"},
    "4": {"name": "BUSD", "symbol": "BUSD", "gecko_id": "binance-usd"},
    "5": {"name": "FRAX", "symbol": "FRAX", "gecko_id": "frax"},
}


def get_all_stablecoins() -> Dict[str, Any]:
    """
    Fetch all stablecoins metadata from DeFi Llama
    Returns list of all tracked stablecoins with current supply
    """
    try:
        url = f"{DEFILLAMA_STABLECOINS_BASE}/stablecoins?includePrices=true"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract key metrics
        stablecoins = data.get("peggedAssets", [])
        
        # Sort by circulating supply
        stablecoins_sorted = sorted(
            stablecoins,
            key=lambda x: x.get("circulating", {}).get("peggedUSD", 0),
            reverse=True
        )
        
        # Calculate totals
        total_supply = sum(
            s.get("circulating", {}).get("peggedUSD", 0) 
            for s in stablecoins
        )
        
        return {
            "total_market_cap_usd": total_supply,
            "stablecoin_count": len(stablecoins),
            "top_10": [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "symbol": s.get("symbol"),
                    "circulating_usd": s.get("circulating", {}).get("peggedUSD", 0),
                    "price": s.get("price"),
                    "chains": list(s.get("chainCirculating", {}).keys()),
                    "change_7d": s.get("circulatingPrevWeek", {}).get("peggedUSD"),
                }
                for s in stablecoins_sorted[:10]
            ],
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_stablecoin_detail(stablecoin_id: str) -> Dict[str, Any]:
    """
    Get detailed data for a specific stablecoin including historical supply
    stablecoin_id: ID from DeFi Llama (e.g., "1" for USDT)
    """
    try:
        url = f"{DEFILLAMA_STABLECOINS_BASE}/stablecoin/{stablecoin_id}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract current state
        current = {
            "id": data.get("id"),
            "name": data.get("name"),
            "symbol": data.get("symbol"),
            "price": data.get("price"),
            "circulating_usd": data.get("circulating", {}).get("peggedUSD", 0),
            "chains": list(data.get("chainCirculating", {}).keys()) if data.get("chainCirculating") else [],
        }
        
        # Get chain breakdown
        chain_breakdown = []
        if data.get("chainCirculating"):
            for chain, amounts in data.get("chainCirculating", {}).items():
                chain_breakdown.append({
                    "chain": chain,
                    "circulating_usd": amounts.get("current", {}).get("peggedUSD", 0),
                })
        
        chain_breakdown_sorted = sorted(
            chain_breakdown,
            key=lambda x: x["circulating_usd"],
            reverse=True
        )
        
        # Parse historical data for mint/burn analysis
        historical = data.get("tokens", [])
        recent_changes = []
        
        if historical and len(historical) >= 2:
            # Compare last 7 days
            for i in range(min(7, len(historical) - 1)):
                today = historical[-(i+1)]
                yesterday = historical[-(i+2)]
                
                date_val = today.get("date")
                today_supply = today.get("totalCirculating", {}).get("peggedUSD", 0)
                yesterday_supply = yesterday.get("totalCirculating", {}).get("peggedUSD", 0)
                
                change = today_supply - yesterday_supply
                change_pct = (change / yesterday_supply * 100) if yesterday_supply > 0 else 0
                
                recent_changes.append({
                    "date": datetime.fromtimestamp(date_val).strftime("%Y-%m-%d") if date_val else "unknown",
                    "supply_usd": today_supply,
                    "change_usd": change,
                    "change_pct": round(change_pct, 4),
                    "event_type": "mint" if change > 0 else "burn" if change < 0 else "stable",
                })
        
        return {
            "current": current,
            "chain_breakdown": chain_breakdown_sorted[:10],
            "recent_activity": recent_changes[:7],
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_chain_stablecoins(chain: str = "Ethereum") -> Dict[str, Any]:
    """
    Get all stablecoins on a specific chain
    chain: "Ethereum", "BSC", "Polygon", "Arbitrum", etc.
    """
    try:
        url = f"{DEFILLAMA_STABLECOINS_BASE}/stablecoincharts/{chain}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return {"error": f"No data found for chain: {chain}"}
        
        # Get latest datapoint
        latest = data[-1] if data else {}
        
        stablecoins_on_chain = []
        total_supply = 0
        
        for key, value in latest.items():
            if key == "date":
                continue
            
            if isinstance(value, (int, float)) and value > 0:
                stablecoins_on_chain.append({
                    "name": key,
                    "supply_usd": value,
                })
                total_supply += value
        
        stablecoins_sorted = sorted(
            stablecoins_on_chain,
            key=lambda x: x["supply_usd"],
            reverse=True
        )
        
        return {
            "chain": chain,
            "total_supply_usd": total_supply,
            "stablecoin_count": len(stablecoins_on_chain),
            "stablecoins": stablecoins_sorted[:20],
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def analyze_mint_burn_events(stablecoin_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Analyze mint and burn events over a specified period
    Returns aggregated statistics on supply changes
    """
    try:
        url = f"{DEFILLAMA_STABLECOINS_BASE}/stablecoin/{stablecoin_id}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        historical = data.get("tokens", [])
        
        if not historical or len(historical) < 2:
            return {"error": "Insufficient historical data"}
        
        # Analyze last N days
        recent_data = historical[-days:] if len(historical) >= days else historical
        
        mint_events = []
        burn_events = []
        total_minted = 0
        total_burned = 0
        
        for i in range(1, len(recent_data)):
            prev = recent_data[i-1]
            curr = recent_data[i]
            
            prev_supply = prev.get("totalCirculating", {}).get("peggedUSD", 0)
            curr_supply = curr.get("totalCirculating", {}).get("peggedUSD", 0)
            
            change = curr_supply - prev_supply
            
            if change > 0:
                mint_events.append({
                    "date": datetime.fromtimestamp(curr.get("date")).strftime("%Y-%m-%d") if curr.get("date") else "unknown",
                    "amount_usd": change,
                })
                total_minted += change
            elif change < 0:
                burn_events.append({
                    "date": datetime.fromtimestamp(curr.get("date")).strftime("%Y-%m-%d") if curr.get("date") else "unknown",
                    "amount_usd": abs(change),
                })
                total_burned += abs(change)
        
        return {
            "stablecoin": data.get("name"),
            "symbol": data.get("symbol"),
            "analysis_period_days": days,
            "mint_events": len(mint_events),
            "burn_events": len(burn_events),
            "total_minted_usd": total_minted,
            "total_burned_usd": total_burned,
            "net_change_usd": total_minted - total_burned,
            "recent_mints": mint_events[-5:] if mint_events else [],
            "recent_burns": burn_events[-5:] if burn_events else [],
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_stablecoin_dominance() -> Dict[str, Any]:
    """
    Calculate market dominance for top stablecoins
    Returns percentage breakdown of stablecoin market
    """
    try:
        all_data = get_all_stablecoins()
        
        if "error" in all_data:
            return all_data
        
        total_market = all_data.get("total_market_cap_usd", 0)
        top_stablecoins = all_data.get("top_10", [])
        
        dominance = []
        for coin in top_stablecoins:
            supply = coin.get("circulating_usd", 0)
            dominance_pct = (supply / total_market * 100) if total_market > 0 else 0
            
            dominance.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "supply_usd": supply,
                "dominance_pct": round(dominance_pct, 2),
            })
        
        return {
            "total_market_usd": total_market,
            "dominance": dominance,
            "top_3_dominance_pct": sum(d["dominance_pct"] for d in dominance[:3]),
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}


def main():
    """CLI interface for stablecoin supply monitoring"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing command",
            "usage": "stablecoin_supply.py <command> [args]",
            "commands": {
                "stablecoin-all": "List all stablecoins",
                "stablecoin-detail <id>": "Get detailed data for specific stablecoin (e.g., 1 for USDT)",
                "stablecoin-chain <name>": "Get stablecoins on specific chain (e.g., Ethereum)",
                "stablecoin-mint-burn <id> [days]": "Analyze mint/burn events (default: 30 days)",
                "stablecoin-dominance": "Calculate market dominance",
            }
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    result = {}
    
    if command == "stablecoin-all":
        result = get_all_stablecoins()
    
    elif command == "stablecoin-detail":
        if len(sys.argv) < 3:
            result = {"error": "Missing stablecoin ID"}
        else:
            stablecoin_id = sys.argv[2]
            result = get_stablecoin_detail(stablecoin_id)
    
    elif command == "stablecoin-chain":
        if len(sys.argv) < 3:
            result = {"error": "Missing chain name"}
        else:
            chain = sys.argv[2]
            result = get_chain_stablecoins(chain)
    
    elif command == "stablecoin-mint-burn":
        if len(sys.argv) < 3:
            result = {"error": "Missing stablecoin ID"}
        else:
            stablecoin_id = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            result = analyze_mint_burn_events(stablecoin_id, days)
    
    elif command == "stablecoin-dominance":
        result = get_stablecoin_dominance()
    
    else:
        result = {"error": f"Unknown command: {command}"}
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
