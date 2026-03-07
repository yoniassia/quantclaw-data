#!/usr/bin/env python3
"""
PortWatch API — IMF Port Activity Data via ArcGIS Hub

PortWatch is an IMF platform providing data on global port activity via ArcGIS Hub.
Aggregates datasets on port congestion, shipping volumes, vessel tracking, and maritime trade flows.
Access maritime supply chain data that signals disruptions affecting commodity prices and logistics.

Source: https://portwatch.imf.org
API Base: https://portwatch.imf.org/api/v3
Category: Infrastructure & Transport
Free tier: Yes (public ArcGIS Hub API)
Update frequency: Varies by dataset (daily to weekly)

Integration: Uses ArcGIS Hub v3 REST API for dataset discovery and feature service queries
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
import time

# API Configuration
BASE_URL = "https://portwatch.imf.org/api/v3"
TIMEOUT = 30

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to PortWatch API
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        JSON response as dict
    """
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}

def search_datasets(query: str, limit: int = 10) -> Dict:
    """
    Search for datasets on PortWatch Hub
    
    Args:
        query: Search query (e.g., "port", "vessel", "shipping", "congestion")
        limit: Maximum number of results (default 10)
        
    Returns:
        Dict with 'data' (list of datasets) and 'meta' (search metadata)
        
    Example:
        >>> results = search_datasets("port congestion", limit=5)
        >>> for dataset in results.get('data', []):
        ...     print(dataset['attributes']['name'])
    """
    params = {
        'q': query,
        'page[size]': limit
    }
    return _make_request('datasets', params)

def get_dataset_by_id(dataset_id: str) -> Dict:
    """
    Get specific dataset by ID
    
    Args:
        dataset_id: ArcGIS item ID
        
    Returns:
        Dataset details including description, fields, and service URLs
        
    Example:
        >>> dataset = get_dataset_by_id("9078b38d23fc43d783ea65357c93398e_7")
    """
    return _make_request(f'datasets/{dataset_id}')

def search_port_data(limit: int = 20) -> List[Dict]:
    """
    Search for port-specific datasets (congestion, throughput, activity)
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of port-related datasets with metadata
        
    Example:
        >>> ports = search_port_data(limit=10)
        >>> print(f"Found {len(ports)} port datasets")
    """
    result = search_datasets("port", limit=limit)
    if 'data' in result:
        return [{
            'id': item.get('id'),
            'name': item['attributes'].get('name'),
            'description': item['attributes'].get('description', '')[:200],
            'owner': item['attributes'].get('owner'),
            'url': item['attributes'].get('url'),
            'modified': item['attributes'].get('itemModified')
        } for item in result['data']]
    return []

def search_vessel_data(limit: int = 20) -> List[Dict]:
    """
    Search for vessel tracking and AIS data
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of vessel/AIS datasets with metadata
        
    Example:
        >>> vessels = search_vessel_data(limit=15)
    """
    result = search_datasets("vessel AIS", limit=limit)
    if 'data' in result:
        return [{
            'id': item.get('id'),
            'name': item['attributes'].get('name'),
            'description': item['attributes'].get('description', '')[:200],
            'owner': item['attributes'].get('owner'),
            'org': item['attributes'].get('orgName'),
            'url': item['attributes'].get('url'),
            'tags': item['attributes'].get('tags', [])
        } for item in result['data']]
    return []

def search_shipping_routes(limit: int = 15) -> List[Dict]:
    """
    Search for maritime shipping route and trade flow data
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of shipping/maritime datasets
        
    Example:
        >>> routes = search_shipping_routes()
    """
    result = search_datasets("maritime shipping", limit=limit)
    if 'data' in result:
        return [{
            'id': item.get('id'),
            'name': item['attributes'].get('name'),
            'description': item['attributes'].get('description', '')[:250],
            'content_type': item['attributes'].get('content'),
            'url': item['attributes'].get('url')
        } for item in result['data']]
    return []

