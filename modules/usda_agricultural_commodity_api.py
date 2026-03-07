"""USDA Agricultural Commodity API — Livestock market prices from USDA Market News.

Fetches real-time agricultural commodity data from the USDA Livestock Mandatory
Reporting (LMR) system. Covers cattle, hog, pork, lamb, and dairy markets.

Data source: https://mpr.datamart.ams.usda.gov/ (free, no API key required).
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

BASE_URL = "https://mpr.datamart.ams.usda.gov/services/v1.1"

# Key report IDs
REPORT_CATTLE_5AREA = 2477    # 5 Area Weekly Weighted Average Direct Slaughter Cattle
REPORT_PORK_CUTOUT = 2498     # National Daily Pork FOB Plant - Negotiated Sales
REPORT_HOG_DAILY = 2675       # Daily Direct Afternoon Hog Report
REPORT_HOG_SLAUGHTER = 2511   # National Daily Direct Prior Day Slaughtered Swine


def _fetch(path: str) -> dict | list:
    """Fetch JSON from USDA API.

    Args:
        path: URL path after base URL (e.g. '/reports' or '/reports/2498').

    Returns:
        Parsed JSON response.
    """
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_available_reports() -> list[dict[str, Any]]:
    """List all available USDA market reports.

    Returns:
        List of report dicts with slug_id, report_title, published_date,
        market_types, and sectionNames.
    """
    try:
        data = _fetch("/reports")
        return [
            {
                "report_id": r.get("slug_id"),
                "title": r.get("report_title"),
                "published_date": r.get("published_date"),
                "market_types": r.get("market_types", []),
                "sections": r.get("sectionNames", []),
            }
            for r in data
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_report(report_id: int, section: str | None = None) -> dict[str, Any]:
    """Fetch a specific USDA report by ID.

    Args:
        report_id: USDA report slug_id (e.g. 2498 for pork, 2477 for cattle).
        section: Optional section name to fetch (URL-encoded automatically).

    Returns:
        Dict with report metadata, sections list, stats, and results.
    """
    try:
        path = f"/reports/{report_id}"
        if section:
            encoded = urllib.request.quote(section)
            path = f"{path}/{encoded}"
        data = _fetch(path)
        latest_date = None
        if data.get("results"):
            latest_date = data["results"][0].get("report_date")
        return {
            "report_id": report_id,
            "section": data.get("reportSection"),
            "available_sections": data.get("reportSections", []),
            "total_rows": data.get("stats", {}).get("totalRows:", 0),
            "latest_date": latest_date,
            "results": data.get("results", []),
        }
    except Exception as e:
        return {"error": str(e), "report_id": report_id}


def get_cattle_prices() -> dict[str, Any]:
    """Get latest cattle market prices from the 5-Area Weekly Weighted Average report.

    Returns:
        Dict with report date, cattle price data by class/grade, and summary stats.
    """
    try:
        data = _fetch(f"/reports/{REPORT_CATTLE_5AREA}/Detail")
        results = data.get("results", [])
        if not results:
            return {"error": "No cattle data available"}

        latest_date = results[0].get("report_date")
        latest = [r for r in results if r.get("report_date") == latest_date]

        entries = []
        for r in latest:
            entry = {
                "class": r.get("class_description"),
                "selling_basis": r.get("selling_basis_description"),
                "grade": r.get("grade_description"),
                "head_count": r.get("head_count"),
                "weighted_avg_price": r.get("weighted_avg_price"),
                "price_range_low": r.get("price_range_low"),
                "price_range_high": r.get("price_range_high"),
                "weight_range_avg": r.get("weight_range_avg"),
            }
            entries.append({k: v for k, v in entry.items() if v is not None})

        return {
            "commodity": "cattle",
            "report_id": REPORT_CATTLE_5AREA,
            "report_date": latest_date,
            "published_date": results[0].get("published_date"),
            "entries": entries,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_pork_cutout() -> dict[str, Any]:
    """Get latest national pork cutout and primal values.

    Returns:
        Dict with pork carcass and primal cut prices.
    """
    try:
        encoded = urllib.request.quote("Cutout and Primal Values")
        data = _fetch(f"/reports/{REPORT_PORK_CUTOUT}/{encoded}")
        results = data.get("results", [])
        if not results:
            return {"error": "No pork cutout data available"}

        latest = results[0]
        return {
            "commodity": "pork",
            "report_id": REPORT_PORK_CUTOUT,
            "report_date": latest.get("report_date"),
            "published_date": latest.get("published_date"),
            "carcass_price": latest.get("pork_carcass"),
            "loin": latest.get("pork_loin"),
            "butt": latest.get("pork_butt"),
            "picnic": latest.get("pork_picnic"),
            "rib": latest.get("pork_rib"),
            "ham": latest.get("pork_ham"),
            "belly": latest.get("pork_belly"),
            "total_loads": latest.get("total_loads_date_1"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_hog_prices() -> dict[str, Any]:
    """Get latest hog market prices from the Daily Direct Afternoon Hog Report.

    Returns:
        Dict with hog price data by purchase type.
    """
    try:
        encoded = urllib.request.quote("National Volume and Price Data")
        data = _fetch(f"/reports/{REPORT_HOG_DAILY}/{encoded}")
        results = data.get("results", [])
        if not results:
            return {"error": "No hog data available"}

        latest_date = results[0].get("report_date")
        latest = [r for r in results if r.get("report_date") == latest_date]

        entries = []
        for r in latest:
            entry = {
                "purchase_type": r.get("purchase_type"),
                "head_count": r.get("head_count"),
                "price_low": r.get("price_low"),
                "price_high": r.get("price_high"),
                "weighted_avg": r.get("wtd_avg"),
                "price_change": r.get("price_chg"),
                "five_day_avg": r.get("price_5day"),
            }
            entries.append({k: v for k, v in entry.items() if v is not None})

        return {
            "commodity": "hogs",
            "report_id": REPORT_HOG_DAILY,
            "report_date": latest_date,
            "published_date": results[0].get("published_date"),
            "entries": entries,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_grain_prices() -> dict[str, Any]:
    """Grain prices note — USDA LMR API covers livestock only.

    The USDA Datamart LMR system does not include grain/crop prices.
    For grain data, use USDA NASS or WASDE reports instead.

    Returns:
        Dict explaining grain data is not available via this API,
        with pointers to alternative USDA sources.
    """
    return {
        "commodity": "grain",
        "available": False,
        "note": "USDA LMR Datamart covers livestock markets only (cattle, hogs, pork, lamb, dairy).",
        "alternatives": [
            "USDA NASS QuickStats: https://quickstats.nass.usda.gov/api",
            "USDA WASDE: https://www.usda.gov/oce/commodity/wasde",
            "USDA FAS GATS: https://apps.fas.usda.gov/gats/",
        ],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def commodity_summary() -> dict[str, Any]:
    """Overview of major agricultural commodity prices from USDA.

    Fetches the latest cattle, pork cutout, and hog prices in one call.

    Returns:
        Dict with summary prices for each commodity type.
    """
    summary = {"fetched_at": datetime.now(timezone.utc).isoformat(), "commodities": {}}

    # Cattle
    cattle = get_cattle_prices()
    if "error" not in cattle:
        # Find the main steer live fob price
        steer_prices = [
            e for e in cattle.get("entries", [])
            if e.get("class") == "STEER" and "LIVE" in (e.get("selling_basis", "") or "")
        ]
        top = steer_prices[0] if steer_prices else (cattle.get("entries", [{}])[0] if cattle.get("entries") else {})
        summary["commodities"]["cattle"] = {
            "report_date": cattle.get("report_date"),
            "weighted_avg_price": top.get("weighted_avg_price"),
            "price_range": f"{top.get('price_range_low', '?')}-{top.get('price_range_high', '?')}",
            "class": top.get("class"),
            "grade": top.get("grade"),
        }
    else:
        summary["commodities"]["cattle"] = cattle

    # Pork cutout
    pork = get_pork_cutout()
    if "error" not in pork:
        summary["commodities"]["pork"] = {
            "report_date": pork.get("report_date"),
            "carcass_price": pork.get("carcass_price"),
            "belly": pork.get("belly"),
            "loin": pork.get("loin"),
            "ham": pork.get("ham"),
        }
    else:
        summary["commodities"]["pork"] = pork

    # Hogs
    hogs = get_hog_prices()
    if "error" not in hogs:
        negotiated = [
            e for e in hogs.get("entries", [])
            if "negotiated" in (e.get("purchase_type", "") or "").lower()
            and "formula" not in (e.get("purchase_type", "") or "").lower()
        ]
        top_hog = negotiated[0] if negotiated else (hogs.get("entries", [{}])[0] if hogs.get("entries") else {})
        summary["commodities"]["hogs"] = {
            "report_date": hogs.get("report_date"),
            "weighted_avg": top_hog.get("weighted_avg"),
            "price_change": top_hog.get("price_change"),
            "five_day_avg": top_hog.get("five_day_avg"),
        }
    else:
        summary["commodities"]["hogs"] = hogs

    return summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print(json.dumps(commodity_summary(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "reports":
        reports = get_available_reports()
        print(f"Total reports: {len(reports)}")
        for r in reports[:10]:
            print(f"  [{r.get('report_id')}] {r.get('title')}")
    else:
        print(json.dumps({"module": "usda_agricultural_commodity_api", "status": "ready"}, indent=2))
