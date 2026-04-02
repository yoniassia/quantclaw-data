#!/usr/bin/env python3
"""
South Korea KOSIS (Korean Statistical Information Service) Module — Initiative 0055

Comprehensive South Korean economic statistics from KOSIS, the official
statistical portal operated by Statistics Korea (KOSTAT). Covers GDP, CPI,
trade, employment, housing, industrial production, and semiconductors.

Complements bank_of_korea.py (BOK monetary/financial data) with real-economy
statistics from the national statistics office.

Data Source: https://kosis.kr/openapi/
Protocol: REST (JSON)
Auth: API key (free registration at https://kosis.kr/openapi/)
Rate Limits: 1,000 requests/day (free tier)
Refresh: 24h cache (monthly/quarterly releases)
Coverage: South Korea macro-economy

Author: QUANTCLAW DATA Build Agent
Initiative: 0055
"""

import json
import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
API_KEY = os.environ.get("KOSIS_API_KEY", "")
CACHE_DIR = Path(__file__).parent.parent / "cache" / "kosis_korea"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    "GDP": {
        "name": "GDP by Expenditure (Quarterly, Current Prices)",
        "description": "Gross Domestic Product by expenditure approach at current market prices",
        "orgId": "101",
        "tblId": "DT_1B41",
        "itmId": "T10",
        "objL1": "ALL",
        "prdSe": "Q",
        "frequency": "quarterly",
        "unit": "KRW billion",
    },
    "CPI": {
        "name": "Consumer Price Index (Monthly, All Items)",
        "description": "National consumer price index — all items (2020=100)",
        "orgId": "101",
        "tblId": "DT_1J20001",
        "itmId": "T10",
        "objL1": "0",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
    },
    "UNEMPLOYMENT": {
        "name": "Unemployment Rate (Monthly)",
        "description": "Economically active population survey — unemployment rate",
        "orgId": "101",
        "tblId": "DT_1DA7012S",
        "itmId": "T20",
        "objL1": "ALL",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "%",
    },
    "INDUSTRIAL_PRODUCTION": {
        "name": "Index of Industrial Production (Monthly)",
        "description": "Mining and manufacturing production index (2020=100)",
        "orgId": "101",
        "tblId": "DT_1F01013",
        "itmId": "T10",
        "objL1": "ALL",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "Index (2020=100)",
    },
    "EXPORTS": {
        "name": "Exports by Commodity (Monthly)",
        "description": "Total merchandise exports by commodity and country",
        "orgId": "101",
        "tblId": "DT_1B10009",
        "itmId": "T10",
        "objL1": "ALL",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "USD million",
    },
    "HOUSING": {
        "name": "Housing Price Index (Monthly)",
        "description": "Nationwide housing (apartment) price index",
        "orgId": "101",
        "tblId": "DT_1YL20631",
        "itmId": "T10",
        "objL1": "ALL",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "Index",
    },
    "SEMICONDUCTORS": {
        "name": "Semiconductor Production Index (Monthly)",
        "description": "Production index for semiconductors — Korea's key export sector (Samsung, SK Hynix)",
        "orgId": "101",
        "tblId": "DT_2KAA902",
        "itmId": "T10",
        "objL1": "ALL",
        "prdSe": "M",
        "frequency": "monthly",
        "unit": "Index",
    },
}

