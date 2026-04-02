#!/usr/bin/env python3
"""
USGS Earthquake Hazards Program Module

Real-time global earthquake data from the FDSN Event Web Service: magnitude,
location, depth, felt reports, PAGER alert levels. High-value alternative data
for catastrophe bond pricing, reinsurance risk modeling, and commodity supply
disruption analysis (Chilean copper, Japanese manufacturing, Taiwan semis).

Data Source: https://earthquake.usgs.gov/fdsnws/event/1
Protocol: REST (FDSN standard), GeoJSON responses
Auth: None (fully open, no key required)
Rate Limits: Fair use (no hard limit)
Refresh: Real-time (5min cache), Historical (24h cache)

Author: QUANTCLAW DATA Build Agent
Initiative: 0054
"""

import json
import sys
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "usgs_earthquake"
CACHE_TTL_REALTIME = 300       # 5 minutes for real-time feeds
CACHE_TTL_HISTORICAL = 86400   # 24 hours for historical queries
REQUEST_TIMEOUT = 30

FINANCIAL_HOTSPOTS = {
    "taiwan": {
        "name": "Taiwan (TSMC / Semiconductor)",
        "latitude": 23.5,
        "longitude": 121.0,
        "maxradiuskm": 300,
        "relevance": "TSMC fabs, global semiconductor supply chain",
    },
    "japan": {
        "name": "Japan (Tokyo / Financial Hub)",
        "latitude": 35.7,
        "longitude": 139.7,
        "maxradiuskm": 500,
        "relevance": "Tokyo Stock Exchange, Japanese manufacturing, BOJ",
    },
    "chile": {
        "name": "Chile (Santiago / Copper Belt)",
        "latitude": -33.4,
        "longitude": -70.6,
        "maxradiuskm": 800,
        "relevance": "Chilean copper mines, commodity supply disruption",
    },
    "turkey": {
        "name": "Turkey (Istanbul / Bosphorus)",
        "latitude": 41.0,
        "longitude": 29.0,
        "maxradiuskm": 400,
        "relevance": "Istanbul financial center, Bosphorus shipping lane",
    },
    "california": {
        "name": "California (Silicon Valley / Tech)",
        "latitude": 37.4,
        "longitude": -122.1,
        "maxradiuskm": 300,
        "relevance": "Big Tech HQs, data centers, venture capital",
    },
}

