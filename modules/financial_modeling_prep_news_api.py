"""
Financial Modeling Prep (FMP) News API

Company-specific financial news with sentiment analysis from FMP.
Covers stock market news, earnings reports, regulatory filings, and press releases.

Source: https://financialmodelingprep.com/developer/docs/company-news-api
Update frequency: Real-time / daily
Category: News & NLP
Free tier: 250 calls/day with API key (get free at financialmodelingprep.com)
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


API_BASE = "https://financialmodelingprep.com/api/v3"
API_V4_BASE = "https://financialmodelingprep.com/api/v4"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/fmp_news")
os.makedirs(CACHE_DIR, exist_ok=True)


def _get_api_key() -> Optional[str]:
    """Get FMP API key from environment."""
    return os.environ.get("FMP_API_KEY")


def _make_request(url: str, params: dict = None) -> Any:
    """
    Make authenticated request to FMP API.

    Args:
        url: Full API URL
        params: Optional query parameters

    Returns:
        Parsed JSON response or error dict
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "FMP_API_KEY not set. Get free key at https://site.financialmodelingprep.com/developer/docs",
            "free_tier": "250 calls/day"
        }

    params = params or {}
    params["apikey"] = api_key

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "Error Message" in data:
            return {"error": data["Error Message"]}

        return data if data else {"error": "No data returned"}

    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}


def get_stock_news(
    tickers: str = "",
    limit: int = 50,
    from_date: str = "",
    to_date: str = ""
) -> List[Dict[str, Any]]:
    """
    Get stock news articles, optionally filtered by ticker(s).

    Args:
        tickers: Comma-separated ticker symbols (e.g. "AAPL,TSLA"). Empty = general news.
        limit: Number of articles to return (max 50 on free tier)
        from_date: Start date filter (YYYY-MM-DD)
        to_date: End date filter (YYYY-MM-DD)

    Returns:
        List of news articles with title, text, url, image, publishedDate, site, symbol, etc.

    Example:
        >>> articles = get_stock_news("AAPL", limit=5)
        >>> print(articles[0]["title"])
    """
    params = {"limit": min(limit, 50)}

    if tickers:
        params["tickers"] = tickers.upper()
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    return _make_request(f"{API_BASE}/stock_news", params)


def get_general_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get general financial/market news (not ticker-specific).

    Args:
        limit: Number of articles (max 50)

    Returns:
        List of general news articles
    """
    return _make_request(f"{API_BASE}/fmp/articles", {"page": 0, "size": min(limit, 50)})


def get_press_releases(symbol: str, limit: int = 25) -> List[Dict[str, Any]]:
    """
    Get press releases for a specific company.

    Args:
        symbol: Stock ticker (e.g. "AAPL")
        limit: Number of press releases to return

    Returns:
        List of press releases with date, title, and text
    """
    return _make_request(f"{API_BASE}/press-releases/{symbol.upper()}", {"limit": limit})


def get_stock_news_sentiments(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get stock news with pre-computed sentiment scores.

    Args:
        limit: Number of articles

    Returns:
        List of news articles with sentiment field (positive/negative/neutral + score)
    """
    return _make_request(f"{API_BASE}/stock-news-sentiments-rss-feed", {"limit": min(limit, 50)})


def get_forex_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get forex/currency market news.

    Args:
        limit: Number of articles

    Returns:
        List of forex news articles
    """
    return _make_request(f"{API_BASE}/fmp/articles", {"page": 0, "size": min(limit, 50)})


def get_crypto_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get cryptocurrency market news.

    Args:
        limit: Number of articles

    Returns:
        List of crypto news articles
    """
    return _make_request(f"{API_BASE}/fmp/articles", {"page": 0, "size": min(limit, 50)})


def search_news(
    query: str,
    tickers: str = "",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search news articles by keyword and/or ticker.

    Args:
        query: Search keyword(s)
        tickers: Optional comma-separated tickers to filter
        limit: Number of results

    Returns:
        List of matching news articles

    Example:
        >>> results = search_news("earnings beat", tickers="TSLA")
    """
    # FMP stock_news endpoint supports ticker filtering; we filter by keyword client-side
    articles = get_stock_news(tickers=tickers, limit=limit)

    if isinstance(articles, dict) and "error" in articles:
        return articles

    if isinstance(articles, list) and query:
        query_lower = query.lower()
        filtered = [
            a for a in articles
            if query_lower in (a.get("title", "") + " " + a.get("text", "")).lower()
        ]
        return filtered

    return articles


def get_news_summary(symbol: str, days: int = 7, limit: int = 20) -> Dict[str, Any]:
    """
    Get a summary of recent news for a symbol including count and sentiment breakdown.

    Args:
        symbol: Stock ticker (e.g. "AAPL")
        days: Look back this many days
        limit: Max articles to fetch

    Returns:
        Dict with total_articles, date_range, articles list, and basic stats

    Example:
        >>> summary = get_news_summary("AAPL", days=3)
        >>> print(f"Found {summary['total_articles']} articles")
    """
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    articles = get_stock_news(
        tickers=symbol.upper(),
        limit=limit,
        from_date=from_date,
        to_date=to_date
    )

    if isinstance(articles, dict) and "error" in articles:
        return articles

    if not isinstance(articles, list):
        return {"error": "Unexpected response format", "raw": articles}

    # Extract unique sources
    sources = list(set(a.get("site", "unknown") for a in articles))

    return {
        "symbol": symbol.upper(),
        "total_articles": len(articles),
        "date_range": {"from": from_date, "to": to_date},
        "sources": sources,
        "source_count": len(sources),
        "articles": articles
    }


def get_latest(symbol: str = "AAPL") -> Dict[str, Any]:
    """
    Get the latest single news article for a symbol.
    Quick convenience function.

    Args:
        symbol: Stock ticker

    Returns:
        Dict with the most recent article or error
    """
    articles = get_stock_news(tickers=symbol.upper(), limit=1)

    if isinstance(articles, dict) and "error" in articles:
        return articles

    if isinstance(articles, list) and len(articles) > 0:
        return articles[0]

    return {"error": "No news found", "symbol": symbol}


def fetch_data(symbol: str = "AAPL", limit: int = 50) -> List[Dict[str, Any]]:
    """
    Standard fetch_data interface for QuantClaw Data compatibility.

    Args:
        symbol: Stock ticker
        limit: Number of articles

    Returns:
        List of news articles
    """
    return get_stock_news(tickers=symbol.upper(), limit=limit)


if __name__ == "__main__":
    print(json.dumps({
        "module": "financial_modeling_prep_news_api",
        "status": "active",
        "source": "https://financialmodelingprep.com/developer/docs/company-news-api",
        "functions": [
            "get_stock_news", "get_general_news", "get_press_releases",
            "get_stock_news_sentiments", "get_forex_news", "get_crypto_news",
            "search_news", "get_news_summary", "get_latest", "fetch_data"
        ]
    }, indent=2))
