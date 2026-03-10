"""
MobileAction Intelligence API — App intelligence with ad spend estimates,
user demographics, and performance metrics across app stores.

Since MobileAction's API requires paid access, this module provides app
intelligence by scraping publicly available data from the iTunes/Google Play
APIs and estimating metrics. Functions return structured dicts/lists suitable
for quantitative analysis of mobile app ecosystems and digital ad trends.

Source: https://www.mobileaction.co/ (reference), Apple/Google public APIs (data)
Update frequency: Daily (app store data refreshes daily)
Category: Web Traffic & App Data
Free tier: Yes — uses public app store endpoints, no API key required
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


# Public endpoints (no key required)
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
ITUNES_SEARCH = "https://itunes.apple.com/search"
GPLAY_SUGGEST = "https://market.android.com/suggest"

# Category mapping for ad-spend estimation heuristics
CATEGORY_AD_MULTIPLIERS = {
    "Games": 1.8, "Entertainment": 1.5, "Social Networking": 2.0,
    "Shopping": 1.7, "Finance": 1.4, "Health & Fitness": 1.3,
    "Education": 0.9, "Productivity": 1.0, "Utilities": 0.8,
    "Travel": 1.6, "Food & Drink": 1.5, "Music": 1.2,
    "News": 1.1, "Sports": 1.4, "Photo & Video": 1.3,
    "Business": 1.1, "Weather": 0.7, "Reference": 0.6,
    "Navigation": 1.0, "Lifestyle": 1.2,
}

# Demographics heuristics by genre
GENRE_DEMOGRAPHICS = {
    "Games": {"18-24": 0.35, "25-34": 0.30, "35-44": 0.18, "45+": 0.17, "male_pct": 0.58},
    "Social Networking": {"18-24": 0.40, "25-34": 0.28, "35-44": 0.18, "45+": 0.14, "male_pct": 0.45},
    "Finance": {"18-24": 0.12, "25-34": 0.32, "35-44": 0.30, "45+": 0.26, "male_pct": 0.62},
    "Shopping": {"18-24": 0.22, "25-34": 0.30, "35-44": 0.25, "45+": 0.23, "male_pct": 0.38},
    "Health & Fitness": {"18-24": 0.20, "25-34": 0.35, "35-44": 0.25, "45+": 0.20, "male_pct": 0.48},
    "Education": {"18-24": 0.30, "25-34": 0.28, "35-44": 0.24, "45+": 0.18, "male_pct": 0.50},
    "Entertainment": {"18-24": 0.32, "25-34": 0.28, "35-44": 0.22, "45+": 0.18, "male_pct": 0.52},
    "Productivity": {"18-24": 0.15, "25-34": 0.35, "35-44": 0.28, "45+": 0.22, "male_pct": 0.55},
}

DEFAULT_DEMOGRAPHICS = {"18-24": 0.25, "25-34": 0.30, "35-44": 0.23, "45+": 0.22, "male_pct": 0.50}


def _fetch_json(url: str, timeout: int = 15) -> dict:
    """Internal helper to fetch JSON from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "QuantClaw-Data/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_ios_app(app_id: str, country: str = "us") -> dict[str, Any]:
    """
    Look up an iOS app by its Apple ID or bundle ID.

    Args:
        app_id: Numeric Apple ID (e.g. '389801252') or bundle ID (e.g. 'com.instagram.Instagram')
        country: Two-letter country code for store region

    Returns:
        dict with app metadata: name, publisher, category, price, rating,
        rating_count, current_version, release_date, content_rating, etc.

    Example:
        >>> data = lookup_ios_app('389801252')  # Instagram
        >>> print(data['name'], data['rating'])
    """
    try:
        params = {"country": country}
        if app_id.isdigit():
            params["id"] = app_id
        else:
            params["bundleId"] = app_id

        url = f"{ITUNES_LOOKUP}?{urllib.parse.urlencode(params)}"
        raw = _fetch_json(url)

        if raw.get("resultCount", 0) == 0:
            return {"error": f"App not found: {app_id}", "source": "itunes_lookup"}

        r = raw["results"][0]
        return {
            "app_id": str(r.get("trackId", "")),
            "bundle_id": r.get("bundleId", ""),
            "name": r.get("trackName", ""),
            "publisher": r.get("artistName", ""),
            "publisher_id": str(r.get("artistId", "")),
            "category": r.get("primaryGenreName", ""),
            "genres": r.get("genres", []),
            "price_usd": r.get("price", 0),
            "currency": r.get("currency", "USD"),
            "rating": r.get("averageUserRating"),
            "rating_count": r.get("userRatingCount"),
            "current_version": r.get("version", ""),
            "min_os": r.get("minimumOsVersion", ""),
            "size_bytes": r.get("fileSizeBytes"),
            "release_date": r.get("releaseDate", ""),
            "last_updated": r.get("currentVersionReleaseDate", ""),
            "content_rating": r.get("contentAdvisoryRating", ""),
            "description_snippet": (r.get("description", ""))[:300],
            "icon_url": r.get("artworkUrl512", ""),
            "store_url": r.get("trackViewUrl", ""),
            "country": country,
            "fetched_at": datetime.utcnow().isoformat(),
            "source": "itunes_lookup",
        }
    except Exception as e:
        return {"error": str(e), "source": "itunes_lookup", "app_id": app_id}


