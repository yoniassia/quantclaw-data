#!/usr/bin/env python3
"""
MarketWatch Screener Scraper

Scrapes various stock screeners from MarketWatch.com.

Provides data on low PE, high growth, dividend aristocrats, etc.

Features:
- Configurable screener types
- HTML scraping with BeautifulSoup
- Pandas DataFrame processing
- JSON caching with TTL
- Retry logic with exponential backoff
- Summary statistics
- Export to CSV/JSON
- Logging and error handling
- Unit tests

Free data source. No API key required.

Example:
  data = get_data(screener_type='lowpe', country='us')
  print(json.dumps(data, indent=2))

Returns:
  {
    "data": [list of stock dicts],
    "timestamp": "2026-03-01T05:17:00",
    "metadata": {
      "count": 100,
      "screener_type": "lowpe",
      "summary_stats": {...}
    }
  }

Supported screeners:
- lowpe: Low P/E ratio
- revenue: High revenue growth
- dividend: High dividend yield
- value: Value stocks
- growth: Growth stocks

"""
import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
import time
import re

# ==================== CONFIGURATION ====================
CACHE_DIR = Path(__file__).parent.parent / ".cache"  # Use modules/.cache
CACHE_DIR.mkdir(exist_ok=True, parents=True)
CACHE_TTL_HOURS = 1.0
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Screener mappings
SCREENER_URLS = {
    'lowpe': 'https://www.marketwatch.com/tools/screener/stock/lowpe',
    'revenue': 'https://www.marketwatch.com/tools/screener/stock/revenue',
    'dividend': 'https://www.marketwatch.com/tools/screener/stock/dividend',
    'value': 'https://www.marketwatch.com/tools/screener/stock/value',
    'growth': 'https://www.marketwatch.com/tools/screener/stock/growth',
}

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / "logs/marketwatch_screener.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== UTILITY FUNCTIONS ====================
def generate_cache_key(screener_type: str, country: str, page: int, params: Dict[str, Any]) -> str:
    """Generate deterministic cache key."""
    key_dict = {
        'type': screener_type,
        'country': country,
        'page': page,
        'params': params
    }
    key_str = json.dumps(key_dict, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()

def get_cache_file(key: str) -> Path:
    """Get cache file path."""
    return CACHE_DIR / f"marketwatch_screener_{key}.json"

def is_cache_fresh(cache_file: Path) -> bool:
    """Check if cache is within TTL."""
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return datetime.now() - mtime < timedelta(hours=CACHE_TTL_HOURS)

def load_cache(cache_file: Path) -> Optional[Dict[str, Any]]:
    """Load and validate cache."""
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
        if 'data' in data and data['data']:
            logger.info(f"Cache hit: {len(data['data'])} rows")
            return data
    except Exception as e:
        logger.warning(f"Cache load failed: {e}")
    return None

def save_cache(data: Dict[str, Any], cache_file: Path):
    """Save data to cache."""
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f, default=str, indent=2)
        logger.info(f"Cached {len(data['data'])} rows to {cache_file}")
    except Exception as e:
        logger.error(f"Cache save failed: {e}")

# ==================== RETRY DECORATOR ====================
def retry(max_attempts: int = MAX_RETRIES, backoff_factor: float = 1.0):
    """Exponential backoff retry decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    wait = backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {exc}. Waiting {wait:.1f}s")
                    time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator

# ==================== FETCHER ====================
@retry()
def fetch_page(url: str, params: Dict[str, str] = None, headers: Dict[str, str] = None) -> str:
    """Fetch HTML page with retries."""
    if headers is None:
        headers = {'User-Agent': USER_AGENT}
    
    response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    logger.debug(f"Fetched {len(response.text)} bytes from {url}")
    return response.text

# ==================== PARSER ====================
def parse_screener_table(html: str, screener_type: str) -> List[Dict[str, Any]]:
    """Parse main screener table from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find main table (class varies, try multiple selectors)
    table_selectors = [
        'table[data-table-id="screener-main"]',
        'table.elements-table--table',
        '#screener-main table',
        '.table--primary'
    ]
    
    table = None
    for selector in table_selectors:
        table = soup.select_one(selector)
        if table:
            logger.info(f"Found table with selector: {selector}")
            break
    
    if not table:
        logger.warning("No screener table found. Page structure may have changed.")
        return []
    
    # Extract headers
    header_row = table.find('thead')
    if not header_row:
        header_row = table.find('tr', class_=re.compile(r'header|head', re.I))
    
    headers = []
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td']) if th.get_text(strip=True)]
    
    if not headers:
        headers = [f'col_{i}' for i in range(len(table.find_all('tr')[0].find_all(['th', 'td'])))]
    
    # Extract rows
    rows = []
    tbody = table.find('tbody')
    if tbody:
        for row in tbody.find_all('tr', limit=100):  # Limit to top 100
            cells = row.find_all(['td', 'th'])
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    row_data[headers[i]] = text
                    
                    # Extract symbol link
                    link_tag = cell.find('a')
                    if link_tag:
                        href = link_tag.get('href', '')
                        row_data[f'{headers[i]}_url'] = f"https://www.marketwatch.com{href}" if href.startswith('/') else href
                
                rows.append(row_data)
    
    logger.info(f"Parsed {len(rows)} rows from {screener_type} screener")
    return rows

