#!/usr/bin/env python3
"""
IMF Global Macro API — Comprehensive macroeconomic data for 190+ countries.

Uses the IMF DataMapper API to fetch GDP, inflation, debt, unemployment,
fiscal balances, trade, reserves, commodity terms-of-trade, and more.
133 indicators available covering WEO, fiscal monitor, and global debt datasets.

Data Source: https://www.imf.org/external/datamapper/api/v1/
Category: Macro / Central Banks
Free tier: Yes — no API key required, ~500 queries/hour
Update frequency: Quarterly (WEO updates) + annual (fiscal/debt)
Coverage: 190+ countries, 1980–2029 (including forecasts)

Note: Uses `requests` library (urllib blocked by IMF WAF).

Author: QUANTCLAW DATA NightBuilder
"""

import json
import subprocess
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

try:
    import requests
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False

# ── API Configuration ──────────────────────────────────────────────────
IMF_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"
_TIMEOUT = 15

# ── Indicator Registry ────────────────────────────────────────────────
# Core macro indicators with human-readable metadata
INDICATORS = {
    # GDP & Growth
    "NGDP_RPCH": {"name": "Real GDP Growth", "unit": "%", "category": "growth"},
    "NGDPD": {"name": "Nominal GDP (USD bn)", "unit": "USD bn", "category": "growth"},
    "NGDPDPC": {"name": "GDP Per Capita (USD)", "unit": "USD", "category": "growth"},
    "PPPGDP": {"name": "GDP PPP (Intl$ bn)", "unit": "Intl$ bn", "category": "growth"},
    "PPPPC": {"name": "GDP Per Capita PPP", "unit": "Intl$", "category": "growth"},
    # Inflation
    "PCPIPCH": {"name": "Inflation (CPI avg)", "unit": "%", "category": "inflation"},
    "PCPIEPCH": {"name": "Inflation (CPI eop)", "unit": "%", "category": "inflation"},
    # Labor
    "LUR": {"name": "Unemployment Rate", "unit": "%", "category": "labor"},
    "LP": {"name": "Population", "unit": "millions", "category": "demographics"},
    # External
    "BCA_NGDPD": {"name": "Current Account (% GDP)", "unit": "% GDP", "category": "external"},
    "BCA": {"name": "Current Account (USD)", "unit": "USD bn", "category": "external"},
    "TTT": {"name": "Terms of Trade", "unit": "index 2010=100", "category": "external"},
    # Fiscal
    "GGXWDG_NGDP": {"name": "Govt Gross Debt (% GDP)", "unit": "% GDP", "category": "fiscal"},
    "GGXCNL_NGDP": {"name": "Govt Net Lending (% GDP)", "unit": "% GDP", "category": "fiscal"},
    "GGR_NGDP": {"name": "Govt Revenue (% GDP)", "unit": "% GDP", "category": "fiscal"},
    "GGX_NGDP": {"name": "Govt Expenditure (% GDP)", "unit": "% GDP", "category": "fiscal"},
    # Debt breakdown
    "PS_DEBT_GDP": {"name": "Public Sector Debt (% GDP)", "unit": "% GDP", "category": "debt"},
    "GG_DEBT_GDP": {"name": "General Govt Debt (% GDP)", "unit": "% GDP", "category": "debt"},
    "CG_DEBT_GDP": {"name": "Central Govt Debt (% GDP)", "unit": "% GDP", "category": "debt"},
    "Privatedebt_all": {"name": "Private Debt All (% GDP)", "unit": "% GDP", "category": "debt"},
    "HH_ALL": {"name": "Household Debt (% GDP)", "unit": "% GDP", "category": "debt"},
    "NFC_ALL": {"name": "Corporate Debt (% GDP)", "unit": "% GDP", "category": "debt"},
    # Reserves
    "Reserves_M2": {"name": "Reserves / Broad Money", "unit": "ratio", "category": "reserves"},
    "Reserves_STD": {"name": "Reserves / ST Debt", "unit": "ratio", "category": "reserves"},
    "BRASS_MI": {"name": "Reserves (Months Imports)", "unit": "months", "category": "reserves"},
    # Trade & volumes
    "TM_RPCH": {"name": "Import Volume Growth", "unit": "%", "category": "trade"},
    "TX_RPCH": {"name": "Export Volume Growth", "unit": "%", "category": "trade"},
    "BT_GDP": {"name": "Trade Balance (% GDP)", "unit": "% GDP", "category": "trade"},
}

