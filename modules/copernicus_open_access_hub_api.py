"""
Copernicus Open Access Hub API — Satellite & Geospatial Alternative Data

Data Source: Copernicus Data Space Ecosystem (formerly SciHub)
URL: https://dataspace.copernicus.eu/
Category: Alternative Data — Satellite & Geospatial
Free: Yes (registration required for downloads, catalog browsing is free)
Update: Real-time (new products ingested continuously)

Provides:
- Sentinel satellite product catalog search (S1 radar, S2 optical, S3, S5P)
- Product metadata (cloud cover, orbit, sensing date, footprint)
- Collection info and availability
- Geospatial queries (point/polygon intersection)

Quant Applications:
- Crop health monitoring via NDVI (Sentinel-2) → commodity futures signals
- Oil storage/tanker tracking via SAR (Sentinel-1) → crude oil positioning
- Pollution/emissions monitoring (Sentinel-5P) → ESG/carbon credit signals
- Port activity & shipping density → trade flow indicators
- Deforestation tracking → palm oil, soybean futures

Note: The original scihub.copernicus.eu OData API was migrated to the
Copernicus Data Space Ecosystem (CDSE). This module uses the CDSE OData
catalog API which is publicly accessible without authentication for
metadata queries.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/copernicus")
os.makedirs(CACHE_DIR, exist_ok=True)

# Copernicus Data Space Ecosystem — OData catalog API (public, no auth for search)
ODATA_BASE = "https://catalogue.dataspace.copernicus.eu/odata/v1"

# STAC API (also public for search)
STAC_BASE = "https://catalogue.dataspace.copernicus.eu/stac"

HEADERS = {
    "User-Agent": "QuantClaw-Data/1.0",
    "Accept": "application/json",
}

# Sentinel collection IDs used in queries
COLLECTIONS = {
    "S1": "SENTINEL-1",
    "S2": "SENTINEL-2",
    "S3": "SENTINEL-3",
    "S5P": "SENTINEL-5P",
}

# Common product types
PRODUCT_TYPES = {
    "S2_MSI_L2A": "S2MSI2A",   # Sentinel-2 L2A (surface reflectance — best for NDVI)
    "S2_MSI_L1C": "S2MSI1C",   # Sentinel-2 L1C (top-of-atmosphere)
    "S1_GRD": "GRD",            # Sentinel-1 Ground Range Detected (SAR)
    "S1_SLC": "SLC",            # Sentinel-1 Single Look Complex
    "S5P_L2": "L2__NO2___",     # Sentinel-5P NO2
}


def search_products(
    collection: str = "SENTINEL-2",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bbox: Optional[List[float]] = None,
    cloud_cover_max: Optional[float] = None,
    product_type: Optional[str] = None,
    max_results: int = 10,
) -> Dict:
    """
    Search Copernicus satellite product catalog via OData API.

    Args:
        collection: Sentinel collection (SENTINEL-1, SENTINEL-2, SENTINEL-3, SENTINEL-5P)
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        bbox: Bounding box [west, south, east, north] in WGS84 degrees.
        cloud_cover_max: Max cloud cover % (Sentinel-2 only, 0-100).
        product_type: Product type filter (e.g. S2MSI2A, GRD).
        max_results: Max number of results (default 10, max 1000).

    Returns:
        dict with 'products' list and 'total_results' count.

    Example:
        # Sentinel-2 imagery over Iowa cornbelt, low cloud cover
        search_products("SENTINEL-2", "2025-07-01", "2025-07-15",
                        bbox=[-96, 41, -90, 43], cloud_cover_max=20)
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Build OData filter
    filters = []
    filters.append(f"Collection/Name eq '{collection}'")
    filters.append(
        f"ContentDate/Start gt {start_date}T00:00:00.000Z "
        f"and ContentDate/Start lt {end_date}T23:59:59.999Z"
    )

    if cloud_cover_max is not None:
        filters.append(
            f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq "
            f"'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {cloud_cover_max:.1f})"
        )

    if product_type:
        filters.append(
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq "
            f"'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}')"
        )

    if bbox and len(bbox) == 4:
        w, s, e, n = bbox
        wkt = f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
        filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')")

    filter_str = " and ".join(filters)

    url = f"{ODATA_BASE}/Products"
    params = {
        "$filter": filter_str,
        "$top": min(max_results, 1000),
        "$orderby": "ContentDate/Start desc",
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        products = []
        for item in data.get("value", []):
            product = {
                "id": item.get("Id"),
                "name": item.get("Name"),
                "collection": collection,
                "sensing_start": item.get("ContentDate", {}).get("Start"),
                "sensing_end": item.get("ContentDate", {}).get("End"),
                "online": item.get("Online", False),
                "size_mb": round(item.get("ContentLength", 0) / (1024 * 1024), 1),
                "footprint": item.get("GeoFootprint", {}).get("coordinates"),
                "publication_date": item.get("PublicationDate"),
            }
            products.append(product)

        return {
            "source": "copernicus_dataspace",
            "collection": collection,
            "date_range": f"{start_date} to {end_date}",
            "total_results": len(products),
            "products": products,
            "query_time": datetime.utcnow().isoformat(),
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "source": "copernicus_dataspace",
            "collection": collection,
            "products": [],
            "total_results": 0,
        }


def get_collections() -> List[Dict]:
    """
    List all available collections in the Copernicus Data Space catalog.

    Returns:
        List of collection dicts with name, description, and temporal extent.
    """
    cache_file = os.path.join(CACHE_DIR, "collections.json")

    # Cache for 24h
    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)

    try:
        url = f"{STAC_BASE}/collections"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        collections = []
        for c in data.get("collections", []):
            collections.append({
                "id": c.get("id"),
                "title": c.get("title"),
                "description": (c.get("description", "") or "")[:200],
                "license": c.get("license"),
                "temporal_start": (c.get("extent", {}).get("temporal", {}).get("interval", [[None]])[0][0]),
                "temporal_end": (c.get("extent", {}).get("temporal", {}).get("interval", [[None, None]])[0][1]),
            })

        # Cache
        with open(cache_file, "w") as f:
            json.dump(collections, f, indent=2)

        return collections

    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]


