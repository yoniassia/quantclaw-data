#!/usr/bin/env python3
"""
Destatis GENESIS-Online Germany Module

German federal statistics office (Statistisches Bundesamt): GDP, CPI/HICP,
labour market, foreign trade, industrial production, producer prices,
and construction activity.

Data Source: https://www-genesis.destatis.de/genesisWS/rest/2020/
Protocol: REST (POST with header auth)
Auth: Free registration required (DESTATIS_USER / DESTATIS_PASSWORD in .env)
Formats: JSON, flat-file CSV (ffcsv)
Refresh: Monthly (most series), Quarterly (GDP)
Coverage: Germany

Author: QUANTCLAW DATA Build Agent
Initiative: 0025
"""

import json
import os
import re
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://www-genesis.destatis.de/genesisWS/rest/2020"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "destatis_germany"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 1.0

INDICATORS = {
    # --- GDP (National Accounts) ---
    "GDP_ANNUAL": {
        "table": "81000-0001",
        "name": "GDP — Gross Domestic Product (Annual)",
        "description": "Gross value added and GDP, nominal and price-adjusted, Germany, years",
        "frequency": "annual",
        "unit": "EUR bn",
        "category": "gdp",
    },
    "GDP_QUARTERLY": {
        "table": "81000-0002",
        "name": "GDP — Gross Domestic Product (Quarterly)",
        "description": "Gross value added and GDP, nominal and price-adjusted, Germany, quarters",
        "frequency": "quarterly",
        "unit": "EUR bn",
        "category": "gdp",
    },
    # --- Consumer Prices ---
    "CPI_MONTHLY": {
        "table": "61111-0002",
        "name": "Consumer Price Index (Monthly)",
        "description": "Verbraucherpreisindex, Germany, months (2020=100)",
        "frequency": "monthly",
        "unit": "Index 2020=100",
        "category": "cpi",
    },
    "CPI_ANNUAL": {
        "table": "61111-0001",
        "name": "Consumer Price Index (Annual)",
        "description": "Verbraucherpreisindex, Germany, years (2020=100)",
        "frequency": "annual",
        "unit": "Index 2020=100",
        "category": "cpi",
    },
    "HICP_MONTHLY": {
        "table": "61121-0002",
        "name": "Harmonised Index of Consumer Prices (Monthly)",
        "description": "HICP for Germany, months (2015=100)",
        "frequency": "monthly",
        "unit": "Index 2015=100",
        "category": "cpi",
    },
    "HICP_ANNUAL": {
        "table": "61121-0001",
        "name": "Harmonised Index of Consumer Prices (Annual)",
        "description": "HICP for Germany, years (2015=100)",
        "frequency": "annual",
        "unit": "Index 2015=100",
        "category": "cpi",
    },
    # --- Labour Market ---
    "EMPLOYMENT": {
        "table": "12211-0001",
        "name": "Employment & Unemployment (Annual)",
        "description": "Population, employed, unemployed, economically active from main-residence households, years",
        "frequency": "annual",
        "unit": "1000 persons",
        "category": "labour",
    },
    # --- Foreign Trade ---
    "TRADE_MONTHLY": {
        "table": "51000-0002",
        "name": "Foreign Trade — Exports & Imports (Monthly)",
        "description": "Exports and imports (foreign trade), Germany, months",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "trade",
    },
    "TRADE_ANNUAL": {
        "table": "51000-0001",
        "name": "Foreign Trade — Exports & Imports (Annual)",
        "description": "Exports and imports (foreign trade), Germany, years",
        "frequency": "annual",
        "unit": "EUR mn",
        "category": "trade",
    },
    # --- Industrial Production ---
    "INDUSTRIAL_PRODUCTION": {
        "table": "42153-0001",
        "name": "Industrial Production Index (Monthly)",
        "description": "Production index for manufacturing, original and adjusted data, months",
        "frequency": "monthly",
        "unit": "Index 2021=100",
        "category": "production",
    },
    # --- Producer Prices ---
    "PPI_MONTHLY": {
        "table": "61241-0002",
        "name": "Producer Price Index (Monthly)",
        "description": "Producer price index for industrial products, Germany, months",
        "frequency": "monthly",
        "unit": "Index 2021=100",
        "category": "ppi",
    },
    "PPI_ANNUAL": {
        "table": "61241-0001",
        "name": "Producer Price Index (Annual)",
        "description": "Producer price index for industrial products, Germany, years",
        "frequency": "annual",
        "unit": "Index 2021=100",
        "category": "ppi",
    },
    # --- Construction ---
    "CONSTRUCTION": {
        "table": "44231-0001",
        "name": "Construction Activity (Monthly)",
        "description": "Establishments, persons employed, hours worked, turnover in main construction sector",
        "frequency": "monthly",
        "unit": "various",
        "category": "construction",
    },
}


