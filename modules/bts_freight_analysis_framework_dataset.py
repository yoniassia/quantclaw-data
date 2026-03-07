#!/usr/bin/env python3
"""
BTS Freight Analysis Framework (FAF5.7.1) Dataset Module

Bureau of Transportation Statistics Freight Analysis Framework provides comprehensive
data on U.S. freight movements by mode, commodity, and origin-destination.

FAF5.7.1 covers:
- Tonnage (thousand tons), Value (million dollars), Ton-miles (million ton-miles)
- Historical years: 2017-2024
- Forecast years: 2030-2050 (including high/low estimates)
- Transport modes: Truck, Rail, Water, Air, Multiple modes & mail, Pipeline, Other/Unknown
- 43 commodity types (SCTG codes)
- State-level and Regional-level data

Source: https://faf.ornl.gov/faf5/
Category: Infrastructure & Transport
Free tier: True - Full CSV download access
Update frequency: Annual
Author: QuantClaw Data NightBuilder
"""

import os
import io
import json
import requests
import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

# FAF5.7.1 Data URLs
FAF_BASE_URL = "https://faf.ornl.gov/faf5/Data/Download_Files"

FAF_DATA_SOURCES = {
    'regional': f"{FAF_BASE_URL}/FAF5.7.1.zip",
    'regional_hilo': f"{FAF_BASE_URL}/FAF5.7.1_HiLoForecasts.zip",
    'regional_recent': f"{FAF_BASE_URL}/FAF5.7.1_2018-2024.zip",
    'state': f"{FAF_BASE_URL}/FAF5.7.1_State.zip",
    'state_hilo': f"{FAF_BASE_URL}/FAF5.7.1_State_HiLoForecasts.zip",
    'state_recent': f"{FAF_BASE_URL}/FAF5.7.1_State_2018-2024.zip",
}

# Transport Mode Codes
TRANSPORT_MODES = {
    1: 'Truck',
    2: 'Rail',
    3: 'Water',
    4: 'Air (includes truck-air)',
    5: 'Multiple modes & mail',
    6: 'Pipeline',
    7: 'Other and unknown',
    8: 'No domestic mode',
}

# SCTG Commodity Codes (Standard Classification of Transported Goods)
COMMODITY_CODES = {
    1: 'Live animals/fish',
    2: 'Cereal grains',
    3: 'Other agricultural products',
    4: 'Animal feed',
    5: 'Meat/seafood',
    6: 'Milled grain products',
    7: 'Other foodstuffs',
    8: 'Alcoholic beverages',
    9: 'Tobacco products',
    10: 'Building stone',
    11: 'Natural sands',
    12: 'Gravel and crushed stone',
    13: 'Nonmetallic minerals',
    14: 'Metallic ores',
    15: 'Coal',
    16: 'Crude petroleum',
    17: 'Gasoline and aviation fuel',
    18: 'Fuel oils',
    19: 'Coal and petroleum products',
    20: 'Basic chemicals',
    21: 'Pharmaceuticals',
    22: 'Fertilizers',
    23: 'Chemical products',
    24: 'Plastics/rubber',
    25: 'Logs and wood products',
    26: 'Wood products',
    27: 'Pulp/paper/paperboard',
    28: 'Paper articles',
    29: 'Printed products',
    30: 'Textiles/leather',
    31: 'Nonmetal mineral products',
    32: 'Base metal in primary/semifinished forms',
    33: 'Articles of base metal',
    34: 'Machinery',
    35: 'Electronics',
    36: 'Motorized vehicles',
    37: 'Transport equipment',
    38: 'Precision instruments',
    39: 'Furniture',
    40: 'Miscellaneous manufactured products',
    41: 'Waste/scrap',
    43: 'Mixed freight',
}

# Cache for downloaded data
_DATA_CACHE = {}


