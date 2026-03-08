#!/usr/bin/env python3
"""
TradeFlow API Module — Global Trade Flow Data

Real-time and historical data on global import/export flows, trade volumes
by country and commodity, using the UN Comtrade public API (no key required
for preview endpoints).

Data Sources:
- UN Comtrade API v1 (public/preview): https://comtradeapi.un.org/public/v1/
- Covers: Merchandise trade (commodities), annual & monthly frequencies
- HS classification (Harmonized System) commodity codes
Refresh: Annual data (yearly), Monthly data (monthly lag ~2-3 months)
Coverage: 200+ countries, 5000+ HS commodity codes

Author: QUANTCLAW DATA NightBuilder
"""

import json
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# UN Comtrade public API — no key required for preview endpoints
# ---------------------------------------------------------------------------
COMTRADE_BASE = "https://comtradeapi.un.org/public/v1"
REQUEST_TIMEOUT = 30

# Common country codes (UN M49 numeric)
COUNTRY_CODES = {
    "US": 842, "USA": 842,
    "CN": 156, "CHN": 156, "CHINA": 156,
    "DE": 276, "DEU": 276, "GERMANY": 276,
    "JP": 392, "JPN": 392, "JAPAN": 392,
    "GB": 826, "GBR": 826, "UK": 826,
    "FR": 250, "FRA": 250, "FRANCE": 250,
    "IN": 699, "IND": 699, "INDIA": 699,
    "KR": 410, "KOR": 410, "SOUTH KOREA": 410,
    "BR": 76,  "BRA": 76,  "BRAZIL": 76,
    "CA": 124, "CAN": 124, "CANADA": 124,
    "MX": 484, "MEX": 484, "MEXICO": 484,
    "AU": 36,  "AUS": 36,  "AUSTRALIA": 36,
    "IT": 380, "ITA": 380, "ITALY": 380,
    "NL": 528, "NLD": 528, "NETHERLANDS": 528,
    "SG": 702, "SGP": 702, "SINGAPORE": 702,
    "TW": 490, "TWN": 490, "TAIWAN": 490,
    "SA": 682, "SAU": 682, "SAUDI ARABIA": 682,
    "IL": 376, "ISR": 376, "ISRAEL": 376,
    "AE": 784, "ARE": 784, "UAE": 784,
    "RU": 643, "RUS": 643, "RUSSIA": 643,
    "CH": 757, "CHE": 757, "SWITZERLAND": 757,
    "WORLD": 0,
}

# Common HS commodity codes (2-digit chapters + key 4-digit)
HS_COMMODITIES = {
    "CRUDE_OIL": "2709",
    "REFINED_OIL": "2710",
    "NATURAL_GAS": "2711",
    "COAL": "2701",
    "IRON_ORE": "2601",
    "COPPER": "7403",
    "GOLD": "7108",
    "SEMICONDUCTORS": "8542",
    "ELECTRONICS": "85",
    "VEHICLES": "87",
    "PHARMACEUTICALS": "30",
    "MACHINERY": "84",
    "PLASTICS": "39",
    "ORGANIC_CHEMICALS": "29",
    "CEREALS": "10",
    "WHEAT": "1001",
    "CORN": "1005",
    "SOYBEANS": "1201",
    "COFFEE": "0901",
    "COTTON": "5201",
    "STEEL": "72",
    "ALUMINUM": "76",
    "TEXTILES": "50",
    "AIRCRAFT": "8802",
    "SHIPS": "8901",
    "FERTILIZERS": "31",
    "RUBBER": "4001",
    "WOOD": "44",
    "PAPER": "48",
}

FLOW_CODES = {
    "IMPORT": "M",
    "EXPORT": "X",
    "RE_IMPORT": "RM",
    "RE_EXPORT": "RX",
    "M": "M",
    "X": "X",
}


def _resolve_country(country: str) -> int:
    """Resolve country name/ISO to UN M49 numeric code."""
    if isinstance(country, int):
        return country
    key = country.upper().strip()
    if key in COUNTRY_CODES:
        return COUNTRY_CODES[key]
    # Try numeric
    try:
        return int(country)
    except (ValueError, TypeError):
        raise ValueError(
            f"Unknown country code: '{country}'. Use ISO-2, ISO-3, name, or UN M49 numeric. "
            f"Available: {', '.join(sorted(set(k for k in COUNTRY_CODES.keys() if len(k) == 2)))}"
        )


