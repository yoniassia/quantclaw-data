#!/usr/bin/env python3
"""
EIA Natural Gas Supply/Demand Module — Phase 170

US Energy Information Administration (EIA) natural gas data:
- Weekly natural gas storage reports (injections/withdrawals)
- Natural gas production by region
- Natural gas demand forecasts and actuals
- Working gas in storage vs 5-year averages

Data Source: https://api.eia.gov/v2/
Refresh: Weekly (storage reports every Thursday)
Coverage: United States

Key EIA Series:
- NG.NW2_EPG0_SWO_R48_BCF.W: Weekly Lower 48 Working Gas in Storage
- NG.N9070US2.M: US Dry Natural Gas Production
- NG.N3060US3.M: US Natural Gas Total Consumption

Author: QUANTCLAW DATA Build Agent
Phase: 170
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


# EIA API Configuration
EIA_API_BASE = "https://api.eia.gov/v2"
EIA_API_KEY = ""  # Optional: Register at https://www.eia.gov/opendata/register.php

# Key Natural Gas Series
NG_SERIES = {
    # Storage Data (Weekly)
    "STORAGE_WORKING": {
        "route": "natural-gas/stor/wkly",
        "series_id": "NG.NW2_EPG0_SWO_R48_BCF.W",
        "name": "Working Gas in Storage - Lower 48 (BCF)",
        "frequency": "weekly",
        "description": "Total working natural gas in underground storage"
    },
    "STORAGE_NET_CHANGE": {
        "route": "natural-gas/stor/wkly", 
        "series_id": "NG.NW2_EPG0_SAC_R48_BCF.W",
        "name": "Net Storage Change - Lower 48 (BCF)",
        "frequency": "weekly",
        "description": "Weekly net injections (+) or withdrawals (-)"
    },
    
    # Production Data (Monthly)
    "PRODUCTION_DRY": {
        "route": "natural-gas/prod/sum",
        "series_id": "NG.N9070US2.M",
        "name": "US Dry Natural Gas Production (BCF)",
        "frequency": "monthly",
        "description": "Total US dry natural gas production"
    },
    "PRODUCTION_MARKETED": {
        "route": "natural-gas/prod/sum",
        "series_id": "NG.N9050US2.M",
        "name": "US Marketed Natural Gas Production (BCF)",
        "frequency": "monthly",
        "description": "Total US marketed natural gas production"
    },
    
    # Consumption/Demand (Monthly)
    "CONSUMPTION_TOTAL": {
        "route": "natural-gas/cons/sum",
        "series_id": "NG.N3060US3.M",
        "name": "US Total Natural Gas Consumption (BCF)",
        "frequency": "monthly",
        "description": "Total US natural gas consumption"
    },
    "CONSUMPTION_RESIDENTIAL": {
        "route": "natural-gas/cons/sum",
        "series_id": "NG.N3010US3.M",
        "name": "Residential Natural Gas Consumption (BCF)",
        "frequency": "monthly",
        "description": "Residential sector consumption"
    },
    "CONSUMPTION_COMMERCIAL": {
        "route": "natural-gas/cons/sum",
        "series_id": "NG.N3020US3.M",
        "name": "Commercial Natural Gas Consumption (BCF)",
        "frequency": "monthly",
        "description": "Commercial sector consumption"
    },
    "CONSUMPTION_INDUSTRIAL": {
        "route": "natural-gas/cons/sum",
        "series_id": "NG.N3035US3.M",
        "name": "Industrial Natural Gas Consumption (BCF)",
        "frequency": "monthly",
        "description": "Industrial sector consumption (excludes lease/plant)"
    },
    "CONSUMPTION_ELECTRIC_POWER": {
        "route": "natural-gas/cons/sum",
        "series_id": "NG.N3050US3.M",
        "name": "Electric Power Natural Gas Consumption (BCF)",
        "frequency": "monthly",
        "description": "Electric power sector consumption"
    },
}


def fetch_eia_series(series_key: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, limit: int = 5000) -> Dict:
    """
    Fetch data from EIA API v2 for a natural gas series
    
    Args:
        series_key: Key from NG_SERIES dict
        start_date: Optional start date (YYYY-MM-DD format)
        end_date: Optional end date (YYYY-MM-DD format)
        limit: Maximum number of data points to return
    
    Returns:
        Dict with series data
    """
    if series_key not in NG_SERIES:
        return {
            "status": "error",
            "message": f"Unknown series key: {series_key}. Valid keys: {list(NG_SERIES.keys())}"
        }
    
    series_info = NG_SERIES[series_key]
    route = series_info["route"]
    
    # Build API request
    params = {
        "frequency": series_info["frequency"][0].upper(),  # W for weekly, M for monthly
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": limit
    }
    
    if EIA_API_KEY:
        params["api_key"] = EIA_API_KEY
    
    if start_date:
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    
    try:
        url = f"{EIA_API_BASE}/{route}/data/"
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if "response" in data and "data" in data["response"]:
                return {
                    "status": "success",
                    "series_key": series_key,
                    "series_name": series_info["name"],
                    "description": series_info["description"],
                    "frequency": series_info["frequency"],
                    "data": data["response"]["data"],
                    "total_records": data["response"].get("total", len(data["response"]["data"]))
                }
            else:
                return {
                    "status": "error",
                    "message": "Unexpected API response structure",
                    "raw_data": data
                }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}",
                "status_code": response.status_code
            }
            
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }


def get_weekly_storage_report(weeks: int = 52) -> Dict:
    """
    Get latest weekly natural gas storage report
    
    Args:
        weeks: Number of weeks of historical data to fetch
    
    Returns:
        Dict with storage levels and net changes
    """
    storage = fetch_eia_series("STORAGE_WORKING", limit=weeks)
    net_change = fetch_eia_series("STORAGE_NET_CHANGE", limit=weeks)
    
    if storage["status"] != "success" or net_change["status"] != "success":
        return {
            "status": "error",
            "message": "Failed to fetch storage data",
            "storage_error": storage.get("message"),
            "net_change_error": net_change.get("message")
        }
    
    # Calculate 5-year average (simplified - would need historical data)
    current_storage = storage["data"][0] if storage["data"] else None
    current_change = net_change["data"][0] if net_change["data"] else None
    
    # Calculate YoY change
    yoy_storage = None
    if len(storage["data"]) >= 52:
        current_val = float(storage["data"][0].get("value", 0))
        year_ago_val = float(storage["data"][51].get("value", 0))
        yoy_storage = {
            "current": current_val,
            "year_ago": year_ago_val,
            "change_bcf": current_val - year_ago_val,
            "change_pct": ((current_val - year_ago_val) / year_ago_val * 100) if year_ago_val else None
        }
    
    return {
        "status": "success",
        "report_date": current_storage.get("period") if current_storage else None,
        "current_storage": current_storage,
        "latest_net_change": current_change,
        "year_over_year": yoy_storage,
        "historical_storage": storage["data"][:weeks],
        "historical_net_changes": net_change["data"][:weeks]
    }


def get_production_data(months: int = 12) -> Dict:
    """
    Get natural gas production data
    
    Args:
        months: Number of months of historical data
    
    Returns:
        Dict with production data
    """
    dry_prod = fetch_eia_series("PRODUCTION_DRY", limit=months)
    marketed_prod = fetch_eia_series("PRODUCTION_MARKETED", limit=months)
    
    if dry_prod["status"] != "success":
        return dry_prod
    
    # Calculate growth rates
    growth_rates = []
    if len(dry_prod["data"]) >= 2:
        for i in range(min(12, len(dry_prod["data"]) - 1)):
            current = float(dry_prod["data"][i].get("value", 0))
            previous = float(dry_prod["data"][i + 1].get("value", 0))
            if previous:
                mom_growth = ((current - previous) / previous * 100)
                growth_rates.append({
                    "period": dry_prod["data"][i].get("period"),
                    "value": current,
                    "mom_growth_pct": round(mom_growth, 2)
                })
    
    # YoY growth
    yoy_growth = None
    if len(dry_prod["data"]) >= 13:
        current = float(dry_prod["data"][0].get("value", 0))
        year_ago = float(dry_prod["data"][12].get("value", 0))
        if year_ago:
            yoy_growth = {
                "current_period": dry_prod["data"][0].get("period"),
                "current_value": current,
                "year_ago_value": year_ago,
                "yoy_growth_pct": round((current - year_ago) / year_ago * 100, 2)
            }
    
    return {
        "status": "success",
        "dry_production": dry_prod["data"],
        "marketed_production": marketed_prod["data"] if marketed_prod["status"] == "success" else None,
        "growth_rates": growth_rates,
        "yoy_growth": yoy_growth
    }


def get_demand_data(months: int = 12) -> Dict:
    """
    Get natural gas consumption/demand data by sector
    
    Args:
        months: Number of months of historical data
    
    Returns:
        Dict with demand breakdown by sector
    """
    total = fetch_eia_series("CONSUMPTION_TOTAL", limit=months)
    residential = fetch_eia_series("CONSUMPTION_RESIDENTIAL", limit=months)
    commercial = fetch_eia_series("CONSUMPTION_COMMERCIAL", limit=months)
    industrial = fetch_eia_series("CONSUMPTION_INDUSTRIAL", limit=months)
    electric = fetch_eia_series("CONSUMPTION_ELECTRIC_POWER", limit=months)
    
    if total["status"] != "success":
        return total
    
    # Calculate latest sector breakdown
    latest_breakdown = None
    if (total["data"] and residential["status"] == "success" and 
        commercial["status"] == "success" and industrial["status"] == "success" and
        electric["status"] == "success"):
        
        latest_period = total["data"][0].get("period")
        total_val = float(total["data"][0].get("value", 0))
        
        if total_val > 0:
            latest_breakdown = {
                "period": latest_period,
                "total_bcf": total_val,
                "sectors": {
                    "residential": {
                        "bcf": float(residential["data"][0].get("value", 0)),
                        "pct_of_total": round(float(residential["data"][0].get("value", 0)) / total_val * 100, 1)
                    },
                    "commercial": {
                        "bcf": float(commercial["data"][0].get("value", 0)),
                        "pct_of_total": round(float(commercial["data"][0].get("value", 0)) / total_val * 100, 1)
                    },
                    "industrial": {
                        "bcf": float(industrial["data"][0].get("value", 0)),
                        "pct_of_total": round(float(industrial["data"][0].get("value", 0)) / total_val * 100, 1)
                    },
                    "electric_power": {
                        "bcf": float(electric["data"][0].get("value", 0)),
                        "pct_of_total": round(float(electric["data"][0].get("value", 0)) / total_val * 100, 1)
                    }
                }
            }
    
    return {
        "status": "success",
        "latest_breakdown": latest_breakdown,
        "total_consumption": total["data"],
        "by_sector": {
            "residential": residential["data"] if residential["status"] == "success" else None,
            "commercial": commercial["data"] if commercial["status"] == "success" else None,
            "industrial": industrial["data"] if industrial["status"] == "success" else None,
            "electric_power": electric["data"] if electric["status"] == "success" else None
        }
    }


def get_supply_demand_balance(months: int = 12) -> Dict:
    """
    Get comprehensive natural gas supply/demand balance
    
    Args:
        months: Number of months of historical data
    
    Returns:
        Dict with supply/demand balance analysis
    """
    storage = get_weekly_storage_report(weeks=12)
    production = get_production_data(months=months)
    demand = get_demand_data(months=months)
    
    # Calculate balance indicator
    balance_indicator = "balanced"
    if storage["status"] == "success" and storage.get("year_over_year"):
        yoy_change = storage["year_over_year"]["change_pct"]
        if yoy_change > 10:
            balance_indicator = "oversupplied"
        elif yoy_change < -10:
            balance_indicator = "undersupplied"
    
    return {
        "status": "success",
        "balance_indicator": balance_indicator,
        "latest_storage": storage.get("current_storage") if storage["status"] == "success" else None,
        "latest_production": production.get("dry_production", [{}])[0] if production["status"] == "success" else None,
        "latest_demand": demand.get("latest_breakdown") if demand["status"] == "success" else None,
        "storage_report": storage if storage["status"] == "success" else None,
        "production_data": production if production["status"] == "success" else None,
        "demand_data": demand if demand["status"] == "success" else None
    }


def list_available_series() -> Dict:
    """
    List all available natural gas series
    
    Returns:
        Dict with all series metadata
    """
    return {
        "status": "success",
        "series_count": len(NG_SERIES),
        "series": {
            key: {
                "name": info["name"],
                "description": info["description"],
                "frequency": info["frequency"]
            }
            for key, info in NG_SERIES.items()
        }
    }


def main():
    """CLI interface for natural gas supply/demand data"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing command",
            "usage": "natural_gas_supply_demand.py <command> [args]",
            "commands": {
                "ng-storage": "Get weekly storage report (args: [weeks=52])",
                "ng-production": "Get production data (args: [months=12])",
                "ng-demand": "Get demand data by sector (args: [months=12])",
                "ng-balance": "Get supply/demand balance (args: [months=12])",
                "ng-series": "Get specific series data (args: series_key [limit=5000])",
                "ng-list": "List all available series"
            }
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "ng-storage":
            weeks = int(sys.argv[2]) if len(sys.argv) > 2 else 52
            result = get_weekly_storage_report(weeks=weeks)
        
        elif command == "ng-production":
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            result = get_production_data(months=months)
        
        elif command == "ng-demand":
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            result = get_demand_data(months=months)
        
        elif command == "ng-balance":
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            result = get_supply_demand_balance(months=months)
        
        elif command == "ng-series":
            if len(sys.argv) < 3:
                result = {"error": "Missing series_key argument"}
            else:
                series_key = sys.argv[2]
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
                result = fetch_eia_series(series_key, limit=limit)
        
        elif command == "ng-list":
            result = list_available_series()
        
        else:
            result = {"error": f"Unknown command: {command}"}
        
        print(json.dumps(result, indent=2, default=str))
    
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
