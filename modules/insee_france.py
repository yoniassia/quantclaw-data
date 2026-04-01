#!/usr/bin/env python3
"""
INSEE France SDMX Module — Phase 1

French national statistics: GDP growth, CPI/HICP inflation, unemployment rate,
industrial production index, consumer confidence, household consumption,
and foreign trade (exports/imports).

Data Source: https://bdm.insee.fr/series/sdmx
Protocol: SDMX 2.1 REST (SDMX-ML / XML)
Auth: None (open access, 30 req/min rate limit)
Refresh: Monthly (CPI, IPI, confidence), Quarterly (GDP, unemployment, national accounts)
Coverage: France

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://bdm.insee.fr/series/sdmx"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "insee_france"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- GDP (quarterly, % change q/q) ---
    "GDP_GROWTH": {
        "idbank": "011794844",
        "name": "GDP Growth Rate (% q/q, SA-WDA)",
        "description": "Quarterly accounts (base 2020) — evolution of total GDP, volumes chained at previous year prices, seasonally and working-day adjusted",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Consumer Price Index (monthly) ---
    "CPI_INDEX": {
        "idbank": "011814630",
        "name": "CPI — All Items (base 2025=100)",
        "description": "Consumer price index, base 2025, all households, France, all items",
        "frequency": "monthly",
        "unit": "index",
    },
    "CPI_YOY": {
        "idbank": "011814632",
        "name": "CPI — Year-on-Year Change (%)",
        "description": "Consumer price index, base 2025, year-on-year change, all households, France, all items",
        "frequency": "monthly",
        "unit": "%",
    },
    "HICP_INDEX": {
        "idbank": "011812231",
        "name": "HICP — All Items (base 2025=100)",
        "description": "Harmonised index of consumer prices, base 2025, all households, France, COICOP 00 total",
        "frequency": "monthly",
        "unit": "index",
    },
    # --- Unemployment (quarterly) ---
    "UNEMPLOYMENT_RATE": {
        "idbank": "001688527",
        "name": "ILO Unemployment Rate (%)",
        "description": "ILO unemployment rate, total, France excluding Mayotte, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Industrial Production (monthly) ---
    "IPI_MANUFACTURING": {
        "idbank": "010768261",
        "name": "Industrial Production Index (base 2021=100, SA-WDA)",
        "description": "SA-WDA industrial production index, base 2021, manufacturing, mining/quarrying and other industrial activities (NAF A10 item BE)",
        "frequency": "monthly",
        "unit": "index",
    },
    # --- Consumer Confidence (monthly) ---
    "CONSUMER_CONFIDENCE": {
        "idbank": "001587668",
        "name": "Consumer Confidence Indicator (SA)",
        "description": "Monthly consumer confidence survey — synthetic indicator of household confidence (first factor of opinion balances), long-term average = 100",
        "frequency": "monthly",
        "unit": "index",
    },
    # --- National Accounts Components (quarterly, EUR mn chained volumes SA-WDA) ---
    "HOUSEHOLD_CONSUMPTION": {
        "idbank": "011794864",
        "name": "Household Consumption (EUR mn, SA-WDA)",
        "description": "Consumption expenditures of households, total, volumes chained at previous year prices, seasonally and working-day adjusted",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "EXPORTS": {
        "idbank": "011794876",
        "name": "Exports — Total (EUR mn, SA-WDA)",
        "description": "Exports, total, values at current prices, seasonally and working-day adjusted",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "IMPORTS": {
        "idbank": "011794878",
        "name": "Imports — Total (EUR mn, SA-WDA)",
        "description": "Imports, total, values at current prices, seasonally and working-day adjusted",
        "frequency": "quarterly",
        "unit": "EUR mn",
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


def _parse_sdmx_xml(raw_xml: str) -> List[Dict]:
    """Extract time-period/value pairs from INSEE SDMX-ML StructureSpecificData."""
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError:
        return []

    results = []
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "Series":
            series_meta = {
                "title_en": el.get("TITLE_EN", ""),
                "title_fr": el.get("TITLE_FR", ""),
                "unit_measure": el.get("UNIT_MEASURE", ""),
                "last_update": el.get("LAST_UPDATE", ""),
            }
        elif tag == "Obs":
            tp = el.get("TIME_PERIOD")
            val = el.get("OBS_VALUE")
            if tp is not None and val is not None:
                try:
                    results.append({
                        "time_period": tp,
                        "value": float(val),
                        "status": el.get("OBS_STATUS", ""),
                        "quality": el.get("OBS_QUAL", ""),
                        **series_meta,
                    })
                except (ValueError, TypeError):
                    pass

    results.sort(key=lambda x: x["time_period"], reverse=True)
    return results


def _api_request(idbank: str, last_n: int = 52, start_period: str = None) -> Dict:
    url = f"{BASE_URL}/data/SERIES_BDM/{idbank}"
    params = {"lastNObservations": last_n}
    if start_period:
        params["startPeriod"] = start_period
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 404:
            return {"success": False, "error": "Series not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    last_n = 60 if cfg["frequency"] == "monthly" else 40

    result = _api_request(cfg["idbank"], last_n=last_n, start_period=start_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_sdmx_xml(result["data"])
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
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/data/SERIES_BDM/{cfg['idbank']}",
        "last_update": observations[0].get("last_update", ""),
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
            "idbank": v["idbank"],
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
        "source": "INSEE France BDM (SDMX)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_trade_balance() -> Dict:
    """Compute France's trade balance from exports minus imports."""
    exports = fetch_data("EXPORTS")
    time.sleep(REQUEST_DELAY)
    imports = fetch_data("IMPORTS")

    if not exports.get("success") or not imports.get("success"):
        return {"success": False, "error": "Failed to fetch exports or imports"}

    exp_pts = {d["period"]: d["value"] for d in exports["data_points"]}
    imp_pts = {d["period"]: d["value"] for d in imports["data_points"]}
    common = sorted(set(exp_pts) & set(imp_pts), reverse=True)

    balance = [
        {"period": p, "exports": exp_pts[p], "imports": imp_pts[p], "balance": round(exp_pts[p] - imp_pts[p], 2)}
        for p in common[:20]
    ]

    return {
        "success": bool(balance),
        "name": "France Trade Balance (EUR mn)",
        "latest_period": balance[0]["period"] if balance else None,
        "latest_balance": balance[0]["balance"] if balance else None,
        "data_points": balance,
        "count": len(balance),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
INSEE France SDMX Module (Phase 1)

Usage:
  python insee_france.py                           # Latest values for all indicators
  python insee_france.py <INDICATOR>                # Fetch specific indicator
  python insee_france.py list                       # List available indicators
  python insee_france.py trade-balance              # France trade balance (exports - imports)

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (SDMX-ML / XML)
Coverage: France
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
