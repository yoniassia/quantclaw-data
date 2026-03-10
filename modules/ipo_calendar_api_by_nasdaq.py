"""
IPO Calendar API by Nasdaq — QuantClaw Data Module

Data Source: Nasdaq IPO Calendar API (public, no auth required)
Update: Daily
Free: Yes (no API key needed)
Rate Limit: ~500 calls/day

Provides:
- Upcoming IPOs (scheduled but not yet priced)
- Recently priced IPOs
- Filed IPOs (S-1 filed, date TBD)
- Withdrawn IPOs
- Monthly/historical IPO calendar data

Endpoints used:
- GET https://api.nasdaq.com/api/ipo/calendar?date=YYYY-MM
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://api.nasdaq.com/api/ipo/calendar"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/nasdaq_ipo")
os.makedirs(CACHE_DIR, exist_ok=True)


def _fetch_calendar(date_str: str, use_cache: bool = True, cache_hours: int = 6) -> Dict:
    """
    Fetch IPO calendar data for a given month.

    Args:
        date_str: Month in YYYY-MM format (e.g. '2026-03')
        use_cache: Whether to use cached results
        cache_hours: Cache validity in hours

    Returns:
        Raw API response dict with keys: priced, upcoming, filed, withdrawn
    """
    cache_file = os.path.join(CACHE_DIR, f"calendar_{date_str}.json")

    if use_cache and os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=cache_hours):
            with open(cache_file) as f:
                return json.load(f)

    try:
        resp = requests.get(
            BASE_URL,
            params={"date": date_str},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("data"):
            with open(cache_file, "w") as f:
                json.dump(data["data"], f, indent=2)
            return data["data"]

        return {}

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch Nasdaq IPO calendar for {date_str}: {e}")


def _parse_rows(section: Optional[Dict]) -> List[Dict]:
    """Extract rows from a calendar section, returning empty list if none."""
    if not section or not isinstance(section, dict):
        return []
    return section.get("rows") or []


def get_upcoming_ipos(date_str: Optional[str] = None) -> List[Dict]:
    """
    Get upcoming IPOs (scheduled but not yet priced).

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        List of dicts with keys: dealID, proposedTickerSymbol, companyName,
        proposedExchange, proposedSharePrice, sharesOffered, expectedPriceDate,
        dollarValueOfSharesOffered, dealStatus
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)
    return _parse_rows(data.get("upcoming"))


def get_priced_ipos(date_str: Optional[str] = None) -> List[Dict]:
    """
    Get recently priced IPOs for a given month.

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        List of dicts with keys: dealID, proposedTickerSymbol, companyName,
        proposedExchange, proposedSharePrice, sharesOffered, pricedDate,
        dollarValueOfSharesOffered, dealStatus
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)
    return _parse_rows(data.get("priced"))


def get_filed_ipos(date_str: Optional[str] = None) -> List[Dict]:
    """
    Get IPOs that have filed (S-1) but not yet scheduled.

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        List of dicts with keys: dealID, proposedTickerSymbol, companyName,
        proposedExchange, proposedSharePrice, sharesOffered, filedDate,
        dollarValueOfSharesOffered, dealStatus
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)
    return _parse_rows(data.get("filed"))


def get_withdrawn_ipos(date_str: Optional[str] = None) -> List[Dict]:
    """
    Get IPOs that have been withdrawn for a given month.

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        List of dicts with keys: dealID, proposedTickerSymbol, companyName,
        proposedExchange, withdrawDate, dollarValueOfSharesOffered, dealStatus
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)
    return _parse_rows(data.get("withdrawn"))


def get_monthly_summary(date_str: Optional[str] = None) -> Dict:
    """
    Get a summary of all IPO activity for a given month.

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        Dict with counts per category and total dollar value of priced deals.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)

    priced = _parse_rows(data.get("priced"))
    upcoming = _parse_rows(data.get("upcoming"))
    filed = _parse_rows(data.get("filed"))
    withdrawn = _parse_rows(data.get("withdrawn"))

    # Sum dollar values from priced IPOs
    total_raised = 0
    for ipo in priced:
        val = ipo.get("dollarValueOfSharesOffered", "")
        if val:
            try:
                total_raised += float(val.replace("$", "").replace(",", ""))
            except (ValueError, AttributeError):
                pass

    return {
        "month": date_str,
        "priced_count": len(priced),
        "upcoming_count": len(upcoming),
        "filed_count": len(filed),
        "withdrawn_count": len(withdrawn),
        "total_priced_value_usd": total_raised,
        "fetched_at": datetime.now().isoformat(),
    }


def get_full_calendar(date_str: Optional[str] = None) -> Dict:
    """
    Get the complete IPO calendar for a month (all sections).

    Args:
        date_str: Month in YYYY-MM format. Defaults to current month.

    Returns:
        Dict with keys: priced, upcoming, filed, withdrawn (each a list of dicts).
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m")
    data = _fetch_calendar(date_str)

    return {
        "month": date_str,
        "priced": _parse_rows(data.get("priced")),
        "upcoming": _parse_rows(data.get("upcoming")),
        "filed": _parse_rows(data.get("filed")),
        "withdrawn": _parse_rows(data.get("withdrawn")),
    }


def search_ipo(company_or_ticker: str, months_back: int = 6) -> List[Dict]:
    """
    Search for a specific IPO by company name or ticker across recent months.

    Args:
        company_or_ticker: Company name or ticker symbol (case-insensitive)
        months_back: How many months back to search (default 6)

    Returns:
        List of matching IPO entries with added 'section' and 'month' fields.
    """
    query = company_or_ticker.upper()
    results = []
    now = datetime.now()

    for i in range(months_back):
        dt = now - timedelta(days=30 * i)
        date_str = dt.strftime("%Y-%m")

        try:
            cal = get_full_calendar(date_str)
        except ConnectionError:
            continue

        for section_name in ["priced", "upcoming", "filed", "withdrawn"]:
            for row in cal.get(section_name, []):
                ticker = (row.get("proposedTickerSymbol") or "").upper()
                name = (row.get("companyName") or "").upper()
                if query in ticker or query in name:
                    row["section"] = section_name
                    row["month"] = date_str
                    results.append(row)

    return results


def get_latest() -> Dict:
    """
    Get the latest IPO data point — current month summary + upcoming IPOs.

    Returns:
        Dict with 'summary' and 'upcoming' keys.
    """
    date_str = datetime.now().strftime("%Y-%m")
    return {
        "summary": get_monthly_summary(date_str),
        "upcoming": get_upcoming_ipos(date_str),
    }


if __name__ == "__main__":
    print(json.dumps(get_latest(), indent=2))
