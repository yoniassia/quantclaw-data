#!/usr/bin/env python3
"""
FlowTrack API — ETF Inflow/Outflow Tracking Module

Tracks daily ETF flows (inflows/outflows) across major ETFs using Yahoo Finance
price/volume data and estimated flow calculations. Provides sector-level aggregates
and market-wide flow summaries.

Data Sources:
- Yahoo Finance (price, volume, shares outstanding)
- Calculated flow estimates from volume patterns
- ETF sector classification

Update Frequency: Daily (market close)
Coverage: Major US ETFs (SPY, QQQ, IWM, DIA, etc.)
Free: Yes (no API key required)

Author: NightBuilder
Phase: NightOps
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from bs4 import BeautifulSoup

# Major ETF universe with sector classification
ETF_UNIVERSE = {
    # Broad Market
    'SPY': {'name': 'SPDR S&P 500', 'sector': 'broad_market', 'aum_b': 450},
    'VOO': {'name': 'Vanguard S&P 500', 'sector': 'broad_market', 'aum_b': 380},
    'IVV': {'name': 'iShares S&P 500', 'sector': 'broad_market', 'aum_b': 370},
    'QQQ': {'name': 'Invesco QQQ', 'sector': 'technology', 'aum_b': 220},
    'IWM': {'name': 'iShares Russell 2000', 'sector': 'small_cap', 'aum_b': 60},
    'DIA': {'name': 'SPDR Dow Jones', 'sector': 'broad_market', 'aum_b': 32},
    'VTI': {'name': 'Vanguard Total Stock', 'sector': 'broad_market', 'aum_b': 340},
    
    # Sector ETFs
    'XLK': {'name': 'Technology Select', 'sector': 'technology', 'aum_b': 55},
    'XLF': {'name': 'Financial Select', 'sector': 'financials', 'aum_b': 42},
    'XLE': {'name': 'Energy Select', 'sector': 'energy', 'aum_b': 35},
    'XLV': {'name': 'Healthcare Select', 'sector': 'healthcare', 'aum_b': 38},
    'XLY': {'name': 'Consumer Disc Select', 'sector': 'consumer', 'aum_b': 20},
    'XLP': {'name': 'Consumer Staples', 'sector': 'consumer', 'aum_b': 16},
    'XLI': {'name': 'Industrial Select', 'sector': 'industrials', 'aum_b': 18},
    'XLU': {'name': 'Utilities Select', 'sector': 'utilities', 'aum_b': 15},
    'XLB': {'name': 'Materials Select', 'sector': 'materials', 'aum_b': 6},
    'XLRE': {'name': 'Real Estate Select', 'sector': 'real_estate', 'aum_b': 6},
    
    # Bond ETFs
    'AGG': {'name': 'Core US Aggregate', 'sector': 'bonds', 'aum_b': 95},
    'BND': {'name': 'Vanguard Total Bond', 'sector': 'bonds', 'aum_b': 90},
    'TLT': {'name': '20+ Year Treasury', 'sector': 'bonds', 'aum_b': 45},
    'LQD': {'name': 'Investment Grade Corp', 'sector': 'bonds', 'aum_b': 35},
    
    # International
    'EFA': {'name': 'MSCI EAFE', 'sector': 'international', 'aum_b': 68},
    'VEA': {'name': 'Vanguard FTSE Dev', 'sector': 'international', 'aum_b': 120},
    'EEM': {'name': 'MSCI Emerging Markets', 'sector': 'international', 'aum_b': 22},
    'VWO': {'name': 'Vanguard FTSE EM', 'sector': 'international', 'aum_b': 85},
    
    # Gold & Commodities
    'GLD': {'name': 'SPDR Gold', 'sector': 'commodities', 'aum_b': 58},
    'SLV': {'name': 'iShares Silver', 'sector': 'commodities', 'aum_b': 12},
    'USO': {'name': 'US Oil Fund', 'sector': 'commodities', 'aum_b': 1.5},
}

SECTOR_MAP = {
    'broad_market': ['SPY', 'VOO', 'IVV', 'DIA', 'VTI'],
    'technology': ['QQQ', 'XLK'],
    'financials': ['XLF'],
    'energy': ['XLE'],
    'healthcare': ['XLV'],
    'consumer': ['XLY', 'XLP'],
    'industrials': ['XLI'],
    'utilities': ['XLU'],
    'materials': ['XLB'],
    'real_estate': ['XLRE'],
    'small_cap': ['IWM'],
    'bonds': ['AGG', 'BND', 'TLT', 'LQD'],
    'international': ['EFA', 'VEA', 'EEM', 'VWO'],
    'commodities': ['GLD', 'SLV', 'USO'],
}


def get_yahoo_quote(symbol: str) -> Dict:
    """
    Fetch current quote data from Yahoo Finance
    Returns price, volume, market cap
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        'interval': '1d',
        'range': '5d'
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        result = data.get('chart', {}).get('result', [])
        
        if not result:
            return {'error': 'No data available'}
        
        meta = result[0].get('meta', {})
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        timestamps = result[0].get('timestamp', [])
        
        # Get latest values
        volumes = quotes.get('volume', [])
        closes = quotes.get('close', [])
        
        if not volumes or not closes:
            return {'error': 'Incomplete data'}
        
        # Filter out None values and get last valid data
        valid_data = [(v, c) for v, c in zip(volumes, closes) if v is not None and c is not None]
        
        if not valid_data:
            return {'error': 'No valid data points'}
        
        latest_volume = valid_data[-1][0]
        latest_close = valid_data[-1][1]
        avg_volume = sum(v for v, _ in valid_data) / len(valid_data)
        
        return {
            'symbol': symbol,
            'price': latest_close,
            'volume': latest_volume,
            'avg_volume_5d': avg_volume,
            'currency': meta.get('currency', 'USD'),
            'exchange': meta.get('exchangeName', 'Unknown'),
            'timestamp': datetime.fromtimestamp(timestamps[-1]).strftime('%Y-%m-%d') if timestamps else None
        }
        
    except Exception as e:
        return {
            'error': True,
            'message': f"Yahoo Finance request failed: {str(e)}",
            'symbol': symbol
        }


