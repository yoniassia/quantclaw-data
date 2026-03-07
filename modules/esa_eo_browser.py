#!/usr/bin/env python3
"""
ESA EO Browser — Satellite Imagery & Geospatial Data Module

Access free satellite imagery from the European Space Agency via Copernicus Data Space.
Search and analyze Sentinel satellite data for oil storage, shipping, agriculture,
and environmental monitoring without API keys.

Source: https://apps.sentinel-hub.com/eo-browser/
Free API: https://catalogue.dataspace.copernicus.eu/
Category: Alternative Data — Satellite & Geospatial
Free tier: True (no authentication required for catalog search)
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from math import radians, cos, sin, asin, sqrt


# Copernicus Data Space API endpoints
ODATA_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
STAC_BASE_URL = "https://catalogue.dataspace.copernicus.eu/stac"


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth in kilometers
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r


def _create_bbox_from_point(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Create bounding box from center point and radius
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Radius in kilometers
    
    Returns:
        Tuple of (min_lon, min_lat, max_lon, max_lat)
    """
    # Approximate conversion (works well for small areas)
    lat_delta = radius_km / 111.0  # 1 degree lat ≈ 111 km
    lon_delta = radius_km / (111.0 * cos(radians(lat)))  # Adjust for latitude
    
    return (
        lon - lon_delta,  # min_lon
        lat - lat_delta,  # min_lat
        lon + lon_delta,  # max_lon
        lat + lat_delta   # max_lat
    )


