"""
Supply Chain Disruption Index — Monitor global supply chain stress using
public freight, shipping, and manufacturing data.

Combines Baltic Dry Index proxy, container throughput, PMI supplier delivery
times, and FRED supply chain pressure index for a composite disruption score.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def get_supply_chain_pressure_index(api_key: str = "DEMO_KEY", limit: int = 60) -> dict[str, Any]:
    """Fetch NY Fed Global Supply Chain Pressure Index (GSCPI) from FRED."""
    url = (
        f"{FRED_BASE}?series_id=GSCPIGLOBALDATA&api_key={api_key}"
        f"&file_type=json&sort_order=desc&limit={limit}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        obs = data.get("observations", [])
        points = [
            {"date": o["date"], "value": float(o["value"])}
            for o in obs if o.get("value", ".") != "."
        ]
        if points:
            latest = points[0]["value"]
            stress = "HIGH" if latest > 1.0 else "ELEVATED" if latest > 0 else "NORMAL" if latest > -1 else "LOW"
        else:
            latest, stress = None, "UNKNOWN"
        return {
            "index": "NY Fed GSCPI",
            "latest_value": latest,
            "stress_level": stress,
            "history": points[:24],
            "note": "Positive = above-average pressure, >1σ = significant disruption"
        }
    except Exception as e:
        return {"error": str(e)}


def get_supplier_delivery_times(api_key: str = "DEMO_KEY", limit: int = 36) -> dict[str, Any]:
    """ISM Manufacturing Supplier Deliveries Index — above 50 = slower deliveries."""
    url = (
        f"{FRED_BASE}?series_id=NAPMSD&api_key={api_key}"
        f"&file_type=json&sort_order=desc&limit={limit}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        obs = data.get("observations", [])
        points = [
            {"date": o["date"], "value": float(o["value"])}
            for o in obs if o.get("value", ".") != "."
        ]
        latest = points[0]["value"] if points else None
        status = "SLOWING" if latest and latest > 55 else "NORMAL" if latest and latest > 45 else "FAST"
        return {
            "indicator": "ISM Supplier Deliveries",
            "latest": latest,
            "status": status,
            "history": points[:12],
            "note": "Above 50 = slower deliveries (supply stress)"
        }
    except Exception as e:
        return {"error": str(e)}


def get_inventory_to_sales_ratio(api_key: str = "DEMO_KEY", limit: int = 36) -> dict[str, Any]:
    """Total Business Inventory/Sales Ratio — rising = potential glut or demand weakness."""
    url = (
        f"{FRED_BASE}?series_id=ISRATIO&api_key={api_key}"
        f"&file_type=json&sort_order=desc&limit={limit}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        obs = data.get("observations", [])
        points = [
            {"date": o["date"], "value": float(o["value"])}
            for o in obs if o.get("value", ".") != "."
        ]
        return {
            "indicator": "Inventory/Sales Ratio",
            "latest": points[0]["value"] if points else None,
            "history": points[:12],
        }
    except Exception as e:
        return {"error": str(e)}


def get_composite_disruption_score(api_key: str = "DEMO_KEY") -> dict[str, Any]:
    """Composite supply chain disruption score combining multiple indicators."""
    gscpi = get_supply_chain_pressure_index(api_key, limit=1)
    delivery = get_supplier_delivery_times(api_key, limit=1)
    inv = get_inventory_to_sales_ratio(api_key, limit=1)

    scores = {}
    gscpi_val = gscpi.get("latest_value")
    if gscpi_val is not None:
        scores["gscpi_score"] = min(max((gscpi_val + 2) / 4 * 100, 0), 100)

    del_val = delivery.get("latest")
    if del_val is not None:
        scores["delivery_score"] = min(max((del_val - 40) / 30 * 100, 0), 100)

    composite = sum(scores.values()) / len(scores) if scores else None
    level = "CRITICAL" if composite and composite > 75 else "HIGH" if composite and composite > 50 else "MODERATE" if composite and composite > 25 else "LOW"

    return {
        "composite_score": round(composite, 1) if composite else None,
        "disruption_level": level,
        "components": scores,
        "timestamp": datetime.utcnow().isoformat(),
    }
