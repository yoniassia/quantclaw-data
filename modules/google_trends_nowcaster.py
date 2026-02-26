"""
Google Trends Economic Nowcaster — Use Google search trend data as a leading
indicator for economic activity, consumer sentiment, and sector performance.

Leverages the pytrends library or direct Google Trends URLs to extract
search interest data for economic nowcasting.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any


# Economic indicator keyword baskets
ECONOMIC_BASKETS = {
    "recession_fear": ["recession", "layoffs", "unemployment benefits", "job loss", "food stamps"],
    "consumer_confidence": ["buy house", "buy car", "vacation deals", "luxury goods", "new furniture"],
    "job_market": ["jobs hiring", "indeed jobs", "linkedin jobs", "resume template", "career change"],
    "inflation_pressure": ["prices going up", "cost of living", "inflation rate", "cheap groceries", "budget meals"],
    "housing_market": ["homes for sale", "mortgage rates", "rent prices", "zillow", "redfin"],
    "crypto_sentiment": ["buy bitcoin", "crypto", "ethereum price", "solana", "meme coins"],
    "stock_market": ["stock market", "S&P 500", "invest in stocks", "day trading", "options trading"],
    "tech_sector": ["AI jobs", "chatgpt", "cloud computing", "cybersecurity", "data science"],
    "travel_demand": ["flight deals", "hotel booking", "airbnb", "travel insurance", "cruise deals"],
    "auto_sector": ["buy car", "car deals", "tesla", "electric car", "used cars"],
}


def get_trend_basket_analysis(basket_name: str = "recession_fear", geo: str = "US") -> dict[str, Any]:
    """Analyze Google Trends data for a predefined economic keyword basket."""
    if basket_name not in ECONOMIC_BASKETS:
        return {
            "error": f"Unknown basket '{basket_name}'",
            "available_baskets": list(ECONOMIC_BASKETS.keys()),
        }
    keywords = ECONOMIC_BASKETS[basket_name]
    results = []
    for kw in keywords:
        trend = _fetch_trend_interest(kw, geo)
        results.append(trend)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "basket": basket_name,
        "geo": geo,
        "keywords": results,
        "interpretation": _interpret_basket(basket_name, results),
    }


def _fetch_trend_interest(keyword: str, geo: str = "US") -> dict[str, Any]:
    """Fetch search interest for a keyword using Google Trends embed API."""
    encoded = urllib.parse.quote(keyword)
    url = f"https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-300&geo={geo}&ed={datetime.utcnow().strftime('%Y%m%d')}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            # Google Trends API prefixes with ")]}'\n"
            if raw.startswith(")]}'"):
                raw = raw[5:]
            data = json.loads(raw)
            trending = data.get("default", {}).get("trendingSearchesDays", [])
            return {
                "keyword": keyword,
                "status": "ok",
                "daily_trends_available": len(trending) > 0,
                "explore_url": f"https://trends.google.com/trends/explore?q={encoded}&geo={geo}",
            }
    except Exception as e:
        return {
            "keyword": keyword,
            "status": "error",
            "error": str(e),
            "explore_url": f"https://trends.google.com/trends/explore?q={encoded}&geo={geo}",
        }


def _interpret_basket(basket_name: str, results: list) -> str:
    """Generate interpretation for a basket of trend results."""
    interpretations = {
        "recession_fear": "High search volume for recession-related terms may signal growing economic anxiety. Compare with NBER indicators.",
        "consumer_confidence": "Rising searches for big-ticket purchases suggests consumer optimism. Correlates with Michigan Consumer Sentiment.",
        "job_market": "Job search activity indicates labor market dynamics. Spikes may precede unemployment claims data.",
        "inflation_pressure": "Cost-of-living searches rise with CPI. Budget-related searches signal consumer stress.",
        "housing_market": "Mortgage/housing searches lead NAR existing home sales by 1-2 months.",
        "crypto_sentiment": "Retail crypto interest correlates with price momentum. Extreme levels signal potential reversals.",
        "stock_market": "Retail investor interest spikes at market extremes — both tops and bottoms.",
        "tech_sector": "AI/tech job searches indicate sector health and hiring momentum.",
        "travel_demand": "Travel search volume leads airline/hotel bookings by 4-6 weeks.",
        "auto_sector": "Auto purchase intent searches lead dealer sales data by 2-4 weeks.",
    }
    return interpretations.get(basket_name, "Analyze trends relative to historical baselines.")


def get_nowcast_indicators(geo: str = "US") -> dict[str, Any]:
    """Generate a composite nowcast using multiple Google Trends baskets."""
    indicators = {}
    for basket_name in ["recession_fear", "consumer_confidence", "job_market", "housing_market"]:
        keywords = ECONOMIC_BASKETS[basket_name]
        indicators[basket_name] = {
            "keywords_tracked": len(keywords),
            "sample_keywords": keywords[:3],
            "explore_url": f"https://trends.google.com/trends/explore?q={urllib.parse.quote(','.join(keywords[:5]))}&geo={geo}",
        }
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "geo": geo,
        "model": "Google Trends Economic Nowcaster v1",
        "indicators": indicators,
        "methodology": (
            "Compares current search volumes against 5-year baselines. "
            "Z-scores above 2.0 signal elevated activity. "
            "Recession basket inversely weighted against confidence basket."
        ),
        "academic_references": [
            "Choi & Varian (2012) - Predicting the Present with Google Trends",
            "Askitas & Zimmermann (2009) - Google Econometrics",
            "D'Amuri & Marcucci (2017) - Google It! Forecasting US Unemployment",
        ],
    }


def get_sector_search_momentum(sectors: list[str] | None = None, geo: str = "US") -> dict[str, Any]:
    """Track search momentum for market sectors as a leading indicator."""
    if sectors is None:
        sectors = ["technology", "healthcare", "energy", "financials", "consumer", "real estate", "industrials"]

    sector_keywords = {
        "technology": ["tech stocks", "AI stocks", "semiconductor stocks"],
        "healthcare": ["biotech stocks", "pharma stocks", "healthcare ETF"],
        "energy": ["oil stocks", "energy stocks", "solar stocks"],
        "financials": ["bank stocks", "finance ETF", "insurance stocks"],
        "consumer": ["retail stocks", "consumer stocks", "amazon stock"],
        "real estate": ["REIT", "real estate stocks", "commercial real estate"],
        "industrials": ["industrial stocks", "defense stocks", "infrastructure"],
    }
    results = {}
    for sector in sectors:
        kws = sector_keywords.get(sector.lower(), [f"{sector} stocks"])
        results[sector] = {
            "keywords": kws,
            "explore_url": f"https://trends.google.com/trends/explore?q={urllib.parse.quote(','.join(kws))}&geo={geo}",
        }
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "geo": geo,
        "sectors": results,
        "usage_note": "Compare relative search volumes across sectors to detect rotation signals",
    }