def search_ios_apps(query: str, country: str = "us", limit: int = 10) -> list[dict]:
    """
    Search the iOS App Store for apps matching a query.

    Args:
        query: Search term (e.g. 'trading', 'fitness tracker')
        country: Two-letter country code
        limit: Max results (1-50)

    Returns:
        List of dicts with app_id, name, publisher, category, rating, price_usd

    Example:
        >>> results = search_ios_apps('stock trading', limit=5)
        >>> for app in results: print(app['name'], app['rating'])
    """
    try:
        limit = max(1, min(50, limit))
        params = {
            "term": query,
            "country": country,
            "media": "software",
            "limit": str(limit),
        }
        url = f"{ITUNES_SEARCH}?{urllib.parse.urlencode(params)}"
        raw = _fetch_json(url)

        results = []
        for r in raw.get("results", []):
            results.append({
                "app_id": str(r.get("trackId", "")),
                "bundle_id": r.get("bundleId", ""),
                "name": r.get("trackName", ""),
                "publisher": r.get("artistName", ""),
                "category": r.get("primaryGenreName", ""),
                "price_usd": r.get("price", 0),
                "rating": r.get("averageUserRating"),
                "rating_count": r.get("userRatingCount"),
                "store_url": r.get("trackViewUrl", ""),
            })
        return results
    except Exception as e:
        return [{"error": str(e), "source": "itunes_search"}]