# Common country code aliases
COUNTRY_ALIASES = {
    "US": "USA", "UK": "GBR", "CHINA": "CHN", "JAPAN": "JPN",
    "GERMANY": "DEU", "FRANCE": "FRA", "INDIA": "IND", "BRAZIL": "BRA",
    "CANADA": "CAN", "AUSTRALIA": "AUS", "KOREA": "KOR", "MEXICO": "MEX",
    "RUSSIA": "RUS", "TURKEY": "TUR", "INDONESIA": "IDN",
    "SAUDI": "SAU", "ARGENTINA": "ARG", "SOUTH AFRICA": "ZAF",
}

# Indicator aliases for natural-language queries
INDICATOR_ALIASES = {
    "gdp": "NGDP_RPCH", "gdp growth": "NGDP_RPCH", "growth": "NGDP_RPCH",
    "nominal gdp": "NGDPD", "gdp per capita": "NGDPDPC",
    "inflation": "PCPIPCH", "cpi": "PCPIPCH",
    "unemployment": "LUR", "jobs": "LUR",
    "debt": "GGXWDG_NGDP", "government debt": "GGXWDG_NGDP",
    "current account": "BCA_NGDPD", "trade balance": "BT_GDP",
    "deficit": "GGXCNL_NGDP", "fiscal balance": "GGXCNL_NGDP",
    "reserves": "BRASS_MI", "population": "LP",
    "terms of trade": "TTT", "private debt": "Privatedebt_all",
    "household debt": "HH_ALL", "corporate debt": "NFC_ALL",
}


# ── Internal helpers ──────────────────────────────────────────────────

def _resolve_country(country: str) -> str:
    """Resolve country alias to ISO 3-letter code."""
    c = country.strip().upper()
    return COUNTRY_ALIASES.get(c, c)


def _resolve_indicator(indicator: str) -> str:
    """Resolve natural-language indicator name to IMF code."""
    key = indicator.strip().lower()
    return INDICATOR_ALIASES.get(key, indicator)


def _fetch_json(url: str) -> dict:
    """Fetch JSON from IMF DataMapper API.

    Uses requests library (urllib blocked by IMF WAF).
    Falls back to curl subprocess if requests unavailable.
    """
    if _USE_REQUESTS:
        try:
            r = requests.get(url, timeout=_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            raise ConnectionError(f"IMF API timeout: {url}")
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"IMF API HTTP error: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"IMF API connection error: {e}")
    else:
        # Fallback: use curl subprocess
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", str(_TIMEOUT), url],
                capture_output=True, text=True, timeout=_TIMEOUT + 5
            )
            if result.returncode != 0:
                raise ConnectionError(f"curl failed: {result.stderr}")
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise ConnectionError(f"IMF API timeout via curl: {url}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from IMF API")


def _build_url(indicator: str, countries: Optional[List[str]] = None,
               periods: Optional[List[int]] = None) -> str:
    """Build IMF DataMapper API URL."""
    parts = [IMF_BASE_URL, indicator]
    if countries:
        parts.append(",".join(countries))
    url = "/".join(parts)
    if periods:
        url += "?periods=" + ",".join(map(str, periods))
    return url


# ── Core data functions ───────────────────────────────────────────────

def get_indicator(indicator: str,
                  countries: Optional[Union[str, List[str]]] = None,
                  years: Optional[Union[int, List[int]]] = None) -> Dict[str, Dict[str, float]]:
    """Fetch any IMF indicator for one or more countries.

    Args:
        indicator: IMF indicator code or natural-language alias
                   (e.g., 'NGDP_RPCH', 'inflation', 'debt')
        countries: Country code(s) — ISO 3-letter or alias.
                   String for one, list for multiple, None for all.
        years: Year(s) to retrieve. Int for one, list for multiple,
               None for all available.

    Returns:
        Dict: {country_code: {year_str: value}}

    Example:
        >>> get_indicator('inflation', 'USA', [2023, 2024, 2025])
        {'USA': {'2023': 4.1, '2024': 2.9, '2025': 2.1}}
    """
    code = _resolve_indicator(indicator)

    # Normalize countries
    if isinstance(countries, str):
        country_list = [_resolve_country(countries)]
    elif countries:
        country_list = [_resolve_country(c) for c in countries]
    else:
        country_list = None

    # Normalize years
    if isinstance(years, int):
        year_list = [years]
    elif years:
        year_list = list(years)
    else:
        year_list = None

    url = _build_url(code, country_list, year_list)
    data = _fetch_json(url)
    values = data.get("values", {})

    # DataMapper returns {indicator: {country: {year: val}}}
    indicator_data = values.get(code, {})

    # Filter to requested countries (API sometimes returns all)
    if country_list:
        indicator_data = {k: v for k, v in indicator_data.items() if k in country_list}

    return indicator_data


