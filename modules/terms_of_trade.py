"""
Terms of Trade Monitor — Roadmap #267

Tracks export/import price ratios for major economies using
free World Bank and FRED data. Rising ToT = improving trade position.

Sources:
- World Bank API (net barter terms of trade index)
- FRED (US import/export price indices)
- UN Comtrade for supplementary data
"""

import json
import urllib.request
from typing import Dict, List, Optional


WORLDBANK_BASE = "https://api.worldbank.org/v2"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Major economies to track
G20_CODES = {
    "US": "USA", "EU": "EMU", "CN": "CHN", "JP": "JPN", "GB": "GBR",
    "DE": "DEU", "FR": "FRA", "IN": "IND", "BR": "BRA", "CA": "CAN",
    "AU": "AUS", "KR": "KOR", "MX": "MEX", "ID": "IDN", "TR": "TUR",
    "SA": "SAU", "ZA": "ZAF", "AR": "ARG", "RU": "RUS", "IT": "ITA",
}

# World Bank indicator for net barter terms of trade
TOT_INDICATOR = "TT.PRI.MRCH.XD.WD"


def fetch_terms_of_trade(countries: Optional[List[str]] = None, years: int = 10) -> List[Dict]:
    """
    Fetch net barter terms of trade index from World Bank for specified countries.
    Index base = 2015 = 100. Values > 100 mean improved terms.

    Args:
        countries: ISO3 country codes (default: G20)
        years: number of years of history
    """
    if countries is None:
        countries = list(G20_CODES.values())

    country_str = ";".join(countries)
    url = (
        f"{WORLDBANK_BASE}/country/{country_str}/indicator/{TOT_INDICATOR}"
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
        if entry.get("value") is not None:
            results.append({
                "country": entry["country"]["value"],
                "iso3": entry["countryiso3code"],
                "year": int(entry["date"]),
                "tot_index": round(float(entry["value"]), 2),
                "interpretation": "improving" if float(entry["value"]) > 100 else "deteriorating",
            })

    return sorted(results, key=lambda x: (x["iso3"], x["year"]))


def get_us_trade_prices() -> Dict:
    """
    Fetch US import and export price indices from FRED to compute
    a real-time terms of trade proxy.

    Returns latest values and computed ToT ratio.
    """
    series = {
        "export_price_index": "IQ",       # Export Price Index
        "import_price_index": "IR",       # Import Price Index
    }

    results = {}
    for label, series_id in series.items():
        url = (
            f"{FRED_BASE}?series_id={series_id}"
            f"&sort_order=desc&limit=12&file_type=json"
            f"&api_key=DEMO_KEY"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            obs = data.get("observations", [])
            if obs:
                latest = obs[0]
                results[label] = {
                    "value": float(latest["value"]) if latest["value"] != "." else None,
                    "date": latest["date"],
                }
        except Exception:
            results[label] = {"value": None, "date": None}

    # Compute ToT ratio
    exp_val = results.get("export_price_index", {}).get("value")
    imp_val = results.get("import_price_index", {}).get("value")

    if exp_val and imp_val and imp_val != 0:
        tot_ratio = round((exp_val / imp_val) * 100, 2)
    else:
        tot_ratio = None

    return {
        "country": "United States",
        "export_price_index": results.get("export_price_index"),
        "import_price_index": results.get("import_price_index"),
        "terms_of_trade_ratio": tot_ratio,
        "interpretation": "improving" if tot_ratio and tot_ratio > 100 else "deteriorating" if tot_ratio else "unknown",
    }


def compare_tot_trends(country_a: str = "USA", country_b: str = "CHN", years: int = 10) -> Dict:
    """
    Compare terms of trade trends between two countries.
    Shows direction and relative change.
    """
    data = fetch_terms_of_trade([country_a, country_b], years)
    a_data = [d for d in data if d["iso3"] == country_a]
    b_data = [d for d in data if d["iso3"] == country_b]

    def calc_change(series):
        if len(series) < 2:
            return None
        return round(series[-1]["tot_index"] - series[0]["tot_index"], 2)

    return {
        "country_a": {"iso3": country_a, "data": a_data, "change": calc_change(a_data)},
        "country_b": {"iso3": country_b, "data": b_data, "change": calc_change(b_data)},
        "years_compared": years,
    }
