#!/usr/bin/env python3
"""
SPACInsider SPAC Data Module — SPAC Lifecycle Tracking & Analysis

Data Source: SPACInsider.com (web scraping of public pages)
Update: Real-time scraping of public SPAC data
Free: Yes (public data)

Provides:
- Active SPAC listings (trading SPACs with trust values, redemption deadlines)
- SPAC merger/deal announcements (targets, vote dates, completion status)
- Post-merger performance tracking (NAV vs market price)
- SPAC IPO filings and pricings
- SPAC liquidations and deadline tracking

Usage:
    from modules import spacinsider
    
    # Get active SPACs
    df = spacinsider.get_data(period='active')
    
    # Get merger announcements
    df = spacinsider.get_data(period='merger')
    
    # Get performance tracking
    df = spacinsider.get_data(period='performance')
    
    # Get SPAC IPOs
    df = spacinsider.get_data(period='ipo')
    
    # Get liquidations
    df = spacinsider.get_data(period='liquidation')
"""

import requests
import pandas as pd
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from bs4 import BeautifulSoup

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 4 * 3600  # 4 hours

# Base URL
SPACINSIDER_BASE = "https://www.spacinsider.com"
HEADERS = {
    "User-Agent": "QuantClaw/1.0 quant@moneyclaw.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


def get_api_key() -> Optional[str]:
    """
    Check for SPACInsider API key in multiple locations:
    1. Environment variable SPACINSIDER_API_KEY
    2. .env file in quantclaw-data directory
    3. ~/.credentials/spacinsider.json
    
    Returns API key or None if not found.
    """
    # Check environment variable
    api_key = os.environ.get('SPACINSIDER_API_KEY')
    if api_key:
        return api_key
    
    # Check .env file
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('SPACINSIDER_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    
    # Check .credentials directory
    creds_file = os.path.expanduser('~/.credentials/spacinsider.json')
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            creds = json.load(f)
            return creds.get('api_key') or creds.get('SPACINSIDER_API_KEY')
    
    return None


def scrape_spac_listings(url: str) -> List[Dict]:
    """
    Scrape SPAC listings from SPACInsider public pages.
    
    Args:
        url: Full URL to scrape
        
    Returns:
        List of SPAC data dictionaries
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # SPACInsider uses dynamic data loading
        # Look for script tags with JSON data or tables
        spacs = []
        
        # Try to find data in script tags (Next.js often embeds data)
        scripts = soup.find_all('script', {'id': '__NEXT_DATA__'})
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Extract SPAC data from Next.js data structure
                if 'props' in data and 'pageProps' in data['props']:
                    page_data = data['props']['pageProps']
                    # Data structure varies, try common patterns
                    if 'spacs' in page_data:
                        spacs.extend(page_data['spacs'])
                    elif 'data' in page_data:
                        spacs.extend(page_data.get('data', []))
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Fallback: parse visible tables if no JSON found
        if not spacs:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                headers = [th.get_text(strip=True) for th in rows[0].find_all('th')] if rows else []
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        spac_entry = {}
                        for i, col in enumerate(cols):
                            key = headers[i] if i < len(headers) else f'column_{i}'
                            spac_entry[key] = col.get_text(strip=True)
                        spacs.append(spac_entry)
        
        return spacs
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []


def fetch_active_spacs() -> List[Dict]:
    """
    Fetch active SPAC listings.
    
    Returns:
        List of active SPAC dictionaries
    """
    url = f"{SPACINSIDER_BASE}/spacs"
    spacs = scrape_spac_listings(url)
    
    # Normalize data structure
    normalized = []
    for spac in spacs:
        entry = {
            'symbol': spac.get('symbol') or spac.get('ticker', 'N/A'),
            'name': spac.get('name') or spac.get('company', 'N/A'),
            'status': spac.get('status', 'Active'),
            'trust_value': spac.get('trust_value') or spac.get('trust', None),
            'redemption_deadline': spac.get('redemption_deadline') or spac.get('deadline', None),
            'unit_split': spac.get('unit_split', None),
            'sponsor': spac.get('sponsor', None),
            'ipo_date': spac.get('ipo_date', None),
            'focus': spac.get('focus') or spac.get('sector', None),
        }
        normalized.append(entry)
    
    return normalized


def fetch_merger_spacs() -> List[Dict]:
    """
    Fetch SPACs with merger announcements.
    
    Returns:
        List of SPAC merger dictionaries
    """
    # SPACInsider likely has a dedicated mergers/deals page
    url = f"{SPACINSIDER_BASE}/spacs"  # May need specific filter
    spacs = scrape_spac_listings(url)
    
    # Filter for merger-related SPACs
    merger_spacs = []
    for spac in spacs:
        if 'target' in spac or 'deal' in spac.get('status', '').lower():
            entry = {
                'symbol': spac.get('symbol') or spac.get('ticker', 'N/A'),
                'name': spac.get('name', 'N/A'),
                'target_company': spac.get('target') or spac.get('target_company', None),
                'announcement_date': spac.get('announcement_date') or spac.get('da_date', None),
                'vote_date': spac.get('vote_date') or spac.get('meeting_date', None),
                'completion_status': spac.get('status', 'Announced'),
                'deal_value': spac.get('deal_value') or spac.get('valuation', None),
                'industry': spac.get('industry') or spac.get('sector', None),
            }
            merger_spacs.append(entry)
    
    return merger_spacs if merger_spacs else [{'message': 'No merger data found'}]


def fetch_performance_data() -> List[Dict]:
    """
    Fetch post-merger performance data.
    
    Returns:
        List of performance dictionaries
    """
    # This would require price tracking post-merger
    # Placeholder implementation
    return [{
        'symbol': 'Example',
        'merger_close_date': None,
        'ipo_price': None,
        'nav_price': 10.00,
        'current_price': None,
        'return_from_nav': None,
        'message': 'Performance tracking requires real-time price data integration'
    }]


def fetch_ipo_spacs() -> List[Dict]:
    """
    Fetch recent SPAC IPO filings and pricings.
    
    Returns:
        List of SPAC IPO dictionaries
    """
    # Could scrape recent S-1 filings or IPO pricings
    url = f"{SPACINSIDER_BASE}/news/new-ipos"
    spacs = scrape_spac_listings(url)
    
    normalized = []
    for spac in spacs:
        entry = {
            'symbol': spac.get('symbol') or spac.get('ticker', 'N/A'),
            'name': spac.get('name', 'N/A'),
            'filing_date': spac.get('filing_date') or spac.get('s1_date', None),
            'pricing_date': spac.get('pricing_date') or spac.get('ipo_date', None),
            'offering_size': spac.get('offering_size') or spac.get('size', None),
            'unit_price': spac.get('unit_price', 10.00),
            'underwriter': spac.get('underwriter', None),
            'sponsor': spac.get('sponsor', None),
        }
        normalized.append(entry)
    
    return normalized if normalized else [{'message': 'No recent IPO data found'}]


def fetch_liquidation_spacs() -> List[Dict]:
    """
    Fetch SPACs approaching liquidation or already liquidated.
    
    Returns:
        List of liquidation dictionaries
    """
    url = f"{SPACINSIDER_BASE}/spacs"
    spacs = scrape_spac_listings(url)
    
    # Filter for SPACs near deadline or liquidating
    liquidation_spacs = []
    for spac in spacs:
        status = spac.get('status', '').lower()
        if 'liquidat' in status or 'deadline' in status or 'expir' in status:
            entry = {
                'symbol': spac.get('symbol') or spac.get('ticker', 'N/A'),
                'name': spac.get('name', 'N/A'),
                'deadline': spac.get('redemption_deadline') or spac.get('deadline', None),
                'trust_value': spac.get('trust_value', None),
                'status': spac.get('status', 'Approaching Deadline'),
                'days_remaining': spac.get('days_remaining', None),
                'extension_status': spac.get('extension', None),
            }
            liquidation_spacs.append(entry)
    
    return liquidation_spacs if liquidation_spacs else [{'message': 'No liquidation data found'}]


def get_data(
    ticker: Optional[str] = None,
    period: str = 'active',
    **kwargs
) -> pd.DataFrame:
    """
    Fetch SPAC data from SPACInsider.
    
    Args:
        ticker: Filter by specific ticker symbol (optional)
        period: Data category to fetch:
                - 'active': Active SPAC listings (default)
                - 'merger': SPAC mergers/deals
                - 'performance': Post-merger performance
                - 'ipo': Recent SPAC IPOs
                - 'liquidation': SPACs approaching liquidation
        
    Returns:
        DataFrame with SPAC data
    """
    # Check cache
    cache_key = f"{period}"
    cache_file = os.path.join(CACHE_DIR, f"spacinsider_{cache_key}.json")
    
    if os.path.exists(cache_file):
        cache_age = time.time() - os.path.getmtime(cache_file)
        if cache_age < CACHE_TTL:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                df = pd.DataFrame(cached_data)
                
                # Apply ticker filter if provided
                if ticker and 'symbol' in df.columns:
                    df = df[df['symbol'].str.contains(ticker, case=False, na=False)]
                
                return df
    
    # Fetch fresh data based on period
    if period == 'active':
        data = fetch_active_spacs()
    elif period == 'merger':
        data = fetch_merger_spacs()
    elif period == 'performance':
        data = fetch_performance_data()
    elif period == 'ipo':
        data = fetch_ipo_spacs()
    elif period == 'liquidation':
        data = fetch_liquidation_spacs()
    else:
        return pd.DataFrame({
            "error": [f"Invalid period: {period}. Use 'active', 'merger', 'performance', 'ipo', or 'liquidation'"]
        })
    
    if not data:
        return pd.DataFrame({
            "message": [f"No data returned for period: {period}"]
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add fetch timestamp
    df['fetch_time'] = datetime.now().isoformat()
    
    # Cache the results
    cache_data = df.to_dict('records')
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, default=str)
    
    # Apply ticker filter if provided
    if ticker and 'symbol' in df.columns:
        df = df[df['symbol'].str.contains(ticker, case=False, na=False)]
    
    return df


if __name__ == "__main__":
    import sys
    
    # CLI test interface
    if len(sys.argv) > 1:
        period = sys.argv[1]
        print(f"=== SPACInsider {period.upper()} Data ===")
        result = get_data(period=period)
    else:
        print("=== SPACInsider Active SPACs (Default) ===")
        result = get_data(period='active')
    
    if not result.empty:
        print(result.to_json(orient='records', date_format='iso', indent=2))
    else:
        print("No data returned")
