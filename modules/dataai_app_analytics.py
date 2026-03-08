"""
Data.ai App Analytics — Mobile app market intelligence and analytics.

App store data for iOS and Android including downloads, ratings, reviews,
category rankings, and competitive analysis for quantitative research.

Note: data.ai (formerly App Annie) was acquired by Sensor Tower in 2024
and no longer offers a free public API. This module uses FREE alternatives:
  - Apple iTunes Search API (no key required)
  - Google Play Store public pages (HTML parsing)
  - RSS feeds for top charts

Source: https://www.data.ai/en/platform/api (reference)
Update frequency: Real-time (iTunes API), Daily (charts)
Category: Web Traffic & App Data
Free tier: Unlimited (uses free public APIs)
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


ITUNES_API = "https://itunes.apple.com"
ITUNES_RSS = "https://rss.applemarketingtools.com/api/v2"
PLAY_STORE = "https://play.google.com/store/apps"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _fetch(url: str, timeout: int = 15) -> bytes:
    """Internal helper to fetch URL with headers."""
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Internal helper to fetch and parse JSON."""
    return json.loads(_fetch(url, timeout).decode("utf-8"))


# ---------------------------------------------------------------------------
# iOS App Analytics (iTunes Search API — free, no key)
# ---------------------------------------------------------------------------

def search_ios_apps(
    query: str,
    country: str = "us",
    limit: int = 25,
    genre: Optional[str] = None
) -> dict[str, Any]:
    """
    Search iOS apps via the iTunes Search API (free, no key required).

    Args:
        query: Search term (e.g., 'trading', 'fitness tracker')
        country: ISO 3166-1 alpha-2 country code
        limit: Max results (1-200)
        genre: Optional genre ID filter (e.g., '6015' for Finance)

    Returns:
        dict with 'results' list of app dicts and metadata

    Example:
        >>> apps = search_ios_apps('stock trading', limit=5)
        >>> for a in apps['results']:
        ...     print(a['name'], a['rating'], a['rating_count'])
    """
    params = {
        "term": query,
        "country": country,
        "media": "software",
        "limit": min(int(limit), 200),
    }
    if genre:
        params["genreId"] = genre

    url = f"{ITUNES_API}/search?{urllib.parse.urlencode(params)}"

    try:
        data = _fetch_json(url)
        results = []
        for app in data.get("results", []):
            results.append({
                "app_id": app.get("trackId"),
                "bundle_id": app.get("bundleId"),
                "name": app.get("trackName"),
                "publisher": app.get("artistName"),
                "price": app.get("price", 0),
                "currency": app.get("currency"),
                "rating": app.get("averageUserRating"),
                "rating_count": app.get("userRatingCount"),
                "current_version_rating": app.get("averageUserRatingForCurrentVersion"),
                "genres": app.get("genres", []),
                "primary_genre": app.get("primaryGenreName"),
                "content_rating": app.get("contentAdvisoryRating"),
                "size_bytes": app.get("fileSizeBytes"),
                "min_os": app.get("minimumOsVersion"),
                "release_date": app.get("releaseDate"),
                "updated_date": app.get("currentVersionReleaseDate"),
                "version": app.get("version"),
                "description": (app.get("description") or "")[:300],
                "url": app.get("trackViewUrl"),
                "icon": app.get("artworkUrl512"),
            })

        return {
            "query": query,
            "country": country,
            "total": data.get("resultCount", 0),
            "results": results,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "query": query}


def get_ios_app_details(app_id: int, country: str = "us") -> dict[str, Any]:
    """
    Get detailed info for a single iOS app by its App Store ID.

    Args:
        app_id: Numeric App Store ID (e.g., 1451685025 for eToro)
        country: ISO country code

    Returns:
        dict with full app metadata

    Example:
        >>> details = get_ios_app_details(1451685025)
        >>> print(details['name'], details['rating'])
    """
    url = f"{ITUNES_API}/lookup?id={app_id}&country={country}"

    try:
        data = _fetch_json(url)
        results = data.get("results", [])
        if not results:
            return {"error": f"App {app_id} not found", "app_id": app_id}

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
            "rating": app.get("averageUserRating"),
            "rating_count": app.get("userRatingCount"),
            "current_version_rating": app.get("averageUserRatingForCurrentVersion"),
            "genres": app.get("genres", []),
            "genre_ids": app.get("genreIds", []),
            "primary_genre": app.get("primaryGenreName"),
            "content_rating": app.get("contentAdvisoryRating"),
            "size_bytes": app.get("fileSizeBytes"),
            "size_mb": round(int(app.get("fileSizeBytes", 0)) / 1_048_576, 1),
            "min_os": app.get("minimumOsVersion"),
            "supported_devices": app.get("supportedDevices", [])[:10],
            "languages": app.get("languageCodesISO2A", []),
            "release_date": app.get("releaseDate"),
            "updated_date": app.get("currentVersionReleaseDate"),
            "version": app.get("version"),
            "release_notes": (app.get("releaseNotes") or "")[:500],
            "description": (app.get("description") or "")[:500],
            "url": app.get("trackViewUrl"),
            "icon": app.get("artworkUrl512"),
            "screenshots": app.get("screenshotUrls", [])[:5],
            "in_app_purchases": bool(app.get("isVppDeviceBasedLicensingEnabled")),
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "app_id": app_id}


