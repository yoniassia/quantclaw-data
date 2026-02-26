"""
Big Mac Index Calculator — Roadmap #266

Computes purchasing power parity (PPP) implied exchange rates using
The Economist's Big Mac Index methodology. Uses free GitHub-hosted
historical Big Mac data and FRED for current exchange rates.

Sources:
- The Economist Big Mac Index (GitHub CSV)
- FRED for nominal exchange rates
"""

import csv
import io
import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


BMI_CSV_URL = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def fetch_big_mac_data(limit: int = 200) -> List[Dict]:
    """
    Fetch latest Big Mac Index data from The Economist's open dataset.

    Returns list of dicts with country, local_price, dollar_ex, dollar_price,
    raw_index (over/undervaluation vs USD), and date.
    """
    req = urllib.request.Request(BMI_CSV_URL, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    # Get the most recent date
    dates = sorted(set(r.get("date", "") for r in rows if r.get("date")))
    if not dates:
        return []

    latest_date = dates[-1]
    latest = [r for r in rows if r.get("date") == latest_date]

    results = []
    for r in latest[:limit]:
        try:
            local_price = float(r.get("local_price", 0))
            dollar_ex = float(r.get("dollar_ex", 1))
            dollar_price = float(r.get("dollar_price", 0))
            raw_index = float(r.get("USD_raw", 0)) if r.get("USD_raw") else None
            adj_index = float(r.get("USD_adjusted", 0)) if r.get("USD_adjusted") else None
        except (ValueError, TypeError):
            continue

        results.append({
            "country": r.get("name", "Unknown"),
            "iso_a3": r.get("iso_a3", ""),
            "currency_code": r.get("currency_code", ""),
            "local_price": round(local_price, 2),
            "dollar_exchange_rate": round(dollar_ex, 4),
            "dollar_price": round(dollar_price, 2),
            "implied_ppp_rate": round(local_price / 5.69, 4) if dollar_price else None,  # vs US price
            "raw_index_pct": round(raw_index * 100, 1) if raw_index is not None else None,
            "gdp_adjusted_index_pct": round(adj_index * 100, 1) if adj_index is not None else None,
            "date": latest_date,
        })

    return sorted(results, key=lambda x: x.get("raw_index_pct") or 0)


def get_most_undervalued(top_n: int = 10) -> List[Dict]:
    """
    Return the top N most undervalued currencies vs USD
    based on the raw Big Mac Index.
    """
    data = fetch_big_mac_data()
    undervalued = [d for d in data if d.get("raw_index_pct") is not None and d["raw_index_pct"] < 0]
    return undervalued[:top_n]


def get_most_overvalued(top_n: int = 10) -> List[Dict]:
    """
    Return the top N most overvalued currencies vs USD
    based on the raw Big Mac Index.
    """
    data = fetch_big_mac_data()
    overvalued = [d for d in data if d.get("raw_index_pct") is not None and d["raw_index_pct"] > 0]
    return list(reversed(overvalued))[:top_n]


def compare_currencies(country_a: str, country_b: str) -> Dict:
    """
    Compare Big Mac implied exchange rate between two countries.
    Returns implied rate, actual rate, and mis-valuation.
    """
    data = fetch_big_mac_data()
    a = next((d for d in data if d["country"].lower() == country_a.lower()), None)
    b = next((d for d in data if d["country"].lower() == country_b.lower()), None)

    if not a or not b:
        return {"error": f"Country not found. Available: {[d['country'] for d in data[:10]]}..."}

    if a["local_price"] and b["local_price"]:
        implied_rate = a["local_price"] / b["local_price"]
        actual_rate = a["dollar_exchange_rate"] / b["dollar_exchange_rate"]
        misvaluation = ((implied_rate / actual_rate) - 1) * 100
    else:
        implied_rate = actual_rate = misvaluation = None

    return {
        "country_a": a["country"],
        "country_b": b["country"],
        "implied_exchange_rate": round(implied_rate, 4) if implied_rate else None,
        "actual_exchange_rate": round(actual_rate, 4) if actual_rate else None,
        "a_vs_b_misvaluation_pct": round(misvaluation, 1) if misvaluation else None,
        "date": a.get("date"),
    }
