"""
Google Earth Engine API — Satellite & Geospatial Data for Quant Trading

Provides access to Earth Engine's public STAC data catalog for dataset discovery,
plus NASA POWER API for actual climate/solar/meteorological data at any coordinates.
No API keys required.

Data Sources:
- Google Earth Engine STAC Catalog (public, no auth)
- NASA POWER API (free, no auth) — solar, temperature, precipitation, wind
- Open-Elevation API (free, no auth)

Use Cases for Trading:
- Agriculture commodity signals (NDVI proxy, precipitation, temperature)
- Insurance risk (flood, drought, extreme weather)
- Energy trading (solar irradiance, wind speed)
- Climate risk assessment for portfolio hedging

Update: Daily (NASA POWER), catalog is static
Free: Yes (all endpoints are free, no API key needed)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/gee")
os.makedirs(CACHE_DIR, exist_ok=True)

# --- Public STAC Catalog Endpoints ---
GEE_STAC_ROOT = "https://earthengine-stac.storage.googleapis.com/catalog/catalog.json"
GEE_STAC_BASE = "https://earthengine-stac.storage.googleapis.com/catalog"

# --- NASA POWER API (free, no key) ---
NASA_POWER_BASE = "https://power.larc.nasa.gov/api/temporal"

# --- Open Elevation ---
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"

HEADERS = {
    "User-Agent": "QuantClaw-Data/1.0 (geospatial module)"
}


def _cache_get(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Read from disk cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data: dict):
    """Write to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def search_datasets(query: str, limit: int = 10) -> List[Dict]:
    """
    Search the Google Earth Engine STAC catalog for datasets.

    Args:
        query: Search term (e.g. 'NDVI', 'Landsat', 'temperature', 'precipitation')
        limit: Max results to return

    Returns:
        List of dicts with dataset id, title, description, temporal extent, links
    """
    cache_key = f"catalog_root"
    cached = _cache_get(cache_key, max_age_hours=168)  # cache 1 week

    if cached:
        catalog = cached
    else:
        try:
            resp = requests.get(GEE_STAC_ROOT, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            catalog = resp.json()
            _cache_set(cache_key, catalog)
        except requests.RequestException as e:
            return [{"error": f"Failed to fetch GEE catalog: {e}"}]

    query_lower = query.lower()
    results = []
    for link in catalog.get("links", []):
        rel = link.get("rel", "")
        title = link.get("title", "")
        href = link.get("href", "")
        if rel == "child" and query_lower in title.lower():
            results.append({
                "id": title,
                "title": title,
                "href": href,
                "type": link.get("type", "unknown"),
            })
            if len(results) >= limit:
                break

    return results


def get_dataset_info(dataset_path: str) -> Dict:
    """
    Get detailed info about a specific GEE dataset from the STAC catalog.

    Args:
        dataset_path: Dataset identifier path (e.g. 'MODIS', 'LANDSAT', 'COPERNICUS')

    Returns:
        Dict with dataset metadata, bands, temporal extent, spatial resolution
    """
    url = f"{GEE_STAC_BASE}/{dataset_path}/catalog.json"
    cache_key = f"dataset_{dataset_path.replace('/', '_')}"
    cached = _cache_get(cache_key, max_age_hours=168)
    if cached:
        return cached

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        _cache_set(cache_key, data)
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "description": data.get("description", ""),
            "links": [
                {"title": l.get("title", ""), "href": l.get("href", "")}
                for l in data.get("links", [])
                if l.get("rel") == "child"
            ][:20],
            "source": url,
        }
    except requests.RequestException as e:
        return {"error": f"Failed to fetch dataset info: {e}"}


