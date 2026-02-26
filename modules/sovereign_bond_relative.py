"""
Sovereign Bond Relative Value — Compare government bond yields across countries.

Analyzes relative value opportunities in sovereign debt markets by comparing
yields, spreads to benchmark, and currency-adjusted returns. Uses FRED + Yahoo Finance.
"""

import json
import urllib.request
from datetime import datetime


SOVEREIGN_BONDS = {
    "^TNX": {"name": "US 10Y Treasury", "country": "US", "currency": "USD"},
    "^TYX": {"name": "US 30Y Treasury", "country": "US", "currency": "USD"},
    "^FVX": {"name": "US 5Y Treasury", "country": "US", "currency": "USD"},
}

FRED_YIELDS = {
    "DGS10": {"name": "US 10Y", "country": "US"},
    "DGS2": {"name": "US 2Y", "country": "US"},
    "DGS30": {"name": "US 30Y", "country": "US"},
    "IRLTLT01DEM156N": {"name": "Germany 10Y", "country": "DE"},
    "IRLTLT01GBM156N": {"name": "UK 10Y", "country": "GB"},
    "IRLTLT01JPM156N": {"name": "Japan 10Y", "country": "JP"},
}


def get_sovereign_yields(api_key: str = "DEMO_KEY") -> dict:
    """Fetch latest sovereign bond yields from FRED for G7 countries."""
    results = {}
    for series_id, meta in FRED_YIELDS.items():
        try:
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={series_id}&api_key={api_key}&file_type=json"
                f"&sort_order=desc&limit=5"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            obs = data.get("observations", [])
            valid = [(o["date"], float(o["value"])) for o in obs if o.get("value") != "."]
            if valid:
                results[series_id] = {
                    **meta,
                    "yield_pct": valid[0][1],
                    "date": valid[0][0],
                }
        except Exception as e:
            results[series_id] = {**meta, "error": str(e)}
    return {"sovereign_yields": results, "as_of": datetime.utcnow().isoformat()}


def compute_relative_value(api_key: str = "DEMO_KEY") -> dict:
    """
    Compute relative value metrics: spreads to US 10Y benchmark,
    curve slope, and cross-country comparisons.
    """
    data = get_sovereign_yields(api_key)
    yields = data.get("sovereign_yields", {})

    us10 = yields.get("DGS10", {}).get("yield_pct")
    us2 = yields.get("DGS2", {}).get("yield_pct")
    us30 = yields.get("DGS30", {}).get("yield_pct")
    de10 = yields.get("IRLTLT01DEM156N", {}).get("yield_pct")
    gb10 = yields.get("IRLTLT01GBM156N", {}).get("yield_pct")
    jp10 = yields.get("IRLTLT01JPM156N", {}).get("yield_pct")

    spreads = {}
    if us10 is not None:
        if de10 is not None:
            spreads["US_DE_10Y"] = round(us10 - de10, 3)
        if gb10 is not None:
            spreads["US_GB_10Y"] = round(us10 - gb10, 3)
        if jp10 is not None:
            spreads["US_JP_10Y"] = round(us10 - jp10, 3)

    curve = {}
    if us10 is not None and us2 is not None:
        curve["US_2s10s"] = round(us10 - us2, 3)
    if us30 is not None and us10 is not None:
        curve["US_10s30s"] = round(us30 - us10, 3)

    return {
        "benchmark_spreads_pct": spreads,
        "us_curve": curve,
        "yields": {k: v.get("yield_pct") for k, v in yields.items() if v.get("yield_pct")},
        "as_of": datetime.utcnow().isoformat(),
    }


def get_cheapest_sovereign() -> dict:
    """Identify which sovereign bond market offers the highest yield (cheapest)."""
    data = get_sovereign_yields()
    yields = data.get("sovereign_yields", {})
    ten_year = {k: v for k, v in yields.items() if "10Y" in v.get("name", "") and v.get("yield_pct")}
    if not ten_year:
        return {"cheapest": None, "error": "no_data"}
    sorted_bonds = sorted(ten_year.items(), key=lambda x: x[1]["yield_pct"], reverse=True)
    return {
        "ranking": [
            {"series": k, "country": v["country"], "name": v["name"], "yield_pct": v["yield_pct"]}
            for k, v in sorted_bonds
        ],
        "cheapest": sorted_bonds[0][1]["name"],
        "richest": sorted_bonds[-1][1]["name"],
        "as_of": datetime.utcnow().isoformat(),
    }
