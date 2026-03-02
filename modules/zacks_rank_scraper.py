"""
Zacks Rank Scraper — Zacks.com Stock Research Ranks (1-5 Scale)

Scrapes Zacks Rank for popular US stocks from individual stock quote pages.
Zacks Rank: 1 (Strong Buy) > 2 (Buy) > 3 (Hold) > 4 (Sell) > 5 (Strong Sell)
Data source: https://www.zacks.com/stock/quote/[TICKER]
Update frequency: Daily (ranks change weekly, but scrape anytime)
Use cases:
- Stock screening by rank
- Portfolio rank average
- Rank changes tracking
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
import time
import re
from typing import Optional, List, Dict
import sys
import argparse

CACHE_DIR = Path(__file__).parent.parent / "cache" / "zacks_rank"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.zacks.com"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

POPULAR_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO',
    'JPM', 'UNH', 'V', 'XOM', 'MA', 'PG', 'JNJ', 'HD', 'MRK', 'COST',
    'ABBV', 'NFLX', 'AMD', 'WMT', 'BAC', 'CVX', 'KO', 'ORCL', 'ABT', 'CRM',
    'TMO', 'ACN', 'LIN', 'SPGI', 'NEE', 'WFC', 'DHR', 'TXN', 'PM', 'C',
    'AMGN', 'RTX', 'HON', 'INTU', 'GS', 'CAT', 'DIS', 'AXP', 'PFE', 'IBM',
    'NOW', 'GE', 'UPS', 'SYK', 'COP', 'SCHW', 'VRTX', 'MDT', 'BSX', 'GILD'
]

def get_session():
    session = requests.Session()
    ua = USER_AGENTS[hash(time.time()) % len(USER_AGENTS)]
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def fetch_single_rank(session, ticker, retries=3):
    url = f"{BASE_URL}/stock/quote/{ticker}"
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            rank_elem = soup.find('span', class_=re.compile(r'rank.*num|rank.*value', re.I)) or \
                        soup.find('div', attrs={'data-zacks-rank': True}) or \
                        soup.find(string=re.compile(r'Zacks Rank #\d{1,2}'))
            if rank_elem:
                rank_text = rank_elem.parent.get_text(strip=True) if not rank_elem.name == 'span' else rank_elem.get_text(strip=True)
                rank_match = re.search(r'#(\d{1,2})', rank_text)
                rank_num = int(rank_match.group(1)) if rank_match else None
                rank_desc_match = re.search(r'\(([^)]+)\)', rank_text)
                rank_desc = rank_desc_match.group(1) if rank_desc_match else ''
                
                price_elem = soup.find('span', class_=re.compile(r'last-price|current-price', re.I))
                price = price_elem.get_text(strip=True).replace('$', '').replace(',', '') if price_elem else None
                price = float(price) if price else None
                
                change_elem = soup.find('span', class_=re.compile(r'change|net-change', re.I))
                change = change_elem.get_text(strip=True) if change_elem else ''
                
                return {
                    'ticker': ticker,
                    'rank': rank_num,
                    'rank_description': rank_desc,
                    'rank_text': rank_text,
                    'price': price,
                    'change_pct': change,
                    'scrape_time': datetime.now().isoformat(),
                    'url': url
                }
            time.sleep(1)
        except Exception as e:
            time.sleep(2 ** attempt)
    return None

def fetch_all_ranks(force_refresh=False):
    cache_path = CACHE_DIR / "ranks_latest.json"
    if not force_refresh and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    session = get_session()
    results = []
    for i, ticker in enumerate(POPULAR_TICKERS):
        print(f"Fetching {ticker} ({i+1}/{len(POPULAR_TICKERS)})...")
        result = fetch_single_rank(session, ticker)
        if result:
            results.append(result)
        time.sleep(1.5)
    
    if results:
        with open(cache_path, 'w') as f:
            json.dump(results, f, indent=2)
    return results

def get_data(force_refresh=False):
    results = fetch_all_ranks(force_refresh)
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results)
    if not df.empty:
        df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
        df = df.sort_values('rank')
        df['scrape_date'] = pd.to_datetime(df['scrape_time']).dt.date
    return df

def get_top_strong_buys(df, n=10):
    return df[df['rank'] == 1][['ticker', 'rank_description', 'price', 'change_pct']].head(n)

def cli_summary():
    df = get_data()
    if df.empty:
        print("No data available")
        return
    print("\\n=== Zacks Rank Summary ===")
    print(f"Data for {len(df)} stocks, scraped {df['scrape_date'].iloc[0]}")
    print(f"Average Rank: {df['rank'].mean():.1f}")
    print(f"Strong Buy (#1): {len(df[df['rank'] == 1])}")
    print(f"Buy (#2): {len(df[df['rank'] == 2])}")
    print(f"Hold (#3): {len(df[df['rank'] == 3])}")
    print("\\nTop Strong Buys:")
    top = get_top_strong_buys(df, 5)
    print(top.to_string(index=False))

def cli_top_strong_buys(n=10):
    df = get_data()
    top = get_top_strong_buys(df, n)
    print(f"\\nTop {n} Zacks #1 Strong Buy Stocks:")
    print(top.to_string(index=False))

def cli_rank_for_ticker(ticker):
    session = get_session()
    result = fetch_single_rank(session, ticker)
    if result:
        print(f"\\nZacks Rank for {ticker}:")
        print(f"Rank: {result['rank']} ({result['rank_description']})")
        if result['price']:
            print(f"Price: ${result['price']:.2f}")
        print(f"Change: {result['change_pct']}")
    else:
        print(f"No data for {ticker}")

def cli_average_rank():
    df = get_data()
    if df.empty:
        print("No data")
        return
    print(f"\\nAverage Zacks Rank: {df['rank'].mean():.2f}")
    print("Rank Distribution:")
    print(df['rank'].value_counts().sort_index().to_string())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Zacks Rank Scraper CLI')
    parser.add_argument('command', choices=['summary', 'top1', 'ticker', 'avg'], nargs='?', default='summary')
    parser.add_argument('--n', type=int, default=10)
    parser.add_argument('--ticker', help='Specific ticker')
    args = parser.parse_args()
    
    if args.command == 'summary':
        cli_summary()
    elif args.command == 'top1':
        cli_top_strong_buys(args.n)
    elif args.command == 'ticker':
        if args.ticker:
            cli_rank_for_ticker(args.ticker)
        else:
            print("Need --ticker")
            sys.exit(1)
    elif args.command == 'avg':
        cli_average_rank()
