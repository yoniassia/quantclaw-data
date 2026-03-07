#!/usr/bin/env python3
"""
Planet Labs API — Satellite Imagery & Geospatial Data

Planet Labs provides high-resolution satellite imagery through its API, focusing on 
daily global coverage for monitoring changes in infrastructure, agriculture, and 
energy sectors. Enables financial analysis for trading commodities, detecting supply 
chain issues, or assessing geopolitical events via imagery.

Source: https://www.planet.com/products/planet-api/
Category: Alternative Data — Satellite & Geospatial
Free tier: True - Free basemap tiles + 1,000 sq km imagery/month with API key
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Planet Labs API Configuration
PLANET_BASE_URL = "https://api.planet.com"
PLANET_DATA_API = f"{PLANET_BASE_URL}/data/v1"
PLANET_BASEMAP_URL = "https://tiles.planet.com/basemaps/v1/planet-tiles"
PLANET_API_KEY = os.environ.get("PLANET_API_KEY", "")

# Default item types for imagery search
ITEM_TYPES = ["PSScene", "REOrthoTile", "SkySatCollect", "Landsat8L1G", "Sentinel2L1C"]

def _make_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, 
                  auth_required: bool = True) -> Dict:
    """
    Make authenticated request to Planet API
    
    Args:
        endpoint: API endpoint URL
        method: HTTP method (GET, POST)
        data: JSON payload for POST requests
        auth_required: Whether authentication is required
        
    Returns:
        JSON response as dict
    """
    headers = {"Content-Type": "application/json"}
    auth = None
    
    if auth_required:
        if not PLANET_API_KEY:
            return {
                "error": "PLANET_API_KEY not set",
                "message": "Set PLANET_API_KEY environment variable for authenticated endpoints",
                "free_tier_note": "Get free API key at https://www.planet.com/account/"
            }
        auth = (PLANET_API_KEY, "")
    
    try:
        if method == "POST":
            response = requests.post(endpoint, json=data, headers=headers, auth=auth, timeout=30)
        else:
            response = requests.get(endpoint, headers=headers, auth=auth, timeout=30)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            return {"error": "Authentication failed", "message": "Invalid PLANET_API_KEY"}
        elif status_code == 429:
            return {"error": "Rate limit exceeded", "message": "Too many requests"}
        else:
            return {"error": f"HTTP {status_code}", "message": str(e)}
    
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "message": "API request took too long"}
    
    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}
    
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "message": "Could not parse API response"}


def search_imagery(lat: float, lon: float, date_range: Optional[Tuple[str, str]] = None,
                   item_types: Optional[List[str]] = None, cloud_cover: float = 0.2,
                   limit: int = 10) -> Dict:
    """
    Search for available satellite imagery at a location
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        date_range: Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
        item_types: List of imagery types (default: PSScene, REOrthoTile, etc.)
        cloud_cover: Maximum cloud cover (0.0 to 1.0, default 0.2 = 20%)
        limit: Maximum number of results (default 10)
        
    Returns:
        Dict with search results including scene IDs, dates, and metadata
        
    Example:
        >>> search_imagery(40.7128, -74.0060, date_range=("2026-01-01", "2026-01-31"))
        {'features': [...], 'count': 5, 'location': 'New York City area'}
    """
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return {"error": "Invalid coordinates", "message": "Lat must be -90 to 90, Lon -180 to 180"}
    
    # Default to last 30 days if no date range provided
    if date_range is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    if item_types is None:
        item_types = ["PSScene"]  # PlanetScope Scene - most common
    
    # Build search filter
    search_filter = {
        "type": "AndFilter",
        "config": [
            {
                "type": "GeometryFilter",
                "field_name": "geometry",
                "config": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            },
            {
                "type": "DateRangeFilter",
                "field_name": "acquired",
                "config": {
                    "gte": f"{date_range[0]}T00:00:00Z",
                    "lte": f"{date_range[1]}T23:59:59Z"
                }
            },
            {
                "type": "RangeFilter",
                "field_name": "cloud_cover",
                "config": {
                    "lte": cloud_cover
                }
            }
        ]
    }
    
    # Quick search request
    search_request = {
        "item_types": item_types,
        "filter": search_filter,
        "limit": limit
    }
    
    endpoint = f"{PLANET_DATA_API}/quick-search"
    result = _make_request(endpoint, method="POST", data=search_request)
    
    if "error" in result:
        return result
    
    # Simplify response
    features = result.get("features", [])
    simplified = {
        "count": len(features),
        "date_range": date_range,
        "location": {"lat": lat, "lon": lon},
        "scenes": []
    }
    
    for feature in features:
        scene = {
            "id": feature.get("id"),
            "acquired": feature.get("properties", {}).get("acquired"),
            "cloud_cover": feature.get("properties", {}).get("cloud_cover"),
            "item_type": feature.get("properties", {}).get("item_type"),
            "instrument": feature.get("properties", {}).get("instrument"),
            "quality_category": feature.get("properties", {}).get("quality_category"),
        }
        simplified["scenes"].append(scene)
    
    return simplified


def get_scene_metadata(scene_id: str, item_type: str = "PSScene") -> Dict:
    """
    Get detailed metadata for a specific satellite scene
    
    Args:
        scene_id: Unique scene identifier
        item_type: Type of imagery (default: PSScene)
        
    Returns:
        Dict with full scene metadata including geometry, timestamps, assets
        
    Example:
        >>> get_scene_metadata("20260115_123456_1234")
        {'id': '...', 'acquired': '...', 'geometry': {...}, 'assets': {...}}
    """
    if not scene_id:
        return {"error": "Invalid scene_id", "message": "Scene ID cannot be empty"}
    
    endpoint = f"{PLANET_DATA_API}/item-types/{item_type}/items/{scene_id}"
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    # Extract key metadata
    metadata = {
        "id": result.get("id"),
        "item_type": result.get("properties", {}).get("item_type"),
        "acquired": result.get("properties", {}).get("acquired"),
        "published": result.get("properties", {}).get("published"),
        "updated": result.get("properties", {}).get("updated"),
        "cloud_cover": result.get("properties", {}).get("cloud_cover"),
        "sun_azimuth": result.get("properties", {}).get("sun_azimuth"),
        "sun_elevation": result.get("properties", {}).get("sun_elevation"),
        "view_angle": result.get("properties", {}).get("view_angle"),
        "geometry": result.get("geometry"),
        "assets": list(result.get("_links", {}).get("assets", {}).keys()) if "_links" in result else [],
        "permissions": result.get("_permissions", [])
    }
    
    return metadata


def get_basemap_tiles(lat: float, lon: float, zoom: int = 12, tile_format: str = "png") -> Dict:
    """
    Get publicly available Planet basemap tile information
    
    Planet provides global basemap mosaics that are publicly accessible via tile URLs.
    These don't require API authentication for viewing.
    
    Args:
        lat: Latitude
        lon: Longitude  
        zoom: Zoom level (1-15, default 12)
        tile_format: Image format ('png' or 'jpg', default 'png')
        
    Returns:
        Dict with tile URL and coordinates
        
    Example:
        >>> get_basemap_tiles(40.7128, -74.0060, zoom=14)
        {'tile_url': 'https://tiles.planet.com/...', 'z': 14, 'x': 1234, 'y': 5678}
    """
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return {"error": "Invalid coordinates", "message": "Lat must be -90 to 90, Lon -180 to 180"}
    
    if not 1 <= zoom <= 15:
        return {"error": "Invalid zoom", "message": "Zoom must be between 1 and 15"}
    
    # Convert lat/lon to tile coordinates (Web Mercator / EPSG:3857)
    import math
    
    def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile x/y coordinates"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    x, y = deg2num(lat, lon, zoom)
    
    # Planet basemap tile URL format (publicly accessible global mosaic)
    # Note: Actual basemap access may require subscription for commercial use
    tile_url = f"{PLANET_BASEMAP_URL}/global_monthly_latest/{zoom}/{x}/{y}.{tile_format}"
    
    return {
        "tile_url": tile_url,
        "tile_coords": {"x": x, "y": y, "z": zoom},
        "location": {"lat": lat, "lon": lon},
        "format": tile_format,
        "note": "Basemap tiles may require Planet account for commercial use",
        "alternative_mosaics": [
            "global_monthly_latest",
            "global_quarterly_latest", 
            "global_annual_latest"
        ]
    }


def monitor_location(lat: float, lon: float, radius_km: float = 1.0, 
                     days_back: int = 30, item_types: Optional[List[str]] = None) -> Dict:
    """
    Monitor changes at a location by retrieving time-series imagery
    
    Useful for tracking construction, deforestation, agricultural changes, etc.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Radius around point in kilometers (default 1.0)
        days_back: How many days to look back (default 30)
        item_types: Imagery types to search (default: PSScene)
        
    Returns:
        Dict with time-series of imagery and change detection info
        
    Example:
        >>> monitor_location(40.7128, -74.0060, radius_km=2, days_back=60)
        {'location': {...}, 'monitoring_period': '60 days', 'scenes': [...]}
    """
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return {"error": "Invalid coordinates", "message": "Lat must be -90 to 90, Lon -180 to 180"}
    
    if radius_km <= 0 or radius_km > 100:
        return {"error": "Invalid radius", "message": "Radius must be between 0 and 100 km"}
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    # Search for imagery at this location
    search_result = search_imagery(
        lat=lat,
        lon=lon,
        date_range=date_range,
        item_types=item_types,
        cloud_cover=0.3,  # Allow slightly more cloud cover for monitoring
        limit=50  # Get more scenes for time series
    )
    
    if "error" in search_result:
        return search_result
    
    # Organize by date
    scenes_by_date = {}
    for scene in search_result.get("scenes", []):
        acquired = scene.get("acquired", "")[:10]  # Get date part only
        if acquired not in scenes_by_date:
            scenes_by_date[acquired] = []
        scenes_by_date[acquired].append(scene)
    
    return {
        "location": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "monitoring_period": f"{days_back} days",
        "date_range": date_range,
        "total_scenes": search_result.get("count", 0),
        "unique_dates": len(scenes_by_date),
        "scenes_by_date": scenes_by_date,
        "coverage_frequency": f"{len(scenes_by_date)} acquisitions over {days_back} days",
        "note": "Use scene IDs with get_scene_metadata() for detailed analysis"
    }


# ========== UTILITY FUNCTIONS ==========

def get_api_status() -> Dict:
    """Check Planet API connectivity and authentication status"""
    if not PLANET_API_KEY:
        return {
            "authenticated": False,
            "message": "PLANET_API_KEY not configured",
            "setup_instructions": "Get free API key at https://www.planet.com/account/"
        }
    
    # Test API with a simple stats request
    endpoint = f"{PLANET_DATA_API}/stats"
    result = _make_request(endpoint, method="POST", data={
        "item_types": ["PSScene"],
        "interval": "year",
        "filter": {
            "type": "DateRangeFilter",
            "field_name": "acquired",
            "config": {
                "gte": "2026-01-01T00:00:00Z",
                "lte": "2026-12-31T23:59:59Z"
            }
        }
    })
    
    if "error" in result:
        return {"authenticated": False, "error": result.get("error")}
    
    return {
        "authenticated": True,
        "api_status": "operational",
        "free_tier_limit": "1,000 sq km/month",
        "available_item_types": ITEM_TYPES
    }


if __name__ == "__main__":
    # Demo: Show API status
    status = get_api_status()
    print(json.dumps(status, indent=2))
    
    # Demo: Get basemap tile (works without API key)
    print("\n--- Basemap Tile Example (NYC) ---")
    tile = get_basemap_tiles(40.7128, -74.0060, zoom=12)
    print(json.dumps(tile, indent=2))
