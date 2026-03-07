#!/usr/bin/env python3
"""
Nasdaq Data Link ETF Flows — Specialized ETF Flow Tracking Module

Focused module for ETF flow analysis and tracking. Provides:
- Single and bulk ETF flow queries
- Top inflow/outflow identification
- Sector flow aggregation
- Flow momentum analysis

Source: https://data.nasdaq.com/api/v3/datasets/
Category: ETF & Fund Flows
Free tier: True (requires NASDAQ_DATA_LINK_API_KEY or QUANDL_API_KEY)
Author: QuantClaw Data NightBuilder
Phase: 107
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Nasdaq Data Link API Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY", "")

# ETF Flow Database Codes (ETFG database on Nasdaq Data Link)
ETFG_DATABASE = "ETFG"

# Sector ETF Mapping
SECTOR_ETFS = {
    'technology': ['XLK', 'QQQ', 'VGT'],
    'financials': ['XLF', 'VFH'],
    'energy': ['XLE', 'VDE'],
    'healthcare': ['XLV', 'VHT'],
    'industrials': ['XLI', 'VIS'],
    'consumer_staples': ['XLP', 'VDC'],
    'consumer_discretionary': ['XLY', 'VCR'],
    'utilities': ['XLU', 'VPU'],
    'real_estate': ['XLRE', 'VNQ'],
    'materials': ['XLB', 'VAW'],
    'communications': ['XLC', 'VOX'],
}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Nasdaq Data Link API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Response JSON data
        
    Raises:
        ValueError: If API key is missing
        requests.RequestException: If API request fails
    """
    if not NASDAQ_API_KEY:
        raise ValueError("NASDAQ_DATA_LINK_API_KEY or QUANDL_API_KEY environment variable not set")
    
    url = f"{NASDAQ_BASE_URL}/{endpoint}"
    params = params or {}
    params['api_key'] = NASDAQ_API_KEY
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()


