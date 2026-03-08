"""
Semrush Traffic Analytics API — Web traffic estimates and analytics.

Provides website traffic data including visitor estimates, traffic sources,
engagement metrics, and geographic distribution for competitive analysis
and quantitative trading signals.

Source: https://www.semrush.com/api-documentation/traffic-analytics/
Update frequency: Monthly
Category: Web Traffic & App Data
Free tier: 10 queries/day, 100 results/query (requires free API key)
"""

import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional


API_BASE = "https://api.semrush.com/analytics/ta/api/v3"
DEFAULT_KEY = os.environ.get("SEMRUSH_API_KEY")

# Simple in-process rate-limit counter (resets on restart; free tier = 10/day)
_request_count = 0
_request_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
FREE_TIER_LIMIT = 10

_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$")


def _validate_domain(domain: str) -> Optional[str]:
    """Return error string if domain is invalid, else None."""
    if not domain or not isinstance(domain, str):
        return "domain must be a non-empty string"
    domain = domain.strip().lower()
    if domain.startswith("http"):
        return f"Pass bare domain without scheme (got '{domain}'). Example: 'amazon.com'"
    if not _DOMAIN_RE.match(domain):
        return f"Invalid domain format: '{domain}'"
    return None


def _check_rate_limit() -> Optional[dict]:
    """Return error dict if daily free-tier limit is exceeded, else None."""
    global _request_count, _request_date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today != _request_date:
        _request_count = 0
        _request_date = today
    if _request_count >= FREE_TIER_LIMIT:
        return {
            "error": f"Free-tier daily limit reached ({FREE_TIER_LIMIT} requests). "
                     "Resets at midnight UTC. Upgrade at https://www.semrush.com/prices/"
        }
    return None


