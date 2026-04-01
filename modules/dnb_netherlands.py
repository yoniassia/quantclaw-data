#!/usr/bin/env python3
"""
DNB Netherlands Statistics Module

De Nederlandsche Bank (Dutch Central Bank) statistical data: banking structure,
financial stability indicators, insurance/pension balance sheets, payment
statistics, monetary aggregates, and household deposit/lending rates.

Data Source: https://api.dnb.nl/statpub-intapi-prd/v1/
Protocol: REST JSON (Azure APIM)
Auth: Subscription key via Ocp-Apim-Subscription-Key header
      (DNB_SUBSCRIPTION_KEY env var, falls back to public website key)
Refresh: Quarterly (most series), Half-yearly (payments)
Coverage: Netherlands

Author: QUANTCLAW DATA Build Agent
Phase: 1
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

BASE_URL = "https://api.dnb.nl/statpub-intapi-prd/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "dnb_netherlands"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

_PUBLIC_FALLBACK_KEY = "e0249d4903b049e6844a8bc0c5961ddf"


def _get_subscription_key() -> Optional[str]:
    key = os.environ.get("DNB_SUBSCRIPTION_KEY", "").strip()
    if key:
        return key
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DNB_SUBSCRIPTION_KEY="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        return val
        except OSError:
            pass
    return _PUBLIC_FALLBACK_KEY


INDICATORS = {
    "FINANCIAL_STABILITY_Q": {
        "resource_id": "780b80e6-f03b-4621-b699-2bdc1cb005a4",
        "name": "Financial Stability Indicators (Quarterly)",
        "description": "Key FSIs for Dutch banking sector — capital adequacy, asset quality, profitability, liquidity",
        "frequency": "quarterly",
        "unit": "% / ratio",
    },
    "FINANCIAL_STABILITY_Y": {
        "resource_id": "fa25d7ba-e776-438e-b1f0-446f526ef517",
        "name": "Financial Stability Indicators (Yearly)",
        "description": "Annual FSIs for Dutch banking sector — capital adequacy, asset quality, profitability, liquidity",
        "frequency": "yearly",
        "unit": "% / ratio",
    },
    "BANK_STRUCTURE": {
        "resource_id": "4babde76-7437-484e-9f85-293a9573040f",
        "name": "Structural Indicators — Dutch Banking System",
        "description": "Number of banks and balance sheet totals by bank type (domestic, foreign, EU, non-EU)",
        "frequency": "quarterly",
        "unit": "EUR mn / count",
    },
    "INSURANCE_BALANCE_SHEET": {
        "resource_id": "0e326e3a-124e-402f-bae9-13c862402744",
        "name": "Insurance Corporations Balance Sheet",
        "description": "Assets and liabilities of Dutch insurance companies by instrument and geography",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "PENSION_BALANCE_SHEET": {
        "resource_id": "69833258-bf55-4fb5-a7ef-cc665dd28f61",
        "name": "Pension Funds Balance Sheet",
        "description": "Assets and liabilities of Dutch pension funds by instrument and geography",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "INSURERS_CASHFLOW": {
        "resource_id": "9b95f3e5-ed3c-42bc-960b-b19541ccc377",
        "name": "Insurers Cash Flow Statement",
        "description": "Cash flow from operating, investing, and financing activities for Dutch insurers",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "PAYMENT_TRANSACTIONS": {
        "resource_id": "a24f247c-72df-44b1-97e9-b3f41767c9ff",
        "name": "Payment Transactions (Number & Value)",
        "description": "Card-based, credit transfer, and direct debit transaction volumes and amounts",
        "frequency": "half-yearly",
        "unit": "EUR mn / millions",
    },
    "PAYMENT_INFRA": {
        "resource_id": "3f5ead83-1fac-4684-8c84-600b9e958fac",
        "name": "Domestic Payment Infrastructure (Units)",
        "description": "POS terminals, ATMs, cards in circulation, and other payment infrastructure counts",
        "frequency": "half-yearly",
        "unit": "units / millions",
    },
    "MONETARY_AGGREGATES": {
        "resource_id": "fcc231d1-9885-480c-b225-5b6df38b42b5",
        "name": "Dutch Contribution to Monetary Aggregates",
        "description": "Netherlands contribution to Euro Area M1/M2/M3 money supply (stocks and flows)",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "HOUSEHOLD_RATES": {
        "resource_id": "fa3ecc16-6bc1-4b35-b5de-c56b13d9cd36",
        "name": "Household Deposits & Loans Interest Rates",
        "description": "MFI interest rates on household deposits, consumer credit, and mortgage loans",
        "frequency": "monthly",
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


def _ts_to_date(ts) -> Optional[str]:
    """Convert millisecond Unix timestamp to YYYY-MM-DD string."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts) / 1000, tz=None).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return str(ts)


