#!/usr/bin/env python3
"""
NASA FIRMS (Fire Information for Resource Management System) Module

Near-real-time satellite-based active fire detections from MODIS and VIIRS
instruments. ~375m resolution, <3h latency. High-value alternative data for
agricultural commodity trading (wheat, palm oil, soy), insurance/reinsurance
catastrophe modeling, and supply chain disruption analysis.

Data Source: https://firms.modaps.eosdis.nasa.gov/api
Protocol: REST, CSV responses
Auth: MAP_KEY (free registration)
Rate Limits: 2,000 transactions/day (free tier)
Refresh: NRT (~3h latency from satellite pass)

Author: QUANTCLAW DATA Build Agent
Initiative: 0059
"""

import csv
import io
import json
import os
import sys
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "nasa_firms_fire"
CACHE_TTL_NRT = 3600          # 1 hour for near-real-time data
CACHE_TTL_AGGREGATE = 86400   # 24 hours for country-level aggregates
REQUEST_TIMEOUT = 60

SATELLITE_SOURCES = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]
DEFAULT_SOURCE = "VIIRS_SNPP_NRT"

API_KEY = os.getenv("NASA_FIRMS_MAP_KEY", "")

OPEN_ARCHIVE_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv"
ARCHIVE_REGIONS = {
    "USA": "SUOMI_VIIRS_C2_USA_contiguous_and_Hawaii_24h.csv",
    "CAN": "SUOMI_VIIRS_C2_Canada_24h.csv",
    "BRA": "SUOMI_VIIRS_C2_South_America_24h.csv",
    "ARG": "SUOMI_VIIRS_C2_South_America_24h.csv",
    "COL": "SUOMI_VIIRS_C2_South_America_24h.csv",
    "MEX": "SUOMI_VIIRS_C2_Central_America_24h.csv",
    "GRC": "SUOMI_VIIRS_C2_Europe_24h.csv",
    "TUR": "SUOMI_VIIRS_C2_Europe_24h.csv",
    "ESP": "SUOMI_VIIRS_C2_Europe_24h.csv",
    "IDN": "SUOMI_VIIRS_C2_South_Asia_24h.csv",
    "MYS": "SUOMI_VIIRS_C2_South_Asia_24h.csv",
    "AUS": "SUOMI_VIIRS_C2_Global_24h.csv",
    "RUS": "SUOMI_VIIRS_C2_Global_24h.csv",
    "GLOBAL": "SUOMI_VIIRS_C2_Global_24h.csv",
}

COUNTRY_BBOX = {
    "AUS": "112.0,-44.0,155.0,-10.0",
    "RUS": "19.0,41.0,180.0,82.0",
}

FINANCIAL_HOTSPOTS = {
    "california": {
        "name": "US West Coast Fires (California/Oregon)",
        "latitude": 37.5,
        "longitude": -120.0,
        "radius_km": 500,
        "relevance": "Wildfire season, insurance stocks, utility liability",
        "commodities": ["insurance", "utilities", "real_estate"],
    },
    "amazon": {
        "name": "Amazon Deforestation Burns (Brazil)",
        "latitude": -5.0,
        "longitude": -55.0,
        "radius_km": 1500,
        "relevance": "Soy, cattle, carbon credits, deforestation policy",
        "commodities": ["soy", "cattle", "carbon_credits"],
    },
    "southeast_asia": {
        "name": "Southeast Asian Haze (Indonesia/Malaysia)",
        "latitude": 0.5,
        "longitude": 110.0,
        "radius_km": 1000,
        "relevance": "Palm oil supply disruption, haze economic impact",
        "commodities": ["palm_oil", "rubber"],
    },
    "australia": {
        "name": "Australian Bushfires (NSW/Victoria)",
        "latitude": -33.0,
        "longitude": 149.0,
        "radius_km": 800,
        "relevance": "Wheat, wool, insurance, tourism",
        "commodities": ["wheat", "wool", "insurance"],
    },
    "canada": {
        "name": "Canadian Boreal Fires",
        "latitude": 55.0,
        "longitude": -105.0,
        "radius_km": 1000,
        "relevance": "Lumber, carbon emissions, air quality",
        "commodities": ["lumber", "carbon_credits"],
    },
    "mediterranean": {
        "name": "Mediterranean Fires (Greece/Turkey/Spain)",
        "latitude": 38.0,
        "longitude": 23.0,
        "radius_km": 500,
        "relevance": "Tourism, olive oil, wine",
        "commodities": ["olive_oil", "wine", "tourism"],
    },
    "siberia": {
        "name": "Siberian Fires (Russia)",
        "latitude": 62.0,
        "longitude": 100.0,
        "radius_km": 1500,
        "relevance": "Carbon emissions, climate feedback loops",
        "commodities": ["carbon_credits", "natural_gas"],
    },
    "sub_saharan_africa": {
        "name": "African Savanna Burns (Sub-Saharan)",
        "latitude": 0.0,
        "longitude": 25.0,
        "radius_km": 2000,
        "relevance": "Agricultural burn cycle indicator, cocoa, coffee",
        "commodities": ["cocoa", "coffee", "agriculture"],
    },
}