def get_ios_top_apps(
    genre: str = "6015",
    country: str = "us",
    limit: int = 25,
    chart: str = "top-free"
) -> dict[str, Any]:
    """
    Get top iOS app charts via Apple RSS feed (free, no key).

    Args:
        genre: Genre ID ('6015'=Finance, '6002'=Utilities, '6014'=Games,
               '6017'=Health, '6018'=Book, '6016'=Entertainment)
        country: ISO country code
        limit: Max results (1-100)
        chart: Chart type ('top-free', 'top-paid', 'top-grossing')

    Returns:
        dict with ranked app list

    Example:
        >>> top = get_ios_top_apps(genre='6015', limit=10)
        >>> for app in top['apps']:
        ...     print(f"#{app['rank']} {app['name']}")
    """
    limit = min(int(limit), 100)
    url = f"{ITUNES_RSS}/{country}/apps/{chart}/{limit}/apps.json"
    if genre:
        url += f"?genre={genre}"

    try:
        data = _fetch_json(url)
        feed = data.get("feed", {})
        apps = []
        for i, entry in enumerate(feed.get("results", []), 1):
            apps.append({
                "rank": i,
                "app_id": entry.get("id"),
                "name": entry.get("name"),
                "publisher": entry.get("artistName"),
                "url": entry.get("url"),
                "icon": entry.get("artworkUrl100"),
                "genres": entry.get("genres", []),
            })

        return {
            "chart": chart,
            "genre": genre,
            "country": country,
            "total": len(apps),
            "apps": apps,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "chart": chart}


# ---------------------------------------------------------------------------
# Android App Analytics (Google Play public data)
# ---------------------------------------------------------------------------

def get_android_app_details(package_id: str, lang: str = "en") -> dict[str, Any]:
    """
    Get Android app details by scraping the Google Play Store page.

    Args:
        package_id: Android package ID (e.g., 'com.etoro.openbook')
        lang: Language code for the page

    Returns:
        dict with app metadata parsed from the store page

    Example:
        >>> app = get_android_app_details('com.etoro.openbook')
        >>> print(app['name'], app.get('rating'))
    """
    url = f"{PLAY_STORE}/details?id={urllib.parse.quote(package_id)}&hl={lang}"

    try:
        html = _fetch(url).decode("utf-8", errors="replace")

        def _extract(pattern: str, html: str, default: Any = None) -> Any:
            m = re.search(pattern, html)
            return m.group(1) if m else default

        name = _extract(r'<h1[^>]*><span>([^<]+)</span>', html)
        publisher = _extract(r'<a[^>]*href="/store/apps/dev[^"]*"[^>]*><span>([^<]+)</span>', html)
        rating_str = _extract(r'aria-label="Rated (\d+\.?\d*) stars', html)
        rating = float(rating_str) if rating_str else None

        # Extract installs from meta or text
        installs = _extract(r'"(\d[\d,]+\+?) downloads', html)
        if not installs:
            installs = _extract(r'>(\d[\d,]+\+?)\s*</div>', html)

        content_rating = _extract(r'Rated for ([^<"]+)', html)
        updated = _extract(r'"Updated on","(\w+ \d+, \d{4})"', html)
        version = _extract(r'"Current Version","([^"]+)"', html)

        return {
            "package_id": package_id,
            "name": name,
            "publisher": publisher,
            "rating": rating,
            "installs": installs,
            "content_rating": content_rating,
            "updated": updated,
            "version": version,
            "url": url,
            "platform": "android",
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"App not found: {package_id}", "package_id": package_id}
        return {"error": f"HTTP {e.code}: {str(e)}", "package_id": package_id}
    except Exception as e:
        return {"error": str(e), "package_id": package_id}


# ---------------------------------------------------------------------------
# Cross-Platform Competitive Analysis
# ---------------------------------------------------------------------------

