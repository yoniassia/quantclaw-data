#!/usr/bin/env python3
"""
Central Bank of Ireland Open Data Module

Irish financial statistics: ECB/interbank interest rates, retail lending &
deposit rates (new business + outstanding), mortgage rates, gross national debt,
official external reserves, and card payment volumes.

Data Source: https://opendata.centralbank.ie
Protocol: CKAN Datastore REST API
Auth: None (open access, CC-BY-4.0)
Refresh: Monthly (rates, reserves), Quarterly (mortgages, debt)
Coverage: Ireland / Euro Area

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

BASE_URL = "https://opendata.centralbank.ie/api/3/action"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "central_bank_ireland"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.0

# Resource UUIDs from the CBI CKAN portal
_RES_OFFICIAL_RATES = "1f1d07aa-8cd3-46ce-86a3-dac04da3eae0"
_RES_RETAIL_NEW_BIZ = "fc4dddc5-c36d-4de0-9605-076d765a0efa"
_RES_DEPOSITS_OUTSTANDING = "f10999a2-24d2-4236-a84a-2e43af482d33"
_RES_LOANS_OUTSTANDING = "120a26a9-acb6-473e-9b9a-469f9b0037eb"
_RES_MORTGAGE_RATES = "fb07a41b-15f7-4697-a7f7-ce8209d794e5"
_RES_NATIONAL_DEBT = "0ec622ab-de07-4072-a53e-959128d37a7e"
_RES_EXTERNAL_RESERVES = "67b9e745-ed6c-45b7-b328-f5d9b4b3ce81"
_RES_CARD_PAYMENTS = "48aca6f9-bfd2-40fd-b746-e93c0ee32e41"

INDICATORS = {
    # --- Eurosystem Official Interest Rates (monthly, Table B.3) ---
    "ECB_DEPOSIT_RATE": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "eurosystem_official_interest_rates__deposit_facility__per_ce",
        "date_field": "Reporting Date",
        "name": "ECB Deposit Facility Rate (% p.a.)",
        "description": "Eurosystem deposit facility rate as reported by CBI",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "ECB_REFI_RATE": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "eurosystem_official_interest_rates__main_refinancing_operati",
        "date_field": "Reporting Date",
        "name": "ECB Main Refinancing Rate (% p.a.)",
        "description": "Eurosystem main refinancing operations rate",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "ECB_MARGINAL_RATE": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "eurosystem_official_interest_rates__marginal_lending_facilit",
        "date_field": "Reporting Date",
        "name": "ECB Marginal Lending Facility Rate (% p.a.)",
        "description": "Eurosystem marginal lending facility rate",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "STR_RATE": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "interbank_market___str__per_cent_per_annum",
        "date_field": "Reporting Date",
        "name": "Euro Short-Term Rate — €STR (% p.a.)",
        "description": "Euro short-term rate, successor to EONIA",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "EURIBOR_3M": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "interbank_market__3_month_euribor__per_cent_per_annum",
        "date_field": "Reporting Date",
        "name": "3-Month Euribor (% p.a.)",
        "description": "3-month Euro interbank offered rate",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "EURIBOR_12M": {
        "resource_id": _RES_OFFICIAL_RATES,
        "field": "interbank_market__12_month_euribor__per_cent_per_annum",
        "date_field": "Reporting Date",
        "name": "12-Month Euribor (% p.a.)",
        "description": "12-month Euro interbank offered rate",
        "frequency": "monthly",
        "unit": "% p.a.",
    },

    # --- Retail Interest Rates — New Business (monthly, Table B.2.1) ---
    "MORTGAGE_RATE_NEW": {
        "resource_id": _RES_RETAIL_NEW_BIZ,
        "field": "loans_to_households_for_house_purchase__interest_rate____",
        "date_field": "Reporting date",
        "name": "New Mortgage Rate — Ireland (%)",
        "description": "Weighted avg interest rate on new house purchase loans to households",
        "frequency": "monthly",
        "unit": "%",
    },
    "CONSUMER_RATE_NEW": {
        "resource_id": _RES_RETAIL_NEW_BIZ,
        "field": "loans_to_households__for_consumer_purposes__interest_rate___",
        "date_field": "Reporting date",
        "name": "New Consumer Credit Rate — Ireland (%)",
        "description": "Weighted avg interest rate on new consumer loans to households",
        "frequency": "monthly",
        "unit": "%",
    },
    "NFC_LENDING_RATE_NEW": {
        "resource_id": _RES_RETAIL_NEW_BIZ,
        "field": "loans_to_non_financial_corporations__interest_rate____",
        "date_field": "Reporting date",
        "name": "New NFC Lending Rate — Ireland (%)",
        "description": "Weighted avg interest rate on new loans to non-financial corporations",
        "frequency": "monthly",
        "unit": "%",
    },
    "HH_DEPOSIT_RATE_NEW": {
        "resource_id": _RES_RETAIL_NEW_BIZ,
        "field": "deposits_from_households__with_agreed_maturity__interest_rat",
        "date_field": "Reporting date",
        "name": "New Household Deposit Rate — Ireland (%)",
        "description": "Interest rate on new agreed maturity deposits from households",
        "frequency": "monthly",
        "unit": "%",
    },
    "NFC_DEPOSIT_RATE_NEW": {
        "resource_id": _RES_RETAIL_NEW_BIZ,
        "field": "deposits_from_non_financial_corporations_with_agreed_maturit",
        "date_field": "Reporting date",
        "name": "New NFC Deposit Rate — Ireland (%)",
        "description": "Interest rate on new agreed maturity deposits from NFCs",
        "frequency": "monthly",
        "unit": "%",
    },

    # --- Retail Interest Rates — Outstanding Deposits (monthly, Table B.1.1) ---
    "HH_OVERNIGHT_DEPOSIT_RATE": {
        "resource_id": _RES_DEPOSITS_OUTSTANDING,
        "field": "household_deposits__overnight__interest_rate____",
        "date_field": "Reporting Date",
        "name": "Household Overnight Deposit Rate — Stock (%)",
        "description": "Interest rate on outstanding overnight deposits from households",
        "frequency": "monthly",
        "unit": "%",
    },
    "HH_TERM_DEPOSIT_RATE": {
        "resource_id": _RES_DEPOSITS_OUTSTANDING,
        "field": "household_deposits__with_agreed_maturity__up_to_2_years___in",
        "date_field": "Reporting Date",
        "name": "Household Term Deposit Rate ≤2Y — Stock (%)",
        "description": "Rate on outstanding household deposits with agreed maturity up to 2 years",
        "frequency": "monthly",
        "unit": "%",
    },

    # --- Retail Interest Rates — Outstanding Loans (monthly, Table B.1.2) ---
    "HH_OVERDRAFT_RATE": {
        "resource_id": _RES_LOANS_OUTSTANDING,
        "field": "loans_to_households__overdrafts__interest_rate____",
        "date_field": "Reporting date",
        "name": "Household Overdraft Rate — Stock (%)",
        "description": "Interest rate on outstanding overdraft facilities to households",
        "frequency": "monthly",
        "unit": "%",
    },
    "MORTGAGE_RATE_STOCK": {
        "resource_id": _RES_LOANS_OUTSTANDING,
        "field": "loans_to_households__loans_for_house_purchases_with_original_3",
        "date_field": "Reporting date",
        "name": "Mortgage Rate — Outstanding Stock, >5Y (%)",
        "description": "Rate on outstanding house purchase loans to households, original maturity over 5 years",
        "frequency": "monthly",
        "unit": "%",
    },

    # --- Mortgage Rates by Type (quarterly, Table B.3.1) ---
    "PDH_FIXED_OVER3Y_RATE": {
        "resource_id": _RES_MORTGAGE_RATES,
        "field": "principal_dwelling_houses__fixed_rate__over_3_years__rates_o",
        "date_field": "Reporting date",
        "name": "PDH Fixed Rate >3Y — Outstanding (%)",
        "description": "Rate on outstanding principal dwelling house mortgages, fixed over 3 years",
        "frequency": "quarterly",
        "unit": "%",
    },
    "PDH_TRACKER_RATE": {
        "resource_id": _RES_MORTGAGE_RATES,
        "field": "principal_dwelling_houses__floating_rate__tracker_mortgages_",
        "date_field": "Reporting date",
        "name": "PDH Tracker Mortgage Rate — Outstanding (%)",
        "description": "Rate on outstanding principal dwelling house tracker mortgages",
        "frequency": "quarterly",
        "unit": "%",
    },

    # --- Gross National Debt (quarterly, client-filtered) ---
    "GROSS_NATIONAL_DEBT": {
        "resource_id": _RES_NATIONAL_DEBT,
        "field": "outstanding_amount_EUR_million",
        "date_field": "reference_date",
        "filters": {"item": "Gross National Debt", "denomination": "All denominations", "residual_maturity": "Total"},
        "client_filter": {"item": "Gross National Debt", "denomination": "All denominations", "residual_maturity": "Total"},
        "name": "Gross National Debt — Ireland (EUR mn)",
        "description": "Total gross national debt outstanding, all denominations",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },

    # --- Official External Reserves (monthly, client-filtered) ---
    "RESERVE_ASSETS_TOTAL": {
        "resource_id": _RES_EXTERNAL_RESERVES,
        "field": "Outstanding_Amount_in_EUR_Millions",
        "date_field": "Reference_Date",
        "filters": {"Item_Name": "Reserve Assets"},
        "client_filter": {"Item_Name": "Reserve Assets"},
        "name": "Official Reserve Assets — Ireland (EUR mn)",
        "description": "Total official external reserve assets held by Ireland",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "FX_RESERVES": {
        "resource_id": _RES_EXTERNAL_RESERVES,
        "field": "Outstanding_Amount_in_EUR_Millions",
        "date_field": "Reference_Date",
        "filters": {"Item_Name": "Foreign Exchange"},
        "client_filter": {"Item_Name": "Foreign Exchange"},
        "name": "Foreign Exchange Reserves — Ireland (EUR mn)",
        "description": "Foreign exchange component of official reserves",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "GOLD_RESERVES": {
        "resource_id": _RES_EXTERNAL_RESERVES,
        "field": "Outstanding_Amount_in_EUR_Millions",
        "date_field": "Reference_Date",
        "filters": {"Item_Name": "Monetary Gold"},
        "client_filter": {"Item_Name": "Monetary Gold"},
        "name": "Monetary Gold Reserves — Ireland (EUR mn)",
        "description": "Monetary gold component of official reserves",
        "frequency": "monthly",
        "unit": "EUR mn",
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


def _datastore_search(resource_id: str, limit: int = 60, sort: str = "_id desc",
                      filters: Optional[Dict] = None, retries: int = 2) -> Dict:
    """Query the CKAN datastore_search endpoint with retry on transient errors.

    Each request uses a fresh session with Connection: close to defeat the CBI
    portal's CDN caching, which returns stale responses over keep-alive.
    """
    url = f"{BASE_URL}/datastore_search"
    params = {
        "resource_id": resource_id,
        "limit": limit,
        "sort": sort,
        "include_total": "true",
    }
    if filters:
        params["filters"] = json.dumps(filters)
    headers = {"Connection": "close", "Cache-Control": "no-cache, no-store"}

    last_error = ""
    for attempt in range(retries + 1):
        try:
            sess = requests.Session()
            sess.headers.update(headers)
            resp = sess.get(url, params=params, timeout=REQUEST_TIMEOUT)
            sess.close()

            if resp.status_code == 202 or (resp.status_code == 200 and not resp.text.strip()):
                last_error = "Server returned 202 (rate limited / queued)"
                time.sleep(2.0 * (attempt + 1))
                continue

            resp.raise_for_status()
            body = resp.json()
            if not body.get("success"):
                last_error = body.get("error", {}).get("message", "API returned success=false")
                time.sleep(0.5)
                continue
            result = body["result"]
            returned_rid = result.get("resource_id", "")
            if returned_rid and returned_rid != resource_id:
                last_error = f"CDN returned wrong resource {returned_rid}"
                time.sleep(1.0)
                continue
            return {"success": True, "result": result}
        except requests.Timeout:
            last_error = "Request timed out"
        except requests.ConnectionError:
            last_error = "Connection failed"
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            last_error = f"HTTP {status}"
        except Exception as e:
            last_error = str(e)
        if attempt < retries:
            time.sleep(1.0 * (attempt + 1))

    return {"success": False, "error": last_error}


def _parse_numeric(val) -> Optional[float]:
    """Coerce a datastore value to float, handling comma-formatted strings."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").strip()
        if cleaned in ("", "..", "n/a", "-"):
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _extract_series(records: List[Dict], field: str, date_field: str) -> List[Dict]:
    """Extract (period, value) pairs from datastore records, newest first."""
    series = []
    for rec in records:
        val = _parse_numeric(rec.get(field))
        period_raw = rec.get(date_field, "")
        if val is None or not period_raw:
            continue
        period = str(period_raw)[:10]
        series.append({"period": period, "value": val})
    series.sort(key=lambda x: x["period"], reverse=True)
    return series


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

    limit = 120 if cfg["frequency"] == "monthly" else 60
    filters = cfg.get("filters")

    result = _datastore_search(
        resource_id=cfg["resource_id"],
        limit=limit,
        sort="_id desc",
        filters=filters,
    )
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    records = result["result"].get("records", [])
    if not records:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No records returned"}

    observations = _extract_series(records, cfg["field"], cfg["date_field"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": f"No numeric values found in field '{cfg['field']}'"}

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
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/datastore_search?resource_id={cfg['resource_id']}",
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
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators.

    Batches API calls by (resource_id, filters) to minimise requests against the
    CBI CKAN portal, which applies aggressive rate limits.
    """
    if indicator:
        return fetch_data(indicator)

    groups: Dict[str, List[str]] = {}
    for key, cfg in INDICATORS.items():
        group_key = cfg["resource_id"]
        groups.setdefault(group_key, []).append(key)

    results = {}
    errors = []
    call_count = 0

    for group_key, indicator_keys in groups.items():
        first_cfg = INDICATORS[indicator_keys[0]]
        resource_id = first_cfg["resource_id"]
        has_client_filter = any(INDICATORS[k].get("client_filter") for k in indicator_keys)
        limit = 500 if has_client_filter else (120 if first_cfg["frequency"] == "monthly" else 60)

        if call_count > 0 and call_count % 5 == 0:
            time.sleep(8.0)

        api_result = _datastore_search(
            resource_id=resource_id,
            limit=limit,
            sort="_id desc",
            retries=3,
        )
        call_count += 1
        time.sleep(REQUEST_DELAY)

        if not api_result["success"]:
            for key in indicator_keys:
                errors.append({"indicator": key, "error": api_result.get("error", "unknown")})
            continue

        records = api_result["result"].get("records", [])
        if not records:
            for key in indicator_keys:
                errors.append({"indicator": key, "error": "No records returned"})
            continue

        for key in indicator_keys:
            cfg = INDICATORS[key]
            cache_params = {"indicator": key, "start": None, "end": None}
            cp = _cache_path(key, _params_hash(cache_params))
            cached = _read_cache(cp)
            if cached:
                cached.pop("_cached_at", None)
                if cached.get("success"):
                    results[key] = {
                        "name": cached["name"],
                        "value": cached["latest_value"],
                        "period": cached["latest_period"],
                        "unit": cached["unit"],
                    }
                else:
                    errors.append({"indicator": key, "error": cached.get("error", "unknown")})
                continue

            filtered_records = records
            client_filter = cfg.get("client_filter")
            if client_filter:
                filtered_records = [
                    r for r in records
                    if all(r.get(fk) == fv for fk, fv in client_filter.items())
                ]

            observations = _extract_series(filtered_records, cfg["field"], cfg["date_field"])
            if not observations:
                errors.append({"indicator": key, "error": f"No numeric values in field '{cfg['field']}'"})
                continue

            period_change = period_change_pct = None
            if len(observations) >= 2:
                latest_v = observations[0]["value"]
                prev_v = observations[1]["value"]
                if prev_v and prev_v != 0:
                    period_change = round(latest_v - prev_v, 4)
                    period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

            response = {
                "success": True,
                "indicator": key,
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
                "source": f"{BASE_URL}/datastore_search?resource_id={cfg['resource_id']}",
                "timestamp": datetime.now().isoformat(),
            }
            _write_cache(cp, response)

            results[key] = {
                "name": cfg["name"],
                "value": observations[0]["value"],
                "period": observations[0]["period"],
                "unit": cfg["unit"],
            }

    return {
        "success": True,
        "source": "Central Bank of Ireland Open Data",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_datasets() -> List[Dict]:
    """List all available datasets on the CBI open data portal."""
    url = f"{BASE_URL}/package_list"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        if body.get("success"):
            return [{"dataset": name} for name in body["result"]]
        return []
    except Exception:
        return []


# --- CLI ---

def _print_help():
    print("""
Central Bank of Ireland Open Data Module

Usage:
  python central_bank_ireland.py                  # Latest values for all indicators
  python central_bank_ireland.py <INDICATOR>       # Fetch specific indicator
  python central_bank_ireland.py list              # List available indicators
  python central_bank_ireland.py datasets          # Discover all CBI datasets

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: CKAN Datastore REST
Coverage: Ireland / Euro Area
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "datasets":
            print(json.dumps(discover_datasets(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
