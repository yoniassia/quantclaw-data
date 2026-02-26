"""
Central Bank Digital Currency (CBDC) Tracker — Monitors global CBDC development status,
pilot programs, and adoption timelines across major economies.

Data sources: Atlantic Council CBDC Tracker (free), BIS CBDC survey data (free),
embedded status database updated from public sources.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# Comprehensive CBDC status database (sourced from Atlantic Council + BIS)
CBDC_DATABASE = {
    "CN": {
        "country": "China",
        "currency": "e-CNY (Digital Yuan)",
        "status": "pilot",
        "phase": "Advanced Pilot",
        "launch_year": None,
        "pilot_cities": 26,
        "technology": "centralized ledger",
        "retail": True,
        "wholesale": True,
        "cross_border": True,
        "notes": "Largest CBDC pilot globally. Over 260M wallets opened. Used in multiple provinces.",
    },
    "EU": {
        "country": "Eurozone",
        "currency": "Digital Euro",
        "status": "development",
        "phase": "Preparation Phase",
        "launch_year": 2027,
        "technology": "DLT hybrid",
        "retail": True,
        "wholesale": True,
        "cross_border": True,
        "notes": "ECB preparation phase started Oct 2023. Legislative framework in progress.",
    },
    "US": {
        "country": "United States",
        "currency": "Digital Dollar",
        "status": "research",
        "phase": "Research/Exploration",
        "launch_year": None,
        "technology": "TBD",
        "retail": False,
        "wholesale": True,
        "cross_border": False,
        "notes": "Fed exploring wholesale CBDC. Political debate ongoing. Project Hamilton research completed.",
    },
    "UK": {
        "country": "United Kingdom",
        "currency": "Digital Pound (Britcoin)",
        "status": "development",
        "phase": "Design Phase",
        "launch_year": 2028,
        "technology": "centralized core + API layer",
        "retail": True,
        "wholesale": False,
        "cross_border": False,
        "notes": "BoE + HM Treasury joint project. Design phase 2024-2025.",
    },
    "IN": {
        "country": "India",
        "currency": "e-Rupee",
        "status": "pilot",
        "phase": "Retail + Wholesale Pilot",
        "launch_year": None,
        "pilot_cities": 15,
        "technology": "centralized ledger",
        "retail": True,
        "wholesale": True,
        "cross_border": False,
        "notes": "RBI pilot since Dec 2022. Growing merchant acceptance.",
    },
    "JP": {
        "country": "Japan",
        "currency": "Digital Yen",
        "status": "development",
        "phase": "Pilot Planning",
        "launch_year": 2026,
        "technology": "DLT hybrid",
        "retail": True,
        "wholesale": False,
        "cross_border": True,
        "notes": "BoJ completed Phase 2 proof-of-concept. Pilot with private sector planned.",
    },
    "BR": {
        "country": "Brazil",
        "currency": "Drex (Digital Real)",
        "status": "pilot",
        "phase": "Advanced Pilot",
        "launch_year": 2025,
        "technology": "Hyperledger Besu",
        "retail": True,
        "wholesale": True,
        "cross_border": False,
        "notes": "Drex platform pilot with 16 consortiums. Focus on tokenized assets.",
    },
    "NG": {
        "country": "Nigeria",
        "currency": "eNaira",
        "status": "launched",
        "phase": "Live",
        "launch_year": 2021,
        "technology": "Hyperledger Fabric",
        "retail": True,
        "wholesale": False,
        "cross_border": False,
        "notes": "First African CBDC. Low adoption despite government push.",
    },
    "BS": {
        "country": "Bahamas",
        "currency": "Sand Dollar",
        "status": "launched",
        "phase": "Live",
        "launch_year": 2020,
        "technology": "centralized",
        "retail": True,
        "wholesale": False,
        "cross_border": False,
        "notes": "First national CBDC globally. Limited scale due to small population.",
    },
    "JM": {
        "country": "Jamaica",
        "currency": "JAM-DEX",
        "status": "launched",
        "phase": "Live",
        "launch_year": 2022,
        "technology": "centralized",
        "retail": True,
        "wholesale": False,
        "cross_border": False,
        "notes": "National rollout June 2022. Growing merchant adoption.",
    },
    "SE": {
        "country": "Sweden",
        "currency": "e-Krona",
        "status": "development",
        "phase": "Investigation Phase",
        "launch_year": None,
        "technology": "R3 Corda",
        "retail": True,
        "wholesale": False,
        "cross_border": True,
        "notes": "Riksbank e-krona pilot completed. Legislation under review.",
    },
    "RU": {
        "country": "Russia",
        "currency": "Digital Ruble",
        "status": "pilot",
        "phase": "Limited Pilot",
        "launch_year": 2025,
        "technology": "centralized platform",
        "retail": True,
        "wholesale": True,
        "cross_border": True,
        "notes": "CBR pilot with 13 banks. Focus on sanctions-resistant cross-border payments.",
    },
}


def get_cbdc_status(country_code: str | None = None) -> dict[str, Any] | list[dict]:
    """Get CBDC development status for a specific country or all tracked countries."""
    if country_code:
        code = country_code.upper()
        entry = CBDC_DATABASE.get(code)
        if entry:
            return {**entry, "country_code": code, "timestamp": datetime.utcnow().isoformat()}
        return {"error": f"Country {code} not tracked", "tracked_countries": list(CBDC_DATABASE.keys())}
    return [
        {**v, "country_code": k}
        for k, v in sorted(CBDC_DATABASE.items(), key=lambda x: x[1].get("status", ""))
    ]


def get_cbdc_summary() -> dict[str, Any]:
    """Get a global summary of CBDC development stages."""
    status_counts = {}
    for entry in CBDC_DATABASE.values():
        s = entry["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    launched = [k for k, v in CBDC_DATABASE.items() if v["status"] == "launched"]
    pilots = [k for k, v in CBDC_DATABASE.items() if v["status"] == "pilot"]
    developing = [k for k, v in CBDC_DATABASE.items() if v["status"] == "development"]
    researching = [k for k, v in CBDC_DATABASE.items() if v["status"] == "research"]

    return {
        "total_tracked": len(CBDC_DATABASE),
        "status_breakdown": status_counts,
        "launched": launched,
        "pilot": pilots,
        "development": developing,
        "research": researching,
        "retail_cbdc_count": sum(1 for v in CBDC_DATABASE.values() if v.get("retail")),
        "wholesale_cbdc_count": sum(1 for v in CBDC_DATABASE.values() if v.get("wholesale")),
        "cross_border_count": sum(1 for v in CBDC_DATABASE.values() if v.get("cross_border")),
        "note": "134+ countries exploring CBDCs per Atlantic Council tracker",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_cbdc_timeline() -> list[dict[str, Any]]:
    """Get projected CBDC launch timeline for countries with estimated dates."""
    timeline = []
    for code, entry in CBDC_DATABASE.items():
        if entry.get("launch_year"):
            timeline.append({
                "country_code": code,
                "country": entry["country"],
                "currency": entry["currency"],
                "expected_launch": entry["launch_year"],
                "current_status": entry["status"],
            })
    timeline.sort(key=lambda x: x["expected_launch"])
    return timeline


def assess_cbdc_impact_on_crypto() -> dict[str, Any]:
    """Assess potential impact of CBDC adoption on cryptocurrency markets."""
    launched_count = sum(1 for v in CBDC_DATABASE.values() if v["status"] == "launched")
    pilot_count = sum(1 for v in CBDC_DATABASE.values() if v["status"] == "pilot")

    return {
        "adoption_momentum": "accelerating" if pilot_count > 3 else "moderate",
        "key_risks_to_crypto": [
            "Retail CBDCs may reduce stablecoin demand for payments",
            "Cross-border CBDCs could challenge SWIFT alternatives (XRP, XLM)",
            "Government digital wallets may reduce crypto wallet adoption",
            "Programmable money features may compete with smart contract platforms",
        ],
        "potential_crypto_beneficiaries": [
            "Privacy coins (if CBDCs enable surveillance)",
            "DeFi protocols (permissionless alternative to CBDC rails)",
            "Interoperability protocols (bridging CBDCs and crypto)",
        ],
        "countries_with_live_cbdc": launched_count,
        "countries_piloting": pilot_count,
        "timestamp": datetime.utcnow().isoformat(),
    }
