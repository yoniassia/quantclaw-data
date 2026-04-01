#!/usr/bin/env python3
"""
INE Portugal Statistics Module — Phase 1

Portugal's national statistics institute (Instituto Nacional de Estatística):
GDP growth, CPI inflation, unemployment, tourism, foreign trade,
and housing/construction indicators.

Data Source: https://www.ine.pt/ine/json_indicador/pindica.jsp
Protocol: REST / JSON API
Auth: None (open access)
Refresh: Monthly (CPI, tourism, construction), Quarterly (GDP, labour), Annual (trade)
Coverage: Portugal

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://www.ine.pt/ine/json_indicador/pindica.jsp"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ine_portugal"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- GDP / National Accounts (Quarterly) ---
    "GDP_GROWTH_YOY": {
        "varcd": "0013431",
        "name": "GDP Real Growth YoY (%)",
        "description": "Gross domestic product, chained volume, year-on-year growth rate (Base 2021)",
        "frequency": "quarterly",
        "unit": "%",
        "dim_params": {},
        "geocod_filter": "PT",
        "value_filter": {},
    },
    "GDP_NOMINAL": {
        "varcd": "0013428",
        "name": "GDP Nominal (EUR)",
        "description": "Gross domestic product at current prices (Base 2021)",
        "frequency": "quarterly",
        "unit": "EUR",
        "dim_params": {},
        "geocod_filter": "PT",
        "value_filter": {},
    },
    "GDP_PERCAPITA_GROWTH": {
        "varcd": "0013493",
        "name": "GDP Real Per Capita Growth (%)",
        "description": "Real GDP per capita, annual growth rate (Base 2021)",
        "frequency": "annual",
        "unit": "%",
        "dim_params": {},
        "geocod_filter": None,
        "value_filter": {},
    },
    # --- Prices / Inflation (Monthly) ---
    "CPI_YOY": {
        "varcd": "0014648",
        "name": "CPI Year-on-Year (%)",
        "description": "Consumer price index, year-on-year growth rate (Base 2025)",
        "frequency": "monthly",
        "unit": "%",
        "dim_params": {"Dim2": "PT"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    "CPI_INDEX": {
        "varcd": "0014640",
        "name": "CPI Index (Base 2025)",
        "description": "Consumer price index level (Base 2025 = 100)",
        "frequency": "monthly",
        "unit": "index",
        "dim_params": {"Dim2": "PT"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    "HICP_YOY": {
        "varcd": "0014655",
        "name": "HICP Year-on-Year (%)",
        "description": "Harmonised index of consumer prices, year-on-year growth rate (Base 2025)",
        "frequency": "monthly",
        "unit": "%",
        "dim_params": {},
        "geocod_filter": None,
        "value_filter": {"dim_3": "T"},
    },
    # --- Labour Market (Quarterly) ---
    "UNEMPLOYMENT_RATE": {
        "varcd": "0012136",
        "name": "Unemployment Rate (%)",
        "description": "Unemployment rate (Series 2021), total population by sex",
        "frequency": "quarterly",
        "unit": "%",
        "dim_params": {"Dim2": "PT", "Dim3": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    "EMPLOYED_POPULATION": {
        "varcd": "0012117",
        "name": "Employed Population (thousands)",
        "description": "Employed population (Series 2021), total",
        "frequency": "quarterly",
        "unit": "thousands",
        "dim_params": {"Dim2": "PT", "Dim3": "T", "Dim4": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    "ACTIVITY_RATE": {
        "varcd": "0012135",
        "name": "Activity Rate (%)",
        "description": "Activity rate of working-age population (Series 2021)",
        "frequency": "quarterly",
        "unit": "%",
        "dim_params": {"Dim2": "PT", "Dim3": "T", "Dim4": "T", "Dim5": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    # --- Tourism (Monthly) ---
    "TOURISM_OVERNIGHT_STAYS": {
        "varcd": "0012088",
        "name": "Tourism Overnight Stays (No.)",
        "description": "Overnight stays in tourist accommodation establishments, total",
        "frequency": "monthly",
        "unit": "number",
        "dim_params": {"Dim2": "PT", "Dim3": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    # --- Foreign Trade (Annual) ---
    "EXPORTS": {
        "varcd": "0012349",
        "name": "Exports of Goods (EUR)",
        "description": "Total exports of goods by NUTS region",
        "frequency": "annual",
        "unit": "EUR",
        "dim_params": {"Dim2": "PT"},
        "geocod_filter": "PT",
        "value_filter": {},
    },
    "IMPORTS": {
        "varcd": "0012348",
        "name": "Imports of Goods (EUR)",
        "description": "Total imports of goods by NUTS region",
        "frequency": "annual",
        "unit": "EUR",
        "dim_params": {"Dim2": "PT"},
        "geocod_filter": "PT",
        "value_filter": {},
    },
    "TRADE_COVERAGE": {
        "varcd": "0012350",
        "name": "Trade Coverage Rate (%)",
        "description": "Import-export coverage rate, goods trade",
        "frequency": "annual",
        "unit": "%",
        "dim_params": {"Dim2": "PT"},
        "geocod_filter": "PT",
        "value_filter": {},
    },
    # --- Construction & Housing (Monthly / Annual) ---
    "CONSTRUCTION_COST_INDEX": {
        "varcd": "0011748",
        "name": "New Housing Construction Cost Index (Base 2021)",
        "description": "Cost index for new housing construction, total production factors",
        "frequency": "monthly",
        "unit": "index",
        "dim_params": {"Dim3": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
    },
    "CONSTRUCTION_COST_YOY": {
        "varcd": "0011751",
        "name": "Construction Cost Annual Avg Change (%)",
        "description": "New housing construction cost index, annual average change rate (Base 2021)",
        "frequency": "monthly",
        "unit": "%",
        "dim_params": {"Dim3": "T"},
        "geocod_filter": "PT",
        "value_filter": {"dim_3": "T"},
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


_PERIOD_ORDER_RE = re.compile(
    r"(?:(\d{4})|"                                 # annual: "2025"
    r"(\d)\w{1,2}\s+Quarter\s+(\d{4})|"            # quarterly: "4th Quarter 2025"
    r"(\w+)\s+(\d{4}))"                             # monthly: "February 2026"
)

_MONTH_MAP = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12",
}


def _period_sort_key(period_label: str) -> str:
    """Convert human-readable period label to a sortable string."""
    m = _PERIOD_ORDER_RE.search(period_label)
    if not m:
        return period_label
    if m.group(1):
        return m.group(1)
    if m.group(2) and m.group(3):
        return f"{m.group(3)}Q{m.group(2)}"
    if m.group(4) and m.group(5):
        month_num = _MONTH_MAP.get(m.group(4), "00")
        return f"{m.group(5)}{month_num}"
    return period_label


def _parse_response(raw: dict, cfg: dict) -> List[Dict]:
    """Extract filtered time-series from INE JSON response."""
    dados = raw.get("Dados", {})
    if not dados:
        return []

    geocod_filter = cfg.get("geocod_filter")
    value_filter = cfg.get("value_filter", {})

    results = []
    for period_label, entries in dados.items():
        for entry in entries:
            if geocod_filter and entry.get("geocod") != geocod_filter:
                continue
            if any(entry.get(k) != v for k, v in value_filter.items()):
                continue
            valor = entry.get("valor")
            if valor is None:
                continue
            try:
                value = float(valor)
            except (ValueError, TypeError):
                continue
            results.append({
                "period": period_label,
                "value": value,
                "geocod": entry.get("geocod", ""),
                "geodsg": entry.get("geodsg", ""),
            })

    results.sort(key=lambda x: _period_sort_key(x["period"]), reverse=True)
    return results


def _build_period_params(frequency: str, n_recent: int = 24, lag_months: int = 2) -> Optional[str]:
    """Build Dim1 param with recent period codes, lagged to avoid future periods."""
    now = datetime.now()
    year, month = now.year, now.month
    # Lag start to avoid requesting periods without data yet
    for _ in range(lag_months):
        month -= 1
        if month < 1:
            month = 12
            year -= 1

    codes = []
    if frequency == "monthly":
        y, m = year, month
        for _ in range(n_recent):
            codes.append(f"S3A{y}{m:02d}")
            m -= 1
            if m < 1:
                m = 12
                y -= 1
    elif frequency == "quarterly":
        q = (month - 1) // 3 + 1
        y = year
        for _ in range(n_recent):
            codes.append(f"S5A{y}{q}")
            q -= 1
            if q < 1:
                q = 4
                y -= 1
    elif frequency == "annual":
        for i in range(n_recent):
            codes.append(f"S7A{year - i}")
    else:
        return None
    seen = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return ",".join(seen)


def _api_request(varcd: str, dim_params: dict, frequency: str) -> Dict:
    """Fetch data from INE JSON API with multi-strategy fallback.

    Strategy order:
    1. Recent period codes + dim filters (fast, precise)
    2. Recent period codes without dim filters (broader, filter in Python)
    3. Dim1=T (all periods, may be slow for large datasets)
    """
    base_params = {"op": "2", "varcd": varcd, "lang": "EN"}

    def _try_fetch(params: dict) -> Optional[Dict]:
        try:
            resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                data = data[0] if data else {}
            if data.get("Dados"):
                return data
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError):
            pass
        except Exception:
            pass
        return None

    period_codes = _build_period_params(frequency)

    # Strategy 1: recent periods + dim filters
    if period_codes and dim_params:
        params = {**base_params, "Dim1": period_codes, **dim_params}
        result = _try_fetch(params)
        if result:
            return {"success": True, "data": result}

    # Strategy 2: recent periods, no dim filters (Python-side filtering)
    if period_codes:
        params = {**base_params, "Dim1": period_codes}
        result = _try_fetch(params)
        if result:
            return {"success": True, "data": result}

    # Strategy 3: all periods + dim filters
    params = {**base_params, "Dim1": "T", **dim_params}
    result = _try_fetch(params)
    if result:
        return {"success": True, "data": result}

    # Strategy 4: all periods, no dim filters
    params = {**base_params, "Dim1": "T"}
    result = _try_fetch(params)
    if result:
        return {"success": True, "data": result}

    return {"success": False, "error": "All fetch strategies failed (timeout or no data)"}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
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

    result = _api_request(cfg["varcd"], cfg["dim_params"], cfg["frequency"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_response(result["data"], cfg)
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations after filtering"}

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
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"INE Portugal (varcd={cfg['varcd']})",
        "api_description": result["data"].get("IndicadorDsg", ""),
        "last_updated": result["data"].get("DataUltimoAtualizacao", ""),
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
            "varcd": v["varcd"],
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
        "source": "INE Portugal Statistics",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
INE Portugal Statistics Module (Phase 1)

Usage:
  python ine_portugal.py                   # Latest values for all indicators
  python ine_portugal.py <INDICATOR>        # Fetch specific indicator
  python ine_portugal.py list               # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST / JSON API (open access)
Coverage: Portugal
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