def _api_request(resource_id: str) -> Dict:
    key = _get_subscription_key()
    if not key:
        return {"success": False, "error": "No subscription key available (set DNB_SUBSCRIPTION_KEY)"}

    url = f"{BASE_URL}/resources/{resource_id}/resourcefile/json"
    headers = {
        "Accept": "application/json",
        "Ocp-Apim-Subscription-Key": key,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 401:
            return {"success": False, "error": "Invalid or missing subscription key (HTTP 401)"}
        if status == 404:
            return {"success": False, "error": f"Resource not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_resource(raw: Dict) -> List[Dict]:
    """Parse DNB resource JSON into structured observation dicts."""
    labels = raw.get("labels", [])
    rows = raw.get("data", [])
    if not labels or not rows:
        return []

    period_idx = None
    value_idx = None
    for i, label in enumerate(labels):
        lbl = label.strip().lower()
        if lbl in ("period", "period "):
            period_idx = i
        if lbl in ("waarde", "value"):
            value_idx = i

    if period_idx is None:
        for i, label in enumerate(labels):
            if "period" in label.lower():
                period_idx = i
                break
    if value_idx is None:
        value_idx = len(labels) - 1

    dim_indices = [i for i in range(len(labels)) if i != period_idx and i != value_idx]

    results = []
    for row in rows:
        if len(row) <= max(period_idx or 0, value_idx):
            continue
        val = row[value_idx]
        if val is None:
            continue

        period_raw = row[period_idx] if period_idx is not None else None
        period_str = _ts_to_date(period_raw) if isinstance(period_raw, (int, float)) else str(period_raw) if period_raw else None

        dims = {}
        for di in dim_indices:
            if di < len(row):
                dim_name = labels[di].strip()
                dim_val = row[di]
                if isinstance(dim_val, str):
                    dim_val = dim_val.strip()
                dims[dim_name] = dim_val

        try:
            val = float(val)
        except (ValueError, TypeError):
            continue

        results.append({
            "period": period_str,
            "value": val,
            "dimensions": dims,
        })

    results.sort(key=lambda x: x.get("period") or "", reverse=True)
    return results


def _filter_observations(observations: List[Dict], filters: Optional[Dict] = None) -> List[Dict]:
    """Filter observations by dimension values (case-insensitive substring match)."""
    if not filters:
        return observations
    filtered = []
    for obs in observations:
        match = True
        for fkey, fval in filters.items():
            found = False
            fval_lower = fval.lower()
            for dk, dv in obs.get("dimensions", {}).items():
                if fkey.lower() in dk.lower() and fval_lower in str(dv).lower():
                    found = True
                    break
            if not found:
                match = False
                break
        if match:
            filtered.append(obs)
    return filtered


def fetch_data(indicator: str, filters: Optional[Dict] = None, limit: int = 50) -> Dict:
    """Fetch a specific indicator/resource with optional dimension filters."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "filters": filters}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["resource_id"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_resource(result["data"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed"}

    observations = _filter_observations(observations, filters)
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations match filters"}

    latest = observations[0]
    period_change = period_change_pct = None
    if len(observations) >= 2:
        prev = observations[1]
        if prev["value"] and prev["value"] != 0:
            period_change = round(latest["value"] - prev["value"], 4)
            period_change_pct = round((period_change / abs(prev["value"])) * 100, 4)

    table_name = result["data"].get("name", "").strip()
    labels = result["data"].get("labels", [])

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "table_name": table_name,
        "columns": [l.strip() for l in labels],
        "latest_value": latest["value"],
        "latest_period": latest["period"],
        "latest_dimensions": latest.get("dimensions", {}),
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"period": o["period"], "value": o["value"], "dimensions": o.get("dimensions", {})}
            for o in observations[:limit]
        ],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/resources/{cfg['resource_id']}/resourcefile/json",
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
            "resource_id": v["resource_id"],
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
        "source": "De Nederlandsche Bank (DNB)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def search_datasets(query: str, page: int = 0, page_size: int = 10) -> Dict:
    """Search DNB datasets by keyword."""
    key = _get_subscription_key()
    if not key:
        return {"success": False, "error": "No subscription key available"}

    url = f"{BASE_URL}/datasets"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Ocp-Apim-Subscription-Key": key,
    }
    params = {"q": query, "page": page, "pageSize": page_size, "languageCode": "en"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        datasets = []
        for r in data.get("results", []):
            resources = [
                {"id": res["id"], "name": res.get("name", "?")}
                for res in r.get("resources", [])
            ]
            datasets.append({
                "dataset_id": r["id"],
                "resources": resources,
            })
        return {
            "success": True,
            "total": data.get("count", 0),
            "page": page,
            "datasets": datasets,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- CLI ---

def _print_help():
    print("""
DNB Netherlands Statistics Module (Phase 1)

Usage:
  python dnb_netherlands.py                              # Latest values for all indicators
  python dnb_netherlands.py <INDICATOR>                   # Fetch specific indicator
  python dnb_netherlands.py <INDICATOR> key=val           # Fetch with dimension filter
  python dnb_netherlands.py list                          # List available indicators
  python dnb_netherlands.py search <query>                # Search all DNB datasets

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Filter examples:
  python dnb_netherlands.py FINANCIAL_STABILITY_Q indicator=capital
  python dnb_netherlands.py BANK_STRUCTURE classification=total
  python dnb_netherlands.py PAYMENT_TRANSACTIONS item=debit

Source: {BASE_URL}
Protocol: REST JSON (Azure APIM)
Auth: Ocp-Apim-Subscription-Key header (DNB_SUBSCRIPTION_KEY env var)
Coverage: Netherlands
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            print(json.dumps(search_datasets(query), indent=2, default=str))
        else:
            filters = {}
            for arg in sys.argv[2:]:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    filters[k] = v
            result = fetch_data(cmd, filters=filters if filters else None)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
