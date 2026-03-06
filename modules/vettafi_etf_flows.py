#!/usr/bin/env python3
"""
VettaFi ETF Flows Tracker
Provides daily ETF creation/redemption data, net flows, and holdings changes for global ETFs.

Source: https://www.vettafi.com/etf-flows/api-docs
Category: ETF & Fund Flows
Free tier: 500 queries per month (requires API key)
Update frequency: daily
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://api.vettafi.com/v2"

def get_etf_flows(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
    """
    Get ETF flow data for a specific symbol.
    
    Args:
        symbol: ETF ticker (e.g., 'SPY', 'QQQ')
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        api_key: VettaFi API key (optional - uses demo mode if not provided)
    
    Returns:
        Dictionary with flow data including net flows, creation/redemption units
    """
    try:
        # Default date range: last 30 days
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # In demo mode, return mock data structure (real API requires key)
        if not api_key:
            return {
                "symbol": symbol.upper(),
                "start_date": start_date,
                "end_date": end_date,
                "flows": [
                    {
                        "date": end_date,
                        "net_flow_usd": 125000000,
                        "creation_units": 500000,
                        "redemption_units": 100000,
                        "aum_change_pct": 0.45,
                        "flow_velocity": "moderate"
                    }
                ],
                "summary": {
                    "total_net_flow": 125000000,
                    "avg_daily_flow": 4166667,
                    "flow_direction": "inflow"
                },
                "source": "VettaFi ETF Flows (demo mode - requires API key for real data)"
            }
        
        # Real API call (requires valid key)
        url = f"{BASE_URL}/flows"
        params = {
            "symbol": symbol.upper(),
            "start_date": start_date,
            "end_date": end_date
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch ETF flows: {str(e)}"}

def get_top_inflows(limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get top ETFs by net inflows.
    
    Args:
        limit: Number of top ETFs to return (default: 10)
        api_key: VettaFi API key
    
    Returns:
        List of ETFs ranked by net inflows
    """
    try:
        if not api_key:
            # Demo data
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "top_inflows": [
                    {"symbol": "SPY", "net_flow_usd": 1250000000, "flow_pct": 2.1},
                    {"symbol": "QQQ", "net_flow_usd": 890000000, "flow_pct": 1.8},
                    {"symbol": "IWM", "net_flow_usd": 450000000, "flow_pct": 1.2}
                ][:limit],
                "source": "VettaFi ETF Flows (demo mode)"
            }
        
        url = f"{BASE_URL}/flows/top-inflows"
        params = {"limit": limit}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        return {"error": f"Failed to fetch top inflows: {str(e)}"}

def get_top_outflows(limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get top ETFs by net outflows.
    
    Args:
        limit: Number of top ETFs to return (default: 10)
        api_key: VettaFi API key
    
    Returns:
        List of ETFs ranked by net outflows
    """
    try:
        if not api_key:
            # Demo data
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "top_outflows": [
                    {"symbol": "EEM", "net_flow_usd": -320000000, "flow_pct": -1.5},
                    {"symbol": "HYG", "net_flow_usd": -180000000, "flow_pct": -0.9},
                    {"symbol": "LQD", "net_flow_usd": -125000000, "flow_pct": -0.6}
                ][:limit],
                "source": "VettaFi ETF Flows (demo mode)"
            }
        
        url = f"{BASE_URL}/flows/top-outflows"
        params = {"limit": limit}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        return {"error": f"Failed to fetch top outflows: {str(e)}"}

def get_sector_flows(api_key: Optional[str] = None) -> Dict:
    """
    Get ETF flows by sector.
    
    Args:
        api_key: VettaFi API key
    
    Returns:
        Sector-level flow data
    """
    try:
        if not api_key:
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "sector_flows": [
                    {"sector": "Technology", "net_flow_usd": 2100000000, "rotation_signal": "strong_inflow"},
                    {"sector": "Financials", "net_flow_usd": 890000000, "rotation_signal": "moderate_inflow"},
                    {"sector": "Energy", "net_flow_usd": -450000000, "rotation_signal": "outflow"}
                ],
                "source": "VettaFi ETF Flows (demo mode)"
            }
        
        url = f"{BASE_URL}/flows/sector"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        return {"error": f"Failed to fetch sector flows: {str(e)}"}

if __name__ == "__main__":
    # Test the module
    print("=== VettaFi ETF Flows Test ===\n")
    
    # Test individual ETF flows
    spy_flows = get_etf_flows("SPY")
    print(f"SPY Flows:\n{json.dumps(spy_flows, indent=2)}\n")
    
    # Test top inflows
    top_in = get_top_inflows(5)
    print(f"Top 5 Inflows:\n{json.dumps(top_in, indent=2)}\n")
    
    # Test top outflows
    top_out = get_top_outflows(5)
    print(f"Top 5 Outflows:\n{json.dumps(top_out, indent=2)}\n")
    
    # Test sector flows
    sectors = get_sector_flows()
    print(f"Sector Flows:\n{json.dumps(sectors, indent=2)}")
