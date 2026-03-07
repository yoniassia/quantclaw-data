#!/usr/bin/env python3
"""
BTS Transportation API — Bureau of Transportation Statistics

Access U.S. transportation data via Socrata Open Data API:
- Border Crossing Entry Data - vehicle/passenger/container counts at ports
- Transportation infrastructure and performance metrics

Source: https://data.bts.gov/
Category: Infrastructure & Transport
Free tier: True - No API key required, 1000 requests/hour throttle
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Socrata API base URL
BTS_BASE_URL = "https://data.bts.gov/resource"

# Dataset IDs (Socrata 4x4 identifiers)
DATASETS = {
    'border_crossings': 'keg4-3bc2',  # Border Crossing Entry Data
}

# US State abbreviations to full names mapping
STATE_NAMES = {
    'AZ': 'Arizona', 'CA': 'California', 'TX': 'Texas', 'NM': 'New Mexico',
    'MT': 'Montana', 'ND': 'North Dakota', 'MN': 'Minnesota', 'MI': 'Michigan',
    'NY': 'New York', 'VT': 'Vermont', 'NH': 'New Hampshire', 'ME': 'Maine',
    'WA': 'Washington', 'ID': 'Idaho', 'AK': 'Alaska'
}


def _socrata_query(
    dataset_id: str,
    filters: Optional[Dict] = None,
    limit: int = 1000,
    offset: int = 0,
    order_by: Optional[str] = None
) -> Dict:
    """
    Helper function to query Socrata API
    
    Args:
        dataset_id: Socrata dataset 4x4 ID
        filters: Dict of filter conditions (field: value)
        limit: Max records to return (default 1000)
        offset: Pagination offset
        order_by: Field to sort by (append DESC for descending)
    
    Returns:
        Dict with success status and data or error
    """
    try:
        url = f"{BTS_BASE_URL}/{dataset_id}.json"
        
        params = {
            '$limit': limit,
            '$offset': offset
        }
        
        # Add filters as $where clause
        if filters:
            where_clauses = []
            for field, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{field}='{value}'")
                else:
                    where_clauses.append(f"{field}={value}")
            if where_clauses:
                params['$where'] = ' AND '.join(where_clauses)
        
        if order_by:
            params['$order'] = order_by
        
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'count': len(data),
            'dataset_id': dataset_id
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'dataset_id': dataset_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'dataset_id': dataset_id
        }


def get_border_crossings(
    port_name: Optional[str] = None,
    state: Optional[str] = None,
    border: Optional[str] = None,
    measure: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get border crossing entry data (vehicles, pedestrians, containers)
    
    Tracks inbound crossings at U.S.-Canada and U.S.-Mexico land borders.
    Includes trucks, trains, personal vehicles, buses, pedestrians, and containers.
    
    Args:
        port_name: Port of entry name (e.g., 'San Ysidro')
        state: U.S. state (full name like 'Texas' or abbreviation like 'TX')
        border: 'US-Canada Border' or 'US-Mexico Border'
        measure: Crossing type ('Trucks', 'Trains', 'Personal Vehicles', etc.)
        limit: Max records to return (default 100)
    
    Returns:
        Dict with border crossing counts by measure type and port
        
    Example:
        >>> data = get_border_crossings(state='TX', border='US-Mexico Border')
        >>> print(data['summary']['total_crossings'])
    """
    filters = {}
    
    if port_name:
        filters['port_name'] = port_name
    
    if state:
        # Convert state abbreviation to full name if needed
        state_full = STATE_NAMES.get(state.upper(), state)
        filters['state'] = state_full
    
    if border:
        filters['border'] = border
    
    if measure:
        filters['measure'] = measure
    
    result = _socrata_query(
        dataset_id=DATASETS['border_crossings'],
        filters=filters if filters else None,
        limit=limit,
        order_by='date DESC'  # Most recent first
    )
    
    if not result['success']:
        return result
    
    # Aggregate by measure type
    measures_summary = {}
    ports_summary = {}
    total_crossings = 0
    
    for record in result['data']:
        try:
            measure_type = record.get('measure', 'Unknown')
            port = record.get('port_name', 'Unknown')
            value = int(record.get('value', 0))
            
            # By measure
            if measure_type not in measures_summary:
                measures_summary[measure_type] = 0
            measures_summary[measure_type] += value
            
            # By port
            if port not in ports_summary:
                ports_summary[port] = 0
            ports_summary[port] += value
            
            total_crossings += value
        except (ValueError, KeyError):
            continue
    
    # Top ports
    top_ports = sorted(ports_summary.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'success': True,
        'border_crossings': result['data'][:20],  # Top 20 recent records
        'summary': {
            'total_crossings': total_crossings,
            'by_measure': measures_summary,
            'top_ports': dict(top_ports),
            'record_count': result['count']
        },
        'filters_applied': filters,
        'timestamp': datetime.now().isoformat(),
        'source': 'BTS Border Crossing Entry Data'
    }