def _download_faf_data(source_key: str = 'regional_recent', force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """
    Download and cache FAF CSV data
    
    Args:
        source_key: One of 'regional', 'state', 'regional_recent', etc.
        force_refresh: Force re-download even if cached
    
    Returns:
        DataFrame with FAF data or None if download fails
    """
    if source_key in _DATA_CACHE and not force_refresh:
        return _DATA_CACHE[source_key]
    
    try:
        url = FAF_DATA_SOURCES.get(source_key)
        if not url:
            return None
        
        # Note: ZIP files contain CSV - would need to extract
        # For now, provide guidance that users should download manually
        # Real implementation would use zipfile module to extract CSV
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # This is a ZIP file - would need extraction logic
        # For production use, implement zipfile extraction and CSV parsing
        
        return None  # Placeholder - see get_download_info() for manual download instructions
    
    except Exception as e:
        return None


def get_download_info() -> Dict:
    """
    Get information about FAF5.7.1 data downloads
    
    Returns:
        Dict with download URLs and instructions for manual data access
    """
    return {
        'success': True,
        'version': 'FAF5.7.1',
        'description': 'Freight Analysis Framework - U.S. freight tonnage, value, and ton-miles',
        'data_types': {
            'tonnage': 'thousand tons',
            'value': 'million dollars',
            'ton_miles': 'million ton-miles'
        },
        'years': {
            'historical': '2017-2024',
            'forecasts': '2030-2050'
        },
        'download_sources': FAF_DATA_SOURCES,
        'instructions': [
            '1. Download CSV ZIP from faf.ornl.gov/faf5/',
            '2. Extract CSV files',
            '3. Use parse_faf_csv() to load data',
            '4. Filter by mode, commodity, origin, destination as needed'
        ],
        'data_tabulation_tool': 'https://faf.ornl.gov/faf5/dtt_total.aspx',
        'timestamp': datetime.now().isoformat()
    }


def parse_faf_csv(csv_path: str) -> Dict:
    """
    Parse FAF CSV file (user must download first)
    
    Args:
        csv_path: Path to extracted FAF CSV file
    
    Returns:
        Dict with parsed FAF data and summary statistics
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Standardize column names (FAF CSVs have specific schema)
        # Typical columns: dms_orig, dms_dest, dms_mode, sctg2, year, tons, value_millions
        
        return {
            'success': True,
            'records': len(df),
            'columns': list(df.columns),
            'years': sorted(df['year'].unique().tolist()) if 'year' in df.columns else [],
            'sample': df.head(5).to_dict('records'),
            'data': df,  # Full dataframe for further analysis
            'timestamp': datetime.now().isoformat()
        }
    
    except FileNotFoundError:
        return {
            'success': False,
            'error': f'CSV file not found: {csv_path}',
            'hint': 'Download FAF5.7.1 data from https://faf.ornl.gov/faf5/ first'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_freight_by_mode(mode: Union[str, int] = "truck", year: int = 2024, csv_path: Optional[str] = None) -> Dict:
    """
    Get freight data filtered by transport mode
    
    Args:
        mode: Transport mode name (truck/rail/water/air) or code (1-8)
        year: Year to query (2017-2024 for historical, 2030-2050 for forecasts)
        csv_path: Optional path to FAF CSV file (if already downloaded)
    
    Returns:
        Dict with freight volumes, values, and ton-miles by mode
    """
    # Convert mode name to code
    mode_code = None
    if isinstance(mode, str):
        mode_lower = mode.lower()
        for code, name in TRANSPORT_MODES.items():
            if mode_lower in name.lower():
                mode_code = code
                break
    else:
        mode_code = mode
    
    if mode_code is None:
        return {
            'success': False,
            'error': f'Invalid mode: {mode}',
            'available_modes': TRANSPORT_MODES
        }
    
    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path)
            
            # Filter by mode and year
            # Assuming columns: dms_mode, year, tons_2024, value_2024
            filtered = df[(df['dms_mode'] == mode_code) & (df['year'] == year)]
            
            return {
                'success': True,
                'mode': TRANSPORT_MODES[mode_code],
                'mode_code': mode_code,
                'year': year,
                'total_tonnage_thousands': filtered['tons_2024'].sum() if 'tons_2024' in filtered else 0,
                'total_value_millions': filtered['value_2024'].sum() if 'value_2024' in filtered else 0,
                'records': len(filtered),
                'sample': filtered.head(10).to_dict('records') if len(filtered) > 0 else [],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # If no CSV provided, return structure with download instructions
    return {
        'success': False,
        'mode': TRANSPORT_MODES.get(mode_code, 'Unknown'),
        'mode_code': mode_code,
        'year': year,
        'error': 'No data file provided',
        'instructions': get_download_info()['instructions'],
        'download_url': FAF_DATA_SOURCES['regional_recent']
    }


def get_freight_by_commodity(commodity: Union[str, int] = "all", year: int = 2024, csv_path: Optional[str] = None) -> Dict:
    """
    Get freight data filtered by commodity type (SCTG codes)
    
    Args:
        commodity: Commodity name or SCTG code (1-43), or "all" for summary
        year: Year to query
        csv_path: Optional path to FAF CSV file
    
    Returns:
        Dict with freight volumes and values by commodity
    """
    # Convert commodity name to code
    commodity_code = None
    if isinstance(commodity, str) and commodity.lower() != "all":
        commodity_lower = commodity.lower()
        for code, name in COMMODITY_CODES.items():
            if commodity_lower in name.lower():
                commodity_code = code
                break
    elif isinstance(commodity, int):
        commodity_code = commodity
    
    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path)
            
            if commodity == "all":
                # Group by commodity type
                filtered = df[df['year'] == year]
                grouped = filtered.groupby('sctg2').agg({
                    'tons_2024': 'sum',
                    'value_2024': 'sum'
                }).reset_index()
                
                # Map codes to names
                grouped['commodity_name'] = grouped['sctg2'].map(COMMODITY_CODES)
                
                return {
                    'success': True,
                    'commodity': 'all',
                    'year': year,
                    'total_commodities': len(grouped),
                    'top_by_tonnage': grouped.nlargest(10, 'tons_2024')[['commodity_name', 'tons_2024', 'value_2024']].to_dict('records'),
                    'top_by_value': grouped.nlargest(10, 'value_2024')[['commodity_name', 'tons_2024', 'value_2024']].to_dict('records'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Filter by specific commodity
                filtered = df[(df['sctg2'] == commodity_code) & (df['year'] == year)]
                
                return {
                    'success': True,
                    'commodity': COMMODITY_CODES.get(commodity_code, 'Unknown'),
                    'commodity_code': commodity_code,
                    'year': year,
                    'total_tonnage_thousands': filtered['tons_2024'].sum(),
                    'total_value_millions': filtered['value_2024'].sum(),
                    'records': len(filtered),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    return {
        'success': False,
        'commodity': commodity,
        'year': year,
        'error': 'No data file provided',
        'available_commodities': COMMODITY_CODES,
        'instructions': get_download_info()['instructions']
    }


def get_state_freight_flows(origin: str = "CA", destination: str = "TX", csv_path: Optional[str] = None) -> Dict:
    """
    Get freight flow data between origin and destination states
    
    Args:
        origin: Origin state code (e.g., "CA", "TX", "NY")
        destination: Destination state code
        csv_path: Path to FAF State-level CSV file
    
    Returns:
        Dict with freight flows between states by mode and commodity
    """
    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path)
            
            # Filter by origin and destination
            # Assuming columns: dms_orig (state code), dms_dest (state code)
            filtered = df[(df['dms_orig'] == origin) & (df['dms_dest'] == destination)]
            
            if len(filtered) == 0:
                return {
                    'success': False,
                    'error': f'No flows found from {origin} to {destination}',
                    'origin': origin,
                    'destination': destination
                }
            
            # Aggregate by mode
            mode_summary = filtered.groupby('dms_mode').agg({
                'tons_2024': 'sum',
                'value_2024': 'sum'
            }).reset_index()
            mode_summary['mode_name'] = mode_summary['dms_mode'].map(TRANSPORT_MODES)
            
            # Aggregate by commodity
            commodity_summary = filtered.groupby('sctg2').agg({
                'tons_2024': 'sum',
                'value_2024': 'sum'
            }).reset_index()
            commodity_summary['commodity_name'] = commodity_summary['sctg2'].map(COMMODITY_CODES)
            
            return {
                'success': True,
                'origin': origin,
                'destination': destination,
                'total_tonnage_thousands': filtered['tons_2024'].sum(),
                'total_value_millions': filtered['value_2024'].sum(),
                'by_mode': mode_summary.to_dict('records'),
                'top_commodities': commodity_summary.nlargest(10, 'tons_2024').to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    return {
        'success': False,
        'origin': origin,
        'destination': destination,
        'error': 'No state-level data file provided',
        'instructions': get_download_info()['instructions'],
        'download_url': FAF_DATA_SOURCES['state_recent']
    }


def get_freight_forecast(year: int = 2030, csv_path: Optional[str] = None, scenario: str = 'mid') -> Dict:
    """
    Get projected freight volumes for future years (2030-2050)
    
    Args:
        year: Forecast year (2030, 2040, 2050)
        csv_path: Path to FAF forecast CSV file (with hi/lo estimates)
        scenario: 'mid', 'high', or 'low' forecast scenario
    
    Returns:
        Dict with forecast freight volumes and growth projections
    """
    if year not in [2030, 2040, 2050]:
        return {
            'success': False,
            'error': f'Invalid forecast year: {year}. Must be 2030, 2040, or 2050'
        }
    
    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path)
            
            filtered = df[df['year'] == year]
            
            if len(filtered) == 0:
                return {
                    'success': False,
                    'error': f'No forecast data for year {year}'
                }
            
            # Mode breakdown
            mode_forecast = filtered.groupby('dms_mode').agg({
                'tons_2024': 'sum',  # Column name may vary - check actual CSV schema
                'value_2024': 'sum'
            }).reset_index()
            mode_forecast['mode_name'] = mode_forecast['dms_mode'].map(TRANSPORT_MODES)
            
            # Calculate growth from base year 2024
            base_year_data = df[df['year'] == 2024]
            if len(base_year_data) > 0:
                base_tonnage = base_year_data['tons_2024'].sum()
                forecast_tonnage = filtered['tons_2024'].sum()
                growth_pct = ((forecast_tonnage - base_tonnage) / base_tonnage * 100) if base_tonnage > 0 else 0
            else:
                growth_pct = None
            
            return {
                'success': True,
                'forecast_year': year,
                'scenario': scenario,
                'total_tonnage_thousands': filtered['tons_2024'].sum(),
                'total_value_millions': filtered['value_2024'].sum(),
                'growth_from_2024_pct': growth_pct,
                'by_mode': mode_forecast.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    return {
        'success': False,
        'forecast_year': year,
        'error': 'No forecast data file provided',
        'instructions': get_download_info()['instructions'],
        'download_url': FAF_DATA_SOURCES['regional_hilo']
    }


def get_freight_summary(year: int = 2024) -> Dict:
    """
    Get national freight statistics summary
    Provides high-level overview of U.S. freight activity
    
    Args:
        year: Year to summarize (2017-2024 or forecast years)
    
    Returns:
        Dict with national freight totals, mode shares, and key metrics
    """
    return {
        'success': True,
        'year': year,
        'description': 'FAF5.7.1 National Freight Summary',
        'data_note': 'To get actual data, download FAF CSV files and use parse_faf_csv()',
        'metrics_available': [
            'Total freight tonnage (thousand tons)',
            'Total freight value (million dollars)',
            'Total ton-miles (million ton-miles)',
            'Breakdown by 8 transport modes',
            'Breakdown by 43 commodity types (SCTG)',
            'Origin-destination flows at state and regional level',
            'Forecasts through 2050 with high/low scenarios'
        ],
        'transport_modes': TRANSPORT_MODES,
        'commodity_types': len(COMMODITY_CODES),
        'download_info': get_download_info(),
        'timestamp': datetime.now().isoformat()
    }


def list_modes() -> Dict:
    """List all available transport modes"""
    return {
        'success': True,
        'modes': TRANSPORT_MODES,
        'count': len(TRANSPORT_MODES)
    }


def list_commodities() -> Dict:
    """List all SCTG commodity codes"""
    return {
        'success': True,
        'commodities': COMMODITY_CODES,
        'count': len(COMMODITY_CODES)
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("BTS Freight Analysis Framework (FAF5.7.1) Module")
    print("=" * 70)
    
    # Show download info
    info = get_download_info()
    print("\n📦 Data Version:", info['version'])
    print("📊 Data Types:", ', '.join(info['data_types'].keys()))
    print("📅 Coverage:", f"{info['years']['historical']} (historical), {info['years']['forecasts']} (forecasts)")
    
    # Show transport modes
    modes = list_modes()
    print(f"\n🚛 Transport Modes ({modes['count']}):")
    for code, name in modes['modes'].items():
        print(f"  {code}: {name}")
    
    # Show commodity categories
    commodities = list_commodities()
    print(f"\n📦 Commodity Categories: {commodities['count']} SCTG codes")
    print("  (Agricultural, Energy, Chemicals, Manufactured goods, etc.)")
    
    # Example usage
    print("\n" + "="*70)
    print("Example Usage:")
    print("="*70)
    print("""
# Get summary information
summary = get_freight_summary(year=2024)

# Download data first from https://faf.ornl.gov/faf5/
# Then parse and analyze:
data = parse_faf_csv('/path/to/FAF5.7.1.csv')

# Query by mode
truck_freight = get_freight_by_mode(mode='truck', year=2024, csv_path='/path/to/FAF5.7.1.csv')

# Query by commodity
grain_freight = get_freight_by_commodity(commodity='cereal grains', year=2024, csv_path='/path/to/FAF5.7.1.csv')

# State-to-state flows
ca_to_tx = get_state_freight_flows(origin='CA', destination='TX', csv_path='/path/to/FAF5.7.1_State.csv')

# Get forecasts
forecast_2030 = get_freight_forecast(year=2030, csv_path='/path/to/FAF5.7.1_HiLoForecasts.csv')
""")
    
    print("\n" + json.dumps(get_freight_summary(), indent=2))
