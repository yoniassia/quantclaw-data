"""Liquid Staking Tracker — monitors liquid staking protocols and derivatives.

Tracks TVL, exchange rates, yields, and market share across Lido (stETH),
Rocket Pool (rETH), Coinbase (cbETH), Frax (sfrxETH), and other LST protocols.
Uses DeFiLlama and protocol APIs for free data.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# Protocol metadata
LST_PROTOCOLS = {
    "lido": {
        "name": "Lido",
        "token": "stETH",
        "chain": "ethereum",
        "llama_slug": "lido",
        "type": "pooled",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "medium",
        "api": "https://eth-api.lido.fi/v1/protocol/steth/apr/sma",
    },
    "rocket_pool": {
        "name": "Rocket Pool",
        "token": "rETH",
        "chain": "ethereum",
        "llama_slug": "rocket-pool",
        "type": "decentralized",
        "min_stake": 0,
        "fee_pct": 14.0,
        "decentralization": "high",
    },
    "coinbase": {
        "name": "Coinbase Wrapped Staked ETH",
        "token": "cbETH",
        "chain": "ethereum",
        "llama_slug": "coinbase-wrapped-staked-eth",
        "type": "centralized",
        "min_stake": 0,
        "fee_pct": 25.0,
        "decentralization": "low",
    },
    "frax": {
        "name": "Frax Ether",
        "token": "sfrxETH",
        "chain": "ethereum",
        "llama_slug": "frax-ether",
        "type": "dual_token",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "medium",
    },
    "mantle": {
        "name": "Mantle Staked ETH",
        "token": "mETH",
        "chain": "ethereum",
        "llama_slug": "mantle-staked-eth",
        "type": "pooled",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "low",
    },
    "swell": {
        "name": "Swell",
        "token": "swETH",
        "chain": "ethereum",
        "llama_slug": "swell",
        "type": "pooled",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "medium",
    },
    "stakewise": {
        "name": "StakeWise",
        "token": "osETH",
        "chain": "ethereum",
        "llama_slug": "stakewise",
        "type": "decentralized",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "high",
    },
    "eigenlayer": {
        "name": "EigenLayer (Restaking)",
        "token": "eETH (various)",
        "chain": "ethereum",
        "llama_slug": "eigenlayer",
        "type": "restaking",
        "min_stake": 0,
        "fee_pct": 10.0,
        "decentralization": "medium",
    },
}


def _fetch_json(url: str, timeout: int = 10) -> Any:
    """Fetch JSON from URL with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_lst_tvl_overview() -> Dict[str, Any]:
    """Get TVL overview for all liquid staking protocols.
    
    Returns:
        TVL data, market shares, and rankings.
    """
    # Fetch from DeFiLlama
    data = _fetch_json("https://api.llama.fi/protocols")
    if "error" in data if isinstance(data, dict) else False:
        return data
    
    results = {}
    total_lst_tvl = 0
    
    for protocol in data if isinstance(data, list) else []:
        slug = protocol.get("slug", "")
        for key, meta in LST_PROTOCOLS.items():
            if meta["llama_slug"] == slug:
                tvl = protocol.get("tvl", 0)
                results[key] = {
                    "name": meta["name"],
                    "token": meta["token"],
                    "tvl_usd": tvl,
                    "type": meta["type"],
                    "fee_pct": meta["fee_pct"],
                    "decentralization": meta["decentralization"],
                    "change_1d": protocol.get("change_1d", 0),
                    "change_7d": protocol.get("change_7d", 0),
                }
                total_lst_tvl += tvl
                break
    
    # Calculate market shares
    for key in results:
        if total_lst_tvl > 0:
            results[key]["market_share_pct"] = round(results[key]["tvl_usd"] / total_lst_tvl * 100, 2)
    
    # Sort by TVL
    ranked = sorted(results.items(), key=lambda x: x[1].get("tvl_usd", 0), reverse=True)
    
    return {
        "protocols": dict(ranked),
        "total_lst_tvl": total_lst_tvl,
        "protocol_count": len(results),
        "leader": ranked[0][1]["name"] if ranked else None,
        "leader_share": ranked[0][1].get("market_share_pct", 0) if ranked else 0,
        "hhi_concentration": round(sum(v.get("market_share_pct", 0) ** 2 for v in results.values()), 1),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_staking_yields() -> Dict[str, Any]:
    """Get current staking APR/APY for all LST protocols.
    
    Returns:
        Yield comparison across protocols.
    """
    # Try Lido API for reference rate
    lido_apr = None
    lido_data = _fetch_json("https://eth-api.lido.fi/v1/protocol/steth/apr/sma")
    if isinstance(lido_data, dict) and "data" in lido_data:
        lido_apr = lido_data.get("data", {}).get("smaApr")
    
    # DeFiLlama yields
    yields_data = _fetch_json("https://yields.llama.fi/pools")
    
    lst_yields = {}
    target_pools = {
        "stETH": "lido",
        "rETH": "rocket_pool",
        "cbETH": "coinbase",
        "sfrxETH": "frax",
        "mETH": "mantle",
        "swETH": "swell",
    }
    
    if isinstance(yields_data, dict) and "data" in yields_data:
        for pool in yields_data["data"]:
            symbol = pool.get("symbol", "")
            for token, key in target_pools.items():
                if token.upper() in symbol.upper() and pool.get("chain", "") == "Ethereum":
                    if key not in lst_yields or pool.get("tvlUsd", 0) > lst_yields[key].get("tvl", 0):
                        lst_yields[key] = {
                            "name": LST_PROTOCOLS[key]["name"],
                            "token": token,
                            "apy": pool.get("apy", 0),
                            "apy_base": pool.get("apyBase", 0),
                            "apy_reward": pool.get("apyReward", 0),
                            "tvl": pool.get("tvlUsd", 0),
                        }
    
    if lido_apr and "lido" in lst_yields:
        lst_yields["lido"]["protocol_apr"] = lido_apr
    
    # Sort by yield
    ranked = sorted(lst_yields.items(), key=lambda x: x[1].get("apy", 0), reverse=True)
    
    return {
        "yields": dict(ranked),
        "highest_yield": ranked[0][1] if ranked else None,
        "eth_base_staking_apr": lido_apr or 3.5,
        "protocols_with_data": len(lst_yields),
        "timestamp": datetime.utcnow().isoformat(),
    }


def analyze_lst_risks() -> Dict[str, Any]:
    """Analyze risks across liquid staking protocols.
    
    Returns:
        Risk assessment for each protocol.
    """
    risk_factors = {}
    
    for key, meta in LST_PROTOCOLS.items():
        risks = []
        score = 0
        
        # Centralization risk
        if meta["decentralization"] == "low":
            risks.append("High centralization risk — single entity controls validators")
            score += 30
        elif meta["decentralization"] == "medium":
            risks.append("Moderate centralization — limited validator set")
            score += 15
        
        # Fee risk
        if meta["fee_pct"] >= 20:
            risks.append(f"High fees ({meta['fee_pct']}%) reduce staker yield")
            score += 15
        elif meta["fee_pct"] >= 10:
            score += 5
        
        # Smart contract risk (newer = higher risk)
        if meta["type"] == "restaking":
            risks.append("Restaking introduces additional smart contract layers")
            score += 25
        
        # Depeg risk
        if meta["type"] in ["pooled", "centralized"]:
            risks.append("Potential depeg risk during market stress")
            score += 10
        
        risk_level = "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW"
        
        risk_factors[key] = {
            "name": meta["name"],
            "token": meta["token"],
            "risk_score": score,
            "risk_level": risk_level,
            "risks": risks,
            "decentralization": meta["decentralization"],
            "fee_pct": meta["fee_pct"],
            "type": meta["type"],
        }
    
    ranked = sorted(risk_factors.items(), key=lambda x: x[1]["risk_score"])
    
    return {
        "risk_assessments": dict(ranked),
        "safest": ranked[0][1]["name"] if ranked else None,
        "riskiest": ranked[-1][1]["name"] if ranked else None,
        "timestamp": datetime.utcnow().isoformat(),
    }


def lst_market_concentration() -> Dict[str, Any]:
    """Analyze market concentration and decentralization metrics.
    
    Returns:
        Concentration metrics including HHI and dominance ratios.
    """
    overview = get_lst_tvl_overview()
    if "error" in overview:
        return overview
    
    protocols = overview.get("protocols", {})
    shares = [v.get("market_share_pct", 0) for v in protocols.values()]
    
    if not shares:
        return {"error": "No TVL data available"}
    
    hhi = sum(s ** 2 for s in shares)
    top1 = max(shares) if shares else 0
    top3 = sum(sorted(shares, reverse=True)[:3])
    
    if hhi > 2500:
        concentration = "HIGHLY_CONCENTRATED"
    elif hhi > 1500:
        concentration = "MODERATELY_CONCENTRATED"
    else:
        concentration = "COMPETITIVE"
    
    return {
        "hhi_index": round(hhi, 1),
        "concentration_level": concentration,
        "top1_dominance": round(top1, 1),
        "top3_dominance": round(top3, 1),
        "protocol_count": len(shares),
        "decentralized_share": round(sum(
            v.get("market_share_pct", 0) for v in protocols.values()
            if v.get("decentralization") == "high"
        ), 1),
        "timestamp": datetime.utcnow().isoformat(),
    }