def get_country_snapshot(country: str,
                         year: Optional[int] = None) -> Dict[str, Any]:
    """Get a comprehensive macro snapshot for a single country.

    Fetches GDP growth, inflation, unemployment, debt, current account,
    fiscal balance, and population in one call.

    Args:
        country: ISO 3-letter code or alias (e.g., 'USA', 'US', 'China')
        year: Year to fetch (default: current year)

    Returns:
        Dict with indicator names as keys and values.

    Example:
        >>> get_country_snapshot('USA', 2024)
        {'country': 'USA', 'year': 2024, 'Real GDP Growth': 2.8, ...}
    """
    cc = _resolve_country(country)
    yr = year or datetime.now().year
    snapshot_indicators = [
        "NGDP_RPCH", "NGDPD", "NGDPDPC", "PCPIPCH", "LUR",
        "GGXWDG_NGDP", "BCA_NGDPD", "GGXCNL_NGDP", "LP"
    ]

    result = {"country": cc, "year": yr}
    for ind in snapshot_indicators:
        try:
            data = get_indicator(ind, cc, yr)
            val = data.get(cc, {}).get(str(yr))
            meta = INDICATORS.get(ind, {})
            name = meta.get("name", ind)
            result[name] = round(val, 2) if isinstance(val, (int, float)) else val
        except Exception:
            meta = INDICATORS.get(ind, {})
            result[meta.get("name", ind)] = None

    return result


def compare_countries(countries: List[str],
                      indicator: str = "NGDP_RPCH",
                      years: Optional[List[int]] = None) -> Dict[str, Dict[str, float]]:
    """Compare an indicator across multiple countries.

    Args:
        countries: List of country codes or aliases.
        indicator: IMF indicator code or alias (default: GDP growth).
        years: Years to compare (default: last 3 years + next 2 forecasts).

    Returns:
        Dict: {country: {year: value}}

    Example:
        >>> compare_countries(['USA', 'China', 'Germany'], 'inflation')
    """
    if years is None:
        now = datetime.now().year
        years = list(range(now - 2, now + 3))

    return get_indicator(indicator, countries, years)


def get_debt_profile(country: str,
                     years: Optional[List[int]] = None) -> Dict[str, Any]:
    """Get comprehensive debt profile for a country.

    Includes government debt, private debt, household debt, and corporate debt.

    Args:
        country: ISO 3-letter code or alias.
        years: Years to fetch (default: last 5 years).

    Returns:
        Dict with debt breakdown by type and year.
    """
    cc = _resolve_country(country)
    if years is None:
        now = datetime.now().year
        years = list(range(now - 4, now + 1))

    debt_indicators = [
        "GGXWDG_NGDP", "PS_DEBT_GDP", "GG_DEBT_GDP", "CG_DEBT_GDP",
        "Privatedebt_all", "HH_ALL", "NFC_ALL"
    ]

    result = {"country": cc, "years": years}
    for ind in debt_indicators:
        try:
            data = get_indicator(ind, cc, years)
            meta = INDICATORS.get(ind, {})
            name = meta.get("name", ind)
            values = data.get(cc, {})
            result[name] = {k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in values.items()}
        except Exception:
            pass

    return result


def get_fiscal_overview(country: str,
                        years: Optional[List[int]] = None) -> Dict[str, Any]:
    """Get fiscal overview: revenue, spending, balance, and debt.

    Args:
        country: ISO 3-letter code or alias.
        years: Years to fetch (default: last 5 years).

    Returns:
        Dict with fiscal metrics by year.
    """
    cc = _resolve_country(country)
    if years is None:
        now = datetime.now().year
        years = list(range(now - 4, now + 1))

    fiscal_indicators = [
        "GGR_NGDP", "GGX_NGDP", "GGXCNL_NGDP", "GGXWDG_NGDP"
    ]

    result = {"country": cc, "years": years}
    for ind in fiscal_indicators:
        try:
            data = get_indicator(ind, cc, years)
            meta = INDICATORS.get(ind, {})
            name = meta.get("name", ind)
            values = data.get(cc, {})
            result[name] = {k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in values.items()}
        except Exception:
            pass

    return result