def compare_apps(
    app_ids: list[int],
    country: str = "us"
) -> dict[str, Any]:
    """
    Compare multiple iOS apps side-by-side.

    Args:
        app_ids: List of App Store IDs to compare
        country: ISO country code

    Returns:
        dict with comparison table and rankings

    Example:
        >>> cmp = compare_apps([1451685025, 1513685928, 1374872250])
        >>> for a in cmp['apps']:
        ...     print(a['name'], a['rating'], a['rating_count'])
    """
    if not app_ids:
        return {"error": "Provide at least one app_id"}

    ids_str = ",".join(str(i) for i in app_ids[:20])
    url = f"{ITUNES_API}/lookup?id={ids_str}&country={country}"

    try:
        data = _fetch_json(url)
        apps = []
        for app in data.get("results", []):
            apps.append({
                "app_id": app.get("trackId"),
                "name": app.get("trackName"),
                "publisher": app.get("artistName"),
                "price": app.get("price", 0),
                "rating": app.get("averageUserRating"),
                "rating_count": app.get("userRatingCount"),
                "primary_genre": app.get("primaryGenreName"),
                "size_mb": round(int(app.get("fileSizeBytes", 0)) / 1_048_576, 1),
                "version": app.get("version"),
                "updated_date": app.get("currentVersionReleaseDate"),
            })

        # Sort by rating_count descending
        apps.sort(key=lambda x: x.get("rating_count") or 0, reverse=True)

        return {
            "country": country,
            "total": len(apps),
            "apps": apps,
            "best_rated": max(apps, key=lambda x: x.get("rating") or 0)["name"] if apps else None,
            "most_reviewed": apps[0]["name"] if apps else None,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_publisher_apps(
    publisher_id: int,
    country: str = "us",
    limit: int = 50
) -> dict[str, Any]:
    """
    Get all apps from a specific iOS publisher/developer.

    Args:
        publisher_id: iTunes artist/developer ID
        country: ISO country code
        limit: Max results (1-200)

    Returns:
        dict with publisher's app portfolio

    Example:
        >>> apps = get_publisher_apps(363015658)  # eToro
        >>> for a in apps['apps']:
        ...     print(a['name'], a['rating'])
    """
    url = (
        f"{ITUNES_API}/lookup?id={publisher_id}&entity=software"
        f"&country={country}&limit={min(int(limit), 200)}"
    )

    try:
        data = _fetch_json(url)
        results = data.get("results", [])

        publisher_info = None
        apps = []
        for item in results:
            if item.get("wrapperType") == "artist":
                publisher_info = {
                    "publisher_id": item.get("artistId"),
                    "name": item.get("artistName"),
                    "url": item.get("artistLinkUrl"),
                }
            elif item.get("wrapperType") == "software":
                apps.append({
                    "app_id": item.get("trackId"),
                    "name": item.get("trackName"),
                    "price": item.get("price", 0),
                    "rating": item.get("averageUserRating"),
                    "rating_count": item.get("userRatingCount"),
                    "primary_genre": item.get("primaryGenreName"),
                    "bundle_id": item.get("bundleId"),
                    "version": item.get("version"),
                    "updated_date": item.get("currentVersionReleaseDate"),
                })

        return {
            "publisher": publisher_info,
            "total_apps": len(apps),
            "apps": apps,
            "country": country,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "publisher_id": publisher_id}


def ios_genre_ids() -> dict[str, str]:
    """
    Return mapping of common iOS App Store genre IDs.

    Returns:
        dict mapping genre name to genre ID

    Example:
        >>> genres = ios_genre_ids()
        >>> print(genres['Finance'])  # '6015'
    """
    return {
        "Books": "6018",
        "Business": "6000",
        "Education": "6017",
        "Entertainment": "6016",
        "Finance": "6015",
        "Food & Drink": "6023",
        "Games": "6014",
        "Health & Fitness": "6013",
        "Lifestyle": "6012",
        "Medical": "6020",
        "Music": "6011",
        "Navigation": "6010",
        "News": "6009",
        "Photo & Video": "6008",
        "Productivity": "6007",
        "Reference": "6006",
        "Shopping": "6024",
        "Social Networking": "6005",
        "Sports": "6004",
        "Travel": "6003",
        "Utilities": "6002",
        "Weather": "6001",
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> dict[str, Any]:
    """Run a quick demo using the free iTunes API (no key needed)."""
    result = search_ios_apps("stock trading", limit=3)
    return {
        "demo": "search_ios_apps('stock trading', limit=3)",
        "status": "ok" if "results" in result else "error",
        "sample": result,
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, default=str))
