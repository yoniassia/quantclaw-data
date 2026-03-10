"""
TrackInsight ETF API — ETF analytics, ratings, flows, and ESG data.

TrackInsight is a leading ETF analytics platform providing ratings, flows,
ESG scores, and performance data for thousands of ETFs globally.
This module scrapes publicly available data from trackinsight.com.

Source: https://www.trackinsight.com/en/api
Update frequency: Daily
Category: ETF & Fund Flows
Free tier: Public web data (no API key required)
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


BASE_URL = "https://www.trackinsight.com"
LOCATE_URL = f"{BASE_URL}/locate-api"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _request(url: str, headers: Optional[dict] = None, timeout: int = 15) -> str:
    """Make an HTTP request with browser-like headers."""
    hdrs = {**_HEADERS, **(headers or {})}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return json.dumps({"error": str(e)})


def _request_json(url: str, headers: Optional[dict] = None, timeout: int = 15) -> dict:
    """Make an HTTP request and parse JSON response."""
    hdrs = {**_HEADERS, "Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"error": str(e)}


def get_user_location() -> dict:
    """
    Get the user's detected location from TrackInsight's locate API.

    Returns:
        dict with country, continent, investment region, currency info

    Example:
        >>> loc = get_user_location()
        >>> print(loc.get('ctry'), loc.get('cur'))
    """
    return _request_json(LOCATE_URL)


def get_fund_page_url(ticker: str, locale: str = "en") -> str:
    """
    Get the TrackInsight fund page URL for a given ticker.

    Args:
        ticker: ETF ticker symbol (e.g., 'SPY', 'QQQ', 'VTI')
        locale: Language locale ('en', 'fr', 'de', etc.)

    Returns:
        str: URL of the fund page on TrackInsight
    """
    return f"{BASE_URL}/{locale}/fund/{ticker.upper()}"


def search_etfs_sitemap(limit: int = 100) -> list[dict]:
    """
    Get ETF fund listings from TrackInsight's sitemap.

    Parses the XML sitemap to discover available ETF fund pages
    and extract ticker symbols.

    Args:
        limit: Maximum number of funds to return

    Returns:
        list of dicts with 'ticker', 'url', 'locale' keys

    Example:
        >>> funds = search_etfs_sitemap(limit=10)
        >>> for f in funds[:3]:
        ...     print(f['ticker'], f['url'])
    """
    url = f"{BASE_URL}/sitemap.xml"
    try:
        content = _request(url)
        # Find tickers from compare-etfs and fund page URLs
        compare_pattern = re.compile(
            r'<loc>https://www\.trackinsight\.com/en/compare-etfs/([A-Z0-9.]+(?:,[A-Z0-9.]+)*)</loc>'
        )
        fund_pattern = re.compile(
            r'<loc>(https://www\.trackinsight\.com/(en)/fund/([A-Z0-9.]+))</loc>'
        )
        results = []
        seen = set()
        # From fund pages
        for match in fund_pattern.finditer(content):
            full_url, locale, ticker = match.groups()
            if ticker not in seen:
                seen.add(ticker)
                results.append({"ticker": ticker, "url": full_url, "locale": locale})
        # From compare pages
        for match in compare_pattern.finditer(content):
            for ticker in match.group(1).split(","):
                if ticker not in seen:
                    seen.add(ticker)
                    results.append({
                        "ticker": ticker,
                        "url": f"{BASE_URL}/en/fund/{ticker}",
                        "locale": "en",
                    })
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_etf_universe() -> dict:
    """
    Get a summary of the ETF universe available on TrackInsight.

    Scrapes the main sitemap to count available ETFs by region/locale.

    Returns:
        dict with 'total_funds', 'locales', 'sample_tickers'

    Example:
        >>> universe = get_etf_universe()
        >>> print(f"Total ETFs: {universe.get('total_funds')}")
    """
    url = f"{BASE_URL}/sitemap.xml"
    try:
        content = _request(url)
        # Extract tickers from both fund pages and compare pages
        compare_pattern = re.compile(
            r'<loc>https://www\.trackinsight\.com/(\w+)/compare-etfs/([A-Z0-9.]+(?:,[A-Z0-9.]+)*)</loc>'
        )
        fund_pattern = re.compile(
            r'<loc>https://www\.trackinsight\.com/(\w+)/fund/([A-Z0-9.]+)</loc>'
        )
        tickers = set()
        locales = {}
        for match in fund_pattern.finditer(content):
            locale, ticker = match.groups()
            tickers.add(ticker)
            locales[locale] = locales.get(locale, 0) + 1
        for match in compare_pattern.finditer(content):
            locale = match.group(1)
            for ticker in match.group(2).split(","):
                tickers.add(ticker)
                locales[locale] = locales.get(locale, 0) + 1

        sample = sorted(list(tickers))[:20]
        return {
            "total_funds": len(tickers),
            "locales": locales,
            "sample_tickers": sample,
            "source": "trackinsight.com/sitemap.xml",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_fund_metadata(ticker: str) -> dict:
    """
    Get metadata for an ETF fund from TrackInsight page HTML.

    Extracts available metadata from the fund's page including
    the page title, canonical URL, and any structured data.

    Args:
        ticker: ETF ticker symbol (e.g., 'SPY', 'QQQ')

    Returns:
        dict with fund metadata including 'ticker', 'url', 'title',
        'has_page' (bool), and 'available_locales'

    Example:
        >>> meta = get_fund_metadata('SPY')
        >>> print(meta.get('title'), meta.get('has_page'))
    """
    ticker = ticker.upper()
    url = f"{BASE_URL}/en/fund/{ticker}"
    try:
        content = _request(url)

        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', content)
        title = title_match.group(1).strip() if title_match else None

        # Check for alternate language links
        alt_pattern = re.compile(
            r'hreflang="(\w+)"\s+href="(https://[^"]+/fund/' + re.escape(ticker) + r')"'
        )
        locales = {}
        for m in alt_pattern.finditer(content):
            locales[m.group(1)] = m.group(2)

        # Check if page actually has fund data (not a 404/redirect)
        has_page = bool(title and "Trackinsight" in title and ticker.lower() in title.lower()) or bool(locales)

        # Extract meta description
        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
        description = desc_match.group(1) if desc_match else None

        # Extract og:image
        img_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', content)
        og_image = img_match.group(1) if img_match else None

        return {
            "ticker": ticker,
            "url": url,
            "title": title,
            "description": description,
            "og_image": og_image,
            "has_page": has_page,
            "available_locales": locales,
            "source": "trackinsight.com",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_available_fund_tickers(max_funds: int = 500) -> list[str]:
    """
    Get a list of all available ETF ticker symbols from TrackInsight.

    Args:
        max_funds: Maximum number of tickers to retrieve

    Returns:
        Sorted list of ticker symbols

    Example:
        >>> tickers = get_available_fund_tickers(50)
        >>> print(f"Found {len(tickers)} tickers")
        >>> print(tickers[:5])
    """
    url = f"{BASE_URL}/sitemap.xml"
    try:
        content = _request(url)
        compare_pattern = re.compile(
            r'<loc>https://www\.trackinsight\.com/en/compare-etfs/([A-Z0-9.]+(?:,[A-Z0-9.]+)*)</loc>'
        )
        fund_pattern = re.compile(
            r'<loc>https://www\.trackinsight\.com/en/fund/([A-Z0-9.]+)</loc>'
        )
        tickers = set()
        for match in fund_pattern.finditer(content):
            tickers.add(match.group(1))
        for match in compare_pattern.finditer(content):
            for ticker in match.group(1).split(","):
                tickers.add(ticker)
            if len(tickers) >= max_funds:
                break
        return sorted(list(tickers))[:max_funds]
    except Exception as e:
        return []


def build_comparison_url(tickers: list[str], locale: str = "en") -> str:
    """
    Build a TrackInsight comparison URL for multiple ETFs.

    Args:
        tickers: List of ETF ticker symbols to compare
        locale: Language locale

    Returns:
        str: TrackInsight comparison URL

    Example:
        >>> url = build_comparison_url(['SPY', 'QQQ', 'VTI'])
        >>> print(url)
    """
    ticker_str = ",".join(t.upper() for t in tickers)
    return f"{BASE_URL}/{locale}/compare-etfs/{ticker_str}"


def get_screener_url(
    asset_class: str = "equity",
    region: Optional[str] = None,
    locale: str = "en",
) -> str:
    """
    Build a TrackInsight ETF screener URL with filters.

    Args:
        asset_class: Asset class filter ('equity', 'bond', 'commodity', etc.)
        region: Region filter ('us', 'europe', 'asia', etc.)
        locale: Language locale

    Returns:
        str: TrackInsight screener URL with applied filters

    Example:
        >>> url = get_screener_url('equity', 'us')
        >>> print(url)
    """
    base = f"{BASE_URL}/{locale}/screener"
    params = {}
    if asset_class:
        params["assetClass"] = asset_class
    if region:
        params["region"] = region
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base


def get_top_etf_categories() -> list[dict]:
    """
    Get the main ETF categories tracked by TrackInsight.

    Returns a curated list of ETF categories with their
    TrackInsight screener URLs and descriptions.

    Returns:
        list of dicts with 'category', 'description', 'screener_url'

    Example:
        >>> cats = get_top_etf_categories()
        >>> for c in cats[:3]:
        ...     print(c['category'])
    """
    categories = [
        {"category": "Equity", "description": "Stock market ETFs tracking equity indices",
         "screener_url": get_screener_url("equity")},
        {"category": "Fixed Income", "description": "Bond and fixed income ETFs",
         "screener_url": get_screener_url("bond")},
        {"category": "Commodity", "description": "Commodity tracking ETFs (gold, oil, etc.)",
         "screener_url": get_screener_url("commodity")},
        {"category": "Real Estate", "description": "REIT and real estate ETFs",
         "screener_url": get_screener_url("real-estate")},
        {"category": "Multi-Asset", "description": "Diversified multi-asset ETFs",
         "screener_url": get_screener_url("multi-asset")},
        {"category": "Currency", "description": "Currency and forex ETFs",
         "screener_url": get_screener_url("currency")},
        {"category": "Alternatives", "description": "Alternative strategy ETFs",
         "screener_url": get_screener_url("alternatives")},
    ]
    return categories


def check_etf_exists(ticker: str) -> bool:
    """
    Check if an ETF exists on TrackInsight.

    Args:
        ticker: ETF ticker symbol

    Returns:
        bool: True if the ETF has a page on TrackInsight

    Example:
        >>> check_etf_exists('SPY')
        True
        >>> check_etf_exists('ZZZZZ')
        False
    """
    meta = get_fund_metadata(ticker)
    return meta.get("has_page", False)


def get_fund_links(ticker: str) -> dict:
    """
    Get all useful TrackInsight links for a given ETF.

    Args:
        ticker: ETF ticker symbol

    Returns:
        dict with various TrackInsight page URLs for the ETF

    Example:
        >>> links = get_fund_links('SPY')
        >>> print(links['fund_page'])
        >>> print(links['compare_with_peers'])
    """
    ticker = ticker.upper()
    return {
        "ticker": ticker,
        "fund_page": get_fund_page_url(ticker),
        "compare_url": build_comparison_url([ticker]),
        "screener": get_screener_url(),
        "source": "trackinsight.com",
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "trackinsight_etf_api",
        "status": "active",
        "source": "https://www.trackinsight.com/en/api",
        "functions": [
            "get_user_location",
            "get_fund_page_url",
            "search_etfs_sitemap",
            "get_etf_universe",
            "get_fund_metadata",
            "get_available_fund_tickers",
            "build_comparison_url",
            "get_screener_url",
            "get_top_etf_categories",
            "check_etf_exists",
            "get_fund_links",
        ]
    }, indent=2))
