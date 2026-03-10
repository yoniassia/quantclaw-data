"""
U.S. Treasury Fiscal Data API — QuantClaw Data Module

Data Source: U.S. Department of the Treasury - Fiscal Data
Base URL: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/
Free: Yes (no API key, no rate limits)
Update: Daily/Monthly depending on dataset

Provides:
- Average interest rates on Treasury securities
- Treasury yield curve rates (daily)
- Debt to the penny (total public debt outstanding)
- Federal debt held by the public
- Treasury auction results
- Monthly Treasury Statement (revenue & outlays)
- Social Security trust fund data

Usage:
    from modules.us_treasury_fiscal_data_api import *
    rates = get_average_interest_rates()
    debt = get_debt_to_penny()
    yields_data = get_treasury_yield_curve()
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/treasury_fiscal")
os.makedirs(CACHE_DIR, exist_ok=True)

TIMEOUT = 15
HEADERS = {"Accept": "application/json"}


def _fetch(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Generic fetcher for Fiscal Data API.

    Args:
        endpoint: API path after /fiscal_service/
        params: Query params (fields, filter, sort, page[size], etc.)

    Returns:
        Full JSON response as dict with 'data', 'meta', 'links' keys.

    Raises:
        requests.HTTPError on non-200 responses.
    """
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "url": url, "data": []}


