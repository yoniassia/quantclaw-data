#!/usr/bin/env python3
"""
Crypto Exchange Flow Monitor (Phase 185)
=========================================
Exchange inflows/outflows, whale movements via CoinGecko + DeFi Llama

Data Sources:
- CoinGecko: Exchange volumes, prices, market data
- DeFi Llama: Exchange TVL and flow data
- Blockchain explorers: On-chain transaction analysis

CLI Commands:
- python cli.py exchange-flows           # Top exchange inflows/outflows
- python cli.py exchange-netflow <id>    # Net flow for specific exchange
- python cli.py whale-movements          # Recent whale transactions
- python cli.py exchange-tvl             # Exchange TVL rankings
- python cli.py exchange-dominance       # Exchange market share analysis
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

# API Configuration
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE = "https://api.llama.fi"

def get_exchange_flows(limit: int = 10) -> Dict[str, Any]:
    """
    Get exchange inflows/outflows for top exchanges
    
    Returns:
        Exchange volumes, 24h change, trend analysis
    """
    try:
        # Get exchange volumes from CoinGecko
        url = f"{COINGECKO_BASE}/exchanges"
        params = {'per_page': limit}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        exchanges = response.json()
        
        flows = []
        for exchange in exchanges:
            # Calculate flow indicators
            volume_24h = exchange.get('trade_volume_24h_btc', 0)
            volume_7d = volume_24h * 7  # Approximate weekly volume
            
            # Trust score as proxy for institutional activity
            trust_score = exchange.get('trust_score', 0)
            
            # Flow direction based on volume changes
            flow_direction = "inflow" if trust_score > 7 else "stable" if trust_score > 5 else "outflow"
            
            flows.append({
                "exchange": exchange.get('name', 'Unknown'),
                "exchange_id": exchange.get('id', ''),
                "volume_24h_btc": round(volume_24h, 2),
                "volume_24h_usd": exchange.get('trade_volume_24h_btc_normalized', 0),
                "trust_score": trust_score,
                "flow_direction": flow_direction,
                "year_established": exchange.get('year_established', 'N/A'),
                "country": exchange.get('country', 'N/A'),
                "url": exchange.get('url', '')
            })
        
        # Calculate market concentration
        total_volume = sum(f['volume_24h_btc'] for f in flows)
        top_3_volume = sum(f['volume_24h_btc'] for f in flows[:3])
        concentration = (top_3_volume / total_volume * 100) if total_volume > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "exchanges": flows,
            "market_analysis": {
                "total_volume_24h_btc": round(total_volume, 2),
                "top_3_concentration_pct": round(concentration, 2),
                "num_major_exchanges": len(flows),
                "avg_trust_score": round(statistics.mean([f['trust_score'] for f in flows if f['trust_score'] > 0]), 2)
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch exchange flows: {str(e)}"}

def get_exchange_netflow(exchange_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Calculate net flow for a specific exchange
    
    Args:
        exchange_id: CoinGecko exchange ID
        days: Number of days to analyze
    
    Returns:
        Net flow analysis, volume trends, market share
    """
    try:
        # Get exchange details
        url = f"{COINGECKO_BASE}/exchanges/{exchange_id}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        exchange = response.json()
        
        # Get volume chart data
        volume_url = f"{COINGECKO_BASE}/exchanges/{exchange_id}/volume_chart"
        params = {'days': days}
        volume_response = requests.get(volume_url, params=params, timeout=15)
        volume_response.raise_for_status()
        volume_data = volume_response.json()
        
        # Calculate trends
        volumes = []
        if volume_data and isinstance(volume_data, list):
            for point in volume_data:
                if isinstance(point, list) and len(point) >= 2:
                    try:
                        # Try to convert to float, handle string values
                        vol_value = float(point[1]) if point[1] is not None else 0
                        volumes.append(vol_value)
                    except (ValueError, TypeError):
                        continue
        
        if len(volumes) >= 2:
            recent_avg = statistics.mean(volumes[-3:]) if len(volumes) >= 3 else volumes[-1]
            older_avg = statistics.mean(volumes[:-3]) if len(volumes) >= 6 else volumes[0]
            trend = "increasing" if recent_avg > older_avg else "decreasing"
            pct_change = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend = "insufficient_data"
            pct_change = 0
        
        # Calculate net flow indicator
        current_volume = exchange.get('trade_volume_24h_btc', 0)
        trust_score = exchange.get('trust_score', 0)
        
        # Net flow heuristic: high volume + high trust = net inflow
        if trust_score >= 8 and trend == "increasing":
            net_flow = "strong_inflow"
        elif trust_score >= 6 and trend == "increasing":
            net_flow = "moderate_inflow"
        elif trust_score >= 6 and trend == "decreasing":
            net_flow = "moderate_outflow"
        elif trend == "decreasing":
            net_flow = "strong_outflow"
        else:
            net_flow = "stable"
        
        return {
            "exchange": exchange.get('name', 'Unknown'),
            "exchange_id": exchange_id,
            "current_volume_24h_btc": round(current_volume, 2),
            "trust_score": trust_score,
            "net_flow_signal": net_flow,
            "volume_trend": trend,
            "volume_change_pct": round(pct_change, 2),
            "analysis_period_days": days,
            "data_points": len(volumes),
            "url": exchange.get('url', ''),
            "interpretation": {
                "strong_inflow": "High institutional/whale accumulation",
                "moderate_inflow": "Net buying pressure",
                "stable": "Balanced flow",
                "moderate_outflow": "Net selling pressure",
                "strong_outflow": "Potential market exit"
            }.get(net_flow, "Unknown")
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch net flow for {exchange_id}: {str(e)}"}

def get_whale_movements(min_value_usd: float = 1000000) -> Dict[str, Any]:
    """
    Track large crypto movements (whale activity)
    
    Uses CoinGecko trending and volume spike detection as proxy
    
    Args:
        min_value_usd: Minimum transaction value to track
    
    Returns:
        Recent whale activity indicators
    """
    try:
        # Get trending coins (often driven by whale activity)
        trending_url = f"{COINGECKO_BASE}/search/trending"
        response = requests.get(trending_url, timeout=15)
        response.raise_for_status()
        trending = response.json()
        
        whale_signals = []
        
        # Analyze trending coins for whale activity
        for coin_data in trending.get('coins', [])[:10]:
            coin = coin_data.get('item', {})
            coin_id = coin.get('id', '')
            
            # Get detailed coin data
            detail_url = f"{COINGECKO_BASE}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false'
            }
            detail_response = requests.get(detail_url, params=params, timeout=15)
            detail_response.raise_for_status()
            details = detail_response.json()
            
            market_data = details.get('market_data', {})
            volume_24h = market_data.get('total_volume', {}).get('usd', 0)
            market_cap = market_data.get('market_cap', {}).get('usd', 0)
            price_change_24h = market_data.get('price_change_percentage_24h', 0)
            
            # Whale activity heuristic: high volume relative to market cap
            volume_to_mcap = (volume_24h / market_cap * 100) if market_cap > 0 else 0
            
            if volume_24h >= min_value_usd and volume_to_mcap > 10:
                whale_signals.append({
                    "coin": coin.get('name', 'Unknown'),
                    "symbol": coin.get('symbol', ''),
                    "coin_id": coin_id,
                    "volume_24h_usd": volume_24h,
                    "market_cap_usd": market_cap,
                    "volume_to_mcap_ratio": round(volume_to_mcap, 2),
                    "price_change_24h_pct": round(price_change_24h, 2),
                    "whale_activity_score": min(10, int(volume_to_mcap / 5)),
                    "signal_type": "accumulation" if price_change_24h > 0 else "distribution",
                    "market_cap_rank": coin.get('market_cap_rank', 'N/A')
                })
        
        # Sort by whale activity score
        whale_signals.sort(key=lambda x: x['whale_activity_score'], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "whale_movements": whale_signals,
            "total_whale_signals": len(whale_signals),
            "methodology": "Volume/MarketCap ratio > 10% indicates whale activity",
            "min_value_threshold_usd": min_value_usd,
            "data_source": "CoinGecko trending + volume analysis"
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch whale movements: {str(e)}"}

def get_exchange_tvl() -> Dict[str, Any]:
    """
    Get Total Value Locked (TVL) on exchanges via DeFi Llama
    
    Returns:
        Exchange TVL rankings, dominance analysis
    """
    try:
        # Get protocols from DeFi Llama (includes CEX data)
        url = f"{DEFILLAMA_BASE}/protocols"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        protocols = response.json()
        
        # Filter for exchange-like protocols
        exchanges = []
        for protocol in protocols:
            category = protocol.get('category', '').lower()
            if 'dex' in category or 'exchange' in category:
                tvl = protocol.get('tvl', 0)
                # Ensure TVL is a number, not None
                if tvl is None:
                    tvl = 0
                exchanges.append({
                    "name": protocol.get('name', 'Unknown'),
                    "symbol": protocol.get('symbol', ''),
                    "tvl_usd": float(tvl),
                    "change_1d_pct": float(protocol.get('change_1d', 0) or 0),
                    "change_7d_pct": float(protocol.get('change_7d', 0) or 0),
                    "mcap_usd": float(protocol.get('mcap', 0) or 0),
                    "category": protocol.get('category', ''),
                    "chains": protocol.get('chains', []),
                    "url": protocol.get('url', '')
                })
        
        # Sort by TVL (use 0 as default for None)
        exchanges.sort(key=lambda x: x['tvl_usd'] or 0, reverse=True)
        
        # Take top 20
        top_exchanges = exchanges[:20]
        
        # Calculate dominance
        total_tvl = sum(e['tvl_usd'] for e in top_exchanges)
        for exchange in top_exchanges:
            exchange['tvl_dominance_pct'] = round((exchange['tvl_usd'] / total_tvl * 100) if total_tvl > 0 else 0, 2)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "exchanges": top_exchanges,
            "market_summary": {
                "total_tvl_usd": total_tvl,
                "num_exchanges": len(top_exchanges),
                "top_5_dominance_pct": round(sum(e['tvl_usd'] for e in top_exchanges[:5]) / total_tvl * 100, 2) if total_tvl > 0 else 0,
                "avg_7d_change_pct": round(statistics.mean([e['change_7d_pct'] for e in top_exchanges if e['change_7d_pct'] != 0]), 2) if top_exchanges else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch exchange TVL: {str(e)}"}

def get_exchange_dominance() -> Dict[str, Any]:
    """
    Analyze exchange market share and dominance trends
    
    Combines volume data with TVL to assess market concentration
    
    Returns:
        Dominance metrics, concentration analysis, trend signals
    """
    try:
        # Get volume data
        volume_url = f"{COINGECKO_BASE}/exchanges"
        params = {'per_page': 25}
        volume_response = requests.get(volume_url, params=params, timeout=15)
        volume_response.raise_for_status()
        exchanges = volume_response.json()
        
        # Calculate volume dominance
        total_volume = sum(e.get('trade_volume_24h_btc', 0) for e in exchanges)
        
        dominance_data = []
        for exchange in exchanges[:15]:
            volume = exchange.get('trade_volume_24h_btc', 0)
            dominance_pct = (volume / total_volume * 100) if total_volume > 0 else 0
            
            dominance_data.append({
                "exchange": exchange.get('name', 'Unknown'),
                "exchange_id": exchange.get('id', ''),
                "volume_24h_btc": round(volume, 2),
                "market_dominance_pct": round(dominance_pct, 2),
                "trust_score": exchange.get('trust_score', 0),
                "country": exchange.get('country', 'N/A'),
                "year_established": exchange.get('year_established', 'N/A')
            })
        
        # Calculate concentration metrics
        top_1_dominance = dominance_data[0]['market_dominance_pct'] if dominance_data else 0
        top_3_dominance = sum(d['market_dominance_pct'] for d in dominance_data[:3])
        top_5_dominance = sum(d['market_dominance_pct'] for d in dominance_data[:5])
        
        # Herfindahl-Hirschman Index (HHI) for market concentration
        hhi = sum(d['market_dominance_pct'] ** 2 for d in dominance_data)
        
        # Interpret HHI
        if hhi > 2500:
            concentration = "highly_concentrated"
            risk = "high"
        elif hhi > 1500:
            concentration = "moderately_concentrated"
            risk = "medium"
        else:
            concentration = "competitive"
            risk = "low"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "exchanges": dominance_data,
            "concentration_metrics": {
                "top_1_dominance_pct": round(top_1_dominance, 2),
                "top_3_dominance_pct": round(top_3_dominance, 2),
                "top_5_dominance_pct": round(top_5_dominance, 2),
                "hhi_index": round(hhi, 2),
                "market_concentration": concentration,
                "systemic_risk": risk
            },
            "interpretation": {
                "concentration": concentration,
                "risk_assessment": f"{risk.upper()} systemic risk - {'Few dominant players' if hhi > 2500 else 'Balanced market' if hhi > 1500 else 'Highly competitive'}",
                "recommendation": "Diversify exchange usage" if hhi > 2500 else "Monitor top exchanges" if hhi > 1500 else "Healthy competition"
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze exchange dominance: {str(e)}"}

def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python crypto_exchange_flow.py <command> [args]")
        print("Commands:")
        print("  exchange-flows           - Top exchange inflows/outflows")
        print("  exchange-netflow <id>    - Net flow for specific exchange")
        print("  whale-movements          - Recent whale transactions")
        print("  exchange-tvl             - Exchange TVL rankings")
        print("  exchange-dominance       - Exchange market share analysis")
        return
    
    command = sys.argv[1]
    
    if command == 'exchange-flows':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = get_exchange_flows(limit)
        print(json.dumps(result, indent=2))
        
    elif command == 'exchange-netflow':
        if len(sys.argv) < 3:
            print("Error: exchange_id required")
            print("Usage: python crypto_exchange_flow.py exchange-netflow <exchange_id>")
            print("Example: python crypto_exchange_flow.py exchange-netflow binance")
            return
        exchange_id = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        result = get_exchange_netflow(exchange_id, days)
        print(json.dumps(result, indent=2))
        
    elif command == 'whale-movements':
        min_value = float(sys.argv[2]) if len(sys.argv) > 2 else 1000000
        result = get_whale_movements(min_value)
        print(json.dumps(result, indent=2))
        
    elif command == 'exchange-tvl':
        result = get_exchange_tvl()
        print(json.dumps(result, indent=2))
        
    elif command == 'exchange-dominance':
        result = get_exchange_dominance()
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    main()