def get_climate_data(
    lat: float,
    lon: float,
    start_date: str = None,
    end_date: str = None,
    parameters: List[str] = None,
    temporal: str = "monthly"
) -> Dict:
    """
    Get climate/meteorological data for any location via NASA POWER API.
    Extremely useful for agriculture commodity trading and energy forecasting.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        start_date: Start date YYYYMMDD (default: 12 months ago)
        end_date: End date YYYYMMDD (default: today)
        parameters: List of NASA POWER parameters. Defaults to key trading-relevant ones:
            - T2M (temperature 2m)
            - PRECTOTCORR (precipitation)
            - ALLSKY_SFC_SW_DWN (solar irradiance)
            - WS2M (wind speed 2m)
        temporal: 'daily', 'monthly', or 'climatology'

    Returns:
        Dict with time-series data for each parameter
    """
    if not parameters:
        parameters = ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"]

    now = datetime.now()
    if temporal == "monthly":
        # Monthly uses YYYY format; NASA POWER data lags ~2 months
        if not end_date:
            end_date = str(now.year - 1)
        if not start_date:
            start_date = str(now.year - 2)
    elif temporal == "climatology":
        # Climatology doesn't need dates, but API wants them
        if not end_date:
            end_date = str(now.year)
        if not start_date:
            start_date = str(now.year - 30)
    else:
        # Daily uses YYYYMMDD
        if not end_date:
            end_date = (now - timedelta(days=7)).strftime("%Y%m%d")
        if not start_date:
            start_date = (now - timedelta(days=90)).strftime("%Y%m%d")

    cache_key = f"power_{lat}_{lon}_{start_date}_{end_date}_{temporal}_{'_'.join(parameters)}"
    cached = _cache_get(cache_key, max_age_hours=24)
    if cached:
        return cached

    params = {
        "parameters": ",".join(parameters),
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    url = f"{NASA_POWER_BASE}/{temporal}/point"

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        raw = resp.json()

        # Extract the useful parts
        props = raw.get("properties", {}).get("parameter", {})
        result = {
            "location": {"lat": lat, "lon": lon},
            "temporal": temporal,
            "start_date": start_date,
            "end_date": end_date,
            "parameters": {},
            "parameter_info": {},
        }

        header = raw.get("header", {})
        if header:
            result["source"] = header.get("title", "NASA POWER")
            result["api_version"] = header.get("api_version", "")

        for param_name, values in props.items():
            # Filter out fill values (-999)
            clean = {k: v for k, v in values.items() if v != -999.0 and v != -999}
            result["parameters"][param_name] = clean

            # Summary stats
            vals = [v for v in clean.values() if isinstance(v, (int, float))]
            if vals:
                result["parameter_info"][param_name] = {
                    "count": len(vals),
                    "min": round(min(vals), 2),
                    "max": round(max(vals), 2),
                    "mean": round(sum(vals) / len(vals), 2),
                }

        _cache_set(cache_key, result)
        return result

    except requests.RequestException as e:
        return {"error": f"NASA POWER API error: {e}"}


def get_solar_irradiance(lat: float, lon: float, months: int = 12) -> Dict:
    """
    Get solar irradiance data for a location — key for energy trading.

    Args:
        lat: Latitude
        lon: Longitude
        months: Lookback months (default 12)

    Returns:
        Dict with monthly solar irradiance (kWh/m²/day), summary stats
    """
    now = datetime.now()
    end = str(now.year)
    start = str(now.year - max(1, months // 12))

    data = get_climate_data(
        lat, lon,
        start_date=start,
        end_date=end,
        parameters=["ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN"],
        temporal="monthly"
    )

    if "error" in data:
        return data

    return {
        "location": {"lat": lat, "lon": lon},
        "period_months": months,
        "all_sky_irradiance": data["parameters"].get("ALLSKY_SFC_SW_DWN", {}),
        "clear_sky_irradiance": data["parameters"].get("CLRSKY_SFC_SW_DWN", {}),
        "summary": data.get("parameter_info", {}),
        "unit": "kWh/m²/day",
        "trading_note": "Higher irradiance = more solar generation = lower peak electricity prices",
    }


def get_precipitation_data(lat: float, lon: float, months: int = 12) -> Dict:
    """
    Get precipitation data for a location — key for agriculture commodity trading.

    Args:
        lat: Latitude
        lon: Longitude
        months: Lookback months

    Returns:
        Dict with precipitation time series and drought/flood indicators
    """
    now = datetime.now()
    end = str(now.year)
    start = str(now.year - max(1, months // 12))

    data = get_climate_data(
        lat, lon,
        start_date=start,
        end_date=end,
        parameters=["PRECTOTCORR", "T2M"],
        temporal="monthly"
    )

    if "error" in data:
        return data

    precip = data["parameters"].get("PRECTOTCORR", {})
    precip_vals = [v for v in precip.values() if isinstance(v, (int, float))]

    drought_indicator = "normal"
    if precip_vals:
        mean_precip = sum(precip_vals) / len(precip_vals)
        latest_val = precip_vals[-1] if precip_vals else 0
        if latest_val < mean_precip * 0.5:
            drought_indicator = "drought_risk"
        elif latest_val > mean_precip * 2.0:
            drought_indicator = "flood_risk"

    return {
        "location": {"lat": lat, "lon": lon},
        "period_months": months,
        "precipitation_mm_day": precip,
        "temperature_c": data["parameters"].get("T2M", {}),
        "summary": data.get("parameter_info", {}),
        "drought_indicator": drought_indicator,
        "unit_precip": "mm/day",
        "unit_temp": "°C",
        "trading_note": "Low precip = drought risk = higher grain/soft commodity prices",
    }


def get_elevation(lat: float, lon: float) -> Dict:
    """
    Get elevation for a coordinate — useful for flood risk and agriculture models.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dict with elevation in meters
    """
    try:
        params = {"locations": f"{lat},{lon}"}
        resp = requests.get(OPEN_ELEVATION_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return {
                "lat": lat,
                "lon": lon,
                "elevation_m": results[0].get("elevation"),
                "source": "open-elevation.com (SRTM data)",
            }
        return {"error": "No elevation data returned"}
    except requests.RequestException as e:
        return {"error": f"Elevation API error: {e}"}


def get_agriculture_signals(lat: float, lon: float) -> Dict:
    """
    Get composite agriculture signals for a location — combines temperature,
    precipitation, and solar data into trading-relevant indicators.

    Args:
        lat: Latitude of agricultural region
        lon: Longitude of agricultural region

    Returns:
        Dict with growing conditions assessment, drought risk, and commodity implications
    """
    climate = get_climate_data(
        lat, lon,
        parameters=["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"],
        temporal="monthly"
    )

    if "error" in climate:
        return climate

    info = climate.get("parameter_info", {})
    t2m = info.get("T2M", {})
    precip = info.get("PRECTOTCORR", {})
    solar = info.get("ALLSKY_SFC_SW_DWN", {})

    # Simple growing conditions score (0-100)
    score = 50  # baseline
    if t2m:
        mean_temp = t2m.get("mean", 20)
        if 15 <= mean_temp <= 30:
            score += 15  # optimal temp range
        elif mean_temp < 5 or mean_temp > 40:
            score -= 20  # extreme temps
    if precip:
        mean_precip = precip.get("mean", 2)
        if 1 <= mean_precip <= 5:
            score += 15  # good rainfall
        elif mean_precip < 0.5:
            score -= 20  # drought
        elif mean_precip > 10:
            score -= 10  # flood risk
    if solar:
        mean_solar = solar.get("mean", 4)
        if mean_solar > 4:
            score += 10  # good sunlight
    score = max(0, min(100, score))

    return {
        "location": {"lat": lat, "lon": lon},
        "growing_conditions_score": score,
        "temperature": t2m,
        "precipitation": precip,
        "solar_irradiance": solar,
        "assessment": (
            "excellent" if score >= 80 else
            "good" if score >= 60 else
            "moderate" if score >= 40 else
            "poor" if score >= 20 else
            "critical"
        ),
        "commodity_implications": {
            "drought_risk": precip.get("mean", 2) < 1 if precip else False,
            "frost_risk": t2m.get("min", 10) < 0 if t2m else False,
            "heat_stress": t2m.get("max", 30) > 35 if t2m else False,
        },
        "trading_note": f"Growing score {score}/100 — affects grain, sugar, coffee, cotton prices",
    }


def get_wind_energy_potential(lat: float, lon: float, months: int = 12) -> Dict:
    """
    Assess wind energy potential at a location — useful for energy sector trading.

    Args:
        lat: Latitude
        lon: Longitude
        months: Lookback period

    Returns:
        Dict with wind speed data and energy potential classification
    """
    now = datetime.now()
    end = str(now.year)
    start = str(now.year - max(1, months // 12))

    data = get_climate_data(
        lat, lon,
        start_date=start,
        end_date=end,
        parameters=["WS2M", "WS10M", "WS50M"],
        temporal="monthly"
    )

    if "error" in data:
        return data

    info = data.get("parameter_info", {})
    ws50 = info.get("WS50M", info.get("WS10M", info.get("WS2M", {})))
    mean_wind = ws50.get("mean", 0)

    classification = (
        "excellent" if mean_wind >= 7 else
        "good" if mean_wind >= 5 else
        "moderate" if mean_wind >= 3.5 else
        "poor"
    )

    return {
        "location": {"lat": lat, "lon": lon},
        "period_months": months,
        "wind_speed_data": data["parameters"],
        "summary": info,
        "classification": classification,
        "mean_wind_speed_ms": mean_wind,
        "unit": "m/s",
        "trading_note": f"Wind class: {classification} — affects wind energy stocks and power prices",
    }


def compare_regions(
    locations: List[Tuple[float, float]],
    parameters: List[str] = None
) -> Dict:
    """
    Compare climate data across multiple locations — useful for relative value trades.

    Args:
        locations: List of (lat, lon) tuples to compare
        parameters: NASA POWER parameters to compare

    Returns:
        Dict with side-by-side comparison of all locations
    """
    if not parameters:
        parameters = ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]

    results = {}
    for i, (lat, lon) in enumerate(locations[:5]):  # max 5 locations
        label = f"loc_{i}_{lat}_{lon}"
        data = get_climate_data(lat, lon, parameters=parameters, temporal="monthly")
        results[label] = {
            "lat": lat,
            "lon": lon,
            "summary": data.get("parameter_info", {}),
            "error": data.get("error"),
        }

    return {
        "comparison": results,
        "parameters": parameters,
        "note": "Compare summary stats across locations for relative value signals",
    }


# --- Module Metadata ---
MODULE_INFO = {
    "name": "google_earth_engine_api",
    "category": "Alternative Data — Satellite & Geospatial",
    "source": "GEE STAC Catalog + NASA POWER API + Open-Elevation",
    "requires_api_key": False,
    "update_frequency": "daily",
    "functions": [
        "search_datasets",
        "get_dataset_info",
        "get_climate_data",
        "get_solar_irradiance",
        "get_precipitation_data",
        "get_elevation",
        "get_agriculture_signals",
        "get_wind_energy_potential",
        "compare_regions",
    ],
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
