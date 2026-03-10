#!/usr/bin/env python3
"""
VettaFi ETF Flows Feed — ETF Fund Flows, AUM & Sentiment

Data Sources:
  - ETF Trends RSS (VettaFi property) — ETF flow news & analysis articles
  - Yahoo Finance — ETF AUM, expense ratios, holdings counts
  - StockAnalysis.com — ETF overview data (price, AUM, holdings)

Update: Daily (RSS), Real-time (Yahoo Finance)
Free: Yes (no API key required)

Provides:
  - Latest ETF flow news from VettaFi/ETF Trends
  - ETF profile data (AUM, expense ratio, holdings, category)
  - Multi-ETF comparison for flow analysis
  - Top ETFs by AUM with category breakdown
  - AUM tracking for implied flow estimation

Usage:
  from modules.vettafi_etf_flows_feed import *
  news = get_etf_flow_news()
  profile = get_etf_profile("SPY")
  comparison = compare_etfs(["SPY", "QQQ", "IWM", "VTI"])
"""

import requests
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from html import unescape

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/vettafi_etf_flows")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ETF_TRENDS_RSS = "https://www.etftrends.com/feed/"

# Major ETF tickers by category for screening
MAJOR_ETFS = {
    "US Large Cap": ["SPY", "VOO", "IVV", "VTI", "QQQ"],
    "US Mid Cap": ["IJH", "VO", "MDY", "IWR"],
    "US Small Cap": ["IWM", "VB", "IJR", "SCHA"],
    "International Developed": ["EFA", "VEA", "IEFA", "SCHF"],
    "Emerging Markets": ["EEM", "VWO", "IEMG", "SCHE"],
    "US Bonds": ["AGG", "BND", "TLT", "SHY", "IEF", "LQD", "HYG"],
    "Sector - Technology": ["XLK", "VGT", "ARKK", "SMH"],
    "Sector - Healthcare": ["XLV", "VHT", "IBB", "XBI"],
    "Sector - Financials": ["XLF", "VFH", "KRE", "KBE"],
    "Sector - Energy": ["XLE", "VDE", "OIH", "XOP"],
    "Commodities": ["GLD", "SLV", "USO", "DBA", "DBC"],
    "Real Estate": ["VNQ", "IYR", "XLRE", "RWR"],
    "Crypto": ["IBIT", "FBTC", "BITO", "ETHE"],
}


def _read_cache(name: str, max_age_hours: int = 6) -> Optional[dict]:
    """Read from cache if fresh enough."""
    cache_file = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=max_age_hours):
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    return None


def _write_cache(name: str, data: dict):
    """Write data to cache."""
    cache_file = os.path.join(CACHE_DIR, f"{name}.json")
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except IOError:
        pass


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    clean = re.sub(r"<[^>]+>", "", text)
    return unescape(clean).strip()


