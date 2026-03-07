#!/usr/bin/env python3
"""
ITC Trade Map API — International Trade Statistics
Mock implementation with sample data structure.

NOTE: UN Comtrade API requires subscription key for real data.
This module provides the interface and sample data to demonstrate structure.
Upgrade with API key when available at: https://comtradeapi.un.org

Country codes: ISO 3-letter (USA, CHN, DEU) or UN numeric (842, 156, 276)
"""

import json
from typing import Dict, List, Union
from datetime import datetime

# Common country code mappings (ISO-3 to UN numeric)
COUNTRY_CODES = {
    "USA": "842", "CHN": "156", "DEU": "276", "GBR": "826", "FRA": "250",
    "JPN": "392", "IND": "356", "BRA": "076", "CAN": "124", "RUS": "643",
    "KOR": "410", "MEX": "484", "ITA": "380", "ESP": "724", "AUS": "036"
}

# Sample trade data for demonstration
SAMPLE_BILATERAL_TRADE = {
    ("CHN", "USA", 2023): {"exports": 536_000_000_000, "imports": 147_000_000_000},
    ("USA", "CHN", 2023): {"exports": 147_000_000_000, "imports": 536_000_000_000},
    ("USA", "MEX", 2023): {"exports": 323_000_000_000, "imports": 475_000_000_000},
    ("DEU", "USA", 2023): {"exports": 158_000_000_000, "imports": 82_000_000_000},
}

SAMPLE_TOP_EXPORTS = {
    ("USA", 2023): [
        {"code": "27", "name": "Mineral fuels, oils", "value": 253_000_000_000},
        {"code": "84", "name": "Machinery, nuclear reactors", "value": 206_000_000_000},
        {"code": "85", "name": "Electrical machinery", "value": 178_000_000_000},
        {"code": "87", "name": "Vehicles", "value": 159_000_000_000},
        {"code": "88", "name": "Aircraft, spacecraft", "value": 140_000_000_000},
        {"code": "90", "name": "Optical, medical instruments", "value": 92_000_000_000},
        {"code": "30", "name": "Pharmaceutical products", "value": 71_000_000_000},
        {"code": "39", "name": "Plastics", "value": 66_000_000_000},
        {"code": "29", "name": "Organic chemicals", "value": 54_000_000_000},
        {"code": "12", "name": "Oil seeds", "value": 47_000_000_000},
    ],
    ("CHN", 2023): [
        {"code": "85", "name": "Electrical machinery", "value": 1_080_000_000_000},
        {"code": "84", "name": "Machinery, nuclear reactors", "value": 890_000_000_000},
        {"code": "94", "name": "Furniture, lighting", "value": 140_000_000_000},
        {"code": "95", "name": "Toys, games, sports", "value": 110_000_000_000},
        {"code": "87", "name": "Vehicles", "value": 105_000_000_000},
        {"code": "39", "name": "Plastics", "value": 95_000_000_000},
        {"code": "73", "name": "Iron or steel articles", "value": 92_000_000_000},
        {"code": "90", "name": "Optical, medical instruments", "value": 88_000_000_000},
        {"code": "61", "name": "Knitted apparel", "value": 82_000_000_000},
        {"code": "62", "name": "Woven apparel", "value": 79_000_000_000},
    ]
}

SAMPLE_TOP_IMPORTS = {
    ("USA", 2023): [
        {"code": "85", "name": "Electrical machinery", "value": 487_000_000_000},
        {"code": "84", "name": "Machinery, nuclear reactors", "value": 436_000_000_000},
        {"code": "87", "name": "Vehicles", "value": 388_000_000_000},
        {"code": "27", "name": "Mineral fuels, oils", "value": 267_000_000_000},
        {"code": "30", "name": "Pharmaceutical products", "value": 157_000_000_000},
        {"code": "90", "name": "Optical, medical instruments", "value": 111_000_000_000},
        {"code": "39", "name": "Plastics", "value": 82_000_000_000},
        {"code": "94", "name": "Furniture, lighting", "value": 79_000_000_000},
        {"code": "29", "name": "Organic chemicals", "value": 73_000_000_000},
        {"code": "95", "name": "Toys, games, sports", "value": 67_000_000_000},
    ]
}

