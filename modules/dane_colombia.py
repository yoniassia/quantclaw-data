#!/usr/bin/env python3
"""
DANE Colombia SDMX Module

Colombian macro indicators from DANE (Departamento Administrativo Nacional
de Estadística): GDP, CPI, unemployment, industrial production, trade balance,
and producer prices via SDMX REST 2.1 API.

Colombia is Latin America's 4th-largest economy, a major oil/coal/coffee exporter,
and an increasingly important emerging-market debt market.

Data Source: https://sdmx.dane.gov.co/gateway/rest
Protocol: SDMX 2.1 REST (SDMX-JSON)
Auth: None (fully open, no key required)
Refresh: Monthly (CPI, unemployment, industrial, trade, PPI), Quarterly (GDP)
Coverage: Colombia

Author: QUANTCLAW DATA Build Agent
Initiative: 0052
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://sdmx.dane.gov.co/gateway/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "dane_colombia"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.5

HEADERS_JSON = {"Accept": "application/vnd.sdmx.data+json;version=1.0.0"}
HEADERS_STRUCTURE = {"Accept": "application/vnd.sdmx.structure+json;version=1.0.0"}

INDICATORS = {
    # --- GDP (quarterly national accounts) ---
    "GDP": {
        "dataflow": "PIB_PRODUCCION",
        "key": "all",
        "name": "GDP — Production Approach (COP bn)",
        "description": "Producto Interno Bruto por enfoque de producción, quarterly",
        "frequency": "quarterly",
        "unit": "COP bn",
        "last_n": 40,
    },
    # --- Consumer Price Index (monthly) ---
    "CPI": {
        "dataflow": "IPC",
        "key": "all",
        "name": "Consumer Price Index (CPI)",
        "description": "Índice de Precios al Consumidor, monthly",
        "frequency": "monthly",
        "unit": "Index",
        "last_n": 60,
    },
    # --- Unemployment Rate (monthly, GEIH household survey) ---
    "UNEMPLOYMENT": {
        "dataflow": "GEIH",
        "key": "all",
        "name": "Unemployment Rate (%)",
        "description": "Tasa de desempleo — Gran Encuesta Integrada de Hogares, monthly",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Industrial Production (monthly, manufacturing survey) ---
    "INDUSTRIAL_PRODUCTION": {
        "dataflow": "EMM",
        "key": "all",
        "name": "Industrial Production — Manufacturing (Index)",
        "description": "Encuesta Mensual Manufacturera — producción industrial, monthly",
        "frequency": "monthly",
        "unit": "Index",
        "last_n": 60,
    },
    # --- Trade Balance (monthly, exports/imports) ---
    "TRADE_BALANCE": {
        "dataflow": "BALANZA_COMERCIAL",
        "key": "all",
        "name": "Trade Balance (USD mn)",
        "description": "Balanza comercial — exportaciones e importaciones, monthly",
        "frequency": "monthly",
        "unit": "USD mn",
        "last_n": 60,
    },
    # --- Producer Price Index (monthly) ---
    "PPI": {
        "dataflow": "IPP",
        "key": "all",
        "name": "Producer Price Index (PPI)",
        "description": "Índice de Precios del Productor, monthly",
        "frequency": "monthly",
        "unit": "Index",
        "last_n": 60,
    },
    # --- Annual Manufacturing Survey ---
    "ANNUAL_MANUFACTURING": {
        "dataflow": "EAM",
        "key": "all",
        "name": "Annual Manufacturing Survey",
        "description": "Encuesta Anual Manufacturera — annual",
        "frequency": "annual",
        "unit": "COP mn",
        "last_n": 20,
    },
}

CLI_ALIASES = {
    "gdp": "GDP",
    "cpi": "CPI",
    "unemployment": "UNEMPLOYMENT",
    "industrial_production": "INDUSTRIAL_PRODUCTION",
    "trade_balance": "TRADE_BALANCE",
    "ppi": "PPI",
    "annual_manufacturing": "ANNUAL_MANUFACTURING",
}


# ---------- caching ----------

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


# ---------- SDMX-JSON parsing ----------

def _parse_sdmx_json(raw: Dict) -> List[Dict]:
    """Extract time-period / value pairs from SDMX-JSON v1.0.0 response.

    Handles both top-level and data-wrapped structures produced by
    various .Stat Suite / NSI implementations.
    """
    try:
        inner = raw.get("data", raw)
        structure = inner.get("structure", inner.get("structures", [None]))
        if isinstance(structure, list):
            structure = structure[0] if structure else {}

        datasets = inner.get("dataSets", [])
        if not datasets or not structure:
            return []

        obs_dims = structure.get("dimensions", {}).get("observation", [])
        if not obs_dims:
            return []
        time_values = obs_dims[0].get("values", [])

        series_dims = structure.get("dimensions", {}).get("series", [])
        series_attrs = structure.get("attributes", {}).get("series", [])

        unit_attr_idx = None
        for i, attr in enumerate(series_attrs):
            if attr.get("id", "").upper() in ("UNIT_MEASURE", "UNIT", "UNIT_MULT", "UNIDAD"):
                unit_attr_idx = i
                break

        results = []
        for series_key, series_data in datasets[0].get("series", {}).items():
            meta = _extract_series_meta(series_key, series_dims)

            if unit_attr_idx is not None:
                attr_val = series_data.get("attributes", [None] * (unit_attr_idx + 1))[unit_attr_idx]
                if isinstance(attr_val, int) and attr_val < len(series_attrs[unit_attr_idx].get("values", [])):
                    meta["unit"] = series_attrs[unit_attr_idx]["values"][attr_val].get("name", "")

            for obs_idx_str, obs_vals in series_data.get("observations", {}).items():
                idx = int(obs_idx_str)
                if idx < len(time_values) and obs_vals and obs_vals[0] is not None:
                    results.append({
                        "time_period": time_values[idx].get("id", time_values[idx].get("name", "")),
                        "value": float(obs_vals[0]),
                        **meta,
                    })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results

    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _extract_series_meta(series_key: str, series_dims: List[Dict]) -> Dict:
    """Build metadata dict from the series dimension indices (colon-separated key)."""
    meta = {}
    if not series_dims:
        return meta
    try:
        indices = [int(x) for x in series_key.split(":")]
        for dim_pos, dim in enumerate(series_dims):
            if dim_pos >= len(indices):
                break
            val_idx = indices[dim_pos]
            values = dim.get("values", [])
            if val_idx < len(values):
                dim_id = dim.get("id", "").upper()
                val_entry = values[val_idx]
                if dim_id in ("INDICATOR", "INDICADOR", "MEASURE", "MEDIDA", "CONCEPTO"):
                    meta["indicator_label"] = val_entry.get("name", val_entry.get("id", ""))
                elif dim_id in ("REF_AREA", "AREA", "DEPARTAMENTO", "GEO"):
                    meta["area"] = val_entry.get("name", val_entry.get("id", ""))
    except (ValueError, IndexError):
        pass
    return meta


# ---------- API request ----------

def _api_request(dataflow: str, key: str = "all", last_n: int = 60,
                 start_period: str = None, end_period: str = None) -> Dict:
    """Fetch data from DANE SDMX REST 2.1 endpoint."""
    if key and key != "all":
        url = f"{BASE_URL}/data/DANE,{dataflow},latest/{key}"
    else:
        url = f"{BASE_URL}/data/DANE,{dataflow},latest"

    params = {"lastNObservations": last_n}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period

    try:
        resp = requests.get(url, headers=HEADERS_JSON, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out (DANE SDMX gateway)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed — sdmx.dane.gov.co may be unreachable"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        if e.response is not None:
            try:
                body = e.response.text[:200]
            except Exception:
                pass
        if status == 404:
            return {"success": False, "error": f"Dataflow '{dataflow}' not found (HTTP 404). {body}".strip()}
        if status == 503:
            return {"success": False, "error": "DANE SDMX gateway temporarily unavailable (503)"}
        return {"success": False, "error": f"HTTP {status}: {body}".strip()}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON response from DANE gateway"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- public API ----------

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range filtering."""
    indicator = _resolve_indicator(indicator)
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    last_n = cfg.get("last_n", 60)
    result = _api_request(
        cfg["dataflow"], cfg["key"], last_n=last_n,
        start_period=start_date, end_period=end_date,
    )
    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_sdmx_json(result["data"])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No observations parsed from SDMX response",
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
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {
                "date": o["time_period"],
                "value": o["value"],
                "indicator": o.get("indicator_label", cfg["name"]),
                "unit": o.get("unit", cfg["unit"]),
                "source": "DANE",
            }
            for o in observations[:30]
        ],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/data/DANE,{cfg['dataflow']},latest",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


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
        "source": "DANE Colombia SDMX",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "dataflow": v["dataflow"],
        }
        for k, v in INDICATORS.items()
    ]