def estimate_ad_spend(
    app_id: str, country: str = "us", monthly_downloads_est: Optional[int] = None
) -> dict[str, Any]:
    """
    Estimate monthly ad spend for an iOS app based on category,
    rating velocity, and industry benchmarks.

    Uses heuristics: CPI (cost per install) by category × estimated downloads.
    Without real download data, uses rating_count growth as a proxy.

    Args:
        app_id: Apple numeric ID
        country: Store country code
        monthly_downloads_est: If known, override the heuristic download estimate

    Returns:
        dict with estimated monthly_ad_spend_usd, cpi_estimate, downloads_estimate,
        confidence level, and methodology notes

    Example:
        >>> spend = estimate_ad_spend('389801252')  # Instagram
        >>> print(f"Est. monthly ad spend: ${spend['monthly_ad_spend_usd']:,.0f}")
    """
    try:
        app = lookup_ios_app(app_id, country)
        if "error" in app:
            return app

        category = app.get("category", "")
        multiplier = CATEGORY_AD_MULTIPLIERS.get(category, 1.0)
        rating_count = app.get("rating_count") or 0

        # Base CPI estimates by region (USD)
        base_cpi = {"us": 2.50, "gb": 2.20, "de": 2.00, "jp": 3.00, "br": 0.80}
        cpi = base_cpi.get(country.lower(), 1.80) * multiplier

        # Estimate monthly downloads from total rating count
        # Heuristic: ~2% of users leave ratings, app lifetime ~36 months
        if monthly_downloads_est:
            downloads = monthly_downloads_est
            confidence = "medium-high"
        elif rating_count > 0:
            lifetime_downloads = rating_count / 0.02
            avg_monthly = lifetime_downloads / 36
            downloads = int(avg_monthly)
            confidence = "low-medium"
        else:
            downloads = 5000  # fallback
            confidence = "very-low"

        # Not all downloads are paid; estimate 30-60% organic for established apps
        organic_pct = 0.50 if rating_count > 100000 else 0.35
        paid_downloads = int(downloads * (1 - organic_pct))
        spend = round(paid_downloads * cpi, 2)

        return {
            "app_id": app_id,
            "app_name": app.get("name", ""),
            "category": category,
            "country": country,
            "cpi_estimate_usd": round(cpi, 2),
            "downloads_estimate_monthly": downloads,
            "organic_pct": organic_pct,
            "paid_downloads_estimate": paid_downloads,
            "monthly_ad_spend_usd": spend,
            "annual_ad_spend_usd": round(spend * 12, 2),
            "confidence": confidence,
            "methodology": "CPI × paid-download estimate (rating-count proxy)",
            "fetched_at": datetime.utcnow().isoformat(),
            "source": "quantclaw_heuristic",
        }
    except Exception as e:
        return {"error": str(e), "source": "estimate_ad_spend", "app_id": app_id}


def estimate_demographics(app_id: str, country: str = "us") -> dict[str, Any]:
    """
    Estimate user demographics for an iOS app based on its category.

    Uses industry benchmark data for age distribution and gender split
    by app category. More accurate for large, well-known apps.

    Args:
        app_id: Apple numeric ID
        country: Store country code

    Returns:
        dict with age_distribution (18-24, 25-34, 35-44, 45+),
        male_pct, female_pct, and confidence level

    Example:
        >>> demo = estimate_demographics('389801252')
        >>> print(demo['age_distribution'])
    """
    try:
        app = lookup_ios_app(app_id, country)
        if "error" in app:
            return app

        category = app.get("category", "")
        demo = GENRE_DEMOGRAPHICS.get(category, DEFAULT_DEMOGRAPHICS).copy()
        male_pct = demo.pop("male_pct", 0.50)

        return {
            "app_id": app_id,
            "app_name": app.get("name", ""),
            "category": category,
            "age_distribution": {k: v for k, v in demo.items()},
            "male_pct": round(male_pct, 2),
            "female_pct": round(1 - male_pct, 2),
            "confidence": "medium" if category in GENRE_DEMOGRAPHICS else "low",
            "methodology": "Industry benchmarks by app category (eMarketer/Statista proxies)",
            "fetched_at": datetime.utcnow().isoformat(),
            "source": "quantclaw_heuristic",
        }
    except Exception as e:
        return {"error": str(e), "source": "estimate_demographics", "app_id": app_id}


