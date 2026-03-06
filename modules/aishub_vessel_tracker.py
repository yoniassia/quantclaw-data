"""
AISHub Vessel Tracker — Real-time vessel positions via AIS data feed.

Automatic Identification System (AIS) data for global maritime traffic.
Tracks vessel positions, speed, course, and destination for supply chain analysis.

Source: https://www.aishub.net
Update frequency: Real-time (free tier: 1000 messages/day)
Category: Trade & Supply Chain
"""

import json
import urllib.request
from datetime import datetime
from typing import Any, Optional


AISHUB_BASE = "http://data.aishub.net/ws.php"


def get_vessels_in_area(
    north: float, south: float, east: float, west: float,
    username: Optional[str] = None
) -> dict[str, Any]:
    """
    Get all vessels in a geographic bounding box.
    
    Args:
        north: Northern latitude boundary
        south: Southern latitude boundary  
        east: Eastern longitude boundary
        west: Western longitude boundary
        username: AISHub username (optional, increases rate limit)
    
    Returns:
        Dictionary with vessel list and metadata
        
    Example:
        # Singapore Strait area
        get_vessels_in_area(north=1.5, south=1.0, east=104.5, west=103.5)
    """
    params = {
        "format": "1",  # JSON format
        "north": north,
        "south": south,
        "east": east,
        "west": west,
        "output": "json"
    }
    
    if username:
        params["username"] = username
        
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{AISHUB_BASE}?{query}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            
        vessels = []
        error_count = data.get("ERROR", False)
        
        if error_count:
            return {
                "error": "AISHub API error",
                "error_code": error_count,
                "message": "Check rate limits or parameters"
            }
            
        # Parse vessel data from response
        for entry in data:
            if isinstance(entry, dict) and "MMSI" in entry:
                vessel = {
                    "mmsi": entry.get("MMSI"),
                    "name": entry.get("NAME", "Unknown").strip(),
                    "latitude": float(entry.get("LATITUDE", 0)),
                    "longitude": float(entry.get("LONGITUDE", 0)),
                    "speed_knots": float(entry.get("SPEED", 0)) / 10,  # AISHub reports in tenths
                    "course": float(entry.get("COURSE", 0)) / 10,
                    "heading": entry.get("HEADING", 0),
                    "type": entry.get("TYPE", 0),
                    "destination": entry.get("DESTINATION", "").strip(),
                    "eta": entry.get("ETA", ""),
                    "timestamp": entry.get("TIME", ""),
                    "imo": entry.get("IMO", "")
                }
                vessels.append(vessel)
                
        return {
            "vessels": vessels,
            "count": len(vessels),
            "area": {
                "north": north,
                "south": south,
                "east": east,
                "west": west
            },
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {"error": str(e), "url": url}


def get_vessel_by_mmsi(mmsi: int, username: Optional[str] = None) -> dict[str, Any]:
    """
    Get current position and details for a specific vessel by MMSI number.
    
    Args:
        mmsi: Maritime Mobile Service Identity number
        username: AISHub username (optional)
        
    Returns:
        Vessel details dictionary
    """
    params = {
        "format": "1",
        "mmsi": mmsi,
        "output": "json"
    }
    
    if username:
        params["username"] = username
        
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{AISHUB_BASE}?{query}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            
        if not data or (isinstance(data, list) and len(data) == 0):
            return {"error": "Vessel not found", "mmsi": mmsi}
            
        entry = data[0] if isinstance(data, list) else data
        
        return {
            "mmsi": entry.get("MMSI"),
            "name": entry.get("NAME", "Unknown").strip(),
            "position": {
                "latitude": float(entry.get("LATITUDE", 0)),
                "longitude": float(entry.get("LONGITUDE", 0))
            },
            "speed_knots": float(entry.get("SPEED", 0)) / 10,
            "course": float(entry.get("COURSE", 0)) / 10,
            "heading": entry.get("HEADING", 0),
            "vessel_type": entry.get("TYPE", 0),
            "destination": entry.get("DESTINATION", "").strip(),
            "eta": entry.get("ETA", ""),
            "imo": entry.get("IMO", ""),
            "callsign": entry.get("CALLSIGN", ""),
            "last_update": entry.get("TIME", ""),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {"error": str(e), "mmsi": mmsi}


def get_vessels_by_type(vessel_type: int, username: Optional[str] = None) -> dict[str, Any]:
    """
    Get vessels of a specific type (cargo, tanker, etc).
    
    Vessel types (AIS standard):
    - 70-79: Cargo vessels
    - 80-89: Tanker vessels
    - 60-69: Passenger vessels
    - 30-39: Fishing vessels
    
    Args:
        vessel_type: AIS vessel type code
        username: AISHub username (optional)
        
    Returns:
        Dictionary with matching vessels
    """
    params = {
        "format": "1",
        "type": vessel_type,
        "output": "json"
    }
    
    if username:
        params["username"] = username
        
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{AISHUB_BASE}?{query}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            
        vessels = []
        for entry in data:
            if isinstance(entry, dict) and "MMSI" in entry:
                vessels.append({
                    "mmsi": entry.get("MMSI"),
                    "name": entry.get("NAME", "Unknown").strip(),
                    "latitude": float(entry.get("LATITUDE", 0)),
                    "longitude": float(entry.get("LONGITUDE", 0)),
                    "speed_knots": float(entry.get("SPEED", 0)) / 10,
                    "destination": entry.get("DESTINATION", "").strip()
                })
                
        return {
            "vessels": vessels,
            "count": len(vessels),
            "vessel_type": vessel_type,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {"error": str(e)}


def get_major_shipping_lanes() -> dict[str, Any]:
    """
    Get predefined bounding boxes for major global shipping lanes.
    
    Returns:
        Dictionary of shipping lane areas
    """
    lanes = {
        "suez_canal": {
            "name": "Suez Canal",
            "north": 31.5,
            "south": 29.5,
            "east": 33.0,
            "west": 32.0
        },
        "singapore_strait": {
            "name": "Singapore Strait",
            "north": 1.5,
            "south": 1.0,
            "east": 104.5,
            "west": 103.5
        },
        "panama_canal": {
            "name": "Panama Canal",
            "north": 9.5,
            "south": 8.5,
            "east": -79.0,
            "west": -80.0
        },
        "english_channel": {
            "name": "English Channel",
            "north": 51.0,
            "south": 50.0,
            "east": 1.5,
            "west": -1.0
        },
        "malacca_strait": {
            "name": "Malacca Strait",
            "north": 6.0,
            "south": 1.0,
            "east": 101.0,
            "west": 99.0
        }
    }
    
    return {
        "shipping_lanes": lanes,
        "note": "Use coordinates with get_vessels_in_area() to monitor these critical routes"
    }


if __name__ == "__main__":
    # Example usage
    print("AISHub Vessel Tracker — Testing Singapore Strait")
    result = get_vessels_in_area(north=1.5, south=1.0, east=104.5, west=103.5)
    print(json.dumps(result, indent=2))
