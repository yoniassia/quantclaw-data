#!/usr/bin/env python3
"""
Statistics Canada WDS Module — Phase 1

Canadian official statistics: GDP (expenditure & monthly), CPI inflation,
labour force survey (unemployment, employment, participation), international
merchandise trade, retail sales, and housing starts.

Data Source: https://www150.statcan.gc.ca/t1/wds/rest
Protocol: REST (WDS — Web Data Service)
Auth: None (open access)
Refresh: Business days at 8:30 AM EST
Coverage: Canada
Rate Limit: 50 req/s global, 25 req/s per IP

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

BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "statcan_canada"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.3

SCALAR_MULTIPLIERS = {
    0: 1, 1: 10, 2: 100, 3: 1_000, 4: 10_000,
    5: 100_000, 6: 1_000_000, 7: 10_000_000,
    8: 100_000_000, 9: 1_000_000_000,
}

INDICATORS = {
    # === GDP (Table 36-10-0104-01, quarterly, expenditure-based) ===
    "GDP_CURRENT": {
        "vectorId": 62305752,
        "name": "GDP at Market Prices — Current Dollars (SAAR)",
        "description": "GDP expenditure-based, current prices, seasonally adjusted at annual rates",
        "frequency": "quarterly",
        "unit": "CAD millions",
        "table": "36-10-0104-01",
    },
    "GDP_REAL": {
        "vectorId": 62305723,
        "name": "GDP at Market Prices — Chained 2017$ (SAAR)",
        "description": "GDP expenditure-based, chained (2017) dollars, seasonally adjusted at annual rates",
        "frequency": "quarterly",
        "unit": "CAD millions",
        "table": "36-10-0104-01",
    },
    "GDP_MONTHLY": {
        "vectorId": 65201210,
        "name": "Monthly GDP — All Industries",
        "description": "GDP at basic prices, all industries, seasonally adjusted",
        "frequency": "monthly",
        "unit": "CAD millions",
        "table": "36-10-0434-01",
    },

    # === CPI / Inflation (Table 18-10-0004-01, monthly) ===
    "CPI_ALL_ITEMS": {
        "vectorId": 41690973,
        "name": "CPI All-Items (2002=100)",
        "description": "Consumer Price Index, all-items, Canada, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2002=100)",
        "table": "18-10-0004-01",
    },
    "CPI_FOOD": {
        "vectorId": 41690974,
        "name": "CPI Food",
        "description": "Consumer Price Index, food, Canada, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2002=100)",
        "table": "18-10-0004-01",
    },
    "CPI_SHELTER": {
        "productId": 18100004,
        "coordinate": "2.79.0.0.0.0.0.0.0.0",
        "name": "CPI Shelter",
        "description": "Consumer Price Index, shelter, Canada, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2002=100)",
        "table": "18-10-0004-01",
    },
    "CPI_ENERGY": {
        "productId": 18100004,
        "coordinate": "2.288.0.0.0.0.0.0.0.0",
        "name": "CPI Energy",
        "description": "Consumer Price Index, energy, Canada, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2002=100)",
        "table": "18-10-0004-01",
    },

    # === Labour Force Survey (Table 14-10-0287-01, monthly, SA) ===
    # Dims: Geography / Characteristic / Gender / Age / Statistics / DataType
    "UNEMPLOYMENT_RATE": {
        "productId": 14100287,
        "coordinate": "1.7.1.1.1.1.0.0.0.0",
        "name": "Unemployment Rate — SA (%)",
        "description": "Unemployment rate, Canada, both sexes, 15+, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "table": "14-10-0287-01",
    },
    "EMPLOYMENT": {
        "productId": 14100287,
        "coordinate": "1.3.1.1.1.1.0.0.0.0",
        "name": "Employment — SA (thousands)",
        "description": "Total employment, Canada, both sexes, 15+, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Thousands of persons",
        "table": "14-10-0287-01",
    },
    "FULL_TIME_EMPLOYMENT": {
        "productId": 14100287,
        "coordinate": "1.4.1.1.1.1.0.0.0.0",
        "name": "Full-Time Employment — SA (thousands)",
        "description": "Full-time employment, Canada, both sexes, 15+, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Thousands of persons",
        "table": "14-10-0287-01",
    },
    "PARTICIPATION_RATE": {
        "productId": 14100287,
        "coordinate": "1.8.1.1.1.1.0.0.0.0",
        "name": "Participation Rate — SA (%)",
        "description": "Labour force participation rate, Canada, both sexes, 15+, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "table": "14-10-0287-01",
    },
    "EMPLOYMENT_RATE": {
        "productId": 14100287,
        "coordinate": "1.9.1.1.1.1.0.0.0.0",
        "name": "Employment Rate — SA (%)",
        "description": "Employment rate, Canada, both sexes, 15+, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "table": "14-10-0287-01",
    },

    # === International Merchandise Trade (Table 12-10-0011-01, monthly) ===
    # Dims: Geography / Trade / Basis / Seasonal adjustment / Principal trading partners
    "MERCHANDISE_EXPORTS": {
        "productId": 12100011,
        "coordinate": "1.2.2.2.1.0.0.0.0.0",
        "name": "Merchandise Exports — BOP, SA (CAD mn)",
        "description": "International merchandise exports, balance of payments basis, seasonally adjusted, all countries",
        "frequency": "monthly",
        "unit": "CAD millions",
        "table": "12-10-0011-01",
    },
    "MERCHANDISE_IMPORTS": {
        "productId": 12100011,
        "coordinate": "1.1.2.2.1.0.0.0.0.0",
        "name": "Merchandise Imports — BOP, SA (CAD mn)",
        "description": "International merchandise imports, balance of payments basis, seasonally adjusted, all countries",
        "frequency": "monthly",
        "unit": "CAD millions",
        "table": "12-10-0011-01",
    },
    "TRADE_BALANCE": {
        "productId": 12100011,
        "coordinate": "1.3.2.2.1.0.0.0.0.0",
        "name": "Merchandise Trade Balance — BOP, SA (CAD mn)",
        "description": "International merchandise trade balance, balance of payments basis, seasonally adjusted",
        "frequency": "monthly",
        "unit": "CAD millions",
        "table": "12-10-0011-01",
    },

    # === Retail Trade (Table 20-10-0056-01, monthly) ===
    # Dims: Geography / NAICS / Sales / Adjustments
    "RETAIL_SALES": {
        "productId": 20100056,
        "coordinate": "1.1.1.2.0.0.0.0.0.0",
        "name": "Retail Trade Sales — Total, SA (CAD)",
        "description": "Retail trade sales, all trade groups, Canada, total sales, seasonally adjusted",
        "frequency": "monthly",
        "unit": "CAD (scalar: thousands)",
        "table": "20-10-0056-01",
    },

    # === Housing (Table 34-10-0156-01, monthly, CMHC) ===
    # Dims: Geography / Type of unit
    "HOUSING_STARTS": {
        "productId": 34100156,
        "coordinate": "1.1.0.0.0.0.0.0.0.0",
        "name": "Housing Starts — Total, SAAR (units)",
        "description": "CMHC housing starts, all areas 10,000+, Canada, total units, SAAR",
        "frequency": "monthly",
        "unit": "Units (scalar: thousands)",
        "table": "34-10-0156-01",
    },
    "NEW_HOUSING_PRICE_INDEX": {
        "vectorId": 111955442,
        "name": "New Housing Price Index — Total",
        "description": "New Housing Price Index, Canada, total (house and land)",
        "frequency": "monthly",
        "unit": "Index",
        "table": "18-10-0205-01",
    },
}


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# WDS API helpers
# ---------------------------------------------------------------------------

def _post_request(endpoint: str, body) -> Dict:
    """POST to a WDS endpoint, return parsed JSON or error dict."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.post(url, json=body, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": f"Request timed out ({REQUEST_TIMEOUT}s)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed — StatCan may be temporarily unavailable"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_request(endpoint: str) -> Dict:
    """GET from a WDS endpoint."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": f"Request timed out ({REQUEST_TIMEOUT}s)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed — StatCan may be temporarily unavailable"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_vector_data(raw_item: Dict) -> List[Dict]:
    """Parse a single WDS vector response item into data points."""
    if raw_item.get("status") != "SUCCESS":
        return []
    obj = raw_item.get("object", {})
    points = []
    for dp in obj.get("vectorDataPoint", []):
        val = dp.get("value")
        if val is None:
            continue
        try:
            val = float(val)
        except (ValueError, TypeError):
            continue
        scalar = dp.get("scalarFactorCode", 0)
        points.append({
            "ref_period": dp.get("refPer", ""),
            "value": val,
            "scalar_factor": scalar,
            "decimals": dp.get("decimals", 0),
            "status_code": dp.get("statusCode", 0),
            "release_time": dp.get("releaseTime", ""),
        })
    points.sort(key=lambda x: x["ref_period"], reverse=True)
    return points


def _fetch_by_vector(vector_id: int, latest_n: int = 24) -> Dict:
    """Fetch data using vector ID."""
    body = [{"vectorId": vector_id, "latestN": latest_n}]
    result = _post_request("getDataFromVectorsAndLatestNPeriods", body)
    if not result["success"]:
        return result
    data = result["data"]
    if not data or not isinstance(data, list):
        return {"success": False, "error": "Empty response from WDS"}
    return {"success": True, "items": data}


def _fetch_by_coordinate(product_id: int, coordinate: str, latest_n: int = 24) -> Dict:
    """Fetch data using table PID + coordinate."""
    body = [{"productId": product_id, "coordinate": coordinate, "latestN": latest_n}]
    result = _post_request("getDataFromCubePidCoordAndLatestNPeriods", body)
    if not result["success"]:
        return result
    data = result["data"]
    if not data or not isinstance(data, list):
        return {"success": False, "error": "Empty response from WDS"}
    return {"success": True, "items": data}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_data(indicator: str) -> Dict:
    """Fetch a specific indicator's time series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    last_n = 12 if cfg["frequency"] == "quarterly" else 24

    if "vectorId" in cfg:
        result = _fetch_by_vector(cfg["vectorId"], latest_n=last_n)
    elif "productId" in cfg and "coordinate" in cfg:
        result = _fetch_by_coordinate(cfg["productId"], cfg["coordinate"], latest_n=last_n)
    else:
        return {"success": False, "indicator": indicator, "error": "No vectorId or coordinate defined"}

    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_vector_data(result["items"][0])
    if not observations:
        status = result["items"][0].get("status", "UNKNOWN")
        code = result["items"][0].get("object", {}).get("responseStatusCode", "")
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": f"No data points returned (status={status}, code={code})",
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
        "table": cfg.get("table", ""),
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["ref_period"],
        "latest_release": observations[0].get("release_time", ""),
        "scalar_factor": observations[0].get("scalar_factor", 0),
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"period": o["ref_period"], "value": o["value"]}
            for o in observations[:30]
        ],
        "total_observations": len(observations),
        "source": BASE_URL,
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
            "table": v.get("table", ""),
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
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Statistics Canada WDS",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Table discovery
# ---------------------------------------------------------------------------

