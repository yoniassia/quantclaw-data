#!/usr/bin/env python3
"""
CSO Ireland (Central Statistics Office) — PxStat JSON-stat Module

Irish macroeconomic data: GDP/GNP, CPI inflation, labour force, retail sales,
residential property prices, and merchandise trade.

Data Source: https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset
Protocol: PxStat / JSON-stat 2.0
Auth: None (open access)
Formats: JSON-stat 2.0
Refresh: Monthly (CPI, retail, housing, trade), Quarterly (GDP, labour)
Coverage: Ireland

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

BASE_URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "cso_ireland"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- GDP / GNP (Quarterly, chain-linked 2019 reference year) ---
    "GDP_QUARTERLY": {
        "table_id": "NQQ48",
        "filters": {
            "STATISTIC": "NQQ48S04",
            "C02196V02652": "-",
        },
        "name": "GDP at Constant Market Prices (EUR mn, SA)",
        "description": "Quarterly GDP chain-linked 2019 prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "EUR million",
    },
    "GDP_CURRENT": {
        "table_id": "NQQ48",
        "filters": {
            "STATISTIC": "NQQ48S10",
            "C02196V02652": "-",
        },
        "name": "GDP at Current Market Prices (EUR mn, SA)",
        "description": "Quarterly GDP current prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "EUR million",
    },
    "GNP_QUARTERLY": {
        "table_id": "NQQ48",
        "filters": {
            "STATISTIC": "NQQ48S06",
            "C02196V02652": "-",
        },
        "name": "GNP at Constant Market Prices (EUR mn, SA)",
        "description": "Quarterly GNP chain-linked 2019 prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "EUR million",
    },
    # --- Consumer Prices (Monthly) ---
    "CPI_INDEX": {
        "table_id": "CPM01",
        "filters": {
            "STATISTIC": "CPM01C08",
            "C01779V03424": "-",
        },
        "name": "CPI All Items (Base Dec 2023=100)",
        "description": "Consumer Price Index, all items, base December 2023 = 100",
        "frequency": "monthly",
        "unit": "Index",
    },
    "CPI_YOY": {
        "table_id": "CPM01",
        "filters": {
            "STATISTIC": "CPM01C07",
            "C01779V03424": "-",
        },
        "name": "CPI Annual % Change",
        "description": "Consumer Price Index, percentage change over 12 months, all items",
        "frequency": "monthly",
        "unit": "%",
    },
    "CPI_MOM": {
        "table_id": "CPM01",
        "filters": {
            "STATISTIC": "CPM01C06",
            "C01779V03424": "-",
        },
        "name": "CPI Monthly % Change",
        "description": "Consumer Price Index, percentage change over 1 month, all items",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Labour Force (Quarterly) ---
    "UNEMPLOYMENT_RATE": {
        "table_id": "QLF18",
        "filters": {
            "STATISTIC": "QLF18C06",
            "C02076V02508": "316",
            "C02199V02655": "-",
        },
        "name": "ILO Unemployment Rate (15-74 years, %)",
        "description": "ILO unemployment rate, persons aged 15-74, both sexes",
        "frequency": "quarterly",
        "unit": "%",
    },
    "EMPLOYMENT_RATE": {
        "table_id": "QLF18",
        "filters": {
            "STATISTIC": "QLF18C04",
            "C02076V02508": "315",
            "C02199V02655": "-",
        },
        "name": "ILO Employment Rate (15-64 years, %)",
        "description": "ILO employment rate, persons aged 15-64, both sexes",
        "frequency": "quarterly",
        "unit": "%",
    },
    "PARTICIPATION_RATE": {
        "table_id": "QLF18",
        "filters": {
            "STATISTIC": "QLF18C02",
            "C02076V02508": "320",
            "C02199V02655": "-",
        },
        "name": "ILO Participation Rate (15+ years, %)",
        "description": "ILO labour force participation rate, persons aged 15 and over, both sexes",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Retail Sales (Monthly, Base 2015=100) ---
    "RETAIL_SALES_VOLUME": {
        "table_id": "RSM05",
        "filters": {
            "STATISTIC": "RSM05C04",
            "C02583V03135": "V3970",
        },
        "name": "Retail Sales Index — Volume (SA, 2015=100)",
        "description": "Retail sales index, volume adjusted (deflated), all retail businesses, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    "RETAIL_SALES_VALUE": {
        "table_id": "RSM05",
        "filters": {
            "STATISTIC": "RSM05C03",
            "C02583V03135": "V3970",
        },
        "name": "Retail Sales Index — Value (SA, 2015=100)",
        "description": "Retail sales index, value adjusted, all retail businesses, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
    },
    # --- Residential Property Prices (Monthly) ---
    "HOUSE_PRICE_INDEX": {
        "table_id": "HPM09",
        "filters": {
            "STATISTIC": "HPM09C01",
            "C02803V03373": "-",
        },
        "name": "Residential Property Price Index (National)",
        "description": "Residential property price index, national — all residential properties",
        "frequency": "monthly",
        "unit": "Index",
    },
    "HOUSE_PRICE_YOY": {
        "table_id": "HPM09",
        "filters": {
            "STATISTIC": "HPM09C04",
            "C02803V03373": "-",
        },
        "name": "House Price Annual % Change (National)",
        "description": "Residential property price index, percentage change over 12 months, national",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Merchandise Trade (Monthly, EUR million) ---
    "TRADE_EXPORTS": {
        "table_id": "TSM01",
        "filters": {
            "STATISTIC": "TSM01S2",
            "C02196V02652": "-",
        },
        "name": "Total Exports (EUR mn, SA)",
        "description": "Total merchandise exports, seasonally adjusted",
        "frequency": "monthly",
        "unit": "EUR million",
    },
    "TRADE_IMPORTS": {
        "table_id": "TSM01",
        "filters": {
            "STATISTIC": "TSM01S1",
            "C02196V02652": "-",
        },
        "name": "Total Imports (EUR mn, SA)",
        "description": "Total merchandise imports, seasonally adjusted",
        "frequency": "monthly",
        "unit": "EUR million",
    },
    "TRADE_BALANCE": {
        "table_id": "TSM01",
        "filters": {
            "STATISTIC": "TSM01S3",
            "C02196V02652": "-",
        },
        "name": "Trade Balance (EUR mn, SA)",
        "description": "Merchandise trade surplus (exports minus imports), seasonally adjusted",
        "frequency": "monthly",
        "unit": "EUR million",
    },
}


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


def _get_cat_position(dimension: dict, code: str) -> int:
    """Get the integer position of a category code within a JSON-stat dimension."""
    idx = dimension["category"]["index"]
    if isinstance(idx, list):
        return idx.index(code)
    return idx[code]


def _parse_time_label(raw_label: str) -> str:
    """Normalise PxStat time labels to sortable strings (e.g. '2024Q3', '2024-01')."""
    raw = raw_label.strip()
    if "Q" in raw and len(raw) >= 6:
        return raw
    parts = raw.split()
    if len(parts) == 2:
        year, month_name = parts
        months = {
            "January": "01", "February": "02", "March": "03", "April": "04",
            "May": "05", "June": "06", "July": "07", "August": "08",
            "September": "09", "October": "10", "November": "11", "December": "12",
        }
        m = months.get(month_name)
        if m:
            return f"{year}-{m}"
    return raw


def _parse_jsonstat(raw: dict, filters: dict) -> List[Dict]:
    """
    Extract a single time series from a JSON-stat 2.0 response.

    `filters` maps non-time dimension IDs to the category code to select.
    The time dimension (TLIST*) is auto-detected; all its periods are returned.
    """
    dims = raw["id"]
    sizes = raw["size"]
    values = raw["value"]

    time_dim_id = None
    time_dim_pos = None
    for i, d in enumerate(dims):
        if d.startswith("TLIST"):
            time_dim_id = d
            time_dim_pos = i
            break
    if time_dim_id is None:
        return []

    time_dim = raw["dimension"][time_dim_id]
    time_idx = time_dim["category"]["index"]
    time_labels = time_dim["category"]["label"]
    time_codes = time_idx if isinstance(time_idx, list) else sorted(time_idx, key=lambda k: time_idx[k])

    fixed_positions = {}
    for dim_id in dims:
        if dim_id == time_dim_id:
            continue
        code = filters.get(dim_id)
        if code is None:
            fixed_positions[dim_id] = 0
        else:
            fixed_positions[dim_id] = _get_cat_position(raw["dimension"][dim_id], code)

    strides = []
    for i in range(len(dims)):
        stride = 1
        for j in range(i + 1, len(dims)):
            stride *= sizes[j]
        strides.append(stride)

    results = []
    for t, time_code in enumerate(time_codes):
        flat_idx = 0
        for i, dim_id in enumerate(dims):
            if dim_id == time_dim_id:
                flat_idx += t * strides[i]
            else:
                flat_idx += fixed_positions[dim_id] * strides[i]

        val = None
        if isinstance(values, list) and flat_idx < len(values):
            val = values[flat_idx]
        elif isinstance(values, dict):
            val = values.get(str(flat_idx))

        if val is not None:
            label = time_labels.get(time_code, str(time_code))
            results.append({
                "time_period": _parse_time_label(label),
                "raw_code": time_code,
                "value": float(val),
            })

    results.sort(key=lambda x: x["time_period"], reverse=True)
    return results


def _api_request(table_id: str) -> Dict:
    """Fetch a full PxStat table as JSON-stat 2.0."""
    url = f"{BASE_URL}/{table_id}/JSON-stat/2.0/en"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
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


_table_cache: Dict[str, dict] = {}


def _get_table(table_id: str) -> Dict:
    """Fetch table with in-memory de-duplication (same table used by multiple indicators)."""
    if table_id in _table_cache:
        return _table_cache[table_id]
    result = _api_request(table_id)
    if result["success"]:
        _table_cache[table_id] = result
    return result


def fetch_data(indicator: str) -> Dict:
    """Fetch a specific indicator time series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]

    cache_params = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _get_table(cfg["table_id"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_jsonstat(result["data"], cfg["filters"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed"}

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
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
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['table_id']}/JSON-stat/2.0/en",
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
            "table_id": v["table_id"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    results = {}
    errors = []
    seen_tables = set()
    for key in INDICATORS:
        tid = INDICATORS[key]["table_id"]
        if tid not in seen_tables:
            time.sleep(REQUEST_DELAY)
            seen_tables.add(tid)
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})

    return {
        "success": True,
        "source": "CSO Ireland (PxStat)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_tables(table_id: str) -> Dict:
    """Discover dimensions and categories for a given PxStat table."""
    result = _api_request(table_id)
    if not result["success"]:
        return result

    raw = result["data"]
    info = {
        "table_id": table_id,
        "label": raw.get("label"),
        "updated": raw.get("updated"),
        "dimensions": [],
    }
    for dim_id in raw.get("id", []):
        dim = raw["dimension"][dim_id]
        cats = dim["category"]["label"]
        info["dimensions"].append({
            "id": dim_id,
            "label": dim.get("label", dim_id),
            "categories": {k: v for k, v in cats.items()},
        })
    return {"success": True, **info}


# --- CLI ---

def _print_help():
    print("""
CSO Ireland (PxStat) Module — Phase 1

Usage:
  python cso_ireland.py                     # Latest values for all indicators
  python cso_ireland.py <INDICATOR>         # Fetch specific indicator
  python cso_ireland.py list                # List available indicators
  python cso_ireland.py discover <TABLE>    # Discover table dimensions

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: PxStat / JSON-stat 2.0
Coverage: Ireland
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "discover" and len(sys.argv) > 2:
            print(json.dumps(discover_tables(sys.argv[2]), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
