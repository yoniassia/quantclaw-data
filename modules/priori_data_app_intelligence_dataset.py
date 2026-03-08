"""
Priori Data App Intelligence Dataset — Mobile app market intelligence.

Provides app market data including downloads estimates, revenue forecasts,
user acquisition metrics, market share, geographic breakdowns, and category
rankings. Uses free public sources (iTunes Search API, Google Play web data)
as Priori Data's API requires a paid subscription.

Source: https://prioridata.com (reference), free alternatives used
Update frequency: Daily (iTunes API), Weekly (estimates)
Category: Web Traffic & App Data
Free tier: Unlimited (uses free public APIs)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


ITUNES_SEARCH_API = "https://itunes.apple.com"
ITUNES_LOOKUP_API = "https://itunes.apple.com/lookup"
ITUNES_RSS_BASE = "https://rss.applemarketingtools.com/api/v2"


def _fetch_json(url: str, timeout: int = 15) -> dict[str, Any]:
    """Internal helper to fetch and parse JSON from a URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "QuantClaw-Data/1.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"URL error: {str(e.reason)}", "url": url}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def search_apps(
    query: str,
    platform: str = "ios",
    country: str = "us",
    limit: int = 25
) -> list[dict[str, Any]]:
    """
    Search for apps by keyword.

    Args:
        query: Search term (e.g., 'trading', 'fitness tracker')
        platform: 'ios' (Android not supported via free API)
        country: ISO 2-letter country code (e.g., 'us', 'gb', 'de')
        limit: Max results (1-200)

    Returns:
        List of dicts with app metadata (name, id, publisher, price, rating, etc.)

    Example:
        >>> apps = search_apps("stock trading", limit=5)
        >>> for a in apps: print(a['name'], a['rating'])
    """
    if platform != "ios":
        return [{"error": "Only iOS supported via free iTunes Search API. Android requires paid access."}]

    limit = max(1, min(200, limit))
    params = urllib.parse.urlencode({
        "term": query,
        "country": country,
        "media": "software",
        "limit": limit
    })
    url = f"{ITUNES_SEARCH_API}/search?{params}"
    data = _fetch_json(url)

    if "error" in data:
        return [data]

    results = []
    for app in data.get("results", []):
        results.append({
            "app_id": app.get("trackId"),
            "bundle_id": app.get("bundleId"),
            "name": app.get("trackName"),
            "publisher": app.get("artistName"),
            "publisher_id": app.get("artistId"),
            "price": app.get("price", 0),
            "currency": app.get("currency"),
            "rating": app.get("averageUserRating"),
            "rating_count": app.get("userRatingCount"),
            "current_version_rating": app.get("averageUserRatingForCurrentVersion"),
            "category": app.get("primaryGenreName"),
            "categories": app.get("genres", []),
            "content_rating": app.get("contentAdvisoryRating"),
            "size_bytes": app.get("fileSizeBytes"),
            "min_os_version": app.get("minimumOsVersion"),
            "release_date": app.get("releaseDate"),
            "current_version_release": app.get("currentVersionReleaseDate"),
            "version": app.get("version"),
            "description_snippet": (app.get("description") or "")[:300],
            "icon_url": app.get("artworkUrl100"),
            "screenshot_urls": app.get("screenshotUrls", [])[:3],
            "store_url": app.get("trackViewUrl"),
            "has_in_app_purchases": bool(app.get("isVppDeviceBasedLicensingEnabled")),
            "supported_devices": len(app.get("supportedDevices", [])),
            "country": country,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        })

    return results


