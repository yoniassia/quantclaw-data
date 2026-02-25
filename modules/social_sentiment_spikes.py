#!/usr/bin/env python3
"""
Social Sentiment Spike Detector — Phase 93

Real-time Reddit/Twitter surge detection, meme stock momentum, pump detection.

Monitors social media platforms for:
- Sudden volume/sentiment surges
- Meme stock momentum patterns
- Coordinated pump detection
- Retail investor attention spikes
- Viral ticker mentions

Uses free APIs:
- Reddit API (public endpoints, no auth needed for read)
- yfinance for price/volume correlation
- SEC EDGAR for float data
- Basic keyword analysis for pump detection

No API keys required for basic functionality.
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import re
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import time
import warnings
from statistics import mean, stdev

# Reddit API endpoints (public, no auth required)
REDDIT_API = "https://www.reddit.com/r/{subreddit}/{filter}.json"
REDDIT_SEARCH = "https://www.reddit.com/search.json"

# Subreddits to monitor for stock mentions
STOCK_SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "stockmarket",
    "pennystocks",
    "daytrading",
    "options"
]

# Meme stock keywords
MEME_KEYWORDS = [
    "moon", "rocket", "diamond hands", "hodl", "apes", "squeeze",
    "gamma squeeze", "short squeeze", "to the moon", "yolo", "fomo",
    "tendies", "stonks", "ape strong", "buy the dip", "btd"
]

# Pump detection keywords
PUMP_KEYWORDS = [
    "pump", "guaranteed", "insider", "secret", "next big thing",
    "100x", "10x", "moonshot", "can't lose", "sure thing",
    "going parabolic", "about to explode", "huge news coming"
]


@dataclass
class MentionData:
    """Social media mention data point."""
    ticker: str
    timestamp: str
    platform: str
    source: str  # subreddit name, twitter handle, etc
    text: str
    upvotes: int
    comments: int
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1 to 1
    meme_score: float  # 0-100 (how meme-y is this post)
    pump_score: float  # 0-100 (pump & dump risk)
    url: str


@dataclass
class SpikeEvent:
    """Detected sentiment/mention spike."""
    ticker: str
    platform: str
    spike_type: str  # volume_spike, sentiment_surge, meme_momentum, pump_alert
    detected_at: str
    spike_magnitude: float  # multiple of baseline (2x, 5x, 10x, etc)
    baseline_mentions: float
    current_mentions: float
    sentiment_shift: float  # change in sentiment score
    meme_score: float
    pump_risk: str  # low, medium, high, critical
    price_move_24h: float  # % price change in last 24h
    volume_spike: float  # volume vs 30d average
    confidence: float  # 0-100
    evidence: List[MentionData]
    recommendation: str


@dataclass
class TickerMomentum:
    """Social momentum tracking for a ticker."""
    ticker: str
    company_name: str
    current_price: float
    price_change_24h: float
    volume_ratio: float  # current vs 30d avg
    mention_count_1h: int
    mention_count_24h: int
    mention_growth_rate: float  # % change vs previous period
    avg_sentiment: float
    sentiment_volatility: float
    meme_intensity: float  # 0-100
    pump_risk: float  # 0-100
    top_subreddits: List[Tuple[str, int]]  # (subreddit, count)
    recent_mentions: List[MentionData]
    classification: str  # organic, meme_stock, pump_candidate, viral


@dataclass
class SpikeReport:
    """Comprehensive spike detection report."""
    report_date: str
    scan_period: str
    tickers_scanned: int
    spikes_detected: int
    active_meme_stocks: List[str]
    pump_alerts: List[str]
    top_momentum: List[TickerMomentum]
    spike_events: List[SpikeEvent]
    summary: str


class SocialSentimentSpikeDetector:
    """Detect social sentiment spikes and meme stock momentum."""
    
    def __init__(self, cache_ttl: int = 300):
        """Initialize detector.
        
        Args:
            cache_ttl: Cache TTL in seconds (default 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        
    def _get_reddit_posts(self, subreddit: str, filter: str = "new", limit: int = 100) -> List[Dict]:
        """Fetch Reddit posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            filter: new, hot, top, rising
            limit: Number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        url = REDDIT_API.format(subreddit=subreddit, filter=filter)
        params = {"limit": limit}
        headers = {"User-Agent": "QuantClaw/1.0"}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [child["data"] for child in data.get("data", {}).get("children", [])]
        except Exception as e:
            warnings.warn(f"Reddit API error for r/{subreddit}: {e}")
            return []
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text.
        
        Args:
            text: Text to search for tickers
            
        Returns:
            List of uppercase tickers found
        """
        # Prioritize $TICKER format (1-5 caps after $)
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        dollar_matches = re.findall(dollar_pattern, text.upper())
        
        # For standalone tickers, be very conservative:
        # - Must be 2-5 letters
        # - Must be surrounded by word boundaries
        # - Exclude common words aggressively
        
        # Filter common false positives (comprehensive list)
        exclude = {
            # Common words
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "CAN", "GET", "ALL", "OUT",
            "NEW", "NOW", "WAY", "MAY", "ONE", "TWO", "DAY", "TOP", "BIG", "OLD",
            "OWN", "SEE", "MAKE", "JUST", "KNOW", "TAKE", "COME", "BACK", "BEST",
            "WEEK", "YEAR", "HUGE", "MORE", "SOME", "THIS", "THAT", "FROM", "ALSO",
            "BEEN", "WERE", "ONLY", "VERY", "WHEN", "TIME", "WHAT", "HAVE", "INTO",
            "GOOD", "WILL", "WELL", "SAID", "NEED", "EVEN", "MUCH", "MOST", "SUCH",
            "THEM", "LIKE", "THAN", "MANY", "SAME", "OVER", "BOTH", "NEXT", "EDIT",
            "THEY", "WITH", "WENT", "DONE", "LOOK", "CALL", "WORK", "FIRST", "LAST",
            "LONG", "HELP", "MUCH", "PART", "HIGH", "HAND", "KEEP", "LIFE", "STILL",
            "MADE", "FIND", "MUST", "HOME", "LESS", "GIVE", "AREA", "SHOW", "TOLD",
            "DOES", "AWAY", "WENT", "GOING", "THINK", "MONEY", "STOCK", "ABOUT",
            "LOOKS", "AFTER", "CALLS", "PUTS", "COULD", "WOULD", "SHOULD", "THERE",
            "CHECK", "TECH", "PRICE", "CASH", "RISK", "PLAY", "MOVE", "NEWS",
            # Finance/trading jargon
            "USA", "CEO", "CFO", "CTO", "COO", "IPO", "ETF", "NYSE", "NASDAQ", 
            "SEC", "FDA", "FED", "GDP", "CPI", "ATH", "ATL", "YTD", "MTD", "QOQ",
            "YOY", "EOD", "AH", "PM", "FOMO", "YOLO", "BTFD", "HODL", "APES",
            "MOON", "HOLD", "LOSS", "GAIN", "SHORT", "LMAO", "ROFL", "BOOM",
            # Common Reddit/social words
            "DD", "IMO", "TLDR", "EDIT", "PSA", "FYI", "TIL", "ELI5", "FTFY",
            "AMA", "TL;DR", "NSFW", "AFAIK", "IIRC", "IMHO", "LOL", "WTF", "OMG",
            # Directional words
            "UP", "DOWN", "BUY", "SELL", "AT", "TO", "IN", "ON", "BY", "AS", "IS",
            "IT", "OF", "OR", "IF", "SO", "NO", "YES", "MY", "HE", "SHE", "WE", "US",
            "ME", "HIS", "HER", "OUR", "WHO", "WHY", "HOW", "ANY", "FEW", "OFF"
        }
        
        # Return only $TICKER matches + verified standalone tickers
        # For standalone, only include if NOT in exclude list
        tickers = set(dollar_matches)  # $TICKER always included
        
        # Only add standalone tickers that pass strict filtering
        standalone_pattern = r'(?:^|[\s,.:;!?"\'])([A-Z]{2,5})(?=$|[\s,.:;!?"\'])'
        standalone_matches = re.findall(standalone_pattern, text.upper())
        for ticker in standalone_matches:
            if ticker not in exclude and len(ticker) >= 2 and len(ticker) <= 5:
                tickers.add(ticker)
        
        return sorted(list(tickers))
    
    def _calculate_sentiment(self, text: str) -> Tuple[str, float]:
        """Calculate sentiment from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score)
        """
        text_lower = text.lower()
        
        # Positive words
        pos_words = [
            "bullish", "buy", "long", "calls", "moon", "rocket", "gain", "profit",
            "beat", "strong", "growth", "breakout", "rally", "squeeze", "up", "green"
        ]
        
        # Negative words
        neg_words = [
            "bearish", "sell", "short", "puts", "crash", "loss", "miss", "weak",
            "decline", "drop", "down", "red", "bag holding", "dump", "rug pull"
        ]
        
        pos_count = sum(1 for word in pos_words if word in text_lower)
        neg_count = sum(1 for word in neg_words if word in text_lower)
        total = pos_count + neg_count
        
        if total == 0:
            return "neutral", 0.0
        
        score = (pos_count - neg_count) / total
        
        if score > 0.2:
            return "positive", score
        elif score < -0.2:
            return "negative", score
        else:
            return "neutral", score
    
    def _calculate_meme_score(self, text: str) -> float:
        """Calculate how meme-y a post is (0-100).
        
        Args:
            text: Post text
            
        Returns:
            Meme score 0-100
        """
        text_lower = text.lower()
        meme_count = sum(1 for keyword in MEME_KEYWORDS if keyword in text_lower)
        
        # Emoji bonus
        emoji_pattern = r'🚀|💎|🦍|🌙|📈|💰|🤑'
        emoji_count = len(re.findall(emoji_pattern, text))
        
        # All caps bonus
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        score = (meme_count * 20) + (emoji_count * 10) + (caps_ratio * 30)
        return min(score, 100)
    
    def _calculate_pump_score(self, text: str) -> float:
        """Calculate pump & dump risk score (0-100).
        
        Args:
            text: Post text
            
        Returns:
            Pump risk score 0-100
        """
        text_lower = text.lower()
        pump_count = sum(1 for keyword in PUMP_KEYWORDS if keyword in text_lower)
        
        # Check for excessive gains claims
        gains_pattern = r'(\d+)x|(\d+)%\s*(gain|profit|return)'
        gains_matches = re.findall(gains_pattern, text_lower)
        excessive_gains = any(
            int(m[0] or m[1] or 0) > 50 for m in gains_matches
        )
        
        # Check for urgency ("buy now", "last chance", etc)
        urgency_words = ["now", "urgent", "hurry", "last chance", "before", "tonight"]
        urgency_count = sum(1 for word in urgency_words if word in text_lower)
        
        score = (pump_count * 25) + (30 if excessive_gains else 0) + (urgency_count * 10)
        return min(score, 100)
    
    def scan_reddit_mentions(self, hours: int = 24, limit_per_sub: int = 100) -> Dict[str, List[MentionData]]:
        """Scan Reddit for ticker mentions.
        
        Args:
            hours: Hours of history to scan
            limit_per_sub: Posts per subreddit to fetch
            
        Returns:
            Dict mapping tickers to list of mentions
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        mentions = defaultdict(list)
        
        for subreddit in STOCK_SUBREDDITS:
            posts = self._get_reddit_posts(subreddit, filter="new", limit=limit_per_sub)
            
            for post in posts:
                # Check post age
                post_time = datetime.utcfromtimestamp(post.get("created_utc", 0))
                if post_time < cutoff:
                    continue
                
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title} {selftext}"
                
                tickers = self._extract_tickers(full_text)
                if not tickers:
                    continue
                
                sentiment, score = self._calculate_sentiment(full_text)
                meme_score = self._calculate_meme_score(full_text)
                pump_score = self._calculate_pump_score(full_text)
                
                for ticker in tickers:
                    mention = MentionData(
                        ticker=ticker,
                        timestamp=post_time.isoformat(),
                        platform="reddit",
                        source=f"r/{subreddit}",
                        text=title[:200],
                        upvotes=post.get("ups", 0),
                        comments=post.get("num_comments", 0),
                        sentiment=sentiment,
                        sentiment_score=score,
                        meme_score=meme_score,
                        pump_score=pump_score,
                        url=f"https://reddit.com{post.get('permalink', '')}"
                    )
                    mentions[ticker].append(mention)
            
            time.sleep(0.5)  # Rate limit
        
        return dict(mentions)
    
    def detect_spikes(self, ticker: str, mentions: List[MentionData], baseline_hours: int = 168) -> Optional[SpikeEvent]:
        """Detect if there's a sentiment spike for a ticker.
        
        Args:
            ticker: Stock ticker
            mentions: List of recent mentions
            baseline_hours: Hours for baseline calculation (default 7 days)
            
        Returns:
            SpikeEvent if spike detected, None otherwise
        """
        if len(mentions) < 5:
            return None
        
        # Get price data
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'].iloc[-1]
            price_24h_ago = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
            price_change = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            volume_30d_avg = hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            volume_spike = current_volume / volume_30d_avg if volume_30d_avg > 0 else 1.0
        except:
            price_change = 0.0
            volume_spike = 1.0
        
        # Calculate mention metrics
        now = datetime.utcnow()
        last_24h = [m for m in mentions if (now - datetime.fromisoformat(m.timestamp)).total_seconds() < 86400]
        last_1h = [m for m in mentions if (now - datetime.fromisoformat(m.timestamp)).total_seconds() < 3600]
        
        current_rate = len(last_1h)
        baseline_rate = len(mentions) / (baseline_hours / 24) if len(mentions) > 0 else 0.1
        
        spike_magnitude = current_rate / baseline_rate if baseline_rate > 0 else 0
        
        # Calculate sentiment metrics
        sentiments = [m.sentiment_score for m in last_24h if m.sentiment_score != 0]
        avg_sentiment = mean(sentiments) if sentiments else 0.0
        sentiment_volatility = stdev(sentiments) if len(sentiments) > 1 else 0.0
        
        # Calculate meme/pump scores
        avg_meme = mean([m.meme_score for m in last_24h]) if last_24h else 0
        avg_pump = mean([m.pump_score for m in last_24h]) if last_24h else 0
        
        # Classify spike type
        if spike_magnitude < 2.0:
            return None  # No spike
        
        spike_type = "volume_spike"
        pump_risk = "low"
        
        if avg_meme > 50:
            spike_type = "meme_momentum"
        if avg_pump > 60:
            spike_type = "pump_alert"
            pump_risk = "critical"
        elif avg_pump > 40:
            pump_risk = "high"
        elif avg_pump > 20:
            pump_risk = "medium"
        
        if avg_sentiment > 0.5 and spike_magnitude > 5:
            spike_type = "sentiment_surge"
        
        # Calculate confidence
        confidence = min(100, (spike_magnitude * 10) + (len(last_24h) * 2))
        
        # Generate recommendation
        if pump_risk in ["critical", "high"]:
            recommendation = f"⚠️ HIGH PUMP RISK — Avoid or extreme caution. Coordinated activity detected."
        elif spike_type == "meme_momentum":
            recommendation = f"🎮 Meme stock momentum — High volatility expected. Retail-driven. Trade cautiously."
        elif spike_type == "sentiment_surge" and price_change > 0:
            recommendation = f"📈 Positive sentiment surge — Monitor for continuation. {price_change:+.1f}% price move."
        else:
            recommendation = f"📊 Social volume spike detected — Watch for price action confirmation."
        
        return SpikeEvent(
            ticker=ticker,
            platform="reddit",
            spike_type=spike_type,
            detected_at=datetime.utcnow().isoformat(),
            spike_magnitude=spike_magnitude,
            baseline_mentions=baseline_rate,
            current_mentions=current_rate,
            sentiment_shift=avg_sentiment,
            meme_score=avg_meme,
            pump_risk=pump_risk,
            price_move_24h=price_change,
            volume_spike=volume_spike,
            confidence=confidence,
            evidence=sorted(last_24h, key=lambda m: m.upvotes, reverse=True)[:10],
            recommendation=recommendation
        )
    
    def track_ticker_momentum(self, ticker: str, hours: int = 24) -> Optional[TickerMomentum]:
        """Track social momentum for a specific ticker.
        
        Args:
            ticker: Stock ticker
            hours: Hours of history to analyze
            
        Returns:
            TickerMomentum data or None if insufficient data
        """
        mentions_dict = self.scan_reddit_mentions(hours=hours)
        mentions = mentions_dict.get(ticker, [])
        
        if len(mentions) < 3:
            return None
        
        # Get stock info
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get("longName", ticker)
            current_price = info.get("currentPrice", 0)
            
            hist = stock.history(period="1mo")
            price_24h_ago = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
            price_change = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            volume_30d_avg = hist['Volume'].mean()
            volume_ratio = hist['Volume'].iloc[-1] / volume_30d_avg if volume_30d_avg > 0 else 1.0
        except:
            company_name = ticker
            current_price = 0.0
            price_change = 0.0
            volume_ratio = 1.0
        
        # Time-based metrics
        now = datetime.utcnow()
        mentions_1h = [m for m in mentions if (now - datetime.fromisoformat(m.timestamp)).total_seconds() < 3600]
        mentions_24h = [m for m in mentions if (now - datetime.fromisoformat(m.timestamp)).total_seconds() < 86400]
        
        # Calculate growth rate (compare first half vs second half of period)
        midpoint = now - timedelta(hours=hours/2)
        first_half = [m for m in mentions if datetime.fromisoformat(m.timestamp) < midpoint]
        second_half = [m for m in mentions if datetime.fromisoformat(m.timestamp) >= midpoint]
        growth_rate = ((len(second_half) - len(first_half)) / max(len(first_half), 1)) * 100
        
        # Sentiment metrics
        sentiments = [m.sentiment_score for m in mentions_24h if m.sentiment_score != 0]
        avg_sentiment = mean(sentiments) if sentiments else 0.0
        sentiment_volatility = stdev(sentiments) if len(sentiments) > 1 else 0.0
        
        # Meme/pump scores
        meme_intensity = mean([m.meme_score for m in mentions_24h]) if mentions_24h else 0
        pump_risk = mean([m.pump_score for m in mentions_24h]) if mentions_24h else 0
        
        # Top subreddits
        subreddit_counts = Counter([m.source for m in mentions_24h])
        top_subreddits = subreddit_counts.most_common(5)
        
        # Classify
        if pump_risk > 60:
            classification = "pump_candidate"
        elif meme_intensity > 50:
            classification = "meme_stock"
        elif growth_rate > 200 and len(mentions_24h) > 50:
            classification = "viral"
        else:
            classification = "organic"
        
        return TickerMomentum(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            price_change_24h=price_change,
            volume_ratio=volume_ratio,
            mention_count_1h=len(mentions_1h),
            mention_count_24h=len(mentions_24h),
            mention_growth_rate=growth_rate,
            avg_sentiment=avg_sentiment,
            sentiment_volatility=sentiment_volatility,
            meme_intensity=meme_intensity,
            pump_risk=pump_risk,
            top_subreddits=top_subreddits,
            recent_mentions=sorted(mentions_24h, key=lambda m: m.upvotes, reverse=True)[:5],
            classification=classification
        )
    
    def generate_spike_report(self, top_n: int = 20, hours: int = 24) -> SpikeReport:
        """Generate comprehensive spike detection report.
        
        Args:
            top_n: Number of top tickers to analyze
            hours: Hours of history to scan
            
        Returns:
            SpikeReport with detected spikes and momentum data
        """
        # Scan Reddit for all mentions
        all_mentions = self.scan_reddit_mentions(hours=hours)
        
        # Sort by mention count
        sorted_tickers = sorted(
            all_mentions.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:top_n]
        
        spike_events = []
        top_momentum = []
        active_meme_stocks = []
        pump_alerts = []
        
        for ticker, mentions in sorted_tickers:
            # Detect spikes
            spike = self.detect_spikes(ticker, mentions)
            if spike:
                spike_events.append(spike)
                
                if spike.spike_type == "meme_momentum":
                    active_meme_stocks.append(ticker)
                if spike.pump_risk in ["critical", "high"]:
                    pump_alerts.append(ticker)
            
            # Track momentum
            momentum = self.track_ticker_momentum(ticker, hours=hours)
            if momentum:
                top_momentum.append(momentum)
        
        # Sort momentum by mention growth rate
        top_momentum.sort(key=lambda m: m.mention_growth_rate, reverse=True)
        
        # Generate summary
        summary = f"Scanned {len(all_mentions)} tickers across {len(STOCK_SUBREDDITS)} subreddits. "
        summary += f"Detected {len(spike_events)} sentiment spikes. "
        if active_meme_stocks:
            summary += f"Active meme stocks: {', '.join(active_meme_stocks[:5])}. "
        if pump_alerts:
            summary += f"⚠️ PUMP ALERTS: {', '.join(pump_alerts)}."
        
        return SpikeReport(
            report_date=datetime.utcnow().isoformat(),
            scan_period=f"{hours}h",
            tickers_scanned=len(all_mentions),
            spikes_detected=len(spike_events),
            active_meme_stocks=active_meme_stocks,
            pump_alerts=pump_alerts,
            top_momentum=top_momentum[:10],
            spike_events=spike_events,
            summary=summary
        )


def print_spike_report(report: SpikeReport):
    """Pretty print a spike detection report."""
    print("=" * 70)
    print(f"Social Sentiment Spike Detector — {report.report_date[:10]}")
    print("=" * 70)
    print(f"\nPeriod: {report.scan_period}")
    print(f"Tickers Scanned: {report.tickers_scanned}")
    print(f"Spikes Detected: {report.spikes_detected}")
    print(f"\n{report.summary}\n")
    
    if report.pump_alerts:
        print("\n🚨 PUMP & DUMP ALERTS")
        print("-" * 70)
        for ticker in report.pump_alerts:
            spike = next((s for s in report.spike_events if s.ticker == ticker), None)
            if spike:
                print(f"\n{ticker}: {spike.pump_risk.upper()} RISK")
                print(f"  Magnitude: {spike.spike_magnitude:.1f}x baseline")
                print(f"  Pump Score: {spike.meme_score:.0f}/100")
                print(f"  {spike.recommendation}")
    
    if report.active_meme_stocks:
        print("\n🎮 ACTIVE MEME STOCKS")
        print("-" * 70)
        for ticker in report.active_meme_stocks[:5]:
            momentum = next((m for m in report.top_momentum if m.ticker == ticker), None)
            if momentum:
                print(f"\n{ticker} ({momentum.company_name})")
                print(f"  Price: ${momentum.current_price:.2f} ({momentum.price_change_24h:+.1f}%)")
                print(f"  Mentions 24h: {momentum.mention_count_24h} ({momentum.mention_growth_rate:+.0f}%)")
                print(f"  Sentiment: {momentum.avg_sentiment:+.2f}")
                print(f"  Meme Intensity: {momentum.meme_intensity:.0f}/100")
    
    if report.top_momentum:
        print("\n📈 TOP MOMENTUM TICKERS")
        print("-" * 70)
        for i, momentum in enumerate(report.top_momentum[:10], 1):
            print(f"\n{i}. {momentum.ticker} — {momentum.classification.upper()}")
            print(f"   Mentions: {momentum.mention_count_24h} (+{momentum.mention_growth_rate:.0f}%)")
            print(f"   Price: ${momentum.current_price:.2f} ({momentum.price_change_24h:+.1f}%)")
            print(f"   Sentiment: {momentum.avg_sentiment:+.2f} | Volume: {momentum.volume_ratio:.1f}x")


# CLI-friendly functions
def scan_social_mentions(hours: int = 24) -> Dict[str, List[Dict]]:
    """Scan social media for ticker mentions (CLI wrapper)."""
    detector = SocialSentimentSpikeDetector()
    mentions = detector.scan_reddit_mentions(hours=hours)
    return {
        ticker: [asdict(m) for m in mention_list]
        for ticker, mention_list in mentions.items()
    }


def detect_ticker_spike(ticker: str, hours: int = 24) -> Optional[Dict]:
    """Detect spike for specific ticker (CLI wrapper)."""
    detector = SocialSentimentSpikeDetector()
    mentions_dict = detector.scan_reddit_mentions(hours=hours)
    mentions = mentions_dict.get(ticker, [])
    
    if not mentions:
        return None
    
    spike = detector.detect_spikes(ticker, mentions)
    return asdict(spike) if spike else None


def get_ticker_momentum(ticker: str, hours: int = 24) -> Optional[Dict]:
    """Get social momentum for ticker (CLI wrapper)."""
    detector = SocialSentimentSpikeDetector()
    momentum = detector.track_ticker_momentum(ticker, hours=hours)
    return asdict(momentum) if momentum else None


def generate_report(top_n: int = 20, hours: int = 24) -> Dict:
    """Generate spike report (CLI wrapper)."""
    detector = SocialSentimentSpikeDetector()
    report = detector.generate_spike_report(top_n=top_n, hours=hours)
    return asdict(report)


if __name__ == "__main__":
    # Quick test
    detector = SocialSentimentSpikeDetector()
    report = detector.generate_spike_report(top_n=10, hours=24)
    print_spike_report(report)
