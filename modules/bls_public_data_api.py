"""
BLS Public Data API — U.S. Bureau of Labor Statistics

Data Source: https://www.bls.gov/developers/
Update: Monthly (most series)
Free: Yes — No API key required (v2 public access: 500 daily queries, 10 series/request)

Provides:
- Unemployment rate (national, state, metro)
- Consumer Price Index (CPI) / Inflation
- Producer Price Index (PPI)
- Employment / Nonfarm Payrolls
- Average hourly earnings / wages
- Job Openings (JOLTS)
- Labor productivity
- Import/Export price indexes

Key Series IDs:
- LNS14000000  — National unemployment rate (seasonally adjusted)
- CUUR0000SA0  — CPI-U All Items (US city average)
- CES0000000001 — Total nonfarm employment
- JTS000000000000000JOL — JOLTS job openings
- PRS85006092  — Nonfarm business labor productivity
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/bls")
os.makedirs(CACHE_DIR, exist_ok=True)

# Well-known series IDs for convenience functions
SERIES = {
    # Labor force
    "unemployment_rate": "LNS14000000",
    "labor_force": "LNS11000000",
    "employment_level": "LNS12000000",
    "participation_rate": "LNS11300000",
    # Prices
    "cpi_all_items": "CUUR0000SA0",
    "cpi_food": "CUUR0000SAF1",
    "cpi_energy": "CUUR0000SA0E",
    "cpi_core": "CUUR0000SA0L1E",  # All items less food & energy
    "ppi_final_demand": "WPSFD4",
    # Employment
    "nonfarm_payrolls": "CES0000000001",
    "avg_hourly_earnings": "CES0500000003",
    "avg_weekly_hours": "CES0500000002",
    # JOLTS
    "job_openings": "JTS000000000000000JOL",
    "hires": "JTS000000000000000HIR",
    "quits": "JTS000000000000000QUR",
    # Productivity
    "labor_productivity": "PRS85006092",
    # Import/Export
    "import_price_index": "EIUIR",
    "export_price_index": "EIUIQ",
}

TIMEOUT = 30

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cache_key(series_ids: list, start: str, end: str) -> str:
    """Generate a cache filename."""
    ids = "_".join(sorted(series_ids))[:80]
    return os.path.join(CACHE_DIR, f"{ids}_{start}_{end}.json")


def _read_cache(path: str, max_age_hours: int = 12) -> Optional[dict]:
    """Return cached data if fresh enough."""
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    with open(path) as f:
        return json.load(f)


def _write_cache(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f)


def _post_series(series_ids: List[str], start_year: int, end_year: int) -> dict:
    """
    Core POST request to BLS API v2.
    Returns raw JSON response dict.
    """
    if len(series_ids) > 10:
        raise ValueError("BLS public API allows max 10 series per request (no registration key)")

    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(BASE_URL, json=payload, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        msgs = data.get("message", [])
        raise RuntimeError(f"BLS API error: {msgs}")

    return data


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_series(series_id: str,
               start_year: Optional[int] = None,
               end_year: Optional[int] = None,
               use_cache: bool = True) -> List[Dict]:
    """
    Fetch time-series data for a single BLS series.

    Args:
        series_id: BLS series identifier (e.g. 'LNS14000000')
        start_year: First year of data (default: current year - 2)
        end_year: Last year of data (default: current year)
        use_cache: Whether to use local file cache

    Returns:
        List of dicts with keys: year, period, periodName, value, footnotes
        Sorted newest-first.
    """
    now = datetime.now()
    end_year = end_year or now.year
    start_year = start_year or (end_year - 2)

    cache_path = _cache_key([series_id], str(start_year), str(end_year))
    if use_cache:
        cached = _read_cache(cache_path)
        if cached:
            return cached

    raw = _post_series([series_id], start_year, end_year)
    series_list = raw.get("Results", {}).get("series", [])
    if not series_list:
        return []

    records = series_list[0].get("data", [])
    # Normalise values to float where possible
    for rec in records:
        try:
            rec["value"] = float(rec["value"])
        except (ValueError, TypeError):
            pass

    if use_cache:
        _write_cache(cache_path, records)

    return records


def get_multiple_series(series_ids: List[str],
                        start_year: Optional[int] = None,
                        end_year: Optional[int] = None) -> Dict[str, List[Dict]]:
    """
    Fetch data for multiple BLS series in one request (max 10).

    Returns:
        Dict mapping series_id -> list of data points.
    """
    now = datetime.now()
    end_year = end_year or now.year
    start_year = start_year or (end_year - 2)

    raw = _post_series(series_ids, start_year, end_year)
    result = {}
    for s in raw.get("Results", {}).get("series", []):
        sid = s.get("seriesID", "")
        records = s.get("data", [])
        for rec in records:
            try:
                rec["value"] = float(rec["value"])
            except (ValueError, TypeError):
                pass
        result[sid] = records
    return result


def get_unemployment_rate(start_year: Optional[int] = None,
                          end_year: Optional[int] = None) -> List[Dict]:
    """
    Get U.S. national unemployment rate (seasonally adjusted).

    Returns list of monthly readings, newest first.
    """
    return get_series(SERIES["unemployment_rate"], start_year, end_year)


def get_cpi(start_year: Optional[int] = None,
            end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Consumer Price Index — All Urban Consumers, All Items (CPI-U).

    Returns list of monthly index values, newest first.
    """
    return get_series(SERIES["cpi_all_items"], start_year, end_year)


