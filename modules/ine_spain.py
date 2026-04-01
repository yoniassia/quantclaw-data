#!/usr/bin/env python3
"""
INE Spain Statistics Module — Instituto Nacional de Estadística

Spain's national statistics: GDP (quarterly national accounts), CPI inflation,
labour force survey (EPA), industrial production, housing price index,
and foreign trade (exports/imports).

Data Source: https://servicios.ine.es/wstempus/js/EN/
Protocol: REST JSON (Tempus3 API)
Auth: None (open access)
Refresh: Quarterly (GDP, EPA, HPI, Trade), Monthly (CPI, IPI)
Coverage: Spain

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

BASE_URL = "https://servicios.ine.es/wstempus/js/EN"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ine_spain"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

PERIOD_MAP = {
    1: "M01", 2: "M02", 3: "M03", 4: "M04", 5: "M05", 6: "M06",
    7: "M07", 8: "M08", 9: "M09", 10: "M10", 11: "M11", 12: "M12",
    19: "Q1", 20: "Q2", 21: "Q3", 22: "Q4",
    28: "Annual",
}

INDICATORS = {
    # --- GDP (Quarterly National Accounts, Operation 237) ---
    "GDP_CURRENT": {
        "series": "CNTR6548",
        "name": "GDP at Market Prices — Current Prices (EUR mn)",
        "description": "Gross domestic product at market prices, seasonally unadjusted, current prices",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GDP_QOQ": {
        "series": "CNTR6653",
        "name": "GDP QoQ Growth Rate — SA Volume (%)",
        "description": "GDP seasonally adjusted quarter-on-quarter growth, chain-linked volume measures",
        "frequency": "quarterly",
        "unit": "%",
    },
    "GDP_YOY": {
        "series": "CNTR6654",
        "name": "GDP YoY Growth Rate — SA Volume (%)",
        "description": "GDP seasonally adjusted year-on-year growth, chain-linked volume measures",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- CPI / Inflation (Operation 25) ---
    "CPI_INDEX": {
        "series": "IPC290751",
        "name": "CPI Overall Index (Base 2024=100)",
        "description": "Consumer Price Index, national overall index",
        "frequency": "monthly",
        "unit": "Index",
    },
    "CPI_MOM": {
        "series": "IPC290752",
        "name": "CPI Monthly Variation Rate (%)",
        "description": "Consumer Price Index month-on-month change",
        "frequency": "monthly",
        "unit": "%",
    },
    "CPI_YOY": {
        "series": "IPC290750",
        "name": "CPI Annual Inflation Rate (%)",
        "description": "Consumer Price Index year-on-year variation (headline inflation)",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Labour Force Survey / EPA (Operation 293) ---
    "UNEMPLOYMENT_RATE": {
        "series": "EPA452434",
        "name": "Unemployment Rate — All Ages (%)",
        "description": "EPA unemployment rate, both genders, national total, all ages",
        "frequency": "quarterly",
        "unit": "%",
    },
    "YOUTH_UNEMPLOYMENT": {
        "series": "EPA452436",
        "name": "Youth Unemployment Rate — Under 25 (%)",
        "description": "EPA unemployment rate, both genders, under 25 years old",
        "frequency": "quarterly",
        "unit": "%",
    },
    "ACTIVE_POPULATION": {
        "series": "EPA387794",
        "name": "Active Population — 16+ (thousands)",
        "description": "Economically active population, both genders, 16 and over",
        "frequency": "quarterly",
        "unit": "thousands",
    },
    "EMPLOYED_PERSONS": {
        "series": "EPA387796",
        "name": "Employed Persons — 16+ (thousands)",
        "description": "Total employed persons, both genders, 16 and over",
        "frequency": "quarterly",
        "unit": "thousands",
    },
    # --- Industrial Production Index (Operation 26) ---
    "IPI_TOTAL": {
        "series": "IPI15360",
        "name": "Industrial Production Index — SA Total (Base 2021=100)",
        "description": "Industrial Production Index, seasonally and calendar adjusted, total industry",
        "frequency": "monthly",
        "unit": "Index",
    },
    "IPI_MOM": {
        "series": "IPI15381",
        "name": "IPI Monthly Variation Rate — SA (%)",
        "description": "Industrial Production Index month-on-month change, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Housing Price Index (Operation 15) ---
    "HPI_INDEX": {
        "series": "IPV769",
        "name": "Housing Price Index — General (Base 2015=100)",
        "description": "Housing Price Index, national total, general (new + second-hand)",
        "frequency": "quarterly",
        "unit": "Index",
    },
    "HPI_YOY": {
        "series": "IPV948",
        "name": "Housing Price Index — YoY Change (%)",
        "description": "Housing Price Index annual variation, general",
        "frequency": "quarterly",
        "unit": "%",
    },
    "HPI_QOQ": {
        "series": "IPV949",
        "name": "Housing Price Index — QoQ Change (%)",
        "description": "Housing Price Index quarterly variation, general",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Foreign Trade (from National Accounts Demand, SA chain-linked) ---
    "EXPORTS_VOLUME": {
        "series": "CNTR7265",
        "name": "Exports of Goods & Services — SA Volume Index",
        "description": "Exports of goods and services, seasonally adjusted, chain-linked volume measures",
        "frequency": "quarterly",
        "unit": "Index",
    },
    "EXPORTS_YOY": {
        "series": "CNTR7267",
        "name": "Exports YoY Growth — SA Volume (%)",
        "description": "Exports of goods and services, seasonally adjusted, year-on-year volume growth",
        "frequency": "quarterly",
        "unit": "%",
    },
    "IMPORTS_VOLUME": {
        "series": "CNTR7285",
        "name": "Imports of Goods & Services — SA Volume Index",
        "description": "Imports of goods and services, seasonally adjusted, chain-linked volume measures",
        "frequency": "quarterly",
        "unit": "Index",
    },
    "IMPORTS_YOY": {
        "series": "CNTR7287",
        "name": "Imports YoY Growth — SA Volume (%)",
        "description": "Imports of goods and services, seasonally adjusted, year-on-year volume growth",
        "frequency": "quarterly",
        "unit": "%",
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


def _format_period(anyo: int, fk_periodo: int) -> str:
    """Convert INE year + period code to readable period string."""
    label = PERIOD_MAP.get(fk_periodo, f"P{fk_periodo}")
    if label.startswith("M"):
        return f"{anyo}-{label[1:]}"
    if label.startswith("Q"):
        return f"{anyo}-{label}"
    if label == "Annual":
        return str(anyo)
    return f"{anyo}-{label}"


def _parse_ine_series(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from INE Tempus3 series response."""
    try:
        data_points = raw.get("Data", [])
        if not data_points:
            return []

        results = []
        for obs in data_points:
            valor = obs.get("Valor")
            if valor is None or obs.get("Secreto", False):
                continue
            results.append({
                "period": _format_period(obs["Anyo"], obs["FK_Periodo"]),
                "value": float(valor),
                "year": obs["Anyo"],
                "fk_periodo": obs["FK_Periodo"],
                "data_type": obs.get("FK_TipoDato"),
            })

        results.sort(key=lambda x: (x["year"], x["fk_periodo"]), reverse=True)
        return results
    except (KeyError, TypeError, ValueError):
        return []


