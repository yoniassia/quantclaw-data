"""
Sensor Tower App Intelligence API — Mobile app download/revenue estimates and rankings.

App store analytics for iOS and Android including download estimates, revenue estimates,
user ratings, category rankings, SDK usage, and ad spend insights for quantitative analysis.

Source: https://sensortower.com/api/docs/app-intelligence
Update frequency: Daily
Category: Web Traffic & App Data
Free tier: 50 API calls/month (public app data, no credit card required)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


API_BASE = "https://api.sensortower.com/v1"
# Auth token from environment or passed per-call; free tier = 50 calls/month
DEFAULT_TOKEN = None


def _api_request(endpoint: str, params: dict, auth_token: Optional[str] = None) -> dict:
    """
    Internal helper for Sensor Tower API requests.

    Args:
        endpoint: API endpoint path (e.g., '/apps')
        params: Query parameters
        auth_token: Sensor Tower auth token

    Returns:
        Parsed JSON response as dict/list

    Raises:
        ValueError: If no auth token provided
    """
    token = auth_token or DEFAULT_TOKEN
    if not token:
        return {
            "error": "API token required. Get free token at https://sensortower.com (50 calls/month free)",
            "signup_url": "https://sensortower.com/signup"
        }

    params["auth_token"] = token
    url = f"{API_BASE}{endpoint}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "QuantClaw-Data/1.0"
        })
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
        return {"error": f"Connection error: {str(e.reason)}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_app_details(
    app_id: str,
    platform: str = "ios",
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get detailed information about a specific app.

    Args:
        app_id: App store ID (e.g., '389801252' for Instagram on iOS,
                'com.instagram.android' for Android)
        platform: 'ios' or 'android'
        auth_token: Sensor Tower API auth token

    Returns:
        dict with app metadata, ratings, downloads, revenue estimates

    Example:
        >>> details = get_app_details('389801252', platform='ios')
        >>> print(details.get('name'), details.get('rating'))
    """
    endpoint = f"/{platform}/app/info"
    params = {"app_id": app_id}
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    return {
        "app_id": data.get("app_id") or data.get("id") or app_id,
        "name": data.get("name") or data.get("title"),
        "publisher": data.get("publisher") or data.get("developer"),
        "platform": platform,
        "rating": data.get("rating"),
        "rating_count": data.get("rating_count") or data.get("ratings_count"),
        "current_version": data.get("version") or data.get("current_version"),
        "price": data.get("price"),
        "category": data.get("category") or data.get("primary_category"),
        "release_date": data.get("release_date"),
        "last_updated": data.get("last_updated") or data.get("updated_date"),
        "description": data.get("description", "")[:500],
        "icon_url": data.get("icon_url") or data.get("icon"),
        "raw": data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_download_estimates(
    app_id: str,
    platform: str = "ios",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "monthly",
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get app download estimates over a time range.

    Args:
        app_id: App store ID
        platform: 'ios' or 'android'
        start_date: Start date 'YYYY-MM-DD' (default: 6 months ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        granularity: 'daily', 'weekly', or 'monthly'
        auth_token: Sensor Tower API auth token

    Returns:
        dict with download estimates timeline

    Example:
        >>> dl = get_download_estimates('389801252', granularity='monthly')
        >>> for point in dl.get('estimates', []):
        ...     print(point['date'], point['downloads'])
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")

    endpoint = f"/{platform}/app/download_estimates"
    params = {
        "app_id": app_id,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    estimates = []
    if isinstance(data, list):
        for entry in data:
            estimates.append({
                "date": entry.get("date"),
                "downloads": entry.get("downloads") or entry.get("units"),
            })
    elif isinstance(data, dict) and "estimates" in data:
        estimates = data["estimates"]

    return {
        "app_id": app_id,
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity,
        "estimates": estimates or data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_revenue_estimates(
    app_id: str,
    platform: str = "ios",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "monthly",
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get app revenue estimates over a time range.

    Args:
        app_id: App store ID
        platform: 'ios' or 'android'
        start_date: Start date 'YYYY-MM-DD' (default: 6 months ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        granularity: 'daily', 'weekly', or 'monthly'
        auth_token: Sensor Tower API auth token

    Returns:
        dict with revenue estimates timeline

    Example:
        >>> rev = get_revenue_estimates('389801252', granularity='monthly')
        >>> print(rev.get('estimates'))
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")

    endpoint = f"/{platform}/app/revenue_estimates"
    params = {
        "app_id": app_id,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    estimates = []
    if isinstance(data, list):
        for entry in data:
            estimates.append({
                "date": entry.get("date"),
                "revenue": entry.get("revenue") or entry.get("amount"),
            })
    elif isinstance(data, dict) and "estimates" in data:
        estimates = data["estimates"]

    return {
        "app_id": app_id,
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity,
        "estimates": estimates or data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_category_rankings(
    app_id: str,
    platform: str = "ios",
    country: str = "US",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get app category ranking history.

    Args:
        app_id: App store ID
        platform: 'ios' or 'android'
        country: ISO country code (default 'US')
        start_date: Start date 'YYYY-MM-DD' (default: 30 days ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        auth_token: Sensor Tower API auth token

    Returns:
        dict with ranking history by category

    Example:
        >>> ranks = get_category_rankings('389801252', country='US')
        >>> print(ranks.get('rankings'))
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    endpoint = f"/{platform}/app/rankings"
    params = {
        "app_id": app_id,
        "country": country,
        "start_date": start_date,
        "end_date": end_date
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    return {
        "app_id": app_id,
        "platform": platform,
        "country": country,
        "start_date": start_date,
        "end_date": end_date,
        "rankings": data if isinstance(data, list) else data.get("rankings", data),
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_ratings_and_reviews(
    app_id: str,
    platform: str = "ios",
    country: str = "US",
    limit: int = 50,
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get recent ratings and reviews for an app.

    Args:
        app_id: App store ID
        platform: 'ios' or 'android'
        country: ISO country code
        limit: Max reviews to return (default 50)
        auth_token: Sensor Tower API auth token

    Returns:
        dict with reviews list and rating summary

    Example:
        >>> reviews = get_ratings_and_reviews('389801252', limit=10)
        >>> print(reviews.get('average_rating'), len(reviews.get('reviews', [])))
    """
    endpoint = f"/{platform}/app/reviews"
    params = {
        "app_id": app_id,
        "country": country,
        "limit": str(limit)
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    reviews = []
    raw_reviews = data if isinstance(data, list) else data.get("reviews", [])
    for r in raw_reviews[:limit]:
        reviews.append({
            "rating": r.get("rating") or r.get("score"),
            "title": r.get("title"),
            "body": r.get("body") or r.get("content", "")[:500],
            "author": r.get("author") or r.get("username"),
            "date": r.get("date") or r.get("created_at"),
        })

    return {
        "app_id": app_id,
        "platform": platform,
        "country": country,
        "review_count": len(reviews),
        "average_rating": data.get("average_rating") if isinstance(data, dict) else None,
        "reviews": reviews,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_sdk_intelligence(
    app_id: str,
    platform: str = "android",
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get SDK/library usage data for an app.

    Args:
        app_id: App store ID or package name
        platform: 'ios' or 'android'
        auth_token: Sensor Tower API auth token

    Returns:
        dict with list of SDKs/libraries integrated in the app

    Example:
        >>> sdks = get_sdk_intelligence('com.instagram.android', platform='android')
        >>> for sdk in sdks.get('sdks', []):
        ...     print(sdk['name'], sdk.get('category'))
    """
    endpoint = f"/{platform}/app/sdks"
    params = {"app_id": app_id}
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    sdks = []
    raw_sdks = data if isinstance(data, list) else data.get("sdks", [])
    for sdk in raw_sdks:
        sdks.append({
            "name": sdk.get("name") or sdk.get("sdk_name"),
            "category": sdk.get("category"),
            "first_seen": sdk.get("first_seen") or sdk.get("installed_date"),
            "last_seen": sdk.get("last_seen"),
        })

    return {
        "app_id": app_id,
        "platform": platform,
        "sdk_count": len(sdks),
        "sdks": sdks or data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_top_apps(
    category: str = "overall",
    platform: str = "ios",
    country: str = "US",
    chart_type: str = "free",
    limit: int = 25,
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get top-ranked apps in a category.

    Args:
        category: Category name or ID (default 'overall')
        platform: 'ios' or 'android'
        country: ISO country code
        chart_type: 'free', 'paid', or 'grossing'
        limit: Number of apps to return (default 25)
        auth_token: Sensor Tower API auth token

    Returns:
        dict with ranked list of top apps

    Example:
        >>> top = get_top_apps(category='overall', chart_type='grossing', limit=10)
        >>> for app in top.get('apps', []):
        ...     print(app['rank'], app['name'])
    """
    endpoint = f"/{platform}/rankings/top_charts"
    params = {
        "category": category,
        "country": country,
        "chart_type": chart_type,
        "limit": str(limit)
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    apps = []
    raw_apps = data if isinstance(data, list) else data.get("apps", [])
    for i, app in enumerate(raw_apps[:limit], 1):
        apps.append({
            "rank": app.get("rank", i),
            "app_id": app.get("app_id") or app.get("id"),
            "name": app.get("name") or app.get("title"),
            "publisher": app.get("publisher") or app.get("developer"),
            "rating": app.get("rating"),
            "downloads": app.get("downloads"),
        })

    return {
        "category": category,
        "platform": platform,
        "country": country,
        "chart_type": chart_type,
        "app_count": len(apps),
        "apps": apps or data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_ad_intelligence(
    app_id: str,
    platform: str = "ios",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get ad spend and creative intelligence for an app.

    Args:
        app_id: App store ID
        platform: 'ios' or 'android'
        start_date: Start date 'YYYY-MM-DD' (default: 30 days ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        auth_token: Sensor Tower API auth token

    Returns:
        dict with ad network presence, creative counts, spend estimates

    Example:
        >>> ads = get_ad_intelligence('389801252')
        >>> print(ads.get('networks'), ads.get('creative_count'))
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    endpoint = f"/{platform}/app/ad_intelligence"
    params = {
        "app_id": app_id,
        "start_date": start_date,
        "end_date": end_date
    }
    data = _api_request(endpoint, params, auth_token)

    if "error" in data:
        return data

    return {
        "app_id": app_id,
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
        "networks": data.get("networks") or data.get("ad_networks", []),
        "creative_count": data.get("creative_count") or data.get("total_creatives"),
        "spend_estimate": data.get("spend_estimate") or data.get("estimated_spend"),
        "raw": data,
        "source": "sensor_tower",
        "fetched_at": datetime.utcnow().isoformat()
    }


# --- Convenience aliases ---

def fetch_data(app_id: str, platform: str = "ios", auth_token: Optional[str] = None) -> dict:
    """Fetch comprehensive app data (alias for get_app_details)."""
    return get_app_details(app_id, platform, auth_token)


def get_latest(app_id: str, platform: str = "ios", auth_token: Optional[str] = None) -> dict:
    """Get latest data point for an app (alias for get_app_details)."""
    return get_app_details(app_id, platform, auth_token)


if __name__ == "__main__":
    print(json.dumps({
        "module": "sensor_tower_app_intelligence_api",
        "status": "implemented",
        "source": "https://sensortower.com/api/docs/app-intelligence",
        "functions": [
            "get_app_details", "get_download_estimates", "get_revenue_estimates",
            "get_category_rankings", "get_ratings_and_reviews", "get_sdk_intelligence",
            "get_top_apps", "get_ad_intelligence", "fetch_data", "get_latest"
        ],
        "free_tier": "50 API calls/month"
    }, indent=2))
