"""App Download Tracker — Track mobile app popularity as investment signals.

Roadmap #323: Monitors app store trends using free proxy data sources including
Apple RSS feeds, Google Trends, and public app metadata APIs.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional


# Apple iTunes RSS feeds for top charts (free, no auth)
APPLE_RSS_BASE = "https://rss.applemarketingtools.com/api/v2"

APPLE_CATEGORIES = {
    "all": 0,
    "business": 6000,
    "finance": 6015,
    "games": 6014,
    "social_networking": 6005,
    "entertainment": 6016,
    "productivity": 6007,
    "shopping": 6024,
    "health_fitness": 6013,
    "education": 6017,
    "news": 6009,
    "travel": 6003,
}

COUNTRY_CODES = ["us", "gb", "de", "jp", "kr", "in", "br", "au", "ca", "fr"]


def get_top_free_apps(country: str = "us", limit: int = 25,
                      category: str = "all") -> Dict:
    """Get top free apps from Apple App Store RSS feed.
    
    Args:
        country: Two-letter country code (us, gb, de, jp, etc.)
        limit: Number of apps to return (max 200)
        category: App category (all, business, finance, games, etc.)
    
    Returns:
        Dict with ranked list of top apps and metadata.
    """
    try:
        genre_id = APPLE_CATEGORIES.get(category.lower(), 0)
        url = f"{APPLE_RSS_BASE}/{country}/apps/top-free/{limit}/apps.json"
        if genre_id > 0:
            url = f"{APPLE_RSS_BASE}/{country}/apps/top-free/{limit}/genre={genre_id}/apps.json"
        
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        feed = data.get("feed", {})
        results = feed.get("results", [])
        
        apps = []
        for i, app in enumerate(results, 1):
            apps.append({
                "rank": i,
                "name": app.get("name", ""),
                "artist": app.get("artistName", ""),
                "id": app.get("id", ""),
                "url": app.get("url", ""),
                "genres": [g.get("name", "") for g in app.get("genres", [])],
            })
        
        return {
            "country": country,
            "category": category,
            "chart": "top_free",
            "count": len(apps),
            "timestamp": datetime.utcnow().isoformat(),
            "apps": apps,
            "source": "Apple App Store RSS"
        }
    except Exception as e:
        return {"country": country, "category": category, "error": str(e)}


def get_top_paid_apps(country: str = "us", limit: int = 25,
                      category: str = "all") -> Dict:
    """Get top paid apps from Apple App Store RSS feed.
    
    Args:
        country: Two-letter country code
        limit: Number of apps (max 200)
        category: App category
    
    Returns:
        Dict with ranked list of top paid apps.
    """
    try:
        genre_id = APPLE_CATEGORIES.get(category.lower(), 0)
        url = f"{APPLE_RSS_BASE}/{country}/apps/top-paid/{limit}/apps.json"
        if genre_id > 0:
            url = f"{APPLE_RSS_BASE}/{country}/apps/top-paid/{limit}/genre={genre_id}/apps.json"
        
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        feed = data.get("feed", {})
        results = feed.get("results", [])
        
        apps = []
        for i, app in enumerate(results, 1):
            apps.append({
                "rank": i,
                "name": app.get("name", ""),
                "artist": app.get("artistName", ""),
                "id": app.get("id", ""),
                "url": app.get("url", ""),
            })
        
        return {
            "country": country,
            "category": category,
            "chart": "top_paid",
            "count": len(apps),
            "timestamp": datetime.utcnow().isoformat(),
            "apps": apps,
            "source": "Apple App Store RSS"
        }
    except Exception as e:
        return {"country": country, "category": category, "error": str(e)}


def compare_app_rankings(app_name: str, countries: Optional[List[str]] = None,
                         category: str = "all") -> Dict:
    """Compare an app's ranking across multiple countries.
    
    Args:
        app_name: App name to search for (case-insensitive partial match)
        countries: List of country codes (defaults to top 10 markets)
        category: App category to check
    
    Returns:
        Dict with the app's rank in each country (None if not in top charts).
    """
    if countries is None:
        countries = COUNTRY_CODES
    
    rankings = {}
    app_lower = app_name.lower()
    
    for country in countries:
        chart = get_top_free_apps(country, limit=100, category=category)
        apps = chart.get("apps", [])
        
        found = None
        for app in apps:
            if app_lower in app.get("name", "").lower():
                found = app["rank"]
                break
        
        rankings[country] = found
    
    ranked_countries = {k: v for k, v in rankings.items() if v is not None}
    unranked = [k for k, v in rankings.items() if v is None]
    
    return {
        "app_name": app_name,
        "category": category,
        "rankings": rankings,
        "ranked_in": len(ranked_countries),
        "total_markets": len(countries),
        "best_rank": min(ranked_countries.values()) if ranked_countries else None,
        "best_market": min(ranked_countries, key=ranked_countries.get) if ranked_countries else None,
        "not_ranked_in": unranked,
        "timestamp": datetime.utcnow().isoformat()
    }


def finance_app_leaderboard(country: str = "us", limit: int = 50) -> Dict:
    """Get the finance/fintech app leaderboard — useful for tracking competitors.
    
    Args:
        country: Country code
        limit: Number of apps
    
    Returns:
        Dict with top finance apps and investment signals.
    """
    return get_top_free_apps(country, limit, category="finance")
