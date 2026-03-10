#!/usr/bin/env python3
"""
MarineTraffic Open Data — Maritime AIS & Port Call Intelligence

Uses Digitraffic Marine API (Finnish Transport Infrastructure Agency)
— a fully free, no-API-key, open-data source for real-time AIS vessel
positions, vessel metadata, port calls, and port information.

Data Source: https://meri.digitraffic.fi
Category: Infrastructure & Transport
Free tier: True (completely free, no key required)
Update frequency: Real-time (AIS positions update every few seconds)

Provides:
- Real-time AIS vessel positions (lat/lon, speed, heading, course)
- Vessel metadata by MMSI (name, IMO, ship type, destination)
- Port call records (arrivals, departures, cargo status)
- Port metadata with UN/LOCODE and coordinates
- Navigation status interpretation
- Ship type classification

Usage for Quant:
- Trade flow analysis via port call volumes
- Supply chain disruption detection (delayed arrivals)
- Commodity shipping patterns (tanker tracking)
- Congestion metrics from port call density
"""

import requests
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/marinetraffic")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://meri.digitraffic.fi"
HEADERS = {
    "Accept-Encoding": "gzip",
    "Accept": "application/json",
    "User-Agent": "QuantClaw/1.0"
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
    12: "Power-driven vessel pushing ahead/towing alongside",
    13: "Reserved",
    14: "AIS-SART / MOB / EPIRB",
    15: "Undefined / default"
}

# AIS Ship Type codes (broad categories)
SHIP_TYPES = {
    (20, 29): "Wing in ground (WIG)",
    (30, 30): "Fishing",
    (31, 32): "Towing",
    (33, 33): "Dredging/Underwater ops",
    (34, 34): "Diving ops",
    (35, 35): "Military ops",
    (36, 36): "Sailing",
    (37, 37): "Pleasure craft",
    (40, 49): "High-speed craft (HSC)",
    (50, 50): "Pilot vessel",
    (51, 51): "Search and rescue",
    (52, 52): "Tug",
    (53, 53): "Port tender",
    (54, 54): "Anti-pollution equipment",
    (55, 55): "Law enforcement",
    (58, 58): "Medical transport",
    (60, 69): "Passenger",
    (70, 79): "Cargo",
    (80, 89): "Tanker",
    (90, 99): "Other"
}


def _get_ship_type_name(code: int) -> str:
    """Convert AIS ship type code to human-readable name."""
    if code is None:
        return "Unknown"
    for (lo, hi), name in SHIP_TYPES.items():
        if lo <= code <= hi:
            return name
    return f"Unknown ({code})"


def _request(endpoint: str, params: Optional[Dict] = None, timeout: int = 15) -> Dict:
    """Make a request to the Digitraffic Marine API."""
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "endpoint": endpoint}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}", "message": str(e), "endpoint": endpoint}
    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e), "endpoint": endpoint}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "endpoint": endpoint}


def get_all_vessel_locations(limit: int = 100) -> List[Dict]:
    """
    Get real-time AIS positions for all tracked vessels.

    Returns list of vessel positions with coordinates, speed, heading.
    Data from Finnish waters / Baltic Sea AIS network.

    Args:
        limit: Max number of vessels to return (default 100, API returns thousands)

    Returns:
        List of dicts with mmsi, lat, lon, sog, cog, heading, nav_status
    """
    data = _request("/api/ais/v1/locations")
    if "error" in data:
        return [data]

    features = data.get("features", [])
    results = []
    for f in features[:limit]:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None])
        nav_code = props.get("navStat")
        results.append({
            "mmsi": props.get("mmsi") or f.get("mmsi"),
            "longitude": coords[0],
            "latitude": coords[1],
            "speed_knots": props.get("sog"),
            "course_over_ground": props.get("cog"),
            "heading": props.get("heading"),
            "nav_status": NAV_STATUS.get(nav_code, f"Unknown ({nav_code})"),
            "nav_status_code": nav_code,
            "position_accuracy": props.get("posAcc"),
            "data_updated": data.get("dataUpdatedTime")
        })
    return results


