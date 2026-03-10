"""
CAD Trust Carbon Market Data API — Carbon Emissions & Climate Data Aggregator

Aggregates carbon emissions and climate data from free public sources:
- World Bank Climate Data (CO2 emissions, GHG, per capita, intensity)
- World Bank Development Indicators (GDP for carbon intensity calculations)

Since the cadtrust.net API is not yet live, this module provides equivalent
carbon market intelligence from the World Bank's free, no-key-required APIs.

Category: ESG & Climate
Free tier: Yes — World Bank APIs are free, no API key required
Update frequency: Annual (World Bank indicators)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

BASE_URL = "https://api.worldbank.org/v2"
HEADERS = {"User-Agent": "QuantClaw/1.0"}
CACHE: Dict[str, tuple] = {}
CACHE_TTL = timedelta(hours=12)

# Key World Bank climate/carbon indicators
INDICATORS = {
    "co2_total": "EN.GHG.CO2.MT.CE.AR5",          # CO2 emissions total (Mt CO2e)
    "co2_per_capita": "EN.ATM.CO2E.PC",             # CO2 per capita (metric tons)
    "ghg_total": "EN.GHG.ALL.MT.CE.AR5",           # Total GHG emissions (Mt CO2e)
    "methane": "EN.GHG.CH4.MT.CE.AR5",             # Methane emissions (Mt CO2e)
    "nitrous_oxide": "EN.GHG.N2O.MT.CE.AR5",       # N2O emissions (Mt CO2e)
    "renewable_energy_pct": "EG.FEC.RNEW.ZS",      # Renewable energy % of total
    "fossil_fuel_pct": "EG.USE.COMM.FO.ZS",        # Fossil fuel energy consumption %
    "electric_renewable_pct": "EG.ELC.RNEW.ZS",    # Renewable electricity % of total
    "energy_use_per_capita": "EG.USE.PCAP.KG.OE",  # Energy use per capita (kg oil eq)
    "forest_area_pct": "AG.LND.FRST.ZS",           # Forest area (% of land)
    "gdp": "NY.GDP.MKTP.CD",                        # GDP current USD
}


def _wb_get(url: str, timeout: int = 15) -> Any:
    """HTTP GET with in-memory cache for World Bank API."""
    now = datetime.utcnow()
    if url in CACHE:
        data, ts = CACHE[url]
        if now - ts < CACHE_TTL:
            return data
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    data = json.loads(raw)
    CACHE[url] = (data, now)
    return data


def _fetch_indicator(country: str, indicator_id: str, mrv: int = 5) -> List[Dict]:
    """Fetch a World Bank indicator for a country. Returns list of data points."""
    url = f"{BASE_URL}/country/{country}/indicator/{indicator_id}?format=json&per_page={mrv}&mrv={mrv}"
    data = _wb_get(url)
    if not isinstance(data, list) or len(data) < 2:
        return []
    return [
        {"date": r["date"], "value": r["value"]}
        for r in data[1]
        if r.get("value") is not None
    ]


def get_co2_emissions(country: str = "US", years: int = 10) -> Dict[str, Any]:
    """
    Get CO2 emissions for a country (total, excluding LULUCF).

    Args:
        country: ISO 2-letter country code (e.g. 'US', 'CN', 'DE', 'GB', 'IN').
        years: Number of most recent years to return.

    Returns:
        Dict with CO2 emissions time series in Mt CO2e.
    """
    try:
        records = _fetch_indicator(country, INDICATORS["co2_total"], years)
        return {
            "country": country.upper(),
            "indicator": "CO2 emissions (total, excl. LULUCF)",
            "unit": "Mt CO2e",
            "data": records,
            "count": len(records),
            "source": "World Bank (EN.GHG.CO2.MT.CE.AR5)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def get_ghg_emissions(country: str = "US", years: int = 10) -> Dict[str, Any]:
    """
    Get total greenhouse gas emissions for a country (all GHGs).

    Args:
        country: ISO 2-letter country code.
        years: Number of most recent years.

    Returns:
        Dict with total GHG emissions time series in Mt CO2e.
    """
    try:
        records = _fetch_indicator(country, INDICATORS["ghg_total"], years)
        return {
            "country": country.upper(),
            "indicator": "Total GHG emissions (all gases)",
            "unit": "Mt CO2e",
            "data": records,
            "count": len(records),
            "source": "World Bank (EN.GHG.ALL.MT.CE.AR5)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def get_emissions_per_capita(country: str = "US", years: int = 10) -> Dict[str, Any]:
    """
    Get CO2 emissions per capita for a country.

    Args:
        country: ISO 2-letter country code.
        years: Number of most recent years.

    Returns:
        Dict with per-capita CO2 emissions time series.
    """
    try:
        records = _fetch_indicator(country, INDICATORS["co2_per_capita"], years)
        return {
            "country": country.upper(),
            "indicator": "CO2 emissions per capita",
            "unit": "metric tons per capita",
            "data": records,
            "count": len(records),
            "source": "World Bank (EN.ATM.CO2E.PC)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def get_renewable_energy_share(country: str = "US", years: int = 10) -> Dict[str, Any]:
    """
    Get renewable energy consumption as % of total energy for a country.

    Args:
        country: ISO 2-letter country code.
        years: Number of most recent years.

    Returns:
        Dict with renewable energy share time series.
    """
    try:
        records = _fetch_indicator(country, INDICATORS["renewable_energy_pct"], years)
        return {
            "country": country.upper(),
            "indicator": "Renewable energy (% of total final energy)",
            "unit": "percent",
            "data": records,
            "count": len(records),
            "source": "World Bank (EG.FEC.RNEW.ZS)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def get_energy_profile(country: str = "US") -> Dict[str, Any]:
    """
    Get a comprehensive energy/carbon profile for a country — CO2, GHG,
    renewable share, fossil fuel dependency, and forest coverage.

    Args:
        country: ISO 2-letter country code.

    Returns:
        Dict with latest values for multiple climate/energy indicators.
    """
    try:
        profile = {}
        indicator_map = {
            "co2_total_mt": "co2_total",
            "ghg_total_mt": "ghg_total",
            "renewable_pct": "renewable_energy_pct",
            "fossil_fuel_pct": "fossil_fuel_pct",
            "forest_area_pct": "forest_area_pct",
            "energy_per_capita_kgoe": "energy_use_per_capita",
        }
        for key, ind_key in indicator_map.items():
            records = _fetch_indicator(country, INDICATORS[ind_key], 1)
            if records:
                profile[key] = {"value": records[0]["value"], "year": records[0]["date"]}
            else:
                profile[key] = {"value": None, "year": None}

        return {
            "country": country.upper(),
            "profile": profile,
            "source": "World Bank Climate Indicators",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def compare_countries(countries: List[str] = None, indicator: str = "co2_total") -> Dict[str, Any]:
    """
    Compare multiple countries on a carbon/climate indicator.

    Args:
        countries: List of ISO 2-letter codes. Defaults to top emitters.
        indicator: One of: co2_total, ghg_total, co2_per_capita,
                   renewable_energy_pct, fossil_fuel_pct, forest_area_pct.

    Returns:
        Dict with latest value for each country, sorted by value.
    """
    if countries is None:
        countries = ["US", "CN", "IN", "DE", "GB", "JP", "RU", "BR", "CA", "AU"]
    if indicator not in INDICATORS:
        return {"error": f"Unknown indicator '{indicator}'. Available: {list(INDICATORS.keys())}"}

    try:
        results = []
        for c in countries:
            records = _fetch_indicator(c, INDICATORS[indicator], 1)
            if records and records[0]["value"] is not None:
                results.append({
                    "country": c.upper(),
                    "value": records[0]["value"],
                    "year": records[0]["date"],
                })
        results.sort(key=lambda x: x["value"] or 0, reverse=True)
        return {
            "indicator": indicator,
            "indicator_id": INDICATORS[indicator],
            "count": len(results),
            "comparison": results,
            "source": "World Bank",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "source": "World Bank"}


def get_carbon_intensity_gdp(country: str = "US", years: int = 5) -> Dict[str, Any]:
    """
    Calculate carbon intensity of GDP (CO2 per $M GDP) for a country.

    Args:
        country: ISO 2-letter country code.
        years: Number of years to calculate.

    Returns:
        Dict with CO2/GDP ratio over time — key metric for decarbonization progress.
    """
    try:
        co2_data = _fetch_indicator(country, INDICATORS["co2_total"], years)
        gdp_data = _fetch_indicator(country, INDICATORS["gdp"], years)
        gdp_by_year = {r["date"]: r["value"] for r in gdp_data if r["value"]}
        intensity = []
        for r in co2_data:
            yr = r["date"]
            if yr in gdp_by_year and r["value"] and gdp_by_year[yr]:
                gdp_m = gdp_by_year[yr] / 1e6
                ratio = round(r["value"] / gdp_m, 4) if gdp_m > 0 else None
                intensity.append({
                    "year": yr,
                    "co2_mt": r["value"],
                    "gdp_usd_m": round(gdp_m, 1),
                    "co2_per_gdp_m": ratio,
                })
        return {
            "country": country.upper(),
            "indicator": "Carbon intensity of GDP",
            "unit": "Mt CO2e per $M GDP",
            "data": intensity,
            "count": len(intensity),
            "source": "World Bank (calculated)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


def get_methane_emissions(country: str = "US", years: int = 10) -> Dict[str, Any]:
    """
    Get methane (CH4) emissions for a country.

    Args:
        country: ISO 2-letter country code.
        years: Number of most recent years.

    Returns:
        Dict with methane emissions time series in Mt CO2e.
    """
    try:
        records = _fetch_indicator(country, INDICATORS["methane"], years)
        return {
            "country": country.upper(),
            "indicator": "Methane emissions (CH4)",
            "unit": "Mt CO2e",
            "data": records,
            "count": len(records),
            "source": "World Bank (EN.GHG.CH4.MT.CE.AR5)",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "country": country, "source": "World Bank"}


if __name__ == "__main__":
    print("=== US CO2 Emissions ===")
    print(json.dumps(get_co2_emissions("US", 3), indent=2, default=str))
    print("\n=== Country Comparison ===")
    print(json.dumps(compare_countries(["US", "CN", "DE"], "co2_total"), indent=2, default=str))