def get_congestion_data(search_term: str = "congestion", limit: int = 10) -> List[Dict]:
    """
    Get port congestion and delay data
    
    Args:
        search_term: Search refinement (default "congestion")
        limit: Maximum results
        
    Returns:
        List of congestion datasets
        
    Example:
        >>> congestion = get_congestion_data("port congestion", limit=5)
    """
    result = search_datasets(search_term, limit=limit)
    if 'data' in result:
        return [{
            'id': item.get('id'),
            'name': item['attributes'].get('name'),
            'description': item['attributes'].get('description', '')[:200],
            'fields': [f['name'] for f in item['attributes'].get('fields', [])[:10]],
            'url': item['attributes'].get('url')
        } for item in result['data'] if 'congestion' in item['attributes'].get('name', '').lower() 
                                        or 'congestion' in item['attributes'].get('description', '').lower()]
    return []

def query_feature_service(service_url: str, where_clause: str = "1=1", 
                          out_fields: str = "*", limit: int = 100) -> Dict:
    """
    Query an ArcGIS Feature Service directly
    
    Args:
        service_url: Feature service URL (from dataset metadata)
        where_clause: SQL WHERE clause (default "1=1" for all)
        out_fields: Fields to return (default "*" for all)
        limit: Result limit
        
    Returns:
        Feature query results
        
    Example:
        >>> url = "https://services9.arcgis.com/.../FeatureServer/0"
        >>> data = query_feature_service(url, where_clause="RANK < 100", limit=50)
    """
    if not service_url or not service_url.startswith('http'):
        return {"error": "Invalid service URL", "status": "failed"}
    
    # Add /query if not present
    if not service_url.endswith('/query'):
        service_url = service_url.rstrip('/') + '/query'
    
    params = {
        'where': where_clause,
        'outFields': out_fields,
        'returnGeometry': 'false',
        'resultRecordCount': limit,
        'f': 'json'
    }
    
    try:
        response = requests.get(service_url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}

def get_dataset_categories(limit: int = 50) -> Dict[str, int]:
    """
    Get available dataset categories and counts
    
    Args:
        limit: Number of datasets to sample
        
    Returns:
        Dict of categories with dataset counts
        
    Example:
        >>> categories = get_dataset_categories()
        >>> print(categories)
    """
    result = search_datasets("", limit=limit)
    categories = {}
    
    if 'data' in result:
        for item in result['data']:
            cats = item['attributes'].get('categories', [])
            for cat in cats:
                categories[cat] = categories.get(cat, 0) + 1
    
    return categories

def get_latest_updates(query: str = "port vessel", limit: int = 10) -> List[Dict]:
    """
    Get recently updated port/vessel datasets
    
    Args:
        query: Search query
        limit: Number of results
        
    Returns:
        List of recently updated datasets sorted by modification date
        
    Example:
        >>> recent = get_latest_updates("shipping", limit=5)
    """
    result = search_datasets(query, limit=limit)
    if 'data' in result:
        datasets = [{
            'name': item['attributes'].get('name'),
            'modified': item['attributes'].get('itemModified'),
            'modified_date': datetime.fromtimestamp(item['attributes'].get('itemModified', 0)/1000).strftime('%Y-%m-%d') if item['attributes'].get('itemModified') else None,
            'description': (item['attributes'].get('description') or '')[:150],
            'url': item['attributes'].get('url')
        } for item in result['data']]
        
        # Sort by modification date
        return sorted(datasets, key=lambda x: x.get('modified', 0), reverse=True)
    return []

def get_module_info() -> Dict:
    """
    Get module information and API status
    
    Returns:
        Dict with module metadata and connection status
    """
    try:
        # Test API connectivity
        test = _make_request('datasets', {'page[size]': 1})
        api_status = "connected" if 'data' in test else "error"
    except:
        api_status = "unreachable"
    
    return {
        "module": "portwatch_api",
        "version": "1.0.0",
        "source": "https://portwatch.imf.org",
        "api_base": BASE_URL,
        "api_status": api_status,
        "description": "IMF PortWatch - Global port activity data via ArcGIS Hub",
        "capabilities": [
            "search_datasets",
            "search_port_data", 
            "search_vessel_data",
            "search_shipping_routes",
            "get_congestion_data",
            "query_feature_service"
        ],
        "data_types": [
            "Port congestion",
            "Vessel tracking (AIS)",
            "Shipping routes",
            "Maritime trade flows",
            "Port activity metrics"
        ]
    }

if __name__ == "__main__":
    info = get_module_info()
    print(json.dumps(info, indent=2))
