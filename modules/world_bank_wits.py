#!/usr/bin/env python3
"""
World Bank WITS (World Integrated Trade Solution) Reference Data
Provides HS product codes, country mappings, and tariff indicators for trade analysis.

Note: Full WITS API requires specific SDMX query structure.
This module provides reference data for trade modeling.

Source: https://wits.worldbank.org/
Free tier: unlimited access to reference data
Update frequency: annual
"""

import json
from datetime import datetime, timezone
from typing import Dict, List

def get_hs_products() -> Dict:
    """
    Get Harmonized System (HS) product classification codes.
    
    Returns:
        Dict with HS2 product codes and descriptions
    """
    return {
        'product_codes': {
            '01': 'Live animals',
            '02': 'Meat and edible meat offal',
            '03': 'Fish and crustaceans',
            '04': 'Dairy, eggs, honey',
            '05': 'Animal products',
            '10': 'Cereals',
            '12': 'Oil seeds, grains',
            '15': 'Animal/vegetable fats and oils',
            '27': 'Mineral fuels, oils, petroleum',
            '28': 'Inorganic chemicals',
            '29': 'Organic chemicals',
            '30': 'Pharmaceutical products',
            '39': 'Plastics',
            '40': 'Rubber',
            '41': 'Raw hides and skins',
            '44': 'Wood',
            '47': 'Pulp, paper',
            '48': 'Paper products',
            '71': 'Pearls, precious stones, metals',
            '72': 'Iron and steel',
            '73': 'Articles of iron or steel',
            '74': 'Copper',
            '76': 'Aluminum',
            '84': 'Machinery, mechanical appliances',
            '85': 'Electrical machinery, equipment',
            '87': 'Vehicles',
            '88': 'Aircraft, spacecraft',
            '89': 'Ships, boats',
            '90': 'Optical, medical instruments',
            '94': 'Furniture, bedding',
            '95': 'Toys, games, sports equipment',
            '99': 'Special classifications'
        },
        'source': 'World Bank WITS',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def get_tariff_types() -> Dict:
    """
    Get common tariff measure types used in trade analysis.
    
    Returns:
        Dict with tariff type definitions
    """
    return {
        'tariff_types': {
            'MFN': 'Most Favored Nation - standard tariff rate',
            'BND': 'Bound Rate - WTO negotiated ceiling',
            'AHS': 'Applied Rate - actual rate in effect',
            'PFR': 'Preferential Rate - FTA/trade agreement rate',
            'AVE': 'Ad Valorem Equivalent - percentage of value',
            'AV': 'Ad Valorem - percentage duty',
            'SP': 'Specific - fixed amount per unit'
        },
        'indicators': {
            'MPRT-TRD-VL': 'Import Trade Value',
            'XPRT-TRD-VL': 'Export Trade Value',
            'RT-TRF-RT': 'Tariff Rate',
            'NTM-NMBR': 'Non-Tariff Measures Count'
        },
        'source': 'World Bank WITS',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def get_country_codes() -> List[Dict]:
    """
    Get ISO3 country codes for major trading nations.
    
    Returns:
        List of country code mappings
    """
    return [
        {'iso3': 'USA', 'name': 'United States', 'region': 'North America'},
        {'iso3': 'CHN', 'name': 'China', 'region': 'East Asia'},
        {'iso3': 'DEU', 'name': 'Germany', 'region': 'Europe'},
        {'iso3': 'GBR', 'name': 'United Kingdom', 'region': 'Europe'},
        {'iso3': 'FRA', 'name': 'France', 'region': 'Europe'},
        {'iso3': 'JPN', 'name': 'Japan', 'region': 'East Asia'},
        {'iso3': 'IND', 'name': 'India', 'region': 'South Asia'},
        {'iso3': 'BRA', 'name': 'Brazil', 'region': 'South America'},
        {'iso3': 'CAN', 'name': 'Canada', 'region': 'North America'},
        {'iso3': 'MEX', 'name': 'Mexico', 'region': 'North America'},
        {'iso3': 'KOR', 'name': 'South Korea', 'region': 'East Asia'},
        {'iso3': 'ITA', 'name': 'Italy', 'region': 'Europe'},
        {'iso3': 'ESP', 'name': 'Spain', 'region': 'Europe'},
        {'iso3': 'RUS', 'name': 'Russia', 'region': 'Eurasia'},
        {'iso3': 'AUS', 'name': 'Australia', 'region': 'Oceania'},
        {'iso3': 'NLD', 'name': 'Netherlands', 'region': 'Europe'},
        {'iso3': 'CHE', 'name': 'Switzerland', 'region': 'Europe'},
        {'iso3': 'SAU', 'name': 'Saudi Arabia', 'region': 'Middle East'},
        {'iso3': 'TUR', 'name': 'Turkey', 'region': 'Middle East'},
        {'iso3': 'IDN', 'name': 'Indonesia', 'region': 'Southeast Asia'}
    ]


def get_trade_indicators() -> Dict:
    """
    Get definitions of key trade analysis indicators.
    
    Returns:
        Dict with indicator definitions
    """
    return {
        'indicators': {
            'trade_balance': 'Exports - Imports',
            'trade_intensity': 'Bilateral trade / Total trade',
            'revealed_comparative_advantage': 'RCA index for product specialization',
            'import_penetration': 'Imports / (Domestic production + Imports - Exports)',
            'export_concentration': 'HHI of product export shares',
            'tariff_escalation': 'Tariff increase by processing stage',
            'effective_protection_rate': 'Protection net of input tariffs'
        },
        'use_cases': {
            'supply_chain': 'Model tariff impacts on supply chains',
            'trade_war': 'Analyze bilateral tariff escalation',
            'commodity_flow': 'Track product-level trade flows',
            'market_access': 'Evaluate tariff barriers to entry'
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def get_api_info() -> Dict:
    """
    Get WITS API access information.
    
    Returns:
        Dict with API details and endpoints
    """
    return {
        'base_url': 'https://wits.worldbank.org/API/V1/SDMX/V21/rest',
        'access': 'Free, no API key required for basic queries',
        'rate_limit': '50 calls per minute (recommended)',
        'format': 'SDMX-JSON',
        'note': 'API requires specific SDMX parameter combinations',
        'documentation': 'https://wits.worldbank.org/api-documentation.html',
        'alternative': 'Use World Bank Data API for aggregates',
        'coverage': 'Trade data from 1988-2022 (varies by country)',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def get_major_trade_pairs() -> List[Dict]:
    """
    Get list of major bilateral trade relationships for analysis.
    
    Returns:
        List of significant trade pairs
    """
    return [
        {'reporter': 'USA', 'partner': 'CHN', 'description': 'US-China trade (largest bilateral)'},
        {'reporter': 'USA', 'partner': 'MEX', 'description': 'US-Mexico (USMCA)'},
        {'reporter': 'USA', 'partner': 'CAN', 'description': 'US-Canada (USMCA)'},
        {'reporter': 'DEU', 'partner': 'FRA', 'description': 'Germany-France (EU core)'},
        {'reporter': 'CHN', 'partner': 'JPN', 'description': 'China-Japan (Asian trade)'},
        {'reporter': 'GBR', 'partner': 'DEU', 'description': 'UK-Germany (post-Brexit)'},
        {'reporter': 'USA', 'partner': 'JPN', 'description': 'US-Japan'},
        {'reporter': 'CHN', 'partner': 'KOR', 'description': 'China-Korea'},
    ]


if __name__ == "__main__":
    print("World Bank WITS Reference Data Module\n")
    
    # Test 1: HS Products
    print("1. HS Product Codes (sample):")
    products = get_hs_products()
    for code, desc in list(products['product_codes'].items())[:5]:
        print(f"  {code}: {desc}")
    print(f"  ... ({len(products['product_codes'])} total codes)\n")
    
    # Test 2: Tariff types
    print("2. Tariff Measure Types:")
    tariffs = get_tariff_types()
    for code, desc in list(tariffs['tariff_types'].items())[:3]:
        print(f"  {code}: {desc}")
    print()
    
    # Test 3: Countries
    print("3. Major Trading Nations (sample):")
    countries = get_country_codes()
    for c in countries[:5]:
        print(f"  {c['iso3']}: {c['name']}")
    print(f"  ... ({len(countries)} countries)\n")
    
    # Test 4: Trade pairs
    print("4. Major Trade Relationships:")
    pairs = get_major_trade_pairs()
    for p in pairs[:3]:
        print(f"  {p['reporter']}-{p['partner']}: {p['description']}")
    
    # Test 5: API info
    print("\n5. API Information:")
    api = get_api_info()
    print(json.dumps(api, indent=2))
