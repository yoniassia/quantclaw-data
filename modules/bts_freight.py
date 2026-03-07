#!/usr/bin/env python3
"""
Bureau of Transportation Statistics Freight API

U.S. freight transportation data including commodity flows, transborder shipments,
and modal volumes across truck, rail, air, and water. Supports analysis of U.S.
supply chain dynamics and infrastructure impacts.

Source: https://data.transportation.gov/browse?category=Freight
Category: Infrastructure & Transport
Free tier: True (Socrata Open Data API - no key required, higher limits with app token)
Author: QuantClaw Data NightBuilder
Phase: Night Build 2026-03-06
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

# Socrata API Configuration
BTS_BASE_URL = "https://data.bts.gov/resource"

# Key Dataset Endpoints
FREIGHT_INDICATORS = f"{BTS_BASE_URL}/h7pv-kjj5.json"  # Weekly freight indicators
SUPPLY_CHAIN_FREIGHT = f"{BTS_BASE_URL}/y5ut-ibwt.json"  # Supply chain & freight indicators
BORDER_CROSSING = f"{BTS_BASE_URL}/keg4-3bc2.json"  # Border crossing entry data (US-Canada/Mexico)

# Mode mappings
FREIGHT_MODES = {
    "truck": "Truck",
    "rail": "Rail",
    "water": "Water",
    "air": "Air",
    "pipeline": "Pipeline",
    "multimodal": "Multiple modes & mail",
    "other": "Other and unknown"
}


def _make_request(url: str, params: Optional[Dict] = None) -> List[Dict]:
    """
    Make request to BTS Socrata API with error handling.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        
    Returns:
        List of data records
        
    Raises:
        requests.exceptions.RequestException: On API errors
    """
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"BTS API request failed: {str(e)}")


def get_freight_summary(year: int = 2024) -> Dict[str, Union[str, Dict]]:
    """
    Get freight activity summary by transportation mode.
    
    Args:
        year: Year for data (default: 2024)
        
    Returns:
        Dict with year and activity by mode
        
    Example:
        >>> summary = get_freight_summary(2024)
        >>> print(summary['by_mode'])
    """
    try:
        # Query Supply Chain & Freight Indicators for latest year data
        params = {
            "$limit": 1000,
            "$where": f"year='{year}'",
            "$order": "date DESC"
        }
        
        data = _make_request(SUPPLY_CHAIN_FREIGHT, params)
        
        mode_data = {}
        indicators = {}
        
        for record in data:
            indicator = record.get('indicator', 'Unknown')
            value = float(record.get('value1', 0))
            source = record.get('source', 'BTS')
            
            if indicator not in indicators:
                indicators[indicator] = {
                    "latest_value": value,
                    "source": source,
                    "count": 0
                }
            indicators[indicator]["count"] += 1
        
        return {
            "year": year,
            "indicators": indicators,
            "record_count": len(data),
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Supply Chain & Freight Indicators"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "year": year,
            "message": "Failed to fetch freight summary"
        }


def get_commodity_flows(commodity: str = "all", year: int = 2024) -> Dict[str, Union[str, List]]:
    """
    Get freight indicator data filtered by type.
    
    Args:
        commodity: Indicator type filter (default: "all")
        year: Year for data (default: 2024)
        
    Returns:
        Dict with freight indicator records
        
    Example:
        >>> flows = get_commodity_flows("rail", 2024)
        >>> print(flows['records'][:5])
    """
    try:
        params = {
            "$limit": 500,
            "$where": f"year='{year}'",
            "$order": "date DESC"
        }
        
        if commodity != "all":
            params["$where"] += f" AND indicator LIKE '%{commodity}%'"
        
        data = _make_request(SUPPLY_CHAIN_FREIGHT, params)
        
        records = []
        for record in data:
            records.append({
                "date": record.get('date', 'Unknown'),
                "indicator": record.get('indicator', 'Unknown'),
                "measure": record.get('measure1_description', 'Unknown'),
                "value": float(record.get('value1', 0)),
                "units": record.get('units', ''),
                "source": record.get('source', 'BTS')
            })
        
        return {
            "filter": commodity,
            "year": year,
            "record_count": len(records),
            "records": records[:100],  # Limit to 100
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Supply Chain & Freight Indicators"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "filter": commodity,
            "year": year,
            "message": "Failed to fetch commodity flows"
        }


def get_transborder_freight(country: str = "canada", year: int = 2024) -> Dict[str, Union[str, List]]:
    """
    Get US-Canada or US-Mexico border crossing freight data.
    
    Args:
        country: "canada" or "mexico" (default: "canada")
        year: Year for data (default: 2024)
        
    Returns:
        Dict with border crossing records
        
    Example:
        >>> freight = get_transborder_freight("canada", 2024)
        >>> print(freight['total_crossings'])
    """
    try:
        border = "US-Canada Border" if country.lower() == "canada" else "US-Mexico Border"
        
        params = {
            "$limit": 1000,
            "$where": f"border='{border}' AND date >= '{year}-01-01T00:00:00.000' AND date < '{year+1}-01-01T00:00:00.000'",
            "$order": "value DESC"
        }
        
        data = _make_request(BORDER_CROSSING, params)
        
        records = []
        total_crossings = 0
        by_measure = {}
        
        for record in data:
            value = int(record.get('value', 0))
            measure = record.get('measure', 'Unknown')
            
            records.append({
                "port": record.get('port_name', 'Unknown'),
                "state": record.get('state', 'Unknown'),
                "measure": measure,
                "value": value,
                "date": record.get('date', '')
            })
            
            total_crossings += value
            by_measure[measure] = by_measure.get(measure, 0) + value
        
        return {
            "country": country,
            "border": border,
            "year": year,
            "total_crossings": total_crossings,
            "by_measure": by_measure,
            "record_count": len(records),
            "records": records[:100],  # Top 100
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Border Crossing Entry Data"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "country": country,
            "year": year,
            "message": "Failed to fetch transborder freight"
        }


def get_modal_comparison(modes: List[str] = ["truck", "rail", "air", "water"]) -> Dict[str, Union[str, List]]:
    """
    Compare freight activity across transportation modes using weekly indicators.
    
    Args:
        modes: List of modes to compare (default: ["truck", "rail", "air", "water"])
        
    Returns:
        Dict with modal comparison data
        
    Example:
        >>> comparison = get_modal_comparison(["truck", "rail"])
        >>> print(comparison['mode_stats'])
    """
    try:
        # Get latest week of data for all modes
        params = {
            "$limit": 1000,
            "$order": "week_ending DESC"
        }
        
        data = _make_request(FREIGHT_INDICATORS, params)
        
        mode_stats = {}
        latest_week = None
        
        for record in data:
            mode = record.get('mode', 'Unknown')
            indicator = record.get('indicator', 'Unknown')
            week_ending = record.get('week_ending', '')
            week_change = float(record.get('week_change', 0))
            
            if latest_week is None:
                latest_week = week_ending
            
            # Filter to requested modes (case-insensitive partial match)
            if any(m.lower() in mode.lower() for m in modes):
                key = f"{mode} - {indicator}"
                if key not in mode_stats:
                    mode_stats[key] = {
                        "mode": mode,
                        "indicator": indicator,
                        "week_change": week_change,
                        "week_ending": week_ending
                    }
        
        stats_list = list(mode_stats.values())
        
        return {
            "modes_compared": modes,
            "latest_week": latest_week,
            "mode_stats": stats_list,
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Freight Indicators (Weekly)"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "modes": modes,
            "message": "Failed to fetch modal comparison"
        }


def get_port_performance() -> Dict[str, Union[str, List]]:
    """
    Get border port performance metrics based on crossing volumes.
    
    Returns:
        Dict with port performance data
        
    Example:
        >>> ports = get_port_performance()
        >>> print(ports['top_ports'][:10])
    """
    try:
        # Get recent border crossing data grouped by port
        params = {
            "$limit": 2000,
            "$where": "date >= '2024-01-01T00:00:00.000'",
            "$select": "port_name,state,border,sum(value) as total_crossings",
            "$group": "port_name,state,border",
            "$order": "total_crossings DESC"
        }
        
        data = _make_request(BORDER_CROSSING, params)
        
        ports = []
        for record in data:
            ports.append({
                "port": record.get('port_name', 'Unknown'),
                "state": record.get('state', 'Unknown'),
                "border": record.get('border', 'Unknown'),
                "total_crossings": int(record.get('total_crossings', 0))
            })
        
        return {
            "year": 2024,
            "port_count": len(ports),
            "top_ports": ports[:50],  # Top 50 ports by volume
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Border Crossing Entry Data"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to fetch port performance"
        }


def get_freight_trends(start_year: int = 2019, end_year: int = 2025) -> Dict[str, Union[str, List]]:
    """
    Get historical freight trends across multiple years from weekly indicators.
    
    Args:
        start_year: Starting year (default: 2019)
        end_year: Ending year (default: 2025)
        
    Returns:
        Dict with yearly trend data
        
    Example:
        >>> trends = get_freight_trends(2020, 2024)
        >>> print(trends['yearly_data'])
    """
    try:
        # Use weekly freight indicators for historical trends
        params = {
            "$limit": 5000,
            "$order": "week_ending ASC"
        }
        
        data = _make_request(FREIGHT_INDICATORS, params)
        
        yearly_data = {}
        for record in data:
            week_ending = record.get('week_ending', '')
            if not week_ending:
                continue
                
            # Extract year from date string
            year = int(week_ending.split('-')[0]) if '-' in week_ending else 0
            
            if year < start_year or year > end_year:
                continue
            
            mode = record.get('mode', 'Unknown')
            indicator = record.get('indicator', 'Unknown')
            week_change = float(record.get('week_change', 0))
            
            if year not in yearly_data:
                yearly_data[year] = {
                    "year": year,
                    "modes": {},
                    "week_count": 0
                }
            
            yearly_data[year]["week_count"] += 1
            
            key = f"{mode} - {indicator}"
            if key not in yearly_data[year]["modes"]:
                yearly_data[year]["modes"][key] = {
                    "avg_change": 0,
                    "count": 0
                }
            
            yearly_data[year]["modes"][key]["avg_change"] += week_change
            yearly_data[year]["modes"][key]["count"] += 1
        
        # Calculate averages
        for year_data in yearly_data.values():
            for mode_data in year_data["modes"].values():
                if mode_data["count"] > 0:
                    mode_data["avg_change"] /= mode_data["count"]
        
        # Convert to sorted list
        trends = sorted(yearly_data.values(), key=lambda x: x['year'])
        
        return {
            "start_year": start_year,
            "end_year": end_year,
            "years_covered": len(trends),
            "yearly_data": trends,
            "timestamp": datetime.now().isoformat(),
            "source": "BTS Freight Indicators (Weekly)"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "start_year": start_year,
            "end_year": end_year,
            "message": "Failed to fetch freight trends"
        }


if __name__ == "__main__":
    print(json.dumps({
        "module": "bts_freight",
        "status": "active",
        "functions": [
            "get_freight_summary",
            "get_commodity_flows",
            "get_transborder_freight",
            "get_modal_comparison",
            "get_port_performance",
            "get_freight_trends"
        ],
        "source": "https://data.transportation.gov/browse?category=Freight",
        "api": "Socrata Open Data API",
        "free_tier": True
    }, indent=2))
