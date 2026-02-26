"""Metaverse Economy Dashboard — tracks metaverse market data, virtual world metrics, and XR industry trends."""

import json
import urllib.request
from datetime import datetime


def get_metaverse_companies():
    """Return publicly traded companies with significant metaverse exposure."""
    companies = [
        {"ticker": "META", "name": "Meta Platforms", "segment": "Reality Labs", "revenue_segment_pct": 3},
        {"ticker": "RBLX", "name": "Roblox", "segment": "Virtual World Platform", "revenue_segment_pct": 100},
        {"ticker": "U", "name": "Unity Software", "segment": "3D Engine / XR", "revenue_segment_pct": 100},
        {"ticker": "SNAP", "name": "Snap Inc", "segment": "AR Lenses / Spectacles", "revenue_segment_pct": 15},
        {"ticker": "MANA-USD", "name": "Decentraland", "segment": "Virtual Real Estate", "revenue_segment_pct": 100},
        {"ticker": "SAND-USD", "name": "The Sandbox", "segment": "Virtual Real Estate", "revenue_segment_pct": 100},
        {"ticker": "AXS-USD", "name": "Axie Infinity", "segment": "GameFi", "revenue_segment_pct": 100},
        {"ticker": "AAPL", "name": "Apple", "segment": "Vision Pro / XR", "revenue_segment_pct": 1},
        {"ticker": "MSFT", "name": "Microsoft", "segment": "Mesh / HoloLens", "revenue_segment_pct": 2},
        {"ticker": "NVDA", "name": "NVIDIA", "segment": "Omniverse", "revenue_segment_pct": 5},
    ]
    return {"companies": companies, "count": len(companies), "as_of": datetime.utcnow().isoformat()}


def get_metaverse_market_size():
    """Return metaverse market size estimates and growth projections."""
    return {
        "global_market_2024_usd_bn": 74.4,
        "projected_2030_usd_bn": 507.8,
        "cagr_pct": 37.7,
        "segments": [
            {"name": "Gaming", "share_pct": 30, "growth": "High"},
            {"name": "Social / Communication", "share_pct": 20, "growth": "High"},
            {"name": "Virtual Commerce", "share_pct": 18, "growth": "Very High"},
            {"name": "Enterprise / Collaboration", "share_pct": 15, "growth": "Medium"},
            {"name": "Education / Training", "share_pct": 10, "growth": "Medium"},
            {"name": "Healthcare / Therapy", "share_pct": 7, "growth": "Medium"},
        ],
        "hardware": {
            "vr_headset_shipments_2024_m": 8.5,
            "ar_glasses_shipments_2024_m": 1.2,
            "key_devices": ["Meta Quest 3", "Apple Vision Pro", "PSVR2", "Pico 4"],
        },
        "as_of": datetime.utcnow().isoformat(),
    }


def get_virtual_land_metrics():
    """Get virtual real estate metrics across major metaverse platforms."""
    platforms = [
        {"platform": "Decentraland", "token": "MANA", "total_parcels": 90601, "avg_price_usd": 1200, "floor_price_usd": 800},
        {"platform": "The Sandbox", "token": "SAND", "total_parcels": 166464, "avg_price_usd": 900, "floor_price_usd": 500},
        {"platform": "Otherside", "token": "APE", "total_parcels": 100000, "avg_price_usd": 600, "floor_price_usd": 350},
        {"platform": "Somnium Space", "token": "CUBE", "total_parcels": 5000, "avg_price_usd": 3500, "floor_price_usd": 2000},
    ]
    total_value = sum(p["total_parcels"] * p["avg_price_usd"] for p in platforms)
    return {"platforms": platforms, "total_estimated_value_usd": total_value, "as_of": datetime.utcnow().isoformat()}


def get_xr_adoption_metrics():
    """Track XR (VR/AR/MR) hardware and software adoption trends."""
    return {
        "vr_monthly_active_users_m": 35,
        "ar_daily_active_users_m": 200,
        "steam_vr_pct_users": 1.8,
        "top_vr_apps": ["Beat Saber", "VRChat", "Gorilla Tag", "Resident Evil 4 VR", "Half-Life: Alyx"],
        "enterprise_adoption_pct_fortune500": 22,
        "developer_count_estimate": 500000,
        "investment_2024_usd_bn": 12.5,
        "as_of": datetime.utcnow().isoformat(),
    }
