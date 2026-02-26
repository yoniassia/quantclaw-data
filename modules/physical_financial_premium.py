"""
Physical vs Financial Premium Tracker — Monitor the premium/discount
between physical commodity prices and financial (futures/ETF) prices.
Key indicator for supply chain stress, delivery bottlenecks, and
real economy vs financial economy divergence.

Uses free data from Yahoo Finance and commodity ETF NAVs.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


# Commodity physical vs financial proxies
COMMODITY_PAIRS = {
    "gold": {
        "name": "Gold",
        "physical_proxy": "GLD",      # SPDR Gold (tracks physical)
        "financial_proxy": "GC=F",     # Gold futures
        "unit": "$/oz",
        "conversion": 1 / 10,          # GLD = 1/10 oz gold
    },
    "silver": {
        "name": "Silver",
        "physical_proxy": "SLV",
        "financial_proxy": "SI=F",
        "unit": "$/oz",
        "conversion": 1.0,
    },
    "crude_oil": {
        "name": "WTI Crude Oil",
        "physical_proxy": "USO",
        "financial_proxy": "CL=F",
        "unit": "$/bbl",
        "conversion": 1.0,
    },
    "natural_gas": {
        "name": "Natural Gas",
        "physical_proxy": "UNG",
        "financial_proxy": "NG=F",
        "unit": "$/MMBtu",
        "conversion": 1.0,
    },
    "copper": {
        "name": "Copper",
        "physical_proxy": "CPER",
        "financial_proxy": "HG=F",
        "unit": "$/lb",
        "conversion": 1.0,
    },
}


def _fetch_price(symbol: str) -> Optional[float]:
    """Fetch latest price from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (QuantClaw/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        for c in reversed(closes):
            if c is not None:
                return round(c, 4)
        return None
    except Exception:
        return None


def get_premium_for_commodity(commodity: str) -> Dict:
    """
    Calculate the physical vs financial premium/discount for a commodity.

    Args:
        commodity: Key from COMMODITY_PAIRS (e.g., 'gold', 'crude_oil')

    Returns:
        Dict with physical price proxy, futures price, premium/discount
    """
    if commodity not in COMMODITY_PAIRS:
        return {"error": f"Unknown commodity. Choose from: {list(COMMODITY_PAIRS.keys())}"}

    pair = COMMODITY_PAIRS[commodity]
    phys_price = _fetch_price(pair["physical_proxy"])
    fin_price = _fetch_price(pair["financial_proxy"])

    if phys_price is None or fin_price is None:
        return {
            "commodity": pair["name"],
            "error": "Price data unavailable",
            "physical_proxy": pair["physical_proxy"],
            "financial_proxy": pair["financial_proxy"],
        }

    # Premium = (physical - financial) / financial * 100
    premium_pct = (phys_price - fin_price) / fin_price * 100 if fin_price != 0 else 0

    if premium_pct > 1.0:
        condition = "PHYSICAL_PREMIUM"
        interpretation = "Physical scarcity — delivery demand exceeds paper market"
    elif premium_pct < -1.0:
        condition = "FINANCIAL_PREMIUM"
        interpretation = "Financial speculation — futures priced above physical delivery"
    else:
        condition = "CONVERGENCE"
        interpretation = "Physical and financial markets aligned"

    return {
        "commodity": pair["name"],
        "physical_proxy": pair["physical_proxy"],
        "physical_price": phys_price,
        "financial_proxy": pair["financial_proxy"],
        "financial_price": fin_price,
        "premium_pct": round(premium_pct, 3),
        "condition": condition,
        "interpretation": interpretation,
        "unit": pair["unit"],
        "retrieved_at": datetime.utcnow().isoformat(),
    }


def scan_all_premiums() -> Dict:
    """
    Scan all tracked commodities for physical vs financial premiums.

    Returns:
        Dict with per-commodity premium data and market stress summary
    """
    results = {}
    stress_count = 0

    for key in COMMODITY_PAIRS:
        result = get_premium_for_commodity(key)
        results[key] = result
        if result.get("condition") == "PHYSICAL_PREMIUM":
            stress_count += 1

    total = len(COMMODITY_PAIRS)
    stress_level = "HIGH" if stress_count >= 3 else "MODERATE" if stress_count >= 1 else "LOW"

    return {
        "premiums": results,
        "summary": {
            "total_scanned": total,
            "physical_premium_count": stress_count,
            "supply_stress_level": stress_level,
        },
        "scanned_at": datetime.utcnow().isoformat(),
    }


def get_historical_premium_context(commodity: str = "gold") -> Dict:
    """
    Provide historical context for physical/financial premiums.
    
    Args:
        commodity: Commodity to analyze

    Returns:
        Dict with historical premium episodes and current assessment
    """
    current = get_premium_for_commodity(commodity)

    # Historical notable episodes
    episodes = {
        "gold": [
            {"period": "2020-03", "event": "COVID crash", "premium_pct": 4.5, "note": "GLD premium spiked as physical delivery seized up"},
            {"period": "2008-10", "event": "GFC", "premium_pct": 3.2, "note": "Physical gold premium vs futures during Lehman"},
            {"period": "2013-04", "event": "Gold crash", "premium_pct": -2.1, "note": "Futures sold off faster than physical"},
        ],
        "crude_oil": [
            {"period": "2020-04", "event": "WTI negative", "premium_pct": -300, "note": "Futures went negative, physical held ~$20"},
            {"period": "2022-03", "event": "Russia-Ukraine", "premium_pct": 8.0, "note": "Physical premium on delivery fears"},
        ],
    }

    return {
        "commodity": commodity,
        "current": current,
        "historical_episodes": episodes.get(commodity, []),
        "note": "Historical episodes are illustrative benchmarks",
    }
