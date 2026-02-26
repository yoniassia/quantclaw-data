"""
Commodity Spot vs Futures Basis Monitor — Track contango/backwardation across commodities.

Monitors the basis (spot - futures) spread for major commodities using
free data sources to identify roll yield opportunities and supply/demand signals.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Common commodity symbols and their futures contracts
COMMODITY_MAP = {
    "crude_oil": {"name": "WTI Crude Oil", "unit": "$/barrel", "yahoo": "CL=F", "spot_yahoo": "CL=F"},
    "gold": {"name": "Gold", "unit": "$/oz", "yahoo": "GC=F", "spot_yahoo": "GC=F"},
    "silver": {"name": "Silver", "unit": "$/oz", "yahoo": "SI=F", "spot_yahoo": "SI=F"},
    "natural_gas": {"name": "Natural Gas", "unit": "$/MMBtu", "yahoo": "NG=F", "spot_yahoo": "NG=F"},
    "copper": {"name": "Copper", "unit": "$/lb", "yahoo": "HG=F", "spot_yahoo": "HG=F"},
    "corn": {"name": "Corn", "unit": "¢/bushel", "yahoo": "ZC=F", "spot_yahoo": "ZC=F"},
    "soybeans": {"name": "Soybeans", "unit": "¢/bushel", "yahoo": "ZS=F", "spot_yahoo": "ZS=F"},
    "wheat": {"name": "Wheat", "unit": "¢/bushel", "yahoo": "ZW=F", "spot_yahoo": "ZW=F"},
}


def calculate_basis(spot_price: float, futures_price: float, days_to_expiry: int) -> Dict:
    """
    Calculate the spot-futures basis and annualized carry.

    Args:
        spot_price: Current spot price
        futures_price: Futures contract price
        days_to_expiry: Days until futures expiration

    Returns:
        Dict with basis calculations including annualized carry yield
    """
    if spot_price <= 0 or futures_price <= 0:
        return {"error": "Prices must be positive"}
    if days_to_expiry <= 0:
        return {"error": "Days to expiry must be positive"}

    basis = spot_price - futures_price
    basis_pct = (basis / spot_price) * 100
    annualized_carry = basis_pct * (365 / days_to_expiry)

    structure = "BACKWARDATION" if basis > 0 else "CONTANGO" if basis < 0 else "FLAT"

    return {
        "spot_price": spot_price,
        "futures_price": futures_price,
        "days_to_expiry": days_to_expiry,
        "basis": round(basis, 4),
        "basis_pct": round(basis_pct, 4),
        "annualized_carry_pct": round(annualized_carry, 4),
        "term_structure": structure,
        "roll_yield_signal": {
            "BACKWARDATION": "POSITIVE — long futures earns roll yield as contracts converge up to spot",
            "CONTANGO": "NEGATIVE — long futures loses on roll as contracts converge down to spot",
            "FLAT": "NEUTRAL — no roll yield",
        }[structure],
        "supply_demand_signal": {
            "BACKWARDATION": "Tight supply / strong demand — market paying premium for immediate delivery",
            "CONTANGO": "Adequate supply / weak demand — storage costs push futures above spot",
            "FLAT": "Balanced market",
        }[structure],
    }


def get_commodity_basis_dashboard(commodities: Optional[List[str]] = None) -> Dict:
    """
    Generate a basis dashboard for multiple commodities using estimated data.

    Provides spot vs front-month futures comparison for major commodities.

    Args:
        commodities: List of commodity keys (default: all major commodities)

    Returns:
        Dict with basis analysis for each commodity
    """
    if commodities is None:
        commodities = list(COMMODITY_MAP.keys())

    results = {}
    for commodity in commodities:
        info = COMMODITY_MAP.get(commodity)
        if not info:
            results[commodity] = {"error": f"Unknown commodity: {commodity}"}
            continue

        # Try to fetch from Yahoo Finance API
        try:
            symbol = info["yahoo"]
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                f"?interval=1d&range=5d"
            )
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (QuantClaw/1.0)",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("chartPreviousClose", 0)

            if price:
                results[commodity] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "front_month_price": price,
                    "prev_close": prev_close,
                    "daily_change_pct": round((price - prev_close) / prev_close * 100, 2) if prev_close else None,
                    "source": "Yahoo Finance (front-month futures)",
                    "note": "Spot-futures basis requires both spot and deferred month data",
                }
            else:
                results[commodity] = {"name": info["name"], "error": "No price data"}

        except Exception as e:
            results[commodity] = {"name": info["name"], "error": str(e)}

    return {
        "dashboard": results,
        "commodities_tracked": len(results),
        "generated_at": datetime.now().isoformat(),
    }


def analyze_term_structure(
    contract_prices: List[Dict],
) -> Dict:
    """
    Analyze the futures term structure from a list of contract prices.

    Args:
        contract_prices: List of dicts with 'month' (YYYY-MM), 'price', 'expiry_date'
            sorted by expiry date (nearest first)

    Returns:
        Dict with term structure analysis including curve shape and calendar spreads
    """
    if len(contract_prices) < 2:
        return {"error": "Need at least 2 contract months"}

    # Sort by expiry
    contracts = sorted(contract_prices, key=lambda x: x.get("month", ""))

    # Overall structure
    front = contracts[0]["price"]
    back = contracts[-1]["price"]
    overall = "BACKWARDATION" if front > back else "CONTANGO" if front < back else "FLAT"

    # Calendar spreads
    spreads = []
    for i in range(len(contracts) - 1):
        near = contracts[i]
        far = contracts[i + 1]
        spread = near["price"] - far["price"]
        spreads.append({
            "near_month": near["month"],
            "far_month": far["month"],
            "near_price": near["price"],
            "far_price": far["price"],
            "spread": round(spread, 4),
            "spread_pct": round(spread / near["price"] * 100, 4) if near["price"] else 0,
            "structure": "BACKWARDATION" if spread > 0 else "CONTANGO",
        })

    # Curve steepness
    total_spread = front - back
    months_span = len(contracts) - 1
    avg_monthly_spread = total_spread / months_span if months_span else 0

    return {
        "overall_structure": overall,
        "front_price": front,
        "back_price": back,
        "total_spread": round(total_spread, 4),
        "total_spread_pct": round(total_spread / front * 100, 4) if front else 0,
        "avg_monthly_spread": round(avg_monthly_spread, 4),
        "contracts": len(contracts),
        "calendar_spreads": spreads,
        "curve_assessment": (
            "STEEP BACKWARDATION" if avg_monthly_spread > front * 0.02 else
            "MILD BACKWARDATION" if avg_monthly_spread > 0 else
            "FLAT" if abs(avg_monthly_spread) < front * 0.001 else
            "MILD CONTANGO" if avg_monthly_spread > -front * 0.02 else
            "STEEP CONTANGO"
        ),
    }
