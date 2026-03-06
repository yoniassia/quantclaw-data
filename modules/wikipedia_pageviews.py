#!/usr/bin/env python3
"""
Wikipedia Pageviews — Attention Proxy
======================================
Track page views for company/topic Wikipedia articles as an attention/interest proxy.
Spikes in Wikipedia views often precede or coincide with major stock moves.

Data points: Daily/hourly pageviews per article, project, agent type
Update frequency: Daily (1-2 day lag)
No API key required, completely free, generous rate limits.

Source: https://wikimedia.org/api/rest_v1/
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
from typing import Optional, Dict, List
from functools import lru_cache

BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
PROJECT = "en.wikipedia"
ACCESS = "all-access"
AGENT = "all-agents"
GRANULARITY = "daily"


@lru_cache(maxsize=256)
def get_pageviews(
    article: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: int = 30
) -> pd.DataFrame:
    """
    Fetch Wikipedia pageview data for an article.
    
    Args:
        article: Article title (e.g., 'Apple_Inc' or 'Tesla,_Inc.')
        start_date: Start date in YYYYMMDD format (optional)
        end_date: End date in YYYYMMDD format (optional)
        days: Number of days to fetch if dates not specified (default 30)
        
    Returns:
        DataFrame with columns: date, article, views, project
    """
    try:
        # Calculate date range if not provided
        if not end_date:
            end = datetime.now() - timedelta(days=2)  # API has 1-2 day lag
            end_date = end.strftime("%Y%m%d")
        
        if not start_date:
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            start = end_dt - timedelta(days=days)
            start_date = start.strftime("%Y%m%d")
        
        # Clean article name (replace spaces with underscores)
        article_clean = article.replace(' ', '_')
        
        # Build API URL
        url = f"{BASE_URL}/{PROJECT}/{ACCESS}/{AGENT}/{article_clean}/{GRANULARITY}/{start_date}/{end_date}"
        
        headers = {
            'User-Agent': 'QuantClawData/1.0 (https://github.com/quantclaw)'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return pd.DataFrame(columns=['date', 'article', 'views', 'project'])
        
        data = response.json()
        
        if 'items' not in data:
            return pd.DataFrame(columns=['date', 'article', 'views', 'project'])
        
        # Parse response into DataFrame
        rows = []
        for item in data['items']:
            timestamp = item['timestamp']
            date = datetime.strptime(timestamp, "%Y%m%d%H")
            
            rows.append({
                'date': date.date(),
                'article': item['article'],
                'views': item['views'],
                'project': item['project']
            })
        
        df = pd.DataFrame(rows)
        df = df.sort_values('date', ascending=False)
        
        return df
        
    except Exception as e:
        print(f"Error fetching Wikipedia pageviews for {article}: {e}", file=sys.stderr)
        return pd.DataFrame(columns=['date', 'article', 'views', 'project'])


def detect_spikes(article: str, threshold: float = 2.0, days: int = 60) -> Dict:
    """
    Detect unusual spikes in Wikipedia pageviews.
    
    Args:
        article: Article title
        threshold: Multiple of average to consider a spike (default 2.0x)
        days: Lookback period in days (default 60)
        
    Returns:
        Dictionary with spike analysis
    """
    df = get_pageviews(article, days=days)
    
    if df.empty or len(df) < 7:
        return {
            'article': article,
            'spike_detected': False,
            'reason': 'insufficient_data'
        }
    
    # Calculate statistics
    avg_views = df['views'].mean()
    std_views = df['views'].std()
    latest_views = df.iloc[0]['views']
    recent_7d_avg = df.head(7)['views'].mean()
    
    # Detect spike
    spike_detected = latest_views > (avg_views * threshold)
    recent_spike = recent_7d_avg > (avg_views * threshold)
    
    return {
        'article': article,
        'latest_date': str(df.iloc[0]['date']),
        'latest_views': int(latest_views),
        'avg_views': int(avg_views),
        'recent_7d_avg': int(recent_7d_avg),
        'std_deviation': int(std_views),
        'spike_detected': spike_detected,
        'recent_spike_7d': recent_spike,
        'threshold_multiple': threshold,
        'above_threshold': round(latest_views / avg_views, 2) if avg_views > 0 else 0
    }


def compare_tickers(articles: List[str], days: int = 30) -> pd.DataFrame:
    """
    Compare pageview trends for multiple articles/companies.
    
    Args:
        articles: List of article titles
        days: Number of days to fetch
        
    Returns:
        DataFrame with comparative metrics
    """
    results = []
    
    for article in articles:
        df = get_pageviews(article, days=days)
        if not df.empty:
            results.append({
                'article': article,
                'avg_daily_views': int(df['views'].mean()),
                'max_views': int(df['views'].max()),
                'total_views': int(df['views'].sum()),
                'data_points': len(df)
            })
    
    return pd.DataFrame(results).sort_values('avg_daily_views', ascending=False)


def cli_pageviews(article: str, days: int = 30, detect_spike: bool = False) -> None:
    """CLI command: Display Wikipedia pageviews for an article."""
    df = get_pageviews(article, days=days)
    
    if df.empty:
        print(f"No pageview data found for '{article}'")
        print(f"Tip: Use underscores for spaces, e.g., 'Apple_Inc' or 'Tesla,_Inc.'")
        return
    
    print(f"\n{'='*70}")
    print(f"Wikipedia Pageviews — {article}")
    print(f"{'='*70}\n")
    
    print(f"{'Date':<12} {'Views':>15} {'Change':>10}")
    print(f"{'-'*70}")
    
    for i, row in df.iterrows():
        if i > 0:
            prev_views = df.iloc[i-1]['views']
            change = ((row['views'] - prev_views) / prev_views * 100) if prev_views > 0 else 0
            change_str = f"{change:+.1f}%"
        else:
            change_str = "—"
        
        date_str = str(row['date'])
        print(f"{date_str:<12} {row['views']:>15,} {change_str:>10}")
    
    # Summary statistics
    print(f"\n{'='*70}")
    print(f"Summary (last {len(df)} days):")
    print(f"  Average Views/Day: {df['views'].mean():,.0f}")
    print(f"  Max Views:         {df['views'].max():,.0f}")
    print(f"  Min Views:         {df['views'].min():,.0f}")
    print(f"  Total Views:       {df['views'].sum():,.0f}")
    
    # Spike detection
    if detect_spike:
        spike_data = detect_spikes(article, threshold=2.0, days=days)
        print(f"\nSpike Analysis:")
        print(f"  Latest Views:      {spike_data['latest_views']:,}")
        print(f"  vs Avg:            {spike_data['above_threshold']:.2f}x")
        if spike_data['spike_detected']:
            print(f"  🔥 SPIKE DETECTED — Views are {spike_data['above_threshold']:.1f}x average!")
        else:
            print(f"  ✓ Normal traffic (below {spike_data['threshold_multiple']:.1f}x threshold)")
    
    print(f"\nSource: Wikimedia REST API")
    print(f"Note: Data has 1-2 day lag")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python wikipedia_pageviews.py <ARTICLE> [days] [--detect-spike]")
        print("Example: python wikipedia_pageviews.py Apple_Inc 30")
        print("Example: python wikipedia_pageviews.py Tesla,_Inc. 60 --detect-spike")
        sys.exit(1)
    
    article = sys.argv[1]
    days = 30
    detect_spike = False
    
    if len(sys.argv) > 2:
        try:
            days = int(sys.argv[2])
        except ValueError:
            if sys.argv[2] == '--detect-spike':
                detect_spike = True
    
    if len(sys.argv) > 3 and sys.argv[3] == '--detect-spike':
        detect_spike = True
    
    cli_pageviews(article, days=days, detect_spike=detect_spike)
