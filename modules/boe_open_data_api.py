#!/usr/bin/env python3
"""
BOE Open Data API — Bank of England Statistical Database

Data Source: Bank of England Interactive Statistical Database
URL: https://www.bankofengland.co.uk/boeapps/database/
Category: Macro / Central Banks
Free tier: True (no API key required)
Update frequency: Daily (rates), Weekly/Monthly (statistics)

Provides:
- Official Bank Rate (base interest rate) history
- GBP exchange rates against major currencies
- Exchange rate cross-rates (USD, EUR denominated)
- Key monetary/financial series codes lookup

Series Code Reference:
- IUDBEDR: Official Bank Rate
- XUDLGBD: GBP/USD spot
- XUDLERD: EUR/USD spot
- XUDL* : Exchange rate series
"""

import requests
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/boe")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://www.bankofengland.co.uk/boeapps/database"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Well-known series codes for quick reference
KNOWN_SERIES = {
    "bank_rate": "IUDBEDR",
    "gbp_usd": "XUDLGBD",
    "gbp_eur": "XUDLERD",
    "gbp_jpy": "XUDLJYD",
    "gbp_chf": "XUDLSFD",
    "gbp_aud": "XUDLADD",
    "gbp_cad": "XUDLCDD",
    "gbp_nzd": "XUDLNDD",
    "gbp_sek": "XUDLSKD",
    "gbp_nok": "XUDLNKD",
    "gbp_dkk": "XUDLDKD",
    "gbp_hkd": "XUDLHDD",
    "gbp_sgd": "XUDLSGD",
    "gbp_inr": "XUDLBK64",
    "gbp_cny": "XUDLBK73",
    "gbp_brl": "XUDLB8KL",
    "gbp_zar": "XUDLZRD",
    "gbp_ils": "XUDLBK65",
}


def _read_cache(key: str, max_age_hours: int = 4) -> Optional[dict]:
    """Read from disk cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _write_cache(key: str, data: dict) -> None:
    """Write data to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_bank_rate_history(limit: int = 50) -> List[Dict]:
    """
    Get the official Bank of England Bank Rate history.

    Returns a list of rate changes with date and rate value,
    ordered most recent first.

    Args:
        limit: Max number of entries to return (default 50, 0 = all)

    Returns:
        List of dicts with keys: date, rate, date_raw
        Example: [{"date": "2024-08-01", "rate": 5.0, "date_raw": "01 Aug 24"}, ...]
    """
    cached = _read_cache("bank_rate_history", max_age_hours=24)
    if cached:
        return cached[:limit] if limit > 0 else cached

    url = f"{BASE_URL}/Bank-Rate.asp"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [{"error": f"Failed to fetch Bank Rate data: {str(e)}"}]

    # Parse the first table (bank rate history)
    tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
    if not tables:
        return [{"error": "Could not find rate table in page"}]

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.DOTALL)
    results = []
    for row in rows[1:]:  # skip header
        cells = re.findall(r'<td[^>]*>\s*(.*?)\s*</td>', row, re.DOTALL)
        if len(cells) >= 2:
            date_raw = cells[0].strip()
            rate_str = cells[1].strip()
            try:
                rate = float(rate_str)
                # Parse date like "01 Aug 24" -> 2024-08-01
                dt = _parse_boe_date(date_raw)
                results.append({
                    "date": dt,
                    "rate": rate,
                    "date_raw": date_raw,
                })
            except (ValueError, TypeError):
                continue

    _write_cache("bank_rate_history", results)
    return results[:limit] if limit > 0 else results


def get_current_bank_rate() -> Dict:
    """
    Get the current Bank of England Bank Rate.

    Returns:
        Dict with keys: rate, date, previous_rate, previous_date
    """
    history = get_bank_rate_history(limit=2)
    if not history or "error" in history[0]:
        return history[0] if history else {"error": "No data"}

    result = {
        "rate": history[0]["rate"],
        "date": history[0]["date"],
        "currency": "GBP",
        "source": "Bank of England",
    }
    if len(history) > 1:
        result["previous_rate"] = history[1]["rate"]
        result["previous_date"] = history[1]["date"]
        result["change_bps"] = round((history[0]["rate"] - history[1]["rate"]) * 100)

    return result