INDICATORS = {
    "SIGNIFICANT_GLOBAL": {
        "name": "Significant Earthquakes — Global (M5.0+, 24h)",
        "description": "Real-time M5.0+ earthquakes worldwide, last 24 hours",
        "params": {"minmagnitude": 5.0},
        "window_hours": 24,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "RECENT_M4": {
        "name": "Recent Earthquakes — Global (M4.0+, 7 days)",
        "description": "M4.0+ earthquakes worldwide over the past 7 days",
        "params": {"minmagnitude": 4.0},
        "window_hours": 168,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "PAGER_ALERTS": {
        "name": "PAGER Alert Events (Red/Orange)",
        "description": "Earthquakes with PAGER red or orange alert level (significant economic impact)",
        "params": {"alertlevel": "orange", "minmagnitude": 4.5},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "HOTSPOT_TAIWAN": {
        "name": "Seismic Activity — Taiwan (TSMC Region)",
        "description": "M3.0+ earthquakes within 300km of Taiwan, last 30 days",
        "params": {"minmagnitude": 3.0, "latitude": 23.5, "longitude": 121.0, "maxradiuskm": 300},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "HOTSPOT_JAPAN": {
        "name": "Seismic Activity — Japan (Tokyo Region)",
        "description": "M3.0+ earthquakes within 500km of Tokyo, last 30 days",
        "params": {"minmagnitude": 3.0, "latitude": 35.7, "longitude": 139.7, "maxradiuskm": 500},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "HOTSPOT_CHILE": {
        "name": "Seismic Activity — Chile (Copper Belt)",
        "description": "M3.0+ earthquakes within 800km of Santiago, last 30 days",
        "params": {"minmagnitude": 3.0, "latitude": -33.4, "longitude": -70.6, "maxradiuskm": 800},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "HOTSPOT_TURKEY": {
        "name": "Seismic Activity — Turkey (Istanbul Region)",
        "description": "M3.0+ earthquakes within 400km of Istanbul, last 30 days",
        "params": {"minmagnitude": 3.0, "latitude": 41.0, "longitude": 29.0, "maxradiuskm": 400},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "HOTSPOT_CALIFORNIA": {
        "name": "Seismic Activity — California (Silicon Valley)",
        "description": "M3.0+ earthquakes within 300km of Silicon Valley, last 30 days",
        "params": {"minmagnitude": 3.0, "latitude": 37.4, "longitude": -122.1, "maxradiuskm": 300},
        "window_hours": 720,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
    "ANNUAL_M5_PLUS": {
        "name": "Annual M5+ Earthquake Count (Historical)",
        "description": "Total M5.0+ earthquakes per year, for catastrophe bond pricing benchmarks",
        "params": {"minmagnitude": 5.0},
        "window_hours": 8760,
        "cache_ttl": CACHE_TTL_HISTORICAL,
    },
    "FELT_REPORTS": {
        "name": "Widely Felt Earthquakes (DYFI, 7 days)",
        "description": "Earthquakes with significant felt reports (minfelt >= 100) in last 7 days",
        "params": {"minfelt": 100},
        "window_hours": 168,
        "cache_ttl": CACHE_TTL_REALTIME,
    },
}


# --- Cache ---

def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_seconds: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if (now - cached_at).total_seconds() < ttl_seconds:
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


# --- GeoJSON Parsing ---

def _parse_geojson_events(raw: Dict) -> List[Dict]:
    """Parse USGS GeoJSON FeatureCollection into structured event dicts."""
    features = raw.get("features", [])
    events = []
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])

        epoch_ms = props.get("time")
        event_time = None
        if epoch_ms is not None:
            event_time = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).isoformat()

        updated_ms = props.get("updated")
        updated_time = None
        if updated_ms is not None:
            updated_time = datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc).isoformat()

        events.append({
            "event_id": f.get("id"),
            "magnitude": props.get("mag"),
            "magnitude_type": props.get("magType"),
            "place": props.get("place"),
            "time": event_time,
            "updated": updated_time,
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "depth_km": coords[2] if len(coords) > 2 else None,
            "alert_level": props.get("alert"),
            "tsunami_flag": props.get("tsunami"),
            "felt_reports": props.get("felt"),
            "cdi": props.get("cdi"),
            "mmi": props.get("mmi"),
            "significance": props.get("sig"),
            "status": props.get("status"),
            "detail_url": props.get("detail"),
            "url": props.get("url"),
        })

    events.sort(key=lambda e: e.get("time") or "", reverse=True)
    return events


# --- API Requests ---

def _api_query(params: dict) -> Dict:
    """Execute a query against the USGS FDSN event service."""
    url = f"{BASE_URL}/query"
    params = {**params, "format": "geojson", "orderby": "time"}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        try:
            body = e.response.text[:200]
        except Exception:
            pass
        return {"success": False, "error": f"HTTP {status}: {body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _api_count(params: dict) -> Dict:
    """Get event count from USGS FDSN count endpoint."""
    url = f"{BASE_URL}/count"
    params = {**params, "format": "geojson"}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "count": data.get("count", 0)}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Core Functions ---

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range override."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    now = datetime.now(timezone.utc)

    query_params = dict(cfg["params"])
    if start_date:
        query_params["starttime"] = start_date
    else:
        window = timedelta(hours=cfg["window_hours"])
        query_params["starttime"] = (now - window).strftime("%Y-%m-%dT%H:%M:%S")
    if end_date:
        query_params["endtime"] = end_date

    cache_key_params = {"indicator": indicator, **query_params}
    cp = _cache_path(indicator, _params_hash(cache_key_params))
    cached = _read_cache(cp, cfg["cache_ttl"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_query(query_params)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    events = _parse_geojson_events(result["data"])
    metadata = result["data"].get("metadata", {})

    mag_values = [e["magnitude"] for e in events if e.get("magnitude") is not None]
    depth_values = [e["depth_km"] for e in events if e.get("depth_km") is not None]

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "event_count": len(events),
        "api_count": metadata.get("count", len(events)),
        "max_magnitude": round(max(mag_values), 2) if mag_values else None,
        "min_magnitude": round(min(mag_values), 2) if mag_values else None,
        "avg_magnitude": round(sum(mag_values) / len(mag_values), 2) if mag_values else None,
        "avg_depth_km": round(sum(depth_values) / len(depth_values), 1) if depth_values else None,
        "events": events[:50],
        "query_params": query_params,
        "source": BASE_URL,
        "timestamp": now.isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all core indicators."""
    if indicator:
        return fetch_data(indicator)

    core = ["SIGNIFICANT_GLOBAL", "RECENT_M4", "PAGER_ALERTS"]
    results = {}
    errors = []
    for key in core:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "event_count": data["event_count"],
                "max_magnitude": data.get("max_magnitude"),
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})

    return {
        "success": True,
        "source": "USGS Earthquake Hazards Program",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "cache_ttl_seconds": v["cache_ttl"],
        }
        for k, v in INDICATORS.items()
    ]


def query_hotspot(region: str, days: int = 30, min_magnitude: float = 3.0) -> Dict:
    """Query seismic activity near a pre-configured financial hotspot."""
    region = region.lower()
    if region not in FINANCIAL_HOTSPOTS:
        return {
            "success": False,
            "error": f"Unknown hotspot: {region}",
            "available": list(FINANCIAL_HOTSPOTS.keys()),
        }

    hs = FINANCIAL_HOTSPOTS[region]
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")

    query_params = {
        "starttime": start,
        "minmagnitude": min_magnitude,
        "latitude": hs["latitude"],
        "longitude": hs["longitude"],
        "maxradiuskm": hs["maxradiuskm"],
    }

    cache_key = {"hotspot": region, "days": days, "minmag": min_magnitude}
    cp = _cache_path(f"hotspot_{region}", _params_hash(cache_key))
    cached = _read_cache(cp, CACHE_TTL_REALTIME)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_query(query_params)
    if not result["success"]:
        return {"success": False, "region": region, "name": hs["name"], "error": result["error"]}

    events = _parse_geojson_events(result["data"])
    mag_values = [e["magnitude"] for e in events if e.get("magnitude") is not None]

    response = {
        "success": True,
        "region": region,
        "hotspot": hs,
        "period_days": days,
        "min_magnitude": min_magnitude,
        "event_count": len(events),
        "max_magnitude": round(max(mag_values), 2) if mag_values else None,
        "avg_magnitude": round(sum(mag_values) / len(mag_values), 2) if mag_values else None,
        "events": events[:30],
        "risk_level": _assess_risk(events),
        "source": BASE_URL,
        "timestamp": now.isoformat(),
    }

    _write_cache(cp, response)
    return response


def _assess_risk(events: List[Dict]) -> str:
    """Simple risk assessment based on event count and magnitudes."""
    if not events:
        return "low"
    mag_values = [e["magnitude"] for e in events if e.get("magnitude") is not None]
    if not mag_values:
        return "low"
    max_mag = max(mag_values)
    if max_mag >= 7.0 or any(e.get("alert_level") in ("red", "orange") for e in events):
        return "critical"
    if max_mag >= 6.0 or len(events) > 50:
        return "high"
    if max_mag >= 5.0 or len(events) > 20:
        return "elevated"
    return "low"


def query_alerts(min_alert: str = "orange", days: int = 30) -> Dict:
    """Fetch events with PAGER alert levels at or above threshold."""
    alert_order = ["green", "yellow", "orange", "red"]
    min_alert = min_alert.lower()
    if min_alert not in alert_order:
        return {"success": False, "error": f"Invalid alert level: {min_alert}. Use: {alert_order}"}

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")

    all_events = []
    levels_to_fetch = alert_order[alert_order.index(min_alert):]

    for level in levels_to_fetch:
        query_params = {
            "starttime": start,
            "alertlevel": level,
        }
        cache_key = {"alerts": level, "days": days}
        cp = _cache_path(f"alerts_{level}", _params_hash(cache_key))
        cached = _read_cache(cp, CACHE_TTL_REALTIME)
        if cached and cached.get("_events"):
            all_events.extend(cached["_events"])
            continue

        result = _api_query(query_params)
        if result["success"]:
            events = _parse_geojson_events(result["data"])
            _write_cache(cp, {"_events": events})
            all_events.extend(events)

    all_events.sort(key=lambda e: e.get("time") or "", reverse=True)

    seen = set()
    unique = []
    for e in all_events:
        eid = e.get("event_id")
        if eid and eid not in seen:
            seen.add(eid)
            unique.append(e)

    return {
        "success": True,
        "min_alert_level": min_alert,
        "period_days": days,
        "event_count": len(unique),
        "events": unique[:50],
        "source": BASE_URL,
        "timestamp": now.isoformat(),
    }


def query_history(year: int, min_magnitude: float = 5.0) -> Dict:
    """Get annual earthquake summary for a given year (cat bond pricing data)."""
    now = datetime.now(timezone.utc)
    current_year = now.year

    start = f"{year}-01-01"
    end = f"{year}-12-31" if year < current_year else now.strftime("%Y-%m-%dT%H:%M:%S")

    cache_key = {"history": year, "minmag": min_magnitude}
    cp = _cache_path(f"history_{year}", _params_hash(cache_key))
    ttl = CACHE_TTL_HISTORICAL if year < current_year else CACHE_TTL_REALTIME
    cached = _read_cache(cp, ttl)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    count_result = _api_count({"starttime": start, "endtime": end, "minmagnitude": min_magnitude})

    query_params = {
        "starttime": start,
        "endtime": end,
        "minmagnitude": min_magnitude,
        "limit": 200,
        "orderby": "magnitude",
    }
    result = _api_query(query_params)
    if not result["success"]:
        return {"success": False, "year": year, "error": result["error"]}

    events = _parse_geojson_events(result["data"])
    mag_values = [e["magnitude"] for e in events if e.get("magnitude") is not None]

    m6_count = sum(1 for m in mag_values if m >= 6.0)
    m7_count = sum(1 for m in mag_values if m >= 7.0)
    m8_count = sum(1 for m in mag_values if m >= 8.0)

    response = {
        "success": True,
        "year": year,
        "min_magnitude": min_magnitude,
        "total_events": count_result.get("count", len(events)) if count_result.get("success") else len(events),
        "m6_plus_count": m6_count,
        "m7_plus_count": m7_count,
        "m8_plus_count": m8_count,
        "max_magnitude": round(max(mag_values), 2) if mag_values else None,
        "avg_magnitude": round(sum(mag_values) / len(mag_values), 2) if mag_values else None,
        "top_events": events[:20],
        "source": BASE_URL,
        "timestamp": now.isoformat(),
    }

    _write_cache(cp, response)
    return response


# --- CLI ---

def _print_help():
    print(f"""
USGS Earthquake Hazards Program Module (Initiative 0054)

Usage:
  python usgs_earthquake.py                          # Significant quakes last 24h (M5.0+)
  python usgs_earthquake.py recent                   # M4.0+ last 7 days
  python usgs_earthquake.py hotspot taiwan           # Activity near TSMC
  python usgs_earthquake.py hotspot japan            # Activity near Tokyo
  python usgs_earthquake.py hotspot chile            # Activity near Chilean copper
  python usgs_earthquake.py hotspot turkey           # Activity near Istanbul
  python usgs_earthquake.py hotspot california       # Activity near Silicon Valley
  python usgs_earthquake.py history 2025             # Annual M5+ summary
  python usgs_earthquake.py alerts                   # Active PAGER alerts (orange+red)
  python usgs_earthquake.py list                     # List available indicators
  python usgs_earthquake.py <INDICATOR>              # Fetch specific indicator

Financial Hotspots:""")
    for key, hs in FINANCIAL_HOTSPOTS.items():
        print(f"  {key:<15s} {hs['name']} (r={hs['maxradiuskm']}km)")
    print(f"""
Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: FDSN Event Web Service (GeoJSON)
Coverage: Global real-time seismicity
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
    elif args[0] in ("--help", "-h", "help"):
        _print_help()
    elif args[0] == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif args[0] == "recent":
        result = fetch_data("RECENT_M4")
        print(json.dumps(result, indent=2, default=str))
    elif args[0] == "hotspot":
        region = args[1] if len(args) > 1 else None
        if not region:
            print(json.dumps({"error": "Specify region", "available": list(FINANCIAL_HOTSPOTS.keys())}))
        else:
            result = query_hotspot(region)
            print(json.dumps(result, indent=2, default=str))
    elif args[0] == "history":
        year = int(args[1]) if len(args) > 1 else datetime.now().year
        result = query_history(year)
        print(json.dumps(result, indent=2, default=str))
    elif args[0] == "alerts":
        min_level = args[1] if len(args) > 1 else "orange"
        result = query_alerts(min_alert=min_level)
        print(json.dumps(result, indent=2, default=str))
    elif args[0].upper() in INDICATORS:
        result = fetch_data(args[0])
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Unknown command: {args[0]}")
        _print_help()
