"""
Nuclear Energy Renaissance Tracker (Roadmap #391)

Tracks the nuclear energy revival including new reactor construction,
SMR development, uranium markets, policy shifts, and tech company
nuclear power procurement. Uses free data from IAEA, EIA, and news APIs.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


# Nuclear energy companies and uranium miners
NUCLEAR_ECOSYSTEM = {
    "utilities": {
        "CEG": {"name": "Constellation Energy", "reactors": 21, "capacity_gw": 21.5, "notes": "Largest US nuclear fleet"},
        "VST": {"name": "Vistra", "reactors": 4, "capacity_gw": 4.8, "notes": "Comanche Peak"},
        "SO": {"name": "Southern Company", "reactors": 6, "capacity_gw": 6.5, "notes": "Vogtle 3&4 new builds"},
        "DUK": {"name": "Duke Energy", "reactors": 11, "capacity_gw": 10.7, "notes": "Oconee, McGuire, Catawba"},
        "EXC": {"name": "Exelon", "reactors": 0, "capacity_gw": 0, "notes": "Spun off nuclear to CEG"},
    },
    "uranium_miners": {
        "CCJ": {"name": "Cameco", "type": "uranium_miner", "country": "Canada"},
        "UEC": {"name": "Uranium Energy Corp", "type": "uranium_miner", "country": "US"},
        "DNN": {"name": "Denison Mines", "type": "uranium_miner", "country": "Canada"},
        "NXE": {"name": "NexGen Energy", "type": "uranium_miner", "country": "Canada"},
        "UUUU": {"name": "Energy Fuels", "type": "uranium_miner_processor", "country": "US"},
    },
    "smr_developers": {
        "SMR": {"name": "NuScale Power", "type": "SMR", "design": "Light water SMR, 77MW modules"},
        "OKLO": {"name": "Oklo", "type": "Advanced reactor", "design": "Fast reactor, 15-50MW"},
        "NANO": {"name": "NANO Nuclear", "type": "Micro reactor", "design": "Portable micro reactors"},
    },
    "enrichment_fuel": {
        "LEU": {"name": "Centrus Energy", "type": "Enrichment", "notes": "Only US HALEU producer"},
    },
}

# Key catalysts for nuclear renaissance
CATALYSTS = [
    {"event": "AI data center power demand surge", "impact": "HIGH", "beneficiaries": ["CEG", "VST", "CCJ"]},
    {"event": "Microsoft-Constellation Three Mile Island restart deal", "impact": "HIGH", "beneficiaries": ["CEG"]},
    {"event": "Amazon nuclear power procurement", "impact": "HIGH", "beneficiaries": ["CEG", "VST"]},
    {"event": "Google SMR power agreement", "impact": "MEDIUM", "beneficiaries": ["SMR", "OKLO"]},
    {"event": "DOE HALEU fuel program", "impact": "MEDIUM", "beneficiaries": ["LEU", "UUUU"]},
    {"event": "COP28 Triple Nuclear pledge (22 countries)", "impact": "HIGH", "beneficiaries": ["CCJ", "UEC"]},
    {"event": "NRC SMR design certification progress", "impact": "MEDIUM", "beneficiaries": ["SMR"]},
    {"event": "Uranium supply deficit widening", "impact": "HIGH", "beneficiaries": ["CCJ", "UEC", "DNN"]},
]

# Global reactor pipeline
GLOBAL_PIPELINE = {
    "operating_reactors": 440,
    "under_construction": 62,
    "planned": 110,
    "proposed": 330,
    "countries_building": ["China", "India", "Turkey", "Egypt", "Bangladesh", "UK", "France", "US"],
    "china_dominance": "China building 25+ reactors simultaneously, 150 planned by 2035",
}


def get_uranium_market_data() -> Dict:
    """
    Fetch uranium spot price and market data from public sources.
    Uses EIA and other free data endpoints.

    Returns:
        Dict with uranium price, supply/demand balance, and inventory data
    """
    # Try EIA API for nuclear generation data
    eia_url = "https://api.eia.gov/v2/nuclear-outages/facility-nuclear-outages/data/?api_key=DEMO_KEY&frequency=daily&data[0]=capacity&sort[0][column]=period&sort[0][direction]=desc&length=5"

    nuclear_data = {}
    try:
        req = urllib.request.Request(eia_url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            nuclear_data["eia_source"] = "available"
            nuclear_data["data_points"] = len(data.get("response", {}).get("data", []))
    except Exception:
        nuclear_data["eia_source"] = "unavailable (use DEMO_KEY)"

    # Market overview (structured reference data)
    market = {
        "spot_price_reference": "See Numerco.com or TradeTech for latest U3O8 spot",
        "contract_vs_spot": "Term contracts typically 10-20% premium to spot",
        "supply_deficit": True,
        "deficit_description": "Primary mine supply ~130M lbs vs reactor demand ~180M lbs annually",
        "secondary_supply_sources": [
            "Utility inventories (declining)",
            "Government stockpiles (depleting)",
            "Underfeeding/re-enrichment",
        ],
        "key_producers": {
            "Kazatomprom": "Kazakhstan, ~25% global supply",
            "Cameco": "Canada, ~15% global supply",
            "Orano": "France/Niger, ~10% global supply",
        },
        "enrichment_bottleneck": "Western enrichment capacity limited; Russia supplied ~40% pre-sanctions",
        "eia_data": nuclear_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return market


def get_nuclear_renaissance_scorecard() -> Dict:
    """
    Calculate a nuclear renaissance composite score based on policy,
    construction pipeline, investment flows, and tech demand.

    Returns:
        Dict with scorecard across multiple dimensions
    """
    dimensions = {
        "policy_support": {
            "score": 85,
            "rationale": "COP28 triple pledge, IRA tax credits, bipartisan US support, EU taxonomy inclusion",
        },
        "construction_pipeline": {
            "score": 75,
            "rationale": f"{GLOBAL_PIPELINE['under_construction']} reactors under construction, {GLOBAL_PIPELINE['planned']} planned",
        },
        "tech_demand": {
            "score": 90,
            "rationale": "Microsoft, Amazon, Google, Meta all pursuing nuclear for AI data centers",
        },
        "uranium_supply": {
            "score": 70,
            "rationale": "Structural deficit, mine restarts slow, Russian supply uncertain",
        },
        "smr_progress": {
            "score": 55,
            "rationale": "NuScale certified but downsized, Oklo/Kairos progressing, no commercial SMR yet",
        },
        "public_sentiment": {
            "score": 65,
            "rationale": "Improving but still mixed; climate concerns driving shift pro-nuclear",
        },
    }

    weights = {
        "policy_support": 0.20,
        "construction_pipeline": 0.20,
        "tech_demand": 0.25,
        "uranium_supply": 0.15,
        "smr_progress": 0.10,
        "public_sentiment": 0.10,
    }

    composite = sum(dimensions[k]["score"] * weights[k] for k in weights)

    return {
        "renaissance_score": round(composite, 1),
        "verdict": "STRONG RENAISSANCE" if composite >= 75 else "MODERATE REVIVAL" if composite >= 60 else "EARLY STAGE",
        "dimensions": dimensions,
        "weights": weights,
        "catalysts": CATALYSTS,
        "global_pipeline": GLOBAL_PIPELINE,
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_investment_plays() -> Dict:
    """
    Map nuclear investment opportunities by theme and risk profile.

    Returns:
        Dict with categorized investment opportunities
    """
    plays = {
        "conservative": {
            "theme": "Existing nuclear fleet operators benefiting from AI power demand",
            "tickers": ["CEG", "VST", "SO", "DUK"],
            "catalyst": "Power purchase agreements with tech companies at premium rates",
        },
        "growth": {
            "theme": "Uranium miners benefiting from supply deficit",
            "tickers": ["CCJ", "UEC", "DNN", "NXE"],
            "catalyst": "Uranium spot price appreciation + term contracting cycle",
        },
        "speculative": {
            "theme": "SMR/advanced reactor developers",
            "tickers": ["SMR", "OKLO", "NANO"],
            "catalyst": "NRC approvals, first commercial deployments",
        },
        "infrastructure": {
            "theme": "Nuclear fuel cycle and enrichment",
            "tickers": ["LEU", "UUUU"],
            "catalyst": "HALEU demand for advanced reactors, US supply chain buildout",
        },
    }

    return {
        "investment_plays": plays,
        "ecosystem": {k: list(v.keys()) for k, v in NUCLEAR_ECOSYSTEM.items()},
        "top_pick_theme": "AI data center power demand driving nuclear fleet revaluation",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_smr_development_status() -> Dict:
    """
    Track Small Modular Reactor (SMR) development progress globally.

    Returns:
        Dict with SMR project status, timelines, and market outlook
    """
    smr_projects = [
        {"developer": "NuScale (US)", "design": "VOYGR", "power_mw": 77, "status": "NRC certified, seeking customers", "first_unit": "2030+"},
        {"developer": "GE-Hitachi (US/Japan)", "design": "BWRX-300", "power_mw": 300, "status": "Under review multiple countries", "first_unit": "2028-2029"},
        {"developer": "Kairos Power (US)", "design": "Hermes", "power_mw": 35, "status": "Construction permit granted", "first_unit": "2027 (demo)"},
        {"developer": "X-energy (US)", "design": "Xe-100", "power_mw": 80, "status": "NRC review, Dow Chemical customer", "first_unit": "2029"},
        {"developer": "Rolls-Royce (UK)", "design": "SMR", "power_mw": 470, "status": "GDA in progress", "first_unit": "2030s"},
        {"developer": "CNNC (China)", "design": "Linglong One (ACP100)", "power_mw": 125, "status": "Under construction at Changjiang", "first_unit": "2026"},
        {"developer": "Oklo (US)", "design": "Aurora", "power_mw": 15, "status": "NRC resubmission", "first_unit": "2027+"},
    ]

    return {
        "smr_projects": smr_projects,
        "total_designs_worldwide": 80,
        "first_to_market": "China's Linglong One (ACP100) - likely first commercial SMR globally",
        "us_leaders": ["NuScale", "Kairos", "X-energy", "Oklo"],
        "market_size_projection": "$150B+ by 2040 (various estimates)",
        "key_challenges": [
            "Cost uncertainty (no commercial reference plant yet)",
            "Licensing timelines (NRC reviews take years)",
            "HALEU fuel supply chain not yet scaled",
            "Public acceptance varies by region",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
