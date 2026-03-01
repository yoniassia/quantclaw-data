"""
CBOE Put/Call Ratios, Most Active Options, Total Equity/Index Volume

Scrape daily market statistics from CBOE website tables.

Data: https://markets.cboe.com/us/options/market_statistics/daily/

Use cases:
- Market sentiment via PCR
- Volume analysis
- Equity vs index options activity
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pandas as pd
from pathlib import Path
from io import StringIO
import json
import re

CACHE_DIR = Path(__file__).parent.parent / "cache" / "cboe_put_call"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://markets.cboe.com/us/options/market_statistics/daily/"
MOST_ACTIVE_URL = "https://markets.cboe.com/us/options/market_statistics/most_active/"


def fetch_html(url: str, cache_file: str, use_cache: bool = True) -> Optional[str]:
    """Fetch and cache HTML from CBOE page."""
    cache_path = CACHE_DIR / cache_file
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return html
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_put_call_tables(html: str) -> pd.DataFrame:
    """Parse put/call ratio tables from HTML."""
    try:
        dfs = pd.read_html(StringIO(html))
        pcr_dfs = []
        for df in dfs:
            df.columns = df.columns.str.strip()
            df = df.dropna(how='all')
            if df.empty:
                continue
            headers = [str(h).lower() for h in df.columns]
            if any('put/call' in h or 'p/c' in h for h in headers):
                pcr_dfs.append(df)
        if pcr_dfs:
            combined = pd.concat(pcr_dfs, ignore_index=True)
            return combined.reset_index(drop=True)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error parsing PCR tables: {e}")
        return pd.DataFrame()


def get_put_call_ratios(use_cache: bool = True) -> pd.DataFrame:
    """Get latest put/call ratios from CBOE."""
    html = fetch_html(BASE_URL, "daily_stats.html", use_cache)
    if not html:
        return pd.DataFrame()
    return parse_put_call_tables(html)


def parse_volume_tables(html: str) -> Dict[str, float]:
    """Parse total volume from tables."""
    try:
        dfs = pd.read_html(StringIO(html))
        for df in dfs:
            text = df.to_string().lower()
            if 'total volume' in text:
                volumes = re.findall(r'(\\d+(?:,\\d{3})*(?:\\.\\d+)?)', text)
                if len(volumes) >= 3:
                    return {
                        'total_volume': float(volumes[0].replace(',', '')),
                        'equity_volume': float(volumes[1].replace(',', '')),
                        'index_volume': float(volumes[2].replace(',', ''))
                    }
        return {}
    except Exception as e:
        print(f"Error parsing volume: {e}")
        return {}


def get_total_volume(use_cache: bool = True) -> Dict[str, float]:
    """Get total equity/index options volume."""
    html = fetch_html(BASE_URL, "daily_stats.html", use_cache)
    if not html:
        return {}
    return parse_volume_tables(html)


def get_most_active(use_cache: bool = True) -> pd.DataFrame:
    """Get most active options."""
    html = fetch_html(MOST_ACTIVE_URL, "most_active.html", use_cache)
    if not html:
        return pd.DataFrame()
    try:
        dfs = pd.read_html(StringIO(html))
        for df in dfs:
            if len(df.columns) >= 3 and ('volume' in df.to_string().lower() or 'symbol' in df.to_string().lower()):
                return df.head(10)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error parsing most active: {e}")
        return pd.DataFrame()

# CLI functions

def cli_pcr():
    """CLI: Put/Call ratios."""
    df = get_put_call_ratios()
    if df.empty:
        print("No PCR data")
        return
    print("\
=== CBOE Put/Call Ratios ===")
    print(df.to_string(index=False))


def cli_volume():
    """CLI: Total volume."""
    data = get_total_volume()
    if not data:
        print("No volume data")
        return
    print("\
=== CBOE Options Volume ===")
    for k, v in data.items():
        print(f"{k.title().replace('_', ' ')}: {v:,.0f} contracts")


def cli_most_active():
    """CLI: Most active options."""
    df = get_most_active()
    if df.empty:
        print("No most active data")
        return
    print("\
=== CBOE Most Active Options ===")
    print(df.to_string(index=False))


def cli_summary():
    """CLI: Summary."""
    print("=== CBOE Options Market Summary ===")
    data = get_total_volume()
    if data:
        print(f"Total Volume: {data.get('total_volume', 0):,.0f} contracts")
    df = get_put_call_ratios()
    if not df.empty:
        print("Put/Call Ratios:")
        print(df.head().to_string(index=False))

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        cli_summary()
    elif args[0] == "pcr":
        cli_pcr()
    elif args[0] == "volume":
        cli_volume()
    elif args[0] == "most-active":
        cli_most_active()
    elif args[0] == "summary":
        cli_summary()
    else:
        print("Usage: [pcr|volume|most-active|summary]")
