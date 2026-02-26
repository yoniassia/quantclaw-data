"""
Capital Flow Monitor — Roadmap #269

Tracks international capital flows using US Treasury TIC data
and BIS banking statistics. Monitors foreign holdings of US
securities and cross-border capital movements.

Sources:
- US Treasury TIC (Treasury International Capital) via FRED
- BIS International Banking Statistics (free CSV)
- World Bank capital flow indicators
"""

import json
import urllib.request
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Key TIC series on FRED
TIC_SERIES = {
    "foreign_holdings_treasuries": "FDHBFIN",      # Foreign holders of US Treasury securities
    "foreign_holdings_agency": "FDHBFINA",          # Agency bonds
    "japan_treasury_holdings": "FDHBJPN",           # Japan holdings
    "china_treasury_holdings": "FDHBCHN",           # China holdings
    "uk_treasury_holdings": "FDHBGBR",              # UK holdings
    "net_tic_flows": "BOPTICP",                     # Net TIC flows
}

# World Bank capital flow indicators
WB_INDICATORS = {
    "fdi_net_inflows_pct_gdp": "BX.KLT.DINV.WD.GD.ZS",
    "portfolio_equity_net": "BX.PEF.TOTL.CD.WD",
    "remittances_received": "BX.TRF.PWKR.CD.DT",
}


def fetch_tic_data(series_key: str = "foreign_holdings_treasuries", limit: int = 60) -> List[Dict]:
    """
    Fetch Treasury International Capital (TIC) data from FRED.

    Args:
        series_key: one of the TIC_SERIES keys
        limit: number of observations (monthly)

    Returns:
        List of {date, value_billions, series}
    """
    series_id = TIC_SERIES.get(series_key, series_key)
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&sort_order=desc&limit={limit}&file_type=json"
        f"&api_key=DEMO_KEY"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return [{"error": str(e)}]

    results = []
    for obs in data.get("observations", []):
        if obs.get("value") and obs["value"] != ".":
            try:
                val = float(obs["value"])
                results.append({
                    "date": obs["date"],
                    "value_billions": round(val / 1000, 2) if val > 1000 else round(val, 2),
                    "raw_value": val,
                    "series": series_key,
                })
            except ValueError:
                continue

    return results


def get_major_holders_summary() -> Dict:
    """
    Get summary of major foreign holders of US Treasury securities.
    Returns latest holdings for top holder countries.
    """
    holders = {}
    for key in ["japan_treasury_holdings", "china_treasury_holdings", "uk_treasury_holdings"]:
        data = fetch_tic_data(key, limit=1)
        if data and "error" not in data[0]:
            holders[key.replace("_treasury_holdings", "")] = data[0]

    total = fetch_tic_data("foreign_holdings_treasuries", limit=1)
    if total and "error" not in total[0]:
        holders["total_foreign"] = total[0]

    return {
        "summary": "Major foreign holders of US Treasury securities",
        "holders": holders,
    }


def fetch_fdi_flows(countries: Optional[List[str]] = None, years: int = 5) -> List[Dict]:
    """
    Fetch Foreign Direct Investment net inflows (% of GDP) from World Bank.
    """
    if countries is None:
        countries = ["USA", "CHN", "GBR", "DEU", "JPN", "IND", "BRA", "SGP", "HKG", "NLD"]

    country_str = ";".join(countries)
    indicator = WB_INDICATORS["fdi_net_inflows_pct_gdp"]
    url = (
        f"https://api.worldbank.org/v2/country/{country_str}/indicator/{indicator}"
        f"?format=json&per_page=200&mrv={years}"
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
            results.append({
                "country": entry["country"]["value"],
                "iso3": entry["countryiso3code"],
                "year": int(entry["date"]),
                "fdi_pct_gdp": round(float(val), 2),
            })

    return sorted(results, key=lambda x: (x["year"], -x["fdi_pct_gdp"]), reverse=True)


def detect_capital_flight(iso3: str = "CHN", years: int = 10) -> Dict:
    """
    Detect potential capital flight patterns by analyzing FDI trend
    reversals and large outflow periods.
    """
    data = fetch_fdi_flows([iso3], years)
    country_data = sorted([d for d in data if d.get("iso3") == iso3], key=lambda x: x["year"])

    if len(country_data) < 3:
        return {"iso3": iso3, "warning": "insufficient data"}

    # Detect declining trend
    recent_3 = country_data[-3:]
    trend = [recent_3[i + 1]["fdi_pct_gdp"] - recent_3[i]["fdi_pct_gdp"] for i in range(len(recent_3) - 1)]
    declining = all(t < 0 for t in trend)

    avg_early = sum(d["fdi_pct_gdp"] for d in country_data[:3]) / 3
    avg_late = sum(d["fdi_pct_gdp"] for d in country_data[-3:]) / 3

    return {
        "country": country_data[0].get("country", iso3),
        "iso3": iso3,
        "early_avg_fdi_pct": round(avg_early, 2),
        "recent_avg_fdi_pct": round(avg_late, 2),
        "consecutive_decline": declining,
        "capital_flight_risk": "elevated" if declining and avg_late < avg_early * 0.5 else "normal",
        "history": country_data,
    }