def _api_request(series_code: str, last_n: int = 40) -> Dict:
    """Fetch data for a single INE series."""
    url = f"{BASE_URL}/DATOS_SERIE/{series_code}"
    params = {"nult": last_n}
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


def discover_operations() -> Dict:
    """List available INE statistical operations."""
    url = f"{BASE_URL}/OPERACIONES_DISPONIBLES"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        ops = resp.json()
        return {
            "success": True,
            "operations": [
                {"id": o["Id"], "code": o.get("Cod_IOE", ""), "name": o["Nombre"]}
                for o in ops if o.get("Nombre")
            ],
            "count": len(ops),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def discover_tables(operation_id: int) -> Dict:
    """List tables for a given INE operation."""
    url = f"{BASE_URL}/TABLAS_OPERACION/{operation_id}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        tables = resp.json()
        return {
            "success": True,
            "operation_id": operation_id,
            "tables": [{"id": t["Id"], "name": t["Nombre"]} for t in tables],
            "count": len(tables),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, last_n: int = 40) -> Dict:
    """Fetch a specific indicator by key."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "last_n": last_n}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["series"], last_n=last_n)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_ine_series(result["data"])
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
        "series_code": cfg["series"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/DATOS_SERIE/{cfg['series']}",
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
            "series_code": v["series"],
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
        "source": "INE Spain (Instituto Nacional de Estadística)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
INE Spain Statistics Module — Instituto Nacional de Estadística

Usage:
  python ine_spain.py                          # Latest values for all indicators
  python ine_spain.py <INDICATOR>              # Fetch specific indicator
  python ine_spain.py list                     # List available indicators
  python ine_spain.py operations               # Discover INE operations
  python ine_spain.py tables <OPERATION_ID>    # List tables for an operation

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST JSON (Tempus3)
Coverage: Spain
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "operations":
            print(json.dumps(discover_operations(), indent=2, default=str))
        elif cmd == "tables" and len(sys.argv) > 2:
            print(json.dumps(discover_tables(int(sys.argv[2])), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
