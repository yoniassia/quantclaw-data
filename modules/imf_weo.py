#!/usr/bin/env python3
"""
IMF World Economic Outlook (WEO) Module
GDP & CPI Forecasts for 190 Countries via IMF DataMapper API

Data Sources:
- IMF DataMapper API: https://www.imf.org/external/datamapper/api/v1/
- NGDP_RPCH: Real GDP Growth (%)
- PCPIPCH: CPI Inflation (%)  
- NGDPD: Nominal GDP (USD billions)
- PPPPC: GDP per capita, PPP (USD)
- LUR: Unemployment Rate (%)

Updated twice per year:
- April: Spring WEO release
- October: Fall WEO release

Covers 190+ countries with historical data (1980-) and projections (5 years ahead)

Author: QUANTCLAW DATA Build Agent
Phase: 95
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
from collections import defaultdict

# IMF DataMapper API Base URL
IMF_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

# WEO Indicator Mappings
IMF_INDICATORS = {
    "NGDP_RPCH": "Real GDP Growth (%)",
    "PCPIPCH": "CPI Inflation (%)",
    "NGDPD": "Nominal GDP (USD billions)",
    "PPPPC": "GDP per capita, PPP (USD)",
    "LUR": "Unemployment Rate (%)",
    "PCPI": "CPI (Index)",
    "GGR_NGDP": "General Government Revenue (% GDP)",
    "GGX_NGDP": "General Government Expenditure (% GDP)",
    "GGXCNL_NGDP": "General Government Net Lending/Borrowing (% GDP)",
    "BCA_NGDPD": "Current Account Balance (% GDP)"
}

# Common Country Groups
COUNTRY_GROUPS = {
    "g7": ["USA", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN"],
    "g20": ["USA", "CHN", "JPN", "DEU", "IND", "GBR", "FRA", "BRA", "ITA", "CAN", 
            "RUS", "KOR", "AUS", "MEX", "IDN", "TUR", "SAU", "ARG", "ZAF"],
    "brics": ["BRA", "RUS", "IND", "CHN", "ZAF"],
    "emerging": ["CHN", "IND", "BRA", "RUS", "MEX", "IDN", "TUR", "SAU", "ARG", "ZAF"],
    "developed": ["USA", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN", "AUS", "ESP", "NLD"],
    "asia": ["CHN", "JPN", "IND", "IDN", "KOR", "THA", "VNM", "PHL", "MYS", "SGP"],
    "europe": ["DEU", "GBR", "FRA", "ITA", "ESP", "NLD", "POL", "SWE", "BEL", "AUT"],
    "middle_east": ["SAU", "ARE", "TUR", "ISR", "IRN", "IRQ", "QAT", "KWT", "EGY"],
    "latin_america": ["BRA", "MEX", "ARG", "COL", "CHL", "PER", "VEN", "ECU"]
}

# ISO Country Code to Name Mapping (Common ones)
COUNTRY_NAMES = {
    "USA": "United States",
    "CHN": "China",
    "JPN": "Japan",
    "DEU": "Germany",
    "IND": "India",
    "GBR": "United Kingdom",
    "FRA": "France",
    "BRA": "Brazil",
    "ITA": "Italy",
    "CAN": "Canada",
    "RUS": "Russia",
    "KOR": "South Korea",
    "AUS": "Australia",
    "MEX": "Mexico",
    "IDN": "Indonesia",
    "TUR": "Turkey",
    "SAU": "Saudi Arabia",
    "ARG": "Argentina",
    "ZAF": "South Africa",
    "ISR": "Israel",
    "SGP": "Singapore",
    "POL": "Poland",
    "ESP": "Spain",
    "NLD": "Netherlands",
    "CHE": "Switzerland",
    "SWE": "Sweden",
    "NOR": "Norway",
    "DNK": "Denmark",
    "BEL": "Belgium",
    "AUT": "Austria",
    "ARE": "United Arab Emirates",
    "QAT": "Qatar",
    "KWT": "Kuwait",
    "EGY": "Egypt",
    "NGA": "Nigeria"
}


def fetch_imf_indicator(indicator: str, timeout: int = 15) -> Dict:
    """
    Fetch data for a specific IMF WEO indicator
    
    Args:
        indicator: IMF indicator code (e.g., NGDP_RPCH, PCPIPCH)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with country-year data
    """
    try:
        url = f"{IMF_BASE_URL}/{indicator}"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            if "values" in data and indicator in data["values"]:
                return {
                    "indicator": indicator,
                    "name": IMF_INDICATORS.get(indicator, indicator),
                    "data": data["values"][indicator],
                    "countries": len(data["values"][indicator]),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "error": f"Failed to fetch {indicator}",
            "status_code": response.status_code
        }
    
    except Exception as e:
        return {"error": str(e), "indicator": indicator}


def get_country_data(country_code: str, indicators: List[str] = None) -> Dict:
    """
    Get all WEO data for a specific country
    
    Args:
        country_code: ISO 3-letter country code (e.g., USA, CHN, DEU)
        indicators: List of indicator codes to fetch (default: GDP growth + CPI)
        
    Returns:
        Comprehensive country economic outlook
    """
    if indicators is None:
        indicators = ["NGDP_RPCH", "PCPIPCH", "NGDPD", "PPPPC", "LUR"]
    
    country_code = country_code.upper()
    country_name = COUNTRY_NAMES.get(country_code, country_code)
    
    result = {
        "country": country_name,
        "code": country_code,
        "indicators": {},
        "timestamp": datetime.now().isoformat()
    }
    
    for indicator in indicators:
        data = fetch_imf_indicator(indicator)
        if "data" in data and country_code in data["data"]:
            country_series = data["data"][country_code]
            
            # Sort years
            years = sorted([int(y) for y in country_series.keys()])
            current_year = datetime.now().year
            
            # Split into historical and projections
            historical = {str(y): country_series[str(y)] for y in years if y <= current_year}
            projections = {str(y): country_series[str(y)] for y in years if y > current_year}
            
            result["indicators"][indicator] = {
                "name": data["name"],
                "current": country_series.get(str(current_year)),
                "latest_actual": historical[max(historical.keys())] if historical else None,
                "latest_year": max(historical.keys()) if historical else None,
                "projections": projections,
                "historical": {str(y): country_series[str(y)] for y in years[-10:] if y <= current_year},
                "full_data": country_series
            }
    
    return result


def compare_countries(country_codes: List[str], indicator: str = "NGDP_RPCH", 
                     year: Optional[int] = None) -> Dict:
    """
    Compare multiple countries on a specific indicator
    
    Args:
        country_codes: List of ISO country codes
        indicator: IMF indicator code
        year: Specific year to compare (default: current year)
        
    Returns:
        Comparative analysis across countries
    """
    if year is None:
        year = datetime.now().year
    
    data = fetch_imf_indicator(indicator)
    
    if "data" not in data:
        return {"error": "Failed to fetch indicator data"}
    
    comparisons = []
    for code in country_codes:
        code = code.upper()
        if code in data["data"]:
            country_data = data["data"][code]
            value = country_data.get(str(year))
            
            comparisons.append({
                "country": COUNTRY_NAMES.get(code, code),
                "code": code,
                "value": value,
                "year": year
            })
    
    # Sort by value
    comparisons.sort(key=lambda x: x["value"] if x["value"] is not None else -999, reverse=True)
    
    return {
        "indicator": data["name"],
        "indicator_code": indicator,
        "year": year,
        "countries": len(comparisons),
        "comparison": comparisons,
        "timestamp": datetime.now().isoformat()
    }


def get_global_outlook(indicator: str = "NGDP_RPCH", year: Optional[int] = None,
                      top_n: int = 20) -> Dict:
    """
    Get global economic outlook - top and bottom performers
    
    Args:
        indicator: IMF indicator code
        year: Year to analyze (default: current year)
        top_n: Number of top/bottom countries to show
        
    Returns:
        Global economic snapshot
    """
    if year is None:
        year = datetime.now().year
    
    data = fetch_imf_indicator(indicator)
    
    if "data" not in data:
        return {"error": "Failed to fetch indicator data"}
    
    # Extract all countries with data for this year
    countries_data = []
    for code, country_series in data["data"].items():
        value = country_series.get(str(year))
        if value is not None:
            countries_data.append({
                "country": COUNTRY_NAMES.get(code, code),
                "code": code,
                "value": value
            })
    
    # Sort
    countries_data.sort(key=lambda x: x["value"], reverse=True)
    
    return {
        "indicator": data["name"],
        "indicator_code": indicator,
        "year": year,
        "total_countries": len(countries_data),
        "top_performers": countries_data[:top_n],
        "bottom_performers": countries_data[-top_n:],
        "median": countries_data[len(countries_data)//2]["value"] if countries_data else None,
        "timestamp": datetime.now().isoformat()
    }


def get_group_outlook(group: str, indicator: str = "NGDP_RPCH",
                     years: Optional[List[int]] = None) -> Dict:
    """
    Get economic outlook for a country group (G7, G20, BRICS, etc.)
    
    Args:
        group: Group name (g7, g20, brics, emerging, developed, etc.)
        indicator: IMF indicator code
        years: List of years to analyze (default: last 3 years + next 2)
        
    Returns:
        Group economic outlook with time series
    """
    group = group.lower()
    
    if group not in COUNTRY_GROUPS:
        return {"error": f"Unknown group: {group}. Available: {', '.join(COUNTRY_GROUPS.keys())}"}
    
    country_codes = COUNTRY_GROUPS[group]
    
    if years is None:
        current_year = datetime.now().year
        years = [current_year - 3, current_year - 2, current_year - 1, 
                current_year, current_year + 1, current_year + 2]
    
    data = fetch_imf_indicator(indicator)
    
    if "data" not in data:
        return {"error": "Failed to fetch indicator data"}
    
    # Build time series for each country
    group_data = []
    for code in country_codes:
        if code in data["data"]:
            country_series = {}
            for year in years:
                country_series[str(year)] = data["data"][code].get(str(year))
            
            group_data.append({
                "country": COUNTRY_NAMES.get(code, code),
                "code": code,
                "series": country_series
            })
    
    # Calculate group averages
    group_avg = {}
    for year in years:
        values = [country["series"][str(year)] for country in group_data 
                 if country["series"][str(year)] is not None]
        group_avg[str(year)] = round(sum(values) / len(values), 2) if values else None
    
    return {
        "group": group.upper(),
        "indicator": data["name"],
        "indicator_code": indicator,
        "countries": group_data,
        "group_average": group_avg,
        "years": years,
        "timestamp": datetime.now().isoformat()
    }


def get_projections(country_code: str, indicator: str = "NGDP_RPCH",
                   years_ahead: int = 5) -> Dict:
    """
    Get IMF projections for a country
    
    Args:
        country_code: ISO country code
        indicator: IMF indicator code
        years_ahead: Number of years ahead to project
        
    Returns:
        Historical data + projections
    """
    country_code = country_code.upper()
    data = fetch_imf_indicator(indicator)
    
    if "data" not in data or country_code not in data["data"]:
        return {"error": f"No data found for {country_code}"}
    
    country_series = data["data"][country_code]
    current_year = datetime.now().year
    
    # Get last 5 years historical
    historical = {}
    for y in range(current_year - 5, current_year + 1):
        if str(y) in country_series:
            historical[str(y)] = country_series[str(y)]
    
    # Get projections
    projections = {}
    for y in range(current_year + 1, current_year + years_ahead + 1):
        if str(y) in country_series:
            projections[str(y)] = country_series[str(y)]
    
    return {
        "country": COUNTRY_NAMES.get(country_code, country_code),
        "code": country_code,
        "indicator": data["name"],
        "indicator_code": indicator,
        "historical": historical,
        "projections": projections,
        "current_year": current_year,
        "timestamp": datetime.now().isoformat()
    }


def search_countries(query: str) -> List[Dict]:
    """
    Search for countries by name or code
    
    Args:
        query: Search query (name or code)
        
    Returns:
        List of matching countries
    """
    query = query.lower()
    matches = []
    
    for code, name in COUNTRY_NAMES.items():
        if query in name.lower() or query in code.lower():
            matches.append({"code": code, "name": name})
    
    return matches


# ==================== CLI COMMANDS ====================

def cmd_country(args):
    """Get WEO data for a specific country"""
    if not args:
        print("Usage: imf-country <country_code> [indicators...]")
        print("Example: imf-country USA")
        print("Example: imf-country CHN NGDP_RPCH PCPIPCH")
        return
    
    country_code = args[0]
    indicators = args[1:] if len(args) > 1 else None
    
    data = get_country_data(country_code, indicators)
    print(json.dumps(data, indent=2))


def cmd_compare(args):
    """Compare countries on an indicator"""
    if len(args) < 2:
        print("Usage: imf-compare <indicator> <country1> <country2> [country3...] [year]")
        print("Example: imf-compare NGDP_RPCH USA CHN JPN")
        print("Example: imf-compare PCPIPCH USA CHN 2025")
        return
    
    indicator = args[0]
    
    # Check if last arg is a year
    year = None
    try:
        if args[-1].isdigit() and len(args[-1]) == 4:
            year = int(args[-1])
            country_codes = args[1:-1]
        else:
            country_codes = args[1:]
    except:
        country_codes = args[1:]
    
    data = compare_countries(country_codes, indicator, year)
    print(json.dumps(data, indent=2))


def cmd_global(args):
    """Get global economic outlook"""
    indicator = args[0] if args else "NGDP_RPCH"
    year = int(args[1]) if len(args) > 1 else None
    top_n = int(args[2]) if len(args) > 2 else 20
    
    data = get_global_outlook(indicator, year, top_n)
    print(json.dumps(data, indent=2))


def cmd_group(args):
    """Get outlook for country groups"""
    if not args:
        print("Usage: imf-group <group> [indicator]")
        print(f"Available groups: {', '.join(COUNTRY_GROUPS.keys())}")
        print("Example: imf-group g7")
        print("Example: imf-group brics PCPIPCH")
        return
    
    group = args[0]
    indicator = args[1] if len(args) > 1 else "NGDP_RPCH"
    
    data = get_group_outlook(group, indicator)
    print(json.dumps(data, indent=2))


def cmd_projections(args):
    """Get IMF projections for a country"""
    if not args:
        print("Usage: imf-projections <country_code> [indicator] [years_ahead]")
        print("Example: imf-projections USA")
        print("Example: imf-projections CHN PCPIPCH 5")
        return
    
    country_code = args[0]
    indicator = args[1] if len(args) > 1 else "NGDP_RPCH"
    years_ahead = int(args[2]) if len(args) > 2 else 5
    
    data = get_projections(country_code, indicator, years_ahead)
    print(json.dumps(data, indent=2))


def cmd_search(args):
    """Search for countries"""
    if not args:
        print("Usage: imf-search <query>")
        print("Example: imf-search korea")
        return
    
    query = " ".join(args)
    matches = search_countries(query)
    print(json.dumps(matches, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("IMF World Economic Outlook Module")
        print("\nAvailable commands:")
        print("  imf-country <code>           - Get country economic outlook")
        print("  imf-compare <ind> <c1> <c2>  - Compare countries")
        print("  imf-global [indicator]       - Global outlook rankings")
        print("  imf-group <group>            - Group outlook (g7, g20, brics)")
        print("  imf-projections <code>       - GDP/CPI projections")
        print("  imf-search <query>           - Search countries")
        print("\nIndicators:")
        for code, name in IMF_INDICATORS.items():
            print(f"  {code:20s} - {name}")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "imf-country": cmd_country,
        "imf-compare": cmd_compare,
        "imf-global": cmd_global,
        "imf-group": cmd_group,
        "imf-projections": cmd_projections,
        "imf-search": cmd_search
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
