#!/usr/bin/env python3
"""
Electricity Maps Carbon Intensity — Real-time Grid Carbon Data

Data Source: Electricity Maps API (https://www.electricitymaps.com)
Category: ESG & Climate
Free tier: Zones endpoint free; carbon-intensity/power endpoints need free API key
  Sign up at https://api-portal.electricitymaps.com/ for free tier (100 req/day)
Update: Real-time (5-15 min intervals)

Provides:
- All global electricity zones (352+ regions) — FREE, no key needed
- Carbon intensity (gCO2eq/kWh) per zone — requires free API key
- Power breakdown by source (solar, wind, nuclear, coal, gas, etc.)
- Historical carbon intensity data
- Zone-level power consumption/production breakdown

Trading Relevance:
- Energy sector trading: correlate carbon costs with electricity prices
- ESG scoring: real-time carbon data for portfolio ESG analysis
- Renewable energy investment signals
- Carbon credit market indicators
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

BASE_URL = "https://api.electricitymaps.com/v3"
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/electricity_maps")
os.makedirs(CACHE_DIR, exist_ok=True)

# Common zone codes for quick reference
MAJOR_ZONES = {
    "US-CAL-CISO": "California (CAISO)",
    "US-TEX-ERCO": "Texas (ERCOT)",
    "US-NY-NYIS": "New York (NYISO)",
    "US-MIDA-PJM": "PJM Interconnection",
    "DE": "Germany",
    "FR": "France",
    "GB": "Great Britain",
    "ES": "Spain",
    "IT-NO": "Italy North",
    "NO-NO1": "Norway South",
    "SE-SE1": "Sweden North",
    "DK-DK1": "Denmark West",
    "JP-TK": "Japan Tokyo",
    "AU-NSW": "Australia NSW",
    "IN-NO": "India North",
    "BR-S": "Brazil South",
    "CN-NE": "China Northeast",
}


def _get_api_key() -> Optional[str]:
    """
    Get API key from environment or credentials file.
    Sign up free at https://api-portal.electricitymaps.com/
    """
    key = os.environ.get("ELECTRICITYMAPS_API_KEY") or os.environ.get("ELECTRICITY_MAPS_TOKEN")
    if key:
        return key

    cred_paths = [
        os.path.expanduser("~/.credentials/electricity_maps.json"),
        os.path.expanduser("~/.credentials/electricitymaps.json"),
    ]
    for path in cred_paths:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                return data.get("api_key") or data.get("auth_token") or data.get("token")
            except Exception:
                pass
    return None


def _request(endpoint: str, params: Optional[Dict] = None, require_auth: bool = True) -> Dict:
    """Make API request with optional auth."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"User-Agent": "QuantClaw/1.0"}

    if require_auth:
        api_key = _get_api_key()
        if not api_key:
            return {
                "error": "API key required",
                "message": "Set ELECTRICITYMAPS_API_KEY env var or create ~/.credentials/electricity_maps.json with {\"api_key\": \"your-key\"}. Free signup: https://api-portal.electricitymaps.com/",
            }
        headers["auth-token"] = api_key

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}", "message": str(e), "body": resp.text[:500]}
    except requests.exceptions.RequestException as e:
        return {"error": "request_failed", "message": str(e)}


def _load_cache(name: str, max_age_hours: float = 24) -> Optional[Any]:
    """Load from cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _save_cache(name: str, data: Any):
    """Save data to cache."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─── FREE ENDPOINTS (no API key needed) ────────────────────────────

def get_zones() -> Dict:
    """
    Get all available electricity zones worldwide.
    FREE — no API key required.

    Returns dict keyed by zone code with zone metadata:
      - zoneName, countryCode, tier, subZoneKeys, etc.

    >>> zones = get_zones()
    >>> zones['DE']['zoneName']
    'Germany'
    """
    cached = _load_cache("zones", max_age_hours=168)  # Cache 1 week
    if cached:
        return cached

    data = _request("zones", require_auth=False)
    if "error" not in data:
        _save_cache("zones", data)
    return data