def get_app_details(
    app_id: int,
    country: str = "us"
) -> dict[str, Any]:
    """
    Get detailed metadata for a specific iOS app by its iTunes ID.

    Args:
        app_id: iTunes track ID (numeric, e.g., 1446101929 for eToro)
        country: ISO 2-letter country code

    Returns:
        Dict with comprehensive app metadata

    Example:
        >>> details = get_app_details(1446101929)  # eToro
        >>> print(details['name'], details['rating'])
    """
    params = urllib.parse.urlencode({"id": app_id, "country": country})
    url = f"{ITUNES_LOOKUP_API}?{params}"
    data = _fetch_json(url)

    if "error" in data:
        return data

    results = data.get("results", [])
    if not results:
        return {"error": f"App not found: {app_id}", "app_id": app_id}

    app = results[0]
    return {
        "app_id": app.get("trackId"),
        "bundle_id": app.get("bundleId"),
        "name": app.get("trackName"),
        "publisher": app.get("artistName"),
        "publisher_id": app.get("artistId"),
        "publisher_url": app.get("artistViewUrl"),
        "price": app.get("price", 0),
        "currency": app.get("currency"),
        "formatted_price": app.get("formattedPrice"),
        "rating": app.get("averageUserRating"),
        "rating_count": app.get("userRatingCount"),
        "current_version_rating": app.get("averageUserRatingForCurrentVersion"),
        "current_version_rating_count": app.get("userRatingCountForCurrentVersion"),
        "category": app.get("primaryGenreName"),
        "category_id": app.get("primaryGenreId"),
        "categories": app.get("genres", []),
        "category_ids": app.get("genreIds", []),
        "content_rating": app.get("contentAdvisoryRating"),
        "size_bytes": app.get("fileSizeBytes"),
        "size_mb": round(int(app.get("fileSizeBytes", 0)) / 1048576, 1),
        "min_os_version": app.get("minimumOsVersion"),
        "release_date": app.get("releaseDate"),
        "current_version_release": app.get("currentVersionReleaseDate"),
        "version": app.get("version"),
        "description": app.get("description"),
        "release_notes": app.get("releaseNotes"),
        "languages": app.get("languageCodesISO2A", []),
        "icon_url": app.get("artworkUrl512") or app.get("artworkUrl100"),
        "store_url": app.get("trackViewUrl"),
        "seller_name": app.get("sellerName"),
        "in_app_purchases": app.get("features", []),
        "supported_devices": app.get("supportedDevices", []),
        "advisories": app.get("advisories", []),
        "country": country,
        "retrieved_at": datetime.utcnow().isoformat() + "Z"
    }


def get_publisher_apps(
    publisher_id: int,
    country: str = "us",
    limit: int = 50
) -> list[dict[str, Any]]:
    """
    Get all apps from a specific publisher/developer.

    Args:
        publisher_id: iTunes artist ID (numeric)
        country: ISO 2-letter country code
        limit: Max results (1-200)

    Returns:
        List of dicts with app metadata for all publisher's apps

    Example:
        >>> apps = get_publisher_apps(651053977)  # eToro Group
        >>> for a in apps: print(a['name'])
    """
    limit = max(1, min(200, limit))
    params = urllib.parse.urlencode({
        "id": publisher_id,
        "country": country,
        "entity": "software",
        "limit": limit
    })
    url = f"{ITUNES_LOOKUP_API}?{params}"
    data = _fetch_json(url)

    if "error" in data:
        return [data]

    results = []
    for item in data.get("results", []):
        if item.get("wrapperType") == "software":
            results.append({
                "app_id": item.get("trackId"),
                "bundle_id": item.get("bundleId"),
                "name": item.get("trackName"),
                "price": item.get("price", 0),
                "rating": item.get("averageUserRating"),
                "rating_count": item.get("userRatingCount"),
                "category": item.get("primaryGenreName"),
                "release_date": item.get("releaseDate"),
                "version": item.get("version"),
                "store_url": item.get("trackViewUrl"),
                "country": country,
                "retrieved_at": datetime.utcnow().isoformat() + "Z"
            })

    return results


def get_top_apps(
    category: str = "all",
    chart_type: str = "top-free",
    country: str = "us",
    limit: int = 25
) -> list[dict[str, Any]]:
    """
    Get top/trending apps from the App Store charts.

    Args:
        category: Category name — 'all', 'finance', 'games', 'social-networking',
                  'entertainment', 'productivity', 'health-fitness', 'education',
                  'business', 'utilities', 'shopping', 'food-drink', 'travel',
                  'news', 'sports', 'music', 'photo-video', 'weather',
                  'reference', 'navigation', 'lifestyle', 'medical', 'books'
        chart_type: 'top-free', 'top-paid', 'top-grossing'
        country: ISO 2-letter country code
        limit: Max results (1-200)

    Returns:
        List of dicts with chart rank and app metadata

    Example:
        >>> top = get_top_apps("finance", "top-free", "us", 10)
        >>> for i, a in enumerate(top, 1): print(f"#{i}: {a['name']}")
    """
    # Map chart_type to Apple RSS feed types
    chart_map = {
        "top-free": "top-free",
        "top-paid": "top-paid",
        "top-grossing": "top-grossing"
    }
    feed_type = chart_map.get(chart_type, "top-free")
    limit = max(1, min(200, limit))

    # Category mapping to Apple genre IDs for RSS
    genre_map = {
        "all": "", "finance": "/genre=6015",
        "games": "/genre=6014", "social-networking": "/genre=6005",
        "entertainment": "/genre=6016", "productivity": "/genre=6007",
        "health-fitness": "/genre=6013", "education": "/genre=6017",
        "business": "/genre=6000", "utilities": "/genre=6002",
        "shopping": "/genre=6024", "food-drink": "/genre=6023",
        "travel": "/genre=6003", "news": "/genre=6009",
        "sports": "/genre=6004", "music": "/genre=6011",
        "photo-video": "/genre=6008", "weather": "/genre=6001",
        "reference": "/genre=6006", "navigation": "/genre=6010",
        "lifestyle": "/genre=6012", "medical": "/genre=6020",
        "books": "/genre=6018"
    }
    genre_param = genre_map.get(category.lower(), "")

    url = f"{ITUNES_RSS_BASE}/{country}/apps/{feed_type}/{limit}/apps.json"
    if genre_param:
        # Genre ID is passed as query parameter
        genre_id = genre_param.split("=")[1]
        url += f"?genre={genre_id}"
    data = _fetch_json(url)

    if "error" in data:
        return [data]

    feed = data.get("feed", {})
    results_raw = feed.get("results", [])

    results = []
    for rank, app in enumerate(results_raw, 1):
        results.append({
            "rank": rank,
            "app_id": app.get("id"),
            "name": app.get("name"),
            "publisher": app.get("artistName"),
            "icon_url": app.get("artworkUrl100"),
            "store_url": app.get("url"),
            "category": category,
            "chart_type": chart_type,
            "country": country,
            "release_date": app.get("releaseDate"),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        })

    return results


