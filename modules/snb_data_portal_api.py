#!/usr/bin/env python3
"""
SNB Data Portal API Module — Swiss National Bank Open Data

Provides access to Swiss National Bank statistical data via the data.snb.ch API.
Covers: balance sheet (FX reserves, sight deposits), exchange rates, money market
rates (SARON), Swiss government bond yields, and consumer price index (CPI).

Data Source: https://data.snb.ch/api/cube/{cubeId}/data/csv/en
No API key required — fully public.
Refresh: Daily (FX, rates), Monthly (balance sheet, CPI)
Coverage: Switzerland, CHF-centric

Author: QUANTCLAW DATA NightBuilder
"""

import sys
import json
import csv
import io
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# SNB Data Portal configuration
SNB_BASE_URL = "https://data.snb.ch/api/cube"
SNB_USER_AGENT = "QuantClaw-Data/1.0"

# Cube registry — verified working cubes
SNB_CUBES = {
    "snbbipo": {
        "name": "SNB Balance Sheet (Monthly)",
        "description": "Assets & liabilities of the Swiss National Bank",
        "frequency": "monthly",
    },
    "devkum": {
        "name": "Exchange Rates (Monthly averages)",
        "description": "CHF exchange rates vs major currencies",
        "frequency": "monthly",
    },
    "zimoma": {
        "name": "Money Market Rates (Monthly)",
        "description": "SARON, SOFR, ESTR, EURIBOR and other key rates",
        "frequency": "monthly",
    },
    "rendoblim": {
        "name": "Swiss Government Bond Yields",
        "description": "Yield curve for Swiss Confederation bonds (1-30yr)",
        "frequency": "monthly",
    },
    "plkopr": {
        "name": "Consumer Price Index (CPI)",
        "description": "Swiss CPI national index and YoY change",
        "frequency": "monthly",
    },
}

# Balance sheet dimension keys (snbbipo)
BALANCE_SHEET_ITEMS = {
    # Assets
    "GFG": "Gold holdings and claims from gold transactions",
    "D": "Foreign currency investments",
    "RIWF": "Reserve position in the IMF",
    "IZ": "International payment instruments",
    "W": "Monetary assistance loans",
    "FRGSF": "Claims from CHF repo transactions",
    "FRGUSD": "Claims from USD repo transactions",
    "FI": "Amounts due from domestic correspondents",
    "WSF": "CHF securities",
    "UA": "Other assets",
    "T0": "Total assets",
    # Liabilities
    "N": "Banknotes in circulation",
    "GB": "Sight deposits of domestic banks",
    "VB": "Amounts due to the Confederation",
    "GBI": "Sight deposits of foreign banks and institutions",
    "US": "Other sight liabilities",
    "VRGSF": "Liabilities from CHF repo transactions",
    "ES": "SNB debt certificates",
    "VF": "Foreign currency liabilities",
    "RE": "Provisions and equity capital",
    "T1": "Total liabilities",
}

# Money market rate keys (zimoma)
RATE_KEYS = {
    "SARON": "Swiss Average Rate Overnight",
    "1TGT": "Call money rate (Tomorrow next)",
    "EG3M": "Swiss Confederation money market (3M)",
    "SOFR": "Secured Overnight Financing Rate (USD)",
    "TONA": "Tokyo Overnight Average Rate (JPY)",
    "SONIA": "Sterling Overnight Index Average (GBP)",
    "ESTR": "Euro Short-Term Rate (EUR)",
    "EURIBOR": "Euro Interbank Offered Rate (3M)",
}


def _snb_request(cube_id: str, from_date: Optional[str] = None,
                 to_date: Optional[str] = None, lang: str = "en") -> List[Dict]:
    """
    Fetch data from the SNB data portal in CSV format and parse to list of dicts.

    Args:
        cube_id: SNB cube identifier (e.g. 'snbbipo', 'devkum')
        from_date: Start date as YYYY-MM (optional)
        to_date: End date as YYYY-MM (optional)
        lang: Language code ('en', 'de', 'fr')

    Returns:
        List of dicts with parsed rows

    Raises:
        requests.RequestException: On network errors
        ValueError: If cube not found or response invalid
    """
    url = f"{SNB_BASE_URL}/{cube_id}/data/csv/{lang}"
    params = {}
    if from_date:
        params["fromDate"] = from_date
    if to_date:
        params["toDate"] = to_date

    headers = {"User-Agent": SNB_USER_AGENT}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()

    text = resp.text
    if text.startswith("{"):
        data = json.loads(text)
        if "message" in data:
            raise ValueError(f"SNB API error: {data['message']}")

    # Parse SNB CSV format: header rows then semicolon-delimited data
    lines = text.strip().split("\n")
    # Skip metadata lines (CubeId, PublishingDate, empty line, header)
    data_start = 0
    header_line = None
    for i, line in enumerate(lines):
        stripped = line.strip().strip('"')
        if stripped.startswith("Date"):
            header_line = i
            data_start = i + 1
            break

    if header_line is None:
        return []

    # Parse header
    headers_row = [h.strip().strip('"') for h in lines[header_line].split(";")]

    # Parse data rows
    results = []
    for line in lines[data_start:]:
        if not line.strip():
            continue
        fields = [f.strip().strip('"') for f in line.split(";")]
        row = {}
        for j, h in enumerate(headers_row):
            val = fields[j] if j < len(fields) else ""
            # Try to convert Value column to float
            if h == "Value" and val:
                try:
                    val = float(val)
                except ValueError:
                    pass
            row[h] = val
        results.append(row)

    return results


