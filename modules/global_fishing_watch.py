#!/usr/bin/env python3
"""
Global Fishing Watch Module

Tracks global fishing vessel activity using AIS data and machine learning.
Covers fishing effort by flag state/region, vessel identity, port visits,
and transshipment encounters for 65,000+ fishing vessels worldwide.

Data Source: https://gateway.api.globalfishingwatch.org/v3
Protocol: REST (JSON / GeoJSON)
Auth: Bearer token (GFW_API_TOKEN)
Rate Limit: 100 requests/minute (free tier)
Refresh: 6h activity, 24h vessel identity

Author: QUANTCLAW DATA Build Agent
"""

import json
import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://gateway.api.globalfishingwatch.org/v3"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "global_fishing_watch"
CACHE_TTL_ACTIVITY = 6
CACHE_TTL_IDENTITY = 24
REQUEST_TIMEOUT = 45
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

DATASETS = {
    "vessel_identity": "public-global-vessel-identity:latest",
    "fishing_effort": "public-global-fishing-effort:latest",
    "fishing_events": "public-global-fishing-events:latest",
    "port_visits": "public-global-port-visits-c2-events:latest",
    "encounters": "public-global-encounters-events:latest",
}

REGIONS = {
    "west_africa": {"name": "West Africa (Gulf of Guinea)", "lat": (-5, 15), "lon": (-20, 10)},
    "south_pacific": {"name": "South Pacific", "lat": (-50, -5), "lon": (150, -120)},
    "indian_ocean": {"name": "Indian Ocean", "lat": (-40, 25), "lon": (40, 100)},
    "north_atlantic": {"name": "North Atlantic", "lat": (30, 65), "lon": (-80, 0)},
    "southeast_asia": {"name": "Southeast Asia", "lat": (-10, 25), "lon": (95, 140)},
    "east_pacific": {"name": "East Pacific", "lat": (-30, 30), "lon": (-130, -75)},
}

TOP_FISHING_NATIONS = ["CHN", "IDN", "TWN", "JPN", "KOR", "ESP", "PER", "USA", "NOR", "RUS"]

INDICATORS = {
    "GLOBAL_FISHING_EFFORT": {
        "name": "Global Fishing Effort Index",
        "description": "Monthly aggregated fishing hours worldwide by flag state",
        "frequency": "monthly",
        "unit": "fishing hours",
        "command": "effort_by_flag",
    },
    "TOP_NATIONS_ACTIVITY": {
        "name": "Top Fishing Nations Activity",
        "description": "Fishing effort trends for top 10 fishing nations (CHN, IDN, TWN, JPN, KOR, ESP, etc.)",
        "frequency": "monthly",
        "unit": "fishing hours",
        "command": "effort_by_flag",
    },
    "PORT_VISIT_EVENTS": {
        "name": "Port Visit Patterns",
        "description": "Vessel arrivals/departures at major fishing ports with confidence scoring",
        "frequency": "event-based",
        "unit": "events",
        "command": "port_visits",
    },
    "TRANSSHIPMENT_ENCOUNTERS": {
        "name": "Transshipment Events",
        "description": "At-sea vessel encounters indicating potential transshipment (IUU/sanctions risk)",
        "frequency": "event-based",
        "unit": "events",
        "command": "encounters",
    },
    "REGIONAL_FISHING_INTENSITY": {
        "name": "Regional Fishing Intensity",
        "description": "EEZ-level fishing hours for key regions (West Africa, South Pacific, Indian Ocean)",
        "frequency": "monthly",
        "unit": "fishing hours",
        "command": "region",
    },
    "FLEET_SIZE_BY_FLAG": {
        "name": "Fleet Size Tracking",
        "description": "Active vessel counts by flag state and gear type",
        "frequency": "monthly",
        "unit": "vessel count",
        "command": "effort_by_flag",
    },
}


def _get_token() -> Optional[str]:
    token = os.environ.get("GFW_API_TOKEN")
    if token:
        return token
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("GFW_API_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip("\"'")
                    if val:
                        return val
        except OSError:
            pass
    return None


