"""
Container Ship AIS Tracker — Monitor global container shipping activity
using public port data, UNCTAD statistics, and vessel tracking proxies.

Tracks container port throughput, freight indices, major shipping route
congestion, and global trade volume indicators.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def get_container_throughput_index(api_key: str = "DEMO_KEY", limit: int = 36) -> dict[str, Any]:
    """RWI/ISL Container Throughput Index from FRED — proxy for global trade volume."""
    url = (
        f"{FRED_BASE}?series_id=RWICONTAINERTHROUGH&api_key={api_key}"
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
        latest = points[0] if points else None
        yoy = None
        if len(points) >= 13:
            yoy = round((points[0]["value"] / points[12]["value"] - 1) * 100, 2)
        return {
            "index": "RWI/ISL Container Throughput",
            "latest": latest,
            "yoy_change_pct": yoy,
            "history": points[:24],
            "note": "100 = 2015 base; higher = more global shipping activity"
        }
    except Exception as e:
        return {"error": str(e)}


def get_freight_rate_indices(api_key: str = "DEMO_KEY") -> dict[str, Any]:
    """Fetch available freight/shipping cost indices from FRED."""
    series = {
        "DCOILBRENTEU": "Brent Crude (shipping cost driver)",
        "GSCPIGLOBALDATA": "Global Supply Chain Pressure",
    }
    results = {}
    for sid, label in series.items():
        url = (
            f"{FRED_BASE}?series_id={sid}&api_key={api_key}"
            f"&file_type=json&sort_order=desc&limit=5"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            obs = data.get("observations", [])
            val = None
            for o in obs:
                if o.get("value", ".") != ".":
                    val = {"date": o["date"], "value": float(o["value"])}
                    break
            results[label] = val
        except Exception:
            results[label] = None
    return {"freight_indicators": results}


def get_major_port_activity() -> dict[str, Any]:
    """Summary of major container port rankings and throughput estimates."""
    # Static reference data — top ports by TEU (updated annually from UNCTAD/World Shipping Council)
    ports = [
        {"port": "Shanghai", "country": "China", "est_teu_millions": 49.0, "rank": 1},
        {"port": "Singapore", "country": "Singapore", "est_teu_millions": 39.0, "rank": 2},
        {"port": "Ningbo-Zhoushan", "country": "China", "est_teu_millions": 35.3, "rank": 3},
        {"port": "Shenzhen", "country": "China", "est_teu_millions": 30.0, "rank": 4},
        {"port": "Guangzhou", "country": "China", "est_teu_millions": 25.0, "rank": 5},
        {"port": "Busan", "country": "South Korea", "est_teu_millions": 23.0, "rank": 6},
        {"port": "Qingdao", "country": "China", "est_teu_millions": 22.0, "rank": 7},
        {"port": "Hong Kong", "country": "China", "est_teu_millions": 16.0, "rank": 8},
        {"port": "Rotterdam", "country": "Netherlands", "est_teu_millions": 14.5, "rank": 9},
        {"port": "Dubai (Jebel Ali)", "country": "UAE", "est_teu_millions": 14.0, "rank": 10},
    ]
    return {
        "top_ports": ports,
        "note": "Annual TEU estimates from World Shipping Council. Updated periodically.",
        "total_top10_teu": sum(p["est_teu_millions"] for p in ports),
    }


def get_shipping_route_summary() -> dict[str, Any]:
    """Major container shipping routes and their characteristics."""
    routes = [
        {"route": "Trans-Pacific (Asia→N.America)", "share_pct": 28, "key_chokepoint": "None (open ocean)"},
        {"route": "Asia→Europe", "share_pct": 22, "key_chokepoint": "Suez Canal / Cape of Good Hope"},
        {"route": "Intra-Asia", "share_pct": 18, "key_chokepoint": "Strait of Malacca"},
        {"route": "Trans-Atlantic", "share_pct": 8, "key_chokepoint": "None (open ocean)"},
        {"route": "Europe→Asia (return)", "share_pct": 12, "key_chokepoint": "Suez Canal"},
        {"route": "N.America→Asia (return)", "share_pct": 12, "key_chokepoint": "None (open ocean)"},
    ]
    return {
        "major_routes": routes,
        "chokepoints": ["Suez Canal", "Panama Canal", "Strait of Malacca", "Strait of Hormuz", "Bab el-Mandeb"],
        "note": "Route disruptions (e.g., Suez blockage, Red Sea attacks) spike freight rates"
    }