def estimate_etf_flow(symbol: str, volume: float, avg_volume: float, price: float) -> float:
    """
    Estimate net flow based on volume deviation from average
    
    Logic:
    - Volume > avg → likely inflow
    - Volume < avg → likely outflow
    - Flow magnitude proportional to (volume - avg) * price
    
    Returns: Estimated flow in millions USD
    """
    volume_delta = volume - avg_volume
    flow_usd = (volume_delta * price) / 1_000_000  # Convert to millions
    
    return round(flow_usd, 2)


def get_etf_flows(symbol: str, period: str = '1m') -> Dict:
    """
    Get ETF inflow/outflow data for a specific symbol
    
    Args:
        symbol: ETF ticker (e.g., 'SPY', 'QQQ')
        period: Time period ('1d', '1w', '1m', '3m', '1y')
    
    Returns:
        Dict with flow data, volume trends, and estimates
    """
    symbol = symbol.upper()
    
    # Get current quote data
    quote = get_yahoo_quote(symbol)
    
    if 'error' in quote:
        return {
            'symbol': symbol,
            'error': quote.get('message', 'Failed to fetch data'),
            'period': period
        }
    
    # Calculate estimated flow
    flow = estimate_etf_flow(
        symbol,
        quote['volume'],
        quote['avg_volume_5d'],
        quote['price']
    )
    
    etf_info = ETF_UNIVERSE.get(symbol, {'name': symbol, 'sector': 'unknown', 'aum_b': 0})
    
    result = {
        'symbol': symbol,
        'name': etf_info['name'],
        'sector': etf_info['sector'],
        'period': period,
        'date': quote.get('timestamp', datetime.now().strftime('%Y-%m-%d')),
        'price': round(quote['price'], 2),
        'volume': quote['volume'],
        'avg_volume': round(quote['avg_volume_5d']),
        'volume_ratio': round(quote['volume'] / quote['avg_volume_5d'], 2),
        'estimated_flow_usd_m': flow,
        'flow_direction': 'INFLOW' if flow > 0 else 'OUTFLOW' if flow < 0 else 'NEUTRAL',
        'aum_billions': etf_info['aum_b'],
        'source': 'Yahoo Finance + Flow Estimate',
        'note': 'Flow estimated from volume deviation (volume - 5d avg) * price'
    }
    
    return result


