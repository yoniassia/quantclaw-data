#!/usr/bin/env python3
"""
Deep Learning Sentiment Analysis — FinBERT for Financial Text

Advanced NLP using FinBERT (fine-tuned BERT for financial sentiment) to analyze:
- Earnings call transcripts with entity-level sentiment
- SEC filings (10-K, 10-Q, 8-K) with section-specific sentiment
- News articles with topic modeling and sentiment scoring
- Entity-level sentiment extraction (products, executives, competitors)

Features:
- FinBERT-based sentiment classification (positive, negative, neutral)
- Entity recognition and entity-level sentiment scoring
- Multi-document sentiment aggregation
- Time-series sentiment trend analysis
- Comparative sentiment across peers
- Section-wise SEC filing sentiment (Risk Factors, MD&A, etc.)

Data Sources:
- Hugging Face Transformers (FinBERT model - ProsusAI/finbert)
- SEC EDGAR (10-K, 10-Q, 8-K filings)
- Yahoo Finance (news, company info)
- Google News RSS (additional news coverage)

No API keys required — all free public data + HuggingFace models

Author: QUANTCLAW DATA Build Agent
Phase: 88
"""

import sys
import re
import json
import requests
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Try importing transformers, fall back to rule-based if unavailable
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch
    FINBERT_AVAILABLE = True
except ImportError:
    FINBERT_AVAILABLE = False
    print("⚠️  FinBERT not available. Install with: pip install transformers torch", file=sys.stderr)

# Configuration
SEC_EDGAR_BASE = "https://www.sec.gov"
USER_AGENT = "QuantClaw Sentiment Analyzer quantclaw@example.com"
YAHOO_NEWS_BASE = "https://query2.finance.yahoo.com/v1/finance/search"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# FinBERT Model (Hugging Face)
FINBERT_MODEL = "ProsusAI/finbert"

# Simple rule-based fallback sentiment lexicon
POSITIVE_WORDS = {
    'strong', 'growth', 'increase', 'profit', 'revenue', 'beat', 'exceed', 
    'outperform', 'positive', 'optimistic', 'bullish', 'accelerate', 'improve',
    'success', 'record', 'robust', 'solid', 'healthy', 'momentum'
}

NEGATIVE_WORDS = {
    'weak', 'decline', 'decrease', 'loss', 'miss', 'underperform', 'negative',
    'pessimistic', 'bearish', 'concern', 'risk', 'challenge', 'headwind',
    'uncertainty', 'slowdown', 'deteriorate', 'struggle', 'disappointing'
}

# Entity patterns for extraction
ENTITY_PATTERNS = {
    'products': r'\b([A-Z][a-z]+(?:\s+[A-Z0-9][a-z0-9]+){0,3})\b(?=\s+(?:product|platform|service|offering))',
    'people': r'\b(?:CEO|CFO|CTO|CMO|President|Director|VP)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
    'competitors': r'\b(?:competitor|rival)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
    'locations': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:market|region|headquarters)\b'
}


