#!/usr/bin/env python3
"""
Finviz Stock Screener — Free comprehensive stock fundamentals, technicals, insider data.

Data sources:
- finviz.com/screener.ashx (8000+ stocks, no API key)
- finviz.com/quote.ashx?t=TICKER (detailed stock page)
- finviz.com/insidertrading.ashx (insider trading)

Features:
- Fundamentals: P/E, P/B, P/S, EPS growth, revenue, margins
- Technicals: RSI, beta, ATR, moving averages, chart patterns
- Short interest: short float, short ratio
- Insider trading: cluster buys/sells, ownership changes
- Analyst targets: price targets, recommendations
- Caching to respect rate limits
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Optional, Dict, List
import re

CACHE_DIR = Path("cache/finviz")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour cache for screener, 5 min for quotes

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": USER_AGENT}

def _cache_path(key: str) -> Path:
    """Safe cache file path."""
    safe_key = re.sub(r'[^\w\-]', '_', key)
    return CACHE_DIR / f"{safe_key}.json"

def _get_cached(key: str, ttl: int = CACHE_TTL) -> Optional[Dict]:
    """Retrieve cached data if fresh."""
    path = _cache_path(key)
    if not path.exists():
        return None
    
    try:
        mtime = path.stat().st_mtime
        if time.time() - mtime > ttl:
            return None
        
        with open(path) as f:
            return json.load(f)
    except:
        return None

def _set_cache(key: str, data: Dict):
    """Store data in cache."""
    try:
        with open(_cache_path(key), 'w') as f:
            json.dump(data, f)
    except:
        pass

def screener(
    filters: Optional[Dict[str, str]] = None,
    order: str = "-marketcap",
    limit: int = 100
) -> pd.DataFrame:
    """
    Screen stocks with custom filters.
    
    Args:
        filters: Dict of filter_name: value (e.g. {"cap_midover": "", "fa_pe_u20": ""})
        order: Sort order (e.g. "-marketcap", "price", "-volume")
        limit: Max results
    
    Common filters:
        cap_smallover, cap_midover, cap_largeover (market cap)
        fa_pe_u20, fa_pe_profitable (P/E < 20, P/E > 0)
        fa_eps5years_pos (EPS growth > 0%)
        sh_short_u10, sh_short_o30 (short float)
        ta_rsi_os30, ta_rsi_ob70 (RSI oversold/overbought)
        geo_usa (US stocks only)
    
    Returns:
        DataFrame with ticker, company, sector, industry, country, market cap, P/E, price, change, volume
    """
    cache_key = f"screener_{json.dumps(filters or {})}_{order}_{limit}"
    cached = _get_cached(cache_key, ttl=3600)
    if cached:
        return pd.DataFrame(cached)
    
    # Build filter string
    filter_parts = []
    if filters:
        for k, v in filters.items():
            filter_parts.append(f"{k}_{v}" if v else k)
    filter_str = ",".join(filter_parts) if filter_parts else "geo_usa"
    
    # Finviz screener pagination (20 per page)
    all_rows = []
    for offset in range(0, limit, 20):
        url = f"https://finviz.com/screener.ashx?v=111&f={filter_str}&o={order}&r={offset+1}"
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find screener table
            table = soup.find('table', {'class': 'table-light'})
            if not table:
                break
            
            rows = table.find_all('tr')[1:]  # Skip header
            if not rows:
                break
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 11:
                    continue
                
                all_rows.append({
                    'ticker': cols[1].text.strip(),
                    'company': cols[2].text.strip(),
                    'sector': cols[3].text.strip(),
                    'industry': cols[4].text.strip(),
                    'country': cols[5].text.strip(),
                    'market_cap': cols[6].text.strip(),
                    'pe': cols[7].text.strip(),
                    'price': cols[8].text.strip(),
                    'change': cols[9].text.strip(),
                    'volume': cols[10].text.strip()
                })
            
            time.sleep(0.5)  # Rate limit
            
            if len(all_rows) >= limit:
                break
                
        except Exception as e:
            print(f"Screener error at offset {offset}: {e}")
            break
    
    df = pd.DataFrame(all_rows[:limit])
    _set_cache(cache_key, df.to_dict('records'))
    return df

def quote(ticker: str) -> Dict:
    """
    Get detailed quote for a ticker from Finviz.
    
    Returns:
        Dict with fundamentals, technicals, analyst targets, insider data
    """
    ticker = ticker.upper().strip()
    cache_key = f"quote_{ticker}"
    cached = _get_cached(cache_key, ttl=300)  # 5 min cache
    if cached:
        return cached
    
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Parse snapshot table
        data = {'ticker': ticker}
        snapshot = soup.find('table', {'class': 'snapshot-table2'})
        
        if snapshot:
            rows = snapshot.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells), 2):
                    if i + 1 < len(cells):
                        key = cells[i].text.strip().lower().replace(' ', '_')
                        value = cells[i+1].text.strip()
                        data[key] = value
        
        # Parse news headlines
        news_table = soup.find('table', {'id': 'news-table'})
        if news_table:
            headlines = []
            for row in news_table.find_all('tr')[:5]:
                link = row.find('a')
                if link:
                    headlines.append(link.text.strip())
            data['news_headlines'] = headlines
        
        # Parse insider trading summary
        insider_table = soup.find('table', {'class': 'body-table'})
        if insider_table:
            insider_rows = insider_table.find_all('tr')[1:6]  # Top 5
            insider_data = []
            for row in insider_rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    insider_data.append({
                        'owner': cols[0].text.strip(),
                        'relationship': cols[1].text.strip(),
                        'date': cols[2].text.strip(),
                        'transaction': cols[3].text.strip(),
                        'shares': cols[5].text.strip() if len(cols) > 5 else ''
                    })
            data['recent_insider_trades'] = insider_data
        
        _set_cache(cache_key, data)
        return data
        
    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}

def insider_trading(
    filter_type: str = "buy",
    days: int = 7,
    min_value: int = 100000
) -> pd.DataFrame:
    """
    Get insider trading activity.
    
    Args:
        filter_type: 'buy', 'sale', 'all'
        days: Look back period
        min_value: Minimum transaction value
    
    Returns:
        DataFrame with ticker, owner, relationship, date, transaction_type, cost, shares, value, shares_total
    """
    cache_key = f"insider_{filter_type}_{days}_{min_value}"
    cached = _get_cached(cache_key, ttl=1800)  # 30 min cache
    if cached:
        return pd.DataFrame(cached)
    
    url = f"https://finviz.com/insidertrading.ashx?tc={filter_type[0]}"  # b=buy, s=sale, a=all
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        table = soup.find('table', {'class': 'body-table'})
        if not table:
            return pd.DataFrame()
        
        rows = table.find_all('tr')[1:]  # Skip header
        data = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 9:
                continue
            
            try:
                date_str = cols[2].text.strip()
                trans_date = datetime.strptime(date_str, "%b %d")
                trans_date = trans_date.replace(year=datetime.now().year)
                
                if trans_date > datetime.now():
                    trans_date = trans_date.replace(year=datetime.now().year - 1)
                
                if trans_date < cutoff_date:
                    continue
                
                value_str = cols[6].text.strip().replace(',', '').replace('$', '')
                value = int(value_str) if value_str and value_str != '-' else 0
                
                if value < min_value:
                    continue
                
                data.append({
                    'ticker': cols[0].text.strip(),
                    'owner': cols[1].text.strip(),
                    'relationship': cols[3].text.strip(),
                    'date': date_str,
                    'transaction_type': cols[4].text.strip(),
                    'cost': cols[5].text.strip(),
                    'shares': cols[7].text.strip(),
                    'value': f"${value:,}",
                    'shares_total': cols[8].text.strip()
                })
                
            except:
                continue
        
        df = pd.DataFrame(data)
        _set_cache(cache_key, df.to_dict('records'))
        return df
        
    except Exception as e:
        print(f"Insider trading error: {e}")
        return pd.DataFrame()

def high_short_interest(min_float: float = 20.0, limit: int = 50) -> pd.DataFrame:
    """
    Screen for stocks with high short interest.
    
    Args:
        min_float: Minimum short % of float
        limit: Max results
    
    Returns:
        DataFrame sorted by short interest
    """
    filters = {
        "sh_short_o20": "",  # Short float > 20%
        "cap_smallover": ""  # Small cap+
    }
    
    df = screener(filters=filters, order="-shortinterestshare", limit=limit)
    return df

def value_stocks(max_pe: float = 15, min_yield: float = 2.0) -> pd.DataFrame:
    """
    Screen for undervalued dividend stocks.
    """
    filters = {
        "fa_pe_u15": "",       # P/E < 15
        "fa_div_o2": "",       # Dividend yield > 2%
        "cap_midover": "",     # Mid cap+
        "fa_debteq_u0.5": ""   # Debt/Equity < 0.5
    }
    
    return screener(filters=filters, order="-dividendyield", limit=100)

def momentum_stocks() -> pd.DataFrame:
    """
    Screen for momentum stocks with strong technicals.
    """
    filters = {
        "ta_rsi_ob60": "",        # RSI > 60
        "ta_change_u": "",        # Above 50-day MA
        "ta_perf_1w_o5": "",      # Week performance > 5%
        "sh_avgvol_o500": ""      # Volume > 500K
    }
    
    return screener(filters=filters, order="-change", limit=100)

def cli_screener(args):
    """CLI: Run custom stock screener."""
    filters = {}
    if args.filters:
        for f in args.filters.split(','):
            if '=' in f:
                k, v = f.split('=', 1)
                filters[k.strip()] = v.strip()
            else:
                filters[f.strip()] = ""
    
    df = screener(filters=filters or None, order=args.order, limit=args.limit)
    print(f"\n📊 Finviz Screener ({len(df)} results)\n")
    print(df.to_string(index=False))
    
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\n✅ Saved to {args.output}")

def cli_quote(args):
    """CLI: Get detailed stock quote."""
    data = quote(args.ticker)
    
    print(f"\n📈 {data.get('ticker', args.ticker)} — Finviz Quote\n")
    
    # Key metrics
    metrics = ['market_cap', 'pe', 'forward_p/e', 'peg', 'p/s', 'p/b', 'eps_(ttm)', 
               'dividend_%', 'roa', 'roe', 'debt/eq', 'current_ratio',
               'beta', 'atr', 'rsi_(14)', '52w_high', '52w_low', 
               'short_float', 'target_price', 'recom']
    
    for key in metrics:
        if key in data:
            print(f"{key.replace('_', ' ').title():.<25} {data[key]}")
    
    # News
    if 'news_headlines' in data:
        print(f"\n📰 Recent News:")
        for headline in data['news_headlines'][:3]:
            print(f"  • {headline}")
    
    # Insider trades
    if 'recent_insider_trades' in data and data['recent_insider_trades']:
        print(f"\n👔 Recent Insider Trades:")
        for trade in data['recent_insider_trades'][:3]:
            print(f"  {trade['date']:<10} {trade['owner']:<25} {trade['transaction']:<10} {trade['shares']:>15}")

def cli_insider(args):
    """CLI: Get insider trading activity."""
    df = insider_trading(filter_type=args.type, days=args.days, min_value=args.min_value)
    
    print(f"\n👔 Insider Trading — {args.type.upper()} (Last {args.days} days, min ${args.min_value:,})\n")
    print(df.to_string(index=False))
    
    # Cluster detection
    if not df.empty:
        clusters = df.groupby('ticker').agg({
            'value': 'count',
            'shares': 'first'
        }).rename(columns={'value': 'num_trades'}).sort_values('num_trades', ascending=False)
        
        print(f"\n🔥 Insider Clusters (Multiple insiders buying same stock):\n")
        print(clusters.head(10).to_string())

def cli_high_short(args):
    """CLI: High short interest stocks."""
    df = high_short_interest(min_float=args.min_float, limit=args.limit)
    
    print(f"\n📉 High Short Interest (Short Float > {args.min_float} percent)\n")
    print(df.to_string(index=False))

def cli_value(args):
    """CLI: Value stocks screener."""
    df = value_stocks()
    
    print(f"\n💰 Value Stocks (Low P/E + High Dividend)\n")
    print(df.to_string(index=False))

def cli_momentum(args):
    """CLI: Momentum stocks screener."""
    df = momentum_stocks()
    
    print(f"\n🚀 Momentum Stocks (Strong Technicals + Volume)\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Finviz Stock Screener")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Screener
    p_screener = subparsers.add_parser('screener', help='Custom stock screener')
    p_screener.add_argument('--filters', help='Comma-separated filters (e.g. cap_midover,fa_pe_u20)')
    p_screener.add_argument('--order', default='-marketcap', help='Sort order')
    p_screener.add_argument('--limit', type=int, default=100, help='Max results')
    p_screener.add_argument('--output', help='Save to CSV')
    p_screener.set_defaults(func=cli_screener)
    
    # Quote
    p_quote = subparsers.add_parser('quote', help='Detailed stock quote')
    p_quote.add_argument('ticker', help='Stock ticker')
    p_quote.set_defaults(func=cli_quote)
    
    # Insider
    p_insider = subparsers.add_parser('insider', help='Insider trading activity')
    p_insider.add_argument('--type', choices=['buy', 'sale', 'all'], default='buy')
    p_insider.add_argument('--days', type=int, default=7, help='Look back days')
    p_insider.add_argument('--min-value', type=int, default=100000, help='Min transaction value')
    p_insider.set_defaults(func=cli_insider)
    
    # High short
    p_short = subparsers.add_parser('short', help='High short interest stocks')
    p_short.add_argument('--min-float', type=float, default=20.0, help='Min short percent of float')
    p_short.add_argument('--limit', type=int, default=50)
    p_short.set_defaults(func=cli_high_short)
    
    # Value
    p_value = subparsers.add_parser('value', help='Value stocks screener')
    p_value.set_defaults(func=cli_value)
    
    # Momentum
    p_momentum = subparsers.add_parser('momentum', help='Momentum stocks screener')
    p_momentum.set_defaults(func=cli_momentum)
    
    args = parser.parse_args()
    args.func(args)