def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _api_request(endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict:
    token = _get_token()
    if not token:
        return {"success": False, "error": "GFW_API_TOKEN not set. Register at https://globalfishingwatch.org/our-apis/"}

    url = f"{BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                wait = RETRY_BACKOFF * (attempt + 1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except requests.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF)
                continue
            return {"success": False, "error": "Request timed out after retries"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            body = ""
            try:
                body = e.response.text[:300]
            except Exception:
                pass
            return {"success": False, "error": f"HTTP {status}: {body}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded (rate limited)"}


# ── Fishing Effort by Flag State ────────────────────────────────────────────

def fetch_effort_by_flag(year: int = None, months: int = 12) -> Dict:
    """Fetch fishing effort aggregated by flag state (monthly)."""
    now = datetime.now()
    if year is None:
        year = now.year - 1

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    if year == now.year:
        end_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    cache_key = f"effort_flag_{year}"
    cp = _cache_path(cache_key, _params_hash({"year": year}))
    cached = _read_cache(cp, CACHE_TTL_ACTIVITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "spatial-resolution": "low",
        "temporal-resolution": "monthly",
        "group-by": "flag",
        "datasets[0]": DATASETS["fishing_effort"],
        "date-range": f"{start_date},{end_date}",
    }
    result = _api_request("/4wings/report", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "indicator": "GLOBAL_FISHING_EFFORT"}

    raw = result["data"]
    entries = _parse_effort_response(raw, year)

    if not entries:
        return {"success": False, "error": "No fishing effort data returned", "indicator": "GLOBAL_FISHING_EFFORT"}

    flag_totals = {}
    monthly_totals = {}
    for e in entries:
        flag = e.get("flag", "UNKNOWN")
        flag_totals[flag] = flag_totals.get(flag, 0) + e["value"]
        month = e.get("date", "")[:7]
        if month:
            monthly_totals[month] = monthly_totals.get(month, 0) + e["value"]

    top_flags = sorted(flag_totals.items(), key=lambda x: x[1], reverse=True)[:20]
    monthly_series = [{"period": k, "value": round(v, 2)} for k, v in sorted(monthly_totals.items())]
    total_hours = sum(flag_totals.values())

    response = {
        "success": True,
        "indicator": "GLOBAL_FISHING_EFFORT",
        "name": "Global Fishing Effort by Flag State",
        "year": year,
        "total_fishing_hours": round(total_hours, 2),
        "top_fishing_nations": [{"flag": f, "fishing_hours": round(h, 2)} for f, h in top_flags],
        "monthly_series": monthly_series,
        "flag_count": len(flag_totals),
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def _parse_effort_response(raw: dict, year: int) -> List[Dict]:
    """Parse 4wings effort report response into flat records."""
    entries = []
    try:
        for group in raw if isinstance(raw, list) else [raw]:
            flag = group.get("flag") or group.get("flagState") or group.get("id", "UNKNOWN")
            for ts_entry in group.get("timeseries", group.get("data", [])):
                if isinstance(ts_entry, dict):
                    date = ts_entry.get("date", ts_entry.get("startDate", ""))
                    value = ts_entry.get("value", ts_entry.get("hours", ts_entry.get("apparentFishingHours", 0)))
                    if value and float(value) > 0:
                        entries.append({
                            "date": str(date)[:10],
                            "flag": str(flag),
                            "value": float(value),
                            "indicator": "GLOBAL_FISHING_EFFORT",
                            "source": "Global Fishing Watch",
                        })
    except (KeyError, TypeError, ValueError):
        pass
    return entries


# ── Vessel Search ───────────────────────────────────────────────────────────

def vessel_search(query: str, limit: int = 10) -> Dict:
    """Search vessels by name, MMSI, or IMO number."""
    cache_key = f"vessel_search_{query}"
    cp = _cache_path(cache_key, _params_hash({"q": query, "limit": limit}))
    cached = _read_cache(cp, CACHE_TTL_IDENTITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "query": query,
        "datasets[0]": DATASETS["vessel_identity"],
        "limit": limit,
        "includes[0]": "OWNERSHIP",
        "includes[1]": "MATCH_CRITERIA",
    }
    result = _api_request("/vessels/search", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "query": query}

    raw = result["data"]
    vessels = _parse_vessel_results(raw)

    response = {
        "success": True,
        "query": query,
        "vessels": vessels,
        "count": len(vessels),
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def _parse_vessel_results(raw: dict) -> List[Dict]:
    """Parse vessel search response."""
    vessels = []
    try:
        entries = raw.get("entries", raw) if isinstance(raw, dict) else raw
        if not isinstance(entries, list):
            entries = [entries]
        for v in entries:
            reg = v.get("registryInfo", [{}])
            if isinstance(reg, list) and reg:
                reg = reg[0]
            elif not isinstance(reg, dict):
                reg = {}

            combined = v.get("combinedSourcesInfo", [{}])
            if isinstance(combined, list) and combined:
                combined = combined[0]
            elif not isinstance(combined, dict):
                combined = {}

            vessel = {
                "id": v.get("id", ""),
                "name": combined.get("shipsname") or reg.get("shipname", v.get("shipname", "")),
                "flag": combined.get("flag") or reg.get("flag", v.get("flag", "")),
                "mmsi": str(combined.get("ssvid") or reg.get("ssvid", v.get("ssvid", ""))),
                "imo": str(reg.get("imoNumber", v.get("imo", ""))),
                "callsign": combined.get("callsign") or reg.get("callsign", ""),
                "vessel_type": combined.get("vesselType") or reg.get("vesselType", v.get("vesselType", "")),
                "gear_type": combined.get("geartype") or reg.get("geartype", v.get("geartype", "")),
                "length_m": combined.get("lengthM") or reg.get("lengthM"),
                "tonnage_gt": combined.get("tonnageGt") or reg.get("tonnageGt"),
                "owner": reg.get("owner", ""),
            }
            vessels.append(vessel)
    except (KeyError, TypeError, ValueError):
        pass
    return vessels


# ── Vessel Details ──────────────────────────────────────────────────────────

def get_vessel(vessel_id: str) -> Dict:
    """Get detailed vessel identity and characteristics."""
    cache_key = f"vessel_{vessel_id}"
    cp = _cache_path(cache_key, _params_hash({"id": vessel_id}))
    cached = _read_cache(cp, CACHE_TTL_IDENTITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"dataset": DATASETS["vessel_identity"]}
    result = _api_request(f"/vessels/{vessel_id}", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "vessel_id": vessel_id}

    vessels = _parse_vessel_results(result["data"])
    response = {
        "success": True,
        "vessel_id": vessel_id,
        "vessel": vessels[0] if vessels else result["data"],
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Fishing Events ──────────────────────────────────────────────────────────

def get_fishing_events(vessel_id: str, start_date: str = None, end_date: str = None) -> Dict:
    """Get fishing events for a specific vessel."""
    now = datetime.now()
    if not start_date:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")

    cache_key = f"fishing_events_{vessel_id}"
    cp = _cache_path(cache_key, _params_hash({"v": vessel_id, "s": start_date, "e": end_date}))
    cached = _read_cache(cp, CACHE_TTL_ACTIVITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "datasets[0]": DATASETS["fishing_events"],
        "vessels[0]": vessel_id,
        "start-date": start_date,
        "end-date": end_date,
    }
    result = _api_request("/events", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "vessel_id": vessel_id}

    events = _parse_events(result["data"])
    response = {
        "success": True,
        "vessel_id": vessel_id,
        "events": events,
        "count": len(events),
        "date_range": {"start": start_date, "end": end_date},
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Port Visit Events ───────────────────────────────────────────────────────

def get_port_visits(start_date: str = None, end_date: str = None, confidence: int = 4, limit: int = 50) -> Dict:
    """Get port visit events with confidence scoring."""
    now = datetime.now()
    if not start_date:
        start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")

    cache_key = "port_visits"
    cp = _cache_path(cache_key, _params_hash({"s": start_date, "e": end_date, "c": confidence}))
    cached = _read_cache(cp, CACHE_TTL_ACTIVITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "datasets[0]": DATASETS["port_visits"],
        "start-date": start_date,
        "end-date": end_date,
        "confidences[0]": confidence,
        "limit": limit,
        "offset": 0,
    }
    result = _api_request("/events", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "indicator": "PORT_VISIT_EVENTS"}

    events = _parse_events(result["data"])
    port_summary = {}
    for e in events:
        port = e.get("port_name") or e.get("location", "Unknown")
        port_summary[port] = port_summary.get(port, 0) + 1

    top_ports = sorted(port_summary.items(), key=lambda x: x[1], reverse=True)[:15]

    response = {
        "success": True,
        "indicator": "PORT_VISIT_EVENTS",
        "name": "Port Visit Events",
        "events": events[:limit],
        "count": len(events),
        "top_ports": [{"port": p, "visit_count": c} for p, c in top_ports],
        "date_range": {"start": start_date, "end": end_date},
        "confidence_min": confidence,
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Encounter / Transshipment Events ────────────────────────────────────────

def get_encounters(start_date: str = None, end_date: str = None, limit: int = 50) -> Dict:
    """Get vessel encounter/transshipment events."""
    now = datetime.now()
    if not start_date:
        start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")

    cache_key = "encounters"
    cp = _cache_path(cache_key, _params_hash({"s": start_date, "e": end_date}))
    cached = _read_cache(cp, CACHE_TTL_ACTIVITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "datasets[0]": DATASETS["encounters"],
        "start-date": start_date,
        "end-date": end_date,
        "limit": limit,
        "offset": 0,
    }
    result = _api_request("/events", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "indicator": "TRANSSHIPMENT_ENCOUNTERS"}

    events = _parse_events(result["data"])

    response = {
        "success": True,
        "indicator": "TRANSSHIPMENT_ENCOUNTERS",
        "name": "Vessel Encounter / Transshipment Events",
        "events": events[:limit],
        "count": len(events),
        "date_range": {"start": start_date, "end": end_date},
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Regional Fishing Intensity ──────────────────────────────────────────────

def get_region_effort(region_key: str = "south_pacific", year: int = None) -> Dict:
    """Get fishing effort for a specific region."""
    now = datetime.now()
    if year is None:
        year = now.year - 1

    if region_key not in REGIONS:
        return {
            "success": False,
            "error": f"Unknown region: {region_key}",
            "available_regions": list(REGIONS.keys()),
        }

    region = REGIONS[region_key]
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    cache_key = f"region_{region_key}_{year}"
    cp = _cache_path(cache_key, _params_hash({"r": region_key, "y": year}))
    cached = _read_cache(cp, CACHE_TTL_ACTIVITY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "spatial-resolution": "low",
        "temporal-resolution": "monthly",
        "group-by": "flag",
        "datasets[0]": DATASETS["fishing_effort"],
        "date-range": f"{start_date},{end_date}",
    }
    result = _api_request("/4wings/report", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "region": region_key}

    raw = result["data"]
    entries = _parse_effort_response(raw, year)

    monthly_totals = {}
    flag_totals = {}
    for e in entries:
        month = e.get("date", "")[:7]
        if month:
            monthly_totals[month] = monthly_totals.get(month, 0) + e["value"]
        flag = e.get("flag", "UNKNOWN")
        flag_totals[flag] = flag_totals.get(flag, 0) + e["value"]

    monthly_series = [{"period": k, "value": round(v, 2)} for k, v in sorted(monthly_totals.items())]
    top_flags = sorted(flag_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    total = sum(flag_totals.values())

    response = {
        "success": True,
        "indicator": "REGIONAL_FISHING_INTENSITY",
        "name": f"Fishing Intensity — {region['name']}",
        "region": region_key,
        "region_name": region["name"],
        "year": year,
        "total_fishing_hours": round(total, 2),
        "top_flags_in_region": [{"flag": f, "fishing_hours": round(h, 2)} for f, h in top_flags],
        "monthly_series": monthly_series,
        "source": "Global Fishing Watch",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Event Parser ────────────────────────────────────────────────────────────

def _parse_events(raw) -> List[Dict]:
    """Parse GFW events endpoint response (JSON or GeoJSON)."""
    events = []
    try:
        entries = []
        if isinstance(raw, dict):
            if "entries" in raw:
                entries = raw["entries"]
            elif "features" in raw:
                entries = [f.get("properties", f) for f in raw["features"]]
            elif "type" in raw and raw.get("type") == "Feature":
                entries = [raw.get("properties", raw)]
            else:
                entries = [raw]
        elif isinstance(raw, list):
            entries = raw

        for item in entries:
            coords = None
            if "position" in item:
                pos = item["position"]
                coords = {"lat": pos.get("lat"), "lon": pos.get("lon")}
            elif "geometry" in item:
                geom = item["geometry"]
                if geom and geom.get("coordinates"):
                    c = geom["coordinates"]
                    coords = {"lat": c[1] if len(c) > 1 else None, "lon": c[0] if c else None}

            port_name = None
            port_visit = item.get("port_visit") or item.get("portVisit") or {}
            if isinstance(port_visit, dict):
                iport = port_visit.get("intermediateAnchorage", {})
                port_name = iport.get("name") if isinstance(iport, dict) else None

            encounter = item.get("encounter", {})
            encounter_vessel = None
            if isinstance(encounter, dict) and encounter.get("vessel"):
                ev = encounter["vessel"]
                encounter_vessel = {
                    "id": ev.get("id", ""),
                    "name": ev.get("name", ""),
                    "flag": ev.get("flag", ""),
                }

            event = {
                "id": item.get("id", ""),
                "type": item.get("type", ""),
                "start": item.get("start", item.get("startDate", "")),
                "end": item.get("end", item.get("endDate", "")),
                "vessel_id": item.get("vessel", {}).get("id", "") if isinstance(item.get("vessel"), dict) else item.get("vessel", ""),
                "vessel_name": item.get("vessel", {}).get("name", "") if isinstance(item.get("vessel"), dict) else "",
                "flag": item.get("vessel", {}).get("flag", "") if isinstance(item.get("vessel"), dict) else "",
                "location": coords,
                "port_name": port_name,
                "duration_hours": item.get("durationHrs") or item.get("duration"),
            }
            if encounter_vessel:
                event["encounter_vessel"] = encounter_vessel
            events.append(event)
    except (KeyError, TypeError, ValueError):
        pass
    return events


# ── Standard Module Interface ───────────────────────────────────────────────

def fetch_data(indicator: str = None, **kwargs) -> Dict:
    """Fetch a specific indicator or default fishing effort summary."""
    if indicator is None:
        return fetch_effort_by_flag(**kwargs)

    indicator = indicator.upper()
    if indicator in ("GLOBAL_FISHING_EFFORT", "EFFORT_BY_FLAG"):
        return fetch_effort_by_flag(**kwargs)
    elif indicator in ("PORT_VISIT_EVENTS", "PORT_VISITS"):
        return get_port_visits(**kwargs)
    elif indicator in ("TRANSSHIPMENT_ENCOUNTERS", "ENCOUNTERS"):
        return get_encounters(**kwargs)
    elif indicator in ("REGIONAL_FISHING_INTENSITY", "REGION"):
        region = kwargs.get("region", "south_pacific")
        return get_region_effort(region_key=region, **{k: v for k, v in kwargs.items() if k != "region"})
    elif indicator in ("TOP_NATIONS_ACTIVITY",):
        return fetch_effort_by_flag(**kwargs)
    elif indicator in ("FLEET_SIZE_BY_FLAG",):
        return fetch_effort_by_flag(**kwargs)
    elif indicator == "VESSEL_SEARCH":
        query = kwargs.get("query", "")
        if not query:
            return {"success": False, "error": "query parameter required for vessel search"}
        return vessel_search(query)
    else:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)
    return fetch_effort_by_flag()


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
        }
        for k, v in INDICATORS.items()
    ]


# ── CLI ─────────────────────────────────────────────────────────────────────

def _print_help():
    print(f"""
Global Fishing Watch Module

Usage:
  python global_fishing_watch.py                          # Global fishing effort summary
  python global_fishing_watch.py effort_by_flag           # Fishing hours by flag state
  python global_fishing_watch.py vessel_search "name"     # Search vessel by name/MMSI/IMO
  python global_fishing_watch.py vessel <vessel_id>       # Vessel identity details
  python global_fishing_watch.py fishing_events <vid>     # Fishing events for vessel
  python global_fishing_watch.py port_visits              # Recent port visit events
  python global_fishing_watch.py encounters               # Transshipment encounters
  python global_fishing_watch.py region <region_key>      # Regional fishing intensity
  python global_fishing_watch.py list                     # List available indicators

Regions: {', '.join(REGIONS.keys())}

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth: Bearer token (GFW_API_TOKEN in .env)
Rate Limit: 100 req/min
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        result = fetch_effort_by_flag()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd in ("--help", "-h", "help"):
        _print_help()
    elif cmd == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif cmd == "effort_by_flag":
        year = int(sys.argv[2]) if len(sys.argv) > 2 else None
        print(json.dumps(fetch_effort_by_flag(year=year), indent=2, default=str))
    elif cmd == "vessel_search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        if not query:
            print(json.dumps({"success": False, "error": "Usage: vessel_search <name_or_mmsi>"}, indent=2))
        else:
            print(json.dumps(vessel_search(query), indent=2, default=str))
    elif cmd == "vessel":
        vid = sys.argv[2] if len(sys.argv) > 2 else ""
        if not vid:
            print(json.dumps({"success": False, "error": "Usage: vessel <vessel_id>"}, indent=2))
        else:
            print(json.dumps(get_vessel(vid), indent=2, default=str))
    elif cmd == "fishing_events":
        vid = sys.argv[2] if len(sys.argv) > 2 else ""
        if not vid:
            print(json.dumps({"success": False, "error": "Usage: fishing_events <vessel_id>"}, indent=2))
        else:
            print(json.dumps(get_fishing_events(vid), indent=2, default=str))
    elif cmd == "port_visits":
        print(json.dumps(get_port_visits(), indent=2, default=str))
    elif cmd == "encounters":
        print(json.dumps(get_encounters(), indent=2, default=str))
    elif cmd == "region":
        region = sys.argv[2] if len(sys.argv) > 2 else "south_pacific"
        year = int(sys.argv[3]) if len(sys.argv) > 3 else None
        print(json.dumps(get_region_effort(region_key=region, year=year), indent=2, default=str))
    else:
        result = fetch_data(cmd)
        print(json.dumps(result, indent=2, default=str))
