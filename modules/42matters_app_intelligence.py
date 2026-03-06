"""
42matters App Intelligence — Mobile app market data and analytics.

Comprehensive app store data for iOS and Android including download estimates,
ratings, reviews, revenue metrics, and category rankings for quantitative analysis.

Source: https://42matters.com/app-intelligence-api
Update frequency: Daily
Category: Web Traffic & App Data
Free tier: 1,000 API calls/month
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://api.42matters.com"
# Note: Replace with actual API key from environment or config
DEFAULT_KEY = None


def get_app_details(
    package_id: str,
    platform: str = "android",
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get detailed information about a specific app.
    
    Args:
        package_id: App package ID (e.g., 'com.facebook.katana')
        platform: Platform ('android' or 'ios')
        access_token: 42matters API access token
        
    Returns:
        dict with app metadata including downloads, ratings, revenue estimates
        
    Example:
        >>> app = get_app_details('com.facebook.katana')
        >>> print(app.get('title'), app.get('rating'))
    """
    token = access_token or DEFAULT_KEY
    if not token:
        return {"error": "API key required. Get free key at https://42matters.com/app-intelligence-api"}
    
    if platform == "android":
        endpoint = f"{API_BASE}/v3.0/android/apps/lookup.json"
    elif platform == "ios":
        endpoint = f"{API_BASE}/v3.0/ios/apps/lookup.json"
    else:
        return {"error": f"Invalid platform: {platform}. Use 'android' or 'ios'"}
    
    params = {
        "id": package_id,
        "access_token": token
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "package_id": data.get("package_name") or data.get("bundle_id"),
                "title": data.get("title"),
                "rating": data.get("rating"),
                "rating_count": data.get("rating_count"),
                "downloads_min": data.get("downloads_min"),
                "downloads_max": data.get("downloads_max"),
                "price": data.get("price"),
                "publisher": data.get("publisher"),
                "category": data.get("category"),
                "release_date": data.get("release_date"),
                "last_update": data.get("updated_date"),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e)}


def get_top_apps(
    category: Optional[str] = None,
    country: str = "us",
    platform: str = "android",
    limit: int = 100,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get top apps by category and country.
    
    Args:
        category: App category (e.g., 'FINANCE', 'GAME_CASUAL')
        country: Country code (e.g., 'us', 'gb')
        platform: Platform ('android' or 'ios')
        limit: Number of results (max 100)
        access_token: 42matters API access token
        
    Returns:
        dict with list of top apps and metadata
        
    Example:
        >>> top = get_top_apps(category='FINANCE', limit=10)
        >>> for app in top.get('apps', []):
        ...     print(app['title'], app['downloads_min'])
    """
    token = access_token or DEFAULT_KEY
    if not token:
        return {"error": "API key required"}
    
    if platform == "android":
        endpoint = f"{API_BASE}/v3.0/android/apps/top.json"
    else:
        endpoint = f"{API_BASE}/v3.0/ios/apps/top.json"
    
    params = {
        "country": country,
        "limit": min(limit, 100),
        "access_token": token
    }
    
    if category:
        params["category"] = category
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "category": category,
                "country": country,
                "platform": platform,
                "apps": data.get("app_list", []),
                "total": len(data.get("app_list", [])),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e)}


def search_apps(
    query: str,
    platform: str = "android",
    limit: int = 50,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for apps by keyword.
    
    Args:
        query: Search query string
        platform: Platform ('android' or 'ios')
        limit: Number of results (max 100)
        access_token: 42matters API access token
        
    Returns:
        dict with search results
        
    Example:
        >>> results = search_apps('trading app')
        >>> print(len(results.get('apps', [])))
    """
    token = access_token or DEFAULT_KEY
    if not token:
        return {"error": "API key required"}
    
    if platform == "android":
        endpoint = f"{API_BASE}/v3.0/android/apps/search.json"
    else:
        endpoint = f"{API_BASE}/v3.0/ios/apps/search.json"
    
    params = {
        "q": query,
        "limit": min(limit, 100),
        "access_token": token
    }
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "query": query,
                "platform": platform,
                "apps": data.get("app_list", []),
                "total": len(data.get("app_list", [])),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e)}


def get_app_history(
    package_id: str,
    platform: str = "android",
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get historical data for an app (downloads, ratings over time).
    
    Args:
        package_id: App package ID
        platform: Platform ('android' or 'ios')
        access_token: 42matters API access token
        
    Returns:
        dict with historical metrics
        
    Example:
        >>> history = get_app_history('com.robinhood.android')
        >>> print(history.get('downloads_history', []))
    """
    token = access_token or DEFAULT_KEY
    if not token:
        return {"error": "API key required"}
    
    # Note: Historical data may require premium tier
    # This is a placeholder for the endpoint structure
    
    return {
        "package_id": package_id,
        "platform": platform,
        "note": "Historical data requires premium 42matters subscription",
        "alternative": "Use get_app_details() for current snapshot"
    }


# Demo function for testing
def demo():
    """Demo with sample app data (no API key required)."""
    sample_data = {
        "package_id": "com.example.app",
        "title": "Sample App",
        "rating": 4.2,
        "rating_count": 125000,
        "downloads_min": 1000000,
        "downloads_max": 5000000,
        "category": "FINANCE",
        "publisher": "Sample Corp",
        "note": "This is sample data. Provide API key for real data."
    }
    return sample_data


if __name__ == "__main__":
    # Test with demo data
    print(json.dumps(demo(), indent=2))