def get_core_cpi(start_year: Optional[int] = None,
                 end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Core CPI (All Items Less Food and Energy).
    """
    return get_series(SERIES["cpi_core"], start_year, end_year)


def get_nonfarm_payrolls(start_year: Optional[int] = None,
                         end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Total Nonfarm Employment (thousands, seasonally adjusted).

    Key monthly economic indicator watched by markets.
    """
    return get_series(SERIES["nonfarm_payrolls"], start_year, end_year)


def get_avg_hourly_earnings(start_year: Optional[int] = None,
                            end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Average Hourly Earnings of All Employees (Total Private).
    """
    return get_series(SERIES["avg_hourly_earnings"], start_year, end_year)


def get_job_openings(start_year: Optional[int] = None,
                     end_year: Optional[int] = None) -> List[Dict]:
    """
    Get JOLTS Job Openings (thousands).
    """
    return get_series(SERIES["job_openings"], start_year, end_year)


def get_labor_productivity(start_year: Optional[int] = None,
                           end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Nonfarm Business Sector Labor Productivity index.
    """
    return get_series(SERIES["labor_productivity"], start_year, end_year)


def get_ppi(start_year: Optional[int] = None,
            end_year: Optional[int] = None) -> List[Dict]:
    """
    Get Producer Price Index — Final Demand.
    """
    return get_series(SERIES["ppi_final_demand"], start_year, end_year)


def get_inflation_snapshot() -> Dict:
    """
    Get a quick snapshot of key inflation indicators (latest values).

    Returns dict with CPI, Core CPI, and PPI latest readings + YoY context.
    """
    result = {}
    for label, sid in [("cpi", "cpi_all_items"),
                       ("core_cpi", "cpi_core"),
                       ("ppi", "ppi_final_demand")]:
        try:
            data = get_series(SERIES[sid])
            if data:
                latest = data[0]
                result[label] = {
                    "value": latest["value"],
                    "period": latest.get("periodName", ""),
                    "year": latest.get("year", ""),
                    "series_id": SERIES[sid],
                }
        except Exception as e:
            result[label] = {"error": str(e)}
    result["fetched_at"] = datetime.now().isoformat()
    return result


def get_labor_market_dashboard() -> Dict:
    """
    Comprehensive labor market dashboard — pulls unemployment, payrolls,
    earnings, JOLTS, and participation rate in one call.

    Returns dict keyed by indicator name with latest values.
    """
    ids_map = {
        "unemployment_rate": SERIES["unemployment_rate"],
        "participation_rate": SERIES["participation_rate"],
        "nonfarm_payrolls": SERIES["nonfarm_payrolls"],
        "avg_hourly_earnings": SERIES["avg_hourly_earnings"],
        "job_openings": SERIES["job_openings"],
    }
    try:
        multi = get_multiple_series(list(ids_map.values()))
    except Exception as e:
        return {"error": str(e)}

    dashboard = {}
    for name, sid in ids_map.items():
        records = multi.get(sid, [])
        if records:
            latest = records[0]
            dashboard[name] = {
                "value": latest["value"],
                "period": latest.get("periodName", ""),
                "year": latest.get("year", ""),
            }
        else:
            dashboard[name] = {"value": None}

    dashboard["fetched_at"] = datetime.now().isoformat()
    return dashboard


def list_available_series() -> Dict[str, str]:
    """
    Return the built-in mapping of friendly names → BLS series IDs.
    Useful for discovering what's available without looking up docs.
    """
    return dict(SERIES)


if __name__ == "__main__":
    print(json.dumps({
        "module": "bls_public_data_api",
        "status": "ready",
        "source": "https://www.bls.gov/developers/",
        "series_count": len(SERIES),
        "functions": [
            "get_series", "get_multiple_series",
            "get_unemployment_rate", "get_cpi", "get_core_cpi",
            "get_nonfarm_payrolls", "get_avg_hourly_earnings",
            "get_job_openings", "get_labor_productivity", "get_ppi",
            "get_inflation_snapshot", "get_labor_market_dashboard",
            "list_available_series",
        ]
    }, indent=2))
