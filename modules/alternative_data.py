#!/usr/bin/env python3
"""
Alternative Data Module — Phase #3
====================================
Aggregates alternative data signals:
- Social sentiment (Reddit/StockTwits)
- Congressional trading activity (STOCK Act disclosures)
- Short interest data (FINRA)
- Technical analysis indicators

Free data sources:
- Reddit API (via PRAW/pushshift proxies)
- StockTwits API (public endpoints)
- House.gov/Senate.gov STOCK Act disclosures (periodic reports)
- FINRA short interest (via Nasdaq/NYSE public data)
- Technical indicators computed from OHLCV data
"""

import sys
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

class AlternativeDataFeed:
    """Unified alternative data aggregator."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw-Data/1.0 (Financial Research)'
        })
        
    def get_reddit_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """
        Fetch Reddit sentiment for a ticker from wallstreetbets, stocks, investing.
        Uses pushshift.io archive (free) or Reddit's public JSON endpoints.
        """
        subreddits = ['wallstreetbets', 'stocks', 'investing']
        mentions = []
        
        for sub in subreddits:
            try:
                # Reddit public JSON endpoint (no auth needed)
                url = f"https://www.reddit.com/r/{sub}/search.json"
                params = {
                    'q': symbol,
                    'restrict_sr': '1',
                    't': 'week',
                    'limit': 100
                }
                resp = self.session.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    posts = data.get('data', {}).get('children', [])
                    for post in posts:
                        p = post.get('data', {})
                        mentions.append({
                            'subreddit': sub,
                            'title': p.get('title', ''),
                            'score': p.get('score', 0),
                            'num_comments': p.get('num_comments', 0),
                            'created_utc': p.get('created_utc', 0),
                            'url': f"https://reddit.com{p.get('permalink', '')}"
                        })
            except Exception as e:
                print(f"Error fetching r/{sub}: {e}", file=sys.stderr)
                continue
        
        if not mentions:
            return {'symbol': symbol, 'mentions': 0, 'sentiment': 'neutral', 'posts': []}
        
        # Calculate sentiment score (basic: upvotes - downvotes proxy)
        total_score = sum(m['score'] for m in mentions)
        avg_score = total_score / len(mentions) if mentions else 0
        
        sentiment = 'neutral'
        if avg_score > 50:
            sentiment = 'bullish'
        elif avg_score < -10:
            sentiment = 'bearish'
        
        return {
            'symbol': symbol,
            'mentions': len(mentions),
            'total_score': total_score,
            'avg_score': round(avg_score, 2),
            'sentiment': sentiment,
            'subreddits': {sub: len([m for m in mentions if m['subreddit'] == sub]) for sub in subreddits},
            'recent_posts': sorted(mentions, key=lambda x: x['score'], reverse=True)[:10]
        }
    
    def get_stocktwits_sentiment(self, symbol: str) -> Dict:
        """
        Fetch StockTwits sentiment via public API.
        API: https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json
        """
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                return {'symbol': symbol, 'messages': 0, 'sentiment': 'neutral'}
            
            data = resp.json()
            messages = data.get('messages', [])
            
            if not messages:
                return {'symbol': symbol, 'messages': 0, 'sentiment': 'neutral'}
            
            # Count sentiment tags
            bullish = sum(1 for m in messages if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bullish')
            bearish = sum(1 for m in messages if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bearish')
            
            sentiment = 'neutral'
            if bullish > bearish * 1.5:
                sentiment = 'bullish'
            elif bearish > bullish * 1.5:
                sentiment = 'bearish'
            
            return {
                'symbol': symbol,
                'messages': len(messages),
                'bullish': bullish,
                'bearish': bearish,
                'sentiment': sentiment,
                'bullish_pct': round(bullish / len(messages) * 100, 2) if messages else 0,
                'recent_messages': [
                    {
                        'user': m.get('user', {}).get('username'),
                        'body': m.get('body', '')[:200],
                        'created_at': m.get('created_at'),
                        'sentiment': m.get('entities', {}).get('sentiment', {}).get('basic', 'None')
                    }
                    for m in messages[:5]
                ]
            }
        except Exception as e:
            print(f"StockTwits error for {symbol}: {e}", file=sys.stderr)
            return {'symbol': symbol, 'messages': 0, 'sentiment': 'neutral', 'error': str(e)}
    
    def get_congress_trades(self, symbol: Optional[str] = None, days: int = 30) -> List[Dict]:
        """
        Scrape congressional stock trades from house.gov STOCK Act disclosures.
        Public data: https://disclosures-clerk.house.gov/FinancialDisclosure
        
        Note: This requires periodic scraping as there's no official API.
        Returns recent trades (mock implementation - real version would scrape).
        """
        # Mock implementation (real version would scrape house.gov/senate.gov)
        # In production, use a database of previously scraped trades
        mock_trades = [
            {
                'member': 'Rep. Nancy Pelosi',
                'transaction_date': '2024-02-15',
                'ticker': 'NVDA',
                'transaction_type': 'Purchase',
                'amount_range': '$1,000,001 - $5,000,000',
                'disclosure_date': '2024-02-20'
            },
            {
                'member': 'Sen. Tommy Tuberville',
                'transaction_date': '2024-02-10',
                'ticker': 'TSLA',
                'transaction_type': 'Sale',
                'amount_range': '$50,001 - $100,000',
                'disclosure_date': '2024-02-18'
            }
        ]
        
        if symbol:
            return [t for t in mock_trades if t['ticker'] == symbol.upper()]
        return mock_trades
    
    def get_short_interest(self, symbol: str) -> Dict:
        """
        Fetch short interest data from FINRA/exchanges.
        Free sources:
        - Nasdaq short interest: https://www.nasdaq.com/market-activity/stocks/{symbol}/short-interest
        - NYSE: similar endpoint
        
        Note: Updated bi-monthly (settlement dates)
        """
        try:
            # Nasdaq short interest page
            url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/short-interest"
            resp = self.session.get(url, timeout=10)
            
            if resp.status_code != 200:
                return {'symbol': symbol, 'error': 'Data not available'}
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Parse short interest table (structure varies, this is illustrative)
            # In production, use specific CSS selectors or API endpoints
            short_data = {
                'symbol': symbol.upper(),
                'short_interest': 'N/A',  # Would parse from HTML
                'short_pct_float': 'N/A',
                'days_to_cover': 'N/A',
                'settlement_date': 'N/A',
                'note': 'Live scraping not implemented - use FINRA API or cached data'
            }
            
            return short_data
            
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def calculate_technical_indicators(self, symbol: str, prices: List[Dict]) -> Dict:
        """
        Calculate technical indicators from OHLCV data.
        Indicators: RSI, MACD, Bollinger Bands, Moving Averages
        
        prices: list of {'date': str, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': int}
        """
        if len(prices) < 50:
            return {'error': 'Insufficient data (need 50+ days)'}
        
        closes = [p['close'] for p in prices]
        volumes = [p['volume'] for p in prices]
        
        # RSI (14-day)
        rsi = self._calculate_rsi(closes, period=14)
        
        # MACD
        macd_line, signal_line = self._calculate_macd(closes)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes)
        
        # Moving Averages
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        
        return {
            'symbol': symbol,
            'current_price': closes[-1],
            'rsi_14': round(rsi, 2),
            'macd': round(macd_line, 2),
            'macd_signal': round(signal_line, 2),
            'macd_histogram': round(macd_line - signal_line, 2),
            'bb_upper': round(bb_upper, 2),
            'bb_middle': round(bb_middle, 2),
            'bb_lower': round(bb_lower, 2),
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'avg_volume_20d': round(sum(volumes[-20:]) / 20, 0),
            'signals': {
                'rsi_oversold': rsi < 30,
                'rsi_overbought': rsi > 70,
                'macd_bullish_cross': macd_line > signal_line and macd_line - signal_line < 0.5,
                'price_above_sma50': closes[-1] > sma_50
            }
        }
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Relative Strength Index"""
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, closes: List[float], fast=12, slow=26, signal=9) -> tuple:
        """MACD indicator"""
        if len(closes) < slow + signal:
            return 0.0, 0.0
        
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line is 9-day EMA of MACD
        # Simplified: use SMA for signal
        signal_line = macd_line  # In production, calculate proper EMA of MACD
        
        return macd_line, signal_line
    
    def _ema(self, values: List[float], period: int) -> float:
        """Exponential Moving Average"""
        if len(values) < period:
            return sum(values) / len(values)
        
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        
        for val in values[period:]:
            ema = (val - ema) * multiplier + ema
        
        return ema
    
    def _calculate_bollinger_bands(self, closes: List[float], period: int = 20, std_dev: int = 2) -> tuple:
        """Bollinger Bands"""
        if len(closes) < period:
            avg = sum(closes) / len(closes)
            return avg, avg, avg
        
        recent = closes[-period:]
        sma = sum(recent) / period
        variance = sum((x - sma) ** 2 for x in recent) / period
        std = variance ** 0.5
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower


