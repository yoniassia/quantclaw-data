#!/usr/bin/env python3
"""
Banco de Portugal BPstat Module

Portuguese central bank statistics: MFI interest rates (lending/deposit),
balance of payments, exchange rates, banking system indicators, and
financial stability indicators.

Data Source: https://bpstat.bportugal.pt/data/v1
Protocol: REST (JSON-stat 2.0)
Auth: None (open access)
Refresh: Daily (FX rates), Monthly (interest rates, BoP, banking)
Coverage: Portugal

Author: QUANTCLAW DATA Build Agent
Initiative: 0011
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://bpstat.bportugal.pt/data/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "banco_de_portugal"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- MFI Interest Rates (monthly, stocks) ---
    "IR_LOANS_NFC": {
        "series_id": 12519749,
        "domain_id": 21,
        "dataset_id": "851facff504532e95cf096ca9c6a8b9a",
        "name": "Lending Rate — Non-Financial Corporations (%)",
        "description": "Interest rate on outstanding loans to non-financial sector (MU excl. GG)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_LOANS_HOUSING": {
        "series_id": 12519762,
        "domain_id": 21,
        "dataset_id": "851facff504532e95cf096ca9c6a8b9a",
        "name": "Lending Rate — Housing Loans (%)",
        "description": "Interest rate on outstanding housing loans to individuals (MU)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_LOANS_CONSUMER": {
        "series_id": 12519758,
        "domain_id": 21,
        "dataset_id": "851facff504532e95cf096ca9c6a8b9a",
        "name": "Lending Rate — Consumer Credit (%)",
        "description": "Interest rate on outstanding consumer and other purpose loans to individuals (MU)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_DEPOSITS_AGREED": {
        "series_id": 12519712,
        "domain_id": 21,
        "dataset_id": "ec7b2a0f066656833f1013b3a2f9f189",
        "name": "Deposit Rate — Agreed Maturity, Non-Financial Sector (%)",
        "description": "Interest rate on deposits with agreed maturity, non-financial sector (MU excl. GG)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_DEPOSITS_OVERNIGHT_HH": {
        "series_id": 12519717,
        "domain_id": 21,
        "dataset_id": "c4db40b75370917aaf045d1cff74c142",
        "name": "Deposit Rate — Overnight, Individuals (%)",
        "description": "Interest rate on overnight deposits from individuals (MU)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_NEWBIZ_HOUSING": {
        "series_id": 12533735,
        "domain_id": 21,
        "dataset_id": "6eaa8db94523f54733dddc22479c11a4",
        "name": "New Business Rate — Housing Loans (%)",
        "description": "Interest rate on new housing loans to individuals (MU)",
        "frequency": "monthly",
        "unit": "%",
    },
    "IR_NEWBIZ_CONSUMER": {
        "series_id": 12533734,
        "domain_id": 21,
        "dataset_id": "6eaa8db94523f54733dddc22479c11a4",
        "name": "New Business Rate — Consumer Credit (%)",
        "description": "Interest rate on new consumer and other purpose loans to individuals (MU)",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Balance of Payments (monthly) ---
    "BOP_CURRENT_ACCOUNT": {
        "series_id": 12517387,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Current Account Balance (EUR mn)",
        "description": "Portugal current account balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_GOODS_SERVICES": {
        "series_id": 12510231,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Goods & Services Balance (EUR mn)",
        "description": "Portugal goods and services account balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_GOODS": {
        "series_id": 12509543,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Goods Balance (EUR mn)",
        "description": "Portugal goods (trade) balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_SERVICES": {
        "series_id": 12514417,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Services Balance (EUR mn)",
        "description": "Portugal services account balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_PRIMARY_INCOME": {
        "series_id": 12510147,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Primary Income Balance (EUR mn)",
        "description": "Portugal primary income balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_CAPITAL_ACCOUNT": {
        "series_id": 12512248,
        "domain_id": 3,
        "dataset_id": "36a06e0b7d0f57014851b37e204234cc",
        "name": "Capital Account Balance (EUR mn)",
        "description": "Portugal capital account balance, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    # --- Exchange Rates (daily, EUR-based) ---
    "FX_EUR_USD": {
        "series_id": 12531971,
        "domain_id": 29,
        "dataset_id": "23e0cdd56bddb4ad3016a9c3ad63a539",
        "name": "EUR/USD Exchange Rate",
        "description": "Euro vs US Dollar, daily reference rate",
        "frequency": "daily",
        "unit": "USD per EUR",
    },
    "FX_EUR_GBP": {
        "series_id": 12531970,
        "domain_id": 29,
        "dataset_id": "23e0cdd56bddb4ad3016a9c3ad63a539",
        "name": "EUR/GBP Exchange Rate",
        "description": "Euro vs British Pound, daily reference rate",
        "frequency": "daily",
        "unit": "GBP per EUR",
    },
    "FX_EUR_JPY": {
        "series_id": 12531951,
        "domain_id": 29,
        "dataset_id": "23e0cdd56bddb4ad3016a9c3ad63a539",
        "name": "EUR/JPY Exchange Rate",
        "description": "Euro vs Japanese Yen, daily reference rate",
        "frequency": "daily",
        "unit": "JPY per EUR",
    },
    "FX_EUR_CHF": {
        "series_id": 12531968,
        "domain_id": 29,
        "dataset_id": "23e0cdd56bddb4ad3016a9c3ad63a539",
        "name": "EUR/CHF Exchange Rate",
        "description": "Euro vs Swiss Franc, daily reference rate",
        "frequency": "daily",
        "unit": "CHF per EUR",
    },
    "FX_EUR_CNY": {
        "series_id": 12531938,
        "domain_id": 29,
        "dataset_id": "23e0cdd56bddb4ad3016a9c3ad63a539",
        "name": "EUR/CNY Exchange Rate",
        "description": "Euro vs Chinese Yuan Renminbi, daily reference rate",
        "frequency": "daily",
        "unit": "CNY per EUR",
    },
    # --- Banking System Indicators (semi-annual) ---
    "BANK_ROA": {
        "series_id": 12504542,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "Banking Sector — Return on Assets (ROA)",
        "description": "Portuguese banking sector return on assets",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "BANK_CET1": {
        "series_id": 12504543,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "Banking Sector — CET1 Ratio",
        "description": "Portuguese banking sector Common Equity Tier 1 ratio",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "BANK_NPL_RATIO": {
        "series_id": 12504544,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "Banking Sector — NPL Ratio",
        "description": "Portuguese banking sector non-performing loans ratio",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "BANK_LOAN_TO_DEPOSIT": {
        "series_id": 12562721,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "Banking Sector — Loan-to-Deposit Ratio",
        "description": "Portuguese banking sector loan-to-deposit ratio",
        "frequency": "semi-annual",
        "unit": "%",
    },
    # --- FSI Capital Adequacy ---
    "FSI_TIER1_RATIO": {
        "series_id": 12504564,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "FSI — Tier 1 Capital to RWA",
        "description": "Regulatory Tier 1 capital to risk-weighted assets",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "FSI_NPL_TO_LOANS": {
        "series_id": 12504572,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "FSI — NPL to Total Gross Loans",
        "description": "Non-performing loans to total gross loans (asset quality)",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "FSI_ROA": {
        "series_id": 12504575,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "FSI — Return on Assets",
        "description": "FSI earnings and profitability: return on assets",
        "frequency": "semi-annual",
        "unit": "%",
    },
    "FSI_LIQUIDITY": {
        "series_id": 12504578,
        "domain_id": 59,
        "dataset_id": "b8cc662879c9f7b0f3faf89c7871fc38",
        "name": "FSI — Liquid Assets to Short-Term Liabilities",
        "description": "Liquid assets to short-term liabilities ratio",
        "frequency": "semi-annual",
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


def _parse_jsonstat(raw: Dict, series_id: int) -> List[Dict]:
    """Extract date/value pairs from a BPstat JSON-stat 2.0 response."""
    try:
        values = raw.get("value", [])
        statuses = raw.get("status", [])
        ref_dim = raw.get("dimension", {}).get("reference_date", {})
        dates = ref_dim.get("category", {}).get("index", [])

        if not values or not dates:
            return []

        series_list = raw.get("extension", {}).get("series", [])
        target_series = None
        for s in series_list:
            if s["id"] == series_id:
                target_series = s
                break

        dims = raw.get("id", [])
        sizes = raw.get("size", [])
        if not dims or not sizes:
            return []

        date_dim_idx = dims.index("reference_date")

        if len(series_list) == 1:
            results = []
            for i, date_str in enumerate(dates):
                if i < len(values) and values[i] is not None:
                    results.append({
                        "time_period": date_str,
                        "value": float(values[i]),
                        "status": statuses[i] if i < len(statuses) else None,
                    })
            return sorted(results, key=lambda x: x["time_period"], reverse=True)

        # Multi-series: compute flat index offset for the target series
        if target_series is None:
            return []

        target_cats = {dc["dimension_id"]: str(dc["category_id"]) for dc in target_series["dimension_category"]}
        dim_offsets = {}
        for dim_idx, dim_key in enumerate(dims):
            if dim_key == "reference_date":
                continue
            dim_data = raw["dimension"].get(dim_key, {})
            cat_index = dim_data.get("category", {}).get("index", [])
            target_cat = target_cats.get(int(dim_key) if dim_key.isdigit() else dim_key)
            if target_cat is not None and target_cat in cat_index:
                dim_offsets[dim_idx] = cat_index.index(target_cat)
            else:
                dim_offsets[dim_idx] = 0

        results = []
        for t_idx, date_str in enumerate(dates):
            flat_idx = 0
            for d_pos in range(len(dims)):
                stride = 1
                for s_pos in range(d_pos + 1, len(dims)):
                    stride *= sizes[s_pos]
                if d_pos == date_dim_idx:
                    flat_idx += t_idx * stride
                else:
                    flat_idx += dim_offsets.get(d_pos, 0) * stride

            if flat_idx < len(values) and values[flat_idx] is not None:
                results.append({
                    "time_period": date_str,
                    "value": float(values[flat_idx]),
                    "status": statuses[flat_idx] if flat_idx < len(statuses) else None,
                })

        return sorted(results, key=lambda x: x["time_period"], reverse=True)
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(domain_id: int, dataset_id: str, series_id: int, last_n: int = 60) -> Dict:
    url = f"{BASE_URL}/domains/{domain_id}/datasets/{dataset_id}/"
    params = {
        "lang": "EN",
        "series_ids": str(series_id),
        "obs_last_n": last_n,
    }
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
        if status == 404:
            return {"success": False, "error": f"Series not found (HTTP 404)"}
        if status == 429:
            return {"success": False, "error": "Rate limited (HTTP 429) — retry after a few minutes"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series with optional date range."""
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

    last_n = 260 if cfg["frequency"] == "daily" else 60

    result = _api_request(cfg["domain_id"], cfg["dataset_id"], cfg["series_id"], last_n=last_n)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_jsonstat(result["data"], cfg["series_id"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed from response"}

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
        "source": f"{BASE_URL}/domains/{cfg['domain_id']}/datasets/{cfg['dataset_id']}/?series_ids={cfg['series_id']}",
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
            "series_id": v["series_id"],
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
        "source": "Banco de Portugal BPstat",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_series(domain_id: int, dataset_id: str, max_pages: int = 3) -> List[Dict]:
    """Discover available series in a given domain/dataset."""
    all_series = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/domains/{domain_id}/datasets/{dataset_id}/"
        params = {"lang": "EN", "obs_last_n": 1, "page_size": 50, "page": page}
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            series = data.get("extension", {}).get("series", [])
            if not series:
                break
            for s in series:
                all_series.append({"id": s["id"], "label": s["label"]})
            time.sleep(REQUEST_DELAY)
        except Exception:
            break
    return all_series


# --- CLI ---

def _print_help():
    print("""
Banco de Portugal BPstat Module (Initiative 0011)

Usage:
  python banco_de_portugal.py                         # Latest values for all indicators
  python banco_de_portugal.py <INDICATOR>              # Fetch specific indicator
  python banco_de_portugal.py list                     # List available indicators
  python banco_de_portugal.py discover <DOMAIN> <DATASET>  # Discover series in dataset

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON-stat 2.0)
Coverage: Portugal
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "discover" and len(sys.argv) >= 4:
            series = discover_series(int(sys.argv[2]), sys.argv[3])
            print(json.dumps(series, indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
