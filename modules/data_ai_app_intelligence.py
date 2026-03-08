"""
Data.ai (formerly App Annie) App Intelligence — App market data and analytics.

Market data on app downloads, usage, revenue across global app stores.
Supports both data.ai API (with token) and free web scraping fallback
from public app store pages and data.ai public rankings.

Source: https://www.data.ai/en/platform/api
Update frequency: Daily
Category: Web Traffic & App Data
Free tier: 200 API calls/month (with key); public scraping fallback (no key)
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


DATAAI_API_BASE = "https://api.data.ai/v1"
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
GPLAY_SUGGEST = "https://market.android.com/suggest"

# Common headers for web requests
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


# ---------------------------------------------------------------------------
#  Data.ai API functions (requires access_token)
# ---------------------------------------------------------------------------

def dataai_app_details(
    app_id: str,
    platform: str = "ios",
    access_token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get app details from data.ai API.

    Args:
        app_id: App store ID (numeric for iOS, package name for Android)
        platform: 'ios' or 'android'
        access_token: data.ai API access token

    Returns:
        dict with app metadata or error

    Example:
        >>> details = dataai_app_details("544007664", "ios", token)
        >>> print(details.get("title"))
    """
    if not access_token:
        return {"error": "data.ai API requires access_token. Get free key at https://www.data.ai/en/platform/api",
                "hint": "Use itunes_app_details() or gplay_app_details() for free lookups"}

    url = f"{DATAAI_API_BASE}/apps/{platform}/app/{app_id}/details?access_token={access_token}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return {
                "source": "data.ai",
                "platform": platform,
                "app_id": app_id,
                "data": data,
                "fetched_at": datetime.utcnow().isoformat(),
            }
    except urllib.error.HTTPError as e:
        return {"error": f"data.ai API HTTP {e.code}", "message": str(e.reason)}
    except Exception as e:
        return {"error": str(e)}