def discover_dataflows(search: str = None) -> Dict:
    """List available DANE SDMX dataflows, optionally filtered by keyword."""
    url = f"{BASE_URL}/dataflow/DANE/all/latest"
    try:
        resp = requests.get(url, headers=HEADERS_STRUCTURE, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        inner = data.get("data", data)
        flows_raw = inner.get("dataflows", inner.get("Dataflow", []))
        results = []
        for f in flows_raw:
            fid = f.get("id", "")
            name = f.get("name", "")
            if isinstance(name, dict):
                name = name.get("en", name.get("es", next(iter(name.values()), "")))
            if search and search.lower() not in name.lower() and search.lower() not in fid.lower():
                continue
            results.append({"id": fid, "name": name, "version": f.get("version", "")})
        return {"success": True, "count": len(results), "dataflows": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- helpers ----------

def _resolve_indicator(raw: str) -> str:
    """Resolve CLI aliases and case-insensitive lookups to canonical indicator key."""
    upper = raw.upper()
    if upper in INDICATORS:
        return upper
    lower = raw.lower()
    if lower in CLI_ALIASES:
        return CLI_ALIASES[lower]
    for alias, canonical in CLI_ALIASES.items():
        if alias.replace("_", "") == lower.replace("_", ""):
            return canonical
    return upper


# ---------- CLI ----------

def _print_help():
    print(f"""
DANE Colombia SDMX Module (Initiative 0052)

Usage:
  python dane_colombia.py                           # Latest values for all key indicators
  python dane_colombia.py gdp                       # GDP quarterly
  python dane_colombia.py cpi                       # CPI inflation monthly
  python dane_colombia.py unemployment              # Unemployment rate
  python dane_colombia.py industrial_production     # Manufacturing output
  python dane_colombia.py trade_balance             # Exports/imports
  python dane_colombia.py ppi                       # Producer Price Index
  python dane_colombia.py list                      # List available indicators
  python dane_colombia.py discover [search]         # Discover DANE SDMX dataflows
  python dane_colombia.py <INDICATOR>               # Fetch any indicator by key

Indicators:""")
    for key, cfg in INDICATORS.items():
        aliases = [a for a, v in CLI_ALIASES.items() if v == key]
        alias_str = f" (alias: {', '.join(aliases)})" if aliases else ""
        print(f"  {key:<28s} {cfg['name']}{alias_str}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON)
Coverage: Colombia
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "discover":
            search_term = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(discover_dataflows(search_term), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
