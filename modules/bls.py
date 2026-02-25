#!/usr/bin/env python3
"""
US Bureau of Labor Statistics (BLS) Employment & Prices Module

Data Sources:
- BLS Public Data API v2 (api.bls.gov/publicAPI/v2)
- CPI (Consumer Price Index) - All Items and Components
- PPI (Producer Price Index)
- NFP (Non-Farm Payrolls / Employment Situation)
- Wages (Average Hourly Earnings)
- Productivity (Labor Productivity)

Monthly updates on release day. No API key required for basic access (25 queries/day).
With free registration: 500 queries/day + 10 years of data.

Phase: 97
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


# BLS API Configuration
BLS_API_BASE = "https://api.bls.gov/publicAPI/v2"
BLS_API_KEY = ""  # Optional: Register at https://data.bls.gov/registrationEngine/ for higher limits

# Key BLS Series IDs
BLS_SERIES = {
    # CPI - Consumer Price Index
    "CUSR0000SA0": "CPI-U All Items (Headline CPI)",
    "CUSR0000SA0L1E": "CPI-U All Items Less Food & Energy (Core CPI)",
    "CUSR0000SAF1": "CPI-U Food",
    "CUSR0000SAH": "CPI-U Housing",
    "CUSR0000SETB01": "CPI-U Gasoline (All Types)",
    "CUSR0000SAM": "CPI-U Medical Care",
    "CUSR0000SAS": "CPI-U Transportation",
    "CUSR0000SAA": "CPI-U Apparel",
    "CUSR0000SAE": "CPI-U Education & Communication",
    "CUSR0000SAR": "CPI-U Recreation",
    
    # PPI - Producer Price Index
    "WPUFD49207": "PPI - Final Demand",
    "WPUFD49104": "PPI - Final Demand Less Foods & Energy",
    "WPU00": "PPI - All Commodities",
    "WPUIP2311003": "PPI - Industrial Chemicals",
    
    # Employment (CES - Current Employment Statistics)
    "CES0000000001": "Total Nonfarm Employment (NFP)",
    "CES0500000001": "Total Private Employment",
    "CES0600000001": "Goods-Producing Employment",
    "CES0800000001": "Service-Providing Employment",
    "CES4142000001": "Retail Trade Employment",
    "CES5051000001": "Information Employment",
    "CES5552000001": "Financial Activities Employment",
    "CES6054000001": "Professional & Business Services",
    "CES6562000001": "Health Care & Social Assistance",
    
    # Wages (Average Hourly Earnings)
    "CES0500000003": "Average Hourly Earnings - Private",
    "CES0000000003": "Average Hourly Earnings - Total Nonfarm",
    "CES4142000003": "Average Hourly Earnings - Retail Trade",
    "CES6562000003": "Average Hourly Earnings - Health Care",
    
    # Unemployment Rate (from CPS - Current Population Survey)
    "LNS14000000": "Unemployment Rate",
    "LNS12300000": "Labor Force Participation Rate",
    
    # Productivity (Major Sector Productivity)
    "PRS85006092": "Nonfarm Business Labor Productivity",
    "PRS85006112": "Nonfarm Business Unit Labor Costs",
}

# CPI Component Weights (approximate, for reference)
CPI_WEIGHTS = {
    "Housing": 33.3,
    "Transportation": 16.8,
    "Food": 13.4,
    "Medical Care": 8.9,
    "Recreation": 5.6,
    "Education & Communication": 6.4,
    "Apparel": 2.6,
    "Other": 13.0
}


def fetch_bls_series(series_ids: List[str], start_year: Optional[int] = None, 
                     end_year: Optional[int] = None, catalog: bool = False) -> Dict:
    """
    Fetch data from BLS API for one or more series
    
    Args:
        series_ids: List of BLS series IDs
        start_year: Optional start year (defaults to 5 years ago)
        end_year: Optional end year (defaults to current year)
        catalog: Include series catalog metadata
    
    Returns:
        Dict with series data
    """
    if not start_year:
        start_year = datetime.now().year - 5
    if not end_year:
        end_year = datetime.now().year
    
    # Build request payload
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "catalog": catalog,
    }
    
    # Add API key if available (enables 500 queries/day + 20 year lookback)
    if BLS_API_KEY:
        payload["registrationkey"] = BLS_API_KEY
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            f"{BLS_API_BASE}/timeseries/data/",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "REQUEST_SUCCEEDED":
                return {
                    "status": "success",
                    "results": data.get("Results", {}),
                    "message": data.get("message", []),
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", ["Unknown error"]),
                    "data": data
                }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "text": response.text
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_cpi_data(months: int = 12, components: bool = False) -> Dict:
    """
    Get Consumer Price Index data
    
    Args:
        months: Number of months to retrieve
        components: Include CPI component breakdown
    
    Returns:
        Dict with CPI data and year-over-year inflation rate
    """
    end_year = datetime.now().year
    start_year = end_year - (months // 12 + 1)
    
    # Series to fetch
    series_list = ["CUSR0000SA0", "CUSR0000SA0L1E"]  # Headline + Core
    
    if components:
        series_list.extend([
            "CUSR0000SAF1",     # Food
            "CUSR0000SAH",      # Housing
            "CUSR0000SETB01",   # Gasoline
            "CUSR0000SAM",      # Medical Care
            "CUSR0000SAS",      # Transportation
            "CUSR0000SAA",      # Apparel
            "CUSR0000SAE",      # Education & Communication
            "CUSR0000SAR",      # Recreation
        ])
    
    result = fetch_bls_series(series_list, start_year, end_year)
    
    if result["status"] != "success":
        return result
    
    # Parse and structure data
    parsed = {
        "timestamp": datetime.now().isoformat(),
        "headline_cpi": _parse_series_data(result["results"], "CUSR0000SA0"),
        "core_cpi": _parse_series_data(result["results"], "CUSR0000SA0L1E"),
    }
    
    if components:
        parsed["components"] = {
            "food": _parse_series_data(result["results"], "CUSR0000SAF1"),
            "housing": _parse_series_data(result["results"], "CUSR0000SAH"),
            "gasoline": _parse_series_data(result["results"], "CUSR0000SETB01"),
            "medical": _parse_series_data(result["results"], "CUSR0000SAM"),
            "transportation": _parse_series_data(result["results"], "CUSR0000SAS"),
            "apparel": _parse_series_data(result["results"], "CUSR0000SAA"),
            "education_communication": _parse_series_data(result["results"], "CUSR0000SAE"),
            "recreation": _parse_series_data(result["results"], "CUSR0000SAR"),
        }
        parsed["component_weights"] = CPI_WEIGHTS
    
    return parsed


def get_ppi_data(months: int = 12) -> Dict:
    """
    Get Producer Price Index data
    
    Args:
        months: Number of months to retrieve
    
    Returns:
        Dict with PPI data and trends
    """
    end_year = datetime.now().year
    start_year = end_year - (months // 12 + 1)
    
    series_list = [
        "WPUFD49207",   # Final Demand
        "WPUFD49104",   # Final Demand ex Food & Energy
        "WPU00",        # All Commodities
    ]
    
    result = fetch_bls_series(series_list, start_year, end_year)
    
    if result["status"] != "success":
        return result
    
    return {
        "timestamp": datetime.now().isoformat(),
        "final_demand": _parse_series_data(result["results"], "WPUFD49207"),
        "final_demand_core": _parse_series_data(result["results"], "WPUFD49104"),
        "all_commodities": _parse_series_data(result["results"], "WPU00"),
    }


def get_employment_data(months: int = 12, detailed: bool = False) -> Dict:
    """
    Get Non-Farm Payrolls and employment data
    
    Args:
        months: Number of months to retrieve
        detailed: Include sector breakdown
    
    Returns:
        Dict with NFP and employment statistics
    """
    end_year = datetime.now().year
    start_year = end_year - (months // 12 + 1)
    
    series_list = [
        "CES0000000001",  # Total Nonfarm (NFP)
        "CES0500000001",  # Total Private
        "LNS14000000",    # Unemployment Rate
        "LNS12300000",    # Labor Force Participation
    ]
    
    if detailed:
        series_list.extend([
            "CES0600000001",  # Goods-Producing
            "CES0800000001",  # Service-Providing
            "CES4142000001",  # Retail Trade
            "CES5051000001",  # Information
            "CES5552000001",  # Financial Activities
            "CES6054000001",  # Professional & Business Services
            "CES6562000001",  # Health Care
        ])
    
    result = fetch_bls_series(series_list, start_year, end_year)
    
    if result["status"] != "success":
        return result
    
    parsed = {
        "timestamp": datetime.now().isoformat(),
        "total_nonfarm": _parse_series_data(result["results"], "CES0000000001"),
        "total_private": _parse_series_data(result["results"], "CES0500000001"),
        "unemployment_rate": _parse_series_data(result["results"], "LNS14000000"),
        "labor_force_participation": _parse_series_data(result["results"], "LNS12300000"),
    }
    
    if detailed:
        parsed["sectors"] = {
            "goods_producing": _parse_series_data(result["results"], "CES0600000001"),
            "service_providing": _parse_series_data(result["results"], "CES0800000001"),
            "retail_trade": _parse_series_data(result["results"], "CES4142000001"),
            "information": _parse_series_data(result["results"], "CES5051000001"),
            "financial": _parse_series_data(result["results"], "CES5552000001"),
            "professional_business": _parse_series_data(result["results"], "CES6054000001"),
            "health_care": _parse_series_data(result["results"], "CES6562000001"),
        }
    
    return parsed


def get_wages_data(months: int = 12) -> Dict:
    """
    Get Average Hourly Earnings (wage) data
    
    Args:
        months: Number of months to retrieve
    
    Returns:
        Dict with wage data by sector
    """
    end_year = datetime.now().year
    start_year = end_year - (months // 12 + 1)
    
    series_list = [
        "CES0500000003",  # Private
        "CES0000000003",  # Total Nonfarm
        "CES4142000003",  # Retail Trade
        "CES6562000003",  # Health Care
    ]
    
    result = fetch_bls_series(series_list, start_year, end_year)
    
    if result["status"] != "success":
        return result
    
    return {
        "timestamp": datetime.now().isoformat(),
        "private": _parse_series_data(result["results"], "CES0500000003"),
        "total_nonfarm": _parse_series_data(result["results"], "CES0000000003"),
        "retail_trade": _parse_series_data(result["results"], "CES4142000003"),
        "health_care": _parse_series_data(result["results"], "CES6562000003"),
    }


def get_productivity_data(years: int = 5) -> Dict:
    """
    Get Labor Productivity data
    
    Args:
        years: Number of years to retrieve (quarterly data)
    
    Returns:
        Dict with productivity and unit labor cost data
    """
    end_year = datetime.now().year
    start_year = end_year - years
    
    series_list = [
        "PRS85006092",  # Nonfarm Business Labor Productivity
        "PRS85006112",  # Nonfarm Business Unit Labor Costs
    ]
    
    result = fetch_bls_series(series_list, start_year, end_year)
    
    if result["status"] != "success":
        return result
    
    return {
        "timestamp": datetime.now().isoformat(),
        "labor_productivity": _parse_series_data(result["results"], "PRS85006092"),
        "unit_labor_costs": _parse_series_data(result["results"], "PRS85006112"),
    }


def get_inflation_summary() -> Dict:
    """
    Get comprehensive inflation summary with CPI, PPI, and wage growth
    """
    cpi_data = get_cpi_data(months=24, components=True)
    ppi_data = get_ppi_data(months=24)
    wage_data = get_wages_data(months=24)
    
    # Calculate year-over-year changes
    summary = {
        "timestamp": datetime.now().isoformat(),
        "cpi": _extract_latest_yoy(cpi_data.get("headline_cpi", {})),
        "core_cpi": _extract_latest_yoy(cpi_data.get("core_cpi", {})),
        "ppi": _extract_latest_yoy(ppi_data.get("final_demand", {})),
        "wages": _extract_latest_yoy(wage_data.get("private", {})),
        "cpi_components": {},
    }
    
    # Add CPI component inflation rates
    if "components" in cpi_data:
        for component, data in cpi_data["components"].items():
            summary["cpi_components"][component] = _extract_latest_yoy(data)
    
    # Calculate real wage growth (wage growth - CPI)
    if summary["wages"]["value"] and summary["cpi"]["value"]:
        summary["real_wage_growth"] = round(
            summary["wages"]["value"] - summary["cpi"]["value"], 2
        )
    
    return summary


def get_employment_summary() -> Dict:
    """
    Get comprehensive employment summary with NFP, unemployment, and labor market indicators
    """
    emp_data = get_employment_data(months=24, detailed=True)
    
    # Calculate month-over-month changes for NFP
    summary = {
        "timestamp": datetime.now().isoformat(),
        "nonfarm_payrolls": _extract_latest_mom(emp_data.get("total_nonfarm", {})),
        "unemployment_rate": _extract_latest(emp_data.get("unemployment_rate", {})),
        "labor_force_participation": _extract_latest(emp_data.get("labor_force_participation", {})),
        "sector_employment": {},
    }
    
    # Add sector employment changes
    if "sectors" in emp_data:
        for sector, data in emp_data["sectors"].items():
            summary["sector_employment"][sector] = _extract_latest_mom(data)
    
    return summary


def _parse_series_data(results: Dict, series_id: str) -> Dict:
    """
    Parse BLS series data from API response
    """
    series_data = results.get("series", [])
    
    for series in series_data:
        if series.get("seriesID") == series_id:
            observations = series.get("data", [])
            
            if not observations:
                return {"error": "No data available", "series_id": series_id}
            
            # Sort by year and period (latest first)
            observations.sort(key=lambda x: (x["year"], x["period"]), reverse=True)
            
            # Parse data points
            parsed_obs = []
            for obs in observations:
                try:
                    parsed_obs.append({
                        "date": f"{obs['year']}-{obs['period'].replace('M', '')}",
                        "value": float(obs["value"]),
                        "period": obs.get("period"),
                        "year": obs.get("year"),
                    })
                except (ValueError, KeyError):
                    continue
            
            return {
                "series_id": series_id,
                "series_name": BLS_SERIES.get(series_id, series_id),
                "latest": parsed_obs[0] if parsed_obs else None,
                "data": parsed_obs,
                "count": len(parsed_obs),
            }
    
    return {"error": "Series not found", "series_id": series_id}


def _extract_latest(series_data: Dict) -> Dict:
    """
    Extract latest value from series data
    """
    if "latest" in series_data and series_data["latest"]:
        return {
            "value": series_data["latest"]["value"],
            "date": series_data["latest"]["date"],
        }
    return {"value": None, "date": None}


def _extract_latest_yoy(series_data: Dict) -> Dict:
    """
    Extract latest value and calculate year-over-year change
    """
    if "data" in series_data and len(series_data["data"]) >= 13:
        latest = series_data["data"][0]
        year_ago = series_data["data"][12]
        
        yoy_change = ((latest["value"] - year_ago["value"]) / year_ago["value"]) * 100
        
        return {
            "value": round(yoy_change, 2),
            "current": latest["value"],
            "year_ago": year_ago["value"],
            "date": latest["date"],
        }
    
    return {"value": None, "date": None}


def _extract_latest_mom(series_data: Dict) -> Dict:
    """
    Extract latest value and calculate month-over-month change (in thousands for employment)
    """
    if "data" in series_data and len(series_data["data"]) >= 2:
        latest = series_data["data"][0]
        prev_month = series_data["data"][1]
        
        mom_change = latest["value"] - prev_month["value"]
        
        return {
            "value": round(mom_change, 1),
            "current": latest["value"],
            "prev_month": prev_month["value"],
            "date": latest["date"],
        }
    
    return {"value": None, "date": None}


# CLI Interface
def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "cpi":
        # Consumer Price Index
        components = "--components" in sys.argv or "-c" in sys.argv
        data = get_cpi_data(months=24, components=components)
        print(json.dumps(data, indent=2))
        
    elif command == "ppi":
        # Producer Price Index
        data = get_ppi_data(months=24)
        print(json.dumps(data, indent=2))
        
    elif command == "employment" or command == "nfp":
        # Non-Farm Payrolls & Employment
        detailed = "--detailed" in sys.argv or "-d" in sys.argv
        data = get_employment_data(months=24, detailed=detailed)
        print(json.dumps(data, indent=2))
        
    elif command == "wages":
        # Average Hourly Earnings
        data = get_wages_data(months=24)
        print(json.dumps(data, indent=2))
        
    elif command == "productivity":
        # Labor Productivity
        data = get_productivity_data(years=5)
        print(json.dumps(data, indent=2))
        
    elif command == "inflation-summary":
        # Comprehensive inflation summary
        data = get_inflation_summary()
        print(json.dumps(data, indent=2))
        
    elif command == "employment-summary":
        # Comprehensive employment summary
        data = get_employment_summary()
        print(json.dumps(data, indent=2))
        
    elif command == "dashboard":
        # Full BLS dashboard
        data = {
            "timestamp": datetime.now().isoformat(),
            "inflation": get_inflation_summary(),
            "employment": get_employment_summary(),
            "productivity": get_productivity_data(years=3),
        }
        print(json.dumps(data, indent=2))
        
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return 1
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
US Bureau of Labor Statistics Module (Phase 97)

Commands:
  python cli.py cpi [--components]          # Consumer Price Index (headline + core)
  python cli.py ppi                         # Producer Price Index
  python cli.py employment [--detailed]     # Non-Farm Payrolls & employment (alias: nfp)
  python cli.py wages                       # Average Hourly Earnings by sector
  python cli.py productivity                # Labor Productivity & Unit Labor Costs
  python cli.py inflation-summary           # Comprehensive inflation dashboard
  python cli.py employment-summary          # Comprehensive employment dashboard
  python cli.py dashboard                   # Full BLS dashboard (all data)

Options:
  --components, -c    # Include CPI component breakdown (food, housing, etc)
  --detailed, -d      # Include sector employment breakdown

Examples:
  python cli.py cpi --components           # CPI with food, housing, gasoline, etc
  python cli.py employment --detailed      # NFP with sector breakdown
  python cli.py inflation-summary          # Quick inflation snapshot
  python cli.py dashboard                  # Everything at once

Data Source:
  BLS Public Data API v2 (api.bls.gov/publicAPI/v2)
  No API key required (25 queries/day limit)
  Free registration: 500 queries/day + 10 years lookback

Release Schedule:
  - CPI: Mid-month (typically 13th-15th) for prior month
  - PPI: Mid-month (typically 14th-16th) for prior month
  - Employment Situation (NFP): First Friday of month for prior month
  - Productivity: Quarterly (prelim 6 weeks after quarter, revised 3 months later)
""")


if __name__ == "__main__":
    sys.exit(main())