def _resolve_commodity(commodity: str) -> str:
    """Resolve commodity name to HS code."""
    if commodity is None:
        return "TOTAL"
    key = commodity.upper().strip().replace(" ", "_")
    if key in HS_COMMODITIES:
        return HS_COMMODITIES[key]
    # Assume it's already an HS code
    return str(commodity).strip()


def _comtrade_request(endpoint: str, params: dict) -> dict:
    """Make a request to the UN Comtrade API with error handling."""
    url = f"{COMTRADE_BASE}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            return {"error": data["error"], "data": []}
        return data
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "data": []}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {str(e)}", "data": []}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "data": []}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "data": []}


def _format_trade_record(record: dict) -> dict:
    """Format a raw Comtrade record into a clean dict."""
    return {
        "year": record.get("refYear"),
        "period": record.get("period"),
        "reporter_code": record.get("reporterCode"),
        "reporter": record.get("reporterDesc") or record.get("reporterISO"),
        "partner_code": record.get("partnerCode"),
        "partner": record.get("partnerDesc") or record.get("partnerISO"),
        "flow": record.get("flowCode"),
        "commodity_code": record.get("cmdCode"),
        "commodity": record.get("cmdDesc"),
        "value_usd": record.get("primaryValue"),
        "cif_value": record.get("cifvalue"),
        "fob_value": record.get("fobvalue"),
        "net_weight_kg": record.get("netWgt"),
        "quantity": record.get("qty"),
        "qty_unit": record.get("qtyUnitAbbr"),
    }


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def get_trade_flows(
    reporter: str = "US",
    partner: str = "WORLD",
    commodity: str = "TOTAL",
    flow: str = "IMPORT",
    year: int = 2023,
) -> Dict:
    """
    Get bilateral trade flow data between countries for a commodity.

    Args:
        reporter: Reporting country (ISO-2/3, name, or M49 code). Default 'US'.
        partner: Partner country or 'WORLD' for all. Default 'WORLD'.
        commodity: HS code or name from HS_COMMODITIES dict. 'TOTAL' for aggregate.
        flow: 'IMPORT' or 'EXPORT'. Default 'IMPORT'.
        year: Reference year. Default 2023.

    Returns:
        dict with 'data' (list of trade records), 'count', 'meta'.
    """
    reporter_code = _resolve_country(reporter)
    partner_code = _resolve_country(partner)
    cmd_code = _resolve_commodity(commodity)
    flow_code = FLOW_CODES.get(flow.upper(), "M")

    params = {
        "reporterCode": reporter_code,
        "partnerCode": partner_code,
        "cmdCode": cmd_code,
        "flowCode": flow_code,
        "period": str(year),
    }

    raw = _comtrade_request("preview/C/A/HS", params)
    if raw.get("error") and raw["error"] != "":
        return {"error": raw["error"], "data": [], "count": 0}

    records = [_format_trade_record(r) for r in raw.get("data", [])]
    return {
        "data": records,
        "count": len(records),
        "meta": {
            "reporter": reporter,
            "partner": partner,
            "commodity": commodity,
            "flow": flow,
            "year": year,
            "source": "UN Comtrade",
        },
    }


