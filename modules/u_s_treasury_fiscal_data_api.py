#!/usr/bin/env python3
"""
U.S. Treasury Fiscal Data API Module

Query U.S. Treasury fiscal data including interest rates, debt info,
auction results, and Treasury securities data via the open
Fiscal Data API (no API key required).

Data Source:
- https://fiscaldata.treasury.gov/api-documentation/
- Base: https://api.fiscaldata.treasury.gov/services/api/fiscal_service

Endpoints covered:
- Average Interest Rates on U.S. Treasury Securities
- Treasury Securities Auctions Data
- Debt to the Penny (total public debt)
- Federal Debt Held by Foreign Investors
- Statement of the Public Debt (Monthly)

Refresh: Daily / Monthly depending on dataset
Coverage: Historical + current

Author: QUANTCLAW DATA NightBuilder
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ── API Configuration ───────────────────────────────────────────────

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Endpoint paths (relative to BASE_URL)
ENDPOINTS = {
    "interest_rates": "/v2/accounting/od/avg_interest_rates",
    "debt_to_penny": "/v2/accounting/od/debt_to_penny",
    "auctions": None,  # Uses TreasuryDirect API instead
    "treasury_statement": "/v1/accounting/mts/mts_table_1",
    "savings_bonds": "/v2/accounting/od/savings_bonds_report",
    "slgs_statistics": "/v2/accounting/od/slgs_statistics",
}

TIMEOUT = 15


# ── Internal Helpers ────────────────────────────────────────────────

def _fetch(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Generic GET against the Fiscal Data API.
    Returns the full JSON response dict or an error dict.
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params or {}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "url": url}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"HTTP {exc.response.status_code}", "detail": exc.response.text[:500], "url": url}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc), "url": url}


def _build_params(
    fields: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
    sort: Optional[str] = None,
    page_size: int = 100,
    page_number: int = 1,
) -> Dict:
    """Build query-parameter dict for the Fiscal Data API."""
    params: Dict[str, str] = {
        "page[size]": str(page_size),
        "page[number]": str(page_number),
    }
    if fields:
        params["fields"] = ",".join(fields)
    if filters:
        params["filter"] = ",".join(filters)
    if sort:
        params["sort"] = sort
    return params


# ── Public Functions ────────────────────────────────────────────────

def get_interest_rates(
    start_date: Optional[str] = None,
    security_desc: Optional[str] = None,
    page_size: int = 100,
) -> Dict:
    """
    Fetch average interest rates on U.S. Treasury securities.

    Args:
        start_date: ISO date string (YYYY-MM-DD). Defaults to 90 days ago.
        security_desc: Filter by security description (e.g. 'Treasury Notes').
        page_size: Number of records per page (max 10000).

    Returns:
        dict with 'data' list of rate records or 'error'.
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")

    filters = [f"record_date:gte:{start_date}"]
    if security_desc:
        filters.append(f"security_desc:eq:{security_desc}")

    fields = ["record_date", "security_desc", "security_type_desc", "avg_interest_rate_amt"]
    params = _build_params(fields=fields, filters=filters, sort="-record_date", page_size=page_size)
    return _fetch(ENDPOINTS["interest_rates"], params)


def get_latest_interest_rates() -> List[Dict]:
    """
    Return the most recent set of average interest rates (one record per security type).

    Returns:
        list of dicts with keys: security_desc, avg_interest_rate_amt, record_date
        or a single-element list with an error dict.
    """
    result = get_interest_rates(page_size=50)
    if "error" in result:
        return [result]
    data = result.get("data", [])
    if not data:
        return [{"error": "No data returned"}]

    # Get the latest record_date and filter to only that date
    latest_date = data[0].get("record_date")
    return [r for r in data if r.get("record_date") == latest_date]


