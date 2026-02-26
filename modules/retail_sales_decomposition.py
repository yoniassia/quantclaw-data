"""
Retail Sales Decomposition — Online vs brick-and-mortar retail analysis.

Decomposes US retail sales into e-commerce vs physical store components,
tracks channel migration trends, seasonal patterns, and category-level
breakdowns using Census Bureau and FRED data.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# FRED series for retail data
RETAIL_SERIES = {
    "RSXFS": "Retail Sales ex Food Services (millions, SA)",
    "ECOMSA": "E-Commerce Retail Sales (millions, SA)",
    "ECOMPCTSA": "E-Commerce as % of Total Retail Sales",
    "MRTSSM44X72USS": "Total Retail Trade (millions, SA)",
    "RSGASSN": "Gasoline Station Sales (millions, SA)",
    "RSFSDPN": "Food Services & Drinking Places (millions, SA)",
    "RSDBS": "Department Store Sales (millions, SA)",
    "RSEAS": "Electronics & Appliance Store Sales (millions, SA)",
    "RSNSR": "Nonstore Retailers Sales (millions, SA)",
    "RSBMGESD": "Building Material & Garden Sales (millions, SA)",
}


def _fetch_fred(series_id: str, limit: int = 24) -> list[dict]:
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


def get_retail_decomposition() -> dict[str, Any]:
    """
    Decompose total retail sales into e-commerce vs physical channels.

    Returns current split, trend over time, and year-over-year growth
    for both channels.
    """
    ecom_pct_data = _fetch_fred("ECOMPCTSA", limit=8)
    ecom_data = _fetch_fred("ECOMSA", limit=8)
    total_data = _fetch_fred("RSXFS", limit=8)

    result = {"timestamp": datetime.utcnow().isoformat(), "source": "US Census Bureau / FRED"}

    if ecom_pct_data:
        latest_pct = ecom_pct_data[0]["value"]
        result["ecommerce_share_pct"] = latest_pct
        result["physical_store_share_pct"] = round(100 - latest_pct, 1)
        result["latest_date"] = ecom_pct_data[0]["date"]

        # YoY comparison (quarterly data, so 4 periods back)
        if len(ecom_pct_data) >= 5:
            yoy_pct = ecom_pct_data[4]["value"]
            result["ecommerce_share_yoy_change_pp"] = round(latest_pct - yoy_pct, 2)

    if ecom_data and total_data:
        ecom_val = ecom_data[0]["value"]
        total_val = total_data[0]["value"]
        physical_val = total_val - ecom_val

        result["ecommerce_sales_mn"] = ecom_val
        result["physical_sales_mn"] = round(physical_val, 1)
        result["total_retail_mn"] = total_val

        # Growth rates
        if len(ecom_data) >= 5 and len(total_data) >= 5:
            ecom_yoy = round((ecom_val / ecom_data[4]["value"] - 1) * 100, 1)
            total_yoy = round((total_val / total_data[4]["value"] - 1) * 100, 1)
            result["ecommerce_yoy_growth_pct"] = ecom_yoy
            result["total_retail_yoy_growth_pct"] = total_yoy

    return result


def get_category_breakdown() -> dict[str, Any]:
    """
    Break down retail sales by major category.

    Fetches the latest data for key retail categories and ranks them
    by sales volume and growth rate.
    """
    categories = {
        "RSEAS": "Electronics & Appliances",
        "RSGASSN": "Gas Stations",
        "RSFSDPN": "Food Services & Bars",
        "RSDBS": "Department Stores",
        "RSNSR": "Nonstore Retailers (mostly online)",
        "RSBMGESD": "Building Materials & Garden",
    }

    breakdown = []
    for series_id, name in categories.items():
        obs = _fetch_fred(series_id, limit=13)
        if obs:
            latest = obs[0]
            entry = {"category": name, "sales_mn": latest["value"], "date": latest["date"]}
            if len(obs) >= 13:
                yoy = round((latest["value"] / obs[12]["value"] - 1) * 100, 1)
                entry["yoy_growth_pct"] = yoy
            breakdown.append(entry)

    # Sort by sales volume
    breakdown.sort(key=lambda x: x["sales_mn"], reverse=True)

    return {
        "categories": breakdown,
        "count": len(breakdown),
        "source": "US Census Bureau / FRED",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_ecommerce_penetration_trend(years: int = 5) -> dict[str, Any]:
    """
    Track the long-term e-commerce penetration trend.

    Shows how online's share of total retail has evolved, including
    the COVID acceleration and subsequent normalization.

    Args:
        years: Number of years of history (max ~10).
    """
    quarters = min(years * 4, 40)
    obs = _fetch_fred("ECOMPCTSA", limit=quarters)
    if not obs:
        return {"error": "E-commerce penetration data unavailable"}

    obs.reverse()  # oldest first

    # Key milestones
    milestones = {}
    for o in obs:
        year = o["date"][:4]
        if year not in milestones or o["date"] > milestones[year]["date"]:
            milestones[year] = o

    # COVID impact
    pre_covid = next((o["value"] for o in obs if o["date"].startswith("2019")), None)
    covid_peak = max(
        (o["value"] for o in obs if o["date"].startswith("2020")),
        default=None,
    )
    latest = obs[-1]["value"]

    result = {
        "current_penetration_pct": latest,
        "trend_data": [milestones[y] for y in sorted(milestones.keys())],
        "period_years": years,
    }

    if pre_covid and covid_peak:
        result["covid_impact"] = {
            "pre_covid_pct": pre_covid,
            "covid_peak_pct": covid_peak,
            "acceleration_pp": round(covid_peak - pre_covid, 1),
            "current_vs_pre_covid_pp": round(latest - pre_covid, 1),
        }

    return result


def get_retail_health_score() -> dict[str, Any]:
    """
    Calculate an overall retail sector health score (0-100).

    Combines total sales growth, breadth of category performance,
    and consumer spending momentum.
    """
    total = _fetch_fred("RSXFS", limit=13)
    if not total or len(total) < 13:
        return {"score": None, "status": "insufficient data"}

    # MoM growth
    mom = (total[0]["value"] / total[1]["value"] - 1) * 100
    # YoY growth
    yoy = (total[0]["value"] / total[12]["value"] - 1) * 100

    # Score components (each 0-33)
    # 1. YoY growth score (0% = 0, 5% = 33)
    growth_score = min(33, max(0, yoy / 5 * 33))
    # 2. MoM momentum (>0.5% = strong)
    momentum_score = min(33, max(0, (mom + 1) / 2 * 33))
    # 3. Base stability score (positive sales = healthy)
    stability_score = 33 if total[0]["value"] > total[5]["value"] else 16

    total_score = round(growth_score + momentum_score + stability_score)

    if total_score >= 75:
        status = "STRONG"
    elif total_score >= 50:
        status = "HEALTHY"
    elif total_score >= 25:
        status = "WEAK"
    else:
        status = "CONTRACTING"

    return {
        "health_score": total_score,
        "status": status,
        "components": {
            "yoy_growth_pct": round(yoy, 1),
            "mom_growth_pct": round(mom, 2),
            "growth_score": round(growth_score, 1),
            "momentum_score": round(momentum_score, 1),
            "stability_score": round(stability_score, 1),
        },
        "latest_date": total[0]["date"],
        "latest_sales_mn": total[0]["value"],
    }
