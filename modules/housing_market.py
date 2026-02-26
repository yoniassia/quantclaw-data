"""
Housing Market Dashboard — US residential real estate indicators.

Tracks Case-Shiller home price indices, housing starts, building permits,
existing/new home sales, mortgage rates, housing affordability, and
inventory levels using FRED and other free data sources.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# FRED series for housing indicators
HOUSING_SERIES = {
    "CSUSHPINSA": "S&P/Case-Shiller US National Home Price Index",
    "HOUST": "Housing Starts (thousands, SAAR)",
    "PERMIT": "Building Permits (thousands, SAAR)",
    "EXHOSLUSM495S": "Existing Home Sales (millions, SAAR)",
    "HSN1F": "New One-Family Houses Sold (thousands, SAAR)",
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate (%)",
    "MSACSR": "Monthly Supply of New Houses (months)",
    "MSPUS": "Median Sales Price of Houses Sold (USD)",
    "RHORUSQ156N": "Homeownership Rate (%)",
    "FIXHAI": "Housing Affordability Index",
}


def _fetch_fred(series_id: str, limit: int = 12) -> list[dict]:
    """Fetch recent observations from FRED."""
    url = (
        f"https://api.stlouisfed.org/fred/series/observations?"
        f"series_id={series_id}&sort_order=desc&limit={limit}"
        f"&file_type=json&api_key=DEMO_KEY"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return [
            {"date": o["date"], "value": float(o["value"])}
            for o in data.get("observations", [])
            if o.get("value", ".") != "."
        ]
    except Exception:
        return []


def get_housing_dashboard() -> dict[str, Any]:
    """
    Fetch a comprehensive US housing market dashboard.

    Returns latest values for key housing indicators including prices,
    starts, permits, sales, mortgage rates, and affordability.
    """
    dashboard = {}
    for series_id, name in HOUSING_SERIES.items():
        obs = _fetch_fred(series_id, limit=2)
        if obs:
            latest = obs[0]
            prev = obs[1] if len(obs) > 1 else None
            entry = {
                "name": name,
                "latest_value": latest["value"],
                "latest_date": latest["date"],
            }
            if prev:
                change = latest["value"] - prev["value"]
                pct = (change / prev["value"] * 100) if prev["value"] != 0 else 0
                entry["mom_change"] = round(change, 2)
                entry["mom_change_pct"] = round(pct, 2)
            dashboard[series_id] = entry

    return {
        "dashboard": dashboard,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "FRED (Federal Reserve Economic Data)",
    }


def get_home_price_trends(months: int = 24) -> dict[str, Any]:
    """
    Analyze home price trends using Case-Shiller index.

    Fetches national home price index data and calculates year-over-year
    appreciation, cumulative change, and trend direction.

    Args:
        months: Number of months of history to analyze.
    """
    obs = _fetch_fred("CSUSHPINSA", limit=months)
    if not obs:
        return {"error": "Unable to fetch Case-Shiller data", "status": "unavailable"}

    obs.reverse()  # oldest first
    latest = obs[-1]["value"]
    earliest = obs[0]["value"]

    # YoY if we have 12+ months
    yoy = None
    if len(obs) >= 13:
        year_ago = obs[-13]["value"]
        yoy = round((latest / year_ago - 1) * 100, 2)

    cumulative = round((latest / earliest - 1) * 100, 2)

    # Simple trend detection
    if len(obs) >= 6:
        recent_avg = sum(o["value"] for o in obs[-3:]) / 3
        prior_avg = sum(o["value"] for o in obs[-6:-3]) / 3
        trend = "accelerating" if recent_avg > prior_avg else "decelerating"
    else:
        trend = "insufficient data"

    return {
        "index_name": "S&P/Case-Shiller US National Home Price Index",
        "latest_value": latest,
        "latest_date": obs[-1]["date"],
        "yoy_change_pct": yoy,
        "cumulative_change_pct": cumulative,
        "period_months": len(obs),
        "trend": trend,
        "data_points": obs[-6:],  # last 6 months
    }


def get_mortgage_rate_impact(home_price: float = 400000, down_pct: float = 20) -> dict[str, Any]:
    """
    Calculate mortgage payment impact at current rates.

    Shows monthly payment, total interest, and comparison to historical
    average rates.

    Args:
        home_price: Home purchase price in USD.
        down_pct: Down payment percentage.
    """
    obs = _fetch_fred("MORTGAGE30US", limit=1)
    current_rate = obs[0]["value"] / 100 if obs else 0.07

    down_payment = home_price * down_pct / 100
    loan_amount = home_price - down_payment
    monthly_rate = current_rate / 12
    n_payments = 360  # 30 years

    if monthly_rate > 0:
        payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / \
                  ((1 + monthly_rate)**n_payments - 1)
    else:
        payment = loan_amount / n_payments

    total_paid = payment * n_payments
    total_interest = total_paid - loan_amount

    # Compare to historical average (~5.5%)
    hist_rate = 0.055 / 12
    hist_payment = loan_amount * (hist_rate * (1 + hist_rate)**n_payments) / \
                   ((1 + hist_rate)**n_payments - 1)

    return {
        "home_price": home_price,
        "down_payment": down_payment,
        "loan_amount": loan_amount,
        "current_rate_pct": round(current_rate * 100, 2),
        "monthly_payment": round(payment, 2),
        "total_interest": round(total_interest, 2),
        "total_cost": round(total_paid, 2),
        "vs_historical_avg": {
            "historical_rate_pct": 5.5,
            "historical_monthly_payment": round(hist_payment, 2),
            "extra_monthly_cost": round(payment - hist_payment, 2),
            "extra_total_cost": round((payment - hist_payment) * 360, 2),
        },
    }


def get_housing_supply_demand() -> dict[str, Any]:
    """
    Analyze housing supply-demand dynamics.

    Compares new construction (starts + permits) against sales activity
    to gauge market tightness.
    """
    starts = _fetch_fred("HOUST", limit=6)
    permits = _fetch_fred("PERMIT", limit=6)
    supply = _fetch_fred("MSACSR", limit=6)
    new_sales = _fetch_fred("HSN1F", limit=6)

    result = {}
    if starts:
        result["housing_starts_k"] = starts[0]["value"]
    if permits:
        result["building_permits_k"] = permits[0]["value"]
    if supply:
        months_supply = supply[0]["value"]
        result["months_supply"] = months_supply
        if months_supply < 4:
            result["market_condition"] = "TIGHT (seller's market)"
        elif months_supply > 6:
            result["market_condition"] = "LOOSE (buyer's market)"
        else:
            result["market_condition"] = "BALANCED"
    if new_sales:
        result["new_home_sales_k"] = new_sales[0]["value"]

    result["source"] = "FRED"
    result["timestamp"] = datetime.utcnow().isoformat()
    return result
