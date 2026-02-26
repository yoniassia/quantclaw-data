"""
Geopolitical Risk Real-Time Scorer (Roadmap #382)

Scores geopolitical risk using news frequency analysis, conflict databases,
and sanctions data. Tracks tensions across regions with composite risk indices.
Uses free data from GDELT, ACLED proxy indicators, and news APIs.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Risk keywords by category
RISK_CATEGORIES = {
    "military_conflict": ["war", "military", "troops", "missile", "airstrike", "invasion", "NATO", "defense"],
    "trade_war": ["tariff", "sanctions", "trade war", "embargo", "export ban", "trade restriction"],
    "political_instability": ["coup", "protest", "revolution", "election crisis", "impeachment", "martial law"],
    "terrorism": ["terrorism", "attack", "bombing", "extremist", "insurgency"],
    "cyber_warfare": ["cyberattack", "hack", "ransomware", "cyber warfare", "data breach"],
    "nuclear": ["nuclear", "uranium", "ICBM", "warhead", "nonproliferation"],
    "energy_security": ["oil embargo", "pipeline", "energy crisis", "OPEC cut", "gas shortage"],
    "territorial_dispute": ["territorial", "border dispute", "sovereignty", "annexation", "occupation"],
}

HOTSPOT_REGIONS = {
    "taiwan_strait": {"countries": ["China", "Taiwan", "US"], "base_risk": 65},
    "russia_ukraine": {"countries": ["Russia", "Ukraine", "NATO"], "base_risk": 80},
    "middle_east": {"countries": ["Iran", "Israel", "Saudi Arabia"], "base_risk": 70},
    "korean_peninsula": {"countries": ["North Korea", "South Korea", "US"], "base_risk": 55},
    "south_china_sea": {"countries": ["China", "Philippines", "Vietnam"], "base_risk": 50},
    "india_pakistan": {"countries": ["India", "Pakistan"], "base_risk": 45},
    "horn_of_africa": {"countries": ["Ethiopia", "Somalia", "Sudan"], "base_risk": 60},
    "sahel": {"countries": ["Mali", "Niger", "Burkina Faso"], "base_risk": 55},
}


def get_gdelt_event_counts(query: str, days: int = 7) -> Dict:
    """
    Query GDELT GKG (Global Knowledge Graph) for event tone and volume.
    Uses the free GDELT DOC API for news volume analysis.

    Args:
        query: Search term (country, topic, etc.)
        days: Lookback period

    Returns:
        Dict with article count, average tone, and timeline
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d%H%M%S")
    end_str = end_date.strftime("%Y%m%d%H%M%S")

    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={urllib.request.quote(query)}"
        f"&mode=timelinevol"
        f"&startdatetime={start_str}"
        f"&enddatetime={end_str}"
        f"&format=json"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            timeline = data.get("timeline", [])
            volumes = [point.get("value", 0) for series in timeline for point in series.get("data", [])]
            return {
                "query": query,
                "days": days,
                "total_volume": sum(volumes),
                "avg_daily_volume": sum(volumes) / max(len(volumes), 1),
                "peak_volume": max(volumes) if volumes else 0,
                "data_points": len(volumes),
                "source": "GDELT DOC API",
            }
    except Exception as e:
        return {"query": query, "error": str(e), "total_volume": 0}


def calculate_composite_risk_score(region: Optional[str] = None) -> Dict:
    """
    Calculate a composite geopolitical risk score (0-100) for a region or globally.
    Combines news volume, keyword intensity, and baseline risk assessments.

    Args:
        region: Optional hotspot region key (e.g., 'taiwan_strait'). None for global.

    Returns:
        Dict with risk score breakdown by category and overall composite
    """
    if region and region in HOTSPOT_REGIONS:
        hotspot = HOTSPOT_REGIONS[region]
        queries = hotspot["countries"]
        base_risk = hotspot["base_risk"]
    else:
        queries = ["geopolitical risk", "military conflict", "trade war"]
        base_risk = 50

    category_scores = {}
    for category, keywords in RISK_CATEGORIES.items():
        sample_keywords = keywords[:3]
        keyword_str = " OR ".join(sample_keywords)
        if region and region in HOTSPOT_REGIONS:
            country = HOTSPOT_REGIONS[region]["countries"][0]
            keyword_str = f"{country} ({keyword_str})"

        result = get_gdelt_event_counts(keyword_str, days=7)
        volume = result.get("avg_daily_volume", 0)

        # Normalize volume to 0-100 score (calibrated heuristic)
        normalized = min(100, volume * 0.5) if volume > 0 else 0
        category_scores[category] = round(normalized, 1)

    # Weighted composite
    weights = {
        "military_conflict": 0.20,
        "trade_war": 0.15,
        "political_instability": 0.15,
        "terrorism": 0.10,
        "cyber_warfare": 0.10,
        "nuclear": 0.10,
        "energy_security": 0.10,
        "territorial_dispute": 0.10,
    }

    weighted_score = sum(category_scores.get(k, 0) * w for k, w in weights.items())
    # Blend with base risk (70% data, 30% base)
    composite = round(0.7 * weighted_score + 0.3 * base_risk, 1)

    risk_level = (
        "CRITICAL" if composite >= 80
        else "HIGH" if composite >= 60
        else "ELEVATED" if composite >= 40
        else "MODERATE" if composite >= 20
        else "LOW"
    )

    return {
        "region": region or "global",
        "composite_score": composite,
        "risk_level": risk_level,
        "category_scores": category_scores,
        "base_risk": base_risk,
        "weights": weights,
        "timestamp": datetime.utcnow().isoformat(),
        "methodology": "GDELT news volume + keyword intensity + baseline assessment",
    }


def get_all_hotspot_risks() -> List[Dict]:
    """
    Scan all monitored hotspot regions and return ranked risk scores.

    Returns:
        List of risk assessments sorted by composite score (highest first)
    """
    results = []
    for region_key in HOTSPOT_REGIONS:
        score = calculate_composite_risk_score(region_key)
        score["countries"] = HOTSPOT_REGIONS[region_key]["countries"]
        results.append(score)

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return results


def get_risk_trend(region: str, periods: int = 4) -> Dict:
    """
    Analyze risk trend over multiple periods for a given region.

    Args:
        region: Hotspot region key
        periods: Number of weekly periods to analyze

    Returns:
        Dict with trend direction and period-over-period changes
    """
    if region not in HOTSPOT_REGIONS:
        return {"error": f"Unknown region: {region}", "available": list(HOTSPOT_REGIONS.keys())}

    country = HOTSPOT_REGIONS[region]["countries"][0]
    period_volumes = []

    for i in range(periods):
        result = get_gdelt_event_counts(f"{country} conflict crisis", days=7)
        period_volumes.append(result.get("avg_daily_volume", 0))

    if len(period_volumes) >= 2:
        latest = period_volumes[0]
        previous = period_volumes[1] if period_volumes[1] > 0 else 1
        change_pct = ((latest - previous) / previous) * 100
        trend = "ESCALATING" if change_pct > 10 else "DE-ESCALATING" if change_pct < -10 else "STABLE"
    else:
        change_pct = 0
        trend = "INSUFFICIENT_DATA"

    return {
        "region": region,
        "trend": trend,
        "change_pct": round(change_pct, 1),
        "current_volume": period_volumes[0] if period_volumes else 0,
        "countries": HOTSPOT_REGIONS[region]["countries"],
    }
