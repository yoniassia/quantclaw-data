#!/usr/bin/env python3
"""
Bank of England Statistical Interactive Database API

Free access to UK interest rates, exchange rates, yield curves, and monetary
policy data. No API key required. Returns real data from BoE XML endpoint.

Source: https://www.bankofengland.co.uk/boeapps/database/
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://www.bankofengland.co.uk/boeapps/iadb/FromShowColumns.asp"
NS = "https://www.bankofengland.co.uk/website/agg_series"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; QuantClaw/1.0)"}

# Common series codes for quick access
SERIES = {
    "bank_rate": "IUDBEDR",
    "gbp_usd": "XUDLUSS",
    "gbp_eur": "XUDLERS",
    "gbp_jpy": "XUDLJYS",
    "cpi_annual": "D7BT",
    "rpi_annual": "CZBH",
    "m4_money_supply": "LPMAUYM",
    "gilt_10y": "IUDMNZC",
    "gilt_2y": "IUDMNB8",
}


def fetch_series(series_codes: str, from_date: str = "01/Jan/2020",
                 to_date: str = "now") -> List[Dict]:
    """
    Fetch one or more time series from the BoE Statistical Interactive Database.

    Args:
        series_codes: Comma-separated BoE series codes (e.g. 'IUDBEDR' for Bank Rate,
                      or 'IUDBEDR,XUDLUSS' for multiple).
        from_date: Start date as 'DD/Mon/YYYY' (default '01/Jan/2020').
        to_date: End date as 'DD/Mon/YYYY' or 'now' (default 'now').

    Returns:
        List of dicts with keys: time, value, series, updated.

    Example:
        >>> fetch_series("IUDBEDR", "01/Jan/2025")
        [{'time': '2025-01-02', 'value': '4.75', 'series': 'IUDBEDR', ...}, ...]
    """
    params = {
        "xml.x": "1",
        "xml.y": "1",
        "SeriesCodes": series_codes,
        "UsingCodes": "Y",
        "Datefrom": from_date,
        "Dateto": to_date,
    }
    try:
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"BoE API request failed: {e}")

    root = ET.fromstring(resp.text)
    results = []
    current_series = ""

    for elem in root.iter():
        tag = elem.tag.replace(f"{{{NS}}}", "")
        attrib = elem.attrib

        if tag == "Cube" and "SCODE" in attrib:
            current_series = attrib["SCODE"]
        elif tag == "Cube" and "TIME" in attrib and "OBS_VALUE" in attrib:
            results.append({
                "time": attrib["TIME"],
                "value": attrib["OBS_VALUE"],
                "series": current_series,
                "updated": attrib.get("LAST_UPDATED", ""),
            })

    return results


def get_series_metadata(series_code: str) -> Dict:
    """
    Get metadata for a BoE series (description, frequency, date range).

    Args:
        series_code: BoE series code (e.g. 'IUDBEDR').

    Returns:
        Dict with series description, frequency, first/last observation dates.
    """
    params = {
        "xml.x": "1", "xml.y": "1",
        "SeriesCodes": series_code, "UsingCodes": "Y",
        "Datefrom": "01/Jan/2025", "Dateto": "02/Jan/2025",
    }
    try:
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"BoE API request failed: {e}")

    root = ET.fromstring(resp.text)
    meta = {"series_code": series_code}

    for elem in root.iter():
        attrib = elem.attrib
        if "SCODE" in attrib:
            meta["description"] = attrib.get("DESC", "")
        if "FREQ_NAME" in attrib:
            meta["frequency"] = attrib["FREQ_NAME"]
        if "FIRST_OBS" in attrib:
            meta["first_obs"] = attrib["FIRST_OBS"]
            meta["last_obs"] = attrib.get("LAST_OBS", "")

    return meta


def get_bank_rate(from_date: str = "01/Jan/2020", to_date: str = "now") -> List[Dict]:
    """
    Get UK Bank Rate (base interest rate) history.

    Args:
        from_date: Start date as 'DD/Mon/YYYY'.
        to_date: End date or 'now'.

    Returns:
        List of dicts with time, value, series, updated.
    """
    return fetch_series("IUDBEDR", from_date, to_date)


def get_exchange_rate(pair: str = "gbp_usd", from_date: str = "01/Jan/2020",
                      to_date: str = "now") -> List[Dict]:
    """
    Get exchange rate history from BoE.

    Args:
        pair: One of 'gbp_usd', 'gbp_eur', 'gbp_jpy', or a raw BoE series code.
        from_date: Start date.
        to_date: End date or 'now'.

    Returns:
        List of dicts with time, value, series, updated.
    """
    code = SERIES.get(pair, pair)
    return fetch_series(code, from_date, to_date)


def get_yield_curve(from_date: str = "01/Jan/2023", to_date: str = "now") -> List[Dict]:
    """
    Get UK gilt yields (2Y and 10Y) for yield curve analysis.

    Args:
        from_date: Start date.
        to_date: End date or 'now'.

    Returns:
        List of dicts with time, value, series (IUDMNB8=2Y, IUDMNZC=10Y).
    """
    return fetch_series("IUDMNB8,IUDMNZC", from_date, to_date)


def get_inflation(measure: str = "cpi", from_date: str = "01/Jan/2020",
                  to_date: str = "now") -> List[Dict]:
    """
    Get UK inflation data (CPI or RPI annual rate).

    Args:
        measure: 'cpi' or 'rpi'.
        from_date: Start date.
        to_date: End date or 'now'.

    Returns:
        List of dicts with time, value, series.
    """
    code = SERIES.get(f"{measure}_annual", SERIES["cpi_annual"])
    return fetch_series(code, from_date, to_date)


def list_common_series() -> Dict[str, str]:
    """
    List commonly used BoE series codes.

    Returns:
        Dict mapping friendly names to series codes.
    """
    return dict(SERIES)


def get_latest(series_code: str = "IUDBEDR") -> Dict:
    """
    Get the latest available data point for a series.

    Args:
        series_code: BoE series code (default: Bank Rate).

    Returns:
        Dict with the most recent observation.
    """
    now = datetime.utcnow()
    from_date = (now - timedelta(days=90)).strftime("%d/%b/%Y")
    data = fetch_series(series_code, from_date, "now")
    if data:
        return data[-1]
    return {"error": "No data available"}


if __name__ == "__main__":
    print(json.dumps({
        "module": "bank_of_england_statistical_interactive_database_api",
        "status": "ready",
        "functions": ["fetch_series", "get_series_metadata", "get_bank_rate",
                      "get_exchange_rate", "get_yield_curve", "get_inflation",
                      "list_common_series", "get_latest"],
        "series": SERIES,
    }, indent=2))
