#!/usr/bin/env python3
"""
Core Market Data Module
Real-time prices, SEC EDGAR filings, news sentiment, caching layer

Free APIs:
- Yahoo Finance (prices, quotes, fundamentals)
- SEC EDGAR RSS (filings)
- Google News RSS (sentiment)
- Redis caching layer for performance
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
import json
import hashlib
from typing import Optional, Dict, Any, List
import feedparser
from bs4 import BeautifulSoup
import re

# Simple in-memory cache (replace with Redis in production)
_cache: Dict[str, tuple[Any, datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

def _cache_key(*args) -> str:
    """Generate cache key from arguments"""
    return hashlib.md5(str(args).encode()).hexdigest()

def _get_cached(key: str) -> Optional[Any]:
    """Get from cache if not expired"""
    if key in _cache:
        value, timestamp = _cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            return value
    return None

def _set_cache(key: str, value: Any):
    """Store in cache with timestamp"""
    _cache[key] = (value, datetime.now())

def get_quote(symbol: str) -> Dict[str, Any]:
    """
    Get real-time quote for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
    
    Returns:
        dict: Current price, change, volume, market cap, etc.
    """
    cache_key = _cache_key('quote', symbol)
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            'symbol': symbol.upper(),
            'price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'change': info.get('regularMarketChange'),
            'change_percent': info.get('regularMarketChangePercent'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'beta': info.get('beta'),
            '52w_high': info.get('fiftyTwoWeekHigh'),
            '52w_low': info.get('fiftyTwoWeekLow'),
            'timestamp': datetime.now().isoformat()
        }
        
        _set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}

def get_historical_prices(symbol: str, period: str = '1mo', interval: str = '1d') -> List[Dict]:
    """
    Get historical OHLCV data
    
    Args:
        symbol: Stock ticker
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    
    Returns:
        list: OHLCV data points
    """
    cache_key = _cache_key('historical', symbol, period, interval)
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        result = []
        for index, row in df.iterrows():
            result.append({
                'date': index.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
            })
        
        _set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol}]

def get_sec_filings(symbol: str, filing_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get recent SEC EDGAR filings
    
    Args:
        symbol: Stock ticker
        filing_type: Filter by type (10-K, 10-Q, 8-K, DEF 14A, 13D, 13F, S-1, etc)
        limit: Max number of filings to return
    
    Returns:
        list: Recent filings with links and dates
    """
    cache_key = _cache_key('sec_filings', symbol, filing_type, limit)
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        # Get CIK from Yahoo Finance
        ticker = yf.Ticker(symbol)
        cik = ticker.info.get('cik')
        if not cik:
            return [{'error': 'CIK not found for symbol', 'symbol': symbol}]
        
        # Pad CIK to 10 digits
        cik_padded = str(cik).zfill(10)
        
        # SEC EDGAR RSS feed
        rss_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        headers = {
            'User-Agent': 'QuantClaw Data quantclaw@example.com'
        }
        
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        filings = data.get('filings', {}).get('recent', {})
        
        result = []
        forms = filings.get('form', [])
        filing_dates = filings.get('filingDate', [])
        accession_numbers = filings.get('accessionNumber', [])
        primary_docs = filings.get('primaryDocument', [])
        
        for i in range(min(len(forms), limit * 3)):  # Get extra in case of filtering
            form = forms[i]
            
            # Filter by filing type if specified
            if filing_type and form != filing_type:
                continue
            
            accession = accession_numbers[i].replace('-', '')
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}"
            
            result.append({
                'filing_type': form,
                'filing_date': filing_dates[i],
                'accession_number': accession_numbers[i],
                'document_url': doc_url
            })
            
            if len(result) >= limit:
                break
        
        _set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol}]

def get_news_sentiment(symbol: str, limit: int = 10) -> List[Dict]:
    """
    Get recent news with sentiment analysis
    
    Args:
        symbol: Stock ticker or company name
        limit: Max articles to return
    
    Returns:
        list: News articles with title, link, published date, sentiment
    """
    cache_key = _cache_key('news', symbol, limit)
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        # Get company name from Yahoo Finance
        ticker = yf.Ticker(symbol)
        company_name = ticker.info.get('longName', symbol)
        
        # Google News RSS feed
        search_query = f"{company_name} stock"
        rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(search_query)}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        
        result = []
        for entry in feed.entries[:limit]:
            # Simple sentiment heuristic (can be replaced with FinBERT)
            title = entry.title.lower()
            sentiment = 'neutral'
            
            positive_words = ['surge', 'rally', 'gain', 'profit', 'beat', 'upgrade', 'bullish', 'soar', 'jump', 'climb']
            negative_words = ['plunge', 'crash', 'loss', 'miss', 'downgrade', 'bearish', 'drop', 'fall', 'decline', 'slump']
            
            pos_count = sum(1 for word in positive_words if word in title)
            neg_count = sum(1 for word in negative_words if word in title)
            
            if pos_count > neg_count:
                sentiment = 'positive'
            elif neg_count > pos_count:
                sentiment = 'negative'
            
            result.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', ''),
                'source': entry.get('source', {}).get('title', 'Unknown'),
                'sentiment': sentiment,
                'sentiment_score': pos_count - neg_count
            })
        
        _set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol}]

def get_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Get company fundamentals
    
    Args:
        symbol: Stock ticker
    
    Returns:
        dict: Revenue, earnings, ratios, margins, etc.
    """
    cache_key = _cache_key('fundamentals', symbol)
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            'symbol': symbol.upper(),
            'company_name': info.get('longName'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'revenue': info.get('totalRevenue'),
            'revenue_growth': info.get('revenueGrowth'),
            'ebitda': info.get('ebitda'),
            'net_income': info.get('netIncomeToCommon'),
            'eps': info.get('trailingEps'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'free_cash_flow': info.get('freeCashflow'),
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
        }
        
        _set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}

def clear_cache():
    """Clear all cached data"""
    global _cache
    _cache = {}
    return {'status': 'cache cleared', 'timestamp': datetime.now().isoformat()}

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python core_market_data.py <command> <symbol> [options]")
        print("\nCommands:")
        print("  quote SYMBOL              Get real-time quote")
        print("  historical SYMBOL [1mo]   Get historical prices")
        print("  sec SYMBOL [10-K]         Get SEC filings")
        print("  news SYMBOL               Get news with sentiment")
        print("  fundamentals SYMBOL       Get company fundamentals")
        print("  clear-cache               Clear all cached data")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'clear-cache':
        print(json.dumps(clear_cache(), indent=2))
    elif len(sys.argv) < 3:
        print("Error: Symbol required")
        sys.exit(1)
    else:
        symbol = sys.argv[2]
        
        if command == 'quote':
            print(json.dumps(get_quote(symbol), indent=2))
        elif command == 'historical':
            period = sys.argv[3] if len(sys.argv) > 3 else '1mo'
            print(json.dumps(get_historical_prices(symbol, period), indent=2))
        elif command == 'sec':
            filing_type = sys.argv[3] if len(sys.argv) > 3 else None
            print(json.dumps(get_sec_filings(symbol, filing_type), indent=2))
        elif command == 'news':
            print(json.dumps(get_news_sentiment(symbol), indent=2))
        elif command == 'fundamentals':
            print(json.dumps(get_fundamentals(symbol), indent=2))
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