def get_external_sector(country: str,
                        years: Optional[List[int]] = None) -> Dict[str, Any]:
    """Get external sector data: current account, trade, reserves.

    Args:
        country: ISO 3-letter code or alias.
        years: Years to fetch (default: last 5 years).

    Returns:
        Dict with external sector metrics.
    """
    cc = _resolve_country(country)
    if years is None:
        now = datetime.now().year
        years = list(range(now - 4, now + 1))

    ext_indicators = [
        "BCA_NGDPD", "BT_GDP", "TX_RPCH", "TM_RPCH",
        "TTT", "BRASS_MI"
    ]

    result = {"country": cc, "years": years}
    for ind in ext_indicators:
        try:
            data = get_indicator(ind, cc, years)
            meta = INDICATORS.get(ind, {})
            name = meta.get("name", ind)
            values = data.get(cc, {})
            result[name] = {k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in values.items()}
        except Exception:
            pass

    return result


def list_indicators(category: Optional[str] = None) -> List[Dict[str, str]]:
    """List available indicators with metadata.

    Args:
        category: Filter by category (growth, inflation, labor, fiscal,
                  debt, external, trade, reserves, demographics).
                  None returns all.

    Returns:
        List of dicts with code, name, unit, category.
    """
    result = []
    for code, meta in INDICATORS.items():
        if category and meta.get("category") != category.lower():
            continue
        result.append({
            "code": code,
            "name": meta["name"],
            "unit": meta["unit"],
            "category": meta["category"]
        })
    return result


def search_indicators(query: str) -> List[Dict[str, str]]:
    """Search indicators by name or code.

    Args:
        query: Search term (case-insensitive).

    Returns:
        List of matching indicators.
    """
    q = query.lower()
    return [
        {"code": code, "name": meta["name"], "unit": meta["unit"], "category": meta["category"]}
        for code, meta in INDICATORS.items()
        if q in code.lower() or q in meta["name"].lower() or q in meta.get("category", "").lower()
    ]


def fetch_all_indicators() -> List[Dict[str, str]]:
    """Fetch the complete indicator list from the IMF API (133+ indicators).

    Returns:
        List of dicts with code and label for all available indicators.
    """
    url = f"{IMF_BASE_URL}/indicators"
    data = _fetch_json(url)
    indicators = data.get("indicators", {})
    result = []
    for code, meta in indicators.items():
        if meta is None:
            continue
        result.append({
            "code": code,
            "label": meta.get("label", code),
            "source": meta.get("source", ""),
        })
    return result


def get_g20_comparison(indicator: str = "NGDP_RPCH",
                       year: Optional[int] = None) -> Dict[str, float]:
    """Quick G20 comparison for any indicator.

    Args:
        indicator: IMF code or alias (default: GDP growth).
        year: Year (default: current).

    Returns:
        Dict: {country_code: value}, sorted by value descending.
    """
    g20 = ["USA", "CHN", "JPN", "DEU", "IND", "GBR", "FRA", "BRA",
           "ITA", "CAN", "KOR", "RUS", "AUS", "MEX", "IDN", "SAU",
           "TUR", "ARG", "ZAF"]
    yr = year or datetime.now().year
    data = get_indicator(indicator, g20, yr)

    result = {}
    for cc in g20:
        val = data.get(cc, {}).get(str(yr))
        if val is not None:
            result[cc] = round(val, 2) if isinstance(val, (int, float)) else val

    return dict(sorted(result.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True))


# ── Module metadata ───────────────────────────────────────────────────

def module_info() -> Dict[str, Any]:
    """Return module metadata."""
    return {
        "module": "imf_global_macro_api",
        "source": "https://www.imf.org/external/datamapper/api/v1/",
        "category": "Macro / Central Banks",
        "indicators_registered": len(INDICATORS),
        "countries": "190+",
        "coverage": "1980-2029 (inc. forecasts)",
        "auth_required": False,
        "rate_limit": "~500 queries/hour",
        "functions": [
            "get_indicator", "get_country_snapshot", "compare_countries",
            "get_debt_profile", "get_fiscal_overview", "get_external_sector",
            "list_indicators", "search_indicators", "fetch_all_indicators",
            "get_g20_comparison", "module_info"
        ]
    }


if __name__ == "__main__":
    print(json.dumps(module_info(), indent=2))