def get_sector_flows(sector: str = 'technology', period: str = '1m') -> Dict:
    """
    Get aggregated flows for an entire sector
    
    Args:
        sector: Sector name (technology, financials, energy, etc.)
        period: Time period
    
    Returns:
        Dict with sector-level flow aggregates
    """
    sector = sector.lower().replace(' ', '_')
    
    if sector not in SECTOR_MAP:
        available = ', '.join(SECTOR_MAP.keys())
        return {
            'error': f'Unknown sector: {sector}',
            'available_sectors': list(SECTOR_MAP.keys())
        }
    
    sector_etfs = SECTOR_MAP[sector]
    flows = []
    total_inflow = 0
    total_outflow = 0
    
    for symbol in sector_etfs:
        etf_flow = get_etf_flows(symbol, period)
        
        if 'error' not in etf_flow:
            flows.append(etf_flow)
            flow_amt = etf_flow['estimated_flow_usd_m']
            
            if flow_amt > 0:
                total_inflow += flow_amt
            else:
                total_outflow += abs(flow_amt)
    
    net_flow = total_inflow - total_outflow
    
    return {
        'sector': sector,
        'period': period,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'etf_count': len(flows),
        'total_inflow_usd_m': round(total_inflow, 2),
        'total_outflow_usd_m': round(total_outflow, 2),
        'net_flow_usd_m': round(net_flow, 2),
        'flow_direction': 'INFLOW' if net_flow > 0 else 'OUTFLOW' if net_flow < 0 else 'NEUTRAL',
        'etfs': flows,
        'source': 'Yahoo Finance + Flow Estimates'
    }


def get_top_inflows(limit: int = 10, period: str = '1m') -> Dict:
    """
    Get top ETFs by inflows
    
    Args:
        limit: Number of top ETFs to return
        period: Time period
    
    Returns:
        Dict with ranked list of ETFs by inflow amount
    """
    all_flows = []
    
    for symbol in ETF_UNIVERSE.keys():
        etf_flow = get_etf_flows(symbol, period)
        
        if 'error' not in etf_flow and etf_flow['estimated_flow_usd_m'] > 0:
            all_flows.append(etf_flow)
        
        # Rate limiting
        time.sleep(0.1)
    
    # Sort by flow amount descending
    all_flows.sort(key=lambda x: x['estimated_flow_usd_m'], reverse=True)
    top_flows = all_flows[:limit]
    
    total_inflow = sum(f['estimated_flow_usd_m'] for f in top_flows)
    
    return {
        'period': period,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'top_count': len(top_flows),
        'total_inflow_usd_m': round(total_inflow, 2),
        'top_inflows': top_flows,
        'source': 'Yahoo Finance + Flow Estimates'
    }


def get_top_outflows(limit: int = 10, period: str = '1m') -> Dict:
    """
    Get top ETFs by outflows
    
    Args:
        limit: Number of top ETFs to return
        period: Time period
    
    Returns:
        Dict with ranked list of ETFs by outflow amount
    """
    all_flows = []
    
    for symbol in ETF_UNIVERSE.keys():
        etf_flow = get_etf_flows(symbol, period)
        
        if 'error' not in etf_flow and etf_flow['estimated_flow_usd_m'] < 0:
            all_flows.append(etf_flow)
        
        # Rate limiting
        time.sleep(0.1)
    
    # Sort by flow amount ascending (most negative first)
    all_flows.sort(key=lambda x: x['estimated_flow_usd_m'])
    top_flows = all_flows[:limit]
    
    total_outflow = sum(abs(f['estimated_flow_usd_m']) for f in top_flows)
    
    return {
        'period': period,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'top_count': len(top_flows),
        'total_outflow_usd_m': round(total_outflow, 2),
        'top_outflows': top_flows,
        'source': 'Yahoo Finance + Flow Estimates'
    }