def get_etf_flow_news(limit: int = 20) -> List[Dict]:
    """
    Fetch latest ETF news from VettaFi's ETF Trends RSS feed.
    Includes flow-related articles, market commentary, and ETF analysis.

    Args:
        limit: Maximum number of articles to return (default 20)

    Returns:
        List of dicts with keys: title, link, author, date, summary, categories
    """
    cached = _read_cache("etf_flow_news", max_age_hours=2)
    if cached:
        return cached[:limit]

    try:
        response = requests.get(ETF_TRENDS_RSS, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch ETF Trends RSS: {e}")

    root = ET.fromstring(response.text)
    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        author_el = item.find("{http://purl.org/dc/elements/1.1/}creator")
        author = author_el.text if author_el is not None else ""
        pub_date = item.findtext("pubDate", "")
        description = _strip_html(item.findtext("description", ""))
        categories = [cat.text for cat in item.findall("category") if cat.text]

        articles.append({
            "title": title,
            "link": link,
            "author": author,
            "date": pub_date,
            "summary": description,
            "categories": categories,
        })

    _write_cache("etf_flow_news", articles)
    return articles[:limit]


def get_etf_flow_news_filtered(keywords: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
    """
    Fetch ETF news filtered by keywords (e.g., 'flows', 'inflows', 'outflows').

    Args:
        keywords: List of keywords to filter by (default: flow-related terms)
        limit: Maximum results

    Returns:
        Filtered list of ETF news articles
    """
    if keywords is None:
        keywords = ["flow", "inflow", "outflow", "AUM", "assets", "rotation",
                     "fund flow", "money flow", "capital flow", "redemption"]

    articles = get_etf_flow_news(limit=50)
    filtered = []
    for article in articles:
        text = f"{article['title']} {article['summary']}".lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append(article)
        if len(filtered) >= limit:
            break

    return filtered


def get_etf_profile(ticker: str) -> Dict:
    """
    Get ETF profile data including AUM, expense ratio, holdings, category.
    Uses Yahoo Finance as the data source.

    Args:
        ticker: ETF ticker symbol (e.g., 'SPY', 'QQQ')

    Returns:
        Dict with: ticker, name, aum, expense_ratio, holdings_count,
                   category, fund_family, inception_date, price, volume,
                   ytd_return, dividend_yield, pe_ratio, beta
    """
    cache_key = f"etf_profile_{ticker.upper()}"
    cached = _read_cache(cache_key, max_age_hours=12)
    if cached:
        return cached

    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance required: pip install yfinance")

    try:
        etf = yf.Ticker(ticker.upper())
        info = etf.info

        if not info or info.get("quoteType") not in ("ETF", None):
            # Some ETFs may not have quoteType set properly
            pass

        profile = {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName", ""),
            "aum": info.get("totalAssets"),
            "aum_formatted": _format_number(info.get("totalAssets")),
            "expense_ratio": info.get("annualReportExpenseRatio"),
            "holdings_count": info.get("holdings"),  # May not always be available
            "category": info.get("category", ""),
            "fund_family": info.get("fundFamily", ""),
            "inception_date": info.get("fundInceptionDate"),
            "price": info.get("previousClose") or info.get("regularMarketPrice"),
            "currency": info.get("currency", "USD"),
            "volume": info.get("averageVolume"),
            "volume_10d": info.get("averageDailyVolume10Day"),
            "ytd_return": info.get("ytdReturn"),
            "three_year_return": info.get("threeYearAverageReturn"),
            "five_year_return": info.get("fiveYearAverageReturn"),
            "dividend_yield": info.get("yield"),
            "pe_ratio": info.get("trailingPE"),
            "beta": info.get("beta3Year"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "exchange": info.get("exchange", ""),
            "fetched_at": datetime.now().isoformat(),
        }

        _write_cache(cache_key, profile)
        return profile

    except Exception as e:
        raise RuntimeError(f"Failed to fetch ETF profile for {ticker}: {e}")


def compare_etfs(tickers: List[str]) -> List[Dict]:
    """
    Compare multiple ETFs side by side (AUM, expense ratio, returns, etc.).

    Args:
        tickers: List of ETF ticker symbols

    Returns:
        List of ETF profile dicts, sorted by AUM descending
    """
    results = []
    for ticker in tickers:
        try:
            profile = get_etf_profile(ticker)
            results.append(profile)
        except Exception as e:
            results.append({
                "ticker": ticker.upper(),
                "error": str(e),
            })

    # Sort by AUM descending (None values last)
    results.sort(key=lambda x: x.get("aum") or 0, reverse=True)
    return results


def get_top_etfs_by_category(category: Optional[str] = None) -> Dict:
    """
    Get major ETFs organized by category with AUM data.
    If category is specified, returns only that category.

    Args:
        category: Optional category name (e.g., 'US Large Cap', 'Sector - Technology')
                  If None, returns all categories.

    Returns:
        Dict with category names as keys, lists of ETF profiles as values.
        Includes a 'categories' key listing available categories.
    """
    if category and category not in MAJOR_ETFS:
        # Try fuzzy match
        matches = [k for k in MAJOR_ETFS if category.lower() in k.lower()]
        if matches:
            category = matches[0]
        else:
            return {
                "error": f"Unknown category: {category}",
                "categories": list(MAJOR_ETFS.keys()),
            }

    categories_to_fetch = {category: MAJOR_ETFS[category]} if category else MAJOR_ETFS
    result = {"categories": list(MAJOR_ETFS.keys())}

    for cat_name, tickers in categories_to_fetch.items():
        etfs = compare_etfs(tickers)
        result[cat_name] = etfs

    return result


def get_etf_aum_history(ticker: str, period: str = "1y") -> Dict:
    """
    Get ETF price and volume history to estimate AUM changes over time.
    AUM changes + volume spikes indicate fund flow activity.

    Args:
        ticker: ETF ticker symbol
        period: History period ('1mo', '3mo', '6mo', '1y', '2y', '5y')

    Returns:
        Dict with: ticker, current_aum, history (list of date/price/volume records),
                   price_change_pct, volume_trend
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance required: pip install yfinance")

    try:
        etf = yf.Ticker(ticker.upper())
        hist = etf.history(period=period)
        info = etf.info

        if hist.empty:
            return {"ticker": ticker.upper(), "error": "No history data available"}

        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
            })

        first_close = records[0]["close"] if records else 0
        last_close = records[-1]["close"] if records else 0
        price_change_pct = round(((last_close - first_close) / first_close) * 100, 2) if first_close else 0

        avg_volume_first_20 = sum(r["volume"] for r in records[:20]) / min(len(records), 20) if records else 0
        avg_volume_last_20 = sum(r["volume"] for r in records[-20:]) / min(len(records), 20) if records else 0
        volume_trend = "increasing" if avg_volume_last_20 > avg_volume_first_20 * 1.1 else \
                       "decreasing" if avg_volume_last_20 < avg_volume_first_20 * 0.9 else "stable"

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", ""),
            "current_aum": info.get("totalAssets"),
            "current_aum_formatted": _format_number(info.get("totalAssets")),
            "period": period,
            "price_change_pct": price_change_pct,
            "volume_trend": volume_trend,
            "avg_volume_recent": int(avg_volume_last_20),
            "data_points": len(records),
            "history": records,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to fetch AUM history for {ticker}: {e}")


def get_sector_rotation_signals() -> Dict:
    """
    Analyze sector ETF volume and price changes to detect rotation signals.
    Compares recent performance of sector ETFs to identify money flow patterns.

    Returns:
        Dict with sector analysis including performance, volume changes, and signals.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance required: pip install yfinance")

    sectors = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC",
    }

    results = []
    for sector_name, ticker in sectors.items():
        try:
            etf = yf.Ticker(ticker)
            hist_1m = etf.history(period="1mo")
            hist_3m = etf.history(period="3mo")

            if hist_1m.empty or hist_3m.empty:
                continue

            # 1-month return
            first_1m = hist_1m["Close"].iloc[0]
            last_1m = hist_1m["Close"].iloc[-1]
            return_1m = round(((last_1m - first_1m) / first_1m) * 100, 2)

            # 3-month return
            first_3m = hist_3m["Close"].iloc[0]
            last_3m = hist_3m["Close"].iloc[-1]
            return_3m = round(((last_3m - first_3m) / first_3m) * 100, 2)

            # Volume trend (last 5 days vs 20-day avg)
            recent_vol = hist_1m["Volume"].iloc[-5:].mean()
            avg_vol = hist_1m["Volume"].mean()
            vol_ratio = round(recent_vol / avg_vol, 2) if avg_vol > 0 else 1.0

            results.append({
                "sector": sector_name,
                "ticker": ticker,
                "return_1m_pct": return_1m,
                "return_3m_pct": return_3m,
                "volume_ratio": vol_ratio,
                "signal": "inflow" if return_1m > 2 and vol_ratio > 1.1 else
                          "outflow" if return_1m < -2 and vol_ratio > 1.1 else
                          "neutral",
                "price": round(last_1m, 2),
            })
        except Exception:
            continue

    # Sort by 1-month return
    results.sort(key=lambda x: x["return_1m_pct"], reverse=True)

    # Identify strongest signals
    inflows = [r for r in results if r["signal"] == "inflow"]
    outflows = [r for r in results if r["signal"] == "outflow"]

    return {
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "sectors": results,
        "inflow_sectors": [r["sector"] for r in inflows],
        "outflow_sectors": [r["sector"] for r in outflows],
        "top_performer": results[0] if results else None,
        "worst_performer": results[-1] if results else None,
        "rotation_summary": f"Money flowing into: {', '.join(r['sector'] for r in inflows) or 'None detected'}. "
                           f"Flowing out of: {', '.join(r['sector'] for r in outflows) or 'None detected'}.",
    }


def _format_number(value) -> str:
    """Format large numbers with B/M/K suffixes."""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"


def fetch_data() -> Dict:
    """
    Fetch combined ETF flow data: news + top ETF profiles.
    Main entry point for the module.

    Returns:
        Dict with 'news', 'top_etfs', and 'timestamp'.
    """
    news = get_etf_flow_news(limit=10)
    flow_news = get_etf_flow_news_filtered(limit=5)

    # Get profiles for a handful of major ETFs
    major_tickers = ["SPY", "QQQ", "IWM", "VTI", "AGG", "GLD"]
    profiles = compare_etfs(major_tickers)

    return {
        "module": "vettafi_etf_flows_feed",
        "timestamp": datetime.now().isoformat(),
        "latest_news": news,
        "flow_specific_news": flow_news,
        "major_etf_profiles": profiles,
    }


def get_latest() -> Dict:
    """
    Get latest data summary: recent flow news + top ETF stats.

    Returns:
        Dict with latest ETF flow news and key ETF statistics.
    """
    news = get_etf_flow_news(limit=5)
    spy = get_etf_profile("SPY")

    return {
        "module": "vettafi_etf_flows_feed",
        "timestamp": datetime.now().isoformat(),
        "latest_news_count": len(news),
        "latest_headlines": [n["title"] for n in news],
        "spy_aum": spy.get("aum_formatted"),
        "spy_price": spy.get("price"),
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "vettafi_etf_flows_feed",
        "status": "active",
        "source": "VettaFi ETF Trends + Yahoo Finance",
        "functions": [
            "get_etf_flow_news",
            "get_etf_flow_news_filtered",
            "get_etf_profile",
            "compare_etfs",
            "get_top_etfs_by_category",
            "get_etf_aum_history",
            "get_sector_rotation_signals",
            "fetch_data",
            "get_latest",
        ],
    }, indent=2))