def get_vessel_info(mmsi: int) -> Dict:
    """
    Get vessel metadata by MMSI number.

    Args:
        mmsi: Maritime Mobile Service Identity (9-digit number)

    Returns:
        Dict with vessel name, IMO, call sign, ship type, destination, draught
    """
    data = _request(f"/api/ais/v1/vessels/{mmsi}")
    if "error" in data:
        return data

    return {
        "mmsi": mmsi,
        "name": data.get("name"),
        "imo": data.get("imo"),
        "call_sign": data.get("callSign"),
        "destination": data.get("destination"),
        "ship_type_code": data.get("shipType"),
        "ship_type": _get_ship_type_name(data.get("shipType")),
        "draught_dm": data.get("draught"),
        "eta": data.get("eta"),
        "timestamp": data.get("timestamp"),
        "position_type": data.get("posType"),
        "dimensions": {
            "bow_to_ref_m": data.get("referencePointA"),
            "stern_to_ref_m": data.get("referencePointB"),
            "port_to_ref_m": data.get("referencePointC"),
            "starboard_to_ref_m": data.get("referencePointD"),
        }
    }


def get_port_calls(from_date: Optional[str] = None, port_locode: Optional[str] = None,
                   vessel_name: Optional[str] = None, nationality: Optional[str] = None,
                   limit: int = 50) -> List[Dict]:
    """
    Get port call records (arrivals and departures).

    Highly valuable for trade flow analysis — shows which vessels visited
    which ports, cargo status, and timing.

    Args:
        from_date: ISO date string (default: last 24h). e.g. '2026-03-08T00:00:00Z'
        port_locode: Filter by UN/LOCODE (e.g. 'FIHEL' for Helsinki)
        vessel_name: Filter by vessel name (partial match)
        nationality: Filter by vessel flag state (2-letter code, e.g. 'FI')
        limit: Max results to return

    Returns:
        List of port call records with vessel info, timing, cargo status
    """
    if from_date is None:
        from_dt = datetime.now(timezone.utc) - timedelta(hours=24)
        from_date = from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {"from": from_date}
    if vessel_name:
        params["vesselName"] = vessel_name
    if nationality:
        params["nationality"] = nationality

    data = _request("/api/port-call/v1/port-calls", params=params)
    if "error" in data:
        return [data]

    calls = data.get("portCalls", [])
    results = []
    for c in calls:
        # Filter by port if specified
        if port_locode and c.get("portToVisit") != port_locode:
            continue

        results.append({
            "port_call_id": c.get("portCallId"),
            "vessel_name": c.get("vesselName"),
            "vessel_name_prefix": c.get("vesselNamePrefix"),
            "mmsi": c.get("mmsi"),
            "imo": c.get("imoLloyds"),
            "call_sign": c.get("radioCallSign"),
            "nationality": c.get("nationality"),
            "vessel_type_code": c.get("vesselTypeCode"),
            "vessel_type": _get_ship_type_name(c.get("vesselTypeCode", 0)),
            "port_visited": c.get("portToVisit"),
            "prev_port": c.get("prevPort"),
            "next_port": c.get("nextPort"),
            "arrival_with_cargo": c.get("arrivalWithCargo"),
            "discharge": c.get("discharge"),
            "timestamp": c.get("portCallTimestamp"),
            "domestic_traffic_arrival": c.get("domesticTrafficArrival"),
            "domestic_traffic_departure": c.get("domesticTrafficDeparture"),
            "security_level": c.get("currentSecurityLevel"),
            "certificate_issuer": c.get("certificateIssuer"),
            "agents": [
                {"name": a.get("name"), "role": a.get("role"), "direction": a.get("portCallDirection")}
                for a in c.get("agentInfo", [])
            ]
        })

        if len(results) >= limit:
            break

    return results


def get_port_call_summary(from_date: Optional[str] = None, hours: int = 24) -> Dict:
    """
    Get aggregated port call statistics — useful for congestion/trade flow analysis.

    Args:
        from_date: ISO date string (default: last N hours)
        hours: Look-back window in hours (default 24)

    Returns:
        Dict with total calls, by-port breakdown, nationality distribution,
        cargo vs ballast ratio, vessel type distribution
    """
    if from_date is None:
        from_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
        from_date = from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    calls = get_port_calls(from_date=from_date, limit=500)
    if not calls or (len(calls) == 1 and "error" in calls[0]):
        return {"error": "Failed to fetch port calls", "details": calls}

    # Aggregate
    by_port = {}
    by_nationality = {}
    by_vessel_type = {}
    cargo_count = 0
    total = len(calls)

    for c in calls:
        port = c.get("port_visited", "Unknown")
        by_port[port] = by_port.get(port, 0) + 1

        nat = c.get("nationality", "Unknown")
        by_nationality[nat] = by_nationality.get(nat, 0) + 1

        vtype = c.get("vessel_type", "Unknown")
        by_vessel_type[vtype] = by_vessel_type.get(vtype, 0) + 1

        if c.get("arrival_with_cargo"):
            cargo_count += 1

    return {
        "period_start": from_date,
        "total_port_calls": total,
        "unique_ports": len(by_port),
        "cargo_arrivals": cargo_count,
        "ballast_arrivals": total - cargo_count,
        "cargo_ratio": round(cargo_count / total, 3) if total > 0 else 0,
        "top_ports": dict(sorted(by_port.items(), key=lambda x: -x[1])[:10]),
        "by_nationality": dict(sorted(by_nationality.items(), key=lambda x: -x[1])[:10]),
        "by_vessel_type": dict(sorted(by_vessel_type.items(), key=lambda x: -x[1])[:10])
    }


