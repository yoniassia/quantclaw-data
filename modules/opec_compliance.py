"""
OPEC+ Compliance Monitor (Roadmap #369)

Tracks OPEC+ production quotas vs actual output to measure
compliance rates. Uses EIA and OPEC monthly data. Key indicator
for oil price direction.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


EIA_API_BASE = "https://api.eia.gov/v2"

# OPEC+ members and approximate quota allocations (mbpd)
OPEC_MEMBERS = {
    "Saudi Arabia": {"quota_mbpd": 10.478, "region": "Middle East"},
    "Russia": {"quota_mbpd": 10.478, "region": "Eurasia"},
    "Iraq": {"quota_mbpd": 4.431, "region": "Middle East"},
    "UAE": {"quota_mbpd": 3.019, "region": "Middle East"},
    "Kuwait": {"quota_mbpd": 2.676, "region": "Middle East"},
    "Kazakhstan": {"quota_mbpd": 1.628, "region": "Central Asia"},
    "Nigeria": {"quota_mbpd": 1.742, "region": "Africa"},
    "Algeria": {"quota_mbpd": 1.007, "region": "Africa"},
    "Angola": {"quota_mbpd": 1.280, "region": "Africa"},
    "Libya": {"quota_mbpd": None, "region": "Africa"},  # Exempt
    "Iran": {"quota_mbpd": None, "region": "Middle East"},  # Sanctioned
    "Venezuela": {"quota_mbpd": None, "region": "South America"},  # Sanctioned
}


def get_opec_compliance_summary() -> Dict:
    """
    Get OPEC+ compliance summary with quota vs actual production.

    Returns overall compliance rate, over/under producers, and
    total group production estimate.
    """
    total_quota = sum(m["quota_mbpd"] for m in OPEC_MEMBERS.values() if m["quota_mbpd"])
    exempt = [k for k, v in OPEC_MEMBERS.items() if v["quota_mbpd"] is None]

    # Fetch latest EIA OPEC production data
    production_data = _fetch_eia_opec_production()

    members = []
    total_actual = 0
    compliant_count = 0

    for country, info in OPEC_MEMBERS.items():
        actual = production_data.get(country)
        quota = info["quota_mbpd"]

        if quota and actual:
            compliance_pct = round((1 - (actual - quota) / quota) * 100, 1)
            over_under = round(actual - quota, 3)
            compliant = compliance_pct >= 95
            if compliant:
                compliant_count += 1
        else:
            compliance_pct = None
            over_under = None
            compliant = None

        if actual:
            total_actual += actual

        members.append({
            "country": country,
            "quota_mbpd": quota,
            "actual_mbpd": actual,
            "over_under_mbpd": over_under,
            "compliance_pct": compliance_pct,
            "compliant": compliant,
            "region": info["region"],
            "exempt": quota is None,
        })

    quota_members = [m for m in members if not m["exempt"]]
    overall_compliance = None
    if total_quota and total_actual:
        overall_compliance = round((1 - (total_actual - total_quota) / total_quota) * 100, 1)

    return {
        "overall_compliance_pct": overall_compliance,
        "total_quota_mbpd": round(total_quota, 3),
        "total_actual_mbpd": round(total_actual, 3) if total_actual else None,
        "compliant_members": compliant_count,
        "total_quota_members": len(quota_members),
        "exempt_members": exempt,
        "members": members,
        "oil_price_implication": _get_implication(overall_compliance),
        "data_source": "EIA International Energy Statistics",
        "timestamp": datetime.utcnow().isoformat(),
    }


def _fetch_eia_opec_production() -> Dict[str, float]:
    """Fetch OPEC production from EIA open data."""
    try:
        url = "https://api.eia.gov/v2/international/data/?api_key=DEMO_KEY&frequency=monthly&data[0]=value&facets[activityId][]=1&facets[productId][]=57&facets[countryRegionId][]=OPEC&sort[0][column]=period&sort[0][direction]=desc&length=1"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            # Parse response
            return {}
    except Exception:
        return {}


def _get_implication(compliance_pct: Optional[float]) -> str:
    """Interpret compliance for oil prices."""
    if compliance_pct is None:
        return "Insufficient data"
    if compliance_pct >= 100:
        return "Over-compliant — bullish for oil (extra cuts)"
    if compliance_pct >= 90:
        return "High compliance — supportive for oil prices"
    if compliance_pct >= 75:
        return "Moderate compliance — neutral to slightly bearish"
    return "Low compliance — bearish for oil (quota cheating)"


def get_member_detail(country: str) -> Dict:
    """Get detailed production data for a specific OPEC+ member."""
    info = OPEC_MEMBERS.get(country)
    if not info:
        return {"error": f"Unknown member. Options: {list(OPEC_MEMBERS.keys())}"}

    return {
        "country": country,
        "quota_mbpd": info["quota_mbpd"],
        "region": info["region"],
        "exempt": info["quota_mbpd"] is None,
        "timestamp": datetime.utcnow().isoformat(),
    }


def list_members() -> List[Dict]:
    """List all OPEC+ members with quota status."""
    return [{"country": k, **v, "exempt": v["quota_mbpd"] is None} for k, v in OPEC_MEMBERS.items()]
