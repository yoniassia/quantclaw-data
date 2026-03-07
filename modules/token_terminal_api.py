#!/usr/bin/env python3
"""
Token Terminal API — Crypto & DeFi Protocol Metrics Module

Provides access to Token Terminal's comprehensive on-chain financial metrics for crypto projects and DeFi protocols.
Includes protocol revenue, fees, active users, TVL, token metrics, and P/E ratios.
Data is standardized for comparable analysis across 100+ blockchain networks and decentralized applications.

Source: https://tokenterminal.com/api/docs
Category: Crypto & DeFi On-Chain
Free tier: True (100 requests/day, requires TOKEN_TERMINAL_API_KEY)
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Token Terminal API Configuration
TT_BASE_URL = "https://api.tokenterminal.com/v2"
TT_API_KEY = os.environ.get("TOKEN_TERMINAL_API_KEY", "")

# Key metrics registry
TT_KEY_METRICS = {
    'revenue': 'Total protocol revenue',
    'fees': 'Total fees paid by users',
    'tvl': 'Total Value Locked',
    'active_users': 'Daily active users',
    'token_incentives': 'Token incentives distributed',
    'market_cap': 'Fully diluted market capitalization',
    'pe_ratio': 'Price-to-Earnings ratio',
    'ps_ratio': 'Price-to-Sales ratio',
    'token_trading_volume': 'Token trading volume',
    'gmv': 'Gross Merchandise Volume',
}


def _make_request(
    endpoint: str,
    params: Optional[Dict] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Helper function to make authenticated requests to Token Terminal API
    
    Args:
        endpoint: API endpoint path (e.g., '/projects')
        params: Optional query parameters
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        Dict with success status and data or error message
    """
    try:
        key = api_key or TT_API_KEY
        if not key:
            return {
                "success": False,
                "error": "TOKEN_TERMINAL_API_KEY not set in environment",
                "hint": "Add to .env file or pass as parameter"
            }
        
        url = f"{TT_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            return {
                "success": False,
                "error": "Rate limit exceeded (1000 req/min)",
                "retry_after": response.headers.get("Retry-After", "60")
            }
        
        # Handle authentication errors
        if response.status_code in [402, 403]:
            return {
                "success": False,
                "error": f"Authentication failed (HTTP {response.status_code})",
                "hint": "Check your API key or subscription status"
            }
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "data": data.get("data", []),
            "errors": data.get("errors", []),
            "total_records": len(data.get("data", []))
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_projects(api_key: Optional[str] = None) -> Dict:
    """
    Get list of all available projects/protocols
    
    Args:
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with project list including project_id, name, symbol, coingecko_id
    """
    result = _make_request("/projects", api_key=api_key)
    
    if result["success"]:
        # Extract key info from projects
        projects_summary = []
        for project in result["data"]:
            projects_summary.append({
                "project_id": project.get("project_id"),
                "name": project.get("name"),
                "symbol": project.get("symbol"),
                "coingecko_id": project.get("coingecko_id"),
                "is_archived": project.get("is_archived", False),
                "products_count": len(project.get("products", []))
            })
        
        return {
            "success": True,
            "projects": projects_summary,
            "total_projects": len(projects_summary),
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_all_metrics(api_key: Optional[str] = None) -> Dict:
    """
    Get list of all available metrics
    
    Args:
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with metrics list and categories
    """
    result = _make_request("/metrics", api_key=api_key)
    
    if result["success"]:
        metrics_by_category = {}
        
        for metric in result["data"]:
            metric_id = metric.get("metric_id")
            category = metric.get("category", "Other")
            
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            
            metrics_by_category[category].append({
                "metric_id": metric_id,
                "name": metric.get("name"),
                "description": metric.get("description"),
                "unit": metric.get("unit")
            })
        
        return {
            "success": True,
            "metrics_by_category": metrics_by_category,
            "total_metrics": len(result["data"]),
            "categories": list(metrics_by_category.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_project_metrics(
    metric_id: str,
    project_ids: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get metric data for one or more projects
    
    Args:
        metric_id: Metric identifier (e.g., 'revenue', 'tvl', 'active_users')
        project_ids: List of project IDs (e.g., ['aave', 'uniswap']) or None for all
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with time series data for requested metrics
    """
    params = {}
    
    if project_ids:
        params["project_ids"] = ",".join(project_ids)
    
    if start_date:
        params["start"] = start_date
    
    if end_date:
        params["end"] = end_date
    
    result = _make_request(f"/metrics/{metric_id}", params=params, api_key=api_key)
    
    if result["success"]:
        # Organize data by project
        by_project = {}
        
        for record in result["data"]:
            proj_id = record.get("project_id")
            if proj_id not in by_project:
                by_project[proj_id] = {
                    "project_name": record.get("project_name"),
                    "metric_id": record.get("metric_id"),
                    "data_points": []
                }
            
            by_project[proj_id]["data_points"].append({
                "timestamp": record.get("timestamp"),
                "value": float(record.get("value", 0))
            })
        
        # Calculate summary stats for each project
        for proj_id in by_project:
            values = [dp["value"] for dp in by_project[proj_id]["data_points"]]
            if values:
                by_project[proj_id]["latest_value"] = values[-1]
                by_project[proj_id]["avg_value"] = sum(values) / len(values)
                by_project[proj_id]["max_value"] = max(values)
                by_project[proj_id]["min_value"] = min(values)
                by_project[proj_id]["total_points"] = len(values)
        
        return {
            "success": True,
            "metric_id": metric_id,
            "by_project": by_project,
            "errors": result.get("errors", []),
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_protocol_revenue(
    project_ids: Optional[List[str]] = None,
    lookback_days: int = 90,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get protocol revenue data for DeFi protocols
    
    Args:
        project_ids: List of protocol IDs (e.g., ['aave', 'uniswap']) or None for all
        lookback_days: Number of days of history (default 90)
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with revenue data and trends
    """
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    return get_project_metrics(
        metric_id="revenue",
        project_ids=project_ids,
        start_date=start_date,
        end_date=end_date,
        api_key=api_key
    )


def get_protocol_tvl(
    project_ids: Optional[List[str]] = None,
    lookback_days: int = 90,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get Total Value Locked (TVL) for DeFi protocols
    
    Args:
        project_ids: List of protocol IDs or None for all
        lookback_days: Number of days of history (default 90)
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with TVL data and trends
    """
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    return get_project_metrics(
        metric_id="tvl",
        project_ids=project_ids,
        start_date=start_date,
        end_date=end_date,
        api_key=api_key
    )


def get_protocol_active_users(
    project_ids: Optional[List[str]] = None,
    lookback_days: int = 90,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get active users data for protocols
    
    Args:
        project_ids: List of protocol IDs or None for all
        lookback_days: Number of days of history (default 90)
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with active users data and growth trends
    """
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    return get_project_metrics(
        metric_id="active_users",
        project_ids=project_ids,
        start_date=start_date,
        end_date=end_date,
        api_key=api_key
    )


def get_market_sectors(api_key: Optional[str] = None) -> Dict:
    """
    Get all market sectors (DeFi categories)
    
    Args:
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with market sectors list
    """
    result = _make_request("/market-sectors", api_key=api_key)
    
    if result["success"]:
        sectors = []
        for sector in result["data"]:
            sectors.append({
                "sector_id": sector.get("market_sector_id"),
                "name": sector.get("name"),
                "description": sector.get("description")
            })
        
        return {
            "success": True,
            "sectors": sectors,
            "total_sectors": len(sectors),
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_project_aggregations(
    project_id: str,
    metric_ids: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get aggregated metrics for a specific project
    Includes latest values, averages, changes over different time periods
    
    Args:
        project_id: Project identifier (e.g., 'aave', 'uniswap')
        metric_ids: List of metric IDs or None for all available
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with aggregated metrics and time period comparisons
    """
    endpoint = f"/projects/{project_id}/metric-aggregations"
    
    params = {}
    if metric_ids:
        params["metric_ids"] = ",".join(metric_ids)
    
    result = _make_request(endpoint, params=params, api_key=api_key)
    
    if result["success"]:
        aggregations = {}
        
        for agg in result["data"]:
            metric_id = agg.get("metric_id")
            aggregations[metric_id] = {
                "latest_value": agg.get("latest_value"),
                "avg_24h": agg.get("avg_24h"),
                "avg_7d": agg.get("avg_7d"),
                "avg_30d": agg.get("avg_30d"),
                "change_24h": agg.get("change_24h"),
                "change_7d": agg.get("change_7d"),
                "change_30d": agg.get("change_30d"),
            }
        
        return {
            "success": True,
            "project_id": project_id,
            "aggregations": aggregations,
            "timestamp": datetime.now().isoformat()
        }
    
    return result


def get_defi_snapshot(
    protocols: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get comprehensive DeFi snapshot with key metrics for protocols
    
    Args:
        protocols: List of protocol IDs (defaults to major DeFi protocols)
        api_key: Optional Token Terminal API key
    
    Returns:
        Dict with snapshot of TVL, revenue, users across protocols
    """
    # Default to major DeFi protocols if none specified
    if protocols is None:
        protocols = ['aave', 'uniswap', 'curve', 'lido', 'makerdao']
    
    snapshot = {}
    
    # Get TVL
    tvl_data = get_protocol_tvl(project_ids=protocols, lookback_days=7, api_key=api_key)
    if tvl_data.get("success"):
        for proj_id, data in tvl_data.get("by_project", {}).items():
            if proj_id not in snapshot:
                snapshot[proj_id] = {"project_name": data.get("project_name")}
            snapshot[proj_id]["tvl"] = data.get("latest_value")
    
    # Get Revenue
    revenue_data = get_protocol_revenue(project_ids=protocols, lookback_days=7, api_key=api_key)
    if revenue_data.get("success"):
        for proj_id, data in revenue_data.get("by_project", {}).items():
            if proj_id not in snapshot:
                snapshot[proj_id] = {"project_name": data.get("project_name")}
            snapshot[proj_id]["revenue"] = data.get("latest_value")
    
    # Get Active Users
    users_data = get_protocol_active_users(project_ids=protocols, lookback_days=7, api_key=api_key)
    if users_data.get("success"):
        for proj_id, data in users_data.get("by_project", {}).items():
            if proj_id not in snapshot:
                snapshot[proj_id] = {"project_name": data.get("project_name")}
            snapshot[proj_id]["active_users"] = data.get("latest_value")
    
    return {
        "success": True,
        "snapshot": snapshot,
        "protocols_count": len(snapshot),
        "timestamp": datetime.now().isoformat(),
        "source": "Token Terminal API"
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Token Terminal API - Crypto & DeFi Protocol Metrics")
    print("=" * 60)
    
    # Test 1: Get all projects
    print("\n[1/4] Fetching all projects...")
    projects = get_projects()
    if projects.get("success"):
        print(f"✓ Found {projects['total_projects']} projects")
        print(f"Sample projects: {projects['projects'][:3]}")
    else:
        print(f"✗ Error: {projects.get('error')}")
    
    # Test 2: Get all metrics
    print("\n[2/4] Fetching all metrics...")
    metrics = get_all_metrics()
    if metrics.get("success"):
        print(f"✓ Found {metrics['total_metrics']} metrics")
        print(f"Categories: {metrics['categories']}")
    else:
        print(f"✗ Error: {metrics.get('error')}")
    
    # Test 3: Get DeFi snapshot
    print("\n[3/4] Fetching DeFi snapshot for major protocols...")
    snapshot = get_defi_snapshot()
    if snapshot.get("success"):
        print(f"✓ Snapshot for {snapshot['protocols_count']} protocols")
        for proj_id, data in list(snapshot['snapshot'].items())[:2]:
            print(f"  {data.get('project_name', proj_id)}: TVL=${data.get('tvl', 0):,.0f}")
    else:
        print(f"✗ Error: {snapshot.get('error')}")
    
    # Test 4: Get market sectors
    print("\n[4/4] Fetching market sectors...")
    sectors = get_market_sectors()
    if sectors.get("success"):
        print(f"✓ Found {sectors['total_sectors']} market sectors")
        print(f"Sample sectors: {sectors['sectors'][:3]}")
    else:
        print(f"✗ Error: {sectors.get('error')}")
    
    print("\n" + "=" * 60)
    print("Module: token_terminal_api")
    print("Status: Ready")
    print("=" * 60)