CLI_ALIASES = {
    "gdp": "GDP",
    "cpi": "CPI",
    "unemployment": "UNEMPLOYMENT",
    "industrial_production": "INDUSTRIAL_PRODUCTION",
    "exports": "EXPORTS",
    "housing": "HOUSING",
    "semiconductors": "SEMICONDUCTORS",
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


def _format_period(prd_de: str, prd_se: str) -> str:
    """Convert KOSIS period codes (YYYYQQ, YYYYMM, YYYY) to readable format."""
    if prd_se == "Q" and len(prd_de) == 5:
        return f"{prd_de[:4]}-Q{prd_de[4]}"
    elif prd_se == "M" and len(prd_de) == 6:
        return f"{prd_de[:4]}-{prd_de[4:]}"
    elif prd_se == "A" and len(prd_de) == 4:
        return prd_de
    return prd_de


def _parse_kosis_response(raw_data: list, prd_se: str) -> List[Dict]:
    """Parse KOSIS JSON array into structured records, filtering out blanks."""
    results = []
    for row in raw_data:
        dt_val = row.get("DT", "")
        if not dt_val or dt_val.strip() in ("", "-"):
            continue
        try:
            value = float(dt_val.replace(",", ""))
        except (ValueError, TypeError):
            continue

        prd_de = row.get("PRD_DE", "")
        results.append({
            "date": _format_period(prd_de, prd_se),
            "raw_period": prd_de,
            "value": value,
            "item_name": row.get("ITM_NM", ""),
            "unit_name": row.get("UNIT_NM", ""),
            "table_name": row.get("TBL_NM", ""),
            "classification": row.get("C1_NM", ""),
        })

    results.sort(key=lambda x: x["raw_period"], reverse=True)
    return results


def _default_date_range(prd_se: str) -> tuple:
    """Sensible default start/end period strings based on frequency."""
    now = datetime.now()
    if prd_se == "Q":
        start = f"{now.year - 5}01"
        q = (now.month - 1) // 3 + 1
        end = f"{now.year}0{q}"
    elif prd_se == "M":
        start = f"{now.year - 3}01"
        end = f"{now.year}{now.month:02d}"
    else:
        start = str(now.year - 10)
        end = str(now.year)
    return start, end


def _api_request(cfg: Dict, start_prd: str = None, end_prd: str = None) -> Dict:
    """Make a request to the KOSIS statisticsParameterData endpoint."""
    if not API_KEY:
        return {
            "success": False,
            "error": "KOSIS_API_KEY not set — register free at https://kosis.kr/openapi/ and add to .env",
        }

    prd_se = cfg["prdSe"]
    if not start_prd or not end_prd:
        start_prd, end_prd = _default_date_range(prd_se)

    params = {
        "method": "getList",
        "apiKey": API_KEY,
        "itmId": cfg["itmId"],
        "objL1": cfg["objL1"],
        "orgId": cfg["orgId"],
        "tblId": cfg["tblId"],
        "prdSe": prd_se,
        "startPrdDe": start_prd,
        "endPrdDe": end_prd,
        "format": "json",
        "jsonVD": "Y",
    }

    if "objL2" in cfg:
        params["objL2"] = cfg["objL2"]

    try:
        resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type and resp.status_code == 200:
            return {"success": False, "error": "KOSIS returned HTML — verify API key and table parameters"}

        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            err_msg = data.get("errMsg") or data.get("err") or data.get("message")
            if err_msg:
                return {"success": False, "error": f"KOSIS API: {err_msg}"}
            if not data:
                return {"success": False, "error": "Empty response from KOSIS"}

        if isinstance(data, list):
            return {"success": True, "data": data}

        if isinstance(data, dict) and any(k in data for k in ("TBL_NM", "PRD_DE", "DT")):
            return {"success": True, "data": [data]}

        return {"success": False, "error": f"Unexpected response type: {type(data).__name__}"}

    except requests.Timeout:
        return {"success": False, "error": "Request timed out (30s)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed — check network connectivity"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 403:
            return {"success": False, "error": "HTTP 403 Forbidden — check KOSIS_API_KEY validity"}
        if status == 429:
            return {"success": False, "error": "HTTP 429 — rate limit exceeded (1,000 req/day)"}
        return {"success": False, "error": f"HTTP {status}"}
    except (json.JSONDecodeError, ValueError):
        return {"success": False, "error": "Failed to parse JSON response"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific KOSIS indicator with optional date range.

    Args:
        indicator: Key (e.g. 'GDP', 'CPI') or CLI alias (e.g. 'gdp', 'cpi')
        start_date: Start period — YYYYMM (monthly), YYYYQ (quarterly), YYYY (annual)
        end_date:   End period — same format as start_date

    Returns:
        Dict with success flag, data points, and metadata.
    """
    resolved = CLI_ALIASES.get(indicator.lower(), indicator.upper())
    if resolved not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[resolved]

    cache_params = {"indicator": resolved, "start": start_date, "end": end_date}
    cp = _cache_path(resolved, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg, start_date, end_date)
    if not result["success"]:
        return {
            "success": False,
            "indicator": resolved,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_kosis_response(result["data"], cfg["prdSe"])
    if not observations:
        return {
            "success": False,
            "indicator": resolved,
            "name": cfg["name"],
            "error": "No valid observations in response (table may require different itmId/objL1)",
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
        "indicator": resolved,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"period": o["date"], "value": o["value"]}
            for o in observations[:30]
        ],
        "total_observations": len(observations),
        "source": f"KOSIS — Statistics Korea (table {cfg['tblId']})",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return metadata for all available indicators."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "table": v["tblId"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one indicator, or all if none specified."""
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
        "source": "KOSIS — Korean Statistical Information Service",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
South Korea KOSIS Module (Initiative 0055)

Usage:
  python kosis_korea.py                              # Latest key indicators (all)
  python kosis_korea.py gdp                          # GDP quarterly
  python kosis_korea.py cpi                          # CPI inflation monthly
  python kosis_korea.py unemployment                 # Unemployment rate
  python kosis_korea.py industrial_production        # Industrial output index
  python kosis_korea.py exports                      # Export data by commodity
  python kosis_korea.py housing                      # Housing price index
  python kosis_korea.py semiconductors               # Semiconductor production index
  python kosis_korea.py list                         # List all indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        aliases = [a for a, v in CLI_ALIASES.items() if v == key]
        alias_str = f" (alias: {aliases[0]})" if aliases else ""
        print(f"  {key:<25s} {cfg['name']}{alias_str}")
    print(f"""
Source: https://kosis.kr/openapi/
Auth:   KOSIS_API_KEY in .env (free registration)
Rate:   1,000 requests/day (free tier)
Cache:  {CACHE_TTL_HOURS}h TTL in {CACHE_DIR}
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