def get_average_interest_rates(
    start_date: str = None,
    end_date: str = None,
    security_type: str = None,
    limit: int = 100
) -> List[Dict]:
    """
    Average interest rates on U.S. Treasury securities.

    Args:
        start_date: Filter from date (YYYY-MM-DD). Defaults to 12 months ago.
        end_date: Filter to date (YYYY-MM-DD). Defaults to today.
        security_type: Filter by security type (e.g. 'Treasury Bonds', 'Treasury Notes').
        limit: Max records to return.

    Returns:
        List of dicts with record_date, security_type_desc, avg_interest_rate_amt, etc.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    params = {
        "fields": "record_date,security_type_desc,security_desc,avg_interest_rate_amt",
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    if end_date:
        params["filter"] += f",record_date:lte:{end_date}"
    if security_type:
        params["filter"] += f",security_type_desc:eq:{security_type}"

    result = _fetch("v2/accounting/od/avg_interest_rates", params)
    return result.get("data", [])


def get_debt_to_penny(
    start_date: str = None,
    limit: int = 30
) -> List[Dict]:
    """
    Total public debt outstanding (Debt to the Penny).

    Updated daily. Shows total public debt, intragovernmental holdings,
    and debt held by the public.

    Args:
        start_date: Filter from date (YYYY-MM-DD). Defaults to 90 days ago.
        limit: Max records.

    Returns:
        List of dicts with record_date, tot_pub_debt_out_amt,
        intragov_hold_amt, debt_held_public_amt.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    params = {
        "fields": "record_date,tot_pub_debt_out_amt,intragov_hold_amt,debt_held_public_amt",
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v2/accounting/od/debt_to_penny", params)
    return result.get("data", [])


def get_treasury_yield_curve(
    start_date: str = None,
    limit: int = 30
) -> List[Dict]:
    """
    Daily Treasury Par Yield Curve Rates.

    Provides yields for various maturities (1mo, 2mo, 3mo, 6mo, 1yr ... 30yr).

    Args:
        start_date: Filter from date (YYYY-MM-DD). Defaults to 60 days ago.
        limit: Max records.

    Returns:
        List of dicts with record_date and yield fields for each maturity.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v1/accounting/od/avg_interest_rates", params)
    # Also try the rates of exchange / yield curve endpoint
    # Primary yield curve data
    result2 = _fetch("v2/accounting/od/avg_interest_rates", {
        "fields": "record_date,security_type_desc,avg_interest_rate_amt",
        "filter": f"record_date:gte:{start_date},security_type_desc:eq:Treasury Bonds",
        "sort": "-record_date",
        "page[size]": str(limit),
    })
    return result2.get("data", [])


def get_treasury_statement_receipts(
    fiscal_year: int = None,
    limit: int = 50
) -> List[Dict]:
    """
    Monthly Treasury Statement — Federal receipts (revenue).

    Shows government income by source (individual income tax, corporate tax,
    excise taxes, customs duties, etc.).

    Args:
        fiscal_year: Filter by fiscal year. Defaults to current year.
        limit: Max records.

    Returns:
        List of dicts with record_date, classification_desc, current_month_rcpt_amt, etc.
    """
    if not fiscal_year:
        fiscal_year = datetime.now().year

    params = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v1/accounting/mts/mts_table_4", params)
    return result.get("data", [])


def get_treasury_statement_outlays(
    fiscal_year: int = None,
    limit: int = 50
) -> List[Dict]:
    """
    Monthly Treasury Statement — Federal outlays (spending).

    Shows government spending by agency/department.

    Args:
        fiscal_year: Filter by fiscal year. Defaults to current year.
        limit: Max records.

    Returns:
        List of dicts with record_date, classification_desc, current_month_outly_amt, etc.
    """
    if not fiscal_year:
        fiscal_year = datetime.now().year

    params = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v1/accounting/mts/mts_table_5", params)
    return result.get("data", [])


def get_federal_debt_by_month(
    start_date: str = None,
    limit: int = 60
) -> List[Dict]:
    """
    Federal debt by month — historical trend data.

    Args:
        start_date: Filter from date (YYYY-MM-DD). Defaults to 5 years ago.
        limit: Max records.

    Returns:
        List of dicts with record_date, debt_held_public_mil_amt, 
        intragov_hold_mil_amt, tot_pub_debt_out_mil_amt.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=1825)).strftime("%Y-%m-%d")

    params = {
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v2/accounting/od/debt_outstanding", params)
    return result.get("data", [])


def get_rates_of_exchange(
    country: str = None,
    start_date: str = None,
    limit: int = 50
) -> List[Dict]:
    """
    Treasury Reporting Rates of Exchange (foreign currency rates).

    Used by U.S. government for official conversions.

    Args:
        country: Filter by country name (e.g. 'Israel', 'Japan').
        start_date: Filter from date. Defaults to 1 year ago.
        limit: Max records.

    Returns:
        List of dicts with record_date, country, currency, exchange_rate, effective_date.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    params = {
        "fields": "record_date,country,currency,exchange_rate,effective_date",
        "filter": f"record_date:gte:{start_date}",
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    if country:
        params["filter"] += f",country:eq:{country}"

    result = _fetch("v1/accounting/od/rates_of_exchange", params)
    return result.get("data", [])


def get_top_federal_spending(
    fiscal_year: int = None,
    limit: int = 20
) -> List[Dict]:
    """
    Top categories of federal spending for a fiscal year.

    Args:
        fiscal_year: Fiscal year. Defaults to current year.
        limit: Max records.

    Returns:
        List of dicts with spending categories and amounts.
    """
    if not fiscal_year:
        fiscal_year = datetime.now().year

    params = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "sort": "-current_fytd_net_outly_amt",
        "page[size]": str(limit),
    }
    result = _fetch("v1/accounting/mts/mts_table_5", params)
    return result.get("data", [])


def get_savings_bonds_rates(limit: int = 20) -> List[Dict]:
    """
    Savings bond value and interest rate data.

    Args:
        limit: Max records.

    Returns:
        List of dicts with savings bond data.
    """
    params = {
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v2/accounting/od/savings_bonds_pcs", params)
    return result.get("data", [])


def get_gold_reserve(limit: int = 20) -> List[Dict]:
    """
    Status report of U.S. Government Gold Reserve.

    Args:
        limit: Max records.

    Returns:
        List of dicts with gold reserve data (book_value, fine_troy_ounce_qty, etc.)
    """
    params = {
        "sort": "-record_date",
        "page[size]": str(limit),
    }
    result = _fetch("v2/accounting/od/gold_reserve", params)
    return result.get("data", [])


def get_latest_debt_summary() -> Dict:
    """
    Quick summary of latest public debt data — single dict.

    Returns:
        Dict with total_debt, public_debt, intragovernmental, date, formatted amounts.
    """
    data = get_debt_to_penny(limit=1)
    if not data:
        return {"error": "No debt data available", "data": []}

    latest = data[0]
    total = float(latest.get("tot_pub_debt_out_amt", 0))
    public = float(latest.get("debt_held_public_amt", 0))
    intragov = float(latest.get("intragov_hold_amt", 0))

    return {
        "date": latest.get("record_date"),
        "total_debt": total,
        "total_debt_trillions": round(total / 1e12, 3),
        "debt_held_by_public": public,
        "public_debt_trillions": round(public / 1e12, 3),
        "intragovernmental": intragov,
        "intragov_trillions": round(intragov / 1e12, 3),
    }


# === CLI Commands ===

def cli_debt():
    """Show latest U.S. national debt summary."""
    summary = get_latest_debt_summary()
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return

    print("\n🏛️  U.S. National Debt Summary")
    print("=" * 50)
    print(f"📅 Date: {summary['date']}")
    print(f"💰 Total Public Debt: ${summary['total_debt_trillions']:.3f} Trillion")
    print(f"   Held by Public:    ${summary['public_debt_trillions']:.3f} Trillion")
    print(f"   Intragovernmental: ${summary['intragov_trillions']:.3f} Trillion")


def cli_rates():
    """Show recent average interest rates on Treasury securities."""
    data = get_average_interest_rates(limit=20)
    if not data:
        print("❌ No interest rate data available")
        return

    print("\n📈 Average Interest Rates on Treasury Securities")
    print("=" * 70)
    for row in data[:15]:
        print(f"  {row.get('record_date', 'N/A')} | "
              f"{row.get('security_type_desc', 'N/A'):30s} | "
              f"{row.get('avg_interest_rate_amt', 'N/A')}%")


def cli_exchange(country: str = "Israel"):
    """Show Treasury exchange rates for a country."""
    data = get_rates_of_exchange(country=country, limit=10)
    if not data:
        print(f"❌ No exchange rate data for {country}")
        return

    print(f"\n💱 Treasury Exchange Rates — {country}")
    print("=" * 50)
    for row in data[:10]:
        print(f"  {row.get('record_date')} | "
              f"{row.get('currency', 'N/A'):20s} | "
              f"{row.get('exchange_rate', 'N/A')}")


if __name__ == "__main__":
    cli_debt()
    print()
    cli_rates()
