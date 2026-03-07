#!/usr/bin/env python3
"""
Climate TRACE Emissions Dataset API

Global greenhouse gas emissions tracking from sectors like power, oil & gas, transportation.
Asset-level granularity for financial analysis of carbon markets and ESG investments.

Source: https://api.climatetrace.org/
Category: ESG & Climate
Free tier: True - Public API with usage limits of 500 requests per day
Update frequency: Quarterly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

# Climate TRACE API Configuration
BASE_URL = "https://api.climatetrace.org/v6"
TIMEOUT = 15

# Known sectors from API exploration
KNOWN_SECTORS = [
    'aluminum', 'electricity-generation', 'forest-land-clearing',
    'forest-land-fires', 'iron-and-steel', 'oil-and-gas-production',
    'oil-and-gas-transport', 'residential-onsite-fuel-usage',
    'road-transportation', 'shrubgrass-fires', 'power'
]

# ISO3 country codes (subset of common countries)
KNOWN_COUNTRIES = [
    'USA', 'CHN', 'IND', 'RUS', 'JPN', 'DEU', 'GBR', 'FRA', 'BRA', 'CAN',
    'SAU', 'ARE', 'QAT', 'KWT', 'IRQ', 'OMN', 'NGA', 'VEN', 'LBY', 'AGO'
]


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to Climate TRACE API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        Exception: On HTTP errors or invalid responses
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")


def get_global_emissions_summary(year: Optional[int] = None) -> Dict:
    """
    Get global total emissions summary across all countries and sectors.
    
    Args:
        year: Year for emissions data (e.g., 2023). Note: API currently returns
              latest available data regardless of year parameter.
              
    Returns:
        Dict with keys:
            - country: 'all'
            - emissions: Dict with co2, ch4, n2o, co2e_100yr, co2e_20yr
            - worldEmissions: Global totals
            - emissionsChange: Year-over-year changes (if available)
            - assetCount: Number of tracked assets
            
    Example:
        >>> data = get_global_emissions_summary(2023)
        >>> print(f"Global CO2: {data['emissions']['co2']:,.0f} tonnes")
    """
    params = {}
    if year:
        params['year'] = year
        
    data = _make_request("/country/emissions", params)
    return {
        'country': data.get('country', 'all'),
        'continent': data.get('continent'),
        'emissions': data.get('emissions', {}),
        'worldEmissions': data.get('worldEmissions', {}),
        'emissionsChange': data.get('emissionsChange', {}),
        'assetCount': data.get('assetCount'),
        'rank': data.get('rank'),
        'year': year
    }


def get_country_emissions(country_code: str = 'USA', year: Optional[int] = None) -> Dict:
    """
    Get emissions data for a specific country.
    
    Note: Current API limitation - endpoint returns global totals regardless of
    country_code parameter. Use get_asset_emissions() for country-specific data.
    
    Args:
        country_code: ISO3 country code (e.g., 'USA', 'CHN', 'GBR')
        year: Year for emissions data (optional)
        
    Returns:
        Dict with emissions data (currently global totals)
        
    Example:
        >>> data = get_country_emissions('USA', 2023)
        >>> print(data['emissions']['co2'])
    """
    params = {'iso3': country_code.upper()}
    if year:
        params['year'] = year
        
    data = _make_request("/country/emissions", params)
    return {
        'requested_country': country_code.upper(),
        'returned_data': data.get('country', 'all'),
        'emissions': data.get('emissions', {}),
        'worldEmissions': data.get('worldEmissions', {}),
        'year': year,
        'note': 'API currently returns global totals. Use get_asset_emissions() for country-specific data.'
    }


def get_asset_emissions(asset_type: Optional[str] = None, 
                       country: Optional[str] = None,
                       sector: Optional[str] = None,
                       limit: int = 100) -> Dict:
    """
    Get asset-level emissions data with optional filters.
    
    This is the primary endpoint for granular emissions data by country and sector.
    
    Args:
        asset_type: Type of asset (e.g., 'power-plants', 'refineries')
        country: ISO3 country code (e.g., 'USA')
        sector: Sector name (e.g., 'electricity-generation', 'oil-and-gas-production')
        limit: Max number of assets to return (default 100)
        
    Returns:
        Dict with keys:
            - bbox: Bounding box coordinates
            - assets: List of asset objects with emissions data
            - asset_count: Number of assets returned
            - filters_applied: Dict of filters used
            
    Example:
        >>> # Get US power sector emissions
        >>> data = get_asset_emissions(country='USA', sector='electricity-generation', limit=50)
        >>> for asset in data['assets'][:5]:
        ...     print(f"{asset['Name']}: {asset['EmissionsSummary'][0]['EmissionsQuantity']:,.0f}")
    """
    params = {}
    if country:
        params['country'] = country.upper()
    if sector:
        params['sector'] = sector.lower()
    if asset_type:
        params['asset_type'] = asset_type.lower()
    if limit:
        params['limit'] = limit
        
    data = _make_request("/assets", params)
    
    assets = data.get('assets', [])
    
    return {
        'bbox': data.get('bbox'),
        'assets': assets,
        'asset_count': len(assets),
        'filters_applied': {
            'country': country,
            'sector': sector,
            'asset_type': asset_type,
            'limit': limit
        },
        'retrieved_at': datetime.now(timezone.utc).isoformat()
    }


def get_sector_emissions(sector: str = 'power', year: Optional[int] = None, 
                        limit: int = 100) -> Dict:
    """
    Get emissions data aggregated by sector across all countries.
    
    Args:
        sector: Sector name (e.g., 'electricity-generation', 'oil-and-gas-production',
                'road-transportation', 'forest-land-clearing')
        year: Year for emissions data (optional, currently not used by API)
        limit: Max assets to retrieve for aggregation
        
    Returns:
        Dict with:
            - sector: Sector name
            - total_emissions: Aggregated emissions from assets
            - asset_count: Number of assets included
            - top_emitters: List of top emitting assets
            - year: Requested year
            
    Example:
        >>> data = get_sector_emissions('electricity-generation', 2023)
        >>> print(f"Total sector CO2e: {data['total_emissions']['co2e_100yr']:,.0f}")
    """
    # Normalize sector name
    sector_normalized = sector.lower().replace('power', 'electricity-generation')
    
    # Get assets for this sector
    asset_data = get_asset_emissions(sector=sector_normalized, limit=limit)
    assets = asset_data.get('assets', [])
    
    # Aggregate emissions
    total_emissions = {
        'co2': 0,
        'ch4': 0,
        'n2o': 0,
        'co2e_100yr': 0,
        'co2e_20yr': 0
    }
    
    top_emitters = []
    
    for asset in assets:
        # Extract emissions from EmissionsSummary
        for emission_entry in asset.get('EmissionsSummary', []):
            gas = emission_entry.get('Gas', '')
            quantity = emission_entry.get('EmissionsQuantity', 0)
            
            if gas in total_emissions:
                total_emissions[gas] += quantity
            
            if gas == 'co2e_100yr':
                top_emitters.append({
                    'name': asset.get('Name'),
                    'country': asset.get('Country'),
                    'emissions': quantity
                })
    
    # Sort top emitters
    top_emitters.sort(key=lambda x: x['emissions'], reverse=True)
    
    return {
        'sector': sector_normalized,
        'requested_sector': sector,
        'total_emissions': total_emissions,
        'asset_count': len(assets),
        'top_emitters': top_emitters[:10],
        'year': year,
        'retrieved_at': datetime.now(timezone.utc).isoformat()
    }


def list_sectors() -> List[str]:
    """
    List known available sectors in Climate TRACE database.
    
    Returns:
        List of sector names
        
    Example:
        >>> sectors = list_sectors()
        >>> print(f"Available sectors: {', '.join(sectors)}")
    """
    # Return known sectors from exploration + common mappings
    return sorted(KNOWN_SECTORS)


def list_countries() -> List[str]:
    """
    List known available countries in Climate TRACE database.
    
    Returns:
        List of ISO3 country codes
        
    Example:
        >>> countries = list_countries()
        >>> print(f"Tracked countries: {', '.join(countries[:10])}")
    """
    # Return known countries from exploration
    return sorted(KNOWN_COUNTRIES)


def get_country_sector_summary(country_code: str, sector: str, limit: int = 50) -> Dict:
    """
    Get emissions summary for a specific country and sector combination.
    
    Args:
        country_code: ISO3 country code (e.g., 'USA')
        sector: Sector name
        limit: Max assets to include
        
    Returns:
        Dict with filtered asset data and aggregated emissions
        
    Example:
        >>> data = get_country_sector_summary('USA', 'electricity-generation', 25)
        >>> print(f"US power sector: {data['total_emissions']['co2e_100yr']:,.0f} tonnes CO2e")
    """
    asset_data = get_asset_emissions(country=country_code, sector=sector, limit=limit)
    
    assets = asset_data.get('assets', [])
    
    # Aggregate emissions for this country-sector
    total_emissions = {
        'co2e_100yr': 0,
        'co2e_20yr': 0
    }
    
    for asset in assets:
        if asset.get('Country') == country_code.upper():
            for emission in asset.get('EmissionsSummary', []):
                gas = emission.get('Gas')
                if gas in total_emissions:
                    total_emissions[gas] += emission.get('EmissionsQuantity', 0)
    
    return {
        'country': country_code.upper(),
        'sector': sector,
        'total_emissions': total_emissions,
        'matching_assets': len([a for a in assets if a.get('Country') == country_code.upper()]),
        'assets': [a for a in assets if a.get('Country') == country_code.upper()][:10]
    }


# Convenience alias
get_emissions = get_global_emissions_summary


if __name__ == "__main__":
    # Test module
    print("=" * 60)
    print("Climate TRACE Emissions Dataset API - Test Run")
    print("=" * 60)
    
    try:
        # Test 1: Global emissions
        print("\n1. Global Emissions Summary:")
        global_data = get_global_emissions_summary(2023)
        print(f"   CO2: {global_data['emissions']['co2']:,.0f} tonnes")
        print(f"   CO2e (100yr): {global_data['emissions']['co2e_100yr']:,.0f} tonnes")
        
        # Test 2: List sectors
        print("\n2. Available Sectors:")
        sectors = list_sectors()
        print(f"   Found {len(sectors)} sectors: {', '.join(sectors[:5])}...")
        
        # Test 3: Sector emissions
        print("\n3. Electricity Generation Sector:")
        sector_data = get_sector_emissions('electricity-generation', limit=20)
        print(f"   Total CO2e: {sector_data['total_emissions']['co2e_100yr']:,.0f} tonnes")
        print(f"   Assets tracked: {sector_data['asset_count']}")
        if sector_data['top_emitters']:
            print(f"   Top emitter: {sector_data['top_emitters'][0]['name']}")
        
        # Test 4: Country list
        print("\n4. Available Countries:")
        countries = list_countries()
        print(f"   Tracked countries: {', '.join(countries[:10])}")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
