#!/usr/bin/env python3
"""
Quiver Quant WallStreetBets — Retail Sentiment Tracker
Reddit WallStreetBets mentions, sentiment, and discussion volume for stocks.
Identifies meme stock trends and retail sentiment shifts.

API: Quiver Quantitative API
Docs: https://www.quiverquant.com/sources/wallstreetbets
Free tier: 100 queries per day
Update frequency: daily
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class QuiverQuantWSB:
    """WallStreetBets mention and sentiment tracker."""
    
    BASE_URL = "https://api.quiverquant.com/beta/live/wallstreetbets"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key.
        
        Args:
            api_key: Quiver Quant API token (defaults to QUIVER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('QUIVER_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0 (quantclaw-data; educational use)',
            'Accept': 'application/json'
        })
    
    def get_ticker_mentions(
        self,
        ticker: str,
        days: int = 30
    ) -> Dict:
        """
        Get WallStreetBets mentions for a ticker.
        
        Args:
            ticker: Stock ticker (e.g., "GME", "TSLA")
            days: Number of days to retrieve (default: 30)
        
        Returns:
            Dict with mention data including frequency, sentiment, upvotes
        """
        if not self.api_key:
            return {
                'error': 'API key required. Set QUIVER_API_KEY environment variable or pass to constructor.',
                'ticker': ticker
            }
        
        params = {
            'symbol': ticker.upper(),
            'token': self.api_key
        }
        
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            # Filter to last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if isinstance(data, list):
                filtered_data = [
                    item for item in data
                    if datetime.fromisoformat(item.get('Date', '2000-01-01')) >= cutoff_date
                ]
            else:
                filtered_data = data
            
            # Calculate aggregates
            total_mentions = sum(item.get('Mentions', 0) for item in filtered_data) if isinstance(filtered_data, list) else 0
            total_upvotes = sum(item.get('Upvotes', 0) for item in filtered_data) if isinstance(filtered_data, list) else 0
            
            return {
                'ticker': ticker.upper(),
                'period_days': days,
                'total_mentions': total_mentions,
                'total_upvotes': total_upvotes,
                'avg_daily_mentions': total_mentions / max(days, 1),
                'data': filtered_data if isinstance(filtered_data, list) else [filtered_data],
                'retrieved_at': datetime.now().isoformat()
            }
        
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                return {
                    'error': 'Rate limit exceeded. Free tier allows 100 queries per day.',
                    'ticker': ticker
                }
            elif e.response.status_code == 401:
                return {
                    'error': 'Invalid API key. Check your QUIVER_API_KEY.',
                    'ticker': ticker
                }
            else:
                return {
                    'error': f'HTTP {e.response.status_code}: {str(e)}',
                    'ticker': ticker
                }
        except requests.RequestException as e:
            return {
                'error': str(e),
                'ticker': ticker
            }
    
    def detect_mention_spikes(
        self,
        ticker: str,
        days: int = 90,
        threshold: float = 3.0
    ) -> Dict:
        """
        Detect abnormal spikes in WallStreetBets mentions.
        
        Args:
            ticker: Stock ticker
            days: Lookback period
            threshold: Multiplier above average to flag as spike (default: 3.0x)
        
        Returns:
            Dict with spike analysis
        """
        data = self.get_ticker_mentions(ticker, days)
        
        if 'error' in data:
            return data
        
        items = data.get('data', [])
        if not items:
            return {'error': 'No mention data available', 'ticker': ticker}
        
        mentions_list = [item.get('Mentions', 0) for item in items]
        if not mentions_list:
            return {'error': 'No mention data available', 'ticker': ticker}
        
        avg_mentions = sum(mentions_list) / len(mentions_list)
        
        spikes = []
        for item in items:
            mentions = item.get('Mentions', 0)
            if mentions > avg_mentions * threshold:
                spikes.append({
                    'date': item.get('Date', 'N/A'),
                    'mentions': mentions,
                    'upvotes': item.get('Upvotes', 0),
                    'multiplier': round(mentions / avg_mentions, 2) if avg_mentions > 0 else 0
                })
        
        return {
            'ticker': ticker,
            'avg_daily_mentions': round(avg_mentions, 1),
            'threshold': threshold,
            'spike_count': len(spikes),
            'spikes': sorted(spikes, key=lambda x: x['multiplier'], reverse=True),
            'max_spike': max(spikes, key=lambda x: x['multiplier']) if spikes else None
        }
    
    def compare_tickers(
        self,
        tickers: List[str],
        days: int = 7
    ) -> Dict:
        """
        Compare WallStreetBets mention volume for multiple tickers.
        
        Args:
            tickers: List of tickers to compare
            days: Lookback period
        
        Returns:
            Dict with comparative rankings
        """
        results = {}
        for ticker in tickers:
            data = self.get_ticker_mentions(ticker, days)
            if 'error' not in data:
                results[ticker] = {
                    'total_mentions': data['total_mentions'],
                    'total_upvotes': data['total_upvotes'],
                    'avg_daily_mentions': round(data['avg_daily_mentions'], 1)
                }
        
        # Rank by total mentions
        ranked = sorted(
            results.items(),
            key=lambda x: x[1]['total_mentions'],
            reverse=True
        )
        
        return {
            'period_days': days,
            'tickers_analyzed': len(results),
            'rankings': [
                {
                    'rank': i + 1,
                    'ticker': ticker,
                    **metrics
                }
                for i, (ticker, metrics) in enumerate(ranked)
            ]
        }
    
    def get_trending_tickers(self, top_n: int = 10) -> Dict:
        """
        Get most mentioned tickers on WallStreetBets (if API supports it).
        
        This is a placeholder - actual implementation depends on API capabilities.
        """
        return {
            'info': 'Direct trending endpoint not available in free tier.',
            'suggestion': 'Use compare_tickers() with a watchlist of suspected meme stocks.'
        }


def main():
    """CLI interface."""
    import sys
    
    wsb = QuiverQuantWSB()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python quiver_quant_wallstreetbets.py wsb-mentions <TICKER> [--days DAYS]")
        print("  python quiver_quant_wallstreetbets.py wsb-spikes <TICKER> [--days DAYS] [--threshold FLOAT]")
        print("  python quiver_quant_wallstreetbets.py wsb-compare <TICKER1,TICKER2,...> [--days DAYS]")
        print("\nExamples:")
        print("  python quiver_quant_wallstreetbets.py wsb-mentions GME --days 30")
        print("  python quiver_quant_wallstreetbets.py wsb-spikes TSLA --days 90 --threshold 3.0")
        print("  python quiver_quant_wallstreetbets.py wsb-compare GME,AMC,TSLA --days 7")
        print("\nNote: Requires QUIVER_API_KEY environment variable.")
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
    
    if cmd == 'wsb-mentions':
        if len(sys.argv) < 3:
            print("Error: Missing ticker argument")
            sys.exit(1)
        ticker = sys.argv[2]
        days = get_flag_value('--days', 30, int)
        result = wsb.get_ticker_mentions(ticker, days)
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"\n📊 r/WallStreetBets Mentions: {ticker}")
        print(f"Total mentions ({days}d): {result.get('total_mentions', 0):,}")
        print(f"Total upvotes: {result.get('total_upvotes', 0):,}")
        print(f"Avg daily mentions: {result.get('avg_daily_mentions', 0):.1f}")
    
    elif cmd == 'wsb-spikes':
        if len(sys.argv) < 3:
            print("Error: Missing ticker argument")
            sys.exit(1)
        ticker = sys.argv[2]
        days = get_flag_value('--days', 90, int)
        threshold = get_flag_value('--threshold', 3.0, float)
        result = wsb.detect_mention_spikes(ticker, days, threshold)
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"\n🚨 r/WSB Mention Spikes: {result.get('ticker')}")
        print(f"Avg daily mentions: {result.get('avg_daily_mentions', 0):,.1f}")
        print(f"Spike threshold: {result.get('threshold')}x")
        print(f"Spikes detected: {result.get('spike_count')}")
        if result.get('max_spike'):
            max_spike = result['max_spike']
            print(f"Max spike: {max_spike['date']} ({max_spike['multiplier']}x normal, {max_spike['mentions']} mentions)")
    
    elif cmd == 'wsb-compare':
        if len(sys.argv) < 3:
            print("Error: Missing tickers argument")
            sys.exit(1)
        tickers = sys.argv[2].split(',')
        days = get_flag_value('--days', 7, int)
        result = wsb.compare_tickers(tickers, days)
        
        print(f"\n📊 r/WallStreetBets Comparison ({days} days)")
        for item in result['rankings']:
            print(f"{item['rank']}. {item['ticker']}: {item['total_mentions']:,} mentions ({item['avg_daily_mentions']:.1f}/day)")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
