"""
Semiconductor Lead Time Monitor — Track chip delivery times and supply chain trends.

Uses FRED economic data and web-scraped industry reports to monitor semiconductor
supply chain health, lead time trends, and capacity utilization.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# FRED series related to semiconductor/electronics production
SERIES_MAP = {
    "IPMAN": "Manufacturing Industrial Production",
    "IPB53122S": "Semiconductor & Electronic Component Production",
    "AMDMUO": "Unfilled Durable Goods Orders (Computers & Electronics)",
    "NEWORDER": "New Orders Manufacturing",
    "AMTMUO": "Unfilled Orders Total Manufacturing",
}


def get_semiconductor_production(fred_api_key: str, months: int = 24) -> Dict:
    """
    Fetch semiconductor production index and related manufacturing data from FRED.

    Args:
        fred_api_key: FRED API key
        months: Number of months of history

    Returns:
        Dict with production indices and trend analysis
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    results = {}

    for series_id, label in SERIES_MAP.items():
        try:
            url = (
                f"{FRED_BASE}?series_id={series_id}"
                f"&api_key={fred_api_key}&file_type=json"
                f"&observation_start={start_date}&observation_end={end_date}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            observations = [
                {"date": o["date"], "value": float(o["value"])}
                for o in data.get("observations", [])
                if o["value"] != "."
            ]

            if observations:
                latest = observations[-1]["value"]
                prev = observations[-2]["value"] if len(observations) > 1 else latest
                yoy = None
                if len(observations) > 12:
                    year_ago = observations[-13]["value"]
                    yoy = round((latest - year_ago) / year_ago * 100, 2)

                results[series_id] = {
                    "label": label,
                    "latest_value": latest,
                    "latest_date": observations[-1]["date"],
                    "mom_change_pct": round((latest - prev) / prev * 100, 2) if prev else None,
                    "yoy_change_pct": yoy,
                    "observations_count": len(observations),
                }
        except Exception as e:
            results[series_id] = {"label": label, "error": str(e)}

    return {
        "period": f"{start_date} to {end_date}",
        "series": results,
        "generated_at": datetime.now().isoformat(),
    }


def estimate_lead_times(fred_api_key: str) -> Dict:
    """
    Estimate semiconductor lead time stress from unfilled orders vs new orders ratio.

    Higher unfilled/new orders ratio suggests longer lead times.

    Args:
        fred_api_key: FRED API key

    Returns:
        Dict with lead time stress indicators and historical comparison
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")

    def _fetch_series(series_id: str) -> List[Dict]:
        url = (
            f"{FRED_BASE}?series_id={series_id}"
            f"&api_key={fred_api_key}&file_type=json"
            f"&observation_start={start_date}&observation_end={end_date}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return [
            {"date": o["date"], "value": float(o["value"])}
            for o in data.get("observations", [])
            if o["value"] != "."
        ]

    try:
        unfilled = _fetch_series("AMDMUO")
        new_orders = _fetch_series("NEWORDER")

        # Align by date
        unfilled_map = {o["date"]: o["value"] for o in unfilled}
        ratios = []
        for o in new_orders:
            if o["date"] in unfilled_map and o["value"] > 0:
                ratio = unfilled_map[o["date"]] / o["value"]
                ratios.append({"date": o["date"], "ratio": round(ratio, 4)})

        if ratios:
            latest_ratio = ratios[-1]["ratio"]
            avg_ratio = sum(r["ratio"] for r in ratios) / len(ratios)
            max_ratio = max(r["ratio"] for r in ratios)
            stress_level = "LOW" if latest_ratio < avg_ratio * 0.9 else (
                "HIGH" if latest_ratio > avg_ratio * 1.1 else "NORMAL"
            )

            return {
                "latest_ratio": latest_ratio,
                "latest_date": ratios[-1]["date"],
                "avg_ratio_3yr": round(avg_ratio, 4),
                "max_ratio_3yr": round(max_ratio, 4),
                "stress_level": stress_level,
                "stress_description": {
                    "LOW": "Lead times likely contracting — supply catching up",
                    "NORMAL": "Lead times stable — balanced supply/demand",
                    "HIGH": "Lead times likely expanding — demand exceeding supply",
                }[stress_level],
                "data_points": len(ratios),
            }
    except Exception as e:
        return {"error": str(e)}

    return {"error": "Insufficient data"}


def get_chip_capacity_utilization(fred_api_key: str) -> Dict:
    """
    Get capacity utilization for computer & electronic products manufacturing.

    Args:
        fred_api_key: FRED API key

    Returns:
        Dict with capacity utilization data and analysis
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")

    # CAPUTLB00004S = Capacity Utilization: Computer and Electronic Product
    series_id = "CAPUTLB00004S"
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&api_key={fred_api_key}&file_type=json"
        f"&observation_start={start_date}&observation_end={end_date}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        obs = [
            {"date": o["date"], "value": float(o["value"])}
            for o in data.get("observations", [])
            if o["value"] != "."
        ]

        if obs:
            values = [o["value"] for o in obs]
            latest = values[-1]
            avg_5yr = sum(values) / len(values)

            return {
                "series": "Computer & Electronic Product Capacity Utilization",
                "latest_pct": latest,
                "latest_date": obs[-1]["date"],
                "avg_5yr_pct": round(avg_5yr, 2),
                "max_5yr_pct": max(values),
                "min_5yr_pct": min(values),
                "vs_average": "ABOVE" if latest > avg_5yr else "BELOW",
                "tight_capacity": latest > 78,
                "data_points": len(obs),
            }
    except Exception as e:
        return {"error": str(e)}

    return {"error": "No data available"}
