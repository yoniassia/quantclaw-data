#!/usr/bin/env python3
"""
UK Office for National Statistics (ONS) Module

UK macroeconomic data via the ONS CMD (Customise My Data) beta API:
GDP (monthly), CPIH inflation, retail sales, trade in goods,
construction output, private housing rental prices, and labour market.

Data Source: https://api.beta.ons.gov.uk/v1
Protocol: REST / JSON
Auth: None (open beta)
Refresh: Monthly (varies by dataset)
Coverage: United Kingdom / Great Britain

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.beta.ons.gov.uk/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ons_uk"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.2

INDICATORS = {
    # --- GDP ---
    "GDP_MONTHLY": {
        "dataset": "gdp-to-four-decimal-places",
        "dimensions": {
            "geography": "K02000001",
            "unofficialstandardindustrialclassification": "A--T",
        },
        "name": "UK Monthly GDP Index (SA, 2016=100)",
        "description": "Monthly GDP estimate for the UK, all industries (A-T), seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2016=100)",
    },
    "GDP_SERVICES": {
        "dataset": "gdp-to-four-decimal-places",
        "dimensions": {
            "geography": "K02000001",
            "unofficialstandardindustrialclassification": "G--T",
        },
        "name": "UK Index of Services (SA, 2016=100)",
        "description": "Monthly index of services output, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2016=100)",
    },
    "GDP_PRODUCTION": {
        "dataset": "gdp-to-four-decimal-places",
        "dimensions": {
            "geography": "K02000001",
            "unofficialstandardindustrialclassification": "B--E",
        },
        "name": "UK Production Industries Index (SA, 2016=100)",
        "description": "Monthly index of production industries (B-E), seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2016=100)",
    },
    "GDP_MANUFACTURING": {
        "dataset": "gdp-to-four-decimal-places",
        "dimensions": {
            "geography": "K02000001",
            "unofficialstandardindustrialclassification": "C",
        },
        "name": "UK Manufacturing Index (SA, 2016=100)",
        "description": "Monthly manufacturing output index, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2016=100)",
    },
    # --- CPIH Inflation ---
    "CPIH_ALL": {
        "dataset": "cpih01",
        "dimensions": {
            "geography": "K02000001",
            "aggregate": "CP00",
        },
        "name": "CPIH All Items (Index, 2015=100)",
        "description": "Consumer Prices Index including owner occupiers' housing costs, all items",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    "CPIH_FOOD": {
        "dataset": "cpih01",
        "dimensions": {
            "geography": "K02000001",
            "aggregate": "CP01",
        },
        "name": "CPIH Food & Non-Alcoholic Beverages (Index)",
        "description": "CPIH: food and non-alcoholic beverages component",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    "CPIH_HOUSING": {
        "dataset": "cpih01",
        "dimensions": {
            "geography": "K02000001",
            "aggregate": "CP04",
        },
        "name": "CPIH Housing, Water, Electricity & Gas (Index)",
        "description": "CPIH: housing, water, electricity, gas and other fuels component",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    "CPIH_TRANSPORT": {
        "dataset": "cpih01",
        "dimensions": {
            "geography": "K02000001",
            "aggregate": "CP07",
        },
        "name": "CPIH Transport (Index)",
        "description": "CPIH: transport component",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    # --- Retail Sales ---
    "RETAIL_SALES_VOLUME": {
        "dataset": "retail-sales-index",
        "dimensions": {
            "geography": "K03000001",
            "unofficialstandardindustrialclassification": "all-retailing-including-automotive-fuel",
            "prices": "chained-volume-of-retail-sales",
            "seasonaladjustment": "seasonal-adjustment",
        },
        "name": "UK Retail Sales Volume Index (SA, 2019=100)",
        "description": "Chained volume of retail sales, all retailing incl. automotive fuel, SA",
        "frequency": "monthly",
        "unit": "Index (2019=100)",
    },
    "RETAIL_SALES_VALUE": {
        "dataset": "retail-sales-index",
        "dimensions": {
            "geography": "K03000001",
            "unofficialstandardindustrialclassification": "all-retailing-including-automotive-fuel",
            "prices": "value-of-retail-sales-at-current-prices",
            "seasonaladjustment": "seasonal-adjustment",
        },
        "name": "UK Retail Sales Value Index (SA, current prices)",
        "description": "Value of retail sales at current prices, all retailing incl. automotive fuel, SA",
        "frequency": "monthly",
        "unit": "Index (2019=100)",
    },
    # --- Trade in Goods ---
    "TRADE_EXPORTS_TOTAL": {
        "dataset": "trade",
        "dimensions": {
            "geography": "K02000001",
            "countriesandterritories": "W1",
            "direction": "EX",
            "standardindustrialtradeclassification": "T",
        },
        "name": "UK Total Goods Exports (GBP mn)",
        "description": "UK total goods exports to whole world, all SITC categories",
        "frequency": "monthly",
        "unit": "GBP mn",
    },
    "TRADE_IMPORTS_TOTAL": {
        "dataset": "trade",
        "dimensions": {
            "geography": "K02000001",
            "countriesandterritories": "W1",
            "direction": "IM",
            "standardindustrialtradeclassification": "T",
        },
        "name": "UK Total Goods Imports (GBP mn)",
        "description": "UK total goods imports from whole world, all SITC categories",
        "frequency": "monthly",
        "unit": "GBP mn",
    },
    "TRADE_EXPORTS_EU": {
        "dataset": "trade",
        "dimensions": {
            "geography": "K02000001",
            "countriesandterritories": "B5",
            "direction": "EX",
            "standardindustrialtradeclassification": "T",
        },
        "name": "UK Goods Exports to EU (GBP mn)",
        "description": "UK total goods exports to EU(28)",
        "frequency": "monthly",
        "unit": "GBP mn",
    },
    # --- Construction Output ---
    "CONSTRUCTION_OUTPUT": {
        "dataset": "output-in-the-construction-industry",
        "dimensions": {
            "geography": "K03000001",
            "seriestype": "pounds-million",
            "seasonaladjustment": "seasonal-adjustment",
            "typeofwork": "1",
        },
        "name": "UK Construction Output — All Work (GBP mn, SA)",
        "description": "Construction output in Great Britain, all work, seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
    },
    "CONSTRUCTION_NEW_WORK": {
        "dataset": "output-in-the-construction-industry",
        "dimensions": {
            "geography": "K03000001",
            "seriestype": "pounds-million",
            "seasonaladjustment": "seasonal-adjustment",
            "typeofwork": "1-2",
        },
        "name": "UK Construction Output — New Work (GBP mn, SA)",
        "description": "Construction output in Great Britain, all new work, seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
    },
    # --- Housing Rental Prices ---
    "HOUSING_RENTAL_INDEX": {
        "dataset": "index-private-housing-rental-prices",
        "dimensions": {
            "geography": "K02000001",
            "indexandyearchange": "index",
        },
        "name": "UK Private Housing Rental Price Index",
        "description": "Index of private housing rental prices, UK, Jan 2015=100",
        "frequency": "monthly",
        "unit": "Index (Jan 2015=100)",
    },
    "HOUSING_RENTAL_YOY": {
        "dataset": "index-private-housing-rental-prices",
        "dimensions": {
            "geography": "K02000001",
            "indexandyearchange": "year-on-year-change",
        },
        "name": "UK Private Housing Rental Prices YoY Change (%)",
        "description": "Year-on-year percentage change in private housing rental prices, UK",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Labour Market ---
    "UNEMPLOYMENT_RATE": {
        "dataset": "labour-market",
        "dimensions": {
            "geography": "K02000001",
            "agegroups": "16+",
            "economicactivity": "unemployed",
            "seasonaladjustment": "seasonal-adjustment",
            "sex": "all-adults",
            "unitofmeasure": "rates",
        },
        "name": "UK Unemployment Rate (%, 16+, SA)",
        "description": "UK unemployment rate, aged 16+, seasonally adjusted",
        "frequency": "quarterly-rolling",
        "unit": "%",
    },
    "EMPLOYMENT_RATE": {
        "dataset": "labour-market",
        "dimensions": {
            "geography": "K02000001",
            "agegroups": "16-64",
            "economicactivity": "in-employment",
            "seasonaladjustment": "seasonal-adjustment",
            "sex": "all-adults",
            "unitofmeasure": "rates",
        },
        "name": "UK Employment Rate (%, 16-64, SA)",
        "description": "UK employment rate, aged 16-64, seasonally adjusted",
        "frequency": "quarterly-rolling",
        "unit": "%",
    },
    "ECONOMIC_INACTIVITY_RATE": {
        "dataset": "labour-market",
        "dimensions": {
            "geography": "K02000001",
            "agegroups": "16-64",
            "economicactivity": "economically-inactive",
            "seasonaladjustment": "seasonal-adjustment",
            "sex": "all-adults",
            "unitofmeasure": "rates",
        },
        "name": "UK Economic Inactivity Rate (%, 16-64, SA)",
        "description": "UK economic inactivity rate, aged 16-64, seasonally adjusted",
        "frequency": "quarterly-rolling",
        "unit": "%",
    },
}

_version_cache: Dict[str, dict] = {}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
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


def _api_get(path: str, params: dict = None) -> Dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
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
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _discover_latest_version(dataset: str) -> Optional[str]:
    """Get the latest version number for a dataset (cached in-memory)."""
    if dataset in _version_cache:
        entry = _version_cache[dataset]
        if datetime.now() - entry["ts"] < timedelta(hours=CACHE_TTL_HOURS):
            return entry["version"]

    result = _api_get(f"datasets/{dataset}/editions/time-series")
    if not result["success"]:
        return None

    data = result["data"]
    latest_id = data.get("links", {}).get("latest_version", {}).get("id")
    if not latest_id:
        items = data.get("items", [])
        if items:
            latest_id = items[0].get("links", {}).get("latest_version", {}).get("id")

    if latest_id:
        _version_cache[dataset] = {"version": latest_id, "ts": datetime.now()}
    return latest_id


def _get_time_periods(dataset: str, version: str, limit: int = 24) -> List[str]:
    """Fetch available time periods for a dataset, newest first."""
    result = _api_get(
        f"datasets/{dataset}/editions/time-series/versions/{version}/dimensions/time/options",
        params={"limit": limit, "sort": "-time"},
    )
    if not result["success"]:
        return []
    return [item["option"] for item in result["data"].get("items", []) if "option" in item]


def _fetch_observation(dataset: str, version: str, dimensions: dict, time_val: str) -> Optional[dict]:
    """Fetch a single observation for specific dimension values + time."""
    params = {**dimensions, "time": time_val}
    result = _api_get(
        f"datasets/{dataset}/editions/time-series/versions/{version}/observations",
        params=params,
    )
    if not result["success"]:
        return None

    data = result["data"]
    obs_list = data.get("observations")
    if not obs_list:
        return None

    raw_val = obs_list[0].get("observation")
    if raw_val is None or raw_val == "":
        return None

    try:
        value = float(raw_val)
    except (ValueError, TypeError):
        return None

    return {
        "time_period": time_val,
        "value": value,
        "unit_of_measure": data.get("unit_of_measure"),
    }


def _period_granularity(period: str) -> str:
    """Classify a time period string: 'month', 'quarter', 'year', or 'rolling'."""
    p = period.lower()
    if "-q" in p:
        return "quarter"
    if any(m in p for m in ["jan", "feb", "mar", "apr", "may", "jun",
                            "jul", "aug", "sep", "oct", "nov", "dec"]):
        return "month"
    if p.replace("-", "").isdigit() and len(p.replace("-", "")) == 4:
        return "year"
    return "rolling"


def _find_comparable_previous(observations: List[Dict]) -> Optional[Dict]:
    """Find the next observation with the same granularity as the latest."""
    if len(observations) < 2:
        return None
    latest_gran = _period_granularity(observations[0]["time_period"])
    for obs in observations[1:]:
        if _period_granularity(obs["time_period"]) == latest_gran:
            return obs
    return observations[1] if len(observations) >= 2 else None


def fetch_data(indicator: str, n_periods: int = 24) -> Dict:
    """Fetch a time series for a specific indicator."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "n_periods": n_periods}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    version = _discover_latest_version(cfg["dataset"])
    if not version:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Could not discover dataset version"}

    periods = _get_time_periods(cfg["dataset"], version, limit=n_periods)
    if not periods:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No time periods available"}

    observations = []
    for period in periods:
        obs = _fetch_observation(cfg["dataset"], version, cfg["dimensions"], period)
        if obs:
            observations.append(obs)
        time.sleep(REQUEST_DELAY)

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

    period_change = period_change_pct = None
    prev_obs = _find_comparable_previous(observations)
    if prev_obs:
        latest_v = observations[0]["value"]
        prev_v = prev_obs["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "dataset": cfg["dataset"],
        "dataset_version": version,
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/datasets/{cfg['dataset']}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "dataset": v["dataset"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest value for one indicator, or latest for all."""
    if indicator:
        return fetch_data(indicator, n_periods=3)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key, n_periods=3)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "UK Office for National Statistics (ONS)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_datasets() -> List[Dict]:
    """List all available CMD datasets from ONS beta API."""
    all_datasets = []
    offset = 0
    while True:
        result = _api_get("datasets", params={"limit": 100, "offset": offset})
        if not result["success"]:
            break
        items = result["data"].get("items", [])
        if not items:
            break
        for item in items:
            all_datasets.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "description": item.get("description", "")[:120],
                "release_frequency": item.get("release_frequency"),
                "state": item.get("state"),
            })
        offset += 100
        if offset >= result["data"].get("total_count", 0):
            break
        time.sleep(REQUEST_DELAY)

    return all_datasets


# --- CLI ---

def _print_help():
    print("""
UK Office for National Statistics (ONS) Module

Usage:
  python ons_uk.py                         # Latest values for all indicators
  python ons_uk.py <INDICATOR>             # Fetch specific indicator time series
  python ons_uk.py list                    # List available indicators
  python ons_uk.py datasets                # Discover all ONS CMD datasets
  python ons_uk.py --help                  # This help message

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST / JSON (ONS CMD beta)
Coverage: United Kingdom
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "datasets":
            print(json.dumps(discover_datasets(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
