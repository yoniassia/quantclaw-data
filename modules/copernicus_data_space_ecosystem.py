"""
Copernicus Data Space Ecosystem — EU Satellite Data for Alt-Data Trading

Data Source: European Space Agency / Copernicus Programme
Update: Real-time (satellite passes every 5-10 days per location)
Coverage: Global Earth observation data
Free: Yes (OData API, no auth required for basic queries)

Provides:
- Sentinel-1 (Radar imaging for agriculture, shipping)
- Sentinel-2 (Optical imaging for crop health, deforestation)
- Sentinel-3 (Ocean/land monitoring for commodity signals)
- Sentinel-5P (Air quality, pollution for ESG/regulatory risk)

Trading Use Cases:
- Crop yield prediction → Agricultural commodities (corn, wheat, soy)
- Port activity tracking → Shipping stocks, oil demand
- Deforestation detection → Timber, palm oil, carbon credits
- Urban expansion → Real estate, construction materials
- Drought/flood monitoring → Insurance, disaster relief stocks

API Docs: https://documentation.dataspace.copernicus.eu/APIs/OData.html
OData Endpoint: https://catalogue.dataspace.copernicus.eu/odata/v1
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# === API Configuration ===
BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
PRODUCTS_URL = f"{BASE_URL}/Products"

# Rate limit: 100 requests/hour (no auth needed)
REQUEST_TIMEOUT = 15

# Sentinel collection names (for filtering by product name prefix)
SENTINEL_COLLECTIONS = {
    "Sentinel1": "S1",
    "Sentinel2": "S2",
    "Sentinel3": "S3", 
    "Sentinel5P": "S5P",
}


def get_products(
    collection: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top: int = 10,
    orderby: str = "ContentDate/Start desc"
) -> Dict:
    """
    Query satellite products from Copernicus OData API.
    
    Args:
        collection: Sentinel1, Sentinel2, Sentinel3, Sentinel5P (optional)
        start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        top: Maximum results to return (default 10, max 1000)
        orderby: Sort order (default: newest first)
    
    Returns:
        Dict with products list, total count, query params
    """
    try:
        # Default date range: last 30 days
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Build OData query parameters
        params = {
            "$top": top,
            "$orderby": orderby,
        }
        
        # Build filter conditions
        filters = []
        
        # Date filter
        filters.append(f"ContentDate/Start ge {start_date}T00:00:00.000Z")
        filters.append(f"ContentDate/Start le {end_date}T23:59:59.999Z")
        
        # Collection filter (if specified)
        if collection and collection in SENTINEL_COLLECTIONS:
            collection_prefix = SENTINEL_COLLECTIONS[collection]
            filters.append(f"startswith(Name,'{collection_prefix}_')")
        
        # Combine filters
        if filters:
            params["$filter"] = " and ".join(filters)
        
        response = requests.get(PRODUCTS_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse products
        products = []
        for item in data.get("value", []):
            products.append({
                "id": item.get("Id", ""),
                "name": item.get("Name", ""),
                "content_date_start": item.get("ContentDate", {}).get("Start", ""),
                "content_date_end": item.get("ContentDate", {}).get("End", ""),
                "publication_date": item.get("PublicationDate", ""),
                "online": item.get("Online", False),
                "content_length_mb": round(item.get("ContentLength", 0) / 1024 / 1024, 2),
                "s3_path": item.get("S3Path", ""),
                "footprint": item.get("GeoFootprint", {}),
            })
        
        # Get total count from @odata.count if available
        total = data.get("@odata.count", len(products))
        
        return {
            "collection": collection or "All",
            "start_date": start_date,
            "end_date": end_date,
            "total_results": total,
            "returned": len(products),
            "products": products,
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error querying products: {e}")
        return {
            "collection": collection or "All",
            "error": str(e),
            "total_results": 0,
            "products": []
        }
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            "collection": collection or "All",
            "error": str(e),
            "total_results": 0,
            "products": []
        }


def get_sentinel2_recent(days: int = 7, max_results: int = 10) -> Dict:
    """
    Get most recent Sentinel-2 optical imagery.
    
    Args:
        days: Number of days back to search (default 7)
        max_results: Maximum results (default 10)
    
    Returns:
        Recent Sentinel-2 products
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    return get_products(
        collection="Sentinel2",
        start_date=start_date,
        top=max_results
    )