def get_collections() -> Dict:
    """
    Get list of available Sentinel satellite collections
    
    Returns:
        Dict with available collections and their descriptions
    """
    try:
        # Use STAC API to get collections
        url = f"{STAC_BASE_URL}/collections"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        collections = []
        if 'collections' in data:
            for col in data['collections']:
                collections.append({
                    'id': col.get('id'),
                    'title': col.get('title', col.get('id')),
                    'description': col.get('description', ''),
                    'license': col.get('license', ''),
                    'extent': col.get('extent', {})
                })
        
        return {
            'success': True,
            'collections': collections,
            'count': len(collections),
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        # Fallback: return known Sentinel collections
        return {
            'success': True,
            'collections': [
                {'id': 'SENTINEL-1', 'title': 'Sentinel-1 SAR', 'description': 'C-band synthetic aperture radar imaging'},
                {'id': 'SENTINEL-2', 'title': 'Sentinel-2 MSI', 'description': 'Multispectral optical imaging'},
                {'id': 'SENTINEL-3', 'title': 'Sentinel-3 OLCI/SLSTR', 'description': 'Ocean and land monitoring'},
                {'id': 'SENTINEL-5P', 'title': 'Sentinel-5 Precursor', 'description': 'Atmospheric monitoring'},
            ],
            'count': 4,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'note': f'STAC API unavailable: {str(e)}'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def search_imagery(
    bbox: Tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    collection: str = 'SENTINEL-2',
    max_cloud: int = 30
) -> Dict:
    """
    Search satellite imagery by bounding box and date range
    
    Args:
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        collection: Satellite collection (default 'SENTINEL-2')
        max_cloud: Maximum cloud coverage percentage (0-100)
    
    Returns:
        Dict with matching products and metadata
    """
    try:
        # Format bbox for OData query
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Build OData filter query
        # OData uses POLYGON format for spatial queries
        polygon = f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"
        
        # Collection name mapping
        collection_map = {
            'SENTINEL-1': 'SENTINEL-1',
            'SENTINEL-2': 'SENTINEL-2',
            'SENTINEL-3': 'SENTINEL-3',
            'SENTINEL-5P': 'SENTINEL-5P'
        }
        
        collection_name = collection_map.get(collection.upper(), 'SENTINEL-2')
        
        # Build filter
        filters = [
            f"Collection/Name eq '{collection_name}'",
            f"ContentDate/Start ge {start_date}T00:00:00.000Z",
            f"ContentDate/Start le {end_date}T23:59:59.999Z",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon}')"
        ]
        
        # Add cloud coverage filter for optical satellites
        if 'SENTINEL-2' in collection_name:
            filters.append(f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {max_cloud})")
        
        filter_string = " and ".join(filters)
        
        url = f"{ODATA_BASE_URL}/Products"
        params = {
            "$filter": filter_string,
            "$top": 50,
            "$expand": "Attributes",
            "$orderby": "ContentDate/Start desc"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        products = []
        if 'value' in data:
            for item in data['value']:
                product = {
                    'id': item.get('Id'),
                    'name': item.get('Name'),
                    'collection': collection_name,
                    'acquisition_date': item.get('ContentDate', {}).get('Start'),
                    'size_mb': item.get('ContentLength', 0) / (1024 * 1024),
                    'online': item.get('Online', False),
                }
                
                # Extract cloud coverage if available
                if 'Attributes' in item:
                    for attr in item.get('Attributes', []):
                        if attr.get('Name') == 'cloudCover':
                            product['cloud_coverage'] = attr.get('Value')
                        elif attr.get('Name') == 'resolution':
                            product['resolution'] = attr.get('Value')
                
                # Extract footprint if available
                if 'GeoFootprint' in item:
                    product['footprint'] = item['GeoFootprint']
                
                products.append(product)
        
        return {
            'success': True,
            'products': products,
            'count': len(products),
            'query': {
                'bbox': bbox,
                'start_date': start_date,
                'end_date': end_date,
                'collection': collection_name,
                'max_cloud': max_cloud
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'query': {
                'bbox': bbox,
                'start_date': start_date,
                'end_date': end_date,
                'collection': collection
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def search_by_location(
    lat: float,
    lon: float,
    radius_km: float = 50,
    days_back: int = 30,
    collection: str = 'SENTINEL-2',
    max_cloud: int = 30
) -> Dict:
    """
    Search satellite imagery near a point location
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Search radius in kilometers (default 50)
        days_back: Number of days to look back (default 30)
        collection: Satellite collection (default 'SENTINEL-2')
        max_cloud: Maximum cloud coverage percentage (default 30)
    
    Returns:
        Dict with matching products near the location
    """
    try:
        # Create bounding box from point and radius
        bbox = _create_bbox_from_point(lat, lon, radius_km)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Use search_imagery with generated bbox
        result = search_imagery(
            bbox=bbox,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            collection=collection,
            max_cloud=max_cloud
        )
        
        # Add location info to result
        if result['success']:
            result['query']['location'] = {
                'lat': lat,
                'lon': lon,
                'radius_km': radius_km
            }
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_product_metadata(product_id: str) -> Dict:
    """
    Get detailed metadata for a specific product
    
    Args:
        product_id: Product identifier (UUID)
    
    Returns:
        Dict with detailed product metadata
    """
    try:
        url = f"{ODATA_BASE_URL}/Products({product_id})"
        params = {
            "$expand": "Attributes,Assets"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        metadata = {
            'id': data.get('Id'),
            'name': data.get('Name'),
            'collection': data.get('Collection', {}).get('Name'),
            'size_mb': data.get('ContentLength', 0) / (1024 * 1024),
            'online': data.get('Online', False),
            'content_date': data.get('ContentDate', {}),
            'modification_date': data.get('ModificationDate'),
            'geo_footprint': data.get('GeoFootprint'),
            'checksum': data.get('Checksum', [])
        }
        
        # Extract attributes
        attributes = {}
        if 'Attributes' in data:
            for attr in data['Attributes']:
                name = attr.get('Name')
                value = attr.get('Value')
                if name and value is not None:
                    attributes[name] = value
        
        metadata['attributes'] = attributes
        
        return {
            'success': True,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'product_id': product_id,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'product_id': product_id,
            'timestamp': datetime.now().isoformat()
        }


def get_oil_storage_imagery(
    lat: float,
    lon: float,
    date: str,
    radius_km: float = 10,
    days_tolerance: int = 7
) -> Dict:
    """
    Specialized search for oil storage facility monitoring
    Uses high-resolution Sentinel-2 imagery with strict cloud coverage limits
    
    Args:
        lat: Latitude of oil facility
        lon: Longitude of oil facility  
        date: Target date in YYYY-MM-DD format
        radius_km: Search radius around facility (default 10km for precise targeting)
        days_tolerance: Days before/after target date (default 7)
    
    Returns:
        Dict with suitable imagery for oil storage monitoring
    """
    try:
        # Parse target date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = target_date - timedelta(days=days_tolerance)
        end_date = target_date + timedelta(days=days_tolerance)
        
        # Create tight bounding box around facility
        bbox = _create_bbox_from_point(lat, lon, radius_km)
        
        # Search with strict cloud coverage for oil facility monitoring
        result = search_imagery(
            bbox=bbox,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            collection='SENTINEL-2',  # High-resolution optical
            max_cloud=15  # Strict limit for clear facility monitoring
        )
        
        if result['success']:
            # Add oil monitoring context
            result['monitoring_info'] = {
                'facility_location': {'lat': lat, 'lon': lon},
                'target_date': date,
                'search_radius_km': radius_km,
                'use_case': 'Oil storage monitoring',
                'recommended_bands': ['B04 (Red)', 'B03 (Green)', 'B02 (Blue)', 'B08 (NIR)'],
                'analysis_tips': [
                    'Compare imagery across dates to detect tank level changes',
                    'Use NIR band to identify oil slicks or spills',
                    'Monitor shadow patterns for tank volume estimation',
                    'Track shipping traffic at loading terminals'
                ]
            }
            
            # Rank products by proximity to target date
            if result['products']:
                for product in result['products']:
                    acq_date = datetime.fromisoformat(product['acquisition_date'].replace('Z', '+00:00'))
                    days_diff = abs((acq_date.date() - target_date.date()).days)
                    product['days_from_target'] = days_diff
                
                # Sort by date proximity
                result['products'].sort(key=lambda x: x['days_from_target'])
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("ESA EO Browser - Satellite Imagery Module")
    print("=" * 60)
    
    # Test 1: Get collections
    print("\n[1] Available Collections:")
    collections = get_collections()
    if collections['success']:
        print(f"Found {collections['count']} collections")
        for col in collections['collections'][:5]:
            print(f"  - {col['id']}: {col.get('title', 'N/A')}")
    
    # Test 2: Search by location (New York area)
    print("\n[2] Recent imagery near New York:")
    ny_result = search_by_location(
        lat=40.7128,
        lon=-74.0060,
        radius_km=50,
        days_back=30,
        max_cloud=40
    )
    if ny_result['success']:
        print(f"Found {ny_result['count']} products")
        if ny_result['products']:
            latest = ny_result['products'][0]
            print(f"  Latest: {latest['name']}")
            print(f"  Date: {latest['acquisition_date']}")
            print(f"  Cloud: {latest.get('cloud_coverage', 'N/A')}%")
    
    print("\n" + json.dumps(collections, indent=2))