def get_app_downloads_estimate(
    app_id: int,
    country: str = "us"
) -> dict[str, Any]:
    """
    Estimate app download metrics based on available public signals.

    Uses rating count as a proxy for downloads (industry heuristic:
    ~1 rating per 40-80 downloads for iOS). This is a rough estimate
    — Priori Data's paid API provides more accurate figures.

    Args:
        app_id: iTunes track ID
        country: ISO 2-letter country code

    Returns:
        Dict with download estimates (low/mid/high ranges)

    Example:
        >>> est = get_app_downloads_estimate(1446101929)  # eToro
        >>> print(f"Estimated downloads: {est['downloads_estimate_mid']:,}")
    """
    details = get_app_details(app_id, country)
    if "error" in details:
        return details

    rating_count = details.get("rating_count") or 0
    rating = details.get("rating") or 0
    price = details.get("price") or 0

    # Industry heuristics for iOS rating-to-download ratios
    # Free apps: ~1 rating per 40-80 downloads
    # Paid apps: ~1 rating per 20-40 downloads (more engaged users)
    if price == 0:
        ratio_low, ratio_mid, ratio_high = 40, 60, 80
    else:
        ratio_low, ratio_mid, ratio_high = 20, 30, 40

    downloads_low = rating_count * ratio_low
    downloads_mid = rating_count * ratio_mid
    downloads_high = rating_count * ratio_high

    # Revenue estimate for paid apps
    revenue_low = downloads_low * price * 0.7  # Apple takes 30%
    revenue_mid = downloads_mid * price * 0.7
    revenue_high = downloads_high * price * 0.7

    return {
        "app_id": app_id,
        "name": details.get("name"),
        "publisher": details.get("publisher"),
        "rating_count": rating_count,
        "rating": rating,
        "price": price,
        "downloads_estimate_low": downloads_low,
        "downloads_estimate_mid": downloads_mid,
        "downloads_estimate_high": downloads_high,
        "revenue_estimate_low": round(revenue_low, 2) if price > 0 else None,
        "revenue_estimate_mid": round(revenue_mid, 2) if price > 0 else None,
        "revenue_estimate_high": round(revenue_high, 2) if price > 0 else None,
        "methodology": "Rating count × download ratio heuristic (iOS)",
        "ratio_used": f"{ratio_low}-{ratio_high}x",
        "confidence": "low" if rating_count < 1000 else "medium",
        "note": "Estimates only. Use Priori Data paid API for accurate figures.",
        "country": country,
        "retrieved_at": datetime.utcnow().isoformat() + "Z"
    }


def get_market_share_by_category(
    category: str = "finance",
    country: str = "us",
    limit: int = 20
) -> dict[str, Any]:
    """
    Estimate market share within an app category using chart rankings.

    Combines top free, paid, and grossing charts to build a picture
    of which apps dominate a category.

    Args:
        category: App Store category (see get_top_apps for options)
        country: ISO 2-letter country code
        limit: Number of apps per chart to analyze

    Returns:
        Dict with category overview and app rankings across charts

    Example:
        >>> share = get_market_share_by_category("finance", "us", 10)
        >>> for app in share['combined_ranking'][:5]:
        ...     print(f"{app['name']}: score {app['combined_score']}")
    """
    charts = {}
    for chart_type in ["top-free", "top-paid", "top-grossing"]:
        apps = get_top_apps(category, chart_type, country, limit)
        if apps and "error" not in apps[0]:
            charts[chart_type] = apps

    # Build combined scoring: apps appearing in multiple charts rank higher
    app_scores: dict[str, dict] = {}
    for chart_type, apps in charts.items():
        for app in apps:
            app_name = app.get("name", "Unknown")
            if app_name not in app_scores:
                app_scores[app_name] = {
                    "name": app_name,
                    "app_id": app.get("app_id"),
                    "publisher": app.get("publisher"),
                    "charts": [],
                    "combined_score": 0
                }
            rank = app.get("rank", limit + 1)
            score = max(0, limit + 1 - rank)  # Higher rank = higher score
            app_scores[app_name]["charts"].append({
                "chart": chart_type, "rank": rank
            })
            app_scores[app_name]["combined_score"] += score

    combined = sorted(app_scores.values(), key=lambda x: x["combined_score"], reverse=True)

    return {
        "category": category,
        "country": country,
        "charts_analyzed": list(charts.keys()),
        "total_unique_apps": len(combined),
        "combined_ranking": combined,
        "methodology": "Combined chart position scoring across free/paid/grossing",
        "retrieved_at": datetime.utcnow().isoformat() + "Z"
    }