SAMPLE_TRADE_BALANCE = {
    ("USA", 2023): {"exports": 2_019_000_000_000, "imports": 3_113_000_000_000},
    ("CHN", 2023): {"exports": 3_380_000_000_000, "imports": 2_560_000_000_000},
    ("DEU", 2023): {"exports": 1_688_000_000_000, "imports": 1_560_000_000_000},
}

def _normalize_country(country: Union[str, int]) -> str:
    """Convert country name/code to UN numeric code."""
    if isinstance(country, int):
        return str(country)
    country = str(country).upper().strip()
    if country in COUNTRY_CODES:
        return country  # Return ISO-3 for sample data lookups
    if country.isdigit():
        # Convert numeric to ISO-3 if possible
        for iso3, code in COUNTRY_CODES.items():
            if code == str(country):
                return iso3
    return country

def get_bilateral_trade(reporter: Union[str, int], partner: Union[str, int], year: int) -> Dict:
    """
    Get bilateral trade data between two countries.
    
    Args:
        reporter: Reporting country (ISO-3 or UN numeric code)
        partner: Partner country (ISO-3 or UN numeric code)
        year: Year (e.g., 2023)
    
    Returns:
        Dict with bilateral trade statistics (exports, imports, balance)
    """
    reporter_code = _normalize_country(reporter)
    partner_code = _normalize_country(partner)
    
    # Look up sample data
    key = (reporter_code, partner_code, year)
    if key in SAMPLE_BILATERAL_TRADE:
        data = SAMPLE_BILATERAL_TRADE[key]
        exports = data["exports"]
        imports = data["imports"]
    else:
        # Return zero values with note
        exports = 0
        imports = 0
    
    return {
        "reporter": reporter,
        "partner": partner,
        "year": year,
        "exports_usd": exports,
        "imports_usd": imports,
        "trade_balance_usd": exports - imports,
        "total_trade_usd": exports + imports,
        "note": "Sample data - requires UN Comtrade API key for real-time data"
    }

def get_top_exports(country: Union[str, int], year: int, limit: int = 10) -> List[Dict]:
    """
    Get top exported products for a country.
    
    Args:
        country: Country code (ISO-3 or UN numeric)
        year: Year (e.g., 2023)
        limit: Number of top products to return
    
    Returns:
        List of dicts with product code, description, and export value
    """
    country_code = _normalize_country(country)
    key = (country_code, year)
    
    if key in SAMPLE_TOP_EXPORTS:
        products = SAMPLE_TOP_EXPORTS[key][:limit]
        return [
            {
                "product_code": p["code"],
                "product_name": p["name"],
                "export_value_usd": p["value"]
            }
            for p in products
        ]
    
    return []

def get_top_imports(country: Union[str, int], year: int, limit: int = 10) -> List[Dict]:
    """
    Get top imported products for a country.
    
    Args:
        country: Country code (ISO-3 or UN numeric)
        year: Year (e.g., 2023)
        limit: Number of top products to return
    
    Returns:
        List of dicts with product code, description, and import value
    """
    country_code = _normalize_country(country)
    key = (country_code, year)
    
    if key in SAMPLE_TOP_IMPORTS:
        products = SAMPLE_TOP_IMPORTS[key][:limit]
        return [
            {
                "product_code": p["code"],
                "product_name": p["name"],
                "import_value_usd": p["value"]
            }
            for p in products
        ]
    
    return []

def get_trade_balance(country: Union[str, int], year: int) -> Dict:
    """
    Get overall trade balance for a country.
    
    Args:
        country: Country code (ISO-3 or UN numeric)
        year: Year (e.g., 2023)
    
    Returns:
        Dict with total exports, imports, and trade balance
    """
    country_code = _normalize_country(country)
    key = (country_code, year)
    
    if key in SAMPLE_TRADE_BALANCE:
        data = SAMPLE_TRADE_BALANCE[key]
        exports = data["exports"]
        imports = data["imports"]
    else:
        exports = 0
        imports = 0
    
    return {
        "country": country,
        "year": year,
        "total_exports_usd": exports,
        "total_imports_usd": imports,
        "trade_balance_usd": exports - imports,
        "total_trade_usd": exports + imports,
        "note": "Sample data - requires UN Comtrade API key for real-time data"
    }

