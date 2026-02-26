"""
EV Adoption Curve Tracker — Monitor electric vehicle adoption rates, sales data,
market penetration, and transition metrics globally using free public data sources.

Tracks BEV/PHEV sales, charging infrastructure growth, battery cost trends,
and adoption S-curves by country.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


def get_global_ev_adoption_data() -> dict[str, Any]:
    """Get global EV adoption statistics from IEA Global EV Data Explorer."""
    # IEA publishes annual Global EV Outlook data
    url = "https://api.iea.org/evs?parameters=EV+sales&category=Historical&mode=Cars&csv=false"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "IEA Global EV Data Explorer",
                "data": data[:50] if isinstance(data, list) else data,
            }
    except Exception as e:
        # Fallback with curated data
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "IEA/BloombergNEF estimates",
            "error": str(e),
            "fallback_data": _get_curated_ev_data(),
        }


def _get_curated_ev_data() -> dict[str, Any]:
    """Curated EV market data from public sources."""
    return {
        "global_ev_sales_millions": {
            "2020": 3.0, "2021": 6.6, "2022": 10.5,
            "2023": 14.2, "2024": 17.5, "2025_est": 20.0,
        },
        "market_share_percent": {
            "2020": 4.1, "2021": 8.6, "2022": 14.0,
            "2023": 18.0, "2024": 22.0, "2025_est": 25.0,
        },
        "top_markets_2024": [
            {"country": "China", "ev_share_pct": 45, "sales_millions": 10.5},
            {"country": "Europe", "ev_share_pct": 24, "sales_millions": 3.5},
            {"country": "USA", "ev_share_pct": 10, "sales_millions": 1.8},
            {"country": "South Korea", "ev_share_pct": 12, "sales_millions": 0.3},
            {"country": "Japan", "ev_share_pct": 3, "sales_millions": 0.15},
        ],
    }


def get_ev_stock_universe() -> dict[str, Any]:
    """Get the investable EV stock universe — pure-play and legacy OEMs."""
    stocks = {
        "pure_play_ev": [
            {"ticker": "TSLA", "name": "Tesla", "market": "US", "focus": "BEV + Energy"},
            {"ticker": "RIVN", "name": "Rivian", "market": "US", "focus": "EV trucks/SUVs"},
            {"ticker": "LCID", "name": "Lucid Group", "market": "US", "focus": "Luxury BEV"},
            {"ticker": "NIO", "name": "NIO Inc", "market": "US/China", "focus": "Premium BEV + BaaS"},
            {"ticker": "XPEV", "name": "XPeng", "market": "US/China", "focus": "Smart BEV"},
            {"ticker": "LI", "name": "Li Auto", "market": "US/China", "focus": "EREV/BEV"},
        ],
        "legacy_oem_ev_leaders": [
            {"ticker": "VWAGY", "name": "Volkswagen", "ev_brand": "ID series"},
            {"ticker": "BMWYY", "name": "BMW", "ev_brand": "iX/i4/i5"},
            {"ticker": "HMC", "name": "Hyundai", "ev_brand": "Ioniq"},
            {"ticker": "GM", "name": "General Motors", "ev_brand": "Ultium/Equinox EV"},
            {"ticker": "F", "name": "Ford", "ev_brand": "Mustang Mach-E/F-150 Lightning"},
        ],
        "supply_chain": [
            {"ticker": "ALB", "name": "Albemarle", "focus": "Lithium"},
            {"ticker": "SQM", "name": "SQM", "focus": "Lithium"},
            {"ticker": "CHPT", "name": "ChargePoint", "focus": "Charging infra"},
            {"ticker": "BLNK", "name": "Blink Charging", "focus": "Charging infra"},
            {"ticker": "QS", "name": "QuantumScape", "focus": "Solid-state batteries"},
        ],
    }
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "universe": stocks,
        "total_tickers": sum(len(v) for v in stocks.values()),
    }


def get_battery_cost_curve() -> dict[str, Any]:
    """Track lithium-ion battery pack cost decline — key driver of EV adoption."""
    cost_per_kwh = {
        "2010": 1183, "2011": 899, "2012": 726, "2013": 599,
        "2014": 540, "2015": 373, "2016": 295, "2017": 226,
        "2018": 181, "2019": 157, "2020": 140, "2021": 132,
        "2022": 151, "2023": 139, "2024": 115, "2025_est": 100,
    }
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "BloombergNEF Battery Price Survey",
        "cost_per_kwh_usd": cost_per_kwh,
        "parity_threshold": 100,
        "parity_note": "$100/kWh widely considered ICE cost parity point",
        "decline_pct_2010_2024": round((1 - 115 / 1183) * 100, 1),
        "chemistry_trends": [
            "LFP gaining share (lower cost, no cobalt)",
            "Sodium-ion emerging for low-cost segment",
            "Solid-state batteries expected post-2027",
            "Cell-to-pack designs reducing pack-level costs",
        ],
    }


def calculate_adoption_s_curve(country: str = "global") -> dict[str, Any]:
    """Model EV adoption S-curve and estimate inflection points."""
    # S-curve parameters based on historical technology adoption
    curves = {
        "norway": {"current_share": 90, "phase": "saturation", "inflection_year": 2019},
        "china": {"current_share": 45, "phase": "rapid_growth", "inflection_year": 2023},
        "europe": {"current_share": 24, "phase": "early_majority", "inflection_year": 2024},
        "usa": {"current_share": 10, "phase": "early_adopters", "inflection_year": 2026},
        "japan": {"current_share": 3, "phase": "innovators", "inflection_year": 2028},
        "india": {"current_share": 2, "phase": "innovators", "inflection_year": 2029},
        "global": {"current_share": 22, "phase": "early_majority", "inflection_year": 2025},
    }
    curve = curves.get(country.lower(), curves["global"])
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "country": country,
        "current_ev_share_pct": curve["current_share"],
        "adoption_phase": curve["phase"],
        "estimated_inflection_year": curve["inflection_year"],
        "phases": {
            "innovators": "0-5% market share",
            "early_adopters": "5-16% market share",
            "early_majority": "16-50% market share",
            "late_majority": "50-84% market share",
            "saturation": "84%+ market share",
        },
        "key_catalysts": [
            "Battery cost below $100/kWh",
            "Charging infrastructure density",
            "Government ICE ban timelines",
            "Used EV market maturation",
            "Grid capacity for mass charging",
        ],
    }