def get_exchange_rates(base: str = "USD") -> List[Dict]:
    """
    Get latest exchange rates from the Bank of England.

    Supports base currencies: USD, EUR, GBP (cross-rates computed).

    Args:
        base: Base currency code (USD or EUR supported directly)

    Returns:
        List of dicts with keys: currency, series_code, rate, high_52w, low_52w
    """
    base = base.upper()
    if base not in ("USD", "EUR"):
        return [{"error": f"Base currency '{base}' not supported. Use USD or EUR."}]

    cache_key = f"fx_rates_{base}"
    cached = _read_cache(cache_key, max_age_hours=4)
    if cached:
        return cached

    into = base
    url = f"{BASE_URL}/Rates.asp?Travel=NIxAZx&into={into}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [{"error": f"Failed to fetch exchange rates: {str(e)}"}]

    # Extract series codes and descriptions
    series_info = re.findall(
        r'title="(\w+)\s*-\s*Spot exchange rate,\s*([^"]+)"',
        resp.text
    )

    # Parse rates from the page - BoE HTML has malformed nesting, so we
    # extract series info and then pull numeric values per row.
    tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
    if not tables:
        return [{"error": "Could not find rates table"}]

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.DOTALL)
    results = []
    for row in rows[1:]:  # skip header
        # Extract series code and description from the <a title="..."> tag
        title_match = re.search(
            r'title="(\w+)\s*-\s*Spot exchange rate,\s*([^"]+)"', row
        )
        if not title_match:
            continue
        code = title_match.group(1)
        currency = title_match.group(2).strip()

        # Extract all numeric values from the row (spot, 52w-high, 52w-low)
        nums = re.findall(r'[\s>]([\d]+\.[\d]+)', row)
        if not nums:
            continue

        try:
            spot_rate = float(nums[0])
        except (ValueError, IndexError):
            continue

        entry = {
            "currency": currency,
            "series_code": code,
            "rate": spot_rate,
            "base": base,
        }
        if len(nums) >= 2:
            try:
                entry["high_52w"] = float(nums[1])
            except ValueError:
                pass
        if len(nums) >= 3:
            try:
                entry["low_52w"] = float(nums[2])
            except ValueError:
                pass

        results.append(entry)

    _write_cache(cache_key, results)
    return results


def get_gbp_rate(currency: str = "USD") -> Dict:
    """
    Get the GBP exchange rate for a specific currency.

    Args:
        currency: Target currency code (e.g., USD, EUR, JPY, CHF)

    Returns:
        Dict with rate, series_code, and 52-week range if available
    """
    currency = currency.upper()
    # Look up in known series
    key = f"gbp_{currency.lower()}"
    if key not in KNOWN_SERIES:
        # Try to find it in the full rates list
        rates = get_exchange_rates("USD")
        for r in rates:
            if currency.lower() in r.get("currency", "").lower():
                return r
        return {"error": f"Currency '{currency}' not found. Available: {list(KNOWN_SERIES.keys())}"}

    # Get from exchange rates page
    rates = get_exchange_rates("USD")
    series_code = KNOWN_SERIES[key]
    for r in rates:
        if r.get("series_code") == series_code:
            return r

    return {"error": f"Could not find rate for {currency}"}


