"""
U.S. Treasury Fiscal Data API — Federal Financial Data

Data Source: U.S. Department of the Treasury, Bureau of the Fiscal Service
Base URL: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/
Free: Yes (no API key, no registration required)
Format: JSON (default), CSV, XML

Provides:
- National debt (total public debt outstanding)
- Treasury interest rates and yield curves
- Federal revenue and spending (Monthly Treasury Statement)
- Exchange rates (Treasury reporting rates)
- Federal debt held by the public vs. intragovernmental
- Daily Treasury statement data
- Savings bonds rates and data
- Federal budget surplus/deficit

Usage:
    from modules.u_s__treasury_fiscal_data_api import *
    debt = get_total_public_debt()
    rates = get_treasury_interest_rates()
    exchange = get_exchange_rates("Canada-Dollar")
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import json

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/treasury_fiscal")
os.makedirs(CACHE_DIR, exist_ok=True)

# Common endpoints
ENDPOINTS = {
    "debt_outstanding": "/v2/accounting/od/debt_outstanding",
    "debt_to_penny": "/v2/accounting/od/debt_to_penny",
    "interest_rates": "/v2/accounting/od/avg_interest_rates",
    "exchange_rates": "/v1/accounting/od/rates_of_exchange",
    "mts_revenue": "/v1/accounting/mts/mts_table_4",
    "mts_spending": "/v1/accounting/mts/mts_table_5",
    "mts_summary": "/v1/accounting/mts/mts_table_1",
    "dts_deposits": "/v1/accounting/dts/dts_table_1",
    "dts_withdrawals": "/v1/accounting/dts/dts_table_2",
    "dts_operating_balance": "/v1/accounting/dts/operating_cash_balance",
    "savings_bonds": "/v2/accounting/od/sb_value",
    "treasury_securities": "/v2/accounting/od/securities_outstanding",
    "federal_debt_held_public": "/v2/accounting/od/debt_held_public",
    "yield_curve": "/v2/accounting/od/avg_interest_rates",
    "statement_net_cost": "/v2/accounting/od/statement_net_cost",
    "record_setting_auction": "/v2/accounting/od/record_setting_auction",
}


def _request(endpoint: str, params: Optional[Dict] = None, page_size: int = 100) -> Dict:
    """
    Make a GET request to the Treasury Fiscal Data API.

    Args:
        endpoint: API endpoint path (e.g., /v2/accounting/od/debt_to_penny)
        params: Optional query parameters dict
        page_size: Number of results per page (default 100, max 10000)

    Returns:
        Full JSON response as dict with 'data', 'meta', 'links' keys.

    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On non-200 responses
    """
    url = f"{BASE_URL}{endpoint}"
    query_params = {"page[size]": str(page_size)}
    if params:
        query_params.update(params)

    resp = requests.get(url, params=query_params, timeout=30)
    if resp.status_code != 200:
        raise ValueError(f"Treasury API returned {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def _cache_get(key: str, max_age_hours: int = 24) -> Optional[Any]:
    """Read from cache if fresh enough."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=max_age_hours):
            with open(cache_file) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data: Any) -> None:
    """Write data to cache."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    with open(cache_file, "w") as f:
        json.dump(data, f)


def get_total_public_debt(recent_days: int = 30) -> Dict:
    """
    Get total public debt outstanding (debt to the penny).

    Args:
        recent_days: Number of recent days to fetch (default 30)

    Returns:
        Dict with keys:
            - latest: Most recent debt record
            - history: List of recent records with record_date, tot_pub_debt_out_amt, etc.
            - meta: API metadata
    """
    cached = _cache_get("debt_to_penny", max_age_hours=12)
    if cached:
        return cached

    start_date = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
    }
    result = _request(ENDPOINTS["debt_to_penny"], params)
    data = result.get("data", [])

    output = {
        "latest": data[0] if data else None,
        "history": data,
        "meta": result.get("meta", {}),
        "source": "U.S. Treasury Fiscal Data API",
    }
    _cache_set("debt_to_penny", output)
    return output


def get_debt_breakdown(date: Optional[str] = None) -> Dict:
    """
    Get breakdown of public debt: held by public vs. intragovernmental.

    Args:
        date: Optional date string (YYYY-MM-DD). If None, gets most recent.

    Returns:
        Dict with debt breakdown including:
            - debt_held_public_amt
            - intragov_hold_amt
            - tot_pub_debt_out_amt
            - record_date
    """
    params = {"sort": "-record_date", "page[size]": "1"}
    if date:
        params["filter"] = f"record_date:eq:{date}"

    result = _request(ENDPOINTS["debt_to_penny"], params)
    data = result.get("data", [])

    if not data:
        return {"error": "No data found", "date_requested": date}

    record = data[0]
    return {
        "record_date": record.get("record_date"),
        "total_public_debt": record.get("tot_pub_debt_out_amt"),
        "debt_held_by_public": record.get("debt_held_public_amt"),
        "intragovernmental_holdings": record.get("intragov_hold_amt"),
        "source": "U.S. Treasury Fiscal Data - Debt to the Penny",
    }


def get_treasury_interest_rates(security_type: Optional[str] = None, recent_months: int = 3) -> Dict:
    """
    Get average interest rates on Treasury securities.

    Args:
        security_type: Filter by security type (e.g., "Treasury Bonds", "Treasury Notes")
        recent_months: Number of recent months (default 3)

    Returns:
        Dict with interest rate data including rates by security type and date.
    """
    start_date = (datetime.now() - timedelta(days=recent_months * 31)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": "500",
    }
    if security_type:
        params["filter"] += f",security_type_desc:eq:{security_type}"

    result = _request(ENDPOINTS["interest_rates"], params)
    data = result.get("data", [])

    return {
        "records": data,
        "count": len(data),
        "meta": result.get("meta", {}),
        "source": "U.S. Treasury Fiscal Data - Average Interest Rates",
    }


def get_exchange_rates(
    currency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Get Treasury reporting rates of exchange (foreign currency to USD).

    Args:
        currency: Currency description filter (e.g., "Canada-Dollar", "Euro Zone-Euro")
        start_date: Start date (YYYY-MM-DD). Defaults to 1 year ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns:
        Dict with exchange rate records.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    filters = [f"record_date:gte:{start_date}"]
    if end_date:
        filters.append(f"record_date:lte:{end_date}")
    if currency:
        filters.append(f"country_currency_desc:eq:{currency}")

    params = {
        "filter": ",".join(filters),
        "sort": "-record_date",
        "fields": "country_currency_desc,exchange_rate,record_date,effective_date",
    }

    result = _request(ENDPOINTS["exchange_rates"], params, page_size=500)
    data = result.get("data", [])

    return {
        "records": data,
        "count": len(data),
        "currency_filter": currency,
        "date_range": {"start": start_date, "end": end_date or "latest"},
        "source": "U.S. Treasury Fiscal Data - Rates of Exchange",
    }


def get_monthly_treasury_statement(
    table: str = "summary",
    fiscal_year: Optional[int] = None,
    recent_months: int = 12,
) -> Dict:
    """
    Get Monthly Treasury Statement (MTS) data: revenue, spending, or summary.

    Args:
        table: One of 'summary', 'revenue', 'spending'
        fiscal_year: Optional fiscal year filter (e.g., 2024)
        recent_months: Number of recent months to fetch (default 12)

    Returns:
        Dict with MTS data records.
    """
    endpoint_map = {
        "summary": ENDPOINTS["mts_summary"],
        "revenue": ENDPOINTS["mts_revenue"],
        "spending": ENDPOINTS["mts_spending"],
    }
    endpoint = endpoint_map.get(table, ENDPOINTS["mts_summary"])

    start_date = (datetime.now() - timedelta(days=recent_months * 31)).strftime("%Y-%m-%d")
    filters = [f"record_date:gte:{start_date}"]
    if fiscal_year:
        filters.append(f"record_fiscal_year:eq:{fiscal_year}")

    params = {
        "filter": ",".join(filters),
        "sort": "-record_date",
    }

    result = _request(endpoint, params, page_size=500)
    data = result.get("data", [])

    return {
        "table": table,
        "records": data,
        "count": len(data),
        "meta": result.get("meta", {}),
        "source": f"U.S. Treasury - Monthly Treasury Statement ({table})",
    }


def get_daily_treasury_statement(
    report_type: str = "operating_balance",
    recent_days: int = 30,
) -> Dict:
    """
    Get Daily Treasury Statement (DTS) data.

    Args:
        report_type: One of 'operating_balance', 'deposits', 'withdrawals'
        recent_days: Number of recent days (default 30)

    Returns:
        Dict with daily treasury statement records.
    """
    endpoint_map = {
        "operating_balance": ENDPOINTS["dts_operating_balance"],
        "deposits": ENDPOINTS["dts_deposits"],
        "withdrawals": ENDPOINTS["dts_withdrawals"],
    }
    endpoint = endpoint_map.get(report_type, ENDPOINTS["dts_operating_balance"])

    start_date = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
    }

    result = _request(endpoint, params, page_size=500)
    data = result.get("data", [])

    return {
        "report_type": report_type,
        "records": data,
        "count": len(data),
        "meta": result.get("meta", {}),
        "source": f"U.S. Treasury - Daily Treasury Statement ({report_type})",
    }


def get_treasury_securities_outstanding(recent_months: int = 3) -> Dict:
    """
    Get outstanding Treasury securities by type.

    Args:
        recent_months: Number of recent months to fetch (default 3)

    Returns:
        Dict with securities outstanding data.
    """
    start_date = (datetime.now() - timedelta(days=recent_months * 31)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
    }

    result = _request(ENDPOINTS["treasury_securities"], params, page_size=500)
    data = result.get("data", [])

    return {
        "records": data,
        "count": len(data),
        "meta": result.get("meta", {}),
        "source": "U.S. Treasury - Securities Outstanding",
    }


def get_federal_revenue_by_source(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get federal revenue breakdown by source (MTS Table 4).

    Args:
        fiscal_year: Fiscal year (e.g., 2024). Defaults to current/recent.

    Returns:
        Dict with revenue by source (individual income tax, corporate, excise, etc.)
    """
    if not fiscal_year:
        fiscal_year = datetime.now().year

    params = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "sort": "-record_date",
    }

    result = _request(ENDPOINTS["mts_revenue"], params, page_size=500)
    data = result.get("data", [])

    return {
        "fiscal_year": fiscal_year,
        "records": data,
        "count": len(data),
        "source": "U.S. Treasury - MTS Table 4 (Revenue by Source)",
    }