def search_zones(query: str) -> List[Dict]:
    """
    Search zones by name, country code, or keyword.
    FREE — no API key required.

    Args:
        query: Search string (e.g., 'Texas', 'DE', 'wind', 'California')

    Returns:
        List of matching zones with code and name.
    """
    zones = get_zones()
    if "error" in zones:
        return [zones]

    query_lower = query.lower()
    results = []
    for code, info in zones.items():
        searchable = f"{code} {info.get('zoneName', '')} {info.get('countryName', '')} {info.get('displayName', '')}".lower()
        if query_lower in searchable:
            results.append({
                "zone": code,
                "name": info.get("zoneName", ""),
                "country": info.get("countryCode", ""),
                "display_name": info.get("displayName", ""),
                "tier": info.get("tier", ""),
            })
    return sorted(results, key=lambda x: x["zone"])


def list_country_zones(country_code: str) -> List[Dict]:
    """
    List all zones for a specific country.
    FREE — no API key required.

    Args:
        country_code: ISO 2-letter country code (e.g., 'US', 'DE', 'FR')

    Returns:
        List of zones for that country.
    """
    zones = get_zones()
    if "error" in zones:
        return [zones]

    cc = country_code.upper()
    results = []
    for code, info in zones.items():
        if info.get("countryCode", "").upper() == cc:
            results.append({
                "zone": code,
                "name": info.get("zoneName", ""),
                "display_name": info.get("displayName", ""),
                "tier": info.get("tier", ""),
                "sub_zones": info.get("subZoneKeys", []),
            })
    return sorted(results, key=lambda x: x["zone"])


