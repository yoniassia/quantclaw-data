#!/usr/bin/env python3
"""
Statistics Estonia (PxWeb) Module

Estonian national statistics: GDP, CPI inflation, labour market,
foreign trade (exports/imports), and industrial production.

Data Source: https://andmed.stat.ee/api/v1/en/stat
Protocol: PxWeb REST API
Auth: None (open access)
Refresh: Quarterly (GDP, labour, trade), Monthly (CPI, industrial production)
Coverage: Estonia

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

BASE_URL = "https://andmed.stat.ee/api/v1/en/stat"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "statistics_estonia"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- GDP (quarterly) ---
    "GDP_NOMINAL": {
        "table_path": "majandus/rahvamajanduse-arvepidamine/sisemajanduse-koguprodukt-(skp)/pehilised-rahvamajanduse-arvepidamise-naitajad/RAA0012.PX",
        "query": [
            {"code": "Aasta", "selection": {"filter": "top", "values": ["5"]}},
            {"code": "Kvartal", "selection": {"filter": "item", "values": ["I", "II", "III", "IV"]}},
            {"code": "Sesoonne korrigeerimine", "selection": {"filter": "item", "values": ["1"]}},
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "name": "GDP at Current Prices (EUR mn, quarterly)",
        "description": "Estonia gross domestic product at current prices, seasonally unadjusted",
        "frequency": "quarterly",
        "unit": "EUR mn",
        "key_map": {"year_idx": 0, "quarter_idx": 1},
    },
    "GDP_REAL_GROWTH": {
        "table_path": "majandus/rahvamajanduse-arvepidamine/sisemajanduse-koguprodukt-(skp)/pehilised-rahvamajanduse-arvepidamise-naitajad/RAA0012.PX",
        "query": [
            {"code": "Aasta", "selection": {"filter": "top", "values": ["5"]}},
            {"code": "Kvartal", "selection": {"filter": "item", "values": ["I", "II", "III", "IV"]}},
            {"code": "Sesoonne korrigeerimine", "selection": {"filter": "item", "values": ["1"]}},
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["5"]}},
        ],
        "name": "Real GDP Growth YoY (%)",
        "description": "GDP chain-linked volume change vs same quarter previous year",
        "frequency": "quarterly",
        "unit": "%",
        "key_map": {"year_idx": 0, "quarter_idx": 1},
    },
    # --- CPI Inflation (annual) ---
    "CPI_ANNUAL": {
        "table_path": "majandus/hinnad/IA001.PX",
        "query": [
            {"code": "Aasta", "selection": {"filter": "top", "values": ["10"]}},
            {"code": "Kaubagrupp", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "name": "CPI Inflation YoY (%, annual)",
        "description": "Consumer price index, annual change over previous year, all items",
        "frequency": "annual",
        "unit": "%",
        "key_map": {"year_idx": 0},
    },
    # --- CPI Monthly ---
    "CPI_MONTHLY": {
        "table_path": "majandus/hinnad/IA021.PX",
        "query": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["1"]}},
            {"code": "Aasta", "selection": {"filter": "top", "values": ["3"]}},
            {"code": "Kuu", "selection": {"filter": "item", "values": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]}},
        ],
        "name": "CPI Inflation YoY (%, monthly)",
        "description": "Consumer price index, monthly change vs same month previous year",
        "frequency": "monthly",
        "unit": "%",
        "key_map": {"indicator_idx": 0, "year_idx": 1, "month_idx": 2},
    },
    # --- HICP ---
    "HICP_ANNUAL": {
        "table_path": "majandus/hinnad/IA022.PX",
        "query": [
            {"code": "Aasta", "selection": {"filter": "top", "values": ["10"]}},
            {"code": "Kaubad, teenused", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "name": "HICP Inflation YoY (%, annual)",
        "description": "Harmonised index of consumer prices, annual change, all items",
        "frequency": "annual",
        "unit": "%",
        "key_map": {"year_idx": 0},
    },
    # --- Labour Market (quarterly) ---
    "EMPLOYMENT_RATE": {
        "table_path": "sotsiaalelu/tooturg/tooturu-uldandmed/luhiajastatistika/TT0160.px",
        "query": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["EMPRATE"]}},
            {"code": "Sugu", "selection": {"filter": "item", "values": ["T"]}},
            {"code": "Vanuser\u00fchm", "selection": {"filter": "item", "values": ["Y15-74"]}},
            {"code": "Vaatlusperiood", "selection": {"filter": "top", "values": ["20"]}},
        ],
        "name": "Employment Rate (%, ages 15-74)",
        "description": "Employment rate, total population aged 15-74, quarterly",
        "frequency": "quarterly",
        "unit": "%",
        "key_map": {"period_idx": 3},
    },
    "UNEMPLOYMENT_RATE": {
        "table_path": "sotsiaalelu/tooturg/tooturu-uldandmed/luhiajastatistika/TT0160.px",
        "query": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["UNEMP_RATE"]}},
            {"code": "Sugu", "selection": {"filter": "item", "values": ["T"]}},
            {"code": "Vanuser\u00fchm", "selection": {"filter": "item", "values": ["Y15-74"]}},
            {"code": "Vaatlusperiood", "selection": {"filter": "top", "values": ["20"]}},
        ],
        "name": "Unemployment Rate (%, ages 15-74)",
        "description": "Unemployment rate, total population aged 15-74, quarterly",
        "frequency": "quarterly",
        "unit": "%",
        "key_map": {"period_idx": 3},
    },
    "LABOUR_FORCE": {
        "table_path": "sotsiaalelu/tooturg/tooturu-uldandmed/luhiajastatistika/TT0160.px",
        "query": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["LABOUR"]}},
            {"code": "Sugu", "selection": {"filter": "item", "values": ["T"]}},
            {"code": "Vanuser\u00fchm", "selection": {"filter": "item", "values": ["Y15-74"]}},
            {"code": "Vaatlusperiood", "selection": {"filter": "top", "values": ["20"]}},
        ],
        "name": "Labour Force (thousands, ages 15-74)",
        "description": "Labour force size in thousands, total population aged 15-74, quarterly",
        "frequency": "quarterly",
        "unit": "thousands",
        "key_map": {"period_idx": 3},
    },
    # --- Foreign Trade (annual, from national accounts expenditure approach) ---
    "EXPORTS": {
        "table_path": "majandus/rahvamajanduse-arvepidamine/sisemajanduse-koguprodukt-(skp)/sisemajanduse-koguprodukt-tarbimise-meetodil/RAA0061.PX",
        "query": [
            {"code": "Komponent", "selection": {"filter": "item", "values": ["7"]}},
            {"code": "Aasta", "selection": {"filter": "top", "values": ["5"]}},
            {"code": "Kvartal", "selection": {"filter": "item", "values": ["I", "II", "III", "IV"]}},
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "name": "Exports of Goods & Services (EUR mn, quarterly)",
        "description": "Exports of goods and services (f.o.b.), current prices, quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
        "key_map": {"year_idx": 1, "quarter_idx": 2},
    },
    "IMPORTS": {
        "table_path": "majandus/rahvamajanduse-arvepidamine/sisemajanduse-koguprodukt-(skp)/sisemajanduse-koguprodukt-tarbimise-meetodil/RAA0061.PX",
        "query": [
            {"code": "Komponent", "selection": {"filter": "item", "values": ["10"]}},
            {"code": "Aasta", "selection": {"filter": "top", "values": ["5"]}},
            {"code": "Kvartal", "selection": {"filter": "item", "values": ["I", "II", "III", "IV"]}},
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "name": "Imports of Goods & Services (EUR mn, quarterly)",
        "description": "Imports of goods and services (f.o.b.), current prices, quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
        "key_map": {"year_idx": 1, "quarter_idx": 2},
    },
    # --- Industrial Production (monthly, requires dynamic period resolution) ---
    "INDUSTRIAL_PRODUCTION_INDEX": {
        "table_path": "majandus/toostus/TO0053.PX",
        "query_template": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["PROD"]}},
            {"code": "Tegevusala", "selection": {"filter": "item", "values": ["BTD"]}},
            {"code": "Korrigeerimine", "selection": {"filter": "item", "values": ["Y"]}},
        ],
        "dynamic_time_dim": {"code": "Vaatlusperiood", "last_n": 24},
        "name": "Industrial Production Index (2021=100, monthly)",
        "description": "Volume index of industrial production, calendar & seasonally adjusted, total industry",
        "frequency": "monthly",
        "unit": "index 2021=100",
        "key_map": {"period_idx": 3},
    },
    "INDUSTRIAL_PRODUCTION_YOY": {
        "table_path": "majandus/toostus/TO0053.PX",
        "query_template": [
            {"code": "N\u00e4itaja", "selection": {"filter": "item", "values": ["PROD_SM"]}},
            {"code": "Tegevusala", "selection": {"filter": "item", "values": ["BTD"]}},
            {"code": "Korrigeerimine", "selection": {"filter": "item", "values": ["N"]}},
        ],
        "dynamic_time_dim": {"code": "Vaatlusperiood", "last_n": 24},
        "name": "Industrial Production YoY Change (%)",
        "description": "Industrial production volume index change vs same period previous year, unadjusted",
        "frequency": "monthly",
        "unit": "%",
        "key_map": {"period_idx": 3},
    },
}

QUARTER_MAP = {"I": "Q1", "II": "Q2", "III": "Q3", "IV": "Q4"}


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


def _build_period(key: List[str], key_map: Dict) -> str:
    """Build a sortable period string from PxWeb response key fields."""
    if "period_idx" in key_map:
        return key[key_map["period_idx"]]
    year = key[key_map["year_idx"]]
    if "quarter_idx" in key_map:
        q = key[key_map["quarter_idx"]]
        return f"{year}{QUARTER_MAP.get(q, q)}"
    if "month_idx" in key_map:
        month = key[key_map["month_idx"]].zfill(2)
        return f"{year}M{month}"
    return year


def _parse_pxweb_json(raw: Dict, key_map: Dict) -> List[Dict]:
    """Extract period/value pairs from PxWeb JSON response."""
    results = []
    for row in raw.get("data", []):
        val_str = row["values"][0] if row.get("values") else None
        if val_str is None or val_str in ("..", "...", "", "None"):
            continue
        try:
            value = float(val_str)
        except (ValueError, TypeError):
            continue
        period = _build_period(row["key"], key_map)
        results.append({"period": period, "value": value})
    results.sort(key=lambda x: x["period"], reverse=True)
    return results


def _resolve_dynamic_periods(table_path: str, dim_code: str, last_n: int) -> Optional[List[str]]:
    """Fetch table metadata and return the last N values for a given dimension."""
    url = f"{BASE_URL}/{table_path}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        meta = resp.json()
        for v in meta.get("variables", []):
            if v["code"] == dim_code:
                return v["values"][-last_n:]
    except Exception:
        pass
    return None


def _build_query(cfg: Dict) -> Optional[List[Dict]]:
    """Build the PxWeb query, resolving dynamic time dimensions if needed."""
    if "query" in cfg:
        return cfg["query"]
    if "query_template" in cfg and "dynamic_time_dim" in cfg:
        dtd = cfg["dynamic_time_dim"]
        periods = _resolve_dynamic_periods(cfg["table_path"], dtd["code"], dtd["last_n"])
        if not periods:
            return None
        query = list(cfg["query_template"])
        query.append({"code": dtd["code"], "selection": {"filter": "item", "values": periods}})
        return query
    return None


def _api_request(table_path: str, query: List[Dict]) -> Dict:
    url = f"{BASE_URL}/{table_path}"
    payload = {"query": query, "response": {"format": "json"}}
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
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


def fetch_data(indicator: str) -> Dict:
    """Fetch a specific indicator from Statistics Estonia."""
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

    query = _build_query(cfg)
    if query is None:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Failed to resolve query parameters"}

    result = _api_request(cfg["table_path"], query)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_pxweb_json(result["data"], cfg["key_map"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

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
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['table_path']}",
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
        "source": "Statistics Estonia (PxWeb)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_trade_balance() -> Dict:
    """Compute trade balance from exports minus imports."""
    exports = fetch_data("EXPORTS")
    time.sleep(REQUEST_DELAY)
    imports = fetch_data("IMPORTS")

    if not exports.get("success") or not imports.get("success"):
        return {"success": False, "error": "Failed to fetch trade data"}

    exp_map = {dp["period"]: dp["value"] for dp in exports["data_points"]}
    imp_map = {dp["period"]: dp["value"] for dp in imports["data_points"]}

    balance = []
    for period in sorted(set(exp_map) & set(imp_map), reverse=True):
        balance.append({
            "period": period,
            "exports": exp_map[period],
            "imports": imp_map[period],
            "balance": round(exp_map[period] - imp_map[period], 1),
        })

    return {
        "success": bool(balance),
        "name": "Trade Balance (EUR mn)",
        "data_points": balance[:20],
        "latest": balance[0] if balance else None,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Statistics Estonia (PxWeb) Module

Usage:
  python statistics_estonia.py                    # Latest values for all indicators
  python statistics_estonia.py <INDICATOR>         # Fetch specific indicator
  python statistics_estonia.py list                # List available indicators
  python statistics_estonia.py trade-balance       # Compute trade balance

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<35s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: PxWeb REST API (JSON)
Coverage: Estonia
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "trade-balance":
            print(json.dumps(get_trade_balance(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
