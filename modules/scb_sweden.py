#!/usr/bin/env python3
"""
SCB Sweden (Statistics Sweden) PxWeb Module

Swedish macroeconomic data: GDP growth, CPI/CPIF inflation, unemployment,
housing prices, industrial production, foreign trade, and government debt.

Data Source: https://api.scb.se/OV0104/v1/doris/en/ssd/
Protocol: PxWeb REST API (POST with JSON query)
Auth: None (open access)
Formats: JSON (PxWeb tabular)
Refresh: Monthly (most series), Quarterly (GDP, housing)
Coverage: Sweden

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

BASE_URL = "https://api.scb.se/OV0104/v1/doris/en/ssd"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "scb_sweden"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- GDP (Quarterly, Seasonally Adjusted) ---
    "GDP_QOQ": {
        "table_path": "NR/NR0103/NR0103B/NR0103ENS2010T10SKv",
        "query_filters": [
            {"code": "Anvandningstyp", "selection": {"filter": "item", "values": ["BNPM"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["NR0103CF"]}},
        ],
        "name": "GDP Growth QoQ (%, SA)",
        "description": "GDP expenditure approach, seasonally adjusted volume change vs previous quarter",
        "frequency": "quarterly",
        "unit": "%",
        "last_n": 40,
    },
    "GDP_CURRENT_PRICES": {
        "table_path": "NR/NR0103/NR0103B/NR0103ENS2010T10SKv",
        "query_filters": [
            {"code": "Anvandningstyp", "selection": {"filter": "item", "values": ["BNPM"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["NR0103CG"]}},
        ],
        "name": "GDP at Current Prices (SEK mn, SA)",
        "description": "GDP at market prices, seasonally adjusted current prices",
        "frequency": "quarterly",
        "unit": "SEK million",
        "last_n": 40,
    },
    # --- Monthly GDP Indicator ---
    "GDP_INDICATOR_MOM": {
        "table_path": "NR/NR9999/NR9999A/NR9999ENS2010BNPIndN",
        "query_filters": [
            {"code": "BNPMarknadspris", "selection": {"filter": "item", "values": ["BNPM"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000000X2"]}},
        ],
        "name": "GDP Indicator MoM (%, SA)",
        "description": "Monthly GDP indicator, seasonally adjusted volume change vs previous month",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "GDP_INDICATOR_YOY": {
        "table_path": "NR/NR9999/NR9999A/NR9999ENS2010BNPIndN",
        "query_filters": [
            {"code": "BNPMarknadspris", "selection": {"filter": "item", "values": ["BNPM"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["0000027O"]}},
        ],
        "name": "GDP Indicator YoY (%)",
        "description": "Monthly GDP indicator, working-day adjusted volume change vs same month previous year",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Consumer Prices ---
    "CPI_INDEX": {
        "table_path": "PR/PR0101/PR0101A/KPI2020M",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["00000808"]}},
        ],
        "name": "CPI Index (2020=100)",
        "description": "Consumer Price Index, fixed index numbers, base year 2020",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
        "last_n": 60,
    },
    "CPI_ANNUAL_CHANGE": {
        "table_path": "PR/PR0101/PR0101A/KPI2020M",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["00000804"]}},
        ],
        "name": "CPI Annual Change (%)",
        "description": "Consumer Price Index, annual percentage change (inflation rate)",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "CPIF_INDEX": {
        "table_path": "PR/PR0101/PR0101G/KPIF2020",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000007ZN"]}},
        ],
        "name": "CPIF Index (2020=100)",
        "description": "CPI with fixed interest rate (Riksbank target measure), base year 2020",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
        "last_n": 60,
    },
    "CPIF_ANNUAL_CHANGE": {
        "table_path": "PR/PR0101/PR0101G/KPIF2020",
        "query_filters": [
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000007ZM"]}},
        ],
        "name": "CPIF Annual Change (%)",
        "description": "CPIF annual percentage change (Riksbank inflation target measure)",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Labour Market ---
    "UNEMPLOYMENT_RATE": {
        "table_path": "AM/AM0401/AM0401A/AKURLBefM",
        "query_filters": [
            {"code": "Arbetskraftstillh", "selection": {"filter": "item", "values": ["AL\u00d6SP"]}},
            {"code": "TypData", "selection": {"filter": "item", "values": ["SR_DATA"]}},
            {"code": "Kon", "selection": {"filter": "item", "values": ["1+2"]}},
            {"code": "Alder", "selection": {"filter": "item", "values": ["tot15-74"]}},
        ],
        "name": "Unemployment Rate (%, SA)",
        "description": "Unemployment rate, ages 15-74, total, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "EMPLOYMENT_RATE": {
        "table_path": "AM/AM0401/AM0401A/AKURLBefM",
        "query_filters": [
            {"code": "Arbetskraftstillh", "selection": {"filter": "item", "values": ["SYSP"]}},
            {"code": "TypData", "selection": {"filter": "item", "values": ["SR_DATA"]}},
            {"code": "Kon", "selection": {"filter": "item", "values": ["1+2"]}},
            {"code": "Alder", "selection": {"filter": "item", "values": ["tot15-74"]}},
        ],
        "name": "Employment Rate (%, SA)",
        "description": "Employment rate, ages 15-74, total, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Housing ---
    "HOUSING_PRICE_INDEX": {
        "table_path": "BO/BO0501/BO0501A/FastpiPSRegKv",
        "query_filters": [
            {"code": "Region", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["BO0501K2"]}},
        ],
        "name": "Housing Price Index (1981=100)",
        "description": "Real estate price index for one/two-dwelling buildings, Sweden total",
        "frequency": "quarterly",
        "unit": "Index (1981=100)",
        "last_n": 40,
    },
    # --- Industrial Production ---
    "PRODUCTION_INDEX_TOTAL": {
        "table_path": "NV/NV0006/NV0006A/PVI2015FastM07",
        "query_filters": [
            {"code": "SNI2007", "selection": {"filter": "item", "values": ["B-S(ex.K,O)"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000001U2"]}},
        ],
        "name": "Production Value Index YoY (%, total)",
        "description": "PVI annual development, calendar adjusted, total private sector excl. financial",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "PRODUCTION_INDEX_MANUFACTURING": {
        "table_path": "NV/NV0006/NV0006A/PVI2015FastM07",
        "query_filters": [
            {"code": "SNI2007", "selection": {"filter": "item", "values": ["C"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["000001U2"]}},
        ],
        "name": "Production Value Index YoY (%, manufacturing)",
        "description": "PVI annual development, calendar adjusted, manufacturing industry (NACE C)",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Foreign Trade ---
    "EXPORTS": {
        "table_path": "HA/HA0201/HA0201A/ImportExportSnabbM",
        "query_filters": [
            {"code": "ImportExport", "selection": {"filter": "item", "values": ["ETOT"]}},
        ],
        "name": "Total Exports (SEK mn)",
        "description": "Total exports of goods, monthly",
        "frequency": "monthly",
        "unit": "SEK million",
        "last_n": 60,
    },
    "IMPORTS": {
        "table_path": "HA/HA0201/HA0201A/ImportExportSnabbM",
        "query_filters": [
            {"code": "ImportExport", "selection": {"filter": "item", "values": ["ITOT"]}},
        ],
        "name": "Total Imports (SEK mn)",
        "description": "Total imports of goods, monthly",
        "frequency": "monthly",
        "unit": "SEK million",
        "last_n": 60,
    },
    "TRADE_BALANCE": {
        "table_path": "HA/HA0201/HA0201A/ImportExportSnabbM",
        "query_filters": [
            {"code": "ImportExport", "selection": {"filter": "item", "values": ["HANDELSB"]}},
        ],
        "name": "Trade Balance — Goods (SEK mn)",
        "description": "Net trade of goods (exports minus imports), monthly",
        "frequency": "monthly",
        "unit": "SEK million",
        "last_n": 60,
    },
    # --- Government Debt ---
    "GOVT_DEBT": {
        "table_path": "OE/OE0202/OE0202A/StatsskuldNy",
        "query_filters": [
            {"code": "Marknad", "selection": {"filter": "item", "values": ["SSTot"]}},
        ],
        "name": "Central Government Debt (SEK mn)",
        "description": "Swedish central government gross debt, total",
        "frequency": "monthly",
        "unit": "SEK million",
        "last_n": 60,
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


def _parse_pxweb_json(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from PxWeb JSON response."""
    try:
        data_rows = raw.get("data", [])
        if not data_rows:
            return []

        columns = raw.get("columns", [])
        time_col_idx = next((i for i, c in enumerate(columns) if c.get("type") == "t"), None)

        results = []
        for row in data_rows:
            keys = row.get("key", [])
            values = row.get("values", [])
            if not values or values[0] in ("..", "", None):
                continue
            try:
                val = float(values[0])
            except (ValueError, TypeError):
                continue

            period = keys[time_col_idx] if time_col_idx is not None and time_col_idx < len(keys) else keys[-1]
            results.append({"time_period": period, "value": val})

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(table_path: str, query_filters: List[Dict], last_n: int = 60) -> Dict:
    """POST a PxWeb query and return parsed response."""
    url = f"{BASE_URL}/{table_path}"
    body = {
        "query": query_filters + [
            {"code": "Tid", "selection": {"filter": "top", "values": [str(last_n)]}}
        ],
        "response": {"format": "json"},
    }
    try:
        resp = requests.post(url, json=body, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body_text = ""
        try:
            body_text = e.response.text[:200]
        except Exception:
            pass
        if status == 404:
            return {"success": False, "error": f"Table not found (HTTP 404)"}
        if status == 429:
            return {"success": False, "error": "Rate limited (HTTP 429), retry later"}
        return {"success": False, "error": f"HTTP {status}: {body_text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def navigate_table(path: str = "") -> Dict:
    """Navigate the PxWeb table hierarchy. Pass empty string for root."""
    url = f"{BASE_URL}/{path}" if path else f"{BASE_URL}/"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "items": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, last_n: int = None) -> Dict:
    """Fetch a specific indicator with optional observation count."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    obs_count = last_n or cfg["last_n"]
    cache_params = {"indicator": indicator, "last_n": obs_count}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["table_path"], cfg["query_filters"], last_n=obs_count)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_pxweb_json(result["data"])
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
            "table_path": v["table_path"],
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
        "source": "Statistics Sweden (SCB) PxWeb API",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
SCB Sweden (Statistics Sweden) PxWeb Module

Usage:
  python scb_sweden.py                      # Latest values for all indicators
  python scb_sweden.py <INDICATOR>           # Fetch specific indicator
  python scb_sweden.py list                  # List available indicators
  python scb_sweden.py navigate [PATH]       # Browse PxWeb table hierarchy

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<35s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: PxWeb REST API (POST with JSON query)
Coverage: Sweden
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "navigate":
            path = sys.argv[2] if len(sys.argv) > 2 else ""
            print(json.dumps(navigate_table(path), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
