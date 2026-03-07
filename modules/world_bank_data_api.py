"""World Bank Data API — Macro economic indicators for any country.

Fetches GDP, inflation, unemployment, trade balance and 1400+ other indicators
from the World Bank Open Data API. Free, no API key needed.

Data source: https://api.worldbank.org/v2/
Category: Macro Economics
Free tier: true - Unlimited access, no auth required
Update frequency: quarterly/annual depending on indicator
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

_BASE = "https://api.worldbank.org/v2"
_UA = {"User-Agent": "QuantClaw/1.0"}

# Common indicator codes
_POPULAR_INDICATORS = {
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SL.UEM.TOTL.ZS": "Unemployment, total (% of labor force)",
    "NE.TRD.GNFS.ZS": "Trade (% of GDP)",
    "BN.CAB.XOKA.CD": "Current account balance (BoP, current US$)",
    "NE.EXP.GNFS.CD": "Exports of goods and services (current US$)",
    "NE.IMP.GNFS.CD": "Imports of goods and services (current US$)",
    "GC.DOD.TOTL.GD.ZS": "Central government debt, total (% of GDP)",
    "FR.INR.RINR": "Real interest rate (%)",
    "PA.NUS.FCRF": "Official exchange rate (LCU per US$)",
    "SP.POP.TOTL": "Population, total",
    "SP.DYN.LE00.IN": "Life expectancy at birth, total (years)",
    "SE.XPD.TOTL.GD.ZS": "Government expenditure on education (% of GDP)",
    "SH.XPD.CHEX.GD.ZS": "Current health expenditure (% of GDP)",
    "FI.RES.TOTL.CD": "Total reserves (includes gold, current US$)",
    "BX.KLT.DINV.CD.WD": "Foreign direct investment, net inflows (BoP, current US$)",
}


def _fetch_json(url: str) -> Any:
    """Fetch JSON from World Bank API."""
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_indicator(country: str, indicator: str, start_year: int = None, end_year: int = None) -> list[dict[str, Any]]:
    """Fetch any World Bank indicator for a country.

    Args:
        country: ISO 2-letter country code (e.g. 'US', 'BR', 'CN').
        indicator: World Bank indicator code (e.g. 'NY.GDP.MKTP.CD').
        start_year: Start year (default: current year - 10).
        end_year: End year (default: current year).

    Returns:
        List of dicts with year, value, indicator, country sorted ascending.
    """
    now_year = datetime.now(timezone.utc).year
    sy = start_year or (now_year - 10)
    ey = end_year or now_year
    url = f"{_BASE}/country/{country}/indicator/{indicator}?format=json&date={sy}:{ey}&per_page=500"
    try:
        raw = _fetch_json(url)
        if not raw or len(raw) < 2 or not raw[1]:
            return []
        results = []
        for entry in raw[1]:
            if entry.get("value") is not None:
                results.append({
                    "year": int(entry["date"]),
                    "value": entry["value"],
                    "indicator": indicator,
                    "indicator_name": entry.get("indicator", {}).get("value", ""),
                    "country": entry.get("country", {}).get("id", country),
                    "country_name": entry.get("country", {}).get("value", ""),
                })
        results.sort(key=lambda x: x["year"])
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_gdp(country: str = "US", years: int = 5) -> list[dict[str, Any]]:
    """Fetch GDP (current US$) for a country.

    Args:
        country: ISO 2-letter code.
        years: Number of years of history.

    Returns:
        List of dicts with year and GDP value.
    """
    now_year = datetime.now(timezone.utc).year
    return get_indicator(country, "NY.GDP.MKTP.CD", now_year - years, now_year)


def get_inflation(country: str = "US", years: int = 5) -> list[dict[str, Any]]:
    """Fetch CPI inflation rate (annual %) for a country.

    Args:
        country: ISO 2-letter code.
        years: Number of years of history.

    Returns:
        List of dicts with year and inflation value.
    """
    now_year = datetime.now(timezone.utc).year
    return get_indicator(country, "FP.CPI.TOTL.ZG", now_year - years, now_year)


def get_unemployment(country: str = "US", years: int = 5) -> list[dict[str, Any]]:
    """Fetch unemployment rate (% of labor force) for a country.

    Args:
        country: ISO 2-letter code.
        years: Number of years of history.

    Returns:
        List of dicts with year and unemployment value.
    """
    now_year = datetime.now(timezone.utc).year
    return get_indicator(country, "SL.UEM.TOTL.ZS", now_year - years, now_year)


def get_countries() -> list[dict[str, str]]:
    """List all available countries from the World Bank API.

    Returns:
        List of dicts with id, name, region, incomeLevel.
    """
    url = f"{_BASE}/country?format=json&per_page=500"
    try:
        raw = _fetch_json(url)
        if not raw or len(raw) < 2 or not raw[1]:
            return []
        results = []
        for c in raw[1]:
            # Skip aggregates (regions etc) — they have region id = ""
            region_id = c.get("region", {}).get("id", "")
            if region_id and region_id != "NA":
                results.append({
                    "id": c["id"],
                    "iso2Code": c.get("iso2Code", ""),
                    "name": c["name"],
                    "region": c.get("region", {}).get("value", ""),
                    "income_level": c.get("incomeLevel", {}).get("value", ""),
                    "capital": c.get("capitalCity", ""),
                })
        results.sort(key=lambda x: x["name"])
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_popular_indicators() -> dict[str, str]:
    """Return dict of commonly used World Bank indicator codes and descriptions.

    Returns:
        Dict mapping indicator code to human-readable name.
    """
    return dict(_POPULAR_INDICATORS)


def compare_countries(countries: list[str], indicator: str, years: int = 5) -> dict[str, list[dict]]:
    """Compare an indicator across multiple countries.

    Args:
        countries: List of ISO 2-letter codes (e.g. ['US', 'CN', 'DE']).
        indicator: World Bank indicator code.
        years: Number of years of history.

    Returns:
        Dict mapping country code to list of yearly data.
    """
    result = {}
    now_year = datetime.now(timezone.utc).year
    for c in countries:
        data = get_indicator(c, indicator, now_year - years, now_year)
        result[c] = data
    return result


def macro_snapshot(country: str = "US") -> dict[str, Any]:
    """Comprehensive macro snapshot: GDP, inflation, unemployment, trade balance.

    Args:
        country: ISO 2-letter code.

    Returns:
        Dict with latest values and short history for key macro indicators.
    """
    indicators = {
        "gdp": "NY.GDP.MKTP.CD",
        "gdp_growth": "NY.GDP.MKTP.KD.ZG",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "inflation": "FP.CPI.TOTL.ZG",
        "unemployment": "SL.UEM.TOTL.ZS",
        "trade_pct_gdp": "NE.TRD.GNFS.ZS",
        "current_account": "BN.CAB.XOKA.CD",
        "population": "SP.POP.TOTL",
    }
    now_year = datetime.now(timezone.utc).year
    snapshot = {"country": country, "fetched_at": datetime.now(timezone.utc).isoformat()}

    for key, ind_code in indicators.items():
        data = get_indicator(country, ind_code, now_year - 5, now_year)
        if data and "error" not in data[0]:
            latest = data[-1]
            snapshot[key] = {
                "latest_value": latest["value"],
                "latest_year": latest["year"],
                "indicator_name": latest.get("indicator_name", ""),
                "history": [{"year": d["year"], "value": d["value"]} for d in data],
            }
        else:
            snapshot[key] = {"latest_value": None, "error": data[0].get("error") if data else "no data"}

    return snapshot


if __name__ == "__main__":
    import sys
    print("=== World Bank Data API Module ===")
    print(f"Popular indicators: {len(_POPULAR_INDICATORS)}")
    gdp = get_gdp("US", 3)
    print(f"US GDP (3yr): {json.dumps(gdp, indent=2)}")
    inf = get_inflation("US", 3)
    print(f"US Inflation (3yr): {json.dumps(inf, indent=2)}")