def _make_request(endpoint: str, params: dict, api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Internal helper for Semrush Traffic Analytics API requests.

    Args:
        endpoint: API endpoint path
        params: Query parameters
        api_key: Semrush API key (falls back to SEMRUSH_API_KEY env var)

    Returns:
        Parsed JSON response as dict
    """
    global _request_count

    key = api_key or DEFAULT_KEY
    if not key:
        return {
            "error": "API key required. Set SEMRUSH_API_KEY env var or pass api_key. "
                     "Get free key at https://www.semrush.com/analytics/traffic/"
        }

    limit_err = _check_rate_limit()
    if limit_err:
        return limit_err

    params["key"] = key
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            _request_count += 1
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:500]
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": body}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from Semrush"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_domain_summary(
    domain: str,
    display_date: Optional[str] = None,
    country: str = "us",
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get traffic summary for a domain (visits, unique visitors, bounce rate, etc.).

    Args:
        domain: Target domain (e.g., 'example.com')
        display_date: Month in 'YYYY-MM-01' format (default: latest available)
        country: Two-letter country code (default: 'us')
        api_key: Semrush API key

    Returns:
        dict with keys: domain, visits, unique_visitors, pages_per_visit,
        avg_visit_duration, bounce_rate, display_date

    Example:
        >>> summary = get_domain_summary('amazon.com')
        >>> print(summary.get('visits'))
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "display_limit": 1,
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("summary", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list) and len(result) > 0:
        row = result[0]
        return {
            "domain": domain,
            "visits": row.get("visits"),
            "unique_visitors": row.get("users"),
            "pages_per_visit": row.get("pages_per_visit"),
            "avg_visit_duration": row.get("avg_visit_duration"),
            "bounce_rate": row.get("bounce_rate"),
            "display_date": row.get("display_date"),
            "country": country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "domain": domain,
        "raw": result,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_traffic_sources(
    domain: str,
    display_date: Optional[str] = None,
    country: str = "us",
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get traffic source breakdown for a domain (direct, search, social, paid, referral).

    Args:
        domain: Target domain (e.g., 'example.com')
        display_date: Month in 'YYYY-MM-01' format
        country: Two-letter country code
        api_key: Semrush API key

    Returns:
        dict with keys: domain, sources (dict of source_type -> share), display_date

    Example:
        >>> sources = get_traffic_sources('amazon.com')
        >>> print(sources.get('sources', {}).get('search_organic'))
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "display_limit": 1,
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("sources", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list) and len(result) > 0:
        row = result[0]
        return {
            "domain": domain,
            "sources": {
                "direct": row.get("direct"),
                "search_organic": row.get("search_organic"),
                "search_paid": row.get("search_paid"),
                "social": row.get("social"),
                "referral": row.get("referral"),
                "mail": row.get("mail"),
            },
            "display_date": row.get("display_date"),
            "country": country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def get_geo_distribution(
    domain: str,
    display_date: Optional[str] = None,
    limit: int = 20,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get geographic distribution of traffic for a domain.

    Args:
        domain: Target domain (e.g., 'example.com')
        display_date: Month in 'YYYY-MM-01' format
        limit: Max number of countries to return (default: 20, max: 100)
        api_key: Semrush API key

    Returns:
        dict with keys: domain, countries (list of {country, share, visits})

    Example:
        >>> geo = get_geo_distribution('amazon.com', limit=5)
        >>> for c in geo.get('countries', []): print(c['country'], c['share'])
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "display_limit": min(limit, 100),
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("geo", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list):
        countries = []
        for row in result:
            countries.append({
                "country": row.get("country"),
                "share": row.get("share"),
                "visits": row.get("visits"),
                "unique_visitors": row.get("users"),
                "pages_per_visit": row.get("pages_per_visit"),
                "bounce_rate": row.get("bounce_rate"),
            })
        return {
            "domain": domain,
            "countries": countries,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def get_top_pages(
    domain: str,
    display_date: Optional[str] = None,
    country: str = "us",
    limit: int = 20,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get top pages for a domain ranked by traffic share.

    Args:
        domain: Target domain
        display_date: Month in 'YYYY-MM-01' format
        country: Two-letter country code
        limit: Max pages to return (default: 20, max: 100)
        api_key: Semrush API key

    Returns:
        dict with keys: domain, pages (list of {url, share, visits})

    Example:
        >>> pages = get_top_pages('reddit.com', limit=10)
        >>> for p in pages.get('pages', []): print(p['url'], p['share'])
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "display_limit": min(limit, 100),
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("toppages", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list):
        pages = []
        for row in result:
            pages.append({
                "url": row.get("page"),
                "share": row.get("share"),
                "visits": row.get("visits"),
                "unique_visitors": row.get("users"),
            })
        return {
            "domain": domain,
            "pages": pages,
            "country": country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def get_subdomains(
    domain: str,
    display_date: Optional[str] = None,
    country: str = "us",
    limit: int = 20,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get subdomains of a domain ranked by traffic share.

    Args:
        domain: Target domain
        display_date: Month in 'YYYY-MM-01' format
        country: Two-letter country code
        limit: Max subdomains to return (default: 20, max: 100)
        api_key: Semrush API key

    Returns:
        dict with keys: domain, subdomains (list of {subdomain, share, visits})

    Example:
        >>> subs = get_subdomains('google.com', limit=5)
        >>> for s in subs.get('subdomains', []): print(s['subdomain'], s['share'])
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "display_limit": min(limit, 100),
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("subdomains", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list):
        subdomains = []
        for row in result:
            subdomains.append({
                "subdomain": row.get("subdomain"),
                "share": row.get("share"),
                "visits": row.get("visits"),
                "unique_visitors": row.get("users"),
            })
        return {
            "domain": domain,
            "subdomains": subdomains,
            "country": country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def get_competitors(
    domain: str,
    display_date: Optional[str] = None,
    country: str = "us",
    limit: int = 10,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get competitor domains based on audience overlap.

    Args:
        domain: Target domain
        display_date: Month in 'YYYY-MM-01' format
        country: Two-letter country code
        limit: Max competitors to return (default: 10, max: 100)
        api_key: Semrush API key

    Returns:
        dict with keys: domain, competitors (list of {domain, overlap_score, visits})

    Example:
        >>> comps = get_competitors('shopify.com', limit=5)
        >>> for c in comps.get('competitors', []): print(c['domain'], c['overlap_score'])
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "display_limit": min(limit, 100),
    }
    if display_date:
        params["display_date"] = display_date

    result = _make_request("competitors", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list):
        competitors = []
        for row in result:
            competitors.append({
                "domain": row.get("domain"),
                "overlap_score": row.get("overlap"),
                "visits": row.get("visits"),
                "unique_visitors": row.get("users"),
            })
        return {
            "domain": domain,
            "competitors": competitors,
            "country": country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def get_historical_traffic(
    domain: str,
    country: str = "us",
    granularity: str = "monthly",
    months: int = 24,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get historical traffic trend for a domain.

    Args:
        domain: Target domain
        country: Two-letter country code
        granularity: 'monthly' or 'daily'
        months: Number of months of history (default: 24)
        api_key: Semrush API key

    Returns:
        dict with keys: domain, history (list of {date, visits, unique_visitors, ...})

    Example:
        >>> hist = get_historical_traffic('amazon.com')
        >>> for h in hist.get('history', []): print(h['date'], h['visits'])
    """
    err = _validate_domain(domain)
    if err:
        return {"error": err}

    params = {
        "targets": domain.strip().lower(),
        "country": country,
        "granularity": granularity,
        "display_limit": min(months, 60),
    }

    result = _make_request("summary", params, api_key)
    if "error" in result:
        return result

    if isinstance(result, list):
        history = []
        for row in result:
            history.append({
                "date": row.get("display_date"),
                "visits": row.get("visits"),
                "unique_visitors": row.get("users"),
                "pages_per_visit": row.get("pages_per_visit"),
                "avg_visit_duration": row.get("avg_visit_duration"),
                "bounce_rate": row.get("bounce_rate"),
            })
        return {
            "domain": domain,
            "history": sorted(history, key=lambda x: x.get("date") or ""),
            "country": country,
            "granularity": granularity,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"domain": domain, "raw": result, "fetched_at": datetime.now(timezone.utc).isoformat()}


def compare_domains(
    domains: list[str],
    country: str = "us",
    display_date: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Compare traffic metrics across multiple domains side-by-side.

    Args:
        domains: List of domains to compare (max 5)
        country: Two-letter country code
        display_date: Month in 'YYYY-MM-01' format
        api_key: Semrush API key

    Returns:
        dict with keys: domains (list of summary dicts), comparison_date

    Example:
        >>> cmp = compare_domains(['amazon.com', 'ebay.com', 'walmart.com'])
        >>> for d in cmp.get('domains', []): print(d['domain'], d.get('visits'))
    """
    if not domains or not isinstance(domains, list):
        return {"error": "domains must be a non-empty list of domain strings"}
    if len(domains) > 5:
        return {"error": "Maximum 5 domains per comparison (free-tier budget)"}

    results = []
    for domain in domains:
        summary = get_domain_summary(domain, display_date=display_date, country=country, api_key=api_key)
        results.append(summary)

    return {
        "domains": results,
        "country": country,
        "comparison_date": display_date or "latest",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_rate_limit_status() -> dict[str, Any]:
    """
    Check current rate-limit status for the free-tier counter.

    Returns:
        dict with requests_used, requests_remaining, limit, reset_date
    """
    global _request_count, _request_date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today != _request_date:
        _request_count = 0
        _request_date = today
    return {
        "requests_used": _request_count,
        "requests_remaining": max(0, FREE_TIER_LIMIT - _request_count),
        "limit": FREE_TIER_LIMIT,
        "reset_date": today,
    }


def fetch_data(domain: str = "example.com", api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Convenience function: fetch full traffic overview for a domain.
    Uses 3 API calls (summary + sources + geo).

    Args:
        domain: Target domain
        api_key: Semrush API key

    Returns:
        dict with summary, sources, and geo data combined
    """
    summary = get_domain_summary(domain, api_key=api_key)
    sources = get_traffic_sources(domain, api_key=api_key)
    geo = get_geo_distribution(domain, limit=10, api_key=api_key)

    return {
        "domain": domain,
        "summary": summary,
        "sources": sources,
        "geo": geo,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_latest(domain: str = "example.com", api_key: Optional[str] = None) -> dict[str, Any]:
    """
    Get latest traffic data point for a domain.
    Alias for get_domain_summary.

    Args:
        domain: Target domain
        api_key: Semrush API key

    Returns:
        dict with latest traffic metrics
    """
    return get_domain_summary(domain, api_key=api_key)


# Public API
__all__ = [
    "get_domain_summary",
    "get_traffic_sources",
    "get_geo_distribution",
    "get_top_pages",
    "get_subdomains",
    "get_competitors",
    "get_historical_traffic",
    "compare_domains",
    "get_rate_limit_status",
    "fetch_data",
    "get_latest",
]


if __name__ == "__main__":
    print(json.dumps({
        "module": "semrush_traffic_analytics_api",
        "status": "ready",
        "functions": __all__,
        "function_count": len(__all__),
        "source": "https://www.semrush.com/api-documentation/traffic-analytics/",
        "requires_key": True,
        "env_var": "SEMRUSH_API_KEY",
        "free_tier": "10 queries/day, 100 results/query",
    }, indent=2))
