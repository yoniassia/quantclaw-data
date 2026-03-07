"""
Copernicus Sentinel Hub — European Space Agency Satellite Data

Provides access to free satellite imagery from the Copernicus Data Space Ecosystem.
Tracks Sentinel-2 multispectral imagery for agricultural monitoring (NDVI), land use changes,
and environmental analysis. No authentication required for catalog search.

Data: https://catalogue.dataspace.copernicus.eu/odata/v1/Products
Docs: https://dataspace.copernicus.eu/

Use cases:
- Agricultural yield monitoring via NDVI
- Land use change detection
- Supply chain risk assessment (floods, droughts, disasters)
- Commodity market indicators (crop health, deforestation)
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "copernicus_sentinel"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"


def search_sentinel2_products(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cloud_cover_max: int = 30,
    bbox: Optional[List[float]] = None,
    limit: int = 10,
    use_cache: bool = True
) -> Optional[pd.DataFrame]:
    """
    Search Sentinel-2 satellite imagery catalog.
    
    Args:
        start_date: ISO date string (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: ISO date string (YYYY-MM-DD). Defaults to today.
        cloud_cover_max: Maximum cloud coverage percentage (0-100)
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        limit: Maximum number of results
        use_cache: Use cached results if available (24hr TTL)
    
    Returns:
        DataFrame with columns: id, name, date, cloud_cover, geometry, download_url
    """
    # Default date range: last 7 days
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Build cache key
    cache_key = f"search_{start_date}_{end_date}_{cloud_cover_max}_{limit}.json"
    if bbox:
        cache_key = f"search_{start_date}_{end_date}_{cloud_cover_max}_{bbox[0]}_{bbox[1]}_{limit}.json"
    cache_path = CACHE_DIR / cache_key
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Build OData filter
    filters = [
        "Collection/Name eq 'SENTINEL-2'",
        f"ContentDate/Start gt {start_date}T00:00:00.000Z",
        f"ContentDate/Start lt {end_date}T23:59:59.999Z"
    ]
    
    if cloud_cover_max < 100:
        filters.append(f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud_cover_max})")
    
    if bbox:
        # OGC intersects filter: geography'POLYGON((lon lat, ...))'
        poly = f"POLYGON(({bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))"
        filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{poly}')")
    
    filter_str = " and ".join(filters)
    
    # Build request
    url = f"{BASE_URL}/Products"
    params = {
        "$filter": filter_str,
        "$top": limit,
        "$orderby": "ContentDate/Start desc"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "value" not in data or not data["value"]:
            return pd.DataFrame()
        
        # Parse products
        records = []
        for product in data["value"]:
            record = {
                "id": product.get("Id", ""),
                "name": product.get("Name", ""),
                "date": product.get("ContentDate", {}).get("Start", ""),
                "geometry": product.get("GeoFootprint", {}).get("coordinates", []),
                "download_url": product.get("download", {}).get("url", "")
            }
            
            # Extract cloud cover from attributes
            attrs = product.get("Attributes", [])
            for attr in attrs:
                if attr.get("Name") == "cloudCover":
                    record["cloud_cover"] = attr.get("Value", 0)
                    break
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        return df
        
    except Exception as e:
        print(f"Error searching Sentinel-2 catalog: {e}")
        return None


def get_recent_imagery(days: int = 7, limit: int = 5) -> pd.DataFrame:
    """
    Get recent Sentinel-2 imagery with low cloud cover.
    
    Args:
        days: Number of days to look back
        limit: Maximum number of results
    
    Returns:
        DataFrame with recent imagery metadata
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    return search_sentinel2_products(
        start_date=start_date,
        end_date=end_date,
        cloud_cover_max=20,
        limit=limit
    )


def check_ndvi_availability(location_bbox: List[float], days_back: int = 30) -> Dict:
    """
    Check NDVI data availability for a specific location.
    
    NDVI (Normalized Difference Vegetation Index) is calculated from Sentinel-2 bands:
    NDVI = (NIR - Red) / (NIR + Red) using B8 (NIR) and B4 (Red)
    
    Args:
        location_bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        days_back: Number of days to look back
    
    Returns:
        Dict with available_images count, latest_date, avg_cloud_cover
    """
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    df = search_sentinel2_products(
        start_date=start_date,
        bbox=location_bbox,
        cloud_cover_max=30,
        limit=50
    )
    
    if df is None or df.empty:
        return {
            "available_images": 0,
            "latest_date": None,
            "avg_cloud_cover": None,
            "status": "no_data"
        }
    
    return {
        "available_images": len(df),
        "latest_date": df.iloc[0]["date"] if not df.empty else None,
        "avg_cloud_cover": df["cloud_cover"].mean() if "cloud_cover" in df.columns else None,
        "date_range": f"{start_date} to {datetime.now().strftime('%Y-%m-%d')}",
        "status": "available"
    }


def get_agriculture_monitoring_products(
    region_bbox: List[float],
    start_date: str,
    end_date: str,
    max_cloud_cover: int = 15
) -> pd.DataFrame:
    """
    Get Sentinel-2 products optimized for agricultural monitoring.
    
    Filters for low cloud cover and returns products suitable for NDVI analysis.
    
    Args:
        region_bbox: Agricultural region [min_lon, min_lat, max_lon, max_lat]
        start_date: Growing season start (YYYY-MM-DD)
        end_date: Growing season end (YYYY-MM-DD)
        max_cloud_cover: Maximum acceptable cloud cover (default 15%)
    
    Returns:
        DataFrame sorted by date, filtered for agricultural analysis
    """
    df = search_sentinel2_products(
        start_date=start_date,
        end_date=end_date,
        cloud_cover_max=max_cloud_cover,
        bbox=region_bbox,
        limit=100
    )
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Add metadata for quant analysis
    df["suitable_for_ndvi"] = df["cloud_cover"] < 20
    df["date_parsed"] = pd.to_datetime(df["date"])
    
    return df.sort_values("date_parsed", ascending=True)


def fetch_catalog_stats(use_cache: bool = True) -> Optional[Dict]:
    """
    Fetch overall catalog statistics.
    
    Returns:
        Dict with total_products, collections, latest_update
    """
    cache_path = CACHE_DIR / "catalog_stats.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    try:
        # Get recent count as proxy for activity
        url = f"{BASE_URL}/Products/$count"
        params = {
            "$filter": "Collection/Name eq 'SENTINEL-2' and ContentDate/Start gt 2026-01-01T00:00:00.000Z"
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        stats = {
            "sentinel2_products_2026": int(response.text),
            "last_checked": datetime.now().isoformat(),
            "api_status": "operational"
        }
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats
        
    except Exception as e:
        print(f"Error fetching catalog stats: {e}")
        return {"api_status": "error", "error": str(e)}


# Convenience function for quick testing
def test_module():
    """Test module functionality with recent data."""
    print("Testing Copernicus Sentinel Hub module...")
    
    # Test 1: Recent imagery
    print("\n1. Recent imagery (last 7 days):")
    df = get_recent_imagery(days=7, limit=5)
    if df is not None and not df.empty:
        print(f"   Found {len(df)} images")
        print(f"   Latest: {df.iloc[0]['date']}")
    else:
        print("   No data found")
    
    # Test 2: Catalog stats
    print("\n2. Catalog statistics:")
    stats = fetch_catalog_stats()
    if stats:
        print(f"   {stats}")
    
    # Test 3: NDVI availability (example: Iowa corn belt)
    print("\n3. NDVI availability check (Iowa example):")
    iowa_bbox = [-96.0, 41.0, -94.0, 43.0]
    ndvi_check = check_ndvi_availability(iowa_bbox, days_back=30)
    print(f"   {ndvi_check}")
    
    return True


if __name__ == "__main__":
    test_module()
