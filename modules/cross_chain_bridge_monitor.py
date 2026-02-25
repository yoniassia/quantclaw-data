#!/usr/bin/env python3
"""
Cross-Chain Bridge Monitor — Bridge TVL, Flow Direction, Exploit Risk Scoring

Data Sources:
- DeFi Llama Bridges API: Cross-chain bridge TVL, volume, transactions (free)
- DeFi Llama Chain TVL API: Chain-level liquidity metrics (free)

Author: QUANTCLAW DATA Build Agent
Phase: 190
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
from collections import defaultdict

# API Configuration
DEFILLAMA_BASE_URL = "https://api.llama.fi"
BRIDGES_API_URL = "https://bridges.llama.fi/bridges"

# Risk scoring thresholds
RISK_THRESHOLDS = {
    "tvl_drop_1d": -0.15,      # -15% TVL drop in 1 day = HIGH RISK
    "tvl_drop_7d": -0.30,      # -30% TVL drop in 7 days = HIGH RISK
    "volume_spike": 3.0,       # 3x normal volume = ELEVATED RISK
    "min_safe_tvl": 10_000_000, # $10M minimum TVL for LOW RISK
    "age_days_safe": 180,      # 6 months = mature bridge
}


def get_all_bridges() -> Dict[str, Any]:
    """
    Fetch all cross-chain bridges with current TVL and volume
    """
    try:
        url = BRIDGES_API_URL
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        bridges = data.get("bridges", [])
        
        # Calculate total volume across all bridges
        total_volume_24h = sum(b.get("last24hVolume", 0) for b in bridges)
        
        result = {
            "total_bridges": len(bridges),
            "total_volume_24h_usd": total_volume_24h,
            "bridges": sorted(
                [
                    {
                        "id": b.get("id"),
                        "name": b.get("displayName", b.get("name")),
                        "volume_24h_usd": b.get("last24hVolume", 0),
                        "volume_prev_day_usd": b.get("volumePrevDay", 0),
                        "volume_7d_usd": b.get("weeklyVolume", 0),
                        "volume_30d_usd": b.get("monthlyVolume", 0),
                        "chains": list(b.get("chains", [])),
                        "chain_count": len(b.get("chains", [])),
                    }
                    for b in bridges
                ],
                key=lambda x: x["volume_24h_usd"],
                reverse=True
            ),
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def get_bridge_details(bridge_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific bridge from the main bridges list
    """
    try:
        url = BRIDGES_API_URL
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        bridges = data.get("bridges", [])
        
        # Find the bridge by ID or name
        bridge = None
        for b in bridges:
            if str(b.get("id")) == str(bridge_id) or b.get("name", "").lower() == bridge_id.lower() or b.get("displayName", "").lower() == bridge_id.lower():
                bridge = b
                break
        
        if not bridge:
            return {"error": f"Bridge '{bridge_id}' not found"}
        
        result = {
            "id": bridge.get("id"),
            "name": bridge.get("displayName", bridge.get("name")),
            "volume_24h_usd": bridge.get("last24hVolume", 0),
            "volume_prev_day_usd": bridge.get("volumePrevDay", 0),
            "volume_7d_usd": bridge.get("weeklyVolume", 0),
            "volume_30d_usd": bridge.get("monthlyVolume", 0),
            "chains": bridge.get("chains", []),
            "chain_count": len(bridge.get("chains", [])),
            "url": bridge.get("url", ""),
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def get_bridge_volume(bridge_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Get volume data for a bridge (using available timeframes)
    """
    try:
        details = get_bridge_details(bridge_id)
        if "error" in details:
            return details
        
        # Use the volume data we have
        if days <= 1:
            volume = details.get("volume_24h_usd", 0)
            period = "24h"
        elif days <= 7:
            volume = details.get("volume_7d_usd", 0)
            period = "7d"
        else:
            volume = details.get("volume_30d_usd", 0)
            period = "30d"
        
        result = {
            "bridge_id": bridge_id,
            "bridge_name": details.get("name"),
            "period": period,
            "period_days": days,
            "total_volume_usd": volume,
            "avg_daily_volume_usd": volume / days if days > 0 else 0,
            "volume_24h_usd": details.get("volume_24h_usd", 0),
            "volume_prev_day_usd": details.get("volume_prev_day_usd", 0),
            "change_24h_pct": ((details.get("volume_24h_usd", 0) / details.get("volume_prev_day_usd", 1) - 1) * 100) if details.get("volume_prev_day_usd", 0) > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def calculate_bridge_risk_score(bridge_id: str) -> Dict[str, Any]:
    """
    Calculate comprehensive risk score for a bridge
    Factors: Volume patterns, chain diversity, activity trends
    
    Risk Levels:
    - LOW: Score 0-3
    - MEDIUM: Score 4-6
    - HIGH: Score 7-8
    - CRITICAL: Score 9-10
    """
    try:
        # Get bridge details and volume
        details = get_bridge_details(bridge_id)
        if "error" in details:
            return details
        
        volume_data = get_bridge_volume(bridge_id, 7)
        if "error" in volume_data:
            return volume_data
        
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Volume Size (low volume = less battle-tested)
        volume_24h = details.get("volume_24h_usd", 0)
        min_safe_volume = 1_000_000  # $1M/day
        
        if volume_24h < min_safe_volume * 0.1:
            risk_score += 3
            risk_factors.append(f"Very low volume (${volume_24h:,.0f}/day)")
        elif volume_24h < min_safe_volume:
            risk_score += 1
            risk_factors.append(f"Low volume (${volume_24h:,.0f}/day)")
        
        # Factor 2: Chain Concentration (single chain = higher risk)
        chain_count = len(details.get("chains", []))
        if chain_count < 2:
            risk_score += 3
            risk_factors.append(f"Single chain bridge (high concentration risk)")
        elif chain_count < 4:
            risk_score += 1
            risk_factors.append(f"Limited chain diversity ({chain_count} chains)")
        
        # Factor 3: Volume Decline (significant drop = potential issue)
        change_24h = volume_data.get("change_24h_pct", 0)
        
        if change_24h < -50:
            risk_score += 3
            risk_factors.append(f"Severe volume drop ({change_24h:.1f}%)")
        elif change_24h < -30:
            risk_score += 2
            risk_factors.append(f"Significant volume drop ({change_24h:.1f}%)")
        elif change_24h < -15:
            risk_score += 1
            risk_factors.append(f"Moderate volume decline ({change_24h:.1f}%)")
        
        # Factor 4: Activity Health
        if volume_24h == 0:
            risk_score += 4
            risk_factors.append(f"No recent activity (bridge may be inactive)")
        
        # Determine risk level
        if risk_score <= 3:
            risk_level = "LOW"
        elif risk_score <= 6:
            risk_level = "MEDIUM"
        elif risk_score <= 8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        result = {
            "bridge_id": bridge_id,
            "bridge_name": details.get("name"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "metrics": {
                "volume_24h_usd": volume_24h,
                "chain_count": chain_count,
                "volume_change_24h_pct": change_24h,
                "volume_7d_usd": details.get("volume_7d_usd", 0),
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def get_top_bridges(limit: int = 10, min_tvl: float = 1_000_000) -> Dict[str, Any]:
    """
    Get top bridges by volume with basic metrics
    """
    try:
        all_bridges = get_all_bridges()
        if "error" in all_bridges:
            return all_bridges
        
        # Filter by minimum volume (using volume as proxy for TVL since TVL not available in free API)
        top_bridges = [
            b for b in all_bridges["bridges"]
            if b["volume_24h_usd"] >= (min_tvl / 10)  # Scale threshold for volume
        ][:limit]
        
        result = {
            "total_bridges": all_bridges["total_bridges"],
            "total_volume_24h_usd": all_bridges["total_volume_24h_usd"],
            "top_bridges": top_bridges,
            "filters": {
                "min_volume_24h_usd": min_tvl / 10,
                "limit": limit,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def get_flow_analysis(bridge_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Analyze cross-chain flow patterns and trends
    """
    try:
        volume_data = get_bridge_volume(bridge_id, days)
        if "error" in volume_data:
            return volume_data
        
        details = get_bridge_details(bridge_id)
        if "error" in details:
            return details
        
        # Analyze volume trend
        volume_24h = details.get("volume_24h_usd", 0)
        volume_prev = details.get("volume_prev_day_usd", 1)
        volume_change = ((volume_24h / volume_prev) - 1) * 100 if volume_prev > 0 else 0
        
        # Classify flow health based on volume stability
        if abs(volume_change) < 10:
            flow_health = "STABLE"
        elif abs(volume_change) < 30:
            flow_health = "MODERATE_VOLATILITY"
        elif volume_change > 30:
            flow_health = "HIGH_GROWTH"
        else:
            flow_health = "HIGH_DECLINE"
        
        result = {
            "bridge_id": bridge_id,
            "bridge_name": details.get("name"),
            "period_days": days,
            "flow_metrics": {
                "volume_24h_usd": volume_24h,
                "volume_prev_day_usd": volume_prev,
                "volume_change_pct": round(volume_change, 2),
                "volume_7d_usd": details.get("volume_7d_usd", 0),
                "volume_30d_usd": details.get("volume_30d_usd", 0),
                "avg_daily_volume": volume_data.get("avg_daily_volume_usd", 0),
            },
            "flow_health": flow_health,
            "chains_supported": details.get("chains", []),
            "chain_count": details.get("chain_count", 0),
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def get_comprehensive_bridge_report(bridge_id: str) -> Dict[str, Any]:
    """
    Generate comprehensive bridge analysis report
    """
    try:
        details = get_bridge_details(bridge_id)
        if "error" in details:
            return details
        
        volume_7d = get_bridge_volume(bridge_id, 7)
        volume_30d = get_bridge_volume(bridge_id, 30)
        risk = calculate_bridge_risk_score(bridge_id)
        flow = get_flow_analysis(bridge_id, 30)
        
        result = {
            "bridge_id": bridge_id,
            "bridge_name": details.get("name"),
            "overview": {
                "url": details.get("url", ""),
                "chains_supported": details.get("chains", []),
                "chain_count": len(details.get("chains", [])),
            },
            "volume_24h": {
                "volume_usd": details.get("volume_24h_usd", 0),
                "prev_day_usd": details.get("volume_prev_day_usd", 0),
                "change_pct": volume_7d.get("change_24h_pct", 0),
            },
            "volume_7d": {
                "total_usd": volume_7d.get("total_volume_usd", 0),
                "avg_daily_usd": volume_7d.get("avg_daily_volume_usd", 0),
            },
            "volume_30d": {
                "total_usd": volume_30d.get("total_volume_usd", 0),
                "avg_daily_usd": volume_30d.get("avg_daily_volume_usd", 0),
            },
            "risk_assessment": {
                "score": risk.get("risk_score", 0),
                "level": risk.get("risk_level", "UNKNOWN"),
                "factors": risk.get("risk_factors", []),
            },
            "flow_health": flow.get("flow_health", "UNKNOWN"),
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing command",
            "usage": "cross_chain_bridge_monitor.py <command> [args]",
            "commands": [
                "bridge-list [limit] [min_tvl]",
                "bridge-details <bridge_id>",
                "bridge-volume <bridge_id> [days]",
                "bridge-risk <bridge_id>",
                "bridge-flow <bridge_id> [days]",
                "bridge-report <bridge_id>",
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "bridge-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
        min_tvl = float(sys.argv[3]) if len(sys.argv) > 3 else 1_000_000
        result = get_top_bridges(limit, min_tvl)
    
    elif command == "bridge-details":
        if len(sys.argv) < 3:
            result = {"error": "Missing bridge_id"}
        else:
            bridge_id = sys.argv[2]
            result = get_bridge_details(bridge_id)
    
    elif command == "bridge-volume":
        if len(sys.argv) < 3:
            result = {"error": "Missing bridge_id"}
        else:
            bridge_id = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 7
            result = get_bridge_volume(bridge_id, days)
    
    elif command == "bridge-risk":
        if len(sys.argv) < 3:
            result = {"error": "Missing bridge_id"}
        else:
            bridge_id = sys.argv[2]
            result = calculate_bridge_risk_score(bridge_id)
    
    elif command == "bridge-flow":
        if len(sys.argv) < 3:
            result = {"error": "Missing bridge_id"}
        else:
            bridge_id = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 30
            result = get_flow_analysis(bridge_id, days)
    
    elif command == "bridge-report":
        if len(sys.argv) < 3:
            result = {"error": "Missing bridge_id"}
        else:
            bridge_id = sys.argv[2]
            result = get_comprehensive_bridge_report(bridge_id)
    
    else:
        result = {"error": f"Unknown command: {command}"}
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