def get_debt_to_penny(
    start_date: Optional[str] = None,
    page_size: int = 30,
) -> Dict:
    """
    Total public debt outstanding (Debt to the Penny).

    Args:
        start_date: ISO date string. Defaults to 90 days ago.
        page_size: Records per page.

    Returns:
        dict with 'data' list containing debt records.
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")

    fields = [
        "record_date",
        "tot_pub_debt_out_amt",
        "intragov_hold_amt",
        "debt_held_public_amt",
    ]
    filters = [f"record_date:gte:{start_date}"]
    params = _build_params(fields=fields, filters=filters, sort="-record_date", page_size=page_size)
    return _fetch(ENDPOINTS["debt_to_penny"], params)


def get_latest_debt() -> Dict:
    """
    Return the most recent total public debt figure.

    Returns:
        dict with total_public_debt, debt_held_by_public, intragovernmental,
        record_date — or an error dict.
    """
    result = get_debt_to_penny(page_size=1)
    if "error" in result:
        return result
    data = result.get("data", [])
    if not data:
        return {"error": "No debt data returned"}
    rec = data[0]
    return {
        "record_date": rec.get("record_date"),
        "total_public_debt": rec.get("tot_pub_debt_out_amt"),
        "debt_held_by_public": rec.get("debt_held_public_amt"),
        "intragovernmental": rec.get("intragov_hold_amt"),
    }


def get_treasury_auctions(
    security_type: Optional[str] = None,
    page_size: int = 10,
) -> Dict:
    """
    Fetch recent Treasury securities auction results via TreasuryDirect API.

    Args:
        security_type: e.g. 'Bill', 'Note', 'Bond', 'TIPS', 'FRN'.
        page_size: Number of results (max ~250).

    Returns:
        dict with 'data' list of auction records or 'error'.
    """
    url = "https://www.treasurydirect.gov/TA_WS/securities/search"
    params = {"format": "json", "pagesize": str(page_size)}
    if security_type:
        params["type"] = security_type
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        raw = resp.json()
        # Normalize to list
        records = raw if isinstance(raw, list) else [raw]
        # Extract key fields
        data = []
        for r in records:
            data.append({
                "type": r.get("type", ""),
                "term": r.get("term") or r.get("securityTermWeekYear", ""),
                "auction_date": r.get("auctionDate", ""),
                "issue_date": r.get("issueDate", ""),
                "high_yield": r.get("highYield", ""),
                "high_price": r.get("pricePer100", ""),
                "bid_to_cover": r.get("bidToCoverRatio", ""),
                "total_accepted": r.get("totalAccepted", ""),
                "cusip": r.get("cusip", ""),
                "offering_amount": r.get("offeringAmount", ""),
            })
        return {"data": data}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc), "url": url}


def get_treasury_statement(
    start_date: Optional[str] = None,
    page_size: int = 50,
) -> Dict:
    """
    Monthly Treasury Statement (receipts, outlays, deficit/surplus).

    Args:
        start_date: ISO date. Defaults to 365 days ago.
        page_size: Records per page.

    Returns:
        dict with 'data' list of monthly statement records or 'error'.
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")

    fields = [
        "record_date",
        "record_fiscal_year",
        "record_fiscal_quarter",
        "record_calendar_month",
        "current_month_receipts_amt",
        "current_month_outlays_amt",
        "current_month_surplus_deficit_amt",
    ]
    filters = [f"record_date:gte:{start_date}"]
    params = _build_params(fields=fields, filters=filters, sort="-record_date", page_size=page_size)
    return _fetch(ENDPOINTS["treasury_statement"], params)


def search_interest_rates_by_security(security_keyword: str, start_date: Optional[str] = None) -> List[Dict]:
    """
    Search interest rates by security description keyword.

    Args:
        security_keyword: Partial match keyword (e.g. 'Notes', 'Bills', 'Bonds', 'TIPS').
        start_date: ISO date. Defaults to 180 days ago.

    Returns:
        list of matching rate records.
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")

    result = get_interest_rates(start_date=start_date, page_size=500)
    if "error" in result:
        return [result]
    data = result.get("data", [])
    keyword_lower = security_keyword.lower()
    return [r for r in data if keyword_lower in r.get("security_desc", "").lower()]


def get_fiscal_summary() -> Dict:
    """
    High-level fiscal summary: latest debt + latest interest rates snapshot.

    Returns:
        dict with 'debt' and 'interest_rates' keys.
    """
    debt = get_latest_debt()
    rates = get_latest_interest_rates()
    return {
        "debt": debt,
        "interest_rates": rates,
    }


# ── CLI Quick Test ──────────────────────────────────────────────────

if __name__ == "__main__":
    import json as _json

    print("=== Latest Interest Rates ===")
    rates = get_latest_interest_rates()
    for r in rates[:5]:
        print(f"  {r.get('security_desc', 'N/A'):40s}  {r.get('avg_interest_rate_amt', 'N/A')}%  ({r.get('record_date', '')})")

    print("\n=== Latest Debt ===")
    debt = get_latest_debt()
    print(f"  Total: ${debt.get('total_public_debt', 'N/A')}")
    print(f"  Date:  {debt.get('record_date', 'N/A')}")

    print("\n=== Recent Auctions (Notes) ===")
    auctions = get_treasury_auctions(security_type="Note", page_size=5)
    for a in auctions.get("data", [])[:3]:
        print(f"  {a.get('security_term', 'N/A'):15s}  Yield: {a.get('high_yield', 'N/A')}  B/C: {a.get('bid_to_cover_ratio', 'N/A')}  ({a.get('auction_date', '')})")
