#!/usr/bin/env python3
"""
Wikipedia Pageviews — Alternative Data Source
Company attention proxy from Wikipedia page views.

API: Wikimedia REST API (no key required)
Docs: https://wikimedia.org/api/rest_v1/
Rate limit: 200 req/sec (generous)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class WikipediaPageviews:
    """Wikipedia pageviews as company attention proxy."""
    
    BASE_URL = "https://wikimedia.org/api/rest_v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0 (quantclaw-data; educational use)',
            'Accept': 'application/json'
        })
    
    def get_company_pageviews(
        self,
        company_name: str,
        days: int = 30,
        granularity: str = "daily"
    ) -> Dict:
        """
        Get Wikipedia pageviews for a company.
        
        Args:
            company_name: Company name (e.g., "Apple_Inc.")
            days: Number of days to retrieve (default: 30)
            granularity: "daily" or "monthly"
        
        Returns:
            Dict with pageview data
        """
        # Format article title (replace spaces with underscores)
        article = company_name.replace(" ", "_")
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime("%Y%m%d00")
        end_str = end_date.strftime("%Y%m%d00")
        
        url = (
            f"{self.BASE_URL}/metrics/pageviews/per-article/"
            f"en.wikipedia/all-access/all-agents/{article}/{granularity}/{start_str}/{end_str}"
        )
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'article': article,
                'company': company_name,
                'granularity': granularity,
                'items': data.get('items', []),
                'total_views': sum(item.get('views', 0) for item in data.get('items', [])),
                'avg_daily_views': sum(item.get('views', 0) for item in data.get('items', [])) / max(len(data.get('items', [])), 1),
                'retrieved_at': datetime.now().isoformat()
            }
        except requests.RequestException as e:
            return {'error': str(e), 'article': article}
    
    def get_ticker_pageviews(self, ticker: str, days: int = 30) -> Dict:
        """
        Get pageviews for a ticker by mapping to Wikipedia article.
        
        Common mappings hardcoded for top stocks.
        """
        # Ticker → Wikipedia article mapping
        ticker_map = {
            'AAPL': 'Apple_Inc.',
            'MSFT': 'Microsoft',
            'GOOGL': 'Alphabet_Inc.',
            'AMZN': 'Amazon_(company)',
            'TSLA': 'Tesla,_Inc.',
            'META': 'Meta_Platforms',
            'NVDA': 'Nvidia',
            'BRK.B': 'Berkshire_Hathaway',
            'JPM': 'JPMorgan_Chase',
            'V': 'Visa_Inc.',
            'WMT': 'Walmart',
            'DIS': 'The_Walt_Disney_Company',
            'NFLX': 'Netflix',
            'BA': 'Boeing',
            'GE': 'General_Electric',
            'F': 'Ford_Motor_Company',
            'GM': 'General_Motors',
            'COIN': 'Coinbase',
            'SQ': 'Block,_Inc.',
            'PYPL': 'PayPal',
        }
        
        article = ticker_map.get(ticker, f"{ticker}_(company)")
        result = self.get_company_pageviews(article, days)
        result['ticker'] = ticker
        return result
    
    def detect_attention_spikes(
        self,
        company_name: str,
        days: int = 90,
        threshold: float = 2.0
    ) -> Dict:
        """
        Detect spikes in Wikipedia pageviews (potential volatility predictor).
        
        Args:
            company_name: Company name
            days: Lookback period
            threshold: Multiplier above average to flag as spike (default: 2.0x)
        
        Returns:
            Dict with spike analysis
        """
        data = self.get_company_pageviews(company_name, days)
        
        if 'error' in data:
            return data
        
        items = data['items']
        if not items:
            return {'error': 'No data available'}
        
        views = [item['views'] for item in items]
        avg_views = sum(views) / len(views)
        
        spikes = []
        for item in items:
            if item['views'] > avg_views * threshold:
                spikes.append({
                    'date': item['timestamp'][:8],  # YYYYMMDD
                    'views': item['views'],
                    'multiplier': round(item['views'] / avg_views, 2)
                })
        
        return {
            'company': company_name,
            'avg_daily_views': round(avg_views),
            'threshold': threshold,
            'spike_count': len(spikes),
            'spikes': spikes,
            'max_spike': max(spikes, key=lambda x: x['multiplier']) if spikes else None
        }
    
    def compare_companies(
        self,
        companies: List[str],
        days: int = 30
    ) -> Dict:
        """
        Compare pageview trends for multiple companies.
        
        Args:
            companies: List of company names
            days: Lookback period
        
        Returns:
            Dict with comparative analysis
        """
        results = {}
        for company in companies:
            time.sleep(0.1)  # Be nice to API
            data = self.get_company_pageviews(company, days)
            if 'error' not in data:
                results[company] = {
                    'total_views': data['total_views'],
                    'avg_daily_views': round(data['avg_daily_views'])
                }
        
        # Rank by total views
        ranked = sorted(
            results.items(),
            key=lambda x: x[1]['total_views'],
            reverse=True
        )
        
        return {
            'period_days': days,
            'companies_analyzed': len(results),
            'rankings': [
                {
                    'rank': i + 1,
                    'company': company,
                    **metrics
                }
                for i, (company, metrics) in enumerate(ranked)
            ]
        }
    
    def get_top_viewed_tech(self, days: int = 7) -> Dict:
        """
        Get top viewed tech companies on Wikipedia.
        Predefined list of major tech stocks.
        """
        tech_companies = [
            'Apple_Inc.',
            'Microsoft',
            'Alphabet_Inc.',
            'Amazon_(company)',
            'Meta_Platforms',
            'Tesla,_Inc.',
            'Nvidia',
            'Netflix',
            'Adobe_Inc.',
            'Salesforce'
        ]
        
        return self.compare_companies(tech_companies, days)


def main():
    """CLI interface."""
    import sys
    
    wiki = WikipediaPageviews()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python wiki_pageviews.py wiki-views <company_name> [--days DAYS]")
        print("  python wiki_pageviews.py wiki-ticker <TICKER> [--days DAYS]")
        print("  python wiki_pageviews.py wiki-spikes <company_name> [--days DAYS] [--threshold FLOAT]")
        print("  python wiki_pageviews.py wiki-compare <company1,company2,...> [--days DAYS]")
        print("  python wiki_pageviews.py wiki-top-tech [--days DAYS]")
        print("\nExamples:")
        print("  python wiki_pageviews.py wiki-views Apple_Inc. --days 30")
        print("  python wiki_pageviews.py wiki-ticker TSLA --days 90")
        print("  python wiki_pageviews.py wiki-spikes 'Tesla,_Inc.' --days 90 --threshold 2.5")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    # Parse flags
    def get_flag_value(flag_name, default, type_func=str):
        """Get value after a flag like --days 30"""
        try:
            idx = sys.argv.index(flag_name)
            return type_func(sys.argv[idx + 1])
        except (ValueError, IndexError):
            return default
    
    if cmd == 'wiki-ticker':
        if len(sys.argv) < 3:
            print("Error: Missing ticker argument")
            sys.exit(1)
        ticker = sys.argv[2]
        days = get_flag_value('--days', 30, int)
        result = wiki.get_ticker_pageviews(ticker, days)
        print(f"\n📊 Wikipedia Pageviews: {ticker}")
        print(f"Article: {result.get('article')}")
        print(f"Total views ({days}d): {result.get('total_views', 0):,}")
        print(f"Avg daily views: {result.get('avg_daily_views', 0):.0f}")
    
    elif cmd == 'wiki-spikes':
        if len(sys.argv) < 3:
            print("Error: Missing company argument")
            sys.exit(1)
        company = sys.argv[2]
        days = get_flag_value('--days', 90, int)
        threshold = get_flag_value('--threshold', 2.0, float)
        result = wiki.detect_attention_spikes(company, days, threshold)
        print(f"\n🚨 Attention Spikes: {result.get('company')}")
        print(f"Avg daily views: {result.get('avg_daily_views', 0):,}")
        print(f"Spike threshold: {result.get('threshold')}x")
        print(f"Spikes detected: {result.get('spike_count')}")
        if result.get('max_spike'):
            max_spike = result['max_spike']
            print(f"Max spike: {max_spike['date']} ({max_spike['multiplier']}x normal)")
    
    elif cmd == 'wiki-compare':
        if len(sys.argv) < 3:
            print("Error: Missing companies argument")
            sys.exit(1)
        companies = sys.argv[2].split(',')
        days = get_flag_value('--days', 30, int)
        result = wiki.compare_companies(companies, days)
        print(f"\n📊 Company Comparison ({days} days)")
        for item in result['rankings']:
            print(f"{item['rank']}. {item['company']}: {item['total_views']:,} views (avg: {item['avg_daily_views']:,}/day)")
    
    elif cmd == 'wiki-top-tech':
        days = get_flag_value('--days', 7, int)
        result = wiki.get_top_viewed_tech(days)
        print(f"\n🏆 Top Viewed Tech Companies ({days} days)")
        for item in result['rankings']:
            print(f"{item['rank']}. {item['company']}: {item['total_views']:,} views")
    
    elif cmd == 'wiki-views':
        if len(sys.argv) < 3:
            print("Error: Missing company argument")
            sys.exit(1)
        company = sys.argv[2]
        days = get_flag_value('--days', 30, int)
        result = wiki.get_company_pageviews(company, days)
        print(f"\n📖 Wikipedia Pageviews: {company}")
        print(f"Total views ({days}d): {result.get('total_views', 0):,}")
        print(f"Avg daily views: {result.get('avg_daily_views', 0):.0f}")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