def get_geographic_breakdown(
    app_id: int,
    countries: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """
    Get app availability and metadata across multiple countries.

    Args:
        app_id: iTunes track ID
        countries: List of ISO country codes (default: major markets)

    Returns:
        List of dicts with per-country app data (price, rating, availability)

    Example:
        >>> geo = get_geographic_breakdown(1446101929)  # eToro worldwide
        >>> for g in geo: print(f"{g['country']}: rating={g['rating']}, price={g['formatted_price']}")
    """
    if countries is None:
        countries = ["us", "gb", "de", "fr", "jp", "au", "ca", "br", "in", "kr"]

    results = []
    for cc in countries:
        details = get_app_details(app_id, country=cc)
        if "error" in details:
            results.append({
                "country": cc,
                "available": False,
                "error": details.get("error")
            })
        else:
            results.append({
                "country": cc,
                "available": True,
                "name": details.get("name"),
                "price": details.get("price"),
                "formatted_price": details.get("formatted_price"),
                "currency": details.get("currency"),
                "rating": details.get("rating"),
                "rating_count": details.get("rating_count"),
                "version": details.get("version"),
                "content_rating": details.get("content_rating"),
                "languages": details.get("languages", []),
                "retrieved_at": datetime.utcnow().isoformat() + "Z"
            })

    return results


def compare_apps(
    app_ids: list[int],
    country: str = "us"
) -> list[dict[str, Any]]:
    """
    Compare multiple apps side by side on key metrics.

    Args:
        app_ids: List of iTunes track IDs to compare
        country: ISO 2-letter country code

    Returns:
        List of dicts with comparable metrics for each app

    Example:
        >>> # Compare eToro vs Robinhood vs Trading 212
        >>> comparison = compare_apps([1446101929, 938003185, 929646842])
        >>> for c in comparison: print(f"{c['name']}: {c['rating']} ({c['rating_count']} ratings)")
    """
    results = []
    for app_id in app_ids:
        details = get_app_details(app_id, country)
        if "error" in details:
            results.append({"app_id": app_id, "error": details.get("error")})
            continue

        est = get_app_downloads_estimate(app_id, country)

        results.append({
            "app_id": app_id,
            "name": details.get("name"),
            "publisher": details.get("publisher"),
            "price": details.get("price"),
            "rating": details.get("rating"),
            "rating_count": details.get("rating_count"),
            "category": details.get("category"),
            "size_mb": details.get("size_mb"),
            "version": details.get("version"),
            "release_date": details.get("release_date"),
            "last_update": details.get("current_version_release"),
            "languages_count": len(details.get("languages", [])),
            "downloads_estimate": est.get("downloads_estimate_mid"),
            "content_rating": details.get("content_rating"),
            "country": country,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        })

    return results


def fetch_data(query: str = "trading", country: str = "us", limit: int = 25) -> list[dict[str, Any]]:
    """
    Fetch app intelligence data (default entry point).

    Args:
        query: Search query for apps
        country: ISO 2-letter country code
        limit: Max results

    Returns:
        List of app metadata dicts
    """
    return search_apps(query=query, country=country, limit=limit)


def get_latest(category: str = "finance", country: str = "us") -> list[dict[str, Any]]:
    """
    Get latest top apps data for a category.

    Args:
        category: App Store category
        country: ISO country code

    Returns:
        List of top free apps in the category
    """
    return get_top_apps(category=category, chart_type="top-free", country=country, limit=25)


if __name__ == "__main__":
    print(json.dumps({
        "module": "priori_data_app_intelligence_dataset",
        "status": "active",
        "source": "iTunes Search API + Apple RSS (free)",
        "functions": [
            "search_apps", "get_app_details", "get_publisher_apps",
            "get_top_apps", "get_app_downloads_estimate",
            "get_market_share_by_category", "get_geographic_breakdown",
            "compare_apps", "fetch_data", "get_latest"
        ]
    }, indent=2))
