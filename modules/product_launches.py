#!/usr/bin/env python3
"""
Product Launch Tracker Module — Social Buzz, Pre-Order Velocity, Review Sentiment

Data Sources:
- Google Trends API (pytrends): Search interest over time, related queries (free)
- Reddit API (PRAW): Product mentions, sentiment, engagement (free)
- News RSS Feeds: Launch announcements, media coverage (free)
- Product Hunt API: Tech product launches, upvotes, comments (free)

Author: QUANTCLAW DATA Build Agent
Phase: 50
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
import re
from collections import defaultdict

# Try importing optional dependencies
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

# API Configuration
PRODUCTHUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"
NEWS_API_URL = "https://newsapi.org/v2/everything"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Product categories for trending analysis
PRODUCT_CATEGORIES = {
    "tech": ["iPhone", "Samsung Galaxy", "PlayStation", "Xbox", "Apple Watch", "AirPods"],
    "automotive": ["Tesla Model", "Ford F-150", "Toyota Camry", "BMW", "Mercedes"],
    "consumer": ["Nike Air", "Adidas", "Lululemon", "Peloton"],
    "entertainment": ["Marvel", "Star Wars", "Nintendo Switch"]
}


def get_google_trends_buzz(product_name: str, timeframe: str = "today 3-m") -> Dict[str, Any]:
    """
    Track search interest over time using Google Trends
    
    Args:
        product_name: Product name to track (e.g., "iPhone 16", "Tesla Cybertruck")
        timeframe: Time range ('today 3-m', 'today 12-m', 'today 5-y')
    
    Returns:
        Dict with interest_over_time, related_queries, peak_interest
    """
    if not PYTRENDS_AVAILABLE:
        return {
            "error": "pytrends not installed. Run: pip install pytrends",
            "install_command": "pip install pytrends"
        }
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Build payload
        pytrends.build_payload([product_name], timeframe=timeframe)
        
        # Interest over time
        interest_df = pytrends.interest_over_time()
        
        if interest_df.empty:
            return {
                "product": product_name,
                "error": "No trend data available for this product",
                "suggestion": "Try a more popular product name or different timeframe"
            }
        
        # Convert to dict
        interest_data = interest_df[product_name].to_dict()
        interest_list = [
            {"date": str(date.date()), "interest": int(value)}
            for date, value in interest_data.items()
            if date != "isPartial"
        ]
        
        # Calculate buzz metrics
        recent_interest = [x["interest"] for x in interest_list[-7:]]  # Last 7 days
        avg_interest = sum(recent_interest) / len(recent_interest) if recent_interest else 0
        peak_interest = max([x["interest"] for x in interest_list])
        
        # Get related queries
        related_queries = pytrends.related_queries()
        
        top_queries = []
        if product_name in related_queries and related_queries[product_name]['top'] is not None:
            top_df = related_queries[product_name]['top']
            top_queries = [
                {"query": row['query'], "value": int(row['value'])}
                for _, row in top_df.head(10).iterrows()
            ]
        
        rising_queries = []
        if product_name in related_queries and related_queries[product_name]['rising'] is not None:
            rising_df = related_queries[product_name]['rising']
            rising_queries = [
                {"query": row['query'], "value": row['value']}
                for _, row in rising_df.head(5).iterrows()
            ]
        
        return {
            "product": product_name,
            "timeframe": timeframe,
            "interest_over_time": interest_list,
            "current_avg_interest": round(avg_interest, 1),
            "peak_interest": peak_interest,
            "top_related_queries": top_queries,
            "rising_queries": rising_queries,
            "buzz_score": round((avg_interest / peak_interest * 100) if peak_interest > 0 else 0, 1),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_reddit_sentiment(product_name: str, subreddit: str = "all", limit: int = 100) -> Dict[str, Any]:
    """
    Analyze Reddit mentions and sentiment for a product
    
    Args:
        product_name: Product to search for
        subreddit: Subreddit to search (default: all)
        limit: Max number of posts to analyze
    
    Returns:
        Dict with post count, sentiment, top posts
    """
    if not PRAW_AVAILABLE:
        # Fallback to Reddit JSON API (no auth required)
        try:
            search_url = f"https://www.reddit.com/search.json"
            params = {
                "q": product_name,
                "limit": min(limit, 100),
                "sort": "new",
                "t": "month"
            }
            
            headers = {"User-Agent": "QuantClaw/1.0"}
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            if not posts:
                return {
                    "product": product_name,
                    "subreddit": subreddit,
                    "total_mentions": 0,
                    "message": "No recent mentions found",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Simple sentiment analysis based on score and text
            positive_keywords = ['great', 'amazing', 'love', 'excellent', 'best', 'awesome', 'perfect']
            negative_keywords = ['bad', 'terrible', 'hate', 'worst', 'awful', 'disappointing', 'sucks']
            
            sentiment_scores = []
            top_posts = []
            
            for post in posts[:limit]:
                post_data = post.get("data", {})
                title = post_data.get("title", "").lower()
                score = post_data.get("score", 0)
                
                # Sentiment scoring
                sentiment = 0
                for word in positive_keywords:
                    if word in title:
                        sentiment += 1
                for word in negative_keywords:
                    if word in title:
                        sentiment -= 1
                
                # Weight by Reddit score
                weighted_sentiment = sentiment * (1 + score / 100)
                sentiment_scores.append(weighted_sentiment)
                
                if len(top_posts) < 10:
                    top_posts.append({
                        "title": post_data.get("title"),
                        "score": score,
                        "subreddit": post_data.get("subreddit"),
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                        "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat(),
                        "num_comments": post_data.get("num_comments", 0)
                    })
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            sentiment_label = "Neutral"
            if avg_sentiment > 0.5:
                sentiment_label = "Positive"
            elif avg_sentiment < -0.5:
                sentiment_label = "Negative"
            
            return {
                "product": product_name,
                "subreddit": subreddit,
                "total_mentions": len(posts),
                "analyzed_posts": len(sentiment_scores),
                "average_sentiment": round(avg_sentiment, 2),
                "sentiment_label": sentiment_label,
                "top_posts": top_posts,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "product": product_name,
                "error": str(e),
                "suggestion": "Install PRAW for better Reddit analysis: pip install praw",
                "timestamp": datetime.now().isoformat()
            }
    
    # PRAW version (if available)
    try:
        # Note: Requires Reddit API credentials in environment or config
        reddit = praw.Reddit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            user_agent="QuantClaw Product Launch Tracker 1.0"
        )
        
        # Search for product mentions
        submissions = reddit.subreddit(subreddit).search(product_name, limit=limit, time_filter="month")
        
        # Analyze sentiment and engagement
        # (Similar logic to fallback version)
        
        return {
            "product": product_name,
            "note": "PRAW implementation - requires API credentials",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_news_coverage(product_name: str, days: int = 30) -> Dict[str, Any]:
    """
    Fetch news articles about product launches via Google News RSS
    
    Args:
        product_name: Product to search for
        days: Number of days to look back
    
    Returns:
        Dict with article count, headlines, sources
    """
    try:
        # Use Google News RSS (free, no API key required)
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Construct RSS URL
        search_query = product_name.replace(" ", "+")
        rss_url = f"{GOOGLE_NEWS_RSS}?q={search_query}+launch+OR+release+when:{days}d&hl=en-US&gl=US&ceid=US:en"
        
        headers = {"User-Agent": "Mozilla/5.0 (compatible; QuantClaw/1.0)"}
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse RSS XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        articles = []
        for item in root.findall(".//item")[:20]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            source = item.find("source")
            
            if title is not None:
                articles.append({
                    "title": title.text,
                    "url": link.text if link is not None else "",
                    "published": pub_date.text if pub_date is not None else "",
                    "source": source.text if source is not None else "Unknown"
                })
        
        # Analyze media coverage velocity
        if articles:
            # Count by source
            source_counts = defaultdict(int)
            for article in articles:
                source_counts[article["source"]] += 1
            
            top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "product": product_name,
                "days_searched": days,
                "total_articles": len(articles),
                "articles": articles,
                "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
                "coverage_velocity": round(len(articles) / days, 2),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "product": product_name,
                "days_searched": days,
                "total_articles": 0,
                "message": "No news coverage found",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_producthunt_data(product_name: str) -> Dict[str, Any]:
    """
    Fetch Product Hunt launch data (tech products)
    
    Args:
        product_name: Product to search for on Product Hunt
    
    Returns:
        Dict with upvotes, comments, maker info
    """
    try:
        # Product Hunt API v2 (GraphQL)
        # Note: Requires API token from https://www.producthunt.com/v2/oauth/applications
        
        # For now, use public endpoints or web scraping fallback
        search_url = f"https://www.producthunt.com/search?q={product_name.replace(' ', '+')}"
        
        headers = {"User-Agent": "Mozilla/5.0 (compatible; QuantClaw/1.0)"}
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Simple parsing (would need BeautifulSoup for production)
            content = response.text
            
            return {
                "product": product_name,
                "source": "Product Hunt",
                "note": "Full API implementation requires Product Hunt API token",
                "search_url": search_url,
                "status": "partial_data",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "product": product_name,
                "error": f"HTTP {response.status_code}",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_launch_summary(product_name: str) -> Dict[str, Any]:
    """
    Comprehensive product launch analysis combining all data sources
    
    Args:
        product_name: Product to analyze
    
    Returns:
        Dict with buzz score, sentiment, media coverage, trending status
    """
    try:
        results = {
            "product": product_name,
            "analysis_date": datetime.now().isoformat(),
            "data_sources": []
        }
        
        # Google Trends buzz
        print(f"Fetching Google Trends data for {product_name}...", file=sys.stderr)
        trends = get_google_trends_buzz(product_name)
        if "error" not in trends:
            results["google_trends"] = {
                "current_buzz": trends.get("current_avg_interest", 0),
                "peak_buzz": trends.get("peak_interest", 0),
                "buzz_score": trends.get("buzz_score", 0),
                "trending_queries": trends.get("top_related_queries", [])[:5]
            }
            results["data_sources"].append("Google Trends")
        else:
            results["google_trends"] = {"status": "unavailable", "reason": trends.get("error")}
        
        # Reddit sentiment
        print(f"Analyzing Reddit sentiment for {product_name}...", file=sys.stderr)
        reddit = get_reddit_sentiment(product_name)
        if "error" not in reddit:
            results["reddit_sentiment"] = {
                "total_mentions": reddit.get("total_mentions", 0),
                "sentiment": reddit.get("sentiment_label", "Neutral"),
                "sentiment_score": reddit.get("average_sentiment", 0),
                "top_discussions": reddit.get("top_posts", [])[:3]
            }
            results["data_sources"].append("Reddit")
        else:
            results["reddit_sentiment"] = {"status": "unavailable", "reason": reddit.get("error")}
        
        # News coverage
        print(f"Fetching news coverage for {product_name}...", file=sys.stderr)
        news = get_news_coverage(product_name)
        if "error" not in news:
            results["news_coverage"] = {
                "total_articles": news.get("total_articles", 0),
                "coverage_velocity": news.get("coverage_velocity", 0),
                "top_sources": news.get("top_sources", []),
                "recent_headlines": [a["title"] for a in news.get("articles", [])[:5]]
            }
            results["data_sources"].append("Google News")
        else:
            results["news_coverage"] = {"status": "unavailable", "reason": news.get("error")}
        
        # Calculate composite launch score
        buzz_score = results.get("google_trends", {}).get("buzz_score", 0)
        mentions = results.get("reddit_sentiment", {}).get("total_mentions", 0)
        articles = results.get("news_coverage", {}).get("total_articles", 0)
        
        # Composite score (0-100)
        composite_score = (buzz_score * 0.4) + (min(mentions / 10, 10) * 4) + (min(articles / 5, 10) * 2)
        
        results["composite_launch_score"] = round(composite_score, 1)
        results["launch_strength"] = (
            "Very Strong" if composite_score >= 75 else
            "Strong" if composite_score >= 50 else
            "Moderate" if composite_score >= 25 else
            "Weak"
        )
        
        return results
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def track_preorder_velocity(product_name: str, ticker: Optional[str] = None) -> Dict[str, Any]:
    """
    Estimate pre-order velocity using search trends as proxy
    
    Args:
        product_name: Product name
        ticker: Optional stock ticker to correlate with stock movement
    
    Returns:
        Dict with velocity metrics, trend direction
    """
    if not PYTRENDS_AVAILABLE:
        return {
            "error": "pytrends not installed. Run: pip install pytrends"
        }
    
    try:
        # Get hourly trends if available, otherwise daily
        trends = get_google_trends_buzz(product_name, timeframe="now 7-d")
        
        if "error" in trends:
            return trends
        
        interest_data = trends.get("interest_over_time", [])
        if len(interest_data) < 2:
            return {
                "product": product_name,
                "error": "Insufficient data for velocity calculation"
            }
        
        # Calculate velocity (change over time)
        recent_values = [x["interest"] for x in interest_data[-7:]]
        previous_values = [x["interest"] for x in interest_data[-14:-7]]
        
        recent_avg = sum(recent_values) / len(recent_values) if recent_values else 0
        previous_avg = sum(previous_values) / len(previous_values) if previous_values else 0
        
        velocity = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        
        return {
            "product": product_name,
            "pre_order_velocity": round(velocity, 1),
            "trend_direction": "Accelerating" if velocity > 10 else "Stable" if velocity > -10 else "Declining",
            "recent_avg_interest": round(recent_avg, 1),
            "previous_avg_interest": round(previous_avg, 1),
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "product": product_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_trending_products(category: str = "tech") -> Dict[str, Any]:
    """
    Get currently trending products in a category
    
    Args:
        category: Product category (tech, automotive, consumer, entertainment)
    
    Returns:
        Dict with trending products and their buzz scores
    """
    if category not in PRODUCT_CATEGORIES:
        return {
            "error": f"Unknown category: {category}",
            "available_categories": list(PRODUCT_CATEGORIES.keys())
        }
    
    products = PRODUCT_CATEGORIES[category]
    trending = []
    
    for product in products:
        print(f"Analyzing {product}...", file=sys.stderr)
        buzz = get_google_trends_buzz(product, timeframe="today 1-m")
        
        if "error" not in buzz:
            trending.append({
                "product": product,
                "buzz_score": buzz.get("buzz_score", 0),
                "current_interest": buzz.get("current_avg_interest", 0)
            })
    
    # Sort by buzz score
    trending.sort(key=lambda x: x["buzz_score"], reverse=True)
    
    return {
        "category": category,
        "trending_products": trending,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """CLI Entry Point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command provided",
            "usage": "python product_launches.py <command> [args]",
            "commands": [
                "launch-summary <product_name>",
                "buzz-tracking <product_name>",
                "reddit-sentiment <product_name>",
                "news-coverage <product_name>",
                "preorder-velocity <product_name>",
                "trending-products <category>"
            ]
        }))
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == "launch-summary":
            if len(sys.argv) < 3:
                result = {"error": "Product name required"}
            else:
                product_name = " ".join(sys.argv[2:])
                result = get_launch_summary(product_name)
        
        elif command == "buzz-tracking":
            if len(sys.argv) < 3:
                result = {"error": "Product name required"}
            else:
                product_name = " ".join(sys.argv[2:])
                result = get_google_trends_buzz(product_name)
        
        elif command == "reddit-sentiment":
            if len(sys.argv) < 3:
                result = {"error": "Product name required"}
            else:
                product_name = " ".join(sys.argv[2:])
                result = get_reddit_sentiment(product_name)
        
        elif command == "news-coverage":
            if len(sys.argv) < 3:
                result = {"error": "Product name required"}
            else:
                product_name = " ".join(sys.argv[2:])
                result = get_news_coverage(product_name)
        
        elif command == "preorder-velocity":
            if len(sys.argv) < 3:
                result = {"error": "Product name required"}
            else:
                product_name = " ".join(sys.argv[2:])
                result = track_preorder_velocity(product_name)
        
        elif command == "trending-products":
            category = sys.argv[2] if len(sys.argv) > 2 else "tech"
            result = get_trending_products(category)
        
        else:
            result = {"error": f"Unknown command: {command}"}
        
        print(json.dumps(result, indent=2))
        return 0
    
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
