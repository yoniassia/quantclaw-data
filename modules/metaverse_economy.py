"""
Metaverse Economy Dashboard (Roadmap #397)

Tracks virtual world economies, digital land markets, avatar commerce,
and metaverse platform metrics using public data sources.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


METAVERSE_PLATFORMS = {
    "Decentraland": {
        "token": "MANA",
        "land_token": "LAND",
        "blockchain": "Ethereum",
        "category": "crypto_native",
        "peak_land_price_usd": 2_400_000,
        "total_land_parcels": 90_601,
    },
    "The Sandbox": {
        "token": "SAND",
        "land_token": "LAND",
        "blockchain": "Ethereum",
        "category": "crypto_native",
        "total_land_parcels": 166_464,
    },
    "Roblox": {
        "ticker": "RBLX",
        "currency": "Robux",
        "category": "gaming",
        "dau_millions": 70,
        "annual_revenue_bn": 2.7,
    },
    "Fortnite / Epic": {
        "category": "gaming",
        "registered_users_millions": 400,
        "virtual_economy_annual_bn": 5.0,
    },
    "Meta Horizon Worlds": {
        "ticker": "META",
        "category": "social",
        "status": "early_stage",
        "reality_labs_annual_loss_bn": 16.0,
    },
    "Otherside (Yuga Labs)": {
        "token": "APE",
        "blockchain": "Ethereum",
        "category": "crypto_native",
        "total_land_parcels": 200_000,
    },
    "Spatial": {
        "category": "social",
        "status": "growing",
    },
    "VRChat": {
        "category": "social",
        "monthly_active_users": 4_000_000,
    },
}

METAVERSE_SECTORS = [
    "virtual_real_estate",
    "avatar_fashion_wearables",
    "virtual_events_concerts",
    "gaming_play_to_earn",
    "virtual_advertising",
    "creator_economy",
    "enterprise_collaboration",
    "education_training",
]


def get_metaverse_overview() -> Dict:
    """
    Get a comprehensive overview of the metaverse economy including
    all tracked platforms, sectors, and market sizing.
    """
    crypto_native = [k for k, v in METAVERSE_PLATFORMS.items() if v.get("category") == "crypto_native"]
    gaming = [k for k, v in METAVERSE_PLATFORMS.items() if v.get("category") == "gaming"]
    social = [k for k, v in METAVERSE_PLATFORMS.items() if v.get("category") == "social"]

    return {
        "platforms_tracked": len(METAVERSE_PLATFORMS),
        "categories": {
            "crypto_native": crypto_native,
            "gaming": gaming,
            "social": social,
        },
        "sectors": METAVERSE_SECTORS,
        "market_size_estimate": {
            "2024_bn_usd": 65,
            "2030_projected_bn_usd": 936,
            "cagr_pct": 40,
        },
        "as_of": datetime.utcnow().isoformat(),
    }


def get_platform_detail(platform_name: str) -> Optional[Dict]:
    """
    Get detailed metrics for a specific metaverse platform.
    """
    for name, data in METAVERSE_PLATFORMS.items():
        if platform_name.lower() in name.lower():
            return {"name": name, **data}
    return None


def virtual_real_estate_metrics() -> Dict:
    """
    Aggregate virtual real estate market metrics across platforms.
    """
    total_parcels = sum(
        p.get("total_land_parcels", 0) for p in METAVERSE_PLATFORMS.values()
    )
    platforms_with_land = [
        {"name": k, "parcels": v["total_land_parcels"], "blockchain": v.get("blockchain", "N/A")}
        for k, v in METAVERSE_PLATFORMS.items()
        if "total_land_parcels" in v
    ]

    return {
        "total_virtual_parcels": total_parcels,
        "platforms": platforms_with_land,
        "market_observations": [
            "Virtual land prices peaked in Q1 2022 during metaverse hype",
            "Floor prices dropped 80-95% from peaks by 2024",
            "Institutional interest shifted to utility-based virtual spaces",
            "Enterprise metaverse (training/collab) growing faster than consumer",
        ],
    }


def metaverse_investment_landscape() -> Dict:
    """
    Track corporate and VC investment in metaverse technologies.
    """
    return {
        "major_corporate_bets": [
            {"company": "Meta", "investment_bn": 46, "period": "2020-2025", "focus": "VR/AR hardware + Horizon"},
            {"company": "Epic Games", "investment_bn": 4, "period": "2020-2025", "focus": "Unreal Engine + Fortnite"},
            {"company": "Microsoft", "investment_bn": 69, "period": "2022", "focus": "Activision acquisition (gaming)"},
            {"company": "Apple", "investment_bn": 2, "period": "2023-2025", "focus": "Vision Pro spatial computing"},
        ],
        "vc_funding_trend": [
            {"year": 2021, "funding_bn": 13.0},
            {"year": 2022, "funding_bn": 7.0},
            {"year": 2023, "funding_bn": 3.5},
            {"year": 2024, "funding_bn": 2.0},
        ],
        "key_enablers": [
            "VR/AR headset adoption curve",
            "5G/6G bandwidth for streaming",
            "AI-generated 3D content",
            "Blockchain interoperability for digital assets",
            "Spatial computing (Apple Vision Pro effect)",
        ],
    }