def _get_credentials() -> tuple:
    """Return (username, password) from env or fallback to GAST."""
    user = os.environ.get("DESTATIS_USER", "").strip()
    pw = os.environ.get("DESTATIS_PASSWORD", "").strip()
    if user and pw:
        return user, pw
    try:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k == "DESTATIS_USER":
                    user = v
                elif k == "DESTATIS_PASSWORD":
                    pw = v
    except OSError:
        pass
    if user and pw:
        return user, pw
    return "GAST", "GAST"


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


def _api_post(endpoint: str, params: dict) -> Dict:
    """Make an authenticated POST request to GENESIS-Online."""
    url = f"{BASE_URL}/{endpoint}"
    user, pw = _get_credentials()
    headers = {
        "username": user,
        "password": pw,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        resp = requests.post(url, headers=headers, data=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type:
            body = resp.json()
            if isinstance(body, dict):
                code = body.get("Code") or (body.get("Status", {}).get("Code") if isinstance(body.get("Status"), dict) else None)
                if code == 15:
                    return {"success": False, "error": "Authentication required — set DESTATIS_USER and DESTATIS_PASSWORD in .env"}
                err_type = body.get("Type") or (body.get("Status", {}).get("Type") if isinstance(body.get("Status"), dict) else None)
                if err_type == "ERROR":
                    msg = body.get("Content") or body.get("Status", {}).get("Content", "Unknown error")
                    return {"success": False, "error": msg}
            return {"success": True, "data": body}
        return {"success": True, "data": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_ffcsv(raw_text: str) -> List[Dict]:
    """Parse GENESIS flat-file CSV into list of observation dicts.

    ffcsv uses semicolons and has a header row with column names.
    Rows contain time period, dimension values, and numeric values.
    """
    lines = raw_text.strip().splitlines()
    if len(lines) < 2:
        return []

    header = [h.strip().strip('"') for h in lines[0].split(";")]

    time_col = None
    value_cols = []
    for i, h in enumerate(header):
        hl = h.lower()
        if hl in ("zeit", "time", "year", "monat", "quartal", "quarter", "month"):
            time_col = i
        if any(kw in hl for kw in ("__", "wert", "value", "index", "anzahl", "amount")):
            value_cols.append(i)

    if time_col is None:
        for i, h in enumerate(header):
            if re.search(r'(zeit|time|jahr|year)', h, re.IGNORECASE):
                time_col = i
                break
    if time_col is None and len(header) > 0:
        time_col = 0

    if not value_cols:
        for i, h in enumerate(header):
            if i != time_col and i > 0:
                value_cols.append(i)

    results = []
    for line in lines[1:]:
        if not line.strip() or line.startswith("#") or line.startswith("__"):
            continue
        cells = [c.strip().strip('"') for c in line.split(";")]
        if len(cells) <= max(time_col or 0, max(value_cols) if value_cols else 0):
            continue

        period = cells[time_col] if time_col is not None else ""
        if not period or period.startswith("__"):
            continue

        row = {"time_period": period}
        for label_idx in range(len(header)):
            if label_idx == time_col or label_idx in value_cols:
                continue
            if label_idx < len(cells) and cells[label_idx]:
                row[header[label_idx]] = cells[label_idx]

        parsed_any = False
        for vi in value_cols:
            if vi < len(cells):
                col_name = header[vi] if vi < len(header) else f"value_{vi}"
                raw_val = cells[vi].replace(",", ".").strip()
                if raw_val in ("", "-", ".", "...", "/", "x", "–"):
                    continue
                try:
                    row[col_name] = float(raw_val)
                    parsed_any = True
                except ValueError:
                    row[col_name] = raw_val

        if parsed_any:
            results.append(row)

    return results


def _parse_table_json(raw: Dict) -> List[Dict]:
    """Parse GENESIS JSON table response into observation dicts."""
    if isinstance(raw, str):
        return _parse_ffcsv(raw)

    obj = raw.get("Object", raw) if isinstance(raw, dict) else raw

    if isinstance(obj, dict) and "Content" in obj and isinstance(obj["Content"], str):
        return _parse_ffcsv(obj["Content"])

    if isinstance(obj, list):
        results = []
        for item in obj:
            if isinstance(item, dict):
                results.append(item)
        return results

    return []


def search_tables(term: str, language: str = "de") -> Dict:
    """Search GENESIS-Online for tables matching a term. Works with guest access."""
    result = _api_post("find/find", {
        "term": term,
        "language": language,
        "pagelength": "20",
        "category": "tables",
    })
    if not result["success"]:
        return result

    data = result["data"]
    tables = data.get("Tables") or []
    return {
        "success": True,
        "tables": [{"code": t["Code"], "content": t.get("Content", "")} for t in tables],
        "count": len(tables),
        "term": term,
    }


def fetch_data(indicator: str, start_year: str = None, end_year: str = None) -> Dict:
    """Fetch a specific indicator from GENESIS-Online."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    if not start_year:
        start_year = str(datetime.now().year - 5)
    if not end_year:
        end_year = str(datetime.now().year)

    cache_params = {"indicator": indicator, "start": start_year, "end": end_year}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    user, _ = _get_credentials()
    if user == "GAST":
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "GENESIS data endpoints require registered credentials. "
                     "Set DESTATIS_USER and DESTATIS_PASSWORD in .env "
                     "(free registration at https://www-genesis.destatis.de).",
        }

    result = _api_post("data/tablefile", {
        "name": cfg["table"],
        "area": "all",
        "compress": "false",
        "format": "ffcsv",
        "language": "en",
        "startyear": start_year,
        "endyear": end_year,
    })

    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_table_json(result["data"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed from response"}

    value_keys = [k for k in observations[0].keys() if k != "time_period" and isinstance(observations[0].get(k), (int, float))]
    primary_key = value_keys[0] if value_keys else None

    latest_value = None
    latest_period = None
    period_change = None
    period_change_pct = None

    if primary_key and len(observations) >= 1:
        sorted_obs = sorted(observations, key=lambda x: x.get("time_period", ""), reverse=True)
        latest_value = sorted_obs[0].get(primary_key)
        latest_period = sorted_obs[0].get("time_period")

        if len(sorted_obs) >= 2 and latest_value is not None:
            prev_v = sorted_obs[1].get(primary_key)
            if prev_v and prev_v != 0:
                period_change = round(latest_value - prev_v, 4)
                period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    data_points = []
    sorted_all = sorted(observations, key=lambda x: x.get("time_period", ""), reverse=True)
    for o in sorted_all[:30]:
        dp = {"period": o.get("time_period")}
        for vk in value_keys[:3]:
            dp[vk] = o.get(vk)
        if not value_keys:
            dp.update({k: v for k, v in o.items() if k != "time_period"})
        data_points.append(dp)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "table": cfg["table"],
        "latest_value": latest_value,
        "latest_period": latest_period,
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": data_points,
        "total_observations": len(observations),
        "source": f"{BASE_URL}/data/tablefile (table {cfg['table']})",
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
            "table": v["table"],
            "category": v["category"],
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
        "success": len(results) > 0 or len(errors) > 0,
        "source": "Destatis GENESIS-Online (Statistisches Bundesamt)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def _print_help():
    print("""
Destatis GENESIS-Online Germany Module (Initiative 0025)

Usage:
  python destatis_germany.py                         # Latest values for all indicators
  python destatis_germany.py <INDICATOR>              # Fetch specific indicator
  python destatis_germany.py list                     # List available indicators
  python destatis_germany.py search <term>            # Search GENESIS tables
  python destatis_germany.py check-auth               # Verify credentials

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Env vars: DESTATIS_USER, DESTATIS_PASSWORD
Register free: https://www-genesis.destatis.de
Source: {BASE_URL}
Protocol: REST (POST, header auth)
Coverage: Germany
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "search":
            term = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Bruttoinlandsprodukt"
            print(json.dumps(search_tables(term), indent=2, default=str, ensure_ascii=False))
        elif cmd == "check-auth":
            user, pw = _get_credentials()
            is_guest = user == "GAST"
            print(f"Username: {user}")
            print(f"Auth source: {'env/file' if not is_guest else 'GUEST (no credentials found)'}")
            result = _api_post("helloworld/logincheck", {"language": "en"})
            if result["success"]:
                status = result["data"].get("Status", "unknown")
                print(f"Login check: {status}")
            else:
                print(f"Login check failed: {result.get('error')}")
            if is_guest:
                print("\nWARNING: Data endpoints require registered credentials.")
                print("Set DESTATIS_USER and DESTATIS_PASSWORD in .env")
                print("Register free at: https://www-genesis.destatis.de")
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