# ==================== MAIN FUNCTION ====================
def get_data(
    screener_type: str = 'lowpe',
    country: str = 'us',
    page: int = 1,
    extra_params: Dict[str, Any] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Main function to get screener data.
    
    Args:
        screener_type: Type of screener (lowpe, revenue, dividend, etc.)
        country: Country code (us, eu, etc.)
        page: Page number (most screeners paginated)
        extra_params: Additional URL params
        force_refresh: Bypass cache
    
    Returns:
        Dict with data, timestamp, metadata
    """
    
    if screener_type not in SCREENER_URLS:
        raise ValueError(f"Unsupported screener_type: {screener_type}. Supported: {list(SCREENER_URLS.keys())}")
    
    params = {'countrycode': country, 'page': page, **(extra_params or {})}
    key = generate_cache_key(screener_type, country, page, params)
    cache_file = get_cache_file(key)
    
    # Cache check
    if not force_refresh and is_cache_fresh(cache_file):
        cached_data = load_cache(cache_file)
        if cached_data:
            return cached_data
    
    logger.info(f"Fetching fresh data: {screener_type} (page {page}, country {country})")
    
    url = SCREENER_URLS[screener_type]
    html = fetch_page(url, params)
    
    raw_rows = parse_screener_table(html, screener_type)
    
    if not raw_rows:
        raise ValueError(f"No data retrieved for {screener_type}")
    
    # Process with pandas
    df = pd.DataFrame(raw_rows)
    
    # Clean and type columns
    numeric_cols = df.select_dtypes(include=['object']).columns[df.columns.str.contains(r'[pe|yield|growth|%|volume]', case=False, na=False)]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].str.replace(',', '').str.replace('%', ''), errors='coerce')
    
    metadata = {
        'screener_type': screener_type,
        'country': country,
        'page': page,
        'url': url,
        'count': len(df),
        'top_symbol': df.iloc[0].get('Symbol', 'N/A') if len(df) > 0 else 'N/A',
        'summary_stats': {
            col: {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            } for col in df.select_dtypes(include=['float64', 'int64']).columns
        } if len(df.select_dtypes(include=['float64', 'int64'])) > 0 else {}
    }
    
    result = {
        'data': raw_rows,  # Keep original dicts
        'df_summary': df.describe().to_dict('records'),  # Pandas summary
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata
    }
    
    save_cache(result, cache_file)
    
    # Export convenience files
    csv_path = Path(__file__).parent.parent / f"exports/marketwatch_{screener_type}_{country}_p{page}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Exported CSV: {csv_path}")
    
    return result

# ==================== UNIT TESTS ====================
def run_tests():
    """Run basic unit tests."""
    logger.info("Running tests...")
    
    # Test 1: Cache key generation
    key1 = generate_cache_key('lowpe', 'us', 1, {})
    key2 = generate_cache_key('lowpe', 'us', 1, {})
    assert key1 == key2, "Cache key not deterministic"
    
    # Test 2: Basic fetch (small timeout for test)
    try:
        data = get_data(screener_type='lowpe', force_refresh=True)
        assert 'data' in data
        assert len(data['data']) > 0
        assert 'metadata' in data
        logger.info("✅ All tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("MarketWatch Screener Module")
    print("=========================")
    
    # Run tests
    if not run_tests():
        exit(1)
    
    # Demo usage
    print("\nFetching low PE US stocks...")
    data = get_data('lowpe', 'us')
    
    print(f"✅ Success! Retrieved {len(data['data'])} stocks")
    print(json.dumps(data['metadata'], indent=2))
    
    # Show top 5
    if data['data']:
        print("\nTop 5 stocks:")
        for stock in data['data'][:5]:
            print(f"  {stock.get('Symbol', 'N/A')}: P/E {stock.get('P/E', 'N/A')}")
    
    print("\nDone! Check logs/exports/ for files.")