def get_dimensions(cube_id: str, lang: str = "en") -> Dict:
    """
    Get dimension metadata for a cube (available series and their descriptions).

    Args:
        cube_id: SNB cube identifier

    Returns:
        Dict with dimension structure
    """
    url = f"{SNB_BASE_URL}/{cube_id}/dimensions/{lang}"
    headers = {"User-Agent": SNB_USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_balance_sheet(from_date: Optional[str] = None,
                      to_date: Optional[str] = None) -> Dict:
    """
    Get SNB balance sheet data (assets and liabilities in CHF millions).

    Includes: gold holdings, foreign currency investments, banknotes in
    circulation, sight deposits, reserves, and totals.

    Args:
        from_date: Start date YYYY-MM (default: last 12 months)
        to_date: End date YYYY-MM (default: latest)

    Returns:
        Dict with 'data' (list of records), 'cube', 'labels'
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("snbbipo", from_date, to_date)

    # Enrich with labels
    for row in rows:
        dim_key = row.get("D0", "")
        row["label"] = BALANCE_SHEET_ITEMS.get(dim_key, dim_key)

    return {
        "cube": "snbbipo",
        "description": "SNB Balance Sheet (CHF millions)",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(rows),
        "data": rows,
    }


def get_fx_reserves(from_date: Optional[str] = None,
                    to_date: Optional[str] = None) -> Dict:
    """
    Get SNB foreign exchange reserves and key balance sheet items.

    Extracts: gold holdings (GFG), foreign currency investments (D),
    IMF reserve position (RIWF), total assets (T0), sight deposits (GB).

    Args:
        from_date: Start date YYYY-MM (default: last 24 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with reserve components by date
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("snbbipo", from_date, to_date)

    reserve_keys = {"GFG", "D", "RIWF", "IZ", "T0", "GB", "GBI"}
    filtered = [r for r in rows if r.get("D0") in reserve_keys]

    # Pivot by date
    by_date = {}
    for r in filtered:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date}
        key = r["D0"]
        by_date[date][key] = r.get("Value")
        by_date[date][f"{key}_label"] = BALANCE_SHEET_ITEMS.get(key, key)

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "snbbipo",
        "description": "SNB FX Reserves & Key Balance Sheet Items (CHF millions)",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(records),
        "components": list(reserve_keys),
        "data": records,
    }


def get_sight_deposits(from_date: Optional[str] = None,
                       to_date: Optional[str] = None) -> Dict:
    """
    Get SNB sight deposit balances (domestic banks + foreign banks).

    Sight deposits are a key indicator of SNB FX intervention activity.
    Rising sight deposits often signal CHF-weakening interventions.

    Args:
        from_date: Start date YYYY-MM (default: last 24 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with sight deposit data by date
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("snbbipo", from_date, to_date)

    deposit_keys = {"GB", "GBI", "US", "VB"}
    filtered = [r for r in rows if r.get("D0") in deposit_keys]

    by_date = {}
    for r in filtered:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date, "total_sight_deposits": 0}
        key = r["D0"]
        val = r.get("Value")
        by_date[date][key] = val
        by_date[date][f"{key}_label"] = BALANCE_SHEET_ITEMS.get(key, key)
        if isinstance(val, (int, float)) and key in {"GB", "GBI", "US"}:
            by_date[date]["total_sight_deposits"] += val

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "snbbipo",
        "description": "SNB Sight Deposits (CHF millions)",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(records),
        "data": records,
    }


def get_exchange_rates(from_date: Optional[str] = None,
                       to_date: Optional[str] = None) -> Dict:
    """
    Get CHF exchange rates vs major currencies (monthly averages).

    Covers: EUR, USD, GBP, JPY, CAD, AUD, CNY, SEK, NOK, and more.

    Args:
        from_date: Start date YYYY-MM (default: last 12 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with exchange rate data
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("devkum", from_date, to_date)

    # Pivot by date, using D1 as currency key
    by_date = {}
    for r in rows:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date}
        currency = r.get("D1", "")
        by_date[date][currency] = r.get("Value")

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "devkum",
        "description": "CHF Exchange Rates (monthly averages)",
        "note": "Values show how much 1 unit of foreign currency costs in CHF (e.g. EUR1 = 0.93 CHF)",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(records),
        "data": records,
    }


