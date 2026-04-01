#!/usr/bin/env python3
"""
Statbel Belgium Open Data Module — Phase 1

Belgian official statistics: Consumer Price Index (CPI/Health Index since 1920),
Harmonised Index of Consumer Prices (HICP by COICOP category), labour force
unemployment by age/sex, retail trade turnover, income inequality (Gini),
and demographic indicators (birth/death rates).

Data Sources:
  - CPI: https://statbel.fgov.be/en/open-data (pipe-delimited TXT via ZIP)
  - HVD API: https://opendata-api.statbel.fgov.be (PostgREST / JSON)
Auth: None (open access, CC BY 4.0)
Refresh: Monthly (CPI, HICP, retail), Annual (labour, demographics, inequality)
Coverage: Belgium

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import io
import zipfile
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

CPI_ZIP_URL = (
    "https://statbel.fgov.be/sites/default/files/files/opendata/"
    "Consumptieprijsindex%20en%20gezondheidsindex/CPI%20All%20base%20years.zip"
)
API_BASE = "https://opendata-api.statbel.fgov.be"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "statbel_belgium"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.25
CPI_BASE_YEAR = 2013

INDICATORS = {
    # --- Consumer Price Index (direct file download, base 2013=100) ---
    "CPI_INDEX": {
        "source": "cpi_file",
        "name": "Consumer Price Index (base 2013=100)",
        "description": "Belgium overall CPI, base year 2013",
        "frequency": "monthly",
        "unit": "index",
        "field": "MS_CPI_IDX",
    },
    "CPI_INFLATION": {
        "source": "cpi_file",
        "name": "CPI Inflation Rate (YoY %)",
        "description": "Year-over-year CPI inflation rate",
        "frequency": "monthly",
        "unit": "%",
        "field": "MS_CPI_INFL",
    },
    "CPI_HEALTH_INDEX": {
        "source": "cpi_file",
        "name": "Health Index (base 2013=100)",
        "description": "CPI excluding tobacco, alcohol, petrol and diesel",
        "frequency": "monthly",
        "unit": "index",
        "field": "MS_HLTH_IDX",
    },
    "CPI_EXCL_ENERGY": {
        "source": "cpi_file",
        "name": "CPI Excluding Energy (base 2013=100)",
        "description": "CPI index excluding energy products",
        "frequency": "monthly",
        "unit": "index",
        "field": "MS_WTHOUT_ENE_IDX",
    },
    # --- HICP by COICOP division (PostgREST API) ---
    "HICP_FOOD": {
        "source": "api",
        "endpoint": "tf_hvd_hicp",
        "name": "HICP — Food & Non-Alcoholic Beverages",
        "description": "Harmonised CPI for food and non-alcoholic beverages (COICOP 01)",
        "frequency": "monthly",
        "unit": "index (2015=100)",
        "params": {"NM_CD_COICOP_LVL": "eq.1", "CD_COICOP": "eq.01"},
        "value_field": "MS_IDX_HICP",
        "period_fields": ["NM_YR", "NM_MTH"],
    },
    "HICP_HOUSING": {
        "source": "api",
        "endpoint": "tf_hvd_hicp",
        "name": "HICP — Housing, Water, Electricity & Gas",
        "description": "Harmonised CPI for housing, water, electricity, gas and other fuels (COICOP 04)",
        "frequency": "monthly",
        "unit": "index (2015=100)",
        "params": {"NM_CD_COICOP_LVL": "eq.1", "CD_COICOP": "eq.04"},
        "value_field": "MS_IDX_HICP",
        "period_fields": ["NM_YR", "NM_MTH"],
    },
    "HICP_TRANSPORT": {
        "source": "api",
        "endpoint": "tf_hvd_hicp",
        "name": "HICP — Transport",
        "description": "Harmonised CPI for transport (COICOP 07)",
        "frequency": "monthly",
        "unit": "index (2015=100)",
        "params": {"NM_CD_COICOP_LVL": "eq.1", "CD_COICOP": "eq.07"},
        "value_field": "MS_IDX_HICP",
        "period_fields": ["NM_YR", "NM_MTH"],
    },
    "HICP_RESTAURANTS": {
        "source": "api",
        "endpoint": "tf_hvd_hicp",
        "name": "HICP — Restaurants & Hotels",
        "description": "Harmonised CPI for restaurants and hotels (COICOP 11)",
        "frequency": "monthly",
        "unit": "index (2015=100)",
        "params": {"NM_CD_COICOP_LVL": "eq.1", "CD_COICOP": "eq.11"},
        "value_field": "MS_IDX_HICP",
        "period_fields": ["NM_YR", "NM_MTH"],
    },
    # --- Labour force unemployment (PostgREST API, Cube 1: sex × age, national) ---
    "UNEMPLOYMENT_MALE_YOUTH": {
        "source": "api",
        "endpoint": "tf_hvd_lfs_unemployment",
        "name": "Male Youth Unemployment Rate (15–24)",
        "description": "Unemployment rate for males aged 15–24, national annual average",
        "frequency": "annual",
        "unit": "ratio",
        "params": {
            "CD_SEX": "eq.MALE", "CD_EMPMT_AGE": "eq.15-24",
            "CD_QUARTER": "eq.TOTAL", "CD_NUTS_LVL2": "eq.TOTAL",
            "CD_ISCED_2011": "eq.TOTAL", "CD_PROPERTY": "eq.MS_UNEMPMT_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    "UNEMPLOYMENT_FEMALE_YOUTH": {
        "source": "api",
        "endpoint": "tf_hvd_lfs_unemployment",
        "name": "Female Youth Unemployment Rate (15–24)",
        "description": "Unemployment rate for females aged 15–24, national annual average",
        "frequency": "annual",
        "unit": "ratio",
        "params": {
            "CD_SEX": "eq.FEMALE", "CD_EMPMT_AGE": "eq.15-24",
            "CD_QUARTER": "eq.TOTAL", "CD_NUTS_LVL2": "eq.TOTAL",
            "CD_ISCED_2011": "eq.TOTAL", "CD_PROPERTY": "eq.MS_UNEMPMT_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    "UNEMPLOYMENT_MALE_PRIME": {
        "source": "api",
        "endpoint": "tf_hvd_lfs_unemployment",
        "name": "Male Prime-Age Unemployment Rate (25–54)",
        "description": "Unemployment rate for males aged 25–54, national annual average",
        "frequency": "annual",
        "unit": "ratio",
        "params": {
            "CD_SEX": "eq.MALE", "CD_EMPMT_AGE": "eq.25-54",
            "CD_QUARTER": "eq.TOTAL", "CD_NUTS_LVL2": "eq.TOTAL",
            "CD_ISCED_2011": "eq.TOTAL", "CD_PROPERTY": "eq.MS_UNEMPMT_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    "UNEMPLOYMENT_FEMALE_PRIME": {
        "source": "api",
        "endpoint": "tf_hvd_lfs_unemployment",
        "name": "Female Prime-Age Unemployment Rate (25–54)",
        "description": "Unemployment rate for females aged 25–54, national annual average",
        "frequency": "annual",
        "unit": "ratio",
        "params": {
            "CD_SEX": "eq.FEMALE", "CD_EMPMT_AGE": "eq.25-54",
            "CD_QUARTER": "eq.TOTAL", "CD_NUTS_LVL2": "eq.TOTAL",
            "CD_ISCED_2011": "eq.TOTAL", "CD_PROPERTY": "eq.MS_UNEMPMT_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    # --- Retail trade turnover (PostgREST API) ---
    "RETAIL_TURNOVER": {
        "source": "api",
        "endpoint": "tf_hvd_retail_turnover",
        "name": "Retail Trade Turnover Index (base 2021=100)",
        "description": "Total retail trade turnover index, non-adjusted, NACE G47",
        "frequency": "monthly",
        "unit": "index (2021=100)",
        "params": {
            "CD_INDICATOR": "eq.TOVT", "CD_ACTIVITY": "eq.G47",
            "CD_SEASONAL_ADJUST": "eq.N",
        },
        "value_field": "MS_OBS_VALUE",
        "period_fields": ["DT_TIME_PERIOD"],
    },
    # --- Income inequality (PostgREST API) ---
    "GINI_COEFFICIENT": {
        "source": "api",
        "endpoint": "tf_hvd_silc_inequality",
        "name": "Gini Coefficient — Equivalised Disposable Income",
        "description": "Gini coefficient of equivalised disposable income, all ages, total population",
        "frequency": "annual",
        "unit": "coefficient (0–100)",
        "params": {
            "CD_INEQ_AGE": "eq.TOTAL",
            "CD_PROPERTY": "eq.MS_EQUIV_DISPOS_INCM_GINI_COEFF",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    # --- Demographics (PostgREST API) ---
    "BIRTH_RATE": {
        "source": "api",
        "endpoint": "tf_hvd_demo_fertility",
        "name": "Crude Birth Rate — Belgium",
        "description": "Crude birth rate per 1,000 population, national level",
        "frequency": "annual",
        "unit": "rate (per capita)",
        "params": {
            "CD_NUTS": "eq.BE", "CD_AGE": "eq.TOTAL",
            "CD_PROPERTY": "eq.MS_CRUDE_BIRTH_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
    },
    "DEATH_RATE": {
        "source": "api",
        "endpoint": "tf_hvd_demo_mortality",
        "name": "Crude Death Rate — Belgium",
        "description": "Crude death rate per 1,000 population, national level",
        "frequency": "annual",
        "unit": "rate (per capita)",
        "params": {
            "CD_NUTS": "eq.BE",
            "CD_PROPERTY": "eq.MS_CRUDE_DEATH_RATE",
        },
        "value_field": "MS_VALUE",
        "period_fields": ["CD_YEAR"],
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
# CPI file download & parse
# ---------------------------------------------------------------------------

def _download_cpi_data() -> List[Dict]:
    """Download CPI ZIP, extract pipe-delimited TXT, return parsed rows for base year."""
    cache_file = CACHE_DIR / "cpi_raw.json"
    cached = _read_cache(cache_file)
    if cached and cached.get("rows"):
        cached.pop("_cached_at", None)
        return cached["rows"]

    try:
        resp = requests.get(CPI_ZIP_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        return []

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
            txt_name = next((n for n in names if n.endswith(".txt")), names[0])
            raw_text = zf.read(txt_name).decode("utf-8-sig")
    except Exception:
        return []

    lines = raw_text.strip().split("\n")
    if len(lines) < 2:
        return []

    headers = [h.strip() for h in lines[0].split("|")]
    rows = []
    for line in lines[1:]:
        fields = [f.strip() for f in line.split("|")]
        if len(fields) != len(headers):
            continue
        row = dict(zip(headers, fields))
        base_yr = row.get("NM_BASE_YR", "")
        if base_yr != str(CPI_BASE_YEAR):
            continue
        try:
            parsed = {
                "year": int(row["NM_YR"]),
                "month": int(row["NM_MTH"]),
            }
            for col in ("MS_CPI_IDX", "MS_HLTH_IDX", "MS_WTHOUT_ENE_IDX",
                        "MS_WITHOUT_PTRL_IDX", "MS_SMOOTH_IDX"):
                val = row.get(col, ".")
                parsed[col] = float(val) if val not in (".", "") else None
            infl = row.get("MS_CPI_INFL", ".")
            if infl not in (".", "") and "%" in infl:
                parsed["MS_CPI_INFL"] = float(infl.replace("%", ""))
            else:
                parsed["MS_CPI_INFL"] = None
            rows.append(parsed)
        except (ValueError, KeyError):
            continue

    rows.sort(key=lambda r: (r["year"], r["month"]), reverse=True)
    _write_cache(cache_file, {"rows": rows})
    return rows


def _compute_yoy_inflation(rows: List[Dict]) -> List[Dict]:
    """Compute YoY inflation from CPI index values."""
    by_period = {}
    for r in rows:
        val = r.get("MS_CPI_IDX")
        if val is not None:
            by_period[(r["year"], r["month"])] = val

    results = []
    for (yr, mth), val in sorted(by_period.items(), reverse=True):
        prev = by_period.get((yr - 1, mth))
        if prev and prev != 0:
            infl = round((val / prev - 1) * 100, 2)
            results.append({"period": f"{yr}-{mth:02d}", "value": infl})
    return results


def _fetch_cpi_indicator(indicator: str) -> Dict:
    """Fetch a CPI indicator from the downloaded file."""
    cfg = INDICATORS[indicator]
    field = cfg["field"]
    rows = _download_cpi_data()
    if not rows:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "Failed to download CPI data"}

    if field == "MS_CPI_INFL":
        observations = _compute_yoy_inflation(rows)
    else:
        observations = []
        for r in rows:
            val = r.get(field)
            if val is not None:
                period = f"{r['year']}-{r['month']:02d}"
                observations.append({"period": period, "value": val})

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations found"}

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v, prev_v = observations[0]["value"], observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
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
        "source": CPI_ZIP_URL,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# PostgREST API helpers
# ---------------------------------------------------------------------------

def _format_period(row: Dict, period_fields: List[str]) -> str:
    """Build a sortable period string from row fields."""
    if period_fields == ["DT_TIME_PERIOD"]:
        return row.get("DT_TIME_PERIOD", "")
    if period_fields == ["NM_YR", "NM_MTH"]:
        yr = row.get("NM_YR", 0)
        mth = row.get("NM_MTH", 0)
        return f"{yr}-{int(mth):02d}"
    if period_fields == ["CD_YEAR"]:
        return str(row.get("CD_YEAR", ""))
    return str(row.get(period_fields[0], ""))


def _api_query(endpoint: str, params: Dict, value_field: str,
               period_fields: List[str], limit: int = 60) -> Dict:
    """Query the Statbel PostgREST API."""
    url = f"{API_BASE}/{endpoint}"

    order_parts = []
    for pf in period_fields:
        order_parts.append(f"{pf}.desc")
    qp = {**params, "order": ",".join(order_parts), "limit": str(limit)}

    select_fields = list(period_fields) + [value_field]
    qp["select"] = ",".join(select_fields)

    try:
        resp = requests.get(url, params=qp, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return {"success": False, "error": "Unexpected response format"}
        return {"success": True, "data": data}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_api_indicator(indicator: str) -> Dict:
    """Fetch an API-backed indicator."""
    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "endpoint": cfg["endpoint"]}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_query(
        cfg["endpoint"], cfg["params"],
        cfg["value_field"], cfg["period_fields"],
    )
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": result["error"]}

    raw_rows = result["data"]
    observations = []
    for row in raw_rows:
        val = row.get(cfg["value_field"])
        if val is None:
            continue
        period = _format_period(row, cfg["period_fields"])
        observations.append({"period": period, "value": float(val)})

    observations.sort(key=lambda x: x["period"], reverse=True)

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations returned"}

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v, prev_v = observations[0]["value"], observations[1]["value"]
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
        "source": f"{API_BASE}/{cfg['endpoint']}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    if cfg["source"] == "cpi_file":
        return _fetch_cpi_indicator(indicator)
    return _fetch_api_indicator(indicator)


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "source": v["source"],
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
        if INDICATORS[key]["source"] == "api":
            time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Statbel — Statistics Belgium",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
Statbel Belgium Open Data Module (Phase 1)

Usage:
  python statbel_belgium.py                     # Latest values for all indicators
  python statbel_belgium.py <INDICATOR>          # Fetch specific indicator
  python statbel_belgium.py list                 # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Data Sources:
  CPI/Health Index: {CPI_ZIP_URL}
  HVD API:          {API_BASE}
Coverage: Belgium
License: CC BY 4.0
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
