#!/usr/bin/env python3
"""
USDA Quick Stats API - Agricultural Commodities Data

Provides crop production, prices, yields, livestock inventory, and county-level data from USDA NASS Quick Stats.
Free access (limited without API key).

Source: https://quickstats.nass.usda.gov/api/api_GET/
Category: Agriculture Commodities
Free tier: Yes (USDA_API_KEY optional for basic queries)
Update frequency: Weekly/monthly/annual reports
Author: QuantClaw Data NightBuilder
Phase: Implementation
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

USDA_BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
USDA_API_KEY = os.environ.get("USDA_NASS_API_KEY", "") or os.environ.get("USDA_API_KEY", "")

def query(params: Dict[str, str]) -> List[Dict]:
    """
    Core query function for USDA Quick Stats API.
    
    Args:
        params: Dict of API parameters (e.g., {'commodity_desc': 'CORN', 'statisticcat_desc': 'PRICE'})
    
    Returns:
        List of data records as dicts.
    
    Raises:
        ValueError: On API errors or network issues.
    """
    url = USDA_BASE_URL
    p = params.copy()
    p["key"] = USDA_API_KEY
    p["format"] = "JSON"
    
    try:
        resp = requests.get(url, params=p, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(f"API error: {data['error']}")
        return data.get("data", [])
    except requests.RequestException as e:
        raise ValueError(f"Request failed: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Parse failed: {str(e)}")

def get_crop_prices(commodity: str = 'CORN', year: Optional[int] = None) -> List[Dict]:
    """
    Get commodity prices.
    
    Args:
        commodity: e.g., 'CORN', 'SOYBEANS'
        year: Optional filter year
    
    Returns:
        List of price records.
    """
    params = {'commodity_desc': commodity, 'statisticcat_desc': 'PRICE'}
    if year:
        params['year'] = str(year)
    params['sort_by'] = 'year,DESC'
    return query(params)

def get_crop_production(commodity: str = 'CORN', year: Optional[int] = None) -> List[Dict]:
    """
    Get crop production volumes.
    """
    params = {'commodity_desc': commodity, 'statisticcat_desc': 'PRODUCTION'}
    if year:
        params['year'] = str(year)
    params['sort_by'] = 'year,DESC'
    return query(params)

def get_crop_yield(commodity: str = 'CORN', state: Optional[str] = None, year: Optional[int] = None) -> List[Dict]:
    """
    Get crop yield per acre.
    """
    params = {'commodity_desc': commodity, 'statisticcat_desc': 'YIELD'}
    if state:
        params['state_alpha'] = state.upper()
    if year:
        params['year'] = str(year)
    params['sort_by'] = 'year,DESC'
    return query(params)

def get_livestock_inventory(commodity: str = 'CATTLE', year: Optional[int] = None) -> List[Dict]:
    """
    Get livestock inventory.
    """
    params = {'commodity_desc': commodity, 'statisticcat_desc': 'INVENTORY'}
    if year:
        params['year'] = str(year)
    params['sort_by'] = 'year,DESC'
    return query(params)

def search_commodities(query: str) -> List[str]:
    """
    Search commodities matching query (partial match via API filter).
    """
    params = {'commodity_desc': query}
    data = query(params)
    commodities = {row.get('commodity_desc', '') for row in data}
    return sorted(list(commodities))

def get_county_data(commodity: str, state: str, county: Optional[str] = None) -> List[Dict]:
    """
    Get county-level data (defaults to yield).
    """
    params = {
        'commodity_desc': commodity,
        'state_alpha': state.upper(),
        'agg_level_desc': 'COUNTY',
        'statisticcat_desc': 'YIELD'
    }
    if county:
        params['county_name'] = county.title()
    params['sort_by'] = 'county_name,ASC'
    return query(params)

if __name__ == "__main__":
    print(json.dumps({
        "module": "usda_quick_stats_api",
        "status": "ready",
        "functions": ['query', 'get_crop_prices', 'get_crop_production', 'get_crop_yield', 'get_livestock_inventory', 'search_commodities', 'get_county_data'],
        "api_key_required": USDA_API_KEY != ""
    }, indent=2))
