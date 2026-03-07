#!/usr/bin/env python3
"""
BLS Public Data API — Labor Statistics & Economic Indicators

The U.S. Bureau of Labor Statistics provides access to comprehensive labor market data 
including employment, unemployment, wages, productivity, and price indices.

Specialized module for:
- Unemployment rates (national, state, demographic)
- Nonfarm payrolls and employment
- Consumer Price Index (CPI) and inflation
- Labor force participation rates
- Productivity and costs
- Job openings and labor turnover (JOLTS)

Source: https://www.bls.gov/developers/
Category: Labor & Demographics
Free tier: True (25 queries/day without key, 500/day with registration)
Update frequency: Monthly, Quarterly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# BLS API Configuration
BLS_BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_API_KEY = os.environ.get("BLS_API_KEY", "")

# ========== BLS SERIES REGISTRY ==========

BLS_SERIES = {
    # ===== UNEMPLOYMENT =====
    'UNEMPLOYMENT': {
        'LNS14000000': 'Unemployment Rate (Seasonally Adjusted)',
        'LNS14000001': 'Unemployment Rate - Men',
        'LNS14000002': 'Unemployment Rate - Women',
        'LNS14000003': 'Unemployment Rate - 16-19 years',
        'LNS14000006': 'Unemployment Rate - White',
        'LNS14000009': 'Unemployment Rate - Black or African American',
        'LNS14032183': 'Unemployment Rate - Asian',
        'LNS14000012': 'Unemployment Rate - Hispanic or Latino',
    },
    
    # ===== EMPLOYMENT & PAYROLLS =====
    'EMPLOYMENT': {
        'CES0000000001': 'Total Nonfarm Employment (Seasonally Adjusted)',
        'CES0500000001': 'Total Private Employment',
        'CES0600000001': 'Goods-Producing Employment',
        'CES0700000001': 'Service-Providing Employment',
        'CES0800000001': 'Private Service-Providing Employment',
        'LNS12000000': 'Employment Level (Household Survey)',
        'LNS11300000': 'Labor Force Level',
    },
    
    # ===== CONSUMER PRICE INDEX (CPI) =====
    'CPI': {
        'CUUR0000SA0': 'CPI-U: All Items (Urban Consumers, SA)',
        'CUUR0000SA0L1E': 'CPI-U: All Items Less Food and Energy (Core CPI)',
        'CUUR0000SAF': 'CPI-U: Food',
        'CUUR0000SAH': 'CPI-U: Housing',
        'CUUR0000SETB01': 'CPI-U: Gasoline (All Types)',
        'CUUR0000SAM': 'CPI-U: Medical Care',
        'CUUR0000SAE': 'CPI-U: Energy',
        'CUSR0000SA0': 'CPI-U: All Items (Not Seasonally Adjusted)',
    },
    
    # ===== LABOR FORCE PARTICIPATION =====
    'LABOR_FORCE': {
        'LNS11300000': 'Civilian Labor Force Level',
        'LNS11300001': 'Labor Force - Men',
        'LNS11300002': 'Labor Force - Women',
        'LNS11300012': 'Labor Force - Hispanic or Latino',
        'LNS11324230': 'Labor Force Participation Rate',
        'LNS11324887': 'Labor Force Participation Rate - Prime Age (25-54)',
    },
    
    # ===== PRODUCTIVITY =====
    'PRODUCTIVITY': {
        'PRS85006092': 'Nonfarm Business Sector: Labor Productivity',
        'PRS85006112': 'Nonfarm Business Sector: Unit Labor Costs',
        'PRS85006152': 'Nonfarm Business Sector: Real Compensation Per Hour',
        'PRS88003092': 'Manufacturing Sector: Labor Productivity',
    },
    
    # ===== JOB OPENINGS & LABOR TURNOVER (JOLTS) =====
    'JOLTS': {
        'JTS000000000000000JOL': 'Job Openings: Total Nonfarm',
        'JTS000000000000000HIL': 'Hires: Total Nonfarm',
        'JTS000000000000000TSL': 'Total Separations: Total Nonfarm',
        'JTS000000000000000QUL': 'Quits: Total Nonfarm',
        'JTS000000000000000LDL': 'Layoffs and Discharges: Total Nonfarm',
    },
}

# ========== CORE API FUNCTIONS ==========

def _make_bls_request(series_ids: List[str], start_year: Optional[str] = None, 
                      end_year: Optional[str] = None, catalog: bool = False) -> Dict:
    """
    Internal helper to make BLS API requests.
    
    Args:
        series_ids: List of BLS series IDs to fetch
        start_year: Starting year (YYYY format), defaults to 10 years ago
        end_year: Ending year (YYYY format), defaults to current year
        catalog: Include series catalog metadata
        
    Returns:
        Dictionary with BLS API response
    """
    if not start_year:
        start_year = str(datetime.now().year - 10)
    if not end_year:
        end_year = str(datetime.now().year)
    
    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
        "catalog": catalog
    }
    
    headers = {"Content-type": "application/json"}
    
    # Add API key if available
    if BLS_API_KEY:
        payload["registrationkey"] = BLS_API_KEY
    
    try:
        response = requests.post(BLS_BASE_URL, 
                                data=json.dumps(payload),
                                headers=headers,
                                timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

def _parse_bls_series(data: Dict, series_id: str) -> List[Dict]:
    """
    Parse BLS API response into clean list of data points.
    
    Args:
        data: BLS API response dictionary
        series_id: Series ID to extract
        
    Returns:
        List of dictionaries with {year, period, value, date}
    """
    if data.get("status") != "REQUEST_SUCCEEDED":
        return []
    
    results = []
    for series in data.get("Results", {}).get("series", []):
        if series.get("seriesID") == series_id:
            for item in series.get("data", []):
                # Parse period (M01-M12, Q01-Q04, or A01 for annual)
                period = item.get("period", "")
                year = item.get("year", "")
                value = item.get("value", "")
                
                # Create approximate date
                if period.startswith("M"):
                    month = int(period[1:])
                    date_str = f"{year}-{month:02d}-01"
                elif period.startswith("Q"):
                    quarter = int(period[1:])
                    month = (quarter - 1) * 3 + 1
                    date_str = f"{year}-{month:02d}-01"
                else:
                    date_str = f"{year}-01-01"
                
                # Handle BLS missing value indicators ("-", empty string)
                parsed_value = None
                if value and value != "-":
                    try:
                        parsed_value = float(value)
                    except (ValueError, TypeError):
                        parsed_value = None
                
                results.append({
                    "date": date_str,
                    "year": year,
                    "period": period,
                    "value": parsed_value,
                    "footnotes": item.get("footnotes", [])
                })
    
    # Sort by date descending (newest first)
    results.sort(key=lambda x: x["date"], reverse=True)
    return results

# ========== PUBLIC API FUNCTIONS ==========

def get_unemployment_rate(start_year: Optional[str] = None, 
                         end_year: Optional[str] = None) -> Dict:
    """
    Get U.S. unemployment rate (seasonally adjusted).
    
    Args:
        start_year: Starting year (YYYY), defaults to 10 years ago
        end_year: Ending year (YYYY), defaults to current year
        
    Returns:
        Dictionary with unemployment rate data
    """
    series_id = "LNS14000000"
    data = _make_bls_request([series_id], start_year, end_year)
    
    return {
        "series_id": series_id,
        "title": "Unemployment Rate (Seasonally Adjusted)",
        "data": _parse_bls_series(data, series_id),
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }

def get_nonfarm_payrolls(start_year: Optional[str] = None,
                        end_year: Optional[str] = None) -> Dict:
    """
    Get total nonfarm employment (payrolls).
    
    Args:
        start_year: Starting year (YYYY), defaults to 10 years ago
        end_year: Ending year (YYYY), defaults to current year
        
    Returns:
        Dictionary with nonfarm payrolls data (in thousands)
    """
    series_id = "CES0000000001"
    data = _make_bls_request([series_id], start_year, end_year)
    
    return {
        "series_id": series_id,
        "title": "Total Nonfarm Employment (Thousands, SA)",
        "data": _parse_bls_series(data, series_id),
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }

def get_cpi_data(start_year: Optional[str] = None,
                end_year: Optional[str] = None,
                include_core: bool = True) -> Dict:
    """
    Get Consumer Price Index (CPI) data.
    
    Args:
        start_year: Starting year (YYYY), defaults to 10 years ago
        end_year: Ending year (YYYY), defaults to current year
        include_core: Also fetch core CPI (excluding food & energy)
        
    Returns:
        Dictionary with CPI data (headline and optionally core)
    """
    series_ids = ["CUUR0000SA0"]  # Headline CPI
    if include_core:
        series_ids.append("CUUR0000SA0L1E")  # Core CPI
    
    data = _make_bls_request(series_ids, start_year, end_year)
    
    result = {
        "headline": {
            "series_id": "CUUR0000SA0",
            "title": "CPI-U: All Items",
            "data": _parse_bls_series(data, "CUUR0000SA0")
        },
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }
    
    if include_core:
        result["core"] = {
            "series_id": "CUUR0000SA0L1E",
            "title": "CPI-U: All Items Less Food and Energy",
            "data": _parse_bls_series(data, "CUUR0000SA0L1E")
        }
    
    return result

def get_labor_force_participation(start_year: Optional[str] = None,
                                 end_year: Optional[str] = None) -> Dict:
    """
    Get labor force participation rate.
    
    Args:
        start_year: Starting year (YYYY), defaults to 10 years ago
        end_year: Ending year (YYYY), defaults to current year
        
    Returns:
        Dictionary with labor force participation rate
    """
    series_id = "LNS11324230"
    data = _make_bls_request([series_id], start_year, end_year)
    
    return {
        "series_id": series_id,
        "title": "Labor Force Participation Rate",
        "data": _parse_bls_series(data, series_id),
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }

def get_multiple_series(series_ids: List[str],
                       start_year: Optional[str] = None,
                       end_year: Optional[str] = None) -> Dict:
    """
    Fetch multiple BLS series in a single request.
    
    Args:
        series_ids: List of BLS series IDs (max 25 without API key)
        start_year: Starting year (YYYY), defaults to 10 years ago
        end_year: Ending year (YYYY), defaults to current year
        
    Returns:
        Dictionary with data for each series
    """
    data = _make_bls_request(series_ids, start_year, end_year)
    
    result = {
        "series": {},
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }
    
    for series_id in series_ids:
        result["series"][series_id] = _parse_bls_series(data, series_id)
    
    return result

def get_latest_release(series_id: str = "LNS14000000") -> Dict:
    """
    Get the most recent data point for a series.
    
    Args:
        series_id: BLS series ID, defaults to unemployment rate
        
    Returns:
        Dictionary with latest data point
    """
    # Fetch just the current year
    current_year = str(datetime.now().year)
    data = _make_bls_request([series_id], current_year, current_year)
    
    parsed = _parse_bls_series(data, series_id)
    
    return {
        "series_id": series_id,
        "latest": parsed[0] if parsed else None,
        "source": "BLS",
        "fetched_at": datetime.now().isoformat()
    }

# ========== UTILITY FUNCTIONS ==========

def list_series(category: Optional[str] = None) -> Dict:
    """
    List available BLS series IDs.
    
    Args:
        category: Filter by category (UNEMPLOYMENT, EMPLOYMENT, CPI, etc.)
        
    Returns:
        Dictionary of series by category
    """
    if category:
        category_upper = category.upper()
        if category_upper in BLS_SERIES:
            return {category_upper: BLS_SERIES[category_upper]}
        else:
            return {"error": f"Category '{category}' not found"}
    
    return BLS_SERIES

# ========== MAIN / TESTING ==========

if __name__ == "__main__":
    # Quick test - fetch latest unemployment rate
    result = get_latest_release("LNS14000000")
    print(json.dumps(result, indent=2))