def get_series_codes(search: str = "") -> List[Dict]:
    """
    List known Bank of England statistical series codes.

    Args:
        search: Optional filter string (searches code and description)

    Returns:
        List of dicts with keys: code, alias, description
    """
    all_series = []
    for alias, code in KNOWN_SERIES.items():
        desc = alias.replace("_", "/").upper()
        all_series.append({
            "code": code,
            "alias": alias,
            "description": f"Spot exchange rate: {desc}" if alias.startswith("gbp_") else desc,
        })

    if search:
        search_lower = search.lower()
        all_series = [
            s for s in all_series
            if search_lower in s["code"].lower()
            or search_lower in s["alias"].lower()
            or search_lower in s["description"].lower()
        ]

    return all_series


def get_inflation_data() -> Dict:
    """
    Get UK CPI inflation data from the Bank of England Monetary Policy pages.

    Returns:
        Dict with current CPI, target, and recent context from BoE
    """
    cached = _read_cache("inflation_data", max_age_hours=24)
    if cached:
        return cached

    url = "https://www.bankofengland.co.uk/monetary-policy"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch inflation data: {str(e)}"}

    # Extract key info from MPC summary page
    # Look for CPI mentions
    cpi_matches = re.findall(
        r'CPI\s+inflation\s+(?:was|fell|rose|stood at|at)\s+([\d.]+)\s*%',
        resp.text, re.IGNORECASE
    )
    target_matches = re.findall(
        r'(?:target|mandate)\s+(?:of|is)\s+([\d.]+)\s*%',
        resp.text, re.IGNORECASE
    )

    result = {
        "source": "Bank of England MPC Summary",
        "target_rate": 2.0,  # BoE CPI target is always 2%
        "currency": "GBP",
        "measure": "CPI",
    }

    if cpi_matches:
        try:
            result["latest_cpi"] = float(cpi_matches[0])
        except ValueError:
            pass

    if target_matches:
        try:
            result["target_rate"] = float(target_matches[0])
        except ValueError:
            pass

    _write_cache("inflation_data", result)
    return result


def get_monetary_policy_summary() -> Dict:
    """
    Get the latest MPC (Monetary Policy Committee) decision summary.

    Returns:
        Dict with decision date, rate, vote split, and key quotes
    """
    cached = _read_cache("mpc_summary", max_age_hours=24)
    if cached:
        return cached

    # Get current rate first
    rate_data = get_current_bank_rate()

    url = "https://www.bankofengland.co.uk/monetary-policy"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch MPC summary: {str(e)}"}

    # Extract vote info
    vote_matches = re.findall(
        r'(\d+)\s*(?:members?\s+)?voted\s+(?:to\s+)?(maintain|reduce|increase|cut|raise|hold|keep)',
        resp.text, re.IGNORECASE
    )

    result = {
        "source": "Bank of England MPC",
        "current_rate": rate_data.get("rate"),
        "last_change_date": rate_data.get("date"),
        "url": url,
    }

    if vote_matches:
        result["vote_details"] = [
            {"count": int(v[0]), "action": v[1].lower()}
            for v in vote_matches
        ]

    # Extract date of latest decision from page
    date_matches = re.findall(
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        resp.text
    )
    if date_matches:
        result["latest_decision_date"] = date_matches[0]

    _write_cache("mpc_summary", result)
    return result


def _parse_boe_date(date_str: str) -> str:
    """
    Parse BoE date formats like '01 Aug 24' or '18 Dec 25' to ISO format.

    Args:
        date_str: Date string in BoE format

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    date_str = date_str.strip()
    # Try "DD Mon YY" format
    try:
        dt = datetime.strptime(date_str, "%d %b %y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    # Try "DD Mon YYYY"
    try:
        dt = datetime.strptime(date_str, "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    # Try "DD/MM/YYYY"
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    return date_str


if __name__ == "__main__":
    print(json.dumps({
        "module": "boe_open_data_api",
        "status": "active",
        "source": "https://www.bankofengland.co.uk/boeapps/database/",
        "functions": [
            "get_bank_rate_history",
            "get_current_bank_rate",
            "get_exchange_rates",
            "get_gbp_rate",
            "get_series_codes",
            "get_inflation_data",
            "get_monetary_policy_summary",
        ],
    }, indent=2))