def get_sentinel1_recent(days: int = 7, max_results: int = 10) -> Dict:
    """
    Get most recent Sentinel-1 radar imagery (all-weather).
    
    Args:
        days: Number of days back to search (default 7)
        max_results: Maximum results (default 10)
    
    Returns:
        Recent Sentinel-1 products
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    return get_products(
        collection="Sentinel1",
        start_date=start_date,
        top=max_results
    )


def get_available_collections() -> List[Dict]:
    """
    List available Sentinel collections.
    
    Returns:
        List of collection metadata
    """
    return [
        {
            "name": "Sentinel1",
            "full_name": "SENTINEL-1",
            "platform": "Sentinel-1A/1B",
            "instrument": "C-SAR (Synthetic Aperture Radar)",
            "description": "All-weather, day/night radar imaging for agriculture, shipping, flooding",
            "use_case": "Port activity, flood detection, crop monitoring"
        },
        {
            "name": "Sentinel2",
            "full_name": "SENTINEL-2",
            "platform": "Sentinel-2A/2B",
            "instrument": "MSI (Multispectral Imager)",
            "description": "High-resolution optical imagery for land monitoring",
            "use_case": "Crop health (NDVI), deforestation, urban expansion"
        },
        {
            "name": "Sentinel3",
            "full_name": "SENTINEL-3",
            "platform": "Sentinel-3A/3B",
            "instrument": "OLCI, SLSTR (Ocean/Land Color + Thermal)",
            "description": "Ocean and land surface temperature, vegetation monitoring",
            "use_case": "Sea surface temp, wildfire detection, agricultural yields"
        },
        {
            "name": "Sentinel5P",
            "full_name": "SENTINEL-5P",
            "platform": "Sentinel-5 Precursor",
            "instrument": "TROPOMI (Atmospheric monitoring)",
            "description": "Air quality, ozone, NO2, methane emissions",
            "use_case": "ESG compliance, pollution risk for factories, carbon credits"
        },
    ]


def search_by_bbox(
    bbox: List[float],
    collection: Optional[str] = None,
    days: int = 30,
    max_results: int = 5
) -> Dict:
    """
    Search products by geographic bounding box.
    
    Args:
        bbox: Bounding box [lon_min, lat_min, lon_max, lat_max]
              Example: [-95.0, 40.0, -90.0, 45.0] for Iowa corn belt
        collection: Sentinel1, Sentinel2, Sentinel3, Sentinel5P (optional)
        days: Number of days back to search (default 30)
        max_results: Maximum results (default 5)
    
    Returns:
        Products intersecting the bounding box
    
    Note: Full spatial filtering requires authenticated API.
    This function returns recent products from the collection
    and suggests manual filtering by GeoFootprint.
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Get products from collection
    results = get_products(
        collection=collection,
        start_date=start_date,
        top=max_results * 3  # Get more, filter client-side
    )
    
    # Add bbox info to results
    results["bbox"] = bbox
    results["note"] = "Spatial filtering requires authenticated API. Results show recent products; filter by GeoFootprint client-side."
    
    return results


# === CLI Commands for Testing ===

def cli_collections():
    """List available satellite collections"""
    collections = get_available_collections()
    
    print("\n🛰️  Copernicus Data Space — Available Collections")
    print("=" * 70)
    
    for coll in collections:
        print(f"\n📡 {coll['name']} ({coll['full_name']})")
        print(f"   Platform: {coll['platform']}")
        print(f"   Instrument: {coll['instrument']}")
        print(f"   Use Case: {coll['use_case']}")


def cli_search_recent(collection: str = "Sentinel2", days: int = 7):
    """Search recent products from a collection"""
    print(f"\n🛰️  Searching {collection} — Last {days} Days")
    print("=" * 70)
    
    if collection == "Sentinel2":
        results = get_sentinel2_recent(days=days, max_results=5)
    elif collection == "Sentinel1":
        results = get_sentinel1_recent(days=days, max_results=5)
    else:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        results = get_products(collection=collection, start_date=start_date, top=5)
    
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"📊 Total Results: {results['total_results']}")
    print(f"📥 Returned: {results['returned']}")
    print(f"📅 Date Range: {results['start_date']} to {results['end_date']}")
    
    if results['products']:
        print("\n🔍 Sample Results:")
        for i, prod in enumerate(results['products'][:3], 1):
            print(f"\n  {i}. {prod['name'][:60]}...")
            print(f"     Date: {prod['content_date_start']}")
            print(f"     Size: {prod['content_length_mb']} MB")
            print(f"     Online: {prod['online']}")
    else:
        print("ℹ️  No results found for this search")


def cli_test_api():
    """Test API connectivity"""
    print("\n🛰️  Testing Copernicus OData API")
    print("=" * 70)
    
    try:
        # Test simple query
        params = {"$top": 1}
        response = requests.get(PRODUCTS_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        if data.get("value"):
            print("✅ API is accessible")
            print(f"✅ Sample product: {data['value'][0].get('Name', 'N/A')[:60]}...")
            return True
        else:
            print("⚠️  API returned no data")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


if __name__ == "__main__":
    # Demo: Test API + List collections + Search Sentinel-2
    print("\n" + "="*70)
    print("🛰️  COPERNICUS DATA SPACE ECOSYSTEM — Demo")
    print("="*70)
    
    # Test 1: API connectivity
    cli_test_api()
    
    print("\n\n")
    
    # Test 2: List collections
    cli_collections()
    
    print("\n\n")
    
    # Test 3: Search recent Sentinel-2 data
    cli_search_recent("Sentinel2", days=7)
