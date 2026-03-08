#!/usr/bin/env python3
"""
AppTweak API — App store optimization data and mobile app intelligence.

Provides keyword rankings, download estimates, reviews, competitor analysis,
and app metadata for iOS and Android apps. Useful for quantitative analysis
of app-driven companies (tracking engagement, market share, sentiment).

Source: https://www.apptweak.com/en/api
Update frequency: Daily
Category: Web Traffic & App Data
Free tier: Up to 500 requests/month with basic data access
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://api.apptweak.com"
DEFAULT_TOKEN = os.environ.get("APPTWEAK_API_KEY") or os.environ.get("APPTWEAK_TOKEN")


def _make_request(endpoint: str, params: Optional[dict] = None, token: Optional[str] = None) -> dict:
    """
    Internal helper to make authenticated requests to the AppTweak API.

    Args:
        endpoint: API path (e.g., '/android/applications/com.whatsapp/metadata.json')
        params: Additional query parameters
        token: API token (falls back to env var APPTWEAK_API_KEY)

    Returns:
        Parsed JSON response as dict
    """
    api_token = token or DEFAULT_TOKEN
    if not api_token:
        return {
            "error": "API key required. Set APPTWEAK_API_KEY env var or pass token= parameter. "
                     "Get a free key at https://www.apptweak.com/en/pricing"
        }

    query = params.copy() if params else {}
    url = f"{API_BASE}{endpoint}"

    headers = {
        "X-Apptweak-Key": api_token,
        "Accept": "application/json",
        "User-Agent": "QuantClaw-Data/1.0"
    }

    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:500]
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": body}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Android endpoints
# ---------------------------------------------------------------------------

def get_android_app_metadata(
    package_id: str,
    country: str = "us",
    language: str = "en",
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get metadata for an Android app from Google Play.

    Args:
        package_id: Android package name (e.g., 'com.whatsapp')
        country: ISO country code
        language: ISO language code
        token: AppTweak API token

    Returns:
        dict with app title, rating, downloads, category, description, etc.

    Example:
        >>> meta = get_android_app_metadata('com.whatsapp')
        >>> print(meta.get('title'), meta.get('rating'))
    """
    endpoint = f"/android/applications/{package_id}/metadata.json"
    params = {"country": country, "language": language}
    return _make_request(endpoint, params, token)