def get_federal_spending_by_agency(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get federal spending breakdown by agency (MTS Table 5).

    Args:
        fiscal_year: Fiscal year (e.g., 2024). Defaults to current/recent.

    Returns:
        Dict with spending by agency.
    """
    if not fiscal_year:
        fiscal_year = datetime.now().year

    params = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "sort": "-record_date",
    }

    result = _request(ENDPOINTS["mts_spending"], params, page_size=500)
    data = result.get("data", [])

    return {
        "fiscal_year": fiscal_year,
        "records": data,
        "count": len(data),
        "source": "U.S. Treasury - MTS Table 5 (Spending by Agency)",
    }


def get_record_setting_auctions(recent_months: int = 12) -> Dict:
    """
    Get record-setting Treasury auction results.

    Args:
        recent_months: Number of recent months (default 12)

    Returns:
        Dict with auction result records.
    """
    start_date = (datetime.now() - timedelta(days=recent_months * 31)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
    }

    result = _request(ENDPOINTS["record_setting_auction"], params, page_size=100)
    data = result.get("data", [])

    return {
        "records": data,
        "count": len(data),
        "source": "U.S. Treasury - Record-Setting Auctions",
    }


def get_debt_history(start_year: int = 2000, end_year: Optional[int] = None) -> List[Dict]:
    """
    Get historical total public debt by year (end-of-fiscal-year snapshots).

    Args:
        start_year: Start year (default 2000)
        end_year: End year (default current year)

    Returns:
        List of dicts with year and total debt amount.
    """
    if not end_year:
        end_year = datetime.now().year

    params = {
        "filter": f"record_date:gte:{start_year}-01-01,record_date:lte:{end_year}-12-31",
        "sort": "-record_date",
        "page[size]": "10000",
    }

    result = _request(ENDPOINTS["debt_to_penny"], params)
    data = result.get("data", [])

    # Get one record per fiscal year (September 30 or closest)
    yearly = {}
    for record in data:
        rd = record.get("record_date", "")
        year = rd[:4] if rd else None
        if year and year not in yearly:
            yearly[year] = {
                "year": year,
                "record_date": rd,
                "total_public_debt": record.get("tot_pub_debt_out_amt"),
                "debt_held_by_public": record.get("debt_held_public_amt"),
                "intragovernmental": record.get("intragov_hold_amt"),
            }

    return sorted(yearly.values(), key=lambda x: x["year"], reverse=True)


def search_datasets(keyword: str) -> Dict:
    """
    Search available Treasury Fiscal Data datasets by keyword.

    Note: This queries the main datasets listing page. For specific endpoint
    discovery, refer to the ENDPOINTS dict in this module.

    Args:
        keyword: Search keyword (e.g., "debt", "revenue", "exchange")

    Returns:
        Dict with matching endpoint names and paths.
    """
    matches = {}
    keyword_lower = keyword.lower()
    for name, path in ENDPOINTS.items():
        if keyword_lower in name.lower() or keyword_lower in path.lower():
            matches[name] = path

    return {
        "keyword": keyword,
        "matches": matches,
        "count": len(matches),
        "note": "Use the endpoint name with the corresponding function, or call _request() directly with the path.",
    }


def get_operating_cash_balance(recent_days: int = 30) -> Dict:
    """
    Get the federal government's daily operating cash balance.

    This shows how much cash the Treasury has on hand — a key indicator
    for debt ceiling discussions and government funding.

    Args:
        recent_days: Number of recent days (default 30)

    Returns:
        Dict with daily operating cash balance records.
    """
    start_date = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
    }

    result = _request(ENDPOINTS["dts_operating_balance"], params)
    data = result.get("data", [])

    return {
        "latest": data[0] if data else None,
        "history": data,
        "count": len(data),
        "source": "U.S. Treasury - Daily Treasury Statement (Operating Cash Balance)",
    }
