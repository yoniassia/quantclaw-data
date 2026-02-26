"""
Sovereign Debt Sustainability Scorer — Roadmap #270

Scores sovereign debt sustainability using debt/GDP, interest/revenue,
primary balance, and growth-adjusted metrics. Uses free World Bank
and IMF data.

Sources:
- World Bank API (debt indicators)
- IMF World Economic Outlook (via API)
- FRED for US-specific data
"""

import json
import urllib.request
from typing import Dict, List, Optional


WORLDBANK_BASE = "https://api.worldbank.org/v2"

# Key World Bank indicators
INDICATORS = {
    "debt_to_gdp": "GC.DOD.TOTL.GD.ZS",           # Central government debt (% GDP)
    "interest_payments_pct_revenue": "GC.XPN.INTP.RV.ZS",  # Interest payments (% revenue)
    "primary_balance_pct_gdp": "GC.NLD.TOTL.GD.ZS",  # Net lending (+) / borrowing (-)
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",               # GDP growth (annual %)
    "inflation": "FP.CPI.TOTL.ZG",                    # Consumer price inflation
    "external_debt_pct_gni": "DT.DOD.DECT.GN.ZS",   # External debt stocks (% GNI)
}

SCORED_COUNTRIES = [
    "USA", "JPN", "GBR", "DEU", "FRA", "ITA", "ESP", "GRC",
    "CHN", "IND", "BRA", "MEX", "ZAF", "TUR", "ARG", "EGY",
    "NGA", "IDN", "KOR", "CAN", "AUS",
]


def fetch_indicator(indicator_key: str, countries: List[str], years: int = 5) -> List[Dict]:
    """
    Fetch a World Bank indicator for given countries.
    """
    indicator_id = INDICATORS.get(indicator_key, indicator_key)
    country_str = ";".join(countries)
    url = (
        f"{WORLDBANK_BASE}/country/{country_str}/indicator/{indicator_id}"
        f"?format=json&per_page=500&mrv={years}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return []

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
                "value": round(float(val), 2),
            })
    return results


def score_debt_sustainability(iso3: str = "USA") -> Dict:
    """
    Compute a composite debt sustainability score (0-100) for a country.

    Scoring methodology:
    - Debt/GDP: <60% = 25pts, 60-90% = 15pts, 90-120% = 5pts, >120% = 0pts
    - Interest/Revenue: <10% = 25pts, 10-20% = 15pts, >20% = 0pts
    - GDP Growth: >3% = 25pts, 1-3% = 15pts, <1% = 5pts, negative = 0pts
    - Debt trajectory (improving?) = 25pts

    Returns score, components, and risk rating.
    """
    metrics = {}
    for key in ["debt_to_gdp", "interest_payments_pct_revenue", "gdp_growth"]:
        data = fetch_indicator(key, [iso3], years=3)
        latest = sorted([d for d in data if d["iso3"] == iso3], key=lambda x: x["year"])
        if latest:
            metrics[key] = latest[-1]["value"]
            if len(latest) >= 2:
                metrics[f"{key}_prev"] = latest[-2]["value"]

    score = 0
    components = {}

    # Debt/GDP score
    d2g = metrics.get("debt_to_gdp")
    if d2g is not None:
        if d2g < 60:
            pts = 25
        elif d2g < 90:
            pts = 15
        elif d2g < 120:
            pts = 5
        else:
            pts = 0
        score += pts
        components["debt_to_gdp"] = {"value": d2g, "score": pts, "max": 25}

    # Interest/Revenue score
    i2r = metrics.get("interest_payments_pct_revenue")
    if i2r is not None:
        if i2r < 10:
            pts = 25
        elif i2r < 20:
            pts = 15
        else:
            pts = 0
        score += pts
        components["interest_to_revenue"] = {"value": i2r, "score": pts, "max": 25}

    # GDP Growth score
    growth = metrics.get("gdp_growth")
    if growth is not None:
        if growth > 3:
            pts = 25
        elif growth > 1:
            pts = 15
        elif growth > 0:
            pts = 5
        else:
            pts = 0
        score += pts
        components["gdp_growth"] = {"value": growth, "score": pts, "max": 25}

    # Trajectory score
    d2g_prev = metrics.get("debt_to_gdp_prev")
    if d2g is not None and d2g_prev is not None:
        improving = d2g < d2g_prev
        pts = 25 if improving else 0
        score += pts
        components["trajectory"] = {
            "improving": improving,
            "change": round(d2g - d2g_prev, 2),
            "score": pts,
            "max": 25,
        }

    # Risk rating
    if score >= 75:
        rating = "LOW_RISK"
    elif score >= 50:
        rating = "MODERATE_RISK"
    elif score >= 25:
        rating = "HIGH_RISK"
    else:
        rating = "CRITICAL_RISK"

    return {
        "country": iso3,
        "sustainability_score": score,
        "max_score": 100,
        "risk_rating": rating,
        "components": components,
    }


def rank_all_countries() -> List[Dict]:
    """
    Score and rank all tracked countries by debt sustainability.
    Returns sorted list from most to least sustainable.
    """
    results = []
    for iso3 in SCORED_COUNTRIES:
        try:
            result = score_debt_sustainability(iso3)
            results.append(result)
        except Exception:
            continue

    return sorted(results, key=lambda x: x["sustainability_score"], reverse=True)


def detect_debt_distress_signals(iso3: str = "ARG") -> Dict:
    """
    Check for debt distress warning signals:
    - Debt/GDP > 100%
    - Interest/Revenue > 25%
    - Negative GDP growth
    - Rising debt trajectory
    """
    score_data = score_debt_sustainability(iso3)
    components = score_data.get("components", {})

    signals = []
    if components.get("debt_to_gdp", {}).get("value", 0) > 100:
        signals.append("EXCESSIVE_DEBT: Debt/GDP exceeds 100%")
    if components.get("interest_to_revenue", {}).get("value", 0) > 25:
        signals.append("INTEREST_BURDEN: Interest exceeds 25% of revenue")
    if components.get("gdp_growth", {}).get("value", 1) < 0:
        signals.append("RECESSION: Negative GDP growth")
    if components.get("trajectory", {}).get("improving") is False:
        signals.append("RISING_DEBT: Debt trajectory worsening")

    return {
        "country": iso3,
        "distress_signals": signals,
        "signal_count": len(signals),
        "risk_level": "CRITICAL" if len(signals) >= 3 else "WARNING" if len(signals) >= 2 else "MONITOR" if signals else "CLEAR",
        "score": score_data,
    }