def get_top_trade_partners(
    country: str = "US",
    commodity: str = "TOTAL",
    flow: str = "IMPORT",
    year: int = 2023,
    top_n: int = 10,
) -> Dict:
    """
    Get top trade partners for a country by trade value.

    Args:
        country: Country code/name. Default 'US'.
        commodity: HS code or name. 'TOTAL' for all goods.
        flow: 'IMPORT' or 'EXPORT'.
        year: Reference year.
        top_n: Number of top partners to return.

    Returns:
        dict with ranked list of trade partners and values.
    """
    result = get_trade_flows(
        reporter=country, partner="WORLD", commodity=commodity,
        flow=flow, year=year
    )

    if result.get("error"):
        return result

    # The preview endpoint with partner=WORLD returns aggregate;
    # we need individual partners. Try without partner filter.
    country_code = _resolve_country(country)
    cmd_code = _resolve_commodity(commodity)
    flow_code = FLOW_CODES.get(flow.upper(), "M")

    # Comtrade preview may not support multi-partner breakdowns easily,
    # so we query a set of major partners individually
    major_partners = ["CN", "DE", "JP", "GB", "FR", "KR", "IN", "CA", "MX",
                      "BR", "AU", "IT", "NL", "SG", "TW", "SA", "CH", "AE",
                      "RU", "IL"]
    # Remove the country itself
    country_upper = country.upper().strip()
    major_partners = [p for p in major_partners if p != country_upper]

    partner_data = []
    for p in major_partners[:20]:
        try:
            p_code = _resolve_country(p)
            params = {
                "reporterCode": country_code,
                "partnerCode": p_code,
                "cmdCode": cmd_code,
                "flowCode": flow_code,
                "period": str(year),
            }
            raw = _comtrade_request("preview/C/A/HS", params)
            if raw.get("data"):
                rec = raw["data"][0]
                val = rec.get("primaryValue")
                if val and val > 0:
                    partner_data.append({
                        "partner": p,
                        "partner_code": p_code,
                        "value_usd": val,
                        "fob_value": rec.get("fobvalue"),
                        "net_weight_kg": rec.get("netWgt"),
                    })
            time.sleep(0.2)  # Rate limit courtesy
        except Exception:
            continue

    # Sort by value descending
    partner_data.sort(key=lambda x: x.get("value_usd", 0) or 0, reverse=True)

    return {
        "data": partner_data[:top_n],
        "count": min(top_n, len(partner_data)),
        "meta": {
            "country": country,
            "commodity": commodity,
            "flow": flow,
            "year": year,
            "source": "UN Comtrade",
        },
    }


def get_commodity_trade_summary(
    country: str = "US",
    commodities: Optional[List[str]] = None,
    flow: str = "IMPORT",
    year: int = 2023,
) -> Dict:
    """
    Get trade values for multiple commodities for a country.

    Args:
        country: Country code/name.
        commodities: List of HS codes or names. None = use common set.
        flow: 'IMPORT' or 'EXPORT'.
        year: Reference year.

    Returns:
        dict with trade values per commodity.
    """
    if commodities is None:
        commodities = [
            "CRUDE_OIL", "SEMICONDUCTORS", "VEHICLES", "MACHINERY",
            "PHARMACEUTICALS", "ELECTRONICS", "CEREALS", "STEEL",
        ]

    country_code = _resolve_country(country)
    flow_code = FLOW_CODES.get(flow.upper(), "M")

    results = []
    for comm in commodities:
        cmd_code = _resolve_commodity(comm)
        params = {
            "reporterCode": country_code,
            "partnerCode": 0,  # World
            "cmdCode": cmd_code,
            "flowCode": flow_code,
            "period": str(year),
        }
        raw = _comtrade_request("preview/C/A/HS", params)
        if raw.get("data"):
            rec = raw["data"][0]
            results.append({
                "commodity": comm,
                "hs_code": cmd_code,
                "value_usd": rec.get("primaryValue"),
                "net_weight_kg": rec.get("netWgt"),
                "quantity": rec.get("qty"),
            })
        else:
            results.append({
                "commodity": comm,
                "hs_code": cmd_code,
                "value_usd": None,
                "error": raw.get("error", "No data"),
            })
        time.sleep(0.2)

    # Sort by value descending
    results.sort(key=lambda x: x.get("value_usd") or 0, reverse=True)

    total = sum(r.get("value_usd", 0) or 0 for r in results)
    return {
        "data": results,
        "total_value_usd": total,
        "count": len(results),
        "meta": {
            "country": country,
            "flow": flow,
            "year": year,
            "source": "UN Comtrade",
        },
    }


def get_trade_balance(
    country: str = "US",
    partner: str = "WORLD",
    commodity: str = "TOTAL",
    year: int = 2023,
) -> Dict:
    """
    Calculate trade balance (exports - imports) between two countries.

    Args:
        country: Reporting country.
        partner: Partner country or 'WORLD'.
        commodity: HS code or name.
        year: Reference year.

    Returns:
        dict with imports, exports, balance, and deficit/surplus indicator.
    """
    imports = get_trade_flows(
        reporter=country, partner=partner, commodity=commodity,
        flow="IMPORT", year=year
    )
    exports = get_trade_flows(
        reporter=country, partner=partner, commodity=commodity,
        flow="EXPORT", year=year
    )

    import_val = 0
    export_val = 0

    if imports.get("data"):
        import_val = imports["data"][0].get("value_usd") or 0
    if exports.get("data"):
        export_val = exports["data"][0].get("value_usd") or 0

    balance = export_val - import_val

    return {
        "country": country,
        "partner": partner,
        "commodity": commodity,
        "year": year,
        "imports_usd": import_val,
        "exports_usd": export_val,
        "balance_usd": balance,
        "status": "surplus" if balance > 0 else "deficit" if balance < 0 else "balanced",
        "source": "UN Comtrade",
    }