def get_money_market_rates(from_date: Optional[str] = None,
                           to_date: Optional[str] = None) -> Dict:
    """
    Get money market interest rates: SARON, SOFR, ESTR, EURIBOR, SONIA, TONA.

    SARON (Swiss Average Rate Overnight) is the key Swiss policy rate benchmark.

    Args:
        from_date: Start date YYYY-MM (default: last 12 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with rate data by date
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("zimoma", from_date, to_date)

    by_date = {}
    for r in rows:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date}
        key = r.get("D0", "")
        by_date[date][key] = r.get("Value")
        if key in RATE_KEYS:
            by_date[date][f"{key}_label"] = RATE_KEYS[key]

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "zimoma",
        "description": "Money Market Rates (%)",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(records),
        "rate_labels": RATE_KEYS,
        "data": records,
    }


def get_bond_yields(from_date: Optional[str] = None,
                    to_date: Optional[str] = None) -> Dict:
    """
    Get Swiss Confederation government bond yields (1Y to 30Y).

    The full yield curve for Swiss government bonds (risk-free CHF rates).

    Args:
        from_date: Start date YYYY-MM (default: last 12 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with yield curve data by date
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("rendoblim", from_date, to_date)

    tenor_labels = {
        "1J": "1Y", "2J": "2Y", "3J": "3Y", "4J": "4Y", "5J": "5Y",
        "6J": "6Y", "7J": "7Y", "8J": "8Y", "9J": "9Y", "10J": "10Y",
        "15J": "15Y", "20J": "20Y", "30J": "30Y",
    }

    by_date = {}
    for r in rows:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date}
        key = r.get("D0", "")
        label = tenor_labels.get(key, key)
        by_date[date][label] = r.get("Value")

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "rendoblim",
        "description": "Swiss Confederation Bond Yields (%)",
        "from_date": from_date,
        "to_date": to_date,
        "tenors": list(tenor_labels.values()),
        "record_count": len(records),
        "data": records,
    }