def get_etf_flows(symbol: str, days: int = 30) -> Dict[str, Union[str, List[Dict]]]:
    """
    Get fund flow data for a specific ETF.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY')
        days: Number of days of historical data (default: 30)
        
    Returns:
        Dictionary with symbol, metadata, and flow data
        
    Example:
        >>> flows = get_etf_flows('SPY')
        >>> flows = get_etf_flows('QQQ', days=60)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Try ETFG database first (ETF Global fund flows)
        dataset_code = f"{ETFG_DATABASE}/{symbol}_FLOW"
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        }
        
        response = _make_request(f"datasets/{dataset_code}/data.json", params)
        
        dataset_data = response.get('dataset_data', {})
        column_names = dataset_data.get('column_names', [])
        data = dataset_data.get('data', [])
        
        # Transform data into structured format
        flows = []
        for row in data:
            flow_entry = dict(zip(column_names, row))
            flows.append(flow_entry)
        
        return {
            'symbol': symbol,
            'database': ETFG_DATABASE,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'count': len(flows),
            'flows': flows
        }
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            # Dataset not found
            return {
                'symbol': symbol,
                'database': ETFG_DATABASE,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'count': 0,
                'flows': [],
                'error': f'Dataset {dataset_code} not found',
                'note': 'This ETF may not have flow data available in Nasdaq Data Link'
            }
        elif e.response.status_code == 403:
            # API key invalid or unauthorized
            return {
                'symbol': symbol,
                'database': ETFG_DATABASE,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'count': 0,
                'flows': [],
                'error': 'Invalid or unauthorized API key',
                'note': 'Please set valid NASDAQ_DATA_LINK_API_KEY or QUANDL_API_KEY'
            }
        raise


def get_etf_flows_bulk(symbols: List[str], days: int = 30) -> Dict[str, Dict]:
    """
    Get fund flow data for multiple ETFs in bulk.
    
    Args:
        symbols: List of ETF ticker symbols (e.g., ['SPY', 'QQQ', 'IWM'])
        days: Number of days of historical data (default: 30)
        
    Returns:
        Dictionary mapping each symbol to its flow data
        
    Example:
        >>> flows = get_etf_flows_bulk(['SPY', 'QQQ', 'IWM', 'EEM'])
    """
    results = {}
    
    for symbol in symbols:
        try:
            results[symbol] = get_etf_flows(symbol, days=days)
        except Exception as e:
            results[symbol] = {
                'symbol': symbol,
                'error': str(e),
                'flows': []
            }
    
    return results


def get_top_inflows(n: int = 10, days: int = 7) -> List[Dict]:
    """
    Get ETFs with the highest inflows over the specified period.
    
    Args:
        n: Number of top ETFs to return (default: 10)
        days: Period for flow calculation (default: 7 days)
        
    Returns:
        List of ETFs with highest inflows, sorted descending
        
    Example:
        >>> top_inflows = get_top_inflows(n=10)
        >>> top_weekly = get_top_inflows(n=20, days=7)
    """
    # Sample ETF universe to scan
    etf_universe = [
        'SPY', 'QQQ', 'IWM', 'EEM', 'VTI', 'AGG', 'BND', 'TLT',
        'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU',
        'GLD', 'SLV', 'USO', 'HYG', 'LQD', 'EFA', 'VWO'
    ]
    
    flows_data = get_etf_flows_bulk(etf_universe, days=days)
    
    # Calculate total flows for each ETF
    etf_totals = []
    for symbol, data in flows_data.items():
        if 'error' in data or not data.get('flows'):
            continue
            
        # Sum up flow values (assuming 'Flow' or 'Net_Flow' column)
        total_flow = 0
        for flow_entry in data['flows']:
            # Try different possible column names
            flow_value = (
                flow_entry.get('Flow') or 
                flow_entry.get('Net_Flow') or 
                flow_entry.get('Net Flow') or 
                flow_entry.get('Value') or 
                0
            )
            if isinstance(flow_value, (int, float)):
                total_flow += flow_value
        
        if total_flow > 0:  # Only include positive flows (inflows)
            etf_totals.append({
                'symbol': symbol,
                'total_inflow': total_flow,
                'days': days,
                'latest_date': data['flows'][0].get('Date') if data['flows'] else None
            })
    
    # Sort by total inflow descending
    etf_totals.sort(key=lambda x: x['total_inflow'], reverse=True)
    
    return etf_totals[:n]


def get_top_outflows(n: int = 10, days: int = 7) -> List[Dict]:
    """
    Get ETFs with the highest outflows over the specified period.
    
    Args:
        n: Number of top ETFs to return (default: 10)
        days: Period for flow calculation (default: 7 days)
        
    Returns:
        List of ETFs with highest outflows, sorted by magnitude
        
    Example:
        >>> top_outflows = get_top_outflows(n=10)
        >>> top_monthly = get_top_outflows(n=15, days=30)
    """
    # Sample ETF universe to scan
    etf_universe = [
        'SPY', 'QQQ', 'IWM', 'EEM', 'VTI', 'AGG', 'BND', 'TLT',
        'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU',
        'GLD', 'SLV', 'USO', 'HYG', 'LQD', 'EFA', 'VWO'
    ]
    
    flows_data = get_etf_flows_bulk(etf_universe, days=days)
    
    # Calculate total flows for each ETF
    etf_totals = []
    for symbol, data in flows_data.items():
        if 'error' in data or not data.get('flows'):
            continue
            
        # Sum up flow values
        total_flow = 0
        for flow_entry in data['flows']:
            flow_value = (
                flow_entry.get('Flow') or 
                flow_entry.get('Net_Flow') or 
                flow_entry.get('Net Flow') or 
                flow_entry.get('Value') or 
                0
            )
            if isinstance(flow_value, (int, float)):
                total_flow += flow_value
        
        if total_flow < 0:  # Only include negative flows (outflows)
            etf_totals.append({
                'symbol': symbol,
                'total_outflow': abs(total_flow),
                'days': days,
                'latest_date': data['flows'][0].get('Date') if data['flows'] else None
            })
    
    # Sort by total outflow descending
    etf_totals.sort(key=lambda x: x['total_outflow'], reverse=True)
    
    return etf_totals[:n]


def get_sector_flows(days: int = 7) -> Dict[str, Dict]:
    """
    Get aggregate fund flows by sector ETFs.
    
    Args:
        days: Period for flow calculation (default: 7 days)
        
    Returns:
        Dictionary mapping sectors to their aggregate flow data
        
    Example:
        >>> sector_flows = get_sector_flows()
        >>> monthly_sector = get_sector_flows(days=30)
    """
    sector_results = {}
    
    for sector, etf_list in SECTOR_ETFS.items():
        sector_data = get_etf_flows_bulk(etf_list, days=days)
        
        # Aggregate flows for the sector
        total_flow = 0
        etf_count = 0
        latest_date = None
        
        for symbol, data in sector_data.items():
            if 'error' in data or not data.get('flows'):
                continue
                
            etf_count += 1
            if not latest_date and data['flows']:
                latest_date = data['flows'][0].get('Date')
            
            # Sum flows
            for flow_entry in data['flows']:
                flow_value = (
                    flow_entry.get('Flow') or 
                    flow_entry.get('Net_Flow') or 
                    flow_entry.get('Net Flow') or 
                    flow_entry.get('Value') or 
                    0
                )
                if isinstance(flow_value, (int, float)):
                    total_flow += flow_value
        
        sector_results[sector] = {
            'total_flow': total_flow,
            'etf_count': etf_count,
            'etfs': etf_list,
            'days': days,
            'latest_date': latest_date,
            'flow_type': 'inflow' if total_flow > 0 else 'outflow' if total_flow < 0 else 'neutral'
        }
    
    return sector_results


def get_flow_momentum(symbol: str, days: int = 30) -> Dict[str, Union[str, float, List]]:
    """
    Calculate flow momentum and trend analysis for an ETF.
    
    Args:
        symbol: ETF ticker symbol
        days: Period for momentum calculation (default: 30)
        
    Returns:
        Dictionary with momentum metrics, trend direction, and analysis
        
    Example:
        >>> momentum = get_flow_momentum('SPY')
        >>> spy_trend = get_flow_momentum('SPY', days=60)
    """
    flows_data = get_etf_flows(symbol, days=days)
    
    if 'error' in flows_data or not flows_data.get('flows'):
        return {
            'symbol': symbol,
            'error': 'No flow data available',
            'momentum': None
        }
    
    flows = flows_data['flows']
    
    # Calculate momentum metrics
    recent_period = len(flows) // 3  # Last 1/3 of period
    older_period = len(flows) // 3   # Middle 1/3 of period
    
    recent_flows = flows[:recent_period]
    older_flows = flows[recent_period:recent_period + older_period]
    
    # Sum flows for each period
    recent_total = sum(
        f.get('Flow', 0) or f.get('Net_Flow', 0) or f.get('Value', 0) or 0
        for f in recent_flows
    )
    older_total = sum(
        f.get('Flow', 0) or f.get('Net_Flow', 0) or f.get('Value', 0) or 0
        for f in older_flows
    )
    
    # Calculate momentum (% change)
    if older_total != 0:
        momentum_pct = ((recent_total - older_total) / abs(older_total)) * 100
    else:
        momentum_pct = 0
    
    # Determine trend
    if momentum_pct > 10:
        trend = 'accelerating_inflow'
    elif momentum_pct > 0:
        trend = 'positive'
    elif momentum_pct > -10:
        trend = 'neutral'
    elif momentum_pct > -20:
        trend = 'negative'
    else:
        trend = 'accelerating_outflow'
    
    # Calculate average daily flow
    total_flow = sum(
        f.get('Flow', 0) or f.get('Net_Flow', 0) or f.get('Value', 0) or 0
        for f in flows
    )
    avg_daily_flow = total_flow / len(flows) if flows else 0
    
    return {
        'symbol': symbol,
        'days': days,
        'momentum_pct': round(momentum_pct, 2),
        'trend': trend,
        'recent_total': recent_total,
        'older_total': older_total,
        'avg_daily_flow': round(avg_daily_flow, 2),
        'total_flow': total_flow,
        'data_points': len(flows)
    }


# Main execution for testing
if __name__ == "__main__":
    print(json.dumps({
        "module": "nasdaq_data_link_etf_flows",
        "status": "implemented",
        "functions": [
            "get_etf_flows",
            "get_etf_flows_bulk",
            "get_top_inflows",
            "get_top_outflows",
            "get_sector_flows",
            "get_flow_momentum"
        ],
        "source": "https://data.nasdaq.com/api/v3/datasets/"
    }, indent=2))
