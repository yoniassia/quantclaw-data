"""
IMF PortWatch API — Global Maritime Trade & Port Activity Monitor

Data Source: IMF PortWatch (ArcGIS Feature Services)
Update: Daily (vessel counts, disruptions)
History: Ongoing since 2019
Free: Yes (public ArcGIS endpoints, no API key required)

Provides:
- Port database with vessel counts by type (container, dry bulk, tanker, etc.)
- Maritime chokepoint monitoring (Suez, Panama, Hormuz, etc.)
- Active disruption tracking (tropical cyclones, conflicts, blockades)
- Climate risk scenarios per port (flooding, wind, storm surge)
- Supply chain spillover impact analysis
- Trade risk scenarios with value-at-risk estimates

Usage for Quant:
- Monitor supply chain disruptions that impact commodity prices
- Track chokepoint congestion affecting shipping/energy costs
- Climate risk exposure for ports → insurance, logistics equities
- Trade flow disruption → macro impact on importing countries
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/imf_portwatch")
os.makedirs(CACHE_DIR, exist_ok=True)

# ArcGIS Feature Service base URLs
BASE = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"
SERVICES = {
    "ports": f"{BASE}/PortWatch_ports_database/FeatureServer/0",
    "chokepoints": f"{BASE}/PortWatch_chokepoints_database/FeatureServer/0",
    "disruptions": f"{BASE}/portwatch_disruptions_database/FeatureServer/0",
    "climate_risk": f"{BASE}/climate_scenarios_climate_risk/FeatureServer/0",
    "spillovers": f"{BASE}/spillovers_supplychain/FeatureServer/0",
    "trade_scenarios": f"{BASE}/scenarios_trade/FeatureServer/0",
}

HEADERS = {"User-Agent": "QuantClaw/1.0"}
DEFAULT_TIMEOUT = 15


def _query_arcgis(service: str, where: str = "1=1", out_fields: str = "*",
                  order_by: str = "", record_count: int = 100,
                  return_geometry: bool = False) -> List[Dict]:
    """
    Generic ArcGIS Feature Service query helper.
    Returns list of attribute dicts (no geometry by default).
    """
    url = f"{SERVICES[service]}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "f": "json",
        "resultRecordCount": record_count,
        "returnGeometry": "true" if return_geometry else "false",
    }
    if order_by:
        params["orderByFields"] = order_by

    resp = requests.get(url, params=params, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error'].get('message', data['error'])}")

    features = data.get("features", [])
    return [f["attributes"] for f in features]


def _epoch_to_iso(epoch_ms) -> Optional[str]:
    """Convert ArcGIS epoch milliseconds to ISO date string."""
    if epoch_ms is None:
        return None
    try:
        return datetime.utcfromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return None


# ── Port Database ──────────────────────────────────────────────────

def get_ports_by_country(iso3: str, limit: int = 50) -> List[Dict]:
    """
    Get all ports for a country by ISO3 code (e.g. 'USA', 'CHN', 'DEU').

    Returns list of port dicts with vessel counts, top industries, trade shares.
    """
    return _query_arcgis(
        "ports",
        where=f"ISO3='{iso3.upper()}'",
        order_by="vessel_count_total DESC",
        record_count=limit,
    )


def search_port(name: str, limit: int = 10) -> List[Dict]:
    """
    Search ports by name (partial match).

    Args:
        name: Port name to search (e.g. 'Shanghai', 'Los Angeles')
        limit: Max results

    Returns list of matching port records.
    """
    safe_name = name.replace("'", "''")
    return _query_arcgis(
        "ports",
        where=f"portname LIKE '%{safe_name}%'",
        order_by="vessel_count_total DESC",
        record_count=limit,
    )


def get_top_ports(limit: int = 20) -> List[Dict]:
    """
    Get the world's busiest ports by total vessel count.

    Returns top N ports globally sorted by vessel_count_total descending.
    """
    return _query_arcgis(
        "ports",
        where="1=1",
        order_by="vessel_count_total DESC",
        record_count=limit,
    )


def get_port_by_id(port_id: str) -> Optional[Dict]:
    """
    Get a single port by its portid (e.g. 'port767').

    Returns port dict or None if not found.
    """
    results = _query_arcgis("ports", where=f"portid='{port_id}'", record_count=1)
    return results[0] if results else None


# ── Chokepoints ────────────────────────────────────────────────────

def get_chokepoints(limit: int = 50) -> List[Dict]:
    """
    Get all maritime chokepoints (Suez Canal, Panama Canal, Strait of Hormuz, etc.).

    Returns list of chokepoint records with vessel traffic data.
    """
    return _query_arcgis(
        "chokepoints",
        where="1=1",
        order_by="vessel_count_total DESC",
        record_count=limit,
    )


def get_chokepoint_by_name(name: str) -> List[Dict]:
    """
    Search chokepoints by name (e.g. 'Suez', 'Panama', 'Hormuz').

    Returns matching chokepoint records.
    """
    safe_name = name.replace("'", "''")
    return _query_arcgis(
        "chokepoints",
        where=f"portname LIKE '%{safe_name}%'",
        record_count=10,
    )


# ── Disruptions ────────────────────────────────────────────────────

def get_active_disruptions(limit: int = 50) -> List[Dict]:
    """
    Get currently active disruptions (no end date set).

    Returns list of active disruption events with alert levels,
    affected ports, and severity info.
    """
    results = _query_arcgis(
        "disruptions",
        where="todate IS NULL",
        order_by="fromdate DESC",
        record_count=limit,
    )
    for r in results:
        r["fromdate_iso"] = _epoch_to_iso(r.get("fromdate"))
        r["todate_iso"] = _epoch_to_iso(r.get("todate"))
    return results


def get_recent_disruptions(days: int = 90, limit: int = 50) -> List[Dict]:
    """
    Get disruptions from the last N days.

    Args:
        days: Look-back period in days (default 90)
        limit: Max results

    Returns list of recent disruption events sorted by start date descending.
    """
    cutoff_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    results = _query_arcgis(
        "disruptions",
        where=f"fromdate >= {cutoff_ms}",
        order_by="fromdate DESC",
        record_count=limit,
    )
    for r in results:
        r["fromdate_iso"] = _epoch_to_iso(r.get("fromdate"))
        r["todate_iso"] = _epoch_to_iso(r.get("todate"))
    return results


def get_disruptions_by_type(event_type: str, limit: int = 50) -> List[Dict]:
    """
    Get disruptions filtered by event type.

    Common types: 'TC' (tropical cyclone), 'EQ' (earthquake),
    'VO' (volcanic), 'FL' (flood), 'OT' (other/conflict).

    Returns disruption records sorted by date descending.
    """
    results = _query_arcgis(
        "disruptions",
        where=f"eventtype='{event_type.upper()}'",
        order_by="fromdate DESC",
        record_count=limit,
    )
    for r in results:
        r["fromdate_iso"] = _epoch_to_iso(r.get("fromdate"))
        r["todate_iso"] = _epoch_to_iso(r.get("todate"))
    return results


def get_red_alert_disruptions(limit: int = 50) -> List[Dict]:
    """
    Get all RED alert level disruptions (highest severity).

    Returns high-severity disruptions sorted by date descending.
    """
    results = _query_arcgis(
        "disruptions",
        where="alertlevel='RED'",
        order_by="fromdate DESC",
        record_count=limit,
    )
    for r in results:
        r["fromdate_iso"] = _epoch_to_iso(r.get("fromdate"))
        r["todate_iso"] = _epoch_to_iso(r.get("todate"))
    return results


# ── Climate Risk ───────────────────────────────────────────────────

def get_climate_risk_by_port(port_id: str, limit: int = 100) -> List[Dict]:
    """
    Get climate risk scenarios for a specific port.

    Returns risk measures across different climate scenarios and hazards
    (flooding, wind, storm surge, etc.).
    """
    return _query_arcgis(
        "climate_risk",
        where=f"portid='{port_id}'",
        record_count=limit,
    )


def get_climate_risk_by_country(iso3: str, limit: int = 200) -> List[Dict]:
    """
    Get climate risk data for all ports in a country.

    Args:
        iso3: Country ISO3 code (e.g. 'USA', 'JPN', 'NLD')
        limit: Max results

    Returns climate risk scenarios for all ports in the country.
    """
    return _query_arcgis(
        "climate_risk",
        where=f"ISO3='{iso3.upper()}'",
        record_count=limit,
    )


# ── Supply Chain Spillovers ────────────────────────────────────────

def get_spillover_impact(from_port_id: str, limit: int = 50) -> List[Dict]:
    """
    Get supply chain spillover impact if a port is disrupted.

    Shows which countries/industries would be affected and how much
    daily consumption and industry output is at risk.

    Args:
        from_port_id: The disrupted port's ID (e.g. 'port123')
        limit: Max results

    Returns spillover records with daily_consumption_at_risk and
    daily_industryoutput_at_risk values.
    """
    return _query_arcgis(
        "spillovers",
        where=f"from_portid='{from_port_id}'",
        order_by="daily_consumption_at_risk DESC",
        record_count=limit,
    )


def get_spillover_to_country(to_iso3: str, limit: int = 50) -> List[Dict]:
    """
    Get all supply chain risks TO a specific country from port disruptions.

    Shows which ports, if disrupted, would impact this country's supply chains.

    Args:
        to_iso3: Target country ISO3 code (e.g. 'USA')
        limit: Max results
    """
    return _query_arcgis(
        "spillovers",
        where=f"to_iso3='{to_iso3.upper()}'",
        order_by="daily_consumption_at_risk DESC",
        record_count=limit,
    )


# ── Trade Scenarios ────────────────────────────────────────────────

def get_trade_risk_scenarios(to_iso3: str, limit: int = 50) -> List[Dict]:
    """
    Get trade value at risk for a country under various disruption scenarios.

    Shows potential trade losses if specific ports face downtime,
    broken down by industry and scenario type.

    Args:
        to_iso3: Importing country ISO3 code
        limit: Max results

    Returns trade scenario records with trade_value_at_risk and
    days_downtime_at_port estimates.
    """
    return _query_arcgis(
        "trade_scenarios",
        where=f"to_ISO3='{to_iso3.upper()}'",
        order_by="trade_value_at_risk DESC",
        record_count=limit,
    )


def get_trade_risk_by_scenario(scenario: str, limit: int = 50) -> List[Dict]:
    """
    Get trade risk data for a specific disruption scenario.

    Args:
        scenario: Scenario name (query available scenarios first)
        limit: Max results
    """
    safe = scenario.replace("'", "''")
    return _query_arcgis(
        "trade_scenarios",
        where=f"scenario='{safe}'",
        order_by="trade_value_at_risk DESC",
        record_count=limit,
    )


# ── Summary / Dashboard ───────────────────────────────────────────

def get_dashboard_summary() -> Dict:
    """
    Get a high-level summary of current PortWatch status.

    Returns dict with:
    - active_disruptions: count and list of current disruptions
    - red_alerts: count of RED-level events
    - top_ports: top 5 busiest ports globally
    - chokepoint_count: number of monitored chokepoints
    """
    active = get_active_disruptions(limit=20)
    red_alerts = [d for d in active if d.get("alertlevel") == "RED"]
    top = get_top_ports(limit=5)
    choke = get_chokepoints(limit=50)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_disruptions": {
            "count": len(active),
            "events": [
                {
                    "name": d.get("eventname"),
                    "type": d.get("eventtype"),
                    "alert": d.get("alertlevel"),
                    "from": d.get("fromdate_iso"),
                    "country": d.get("country"),
                }
                for d in active[:10]
            ],
        },
        "red_alert_count": len(red_alerts),
        "top_ports": [
            {
                "name": p.get("fullname"),
                "vessels": p.get("vessel_count_total"),
                "top_industry": p.get("industry_top1"),
            }
            for p in top
        ],
        "chokepoints_monitored": len(choke),
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "imf_portwatch_api",
        "status": "active",
        "source": "https://portwatch.imf.org",
        "functions": 16,
    }, indent=2))
