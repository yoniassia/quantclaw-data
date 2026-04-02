#!/usr/bin/env python3
"""
Statistics Norway (SSB) PxWeb Module

Norwegian national statistics: GDP, CPI inflation, unemployment, petroleum
deliveries, external trade, house prices, and industrial output.

Data Source: https://data.ssb.no/api/v0/en/table/
Protocol: PxWeb REST (POST JSON query, JSON-stat2 response)
Auth: None (fully open, no key required)
Refresh: Monthly/Quarterly depending on indicator
Coverage: Norway

Author: QUANTCLAW DATA Build Agent
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://data.ssb.no/api/v0/en/table"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ssb_norway"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    "GDP": {
        "table_id": "09189",
        "name": "Gross Domestic Product — Norway (NOK mn)",
        "description": "GDP at market values, current prices",
        "frequency": "annual",
        "unit": "NOK million",
        "query_filters": [
            {"code": "Makrost", "selection": {"filter": "item", "values": ["bnpb.nr23_9"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Priser"]}},
        ],
        "n_periods": 10,
    },
    "GDP_GROWTH": {
        "table_id": "09189",
        "name": "GDP Volume Growth — Norway (%)",
        "description": "Annual change in GDP volume (real growth rate)",
        "frequency": "annual",
        "unit": "%",
        "query_filters": [
            {"code": "Makrost", "selection": {"filter": "item", "values": ["bnpb.nr23_9"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Volum"]}},
        ],
        "n_periods": 10,
    },
    "CPI_INDEX": {
        "table_id": "03013",
        "name": "Consumer Price Index — Norway (2015=100)",
        "description": "CPI all items, monthly index with base year 2015=100",
        "frequency": "monthly",
        "unit": "index (2015=100)",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["KpiIndMnd"]}},
        ],
        "n_periods": 24,
    },
    "CPI_ANNUAL_RATE": {
        "table_id": "03013",
        "name": "CPI 12-Month Rate — Norway (%)",
        "description": "Consumer price index, 12-month rate of change",
        "frequency": "monthly",
        "unit": "%",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Tolvmanedersendring"]}},
        ],
        "n_periods": 24,
    },
    "UNEMPLOYMENT_RATE": {
        "table_id": "13760",
        "name": "Unemployment Rate — Norway (%, SA)",
        "description": "LFS unemployment rate, ages 15-74, both sexes, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "query_filters": [
            {"code": "Kjonn", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Alder", "selection": {"filter": "item", "values": ["15-74"]}},
            {"code": "Justering", "selection": {"filter": "item", "values": ["S"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["ArbledProsArbstyrk"]}},
        ],
        "n_periods": 24,
    },
    "TRADE_EXPORTS": {
        "table_id": "08799",
        "name": "Goods Exports — Norway (NOK)",
        "description": "External trade in goods, total exports value",
        "frequency": "monthly",
        "unit": "NOK",
        "query_filters": [
            {"code": "ImpEks", "selection": {"filter": "item", "values": ["2"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Verdi"]}},
        ],
        "n_periods": 24,
    },
    "TRADE_IMPORTS": {
        "table_id": "08799",
        "name": "Goods Imports — Norway (NOK)",
        "description": "External trade in goods, total imports value",
        "frequency": "monthly",
        "unit": "NOK",
        "query_filters": [
            {"code": "ImpEks", "selection": {"filter": "item", "values": ["1"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Verdi"]}},
        ],
        "n_periods": 24,
    },
    "HOUSE_PRICE_INDEX": {
        "table_id": "07221",
        "name": "House Price Index — Norway",
        "description": "Price index for existing dwellings, all Norway",
        "frequency": "quarterly",
        "unit": "index",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Boligindeks"]}},
        ],
        "n_periods": 20,
    },
    "HOUSE_PRICE_INDEX_SA": {
        "table_id": "07221",
        "name": "House Price Index — Norway (Seasonally Adjusted)",
        "description": "Price index for existing dwellings, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "index",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["SesJustBoligindeks"]}},
        ],
        "n_periods": 20,
    },
    "PETROLEUM_DELIVERIES": {
        "table_id": "11174",
        "name": "Petroleum Product Deliveries — Norway (mill. litres)",
        "description": "Total deliveries of petroleum products, nationwide",
        "frequency": "monthly",
        "unit": "million litres",
        "query_filters": [
            {"code": "Region", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Kjopegrupper", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "PetroleumProd", "selection": {"filter": "item", "values": ["00"]}},
        ],
        "n_periods": 24,
    },
    "INDUSTRIAL_OUTPUT": {
        "table_id": "09170",
        "name": "Industrial Output — Norway (NOK mn)",
        "description": "Total output at basic values, current prices",
        "frequency": "annual",
        "unit": "NOK million",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Prob"]}},
        ],
        "n_periods": 10,
    },
    "VALUE_ADDED": {
        "table_id": "09170",
        "name": "Gross Value Added — Norway (NOK mn)",
        "description": "Value added at basic prices, current prices",
        "frequency": "annual",
        "unit": "NOK million",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["BNPB"]}},
        ],
        "n_periods": 10,
    },
}

INDICATOR_GROUPS = {
    "gdp": ["GDP", "GDP_GROWTH"],
    "cpi": ["CPI_INDEX", "CPI_ANNUAL_RATE"],
    "unemployment": ["UNEMPLOYMENT_RATE"],
    "oil_production": ["PETROLEUM_DELIVERIES"],
    "trade": ["TRADE_EXPORTS", "TRADE_IMPORTS"],
    "house_prices": ["HOUSE_PRICE_INDEX", "HOUSE_PRICE_INDEX_SA"],
    "industrial": ["INDUSTRIAL_OUTPUT", "VALUE_ADDED"],
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


def _parse_jsonstat2(raw: Dict) -> List[Dict]:
    """Parse JSON-stat2 response into list of {period, value} records.

    All non-time dimensions are expected to be filtered to size 1, so the
    flat value array maps directly to the time dimension categories.
    """
    try:
        dim_ids = raw["id"]
        sizes = raw["size"]
        values = raw.get("value", [])
        dimensions = raw["dimension"]

        time_dim_id = None
        for role_time in raw.get("role", {}).get("time", []):
            if role_time in dim_ids:
                time_dim_id = role_time
                break
        if time_dim_id is None:
            time_dim_id = "Tid"

        time_dim = dimensions[time_dim_id]
        time_cat = time_dim["category"]
        time_index = time_cat["index"]
        time_labels = time_cat.get("label", {})

        time_pos = dim_ids.index(time_dim_id)
        time_size = sizes[time_pos]

        stride = 1
        for i in range(time_pos + 1, len(sizes)):
            stride *= sizes[i]
        prefix_stride = time_size * stride

        non_time_block = 0
        for i in range(time_pos):
            non_time_block = 0

        sorted_periods = sorted(time_index.items(), key=lambda x: x[1])

        results = []
        for period_code, period_idx in sorted_periods:
            val_index = period_idx * stride
            if val_index < len(values) and values[val_index] is not None:
                results.append({
                    "period": period_code,
                    "value": values[val_index],
                })

        results.sort(key=lambda x: x["period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return []


def _api_request(table_id: str, query_body: Dict) -> Dict:
    """POST a PxWeb query to SSB and return the response."""
    url = f"{BASE_URL}/{table_id}"
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=query_body, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 400:
            try:
                err = resp.json()
                return {"success": False, "error": f"Bad request: {err}"}
            except Exception:
                return {"success": False, "error": f"Bad request (HTTP 400): {resp.text[:200]}"}
        if resp.status_code == 404:
            return {"success": False, "error": f"Table {table_id} not found (HTTP 404)"}
        if resp.status_code == 403:
            return {"success": False, "error": "Access denied (HTTP 403)"}
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


def _build_query(cfg: Dict, n_periods: Optional[int] = None) -> Dict:
    """Build PxWeb POST query body from indicator config."""
    n = n_periods or cfg.get("n_periods", 12)
    query = list(cfg["query_filters"]) + [
        {"code": "Tid", "selection": {"filter": "top", "values": [str(n)]}}
    ]
    return {"query": query, "response": {"format": "json-stat2"}}


def fetch_data(indicator: str, n_periods: Optional[int] = None) -> Dict:
    """Fetch a specific indicator from SSB."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "n_periods": n_periods or cfg["n_periods"]}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    query_body = _build_query(cfg, n_periods)
    result = _api_request(cfg["table_id"], query_body)
    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_jsonstat2(result["data"])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No observations returned — table may have no data for requested period",
        }

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
        "table_id": cfg["table_id"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['table_id']}",
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
    for key in INDICATORS:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "table_id": data["table_id"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Statistics Norway (SSB)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def fetch_group(group_name: str) -> Dict:
    """Fetch all indicators in a named group (gdp, cpi, trade, etc.)."""
    group_name = group_name.lower()
    if group_name not in INDICATOR_GROUPS:
        return {
            "success": False,
            "error": f"Unknown group: {group_name}",
            "available_groups": list(INDICATOR_GROUPS.keys()),
        }

    results = {}
    errors = []
    for key in INDICATOR_GROUPS[group_name]:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = data
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(results),
        "group": group_name,
        "source": "Statistics Norway (SSB)",
        "indicators": results,
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Statistics Norway (SSB) PxWeb Module

Usage:
  python ssb_norway.py                         # Latest key indicators summary
  python ssb_norway.py <INDICATOR>             # Fetch specific indicator
  python ssb_norway.py gdp                     # GDP quarterly
  python ssb_norway.py cpi                     # CPI inflation monthly
  python ssb_norway.py unemployment            # Unemployment rate
  python ssb_norway.py oil_production          # Petroleum deliveries
  python ssb_norway.py trade                   # External trade (imports/exports)
  python ssb_norway.py house_prices            # House price index
  python ssb_norway.py industrial              # Industrial output
  python ssb_norway.py list                    # List all indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Groups: {', '.join(INDICATOR_GROUPS.keys())}

Source: {BASE_URL}
Protocol: PxWeb REST (POST JSON, JSON-stat2 response)
Coverage: Norway | Auth: None (open access)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd.lower() in INDICATOR_GROUPS:
            result = fetch_group(cmd)
            print(json.dumps(result, indent=2, default=str))
        elif cmd.upper() in INDICATORS:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
        else:
            result = fetch_group(cmd) if cmd.lower() in INDICATOR_GROUPS else fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