def get_cpi(from_date: Optional[str] = None,
            to_date: Optional[str] = None) -> Dict:
    """
    Get Swiss Consumer Price Index (CPI) data.

    Returns both the index level (Dec 2025 = 100) and year-over-year change (%).
    This is the primary inflation measure used by the SNB for policy decisions.

    Args:
        from_date: Start date YYYY-MM (default: last 24 months)
        to_date: End date YYYY-MM

    Returns:
        Dict with CPI index and YoY inflation rate
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m")

    rows = _snb_request("plkopr", from_date, to_date)

    cpi_labels = {
        "LD2010100": "CPI Index (Dec 2025=100)",
        "VVP": "CPI YoY Change (%)",
    }

    by_date = {}
    for r in rows:
        date = r["Date"]
        if date not in by_date:
            by_date[date] = {"date": date}
        key = r.get("D0", "")
        label = cpi_labels.get(key, key)
        by_date[date][label] = r.get("Value")
        by_date[date][f"{key}_raw"] = r.get("Value")

    records = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "cube": "plkopr",
        "description": "Swiss Consumer Price Index",
        "from_date": from_date,
        "to_date": to_date,
        "record_count": len(records),
        "data": records,
    }


def get_inflation_forecast() -> Dict:
    """
    Get latest Swiss CPI/inflation data as a proxy for inflation outlook.

    Returns recent CPI readings and year-over-year changes which inform
    the SNB's inflation expectations and policy stance.

    Returns:
        Dict with recent CPI trend and latest YoY inflation
    """
    result = get_cpi()
    data = result.get("data", [])

    # Extract latest readings
    latest = data[0] if data else {}
    latest_yoy = latest.get("VVP_raw")
    latest_index = latest.get("LD2010100_raw")

    # Build trend from last 6 months
    trend = []
    for rec in data[:6]:
        trend.append({
            "date": rec.get("date"),
            "cpi_index": rec.get("LD2010100_raw"),
            "yoy_pct": rec.get("VVP_raw"),
        })

    return {
        "description": "Swiss Inflation Outlook (based on CPI trend)",
        "latest_date": latest.get("date"),
        "latest_cpi_index": latest_index,
        "latest_yoy_inflation_pct": latest_yoy,
        "trend_6m": trend,
        "source": "SNB Data Portal (plkopr cube)",
        "note": "SNB targets price stability (~0-2% inflation). CPI YoY is the key metric.",
    }


def get_dashboard() -> Dict:
    """
    Get a comprehensive snapshot of Swiss macro data from the SNB.

    Combines: latest balance sheet totals, SARON rate, CPI, EUR/CHF, USD/CHF,
    10Y bond yield, and sight deposits.

    Returns:
        Dict with key Swiss macro indicators
    """
    dashboard = {
        "description": "SNB Macro Dashboard — Key Swiss Indicators",
        "generated_at": datetime.now().isoformat(),
        "indicators": {},
        "errors": [],
    }

    # FX Reserves / Balance sheet
    try:
        reserves = get_fx_reserves()
        if reserves["data"]:
            latest = reserves["data"][0]
            dashboard["indicators"]["total_assets_chf_mn"] = latest.get("T0")
            dashboard["indicators"]["fx_investments_chf_mn"] = latest.get("D")
            dashboard["indicators"]["gold_chf_mn"] = latest.get("GFG")
            dashboard["indicators"]["sight_deposits_domestic_chf_mn"] = latest.get("GB")
            dashboard["indicators"]["balance_sheet_date"] = latest.get("date")
    except Exception as e:
        dashboard["errors"].append(f"balance_sheet: {e}")

    # SARON / money market
    try:
        rates = get_money_market_rates()
        if rates["data"]:
            latest = rates["data"][0]
            dashboard["indicators"]["saron_pct"] = latest.get("SARON")
            dashboard["indicators"]["sofr_pct"] = latest.get("SOFR")
            dashboard["indicators"]["estr_pct"] = latest.get("ESTR")
            dashboard["indicators"]["rates_date"] = latest.get("date")
    except Exception as e:
        dashboard["errors"].append(f"money_market: {e}")

    # CPI
    try:
        cpi = get_cpi()
        if cpi["data"]:
            latest = cpi["data"][0]
            dashboard["indicators"]["cpi_yoy_pct"] = latest.get("VVP_raw")
            dashboard["indicators"]["cpi_index"] = latest.get("LD2010100_raw")
            dashboard["indicators"]["cpi_date"] = latest.get("date")
    except Exception as e:
        dashboard["errors"].append(f"cpi: {e}")

    # Bond yields
    try:
        bonds = get_bond_yields()
        if bonds["data"]:
            latest = bonds["data"][0]
            dashboard["indicators"]["gov_bond_10y_pct"] = latest.get("10Y")
            dashboard["indicators"]["gov_bond_2y_pct"] = latest.get("2Y")
            dashboard["indicators"]["bonds_date"] = latest.get("date")
    except Exception as e:
        dashboard["errors"].append(f"bonds: {e}")

    # Exchange rates
    try:
        fx = get_exchange_rates()
        if fx["data"]:
            latest = fx["data"][0]
            dashboard["indicators"]["eur_chf"] = latest.get("EUR1")
            dashboard["indicators"]["usd_chf"] = latest.get("USD1")
            dashboard["indicators"]["fx_date"] = latest.get("date")
    except Exception as e:
        dashboard["errors"].append(f"fx: {e}")

    return dashboard


def list_cubes() -> Dict:
    """List all available SNB data cubes with descriptions."""
    return {
        "description": "Available SNB Data Portal cubes",
        "cubes": SNB_CUBES,
    }


def main():
    """CLI entry point for testing."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["dashboard"]
    command = args[0].lower()

    if command == "dashboard":
        print(json.dumps(get_dashboard(), indent=2, default=str))
    elif command == "reserves":
        print(json.dumps(get_fx_reserves(), indent=2, default=str))
    elif command == "deposits":
        print(json.dumps(get_sight_deposits(), indent=2, default=str))
    elif command == "rates":
        print(json.dumps(get_money_market_rates(), indent=2, default=str))
    elif command == "bonds":
        print(json.dumps(get_bond_yields(), indent=2, default=str))
    elif command == "cpi":
        print(json.dumps(get_cpi(), indent=2, default=str))
    elif command == "fx":
        print(json.dumps(get_exchange_rates(), indent=2, default=str))
    elif command == "inflation":
        print(json.dumps(get_inflation_forecast(), indent=2, default=str))
    elif command == "cubes":
        print(json.dumps(list_cubes(), indent=2))
    elif command == "help":
        print("Usage: python snb_data_portal_api.py [command]")
        print("Commands: dashboard, reserves, deposits, rates, bonds, cpi, fx, inflation, cubes")
    else:
        print(f"Unknown command: {command}. Use 'help' for options.")


if __name__ == "__main__":
    main()