def get_flow_summary(period: str = '1m') -> Dict:
    """
    Get market-wide flow summary across all tracked ETFs
    
    Args:
        period: Time period
    
    Returns:
        Dict with aggregate flow statistics and sector breakdown
    """
    sector_summaries = {}
    total_inflow = 0
    total_outflow = 0
    etf_count = 0
    
    for sector in SECTOR_MAP.keys():
        sector_data = get_sector_flows(sector, period)
        
        if 'error' not in sector_data:
            sector_summaries[sector] = {
                'net_flow_usd_m': sector_data['net_flow_usd_m'],
                'inflow_usd_m': sector_data['total_inflow_usd_m'],
                'outflow_usd_m': sector_data['total_outflow_usd_m'],
                'direction': sector_data['flow_direction'],
                'etf_count': sector_data['etf_count']
            }
            
            total_inflow += sector_data['total_inflow_usd_m']
            total_outflow += sector_data['total_outflow_usd_m']
            etf_count += sector_data['etf_count']
    
    net_flow = total_inflow - total_outflow
    
    # Rank sectors by net flow
    sector_rankings = sorted(
        sector_summaries.items(),
        key=lambda x: x[1]['net_flow_usd_m'],
        reverse=True
    )
    
    return {
        'period': period,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_etfs_tracked': etf_count,
        'total_inflow_usd_m': round(total_inflow, 2),
        'total_outflow_usd_m': round(total_outflow, 2),
        'net_flow_usd_m': round(net_flow, 2),
        'market_sentiment': 'RISK_ON' if net_flow > 0 else 'RISK_OFF' if net_flow < 0 else 'NEUTRAL',
        'sector_breakdown': dict(sector_summaries),
        'top_sectors_inflow': [
            {'sector': s[0], 'net_flow': s[1]['net_flow_usd_m']}
            for s in sector_rankings[:5]
        ],
        'source': 'Yahoo Finance + Flow Estimates',
        'methodology': 'Flows estimated from volume deviation (current vs 5-day avg) * price'
    }


# === CLI Commands ===

def cmd_flows(args):
    """CLI: Get ETF flows for a symbol"""
    if not args:
        print("Usage: flowtrack_api.py flows <SYMBOL> [period]")
        print("Example: flowtrack_api.py flows SPY 1m")
        return
    
    symbol = args[0]
    period = args[1] if len(args) > 1 else '1m'
    
    data = get_etf_flows(symbol, period)
    print(json.dumps(data, indent=2))


def cmd_sector(args):
    """CLI: Get sector flows"""
    if not args:
        print("Available sectors:", ', '.join(SECTOR_MAP.keys()))
        return
    
    sector = args[0]
    period = args[1] if len(args) > 1 else '1m'
    
    data = get_sector_flows(sector, period)
    print(json.dumps(data, indent=2))


def cmd_top_inflows(args):
    """CLI: Get top inflows"""
    limit = int(args[0]) if args else 10
    data = get_top_inflows(limit)
    print(json.dumps(data, indent=2))


def cmd_top_outflows(args):
    """CLI: Get top outflows"""
    limit = int(args[0]) if args else 10
    data = get_top_outflows(limit)
    print(json.dumps(data, indent=2))


def cmd_summary(args):
    """CLI: Get market-wide flow summary"""
    period = args[0] if args else '1m'
    data = get_flow_summary(period)
    print(json.dumps(data, indent=2))


def cmd_list(args):
    """CLI: List all tracked ETFs"""
    print(json.dumps({
        'tracked_etfs': len(ETF_UNIVERSE),
        'sectors': list(SECTOR_MAP.keys()),
        'etfs': ETF_UNIVERSE
    }, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("FlowTrack API - ETF Flow Tracking")
        print("\nUsage: flowtrack_api.py <command> [args]")
        print("\nCommands:")
        print("  flows <SYMBOL> [period]  - Get ETF flows")
        print("  sector <name> [period]   - Get sector flows")
        print("  top-inflows [limit]      - Top ETFs by inflows")
        print("  top-outflows [limit]     - Top ETFs by outflows")
        print("  summary [period]         - Market-wide summary")
        print("  list                     - List tracked ETFs")
        print("\nExamples:")
        print("  flowtrack_api.py flows SPY")
        print("  flowtrack_api.py sector technology")
        print("  flowtrack_api.py top-inflows 5")
        sys.exit(1)
    
    command = sys.argv[1].replace('-', '_')
    args = sys.argv[2:]
    
    commands = {
        'flows': cmd_flows,
        'sector': cmd_sector,
        'top_inflows': cmd_top_inflows,
        'top_outflows': cmd_top_outflows,
        'summary': cmd_summary,
        'list': cmd_list
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see usage")
        sys.exit(1)