def search_vessels_by_area(lat_min: float, lat_max: float,
                           lon_min: float, lon_max: float,
                           limit: int = 50) -> List[Dict]:
    """
    Find vessels within a geographic bounding box.

    Useful for monitoring specific shipping lanes, straits, or port areas.

    Args:
        lat_min: Southern boundary latitude
        lat_max: Northern boundary latitude
        lon_min: Western boundary longitude
        lon_max: Eastern boundary longitude
        limit: Max vessels to return

    Returns:
        List of vessels with positions within the bounding box
    """
    all_vessels = get_all_vessel_locations(limit=5000)
    if not all_vessels or (len(all_vessels) == 1 and "error" in all_vessels[0]):
        return all_vessels

    results = []
    for v in all_vessels:
        lat = v.get("latitude")
        lon = v.get("longitude")
        if lat is None or lon is None:
            continue
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            results.append(v)
            if len(results) >= limit:
                break

    return results


def get_vessels_in_motion(min_speed_knots: float = 1.0, limit: int = 50) -> List[Dict]:
    """
    Get vessels currently moving (speed > threshold).

    Useful for identifying active shipping traffic vs anchored vessels.

    Args:
        min_speed_knots: Minimum speed to consider "in motion" (default 1.0)
        limit: Max vessels to return

    Returns:
        List of moving vessels sorted by speed (fastest first)
    """
    all_vessels = get_all_vessel_locations(limit=5000)
    if not all_vessels or (len(all_vessels) == 1 and "error" in all_vessels[0]):
        return all_vessels

    moving = [v for v in all_vessels
              if v.get("speed_knots") is not None and v["speed_knots"] >= min_speed_knots]
    moving.sort(key=lambda x: x.get("speed_knots", 0), reverse=True)
    return moving[:limit]


def get_anchored_vessels(limit: int = 50) -> List[Dict]:
    """
    Get vessels currently at anchor (nav_status_code == 1).

    High anchored vessel counts near ports can indicate congestion.

    Args:
        limit: Max vessels to return

    Returns:
        List of anchored vessels
    """
    all_vessels = get_all_vessel_locations(limit=5000)
    if not all_vessels or (len(all_vessels) == 1 and "error" in all_vessels[0]):
        return all_vessels

    anchored = [v for v in all_vessels if v.get("nav_status_code") == 1]
    return anchored[:limit]


def fetch_data() -> Dict:
    """
    Fetch comprehensive maritime data snapshot.

    Returns a summary of current vessel positions and recent port calls.
    """
    summary = get_port_call_summary(hours=24)
    vessels = get_all_vessel_locations(limit=20)
    return {
        "module": "marinetraffic_open_data",
        "source": "Digitraffic Marine API (Finnish Transport Infrastructure Agency)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "port_call_summary": summary,
        "sample_vessels": vessels[:5],
        "total_vessels_tracked": len(vessels)
    }


def get_latest() -> Dict:
    """Get latest maritime data point — most recent port calls and vessel count."""
    calls = get_port_calls(limit=5)
    locations = get_all_vessel_locations(limit=10)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latest_port_calls": calls[:5],
        "active_vessels_sample": len(locations),
        "source": "Digitraffic Marine API"
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "marinetraffic_open_data",
        "status": "active",
        "source": "https://meri.digitraffic.fi",
        "functions": [
            "get_all_vessel_locations", "get_vessel_info", "get_port_calls",
            "get_port_call_summary", "search_vessels_by_area",
            "get_vessels_in_motion", "get_anchored_vessels",
            "fetch_data", "get_latest"
        ]
    }, indent=2))