def get_top_border_ports(
    border: Optional[str] = None,
    measure: Optional[str] = None,
    limit: int = 20
) -> Dict:
    """
    Get top border crossing ports by traffic volume
    
    Args:
        border: 'US-Canada Border' or 'US-Mexico Border' (defaults to both)
        measure: Filter by crossing type (e.g., 'Trucks', 'Personal Vehicles')
        limit: Number of top ports to return
    
    Returns:
        Dict with ranked ports by total crossing volume
    """
    filters = {}
    if border:
        filters['border'] = border
    if measure:
        filters['measure'] = measure
    
    result = _socrata_query(
        dataset_id=DATASETS['border_crossings'],
        filters=filters if filters else None,
        limit=10000
    )
    
    if not result['success']:
        return result
    
    # Aggregate by port
    port_totals = {}
    
    for record in result['data']:
        try:
            port = record.get('port_name', 'Unknown')
            state = record.get('state', '')
            value = int(record.get('value', 0))
            border_val = record.get('border', '')
            
            port_key = f"{port}, {state}"
            
            if port_key not in port_totals:
                port_totals[port_key] = {
                    'port_name': port,
                    'state': state,
                    'border': border_val,
                    'total_crossings': 0
                }
            
            port_totals[port_key]['total_crossings'] += value
        except (ValueError, KeyError):
            continue
    
    # Sort and limit
    sorted_ports = sorted(
        port_totals.values(),
        key=lambda x: x['total_crossings'],
        reverse=True
    )[:limit]
    
    return {
        'success': True,
        'top_ports': sorted_ports,
        'border_filter': border or 'all',
        'measure_filter': measure or 'all',
        'timestamp': datetime.now().isoformat(),
        'source': 'BTS Border Crossing Entry Data'
    }


def get_latest_border_activity(
    border: Optional[str] = None,
    days_back: int = 30
) -> Dict:
    """
    Get recent border crossing activity (last N days)
    
    Args:
        border: 'US-Canada Border' or 'US-Mexico Border'
        days_back: Number of days to look back (default 30)
    
    Returns:
        Dict with recent border activity trends
    """
    # Calculate date threshold
    date_threshold = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    filters = {}
    if border:
        filters['border'] = border
    
    result = _socrata_query(
        dataset_id=DATASETS['border_crossings'],
        filters=filters if filters else None,
        limit=5000,
        order_by='date DESC'
    )
    
    if not result['success']:
        return result
    
    # Filter by date and aggregate
    recent_records = []
    measures_trend = {}
    
    for record in result['data']:
        try:
            record_date = record.get('date', '')[:10]  # Extract YYYY-MM-DD
            if record_date >= date_threshold:
                recent_records.append(record)
                
                measure = record.get('measure', 'Unknown')
                value = int(record.get('value', 0))
                
                if measure not in measures_trend:
                    measures_trend[measure] = 0
                measures_trend[measure] += value
        except (ValueError, KeyError):
            continue
    
    total_recent = sum(int(r.get('value', 0)) for r in recent_records)
    
    return {
        'success': True,
        'recent_crossings': recent_records[:20],  # Sample
        'summary': {
            'days_analyzed': days_back,
            'total_crossings': total_recent,
            'by_measure': measures_trend,
            'record_count': len(recent_records)
        },
        'timestamp': datetime.now().isoformat(),
        'source': 'BTS Border Crossing Entry Data'
    }


def get_border_by_measure(
    measure: str,
    border: Optional[str] = None,
    limit: int = 50
) -> Dict:
    """
    Get border crossing data filtered by measure type
    
    Args:
        measure: Crossing type (e.g., 'Trucks', 'Trains', 'Personal Vehicles')
        border: Optional border filter
        limit: Max records to return
    
    Returns:
        Dict with crossings for specified measure type
    """
    return get_border_crossings(
        border=border,
        measure=measure,
        limit=limit
    )


def get_mexico_border_stats(limit: int = 100) -> Dict:
    """
    Get US-Mexico border crossing statistics
    
    Returns:
        Dict with Mexico border stats by port and measure
    """
    return get_border_crossings(
        border='US-Mexico Border',
        limit=limit
    )


def get_canada_border_stats(limit: int = 100) -> Dict:
    """
    Get US-Canada border crossing statistics
    
    Returns:
        Dict with Canada border stats by port and measure
    """
    return get_border_crossings(
        border='US-Canada Border',
        limit=limit
    )


def list_available_datasets() -> Dict:
    """
    List all available BTS datasets in this module
    
    Returns:
        Dict with dataset information and capabilities
    """
    datasets_info = {
        'border_crossings': {
            'dataset_id': DATASETS['border_crossings'],
            'name': 'Border Crossing Entry Data',
            'description': 'Inbound crossings at US-Canada and US-Mexico borders',
            'update_frequency': 'Monthly',
            'measures': ['Trucks', 'Trains', 'Personal Vehicles', 'Buses', 
                        'Pedestrians', 'Personal Vehicle Passengers', 
                        'Bus Passengers', 'Rail Containers Full', 'Rail Containers Empty'],
            'functions': [
                'get_border_crossings',
                'get_top_border_ports', 
                'get_latest_border_activity',
                'get_border_by_measure',
                'get_mexico_border_stats',
                'get_canada_border_stats'
            ]
        }
    }
    
    return {
        'success': True,
        'total_datasets': len(datasets_info),
        'datasets': datasets_info,
        'module': 'bts_transportation_api',
        'source': 'BTS Socrata Open Data API',
        'base_url': BTS_BASE_URL
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("BTS Transportation API - Bureau of Transportation Statistics")
    print("=" * 60)
    
    # List datasets
    datasets = list_available_datasets()
    print(f"\nAvailable Datasets: {datasets['total_datasets']}")
    print(json.dumps(datasets, indent=2))
    
    print("\n" + "=" * 60)
    print("Sample: Texas Border Crossings")
    print("=" * 60)
    tx_border = get_border_crossings(state='TX', limit=10)
    if tx_border['success']:
        print(json.dumps(tx_border, indent=2))
