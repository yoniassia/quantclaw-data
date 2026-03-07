"""
Eurostat Comext API — EU International Trade Statistics

Data Source: European Commission Eurostat
Update: Monthly
History: 2000-present
Free: Yes (500 queries/day, no API key required)

Provides:
- EU trade flows (imports/exports) by partner country
- Trade balance data
- Product-level trade statistics (HS codes)
- Intra-EU and Extra-EU trade
- Monthly, quarterly, annual aggregations

API Documentation: https://ec.europa.eu/eurostat/web/main/data/web-services
Base URL: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/eurostat")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Working dataset codes (verified 2026-03-07)
DATASETS = {
    "ext_lt_maineu": "Extra-EU trade by partner (main partners)",
    "ext_lt_intratrd": "Intra-EU trade",
    "ext_st_eu27_2020": "EU27 trade since 2020",
    "bop_its6_det": "International trade in services",
    "nama_10_exi": "Exports by Member States",
    "nama_10_imi": "Imports by Member States"
}

# Major trading partners (country codes)
PARTNERS = {
    "US": "United States",
    "CN": "China",
    "GB": "United Kingdom",
    "CH": "Switzerland",
    "RU": "Russia",
    "JP": "Japan",
    "IN": "India",
    "BR": "Brazil",
    "CA": "Canada",
    "KR": "South Korea",
    "NO": "Norway",
    "TR": "Turkey"
}

def fetch_trade_data(
    dataset: str = "ext_lt_maineu",
    filters: Optional[Dict[str, str]] = None,
    format: str = "JSON",
    lang: str = "EN"
) -> Dict:
    """
    Fetch EU trade data from Eurostat API.
    
    Args:
        dataset: Dataset code (default: ext_lt_maineu)
        filters: Optional dict of filters (partner, time, product, etc.)
        format: Response format (JSON or XML)
        lang: Language code (EN, DE, FR, etc.)
    
    Returns:
        Dict with trade statistics
    """
    cache_key = f"{dataset}_{hash(str(filters))}.json"
    cache_file = os.path.join(CACHE_DIR, cache_key)
    
    # Check cache (valid for 7 days for trade data)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/{dataset}"
        params = {
            "format": format,
            "lang": lang
        }
        
        if filters:
            params.update(filters)
        
        headers = {
            'User-Agent': 'QuantClaw/1.0 (Trade Analytics)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Build result with metadata
        result = {
            "dataset": dataset,
            "dataset_label": data.get("label", ""),
            "source": data.get("source", "ESTAT"),
            "updated": data.get("updated", ""),
            "version": data.get("version", ""),
            "filters": filters,
            "fetched_at": datetime.now().isoformat(),
            "value_count": len(data.get("value", {})),
            "dimension": data.get("dimension", {}),
            "value": data.get("value", {}),
            "id": data.get("id", []),
            "size": data.get("size", [])
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "error": "Dataset not found",
                "dataset": dataset,
                "status_code": 404
            }
        elif e.response.status_code == 429:
            return {
                "error": "Rate limit exceeded (500 queries/day)",
                "status_code": 429
            }
        else:
            return {
                "error": f"HTTP error: {e}",
                "status_code": e.response.status_code
            }
    except Exception as e:
        return {
            "error": f"Failed to fetch data: {str(e)}",
            "dataset": dataset
        }

def get_extra_eu_trade(partner: Optional[str] = None) -> Dict:
    """
    Get Extra-EU trade data (trade with non-EU countries).
    
    Args:
        partner: Optional country code filter (e.g., "US", "CN")
    
    Returns:
        Dict with trade flows and balance
    """
    filters = {}
    if partner:
        filters["partner"] = partner
    
    try:
        data = fetch_trade_data(dataset="ext_lt_maineu", filters=filters)
        
        if "error" in data:
            return data
        
        # Extract summary statistics
        values = data.get("value", {})
        
        result = {
            "dataset": "Extra-EU Trade",
            "partner": partner,
            "updated": data.get("updated", ""),
            "data_points": len(values),
            "sample_values": dict(list(values.items())[:10]) if values else {},
            "dimensions": data.get("dimension", {}),
            "full_data": data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get Extra-EU trade: {str(e)}",
            "partner": partner
        }

def get_intra_eu_trade() -> Dict:
    """
    Get Intra-EU trade data (trade between EU member states).
    
    Returns:
        Dict with intra-EU trade statistics
    """
    try:
        data = fetch_trade_data(dataset="ext_lt_intratrd")
        
        if "error" in data:
            return data
        
        values = data.get("value", {})
        
        result = {
            "dataset": "Intra-EU Trade",
            "updated": data.get("updated", ""),
            "data_points": len(values),
            "sample_values": dict(list(values.items())[:10]) if values else {},
            "dimensions": data.get("dimension", {}),
            "full_data": data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get Intra-EU trade: {str(e)}"
        }

def get_eu_exports() -> Dict:
    """
    Get EU exports by member states.
    
    Returns:
        Dict with export statistics
    """
    try:
        data = fetch_trade_data(dataset="nama_10_exi")
        
        if "error" in data:
            return data
        
        values = data.get("value", {})
        
        result = {
            "dataset": "EU Exports by Member State",
            "updated": data.get("updated", ""),
            "data_points": len(values),
            "sample_values": dict(list(values.items())[:10]) if values else {},
            "full_data": data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get EU exports: {str(e)}"
        }

def get_eu_imports() -> Dict:
    """
    Get EU imports by member states.
    
    Returns:
        Dict with import statistics
    """
    try:
        data = fetch_trade_data(dataset="nama_10_imi")
        
        if "error" in data:
            return data
        
        values = data.get("value", {})
        
        result = {
            "dataset": "EU Imports by Member State",
            "updated": data.get("updated", ""),
            "data_points": len(values),
            "sample_values": dict(list(values.items())[:10]) if values else {},
            "full_data": data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get EU imports: {str(e)}"
        }

def get_trade_in_services() -> Dict:
    """
    Get international trade in services data.
    
    Returns:
        Dict with services trade statistics
    """
    try:
        data = fetch_trade_data(dataset="bop_its6_det")
        
        if "error" in data:
            return data
        
        values = data.get("value", {})
        
        result = {
            "dataset": "International Trade in Services",
            "updated": data.get("updated", ""),
            "data_points": len(values),
            "sample_values": dict(list(values.items())[:10]) if values else {},
            "full_data": data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get trade in services: {str(e)}"
        }

def search_datasets(keyword: str = "") -> List[Dict]:
    """
    List available Eurostat trade datasets.
    
    Args:
        keyword: Optional filter keyword
    
    Returns:
        List of available datasets
    """
    datasets_list = []
    
    for code, description in DATASETS.items():
        if not keyword or keyword.lower() in description.lower():
            datasets_list.append({
                "code": code,
                "description": description
            })
    
    return datasets_list

def get_partner_countries() -> List[Dict]:
    """
    Get list of major trading partner countries.
    
    Returns:
        List of partner countries with codes
    """
    return [
        {"code": code, "name": name}
        for code, name in PARTNERS.items()
    ]

# === CLI Commands ===

def cli_extra_eu(partner: Optional[str] = None):
    """Show Extra-EU trade data"""
    print("\n📊 Eurostat — Extra-EU Trade")
    print("=" * 70)
    
    data = get_extra_eu_trade(partner)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Dataset: {data['dataset']}")
        if partner:
            print(f"🌍 Partner: {PARTNERS.get(partner, partner)}")
        print(f"📅 Updated: {data.get('updated', 'N/A')}")
        print(f"📊 Data Points: {data.get('data_points', 0):,}")
        print(f"\n📋 Sample Values:")
        for key, value in list(data.get('sample_values', {}).items())[:5]:
            print(f"  {key}: {value}")

def cli_intra_eu():
    """Show Intra-EU trade data"""
    print("\n📊 Eurostat — Intra-EU Trade")
    print("=" * 70)
    
    data = get_intra_eu_trade()
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Dataset: {data['dataset']}")
        print(f"📅 Updated: {data.get('updated', 'N/A')}")
        print(f"📊 Data Points: {data.get('data_points', 0):,}")
        print(f"\n📋 Sample Values:")
        for key, value in list(data.get('sample_values', {}).items())[:5]:
            print(f"  {key}: {value}")

def cli_exports():
    """Show EU exports"""
    print("\n📊 Eurostat — EU Exports by Member State")
    print("=" * 70)
    
    data = get_eu_exports()
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Dataset: {data['dataset']}")
        print(f"📅 Updated: {data.get('updated', 'N/A')}")
        print(f"📊 Data Points: {data.get('data_points', 0):,}")

def cli_datasets():
    """List available datasets"""
    print("\n📚 Eurostat Trade Datasets")
    print("=" * 70)
    
    datasets = search_datasets()
    for ds in datasets:
        print(f"📊 {ds['code']}: {ds['description']}")

def cli_partners():
    """List major trading partners"""
    print("\n🌍 Major EU Trading Partners")
    print("=" * 70)
    
    partners = get_partner_countries()
    for p in partners:
        print(f"{p['code']}: {p['name']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "extra-eu":
            partner = sys.argv[2] if len(sys.argv) > 2 else None
            cli_extra_eu(partner)
        elif command == "intra-eu":
            cli_intra_eu()
        elif command == "exports":
            cli_exports()
        elif command == "datasets":
            cli_datasets()
        elif command == "partners":
            cli_partners()
        else:
            print("Usage: python eurostat_comext_api.py [extra-eu|intra-eu|exports|datasets|partners]")
    else:
        cli_extra_eu()
