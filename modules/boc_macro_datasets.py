"""
Bank of Canada Macro Datasets — Valet API

Data Source: Bank of Canada Valet API (https://www.bankofcanada.ca/valet/)
Update: Daily (exchange rates), Weekly/Monthly/Quarterly (other series)
History: Varies by series, many back to 1990s+
Free: Yes (no API key required)

Provides:
- Policy interest rate (overnight target rate)
- CPI / inflation metrics
- Exchange rates (26+ currency pairs vs CAD)
- Commodity price indices (BCPI)
- Government bond yields
- Key macro indicators

Valet API docs: https://www.bankofcanada.ca/valet/docs

Key series IDs:
- V39079: Target overnight rate
- V41693242: CPIX year-over-year
- FXUSDCAD: USD/CAD exchange rate
- A.BCPI: Annual commodity price index (total)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

BASE_URL = "https://www.bankofcanada.ca/valet"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/boc")
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Well-known series shortcuts
# ---------------------------------------------------------------------------
SERIES_ALIASES = {
    # Policy rates
    "overnight_target": "V39079",
    "bank_rate": "V39078",
    "prime_rate": "V80691319",
    # CPI / Inflation
    "cpi_total_yoy": "ATOM_V41693242",
    "cpi_trim_yoy": "STATIC_INFLATIONCALC_TRIM_V41693242",
    # Exchange rates
    "usd_cad": "FXUSDCAD",
    "eur_cad": "FXEURCAD",
    "gbp_cad": "FXGBPCAD",
    "jpy_cad": "FXJPYCAD",
    "cny_cad": "FXCNYCAD",
    "aud_cad": "FXAUDCAD",
    # Commodity indices (annual)
    "bcpi_total": "A.BCPI",
    "bcpi_energy": "A.ENER",
    "bcpi_metals": "A.MTLS",
    "bcpi_agriculture": "A.AGRI",
    "bcpi_forestry": "A.FOPR",
    "bcpi_fish": "A.FISH",
    "bcpi_ex_energy": "A.BCNE",
}

# Well-known group IDs
GROUP_ALIASES = {
    "fx_daily": "FX_RATES_DAILY",
    "fx_monthly": "FX_RATES_MONTHLY",
    "fx_annual": "FX_RATES_ANNUAL",
    "bond_yield_all": "bond_yields_all",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_json(url: str, timeout: int = 15) -> dict:
    """Fetch JSON from the Valet API with error handling."""
    headers = {"Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _resolve_series(name_or_id: str) -> str:
    """Resolve a human-friendly alias to a Valet series ID."""
    return SERIES_ALIASES.get(name_or_id.lower(), name_or_id)


def _parse_observations(raw: dict) -> List[Dict]:
    """
    Flatten Valet observation JSON into a list of dicts.
    Each dict has 'date' plus one key per series with its numeric value.
    """
    obs = raw.get("observations", [])
    series_keys = list(raw.get("seriesDetail", {}).keys())
    rows = []
    for o in obs:
        row = {"date": o.get("d")}
        for sk in series_keys:
            val = o.get(sk, {}).get("v")
            if val is not None:
                try:
                    row[sk] = float(val)
                except (ValueError, TypeError):
                    row[sk] = val
            else:
                row[sk] = None
        rows.append(row)
    return rows


def _cache_key(name: str) -> str:
    safe = name.replace("/", "_").replace(".", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _read_cache(name: str, max_age_hours: int = 4) -> Optional[dict]:
    path = _cache_key(name)
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    with open(path) as f:
        return json.load(f)


def _write_cache(name: str, data: dict):
    with open(_cache_key(name), "w") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_series(series: str, recent: int = 10,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None) -> List[Dict]:
    """
    Fetch observations for a single Valet series.

    Args:
        series: Valet series ID or alias (e.g. 'overnight_target', 'FXUSDCAD')
        recent: Number of most recent observations (ignored when date range given)
        start_date: ISO date string YYYY-MM-DD (optional)
        end_date: ISO date string YYYY-MM-DD (optional)

    Returns:
        List of dicts with 'date' and series value.

    Example:
        >>> get_series('overnight_target', recent=5)
        [{'date': '2026-03-05', 'V39079': 2.25}, ...]
    """
    sid = _resolve_series(series)
    cache_name = f"series_{sid}_{recent}_{start_date}_{end_date}"
    cached = _read_cache(cache_name)
    if cached:
        return cached

    url = f"{BASE_URL}/observations/{sid}/json"
    params = []
    if start_date and end_date:
        params.append(f"start_date={start_date}")
        params.append(f"end_date={end_date}")
    else:
        params.append(f"recent={recent}")
    if params:
        url += "?" + "&".join(params)

    data = _get_json(url)
    rows = _parse_observations(data)
    _write_cache(cache_name, rows)
    return rows


def get_policy_rate(recent: int = 10) -> List[Dict]:
    """
    Get the Bank of Canada overnight target rate.

    Returns:
        List of dicts: [{'date': '2026-03-05', 'rate': 2.25}, ...]
    """
    rows = get_series("overnight_target", recent=recent)
    return [{"date": r["date"], "rate": r.get("V39079")} for r in rows]


def get_exchange_rate(currency: str = "USD", recent: int = 10,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict]:
    """
    Get daily exchange rate for a currency vs CAD.

    Args:
        currency: 3-letter currency code (e.g. 'USD', 'EUR', 'GBP')
        recent: Number of recent observations
        start_date / end_date: Date range (YYYY-MM-DD)

    Returns:
        List of dicts: [{'date': '...', 'rate': 1.3613}, ...]
    """
    sid = f"FX{currency.upper()}CAD"
    rows = get_series(sid, recent=recent, start_date=start_date, end_date=end_date)
    return [{"date": r["date"], "rate": r.get(sid)} for r in rows]


def get_cpi(recent: int = 12) -> List[Dict]:
    """
    Get CPI (CPIX) year-over-year percentage change.

    Returns:
        List of dicts: [{'date': '...', 'cpi_yoy_pct': 2.8}, ...]
    """
    sid = "ATOM_V41693242"
    rows = get_series(sid, recent=recent)
    return [{"date": r["date"], "cpi_yoy_pct": r.get(sid)} for r in rows]


def get_commodity_index(component: str = "total", recent: int = 10) -> List[Dict]:
    """
    Get Bank of Canada Commodity Price Index (BCPI).

    Args:
        component: One of 'total', 'energy', 'metals', 'agriculture',
                   'forestry', 'fish', 'ex_energy'

    Returns:
        List of dicts with date and index value.
    """
    alias = f"bcpi_{component.lower()}"
    sid = SERIES_ALIASES.get(alias)
    if not sid:
        raise ValueError(f"Unknown BCPI component '{component}'. "
                         f"Choose from: total, energy, metals, agriculture, forestry, fish, ex_energy")
    rows = get_series(sid, recent=recent)
    return [{"date": r["date"], "index": r.get(sid)} for r in rows]


def get_group(group: str, recent: int = 5) -> Dict:
    """
    Fetch all series in a Valet group (e.g. FX_RATES_DAILY).

    Args:
        group: Group ID or alias (e.g. 'fx_daily', 'FX_RATES_DAILY')
        recent: Number of recent observations

    Returns:
        Dict with 'group_info', 'series_detail', and 'observations'.
    """
    gid = GROUP_ALIASES.get(group.lower(), group)
    url = f"{BASE_URL}/observations/group/{gid}/json?recent={recent}"
    data = _get_json(url)
    return {
        "group_info": data.get("groupDetail", {}),
        "series_detail": {k: v.get("description", v.get("label", k))
                          for k, v in data.get("seriesDetail", {}).items()},
        "observations": _parse_observations(data),
    }


def list_series(search: Optional[str] = None) -> Dict[str, str]:
    """
    List all available Valet series (ID → description).
    WARNING: This is a large payload (~2 MB). Use search to filter.

    Args:
        search: Optional substring filter (case-insensitive)

    Returns:
        Dict mapping series ID to description.
    """
    cached = _read_cache("all_series_list", max_age_hours=24)
    if cached is None:
        data = _get_json(f"{BASE_URL}/lists/series/json")
        cached = {k: v.get("description", v.get("label", ""))
                  for k, v in data.get("series", {}).items()}
        _write_cache("all_series_list", cached)

    if search:
        needle = search.lower()
        return {k: v for k, v in cached.items()
                if needle in k.lower() or needle in v.lower()}
    return cached


def list_groups(search: Optional[str] = None) -> Dict[str, str]:
    """
    List all available Valet groups.

    Args:
        search: Optional substring filter (case-insensitive)

    Returns:
        Dict mapping group ID to label.
    """
    cached = _read_cache("all_groups_list", max_age_hours=24)
    if cached is None:
        data = _get_json(f"{BASE_URL}/lists/groups/json")
        cached = {k: v.get("label", "")
                  for k, v in data.get("groups", {}).items()}
        _write_cache("all_groups_list", cached)

    if search:
        needle = search.lower()
        return {k: v for k, v in cached.items()
                if needle in k.lower() or needle in v.lower()}
    return cached


def get_series_info(series: str) -> Dict:
    """
    Get metadata for a single series.

    Returns:
        Dict with label, description, and dimension info.
    """
    sid = _resolve_series(series)
    data = _get_json(f"{BASE_URL}/series/{sid}/json")
    detail = data.get("seriesDetail", {}).get(sid, {})
    return {
        "series_id": sid,
        "label": detail.get("label", ""),
        "description": detail.get("description", ""),
    }


def get_yield_curve(recent: int = 5) -> List[Dict]:
    """
    Get Canadian government bond yields across maturities.
    Uses individual well-known yield series.

    Returns:
        List of dicts per date with yields for various tenors.
    """
    tenors = {
        "BD.CDN.2YR.DQ.YLD": "2yr",
        "BD.CDN.3YR.DQ.YLD": "3yr",
        "BD.CDN.5YR.DQ.YLD": "5yr",
        "BD.CDN.7YR.DQ.YLD": "7yr",
        "BD.CDN.10YR.DQ.YLD": "10yr",
        "BD.CDN.LONG.DQ.YLD": "long",
    }
    # Fetch all tenors in a single multi-series call
    series_csv = ",".join(tenors.keys())
    url = f"{BASE_URL}/observations/{series_csv}/json?recent={recent}"
    data = _get_json(url)
    obs = data.get("observations", [])
    results = []
    for o in obs:
        row = {"date": o.get("d")}
        for sid, label in tenors.items():
            val = o.get(sid, {}).get("v")
            row[label] = float(val) if val else None
        results.append(row)
    return results


# ---------------------------------------------------------------------------
# Summary / dashboard helper
# ---------------------------------------------------------------------------

def get_macro_snapshot() -> Dict:
    """
    Quick macro snapshot: policy rate, USD/CAD, EUR/CAD, CPI, yield curve.
    Useful for dashboards.

    Returns:
        Dict with latest values for key Canadian macro indicators.
    """
    snapshot = {"fetched_at": datetime.utcnow().isoformat()}

    try:
        rate = get_policy_rate(recent=1)
        snapshot["overnight_target_rate"] = rate[0] if rate else None
    except Exception as e:
        snapshot["overnight_target_rate"] = {"error": str(e)}

    try:
        usd = get_exchange_rate("USD", recent=1)
        snapshot["usd_cad"] = usd[0] if usd else None
    except Exception as e:
        snapshot["usd_cad"] = {"error": str(e)}

    try:
        eur = get_exchange_rate("EUR", recent=1)
        snapshot["eur_cad"] = eur[0] if eur else None
    except Exception as e:
        snapshot["eur_cad"] = {"error": str(e)}

    try:
        cpi = get_cpi(recent=1)
        snapshot["cpi_yoy"] = cpi[0] if cpi else None
    except Exception as e:
        snapshot["cpi_yoy"] = {"error": str(e)}

    try:
        yc = get_yield_curve(recent=1)
        snapshot["yield_curve"] = yc[0] if yc else None
    except Exception as e:
        snapshot["yield_curve"] = {"error": str(e)}

    return snapshot


if __name__ == "__main__":
    print(json.dumps({
        "module": "boc_macro_datasets",
        "status": "active",
        "source": "https://www.bankofcanada.ca/valet/",
        "functions": [
            "get_series", "get_policy_rate", "get_exchange_rate", "get_cpi",
            "get_commodity_index", "get_group", "list_series", "list_groups",
            "get_series_info", "get_yield_curve", "get_macro_snapshot",
        ],
    }, indent=2))
