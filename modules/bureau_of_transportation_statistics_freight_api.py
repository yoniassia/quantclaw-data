#!/usr/bin/env python3
"""
Bureau of Transportation Statistics Freight API

Provides access to U.S. freight transportation data via BTS Socrata/SODA API.
Includes commodity flows, transborder freight, modal volumes, and port performance.
All data is freely available with no API key required.

Source: https://data.transportation.gov/browse?category=Freight
Category: Infrastructure & Transport
Free tier: True (fully free, no rate limits for public data)
Update frequency: Quarterly/Monthly depending on dataset
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# BTS Socrata API Configuration
BTS_BASE_URL = "https://data.transportation.gov/resource"
BTS_TIMEOUT = 30

# ========== BTS FREIGHT DATASET REGISTRY ==========

BTS_FREIGHT_DATASETS = {
    # International Freight (Air)
    'INTL_FREIGHT': {
        'id': 'udzf-9fvh',
        'name': 'International Passengers & Freight - All Types',
        'description': 'International air freight and passenger data by carrier, airport, and route',
        'fields': ['data_dte', 'year', 'month', 'usg_apt', 'fg_apt', 'carrier', 'type', 'total']
    },
    
    # Port Performance (Container TEU)
    'PORT_TEU': {
        'id': 'rd72-aq8r',
        'name': 'Monthly TEU Data',
        'description': 'Monthly container volumes (TEU) for major U.S. ports',
        'fields': ['port', 'charleston_sc', 'houston_tx', 'long_beach_ca', 'los_angeles_ca', 
                   'nwsa_seattle_tacoma_wa', 'oakland_ca', 'port_of_ny_nj', 'port_of_virginia_va', 'savannah_ga']
    },
    
    # Truck Freight
    'TRUCK_DATA': {
        'id': 'mt5m-skz3',
        'name': 'Truck Size and Weight Enforcement Data',
        'description': 'Truck weighing and enforcement statistics by state',
        'fields': ['year', 'state', 'vehicles_weighed_fixed', 'vehicles_weighed_wim', 
                   'overweight_violation_current_year', 'non_divisible_trip_permits']
    },
    
    # Monthly Transportation Statistics
    'MONTHLY_STATS': {
        'id': 'crem-w557',
        'name': 'Monthly Transportation Statistics',
        'description': 'Comprehensive monthly transportation economic indicators',
        'fields': ['date', 'index', 'general_economic_indicators']
    },
    
    # Transportation Services Index
    'TSI': {
        'id': 'bw6n-ddqk',
        'name': 'Transportation Services Index',
        'description': 'Seasonally-adjusted transportation services index',
        'fields': ['date', 'index', 'value']
    }
}


def _make_request(dataset_id: str, params: Optional[Dict] = None) -> Union[List[Dict], Dict]:
    """
    Make request to BTS Socrata API
    
    Args:
        dataset_id: Socrata dataset identifier
        params: Query parameters (SoQL supported)
        
    Returns:
        JSON response as list or dict
        
    Raises:
        requests.RequestException: On API errors
    """
    url = f"{BTS_BASE_URL}/{dataset_id}.json"
    
    try:
        response = requests.get(url, params=params, timeout=BTS_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"BTS API request failed: {str(e)}",
            "dataset_id": dataset_id
        }


def get_freight_commodity_flows(year: Optional[int] = None, commodity: Optional[str] = None, 
                                 limit: int = 1000) -> List[Dict]:
    """
    Get international air freight commodity flow data
    
    Args:
        year: Filter by year (e.g., 2023)
        commodity: Filter by carrier or route
        limit: Maximum records to return (default 1000)
        
    Returns:
        List of freight flow records with carrier, route, volume data
    """
    dataset_id = BTS_FREIGHT_DATASETS['INTL_FREIGHT']['id']
    params = {'$limit': limit}
    
    # Build SoQL where clause
    where_clauses = ["type='Freight'"]
    
    if year:
        where_clauses.append(f"year='{year}'")
    
    if commodity:
        where_clauses.append(f"carrier LIKE '%{commodity}%'")
    
    if where_clauses:
        params['$where'] = ' AND '.join(where_clauses)
    
    params['$order'] = 'data_dte DESC'
    
    return _make_request(dataset_id, params)


def get_transborder_freight(country: Optional[str] = None, mode: Optional[str] = None,
                            year: Optional[int] = None, limit: int = 1000) -> List[Dict]:
    """
    Get U.S. transborder freight statistics (international air freight data)
    
    Args:
        country: Filter by foreign country airport code
        mode: Filter by carrier type
        year: Filter by year
        limit: Maximum records to return (default 1000)
        
    Returns:
        List of transborder freight records
    """
    dataset_id = BTS_FREIGHT_DATASETS['INTL_FREIGHT']['id']
    params = {'$limit': limit}
    
    where_clauses = ["type='Freight'"]
    
    if year:
        where_clauses.append(f"year='{year}'")
    
    if country:
        where_clauses.append(f"fg_apt LIKE '%{country}%'")
    
    if mode:
        where_clauses.append(f"carrier LIKE '%{mode}%'")
    
    if where_clauses:
        params['$where'] = ' AND '.join(where_clauses)
    
    params['$order'] = 'data_dte DESC'
    
    return _make_request(dataset_id, params)


def get_freight_by_mode(mode: Optional[str] = None, year: Optional[int] = None,
                        limit: int = 1000) -> List[Dict]:
    """
    Get freight volume by transport mode (truck/rail/water/air)
    
    Args:
        mode: Transport mode - 'truck', 'air', etc.
        year: Filter by year
        limit: Maximum records to return (default 1000)
        
    Returns:
        List of modal freight volume records
    """
    if mode and mode.lower() == 'truck':
        # Use truck enforcement data
        dataset_id = BTS_FREIGHT_DATASETS['TRUCK_DATA']['id']
        params = {'$limit': limit}
        
        if year:
            params['$where'] = f"year='{year}'"
        
        params['$order'] = 'year DESC, state ASC'
        
        return _make_request(dataset_id, params)
    
    else:
        # Use international air freight data for air mode
        dataset_id = BTS_FREIGHT_DATASETS['INTL_FREIGHT']['id']
        params = {'$limit': limit}
        
        where_clauses = ["type='Freight'"]
        
        if year:
            where_clauses.append(f"year='{year}'")
        
        params['$where'] = ' AND '.join(where_clauses)
        params['$order'] = 'data_dte DESC'
        
        return _make_request(dataset_id, params)


def get_port_performance(port: Optional[str] = None, start_date: Optional[str] = None,
                        limit: int = 100) -> List[Dict]:
    """
    Get port performance metrics (container TEU volumes)
    
    Args:
        port: Port name (e.g., 'los_angeles_ca', 'port_of_ny_nj')
        start_date: Filter from date (YYYY-MM-DD)
        limit: Maximum records to return (default 100)
        
    Returns:
        List of port performance records with TEU volumes
    """
    dataset_id = BTS_FREIGHT_DATASETS['PORT_TEU']['id']
    params = {'$limit': limit}
    
    if start_date:
        params['$where'] = f"port >= '{start_date}'"
    
    params['$order'] = 'port DESC'
    
    data = _make_request(dataset_id, params)
    
    # If specific port requested, filter the data
    if port and isinstance(data, list):
        port_field = port.lower().replace(' ', '_').replace('-', '_')
        filtered = []
        for record in data:
            if port_field in record:
                filtered.append({
                    'date': record.get('port'),
                    'port': port,
                    'teu': record.get(port_field)
                })
        return filtered
    
    return data


def list_freight_datasets() -> List[Dict]:
    """
    List available BTS freight datasets
    
    Returns:
        List of dataset metadata with IDs, names, descriptions
    """
    datasets = []
    for key, info in BTS_FREIGHT_DATASETS.items():
        datasets.append({
            'key': key,
            'id': info['id'],
            'name': info['name'],
            'description': info['description'],
            'fields': info['fields'],
            'url': f"{BTS_BASE_URL}/{info['id']}.json"
        })
    return datasets


def get_transportation_index(start_date: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Get Transportation Services Index (TSI) data
    
    Args:
        start_date: Filter from date (YYYY-MM-DD)
        limit: Maximum records to return (default 100)
        
    Returns:
        List of TSI records
    """
    dataset_id = BTS_FREIGHT_DATASETS['TSI']['id']
    params = {'$limit': limit}
    
    if start_date:
        params['$where'] = f"date >= '{start_date}'"
    
    params['$order'] = 'date DESC'
    
    return _make_request(dataset_id, params)


def get_monthly_statistics(start_date: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Get monthly transportation statistics
    
    Args:
        start_date: Filter from date (YYYY-MM-DD)
        limit: Maximum records to return (default 100)
        
    Returns:
        List of monthly statistics records
    """
    dataset_id = BTS_FREIGHT_DATASETS['MONTHLY_STATS']['id']
    params = {'$limit': limit}
    
    if start_date:
        params['$where'] = f"date >= '{start_date}T00:00:00.000'"
    
    params['$order'] = 'date DESC'
    
    return _make_request(dataset_id, params)


# Module metadata
__version__ = "1.0.0"
__author__ = "QuantClaw Data NightBuilder"
__source__ = "https://data.transportation.gov/browse?category=Freight"

if __name__ == "__main__":
    # Demo usage
    print(json.dumps({
        "module": "bureau_of_transportation_statistics_freight_api",
        "version": __version__,
        "status": "active",
        "datasets": len(BTS_FREIGHT_DATASETS),
        "functions": [
            "get_freight_commodity_flows",
            "get_transborder_freight",
            "get_freight_by_mode",
            "get_port_performance",
            "list_freight_datasets",
            "get_transportation_index",
            "get_monthly_statistics"
        ]
    }, indent=2))