def get_app_performance(app_id: str, country: str = "us") -> dict[str, Any]:
    """
    Get performance metrics for an iOS app: ratings trend, version velocity,
    size, and update frequency indicators.

    Args:
        app_id: Apple numeric ID
        country: Store country code

    Returns:
        dict with rating, rating_count, version, update_frequency_days,
        size_mb, and derived health indicators

    Example:
        >>> perf = get_app_performance('389801252')
        >>> print(perf['health_score'])
    """
    try:
        app = lookup_ios_app(app_id, country)
        if "error" in app:
            return app

        # Calculate update frequency
        release_date = app.get("release_date", "")
        last_updated = app.get("last_updated", "")
        update_freq_days = None
        if release_date and last_updated:
            try:
                released = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
                updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                days_since_update = (datetime.now(released.tzinfo) - updated).days
                update_freq_days = days_since_update
            except (ValueError, TypeError):
                pass

        size_bytes = app.get("size_bytes")
        size_mb = round(int(size_bytes) / (1024 * 1024), 1) if size_bytes else None

        rating = app.get("rating") or 0
        rating_count = app.get("rating_count") or 0

        # Health score: 0-100 composite
        score = 50  # baseline
        if rating >= 4.5:
            score += 20
        elif rating >= 4.0:
            score += 10
        elif rating < 3.0:
            score -= 20

        if rating_count > 1000000:
            score += 15
        elif rating_count > 100000:
            score += 10
        elif rating_count > 10000:
            score += 5

        if update_freq_days is not None:
            if update_freq_days < 30:
                score += 15
            elif update_freq_days < 90:
                score += 5
            elif update_freq_days > 365:
                score -= 15

        score = max(0, min(100, score))

        return {
            "app_id": app_id,
            "app_name": app.get("name", ""),
            "category": app.get("category", ""),
            "rating": rating,
            "rating_count": rating_count,
            "current_version": app.get("current_version", ""),
            "size_mb": size_mb,
            "days_since_update": update_freq_days,
            "content_rating": app.get("content_rating", ""),
            "health_score": score,
            "health_label": "excellent" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "poor",
            "fetched_at": datetime.utcnow().isoformat(),
            "source": "itunes_lookup + quantclaw_heuristic",
        }
    except Exception as e:
        return {"error": str(e), "source": "get_app_performance", "app_id": app_id}


def get_top_apps_by_category(
    category: str = "Finance", country: str = "us", limit: int = 10
) -> list[dict]:
    """
    Get top apps in a category by searching the App Store.

    Args:
        category: Category name to search (e.g. 'Finance', 'Games', 'Health & Fitness')
        country: Store country code
        limit: Max results (1-50)

    Returns:
        List of dicts with app details sorted by relevance/popularity

    Example:
        >>> top = get_top_apps_by_category('Finance', limit=5)
        >>> for app in top: print(app['name'], app['rating_count'])
    """
    return search_ios_apps(category, country=country, limit=limit)


def compare_apps(app_ids: list[str], country: str = "us") -> list[dict]:
    """
    Compare multiple iOS apps side by side on key metrics.

    Args:
        app_ids: List of Apple numeric IDs
        country: Store country code

    Returns:
        List of dicts, one per app, with name, rating, rating_count,
        category, price, health_score, estimated ad spend

    Example:
        >>> comparison = compare_apps(['389801252', '284882215'])  # Instagram vs Facebook
        >>> for app in comparison: print(app['app_name'], app['health_score'])
    """
    results = []
    for aid in app_ids:
        perf = get_app_performance(aid, country)
        spend = estimate_ad_spend(aid, country)
        entry = {
            "app_id": aid,
            "app_name": perf.get("app_name", ""),
            "category": perf.get("category", ""),
            "rating": perf.get("rating"),
            "rating_count": perf.get("rating_count"),
            "health_score": perf.get("health_score"),
            "health_label": perf.get("health_label"),
            "est_monthly_ad_spend_usd": spend.get("monthly_ad_spend_usd"),
            "est_monthly_downloads": spend.get("downloads_estimate_monthly"),
        }
        if "error" in perf:
            entry["error"] = perf["error"]
        results.append(entry)
    return results


# Module metadata
MODULE_INFO = {
    "name": "mobileaction_intelligence_api",
    "version": "1.0.0",
    "description": "App intelligence: ad spend estimates, demographics, performance metrics",
    "functions": [
        "lookup_ios_app", "search_ios_apps", "estimate_ad_spend",
        "estimate_demographics", "get_app_performance",
        "get_top_apps_by_category", "compare_apps",
    ],
    "source": "Apple iTunes API + QuantClaw heuristics",
    "requires_api_key": False,
    "category": "Web Traffic & App Data",
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