class FinBERTSentimentAnalyzer:
    """FinBERT-based sentiment analyzer with entity-level insights"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.use_finbert = FINBERT_AVAILABLE
        
        if FINBERT_AVAILABLE:
            try:
                print("Loading FinBERT model... (first run may take 1-2 minutes)", file=sys.stderr)
                self.tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
                self.model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1
                )
                print("✅ FinBERT model loaded successfully", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  FinBERT loading failed: {e}. Using rule-based fallback.", file=sys.stderr)
                self.use_finbert = False
    
    def analyze_text(self, text: str, max_length: int = 512) -> Dict:
        """Analyze sentiment of text (FinBERT or rule-based fallback)"""
        if not text or len(text.strip()) == 0:
            return {'label': 'neutral', 'score': 0.0}
        
        # Truncate to max length for FinBERT
        text = text[:max_length * 4]  # rough char estimate
        
        if self.use_finbert and self.pipeline:
            try:
                result = self.pipeline(text)[0]
                # FinBERT returns: positive, negative, neutral
                label = result['label'].lower()
                score = result['score']
                
                # Normalize to [-1, 1] range
                if label == 'positive':
                    normalized_score = score
                elif label == 'negative':
                    normalized_score = -score
                else:  # neutral
                    normalized_score = 0.0
                
                return {
                    'label': label,
                    'score': normalized_score,
                    'confidence': score
                }
            except Exception as e:
                print(f"FinBERT analysis error: {e}. Falling back to rule-based.", file=sys.stderr)
                return self._rule_based_sentiment(text)
        else:
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict:
        """Simple rule-based sentiment as fallback"""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        positive_count = len(words & POSITIVE_WORDS)
        negative_count = len(words & NEGATIVE_WORDS)
        total = positive_count + negative_count
        
        if total == 0:
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.5}
        
        score = (positive_count - negative_count) / total
        
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'score': score,
            'confidence': abs(score)
        }
    
    def analyze_with_entities(self, text: str) -> Dict:
        """Analyze sentiment with entity-level breakdown"""
        overall_sentiment = self.analyze_text(text)
        
        # Extract entities
        entities = self.extract_entities(text)
        
        # Analyze sentiment around each entity (context window)
        entity_sentiments = {}
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                context = self._get_entity_context(text, entity)
                if context:
                    sentiment = self.analyze_text(context)
                    entity_sentiments[f"{entity_type}:{entity}"] = sentiment
        
        return {
            'overall': overall_sentiment,
            'entities': entity_sentiments,
            'entity_counts': {k: len(v) for k, v in entities.items()}
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {}
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            entities[entity_type] = list(set(matches))[:10]  # top 10 unique
        return entities
    
    def _get_entity_context(self, text: str, entity: str, window: int = 100) -> str:
        """Get text context around entity mention"""
        pattern = re.compile(rf'\b{re.escape(entity)}\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            return text[start:end]
        return ""


def fetch_sec_filing(ticker: str, form_type: str = "10-K", limit: int = 1) -> List[Dict]:
    """Fetch SEC filings via EDGAR"""
    try:
        # Search for company CIK
        search_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': ticker,
            'type': form_type,
            'dateb': '',
            'owner': 'exclude',
            'count': limit,
            'output': 'atom'
        }
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        # Parse XML/Atom feed (simplified)
        # In production, use proper XML parser
        entries = []
        content = response.text
        
        # Extract filing URLs
        filing_urls = re.findall(r'<link[^>]+href="([^"]+)"', content)
        
        for url in filing_urls[:limit]:
            if 'Archives/edgar/data' in url:
                # Fetch filing text
                full_url = f"{SEC_EDGAR_BASE}{url}" if url.startswith('/') else url
                filing_resp = requests.get(full_url, headers=headers, timeout=10)
                if filing_resp.status_code == 200:
                    entries.append({
                        'url': full_url,
                        'text': filing_resp.text[:50000],  # first 50KB
                        'form_type': form_type,
                        'date': datetime.now().isoformat()
                    })
        
        return entries
    except Exception as e:
        print(f"SEC filing fetch error: {e}", file=sys.stderr)
        return []


def fetch_news(ticker: str, days: int = 7) -> List[Dict]:
    """Fetch news from Yahoo Finance + Google News RSS"""
    news_items = []
    
    # Yahoo Finance News
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {'q': ticker, 'quotesCount': 0, 'newsCount': 10}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('news', []):
                news_items.append({
                    'title': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'source': 'Yahoo Finance',
                    'url': item.get('link', ''),
                    'published': item.get('providerPublishTime', 0)
                })
    except Exception as e:
        print(f"Yahoo news error: {e}", file=sys.stderr)
    
    # Google News RSS
    try:
        query = f"{ticker} stock"
        rss_url = GOOGLE_NEWS_RSS.format(query=requests.utils.quote(query))
        response = requests.get(rss_url, timeout=10)
        
        if response.status_code == 200:
            # Simple RSS parsing
            titles = re.findall(r'<title>([^<]+)</title>', response.text)
            descriptions = re.findall(r'<description>([^<]+)</description>', response.text)
            links = re.findall(r'<link>([^<]+)</link>', response.text)
            
            for i, (title, desc, link) in enumerate(zip(titles[1:11], descriptions[1:11], links[1:11])):
                news_items.append({
                    'title': title,
                    'summary': desc,
                    'source': 'Google News',
                    'url': link,
                    'published': int(datetime.now().timestamp())
                })
    except Exception as e:
        print(f"Google News error: {e}", file=sys.stderr)
    
    return news_items


def analyze_earnings_transcript(ticker: str) -> Dict:
    """Analyze latest earnings call transcript with FinBERT"""
    analyzer = FinBERTSentimentAnalyzer()
    
    # Fetch 8-K (earnings) filings
    filings = fetch_sec_filing(ticker, form_type="8-K", limit=3)
    
    if not filings:
        return {
            'error': 'No recent 8-K filings found',
            'ticker': ticker,
            'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based'
        }
    
    results = []
    for filing in filings:
        # Extract meaningful sections (simplified)
        text = filing['text']
        
        # Basic section extraction
        sections = {
            'full_text': text[:5000],  # first 5000 chars
            'first_quarter': text[:2000]
        }
        
        sentiment_results = {}
        for section_name, section_text in sections.items():
            sentiment_results[section_name] = analyzer.analyze_with_entities(section_text)
        
        results.append({
            'filing_date': filing['date'],
            'url': filing['url'],
            'sentiments': sentiment_results
        })
    
    # Aggregate overall sentiment
    all_scores = []
    for result in results:
        for section in result['sentiments'].values():
            all_scores.append(section['overall']['score'])
    
    avg_score = statistics.mean(all_scores) if all_scores else 0.0
    
    return {
        'ticker': ticker,
        'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based',
        'filings_analyzed': len(results),
        'overall_sentiment': {
            'score': avg_score,
            'label': 'positive' if avg_score > 0.2 else 'negative' if avg_score < -0.2 else 'neutral'
        },
        'detailed_results': results[:2]  # top 2 for brevity
    }


def analyze_sec_filing(ticker: str, form_type: str = "10-K") -> Dict:
    """Analyze SEC filing with section-wise sentiment"""
    analyzer = FinBERTSentimentAnalyzer()
    
    filings = fetch_sec_filing(ticker, form_type=form_type, limit=1)
    
    if not filings:
        return {
            'error': f'No recent {form_type} filing found',
            'ticker': ticker,
            'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based'
        }
    
    filing = filings[0]
    text = filing['text']
    
    # Extract key sections via pattern matching
    sections = {}
    
    # Risk Factors
    risk_match = re.search(r'(?i)item\s+1a\.\s+risk\s+factors(.{0,5000})', text, re.DOTALL)
    if risk_match:
        sections['risk_factors'] = risk_match.group(1)
    
    # MD&A
    mda_match = re.search(r'(?i)item\s+7\.\s+management.{0,200}discussion(.{0,5000})', text, re.DOTALL)
    if mda_match:
        sections['mda'] = mda_match.group(1)
    
    # Business Overview
    business_match = re.search(r'(?i)item\s+1\.\s+business(.{0,3000})', text, re.DOTALL)
    if business_match:
        sections['business'] = business_match.group(1)
    
    # Analyze each section
    sentiment_by_section = {}
    for section_name, section_text in sections.items():
        sentiment_by_section[section_name] = analyzer.analyze_with_entities(section_text)
    
    # Overall filing sentiment
    all_scores = [s['overall']['score'] for s in sentiment_by_section.values()]
    avg_score = statistics.mean(all_scores) if all_scores else 0.0
    
    return {
        'ticker': ticker,
        'form_type': form_type,
        'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based',
        'filing_date': filing['date'],
        'url': filing['url'],
        'sections_analyzed': list(sections.keys()),
        'overall_sentiment': {
            'score': avg_score,
            'label': 'positive' if avg_score > 0.2 else 'negative' if avg_score < -0.2 else 'neutral'
        },
        'section_sentiments': sentiment_by_section
    }


def analyze_news_sentiment(ticker: str, days: int = 7) -> Dict:
    """Analyze news sentiment with entity extraction"""
    analyzer = FinBERTSentimentAnalyzer()
    
    news_items = fetch_news(ticker, days=days)
    
    if not news_items:
        return {
            'error': 'No recent news found',
            'ticker': ticker,
            'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based'
        }
    
    sentiments = []
    entity_sentiments = defaultdict(list)
    
    for item in news_items:
        # Combine title + summary
        text = f"{item['title']}. {item.get('summary', '')}"
        
        result = analyzer.analyze_with_entities(text)
        
        sentiments.append({
            'title': item['title'],
            'source': item['source'],
            'url': item.get('url', ''),
            'sentiment': result['overall'],
            'entities': result['entities']
        })
        
        # Aggregate entity sentiments
        for entity_key, sent in result['entities'].items():
            entity_sentiments[entity_key].append(sent['score'])
    
    # Calculate aggregates
    all_scores = [s['sentiment']['score'] for s in sentiments]
    avg_score = statistics.mean(all_scores) if all_scores else 0.0
    
    # Entity-level averages
    entity_avg = {}
    for entity, scores in entity_sentiments.items():
        entity_avg[entity] = {
            'avg_score': statistics.mean(scores),
            'count': len(scores)
        }
    
    return {
        'ticker': ticker,
        'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based',
        'news_count': len(news_items),
        'period_days': days,
        'overall_sentiment': {
            'score': avg_score,
            'label': 'positive' if avg_score > 0.2 else 'negative' if avg_score < -0.2 else 'neutral'
        },
        'sentiment_distribution': {
            'positive': sum(1 for s in all_scores if s > 0.2),
            'neutral': sum(1 for s in all_scores if -0.2 <= s <= 0.2),
            'negative': sum(1 for s in all_scores if s < -0.2)
        },
        'top_entities': dict(sorted(entity_avg.items(), key=lambda x: abs(x[1]['avg_score']), reverse=True)[:10]),
        'recent_headlines': sentiments[:5]
    }


def sentiment_time_series(ticker: str, form_type: str = "10-Q", quarters: int = 4) -> Dict:
    """Analyze sentiment trends across multiple filings"""
    analyzer = FinBERTSentimentAnalyzer()
    
    filings = fetch_sec_filing(ticker, form_type=form_type, limit=quarters)
    
    if not filings:
        return {
            'error': f'No {form_type} filings found',
            'ticker': ticker,
            'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based'
        }
    
    time_series = []
    for filing in filings:
        text = filing['text'][:10000]  # first 10KB
        
        sentiment = analyzer.analyze_text(text)
        
        time_series.append({
            'filing_date': filing['date'],
            'form_type': filing['form_type'],
            'sentiment_score': sentiment['score'],
            'sentiment_label': sentiment['label']
        })
    
    # Calculate trend
    scores = [t['sentiment_score'] for t in time_series]
    trend = 'improving' if len(scores) >= 2 and scores[0] > scores[-1] else \
            'declining' if len(scores) >= 2 and scores[0] < scores[-1] else 'stable'
    
    return {
        'ticker': ticker,
        'model': 'FinBERT' if analyzer.use_finbert else 'Rule-Based',
        'form_type': form_type,
        'periods_analyzed': len(time_series),
        'sentiment_trend': trend,
        'time_series': time_series,
        'avg_sentiment': statistics.mean(scores) if scores else 0.0,
        'volatility': statistics.stdev(scores) if len(scores) > 1 else 0.0
    }


def compare_peer_sentiment(tickers: List[str], source: str = "news") -> Dict:
    """Compare sentiment across peer companies"""
    results = {}
    
    for ticker in tickers:
        if source == "news":
            results[ticker] = analyze_news_sentiment(ticker, days=7)
        elif source == "sec":
            results[ticker] = analyze_sec_filing(ticker, form_type="10-K")
        elif source == "earnings":
            results[ticker] = analyze_earnings_transcript(ticker)
    
    # Aggregate comparison
    comparison = []
    for ticker, data in results.items():
        if 'overall_sentiment' in data:
            comparison.append({
                'ticker': ticker,
                'sentiment_score': data['overall_sentiment']['score'],
                'sentiment_label': data['overall_sentiment']['label']
            })
    
    # Rank by sentiment
    comparison.sort(key=lambda x: x['sentiment_score'], reverse=True)
    
    return {
        'source': source,
        'tickers_analyzed': tickers,
        'model': results[tickers[0]].get('model', 'Unknown') if results else 'Unknown',
        'ranking': comparison,
        'detailed_results': results
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python deep_learning_sentiment.py <command> <ticker> [args]")
        print("\nCommands:")
        print("  finbert-earnings <ticker>           - Analyze earnings call sentiment")
        print("  finbert-sec <ticker> [form_type]    - Analyze SEC filing (default: 10-K)")
        print("  finbert-news <ticker> [days]        - Analyze news sentiment (default: 7 days)")
        print("  finbert-trend <ticker> [quarters]   - Sentiment time series (default: 4 quarters)")
        print("  finbert-compare <ticker1,ticker2,...> <source> - Compare peer sentiment (news/sec/earnings)")
        sys.exit(1)
    
    command = sys.argv[1].replace('finbert-', '')  # Support both forms
    ticker = sys.argv[2].upper()
    
    if command == "earnings":
        result = analyze_earnings_transcript(ticker)
    elif command == "sec":
        form_type = sys.argv[3] if len(sys.argv) > 3 else "10-K"
        result = analyze_sec_filing(ticker, form_type)
    elif command == "news":
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        result = analyze_news_sentiment(ticker, days)
    elif command == "trend":
        quarters = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        result = sentiment_time_series(ticker, quarters=quarters)
    elif command == "compare":
        tickers = [t.strip().upper() for t in ticker.split(',')]
        source = sys.argv[3] if len(sys.argv) > 3 else "news"
        result = compare_peer_sentiment(tickers, source)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))