def search_product(query: str) -> List[Dict]:
    """
    Search for HS commodity codes by keyword.
    
    Args:
        query: Search term (e.g., "vehicles", "electronics")
    
    Returns:
        List of matching product codes with descriptions
    """
    # HS code reference database (2-digit chapters)
    hs_codes = {
        "live animals": {"code": "01", "description": "Live animals"},
        "meat": {"code": "02", "description": "Meat and edible meat offal"},
        "fish": {"code": "03", "description": "Fish and crustaceans"},
        "dairy": {"code": "04", "description": "Dairy produce; eggs; honey"},
        "coffee": {"code": "09", "description": "Coffee, tea, spices"},
        "cereals": {"code": "10", "description": "Cereals"},
        "seeds": {"code": "12", "description": "Oil seeds and oleaginous fruits"},
        "chemicals": {"code": "28", "description": "Inorganic chemicals"},
        "organic": {"code": "29", "description": "Organic chemicals"},
        "pharmaceuticals": {"code": "30", "description": "Pharmaceutical products"},
        "fertilizers": {"code": "31", "description": "Fertilizers"},
        "plastics": {"code": "39", "description": "Plastics and articles thereof"},
        "rubber": {"code": "40", "description": "Rubber and articles thereof"},
        "wood": {"code": "44", "description": "Wood and articles of wood"},
        "paper": {"code": "48", "description": "Paper and paperboard"},
        "textiles": {"code": "50-63", "description": "Textiles and textile articles"},
        "footwear": {"code": "64", "description": "Footwear"},
        "glass": {"code": "70", "description": "Glass and glassware"},
        "iron": {"code": "72", "description": "Iron and steel"},
        "steel": {"code": "73", "description": "Articles of iron or steel"},
        "copper": {"code": "74", "description": "Copper and articles thereof"},
        "machinery": {"code": "84", "description": "Nuclear reactors, boilers, machinery"},
        "electronics": {"code": "85", "description": "Electrical machinery and equipment"},
        "electrical": {"code": "85", "description": "Electrical machinery and equipment"},
        "vehicles": {"code": "87", "description": "Vehicles other than railway"},
        "aircraft": {"code": "88", "description": "Aircraft, spacecraft"},
        "ships": {"code": "89", "description": "Ships, boats"},
        "optical": {"code": "90", "description": "Optical, medical instruments"},
        "furniture": {"code": "94", "description": "Furniture; lighting"},
        "toys": {"code": "95", "description": "Toys, games, sports equipment"},
        "oil": {"code": "27", "description": "Mineral fuels, oils"},
        "petroleum": {"code": "27", "description": "Mineral fuels, oils"},
        "gas": {"code": "27", "description": "Mineral fuels, oils"},
    }
    
    query_lower = query.lower().strip()
    results = []
    
    for keyword, data in hs_codes.items():
        if query_lower in keyword or keyword in query_lower:
            results.append({
                "code": data["code"],
                "description": data["description"]
            })
    
    if not results:
        return [{"code": "NONE", "description": f"No match for '{query}' - try broader terms"}]
    
    return results

# Module metadata
__version__ = "1.0.0"
__author__ = "NightBuilder"
__source__ = "ITC Trade Map / UN Comtrade (sample data)"
__note__ = "Mock implementation - requires UN Comtrade API subscription for live data"

if __name__ == "__main__":
    # Demo output
    print(json.dumps({
        "module": "itc_trade_map_api",
        "status": "active",
        "implementation": "sample_data",
        "note": "UN Comtrade API requires subscription key - using sample 2023 data",
        "functions": [
            "get_bilateral_trade",
            "get_top_exports",
            "get_top_imports",
            "get_trade_balance",
            "search_product"
        ],
        "sample_countries": list(COUNTRY_CODES.keys())
    }, indent=2))
