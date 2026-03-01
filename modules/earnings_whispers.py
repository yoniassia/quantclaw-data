#!/usr/bin/env python3
"""
Earnings Whispers Scraper

Scrapes earnings calendar and whisper numbers from EarningsWhispers.com.

Tracks expected EPS, whisper EPS (street insider expectations), reported, surprise %.

Features:
- Daily/weekly calendar scrape
- Whisper vs consensus differential
- Surprise history
- Caching & retries
- Pandas processing
- Alert thresholds for big surprises
- Export CSV/JSON

Free scrape. No API.

Example:
  data = get_data(date="today")
  
Returns:
  {'data': [earnings_events], 'metadata': {...}, 'timestamp': ...}

"""

import os
import json
import logging
from datetime import datetime, timedelta, date
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps
import time
import re
from urllib.parse import urljoin, urlparse

# ==================== CONFIGURATION ====================
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)
CACHE_TTL_HOURS = 2.0  # Earnings data updates frequently
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BASE_URL = "https://www.earningswhispers.com"

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== UTILITIES ====================
def cache_key(date_str: str, view: str = "today") -> str:
    key_dict = {'date': date_str, 'view': view}
    return hashlib.md5(json.dumps(key_dict, sort_keys=True).encode()).hexdigest()

def get_cache_path(key: str) -> Path:
    return CACHE_DIR / f"earnings_whispers_{key}.json"

def is_fresh_cache(path: Path) -> bool:
    if not path.exists():
        return False
    stat = path.stat()
    mtime_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
    return mtime_age < timedelta(hours=CACHE_TTL_HOURS)

def load_json_cache(path: Path) -> Optional[Dict]:
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None

def save_json_cache(data: Dict, path: Path):
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, 'w') as f:
        json.dump(data, f, default=str, indent=2)

# ==================== RETRY ====================
def retry(times=MAX_RETRIES):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == times - 1:
                        raise
                    logger.warning(f"Retry {i+1}/{times}: {e}")
                    time.sleep(2 ** i)
        return wrapper
    return deco

# ==================== FETCH ====================
@retry()
def fetch_calendar(date_obj: date, view: str = "today") -> str:
    """Fetch earnings calendar HTML."""
    if view == "today":
        url = f"{BASE_URL}/calendar/t"
    elif view == "w":
        url = f"{BASE_URL}/calendar/w"
    else:
        url = f"{BASE_URL}/calendar?d={date_obj.strftime('%Y%m%d')}&o=marketcap&u={date_obj.strftime('%Y%m%d')}"
    
    headers = {'User-Agent': USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text

# ==================== PARSER ====================
def parse_earnings(html: str) -> List[Dict[str, Any]]:
    """Parse earnings table."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find main calendar table
    table = soup.find('table', class_ = lambda x: x and 'calendar' in x.lower())
    if not table:
        table = soup.find('table', id='calendar')
    
    if not table:
        logger.warning("Calendar table not found")
        return []
    
    events = []
    
    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip header
        cells = row.find_all('td')
        if len(cells) < 8:
            continue
        
        event = {}
        event['time'] = cells[0].get_text(strip=True)
        event['ticker'] = cells[1].find('a').get_text(strip=True) if cells[1].find('a') else ''
        event['company'] = cells[1].get('title', '') or cells[1].get_text(strip=True)
        
        # Whisper numbers
        whisper_cell = cells[2].get_text(strip=True)
        event['whisper_eps'] = re.search(r'([\d\.\-]+)', whisper_cell).group(1) if re.search(r'([\d\.\-]+)', whisper_cell) else None
        
        # Consensus
        consensus_cell = cells[3].get_text(strip=True)
        event['consensus_eps'] = re.search(r'([\d\.\-]+)', consensus_cell).group(1) if re.search(r'([\d\.\-]+)', consensus_cell) else None
        
        # Reported (if after)
        reported_cell = cells[4].get_text(strip=True)
        event['reported_eps'] = re.search(r'([\d\.\-]+)', reported_cell).group(1) if re.search(r'([\d\.\-]+)', reported_cell) else None
        
        # Surprise %
        surprise_cell = cells[5].get_text(strip=True)
        event['surprise_pct'] = re.search(r'([\d\.\-]+)%', surprise_cell).group(1) if re.search(r'([\d\.\-]+)%', surprise_cell) else None
        
        event['market_cap'] = cells[6].get_text(strip=True)
        event['url'] = urljoin(BASE_URL, cells[1].find('a')['href']) if cells[1].find('a') else ''
        
        events.append(event)
    
    return events

# ==================== MAIN ====================
def get_data(
    date_str: str = "today",
    view: str = "today",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get earnings whispers data.
    
    Args:
        date_str: 'today', 'tomorrow', or 'YYYY-MM-DD'
        view: 'today', 'w' (week)
        force_refresh: Ignore cache
    """
    
    if date_str == "today":
        target_date = date.today()
    elif date_str == "tomorrow":
        target_date = date.today() + timedelta(days=1)
    else:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    key = cache_key(target_date.isoformat(), view)
    cache_path = get_cache_path(key)
    
    if not force_refresh and is_fresh_cache(cache_path):
        cached = load_json_cache(cache_path)
        if cached:
            return cached
    
    logger.info(f"Fetching earnings for {target_date} ({view})")
    
    html = fetch_calendar(target_date, view)
    raw_events = parse_earnings(html)
    
    if not raw_events:
        raise ValueError("No earnings data parsed")
    
    # Pandas processing
    df = pd.DataFrame(raw_events)
    
    # Compute differentials
    df['whisper_vs_consensus'] = pd.to_numeric(df['whisper_eps'], errors='coerce') - pd.to_numeric(df['consensus_eps'], errors='coerce')
    
    # Flag big surprises
    df['big_surprise'] = abs(pd.to_numeric(df['surprise_pct'], errors='coerce')) > 5.0
    
    metadata = {
        'date': target_date.isoformat(),
        'view': view,
        'total': len(df),
        'big_surprises': int(df['big_surprise'].sum()),
        'avg_whisper_consensus_diff': float(df['whisper_vs_consensus'].mean())
    }
    
    result = {
        'data': raw_events,
        'pandas_summary': df.describe().to_dict(),
        'metadata': metadata,
        'timestamp': datetime.now().isoformat()
    }
    
    save_json_cache(result, cache_path)
    
    # Export
    export_path = Path(__file__).parent.parent / f"exports/ew_{target_date.strftime('%Y%m%d')}.csv"
    export_path.parent.mkdir(exist_ok=True)
    df.to_csv(export_path, index=False)
    
    return result

if __name__ == "__main__":
    data = get_data()
    print(json.dumps({k: v for k, v in data.items() if k != 'pandas_summary'}, indent=2))
    print(f"\nExported to exports/ folder")