def get_trade_time_series(
    reporter: str = "US",
    partner: str = "CN",
    commodity: str = "TOTAL",
    flow: str = "IMPORT",
    start_year: int = 2018,
    end_year: int = 2023,
) -> Dict:
    """
    Get trade data across multiple years for trend analysis.

    Args:
        reporter: Reporting country.
        partner: Partner country.
        commodity: HS code or name.
        flow: 'IMPORT' or 'EXPORT'.
        start_year: Start year (inclusive).
        end_year: End year (inclusive).

    Returns:
        dict with yearly trade values and growth calculations.
    """
    reporter_code = _resolve_country(reporter)
    partner_code = _resolve_country(partner)
    cmd_code = _resolve_commodity(commodity)
    flow_code = FLOW_CODES.get(flow.upper(), "M")

    series = []
    for yr in range(start_year, end_year + 1):
        params = {
            "reporterCode": reporter_code,
            "partnerCode": partner_code,
            "cmdCode": cmd_code,
            "flowCode": flow_code,
            "period": str(yr),
        }
        raw = _comtrade_request("preview/C/A/HS", params)
        val = None
        if raw.get("data"):
            val = raw["data"][0].get("primaryValue")
        series.append({"year": yr, "value_usd": val})
        time.sleep(0.2)

    # Calculate YoY growth
    for i in range(1, len(series)):
        prev = series[i - 1].get("value_usd")
        curr = series[i].get("value_usd")
        if prev and curr and prev > 0:
            series[i]["yoy_growth_pct"] = round((curr - prev) / prev * 100, 2)
        else:
            series[i]["yoy_growth_pct"] = None

    values = [s["value_usd"] for s in series if s["value_usd"]]
    cagr = None
    if len(values) >= 2 and values[0] > 0:
        n = len(values) - 1
        cagr = round(((values[-1] / values[0]) ** (1 / n) - 1) * 100, 2)

    return {
        "data": series,
        "count": len(series),
        "cagr_pct": cagr,
        "meta": {
            "reporter": reporter,
            "partner": partner,
            "commodity": commodity,
            "flow": flow,
            "start_year": start_year,
            "end_year": end_year,
            "source": "UN Comtrade",
        },
    }


def get_country_codes() -> Dict:
    """
    Return available country code mappings.

    Returns:
        dict of country name/ISO to UN M49 code.
    """
    return {
        "codes": COUNTRY_CODES,
        "count": len(set(COUNTRY_CODES.values())),
    }


def get_commodity_codes() -> Dict:
    """
    Return available HS commodity code mappings.

    Returns:
        dict of commodity names to HS codes.
    """
    return {
        "codes": HS_COMMODITIES,
        "count": len(HS_COMMODITIES),
    }


def get_latest(
    reporter: str = "US",
    commodity: str = "CRUDE_OIL",
    flow: str = "IMPORT",
) -> Dict:
    """
    Get latest available trade data for a country/commodity pair.
    Tries most recent years until data is found.

    Args:
        reporter: Country code/name.
        commodity: HS code or name.
        flow: 'IMPORT' or 'EXPORT'.

    Returns:
        dict with latest trade data point.
    """
    current_year = datetime.now().year
    for yr in range(current_year - 1, current_year - 5, -1):
        result = get_trade_flows(
            reporter=reporter, partner="WORLD", commodity=commodity,
            flow=flow, year=yr
        )
        if result.get("data") and result["data"][0].get("value_usd"):
            return {
                "latest_year": yr,
                "data": result["data"][0],
                "meta": result["meta"],
            }
    return {"error": "No recent data found", "data": None}


if __name__ == "__main__":
    print(json.dumps({
        "module": "tradeflow_api",
        "status": "active",
        "source": "UN Comtrade API",
        "functions": [
            "get_trade_flows", "get_top_trade_partners",
            "get_commodity_trade_summary", "get_trade_balance",
            "get_trade_time_series", "get_country_codes",
            "get_commodity_codes", "get_latest",
        ]
    }, indent=2))
