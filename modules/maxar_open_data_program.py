#!/usr/bin/env python3
"""
Maxar Open Data Program — Satellite Imagery for Disaster & Event-Driven Analysis

Data Source: Maxar Open Data Program (STAC Catalog on AWS S3)
URL: https://www.maxar.com/open-data
License: CC-BY-NC-4.0
Update: Event-driven (disasters, geopolitical events)
Free: Yes (public S3 bucket, no API key required)

Provides:
- Catalog of disaster/event satellite imagery datasets
- Event metadata (earthquakes, hurricanes, floods, wildfires, etc.)
- STAC collection details with acquisition IDs
- Event filtering by type, region, year
- Image asset URLs for GeoTIFF downloads

Quant Trading Relevance:
- Natural disaster impact on supply chains, insurance, commodities
- Geopolitical event verification via satellite imagery
- Infrastructure damage assessment for REIT/insurance exposure
- Agricultural disaster monitoring for commodity trading
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/maxar_open_data")
os.makedirs(CACHE_DIR, exist_ok=True)

CATALOG_URL = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"
COLLECTION_BASE = "https://maxar-opendata.s3.amazonaws.com/events"

# Event type classification based on common naming patterns
EVENT_TYPES = {
    "earthquake": ["earthquake", "quake"],
    "hurricane": ["hurricane", "cyclone", "typhoon", "tropical"],
    "flood": ["flood", "flooding"],
    "wildfire": ["fire", "wildfire"],
    "volcano": ["volcano", "eruption"],
    "landslide": ["landslide"],
    "tornado": ["tornado"],
}

HEADERS = {
    "User-Agent": "QuantClaw-Data/1.0 (research)",
    "Accept": "application/json",
}


def _classify_event(event_id: str) -> str:
    """Classify an event ID into a disaster type."""
    lower = event_id.lower()
    for event_type, keywords in EVENT_TYPES.items():
        for kw in keywords:
            if kw in lower:
                return event_type
    return "other"


def _extract_year(event_id: str) -> Optional[int]:
    """Extract year from event ID string."""
    # Try patterns like -2025, -23, -22, -24, -Sept-2023, etc.
    # 4-digit year
    match = re.search(r'(\d{4})', event_id)
    if match:
        year = int(match.group(1))
        if 2000 <= year <= 2030:
            return year
    # 2-digit year suffix like -23, -22
    match = re.search(r'-(\d{2})(?:/|$)', event_id)
    if match:
        yr = int(match.group(1))
        return 2000 + yr if yr < 50 else 1900 + yr
    return None


def _get_cached(cache_key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Return cached data if fresh enough."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=max_age_hours):
            with open(cache_file) as f:
                return json.load(f)
    return None


def _set_cache(cache_key: str, data: dict):
    """Write data to cache."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_catalog() -> Dict:
    """
    Fetch the full Maxar Open Data STAC catalog.

    Returns dict with:
        - id: catalog identifier
        - description: catalog description
        - events: list of event dicts with id, href, event_type, year
        - total_events: count of available events
        - fetched_at: timestamp

    Example:
        >>> catalog = get_catalog()
        >>> print(catalog['total_events'])
        45
    """
    cached = _get_cached("catalog", max_age_hours=6)
    if cached:
        return cached

    try:
        resp = requests.get(CATALOG_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        events = []
        for link in data.get("links", []):
            if link.get("rel") == "child":
                href = link["href"]
                # Extract event ID from path like ./Event-Name/collection.json
                event_id = href.replace("./", "").replace("/collection.json", "")
                events.append({
                    "id": event_id,
                    "href": f"{COLLECTION_BASE}/{event_id}/collection.json",
                    "event_type": _classify_event(event_id),
                    "year": _extract_year(event_id),
                })

        result = {
            "id": data.get("id", "maxar-opendata"),
            "description": data.get("description", ""),
            "license": data.get("license", "CC-BY-NC-4.0"),
            "stac_version": data.get("stac_version", ""),
            "events": events,
            "total_events": len(events),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _set_cache("catalog", result)
        return result

    except requests.RequestException as e:
        return {"error": str(e), "events": [], "total_events": 0}


def list_events(event_type: Optional[str] = None, year: Optional[int] = None) -> List[Dict]:
    """
    List all available disaster/event datasets with optional filtering.

    Args:
        event_type: Filter by type (earthquake, hurricane, flood, wildfire, volcano, etc.)
        year: Filter by year (e.g., 2024)

    Returns list of event dicts with id, event_type, year, href.

    Example:
        >>> events = list_events(event_type="earthquake")
        >>> for e in events:
        ...     print(e['id'], e['year'])
    """
    catalog = get_catalog()
    events = catalog.get("events", [])

    if event_type:
        events = [e for e in events if e["event_type"] == event_type.lower()]
    if year:
        events = [e for e in events if e.get("year") == year]

    return events


def get_event_details(event_id: str) -> Dict:
    """
    Fetch detailed STAC collection metadata for a specific event.

    Args:
        event_id: Event identifier (e.g., 'Earthquake-Myanmar-March-2025')

    Returns dict with:
        - id: event identifier
        - type: STAC type (Collection)
        - acquisitions: list of acquisition IDs with URLs
        - total_acquisitions: count
        - links: raw STAC links

    Example:
        >>> details = get_event_details("Earthquake-Myanmar-March-2025")
        >>> print(details['total_acquisitions'])
        22
    """
    cache_key = f"event_{event_id.replace('/', '_')}"
    cached = _get_cached(cache_key, max_age_hours=12)
    if cached:
        return cached

    url = f"{COLLECTION_BASE}/{event_id}/collection.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        acquisitions = []
        for link in data.get("links", []):
            if link.get("rel") == "child":
                href = link["href"]
                # Extract acquisition ID from path
                acq_match = re.search(r'([A-F0-9]{16})_collection\.json', href)
                if acq_match:
                    acq_id = acq_match.group(1)
                    acquisitions.append({
                        "acquisition_id": acq_id,
                        "collection_url": f"{COLLECTION_BASE}/{event_id}/ard/acquisition_collections/{acq_id}_collection.json",
                    })

        result = {
            "id": data.get("id", event_id),
            "type": data.get("type", "Collection"),
            "stac_version": data.get("stac_version", ""),
            "event_type": _classify_event(event_id),
            "year": _extract_year(event_id),
            "acquisitions": acquisitions,
            "total_acquisitions": len(acquisitions),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _set_cache(cache_key, result)
        return result

    except requests.RequestException as e:
        return {"error": str(e), "id": event_id, "acquisitions": [], "total_acquisitions": 0}


def get_event_summary() -> Dict:
    """
    Get a summary of all events grouped by type and year.

    Returns dict with:
        - by_type: count of events per disaster type
        - by_year: count of events per year
        - total_events: total count
        - latest_events: 5 most recent events

    Example:
        >>> summary = get_event_summary()
        >>> print(summary['by_type'])
        {'earthquake': 6, 'hurricane': 8, 'flood': 12, ...}
    """
    catalog = get_catalog()
    events = catalog.get("events", [])

    by_type = {}
    by_year = {}
    for e in events:
        t = e.get("event_type", "other")
        by_type[t] = by_type.get(t, 0) + 1
        y = e.get("year")
        if y:
            by_year[y] = by_year.get(y, 0) + 1

    # Sort events by year descending for latest
    sorted_events = sorted(
        [e for e in events if e.get("year")],
        key=lambda x: x["year"],
        reverse=True,
    )

    return {
        "by_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
        "by_year": dict(sorted(by_year.items(), key=lambda x: x[0], reverse=True)),
        "total_events": len(events),
        "latest_events": sorted_events[:5],
        "fetched_at": datetime.utcnow().isoformat(),
    }


def search_events(query: str) -> List[Dict]:
    """
    Search events by keyword in event ID.

    Args:
        query: Search string (e.g., 'Turkey', 'Hawaii', 'Myanmar')

    Returns list of matching event dicts.

    Example:
        >>> results = search_events("Turkey")
        >>> print(results[0]['id'])
        'Kahramanmaras-turkey-earthquake-23'
    """
    catalog = get_catalog()
    events = catalog.get("events", [])
    query_lower = query.lower()
    return [e for e in events if query_lower in e["id"].lower()]


def get_recent_events(limit: int = 10) -> List[Dict]:
    """
    Get the most recent events by year.

    Args:
        limit: Maximum number of events to return (default 10)

    Returns list of event dicts sorted by year descending.

    Example:
        >>> recent = get_recent_events(5)
        >>> print(recent[0]['id'], recent[0]['year'])
    """
    catalog = get_catalog()
    events = catalog.get("events", [])
    sorted_events = sorted(
        [e for e in events if e.get("year")],
        key=lambda x: x["year"],
        reverse=True,
    )
    return sorted_events[:limit]


if __name__ == "__main__":
    print(json.dumps({
        "module": "maxar_open_data_program",
        "status": "active",
        "source": "https://maxar-opendata.s3.amazonaws.com/events/catalog.json",
        "functions": [
            "get_catalog", "list_events", "get_event_details",
            "get_event_summary", "search_events", "get_recent_events"
        ],
    }, indent=2))
