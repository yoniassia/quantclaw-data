"""
World Bank WITS API — Trade, Tariff & Supply Chain Data

Data Source: World Bank WITS (World Integrated Trade Solution)
Update: Quarterly (trade data typically lags 6-12 months)
Coverage: 180+ countries, 1988-present
Free: Yes (rate limited, no API key required)

Provides:
- Country trade metadata
- Trade data availability by country
- Bilateral trade indicators (limited by API restrictions)
- Country and partner information

API Format:
- Base: https://wits.worldbank.org/API/V1/wits/datasource/
- Returns: XML (parsed to dict)
- Reporter: 3-letter country code (USA, CHN, etc.)
- No authentication required

Usage Notes:
- Direct trade data endpoints have restrictions (403/Method not allowed)
- Country metadata and availability checks work
- For full trade data, use web interface or SDMX bulk downloads
- This module provides country lookup and metadata functions
"""

import requests
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
import json

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/wits")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://wits.worldbank.org/API/V1/wits/datasource"

# Country code mapping (common ones)
COUNTRY_CODES = {
    "usa": "USA", "us": "USA", "united states": "USA",
    "china": "CHN", "chn": "CHN",
    "germany": "DEU", "deu": "DEU",
    "japan": "JPN", "jpn": "JPN",
    "uk": "GBR", "gbr": "GBR", "united kingdom": "GBR",
    "india": "IND", "ind": "IND",
    "france": "FRA", "fra": "FRA",
    "canada": "CAN", "can": "CAN",
    "mexico": "MEX", "mex": "MEX",
    "brazil": "BRA", "bra": "BRA",
}

def _normalize_country(country: str) -> str:
    """Convert country name to 3-letter ISO code."""
    if len(country) == 3 and country.isupper():
        return country
    return COUNTRY_CODES.get(country.lower(), country.upper())

def _parse_xml_response(xml_string: str) -> Dict:
    """Parse WITS XML response to dictionary."""
    try:
        # Strip whitespace
        xml_string = xml_string.strip()
        
        root = ET.fromstring(xml_string)
        
        # Handle country metadata
        result = {
            "countries": [],
            "datasource": {},
            "raw_xml_preview": xml_string[:500] if len(xml_string) > 500 else xml_string
        }
        
        # Extract datasource attributes
        for key, value in root.attrib.items():
            clean_key = key.split('}')[-1] if '}' in key else key
            result["datasource"][clean_key] = value
        
        # Find country elements
        ns = {'wits': 'http://wits.worldbank.org'}
        countries = root.findall('.//wits:country', ns)
        
        for country in countries:
            country_data = {}
            
            # Get attributes
            for key, value in country.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                country_data[clean_key] = value
            
            # Get child elements
            iso3 = country.find('wits:iso3Code', ns)
            name = country.find('wits:name', ns)
            
            if iso3 is not None:
                country_data['iso3Code'] = iso3.text
            if name is not None:
                country_data['name'] = name.text
            
            if country_data:
                result["countries"].append(country_data)
        
        return result
        
    except ET.ParseError as e:
        return {
            "error": f"XML parse error: {str(e)}",
            "raw_preview": xml_string[:500]
        }

def get_country_info(country: str, datasource: str = "tradestats-trade") -> Dict:
    """
    Get country information from WITS database.
    
    Args:
        country: Country code (3-letter) or name
        datasource: Data source (default: tradestats-trade)
    
    Returns:
        Dict with country metadata and trade data availability
    
    Example:
        >>> get_country_info("USA")
        {'iso3Code': 'USA', 'name': 'United States', ...}
    """
    country = _normalize_country(country)
    
    cache_key = f"country_{datasource}_{country}.json"
    cache_file = os.path.join(CACHE_DIR, cache_key)
    
    # Check cache (country info doesn't change often)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < 30:  # Cache for 30 days
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/{datasource}/country/{country}"
        
        headers = {
            'User-Agent': 'QuantClaw/1.0 (Trade Analysis)'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Handle response encoding with BOM
        response.encoding = 'utf-8-sig'  # This automatically strips BOM
        
        result = _parse_xml_response(response.text)
        result["query"] = {
            "country": country,
            "datasource": datasource,
            "retrieved_at": datetime.now().isoformat()
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except requests.RequestException as e:
        return {
            "error": str(e),
            "country": country,
            "datasource": datasource
        }

def get_all_countries(datasource: str = "tradestats-trade") -> Dict:
    """
    Get list of all countries available in WITS database.
    
    Args:
        datasource: Data source (default: tradestats-trade)
    
    Returns:
        Dict with list of all available countries
    """
    cache_key = f"all_countries_{datasource}.json"
    cache_file = os.path.join(CACHE_DIR, cache_key)
    
    # Check cache
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < 30:
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/{datasource}/country/all"
        
        headers = {
            'User-Agent': 'QuantClaw/1.0 (Trade Analysis)'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Handle response encoding with BOM
        response.encoding = 'utf-8-sig'  # This automatically strips BOM
        
        result = _parse_xml_response(response.text)
        result["query"] = {
            "datasource": datasource,
            "retrieved_at": datetime.now().isoformat(),
            "total_countries": len(result.get("countries", []))
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except requests.RequestException as e:
        return {
            "error": str(e),
            "datasource": datasource
        }

def search_country(query: str) -> List[Dict]:
    """
    Search for countries by name or code.
    
    Args:
        query: Country name or code to search
    
    Returns:
        List of matching countries
    """
    all_data = get_all_countries()
    
    if "error" in all_data:
        return []
    
    countries = all_data.get("countries", [])
    query_lower = query.lower()
    
    matches = []
    for country in countries:
        name = country.get("name", "").lower()
        code = country.get("iso3Code", "").lower()
        
        if query_lower in name or query_lower in code:
            matches.append(country)
    
    return matches

def get_latest(country: str = "USA") -> Dict:
    """
    Get latest available information for a country.
    
    Args:
        country: Country code or name (default: USA)
    
    Returns:
        Country information with metadata
    """
    return get_country_info(country)

def get_trade_summary(country: str) -> Dict:
    """
    Get trade summary for a country (metadata and availability).
    
    Args:
        country: Country code or name
    
    Returns:
        Summary of trade data availability and country info
    """
    country_info = get_country_info(country)
    
    if "error" in country_info:
        return country_info
    
    countries = country_info.get("countries", [])
    if not countries:
        return {
            "error": "No country data found",
            "country": country
        }
    
    country_data = countries[0]
    
    summary = {
        "country": country_data.get("name", "Unknown"),
        "iso3Code": country_data.get("iso3Code", ""),
        "countrycode": country_data.get("countrycode", ""),
        "isreporter": country_data.get("isreporter") == "1",
        "ispartner": country_data.get("ispartner") == "1",
        "data_available": {
            "can_be_reporter": country_data.get("isreporter") == "1",
            "can_be_partner": country_data.get("ispartner") == "1"
        },
        "note": "Full trade data requires web interface access. API provides metadata only.",
        "retrieved_at": datetime.now().isoformat()
    }
    
    return summary

if __name__ == "__main__":
    # Test functions
    print("Testing World Bank WITS API module...")
    print("\n1. Get USA info:")
    print(json.dumps(get_country_info("USA"), indent=2)[:800])
    
    print("\n2. Search for China:")
    print(json.dumps(search_country("china"), indent=2))
    
    print("\n3. Get trade summary for Germany:")
    print(json.dumps(get_trade_summary("DEU"), indent=2))