def search_stac(
    collection: str = "SENTINEL-2",
    bbox: Optional[List[float]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 10,
) -> Dict:
    """
    Search via STAC API (alternative to OData, good for GeoJSON output).

    Args:
        collection: Collection ID (e.g. SENTINEL-2).
        bbox: Bounding box [west, south, east, north].
        start_date: ISO date string.
        end_date: ISO date string.
        max_results: Max features to return.

    Returns:
        dict with 'features' list (GeoJSON-like items).
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    body = {
        "collections": [collection],
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": min(max_results, 100),
    }
    if bbox:
        body["bbox"] = bbox

    try:
        url = f"{STAC_BASE}/search"
        resp = requests.post(url, json=body, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        features = []
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            features.append({
                "id": feat.get("id"),
                "collection": feat.get("collection"),
                "datetime": props.get("datetime"),
                "cloud_cover": props.get("eo:cloud_cover"),
                "platform": props.get("platform"),
                "instrument": props.get("instruments", [None])[0] if isinstance(props.get("instruments"), list) else props.get("instruments"),
                "bbox": feat.get("bbox"),
            })

        return {
            "source": "copernicus_stac",
            "collection": collection,
            "date_range": f"{start_date} to {end_date}",
            "total_features": data.get("numberMatched", len(features)),
            "returned": len(features),
            "features": features,
            "query_time": datetime.utcnow().isoformat(),
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "source": "copernicus_stac",
            "features": [],
            "total_features": 0,
        }


def get_product_details(product_id: str) -> Dict:
    """
    Get full metadata for a specific product by ID.

    Args:
        product_id: UUID of the product (from search results).

    Returns:
        dict with complete product metadata.
    """
    try:
        url = f"{ODATA_BASE}/Products('{product_id}')"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        item = resp.json()

        return {
            "id": item.get("Id"),
            "name": item.get("Name"),
            "content_type": item.get("ContentType"),
            "content_length_mb": round(item.get("ContentLength", 0) / (1024 * 1024), 1),
            "online": item.get("Online"),
            "sensing_start": item.get("ContentDate", {}).get("Start"),
            "sensing_end": item.get("ContentDate", {}).get("End"),
            "publication_date": item.get("PublicationDate"),
            "modification_date": item.get("ModificationDate"),
            "footprint": item.get("GeoFootprint"),
            "checksum": item.get("Checksum"),
            "source": "copernicus_dataspace",
        }

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "product_id": product_id}


def count_products(
    collection: str = "SENTINEL-2",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bbox: Optional[List[float]] = None,
) -> Dict:
    """
    Count available products matching criteria (useful for coverage analysis).

    Args:
        collection: Sentinel collection name.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        bbox: Bounding box [west, south, east, north].

    Returns:
        dict with product count and query parameters.
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    filters = [
        f"Collection/Name eq '{collection}'",
        f"ContentDate/Start gt {start_date}T00:00:00.000Z "
        f"and ContentDate/Start lt {end_date}T23:59:59.999Z",
    ]

    if bbox and len(bbox) == 4:
        w, s, e, n = bbox
        wkt = f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
        filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')")

    filter_str = " and ".join(filters)

    try:
        # $count endpoint not supported; use $top=0 with $count=true
        url = f"{ODATA_BASE}/Products"
        params = {"$filter": filter_str, "$top": 0, "$count": "true"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        count = data.get("@odata.count", len(data.get("value", [])))

        return {
            "source": "copernicus_dataspace",
            "collection": collection,
            "date_range": f"{start_date} to {end_date}",
            "product_count": count,
            "bbox": bbox,
            "query_time": datetime.utcnow().isoformat(),
        }

    except (requests.exceptions.RequestException, ValueError) as e:
        return {
            "error": str(e),
            "source": "copernicus_dataspace",
            "product_count": -1,
        }


def get_crop_monitoring_data(
    region_bbox: List[float],
    days_back: int = 14,
    cloud_cover_max: float = 30.0,
) -> Dict:
    """
    Convenience: search Sentinel-2 L2A data for agricultural monitoring.

    This is a higher-level function tailored for commodity traders who need
    to monitor crop conditions. Returns recent cloud-free optical imagery
    metadata for a given agricultural region.

    Args:
        region_bbox: [west, south, east, north] of agricultural region.
        days_back: How many days to look back (default 14).
        cloud_cover_max: Maximum cloud cover percentage (default 30%).

    Returns:
        dict with imagery availability and basic stats.

    Example:
        # Iowa corn belt monitoring
        get_crop_monitoring_data([-96, 41, -90, 43], days_back=14, cloud_cover_max=20)
    """
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    result = search_products(
        collection="SENTINEL-2",
        start_date=start_date,
        end_date=end_date,
        bbox=region_bbox,
        cloud_cover_max=cloud_cover_max,
        product_type="S2MSI2A",
        max_results=50,
    )

    # Add convenience stats
    products = result.get("products", [])
    result["application"] = "crop_monitoring"
    result["region_bbox"] = region_bbox,
    result["cloud_filter"] = f"<= {cloud_cover_max}%"
    result["imagery_available"] = len(products) > 0
    result["coverage_days"] = days_back

    return result


def get_shipping_sar_data(
    port_bbox: List[float],
    days_back: int = 7,
) -> Dict:
    """
    Convenience: search Sentinel-1 SAR data for maritime/port monitoring.

    SAR (Synthetic Aperture Radar) works day/night and through clouds,
    making it ideal for tracking shipping activity, oil spills, and
    port congestion — useful signals for energy and shipping equities.

    Args:
        port_bbox: [west, south, east, north] around port area.
        days_back: Lookback period in days.

    Returns:
        dict with SAR imagery availability for the port area.

    Example:
        # Port of Rotterdam monitoring
        get_shipping_sar_data([3.8, 51.85, 4.2, 52.05])
    """
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    result = search_products(
        collection="SENTINEL-1",
        start_date=start_date,
        end_date=end_date,
        bbox=port_bbox,
        product_type="GRD",
        max_results=20,
    )

    result["application"] = "maritime_monitoring"
    result["port_bbox"] = port_bbox
    result["radar_type"] = "SAR (works through clouds, day/night)"

    return result


if __name__ == "__main__":
    print(json.dumps({
        "module": "copernicus_open_access_hub_api",
        "status": "active",
        "source": "https://dataspace.copernicus.eu/",
        "functions": [
            "search_products",
            "get_collections",
            "search_stac",
            "get_product_details",
            "count_products",
            "get_crop_monitoring_data",
            "get_shipping_sar_data",
        ],
    }, indent=2))