def dataai_top_apps(
    platform: str = "ios",
    category: str = "overall",
    country: str = "us",
    access_token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get top app rankings from data.ai API.

    Args:
        platform: 'ios' or 'android'
        category: App category (e.g., 'overall', 'games', 'finance')
        country: ISO country code
        access_token: data.ai API access token

    Returns:
        dict with top apps ranking or error
    """
    if not access_token:
        return {"error": "data.ai API requires access_token",
                "hint": "Use itunes_top_apps() for free iOS rankings"}

    params = urllib.parse.urlencode({
        "category": category,
        "country": country,
        "access_token": access_token,
    })
    url = f"{DATAAI_API_BASE}/apps/{platform}/ranking?{params}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return {
                "source": "data.ai",
                "platform": platform,
                "category": category,
                "country": country,
                "rankings": data,
                "fetched_at": datetime.utcnow().isoformat(),
            }
    except urllib.error.HTTPError as e:
        return {"error": f"data.ai API HTTP {e.code}", "message": str(e.reason)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
#  Free-tier: Apple iTunes Search/Lookup API (no key required)
# ---------------------------------------------------------------------------

def itunes_app_details(app_id: str, country: str = "us") -> dict[str, Any]:
    """
    Get iOS app details from Apple iTunes Lookup API (free, no key).

    Args:
        app_id: Numeric App Store ID (e.g., '544007664' for YouTube)
        country: ISO country code for store region

    Returns:
        dict with app metadata including rating, price, genre, etc.

    Example:
        >>> app = itunes_app_details("544007664")
        >>> print(app["title"], app["rating"])
    """
    params = urllib.parse.urlencode({"id": app_id, "country": country})
    url = f"{ITUNES_LOOKUP}?{params}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("resultCount", 0) == 0:
            return {"error": f"No iOS app found with ID {app_id}"}

        r = data["results"][0]
        return {
            "source": "itunes_lookup",
            "platform": "ios",
            "app_id": str(r.get("trackId", app_id)),
            "bundle_id": r.get("bundleId"),
            "title": r.get("trackName"),
            "publisher": r.get("artistName"),
            "publisher_id": r.get("artistId"),
            "price": r.get("price", 0),
            "currency": r.get("currency"),
            "rating": r.get("averageUserRating"),
            "rating_count": r.get("userRatingCount"),
            "rating_current_version": r.get("averageUserRatingForCurrentVersion"),
            "content_rating": r.get("contentAdvisoryRating"),
            "category": r.get("primaryGenreName"),
            "categories": r.get("genres", []),
            "description": (r.get("description") or "")[:500],
            "release_date": r.get("releaseDate"),
            "current_version": r.get("version"),
            "last_update": r.get("currentVersionReleaseDate"),
            "min_os": r.get("minimumOsVersion"),
            "size_bytes": r.get("fileSizeBytes"),
            "languages": r.get("languageCodesISO2A", []),
            "screenshot_urls": r.get("screenshotUrls", [])[:3],
            "icon_url": r.get("artworkUrl512"),
            "store_url": r.get("trackViewUrl"),
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "app_id": app_id}


def itunes_search_apps(
    query: str,
    country: str = "us",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search iOS apps via iTunes Search API (free, no key).

    Args:
        query: Search term (e.g., 'trading', 'fitness tracker')
        country: ISO country code
        limit: Max results (1-200)

    Returns:
        list of dicts with app metadata

    Example:
        >>> apps = itunes_search_apps("stock trading", limit=5)
        >>> for a in apps: print(a["title"], a["rating"])
    """
    params = urllib.parse.urlencode({
        "term": query,
        "country": country,
        "media": "software",
        "limit": min(limit, 200),
    })
    url = f"https://itunes.apple.com/search?{params}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for r in data.get("results", []):
            results.append({
                "app_id": str(r.get("trackId")),
                "bundle_id": r.get("bundleId"),
                "title": r.get("trackName"),
                "publisher": r.get("artistName"),
                "price": r.get("price", 0),
                "rating": r.get("averageUserRating"),
                "rating_count": r.get("userRatingCount"),
                "category": r.get("primaryGenreName"),
                "store_url": r.get("trackViewUrl"),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def itunes_top_apps(
    genre_id: int = 36,
    country: str = "us",
    limit: int = 20,
    feed_type: str = "topfreeapplications",
) -> list[dict[str, Any]]:
    """
    Get top iOS app rankings via Apple RSS feed (free, no key).

    Args:
        genre_id: iTunes genre ID (36=Finance, 6014=Games, 6002=Utilities, 0=All)
        country: ISO country code
        limit: Number of apps (max 200)
        feed_type: 'topfreeapplications', 'toppaidapplications', 'topgrossingapplications'

    Returns:
        list of dicts with ranked app info

    Example:
        >>> top = itunes_top_apps(genre_id=36, limit=10)  # Top Finance apps
        >>> for i, app in enumerate(top, 1): print(f"{i}. {app['title']}")
    """
    url = (
        f"https://itunes.apple.com/{country}/rss/{feed_type}/"
        f"limit={min(limit, 200)}/genre={genre_id}/json"
    )
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        entries = data.get("feed", {}).get("entry", [])
        results = []
        for i, entry in enumerate(entries, 1):
            name_obj = entry.get("im:name", {})
            title = name_obj.get("label", "") if isinstance(name_obj, dict) else str(name_obj)
            artist_obj = entry.get("im:artist", {})
            artist = artist_obj.get("label", "") if isinstance(artist_obj, dict) else str(artist_obj)

            # Extract app ID from the id link
            id_obj = entry.get("id", {})
            app_id = ""
            if isinstance(id_obj, dict):
                attrs = id_obj.get("attributes", {})
                app_id = attrs.get("im:id", "")

            price_obj = entry.get("im:price", {})
            price_attrs = price_obj.get("attributes", {}) if isinstance(price_obj, dict) else {}

            cat_obj = entry.get("category", {})
            cat_attrs = cat_obj.get("attributes", {}) if isinstance(cat_obj, dict) else {}

            results.append({
                "rank": i,
                "app_id": app_id,
                "title": title,
                "publisher": artist,
                "price": price_attrs.get("amount", "0"),
                "currency": price_attrs.get("currency", "USD"),
                "category": cat_attrs.get("label", ""),
                "summary": (entry.get("summary", {}).get("label", "") if isinstance(entry.get("summary"), dict) else "")[:200],
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
#  Free-tier: Google Play basic app info (no key required)
# ---------------------------------------------------------------------------

def gplay_app_details(package_id: str, lang: str = "en", country: str = "us") -> dict[str, Any]:
    """
    Get Android app details by scraping Google Play Store page (free, no key).

    Args:
        package_id: Android package name (e.g., 'com.google.android.youtube')
        lang: Language code
        country: Country code

    Returns:
        dict with app metadata extracted from store page

    Example:
        >>> app = gplay_app_details("com.google.android.youtube")
        >>> print(app["title"], app.get("rating"))
    """
    url = f"https://play.google.com/store/apps/details?id={package_id}&hl={lang}&gl={country}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _HEADERS["User-Agent"],
            "Accept": "text/html",
            "Accept-Language": f"{lang}",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        result: dict[str, Any] = {
            "source": "google_play_scrape",
            "platform": "android",
            "package_id": package_id,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        # Title from <title> tag
        title_m = re.search(r"<title>([^<]+?)(?:\s*-\s*Apps on Google Play)?</title>", html)
        if title_m:
            result["title"] = title_m.group(1).strip()

        # Rating
        rating_m = re.search(r'"(\d+\.\d+)" stars', html)
        if not rating_m:
            rating_m = re.search(r'aria-label="Rated (\d+\.?\d*)', html)
        if rating_m:
            result["rating"] = float(rating_m.group(1))

        # Downloads / installs
        dl_m = re.search(r'([\d,]+\+?)\s*downloads', html, re.IGNORECASE)
        if not dl_m:
            dl_m = re.search(r'"([\d,BMK]+\+?)"[^>]*>.*?download', html, re.IGNORECASE)
        if dl_m:
            result["downloads"] = dl_m.group(1)

        # Content rating
        cr_m = re.search(r'content-rating[^>]*>([^<]+)<', html, re.IGNORECASE)
        if cr_m:
            result["content_rating"] = cr_m.group(1).strip()

        # Description snippet
        desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]{10,500})"', html)
        if desc_m:
            result["description"] = desc_m.group(1)[:500]

        # Developer / publisher
        dev_m = re.search(r'"author"[^}]*"name"\s*:\s*"([^"]+)"', html)
        if dev_m:
            result["publisher"] = dev_m.group(1)

        # Updated date from structured data
        upd_m = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html)
        if upd_m:
            result["last_update"] = upd_m.group(1)

        result["store_url"] = url
        return result
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "package_id": package_id, "message": str(e.reason)}
    except Exception as e:
        return {"error": str(e), "package_id": package_id}


# ---------------------------------------------------------------------------
#  Cross-platform helpers
# ---------------------------------------------------------------------------

def compare_apps(
    ios_id: Optional[str] = None,
    android_id: Optional[str] = None,
    country: str = "us",
) -> dict[str, Any]:
    """
    Compare an app across iOS and Android stores (free, no key).

    Args:
        ios_id: iOS App Store numeric ID
        android_id: Android package name
        country: ISO country code

    Returns:
        dict with side-by-side comparison

    Example:
        >>> cmp = compare_apps(ios_id="544007664", android_id="com.google.android.youtube")
        >>> print(cmp["ios"]["title"], "vs", cmp["android"]["title"])
    """
    result: dict[str, Any] = {"fetched_at": datetime.utcnow().isoformat()}

    if ios_id:
        result["ios"] = itunes_app_details(ios_id, country)
    if android_id:
        result["android"] = gplay_app_details(android_id, country=country)

    # Cross-platform summary
    ios_data = result.get("ios", {})
    android_data = result.get("android", {})
    if ios_data.get("title") and android_data.get("title"):
        result["comparison"] = {
            "ios_rating": ios_data.get("rating"),
            "android_rating": android_data.get("rating"),
            "ios_rating_count": ios_data.get("rating_count"),
            "android_downloads": android_data.get("downloads"),
            "ios_price": ios_data.get("price"),
        }
    return result


def app_market_overview(
    category: str = "Finance",
    country: str = "us",
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get app market overview for a category — top free + paid + grossing (iOS).

    Args:
        category: Category name to map to genre_id
        country: ISO country code
        limit: Apps per list

    Returns:
        dict with top_free, top_paid, top_grossing lists

    Example:
        >>> overview = app_market_overview("Finance", limit=5)
        >>> for app in overview["top_free"]: print(app["title"])
    """
    genre_map = {
        "finance": 6015, "games": 6014, "utilities": 6002,
        "social": 6005, "entertainment": 6016, "productivity": 6007,
        "health": 6013, "education": 6017, "business": 6000,
        "shopping": 6024, "food": 6023, "travel": 6003,
        "music": 6011, "photo": 6008, "news": 6009,
        "sports": 6004, "weather": 6001, "navigation": 6010,
        "medical": 6020, "lifestyle": 6012, "all": 0,
    }
    genre_id = genre_map.get(category.lower(), 0)

    return {
        "category": category,
        "genre_id": genre_id,
        "country": country,
        "top_free": itunes_top_apps(genre_id, country, limit, "topfreeapplications"),
        "top_paid": itunes_top_apps(genre_id, country, limit, "toppaidapplications"),
        "top_grossing": itunes_top_apps(genre_id, country, limit, "topgrossingapplications"),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def publisher_apps(publisher_id: int, country: str = "us", limit: int = 20) -> list[dict[str, Any]]:
    """
    Get all apps by a publisher on iOS (free, no key).

    Args:
        publisher_id: iTunes artist/publisher numeric ID
        country: ISO country code
        limit: Max results

    Returns:
        list of dicts with the publisher's apps

    Example:
        >>> apps = publisher_apps(544007664)  # Google LLC publisher ID
    """
    params = urllib.parse.urlencode({
        "id": publisher_id,
        "entity": "software",
        "country": country,
        "limit": min(limit, 200),
    })
    url = f"{ITUNES_LOOKUP}?{params}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for r in data.get("results", []):
            if r.get("wrapperType") == "artist":
                continue
            results.append({
                "app_id": str(r.get("trackId", "")),
                "title": r.get("trackName"),
                "price": r.get("price", 0),
                "rating": r.get("averageUserRating"),
                "rating_count": r.get("userRatingCount"),
                "category": r.get("primaryGenreName"),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
#  Module info
# ---------------------------------------------------------------------------

MODULE_INFO = {
    "name": "data_ai_app_intelligence",
    "version": "1.0.0",
    "description": "App market intelligence — data.ai API + free Apple/Google store lookups",
    "source": "https://www.data.ai/en/platform/api",
    "category": "Web Traffic & App Data",
    "update_frequency": "daily",
    "free_tier": True,
    "functions": [
        "dataai_app_details",
        "dataai_top_apps",
        "itunes_app_details",
        "itunes_search_apps",
        "itunes_top_apps",
        "gplay_app_details",
        "compare_apps",
        "app_market_overview",
        "publisher_apps",
    ],
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
