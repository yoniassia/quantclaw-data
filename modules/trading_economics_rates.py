#!/usr/bin/env python3
"""
Trading Economics Rates Module

Access global interest rates, bond yields, currency rates, commodity prices,
and stock market indices via Trading Economics free API (guest access).

Data Source: api.tradingeconomics.com (guest:guest free tier)
Categories: Bonds, Currencies, Commodities, Indices
Refresh: Real-time to daily
Coverage: 196 countries, 300+ indicators

Author: QUANTCLAW DATA NightBuilder
Built: 2026-03-06
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "https://api.tradingeconomics.com"
GUEST_AUTH = "guest:guest"


def _get(endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
    """Make authenticated GET request to Trading Economics API."""
    url = f"{BASE_URL}{endpoint}"
    if params is None:
        params = {}
    params["c"] = GUEST_AUTH
    params["f"] = "json"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return [data] if data else []
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]
    except json.JSONDecodeError:
        return [{"error": "Invalid JSON response"}]


def get_global_bonds() -> List[Dict]:
    """Get global government bond yields across all regions.

    Returns list of bond instruments with current yields,
    daily/weekly/monthly/yearly changes.
    """
    return _get("/markets/bonds")


def get_global_commodities() -> List[Dict]:
    """Get global commodity prices (agricultural, energy, metals).

    Returns list of commodity instruments with current prices and changes.
    """
    return _get("/markets/commodities")


def get_global_currencies() -> List[Dict]:
    """Get global currency exchange rates.

    Returns list of currency pairs with current rates and changes.
    """
    return _get("/markets/currency")


def get_global_indices() -> List[Dict]:
    """Get global stock market indices.

    Returns list of major indices with current values and changes.
    """
    return _get("/markets/index")


def get_market_overview() -> Dict:
    """Get a combined overview of all market categories.

    Returns dict with bonds, commodities, currencies, and indices.
    """
    return {
        "bonds": get_global_bonds(),
        "commodities": get_global_commodities(),
        "currencies": get_global_currencies(),
        "indices": get_global_indices(),
        "timestamp": datetime.utcnow().isoformat()
    }


def search_market(query: str) -> List[Dict]:
    """Search across all market categories for a specific instrument.

    Args:
        query: Search term (e.g., 'US 10Y', 'Gold', 'EURUSD', 'S&P')

    Returns list of matching instruments.
    """
    query_lower = query.lower()
    results = []
    for category, fetcher in [
        ("bonds", get_global_bonds),
        ("commodities", get_global_commodities),
        ("currencies", get_global_currencies),
        ("indices", get_global_indices),
    ]:
        try:
            data = fetcher()
            for item in data:
                if isinstance(item, dict) and not item.get("error"):
                    name = (item.get("Name", "") or "").lower()
                    symbol = (item.get("Symbol", "") or "").lower()
                    country = (item.get("Country", "") or "").lower()
                    if query_lower in name or query_lower in symbol or query_lower in country:
                        item["_category"] = category
                        results.append(item)
        except Exception:
            continue
    return results


def get_country_bonds(country: str = "united states") -> List[Dict]:
    """Get bond yields for a specific country.

    Args:
        country: Country name (e.g., 'united states', 'germany', 'japan')
    """
    bonds = get_global_bonds()
    country_lower = country.lower()
    return [b for b in bonds if isinstance(b, dict)
            and country_lower in (b.get("Country", "") or "").lower()]


def get_bond_spreads() -> List[Dict]:
    """Calculate yield spreads between major economies vs US.

    Returns list of spread calculations for key bond markets.
    """
    bonds = get_global_bonds()
    us_10y = None
    other_bonds = []

    for b in bonds:
        if not isinstance(b, dict) or b.get("error"):
            continue
        name = (b.get("Name", "") or "").lower()
        country = (b.get("Country", "") or "").lower()
        if "united states" in country and "10y" in name:
            us_10y = b.get("Last")
        elif "10y" in name:
            other_bonds.append(b)

    if us_10y is None:
        return [{"error": "US 10Y not found in data"}]

    spreads = []
    for b in other_bonds:
        yield_val = b.get("Last")
        if yield_val is not None:
            spreads.append({
                "country": b.get("Country"),
                "name": b.get("Name"),
                "yield": yield_val,
                "us_10y": us_10y,
                "spread_bps": round((yield_val - us_10y) * 100, 1),
                "timestamp": b.get("Date")
            })
    spreads.sort(key=lambda x: x.get("spread_bps", 0), reverse=True)
    return spreads


def get_commodity_movers(direction: str = "top") -> List[Dict]:
    """Get top/bottom commodity price movers by daily change.

    Args:
        direction: 'top' for gainers, 'bottom' for losers
    """
    commodities = get_global_commodities()
    valid = [c for c in commodities if isinstance(c, dict)
             and not c.get("error") and c.get("DailyPercentualChange") is not None]
    reverse = direction.lower() == "top"
    valid.sort(key=lambda x: x.get("DailyPercentualChange", 0), reverse=reverse)
    return valid[:10]


def format_market_summary(data: List[Dict]) -> str:
    """Format market data into a readable text summary.

    Args:
        data: List of market instrument dicts
    """
    lines = []
    for item in data:
        if isinstance(item, dict) and not item.get("error"):
            name = item.get("Name", "Unknown")
            last = item.get("Last", "N/A")
            change = item.get("DailyPercentualChange", 0)
            arrow = "▲" if change >= 0 else "▼"
            lines.append(f"{name}: {last} {arrow} {abs(change):.2f}%")
    return "\n".join(lines) if lines else "No data available"


if __name__ == "__main__":
    print("=== Trading Economics Rates Module ===")
    bonds = get_global_bonds()
    print(f"Bonds: {len(bonds)} instruments")
    if bonds and not bonds[0].get("error"):
        print(f"Sample: {bonds[0].get('Name')} = {bonds[0].get('Last')}")