COUNTRY_REGIONS = {
    "USA": {"name": "United States", "hotspots": ["california"]},
    "BRA": {"name": "Brazil", "hotspots": ["amazon"]},
    "IDN": {"name": "Indonesia", "hotspots": ["southeast_asia"]},
    "MYS": {"name": "Malaysia", "hotspots": ["southeast_asia"]},
    "AUS": {"name": "Australia", "hotspots": ["australia"]},
    "CAN": {"name": "Canada", "hotspots": ["canada"]},
    "GRC": {"name": "Greece", "hotspots": ["mediterranean"]},
    "TUR": {"name": "Turkey", "hotspots": ["mediterranean"]},
    "ESP": {"name": "Spain", "hotspots": ["mediterranean"]},
    "RUS": {"name": "Russia", "hotspots": ["siberia"]},
}

INDICATORS = {
    "FIRES_USA_24H": {
        "name": "Active Fires — United States (24h)",
        "description": "VIIRS fire detections in the US, last 24 hours",
        "query_type": "country",
        "country": "USA",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "FIRES_BRA_24H": {
        "name": "Active Fires — Brazil (24h)",
        "description": "VIIRS fire detections in Brazil, last 24 hours (Amazon deforestation)",
        "query_type": "country",
        "country": "BRA",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "FIRES_IDN_24H": {
        "name": "Active Fires — Indonesia (24h)",
        "description": "VIIRS fire detections in Indonesia, last 24 hours (palm oil haze)",
        "query_type": "country",
        "country": "IDN",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "FIRES_AUS_24H": {
        "name": "Active Fires — Australia (24h)",
        "description": "VIIRS fire detections in Australia, last 24 hours (bushfire season)",
        "query_type": "country",
        "country": "AUS",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "FIRES_CAN_24H": {
        "name": "Active Fires — Canada (24h)",
        "description": "VIIRS fire detections in Canada, last 24 hours (boreal fires)",
        "query_type": "country",
        "country": "CAN",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "FIRES_RUS_24H": {
        "name": "Active Fires — Russia (24h)",
        "description": "VIIRS fire detections in Russia, last 24 hours (Siberian fires)",
        "query_type": "country",
        "country": "RUS",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "HOTSPOT_CALIFORNIA": {
        "name": "Fire Activity — California Wildfire Zone",
        "description": "Fire detections within 500km of central California, last 24h",
        "query_type": "hotspot",
        "hotspot": "california",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "HOTSPOT_AMAZON": {
        "name": "Fire Activity — Amazon Deforestation Zone",
        "description": "Fire detections within 1500km of central Amazon, last 24h",
        "query_type": "hotspot",
        "hotspot": "amazon",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
    },
    "HOTSPOT_SE_ASIA": {
        "name": "Fire Activity — Southeast Asian Haze Zone",
        "description": "Fire detections within 1000km of Borneo, last 24h",
        "query_type": "hotspot",
        "hotspot": "southeast_asia",
        "days": 1,
        "source": "VIIRS_SNPP_NRT",
        "cache_ttl": CACHE_TTL_NRT,
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


def _get_api_key() -> str:
    key = API_KEY or os.getenv("NASA_FIRMS_MAP_KEY", "")
    if not key:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("NASA_FIRMS_MAP_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    break
    return key


# --- CSV Parsing ---

def _parse_fire_csv(text: str) -> List[Dict]:
    """Parse FIRMS CSV response into structured fire detection records."""
    if not text or not text.strip():
        return []
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return []

    reader = csv.DictReader(io.StringIO(text))
    fires = []
    for row in reader:
        try:
            fire = {
                "latitude": float(row.get("latitude", 0)),
                "longitude": float(row.get("longitude", 0)),
                "brightness": float(row.get("bright_ti4") or row.get("brightness") or 0),
                "scan": float(row.get("scan", 0)),
                "track": float(row.get("track", 0)),
                "acq_date": row.get("acq_date", ""),
                "acq_time": row.get("acq_time", ""),
                "satellite": row.get("satellite", ""),
                "instrument": row.get("instrument", ""),
                "confidence": row.get("confidence", ""),
                "version": row.get("version", ""),
                "bright_t31": float(row.get("bright_ti5") or row.get("bright_t31") or 0),
                "frp": float(row.get("frp") or 0),
                "daynight": row.get("daynight", ""),
            }
            conf = fire["confidence"]
            if conf.isdigit():
                fire["confidence"] = int(conf)
            fires.append(fire)
        except (ValueError, TypeError):
            continue

    fires.sort(key=lambda f: (f["acq_date"], f["acq_time"]), reverse=True)
    return fires


def _compute_fire_stats(fires: List[Dict]) -> Dict:
    """Compute aggregate statistics from fire detections."""
    if not fires:
        return {
            "fire_count": 0,
            "avg_brightness": None,
            "max_brightness": None,
            "avg_frp": None,
            "max_frp": None,
            "high_confidence_count": 0,
            "day_count": 0,
            "night_count": 0,
        }

    brightness_vals = [f["brightness"] for f in fires if f["brightness"] > 0]
    frp_vals = [f["frp"] for f in fires if f["frp"] > 0]

    high_conf = 0
    for f in fires:
        c = f["confidence"]
        if isinstance(c, int) and c >= 80:
            high_conf += 1
        elif isinstance(c, str) and c.lower() in ("high", "h"):
            high_conf += 1

    day_count = sum(1 for f in fires if f["daynight"] == "D")
    night_count = sum(1 for f in fires if f["daynight"] == "N")

    return {
        "fire_count": len(fires),
        "avg_brightness": round(sum(brightness_vals) / len(brightness_vals), 2) if brightness_vals else None,
        "max_brightness": round(max(brightness_vals), 2) if brightness_vals else None,
        "avg_frp": round(sum(frp_vals) / len(frp_vals), 2) if frp_vals else None,
        "max_frp": round(max(frp_vals), 2) if frp_vals else None,
        "total_frp": round(sum(frp_vals), 2) if frp_vals else None,
        "high_confidence_count": high_conf,
        "day_count": day_count,
        "night_count": night_count,
    }


# --- API Requests ---

def _api_archive(region_file: str) -> Dict:
    """Fetch fire data from the open FIRMS archive (no API key needed, 24h only)."""
    url = f"{OPEN_ARCHIVE_URL}/{region_file}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "csv_text": resp.text, "via": "open_archive"}
    except requests.Timeout:
        return {"success": False, "error": "Archive request timed out"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"Archive HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _api_country(country_code: str, days: int = 1, source: str = DEFAULT_SOURCE) -> Dict:
    """Fetch fire detections for a country via the FIRMS API (with archive fallback)."""
    key = _get_api_key()

    if key:
        days = max(1, min(days, 10))
        url = f"{BASE_URL}/country/csv/{key}/{source}/{country_code}/{days}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 401:
                return {"success": False, "error": "Invalid API key (HTTP 401)"}
            if resp.status_code == 429:
                return {"success": False, "error": "Rate limit exceeded (2,000/day). Try again later."}
            if resp.status_code == 400:
                url_alt = f"{BASE_URL}/area/csv/{key}/{source}/{country_code}/{days}"
                resp = requests.get(url_alt, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
            else:
                resp.raise_for_status()
            if "Invalid" in resp.text[:100] or "Error" in resp.text[:100]:
                return {"success": False, "error": f"API error: {resp.text[:200]}"}
            return {"success": True, "csv_text": resp.text}
        except requests.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            return {"success": False, "error": f"HTTP {status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    if days == 1 and country_code in ARCHIVE_REGIONS:
        result = _api_archive(ARCHIVE_REGIONS[country_code])
        if result.get("success") and country_code in COUNTRY_BBOX:
            result["_filter_bbox"] = COUNTRY_BBOX[country_code]
        return result

    return {"success": False, "error": "NASA_FIRMS_MAP_KEY not set (needed for multi-day queries). Register free at https://firms.modaps.eosdis.nasa.gov/api/map_key/"}


def _filter_by_bbox(fires: List[Dict], bbox_str: str) -> List[Dict]:
    """Filter fire records to those within a bounding box string (west,south,east,north)."""
    parts = [float(x) for x in bbox_str.split(",")]
    west, south, east, north = parts
    return [
        f for f in fires
        if south <= f["latitude"] <= north and west <= f["longitude"] <= east
    ]


def _radius_to_bbox(lat: float, lon: float, radius_km: float) -> str:
    """Convert center point + radius to FIRMS bounding box (west,south,east,north)."""
    import math
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    west = max(lon - lon_delta, -180)
    east = min(lon + lon_delta, 180)
    south = max(lat - lat_delta, -90)
    north = min(lat + lat_delta, 90)
    return f"{west:.2f},{south:.2f},{east:.2f},{north:.2f}"


def _api_area(lat: float, lon: float, radius_km: float, days: int = 1, source: str = DEFAULT_SOURCE) -> Dict:
    """Fetch fire detections in a bounding box around a point."""
    key = _get_api_key()

    if key:
        days = max(1, min(days, 5))
        bbox = _radius_to_bbox(lat, lon, radius_km)
        url = f"{BASE_URL}/area/csv/{key}/{source}/{bbox}/{days}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 401:
                return {"success": False, "error": "Invalid API key (HTTP 401)"}
            if resp.status_code == 429:
                return {"success": False, "error": "Rate limit exceeded (2,000/day). Try again later."}
            resp.raise_for_status()
            if "Invalid" in resp.text[:100] or "Error" in resp.text[:100]:
                return {"success": False, "error": f"API error: {resp.text[:200]}"}
            return {"success": True, "csv_text": resp.text}
        except requests.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            return {"success": False, "error": f"HTTP {status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    if days == 1:
        result = _api_archive("SUOMI_VIIRS_C2_Global_24h.csv")
        if result.get("success"):
            result["_filter_bbox"] = _radius_to_bbox(lat, lon, radius_km)
        return result

    return {"success": False, "error": "NASA_FIRMS_MAP_KEY not set (needed for multi-day/area queries). Register free at https://firms.modaps.eosdis.nasa.gov/api/map_key/"}


# --- Core Functions ---

def fetch_country(country_code: str, days: int = 1, source: str = DEFAULT_SOURCE) -> Dict:
    """Fetch fire data for a specific country."""
    country_code = country_code.upper()
    days = max(1, min(days, 10))

    cache_key = {"type": "country", "country": country_code, "days": days, "source": source}
    cp = _cache_path(f"country_{country_code}", _params_hash(cache_key))
    ttl = CACHE_TTL_NRT if days <= 2 else CACHE_TTL_AGGREGATE
    cached = _read_cache(cp, ttl)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_country(country_code, days, source)
    if not result["success"]:
        return {"success": False, "country": country_code, "error": result["error"]}

    fires = _parse_fire_csv(result["csv_text"])
    if result.get("_filter_bbox"):
        fires = _filter_by_bbox(fires, result["_filter_bbox"])
    stats = _compute_fire_stats(fires)
    country_name = COUNTRY_REGIONS.get(country_code, {}).get("name", country_code)

    response = {
        "success": True,
        "country": country_code,
        "country_name": country_name,
        "days": days,
        "satellite_source": source,
        **stats,
        "fires": fires[:100],
        "source": f"{BASE_URL}/country/csv/***/{source}/{country_code}/{days}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_hotspot(region: str, days: int = 1, source: str = DEFAULT_SOURCE) -> Dict:
    """Fetch fire data for a pre-configured financial hotspot region."""
    region = region.lower()
    if region not in FINANCIAL_HOTSPOTS:
        return {
            "success": False,
            "error": f"Unknown hotspot: {region}",
            "available": list(FINANCIAL_HOTSPOTS.keys()),
        }

    hs = FINANCIAL_HOTSPOTS[region]
    days = max(1, min(days, 10))

    cache_key = {"type": "hotspot", "region": region, "days": days, "source": source}
    cp = _cache_path(f"hotspot_{region}", _params_hash(cache_key))
    cached = _read_cache(cp, CACHE_TTL_NRT)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_area(hs["latitude"], hs["longitude"], hs["radius_km"], days, source)
    if not result["success"]:
        return {"success": False, "region": region, "hotspot": hs["name"], "error": result["error"]}

    fires = _parse_fire_csv(result["csv_text"])
    if result.get("_filter_bbox"):
        fires = _filter_by_bbox(fires, result["_filter_bbox"])
    stats = _compute_fire_stats(fires)

    intensity = _assess_fire_intensity(fires)

    response = {
        "success": True,
        "region": region,
        "hotspot_name": hs["name"],
        "center": {"latitude": hs["latitude"], "longitude": hs["longitude"]},
        "radius_km": hs["radius_km"],
        "relevance": hs["relevance"],
        "affected_commodities": hs["commodities"],
        "days": days,
        "satellite_source": source,
        **stats,
        "intensity_level": intensity,
        "fires": fires[:100],
        "source": BASE_URL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator — standard module interface."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]

    if cfg["query_type"] == "country":
        return fetch_country(cfg["country"], cfg["days"], cfg["source"])
    elif cfg["query_type"] == "hotspot":
        return fetch_hotspot(cfg["hotspot"], cfg["days"], cfg["source"])
    else:
        return {"success": False, "error": f"Unknown query type: {cfg['query_type']}"}


def get_latest(indicator: str = None) -> Dict:
    """Get latest fire summary for key regions."""
    if indicator:
        return fetch_data(indicator)

    core_countries = ["USA", "BRA", "IDN", "AUS", "CAN"]
    results = {}
    errors = []

    for cc in core_countries:
        data = fetch_country(cc, days=1)
        if data.get("success"):
            results[cc] = {
                "country_name": data.get("country_name", cc),
                "fire_count": data["fire_count"],
                "high_confidence_count": data.get("high_confidence_count", 0),
                "max_brightness": data.get("max_brightness"),
                "total_frp": data.get("total_frp"),
            }
        else:
            errors.append({"country": cc, "error": data.get("error", "unknown")})

    total = sum(r["fire_count"] for r in results.values())

    return {
        "success": True,
        "source": "NASA FIRMS (Fire Information for Resource Management System)",
        "summary": f"{total} active fire detections across {len(results)} key countries (24h)",
        "countries": results,
        "total_fires": total,
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
            "query_type": v["query_type"],
            "cache_ttl_seconds": v["cache_ttl"],
        }
        for k, v in INDICATORS.items()
    ]


def _assess_fire_intensity(fires: List[Dict]) -> str:
    """Assess fire intensity level for financial risk scoring."""
    if not fires:
        return "none"
    count = len(fires)
    frp_vals = [f["frp"] for f in fires if f["frp"] > 0]
    max_frp = max(frp_vals) if frp_vals else 0
    total_frp = sum(frp_vals)

    if count >= 5000 or max_frp >= 500 or total_frp >= 50000:
        return "extreme"
    if count >= 1000 or max_frp >= 200 or total_frp >= 10000:
        return "very_high"
    if count >= 500 or max_frp >= 100 or total_frp >= 5000:
        return "high"
    if count >= 100 or max_frp >= 50 or total_frp >= 1000:
        return "moderate"
    if count >= 10:
        return "low"
    return "minimal"


def compute_anomaly_scores() -> Dict:
    """
    Compute fire anomaly scores for all hotspot regions.

    With an API key, compares 1-day vs 5-day lookback for proper baselines.
    Without a key, uses the global archive CSV (fetched once) and scores each
    region by fire count, intensity, and FRP relative to other regions.
    """
    now = datetime.now(timezone.utc)
    has_key = bool(_get_api_key())
    results = {}
    errors = []

    if has_key:
        for region, hs in FINANCIAL_HOTSPOTS.items():
            recent = fetch_hotspot(region, days=1)
            baseline = fetch_hotspot(region, days=5)

            if not recent.get("success") or not baseline.get("success"):
                errors.append({
                    "region": region,
                    "error": recent.get("error") or baseline.get("error", "unknown"),
                })
                continue

            current_count = recent["fire_count"]
            baseline_count = baseline["fire_count"]
            daily_avg = baseline_count / 5.0 if baseline_count > 0 else 0

            if daily_avg > 0:
                anomaly_ratio = current_count / daily_avg
                anomaly_score = round(anomaly_ratio - 1.0, 2)
            else:
                anomaly_ratio = 0.0
                anomaly_score = 0.0 if current_count == 0 else 10.0

            results[region] = _build_anomaly_entry(hs, current_count, daily_avg,
                                                    anomaly_ratio, anomaly_score,
                                                    recent.get("intensity_level", "unknown"))
    else:
        archive_result = _api_archive("SUOMI_VIIRS_C2_Global_24h.csv")
        if not archive_result.get("success"):
            return {"success": False, "error": archive_result.get("error", "Failed to fetch global archive")}

        all_fires = _parse_fire_csv(archive_result["csv_text"])

        for region, hs in FINANCIAL_HOTSPOTS.items():
            bbox_str = _radius_to_bbox(hs["latitude"], hs["longitude"], hs["radius_km"])
            region_fires = _filter_by_bbox(all_fires, bbox_str)
            stats = _compute_fire_stats(region_fires)
            intensity = _assess_fire_intensity(region_fires)
            current_count = stats["fire_count"]

            results[region] = _build_anomaly_entry(
                hs, current_count, None, None, None, intensity,
                total_frp=stats.get("total_frp"),
                max_frp=stats.get("max_frp"),
            )

    sorted_results = dict(
        sorted(results.items(),
               key=lambda x: x[1].get("current_24h_fires", 0), reverse=True)
    )

    method = "5-day rolling baseline" if has_key else "24h snapshot (no API key for baseline)"
    return {
        "success": True,
        "type": "fire_anomaly_scores",
        "description": f"Fire activity anomaly — {method}",
        "regions": sorted_results,
        "errors": errors if errors else None,
        "region_count": len(sorted_results),
        "timestamp": now.isoformat(),
    }


def _build_anomaly_entry(hs: Dict, current_count: int, daily_avg, anomaly_ratio,
                          anomaly_score, intensity: str, **extra) -> Dict:
    if anomaly_score is not None:
        if anomaly_score >= 3.0:
            anomaly_level = "extreme"
        elif anomaly_score >= 2.0:
            anomaly_level = "high"
        elif anomaly_score >= 1.0:
            anomaly_level = "elevated"
        elif anomaly_score >= -0.5:
            anomaly_level = "normal"
        else:
            anomaly_level = "below_normal"
    else:
        anomaly_level = intensity

    entry = {
        "hotspot_name": hs["name"],
        "current_24h_fires": current_count,
        "intensity": intensity,
        "affected_commodities": hs["commodities"],
    }
    if daily_avg is not None:
        entry["baseline_daily_avg"] = round(daily_avg, 1)
        entry["anomaly_ratio"] = round(anomaly_ratio, 2)
        entry["anomaly_score"] = anomaly_score
    entry["anomaly_level"] = anomaly_level
    for k, v in extra.items():
        if v is not None:
            entry[k] = v
    return entry


# --- CLI ---

def _print_help():
    print(f"""
NASA FIRMS Fire Detection Module (Initiative 0059)

Usage:
  python nasa_firms_fire.py                              # Global fire summary (top 5 countries, 24h)
  python nasa_firms_fire.py country USA                  # US fires last 24h
  python nasa_firms_fire.py country BRA 5                # Brazil fires last 5 days
  python nasa_firms_fire.py hotspot amazon               # Amazon deforestation region
  python nasa_firms_fire.py hotspot california           # CA wildfire zone
  python nasa_firms_fire.py hotspot southeast_asia       # SE Asian haze region
  python nasa_firms_fire.py anomaly                      # Fire anomaly scores by region
  python nasa_firms_fire.py list                         # List available indicators
  python nasa_firms_fire.py <INDICATOR>                  # Fetch specific indicator

Financial Hotspot Regions:""")
    for key, hs in FINANCIAL_HOTSPOTS.items():
        print(f"  {key:<22s} {hs['name']} (r={hs['radius_km']}km)")
    print(f"""
Country Codes: USA, BRA, IDN, MYS, AUS, CAN, GRC, TUR, ESP, RUS (ISO 3166-1 alpha-3)

Satellite Sources: {', '.join(SATELLITE_SOURCES)}

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth: NASA_FIRMS_MAP_KEY environment variable
Rate Limit: 2,000 transactions/day (free tier)
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
    elif args[0] == "country":
        cc = args[1].upper() if len(args) > 1 else "USA"
        days = int(args[2]) if len(args) > 2 else 1
        result = fetch_country(cc, days)
        print(json.dumps(result, indent=2, default=str))
    elif args[0] == "hotspot":
        region = args[1].lower() if len(args) > 1 else None
        if not region:
            print(json.dumps({"error": "Specify region", "available": list(FINANCIAL_HOTSPOTS.keys())}, indent=2))
        else:
            days = int(args[2]) if len(args) > 2 else 1
            result = fetch_hotspot(region, days)
            print(json.dumps(result, indent=2, default=str))
    elif args[0] == "anomaly":
        result = compute_anomaly_scores()
        print(json.dumps(result, indent=2, default=str))
    elif args[0].upper() in INDICATORS:
        result = fetch_data(args[0])
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Unknown command: {args[0]}")
        _print_help()