def get_android_app_reviews(
    package_id: str,
    country: str = "us",
    language: str = "en",
    limit: int = 25,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get recent reviews for an Android app.

    Args:
        package_id: Android package name
        country: ISO country code
        language: ISO language code
        limit: Number of reviews to return (max 100)
        token: AppTweak API token

    Returns:
        dict with list of reviews including rating, text, date, author
    """
    endpoint = f"/android/applications/{package_id}/reviews.json"
    params = {"country": country, "language": language, "num": min(limit, 100)}
    return _make_request(endpoint, params, token)


def search_android_apps(
    query: str,
    country: str = "us",
    language: str = "en",
    limit: int = 10,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for Android apps by keyword.

    Args:
        query: Search term
        country: ISO country code
        language: ISO language code
        limit: Max results
        token: AppTweak API token

    Returns:
        dict with list of matching apps (title, package_id, rating, etc.)
    """
    endpoint = "/android/searches.json"
    params = {"term": query, "country": country, "language": language, "num": min(limit, 50)}
    return _make_request(endpoint, params, token)


def get_android_top_charts(
    category: str = "",
    chart_type: str = "free",
    country: str = "us",
    limit: int = 25,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get Android top chart rankings.

    Args:
        category: Google Play category (e.g., 'FINANCE', 'GAME'). Empty for overall.
        chart_type: 'free', 'paid', or 'grossing'
        country: ISO country code
        limit: Number of results
        token: AppTweak API token

    Returns:
        dict with ranked list of apps
    """
    endpoint = "/android/rankings.json"
    params = {
        "type": chart_type,
        "country": country,
        "num": min(limit, 200)
    }
    if category:
        params["category"] = category
    return _make_request(endpoint, params, token)


# ---------------------------------------------------------------------------
# iOS endpoints
# ---------------------------------------------------------------------------

def get_ios_app_metadata(
    app_id: str,
    country: str = "us",
    language: str = "en",
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get metadata for an iOS app from the App Store.

    Args:
        app_id: Numeric App Store ID (e.g., '310633997' for WhatsApp)
        country: ISO country code
        language: ISO language code
        token: AppTweak API token

    Returns:
        dict with app title, rating, price, category, description, etc.

    Example:
        >>> meta = get_ios_app_metadata('310633997')
        >>> print(meta.get('title'), meta.get('rating'))
    """
    endpoint = f"/ios/applications/{app_id}/metadata.json"
    params = {"country": country, "language": language}
    return _make_request(endpoint, params, token)


def get_ios_app_reviews(
    app_id: str,
    country: str = "us",
    language: str = "en",
    limit: int = 25,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get recent reviews for an iOS app.

    Args:
        app_id: Numeric App Store ID
        country: ISO country code
        language: ISO language code
        limit: Number of reviews to return
        token: AppTweak API token

    Returns:
        dict with list of reviews including rating, text, date, author
    """
    endpoint = f"/ios/applications/{app_id}/reviews.json"
    params = {"country": country, "language": language, "num": min(limit, 100)}
    return _make_request(endpoint, params, token)


def search_ios_apps(
    query: str,
    country: str = "us",
    language: str = "en",
    limit: int = 10,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for iOS apps by keyword.

    Args:
        query: Search term
        country: ISO country code
        language: ISO language code
        limit: Max results
        token: AppTweak API token

    Returns:
        dict with list of matching apps
    """
    endpoint = "/ios/searches.json"
    params = {"term": query, "country": country, "language": language, "num": min(limit, 50)}
    return _make_request(endpoint, params, token)


def get_ios_top_charts(
    category: str = "",
    chart_type: str = "free",
    country: str = "us",
    limit: int = 25,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get iOS App Store top chart rankings.

    Args:
        category: App Store category ID. Empty for overall.
        chart_type: 'free', 'paid', or 'grossing'
        country: ISO country code
        limit: Number of results
        token: AppTweak API token

    Returns:
        dict with ranked list of apps
    """
    endpoint = "/ios/rankings.json"
    params = {
        "type": chart_type,
        "country": country,
        "num": min(limit, 200)
    }
    if category:
        params["category"] = category
    return _make_request(endpoint, params, token)


# ---------------------------------------------------------------------------
# Cross-platform / keyword tools
# ---------------------------------------------------------------------------

def get_keyword_stats(
    keyword: str,
    platform: str = "android",
    country: str = "us",
    language: str = "en",
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get keyword search volume and difficulty stats.

    Args:
        keyword: Search keyword to analyze
        platform: 'android' or 'ios'
        country: ISO country code
        language: ISO language code
        token: AppTweak API token

    Returns:
        dict with search volume, difficulty, traffic score
    """
    endpoint = f"/{platform}/keywords/{urllib.parse.quote(keyword, safe='')}/stats.json"
    params = {"country": country, "language": language}
    return _make_request(endpoint, params, token)


def get_app_keyword_rankings(
    app_id: str,
    platform: str = "android",
    country: str = "us",
    language: str = "en",
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get keyword rankings for a specific app.

    Args:
        app_id: Package name (Android) or numeric ID (iOS)
        platform: 'android' or 'ios'
        country: ISO country code
        language: ISO language code
        token: AppTweak API token

    Returns:
        dict with keywords the app ranks for and their positions
    """
    endpoint = f"/{platform}/applications/{app_id}/keywords.json"
    params = {"country": country, "language": language}
    return _make_request(endpoint, params, token)


def get_download_estimates(
    app_id: str,
    platform: str = "android",
    country: str = "us",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get download estimates for an app.

    Args:
        app_id: Package name (Android) or numeric ID (iOS)
        platform: 'android' or 'ios'
        country: ISO country code
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        token: AppTweak API token

    Returns:
        dict with daily/monthly download estimates
    """
    endpoint = f"/{platform}/applications/{app_id}/downloads.json"
    params = {"country": country}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _make_request(endpoint, params, token)


def get_revenue_estimates(
    app_id: str,
    platform: str = "android",
    country: str = "us",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get revenue estimates for an app.

    Args:
        app_id: Package name (Android) or numeric ID (iOS)
        platform: 'android' or 'ios'
        country: ISO country code
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        token: AppTweak API token

    Returns:
        dict with daily/monthly revenue estimates
    """
    endpoint = f"/{platform}/applications/{app_id}/revenues.json"
    params = {"country": country}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _make_request(endpoint, params, token)


# ---------------------------------------------------------------------------
# Convenience / aggregation
# ---------------------------------------------------------------------------

def get_app_overview(
    app_id: str,
    platform: str = "android",
    country: str = "us",
    language: str = "en",
    token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get a combined overview of an app: metadata + reviews summary.

    Args:
        app_id: Package name (Android) or numeric ID (iOS)
        platform: 'android' or 'ios'
        country: ISO country code
        language: ISO language code
        token: AppTweak API token

    Returns:
        dict with metadata, recent reviews, and review stats
    """
    if platform == "android":
        meta = get_android_app_metadata(app_id, country, language, token)
        reviews = get_android_app_reviews(app_id, country, language, limit=5, token=token)
    elif platform == "ios":
        meta = get_ios_app_metadata(app_id, country, language, token)
        reviews = get_ios_app_reviews(app_id, country, language, limit=5, token=token)
    else:
        return {"error": f"Invalid platform '{platform}'. Use 'android' or 'ios'."}

    return {
        "app_id": app_id,
        "platform": platform,
        "country": country,
        "metadata": meta,
        "recent_reviews": reviews,
        "fetched_at": datetime.utcnow().isoformat()
    }


# ---------------------------------------------------------------------------
# Module info
# ---------------------------------------------------------------------------

MODULE_INFO = {
    "name": "apptweak_api",
    "version": "1.0.0",
    "source": "https://www.apptweak.com/en/api",
    "category": "Web Traffic & App Data",
    "free_tier": True,
    "free_tier_details": "500 requests/month, basic data access",
    "auth": "API key via X-Apptweak-Key header (env: APPTWEAK_API_KEY)",
    "functions": [
        "get_android_app_metadata",
        "get_android_app_reviews",
        "search_android_apps",
        "get_android_top_charts",
        "get_ios_app_metadata",
        "get_ios_app_reviews",
        "search_ios_apps",
        "get_ios_top_charts",
        "get_keyword_stats",
        "get_app_keyword_rankings",
        "get_download_estimates",
        "get_revenue_estimates",
        "get_app_overview",
    ],
    "update_frequency": "daily",
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