def get_health() -> Dict:
    """
    Check Electricity Maps API health status.
    FREE — no API key required.

    Returns API status, timestamp, and service checks.
    """
    try:
        resp = requests.get(f"{BASE_URL.rsplit('/v3', 1)[0]}/health", timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_zone_count() -> Dict:
    """
    Get summary stats about available zones.
    FREE — no API key required.

    Returns total zones, countries covered, tier breakdown.
    """
    zones = get_zones()
    if "error" in zones:
        return zones

    countries = set()
    tiers = {}
    for code, info in zones.items():
        cc = info.get("countryCode", "unknown")
        countries.add(cc)
        tier = info.get("tier", "unknown")
        tiers[tier] = tiers.get(tier, 0) + 1

    return {
        "total_zones": len(zones),
        "countries": len(countries),
        "tier_breakdown": tiers,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── AUTH ENDPOINTS (free API key required) ─────────────────────────

def get_carbon_intensity_latest(zone: str) -> Dict:
    """
    Get latest carbon intensity for a zone.
    Requires free API key.

    Args:
        zone: Zone code (e.g., 'DE', 'US-CAL-CISO', 'FR')

    Returns:
        Carbon intensity in gCO2eq/kWh with timestamp and data source.
    """
    data = _request("carbon-intensity/latest", params={"zone": zone})
    if "error" not in data:
        data["_zone"] = zone
        data["_unit"] = "gCO2eq/kWh"
    return data


def get_carbon_intensity_history(zone: str, datetime_str: Optional[str] = None) -> Dict:
    """
    Get historical carbon intensity for a zone (last 24h by default).
    Requires free API key.

    Args:
        zone: Zone code (e.g., 'DE', 'US-TEX-ERCO')
        datetime_str: Optional ISO datetime to query around (e.g., '2024-01-15T12:00:00Z')

    Returns:
        List of historical carbon intensity readings.
    """
    params = {"zone": zone}
    if datetime_str:
        params["datetime"] = datetime_str
    return _request("carbon-intensity/history", params=params)


def get_power_breakdown_latest(zone: str) -> Dict:
    """
    Get latest power generation/consumption breakdown by source.
    Requires free API key.

    Args:
        zone: Zone code (e.g., 'DE', 'FR', 'US-CAL-CISO')

    Returns:
        Power breakdown with sources: solar, wind, nuclear, coal, gas,
        hydro, biomass, geothermal, oil, unknown + imports/exports.
    """
    data = _request("power-breakdown/latest", params={"zone": zone})
    if "error" not in data:
        data["_zone"] = zone
    return data


def get_power_breakdown_history(zone: str, datetime_str: Optional[str] = None) -> Dict:
    """
    Get historical power breakdown for a zone (last 24h by default).
    Requires free API key.

    Args:
        zone: Zone code (e.g., 'DE', 'US-TEX-ERCO')
        datetime_str: Optional ISO datetime

    Returns:
        Historical power breakdown readings.
    """
    params = {"zone": zone}
    if datetime_str:
        params["datetime"] = datetime_str
    return _request("power-breakdown/history", params=params)


def get_power_consumption_breakdown(zone: str) -> Dict:
    """
    Get latest power consumption breakdown for a zone.
    Requires free API key.

    Args:
        zone: Zone code

    Returns:
        Consumption breakdown by source including imports.
    """
    return _request("power-consumption-breakdown/latest", params={"zone": zone})


# ─── CONVENIENCE / ANALYSIS FUNCTIONS ───────────────────────────────

def get_major_zones_summary() -> List[Dict]:
    """
    Get a curated list of major trading-relevant electricity zones.
    FREE — uses cached zone data.

    Returns list of major zones with their codes and names.
    """
    zones = get_zones()
    if "error" in zones:
        return [zones]

    results = []
    for code, label in MAJOR_ZONES.items():
        info = zones.get(code, {})
        results.append({
            "zone": code,
            "label": label,
            "name": info.get("zoneName", ""),
            "country": info.get("countryCode", ""),
            "tier": info.get("tier", ""),
        })
    return results


def compare_carbon_intensity(zones_list: List[str]) -> List[Dict]:
    """
    Compare carbon intensity across multiple zones.
    Requires free API key.

    Args:
        zones_list: List of zone codes (e.g., ['DE', 'FR', 'GB', 'US-CAL-CISO'])

    Returns:
        Sorted list (cleanest first) with zone, intensity, and timestamp.
    """
    results = []
    for zone in zones_list:
        data = get_carbon_intensity_latest(zone)
        entry = {"zone": zone}
        if "error" in data:
            entry["error"] = data["error"]
            entry["carbon_intensity"] = None
        else:
            entry["carbon_intensity"] = data.get("carbonIntensity")
            entry["datetime"] = data.get("datetime")
            entry["fossil_free_percentage"] = data.get("fossilFreePercentage")
            entry["renewable_percentage"] = data.get("renewablePercentage")
        results.append(entry)

    # Sort by carbon intensity (cleanest first), nulls last
    results.sort(key=lambda x: x.get("carbon_intensity") or 9999)
    return results


def get_renewable_percentage(zone: str) -> Dict:
    """
    Get renewable energy percentage for a zone.
    Requires free API key.

    Args:
        zone: Zone code

    Returns:
        Renewable and fossil-free percentages with power source breakdown.
    """
    data = get_power_breakdown_latest(zone)
    if "error" in data:
        return data

    production = data.get("powerProductionBreakdown", {})
    total = data.get("powerProductionTotal", 0)

    renewable_sources = ["solar", "wind", "hydro", "biomass", "geothermal"]
    fossil_sources = ["coal", "gas", "oil"]

    renewable_mw = sum(production.get(s, 0) or 0 for s in renewable_sources)
    fossil_mw = sum(production.get(s, 0) or 0 for s in fossil_sources)
    nuclear_mw = production.get("nuclear", 0) or 0

    return {
        "zone": zone,
        "datetime": data.get("datetime"),
        "renewable_mw": round(renewable_mw, 1),
        "fossil_mw": round(fossil_mw, 1),
        "nuclear_mw": round(nuclear_mw, 1),
        "total_production_mw": round(total, 1) if total else None,
        "renewable_pct": round(renewable_mw / total * 100, 1) if total else None,
        "fossil_free_pct": round((renewable_mw + nuclear_mw) / total * 100, 1) if total else None,
        "breakdown": {k: v for k, v in production.items() if v},
    }


if __name__ == "__main__":
    print("=== Electricity Maps Carbon Intensity Module ===")
    print(f"\nZone count: {get_zone_count()}")
    print(f"\nUS zones: {json.dumps(list_country_zones('US')[:5], indent=2)}")
    print(f"\nMajor zones: {json.dumps(get_major_zones_summary()[:3], indent=2)}")
