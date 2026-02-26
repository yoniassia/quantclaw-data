"""
Current Account Balance Tracker — Roadmap #268

Tracks current account balances as % of GDP for G20 economies.
Identifies surplus/deficit countries and trends.

Sources:
- World Bank API (current account balance % of GDP)
- IMF World Economic Outlook data
"""

import json
import urllib.request
from typing import Dict, List, Optional


WORLDBANK_BASE = "https://api.worldbank.org/v2"
CA_INDICATOR = "BN.CAB.XOKA.GD.ZS"  # Current account balance (% of GDP)

G20_COUNTRIES = [
    "USA", "CHN", "JPN", "DEU", "GBR", "FRA", "IND", "BRA",
    "CAN", "AUS", "KOR", "MEX", "IDN", "TUR", "SAU", "ZAF",
    "ARG", "RUS", "ITA", "ESP",
]


def fetch_current_account_balances(
    countries: Optional[List[str]] = None, years: int = 5
) -> List[Dict]:
    """
    Fetch current account balance as % of GDP from World Bank.

    Args:
        countries: ISO3 codes (default: G20)
        years: most recent N years

    Returns:
        List of {country, iso3, year, ca_pct_gdp, status}
    """
    if countries is None:
        countries = G20_COUNTRIES

    country_str = ";".join(countries)
    url = (
        f"{WORLDBANK_BASE}/country/{country_str}/indicator/{CA_INDICATOR}"
        f"?format=json&per_page=500&mrv={years}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return [{"error": str(e)}]

    if not isinstance(data, list) or len(data) < 2:
        return []

    results = []
    for entry in data[1]:
        val = entry.get("value")
        if val is not None:
            pct = round(float(val), 2)
            results.append({
                "country": entry["country"]["value"],
                "iso3": entry["countryiso3code"],
                "year": int(entry["date"]),
                "ca_pct_gdp": pct,
                "status": "surplus" if pct > 0 else "deficit",
                "severity": (
                    "large_surplus" if pct > 5 else
                    "moderate_surplus" if pct > 2 else
                    "balanced" if abs(pct) <= 2 else
                    "moderate_deficit" if pct > -5 else
                    "large_deficit"
                ),
            })

    return sorted(results, key=lambda x: (x["year"], -x["ca_pct_gdp"]), reverse=True)


def get_largest_surpluses(year: Optional[int] = None, top_n: int = 10) -> List[Dict]:
    """
    Get countries with largest current account surpluses.
    """
    data = fetch_current_account_balances(years=3)
    if year:
        data = [d for d in data if d.get("year") == year]
    else:
        # Latest year
        years_available = sorted(set(d["year"] for d in data if "year" in d), reverse=True)
        if years_available:
            data = [d for d in data if d["year"] == years_available[0]]

    surpluses = [d for d in data if d.get("ca_pct_gdp", 0) > 0]
    return sorted(surpluses, key=lambda x: x["ca_pct_gdp"], reverse=True)[:top_n]


def get_largest_deficits(year: Optional[int] = None, top_n: int = 10) -> List[Dict]:
    """
    Get countries with largest current account deficits.
    """
    data = fetch_current_account_balances(years=3)
    if year:
        data = [d for d in data if d.get("year") == year]
    else:
        years_available = sorted(set(d["year"] for d in data if "year" in d), reverse=True)
        if years_available:
            data = [d for d in data if d["year"] == years_available[0]]

    deficits = [d for d in data if d.get("ca_pct_gdp", 0) < 0]
    return sorted(deficits, key=lambda x: x["ca_pct_gdp"])[:top_n]


def track_country_trend(iso3: str = "USA", years: int = 15) -> Dict:
    """
    Track current account trend for a single country over time.
    """
    data = fetch_current_account_balances([iso3], years)
    country_data = sorted(
        [d for d in data if d.get("iso3") == iso3],
        key=lambda x: x["year"]
    )

    if len(country_data) >= 2:
        change = round(country_data[-1]["ca_pct_gdp"] - country_data[0]["ca_pct_gdp"], 2)
        direction = "improving" if change > 0 else "deteriorating"
    else:
        change = None
        direction = "insufficient_data"

    return {
        "country": country_data[0]["country"] if country_data else iso3,
        "iso3": iso3,
        "history": country_data,
        "total_change_pct": change,
        "trend": direction,
    }
