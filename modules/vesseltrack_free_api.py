"""
VesselTrack Free API — Maritime Vessel Tracking via Free AIS Data

Data Sources:
  - Finnish Transport Agency Digitraffic Maritime API (primary)
    https://meri.digitraffic.fi — Free, no API key, real-time AIS data
  - Covers: vessel positions, metadata, port calls, sea state warnings

Provides:
  - Real-time vessel positions by MMSI
  - Vessel metadata (name, IMO, callsign, ship type)
  - Vessels in geographic area (lat/lon + radius)
  - Port call records by port (UN/LOCODE) or vessel
  - Sea state warnings and nautical alerts
  - Ship type classification lookup

Usage for Quant Models:
  - Track shipping delays → supply chain disruption signals
  - Monitor port congestion → freight rate indicators
  - Vessel density in chokepoints → trade flow proxies
  - Ferry/cargo schedules → regional economic activity

Free tier: Yes (fully free, no API key)
Update frequency: Real-time AIS with ~1 min lag
Coverage: Finnish waters + Baltic Sea (AIS range)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://meri.digitraffic.fi"
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/vesseltrack")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "Accept-Encoding": "gzip",
    "Accept": "application/json",
    "User-Agent": "QuantClaw-Data/1.0"
}

# AIS Navigation Status codes
NAV_STATUS = {
    0: "Under way using engine",
    1: "At anchor",
    2: "Not under command",
    3: "Restricted manoeuvrability",
    4: "Constrained by draught",
    5: "Moored",
    6: "Aground",
    7: "Engaged in fishing",
    8: "Under way sailing",
    9: "Reserved (HSC)",
    10: "Reserved (WIG)",
    11: "Power-driven vessel towing astern",
    12: "Power-driven vessel pushing ahead",
    14: "AIS-SART (active)",
    15: "Not defined"
}

# Ship type categories (AIS codes)
SHIP_TYPES = {
    (20, 29): "Wing in ground",
    (30, 30): "Fishing",
    (31, 32): "Towing",
    (33, 33): "Dredging",
    (34, 34): "Diving operations",
    (35, 35): "Military operations",
    (36, 36): "Sailing",
    (37, 37): "Pleasure craft",
    (40, 49): "High speed craft",
    (50, 50): "Pilot vessel",
    (51, 51): "Search and rescue",
    (52, 52): "Tug",
    (53, 53): "Port tender",
    (55, 55): "Law enforcement",
    (60, 69): "Passenger",
    (70, 79): "Cargo",
    (80, 89): "Tanker",
    (90, 99): "Other"
}


def _classify_ship_type(code: int) -> str:
    """Classify AIS ship type code into human-readable category."""
    if code is None:
        return "Unknown"
    for (lo, hi), label in SHIP_TYPES.items():
        if lo <= code <= hi:
            return label
    return f"Unknown ({code})"


def _get(path: str, params: Optional[dict] = None, timeout: int = 15) -> dict:
    """Make a GET request to Digitraffic Maritime API."""
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "url": url}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}", "message": str(e), "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "url": url}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "url": url}


def get_vessel_metadata(mmsi: int) -> Dict:
    """
    Get vessel metadata by MMSI number.

    Args:
        mmsi: Maritime Mobile Service Identity (9-digit number)

    Returns:
        dict with vessel name, IMO, callsign, ship type, draught, destination, ETA

    Example:
        >>> get_vessel_metadata(230629000)
        {'mmsi': 230629000, 'name': 'VIKING GRACE', 'imo': 9606900, ...}
    """
    data = _get(f"/api/ais/v1/vessels/{mmsi}")
    if "error" in data:
        return data

    return {
        "mmsi": data.get("mmsi"),
        "name": data.get("name"),
        "imo": data.get("imo"),
        "call_sign": data.get("callSign"),
        "destination": data.get("destination"),
        "ship_type_code": data.get("shipType"),
        "ship_type": _classify_ship_type(data.get("shipType")),
        "draught_dm": data.get("draught"),
        "draught_m": round(data.get("draught", 0) / 10, 1) if data.get("draught") else None,
        "eta_raw": data.get("eta"),
        "timestamp": data.get("timestamp"),
        "timestamp_utc": datetime.utcfromtimestamp(data["timestamp"] / 1000).isoformat() + "Z" if data.get("timestamp") else None,
        "source": "digitraffic.fi"
    }


def get_vessels_in_area(latitude: float, longitude: float, radius: int = 10) -> List[Dict]:
    """
    Get all vessel positions within a radius of a geographic point.

    Args:
        latitude: Center latitude (e.g., 60.1 for Helsinki)
        longitude: Center longitude (e.g., 24.9 for Helsinki)
        radius: Search radius in km (default 10)

    Returns:
        list of dicts with vessel MMSI, position, speed, heading, nav status

    Example:
        >>> vessels = get_vessels_in_area(60.1, 24.9, radius=15)
        >>> len(vessels)
        42
    """
    data = _get(f"/api/ais/v1/locations", params={
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius
    })
    if "error" in data:
        return [data]

    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None])
        ts = props.get("timestampExternal")
        results.append({
            "mmsi": props.get("mmsi"),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "speed_knots": props.get("sog"),
            "course": props.get("cog"),
            "heading": props.get("heading") if props.get("heading") != 511 else None,
            "nav_status_code": props.get("navStat"),
            "nav_status": NAV_STATUS.get(props.get("navStat"), "Unknown"),
            "position_accuracy": props.get("posAcc"),
            "timestamp_utc": datetime.utcfromtimestamp(ts / 1000).isoformat() + "Z" if ts else None,
        })

    return results


def get_port_calls(locode: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
    """
    Get port call records for a port identified by UN/LOCODE.

    Args:
        locode: UN/LOCODE port code (e.g., 'FIHEL' for Helsinki, 'EETLL' for Tallinn)
        from_date: Start date ISO format (default: 7 days ago)
        to_date: End date ISO format (default: now)

    Returns:
        list of dicts with vessel info, arrival/departure times, cargo status

    Example:
        >>> calls = get_port_calls('FIHEL')
        >>> calls[0]['vessel_name']
        'Finlandia'
    """
    if from_date is None:
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
    if to_date is None:
        to_date = datetime.utcnow().strftime("%Y-%m-%dT23:59:59Z")

    data = _get("/api/port-call/v1/port-calls", params={
        "locode": locode,
        "from": from_date
    })
    if "error" in data:
        return [data]

    port_calls = data.get("portCalls", [])
    results = []
    for pc in port_calls[:100]:  # Cap at 100
        results.append({
            "port_call_id": pc.get("portCallId"),
            "port": pc.get("portToVisit"),
            "vessel_name": pc.get("vesselName"),
            "vessel_name_prefix": pc.get("vesselNamePrefix"),
            "imo": pc.get("imoLloyds"),
            "mmsi": pc.get("mmsi"),
            "nationality": pc.get("nationality"),
            "call_sign": pc.get("radioCallSign"),
            "vessel_type_code": pc.get("vesselTypeCode"),
            "prev_port": pc.get("prevPort"),
            "next_port": pc.get("nextPort"),
            "arrival_with_cargo": pc.get("arrivalWithCargo"),
            "discharge": pc.get("discharge"),
            "domestic_traffic_arrival": pc.get("domesticTrafficArrival"),
            "security_level": pc.get("currentSecurityLevel"),
            "timestamp": pc.get("portCallTimestamp"),
            "source": "digitraffic.fi"
        })

    return results


def get_vessel_port_calls(mmsi: int, from_date: Optional[str] = None) -> List[Dict]:
    """
    Get port call history for a specific vessel by MMSI.

    Args:
        mmsi: Maritime Mobile Service Identity
        from_date: Start date ISO format (default: 30 days ago)

    Returns:
        list of port calls for the vessel

    Example:
        >>> calls = get_vessel_port_calls(230629000)
    """
    if from_date is None:
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")

    data = _get("/api/port-call/v1/port-calls", params={
        "vesselMmsi": mmsi,
        "from": from_date
    })
    if "error" in data:
        return [data]

    port_calls = data.get("portCalls", [])
    results = []
    for pc in port_calls:
        results.append({
            "port_call_id": pc.get("portCallId"),
            "port": pc.get("portToVisit"),
            "prev_port": pc.get("prevPort"),
            "next_port": pc.get("nextPort"),
            "vessel_name": pc.get("vesselName"),
            "arrival_with_cargo": pc.get("arrivalWithCargo"),
            "timestamp": pc.get("portCallTimestamp"),
        })

    return results


def get_sea_warnings() -> List[Dict]:
    """
    Get active nautical warnings and sea state alerts.

    Returns:
        list of active maritime warnings (navigation hazards, weather, ice)

    Example:
        >>> warnings = get_sea_warnings()
        >>> len(warnings)
        5
    """
    data = _get("/api/nautical-warning/v2/warnings/active")
    if "error" in data:
        return [data]

    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates") if f.get("geometry") else None
        results.append({
            "id": props.get("id"),
            "type": props.get("type"),
            "number": props.get("number"),
            "area": props.get("area"),
            "location_description": props.get("location", {}).get("en") if isinstance(props.get("location"), dict) else props.get("location"),
            "description": props.get("contents", [{}])[0].get("en") if props.get("contents") else None,
            "valid_from": props.get("publishingTime"),
            "coordinates": coords,
            "source": "digitraffic.fi"
        })

    return results


def get_port_traffic_summary(locode: str, days: int = 7) -> Dict:
    """
    Get a summary of port traffic volume for quant analysis.

    Args:
        locode: UN/LOCODE port code (e.g., 'FIHEL')
        days: Lookback period in days (default 7)

    Returns:
        dict with total calls, unique vessels, nationality breakdown, cargo stats

    Example:
        >>> summary = get_port_traffic_summary('FIHEL', days=7)
        >>> summary['total_calls']
        156
    """
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    calls = get_port_calls(locode, from_date=from_date)

    if not calls or (len(calls) == 1 and "error" in calls[0]):
        return {"error": "Failed to fetch port calls", "port": locode}

    nationalities = {}
    vessel_types = {}
    unique_vessels = set()
    cargo_arrivals = 0

    for c in calls:
        nat = c.get("nationality", "Unknown")
        nationalities[nat] = nationalities.get(nat, 0) + 1

        vtype = c.get("vessel_type_code")
        vtype_label = _classify_ship_type(vtype) if vtype else "Unknown"
        vessel_types[vtype_label] = vessel_types.get(vtype_label, 0) + 1

        if c.get("mmsi"):
            unique_vessels.add(c["mmsi"])
        if c.get("arrival_with_cargo"):
            cargo_arrivals += 1

    return {
        "port": locode,
        "period_days": days,
        "total_calls": len(calls),
        "unique_vessels": len(unique_vessels),
        "cargo_arrivals": cargo_arrivals,
        "cargo_ratio": round(cargo_arrivals / max(len(calls), 1), 2),
        "nationalities": dict(sorted(nationalities.items(), key=lambda x: -x[1])),
        "vessel_types": dict(sorted(vessel_types.items(), key=lambda x: -x[1])),
        "source": "digitraffic.fi",
        "generated_utc": datetime.utcnow().isoformat() + "Z"
    }


def search_vessel_by_name(name: str) -> List[Dict]:
    """
    Search for vessels by name using port call records.
    Note: Digitraffic doesn't have a direct vessel search, so this
    searches recent port calls for matching vessel names.

    Args:
        name: Vessel name or partial name (case-insensitive)

    Returns:
        list of matching vessels with MMSI, IMO, and last known port

    Example:
        >>> results = search_vessel_by_name('Viking')
        >>> results[0]['vessel_name']
        'VIKING GRACE'
    """
    from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")

    data = _get("/api/port-call/v1/port-calls", params={
        "from": from_date
    })
    if "error" in data:
        return [data]

    port_calls = data.get("portCalls", [])
    name_lower = name.lower()
    seen = set()
    results = []

    for pc in port_calls:
        vname = pc.get("vesselName", "")
        mmsi = pc.get("mmsi")
        if name_lower in vname.lower() and mmsi not in seen:
            seen.add(mmsi)
            results.append({
                "vessel_name": vname,
                "mmsi": mmsi,
                "imo": pc.get("imoLloyds"),
                "call_sign": pc.get("radioCallSign"),
                "nationality": pc.get("nationality"),
                "last_port": pc.get("portToVisit"),
                "last_seen": pc.get("portCallTimestamp"),
            })

    return results


def get_area_vessel_count(latitude: float, longitude: float, radius: int = 50) -> Dict:
    """
    Count vessels in an area — useful as a trade activity proxy.

    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius: Radius in km (default 50)

    Returns:
        dict with total count, breakdown by nav status

    Example:
        >>> count = get_area_vessel_count(60.1, 24.9, radius=30)
        >>> count['total']
        87
    """
    vessels = get_vessels_in_area(latitude, longitude, radius)
    if not vessels or (len(vessels) == 1 and "error" in vessels[0]):
        return {"error": "Failed to fetch vessel positions"}

    status_counts = {}
    moving = 0
    for v in vessels:
        status = v.get("nav_status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if v.get("speed_knots", 0) > 0.5:
            moving += 1

    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius,
        "total": len(vessels),
        "moving": moving,
        "stationary": len(vessels) - moving,
        "by_status": status_counts,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "source": "digitraffic.fi"
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "vesseltrack_free_api",
        "status": "active",
        "source": "https://meri.digitraffic.fi",
        "functions": [
            "get_vessel_metadata",
            "get_vessels_in_area",
            "get_port_calls",
            "get_vessel_port_calls",
            "get_sea_warnings",
            "get_port_traffic_summary",
            "search_vessel_by_name",
            "get_area_vessel_count"
        ]
    }, indent=2))