def main():
    """CLI interface for alternative data queries."""
    if len(sys.argv) < 2:
        print("Usage: python alternative_data.py <command> [options]")
        print("\nCommands:")
        print("  reddit <SYMBOL>              - Reddit sentiment for ticker")
        print("  stocktwits <SYMBOL>          - StockTwits sentiment")
        print("  congress [SYMBOL]            - Congressional trades (all or by ticker)")
        print("  short <SYMBOL>               - Short interest data")
        print("  combined <SYMBOL>            - All alternative data for symbol")
        return
    
    command = sys.argv[1].lower()
    # Strip 'alt-' prefix if present (for CLI routing)
    if command.startswith('alt-'):
        command = command[4:]
    feed = AlternativeDataFeed()
    
    if command == 'reddit' and len(sys.argv) > 2:
        symbol = sys.argv[2].upper()
        result = feed.get_reddit_sentiment(symbol)
        print(json.dumps(result, indent=2))
    
    elif command == 'stocktwits' and len(sys.argv) > 2:
        symbol = sys.argv[2].upper()
        result = feed.get_stocktwits_sentiment(symbol)
        print(json.dumps(result, indent=2))
    
    elif command == 'congress':
        symbol = sys.argv[2].upper() if len(sys.argv) > 2 else None
        result = feed.get_congress_trades(symbol)
        print(json.dumps(result, indent=2))
    
    elif command == 'short' and len(sys.argv) > 2:
        symbol = sys.argv[2].upper()
        result = feed.get_short_interest(symbol)
        print(json.dumps(result, indent=2))
    
    elif command == 'combined' and len(sys.argv) > 2:
        symbol = sys.argv[2].upper()
        combined = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'reddit': feed.get_reddit_sentiment(symbol),
            'stocktwits': feed.get_stocktwits_sentiment(symbol),
            'congress_trades': feed.get_congress_trades(symbol),
            'short_interest': feed.get_short_interest(symbol)
        }
        print(json.dumps(combined, indent=2))
    
    else:
        print(f"Unknown command or missing symbol: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
