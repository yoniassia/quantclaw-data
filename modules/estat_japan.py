#!/usr/bin/env python3
"""
e-Stat Japan Module — Phase 1

Japan's official government statistics portal: GDP (SNA), CPI, labour force,
industrial production, trade statistics, housing starts, machinery orders.

Data Source: https://api.e-stat.go.jp/rest/3.0/app
Protocol: REST (JSON)
Auth: Application ID (free registration at https://www.e-stat.go.jp/api/)
      Store as ESTAT_JAPAN_APP_ID in .env or environment variable.
Refresh: Monthly / Quarterly depending on series
Coverage: Japan (national + prefectural)

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import os
import sys
import time
import hashlib
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "estat_japan"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- Consumer Price Index (Statistics Bureau, MIC) ---
    "CPI_ALL_ITEMS": {
        "stats_data_id": "0003427113",
        "name": "CPI All Items — National (2020=100)",
        "description": "Consumer Price Index, all items, national average, monthly",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
        "stats_code": "00200573",
    },
    "CPI_CORE": {
        "stats_data_id": "0003427113",
        "name": "CPI Core — National, ex Fresh Food (2020=100)",
        "description": "Consumer Price Index, all items less fresh food, national average, monthly",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
        "stats_code": "00200573",
    },

    # --- GDP / National Accounts (Cabinet Office ESRI) ---
    "GDP_NOMINAL": {
        "stats_data_id": None,
        "name": "Nominal GDP — Quarterly (JPY bn)",
        "description": "Quarterly estimates of GDP, expenditure approach, nominal, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "JPY bn",
        "stats_code": "00100409",
        "search_keyword": "国内総生産",
    },
    "GDP_REAL": {
        "stats_data_id": None,
        "name": "Real GDP — Quarterly (JPY bn, chained)",
        "description": "Quarterly estimates of GDP, expenditure approach, real, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "JPY bn (chained)",
        "stats_code": "00100409",
        "search_keyword": "国内総生産 実質",
    },

    # --- Labour Force Survey (Statistics Bureau) ---
    "UNEMPLOYMENT_RATE": {
        "stats_data_id": None,
        "name": "Unemployment Rate (%)",
        "description": "Complete unemployment rate, both sexes, seasonally adjusted, monthly",
        "frequency": "monthly",
        "unit": "%",
        "stats_code": "00200531",
        "search_keyword": "完全失業率",
    },
    "LABOUR_FORCE": {
        "stats_data_id": None,
        "name": "Labour Force Population (10k persons)",
        "description": "Labour force, both sexes, monthly",
        "frequency": "monthly",
        "unit": "10,000 persons",
        "stats_code": "00200531",
        "search_keyword": "労働力人口",
    },

    # --- Industrial Production (METI) ---
    "INDUSTRIAL_PRODUCTION": {
        "stats_data_id": None,
        "name": "Index of Industrial Production (2020=100)",
        "description": "Indices of industrial production, mining and manufacturing, monthly",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
        "stats_code": "00550010",
        "search_keyword": "鉱工業指数 生産",
    },

    # --- Trade Statistics (Ministry of Finance / Customs) ---
    "TRADE_EXPORTS": {
        "stats_data_id": None,
        "name": "Exports — Total Value (JPY mn)",
        "description": "Total value of exports, customs clearance basis, monthly",
        "frequency": "monthly",
        "unit": "JPY mn",
        "stats_code": "00350300",
        "search_keyword": "貿易統計 輸出",
    },
    "TRADE_IMPORTS": {
        "stats_data_id": None,
        "name": "Imports — Total Value (JPY mn)",
        "description": "Total value of imports, customs clearance basis, monthly",
        "frequency": "monthly",
        "unit": "JPY mn",
        "stats_code": "00350300",
        "search_keyword": "貿易統計 輸入",
    },

    # --- Housing Starts (MLIT) ---
    "HOUSING_STARTS": {
        "stats_data_id": None,
        "name": "New Housing Starts — Total Units",
        "description": "New construction starts of dwellings, total number of units, monthly",
        "frequency": "monthly",
        "unit": "units",
        "stats_code": "00600120",
        "search_keyword": "新設住宅着工戸数",
    },

    # --- Machinery Orders (Cabinet Office) ---
    "MACHINERY_ORDERS": {
        "stats_data_id": None,
        "name": "Machinery Orders — Private ex. Volatile (JPY bn)",
        "description": "Machinery orders received, private sector excluding ships and electric power, monthly",
        "frequency": "monthly",
        "unit": "JPY bn",
        "stats_code": "00100407",
        "search_keyword": "機械受注 民需",
    },
}


def _get_app_id() -> Optional[str]:
    """Get the e-Stat Application ID from environment or .env file."""
    app_id = os.environ.get("ESTAT_JAPAN_APP_ID")
    if app_id:
        return app_id
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("ESTAT_JAPAN_APP_ID=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
    return None


def _require_app_id() -> Dict:
    """Check for app ID and return error dict if missing."""
    app_id = _get_app_id()
    if not app_id:
        return {
            "success": False,
            "error": "ESTAT_JAPAN_APP_ID not configured",
            "help": (
                "Register free at https://www.e-stat.go.jp/api/ to get an Application ID. "
                "Then set ESTAT_JAPAN_APP_ID in your .env file or as an environment variable."
            ),
        }
    return None


def _cache_path(key: str, params_hash: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", key)
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
        path.write_text(json.dumps(data, default=str, ensure_ascii=False))
    except OSError:
        pass


def _api_request(endpoint: str, params: dict) -> Dict:
    """Make an authenticated request to the e-Stat JSON API."""
    app_id = _get_app_id()
    if not app_id:
        return {"success": False, "error": "No API key configured"}

    url = f"{BASE_URL}/json/{endpoint}"
    params["appId"] = app_id
    params.setdefault("lang", "E")

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        root_key = None
        for k in data:
            if k.startswith("GET_"):
                root_key = k
                break
        if not root_key:
            return {"success": False, "error": "Unexpected response structure"}

        result_block = data[root_key].get("RESULT", {})
        status = result_block.get("STATUS", -1)
        if status != 0:
            return {
                "success": False,
                "error": result_block.get("ERROR_MSG", f"API status {status}"),
                "status_code": status,
            }
        return {"success": True, "data": data[root_key]}

    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {code}"}
    except (ValueError, KeyError) as e:
        return {"success": False, "error": f"Parse error: {e}"}


def _parse_time_code(code: str) -> str:
    """Parse e-Stat time code into a human-readable period string.

    Common formats:
      Annual:    '2024000000' or '2024100000'
      Monthly:   '2024000101' (Jan), '2024001212' (Dec)
      Quarterly: '2024000103' (Q1), '2024000406' (Q2)
    """
    code = str(code).strip()
    if len(code) >= 10:
        year = code[:4]
        mid = code[4:]
        m1 = int(mid[2:4]) if mid[2:4].isdigit() else 0
        m2 = int(mid[4:6]) if mid[4:6].isdigit() else 0
        if m1 == 0 and m2 == 0:
            return year
        if m1 == m2 and m1 > 0:
            return f"{year}-{m1:02d}"
        if m1 > 0 and m2 > 0 and m2 != m1:
            q = {3: 1, 6: 2, 9: 3, 12: 4}.get(m2, 0)
            if q:
                return f"{year}-Q{q}"
            return f"{year}-{m1:02d}/{m2:02d}"
        if m1 > 0:
            return f"{year}-{m1:02d}"
    return code


def _parse_stats_data(raw: Dict) -> List[Dict]:
    """Extract observations from getStatsData response."""
    try:
        stat_data = raw.get("STATISTICAL_DATA", {})
        data_inf = stat_data.get("DATA_INF", {})
        values = data_inf.get("VALUE", [])
        if not values:
            return []

        class_info = stat_data.get("CLASS_INF", {})
        class_objs = class_info.get("CLASS_OBJ", [])

        dim_labels = {}
        for obj in class_objs:
            dim_id = obj.get("@id", "")
            classes = obj.get("CLASS", [])
            if isinstance(classes, dict):
                classes = [classes]
            dim_labels[dim_id] = {
                c.get("@code", ""): c.get("@name", c.get("@code", ""))
                for c in classes
            }

        observations = []
        for val in values:
            raw_value = val.get("$")
            if raw_value in (None, "", "-", "***", "…", "..."):
                continue
            try:
                numeric = float(raw_value)
            except (ValueError, TypeError):
                continue

            time_code = val.get("@time", "")
            period = _parse_time_code(time_code)

            dims = {}
            for key, v in val.items():
                if key.startswith("@") and key not in ("@time", "@unit"):
                    dim_id = key[1:]
                    label = dim_labels.get(dim_id, {}).get(v, v)
                    dims[dim_id] = {"code": v, "label": label}

            observations.append({
                "time_code": time_code,
                "period": period,
                "value": numeric,
                "dimensions": dims,
            })

        observations.sort(key=lambda x: x["time_code"], reverse=True)
        return observations

    except (KeyError, TypeError, ValueError):
        return []


def search_tables(keyword: str, stats_code: str = None, limit: int = 10) -> Dict:
    """Search for statistical tables via getStatsList.

    Args:
        keyword: Search keyword (Japanese or English).
        stats_code: Government statistics code to narrow results.
        limit: Max results to return.
    """
    auth_err = _require_app_id()
    if auth_err:
        return auth_err

    cache_key = f"search_{keyword}_{stats_code}"
    cp = _cache_path(cache_key, _params_hash({"keyword": keyword, "stats_code": stats_code}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"searchWord": keyword, "limit": str(limit)}
    if stats_code:
        params["statsCode"] = stats_code

    result = _api_request("getStatsList", params)
    if not result["success"]:
        return result

    try:
        datalist = result["data"].get("DATALIST_INF", {})
        tables_raw = datalist.get("TABLE_INF", [])
        if isinstance(tables_raw, dict):
            tables_raw = [tables_raw]

        tables = []
        for t in tables_raw:
            stat_name = t.get("STATISTICS_NAME", "")
            if isinstance(stat_name, dict):
                stat_name = stat_name.get("$", str(stat_name))

            title = t.get("TITLE", "")
            if isinstance(title, dict):
                title = title.get("$", str(title))

            tables.append({
                "stats_data_id": t.get("@id", ""),
                "stat_name": stat_name,
                "title": title,
                "cycle": t.get("CYCLE", ""),
                "survey_date": t.get("SURVEY_DATE", ""),
                "updated": t.get("UPDATED_DATE", ""),
            })

        response = {
            "success": True,
            "keyword": keyword,
            "stats_code": stats_code,
            "tables": tables,
            "count": len(tables),
            "timestamp": datetime.now().isoformat(),
        }
        _write_cache(cp, response)
        return response

    except (KeyError, TypeError) as e:
        return {"success": False, "error": f"Failed to parse table list: {e}"}


def _resolve_table_id(indicator_key: str) -> Optional[str]:
    """Resolve the stats_data_id for an indicator, using search if needed."""
    cfg = INDICATORS.get(indicator_key)
    if not cfg:
        return None

    if cfg.get("stats_data_id"):
        return cfg["stats_data_id"]

    resolve_cache = _cache_path(f"resolve_{indicator_key}", "table_id")
    cached = _read_cache(resolve_cache)
    if cached and cached.get("stats_data_id"):
        return cached["stats_data_id"]

    keyword = cfg.get("search_keyword", "")
    stats_code = cfg.get("stats_code", "")
    if not keyword and not stats_code:
        return None

    result = search_tables(keyword, stats_code=stats_code, limit=5)
    if not result.get("success") or not result.get("tables"):
        return None

    table_id = result["tables"][0]["stats_data_id"]
    _write_cache(resolve_cache, {
        "stats_data_id": table_id,
        "title": result["tables"][0].get("title", ""),
        "resolved_from": indicator_key,
    })
    return table_id


def fetch_table(stats_data_id: str, limit: int = 200, **filters) -> Dict:
    """Fetch raw data from any e-Stat table by its statsDataId.

    Args:
        stats_data_id: The statistical table ID.
        limit: Max data points to retrieve.
        **filters: Category/area filters (cdTab, cdCat01, cdArea, cdTime, etc.).
    """
    auth_err = _require_app_id()
    if auth_err:
        return auth_err

    cache_params = {"id": stats_data_id, "limit": limit, **filters}
    cp = _cache_path(f"table_{stats_data_id}", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "statsDataId": stats_data_id,
        "limit": str(limit),
        "metaGetFlg": "Y",
    }
    for k, v in filters.items():
        params[k] = str(v)

    result = _api_request("getStatsData", params)
    if not result["success"]:
        return {
            "success": False,
            "stats_data_id": stats_data_id,
            "error": result.get("error", "Unknown error"),
        }

    observations = _parse_stats_data(result["data"])
    if not observations:
        return {
            "success": False,
            "stats_data_id": stats_data_id,
            "error": "No valid observations in response",
        }

    table_inf = result["data"].get("STATISTICAL_DATA", {}).get("TABLE_INF", {})
    title = table_inf.get("TITLE", "")
    if isinstance(title, dict):
        title = title.get("$", str(title))

    response = {
        "success": True,
        "stats_data_id": stats_data_id,
        "title": title,
        "observations": observations[:60],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/json/getStatsData?statsDataId={stats_data_id}",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_data(indicator: str, limit: int = 200) -> Dict:
    """Fetch data for a pre-configured indicator.

    Args:
        indicator: Indicator key from INDICATORS dict.
        limit: Max data points.
    """
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    auth_err = _require_app_id()
    if auth_err:
        return auth_err

    cfg = INDICATORS[indicator]

    cache_params = {"indicator": indicator, "limit": limit}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    table_id = _resolve_table_id(indicator)
    if not table_id:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "Could not resolve table ID. Try search_tables() to find the right table.",
        }

    raw = fetch_table(table_id, limit=limit)
    if not raw.get("success"):
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": raw.get("error", "Failed to fetch table data"),
        }

    observations = raw.get("observations", [])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No observations returned",
        }

    latest = observations[0]
    period_change = period_change_pct = None
    if len(observations) >= 2:
        lv = latest["value"]
        pv = observations[1]["value"]
        if pv and pv != 0:
            period_change = round(lv - pv, 4)
            period_change_pct = round((period_change / abs(pv)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest["value"],
        "latest_period": latest["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"period": o["period"], "value": o["value"]} for o in observations[:30]
        ],
        "total_observations": len(observations),
        "stats_data_id": table_id,
        "source": f"{BASE_URL}/json/getStatsData?statsDataId={table_id}",
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
            "stats_data_id": v.get("stats_data_id"),
            "requires_discovery": v.get("stats_data_id") is None,
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    auth_err = _require_app_id()
    if auth_err:
        return auth_err

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
        "source": "e-Stat Japan (api.e-stat.go.jp)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
e-Stat Japan Module (Phase 1) — Official Japanese Government Statistics

Usage:
  python estat_japan.py                         # Latest values for all indicators
  python estat_japan.py <INDICATOR>              # Fetch specific indicator
  python estat_japan.py list                     # List available indicators
  python estat_japan.py search <keyword>         # Search for tables by keyword
  python estat_japan.py table <statsDataId>      # Fetch raw table data by ID

Indicators:""")
    for key, cfg in INDICATORS.items():
        marker = " " if cfg.get("stats_data_id") else "*"
        print(f"  {marker} {key:<28s} {cfg['name']}")
    print(f"""
  * = table ID resolved dynamically via getStatsList on first fetch

Auth: Set ESTAT_JAPAN_APP_ID in .env or environment (free at https://www.e-stat.go.jp/api/)

Source: {BASE_URL}
Coverage: Japan (national + prefectural)
Protocol: REST (JSON)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str, ensure_ascii=False))
        elif cmd == "search":
            kw = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            if not kw:
                print("Usage: python estat_japan.py search <keyword> [statsCode]")
                sys.exit(1)
            sc = None
            if len(sys.argv) > 3 and sys.argv[-1].isdigit() and len(sys.argv[-1]) >= 5:
                sc = sys.argv[-1]
                kw = " ".join(sys.argv[2:-1])
            print(json.dumps(search_tables(kw, stats_code=sc), indent=2, default=str, ensure_ascii=False))
        elif cmd == "table":
            if len(sys.argv) < 3:
                print("Usage: python estat_japan.py table <statsDataId> [limit]")
                sys.exit(1)
            sid = sys.argv[2]
            lim = int(sys.argv[3]) if len(sys.argv) > 3 else 200
            print(json.dumps(fetch_table(sid, limit=lim), indent=2, default=str, ensure_ascii=False))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