def discover_tables(keyword: str = None) -> Dict:
    """List available StatCan cubes, optionally filtered by keyword."""
    result = _get_request("getAllCubesListLite")
    if not result["success"]:
        return result

    tables = result["data"]
    if not isinstance(tables, list):
        return {"success": False, "error": "Unexpected response format"}

    if keyword:
        kw = keyword.lower()
        tables = [
            t for t in tables
            if kw in (t.get("cubeTitleEn") or "").lower()
            or kw in str(t.get("productId", ""))
        ]

    formatted = []
    for t in tables[:50]:
        formatted.append({
            "productId": t.get("productId"),
            "title": t.get("cubeTitleEn", ""),
            "start": t.get("cubeStartDate", ""),
            "end": t.get("cubeEndDate", ""),
            "frequency": t.get("frequencyCode"),
            "archived": t.get("archived"),
        })

    return {
        "success": True,
        "tables": formatted,
        "count": len(formatted),
        "total_available": len(result["data"]),
    }


def get_table_metadata(product_id: int) -> Dict:
    """Get full metadata for a StatCan table/cube."""
    body = [{"productId": product_id}]
    result = _post_request("getCubeMetadata", body)
    if not result["success"]:
        return result

    data = result["data"]
    if not data or not isinstance(data, list) or data[0].get("status") != "SUCCESS":
        return {"success": False, "error": "Metadata not available for this table"}

    obj = data[0]["object"]
    dimensions = []
    for d in obj.get("dimension", []):
        members = [
            {"id": m["memberId"], "name": m.get("memberNameEn", "")}
            for m in d.get("member", [])
        ]
        dimensions.append({
            "position": d["dimensionPositionId"],
            "name": d.get("dimensionNameEn", ""),
            "has_uom": d.get("hasUom", False),
            "members": members,
        })

    return {
        "success": True,
        "productId": obj.get("productId"),
        "title": obj.get("cubeTitleEn", ""),
        "start": obj.get("cubeStartDate", ""),
        "end": obj.get("cubeEndDate", ""),
        "frequency": obj.get("frequencyCode"),
        "series_count": obj.get("nbSeriesCube"),
        "dimensions": dimensions,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
Statistics Canada WDS Module (Phase 1)

Usage:
  python statcan_canada.py                           # Latest values for all indicators
  python statcan_canada.py <INDICATOR>                # Fetch specific indicator
  python statcan_canada.py list                       # List available indicators
  python statcan_canada.py discover [KEYWORD]         # Search StatCan tables
  python statcan_canada.py metadata <PID>             # Table metadata & dimensions

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (WDS — Web Data Service)
Coverage: Canada
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "discover":
            keyword = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(discover_tables(keyword), indent=2, default=str))
        elif cmd == "metadata":
            if len(sys.argv) < 3:
                print("Usage: statcan_canada.py metadata <PRODUCT_ID>")
                sys.exit(1)
            pid = int(sys.argv[2])
            print(json.dumps(get_table_metadata(pid), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
