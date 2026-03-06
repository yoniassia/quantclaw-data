#!/usr/bin/env python3
"""
Maxar Open Data Program
High-resolution satellite imagery for event-driven analysis (disasters, conflicts, geopolitical events).
Source: https://www.maxar.com/open-data
Free tier: Completely free with no quotas for public datasets
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "https://www.maxar.com/open-data"

def list_events() -> List[Dict]:
    """
    List available Maxar Open Data events.
    Returns basic metadata for publicly available imagery collections.
    
    Returns:
        List of event dictionaries with name, date, location, type
    """
    # Maxar maintains a public catalog at their open data page
    # This is a curated list of major events (updated manually from public sources)
    events = [
        {"event_id": "turkiye-earthquake-23", "name": "Turkey-Syria Earthquake", "date": "2023-02-06", "location": "Turkey/Syria", "type": "natural_disaster", "category": "earthquake"},
        {"event_id": "ukraine-conflict-22", "name": "Ukraine Conflict", "date": "2022-02-24", "location": "Ukraine", "type": "geopolitical", "category": "conflict"},
        {"event_id": "morocco-earthquake-23", "name": "Morocco Earthquake", "date": "2023-09-08", "location": "Morocco", "type": "natural_disaster", "category": "earthquake"},
        {"event_id": "maui-wildfires-23", "name": "Maui Wildfires", "date": "2023-08-08", "location": "Hawaii, USA", "type": "natural_disaster", "category": "wildfire"},
        {"event_id": "libya-floods-23", "name": "Libya Floods", "date": "2023-09-10", "location": "Libya", "type": "natural_disaster", "category": "flood"},
    ]
    
    return events

def get_event_metadata(event_id: str) -> Optional[Dict]:
    """
    Get metadata for a specific Maxar Open Data event.
    
    Args:
        event_id: Event identifier (e.g., 'turkiye-earthquake-23')
        
    Returns:
        Event metadata including imagery details and download links
    """
    events = list_events()
    event = next((e for e in events if e["event_id"] == event_id), None)
    
    if not event:
        return None
    
    # Metadata structure for satellite imagery
    event["imagery"] = {
        "resolution": "30cm-50cm",
        "format": "GeoTIFF",
        "projection": "WGS84",
        "download_url": f"https://www.maxar.com/open-data/{event_id}",
        "coverage_area_km2": "varies by event",
    }
    
    event["financial_use_cases"] = [
        "Infrastructure damage assessment",
        "Supply chain disruption monitoring",
        "Insurance claims validation",
        "Geopolitical risk modeling",
        "Agricultural yield impact",
    ]
    
    return event

def get_disaster_timeline() -> List[Dict]:
    """
    Get chronological timeline of Maxar Open Data events for risk correlation.
    Useful for backtesting event-driven trading strategies.
    
    Returns:
        Sorted list of events by date
    """
    events = list_events()
    return sorted(events, key=lambda x: x["date"], reverse=True)

def filter_events_by_type(event_type: str) -> List[Dict]:
    """
    Filter events by type (natural_disaster, geopolitical).
    
    Args:
        event_type: 'natural_disaster' or 'geopolitical'
        
    Returns:
        Filtered list of events
    """
    events = list_events()
    return [e for e in events if e["type"] == event_type]

def get_risk_indicators() -> Dict:
    """
    Generate risk indicators from Maxar Open Data event frequency.
    
    Returns:
        Dictionary with risk metrics (event count by type, geographic distribution)
    """
    events = list_events()
    
    risk_data = {
        "total_events": len(events),
        "by_type": {},
        "by_category": {},
        "geographic_spread": len(set(e["location"] for e in events)),
        "latest_event": max(events, key=lambda x: x["date"]) if events else None,
    }
    
    for event in events:
        event_type = event["type"]
        category = event.get("category", "unknown")
        
        risk_data["by_type"][event_type] = risk_data["by_type"].get(event_type, 0) + 1
        risk_data["by_category"][category] = risk_data["by_category"].get(category, 0) + 1
    
    return risk_data

def search_events(query: str) -> List[Dict]:
    """
    Search events by keyword in name or location.
    
    Args:
        query: Search term (case-insensitive)
        
    Returns:
        List of matching events
    """
    events = list_events()
    query = query.lower()
    return [
        e for e in events 
        if query in e["name"].lower() or query in e["location"].lower()
    ]

if __name__ == "__main__":
    # Test the module
    print("=== Maxar Open Data Program ===\n")
    
    # List all events
    events = list_events()
    print(f"Total events: {len(events)}\n")
    
    # Show timeline
    timeline = get_disaster_timeline()
    print("Recent events:")
    for event in timeline[:3]:
        print(f"  {event['date']}: {event['name']} ({event['location']})")
    
    # Risk indicators
    print("\n=== Risk Indicators ===")
    risk = get_risk_indicators()
    print(json.dumps(risk, indent=2, default=str))
    
    # Event metadata
    print("\n=== Sample Event Metadata ===")
    if timeline:
        metadata = get_event_metadata(timeline[0]["event_id"])
        print(json.dumps(metadata, indent=2))
